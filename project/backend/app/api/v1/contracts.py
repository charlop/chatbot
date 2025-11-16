"""
Contract API endpoints for searching and retrieving contract information.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.requests import ContractSearchRequest
from app.schemas.responses import ContractResponse, ErrorResponse
from app.services.contract_service import ContractService

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
