"""
External RDB Client - Account to Template ID lookup.

MOCK IMPLEMENTATION: Simulates external database for development/testing.
In production, replace with actual HTTP client to external API.
"""

import asyncio
import logging
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.external_rdb.exceptions import (
    ExternalRDBConnectionError,
    ExternalRDBNotFoundError,
    ExternalRDBTimeoutError,
)
from app.integrations.external_rdb.models import (
    ExternalRDBHealthResponse,
    ExternalRDBLookupResponse,
)
from app.models.database import AccountTemplateMapping

logger = logging.getLogger(__name__)


class ExternalRDBClient:
    """
    Client for external Account → Template ID lookup.

    MOCK IMPLEMENTATION: Uses local database to simulate external API.
    Replace with real HTTP client when external API is available.
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        timeout: int = 5,
        retry_attempts: int = 3,
        mock_mode: bool = True,
    ):
        """
        Initialize External RDB client.

        Args:
            api_url: Base URL of external RDB API
            api_key: API key for authentication
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts on failure
            mock_mode: If True, use mock implementation (default for development)
        """
        self.api_url = api_url
        self.api_key = api_key
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.mock_mode = mock_mode

        if not mock_mode:
            self.http_client = httpx.AsyncClient(
                base_url=api_url,
                timeout=timeout,
                headers={"Authorization": f"Bearer {api_key}"},
            )
        else:
            logger.info("External RDB client initialized in MOCK mode")

    async def lookup_template_by_account(
        self, account_number: str, db_session: Optional[AsyncSession] = None
    ) -> ExternalRDBLookupResponse:
        """
        Query external database for template ID associated with account.

        Args:
            account_number: 12-digit customer account number
            db_session: Database session (required for mock mode)

        Returns:
            ExternalRDBLookupResponse with template ID

        Raises:
            ExternalRDBNotFoundError: Account not found
            ExternalRDBTimeoutError: Request timed out
            ExternalRDBConnectionError: Connection failed
        """
        if self.mock_mode:
            return await self._mock_lookup(account_number, db_session)
        else:
            return await self._real_lookup(account_number)

    async def _mock_lookup(
        self, account_number: str, db_session: Optional[AsyncSession]
    ) -> ExternalRDBLookupResponse:
        """
        MOCK: Simulate external API by querying local database.

        In production, this would be replaced with actual HTTP call.
        """
        if not db_session:
            raise ValueError("db_session required for mock mode")

        # Simulate network delay (50-200ms)
        await asyncio.sleep(0.1)

        # Query local database to simulate external API
        result = await db_session.execute(
            select(AccountTemplateMapping).where(
                AccountTemplateMapping.account_number == account_number
            )
        )
        mapping = result.scalar_one_or_none()

        if not mapping:
            logger.warning(f"Account {account_number} not found in external RDB (MOCK)")
            raise ExternalRDBNotFoundError(
                f"Account number {account_number} not found in external database"
            )

        logger.info(f"MOCK: External RDB lookup: {account_number} → {mapping.contract_template_id}")

        return ExternalRDBLookupResponse(
            contract_template_id=mapping.contract_template_id,
            account_number=account_number,
            source="external_api",
        )

    async def _real_lookup(self, account_number: str) -> ExternalRDBLookupResponse:
        """
        PRODUCTION: Make actual HTTP request to external RDB API.

        Replace mock implementation with this when external API is available.
        """
        try:
            response = await self.http_client.post(
                "/lookup",
                json={"account_number": account_number},
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            return ExternalRDBLookupResponse(
                contract_template_id=data["contract_template_id"],
                account_number=account_number,
                source="external_api",
            )

        except httpx.TimeoutException as e:
            logger.error(f"External RDB timeout for account {account_number}: {e}")
            raise ExternalRDBTimeoutError(
                f"External database request timed out after {self.timeout}s"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ExternalRDBNotFoundError(f"Account number {account_number} not found")
            logger.error(f"External RDB HTTP error: {e}")
            raise ExternalRDBConnectionError(f"External database error: {e}")
        except Exception as e:
            logger.error(f"External RDB connection error: {e}")
            raise ExternalRDBConnectionError(f"Failed to connect to external database: {e}")

    async def health_check(self) -> ExternalRDBHealthResponse:
        """
        Check if external RDB is reachable and healthy.

        Returns:
            ExternalRDBHealthResponse with status

        Raises:
            ExternalRDBConnectionError: Health check failed
        """
        if self.mock_mode:
            return ExternalRDBHealthResponse(status="healthy", message="Mock mode - always healthy")

        try:
            response = await self.http_client.get("/health", timeout=2)
            response.raise_for_status()

            data = response.json()
            return ExternalRDBHealthResponse(
                status=data.get("status", "unknown"),
                message=data.get("message"),
            )

        except Exception as e:
            logger.error(f"External RDB health check failed: {e}")
            return ExternalRDBHealthResponse(status="unhealthy", message=str(e))

    async def close(self):
        """Close HTTP client connections."""
        if not self.mock_mode and hasattr(self, "http_client"):
            await self.http_client.aclose()
