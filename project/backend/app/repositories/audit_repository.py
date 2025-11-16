"""
Audit repository for audit event operations.
Implements append-only audit log (no updates or deletes allowed).
"""

from typing import List
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.database.audit_event import AuditEvent


class AuditRepository(BaseRepository[AuditEvent]):
    """
    Repository for AuditEvent model with audit-specific queries.

    Audit events are append-only - updates and deletes are not allowed.
    Inherits generic CRUD operations from BaseRepository and adds
    audit-specific query methods.
    """

    def __init__(self, session: AsyncSession):
        """Initialize audit repository."""
        super().__init__(AuditEvent, session)

    async def create_event(
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
        Create a new audit event.

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
        event = AuditEvent(
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
        return await self.create(event)

    async def get_by_contract_id(
        self, contract_id: str, offset: int = 0, limit: int = 100
    ) -> List[AuditEvent]:
        """
        Retrieve all audit events for a specific contract.

        Args:
            contract_id: The contract ID to search for
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of audit events for the contract, ordered by timestamp descending
        """
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.contract_id == contract_id)
            .order_by(AuditEvent.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_extraction_id(
        self, extraction_id: UUID, offset: int = 0, limit: int = 100
    ) -> List[AuditEvent]:
        """
        Retrieve all audit events for a specific extraction.

        Args:
            extraction_id: The extraction ID to search for
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of audit events for the extraction, ordered by timestamp descending
        """
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.extraction_id == extraction_id)
            .order_by(AuditEvent.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_id(
        self, user_id: UUID, offset: int = 0, limit: int = 100
    ) -> List[AuditEvent]:
        """
        Retrieve all audit events for a specific user.

        Args:
            user_id: The user ID to search for
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of audit events for the user, ordered by timestamp descending
        """
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.user_id == user_id)
            .order_by(AuditEvent.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_event_type(
        self, event_type: str, offset: int = 0, limit: int = 100
    ) -> List[AuditEvent]:
        """
        Retrieve all audit events of a specific type.

        Args:
            event_type: The event type to search for
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of audit events of the specified type, ordered by timestamp descending
        """
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.event_type == event_type)
            .order_by(AuditEvent.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent(
        self, hours: int = 24, offset: int = 0, limit: int = 100
    ) -> List[AuditEvent]:
        """
        Retrieve recent audit events within the last N hours.

        Args:
            hours: Number of hours to look back (default: 24)
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of recent audit events, ordered by timestamp descending
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.timestamp >= cutoff_time)
            .order_by(AuditEvent.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, entity: AuditEvent) -> AuditEvent:
        """
        Updates are not allowed for audit events (immutable log).

        Raises:
            NotImplementedError: Always - audit events cannot be modified
        """
        raise NotImplementedError("Audit events are immutable and cannot be updated")

    async def delete(self, entity_id: UUID) -> bool:
        """
        Deletes are not allowed for audit events (append-only log).

        Raises:
            NotImplementedError: Always - audit events cannot be deleted
        """
        raise NotImplementedError("Audit events are append-only and cannot be deleted")

    async def delete_all(self) -> int:
        """
        Bulk deletes are not allowed for audit events (append-only log).

        Raises:
            NotImplementedError: Always - audit events cannot be deleted
        """
        raise NotImplementedError("Audit events are append-only and cannot be deleted")
