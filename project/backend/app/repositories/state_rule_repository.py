"""
Repository for state validation rules with effective date queries.
"""

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from app.models.database.jurisdiction import Jurisdiction
from app.models.database.contract_jurisdiction import ContractJurisdiction
from app.models.database.state_validation_rule import StateValidationRule


class StateRuleRepository:
    """
    Repository for querying state validation rules and jurisdictions.

    Handles:
    - Effective date queries (versioning)
    - Jurisdiction lookups
    - Rule creation and updates
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_rules_for_jurisdiction(
        self,
        jurisdiction_id: str,
        rule_category: str,
        effective_date: Optional[date] = None,
    ) -> Optional[StateValidationRule]:
        """
        Get active rule for jurisdiction and category at specific date.

        Args:
            jurisdiction_id: Jurisdiction ID (e.g., "US-CA")
            rule_category: Rule category (gap_premium, cancellation_fee, refund_method)
            effective_date: Date to check (defaults to today)

        Returns:
            StateValidationRule if found, None otherwise

        Example:
            rule = await repo.get_active_rules_for_jurisdiction("US-CA", "gap_premium")
            if rule:
                min_val = rule.rule_config.get("min")
                max_val = rule.rule_config.get("max")
        """
        if effective_date is None:
            effective_date = date.today()

        stmt = (
            select(StateValidationRule)
            .where(
                and_(
                    StateValidationRule.jurisdiction_id == jurisdiction_id,
                    StateValidationRule.rule_category == rule_category,
                    StateValidationRule.is_active == True,
                    StateValidationRule.effective_date <= effective_date,
                    or_(
                        StateValidationRule.expiration_date.is_(None),
                        StateValidationRule.expiration_date > effective_date,
                    ),
                )
            )
            .order_by(StateValidationRule.effective_date.desc())
            .limit(1)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_jurisdictions_for_contract(
        self, contract_id: str, as_of_date: Optional[date] = None
    ) -> List[ContractJurisdiction]:
        """
        Get all jurisdictions for a contract at specific date.

        Args:
            contract_id: Contract ID
            as_of_date: Date to check (defaults to today)

        Returns:
            List of ContractJurisdiction mappings, ordered by is_primary DESC

        Example:
            jurisdictions = await repo.get_jurisdictions_for_contract("GAP-2024-001")
            if jurisdictions:
                primary = jurisdictions[0]  # First is primary due to ordering
                print(f"Primary: {primary.jurisdiction_id}")
        """
        if as_of_date is None:
            as_of_date = date.today()

        stmt = (
            select(ContractJurisdiction)
            .where(
                and_(
                    ContractJurisdiction.contract_id == contract_id,
                    or_(
                        ContractJurisdiction.effective_date.is_(None),
                        ContractJurisdiction.effective_date <= as_of_date,
                    ),
                    or_(
                        ContractJurisdiction.expiration_date.is_(None),
                        ContractJurisdiction.expiration_date > as_of_date,
                    ),
                )
            )
            .order_by(ContractJurisdiction.is_primary.desc())
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_jurisdictions(self, active_only: bool = True) -> List[Jurisdiction]:
        """
        Get all jurisdictions.

        Args:
            active_only: If True, only return active jurisdictions

        Returns:
            List of Jurisdiction objects ordered by name
        """
        stmt = select(Jurisdiction)
        if active_only:
            stmt = stmt.where(Jurisdiction.is_active == True)
        stmt = stmt.order_by(Jurisdiction.jurisdiction_name)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_jurisdiction_by_state_code(self, state_code: str) -> Optional[Jurisdiction]:
        """
        Get jurisdiction by state code.

        Args:
            state_code: Two-letter state code (e.g., "CA", "NY")

        Returns:
            Jurisdiction if found, None otherwise
        """
        stmt = select(Jurisdiction).where(
            and_(Jurisdiction.state_code == state_code, Jurisdiction.is_active == True)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_rule(
        self,
        jurisdiction_id: str,
        rule_category: str,
        rule_config: dict,
        effective_date: date,
        rule_description: str | None = None,
        created_by: UUID | None = None,
    ) -> StateValidationRule:
        """
        Create new state validation rule.

        Args:
            jurisdiction_id: Jurisdiction ID
            rule_category: Rule category
            rule_config: JSONB rule configuration
            effective_date: When rule becomes active
            rule_description: Optional description
            created_by: Optional user ID who created the rule

        Returns:
            Created StateValidationRule
        """
        rule = StateValidationRule(
            jurisdiction_id=jurisdiction_id,
            rule_category=rule_category,
            rule_config=rule_config,
            effective_date=effective_date,
            rule_description=rule_description,
            created_by=created_by,
            is_active=True,
        )

        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)

        return rule

    async def update_rule(
        self,
        old_rule_id: UUID,
        new_rule_config: dict,
        new_effective_date: date,
        rule_description: str | None = None,
        created_by: UUID | None = None,
    ) -> StateValidationRule:
        """
        Update rule by creating new version and expiring old one.

        This maintains audit trail by keeping old rule with expiration date.

        Args:
            old_rule_id: ID of rule to update
            new_rule_config: New rule configuration
            new_effective_date: When new rule becomes active
            rule_description: Optional description
            created_by: Optional user ID who updated the rule

        Returns:
            New StateValidationRule version
        """
        # Get old rule
        old_rule = await self.db.get(StateValidationRule, old_rule_id)
        if not old_rule:
            raise ValueError(f"Rule {old_rule_id} not found")

        # Expire old rule (day before new rule effective)
        old_rule.expiration_date = new_effective_date
        old_rule.is_active = False

        # Create new rule version
        new_rule = StateValidationRule(
            jurisdiction_id=old_rule.jurisdiction_id,
            rule_category=old_rule.rule_category,
            rule_config=new_rule_config,
            effective_date=new_effective_date,
            rule_description=rule_description or old_rule.rule_description,
            created_by=created_by,
            is_active=True,
        )

        self.db.add(new_rule)
        await self.db.commit()
        await self.db.refresh(new_rule)

        return new_rule

    async def create_contract_jurisdiction_mapping(
        self,
        contract_id: str,
        jurisdiction_id: str,
        is_primary: bool = False,
        effective_date: Optional[date] = None,
    ) -> ContractJurisdiction:
        """
        Create contract-jurisdiction mapping.

        Args:
            contract_id: Contract ID
            jurisdiction_id: Jurisdiction ID
            is_primary: Whether this is the primary jurisdiction
            effective_date: When mapping becomes effective (defaults to today)

        Returns:
            Created ContractJurisdiction
        """
        if effective_date is None:
            effective_date = date.today()

        mapping = ContractJurisdiction(
            contract_id=contract_id,
            jurisdiction_id=jurisdiction_id,
            is_primary=is_primary,
            effective_date=effective_date,
        )

        self.db.add(mapping)
        await self.db.flush()  # Flush instead of commit for transaction compatibility

        return mapping
