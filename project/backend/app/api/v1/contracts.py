"""
Contract Template API endpoints for searching and retrieving contract templates.
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
    summary="Search for a contract template",
    description=(
        "Search for a contract template by account number OR template ID. "
        "Account number search uses hybrid cache strategy (Redis → DB → External API). "
        "Returns template metadata if found, 404 if not found."
    ),
    responses={
        200: {
            "description": "Contract template found",
            "model": ContractResponse,
        },
        404: {
            "description": "Contract template not found",
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
    Search for a contract template by account number or template ID.

    **Account Number Search Flow (Hybrid Cache):**
    1. Check Redis cache (fast path)
    2. Check account_mappings table (DB cache)
    3. Call external API (fallback)
    4. Cache result in Redis + DB
    5. Fetch template details

    **Template ID Search Flow:**
    1. Direct database lookup
    2. Cache template in Redis

    Args:
        search_request: Search request with account_number OR contract_id
        db: Database session (injected)

    Returns:
        ContractResponse with template metadata

    Raises:
        HTTPException 404: If template not found
        HTTPException 400: If search parameters are invalid
    """
    # Build log message based on search type
    if search_request.account_number:
        search_param = f"account_number: {search_request.account_number}"
    else:
        search_param = f"contract_id: {search_request.contract_id}"

    logger.info(f"POST /contracts/search - {search_param}")

    # Initialize service
    contract_service = ContractService(db)

    # Search for template
    template = await contract_service.search_contract(search_request)

    if not template:
        if search_request.account_number:
            detail = (
                f"No contract template found for account number: {search_request.account_number}"
            )
        else:
            detail = f"Contract template not found: {search_request.contract_id}"

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )

    return template


@router.get(
    "/contracts/{contract_id}",
    response_model=ContractResponse,
    status_code=status.HTTP_200_OK,
    summary="Get contract template by ID",
    description=(
        "Retrieve a contract template by its ID. "
        "Includes extraction data if available. "
        "Returns 404 if template not found."
    ),
    responses={
        200: {
            "description": "Contract template found",
            "model": ContractResponse,
        },
        404: {
            "description": "Contract template not found",
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
    Retrieve a contract template by ID.

    Args:
        contract_id: Contract template ID
        include_extraction: Whether to include extraction data (default: True)
        db: Database session (injected)

    Returns:
        ContractResponse with template metadata and optional extraction

    Raises:
        HTTPException 404: If template not found
    """
    logger.info(f"GET /contracts/{contract_id} - include_extraction: {include_extraction}")

    # Initialize service
    contract_service = ContractService(db)

    # Retrieve template
    template = await contract_service.get_template_by_id(contract_id, include_extraction)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract template not found: {contract_id}",
        )

    return template


@router.get(
    "/contracts/{contract_id}/pdf",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
    summary="Stream contract template PDF",
    description=(
        "Stream contract template PDF from S3 with IAM authentication. "
        "PDFs are cached in Redis for 15 minutes. "
        "Returns PDF binary stream with content-type: application/pdf. "
        "Returns 404 if template or PDF not found."
    ),
    responses={
        200: {
            "description": "PDF stream",
            "content": {"application/pdf": {}},
        },
        404: {
            "description": "Contract template or PDF not found",
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
    Stream contract template PDF from S3.

    Flow:
    1. Query database for template and S3 location
    2. Check Redis cache for PDF
    3. If cache miss, fetch from S3 with IAM credentials
    4. Cache PDF in Redis (TTL: 15 minutes)
    5. Stream PDF to client

    Args:
        contract_id: Contract template ID
        db: Database session (injected)

    Returns:
        StreamingResponse with PDF binary stream

    Raises:
        HTTPException 404: If template or PDF not found
        HTTPException 403: If access to PDF is denied
        HTTPException 500: If S3 error occurs
    """
    logger.info(f"GET /contracts/{contract_id}/pdf - Streaming template PDF")

    # Get template from database to retrieve S3 location
    contract_service = ContractService(db)
    template = await contract_service.get_template_by_id(contract_id, include_extraction=False)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract template not found: {contract_id}",
        )

    # Get S3 location from template
    s3_bucket = template.s3_bucket
    s3_key = template.s3_key

    if not s3_bucket or not s3_key:
        logger.error(f"Template {contract_id} missing S3 location (bucket or key is null)")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template PDF location not configured",
        )

    # Stream PDF from S3 with caching
    s3_service = get_s3_service()

    try:
        pdf_bytes, cache_hit = await s3_service.get_pdf_stream(s3_bucket, s3_key)

        # Log cache status
        cache_status = "HIT" if cache_hit else "MISS"
        logger.info(
            f"Streaming PDF for template {contract_id} "
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
        logger.error(f"PDF not found in S3 for template {contract_id}: s3://{s3_bucket}/{s3_key}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF not found for template: {contract_id}",
        )

    except S3AccessDeniedError:
        logger.error(f"Access denied to PDF for template {contract_id}: s3://{s3_bucket}/{s3_key}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to PDF for template: {contract_id}",
        )

    except Exception as e:
        logger.error(f"Error streaming PDF for template {contract_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stream PDF",
        )
