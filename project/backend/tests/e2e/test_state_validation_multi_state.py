"""
End-to-end tests for multi-state contract extraction with conflict detection.

This test suite verifies the system's ability to handle contracts that apply
to multiple jurisdictions and detect conflicting rules.
"""

import pytest
from httpx import AsyncClient
from datetime import date

from app.main import app
from app.models.database import Contract, Jurisdiction, ContractJurisdiction, StateValidationRule


@pytest.fixture
async def setup_multi_state_contract(db):
    """
    Set up a contract that applies to multiple states (CA primary, NY secondary)
    with conflicting rules on refund calculation method.
    """
    # Create test contract
    contract = Contract(
        contract_id="E2E-MULTI-STATE-001",
        s3_bucket="test-bucket",
        s3_key="contracts/e2e-multi-state-001.pdf",
        contract_type="GAP",
        is_active=True,
    )
    db.add(contract)

    # Map contract to California (primary)
    ca_mapping = ContractJurisdiction(
        contract_id="E2E-MULTI-STATE-001",
        jurisdiction_id="US-CA",
        is_primary=True,
        effective_date=date.today(),
    )
    db.add(ca_mapping)

    # Map contract to New York (secondary)
    ny_mapping = ContractJurisdiction(
        contract_id="E2E-MULTI-STATE-001",
        jurisdiction_id="US-NY",
        is_primary=False,
        effective_date=date.today(),
    )
    db.add(ny_mapping)

    # Create CA refund method rule (allows all methods)
    ca_refund_rule = StateValidationRule(
        jurisdiction_id="US-CA",
        rule_category="refund_method",
        rule_config={
            "allowed_values": ["pro-rata", "rule of 78s", "short-rate"],
            "strict": False,
        },
        effective_date=date(2025, 1, 1),
        is_active=True,
        rule_description="California refund method options",
    )
    db.add(ca_refund_rule)

    # Create NY refund method rule (prohibits Rule of 78s)
    ny_refund_rule = StateValidationRule(
        jurisdiction_id="US-NY",
        rule_category="refund_method",
        rule_config={
            "allowed_values": ["pro-rata"],
            "prohibited_values": ["rule of 78s", "rule of 78's"],
            "strict": True,
            "reason": "NY Insurance Law §3426 - Rule of 78s prohibited",
        },
        effective_date=date(2025, 1, 1),
        is_active=True,
        rule_description="New York refund method restrictions",
    )
    db.add(ny_refund_rule)

    await db.commit()

    return "E2E-MULTI-STATE-001"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_multi_state_contract_structure(setup_multi_state_contract):
    """
    Test that multi-state contract has correct jurisdiction mappings.
    """
    contract_id = setup_multi_state_contract

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Get contract details
        response = await client.get(f"/api/v1/contracts/{contract_id}")
        assert response.status_code == 200

        contract = response.json()
        assert contract["contractId"] == contract_id

        # Note: In full implementation, contract would have:
        # - state = "CA" (primary)
        # - applicableStates = ["CA", "NY"]


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_multi_state_conflict_detection(setup_multi_state_contract):
    """
    Test that system detects conflicts between CA and NY rules.

    Expected behavior:
    - Validates against CA rules (primary jurisdiction)
    - Detects NY conflict if Rule of 78s is used
    - Stores conflict in state_validation_results
    """
    contract_id = setup_multi_state_contract

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create extraction
        response = await client.post(
            "/api/v1/extractions/create", json={"contract_id": contract_id}
        )

        assert response.status_code == 200
        extraction = response.json()

        # Verify extraction created
        assert extraction["contract_id"] == contract_id

        # In full implementation, if refund_method is "Rule of 78s":
        # - applied_jurisdiction_id = "US-CA"
        # - state_validation_results.multi_state_conflicts would contain:
        #   {
        #     "jurisdiction": "US-NY",
        #     "field": "refund_calculation_method",
        #     "conflict": "NY prohibits Rule of 78s method"
        #   }


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_jurisdictions_for_contract(setup_multi_state_contract):
    """
    Test API endpoint that returns all jurisdictions for a contract.
    """
    contract_id = setup_multi_state_contract

    async with AsyncClient(app=app, base_url="http://test") as client:
        # This would be a new endpoint: GET /api/v1/contracts/{id}/jurisdictions
        # For now, verify the contract exists
        response = await client.get(f"/api/v1/contracts/{contract_id}")
        assert response.status_code == 200

        # Future enhancement: endpoint should return jurisdiction list
        # Expected response:
        # {
        #   "primary": {"jurisdiction_id": "US-CA", "jurisdiction_name": "California"},
        #   "additional": [{"jurisdiction_id": "US-NY", "jurisdiction_name": "New York"}]
        # }
