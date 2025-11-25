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
    """

    def __init__(self, session: AsyncSession):
        """Initialize account mapping repository."""
        super().__init__(AccountTemplateMapping, session)

    async def get_by_account_number(self, account_number: str) -> AccountTemplateMapping | None:
        """
        Retrieve a mapping by account number.

        Args:
            account_number: The account number to search for

        Returns:
            AccountTemplateMapping if found, None otherwise
        """
        stmt = select(AccountTemplateMapping).where(
            AccountTemplateMapping.account_number == account_number
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update_mapping(
        self, account_number: str, template_id: str, source: str = "external_api"
    ) -> AccountTemplateMapping:
        """
        Create a new mapping or update existing one (upsert).

        Args:
            account_number: The account number
            template_id: The contract template ID
            source: Source of mapping (external_api, manual, migrated)

        Returns:
            Created or updated AccountTemplateMapping
        """
        existing = await self.get_by_account_number(account_number)

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
                contract_template_id=template_id,
                source=source,
            )
            return await self.create(mapping)

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

    async def update_last_validated(self, account_number: str) -> None:
        """
        Update the last_validated_at timestamp for a mapping.

        Args:
            account_number: The account number to update
        """
        mapping = await self.get_by_account_number(account_number)

        if mapping:
            mapping.last_validated_at = datetime.now(UTC)
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
