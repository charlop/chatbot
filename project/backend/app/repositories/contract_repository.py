"""
Contract repository for contract-specific database operations.
"""

from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.database.contract import Contract


class ContractRepository(BaseRepository[Contract]):
    """
    Repository for Contract model with contract-specific queries.

    Inherits generic CRUD operations from BaseRepository and adds
    contract-specific query methods.
    """

    def __init__(self, session: AsyncSession):
        """Initialize contract repository."""
        super().__init__(Contract, session)

    async def get_by_account_number(self, account_number: str) -> Contract | None:
        """
        Retrieve a contract by account number.

        Args:
            account_number: The account number to search for

        Returns:
            Contract if found, None otherwise
        """
        stmt = select(Contract).where(Contract.account_number == account_number)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_account_number_with_extraction(self, account_number: str) -> Contract | None:
        """
        Retrieve a contract by account number with extraction eagerly loaded.

        Args:
            account_number: The account number to search for

        Returns:
            Contract with extraction relationship loaded, or None if not found
        """
        stmt = (
            select(Contract)
            .where(Contract.account_number == account_number)
            .options(selectinload(Contract.extractions))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_extraction(self, contract_id: str) -> Contract | None:
        """
        Retrieve a contract by ID with extraction eagerly loaded.

        Args:
            contract_id: The contract ID

        Returns:
            Contract with extraction relationship loaded, or None if not found
        """
        stmt = (
            select(Contract)
            .where(Contract.contract_id == contract_id)
            .options(selectinload(Contract.extractions))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_by_customer_name(self, name_pattern: str) -> List[Contract]:
        """
        Search contracts by customer name (case-insensitive partial match).

        Args:
            name_pattern: Pattern to search for in customer names

        Returns:
            List of matching contracts
        """
        stmt = select(Contract).where(Contract.customer_name.ilike(f"%{name_pattern}%"))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_contract_type(self, contract_type: str, limit: int = 100) -> List[Contract]:
        """
        Retrieve contracts by type (GAP, VSC, etc.).

        Args:
            contract_type: The type of contract to filter by
            limit: Maximum number of results (default: 100)

        Returns:
            List of contracts of the specified type
        """
        stmt = select(Contract).where(Contract.contract_type == contract_type).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_or_update(self, contract: Contract) -> Contract:
        """
        Create a new contract or update if it already exists (upsert).
        Uses contract_id as the unique identifier.

        Args:
            contract: Contract instance to create or update

        Returns:
            Created or updated contract
        """
        existing = await self.get_by_id(contract.contract_id)

        if existing:
            # Update existing contract
            existing.account_number = contract.account_number
            existing.pdf_url = contract.pdf_url
            existing.document_repository_id = contract.document_repository_id
            existing.contract_type = contract.contract_type
            existing.contract_date = contract.contract_date
            existing.customer_name = contract.customer_name
            existing.vehicle_info = contract.vehicle_info
            existing.last_synced_at = contract.last_synced_at

            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            # Create new contract
            return await self.create(contract)

    async def get_recent_contracts(self, limit: int = 20) -> List[Contract]:
        """
        Get most recently created contracts.

        Args:
            limit: Number of contracts to return (default: 20)

        Returns:
            List of contracts ordered by creation date descending
        """
        stmt = select(Contract).order_by(Contract.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
