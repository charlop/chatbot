"""
Extraction model - AI-extracted data from contracts.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import (
    String,
    Text,
    Integer,
    TIMESTAMP,
    ForeignKey,
    Index,
    CheckConstraint,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, NUMERIC

from app.database import Base


class Extraction(Base):
    """
    Extractions table: AI-extracted data from contracts.

    Stores three extracted fields:
    - GAP Insurance Premium
    - Refund Calculation Method
    - Cancellation Fee

    Each field has value, confidence score, and source location.
    One extraction per contract (unique constraint).
    """

    __tablename__ = "extractions"

    # Primary key
    extraction_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Foreign key to contracts
    contract_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("contracts.contract_id", ondelete="CASCADE"),
        nullable=False,
    )

    # GAP Insurance Premium field
    gap_insurance_premium: Mapped[Decimal | None] = mapped_column(NUMERIC(10, 2), nullable=True)
    gap_premium_confidence: Mapped[Decimal | None] = mapped_column(NUMERIC(5, 2), nullable=True)
    gap_premium_source: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Refund Calculation Method field
    refund_calculation_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    refund_method_confidence: Mapped[Decimal | None] = mapped_column(NUMERIC(5, 2), nullable=True)
    refund_method_source: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Cancellation Fee field
    cancellation_fee: Mapped[Decimal | None] = mapped_column(NUMERIC(10, 2), nullable=True)
    cancellation_fee_confidence: Mapped[Decimal | None] = mapped_column(
        NUMERIC(5, 2), nullable=True
    )
    cancellation_fee_source: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # LLM Metadata
    llm_model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_cost_usd: Mapped[Decimal | None] = mapped_column(NUMERIC(10, 6), nullable=True)

    # Status and approval fields
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    extracted_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    extracted_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    approved_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True,
    )

    # Auto-updated timestamp
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    contract = relationship("Contract", back_populates="extractions")
    corrections = relationship(
        "Correction",
        back_populates="extraction",
        cascade="all, delete-orphan",
    )
    audit_events = relationship(
        "AuditEvent",
        back_populates="extraction",
        cascade="all, delete-orphan",
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("contract_id", name="unique_contract_extraction"),
        CheckConstraint(
            "status IN ('pending', 'approved')",
            name="check_extraction_status",
        ),
        CheckConstraint(
            "gap_premium_confidence >= 0 AND gap_premium_confidence <= 100",
            name="check_gap_premium_confidence",
        ),
        CheckConstraint(
            "refund_method_confidence >= 0 AND refund_method_confidence <= 100",
            name="check_refund_method_confidence",
        ),
        CheckConstraint(
            "cancellation_fee_confidence >= 0 AND cancellation_fee_confidence <= 100",
            name="check_cancellation_fee_confidence",
        ),
        CheckConstraint(
            "processing_time_ms >= 0",
            name="check_processing_time_ms",
        ),
        Index("idx_extractions_contract_id", "contract_id"),
        Index("idx_extractions_status", "status"),
        Index("idx_extractions_extracted_at", "extracted_at"),
        Index("idx_extractions_extracted_by", "extracted_by"),
        Index("idx_extractions_llm_provider", "llm_provider"),
    )

    def __repr__(self) -> str:
        return f"<Extraction(id={self.extraction_id}, contract_id={self.contract_id}, status={self.status})>"
