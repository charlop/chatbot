"""
Integration tests for state-aware validation flow.
"""

import pytest
from decimal import Decimal
from app.agents.validation_agent import ValidationAgent
from app.agents.base import AgentContext
from app.repositories.state_rule_repository import StateRuleRepository


@pytest.mark.asyncio
async def test_validation_agent_with_state_rules(db_session, test_contract):
    """Test ValidationAgent uses StateAwareRuleValidator with state rules."""
    # Setup: Map contract to California
    repo = StateRuleRepository(db_session)
    await repo.create_contract_jurisdiction_mapping(
        contract_id=test_contract.contract_id,
        jurisdiction_id="US-CA",
        is_primary=True,
    )
    await db_session.flush()

    # Create validation agent
    agent = ValidationAgent(db_session)

    # Prepare extraction data (values within CA range)
    extraction_data = {
        "gap_insurance_premium": {
            "value": Decimal("500.00"),  # Within CA range $200-$1500
            "confidence": Decimal("95.0"),
            "source": {"page": 1},
        },
        "cancellation_fee": {
            "value": Decimal("50.00"),  # Within CA range $0-$75
            "confidence": Decimal("92.0"),
            "source": {"page": 2},
        },
        "refund_calculation_method": {
            "value": "Pro-rata",
            "confidence": Decimal("88.0"),
            "source": {"page": 3},
        },
    }

    # Create agent context
    context = AgentContext(
        contract_id=test_contract.contract_id,
        extraction_id="test-extraction-id",
        extraction_data=extraction_data,
        document_text="Test contract text",
    )

    # Execute validation
    result = await agent.execute(context)

    # Verify results
    assert result.overall_status in ["pass", "warning"]
    assert len(result.field_results) > 0

    # Check that state-aware validator ran
    state_aware_results = [
        r for r in result.field_results if r.get("tool_name") == "state_aware_rule_validator"
    ]
    assert len(state_aware_results) > 0

    # Verify jurisdiction context is included
    for r in state_aware_results:
        if r.get("status") == "pass":
            assert "US-CA" in r.get("message", "")


@pytest.mark.asyncio
async def test_validation_with_out_of_range_values(db_session, test_contract):
    """Test validation fails with out-of-range values."""
    # Setup: Map contract to California
    repo = StateRuleRepository(db_session)
    await repo.create_contract_jurisdiction_mapping(
        contract_id=test_contract.contract_id,
        jurisdiction_id="US-CA",
        is_primary=True,
    )
    await db_session.flush()

    agent = ValidationAgent(db_session)

    # Extraction data with value outside CA range
    extraction_data = {
        "gap_insurance_premium": {
            "value": Decimal("10000.00"),  # Exceeds CA max of $1500
            "confidence": Decimal("95.0"),
            "source": {"page": 1},
        },
        "cancellation_fee": {
            "value": Decimal("50.00"),
            "confidence": Decimal("92.0"),
            "source": {"page": 2},
        },
        "refund_calculation_method": {
            "value": "Pro-rata",
            "confidence": Decimal("88.0"),
            "source": {"page": 3},
        },
    }

    context = AgentContext(
        contract_id=test_contract.contract_id,
        extraction_id="test-extraction-id",
        extraction_data=extraction_data,
        document_text="Test contract text",
    )

    result = await agent.execute(context)

    # Should have failures due to out-of-range GAP premium
    assert result.overall_status in ["fail", "warning"]

    # Find the gap_premium validation result
    gap_results = [
        r
        for r in result.field_results
        if r.get("field_name") == "gap_insurance_premium"
        and r.get("tool_name") == "state_aware_rule_validator"
    ]
    assert len(gap_results) > 0
    assert gap_results[0].get("status") in ["fail", "warning"]
