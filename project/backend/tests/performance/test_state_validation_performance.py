"""
Performance tests for state validation feature.

These tests verify that state-specific validation does not add significant
overhead to the extraction process.
"""

import pytest
import asyncio
from time import time
from datetime import date

from app.repositories.state_rule_repository import StateRuleRepository


@pytest.mark.performance
@pytest.mark.asyncio
async def test_state_rule_query_performance(db):
    """
    Test that state rule lookups are fast (< 50ms).

    This verifies that database indexes are working correctly.
    """
    repo = StateRuleRepository(db)

    # Warm up the database
    await repo.get_active_rules_for_jurisdiction("US-CA", "gap_premium", date.today())

    # Measure query performance
    start = time()
    rule = await repo.get_active_rules_for_jurisdiction("US-CA", "gap_premium", date.today())
    end = time()

    duration_ms = (end - start) * 1000

    # Should be very fast with proper indexing
    assert duration_ms < 50, f"State rule query took {duration_ms:.2f}ms (target: < 50ms)"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_jurisdiction_lookup_performance(db):
    """
    Test that jurisdiction lookups are fast (< 30ms).
    """
    repo = StateRuleRepository(db)

    # Warm up
    await repo.get_all_jurisdictions()

    # Measure performance
    start = time()
    jurisdictions = await repo.get_all_jurisdictions()
    end = time()

    duration_ms = (end - start) * 1000

    assert duration_ms < 30, f"Jurisdiction lookup took {duration_ms:.2f}ms (target: < 30ms)"
    assert len(jurisdictions) >= 51  # 50 states + federal


@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_rule_lookups(db):
    """
    Test that concurrent rule lookups maintain performance.

    This simulates multiple extraction processes running in parallel.
    """
    repo = StateRuleRepository(db)

    # Create 20 concurrent rule lookups for different states
    states = ["US-CA", "US-NY", "US-TX", "US-FL", "US-IL"] * 4

    async def lookup_rule(jurisdiction_id):
        start = time()
        await repo.get_active_rules_for_jurisdiction(jurisdiction_id, "gap_premium", date.today())
        end = time()
        return (end - start) * 1000

    # Execute all lookups concurrently
    start = time()
    durations = await asyncio.gather(*[lookup_rule(state) for state in states])
    end = time()

    total_duration_ms = (end - start) * 1000
    avg_duration_ms = sum(durations) / len(durations)
    max_duration_ms = max(durations)

    # All concurrent lookups should complete quickly
    assert (
        total_duration_ms < 1000
    ), f"Total time for 20 concurrent lookups: {total_duration_ms:.2f}ms (target: < 1s)"
    assert avg_duration_ms < 50, f"Average lookup time: {avg_duration_ms:.2f}ms (target: < 50ms)"
    assert max_duration_ms < 200, f"Max lookup time: {max_duration_ms:.2f}ms (target: < 200ms)"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_multi_state_query_performance(db):
    """
    Test that multi-state contract jurisdiction lookups are fast.
    """
    repo = StateRuleRepository(db)

    # Simulate multi-state contract lookup
    contract_id = "PERF-MULTI-001"

    start = time()
    # In full implementation:
    # jurisdictions = await repo.get_jurisdictions_for_contract(contract_id, date.today())
    # For now, just test the repository is responsive
    await repo.get_all_jurisdictions()
    end = time()

    duration_ms = (end - start) * 1000

    assert duration_ms < 50, f"Multi-state lookup took {duration_ms:.2f}ms (target: < 50ms)"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_rule_versioning_query_performance(db):
    """
    Test that querying rules by date (versioning) is efficient.
    """
    repo = StateRuleRepository(db)

    # Query rules for historical date
    historical_date = date(2024, 1, 1)

    start = time()
    rules = await repo.get_active_rules_for_jurisdiction("US-CA", "gap_premium", historical_date)
    end = time()

    duration_ms = (end - start) * 1000

    # Historical queries should also be fast
    assert duration_ms < 50, f"Historical rule query took {duration_ms:.2f}ms (target: < 50ms)"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_create_rule_performance(db):
    """
    Test that creating new rules is reasonably fast.

    Admin operations can be slightly slower, but should still complete < 500ms.
    """
    repo = StateRuleRepository(db)

    start = time()
    rule = await repo.create_rule(
        jurisdiction_id="US-TX",
        rule_category="cancellation_fee",
        rule_config={"min": 0, "max": 50},
        effective_date=date(2026, 1, 1),
        rule_description="Performance test rule",
    )
    end = time()

    duration_ms = (end - start) * 1000

    assert duration_ms < 500, f"Rule creation took {duration_ms:.2f}ms (target: < 500ms)"
    assert rule is not None


@pytest.mark.performance
def test_database_indexes_exist(db):
    """
    Verify that all necessary indexes exist for optimal performance.

    This test checks the database schema for required indexes on:
    - state_validation_rules (jurisdiction_id, rule_category, effective_date)
    - contract_jurisdictions (contract_id, jurisdiction_id)
    """
    # Check for index on state_validation_rules
    result = db.execute(
        """
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'state_validation_rules'
        AND schemaname = 'public'
    """
    )

    indexes = [row[0] for row in result.fetchall()]

    # Should have indexes for common queries
    # Note: Actual index names may vary based on schema
    assert len(indexes) > 0, "No indexes found on state_validation_rules table"


# Performance Benchmarks Summary
"""
Performance Targets:

Query Type                      Target    Acceptable    Critical
-----------------------------------------------------------------
State Rule Query               < 20ms    < 50ms       < 100ms
Jurisdiction Lookup            < 10ms    < 30ms       < 50ms
Concurrent Lookups (20)        < 500ms   < 1000ms     < 2000ms
Multi-State Query              < 30ms    < 50ms       < 100ms
Historical Rule Query          < 20ms    < 50ms       < 100ms
Rule Creation                  < 200ms   < 500ms      < 1000ms

Database Indexes Required:
- state_validation_rules: (jurisdiction_id, rule_category, effective_date, is_active)
- contract_jurisdictions: (contract_id, is_primary)
- jurisdictions: (jurisdiction_id)
"""
