"""
Audit Service - Comprehensive audit trail and event sourcing.

Handles logging all system events for compliance, debugging, and analytics.
"""

import logging
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_repository import AuditRepository
from app.models.database.audit_event import AuditEvent

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for managing audit events and event sourcing.

    Provides high-level API for creating and querying audit events.
    All events are immutable (append-only log).
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize audit service.

        Args:
            db: Database session
        """
        self.db = db
        self.audit_repo = AuditRepository(db)

    async def log_event(
        self,
        event_type: str,
        contract_id: str | None = None,
        extraction_id: UUID | None = None,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
        event_data: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        duration_ms: int | None = None,
        cost_usd: float | None = None,
    ) -> AuditEvent:
        """
        Log an audit event.

        Args:
            event_type: Type of event (search, view, extract, etc.)
            contract_id: Optional contract ID
            extraction_id: Optional extraction ID
            user_id: Optional user ID
            session_id: Optional session ID
            event_data: Optional event data (JSON)
            ip_address: Optional IP address
            user_agent: Optional user agent
            duration_ms: Optional duration in milliseconds
            cost_usd: Optional cost in USD

        Returns:
            Created AuditEvent
        """
        event = await self.audit_repo.create_event(
            event_type=event_type,
            contract_id=contract_id,
            extraction_id=extraction_id,
            user_id=user_id,
            session_id=session_id,
            event_data=event_data,
            ip_address=ip_address,
            user_agent=user_agent,
            duration_ms=duration_ms,
            cost_usd=cost_usd,
        )

        logger.info(
            f"Audit event logged: {event_type} "
            f"(contract: {contract_id}, extraction: {extraction_id})"
        )

        return event

    # Convenience methods for common event types

    async def log_search(
        self,
        account_number: str,
        found: bool,
        ip_address: str | None = None,
        user_agent: str | None = None,
        duration_ms: int | None = None,
    ) -> AuditEvent:
        """
        Log a contract search event.

        Args:
            account_number: Account number searched
            found: Whether contract was found
            ip_address: Client IP address
            user_agent: Client user agent
            duration_ms: Search duration in milliseconds

        Returns:
            Created AuditEvent
        """
        return await self.log_event(
            event_type="search",
            event_data={"account_number": account_number, "found": found},
            ip_address=ip_address,
            user_agent=user_agent,
            duration_ms=duration_ms,
        )

    async def log_view(
        self,
        contract_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditEvent:
        """
        Log a contract view event.

        Args:
            contract_id: Contract ID viewed
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditEvent
        """
        return await self.log_event(
            event_type="view",
            contract_id=contract_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_extract(
        self,
        contract_id: str,
        extraction_id: UUID,
        llm_provider: str,
        llm_model: str,
        duration_ms: int,
        cost_usd: float | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditEvent:
        """
        Log an extraction event.

        Args:
            contract_id: Contract ID
            extraction_id: Extraction ID
            llm_provider: LLM provider used (openai, anthropic, etc.)
            llm_model: LLM model version
            duration_ms: Extraction duration in milliseconds
            cost_usd: Extraction cost in USD
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditEvent
        """
        return await self.log_event(
            event_type="extract",
            contract_id=contract_id,
            extraction_id=extraction_id,
            event_data={"llm_provider": llm_provider, "llm_model": llm_model},
            ip_address=ip_address,
            user_agent=user_agent,
            duration_ms=duration_ms,
            cost_usd=cost_usd,
        )

    async def log_submit(
        self,
        contract_id: str,
        extraction_id: UUID,
        corrections_count: int,
        user_id: UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditEvent:
        """
        Log an extraction submission event (with optional corrections).

        Args:
            contract_id: Contract ID
            extraction_id: Extraction ID
            corrections_count: Number of corrections applied
            user_id: User ID who submitted
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditEvent
        """
        return await self.log_event(
            event_type="submit",
            contract_id=contract_id,
            extraction_id=extraction_id,
            user_id=user_id,
            event_data={"corrections_count": corrections_count},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_chat(
        self,
        contract_id: str,
        session_id: UUID,
        message_length: int,
        duration_ms: int,
        cost_usd: float | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditEvent:
        """
        Log a chat message event.

        Args:
            contract_id: Contract ID
            session_id: Chat session ID
            message_length: Length of user message
            duration_ms: Chat processing duration
            cost_usd: LLM cost for chat
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditEvent
        """
        return await self.log_event(
            event_type="chat",
            contract_id=contract_id,
            session_id=session_id,
            event_data={"message_length": message_length},
            ip_address=ip_address,
            user_agent=user_agent,
            duration_ms=duration_ms,
            cost_usd=cost_usd,
        )

    # Query methods

    async def get_contract_history(
        self, contract_id: str, offset: int = 0, limit: int = 100
    ) -> List[AuditEvent]:
        """
        Get full audit history for a contract.

        Args:
            contract_id: Contract ID
            offset: Pagination offset
            limit: Pagination limit

        Returns:
            List of audit events
        """
        return await self.audit_repo.get_by_contract_id(contract_id, offset, limit)

    async def get_extraction_history(
        self, extraction_id: UUID, offset: int = 0, limit: int = 100
    ) -> List[AuditEvent]:
        """
        Get full audit history for an extraction.

        Args:
            extraction_id: Extraction ID
            offset: Pagination offset
            limit: Pagination limit

        Returns:
            List of audit events
        """
        return await self.audit_repo.get_by_extraction_id(extraction_id, offset, limit)

    async def get_user_activity(
        self, user_id: UUID, offset: int = 0, limit: int = 100
    ) -> List[AuditEvent]:
        """
        Get all activity for a user.

        Args:
            user_id: User ID
            offset: Pagination offset
            limit: Pagination limit

        Returns:
            List of audit events
        """
        return await self.audit_repo.get_by_user_id(user_id, offset, limit)

    async def get_recent_events(
        self, hours: int = 24, offset: int = 0, limit: int = 100
    ) -> List[AuditEvent]:
        """
        Get recent audit events.

        Args:
            hours: Number of hours to look back
            offset: Pagination offset
            limit: Pagination limit

        Returns:
            List of recent audit events
        """
        return await self.audit_repo.get_recent(hours, offset, limit)
