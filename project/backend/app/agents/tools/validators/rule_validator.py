"""
Rule Validator - Business logic validation.

Validates extracted values against known business rules and constraints.
"""

from decimal import Decimal

from app.agents.base import ToolContext, ToolResult, ToolStatus
from app.agents.tools.base import ValidationTool


class RuleValidator(ValidationTool):
    """
    Validates fields against business rules.

    Rules:
    - GAP Insurance Premium: $100-$2000 (warning if outside range)
    - Cancellation Fee: $0-$100 (warning if outside, fail if negative)
    - Refund Calculation Method: Known values only (warning if unknown)
    """

    # Known refund calculation methods
    KNOWN_REFUND_METHODS = {
        "pro-rata",
        "pro rata",
        "prorata",
        "rule of 78s",
        "rule of 78",
        "actuarial",
        "flat",
        "none",
        "n/a",
        "not applicable",
    }

    # Field-specific ranges
    GAP_PREMIUM_MIN = Decimal("100.00")
    GAP_PREMIUM_MAX = Decimal("2000.00")
    CANCELLATION_FEE_MIN = Decimal("0.00")
    CANCELLATION_FEE_MAX = Decimal("100.00")

    @property
    def name(self) -> str:
        return "rule_validator"

    @property
    def description(self) -> str:
        return "Validates fields against business rules and known constraints"

    async def validate(self, context: ToolContext) -> ToolResult:
        """
        Validate field against business rules.

        Args:
            context: Tool context with field data

        Returns:
            ToolResult with validation status
        """
        field_name = context.field_name
        field_value = context.field_value

        # Route to appropriate validator
        if field_name == "gap_insurance_premium":
            return self._validate_gap_premium(field_value, field_name)
        elif field_name == "cancellation_fee":
            return self._validate_cancellation_fee(field_value, field_name)
        elif field_name == "refund_calculation_method":
            return self._validate_refund_method(field_value, field_name)
        else:
            # Unknown field - skip
            return ToolResult(
                status=ToolStatus.SKIPPED,
                field_name=field_name,
                message=f"No business rules defined for {field_name}",
            )

    def _validate_gap_premium(self, value: str | Decimal, field_name: str) -> ToolResult:
        """
        Validate GAP Insurance Premium.

        Rule: $100-$2000 range (warning if outside)
        """
        try:
            amount = Decimal(str(value))
        except (ValueError, TypeError):
            return ToolResult(
                status=ToolStatus.FAIL,
                field_name=field_name,
                message=f"Invalid premium value: {value}",
            )

        if amount < self.GAP_PREMIUM_MIN or amount > self.GAP_PREMIUM_MAX:
            return ToolResult(
                status=ToolStatus.WARNING,
                field_name=field_name,
                message=f"Premium ${amount} is outside typical range ${self.GAP_PREMIUM_MIN}-${self.GAP_PREMIUM_MAX}",
                details={
                    "value": float(amount),
                    "min": float(self.GAP_PREMIUM_MIN),
                    "max": float(self.GAP_PREMIUM_MAX),
                },
            )

        return ToolResult(
            status=ToolStatus.PASS,
            field_name=field_name,
            message=f"Premium ${amount} is within expected range",
        )

    def _validate_cancellation_fee(self, value: str | Decimal, field_name: str) -> ToolResult:
        """
        Validate Cancellation Fee.

        Rules:
        - Must be >= $0 (fail if negative)
        - $0-$100 range (warning if above $100)
        """
        try:
            amount = Decimal(str(value))
        except (ValueError, TypeError):
            return ToolResult(
                status=ToolStatus.FAIL,
                field_name=field_name,
                message=f"Invalid fee value: {value}",
            )

        # Fail if negative
        if amount < self.CANCELLATION_FEE_MIN:
            return ToolResult(
                status=ToolStatus.FAIL,
                field_name=field_name,
                message=f"Cancellation fee cannot be negative: ${amount}",
                details={"value": float(amount)},
            )

        # Warning if above max
        if amount > self.CANCELLATION_FEE_MAX:
            return ToolResult(
                status=ToolStatus.WARNING,
                field_name=field_name,
                message=f"Fee ${amount} exceeds typical maximum ${self.CANCELLATION_FEE_MAX}",
                details={"value": float(amount), "max": float(self.CANCELLATION_FEE_MAX)},
            )

        return ToolResult(
            status=ToolStatus.PASS,
            field_name=field_name,
            message=f"Fee ${amount} is within expected range",
        )

    def _validate_refund_method(self, value: str | Decimal, field_name: str) -> ToolResult:
        """
        Validate Refund Calculation Method.

        Rule: Must be a known method (warning if unknown)
        """
        if not isinstance(value, str):
            return ToolResult(
                status=ToolStatus.FAIL,
                field_name=field_name,
                message=f"Refund method must be text, got: {type(value).__name__}",
            )

        normalized = value.lower().strip()

        if normalized not in self.KNOWN_REFUND_METHODS:
            return ToolResult(
                status=ToolStatus.WARNING,
                field_name=field_name,
                message=f"Unknown refund method: '{value}'. Expected one of: {', '.join(sorted(self.KNOWN_REFUND_METHODS))}",
                details={"value": value, "known_methods": sorted(self.KNOWN_REFUND_METHODS)},
            )

        return ToolResult(
            status=ToolStatus.PASS,
            field_name=field_name,
            message=f"Refund method '{value}' is recognized",
        )
