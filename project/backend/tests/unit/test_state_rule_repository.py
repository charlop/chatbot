"""
Unit tests for StateRuleRepository.
"""

import pytest
from datetime import date
from app.repositories.state_rule_repository import StateRuleRepository


@pytest.mark.asyncio
async def test_get_active_rules_for_jurisdiction(db_session):
    """Test getting active rules for a jurisdiction."""
    repo = StateRuleRepository(db_session)

    # Test getting California GAP premium rule (from seed data)
    rule = await repo.get_active_rules_for_jurisdiction("US-CA", "gap_premium")

    assert rule is not None
    assert rule.jurisdiction_id == "US-CA"
    assert rule.rule_category == "gap_premium"
    assert "min" in rule.rule_config
    assert "max" in rule.rule_config
    assert rule.rule_config["min"] == 200
    assert rule.rule_config["max"] == 1500


@pytest.mark.asyncio
async def test_get_active_rules_federal_default(db_session):
    """Test getting federal default rules."""
    repo = StateRuleRepository(db_session)

    # Test getting federal GAP premium rule
    rule = await repo.get_active_rules_for_jurisdiction("US-FEDERAL", "gap_premium")

    assert rule is not None
    assert rule.jurisdiction_id == "US-FEDERAL"
    assert rule.rule_category == "gap_premium"
    assert rule.rule_config["min"] == 100
    assert rule.rule_config["max"] == 2000


@pytest.mark.asyncio
async def test_get_all_jurisdictions(db_session):
    """Test getting all jurisdictions."""
    repo = StateRuleRepository(db_session)

    jurisdictions = await repo.get_all_jurisdictions()

    # Should have 51 jurisdictions (50 states + federal)
    assert len(jurisdictions) >= 51

    # Check that California exists
    ca = next((j for j in jurisdictions if j.state_code == "CA"), None)
    assert ca is not None
    assert ca.jurisdiction_name == "California"


@pytest.mark.asyncio
async def test_get_jurisdiction_by_state_code(db_session):
    """Test getting jurisdiction by state code."""
    repo = StateRuleRepository(db_session)

    ca = await repo.get_jurisdiction_by_state_code("CA")

    assert ca is not None
    assert ca.jurisdiction_id == "US-CA"
    assert ca.state_code == "CA"
    assert ca.jurisdiction_name == "California"


@pytest.mark.asyncio
async def test_create_contract_jurisdiction_mapping(db_session, test_contract):
    """Test creating contract-jurisdiction mapping."""
    repo = StateRuleRepository(db_session)

    # Create mapping
    mapping = await repo.create_contract_jurisdiction_mapping(
        contract_id=test_contract.contract_id,
        jurisdiction_id="US-CA",
        is_primary=True,
    )

    await db_session.flush()  # Ensure changes are visible in this transaction

    assert mapping is not None
    assert mapping.contract_id == test_contract.contract_id
    assert mapping.jurisdiction_id == "US-CA"
    assert mapping.is_primary is True

    # Verify we can retrieve it
    jurisdictions = await repo.get_jurisdictions_for_contract(test_contract.contract_id)
    assert len(jurisdictions) == 1
    assert jurisdictions[0].jurisdiction_id == "US-CA"
