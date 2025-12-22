"""
State-aware rule validator using database rules.
"""

from decimal import Decimal
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import ToolContext, ToolResult, ToolStatus
from app.agents.tools.base import ValidationTool
from app.repositories.state_rule_repository import StateRuleRepository
from app.models.database.contract_jurisdiction import ContractJurisdiction
from app.models.database.state_validation_rule import StateValidationRule


class StateAwareRuleValidator(ValidationTool):
    """
    Validates fields against state-specific rules from database.

    Replaces hardcoded RuleValidator with database-driven approach.

    Features:
    - Queries state rules from database
    - Handles multi-state contracts (primary + conflict detection)
    - Applies numeric range validation (GAP, cancellation fee)
    - Applies value list validation (refund methods)
    - Returns state-specific context in results
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize validator with database session.

        Args:
            db: Database session for querying rules
        """
        self.db = db
        self.rule_repo = StateRuleRepository(db)

        # Map extraction field names to database rule categories
        self.field_to_category_map = {
            "gap_insurance_premium": "gap_premium",
            "refund_calculation_method": "refund_method",
            "cancellation_fee": "cancellation_fee",
        }

    @property
    def name(self) -> str:
        return "state_aware_rule_validator"

    @property
    def description(self) -> str:
        return "Validates fields against state-specific business rules from database"

    async def execute(self, context: ToolContext) -> ToolResult:
        """
        Execute state-aware validation on a field.

        Args:
            context: Tool context with field data and contract ID

        Returns:
            ToolResult with validation status and state context
        """
        # Get jurisdictions for this contract
        jurisdictions = await self.rule_repo.get_jurisdictions_for_contract(context.contract_id)

        if not jurisdictions:
            # No jurisdictions found - fall back to federal default
            return await self._validate_with_default_rules(context)

        # Handle multi-state: use primary jurisdiction
        primary_jurisdiction = self._get_primary_jurisdiction(jurisdictions)

        # Map field name to rule category
        rule_category = self.field_to_category_map.get(context.field_name, context.field_name)

        # Get state-specific rule for this field
        rule = await self.rule_repo.get_active_rules_for_jurisdiction(
            jurisdiction_id=primary_jurisdiction.jurisdiction_id,
            rule_category=rule_category,
        )

        if not rule:
            # No rule found for this state/field - try federal default
            rule = await self.rule_repo.get_active_rules_for_jurisdiction(
                jurisdiction_id="US-FEDERAL", rule_category=rule_category
            )

        if not rule:
            # No rules at all - skip validation
            return ToolResult(
                status=ToolStatus.SKIPPED,
                field_name=context.field_name,
                message="No validation rules configured",
                tool_name=self.name,
            )

        # Apply rule configuration
        result = await self._apply_rule_config(context, rule, primary_jurisdiction)

        # Check other jurisdictions for conflicts (multi-state)
        if len(jurisdictions) > 1:
            conflicts = await self._check_multi_state_conflicts(
                context, jurisdictions, primary_jurisdiction, result
            )
            if conflicts:
                # Initialize details dict if needed
                if not hasattr(result, "details") or result.details is None:
                    result.details = {}
                result.details["multi_state_conflicts"] = conflicts
                # Upgrade to warning if there are conflicts
                if result.status == ToolStatus.PASS:
                    result.status = ToolStatus.WARNING
                    result.message += " (conflicts with other states)"

        return result

    def _get_primary_jurisdiction(
        self, jurisdictions: List[ContractJurisdiction]
    ) -> ContractJurisdiction:
        """
        Get primary jurisdiction from list.

        Args:
            jurisdictions: List of contract jurisdictions

        Returns:
            Primary jurisdiction (or first if none marked primary)
        """
        primary = next((j for j in jurisdictions if j.is_primary), None)
        return primary or jurisdictions[0]

    async def _apply_rule_config(
        self,
        context: ToolContext,
        rule: StateValidationRule,
        jurisdiction: ContractJurisdiction,
    ) -> ToolResult:
        """
        Apply validation based on JSONB rule configuration.

        Args:
            context: Tool context with field data
            rule: State validation rule
            jurisdiction: Jurisdiction being validated against

        Returns:
            ToolResult with validation outcome
        """
        config = rule.rule_config
        field_value = context.field_value
        field_name = context.field_name

        # Numeric range validation (GAP premium, cancellation fee)
        if "min" in config or "max" in config:
            return await self._validate_numeric_range(field_name, field_value, config, jurisdiction)

        # Allowed/prohibited values validation (refund methods)
        if "allowed_values" in config or "prohibited_values" in config:
            return await self._validate_value_list(field_name, field_value, config, jurisdiction)

        # Unknown rule type - skip
        return ToolResult(
            status=ToolStatus.SKIPPED,
            field_name=field_name,
            message=f"Unknown rule configuration for {jurisdiction.jurisdiction_id}",
            tool_name=self.name,
        )

    async def _validate_numeric_range(
        self,
        field_name: str,
        field_value: any,
        config: dict,
        jurisdiction: ContractJurisdiction,
    ) -> ToolResult:
        """
        Validate numeric field against min/max range.

        Args:
            field_name: Field being validated
            field_value: Value to validate
            config: Rule configuration with min/max
            jurisdiction: Jurisdiction whose rules are being applied

        Returns:
            ToolResult with pass/warning/fail status
        """
        try:
            value = Decimal(str(field_value)) if field_value is not None else None
            if value is None:
                return ToolResult(
                    status=ToolStatus.SKIPPED,
                    field_name=field_name,
                    message="No value to validate",
                    tool_name=self.name,
                )

            min_val = Decimal(str(config.get("min", 0)))
            max_val = Decimal(str(config.get("max", float("inf"))))
            strict = config.get("strict", False)
            warning_threshold = config.get("warning_threshold")
            reason = config.get("reason", "")

            # Check range
            if value < min_val or value > max_val:
                status = ToolStatus.FAIL if strict else ToolStatus.WARNING
                message = f"{jurisdiction.jurisdiction_id}: Value ${value} outside range ${min_val}-${max_val}"
                if reason:
                    message += f" ({reason})"

                return ToolResult(
                    status=status,
                    field_name=field_name,
                    message=message,
                    tool_name=self.name,
                    details={
                        "jurisdiction": jurisdiction.jurisdiction_id,
                        "value": float(value),
                        "min": float(min_val),
                        "max": float(max_val),
                        "reason": reason,
                    },
                )

            # Check warning threshold
            if warning_threshold and value > Decimal(str(warning_threshold)):
                return ToolResult(
                    status=ToolStatus.WARNING,
                    field_name=field_name,
                    message=f"{jurisdiction.jurisdiction_id}: Value ${value} exceeds recommended threshold ${warning_threshold}",
                    tool_name=self.name,
                    details={
                        "jurisdiction": jurisdiction.jurisdiction_id,
                        "value": float(value),
                        "warning_threshold": float(warning_threshold),
                    },
                )

            # Pass
            return ToolResult(
                status=ToolStatus.PASS,
                field_name=field_name,
                message=f"Complies with {jurisdiction.jurisdiction_id} rules (${min_val}-${max_val})",
                tool_name=self.name,
                details={
                    "jurisdiction": jurisdiction.jurisdiction_id,
                    "value": float(value),
                    "min": float(min_val),
                    "max": float(max_val),
                },
            )

        except (ValueError, TypeError) as e:
            return ToolResult(
                status=ToolStatus.FAIL,
                field_name=field_name,
                message=f"Invalid numeric value for {jurisdiction.jurisdiction_id}: {str(e)}",
                tool_name=self.name,
            )

    async def _validate_value_list(
        self,
        field_name: str,
        field_value: any,
        config: dict,
        jurisdiction: ContractJurisdiction,
    ) -> ToolResult:
        """
        Validate field against allowed/prohibited value lists.

        Args:
            field_name: Field being validated
            field_value: Value to validate
            config: Rule configuration with allowed_values/prohibited_values
            jurisdiction: Jurisdiction whose rules are being applied

        Returns:
            ToolResult with pass/warning/fail status
        """
        if field_value is None:
            return ToolResult(
                status=ToolStatus.SKIPPED,
                field_name=field_name,
                message="No value to validate",
                tool_name=self.name,
            )

        normalized = str(field_value).lower().strip()
        strict = config.get("strict", False)
        reason = config.get("reason", "")

        # Check prohibited values first
        prohibited = config.get("prohibited_values", [])
        if prohibited:
            prohibited_normalized = [v.lower() for v in prohibited]
            if normalized in prohibited_normalized:
                status = ToolStatus.FAIL if strict else ToolStatus.WARNING
                message = f"{jurisdiction.jurisdiction_id}: Value '{field_value}' is prohibited"
                if reason:
                    message += f" ({reason})"

                return ToolResult(
                    status=status,
                    field_name=field_name,
                    message=message,
                    tool_name=self.name,
                    details={
                        "jurisdiction": jurisdiction.jurisdiction_id,
                        "value": field_value,
                        "prohibited_values": prohibited,
                        "reason": reason,
                    },
                )

        # Check allowed values
        allowed = config.get("allowed_values", [])
        if allowed:
            allowed_normalized = [v.lower() for v in allowed]
            if normalized not in allowed_normalized:
                status = ToolStatus.FAIL if strict else ToolStatus.WARNING
                message = f"{jurisdiction.jurisdiction_id}: Value '{field_value}' not in allowed list: {', '.join(allowed)}"
                if reason:
                    message += f" ({reason})"

                return ToolResult(
                    status=status,
                    field_name=field_name,
                    message=message,
                    tool_name=self.name,
                    details={
                        "jurisdiction": jurisdiction.jurisdiction_id,
                        "value": field_value,
                        "allowed_values": allowed,
                        "reason": reason,
                    },
                )

        # Pass
        return ToolResult(
            status=ToolStatus.PASS,
            field_name=field_name,
            message=f"Complies with {jurisdiction.jurisdiction_id} rules",
            tool_name=self.name,
            details={
                "jurisdiction": jurisdiction.jurisdiction_id,
                "value": field_value,
                "allowed_values": allowed,
                "prohibited_values": prohibited,
            },
        )

    async def _check_multi_state_conflicts(
        self,
        context: ToolContext,
        jurisdictions: List[ContractJurisdiction],
        primary: ContractJurisdiction,
        primary_result: ToolResult,
    ) -> List[dict]:
        """
        Check other jurisdictions for conflicts with primary validation.

        Args:
            context: Tool context
            jurisdictions: All jurisdictions for contract
            primary: Primary jurisdiction
            primary_result: Validation result from primary jurisdiction

        Returns:
            List of conflict dictionaries
        """
        conflicts = []

        for jurisdiction in jurisdictions:
            if jurisdiction.jurisdiction_id == primary.jurisdiction_id:
                continue

            # Get rule for this jurisdiction
            rule = await self.rule_repo.get_active_rules_for_jurisdiction(
                jurisdiction_id=jurisdiction.jurisdiction_id,
                rule_category=context.field_name,
            )

            if not rule:
                continue

            # Apply rule and check if result differs from primary
            secondary_result = await self._apply_rule_config(context, rule, jurisdiction)

            # If secondary fails/warns but primary passes, it's a conflict
            if primary_result.status == ToolStatus.PASS and secondary_result.status in [
                ToolStatus.FAIL,
                ToolStatus.WARNING,
            ]:
                conflicts.append(
                    {
                        "jurisdiction": jurisdiction.jurisdiction_id,
                        "field": context.field_name,
                        "conflict": secondary_result.message,
                    }
                )

        return conflicts

    async def _validate_with_default_rules(self, context: ToolContext) -> ToolResult:
        """
        Fallback to federal default rules if no jurisdiction found.

        Args:
            context: Tool context

        Returns:
            ToolResult using federal default rules
        """
        # Map field name to rule category
        rule_category = self.field_to_category_map.get(context.field_name, context.field_name)

        rule = await self.rule_repo.get_active_rules_for_jurisdiction(
            jurisdiction_id="US-FEDERAL", rule_category=rule_category
        )

        if not rule:
            return ToolResult(
                status=ToolStatus.SKIPPED,
                field_name=context.field_name,
                message="No validation rules configured",
                tool_name=self.name,
            )

        # Create mock jurisdiction for federal
        federal_jurisdiction = ContractJurisdiction(
            contract_id=context.contract_id,
            jurisdiction_id="US-FEDERAL",
            is_primary=True,
        )

        return await self._apply_rule_config(context, rule, federal_jurisdiction)

    async def validate(self, context: ToolContext) -> ToolResult:
        """
        Validate method (not used - execute overrides base behavior).

        This method is required by ValidationTool base class but not used
        because we override execute() to handle jurisdictions before validation.
        """
        # This should never be called since we override execute()
        return ToolResult(
            status=ToolStatus.SKIPPED,
            field_name=context.field_name,
            message="Direct validate() call not supported",
            tool_name=self.name,
        )
