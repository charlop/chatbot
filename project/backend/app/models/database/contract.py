"""
Contract model - Metadata for contracts synced from external RDB.
"""

from datetime import datetime, date
from sqlalchemy import String, Text, Date, TIMESTAMP, Index, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Contract(Base):
    """
    Contracts table: Metadata for contracts synced from external RDB.

    Stores contract information including PDF URL, customer data, and vehicle info.
    One-to-one relationship with Extraction.
    """

    __tablename__ = "contracts"

    # Primary key
    contract_id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Required fields
    account_number: Mapped[str] = mapped_column(String(100), nullable=False)

    # S3 Storage (PDFs stored with IAM authentication)
    s3_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(1024), nullable=False)

    # Document Content (populated by external ETL batch process)
    document_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    embeddings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    text_extracted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    text_extraction_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # 'pending', 'completed', 'failed'

    # Optional metadata fields
    document_repository_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contract_type: Mapped[str] = mapped_column(String(50), default="GAP", nullable=False)
    contract_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # JSON field for flexible vehicle data storage
    vehicle_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

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
    last_synced_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    extractions = relationship(
        "Extraction",
        back_populates="contract",
        cascade="all, delete-orphan",
        uselist=False,  # One-to-one relationship
    )
    audit_events = relationship(
        "AuditEvent",
        back_populates="contract",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("s3_bucket <> ''", name="s3_bucket_not_empty"),
        CheckConstraint("s3_key <> ''", name="s3_key_not_empty"),
        Index("idx_contracts_account_number", "account_number"),
        Index("idx_contracts_contract_type", "contract_type"),
        Index("idx_contracts_last_synced_at", "last_synced_at"),
        Index("idx_contracts_contract_date", "contract_date"),
        Index("idx_contracts_s3_location", "s3_bucket", "s3_key"),
        Index("idx_contracts_extraction_status", "text_extraction_status"),
    )

    def __repr__(self) -> str:
        return f"<Contract(id={self.contract_id}, account={self.account_number})>"
