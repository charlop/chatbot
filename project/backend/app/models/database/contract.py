"""
Contract model - Contract TEMPLATES (not filled customer contracts).
"""

from datetime import datetime, date
from sqlalchemy import String, Text, Date, TIMESTAMP, Boolean, Index, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Contract(Base):
    """
    Contracts table: Contract TEMPLATES (not filled customer contracts).

    Stores template information including PDF URL, template version, and refund terms.
    One-to-one relationship with Extraction.
    Account number mappings are stored separately in AccountTemplateMapping.
    """

    __tablename__ = "contracts"

    # Primary key
    contract_id: Mapped[str] = mapped_column(
        String(100), primary_key=True, comment="Template identifier (e.g., GAP-2024-TEMPLATE-001)"
    )

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

    # Template metadata fields
    document_repository_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contract_type: Mapped[str] = mapped_column(String(50), default="GAP", nullable=False)
    contract_date: Mapped[date | None] = mapped_column(
        Date, nullable=True, comment="When template was created"
    )

    # Template versioning
    template_version: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Version number (e.g., 1.0, 2.0)"
    )
    effective_date: Mapped[date | None] = mapped_column(
        Date, nullable=True, comment="When this version became active"
    )
    deprecated_date: Mapped[date | None] = mapped_column(
        Date, nullable=True, comment="When this version was superseded"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this template version is currently active",
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
    account_mappings = relationship(
        "AccountTemplateMapping",
        back_populates="template",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("s3_bucket <> ''", name="s3_bucket_not_empty"),
        CheckConstraint("s3_key <> ''", name="s3_key_not_empty"),
        Index("idx_contracts_contract_type", "contract_type"),
        Index("idx_contracts_last_synced_at", "last_synced_at"),
        Index("idx_contracts_contract_date", "contract_date"),
        Index("idx_contracts_s3_location", "s3_bucket", "s3_key"),
        Index("idx_contracts_extraction_status", "text_extraction_status"),
        Index("idx_contracts_is_active", "is_active"),
        Index("idx_contracts_template_version", "template_version"),
    )

    def __repr__(self) -> str:
        return f"<Contract(id={self.contract_id}, type={self.contract_type}, version={self.template_version})>"
