"""
User repository for user CRUD operations.
Extends BaseRepository with user-specific queries.
"""

from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User model with extended user-specific operations.

    Provides:
    - Standard CRUD operations (via BaseRepository)
    - Soft delete (sets is_active = False)
    - Query by email
    - Filter by role
    - Filter by active status
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize user repository with database session.

        Args:
            session: Async database session
        """
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """
        Get user by email address.

        Args:
            email: User's email address

        Returns:
            User if found, None otherwise
        """
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_auth_provider_id(
        self, auth_provider: str, auth_provider_user_id: str
    ) -> User | None:
        """
        Get user by external auth provider ID.

        Args:
            auth_provider: Auth provider name (e.g., 'auth0', 'okta')
            auth_provider_user_id: User ID from auth provider

        Returns:
            User if found, None otherwise
        """
        stmt = select(User).where(
            User.auth_provider == auth_provider,
            User.auth_provider_user_id == auth_provider_user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_active(self, offset: int = 0, limit: int = 100) -> List[User]:
        """
        Get all active users with pagination.

        Args:
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of active users
        """
        stmt = (
            select(User)
            .where(User.is_active == True)
            .offset(offset)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_role(self, role: str, offset: int = 0, limit: int = 100) -> List[User]:
        """
        Get users by role with pagination.

        Args:
            role: User role ('admin' or 'user')
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of users with specified role
        """
        stmt = (
            select(User)
            .where(User.role == role)
            .offset(offset)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete(self, user_id: UUID) -> bool:
        """
        Soft delete a user by setting is_active to False.
        User data is preserved but marked as inactive.

        Args:
            user_id: User's UUID

        Returns:
            True if user was deactivated, False if not found
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return False

        user.is_active = False
        await self.session.commit()
        await self.session.refresh(user)
        return True

    async def reactivate(self, user_id: UUID) -> bool:
        """
        Reactivate a soft-deleted user by setting is_active to True.

        Args:
            user_id: User's UUID

        Returns:
            True if user was reactivated, False if not found
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return False

        user.is_active = True
        await self.session.commit()
        await self.session.refresh(user)
        return True

    async def email_exists(self, email: str, exclude_user_id: UUID | None = None) -> bool:
        """
        Check if email is already taken by another user.
        Useful for validation during create/update operations.

        Args:
            email: Email address to check
            exclude_user_id: Optional user ID to exclude from check (for updates)

        Returns:
            True if email exists, False otherwise
        """
        stmt = select(User).where(User.email == email)

        if exclude_user_id is not None:
            stmt = stmt.where(User.user_id != exclude_user_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
