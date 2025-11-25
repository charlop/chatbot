"""
Integration tests for template-based contract search.

Tests the full flow: Account Number → External RDB → Template Lookup
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.main import app
from app.models.database import Contract, AccountTemplateMapping
from tests.factories import ContractFactory, AccountMappingFactory


@pytest.mark.integration
class TestTemplateSearch:
    """Integration tests for template search flows."""

    @pytest.mark.asyncio
    async def test_search_by_account_number_success(self, async_client: AsyncClient, db_session):
        """Test searching by account number with mapping in database."""
        # Setup: Create template and mapping
        template = ContractFactory.build(
            contract_id="GAP-2024-TEMPLATE-001",
            contract_type="GAP",
            template_version="1.0",
        )
        mapping = AccountMappingFactory.build(
            account_number="000000000001",
            contract_template_id="GAP-2024-TEMPLATE-001",
            source="external_api",
        )

        db_session.add(template)
        db_session.add(mapping)
        await db_session.commit()

        # Test: Search by account number
        response = await async_client.post(
            "/api/v1/contracts/search",
            json={"account_number": "000000000001"},
        )

        # Assert: Should find template
        assert response.status_code == 200
        data = response.json()
        assert data["contractId"] == "GAP-2024-TEMPLATE-001"
        assert data["contractType"] == "GAP"
        assert data["templateVersion"] == "1.0"
        assert "accountNumber" not in data  # Should not return account number

    @pytest.mark.asyncio
    async def test_search_by_template_id_success(self, async_client: AsyncClient, db_session):
        """Test searching directly by template ID."""
        # Setup: Create template
        template = ContractFactory.build(
            contract_id="VSC-2024-TEMPLATE-002",
            contract_type="VSC",
            template_version="2.0",
        )
        db_session.add(template)
        await db_session.commit()

        # Test: Search by template ID
        response = await async_client.post(
            "/api/v1/contracts/search",
            json={"contract_id": "VSC-2024-TEMPLATE-002"},
        )

        # Assert: Should find template
        assert response.status_code == 200
        data = response.json()
        assert data["contractId"] == "VSC-2024-TEMPLATE-002"
        assert data["contractType"] == "VSC"
        assert data["templateVersion"] == "2.0"

    @pytest.mark.asyncio
    async def test_search_by_account_number_not_found(self, async_client: AsyncClient, db_session):
        """Test searching for account number with no mapping."""
        # No mapping created - should return 404

        response = await async_client.post(
            "/api/v1/contracts/search",
            json={"account_number": "999999999999"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "found" in data["detail"].lower() or "not found" in data["detail"].lower()
        assert "999999999999" in data["detail"]

    @pytest.mark.asyncio
    async def test_search_by_template_id_not_found(self, async_client: AsyncClient, db_session):
        """Test searching for non-existent template ID."""
        response = await async_client.post(
            "/api/v1/contracts/search",
            json={"contract_id": "NONEXISTENT-TEMPLATE"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
        assert "NONEXISTENT-TEMPLATE" in data["detail"]

    @pytest.mark.asyncio
    async def test_search_missing_both_parameters(self, async_client: AsyncClient):
        """Test search request with neither account_number nor contract_id."""
        response = await async_client.post(
            "/api/v1/contracts/search",
            json={},
        )

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_search_with_both_parameters(self, async_client: AsyncClient):
        """Test search request with both account_number and contract_id (invalid)."""
        response = await async_client.post(
            "/api/v1/contracts/search",
            json={
                "account_number": "000000000001",
                "contract_id": "GAP-2024-TEMPLATE-001",
            },
        )

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_search_multiple_mappings_same_template(
        self, async_client: AsyncClient, db_session
    ):
        """Test multiple accounts mapping to the same template."""
        # Setup: One template, multiple account mappings
        template = ContractFactory.build(
            contract_id="GAP-2024-TEMPLATE-SHARED",
            contract_type="GAP",
            template_version="1.0",
        )

        mapping1 = AccountMappingFactory.build(
            account_number="000000000010",
            contract_template_id="GAP-2024-TEMPLATE-SHARED",
        )
        mapping2 = AccountMappingFactory.build(
            account_number="000000000011",
            contract_template_id="GAP-2024-TEMPLATE-SHARED",
        )

        db_session.add(template)
        db_session.add(mapping1)
        db_session.add(mapping2)
        await db_session.commit()

        # Test: Search with first account
        response1 = await async_client.post(
            "/api/v1/contracts/search",
            json={"account_number": "000000000010"},
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["contractId"] == "GAP-2024-TEMPLATE-SHARED"

        # Test: Search with second account
        response2 = await async_client.post(
            "/api/v1/contracts/search",
            json={"account_number": "000000000011"},
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["contractId"] == "GAP-2024-TEMPLATE-SHARED"

        # Assert: Both return the same template
        assert data1["contractId"] == data2["contractId"]

    @pytest.mark.asyncio
    async def test_get_template_by_id_success(self, async_client: AsyncClient, db_session):
        """Test GET endpoint for retrieving template by ID."""
        # Setup: Create template
        template = ContractFactory.build(
            contract_id="GAP-2024-TEMPLATE-GET",
            contract_type="GAP",
            template_version="1.5",
            is_active=True,
        )
        db_session.add(template)
        await db_session.commit()

        # Test: GET /contracts/{id}
        response = await async_client.get("/api/v1/contracts/GAP-2024-TEMPLATE-GET")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["contractId"] == "GAP-2024-TEMPLATE-GET"
        assert data["templateVersion"] == "1.5"
        assert data["isActive"] is True

    @pytest.mark.asyncio
    async def test_get_template_with_extraction(self, async_client: AsyncClient, db_session):
        """Test GET template that has extraction data."""
        # Setup: Create template with extraction
        template = ContractFactory.build_with_extraction(contract_id="GAP-2024-TEMPLATE-EXTRACT")
        db_session.add(template)
        await db_session.commit()

        # Test
        response = await async_client.get("/api/v1/contracts/GAP-2024-TEMPLATE-EXTRACT")

        # Assert: Should include extraction data
        assert response.status_code == 200
        data = response.json()
        assert data["contractId"] == "GAP-2024-TEMPLATE-EXTRACT"
        assert "extractedData" in data
        assert data["extractedData"] is not None

    @pytest.mark.asyncio
    async def test_template_versioning_fields(self, async_client: AsyncClient, db_session):
        """Test that template versioning fields are returned correctly."""
        from datetime import date, timedelta

        template = ContractFactory.build(
            contract_id="GAP-2024-TEMPLATE-VERSION",
            template_version="2.5",
            effective_date=date.today() - timedelta(days=90),
            deprecated_date=None,
            is_active=True,
        )
        db_session.add(template)
        await db_session.commit()

        response = await async_client.get("/api/v1/contracts/GAP-2024-TEMPLATE-VERSION")

        assert response.status_code == 200
        data = response.json()
        assert data["templateVersion"] == "2.5"
        assert "effectiveDate" in data
        assert data["deprecatedDate"] is None
        assert data["isActive"] is True


@pytest.mark.integration
class TestTemplateSearchCaching:
    """Integration tests for template search caching behavior."""

    @pytest.mark.asyncio
    async def test_account_mapping_cached_after_lookup(self, async_client: AsyncClient, db_session):
        """Test that account mappings are cached after first lookup."""
        # Setup
        template = ContractFactory.build(contract_id="GAP-2024-TEMPLATE-CACHE")
        mapping = AccountMappingFactory.build(
            account_number="000000000020",
            contract_template_id="GAP-2024-TEMPLATE-CACHE",
        )
        db_session.add(template)
        db_session.add(mapping)
        await db_session.commit()

        # First lookup - should cache
        response1 = await async_client.post(
            "/api/v1/contracts/search",
            json={"account_number": "000000000020"},
        )
        assert response1.status_code == 200

        # Second lookup - should use cache (faster)
        response2 = await async_client.post(
            "/api/v1/contracts/search",
            json={"account_number": "000000000020"},
        )
        assert response2.status_code == 200
        assert response1.json() == response2.json()
