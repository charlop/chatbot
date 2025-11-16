"""
Contract API endpoints for searching and retrieving contract information.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.requests import ContractSearchRequest
from app.schemas.responses import ContractResponse, ErrorResponse
from app.services.contract_service import ContractService
from app.services.s3_service import get_s3_service, S3ObjectNotFoundError, S3AccessDeniedError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/contracts/search",
    response_model=ContractResponse,
    status_code=status.HTTP_200_OK,
    summary="Search for a contract",
    description=(
        "Search for a contract by account number. "
        "Returns contract metadata if found, 404 if not found."
    ),
    responses={
        200: {
            "description": "Contract found",
            "model": ContractResponse,
        },
        404: {
            "description": "Contract not found",
            "model": ErrorResponse,
        },
        400: {
            "description": "Invalid request",
            "model": ErrorResponse,
        },
    },
)
async def search_contract(
    search_request: ContractSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Search for a contract by account number.

    Flow:
    1. Validate account number
    2. Check cache (Redis) for contract
    3. Query database for contract
    4. If not found, query external RDB (mocked for now)
    5. Store in database if found externally
    6. Log audit event
    7. Return contract metadata

    Args:
        search_request: Contract search request with account number
        db: Database session (injected)

    Returns:
        ContractResponse with contract metadata

    Raises:
        HTTPException 404: If contract not found
        HTTPException 400: If account number is invalid
    """
    logger.info(f"POST /contracts/search - account_number: {search_request.account_number}")

    # Initialize service
    contract_service = ContractService(db)

    # Search for contract
    contract = await contract_service.search_contract(search_request)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract not found for account number: {search_request.account_number}",
        )

    return contract


@router.get(
    "/contracts/{contract_id}",
    response_model=ContractResponse,
    status_code=status.HTTP_200_OK,
    summary="Get contract by ID",
    description=(
        "Retrieve a contract by its ID. "
        "Includes extraction data if available. "
        "Returns 404 if contract not found."
    ),
    responses={
        200: {
            "description": "Contract found",
            "model": ContractResponse,
        },
        404: {
            "description": "Contract not found",
            "model": ErrorResponse,
        },
    },
)
async def get_contract(
    contract_id: str,
    include_extraction: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a contract by ID.

    Args:
        contract_id: Contract ID
        include_extraction: Whether to include extraction data (default: True)
        db: Database session (injected)

    Returns:
        ContractResponse with contract metadata and optional extraction

    Raises:
        HTTPException 404: If contract not found
    """
    logger.info(f"GET /contracts/{contract_id} - include_extraction: {include_extraction}")

    # Initialize service
    contract_service = ContractService(db)

    # Retrieve contract
    contract = await contract_service.get_contract(contract_id, include_extraction)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract not found: {contract_id}",
        )

    return contract


@router.get(
    "/contracts/{contract_id}/pdf",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
    summary="Stream contract PDF",
    description=(
        "Stream contract PDF from S3 with IAM authentication. "
        "PDFs are cached in Redis for 15 minutes. "
        "Returns PDF binary stream with content-type: application/pdf. "
        "Returns 404 if contract or PDF not found."
    ),
    responses={
        200: {
            "description": "PDF stream",
            "content": {"application/pdf": {}},
        },
        404: {
            "description": "Contract or PDF not found",
            "model": ErrorResponse,
        },
        403: {
            "description": "Access denied to PDF",
            "model": ErrorResponse,
        },
    },
)
async def stream_contract_pdf(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Stream contract PDF from S3.

    Flow:
    1. Query database for contract and S3 location
    2. Check Redis cache for PDF
    3. If cache miss, fetch from S3 with IAM credentials
    4. Cache PDF in Redis (TTL: 15 minutes)
    5. Stream PDF to client

    Args:
        contract_id: Contract ID
        db: Database session (injected)

    Returns:
        StreamingResponse with PDF binary stream

    Raises:
        HTTPException 404: If contract or PDF not found
        HTTPException 403: If access to PDF is denied
        HTTPException 500: If S3 error occurs
    """
    logger.info(f"GET /contracts/{contract_id}/pdf - Streaming PDF")

    # Get contract from database to retrieve S3 location
    contract_service = ContractService(db)
    contract = await contract_service.get_contract(contract_id, include_extraction=False)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract not found: {contract_id}",
        )

    # Get S3 location from contract
    s3_bucket = contract.s3_bucket
    s3_key = contract.s3_key

    if not s3_bucket or not s3_key:
        logger.error(f"Contract {contract_id} missing S3 location (bucket or key is null)")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Contract PDF location not configured",
        )

    # Stream PDF from S3 with caching
    s3_service = get_s3_service()

    try:
        pdf_bytes, cache_hit = await s3_service.get_pdf_stream(s3_bucket, s3_key)

        # Log cache status
        cache_status = "HIT" if cache_hit else "MISS"
        logger.info(
            f"Streaming PDF for contract {contract_id} "
            f"(s3://{s3_bucket}/{s3_key}, cache: {cache_status})"
        )

        # Return streaming response
        import io

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="contract-{contract_id}.pdf"',
                "Cache-Control": "private, max-age=900",  # 15 minutes
                "X-Cache-Status": cache_status,
            },
        )

    except S3ObjectNotFoundError:
        logger.error(f"PDF not found in S3 for contract {contract_id}: s3://{s3_bucket}/{s3_key}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF not found for contract: {contract_id}",
        )

    except S3AccessDeniedError:
        logger.error(f"Access denied to PDF for contract {contract_id}: s3://{s3_bucket}/{s3_key}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to PDF for contract: {contract_id}",
        )

    except Exception as e:
        logger.error(f"Error streaming PDF for contract {contract_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stream PDF",
        )
