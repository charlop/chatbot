"""
End-to-end tests for state rules admin API.

This test suite verifies admin functionality for managing state validation rules.
"""

import pytest
from httpx import AsyncClient
from datetime import date

from app.main import app


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_list_all_jurisdictions():
    """
    Test listing all available jurisdictions.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/state-rules/jurisdictions")

        assert response.status_code == 200
        jurisdictions = response.json()

        # Should have at least 51 jurisdictions (50 states + federal)
        assert len(jurisdictions) >= 51

        # Verify structure
        ca = next((j for j in jurisdictions if j["jurisdiction_id"] == "US-CA"), None)
        assert ca is not None
        assert ca["jurisdiction_name"] == "California"
        assert ca["state_code"] == "CA"
        assert ca["country_code"] == "US"
        assert ca["is_active"] is True


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_specific_jurisdiction():
    """
    Test getting details for a specific jurisdiction.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/state-rules/jurisdictions/US-CA")

        assert response.status_code == 200
        jurisdiction = response.json()

        assert jurisdiction["jurisdiction_id"] == "US-CA"
        assert jurisdiction["jurisdiction_name"] == "California"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_rules_for_jurisdiction():
    """
    Test getting all rules for a specific jurisdiction.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/state-rules/jurisdictions/US-CA/rules")

        assert response.status_code == 200
        rules = response.json()

        # Should have rules for different categories
        assert isinstance(rules, list)

        if len(rules) > 0:
            # Verify rule structure
            rule = rules[0]
            assert "rule_id" in rule
            assert "jurisdiction_id" in rule
            assert "rule_category" in rule
            assert "rule_config" in rule
            assert "effective_date" in rule


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_create_new_state_rule():
    """
    Test creating a new state validation rule.

    Note: In production, this would require admin authentication.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        new_rule = {
            "jurisdiction_id": "US-TX",
            "rule_category": "cancellation_fee",
            "rule_config": {"min": 0, "max": 50, "strict": False, "warning_threshold": 40},
            "effective_date": "2026-01-01",
            "rule_description": "Texas cancellation fee limits - test rule",
        }

        response = await client.post("/api/v1/state-rules/rules", json=new_rule)

        assert response.status_code == 200
        created_rule = response.json()

        assert created_rule["jurisdiction_id"] == "US-TX"
        assert created_rule["rule_category"] == "cancellation_fee"
        assert created_rule["rule_config"]["min"] == 0
        assert created_rule["rule_config"]["max"] == 50
        assert "rule_id" in created_rule


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_update_existing_rule():
    """
    Test updating an existing rule (creates new version).
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First, get existing rules for US-FEDERAL
        list_response = await client.get("/api/v1/state-rules/jurisdictions/US-FEDERAL/rules")
        assert list_response.status_code == 200

        rules = list_response.json()
        if len(rules) == 0:
            pytest.skip("No federal rules to update")

        rule_id = rules[0]["rule_id"]

        # Update the rule
        update_data = {
            "rule_config": {"min": 150, "max": 2500, "strict": True},
            "effective_date": "2026-06-01",
            "rule_description": "Updated federal rule - E2E test",
        }

        response = await client.put(f"/api/v1/state-rules/rules/{rule_id}", json=update_data)

        assert response.status_code == 200
        updated_rule = response.json()

        # New rule should have different ID (new version)
        assert updated_rule["rule_id"] != rule_id
        # But same jurisdiction and category
        assert updated_rule["jurisdiction_id"] == rules[0]["jurisdiction_id"]
        assert updated_rule["rule_category"] == rules[0]["rule_category"]
        # Updated config
        assert updated_rule["rule_config"]["min"] == 150


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_invalid_rule_category():
    """
    Test that creating rule with invalid category returns 422.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        invalid_rule = {
            "jurisdiction_id": "US-CA",
            "rule_category": "invalid_category",
            "rule_config": {"min": 100},
            "effective_date": "2025-01-01",
        }

        response = await client.post("/api/v1/state-rules/rules", json=invalid_rule)

        assert response.status_code == 422  # Validation error


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_rule_versioning():
    """
    Test that rule versioning works correctly.

    When a rule is updated:
    1. Old rule is expired
    2. New rule is created with new effective date
    3. Both rules exist in database
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create initial rule
        initial_rule = {
            "jurisdiction_id": "US-CA",
            "rule_category": "gap_premium",
            "rule_config": {"min": 200, "max": 1500},
            "effective_date": "2025-01-01",
            "rule_description": "Version 1",
        }

        create_response = await client.post("/api/v1/state-rules/rules", json=initial_rule)
        assert create_response.status_code == 200
        rule_v1 = create_response.json()

        # Update to create version 2
        update_data = {
            "rule_config": {"min": 250, "max": 1400},
            "effective_date": "2025-07-01",
            "rule_description": "Version 2 - updated limits",
        }

        update_response = await client.put(
            f"/api/v1/state-rules/rules/{rule_v1['rule_id']}", json=update_data
        )
        assert update_response.status_code == 200
        rule_v2 = update_response.json()

        # Version 2 should have different ID
        assert rule_v2["rule_id"] != rule_v1["rule_id"]

        # Version 2 should have updated config
        assert rule_v2["rule_config"]["min"] == 250

        # Both versions should be retrievable individually
        v1_response = await client.get(f"/api/v1/state-rules/rules/{rule_v1['rule_id']}")
        assert v1_response.status_code == 200

        v2_response = await client.get(f"/api/v1/state-rules/rules/{rule_v2['rule_id']}")
        assert v2_response.status_code == 200
