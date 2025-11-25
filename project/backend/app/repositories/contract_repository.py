"""
Contract repository for contract template database operations.
"""

from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.repositories.base import BaseRepository
from app.models.database.contract import Contract


class ContractRepository(BaseRepository[Contract]):
    """
    Repository for Contract (template) model with template-specific queries.

    Inherits generic CRUD operations from BaseRepository and adds
    template-specific query methods.
    """

    def __init__(self, session: AsyncSession):
        """Initialize contract repository."""
        super().__init__(Contract, session)

    async def get_with_extraction(self, contract_id: str) -> Contract | None:
        """
        Retrieve a contract template by ID with extraction eagerly loaded.

        Args:
            contract_id: The contract template ID

        Returns:
            Contract with extraction relationship loaded, or None if not found
        """
        stmt = (
            select(Contract)
            .where(Contract.contract_id == contract_id)
            .options(joinedload(Contract.extractions))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_contract_type(self, contract_type: str, limit: int = 100) -> List[Contract]:
        """
        Retrieve contract templates by type (GAP, VSC, etc.).

        Args:
            contract_type: The type of contract to filter by
            limit: Maximum number of results (default: 100)

        Returns:
            List of contract templates of the specified type
        """
        stmt = select(Contract).where(Contract.contract_type == contract_type).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_templates(
        self, contract_type: str | None = None, limit: int = 100
    ) -> List[Contract]:
        """
        Retrieve active contract templates, optionally filtered by type.

        Args:
            contract_type: Optional contract type filter
            limit: Maximum number of results (default: 100)

        Returns:
            List of active contract templates
        """
        stmt = select(Contract).where(Contract.is_active == True)

        if contract_type:
            stmt = stmt.where(Contract.contract_type == contract_type)

        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_template_version(
        self, template_version: str, limit: int = 100
    ) -> List[Contract]:
        """
        Retrieve contract templates by version.

        Args:
            template_version: The template version to search for
            limit: Maximum number of results (default: 100)

        Returns:
            List of contract templates with the specified version
        """
        stmt = select(Contract).where(Contract.template_version == template_version).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_templates(self, limit: int = 20) -> List[Contract]:
        """
        Get most recently created contract templates.

        Args:
            limit: Number of templates to return (default: 20)

        Returns:
            List of templates ordered by creation date descending
        """
        stmt = select(Contract).order_by(Contract.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_or_update(self, contract: Contract) -> Contract:
        """
        Create a new contract template or update if it already exists (upsert).
        Uses contract_id as the unique identifier.

        Args:
            contract: Contract template instance to create or update

        Returns:
            Created or updated contract template
        """
        existing = await self.get_by_id(contract.contract_id)

        if existing:
            # Update existing template
            existing.s3_bucket = contract.s3_bucket
            existing.s3_key = contract.s3_key
            existing.document_text = contract.document_text
            existing.embeddings = contract.embeddings
            existing.text_extraction_status = contract.text_extraction_status
            existing.text_extracted_at = contract.text_extracted_at
            existing.document_repository_id = contract.document_repository_id
            existing.contract_type = contract.contract_type
            existing.contract_date = contract.contract_date
            existing.template_version = contract.template_version
            existing.effective_date = contract.effective_date
            existing.deprecated_date = contract.deprecated_date
            existing.is_active = contract.is_active
            existing.last_synced_at = contract.last_synced_at

            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            # Create new template
            return await self.create(contract)
