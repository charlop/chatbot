"""
Consistency Validator - Cross-field validation.

Validates consistency across multiple fields in the extraction.
"""

from decimal import Decimal

from app.agents.base import ToolContext, ToolResult, ToolStatus
from app.agents.tools.base import ValidationTool


class ConsistencyValidator(ValidationTool):
    """
    Validates consistency across fields.

    Checks:
    - Cancellation fee must not exceed GAP insurance premium
    - Confidence scores are reasonable (not all 100% or suspiciously low)
    """

    @property
    def name(self) -> str:
        return "consistency_validator"

    @property
    def description(self) -> str:
        return "Validates consistency across multiple fields"

    async def validate(self, context: ToolContext) -> ToolResult:
        """
        Validate field consistency with other fields.

        Args:
            context: Tool context with field data and all_fields

        Returns:
            ToolResult with validation status
        """
        field_name = context.field_name
        field_value = context.field_value
        all_fields = context.all_fields

        # Skip if we don't have all_fields (can't do cross-field validation)
        if not all_fields:
            return ToolResult(
                status=ToolStatus.SKIPPED,
                field_name=field_name,
                message="Cannot perform consistency check without all field data",
            )

        # Validate cancellation fee vs premium
        if field_name == "cancellation_fee":
            return self._validate_fee_vs_premium(field_value, all_fields)

        # Validate confidence scores
        if field_name in ["gap_insurance_premium", "refund_calculation_method", "cancellation_fee"]:
            return self._validate_confidence_score(field_name, context.field_confidence, all_fields)

        # No consistency checks for other fields
        return ToolResult(
            status=ToolStatus.SKIPPED,
            field_name=field_name,
            message=f"No consistency checks defined for {field_name}",
        )

    def _validate_fee_vs_premium(self, fee_value: str | Decimal, all_fields: dict) -> ToolResult:
        """
        Validate that cancellation fee does not exceed GAP premium.

        Args:
            fee_value: Cancellation fee value
            all_fields: All extracted fields

        Returns:
            ToolResult with validation status
        """
        field_name = "cancellation_fee"

        # Get premium value
        premium_data = all_fields.get("gap_insurance_premium", {})
        premium_value = (
            premium_data.get("value") if isinstance(premium_data, dict) else premium_data
        )

        # Skip if premium is missing
        if premium_value is None:
            return ToolResult(
                status=ToolStatus.SKIPPED,
                field_name=field_name,
                message="Cannot validate fee vs premium: premium value is missing",
            )

        try:
            fee = Decimal(str(fee_value))
            premium = Decimal(str(premium_value))
        except (ValueError, TypeError):
            return ToolResult(
                status=ToolStatus.SKIPPED,
                field_name=field_name,
                message=f"Cannot compare non-numeric values: fee={fee_value}, premium={premium_value}",
            )

        # Check if fee exceeds premium
        if fee > premium:
            return ToolResult(
                status=ToolStatus.WARNING,
                field_name=field_name,
                message=f"Cancellation fee (${fee}) exceeds GAP premium (${premium})",
                details={"fee": float(fee), "premium": float(premium)},
            )

        return ToolResult(
            status=ToolStatus.PASS,
            field_name=field_name,
            message=f"Fee (${fee}) is less than premium (${premium})",
            details={"fee": float(fee), "premium": float(premium)},
        )

    def _validate_confidence_score(
        self, field_name: str, confidence: Decimal | None, all_fields: dict
    ) -> ToolResult:
        """
        Validate that confidence scores are reasonable.

        Flags if:
        - All confidence scores are 100% (suspiciously high)
        - All confidence scores are < 50% (suspiciously low)

        Args:
            field_name: Name of the field being validated
            confidence: Confidence score for this field
            all_fields: All extracted fields with confidence scores

        Returns:
            ToolResult with validation status
        """
        if confidence is None:
            return ToolResult(
                status=ToolStatus.SKIPPED,
                field_name=field_name,
                message="No confidence score to validate",
            )

        # Collect all confidence scores
        confidence_scores = []
        for fname in ["gap_insurance_premium", "refund_calculation_method", "cancellation_fee"]:
            field_data = all_fields.get(fname, {})
            if isinstance(field_data, dict):
                score = field_data.get("confidence")
                if score is not None:
                    confidence_scores.append(Decimal(str(score)))

        # Need at least 2 scores for meaningful comparison
        if len(confidence_scores) < 2:
            return ToolResult(
                status=ToolStatus.PASS,
                field_name=field_name,
                message="Confidence score is reasonable",
            )

        # Check if all scores are 100% (suspiciously high)
        if all(score == Decimal("100") for score in confidence_scores):
            return ToolResult(
                status=ToolStatus.WARNING,
                field_name=field_name,
                message="All confidence scores are 100% - unusually high confidence across all fields",
                details={"scores": [float(s) for s in confidence_scores]},
            )

        # Check if all scores are < 50% (suspiciously low)
        if all(score < Decimal("50") for score in confidence_scores):
            return ToolResult(
                status=ToolStatus.WARNING,
                field_name=field_name,
                message="All confidence scores are below 50% - unusually low confidence across all fields",
                details={"scores": [float(s) for s in confidence_scores]},
            )

        return ToolResult(
            status=ToolStatus.PASS,
            field_name=field_name,
            message="Confidence scores are reasonable across fields",
            details={"scores": [float(s) for s in confidence_scores]},
        )
