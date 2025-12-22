"""
Unit tests for User repository.
Tests user-specific CRUD operations and queries.
"""

import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.models.database.user import User


@pytest.mark.unit
@pytest.mark.db
class TestUserRepository:
    """Tests for UserRepository operations."""

    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a new user."""
        repo = UserRepository(db_session)
        unique_id = str(uuid.uuid4())[:8]

        user = User(
            auth_provider="auth0",
            auth_provider_user_id=f"auth0|test-create-{unique_id}",
            email=f"test.create-{unique_id}@example.com",
            first_name="Test",
            last_name="User",
            role="user",
        )

        created = await repo.create(user)
        assert created.email == f"test.create-{unique_id}@example.com"
        assert created.role == "user"
        assert created.is_active is True
        assert created.user_id is not None

    async def test_get_by_id(self, db_session: AsyncSession, test_user: User):
        """Test retrieving user by ID."""
        repo = UserRepository(db_session)

        found = await repo.get_by_id(test_user.user_id)
        assert found is not None
        assert found.user_id == test_user.user_id
        assert found.email == test_user.email

    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """Test get_by_id returns None for non-existent ID."""
        repo = UserRepository(db_session)
        from uuid import uuid4

        found = await repo.get_by_id(uuid4())
        assert found is None

    async def test_get_by_email(self, db_session: AsyncSession, test_user: User):
        """Test retrieving user by email."""
        repo = UserRepository(db_session)

        found = await repo.get_by_email(test_user.email)
        assert found is not None
        assert found.email == test_user.email
        assert found.user_id == test_user.user_id

    async def test_get_by_email_not_found(self, db_session: AsyncSession):
        """Test get_by_email returns None for non-existent email."""
        repo = UserRepository(db_session)

        found = await repo.get_by_email("nonexistent@example.com")
        assert found is None

    async def test_get_by_auth_provider_id(self, db_session: AsyncSession, test_user: User):
        """Test retrieving user by auth provider ID."""
        repo = UserRepository(db_session)

        found = await repo.get_by_auth_provider_id(
            test_user.auth_provider, test_user.auth_provider_user_id
        )
        assert found is not None
        assert found.user_id == test_user.user_id

    async def test_get_by_auth_provider_id_not_found(self, db_session: AsyncSession):
        """Test get_by_auth_provider_id returns None for non-existent provider ID."""
        repo = UserRepository(db_session)

        found = await repo.get_by_auth_provider_id("auth0", "nonexistent-id")
        assert found is None

    async def test_get_all_active(self, db_session: AsyncSession):
        """Test retrieving only active users."""
        repo = UserRepository(db_session)
        unique_id = str(uuid.uuid4())[:8]

        # Create active user
        active_user = User(
            auth_provider="auth0",
            auth_provider_user_id=f"auth0|active-{unique_id}",
            email="active@example.com",
            role="user",
            is_active=True,
        )
        await repo.create(active_user)

        # Create inactive user
        inactive_user = User(
            auth_provider="auth0",
            auth_provider_user_id=f"auth0|inactive-{unique_id}",
            email="inactive@example.com",
            role="user",
            is_active=False,
        )
        await repo.create(inactive_user)

        active_users = await repo.get_all_active()
        active_emails = [u.email for u in active_users]

        assert "active@example.com" in active_emails
        assert "inactive@example.com" not in active_emails

    async def test_get_by_role(self, db_session: AsyncSession):
        """Test retrieving users by role."""
        repo = UserRepository(db_session)
        unique_id = str(uuid.uuid4())[:8]

        # Create admin user
        admin = User(
            auth_provider="auth0",
            auth_provider_user_id=f"auth0|admin-{unique_id}",
            email="admin@example.com",
            role="admin",
        )
        await repo.create(admin)

        # Create regular user
        user = User(
            auth_provider="auth0",
            auth_provider_user_id=f"auth0|user-{unique_id}",
            email="regular@example.com",
            role="user",
        )
        await repo.create(user)

        # Query by role
        admins = await repo.get_by_role("admin")
        admin_emails = [u.email for u in admins]

        assert "admin@example.com" in admin_emails
        assert "regular@example.com" not in admin_emails

    async def test_soft_delete(self, db_session: AsyncSession, test_user: User):
        """Test soft deleting a user."""
        repo = UserRepository(db_session)

        # User should be active initially
        assert test_user.is_active is True

        # Soft delete
        result = await repo.soft_delete(test_user.user_id)
        assert result is True

        # Verify user is now inactive
        updated_user = await repo.get_by_id(test_user.user_id)
        assert updated_user is not None
        assert updated_user.is_active is False

    async def test_soft_delete_not_found(self, db_session: AsyncSession):
        """Test soft delete returns False for non-existent user."""
        repo = UserRepository(db_session)
        from uuid import uuid4

        result = await repo.soft_delete(uuid4())
        assert result is False

    async def test_reactivate(self, db_session: AsyncSession):
        """Test reactivating a soft-deleted user."""
        repo = UserRepository(db_session)
        unique_id = str(uuid.uuid4())[:8]

        # Create inactive user
        user = User(
            auth_provider="auth0",
            auth_provider_user_id=f"auth0|reactivate-{unique_id}",
            email="reactivate@example.com",
            role="user",
            is_active=False,
        )
        created = await repo.create(user)

        # Reactivate
        result = await repo.reactivate(created.user_id)
        assert result is True

        # Verify user is now active
        reactivated = await repo.get_by_id(created.user_id)
        assert reactivated is not None
        assert reactivated.is_active is True

    async def test_reactivate_not_found(self, db_session: AsyncSession):
        """Test reactivate returns False for non-existent user."""
        repo = UserRepository(db_session)
        from uuid import uuid4

        result = await repo.reactivate(uuid4())
        assert result is False

    async def test_email_exists(self, db_session: AsyncSession, test_user: User):
        """Test checking if email exists."""
        repo = UserRepository(db_session)

        # Test existing email
        exists = await repo.email_exists(test_user.email)
        assert exists is True

        # Test non-existent email
        exists = await repo.email_exists("nonexistent@example.com")
        assert exists is False

    async def test_email_exists_with_exclude(self, db_session: AsyncSession, test_user: User):
        """Test email_exists excludes specified user ID."""
        repo = UserRepository(db_session)

        # Should return False when excluding the user who has this email
        exists = await repo.email_exists(test_user.email, exclude_user_id=test_user.user_id)
        assert exists is False

        # Should return True for another user's email
        unique_id = str(uuid.uuid4())[:8]
        other_user = User(
            auth_provider="auth0",
            auth_provider_user_id=f"auth0|other-{unique_id}",
            email="other@example.com",
            role="user",
        )
        created = await repo.create(other_user)

        exists = await repo.email_exists(created.email, exclude_user_id=test_user.user_id)
        assert exists is True

    async def test_get_all_with_pagination(self, db_session: AsyncSession):
        """Test get_all with pagination."""
        repo = UserRepository(db_session)
        unique_base = str(uuid.uuid4())[:8]

        # Create multiple users
        for i in range(10):
            user = User(
                auth_provider="auth0",
                auth_provider_user_id=f"auth0|paginate-{unique_base}-{i:03d}",
                email=f"user{unique_base}-{i:03d}@example.com",
                role="user",
            )
            await repo.create(user)

        # Test limit
        limited = await repo.get_all(limit=5)
        assert len(limited) == 5

        # Test offset
        offset_users = await repo.get_all(offset=5, limit=5)
        assert len(offset_users) == 5

    async def test_update_user(self, db_session: AsyncSession, test_user: User):
        """Test updating a user."""
        repo = UserRepository(db_session)

        # Update user role
        test_user.role = "admin"
        test_user.first_name = "Updated"

        updated = await repo.update(test_user)
        assert updated.role == "admin"
        assert updated.first_name == "Updated"

        # Verify persisted
        fetched = await repo.get_by_id(test_user.user_id)
        assert fetched.role == "admin"
        assert fetched.first_name == "Updated"
