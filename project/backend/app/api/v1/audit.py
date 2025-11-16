"""
Audit API endpoints for querying audit trails.
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.responses import AuditEventResponse, ErrorResponse
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/audit/contract/{contract_id}",
    response_model=List[AuditEventResponse],
    status_code=status.HTTP_200_OK,
    summary="Get audit trail for contract",
    description=(
        "Retrieve full audit history for a specific contract. "
        "Includes all events: search, view, extract, submit, chat. "
        "Results ordered by timestamp descending (most recent first)."
    ),
    responses={
        200: {
            "description": "Audit trail retrieved successfully",
            "model": List[AuditEventResponse],
        },
        404: {
            "description": "Contract not found or no audit events",
            "model": ErrorResponse,
        },
    },
)
async def get_contract_audit_trail(
    contract_id: str,
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=100, ge=1, le=500, description="Pagination limit"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get full audit trail for a contract.

    Args:
        contract_id: Contract ID
        offset: Pagination offset (default: 0)
        limit: Pagination limit (default: 100, max: 500)
        db: Database session (injected)

    Returns:
        List of AuditEventResponse ordered by timestamp descending

    Raises:
        HTTPException 404: If no audit events found
    """
    logger.info(f"GET /audit/contract/{contract_id} (offset={offset}, limit={limit})")

    # Initialize service
    audit_service = AuditService(db)

    # Get audit trail
    events = await audit_service.get_contract_history(
        contract_id=contract_id,
        offset=offset,
        limit=limit,
    )

    if not events and offset == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit events found for contract: {contract_id}",
        )

    # Convert to responses
    responses = [AuditEventResponse.model_validate(event) for event in events]

    logger.info(f"Retrieved {len(responses)} audit events for contract {contract_id}")

    return responses


@router.get(
    "/audit/extraction/{extraction_id}",
    response_model=List[AuditEventResponse],
    status_code=status.HTTP_200_OK,
    summary="Get audit trail for extraction",
    description=(
        "Retrieve full audit history for a specific extraction. "
        "Includes extract, submit, and related events. "
        "Results ordered by timestamp descending (most recent first)."
    ),
    responses={
        200: {
            "description": "Audit trail retrieved successfully",
            "model": List[AuditEventResponse],
        },
        404: {
            "description": "Extraction not found or no audit events",
            "model": ErrorResponse,
        },
    },
)
async def get_extraction_audit_trail(
    extraction_id: UUID,
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=100, ge=1, le=500, description="Pagination limit"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get full audit trail for an extraction.

    Args:
        extraction_id: Extraction UUID
        offset: Pagination offset (default: 0)
        limit: Pagination limit (default: 100, max: 500)
        db: Database session (injected)

    Returns:
        List of AuditEventResponse ordered by timestamp descending

    Raises:
        HTTPException 404: If no audit events found
    """
    logger.info(f"GET /audit/extraction/{extraction_id} (offset={offset}, limit={limit})")

    # Initialize service
    audit_service = AuditService(db)

    # Get audit trail
    events = await audit_service.get_extraction_history(
        extraction_id=extraction_id,
        offset=offset,
        limit=limit,
    )

    if not events and offset == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit events found for extraction: {extraction_id}",
        )

    # Convert to responses
    responses = [AuditEventResponse.model_validate(event) for event in events]

    logger.info(f"Retrieved {len(responses)} audit events for extraction {extraction_id}")

    return responses


@router.get(
    "/audit/recent",
    response_model=List[AuditEventResponse],
    status_code=status.HTTP_200_OK,
    summary="Get recent audit events",
    description=(
        "Retrieve recent audit events across all entities. "
        "Useful for monitoring and debugging. "
        "Results ordered by timestamp descending (most recent first)."
    ),
    responses={
        200: {
            "description": "Recent events retrieved successfully",
            "model": List[AuditEventResponse],
        },
    },
)
async def get_recent_audit_events(
    hours: int = Query(default=24, ge=1, le=168, description="Hours to look back"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=100, ge=1, le=500, description="Pagination limit"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get recent audit events.

    Args:
        hours: Number of hours to look back (default: 24, max: 168)
        offset: Pagination offset (default: 0)
        limit: Pagination limit (default: 100, max: 500)
        db: Database session (injected)

    Returns:
        List of AuditEventResponse ordered by timestamp descending
    """
    logger.info(f"GET /audit/recent (hours={hours}, offset={offset}, limit={limit})")

    # Initialize service
    audit_service = AuditService(db)

    # Get recent events
    events = await audit_service.get_recent_events(
        hours=hours,
        offset=offset,
        limit=limit,
    )

    # Convert to responses
    responses = [AuditEventResponse.model_validate(event) for event in events]

    logger.info(f"Retrieved {len(responses)} recent audit events (last {hours} hours)")

    return responses
