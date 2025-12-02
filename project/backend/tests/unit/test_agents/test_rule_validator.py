"""
Unit tests for RuleValidator.

Tests business rule validation for extracted fields.
"""

import pytest
from decimal import Decimal

from app.agents.tools.validators.rule_validator import RuleValidator
from app.agents.base import ToolContext, ToolStatus


@pytest.fixture
def rule_validator():
    """Create RuleValidator instance."""
    return RuleValidator()


class TestGAPPremiumValidation:
    """Test GAP insurance premium validation ($100-$2000)."""

    @pytest.mark.asyncio
    async def test_valid_gap_premium(self, rule_validator):
        """Test that valid GAP premium passes."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("500.00"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS
        assert "within expected range" in result.message.lower()

    @pytest.mark.asyncio
    async def test_gap_premium_at_lower_boundary(self, rule_validator):
        """Test GAP premium at minimum value ($100)."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("100.00"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS

    @pytest.mark.asyncio
    async def test_gap_premium_at_upper_boundary(self, rule_validator):
        """Test GAP premium at maximum value ($2000)."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("2000.00"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS

    @pytest.mark.asyncio
    async def test_gap_premium_below_minimum(self, rule_validator):
        """Test GAP premium below $100 triggers warning."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("99.99"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.WARNING
        assert "outside typical range" in result.message.lower()

    @pytest.mark.asyncio
    async def test_gap_premium_above_maximum(self, rule_validator):
        """Test GAP premium above $2000 triggers warning."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("2000.01"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.WARNING
        assert "outside typical range" in result.message.lower()

    @pytest.mark.asyncio
    async def test_gap_premium_negative_value(self, rule_validator):
        """Test that negative GAP premium triggers warning (out of range)."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("-100.00"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.WARNING

    @pytest.mark.asyncio
    async def test_gap_premium_zero(self, rule_validator):
        """Test that zero GAP premium triggers warning (out of range)."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("0.00"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.WARNING

    @pytest.mark.asyncio
    async def test_gap_premium_as_string(self, rule_validator):
        """Test that GAP premium can be provided as string."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value="500.00",
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS


class TestCancellationFeeValidation:
    """Test cancellation fee validation ($0-$100)."""

    @pytest.mark.asyncio
    async def test_valid_cancellation_fee(self, rule_validator):
        """Test that valid cancellation fee passes."""
        context = ToolContext(
            field_name="cancellation_fee",
            field_value=Decimal("50.00"),
            field_confidence=0.92,
            field_source="Page 2",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS
        assert "within expected range" in result.message.lower()

    @pytest.mark.asyncio
    async def test_cancellation_fee_at_lower_boundary(self, rule_validator):
        """Test cancellation fee at minimum value ($0)."""
        context = ToolContext(
            field_name="cancellation_fee",
            field_value=Decimal("0.00"),
            field_confidence=0.92,
            field_source="Page 2",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS

    @pytest.mark.asyncio
    async def test_cancellation_fee_at_upper_boundary(self, rule_validator):
        """Test cancellation fee at maximum value ($100)."""
        context = ToolContext(
            field_name="cancellation_fee",
            field_value=Decimal("100.00"),
            field_confidence=0.92,
            field_source="Page 2",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS

    @pytest.mark.asyncio
    async def test_cancellation_fee_below_minimum(self, rule_validator):
        """Test that negative cancellation fee fails."""
        context = ToolContext(
            field_name="cancellation_fee",
            field_value=Decimal("-0.01"),
            field_confidence=0.92,
            field_source="Page 2",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.FAIL
        assert "cannot be negative" in result.message.lower()

    @pytest.mark.asyncio
    async def test_cancellation_fee_above_maximum(self, rule_validator):
        """Test cancellation fee above $100 triggers warning."""
        context = ToolContext(
            field_name="cancellation_fee",
            field_value=Decimal("100.01"),
            field_confidence=0.92,
            field_source="Page 2",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.WARNING
        assert "exceeds typical maximum" in result.message.lower()

    @pytest.mark.asyncio
    async def test_cancellation_fee_as_string(self, rule_validator):
        """Test that cancellation fee can be provided as string."""
        context = ToolContext(
            field_name="cancellation_fee",
            field_value="50.00",
            field_confidence=0.92,
            field_source="Page 2",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS


class TestRefundMethodValidation:
    """Test refund calculation method validation."""

    @pytest.mark.asyncio
    async def test_known_refund_method_pro_rata(self, rule_validator):
        """Test that 'pro-rata' is recognized."""
        context = ToolContext(
            field_name="refund_calculation_method",
            field_value="pro-rata",
            field_confidence=0.88,
            field_source="Page 3",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS
        assert "is recognized" in result.message.lower()

    @pytest.mark.asyncio
    async def test_known_refund_method_prorata_no_hyphen(self, rule_validator):
        """Test that 'pro rata' (no hyphen) is recognized."""
        context = ToolContext(
            field_name="refund_calculation_method",
            field_value="pro rata",
            field_confidence=0.88,
            field_source="Page 3",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS

    @pytest.mark.asyncio
    async def test_known_refund_method_rule_of_78s(self, rule_validator):
        """Test that 'rule of 78s' is recognized."""
        context = ToolContext(
            field_name="refund_calculation_method",
            field_value="rule of 78s",
            field_confidence=0.88,
            field_source="Page 3",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS

    @pytest.mark.asyncio
    async def test_known_refund_method_actuarial(self, rule_validator):
        """Test that 'actuarial' is recognized."""
        context = ToolContext(
            field_name="refund_calculation_method",
            field_value="actuarial",
            field_confidence=0.88,
            field_source="Page 3",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS

    @pytest.mark.asyncio
    async def test_known_refund_method_flat(self, rule_validator):
        """Test that 'flat' is recognized."""
        context = ToolContext(
            field_name="refund_calculation_method",
            field_value="flat",
            field_confidence=0.88,
            field_source="Page 3",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS

    @pytest.mark.asyncio
    async def test_known_refund_method_case_insensitive(self, rule_validator):
        """Test that refund method matching is case-insensitive."""
        context = ToolContext(
            field_name="refund_calculation_method",
            field_value="PRO-RATA",
            field_confidence=0.88,
            field_source="Page 3",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS

    @pytest.mark.asyncio
    async def test_unknown_refund_method(self, rule_validator):
        """Test that unknown refund method triggers warning."""
        context = ToolContext(
            field_name="refund_calculation_method",
            field_value="some-unknown-method",
            field_confidence=0.88,
            field_source="Page 3",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.WARNING
        assert "unknown refund method" in result.message.lower()

    @pytest.mark.asyncio
    async def test_refund_method_na(self, rule_validator):
        """Test that 'N/A' is recognized as valid."""
        context = ToolContext(
            field_name="refund_calculation_method",
            field_value="N/A",
            field_confidence=0.88,
            field_source="Page 3",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS

    @pytest.mark.asyncio
    async def test_refund_method_none(self, rule_validator):
        """Test that 'none' is recognized as valid."""
        context = ToolContext(
            field_name="refund_calculation_method",
            field_value="none",
            field_confidence=0.88,
            field_source="Page 3",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.PASS


class TestApplicableFields:
    """Test that validator only applies to relevant fields."""

    @pytest.mark.asyncio
    async def test_inapplicable_field_is_skipped(self, rule_validator):
        """Test that non-applicable fields are skipped."""
        context = ToolContext(
            field_name="some_other_field",
            field_value="some value",
            field_confidence=0.90,
            field_source="Page 4",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.status == ToolStatus.SKIPPED
        assert "no business rules defined" in result.message.lower()


class TestToolMetadata:
    """Test tool metadata and result format."""

    @pytest.mark.asyncio
    async def test_tool_name_in_result(self, rule_validator):
        """Test that tool name is included in result."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=Decimal("500.00"),
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.tool_name == "rule_validator"

    @pytest.mark.asyncio
    async def test_field_name_in_result(self, rule_validator):
        """Test that field name is preserved in result."""
        context = ToolContext(
            field_name="cancellation_fee",
            field_value=Decimal("50.00"),
            field_confidence=0.92,
            field_source="Page 2",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        assert result.field_name == "cancellation_fee"


class TestErrorHandling:
    """Test error handling for invalid input."""

    @pytest.mark.asyncio
    async def test_invalid_decimal_value(self, rule_validator):
        """Test handling of non-numeric value for numeric field."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value="not-a-number",
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        # Should handle gracefully, likely returning ERROR or FAIL
        assert result.status in [ToolStatus.ERROR, ToolStatus.FAIL]

    @pytest.mark.asyncio
    async def test_none_value(self, rule_validator):
        """Test handling of None value."""
        context = ToolContext(
            field_name="gap_insurance_premium",
            field_value=None,
            field_confidence=0.95,
            field_source="Page 1",
            all_fields={},
        )

        result = await rule_validator.execute(context)

        # Should handle gracefully
        assert result.status in [ToolStatus.ERROR, ToolStatus.FAIL, ToolStatus.SKIPPED]
