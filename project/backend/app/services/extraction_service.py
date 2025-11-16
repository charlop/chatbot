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
from redis.asyncio import Redis

from app.models.database.extraction import Extraction
from app.models.database.contract import Contract
from app.integrations.llm_providers.base import ExtractionResult, LLMError
from app.services.llm_service import LLMService
from app.utils.cache import get_redis

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
        self.cache_ttl = 1800  # 30 minutes in seconds
        self.cache_key_prefix = "extraction"

    def _get_cache_key(self, contract_id: str) -> str:
        """Generate Redis cache key for extraction."""
        return f"{self.cache_key_prefix}:{contract_id}"

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
        redis = await get_redis()

        if redis:
            try:
                # Check if we cached "not found" result
                cached_value = await redis.get(cache_key)
                if cached_value == b"null":
                    logger.debug(f"Cache HIT (null) for extraction {contract_id}")
                    return None
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")

        # Query database
        stmt = select(Extraction).where(Extraction.contract_id == contract_id)
        result = await self.db.execute(stmt)
        extraction = result.scalar_one_or_none()

        # Cache result (including null)
        if redis:
            try:
                if extraction is None:
                    await redis.setex(cache_key, self.cache_ttl, "null")
                    logger.debug(f"Cached null extraction for {contract_id}")
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")

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
        Invalidate cached extraction.

        Args:
            contract_id: Contract ID
        """
        cache_key = self._get_cache_key(contract_id)

        redis = await get_redis()
        if redis:
            try:
                await redis.delete(cache_key)
                logger.info(f"Invalidated extraction cache for {contract_id}")
            except Exception as e:
                logger.warning(f"Failed to invalidate cache: {e}")
