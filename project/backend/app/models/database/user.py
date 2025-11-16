"""
User model - User profile and authorization data.
NOTE: Authentication is handled by external provider (Phase 2).
"""

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import (
    String,
    Boolean,
    TIMESTAMP,
    Index,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class User(Base):
    """
    Users table: Stores user profile and authorization data.

    NOTE: Authentication via external provider (Auth0, Okta, Cognito, etc.)
    will be implemented in Phase 2. This table stores profile and authorization data.
    """

    __tablename__ = "users"

    # Primary key
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # External auth provider identifiers (Phase 2)
    # For Phase 1, these are placeholders
    auth_provider: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'auth0', 'okta', 'cognito', etc.
    auth_provider_user_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )  # sub claim from JWT

    # User profile data
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Application-specific authorization
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'admin' or 'user'
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
    last_login_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'user')",
            name="check_user_role",
        ),
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name="email_format",
        ),
        Index("idx_users_email", "email"),
        Index("idx_users_auth_provider_user_id", "auth_provider_user_id"),
        Index("idx_users_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.user_id}, email={self.email}, role={self.role})>"
