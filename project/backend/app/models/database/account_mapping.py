"""
Account Template Mapping model - Maps account numbers to contract template IDs.
"""

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import String, TIMESTAMP, ForeignKey, Index, CheckConstraint, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AccountTemplateMapping(Base):
    """
    Account-Template Mappings table: Maps account numbers to contract template IDs.

    This table caches lookups from external database for performance.
    Supports hybrid cache strategy (Redis -> DB -> External API).
    MULTI-POLICY SUPPORT: One account can have multiple policies.
    """

    __tablename__ = "account_template_mappings"

    # Primary key
    mapping_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Account number (no longer unique - allows multiple policies)
    account_number: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="12-digit customer account number"
    )

    # Policy identifier (unique within account)
    policy_id: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Policy identifier (e.g., DI_F, GAP_O)"
    )

    # Foreign key to contract template
    contract_template_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("contracts.contract_id", ondelete="CASCADE"),
        nullable=False,
        comment="Contract template ID this policy is mapped to",
    )

    # Cache metadata
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Source of mapping: external_api, manual, or migrated"
    )
    cached_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When mapping was cached from external source",
    )
    last_validated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Last time mapping was validated against external source",
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
    template = relationship(
        "Contract",
        back_populates="account_mappings",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "source IN ('external_api', 'manual', 'migrated')",
            name="account_template_mappings_source_check",
        ),
        UniqueConstraint("account_number", "policy_id", name="unique_account_policy"),
        Index("idx_account_mappings_account_number", "account_number"),
        Index("idx_account_mappings_policy_id", "policy_id"),
        Index("idx_account_mappings_account_policy", "account_number", "policy_id"),
        Index("idx_account_mappings_template_id", "contract_template_id"),
        Index("idx_account_mappings_cached_at", "cached_at"),
        Index("idx_account_mappings_source", "source"),
    )

    def __repr__(self) -> str:
        return f"<AccountTemplateMapping(account={self.account_number}, policy={self.policy_id}, template={self.contract_template_id}, source={self.source})>"
