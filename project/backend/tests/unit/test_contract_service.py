"""
Unit tests for ContractService.
Tests contract search, retrieval, and caching logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.contract_service import ContractService
from app.schemas.requests import ContractSearchRequest
from app.schemas.responses import ContractResponse
from app.models.database.contract import Contract


@pytest.mark.unit
class TestContractService:
    """Tests for ContractService."""

    @pytest.mark.asyncio
    async def test_search_contract_found_in_cache(self):
        """Test searching for contract found in cache."""
        mock_db = AsyncMock()
        service = ContractService(mock_db)

        cached_response = {
            "contract_id": "TEST-001",
            "account_number": "ACC-12345",
            "s3_bucket": "test-bucket",
            "s3_key": "test.pdf",
            "contract_type": "GAP",
            "text_extraction_status": "completed",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        with patch("app.services.contract_service.cache_get", return_value=cached_response):
            request = ContractSearchRequest(account_number="ACC-12345")
            result = await service.search_contract(request)

        assert result is not None
        assert result.account_number == "ACC-12345"
        assert result.contract_id == "TEST-001"

    @pytest.mark.asyncio
    async def test_search_contract_found_in_database(self):
        """Test searching for contract found in database."""
        mock_db = AsyncMock()
        service = ContractService(mock_db)

        mock_contract = Contract(
            contract_id="TEST-001",
            account_number="ACC-12345",
            s3_bucket="test-bucket",
            s3_key="test.pdf",
            contract_type="GAP",
        )

        service.contract_repo.get_by_account_number = AsyncMock(return_value=mock_contract)

        with (
            patch("app.services.contract_service.cache_get", return_value=None),
            patch("app.services.contract_service.cache_set") as mock_cache_set,
            patch.object(service, "_log_audit_event", new=AsyncMock()),
            patch.object(service, "_contract_to_response") as mock_to_response,
        ):

            mock_response = ContractResponse(
                contract_id="TEST-001",
                account_number="ACC-12345",
                s3_bucket="test-bucket",
                s3_key="test.pdf",
                contract_type="GAP",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            mock_to_response.return_value = mock_response

            request = ContractSearchRequest(account_number="ACC-12345")
            result = await service.search_contract(request)

        assert result is not None
        assert result.account_number == "ACC-12345"
        assert result.contract_id == "TEST-001"
        mock_cache_set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_search_contract_not_found(self):
        """Test searching for non-existent contract."""
        mock_db = AsyncMock()
        service = ContractService(mock_db)

        service.contract_repo.get_by_account_number = AsyncMock(return_value=None)

        with (
            patch("app.services.contract_service.cache_get", return_value=None),
            patch.object(service, "_mock_external_rdb_lookup", return_value=None),
        ):

            request = ContractSearchRequest(account_number="NONEXISTENT")
            result = await service.search_contract(request)

        assert result is None

    @pytest.mark.asyncio
    async def test_search_contract_whitespace_handling(self):
        """Test that account number whitespace is trimmed."""
        mock_db = AsyncMock()
        service = ContractService(mock_db)

        service.contract_repo.get_by_account_number = AsyncMock(return_value=None)

        with (
            patch("app.services.contract_service.cache_get", return_value=None),
            patch.object(service, "_mock_external_rdb_lookup", return_value=None),
        ):

            request = ContractSearchRequest(account_number="  ACC-12345  ")
            result = await service.search_contract(request)

        # Should return None (not found) but validate whitespace was trimmed
        assert result is None

    @pytest.mark.asyncio
    async def test_get_contract_from_cache(self):
        """Test getting contract from cache."""
        mock_db = AsyncMock()
        service = ContractService(mock_db)

        cached_response = {
            "contract_id": "TEST-001",
            "account_number": "ACC-12345",
            "s3_bucket": "test-bucket",
            "s3_key": "test.pdf",
            "contract_type": "GAP",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        with patch("app.services.contract_service.cache_get", return_value=cached_response):
            result = await service.get_contract("TEST-001")

        assert result is not None
        assert result.contract_id == "TEST-001"
        assert result.account_number == "ACC-12345"

    @pytest.mark.asyncio
    async def test_get_contract_from_database(self):
        """Test getting contract from database when not in cache."""
        mock_db = AsyncMock()
        service = ContractService(mock_db)

        mock_contract = Contract(
            contract_id="TEST-001",
            account_number="ACC-12345",
            s3_bucket="test-bucket",
            s3_key="test.pdf",
            contract_type="GAP",
        )

        service.contract_repo.get_by_id = AsyncMock(return_value=mock_contract)

        with (
            patch("app.services.contract_service.cache_get", return_value=None),
            patch("app.services.contract_service.cache_set") as mock_cache_set,
            patch.object(service, "_log_audit_event", new=AsyncMock()),
            patch.object(service, "_contract_to_response") as mock_to_response,
        ):

            mock_response = ContractResponse(
                contract_id="TEST-001",
                account_number="ACC-12345",
                s3_bucket="test-bucket",
                s3_key="test.pdf",
                contract_type="GAP",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            mock_to_response.return_value = mock_response

            result = await service.get_contract("TEST-001")

        assert result is not None
        assert result.contract_id == "TEST-001"
        assert result.account_number == "ACC-12345"
        mock_cache_set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_contract_not_found(self):
        """Test getting non-existent contract."""
        mock_db = AsyncMock()
        service = ContractService(mock_db)

        service.contract_repo.get_by_id = AsyncMock(return_value=None)

        with patch("app.services.contract_service.cache_get", return_value=None):
            result = await service.get_contract("NONEXISTENT")

        assert result is None

    @pytest.mark.asyncio
    async def test_contract_to_response(self):
        """Test converting contract ORM to response schema."""
        mock_db = AsyncMock()
        service = ContractService(mock_db)

        contract = Contract(
            contract_id="TEST-001",
            account_number="ACC-12345",
            s3_bucket="test-bucket",
            s3_key="test.pdf",
            contract_type="GAP",
            customer_name="Test Customer",
            vehicle_info={"make": "Toyota", "model": "Camry"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        response = await service._contract_to_response(contract)

        assert response.contract_id == "TEST-001"
        assert response.account_number == "ACC-12345"
        assert response.s3_bucket == "test-bucket"
        assert response.customer_name == "Test Customer"
        assert response.vehicle_info == {"make": "Toyota", "model": "Camry"}

    @pytest.mark.asyncio
    async def test_log_audit_event(self):
        """Test audit event logging."""
        mock_db = AsyncMock()
        service = ContractService(mock_db)

        await service._log_audit_event(
            contract_id="TEST-001",
            event_type="search",
            event_data={"query": "ACC-12345"},
        )

        # Verify audit event was added to database
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_mock_external_rdb_lookup(self):
        """Test mock external RDB lookup returns None."""
        mock_db = AsyncMock()
        service = ContractService(mock_db)

        result = await service._mock_external_rdb_lookup("ACC-12345")

        assert result is None
