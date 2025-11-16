"""
Correction model - Track human corrections to AI extractions.
"""

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import (
    String,
    Text,
    TIMESTAMP,
    ForeignKey,
    Index,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class Correction(Base):
    """
    Corrections table: Track human corrections to AI extractions.

    Stores corrections to extracted fields, maintaining both original
    and corrected values for audit trail purposes.
    """

    __tablename__ = "corrections"

    # Primary key
    correction_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Foreign key to extractions
    extraction_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("extractions.extraction_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Field being corrected (must be one of the three extracted fields)
    field_name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Original and corrected values (stored as text for flexibility)
    original_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_value: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional reason for correction
    correction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Who made the correction
    corrected_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )

    # When the correction was made
    corrected_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    extraction = relationship("Extraction", back_populates="corrections")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "field_name IN ('gap_insurance_premium', 'refund_calculation_method', 'cancellation_fee')",
            name="check_correction_field_name",
        ),
        CheckConstraint(
            "corrected_value <> ''",
            name="corrected_value_not_empty",
        ),
        Index("idx_corrections_extraction_id", "extraction_id"),
        Index("idx_corrections_field_name", "field_name"),
        Index("idx_corrections_corrected_by", "corrected_by"),
        Index("idx_corrections_corrected_at", "corrected_at"),
    )

    def __repr__(self) -> str:
        return f"<Correction(id={self.correction_id}, field={self.field_name})>"
