"""
Mock External RDB Client for testing.

This mock allows tests to control the External RDB responses without
requiring a database or real HTTP requests.
"""

import asyncio
import logging
from typing import Optional

from app.integrations.external_rdb.exceptions import (
    ExternalRDBConnectionError,
    ExternalRDBNotFoundError,
    ExternalRDBTimeoutError,
)
from app.integrations.external_rdb.models import (
    ExternalRDBHealthResponse,
    ExternalRDBLookupResponse,
)

logger = logging.getLogger(__name__)


class MockExternalRDB:
    """
    Mock external database for testing.

    Allows tests to configure account → template mappings without
    requiring a real database or external API.

    Usage:
        mock = MockExternalRDB()
        mock.add_mapping("000000000001", "GAP-2024-TEMPLATE-001")
        response = await mock.lookup_template_by_account("000000000001")
    """

    def __init__(
        self,
        simulate_delay: bool = False,
        delay_ms: int = 100,
        fail_on_lookup: bool = False,
        timeout_on_lookup: bool = False,
    ):
        """
        Initialize mock External RDB.

        Args:
            simulate_delay: If True, add artificial delay to simulate network latency
            delay_ms: Delay duration in milliseconds
            fail_on_lookup: If True, raise connection error on lookup
            timeout_on_lookup: If True, raise timeout error on lookup
        """
        self.mappings: dict[str, str] = {}
        self.simulate_delay = simulate_delay
        self.delay_ms = delay_ms
        self.fail_on_lookup = fail_on_lookup
        self.timeout_on_lookup = timeout_on_lookup
        self.lookup_count = 0
        self.health_check_count = 0

    def add_mapping(self, account_number: str, template_id: str) -> None:
        """Add account number to template ID mapping."""
        self.mappings[account_number] = template_id

    def add_mappings(self, mappings: dict[str, str]) -> None:
        """Add multiple mappings at once."""
        self.mappings.update(mappings)

    def remove_mapping(self, account_number: str) -> None:
        """Remove a mapping."""
        self.mappings.pop(account_number, None)

    def clear_mappings(self) -> None:
        """Clear all mappings."""
        self.mappings.clear()

    def reset_counters(self) -> None:
        """Reset lookup and health check counters."""
        self.lookup_count = 0
        self.health_check_count = 0

    async def lookup_template_by_account(
        self,
        account_number: str,
        db_session: Optional[object] = None,
    ) -> ExternalRDBLookupResponse:
        """
        Mock lookup of template ID by account number.

        Args:
            account_number: 12-digit account number
            db_session: Ignored (for interface compatibility)

        Returns:
            ExternalRDBLookupResponse with template ID

        Raises:
            ExternalRDBNotFoundError: Account not in mappings
            ExternalRDBTimeoutError: If timeout_on_lookup is True
            ExternalRDBConnectionError: If fail_on_lookup is True
        """
        self.lookup_count += 1

        # Simulate network delay if enabled
        if self.simulate_delay:
            await asyncio.sleep(self.delay_ms / 1000.0)

        # Simulate timeout
        if self.timeout_on_lookup:
            raise ExternalRDBTimeoutError("Mock timeout - simulating slow external API")

        # Simulate connection failure
        if self.fail_on_lookup:
            raise ExternalRDBConnectionError(
                "Mock connection error - simulating external API failure"
            )

        # Check if account exists in mappings
        if account_number not in self.mappings:
            raise ExternalRDBNotFoundError(
                f"Account number {account_number} not found in mock external database"
            )

        template_id = self.mappings[account_number]
        logger.debug(f"Mock External RDB: {account_number} → {template_id}")

        return ExternalRDBLookupResponse(
            contract_template_id=template_id,
            account_number=account_number,
            source="external_api",
        )

    async def health_check(self) -> ExternalRDBHealthResponse:
        """
        Mock health check.

        Returns:
            ExternalRDBHealthResponse (always healthy in mock)
        """
        self.health_check_count += 1

        if self.fail_on_lookup:
            return ExternalRDBHealthResponse(
                status="unhealthy",
                message="Mock unhealthy - simulating external API down",
            )

        return ExternalRDBHealthResponse(
            status="healthy",
            message="Mock healthy - test mode",
        )

    async def close(self):
        """Mock close (no-op)."""
        pass


def create_default_mock() -> MockExternalRDB:
    """
    Create a mock with default test mappings.

    Returns:
        MockExternalRDB with common test data
    """
    mock = MockExternalRDB()

    # Add default test mappings (matching seed data)
    default_mappings = {
        "000000000001": "GAP-2024-TEMPLATE-001",
        "000000000002": "GAP-2024-TEMPLATE-002",
        "000000000003": "GAP-2024-TEMPLATE-003",
        "000000000004": "VSC-2024-TEMPLATE-004",
        "000000000005": "VSC-2024-TEMPLATE-005",
        "000000000006": "GAP-2024-TEMPLATE-006",
        "000000000007": "VSC-2024-TEMPLATE-007",
    }

    mock.add_mappings(default_mappings)
    return mock
