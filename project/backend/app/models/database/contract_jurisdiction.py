"""
Contract-Jurisdiction mapping model - Handles multi-state templates.
"""

from datetime import datetime, date
from uuid import UUID, uuid4
from sqlalchemy import (
    String,
    Boolean,
    Date,
    TIMESTAMP,
    ForeignKey,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class ContractJurisdiction(Base):
    """
    Contract-Jurisdiction mapping: Many-to-many relationship.

    Supports multi-state contracts with primary jurisdiction designation.
    """

    __tablename__ = "contract_jurisdictions"

    # Primary key
    contract_jurisdiction_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Foreign keys
    contract_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("contracts.contract_id", ondelete="CASCADE"),
        nullable=False,
    )
    jurisdiction_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("jurisdictions.jurisdiction_id"), nullable=False
    )

    # Multi-state handling
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Versioning support
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    contract = relationship("Contract", back_populates="jurisdictions")
    jurisdiction = relationship("Jurisdiction", back_populates="contract_jurisdictions")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "contract_id",
            "jurisdiction_id",
            "effective_date",
            name="unique_contract_jurisdiction",
        ),
        Index("idx_contract_jurisdictions_contract", "contract_id"),
        Index("idx_contract_jurisdictions_jurisdiction", "jurisdiction_id"),
        Index("idx_contract_jurisdictions_effective", "effective_date"),
    )

    def __repr__(self) -> str:
        return f"<ContractJurisdiction(contract={self.contract_id}, jurisdiction={self.jurisdiction_id}, primary={self.is_primary})>"
