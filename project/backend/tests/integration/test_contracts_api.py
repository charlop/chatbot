"""
Integration tests for contract API endpoints.
Tests contract search and retrieval functionality.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Contract
from tests.factories import ContractFactory


@pytest.mark.integration
@pytest.mark.db
class TestContractSearchEndpoint:
    """Tests for POST /api/v1/contracts/search endpoint."""

    async def test_search_contract_found_in_database(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test searching for a contract that exists in the database."""
        # Create a test contract
        contract = ContractFactory.build(account_number="000000012345", contract_id="GAP-2024-0001")
        db_session.add(contract)
        await db_session.commit()

        # Search for the contract
        response = await async_client.post(
            "/api/v1/contracts/search", json={"account_number": "000000012345"}
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["contract_id"] == "GAP-2024-0001"
        assert data["account_number"] == "000000012345"
        assert "customer_name" in data
        assert "vehicle_info" in data

    async def test_search_contract_not_found(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test searching for a contract that doesn't exist."""
        # Search for non-existent contract (valid 12-digit format but not in DB)
        response = await async_client.post(
            "/api/v1/contracts/search", json={"account_number": "999999999999"}
        )

        # Assert 404 response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    async def test_search_contract_invalid_account_number(self, async_client: AsyncClient):
        """Test searching with an invalid account number."""
        # Search with empty account number
        response = await async_client.post("/api/v1/contracts/search", json={"account_number": ""})

        # Assert validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    async def test_search_contract_whitespace_trimming(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that account numbers are properly trimmed."""
        # Create a test contract
        contract = ContractFactory.build(account_number="000000099999", contract_id="GAP-2024-0099")
        db_session.add(contract)
        await db_session.commit()

        # Search with whitespace
        response = await async_client.post(
            "/api/v1/contracts/search",
            json={"account_number": "  000000099999  "},
        )

        # Assert contract found
        assert response.status_code == 200
        data = response.json()
        assert data["contract_id"] == "GAP-2024-0099"


@pytest.mark.integration
@pytest.mark.db
class TestContractRetrievalEndpoint:
    """Tests for GET /api/v1/contracts/{contract_id} endpoint."""

    async def test_get_contract_found(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test retrieving a contract that exists."""
        # Create a test contract
        contract = ContractFactory.build(contract_id="GAP-2024-TEST-001")
        db_session.add(contract)
        await db_session.commit()

        # Retrieve the contract
        response = await async_client.get("/api/v1/contracts/GAP-2024-TEST-001")

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["contract_id"] == "GAP-2024-TEST-001"
        assert "account_number" in data
        assert "customer_name" in data
        assert "vehicle_info" in data

    async def test_get_contract_not_found(self, async_client: AsyncClient):
        """Test retrieving a contract that doesn't exist."""
        # Retrieve non-existent contract
        response = await async_client.get("/api/v1/contracts/NONEXISTENT-ID")

        # Assert 404 response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    async def test_get_contract_with_extraction(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test retrieving a contract with extraction data."""
        # Create contract with extraction
        contract = ContractFactory.build_with_extraction(contract_id="GAP-2024-WITH-EXT")
        db_session.add(contract)
        await db_session.commit()

        # Retrieve contract
        response = await async_client.get("/api/v1/contracts/GAP-2024-WITH-EXT")

        # Assert response includes extraction
        assert response.status_code == 200
        data = response.json()
        assert data["contract_id"] == "GAP-2024-WITH-EXT"
        assert data["extracted_data"] is not None
        assert "gap_premium" in data["extracted_data"]

    async def test_get_contract_exclude_extraction(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test retrieving a contract without extraction data."""
        # Create contract
        contract = ContractFactory.build(contract_id="GAP-2024-NO-EXT")
        db_session.add(contract)
        await db_session.commit()

        # Retrieve contract without extraction
        response = await async_client.get(
            "/api/v1/contracts/GAP-2024-NO-EXT?include_extraction=false"
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["contract_id"] == "GAP-2024-NO-EXT"
        # Extracted data should be None (no extraction exists)
        assert data.get("extracted_data") is None


@pytest.mark.integration
@pytest.mark.db
class TestContractAuditLogging:
    """Tests for audit logging of contract operations."""

    async def test_search_creates_audit_event(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that searching for a contract creates an audit event."""
        # Create a test contract
        contract = ContractFactory.build(
            account_number="000000001111", contract_id="GAP-2024-AUDIT"
        )
        db_session.add(contract)
        await db_session.commit()

        # Search for the contract
        response = await async_client.post(
            "/api/v1/contracts/search", json={"account_number": "000000001111"}
        )

        # Assert search succeeded
        assert response.status_code == 200

        # Check audit event was created
        from sqlalchemy import select
        from app.models.database import AuditEvent

        result = await db_session.execute(
            select(AuditEvent).where(AuditEvent.contract_id == "GAP-2024-AUDIT")
        )
        audit_events = result.scalars().all()

        assert len(audit_events) > 0
        audit_event = audit_events[0]
        assert audit_event.action == "contract_search"
        assert audit_event.event_data["account_number"] == "000000001111"

    async def test_get_creates_audit_event(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that retrieving a contract creates an audit event."""
        # Create a test contract
        contract = ContractFactory.build(contract_id="GAP-2024-VIEW")
        db_session.add(contract)
        await db_session.commit()

        # Retrieve the contract
        response = await async_client.get("/api/v1/contracts/GAP-2024-VIEW")

        # Assert retrieval succeeded
        assert response.status_code == 200

        # Check audit event was created
        from sqlalchemy import select
        from app.models.database import AuditEvent

        result = await db_session.execute(
            select(AuditEvent).where(AuditEvent.contract_id == "GAP-2024-VIEW")
        )
        audit_events = result.scalars().all()

        assert len(audit_events) > 0
        audit_event = audit_events[0]
        assert audit_event.action == "contract_view"
