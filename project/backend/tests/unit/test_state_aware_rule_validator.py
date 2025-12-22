"""
Unit tests for StateAwareRuleValidator.
"""

import pytest
from decimal import Decimal
from app.agents.tools.validators.state_aware_rule_validator import (
    StateAwareRuleValidator,
)
from app.agents.base import ToolContext, ToolStatus
from app.repositories.state_rule_repository import StateRuleRepository


@pytest.fixture
async def test_contract_with_jurisdiction(db_session, test_contract):
    """Create a test contract with California jurisdiction."""
    repo = StateRuleRepository(db_session)

    # Map contract to California
    await repo.create_contract_jurisdiction_mapping(
        contract_id=test_contract.contract_id,
        jurisdiction_id="US-CA",
        is_primary=True,
    )

    await db_session.flush()  # Ensure mapping is visible in this transaction
    return test_contract


@pytest.mark.asyncio
async def test_numeric_validation_pass(db_session, test_contract_with_jurisdiction):
    """Test numeric validation passes within range."""
    validator = StateAwareRuleValidator(db_session)

    # Create context with GAP premium value in CA range ($200-$1500)
    context = ToolContext(
        field_name="gap_premium",
        field_value=Decimal("500.00"),
        field_confidence=None,
        field_source=None,
        contract_id=test_contract_with_jurisdiction.contract_id,
    )

    result = await validator.execute(context)

    assert result.status == ToolStatus.PASS
    assert "US-CA" in result.message


@pytest.mark.asyncio
async def test_numeric_validation_fail(db_session, test_contract_with_jurisdiction):
    """Test numeric validation fails outside range."""
    validator = StateAwareRuleValidator(db_session)

    # Create context with value outside CA range (max is $1500)
    context = ToolContext(
        field_name="gap_premium",
        field_value=Decimal("5000.00"),
        field_confidence=None,
        field_source=None,
        contract_id=test_contract_with_jurisdiction.contract_id,
    )

    result = await validator.execute(context)

    # California rule is strict=true, so should FAIL
    assert result.status == ToolStatus.FAIL
    assert "US-CA" in result.message


@pytest.mark.asyncio
async def test_federal_default_fallback(db_session, test_contract):
    """Test fallback to federal default when no jurisdiction mapped."""
    validator = StateAwareRuleValidator(db_session)

    # Create context for contract with no jurisdiction mapping
    context = ToolContext(
        field_name="gap_premium",
        field_value=Decimal("1000.00"),
        field_confidence=None,
        field_source=None,
        contract_id=test_contract.contract_id,
    )

    result = await validator.execute(context)

    # Should use federal default rules
    assert result.status == ToolStatus.PASS


@pytest.mark.asyncio
async def test_value_list_validation(db_session):
    """Test value list validation for refund methods."""
    import uuid

    validator = StateAwareRuleValidator(db_session)
    repo = StateRuleRepository(db_session)

    # Create test contract with NY jurisdiction (prohibits Rule of 78s)
    from app.models.database.contract import Contract

    contract_id = f"TEST-NY-{str(uuid.uuid4())[:8]}"
    contract = Contract(
        contract_id=contract_id,
        s3_bucket="test",
        s3_key="test.pdf",
        contract_type="GAP",
    )
    db_session.add(contract)
    await db_session.flush()

    await repo.create_contract_jurisdiction_mapping(
        contract_id=contract_id, jurisdiction_id="US-NY", is_primary=True
    )
    await db_session.flush()

    # Test allowed value (Pro-rata)
    context = ToolContext(
        field_name="refund_method",
        field_value="Pro-Rata",
        field_confidence=None,
        field_source=None,
        contract_id=contract_id,
    )

    result = await validator.execute(context)
    assert result.status == ToolStatus.PASS

    # Test prohibited value (Rule of 78s)
    context.field_value = "Rule of 78s"
    result = await validator.execute(context)
    assert result.status == ToolStatus.FAIL
    assert "prohibited" in result.message.lower()
