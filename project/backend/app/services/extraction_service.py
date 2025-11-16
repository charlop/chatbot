"""
Extraction Service - Orchestrates LLM extraction workflow.

Handles:
- Extraction creation with idempotency (DB + Redis caching)
- LLM provider orchestration
- Database persistence
- Redis caching for performance
"""

import logging
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database.extraction import Extraction
from app.models.database.contract import Contract
from app.integrations.llm_providers.base import ExtractionResult, LLMError
from app.services.llm_service import LLMService
from app.utils.cache import cache_get, cache_set, cache_delete, cache_delete_pattern, get_redis
from app.config import settings

logger = logging.getLogger(__name__)


class ExtractionServiceError(Exception):
    """Base exception for extraction service errors."""

    pass


class ContractTextNotFoundError(ExtractionServiceError):
    """Raised when contract document_text is not available."""

    pass


class ExtractionAlreadyExistsError(ExtractionServiceError):
    """Raised when extraction already exists for contract."""

    pass


class ExtractionService:
    """
    Service for managing contract data extraction.

    Orchestrates:
    - LLM provider calls for extraction
    - Database storage with idempotency
    - Redis caching for performance
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize extraction service.

        Args:
            db: Database session
        """
        self.db = db
        self.llm_service = LLMService()

    def _get_cache_key(self, contract_id: str) -> str:
        """Generate Redis cache key for extraction by contract ID."""
        return f"extraction:contract:{contract_id}"

    def _get_cache_key_by_id(self, extraction_id: UUID) -> str:
        """Generate Redis cache key for extraction by extraction ID."""
        return f"extraction:id:{extraction_id}"

    async def get_extraction_by_contract_id(self, contract_id: str) -> Optional[Extraction]:
        """
        Get extraction for contract (with caching).

        Args:
            contract_id: Contract ID

        Returns:
            Extraction if exists, None otherwise
        """
        # Try cache first
        cache_key = self._get_cache_key(contract_id)
        cached_value = await cache_get(cache_key)

        if cached_value is not None:
            logger.debug(f"Cache HIT for extraction: {contract_id}")
            # If cached value is the string "null", no extraction exists
            if cached_value == "null":
                return None
            # Otherwise reconstruct extraction from cache (would need serialization logic)
            # For now, fall through to DB to keep it simple
        else:
            logger.debug(f"Cache MISS for extraction: {contract_id}")

        # Query database
        stmt = select(Extraction).where(Extraction.contract_id == contract_id)
        result = await self.db.execute(stmt)
        extraction = result.scalar_one_or_none()

        # Cache result - cache "null" for not found, or cache extraction ID for found
        if extraction is None:
            await cache_set(cache_key, "null", ttl=settings.cache_ttl_extraction)
            logger.debug(f"Cached null extraction for {contract_id}")
        else:
            # Cache the extraction ID so we know it exists
            await cache_set(
                cache_key, str(extraction.extraction_id), ttl=settings.cache_ttl_extraction
            )
            logger.debug(f"Cached extraction ID for {contract_id}")

        return extraction

    async def get_extraction_by_id(self, extraction_id: UUID) -> Optional[Extraction]:
        """
        Get extraction by ID.

        Args:
            extraction_id: Extraction UUID

        Returns:
            Extraction if exists, None otherwise
        """
        stmt = select(Extraction).where(Extraction.extraction_id == extraction_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_extraction(
        self,
        contract_id: str,
        extracted_by: Optional[UUID] = None,
    ) -> Extraction:
        """
        Create extraction for contract with idempotency.

        Flow:
        1. Check if extraction already exists (DB + cache)
        2. Get contract and validate document_text exists
        3. Call LLM service to extract data
        4. Create Extraction record in database
        5. Cache extraction in Redis
        6. Return extraction

        Args:
            contract_id: Contract ID to extract
            extracted_by: User ID who triggered extraction (optional)

        Returns:
            Extraction record

        Raises:
            ExtractionAlreadyExistsError: If extraction already exists
            ContractTextNotFoundError: If document_text not available
            ExtractionServiceError: For other errors
        """
        logger.info(f"Creating extraction for contract {contract_id}")

        # Check idempotency - extraction already exists?
        existing_extraction = await self.get_extraction_by_contract_id(contract_id)
        if existing_extraction:
            logger.warning(
                f"Extraction already exists for contract {contract_id}, "
                f"returning existing (idempotent)"
            )
            raise ExtractionAlreadyExistsError(
                f"Extraction already exists for contract {contract_id}"
            )

        # Get contract from database
        stmt = select(Contract).where(Contract.contract_id == contract_id)
        result = await self.db.execute(stmt)
        contract = result.scalar_one_or_none()

        if not contract:
            raise ExtractionServiceError(f"Contract not found: {contract_id}")

        # Validate document_text exists (populated by external ETL)
        if not contract.document_text:
            logger.error(
                f"Contract {contract_id} has no document_text "
                f"(text_extraction_status: {contract.text_extraction_status})"
            )
            raise ContractTextNotFoundError(
                f"Contract {contract_id} document text not available. "
                f"Status: {contract.text_extraction_status or 'pending'}"
            )

        # Call LLM service to extract data
        try:
            logger.info(f"Calling LLM service for contract {contract_id}")
            extraction_result: ExtractionResult = await self.llm_service.extract_contract_data(
                document_text=contract.document_text,
                contract_id=contract_id,
            )
            logger.info(
                f"LLM extraction successful for {contract_id} "
                f"(provider: {extraction_result.provider}, "
                f"model: {extraction_result.model_version})"
            )

        except LLMError as e:
            logger.error(f"LLM extraction failed for contract {contract_id}: {e}")
            raise ExtractionServiceError(f"LLM extraction failed: {str(e)}") from e

        except Exception as e:
            logger.error(f"Unexpected error during LLM extraction for {contract_id}: {e}")
            raise ExtractionServiceError(f"Extraction failed: {str(e)}") from e

        # Map ExtractionResult to Extraction model
        extraction = Extraction(
            contract_id=contract_id,
            # GAP Insurance Premium
            gap_insurance_premium=(
                Decimal(str(extraction_result.gap_insurance_premium.value))
                if extraction_result.gap_insurance_premium
                and extraction_result.gap_insurance_premium.value is not None
                else None
            ),
            gap_premium_confidence=(
                extraction_result.gap_insurance_premium.confidence
                if extraction_result.gap_insurance_premium
                else None
            ),
            gap_premium_source=(
                extraction_result.gap_insurance_premium.source
                if extraction_result.gap_insurance_premium
                else None
            ),
            # Refund Calculation Method
            refund_calculation_method=(
                str(extraction_result.refund_calculation_method.value)
                if extraction_result.refund_calculation_method
                and extraction_result.refund_calculation_method.value is not None
                else None
            ),
            refund_method_confidence=(
                extraction_result.refund_calculation_method.confidence
                if extraction_result.refund_calculation_method
                else None
            ),
            refund_method_source=(
                extraction_result.refund_calculation_method.source
                if extraction_result.refund_calculation_method
                else None
            ),
            # Cancellation Fee
            cancellation_fee=(
                Decimal(str(extraction_result.cancellation_fee.value))
                if extraction_result.cancellation_fee
                and extraction_result.cancellation_fee.value is not None
                else None
            ),
            cancellation_fee_confidence=(
                extraction_result.cancellation_fee.confidence
                if extraction_result.cancellation_fee
                else None
            ),
            cancellation_fee_source=(
                extraction_result.cancellation_fee.source
                if extraction_result.cancellation_fee
                else None
            ),
            # LLM Metadata
            llm_model_version=extraction_result.model_version,
            llm_provider=extraction_result.provider,
            processing_time_ms=extraction_result.processing_time_ms,
            prompt_tokens=extraction_result.prompt_tokens,
            completion_tokens=extraction_result.completion_tokens,
            total_cost_usd=extraction_result.total_cost_usd,
            # Status
            status="pending",  # Default status, requires human approval
            extracted_at=datetime.utcnow(),
            extracted_by=extracted_by,
        )

        # Persist to database
        self.db.add(extraction)
        await self.db.commit()
        await self.db.refresh(extraction)

        logger.info(
            f"Extraction created for contract {contract_id} "
            f"(extraction_id: {extraction.extraction_id}, status: {extraction.status})"
        )

        # Invalidate cache (in case we cached "null" earlier)
        cache_key = self._get_cache_key(contract_id)
        redis = await get_redis()
        if redis:
            try:
                await redis.delete(cache_key)
                logger.debug(f"Invalidated cache for extraction {contract_id}")
            except Exception as e:
                logger.warning(f"Cache invalidation failed: {e}")

        return extraction

    async def invalidate_cache(self, contract_id: str) -> None:
        """
        Invalidate cached extraction and related contract caches.

        When extraction is updated, we need to invalidate:
        1. Extraction cache (by contract_id)
        2. Contract caches (both by account and by id) - because contract response may include extraction

        Args:
            contract_id: Contract ID
        """
        # Invalidate extraction cache
        extraction_cache_key = self._get_cache_key(contract_id)
        await cache_delete(extraction_cache_key)
        logger.info(f"Invalidated extraction cache for {contract_id}")

        # Also invalidate contract caches since they may include extraction data
        contract_cache_pattern = f"contract:*:{contract_id}"
        deleted_count = await cache_delete_pattern(contract_cache_pattern)
        if deleted_count > 0:
            logger.info(f"Invalidated {deleted_count} contract cache entries for {contract_id}")

    async def submit_extraction(
        self,
        extraction_id: UUID,
        corrections: list,
        notes: Optional[str] = None,
        submitted_by: Optional[UUID] = None,
    ) -> Extraction:
        """
        Submit extraction with optional field corrections.

        Handles both simple approval (no corrections) and approval with corrections.
        Corrections are dual-written:
        1. Stored in corrections table (for ML fine-tuning metrics)
        2. Applied to extraction table (source of truth)

        Flow:
        1. Validate extraction exists and is pending
        2. For each correction:
           - Create Correction record (audit trail)
           - Update corresponding field in Extraction (source of truth)
        3. Update status to 'approved'
        4. Set approved_at and approved_by
        5. Commit transaction (atomic)
        6. Invalidate cache
        7. Return updated extraction

        Args:
            extraction_id: Extraction UUID to submit
            corrections: List of field corrections (can be empty)
            notes: Optional submission notes
            submitted_by: User ID who submitted (optional, for future auth)

        Returns:
            Updated Extraction record

        Raises:
            ExtractionServiceError: If extraction not found or already submitted
        """
        from app.models.database.correction import Correction
        from app.repositories.correction_repository import CorrectionRepository

        logger.info(
            f"Submitting extraction {extraction_id} " f"with {len(corrections)} corrections"
        )

        # Get extraction
        extraction = await self.get_extraction_by_id(extraction_id)
        if not extraction:
            raise ExtractionServiceError(f"Extraction not found: {extraction_id}")

        # Validate status
        if extraction.status != "pending":
            raise ExtractionServiceError(
                f"Extraction {extraction_id} already submitted (status: {extraction.status})"
            )

        # Initialize correction repository
        correction_repo = CorrectionRepository(self.db)

        # Process corrections (if any)
        correction_records = []
        for correction_data in corrections:
            field_name = correction_data.field_name
            corrected_value = correction_data.corrected_value
            correction_reason = correction_data.correction_reason

            # Get original value
            original_value = None
            if field_name == "gap_insurance_premium":
                original_value = (
                    str(extraction.gap_insurance_premium)
                    if extraction.gap_insurance_premium
                    else None
                )
                # Update extraction field
                extraction.gap_insurance_premium = (
                    Decimal(corrected_value) if corrected_value else None
                )
            elif field_name == "refund_calculation_method":
                original_value = extraction.refund_calculation_method
                # Update extraction field
                extraction.refund_calculation_method = corrected_value
            elif field_name == "cancellation_fee":
                original_value = (
                    str(extraction.cancellation_fee) if extraction.cancellation_fee else None
                )
                # Update extraction field
                extraction.cancellation_fee = Decimal(corrected_value) if corrected_value else None

            # Create correction record
            correction = Correction(
                extraction_id=extraction_id,
                field_name=field_name,
                original_value=original_value,
                corrected_value=corrected_value,
                correction_reason=correction_reason,
                corrected_by=submitted_by,
            )
            correction_records.append(correction)

            logger.info(
                f"Correction applied to {field_name}: " f"{original_value} -> {corrected_value}"
            )

        # Bulk create corrections
        if correction_records:
            await correction_repo.bulk_create(correction_records)
            logger.info(f"Created {len(correction_records)} correction records")

        # Update extraction status
        extraction.status = "approved"
        extraction.approved_at = datetime.utcnow()
        extraction.approved_by = submitted_by

        # Commit transaction (atomic - all or nothing)
        await self.db.commit()
        await self.db.refresh(extraction)

        logger.info(
            f"Extraction {extraction_id} submitted successfully "
            f"(corrections: {len(corrections)}, status: {extraction.status})"
        )

        # Invalidate cache
        await self.invalidate_cache(extraction.contract_id)

        return extraction
