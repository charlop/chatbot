"""
Unit tests for ExtractionService.
Tests extraction creation, retrieval, submission, and caching logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4
from decimal import Decimal

from app.services.extraction_service import (
    ExtractionService,
    ExtractionServiceError,
    ContractTextNotFoundError,
    ExtractionAlreadyExistsError,
)
from app.models.database.extraction import Extraction
from app.models.database.contract import Contract
from app.integrations.llm_providers.base import ExtractionResult, FieldExtraction


@pytest.mark.unit
class TestExtractionRetrieval:
    """Tests for extraction retrieval methods."""

    @pytest.mark.asyncio
    async def test_get_extraction_by_contract_id_cache_hit(self):
        """Test getting extraction with cache hit."""
        mock_db = AsyncMock()
        service = ExtractionService(mock_db)

        extraction_id = str(uuid4())

        with patch("app.services.extraction_service.cache_get", return_value=extraction_id):
            # Should return extraction ID from cache, then fall through to DB
            # For simplicity, we'll mock the DB query too
            mock_extraction = Extraction(
                extraction_id=extraction_id,
                contract_id="TEST-001",
                status="pending",
            )

            mock_db.execute = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_extraction
            mock_db.execute.return_value = mock_result

            result = await service.get_extraction_by_contract_id("TEST-001")

        assert result is not None
        assert result.extraction_id == extraction_id

    @pytest.mark.asyncio
    async def test_get_extraction_by_contract_id_cache_miss(self):
        """Test getting extraction with cache miss."""
        mock_db = AsyncMock()
        service = ExtractionService(mock_db)

        mock_extraction = Extraction(
            extraction_id=uuid4(),
            contract_id="TEST-001",
            status="pending",
        )

        mock_db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_extraction
        mock_db.execute.return_value = mock_result

        with (
            patch("app.services.extraction_service.cache_get", return_value=None),
            patch("app.services.extraction_service.cache_set") as mock_cache_set,
        ):
            result = await service.get_extraction_by_contract_id("TEST-001")

        assert result is not None
        assert result.contract_id == "TEST-001"
        # Should cache the extraction ID
        mock_cache_set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_extraction_by_contract_id_not_found(self):
        """Test getting non-existent extraction."""
        mock_db = AsyncMock()
        service = ExtractionService(mock_db)

        mock_db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with (
            patch("app.services.extraction_service.cache_get", return_value=None),
            patch("app.services.extraction_service.cache_set") as mock_cache_set,
        ):
            result = await service.get_extraction_by_contract_id("NONEXISTENT")

        assert result is None
        # Should cache "null" for not found
        mock_cache_set.assert_awaited_once()
        call_args = mock_cache_set.call_args
        assert call_args[0][1] == "null"

    @pytest.mark.asyncio
    async def test_get_extraction_by_id(self):
        """Test getting extraction by UUID."""
        mock_db = AsyncMock()
        service = ExtractionService(mock_db)

        extraction_id = uuid4()
        mock_extraction = Extraction(
            extraction_id=extraction_id,
            contract_id="TEST-001",
            status="pending",
        )

        mock_db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_extraction
        mock_db.execute.return_value = mock_result

        result = await service.get_extraction_by_id(extraction_id)

        assert result is not None
        assert result.extraction_id == extraction_id


@pytest.mark.unit
class TestExtractionCreation:
    """Tests for extraction creation."""

    @pytest.mark.asyncio
    async def test_create_extraction_success(self):
        """Test successful extraction creation."""
        mock_db = AsyncMock()
        service = ExtractionService(mock_db)

        # Mock contract
        mock_contract = Contract(
            contract_id="TEST-001",
            account_number="ACC-12345",
            s3_bucket="test-bucket",
            s3_key="test.pdf",
            contract_type="GAP",
            document_text="Sample contract text for extraction",
        )

        # Mock LLM extraction result
        mock_llm_result = ExtractionResult(
            gap_insurance_premium=FieldExtraction(
                value=1500.00,
                confidence=95.0,
                source={"page": 1, "section": "3"},
            ),
            refund_calculation_method=FieldExtraction(
                value="Pro-rata",
                confidence=90.0,
                source={"page": 2, "section": "5"},
            ),
            cancellation_fee=FieldExtraction(
                value=50.00,
                confidence=92.0,
                source={"page": 3, "section": "7"},
            ),
            provider="anthropic",
            model_version="claude-3-5-sonnet-20241022",
            processing_time_ms=1200,
            prompt_tokens=1500,
            completion_tokens=300,
            total_cost_usd=Decimal("0.015"),
        )

        # Mock database queries
        mock_db.execute = AsyncMock()

        # First query: check existing extraction (should be None)
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None

        # Second query: get contract (should return mock_contract)
        mock_contract_result = MagicMock()
        mock_contract_result.scalar_one_or_none.return_value = mock_contract

        mock_db.execute.side_effect = [mock_existing_result, mock_contract_result]

        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock()

        with (
            patch("app.services.extraction_service.cache_get", return_value=None),
            patch.object(
                service.llm_service, "extract_contract_data", return_value=mock_llm_result
            ),
            patch("app.utils.cache.get_redis", return_value=mock_redis),
        ):
            result = await service.create_extraction("TEST-001")

        assert result is not None
        assert result.contract_id == "TEST-001"
        assert result.gap_insurance_premium == Decimal("1500.00")
        assert result.refund_calculation_method == "Pro-rata"
        assert result.cancellation_fee == Decimal("50.00")
        assert result.status == "pending"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_extraction_already_exists(self):
        """Test extraction creation when already exists (idempotency)."""
        mock_db = AsyncMock()
        service = ExtractionService(mock_db)

        # Mock existing extraction
        mock_extraction = Extraction(
            extraction_id=uuid4(),
            contract_id="TEST-001",
            status="pending",
        )

        mock_db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_extraction
        mock_db.execute.return_value = mock_result

        with (
            patch("app.services.extraction_service.cache_get", return_value=None),
            patch("app.services.extraction_service.cache_set"),
        ):
            with pytest.raises(ExtractionAlreadyExistsError) as exc_info:
                await service.create_extraction("TEST-001")

        assert "already exists" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_extraction_contract_not_found(self):
        """Test extraction creation when contract doesn't exist."""
        mock_db = AsyncMock()
        service = ExtractionService(mock_db)

        # Mock no existing extraction
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None

        # Mock no contract found
        mock_contract_result = MagicMock()
        mock_contract_result.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock()
        mock_db.execute.side_effect = [mock_existing_result, mock_contract_result]

        with patch("app.services.extraction_service.cache_get", return_value=None):
            with pytest.raises(ExtractionServiceError) as exc_info:
                await service.create_extraction("NONEXISTENT")

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_extraction_no_document_text(self):
        """Test extraction creation when document_text is missing."""
        mock_db = AsyncMock()
        service = ExtractionService(mock_db)

        # Mock contract without document_text
        mock_contract = Contract(
            contract_id="TEST-001",
            account_number="ACC-12345",
            s3_bucket="test-bucket",
            s3_key="test.pdf",
            contract_type="GAP",
            document_text=None,  # Missing document text
            text_extraction_status="pending",
        )

        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None

        mock_contract_result = MagicMock()
        mock_contract_result.scalar_one_or_none.return_value = mock_contract

        mock_db.execute = AsyncMock()
        mock_db.execute.side_effect = [mock_existing_result, mock_contract_result]

        with patch("app.services.extraction_service.cache_get", return_value=None):
            with pytest.raises(ContractTextNotFoundError) as exc_info:
                await service.create_extraction("TEST-001")

        assert "not available" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_extraction_llm_error(self):
        """Test extraction creation when LLM service fails."""
        from app.integrations.llm_providers.base import LLMError

        mock_db = AsyncMock()
        service = ExtractionService(mock_db)

        mock_contract = Contract(
            contract_id="TEST-001",
            account_number="ACC-12345",
            s3_bucket="test-bucket",
            s3_key="test.pdf",
            contract_type="GAP",
            document_text="Sample contract text",
        )

        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None

        mock_contract_result = MagicMock()
        mock_contract_result.scalar_one_or_none.return_value = mock_contract

        mock_db.execute = AsyncMock()
        mock_db.execute.side_effect = [mock_existing_result, mock_contract_result]

        with (
            patch("app.services.extraction_service.cache_get", return_value=None),
            patch.object(
                service.llm_service,
                "extract_contract_data",
                side_effect=LLMError("API rate limit exceeded"),
            ),
        ):
            with pytest.raises(ExtractionServiceError) as exc_info:
                await service.create_extraction("TEST-001")

        assert "llm extraction failed" in str(exc_info.value).lower()


@pytest.mark.unit
class TestExtractionSubmission:
    """Tests for extraction submission with corrections."""

    @pytest.mark.asyncio
    async def test_submit_extraction_no_corrections(self):
        """Test submitting extraction without corrections."""
        mock_db = AsyncMock()
        service = ExtractionService(mock_db)

        extraction_id = uuid4()
        mock_extraction = Extraction(
            extraction_id=extraction_id,
            contract_id="TEST-001",
            status="pending",
            gap_insurance_premium=Decimal("1500.00"),
        )

        # Mock get_extraction_by_id
        with (
            patch.object(service, "get_extraction_by_id", return_value=mock_extraction),
            patch.object(service, "invalidate_cache", new=AsyncMock()),
        ):
            result = await service.submit_extraction(
                extraction_id=extraction_id,
                corrections=[],
                notes="Approved without changes",
            )

        assert result.status == "approved"
        assert result.approved_at is not None
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_submit_extraction_with_corrections(self):
        """Test submitting extraction with field corrections."""
        from app.schemas.requests import FieldCorrection

        mock_db = AsyncMock()
        service = ExtractionService(mock_db)

        extraction_id = uuid4()
        mock_extraction = Extraction(
            extraction_id=extraction_id,
            contract_id="TEST-001",
            status="pending",
            gap_insurance_premium=Decimal("1500.00"),
            refund_calculation_method="Pro-rata",
        )

        corrections = [
            FieldCorrection(
                field_name="gap_insurance_premium",
                corrected_value="1600.00",
                correction_reason="Incorrect amount extracted",
            ),
            FieldCorrection(
                field_name="refund_calculation_method",
                corrected_value="Rule of 78s",
                correction_reason="Wrong refund method",
            ),
        ]

        with (
            patch.object(service, "get_extraction_by_id", return_value=mock_extraction),
            patch.object(service, "invalidate_cache", new=AsyncMock()),
            patch("app.repositories.correction_repository.CorrectionRepository") as mock_repo_class,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            result = await service.submit_extraction(
                extraction_id=extraction_id,
                corrections=corrections,
                notes="Corrected values",
            )

        # Verify corrections were applied
        assert result.gap_insurance_premium == Decimal("1600.00")
        assert result.refund_calculation_method == "Rule of 78s"
        assert result.status == "approved"
        mock_repo.bulk_create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_submit_extraction_not_found(self):
        """Test submitting non-existent extraction."""
        mock_db = AsyncMock()
        service = ExtractionService(mock_db)

        extraction_id = uuid4()

        with patch.object(service, "get_extraction_by_id", return_value=None):
            with pytest.raises(ExtractionServiceError) as exc_info:
                await service.submit_extraction(
                    extraction_id=extraction_id,
                    corrections=[],
                )

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_submit_extraction_already_submitted(self):
        """Test submitting already-submitted extraction."""
        mock_db = AsyncMock()
        service = ExtractionService(mock_db)

        extraction_id = uuid4()
        mock_extraction = Extraction(
            extraction_id=extraction_id,
            contract_id="TEST-001",
            status="approved",  # Already submitted
        )

        with patch.object(service, "get_extraction_by_id", return_value=mock_extraction):
            with pytest.raises(ExtractionServiceError) as exc_info:
                await service.submit_extraction(
                    extraction_id=extraction_id,
                    corrections=[],
                )

        assert "already submitted" in str(exc_info.value).lower()


@pytest.mark.unit
class TestExtractionCaching:
    """Tests for extraction caching logic."""

    @pytest.mark.asyncio
    async def test_invalidate_cache(self):
        """Test cache invalidation for extraction and related contracts."""
        mock_db = AsyncMock()
        service = ExtractionService(mock_db)

        with (
            patch("app.services.extraction_service.cache_delete") as mock_delete,
            patch(
                "app.services.extraction_service.cache_delete_pattern", return_value=3
            ) as mock_delete_pattern,
        ):
            await service.invalidate_cache("TEST-001")

        # Should delete extraction cache
        mock_delete.assert_awaited_once_with("extraction:contract:TEST-001")

        # Should delete contract cache pattern
        mock_delete_pattern.assert_awaited_once_with("contract:*:TEST-001")

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation methods."""
        mock_db = AsyncMock()
        service = ExtractionService(mock_db)

        # Test contract_id cache key
        cache_key = service._get_cache_key("TEST-001")
        assert cache_key == "extraction:contract:TEST-001"

        # Test extraction_id cache key
        extraction_id = uuid4()
        cache_key_by_id = service._get_cache_key_by_id(extraction_id)
        assert cache_key_by_id == f"extraction:id:{extraction_id}"
