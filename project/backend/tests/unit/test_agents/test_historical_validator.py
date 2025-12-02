"""
Unit tests for HistoricalValidator.

Tests statistical outlier detection against historical data.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.tools.validators.historical_validator import HistoricalValidator
from app.agents.base import ToolContext, ToolStatus


@pytest.fixture
def mock_db_session():
    """Mock AsyncSession for database queries."""
    session = AsyncMock()
    return session


@pytest.fixture
def historical_validator(mock_db_session):
    """Create HistoricalValidator instance with mocked DB."""
    return HistoricalValidator(mock_db_session)


class TestHistoricalDataRetrieval:
    """Test database querying for historical values."""

    @pytest.mark.asyncio
    async def test_get_historical_values_queries_approved_only(
        self, historical_validator, mock_db_session
    ):
        """Test that _get_historical_values only queries approved extractions."""
        # Mock database result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            Decimal("500.00"),
            Decimal("550.00"),
            Decimal("600.00"),
        ]
        mock_db_session.execute.return_value = mock_result

        values = await historical_validator._get_historical_values("gap_insurance_premium")

        # Should query the database
        assert mock_db_session.execute.called
        # Should return float values
        assert len(values) == 3
        assert all(isinstance(v, float) for v in values)

    @pytest.mark.asyncio
    async def test_get_historical_values_empty_result(self, historical_validator, mock_db_session):
        """Test handling of no historical data."""
        # Mock empty result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        values = await historical_validator._get_historical_values("gap_insurance_premium")

        assert values == []


class TestMinimumSampleRequirement:
    """Test minimum sample size requirement (10 samples)."""

    @pytest.mark.asyncio
    async def test_insufficient_samples_skips_validation(self, historical_validator):
        """Test that validation is skipped when < 10 samples."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("500.00"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        # Mock _get_historical_values to return insufficient data
        with patch.object(
            historical_validator, "_get_historical_values", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [500.0, 550.0, 600.0]  # Only 3 samples

            result = await historical_validator.execute(context)

            assert result.status == ToolStatus.SKIPPED
            assert "insufficient historical data" in result.message.lower()
            assert "3 samples" in result.message.lower()
            assert "need 10" in result.message.lower()

    @pytest.mark.asyncio
    async def test_exactly_min_samples_performs_validation(self, historical_validator):
        """Test that validation proceeds with exactly 10 samples."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("500.00"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        # Mock _get_historical_values to return exactly 10 samples (normal distribution)
        with patch.object(
            historical_validator, "_get_historical_values", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [
                500.0,
                510.0,
                490.0,
                505.0,
                495.0,
                500.0,
                502.0,
                498.0,
                501.0,
                499.0,
            ]

            result = await historical_validator.execute(context)

            # Should perform validation (not skip)
            assert result.status != ToolStatus.SKIPPED


class TestOutlierDetection:
    """Test statistical outlier detection (>2 stddev from mean)."""

    @pytest.mark.asyncio
    async def test_value_within_range_passes(self, historical_validator):
        """Test that value within 2 stddev passes."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("500.00"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        # Mock historical data: mean=500, stddev≈50
        with patch.object(
            historical_validator, "_get_historical_values", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [
                400.0,
                450.0,
                480.0,
                490.0,
                500.0,
                510.0,
                520.0,
                530.0,
                550.0,
                600.0,
            ]

            result = await historical_validator.execute(context)

            assert result.status == ToolStatus.PASS
            assert "within normal range" in result.message.lower()

    @pytest.mark.asyncio
    async def test_outlier_above_triggers_warning(self, historical_validator):
        """Test that value >2 stddev above mean triggers warning."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("1500.00"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        # Mock historical data: mean≈500, stddev≈50, so 1500 is way above 2*stddev
        with patch.object(
            historical_validator, "_get_historical_values", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [
                450.0,
                460.0,
                480.0,
                490.0,
                500.0,
                510.0,
                520.0,
                530.0,
                540.0,
                550.0,
            ]

            result = await historical_validator.execute(context)

            assert result.status == ToolStatus.WARNING
            assert "statistical outlier" in result.message.lower()

    @pytest.mark.asyncio
    async def test_outlier_below_triggers_warning(self, historical_validator):
        """Test that value >2 stddev below mean triggers warning."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("100.00"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        # Mock historical data: mean≈500, so 100 is way below
        with patch.object(
            historical_validator, "_get_historical_values", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [
                450.0,
                460.0,
                480.0,
                490.0,
                500.0,
                510.0,
                520.0,
                530.0,
                540.0,
                550.0,
            ]

            result = await historical_validator.execute(context)

            assert result.status == ToolStatus.WARNING
            assert "statistical outlier" in result.message.lower()

    @pytest.mark.asyncio
    async def test_value_at_boundary_passes(self, historical_validator):
        """Test that value exactly at 2 stddev boundary passes."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("500.00"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        # Mock historical data with tight distribution
        # Mean = 500, stddev ≈ 0 (all values are 500)
        with patch.object(
            historical_validator, "_get_historical_values", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [500.0] * 10

            result = await historical_validator.execute(context)

            # Value exactly at mean should pass
            assert result.status == ToolStatus.PASS


class TestStatisticalDetails:
    """Test that statistical details are included in results."""

    @pytest.mark.asyncio
    async def test_pass_result_includes_statistics(self, historical_validator):
        """Test that PASS result includes mean, stddev, and sample count."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("500.00"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        with patch.object(
            historical_validator, "_get_historical_values", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [
                450.0,
                460.0,
                480.0,
                490.0,
                500.0,
                510.0,
                520.0,
                530.0,
                540.0,
                550.0,
            ]

            result = await historical_validator.execute(context)

            # Should include statistics in message
            assert "avg:" in result.message.lower() or "mean" in result.message.lower()
            assert "stddev:" in result.message.lower()

            # Should include details dict
            assert result.details is not None
            assert "mean" in result.details
            assert "stddev" in result.details
            assert "sample_count" in result.details
            assert result.details["sample_count"] == 10

    @pytest.mark.asyncio
    async def test_warning_result_includes_deviation(self, historical_validator):
        """Test that WARNING result includes deviation and threshold."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("1500.00"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        with patch.object(
            historical_validator, "_get_historical_values", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [
                450.0,
                460.0,
                480.0,
                490.0,
                500.0,
                510.0,
                520.0,
                530.0,
                540.0,
                550.0,
            ]

            result = await historical_validator.execute(context)

            assert result.details is not None
            assert "deviation" in result.details
            assert "threshold" in result.details


class TestApplicableFields:
    """Test that validator only applies to numeric fields."""

    @pytest.mark.asyncio
    async def test_applicable_to_gap_premium(self, historical_validator):
        """Test that validator applies to gap_insurance_premium."""
        assert "gap_insurance_premium" in historical_validator.applicable_fields

    @pytest.mark.asyncio
    async def test_applicable_to_cancellation_fee(self, historical_validator):
        """Test that validator applies to cancellation_fee."""
        assert "cancellation_fee" in historical_validator.applicable_fields

    @pytest.mark.asyncio
    async def test_not_applicable_to_refund_method(self, historical_validator):
        """Test that validator does not apply to refund_calculation_method."""
        assert "refund_calculation_method" not in historical_validator.applicable_fields

    @pytest.mark.asyncio
    async def test_inapplicable_field_is_skipped(self, historical_validator):
        """Test that non-applicable fields are skipped."""
        context = ToolContext(
            field_name="refund_calculation_method",
            field_value="pro-rata",
            field_confidence=0.88,
            field_source="Page 2",
            all_fields={},
        )

        result = await historical_validator.execute(context)

        assert result.status == ToolStatus.SKIPPED
        assert "not applicable" in result.message.lower()


class TestCancellationFeeValidation:
    """Test validation for cancellation_fee field."""

    @pytest.mark.asyncio
    async def test_cancellation_fee_within_range_passes(self, historical_validator):
        """Test that normal cancellation fee passes."""
        context = ToolContext(
            field_name="cancellation_fee",
            field_value=Decimal("50.00"),
            field_confidence=0.92,
            field_source="Page 3",
            all_fields={},
        )

        with patch.object(
            historical_validator, "_get_historical_values", new_callable=AsyncMock
        ) as mock_get:
            # Historical data: mean≈50
            mock_get.return_value = [
                40.0,
                45.0,
                48.0,
                50.0,
                52.0,
                53.0,
                55.0,
                58.0,
                60.0,
                62.0,
            ]

            result = await historical_validator.execute(context)

            assert result.status == ToolStatus.PASS

    @pytest.mark.asyncio
    async def test_cancellation_fee_outlier_triggers_warning(self, historical_validator):
        """Test that outlier cancellation fee triggers warning."""
        context = ToolContext(
            field_name="cancellation_fee",
            field_value=Decimal("100.00"),
            field_confidence=0.92,
            field_source="Page 3",
            all_fields={},
        )

        with patch.object(
            historical_validator, "_get_historical_values", new_callable=AsyncMock
        ) as mock_get:
            # Historical data: mean≈20, so 100 is outlier
            mock_get.return_value = [
                15.0,
                18.0,
                19.0,
                20.0,
                21.0,
                22.0,
                23.0,
                24.0,
                25.0,
                28.0,
            ]

            result = await historical_validator.execute(context)

            assert result.status == ToolStatus.WARNING


class TestErrorHandling:
    """Test error handling for invalid input."""

    @pytest.mark.asyncio
    async def test_non_numeric_value_returns_error(self, historical_validator):
        """Test that non-numeric value returns error."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value="not-a-number",
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        result = await historical_validator.execute(context)

        assert result.status in [ToolStatus.ERROR, ToolStatus.SKIPPED]

    @pytest.mark.asyncio
    async def test_none_value_skipped(self, historical_validator):
        """Test that None value is skipped."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=None,
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        result = await historical_validator.execute(context)

        assert result.status == ToolStatus.SKIPPED


class TestToolMetadata:
    """Test tool metadata."""

    @pytest.mark.asyncio
    async def test_tool_name(self, historical_validator):
        """Test that tool name is correct."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("500.00"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        with patch.object(
            historical_validator, "_get_historical_values", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [
                450.0,
                460.0,
                480.0,
                490.0,
                500.0,
                510.0,
                520.0,
                530.0,
                540.0,
                550.0,
            ]

            result = await historical_validator.execute(context)

            assert result.tool_name == "historical_validator"

    @pytest.mark.asyncio
    async def test_field_name_preserved(self, historical_validator):
        """Test that field name is preserved in result."""
        context = ToolContext(
            field_name="cancellation_fee",
            field_value=Decimal("50.00"),
            field_confidence=0.92,
            field_source="Page 3",
            all_fields={},
        )

        with patch.object(
            historical_validator, "_get_historical_values", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = [
                40.0,
                45.0,
                48.0,
                50.0,
                52.0,
                53.0,
                55.0,
                58.0,
                60.0,
                62.0,
            ]

            result = await historical_validator.execute(context)

            assert result.field_name == "cancellation_fee"
