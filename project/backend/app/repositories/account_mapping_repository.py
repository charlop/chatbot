"""
Account Mapping repository for account-template mapping database operations.
"""

from datetime import datetime, timedelta, UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.database.account_mapping import AccountTemplateMapping


class AccountMappingRepository(BaseRepository[AccountTemplateMapping]):
    """
    Repository for AccountTemplateMapping model.

    Manages account number to template ID mappings, including cache operations.
    Inherits generic CRUD operations from BaseRepository.
    MULTI-POLICY SUPPORT: One account can have multiple policies.
    """

    def __init__(self, session: AsyncSession):
        """Initialize account mapping repository."""
        super().__init__(AccountTemplateMapping, session)

    async def get_by_account_number(self, account_number: str) -> list[AccountTemplateMapping]:
        """
        Retrieve ALL policy mappings for an account number.

        Args:
            account_number: The account number to search for

        Returns:
            List of AccountTemplateMapping (empty list if none found)
        """
        stmt = (
            select(AccountTemplateMapping)
            .where(AccountTemplateMapping.account_number == account_number)
            .order_by(AccountTemplateMapping.policy_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_account_and_policy(
        self, account_number: str, policy_id: str
    ) -> AccountTemplateMapping | None:
        """
        Retrieve a specific policy mapping.

        Args:
            account_number: The account number
            policy_id: The policy identifier

        Returns:
            AccountTemplateMapping if found, None otherwise
        """
        stmt = select(AccountTemplateMapping).where(
            AccountTemplateMapping.account_number == account_number,
            AccountTemplateMapping.policy_id == policy_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update_mapping(
        self, account_number: str, policy_id: str, template_id: str, source: str = "external_api"
    ) -> AccountTemplateMapping:
        """
        Create a new policy mapping or update existing one (upsert).

        Args:
            account_number: The account number
            policy_id: The policy identifier
            template_id: The contract template ID
            source: Source of mapping (external_api, manual, migrated)

        Returns:
            Created or updated AccountTemplateMapping
        """
        existing = await self.get_by_account_and_policy(account_number, policy_id)

        if existing:
            # Update existing mapping
            existing.contract_template_id = template_id
            existing.source = source
            existing.cached_at = datetime.now(UTC)
            existing.updated_at = datetime.now(UTC)

            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            # Create new mapping
            mapping = AccountTemplateMapping(
                account_number=account_number,
                policy_id=policy_id,
                contract_template_id=template_id,
                source=source,
            )
            return await self.create(mapping)

    async def upsert_policies(
        self, account_number: str, policies: list[tuple[str, str]], source: str = "external_api"
    ) -> list[AccountTemplateMapping]:
        """
        Create or update multiple policy mappings for an account (bulk upsert).

        Args:
            account_number: The account number
            policies: List of (policy_id, template_id) tuples
            source: Source of mappings (external_api, manual, migrated)

        Returns:
            List of created/updated mappings
        """
        mappings = []
        for policy_id, template_id in policies:
            mapping = await self.create_or_update_mapping(
                account_number=account_number,
                policy_id=policy_id,
                template_id=template_id,
                source=source,
            )
            mappings.append(mapping)

        return mappings

    async def is_cache_fresh(
        self, mapping: AccountTemplateMapping, ttl_seconds: int = 3600
    ) -> bool:
        """
        Check if cached mapping is still fresh based on TTL.

        Args:
            mapping: The account mapping to check
            ttl_seconds: Time-to-live in seconds (default: 3600 = 1 hour)

        Returns:
            True if cache is fresh, False if stale
        """
        if not mapping or not mapping.cached_at:
            return False

        # Calculate cache age
        now = datetime.now(UTC)
        cache_age = (now - mapping.cached_at).total_seconds()

        return cache_age < ttl_seconds

    async def are_all_caches_fresh(
        self, mappings: list[AccountTemplateMapping], ttl_seconds: int = 3600
    ) -> bool:
        """
        Check if ALL cached policy mappings are still fresh.

        Args:
            mappings: List of account mappings to check
            ttl_seconds: Time-to-live in seconds (default: 3600 = 1 hour)

        Returns:
            True if all caches are fresh, False if any are stale
        """
        if not mappings:
            return False

        for mapping in mappings:
            if not await self.is_cache_fresh(mapping, ttl_seconds):
                return False

        return True

    async def update_last_validated(
        self, account_number: str, policy_id: str | None = None
    ) -> None:
        """
        Update the last_validated_at timestamp for a mapping.

        Args:
            account_number: The account number to update
            policy_id: Optional policy ID (if None, updates all policies for account)
        """
        if policy_id:
            # Update specific policy
            mapping = await self.get_by_account_and_policy(account_number, policy_id)
            if mapping:
                mapping.last_validated_at = datetime.now(UTC)
                await self.session.commit()
        else:
            # Update all policies for account
            mappings = await self.get_by_account_number(account_number)
            for mapping in mappings:
                mapping.last_validated_at = datetime.now(UTC)
            if mappings:
                await self.session.commit()

    async def get_stale_mappings(self, ttl_seconds: int = 3600) -> list[AccountTemplateMapping]:
        """
        Get all mappings that are older than TTL.

        Args:
            ttl_seconds: Time-to-live in seconds (default: 3600 = 1 hour)

        Returns:
            List of stale mappings
        """
        cutoff_time = datetime.now(UTC) - timedelta(seconds=ttl_seconds)

        stmt = select(AccountTemplateMapping).where(AccountTemplateMapping.cached_at < cutoff_time)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_mappings_by_template(self, template_id: str) -> list[AccountTemplateMapping]:
        """
        Get all account mappings for a specific template.

        Args:
            template_id: The contract template ID

        Returns:
            List of mappings for the template
        """
        stmt = select(AccountTemplateMapping).where(
            AccountTemplateMapping.contract_template_id == template_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_source(self, source: str) -> int:
        """
        Count mappings by source type.

        Args:
            source: Source type (external_api, manual, migrated)

        Returns:
            Count of mappings from that source
        """
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(AccountTemplateMapping)
            .where(AccountTemplateMapping.source == source)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
