"""
State validation rules model with versioning and JSON configuration.
"""

from datetime import datetime, date
from uuid import UUID, uuid4
from sqlalchemy import (
    String,
    Text,
    Boolean,
    Date,
    TIMESTAMP,
    ForeignKey,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from app.database import Base


class StateValidationRule(Base):
    """
    State validation rules: Database-driven rules with JSONB configuration.

    Supports rule versioning with effective dates.

    Rule configuration examples:
    - Numeric: {"min": 200, "max": 1500, "strict": true}
    - Values: {"allowed_values": ["pro-rata"], "prohibited_values": ["rule of 78s"]}
    """

    __tablename__ = "state_validation_rules"

    # Primary key
    rule_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign key
    jurisdiction_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("jurisdictions.jurisdiction_id"), nullable=False
    )

    # Rule details
    rule_category: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_config: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Rule versioning
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Metadata
    rule_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="validation_rules")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "rule_category IN ('gap_premium', 'cancellation_fee', 'refund_method')",
            name="check_rule_category",
        ),
        Index("idx_state_rules_jurisdiction", "jurisdiction_id"),
        Index("idx_state_rules_category", "rule_category"),
        Index("idx_state_rules_effective", "effective_date"),
        Index("idx_state_rules_active", "is_active", "expiration_date"),
    )

    def __repr__(self) -> str:
        return f"<StateValidationRule(jurisdiction={self.jurisdiction_id}, category={self.rule_category})>"
