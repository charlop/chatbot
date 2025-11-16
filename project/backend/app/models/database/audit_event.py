"""
AuditEvent model - Immutable log of all system events.
"""

from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal
from sqlalchemy import (
    String,
    Text,
    Integer,
    TIMESTAMP,
    ForeignKey,
    Index,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, INET, NUMERIC

from app.database import Base


class AuditEvent(Base):
    """
    Audit events table: Immutable log of all system events.

    Implements event sourcing pattern for complete audit trail.
    Events are append-only - no updates or deletes allowed.
    """

    __tablename__ = "audit_events"

    # Primary key
    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Event type (limited to specific values)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Foreign keys (all optional - not all events relate to all entities)
    contract_id: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("contracts.contract_id"),
        nullable=True,
    )
    extraction_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("extractions.extraction_id"),
        nullable=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True,
    )
    session_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        # ForeignKey("sessions.session_id"),  # Uncomment when sessions table is implemented
        nullable=True,
    )

    # Event data (flexible JSON storage)
    event_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Timestamp of event
    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Request metadata
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Performance and cost tracking
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[Decimal | None] = mapped_column(NUMERIC(10, 6), nullable=True)

    # Relationships
    contract = relationship("Contract", back_populates="audit_events")
    extraction = relationship("Extraction", back_populates="audit_events")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            """event_type IN (
                'search', 'view', 'extract', 'edit', 'approve', 'reject', 'chat',
                'login', 'logout', 'user_created', 'user_updated', 'user_deleted'
            )""",
            name="check_audit_event_type",
        ),
        Index("idx_audit_events_contract_id", "contract_id"),
        Index("idx_audit_events_extraction_id", "extraction_id"),
        Index("idx_audit_events_user_id", "user_id"),
        Index("idx_audit_events_timestamp", "timestamp"),
        Index("idx_audit_events_event_type", "event_type"),
        Index("idx_audit_events_session_id", "session_id"),
        # Partial index for recent events (last 30 days) - faster queries
        Index(
            "idx_audit_events_recent",
            "timestamp",
            postgresql_where="timestamp > CURRENT_TIMESTAMP - INTERVAL '30 days'",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditEvent(id={self.event_id}, type={self.event_type}, timestamp={self.timestamp})>"
        )
