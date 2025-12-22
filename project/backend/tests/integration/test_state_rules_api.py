"""
Integration tests for State Rules API endpoints.
"""

import pytest
from httpx import AsyncClient
from datetime import date

from app.main import app


@pytest.fixture
async def client():
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_list_jurisdictions(client):
    """Test listing all jurisdictions."""
    response = await client.get("/api/v1/state-rules/jurisdictions")

    assert response.status_code == 200
    jurisdictions = response.json()
    assert len(jurisdictions) >= 51  # At least 50 states + federal

    # Check California exists
    ca = next((j for j in jurisdictions if j.get("state_code") == "CA"), None)
    assert ca is not None
    assert ca["jurisdiction_name"] == "California"
    assert ca["jurisdiction_id"] == "US-CA"


@pytest.mark.asyncio
async def test_get_jurisdiction(client):
    """Test getting a specific jurisdiction."""
    response = await client.get("/api/v1/state-rules/jurisdictions/US-CA")

    assert response.status_code == 200
    jurisdiction = response.json()
    assert jurisdiction["jurisdiction_id"] == "US-CA"
    assert jurisdiction["state_code"] == "CA"
    assert jurisdiction["jurisdiction_name"] == "California"


@pytest.mark.asyncio
async def test_get_jurisdiction_not_found(client):
    """Test getting non-existent jurisdiction returns 404."""
    response = await client.get("/api/v1/state-rules/jurisdictions/US-INVALID")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_jurisdiction_rules(client):
    """Test getting rules for a jurisdiction."""
    response = await client.get("/api/v1/state-rules/jurisdictions/US-CA/rules")

    assert response.status_code == 200
    rules = response.json()
    assert len(rules) > 0

    # Check for GAP premium rule
    gap_rule = next((r for r in rules if r["rule_category"] == "gap_premium"), None)
    assert gap_rule is not None
    assert "min" in gap_rule["rule_config"]
    assert "max" in gap_rule["rule_config"]
    assert gap_rule["jurisdiction_id"] == "US-CA"


@pytest.mark.asyncio
async def test_get_jurisdiction_rules_with_date(client):
    """Test getting rules for a specific date."""
    response = await client.get(
        "/api/v1/state-rules/jurisdictions/US-CA/rules",
        params={"as_of_date": "2025-01-01"},
    )

    assert response.status_code == 200
    rules = response.json()
    assert isinstance(rules, list)


@pytest.mark.asyncio
async def test_create_rule(client):
    """Test creating a new rule."""
    new_rule = {
        "jurisdiction_id": "US-FEDERAL",
        "rule_category": "gap_premium",
        "rule_config": {"min": 150, "max": 2500, "strict": True},
        "effective_date": "2026-01-01",
        "rule_description": "Test rule creation",
    }

    response = await client.post("/api/v1/state-rules/rules", json=new_rule)

    assert response.status_code == 200
    created_rule = response.json()
    assert created_rule["jurisdiction_id"] == "US-FEDERAL"
    assert created_rule["rule_category"] == "gap_premium"
    assert created_rule["rule_config"]["min"] == 150
    assert "rule_id" in created_rule


@pytest.mark.asyncio
async def test_create_rule_invalid_category(client):
    """Test creating a rule with invalid category returns 400."""
    invalid_rule = {
        "jurisdiction_id": "US-CA",
        "rule_category": "invalid_category",
        "rule_config": {"min": 100},
        "effective_date": "2025-01-01",
    }

    response = await client.post("/api/v1/state-rules/rules", json=invalid_rule)

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_rule_by_id(client):
    """Test getting a specific rule by ID."""
    # First, get the list of rules to get a valid rule ID
    list_response = await client.get("/api/v1/state-rules/jurisdictions/US-CA/rules")
    rules = list_response.json()
    assert len(rules) > 0

    rule_id = rules[0]["rule_id"]

    # Now get that specific rule
    response = await client.get(f"/api/v1/state-rules/rules/{rule_id}")

    assert response.status_code == 200
    rule = response.json()
    assert rule["rule_id"] == rule_id
    assert rule["jurisdiction_id"] == "US-CA"


@pytest.mark.asyncio
async def test_get_rule_not_found(client):
    """Test getting non-existent rule returns 404."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/state-rules/rules/{fake_uuid}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_rule_creates_version(client):
    """Test updating a rule creates a new version."""
    # First, get an existing rule
    list_response = await client.get("/api/v1/state-rules/jurisdictions/US-FEDERAL/rules")
    rules = list_response.json()
    assert len(rules) > 0
    old_rule = rules[0]

    # Update the rule
    update_data = {
        "rule_config": {"min": 200, "max": 3000, "strict": True},
        "effective_date": "2026-06-01",
        "rule_description": "Updated test rule",
    }

    response = await client.put(
        f"/api/v1/state-rules/rules/{old_rule['rule_id']}", json=update_data
    )

    assert response.status_code == 200
    new_rule = response.json()

    # New rule should have different ID
    assert new_rule["rule_id"] != old_rule["rule_id"]
    # Same jurisdiction and category
    assert new_rule["jurisdiction_id"] == old_rule["jurisdiction_id"]
    assert new_rule["rule_category"] == old_rule["rule_category"]
    # Updated config
    assert new_rule["rule_config"]["min"] == 200
    assert new_rule["rule_config"]["max"] == 3000


@pytest.mark.asyncio
async def test_update_nonexistent_rule(client):
    """Test updating non-existent rule returns 404."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    update_data = {
        "rule_config": {"min": 200},
        "effective_date": "2026-06-01",
    }

    response = await client.put(f"/api/v1/state-rules/rules/{fake_uuid}", json=update_data)

    assert response.status_code == 404
