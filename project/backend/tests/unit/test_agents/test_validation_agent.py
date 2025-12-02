"""
Unit tests for ValidationAgent.

Tests the orchestration of validation tools and aggregation of results.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.validation_agent import ValidationAgent
from app.agents.base import AgentContext, ToolResult, ToolStatus


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def validation_agent(mock_db_session):
    """Create ValidationAgent instance with mocked dependencies."""
    return ValidationAgent(mock_db_session)


@pytest.fixture
def sample_agent_context():
    """Sample AgentContext for testing."""
    return AgentContext(
        contract_id="test-contract-123",
        extraction_id="test-extraction-456",
        extraction_data={
            "gap_insurance_premium": {
                "value": Decimal("500.00"),
                "confidence": 0.95,
                "source": "Page 1, Section 3",
            },
            "refund_calculation_method": {
                "value": "pro-rata",
                "confidence": 0.88,
                "source": "Page 2, Section 5",
            },
            "cancellation_fee": {
                "value": Decimal("50.00"),
                "confidence": 0.92,
                "source": "Page 3, Section 7",
            },
        },
        document_text="Sample contract text...",
    )


class TestValidationAgentOrchestration:
    """Test ValidationAgent orchestration of tools."""

    @pytest.mark.asyncio
    async def test_execute_runs_all_tools(self, validation_agent, sample_agent_context):
        """Test that execute() runs all validation tools for each field."""
        # Mock all tools to return PASS results
        with (
            patch.object(validation_agent.tools[0], "execute", new_callable=AsyncMock) as mock_rule,
            patch.object(
                validation_agent.tools[1], "execute", new_callable=AsyncMock
            ) as mock_historical,
            patch.object(
                validation_agent.tools[2], "execute", new_callable=AsyncMock
            ) as mock_consistency,
        ):

            # Setup mock returns
            mock_rule.return_value = ToolResult(
                status=ToolStatus.PASS,
                field_name="gap_insurance_premium",
                message="Valid premium amount",
                tool_name="RuleValidator",
            )
            mock_historical.return_value = ToolResult(
                status=ToolStatus.PASS,
                field_name="gap_insurance_premium",
                message="Within historical range",
                tool_name="HistoricalValidator",
            )
            mock_consistency.return_value = ToolResult(
                status=ToolStatus.PASS,
                field_name="gap_insurance_premium",
                message="Consistent with other fields",
                tool_name="ConsistencyValidator",
            )

            result = await validation_agent.execute(sample_agent_context)

            # Verify all tools were called (3 tools × 3 fields = 9 calls)
            assert mock_rule.call_count == 3
            assert mock_historical.call_count == 3
            assert mock_consistency.call_count == 3

    @pytest.mark.asyncio
    async def test_skipped_results_not_included(self, validation_agent, sample_agent_context):
        """Test that SKIPPED results are filtered out from field_results."""
        with patch.object(
            validation_agent.tools[0], "execute", new_callable=AsyncMock
        ) as mock_tool:
            # Return SKIPPED status
            mock_tool.return_value = ToolResult(
                status=ToolStatus.SKIPPED,
                field_name="gap_insurance_premium",
                message="Not applicable",
                tool_name="TestTool",
            )

            result = await validation_agent.execute(sample_agent_context)

            # SKIPPED results should not be in field_results
            assert len(result.field_results) == 0


class TestOverallStatusComputation:
    """Test overall status priority logic (fail > warning > pass)."""

    @pytest.mark.asyncio
    async def test_all_pass_returns_pass(self, validation_agent, sample_agent_context):
        """Test that all PASS results yield overall PASS status."""
        with (
            patch.object(
                validation_agent.tools[0], "execute", new_callable=AsyncMock
            ) as mock_tool1,
            patch.object(
                validation_agent.tools[1], "execute", new_callable=AsyncMock
            ) as mock_tool2,
            patch.object(
                validation_agent.tools[2], "execute", new_callable=AsyncMock
            ) as mock_tool3,
        ):
            # All tools return PASS
            mock_tool1.return_value = ToolResult(
                status=ToolStatus.PASS,
                field_name="gap_insurance_premium",
                message="Valid",
                tool_name="TestTool",
            )
            mock_tool2.return_value = ToolResult(
                status=ToolStatus.PASS,
                field_name="gap_insurance_premium",
                message="Valid",
                tool_name="TestTool",
            )
            mock_tool3.return_value = ToolResult(
                status=ToolStatus.PASS,
                field_name="gap_insurance_premium",
                message="Valid",
                tool_name="TestTool",
            )

            result = await validation_agent.execute(sample_agent_context)

            assert result.overall_status == "pass"

    @pytest.mark.asyncio
    async def test_one_warning_returns_warning(self, validation_agent, sample_agent_context):
        """Test that any WARNING result yields overall WARNING status."""
        with (
            patch.object(validation_agent.tools[0], "execute", new_callable=AsyncMock) as mock_rule,
            patch.object(
                validation_agent.tools[1], "execute", new_callable=AsyncMock
            ) as mock_historical,
            patch.object(
                validation_agent.tools[2], "execute", new_callable=AsyncMock
            ) as mock_consistency,
        ):

            # Most pass, one warning
            mock_rule.return_value = ToolResult(
                status=ToolStatus.PASS,
                field_name="gap_insurance_premium",
                message="Valid",
                tool_name="RuleValidator",
            )
            mock_historical.return_value = ToolResult(
                status=ToolStatus.WARNING,
                field_name="gap_insurance_premium",
                message="Statistical outlier",
                tool_name="HistoricalValidator",
            )
            mock_consistency.return_value = ToolResult(
                status=ToolStatus.PASS,
                field_name="gap_insurance_premium",
                message="Consistent",
                tool_name="ConsistencyValidator",
            )

            result = await validation_agent.execute(sample_agent_context)

            assert result.overall_status == "warning"

    @pytest.mark.asyncio
    async def test_one_fail_returns_fail(self, validation_agent, sample_agent_context):
        """Test that any FAIL result yields overall FAIL status (highest priority)."""
        with (
            patch.object(validation_agent.tools[0], "execute", new_callable=AsyncMock) as mock_rule,
            patch.object(
                validation_agent.tools[1], "execute", new_callable=AsyncMock
            ) as mock_historical,
            patch.object(
                validation_agent.tools[2], "execute", new_callable=AsyncMock
            ) as mock_consistency,
        ):

            # Mixed: pass, warning, fail
            mock_rule.return_value = ToolResult(
                status=ToolStatus.FAIL,
                field_name="gap_insurance_premium",
                message="Out of range",
                tool_name="RuleValidator",
            )
            mock_historical.return_value = ToolResult(
                status=ToolStatus.WARNING,
                field_name="gap_insurance_premium",
                message="Statistical outlier",
                tool_name="HistoricalValidator",
            )
            mock_consistency.return_value = ToolResult(
                status=ToolStatus.PASS,
                field_name="gap_insurance_premium",
                message="Consistent",
                tool_name="ConsistencyValidator",
            )

            result = await validation_agent.execute(sample_agent_context)

            # FAIL has highest priority
            assert result.overall_status == "fail"

    @pytest.mark.asyncio
    async def test_error_treated_as_fail(self, validation_agent, sample_agent_context):
        """Test that ERROR status is treated as FAIL."""
        with patch.object(
            validation_agent.tools[0], "execute", new_callable=AsyncMock
        ) as mock_tool:
            mock_tool.return_value = ToolResult(
                status=ToolStatus.ERROR,
                field_name="gap_insurance_premium",
                message="Tool execution error",
                tool_name="TestTool",
            )

            result = await validation_agent.execute(sample_agent_context)

            assert result.overall_status == "fail"


class TestSummaryGeneration:
    """Test summary generation based on validation results."""

    @pytest.mark.asyncio
    async def test_summary_for_pass(self, validation_agent, sample_agent_context):
        """Test summary message when all validations pass."""
        with patch.object(
            validation_agent.tools[0], "execute", new_callable=AsyncMock
        ) as mock_tool:
            mock_tool.return_value = ToolResult(
                status=ToolStatus.PASS,
                field_name="gap_insurance_premium",
                message="Valid",
                tool_name="TestTool",
            )

            result = await validation_agent.execute(sample_agent_context)

            assert "All validations passed" in result.summary

    @pytest.mark.asyncio
    async def test_summary_for_warning(self, validation_agent, sample_agent_context):
        """Test summary message when warnings are present."""
        with patch.object(
            validation_agent.tools[0], "execute", new_callable=AsyncMock
        ) as mock_tool:
            mock_tool.return_value = ToolResult(
                status=ToolStatus.WARNING,
                field_name="gap_insurance_premium",
                message="Statistical outlier",
                tool_name="TestTool",
            )

            result = await validation_agent.execute(sample_agent_context)

            assert "with warnings" in result.summary.lower()

    @pytest.mark.asyncio
    async def test_summary_for_fail(self, validation_agent, sample_agent_context):
        """Test summary message when validation fails."""
        with patch.object(
            validation_agent.tools[0], "execute", new_callable=AsyncMock
        ) as mock_tool:
            mock_tool.return_value = ToolResult(
                status=ToolStatus.FAIL,
                field_name="gap_insurance_premium",
                message="Out of range",
                tool_name="TestTool",
            )

            result = await validation_agent.execute(sample_agent_context)

            assert "failed" in result.summary.lower() or "fail" in result.summary.lower()

    @pytest.mark.asyncio
    async def test_summary_includes_field_count(self, validation_agent, sample_agent_context):
        """Test that summary includes count of validated fields."""
        with patch.object(
            validation_agent.tools[0], "execute", new_callable=AsyncMock
        ) as mock_tool:
            mock_tool.return_value = ToolResult(
                status=ToolStatus.PASS,
                field_name="gap_insurance_premium",
                message="Valid",
                tool_name="TestTool",
            )

            result = await validation_agent.execute(sample_agent_context)

            # Should mention 3 fields
            assert "3" in result.summary or "three" in result.summary.lower()


class TestAgentResultFormat:
    """Test AgentResult structure and data format."""

    @pytest.mark.asyncio
    async def test_result_has_required_fields(self, validation_agent, sample_agent_context):
        """Test that AgentResult contains all required fields."""
        with patch.object(
            validation_agent.tools[0], "execute", new_callable=AsyncMock
        ) as mock_tool:
            mock_tool.return_value = ToolResult(
                status=ToolStatus.PASS,
                field_name="gap_insurance_premium",
                message="Valid",
                tool_name="TestTool",
            )

            result = await validation_agent.execute(sample_agent_context)

            assert hasattr(result, "overall_status")
            assert hasattr(result, "field_results")
            assert hasattr(result, "summary")
            assert isinstance(result.field_results, list)
            assert isinstance(result.summary, str)

    @pytest.mark.asyncio
    async def test_field_results_are_dicts(self, validation_agent, sample_agent_context):
        """Test that field_results are converted to dictionaries."""
        with patch.object(
            validation_agent.tools[0], "execute", new_callable=AsyncMock
        ) as mock_tool:
            mock_tool.return_value = ToolResult(
                status=ToolStatus.PASS,
                field_name="gap_insurance_premium",
                message="Valid",
                tool_name="TestTool",
            )

            result = await validation_agent.execute(sample_agent_context)

            assert len(result.field_results) > 0
            for field_result in result.field_results:
                assert isinstance(field_result, dict)
                assert "field_name" in field_result
                assert "status" in field_result
                assert "message" in field_result
                assert "tool_name" in field_result
