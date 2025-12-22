"""
Validation Agent - Orchestrates validation tools on extracted data.

The ValidationAgent runs multiple validation tools on each extracted field
and aggregates the results to produce an overall validation status.

UPDATED: Now uses StateAwareRuleValidator instead of hardcoded RuleValidator.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import Agent, AgentContext, AgentResult, ToolContext
from app.agents.tools.validators import (
    StateAwareRuleValidator,
    HistoricalValidator,
    ConsistencyValidator,
)


class ValidationAgent(Agent):
    """
    Orchestrates validation tools on extracted contract data.

    The agent:
    1. Iterates through each extracted field
    2. Runs applicable validation tools on each field
    3. Collects all validation results
    4. Computes overall status (fail > warning > pass)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the validation agent.

        Args:
            db: Database session for tools that need historical data and state rules
        """
        self.db = db
        self.tools = [
            StateAwareRuleValidator(db),  # CHANGED: Now requires db, replaces RuleValidator
            HistoricalValidator(db),
            ConsistencyValidator(),
        ]

    @property
    def name(self) -> str:
        return "validation_agent"

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute validation workflow on all extracted fields.

        Args:
            context: Agent context with extraction data

        Returns:
            AgentResult with overall status and field results
        """
        field_results = []

        # Fields to validate
        fields = [
            "gap_insurance_premium",
            "refund_calculation_method",
            "cancellation_fee",
        ]

        # Run validation tools on each field
        for field_name in fields:
            # Get field data from extraction
            field_data = context.extraction_data.get(field_name, {})

            # Extract field components (handle both dict and direct value)
            if isinstance(field_data, dict):
                field_value = field_data.get("value")
                field_confidence = field_data.get("confidence")
                field_source = field_data.get("source")
            else:
                # Fallback for non-dict data
                field_value = field_data
                field_confidence = None
                field_source = None

            # Create tool context
            tool_context = ToolContext(
                field_name=field_name,
                field_value=field_value,
                field_confidence=field_confidence,
                field_source=field_source,
                all_fields=context.extraction_data,
                document_text=context.document_text,
                contract_id=context.contract_id,
                extraction_id=context.extraction_id,
            )

            # Run each tool on this field
            for tool in self.tools:
                result = await tool.execute(tool_context)

                # Only collect non-skipped results
                if result.status.value != "skipped":
                    field_results.append(result.to_dict())

        # Compute overall status
        overall_status = self._compute_overall_status(field_results)

        return AgentResult(
            overall_status=overall_status,
            field_results=field_results,
            summary=self._generate_summary(overall_status, field_results),
        )

    def _generate_summary(self, overall_status: str, field_results: list[dict]) -> str:
        """
        Generate human-readable summary of validation results.

        Args:
            overall_status: Overall validation status
            field_results: List of field validation results

        Returns:
            Human-readable summary string
        """
        total_checks = len(field_results)

        # Count by status
        pass_count = sum(1 for r in field_results if r.get("status") == "pass")
        warning_count = sum(1 for r in field_results if r.get("status") == "warning")
        fail_count = sum(1 for r in field_results if r.get("status") == "fail")
        error_count = sum(1 for r in field_results if r.get("status") == "error")

        if overall_status == "fail":
            return f"Validation failed: {fail_count} failure(s), {warning_count} warning(s) out of {total_checks} checks"
        elif overall_status == "warning":
            return f"Validation passed with warnings: {warning_count} warning(s) out of {total_checks} checks"
        else:
            return f"Validation passed: {pass_count} check(s) passed successfully"
