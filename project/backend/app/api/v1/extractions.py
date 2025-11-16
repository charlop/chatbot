"""
Extraction API endpoints for creating and retrieving contract extractions.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.requests import ExtractionCreateRequest, ExtractionSubmitRequest
from app.schemas.responses import ExtractionResponse, ErrorResponse
from app.services.extraction_service import (
    ExtractionService,
    ExtractionAlreadyExistsError,
    ContractTextNotFoundError,
    ExtractionServiceError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/extractions/create",
    response_model=ExtractionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create extraction for contract",
    description=(
        "Extract contract data using LLM. "
        "Retrieves document_text from database (populated by external ETL). "
        "Calls LLM provider to extract GAP premium, refund method, and cancellation fee. "
        "Returns extraction with confidence scores. "
        "Idempotent - returns existing extraction if already created."
    ),
    responses={
        201: {
            "description": "Extraction created successfully",
            "model": ExtractionResponse,
        },
        200: {
            "description": "Extraction already exists (idempotent)",
            "model": ExtractionResponse,
        },
        404: {
            "description": "Contract not found",
            "model": ErrorResponse,
        },
        400: {
            "description": "Contract document text not available",
            "model": ErrorResponse,
        },
        500: {
            "description": "LLM extraction failed",
            "model": ErrorResponse,
        },
    },
)
async def create_extraction(
    request: ExtractionCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create extraction for contract.

    Flow:
    1. Check if extraction already exists (idempotency)
    2. Retrieve document_text from database
    3. Call LLM service to extract data
    4. Store extraction in database (status: pending)
    5. Return extraction with confidence scores

    Args:
        request: Extraction create request with contract_id
        db: Database session (injected)

    Returns:
        ExtractionResponse with extracted fields and metadata

    Raises:
        HTTPException 404: If contract not found
        HTTPException 400: If document text not available
        HTTPException 500: If LLM extraction fails
    """
    logger.info(f"POST /extractions/create - contract_id: {request.contract_id}")

    # Initialize service
    extraction_service = ExtractionService(db)

    try:
        # Create extraction (idempotent)
        extraction = await extraction_service.create_extraction(
            contract_id=request.contract_id,
            extracted_by=None,  # TODO: Get from auth context in Phase 2
        )

        # Convert to response
        response = ExtractionResponse.from_orm_model(extraction)

        logger.info(
            f"Extraction created for contract {request.contract_id} "
            f"(extraction_id: {extraction.extraction_id})"
        )

        return response

    except ExtractionAlreadyExistsError:
        # Idempotent - return existing extraction
        logger.info(
            f"Extraction already exists for contract {request.contract_id}, returning existing"
        )
        existing_extraction = await extraction_service.get_extraction_by_contract_id(
            request.contract_id
        )
        response = ExtractionResponse.from_orm_model(existing_extraction)
        return response

    except ContractTextNotFoundError as e:
        logger.error(f"Contract document text not available: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except ExtractionServiceError as e:
        # Check if contract not found
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        else:
            # LLM or other error
            logger.error(f"Extraction service error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create extraction: {str(e)}",
            )

    except Exception as e:
        logger.error(f"Unexpected error creating extraction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/extractions/{extraction_id}",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get extraction by ID",
    description=(
        "Retrieve extraction by ID. "
        "Includes all extracted fields with confidence scores and sources. "
        "Returns 404 if extraction not found."
    ),
    responses={
        200: {
            "description": "Extraction found",
            "model": ExtractionResponse,
        },
        404: {
            "description": "Extraction not found",
            "model": ErrorResponse,
        },
    },
)
async def get_extraction(
    extraction_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve extraction by ID.

    Args:
        extraction_id: Extraction UUID
        db: Database session (injected)

    Returns:
        ExtractionResponse with extraction data

    Raises:
        HTTPException 404: If extraction not found
    """
    logger.info(f"GET /extractions/{extraction_id}")

    # Initialize service
    extraction_service = ExtractionService(db)

    # Retrieve extraction
    extraction = await extraction_service.get_extraction_by_id(extraction_id)

    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction not found: {extraction_id}",
        )

    # Convert to response
    response = ExtractionResponse.from_orm_model(extraction)

    return response


@router.post(
    "/extractions/{extraction_id}/submit",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit extraction with optional corrections",
    description=(
        "Submit reviewed extraction data with optional field corrections. "
        "Handles both simple approval (no corrections) and approval with inline edits. "
        "Corrections are dual-written: stored in corrections table for ML metrics "
        "and applied to extractions table as source of truth. "
        "Transaction is atomic - all corrections applied or none."
    ),
    responses={
        200: {
            "description": "Extraction submitted successfully",
            "model": ExtractionResponse,
        },
        404: {
            "description": "Extraction not found",
            "model": ErrorResponse,
        },
        400: {
            "description": "Extraction already submitted or validation error",
            "model": ErrorResponse,
        },
    },
)
async def submit_extraction(
    extraction_id: UUID,
    request: ExtractionSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit extraction with optional corrections.

    Flow:
    1. Validate extraction exists and is pending
    2. Apply any corrections (dual-write to corrections table and extraction fields)
    3. Update status to 'approved'
    4. Return updated extraction

    Args:
        extraction_id: Extraction UUID
        request: Submit request with optional corrections
        db: Database session (injected)

    Returns:
        ExtractionResponse with updated values and corrections applied

    Raises:
        HTTPException 404: If extraction not found
        HTTPException 400: If extraction already submitted or validation error
    """
    logger.info(
        f"POST /extractions/{extraction_id}/submit - " f"corrections: {len(request.corrections)}"
    )

    # Initialize service
    extraction_service = ExtractionService(db)

    try:
        # Submit extraction (with or without corrections)
        extraction = await extraction_service.submit_extraction(
            extraction_id=extraction_id,
            corrections=request.corrections,
            notes=request.notes,
            submitted_by=None,  # TODO: Get from auth context in Phase 2
        )

        # Convert to response
        response = ExtractionResponse.from_orm_model(extraction)

        logger.info(
            f"Extraction {extraction_id} submitted successfully "
            f"(corrections applied: {len(request.corrections)})"
        )

        return response

    except ExtractionServiceError as e:
        # Check if not found vs already submitted
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        else:
            # Already submitted or validation error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

    except Exception as e:
        logger.error(f"Unexpected error submitting extraction {extraction_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
