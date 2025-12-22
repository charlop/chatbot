"""
API endpoints for managing state validation rules.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from uuid import UUID
from typing import List
from datetime import date

from app.database import get_db
from app.repositories.state_rule_repository import StateRuleRepository
from app.schemas.requests import StateRuleCreateRequest, StateRuleUpdateRequest
from app.schemas.responses import (
    JurisdictionResponse,
    StateRuleResponse,
)
from app.models.database import Jurisdiction, StateValidationRule

router = APIRouter(prefix="/state-rules", tags=["State Rules"])


# ==========================================
# Jurisdiction Endpoints
# ==========================================


@router.get("/jurisdictions", response_model=List[JurisdictionResponse])
async def list_jurisdictions(active_only: bool = True, db: AsyncSession = Depends(get_db)):
    """
    List all jurisdictions.

    Args:
        active_only: If true, only return active jurisdictions

    Returns:
        List of jurisdictions

    Example:
        GET /state-rules/jurisdictions
        GET /state-rules/jurisdictions?active_only=false
    """
    repo = StateRuleRepository(db)
    jurisdictions = await repo.get_all_jurisdictions(active_only=active_only)

    return [
        JurisdictionResponse(
            jurisdiction_id=j.jurisdiction_id,
            jurisdiction_name=j.jurisdiction_name,
            country_code=j.country_code,
            state_code=j.state_code,
            is_active=j.is_active,
        )
        for j in jurisdictions
    ]


@router.get("/jurisdictions/{jurisdiction_id}", response_model=JurisdictionResponse)
async def get_jurisdiction(jurisdiction_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get a specific jurisdiction.

    Args:
        jurisdiction_id: Jurisdiction ID (e.g., "US-CA")

    Returns:
        Jurisdiction details

    Example:
        GET /state-rules/jurisdictions/US-CA
    """
    result = await db.execute(
        select(Jurisdiction).where(Jurisdiction.jurisdiction_id == jurisdiction_id)
    )
    jurisdiction = result.scalar_one_or_none()

    if not jurisdiction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jurisdiction {jurisdiction_id} not found",
        )

    return JurisdictionResponse(
        jurisdiction_id=jurisdiction.jurisdiction_id,
        jurisdiction_name=jurisdiction.jurisdiction_name,
        country_code=jurisdiction.country_code,
        state_code=jurisdiction.state_code,
        is_active=jurisdiction.is_active,
    )


# ==========================================
# State Rules Endpoints
# ==========================================


@router.get("/jurisdictions/{jurisdiction_id}/rules", response_model=List[StateRuleResponse])
async def get_jurisdiction_rules(
    jurisdiction_id: str,
    active_only: bool = True,
    as_of_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all rules for a jurisdiction.

    Args:
        jurisdiction_id: Jurisdiction ID (e.g., "US-CA")
        active_only: If true, only return active rules
        as_of_date: Get rules effective on this date (defaults to today)

    Returns:
        List of validation rules for the jurisdiction

    Example:
        GET /state-rules/jurisdictions/US-CA/rules
        GET /state-rules/jurisdictions/US-CA/rules?as_of_date=2024-01-01
    """
    if as_of_date is None:
        as_of_date = date.today()

    # Build query
    query = select(StateValidationRule).where(
        StateValidationRule.jurisdiction_id == jurisdiction_id
    )

    if active_only:
        query = query.where(
            and_(
                StateValidationRule.is_active == True,
                StateValidationRule.effective_date <= as_of_date,
                or_(
                    StateValidationRule.expiration_date.is_(None),
                    StateValidationRule.expiration_date > as_of_date,
                ),
            )
        )

    query = query.order_by(
        StateValidationRule.rule_category, StateValidationRule.effective_date.desc()
    )

    result = await db.execute(query)
    rules = result.scalars().all()

    return [
        StateRuleResponse(
            rule_id=rule.rule_id,
            jurisdiction_id=rule.jurisdiction_id,
            rule_category=rule.rule_category,
            rule_config=rule.rule_config,
            effective_date=rule.effective_date,
            expiration_date=rule.expiration_date,
            is_active=rule.is_active,
            rule_description=rule.rule_description,
            created_at=rule.created_at,
        )
        for rule in rules
    ]


@router.post("/rules", response_model=StateRuleResponse)
async def create_state_rule(
    rule_request: StateRuleCreateRequest,
    db: AsyncSession = Depends(get_db),
    # TODO: Add require_admin dependency when auth is implemented
    # current_user = Depends(require_admin)
):
    """
    Create a new state validation rule.

    NOTE: Currently no auth protection. Add admin role requirement when auth is implemented.

    Args:
        rule_request: Rule creation request

    Returns:
        Created rule

    Example:
        POST /state-rules/rules
        {
            "jurisdiction_id": "US-CA",
            "rule_category": "gap_premium",
            "rule_config": {"min": 200, "max": 1500, "strict": true},
            "effective_date": "2025-01-01",
            "rule_description": "California GAP premium limits"
        }
    """
    repo = StateRuleRepository(db)

    try:
        rule = await repo.create_rule(
            jurisdiction_id=rule_request.jurisdiction_id,
            rule_category=rule_request.rule_category,
            rule_config=rule_request.rule_config,
            effective_date=rule_request.effective_date,
            rule_description=rule_request.rule_description,
            created_by=None,  # TODO: Use current_user.user_id when auth is implemented
        )

        return StateRuleResponse(
            rule_id=rule.rule_id,
            jurisdiction_id=rule.jurisdiction_id,
            rule_category=rule.rule_category,
            rule_config=rule.rule_config,
            effective_date=rule.effective_date,
            expiration_date=rule.expiration_date,
            is_active=rule.is_active,
            rule_description=rule.rule_description,
            created_at=rule.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/rules/{rule_id}", response_model=StateRuleResponse)
async def update_state_rule(
    rule_id: UUID,
    rule_request: StateRuleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    # TODO: Add require_admin dependency when auth is implemented
    # current_user = Depends(require_admin)
):
    """
    Update a state rule by creating a new version.

    This maintains audit trail by expiring the old rule and creating a new one.

    NOTE: Currently no auth protection. Add admin role requirement when auth is implemented.

    Args:
        rule_id: ID of rule to update
        rule_request: Rule update request

    Returns:
        New rule version

    Example:
        PUT /state-rules/rules/{rule_id}
        {
            "rule_config": {"min": 250, "max": 1400, "strict": true},
            "effective_date": "2025-06-01",
            "rule_description": "Updated California GAP premium limits"
        }
    """
    repo = StateRuleRepository(db)

    try:
        new_rule = await repo.update_rule(
            old_rule_id=rule_id,
            new_rule_config=rule_request.rule_config,
            new_effective_date=rule_request.effective_date,
            rule_description=rule_request.rule_description,
            created_by=None,  # TODO: Use current_user.user_id when auth is implemented
        )

        return StateRuleResponse(
            rule_id=new_rule.rule_id,
            jurisdiction_id=new_rule.jurisdiction_id,
            rule_category=new_rule.rule_category,
            rule_config=new_rule.rule_config,
            effective_date=new_rule.effective_date,
            expiration_date=new_rule.expiration_date,
            is_active=new_rule.is_active,
            rule_description=new_rule.rule_description,
            created_at=new_rule.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/rules/{rule_id}", response_model=StateRuleResponse)
async def get_rule(rule_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get a specific rule by ID.

    Args:
        rule_id: Rule ID

    Returns:
        Rule details

    Example:
        GET /state-rules/rules/{rule_id}
    """
    rule = await db.get(StateValidationRule, rule_id)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule {rule_id} not found"
        )

    return StateRuleResponse(
        rule_id=rule.rule_id,
        jurisdiction_id=rule.jurisdiction_id,
        rule_category=rule.rule_category,
        rule_config=rule.rule_config,
        effective_date=rule.effective_date,
        expiration_date=rule.expiration_date,
        is_active=rule.is_active,
        rule_description=rule.rule_description,
        created_at=rule.created_at,
    )
