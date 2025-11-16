"""
Correction repository for correction-specific database operations.
"""

from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.database.correction import Correction


class CorrectionRepository(BaseRepository[Correction]):
    """
    Repository for Correction model with correction-specific queries.

    Inherits generic CRUD operations from BaseRepository and adds
    correction-specific query methods.
    """

    def __init__(self, session: AsyncSession):
        """Initialize correction repository."""
        super().__init__(Correction, session)

    async def get_by_extraction_id(self, extraction_id: UUID) -> List[Correction]:
        """
        Retrieve all corrections for a specific extraction.

        Args:
            extraction_id: The extraction ID to search for

        Returns:
            List of corrections for the extraction
        """
        stmt = (
            select(Correction)
            .where(Correction.extraction_id == extraction_id)
            .order_by(Correction.corrected_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_create(self, corrections: List[Correction]) -> List[Correction]:
        """
        Create multiple corrections in a single transaction.

        Args:
            corrections: List of Correction instances to create

        Returns:
            List of created corrections
        """
        for correction in corrections:
            self.session.add(correction)

        await self.session.flush()  # Flush to get IDs without committing

        return corrections

    async def get_by_field_name(self, extraction_id: UUID, field_name: str) -> List[Correction]:
        """
        Retrieve all corrections for a specific field in an extraction.

        Args:
            extraction_id: The extraction ID
            field_name: The field name to filter by

        Returns:
            List of corrections for the specified field
        """
        stmt = (
            select(Correction)
            .where(
                Correction.extraction_id == extraction_id,
                Correction.field_name == field_name,
            )
            .order_by(Correction.corrected_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
