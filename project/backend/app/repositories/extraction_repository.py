"""
Extraction repository for extraction-specific database operations.
"""

from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.database.extraction import Extraction


class ExtractionRepository(BaseRepository[Extraction]):
    """
    Repository for Extraction model with extraction-specific queries.

    Inherits generic CRUD operations from BaseRepository and adds
    extraction-specific query methods.
    """

    def __init__(self, session: AsyncSession):
        """Initialize extraction repository."""
        super().__init__(Extraction, session)

    async def get_by_contract_id(self, contract_id: str) -> Extraction | None:
        """
        Retrieve an extraction by contract ID.
        Since there's a unique constraint, there's at most one extraction per contract.

        Args:
            contract_id: The contract ID to search for

        Returns:
            Extraction if found, None otherwise
        """
        stmt = select(Extraction).where(Extraction.contract_id == contract_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_contract_id_with_corrections(self, contract_id: str) -> Extraction | None:
        """
        Retrieve an extraction by contract ID with corrections eagerly loaded.

        Args:
            contract_id: The contract ID to search for

        Returns:
            Extraction with corrections relationship loaded, or None if not found
        """
        stmt = (
            select(Extraction)
            .where(Extraction.contract_id == contract_id)
            .options(selectinload(Extraction.corrections))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_corrections(self, extraction_id: UUID) -> Extraction | None:
        """
        Retrieve an extraction by ID with corrections eagerly loaded.

        Args:
            extraction_id: The extraction ID

        Returns:
            Extraction with corrections relationship loaded, or None if not found
        """
        stmt = (
            select(Extraction)
            .where(Extraction.extraction_id == extraction_id)
            .options(selectinload(Extraction.corrections))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending(self, limit: int = 100) -> List[Extraction]:
        """
        Retrieve all extractions with pending status (not yet approved or rejected).

        Args:
            limit: Maximum number of results (default: 100)

        Returns:
            List of pending extractions ordered by extraction date
        """
        stmt = (
            select(Extraction)
            .where(Extraction.status == "pending")
            .order_by(Extraction.extracted_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(self, status: str, limit: int = 100) -> List[Extraction]:
        """
        Retrieve extractions by status.

        Args:
            status: Status to filter by ('pending', 'approved', 'rejected')
            limit: Maximum number of results (default: 100)

        Returns:
            List of extractions with the specified status
        """
        stmt = (
            select(Extraction)
            .where(Extraction.status == status)
            .order_by(Extraction.extracted_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        extraction_id: UUID,
        status: str,
        user_id: UUID | None = None,
        rejection_reason: str | None = None,
    ) -> Extraction | None:
        """
        Update the status of an extraction (approve or reject).

        Args:
            extraction_id: ID of the extraction to update
            status: New status ('approved' or 'rejected')
            user_id: ID of the user performing the action
            rejection_reason: Reason for rejection (required if status is 'rejected')

        Returns:
            Updated extraction, or None if not found
        """
        extraction = await self.get_by_id(extraction_id)
        if extraction is None:
            return None

        extraction.status = status

        if status == "approved":
            from datetime import datetime

            extraction.approved_at = datetime.utcnow()
            extraction.approved_by = user_id
        elif status == "rejected":
            from datetime import datetime

            extraction.rejected_at = datetime.utcnow()
            extraction.rejected_by = user_id
            extraction.rejection_reason = rejection_reason

        await self.session.commit()
        await self.session.refresh(extraction)
        return extraction

    async def get_by_llm_provider(self, provider: str, limit: int = 100) -> List[Extraction]:
        """
        Retrieve extractions by LLM provider.

        Args:
            provider: LLM provider name ('openai', 'anthropic', 'bedrock')
            limit: Maximum number of results (default: 100)

        Returns:
            List of extractions from the specified provider
        """
        stmt = (
            select(Extraction)
            .where(Extraction.llm_provider == provider)
            .order_by(Extraction.extracted_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_extractions(self, limit: int = 20) -> List[Extraction]:
        """
        Get most recently created extractions.

        Args:
            limit: Number of extractions to return (default: 20)

        Returns:
            List of extractions ordered by extraction date descending
        """
        stmt = select(Extraction).order_by(Extraction.extracted_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_status(self, status: str) -> int:
        """
        Count extractions by status.

        Args:
            status: Status to count ('pending', 'approved', 'rejected')

        Returns:
            Number of extractions with the specified status
        """
        from sqlalchemy import func

        stmt = select(func.count()).select_from(Extraction).where(Extraction.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one()
