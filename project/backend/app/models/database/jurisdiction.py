"""
Jurisdiction model - States/regions with specific regulatory rules.
"""

from datetime import datetime
from sqlalchemy import String, Boolean, TIMESTAMP, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Jurisdiction(Base):
    """
    Jurisdictions table: States and regions with regulatory authority.

    Examples:
    - US-CA: California
    - US-NY: New York
    - US-FEDERAL: Federal default rules
    """

    __tablename__ = "jurisdictions"

    # Primary key
    jurisdiction_id: Mapped[str] = mapped_column(String(10), primary_key=True)

    # Jurisdiction details
    jurisdiction_name: Mapped[str] = mapped_column(String(100), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    state_code: Mapped[str | None] = mapped_column(
        String(2), nullable=True
    )  # NULL for federal
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
    contract_jurisdictions = relationship(
        "ContractJurisdiction",
        back_populates="jurisdiction",
        cascade="all, delete-orphan",
    )
    validation_rules = relationship(
        "StateValidationRule",
        back_populates="jurisdiction",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_jurisdictions_state_code", "state_code"),
        Index("idx_jurisdictions_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Jurisdiction(id={self.jurisdiction_id}, name={self.jurisdiction_name})>"
