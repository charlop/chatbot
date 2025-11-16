"""
Unit tests for base repository class.
Tests generic CRUD operations.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.database.contract import Contract


# Concrete implementation for testing
class ContractTestRepository(BaseRepository[Contract]):
    """Test repository using Contract model."""

    def __init__(self, session: AsyncSession):
        super().__init__(Contract, session)


@pytest.mark.unit
@pytest.mark.db
class TestBaseRepository:
    """Tests for BaseRepository CRUD operations."""

    async def test_create(self, db_session: AsyncSession):
        """Test creating an entity."""
        repo = ContractTestRepository(db_session)

        contract = Contract(
            contract_id="TEST-CREATE-001",
            account_number="ACC-CREATE-001",
            pdf_url="https://example.com/create.pdf",
        )

        created = await repo.create(contract)
        assert created.contract_id == "TEST-CREATE-001"
        assert created.account_number == "ACC-CREATE-001"

    async def test_get_by_id(self, db_session: AsyncSession, test_contract: Contract):
        """Test retrieving entity by ID."""
        repo = ContractTestRepository(db_session)

        found = await repo.get_by_id(test_contract.contract_id)
        assert found is not None
        assert found.contract_id == test_contract.contract_id
        assert found.account_number == test_contract.account_number

    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """Test get_by_id returns None for non-existent ID."""
        repo = ContractTestRepository(db_session)

        found = await repo.get_by_id("NONEXISTENT-ID")
        assert found is None

    async def test_get_all(self, db_session: AsyncSession):
        """Test retrieving all entities."""
        repo = ContractTestRepository(db_session)

        # Create multiple contracts
        contracts = [
            Contract(
                contract_id=f"TEST-ALL-{i:03d}",
                account_number=f"ACC-ALL-{i:03d}",
                pdf_url=f"https://example.com/all-{i}.pdf",
            )
            for i in range(5)
        ]

        for contract in contracts:
            await repo.create(contract)

        all_contracts = await repo.get_all()
        assert len(all_contracts) >= 5  # At least the 5 we created

    async def test_get_all_with_limit(self, db_session: AsyncSession):
        """Test retrieving entities with limit."""
        repo = ContractTestRepository(db_session)

        # Create multiple contracts
        for i in range(10):
            contract = Contract(
                contract_id=f"TEST-LIMIT-{i:03d}",
                account_number=f"ACC-LIMIT-{i:03d}",
                pdf_url=f"https://example.com/limit-{i}.pdf",
            )
            await repo.create(contract)

        limited = await repo.get_all(limit=5)
        assert len(limited) == 5

    async def test_get_all_with_offset(self, db_session: AsyncSession):
        """Test retrieving entities with offset."""
        repo = ContractTestRepository(db_session)

        # Create contracts
        for i in range(5):
            contract = Contract(
                contract_id=f"TEST-OFFSET-{i:03d}",
                account_number=f"ACC-OFFSET-{i:03d}",
                pdf_url=f"https://example.com/offset-{i}.pdf",
            )
            await repo.create(contract)

        # Get with offset
        offset_results = await repo.get_all(offset=2, limit=10)
        # Should skip first 2
        assert all(
            c.contract_id >= "TEST-OFFSET-002"
            for c in offset_results
            if c.contract_id.startswith("TEST-OFFSET")
        )

    async def test_update(self, db_session: AsyncSession, test_contract: Contract):
        """Test updating an entity."""
        repo = ContractTestRepository(db_session)

        # Update the contract
        test_contract.customer_name = "Updated Customer Name"
        updated = await repo.update(test_contract)

        assert updated.customer_name == "Updated Customer Name"

        # Verify persistence
        found = await repo.get_by_id(test_contract.contract_id)
        assert found.customer_name == "Updated Customer Name"

    async def test_delete(self, db_session: AsyncSession):
        """Test deleting an entity."""
        repo = ContractTestRepository(db_session)

        # Create a contract to delete
        contract = Contract(
            contract_id="TEST-DELETE-001",
            account_number="ACC-DELETE-001",
            pdf_url="https://example.com/delete.pdf",
        )
        created = await repo.create(contract)

        # Delete it
        success = await repo.delete(created.contract_id)
        assert success is True

        # Verify deletion
        found = await repo.get_by_id(created.contract_id)
        assert found is None

    async def test_delete_nonexistent(self, db_session: AsyncSession):
        """Test deleting non-existent entity returns False."""
        repo = ContractTestRepository(db_session)

        success = await repo.delete("NONEXISTENT-ID")
        assert success is False

    async def test_count(self, db_session: AsyncSession):
        """Test counting entities."""
        repo = ContractTestRepository(db_session)

        # Create some contracts
        for i in range(3):
            contract = Contract(
                contract_id=f"TEST-COUNT-{i:03d}",
                account_number=f"ACC-COUNT-{i:03d}",
                pdf_url=f"https://example.com/count-{i}.pdf",
            )
            await repo.create(contract)

        count = await repo.count()
        assert count >= 3  # At least the 3 we created

    async def test_exists(self, db_session: AsyncSession, test_contract: Contract):
        """Test checking if entity exists."""
        repo = ContractTestRepository(db_session)

        exists = await repo.exists(test_contract.contract_id)
        assert exists is True

        not_exists = await repo.exists("NONEXISTENT-ID")
        assert not_exists is False
