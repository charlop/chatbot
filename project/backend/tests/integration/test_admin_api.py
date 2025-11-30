"""
Integration tests for admin API endpoints.
Tests user management CRUD operations.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database.user import User


@pytest.mark.integration
@pytest.mark.db
class TestAdminCreateUserEndpoint:
    """Tests for POST /api/v1/admin/users endpoint."""

    async def test_create_user_success(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test creating a new user successfully."""
        response = await async_client.post(
            "/api/v1/admin/users",
            json={
                "auth_provider": "auth0",
                "auth_provider_user_id": "auth0|integration-test-001",
                "email": "integration.test@example.com",
                "first_name": "Integration",
                "last_name": "Test",
                "role": "user",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "integration.test@example.com"
        assert data["firstName"] == "Integration"
        assert data["lastName"] == "Test"
        assert data["role"] == "user"
        assert data["isActive"] is True
        assert "userId" in data

    async def test_create_user_duplicate_email(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test creating user with duplicate email fails."""
        # Create first user
        user1 = User(
            auth_provider="auth0",
            auth_provider_user_id="auth0|duplicate-email-001",
            email="duplicate@example.com",
            role="user",
        )
        db_session.add(user1)
        await db_session.commit()

        # Try to create user with same email
        response = await async_client.post(
            "/api/v1/admin/users",
            json={
                "auth_provider": "auth0",
                "auth_provider_user_id": "auth0|duplicate-email-002",
                "email": "duplicate@example.com",
                "role": "user",
            },
        )

        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()

    async def test_create_user_duplicate_auth_provider_id(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test creating user with duplicate auth provider ID fails."""
        # Create first user
        user1 = User(
            auth_provider="auth0",
            auth_provider_user_id="auth0|duplicate-auth-001",
            email="user1@example.com",
            role="user",
        )
        db_session.add(user1)
        await db_session.commit()

        # Try to create user with same auth provider ID
        response = await async_client.post(
            "/api/v1/admin/users",
            json={
                "auth_provider": "auth0",
                "auth_provider_user_id": "auth0|duplicate-auth-001",
                "email": "user2@example.com",
                "role": "user",
            },
        )

        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()

    async def test_create_user_invalid_email(self, async_client: AsyncClient):
        """Test creating user with invalid email fails."""
        response = await async_client.post(
            "/api/v1/admin/users",
            json={
                "auth_provider": "auth0",
                "auth_provider_user_id": "auth0|invalid-email-001",
                "email": "not-an-email",
                "role": "user",
            },
        )

        assert response.status_code == 422

    async def test_create_user_invalid_role(self, async_client: AsyncClient):
        """Test creating user with invalid role fails."""
        response = await async_client.post(
            "/api/v1/admin/users",
            json={
                "auth_provider": "auth0",
                "auth_provider_user_id": "auth0|invalid-role-001",
                "email": "test@example.com",
                "role": "superuser",
            },
        )

        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.db
class TestAdminListUsersEndpoint:
    """Tests for GET /api/v1/admin/users endpoint."""

    async def test_list_users_success(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test listing users successfully."""
        # Create multiple users
        for i in range(5):
            user = User(
                auth_provider="auth0",
                auth_provider_user_id=f"auth0|list-test-{i:03d}",
                email=f"user{i:03d}@example.com",
                role="user",
            )
            db_session.add(user)
        await db_session.commit()

        # List users
        response = await async_client.get("/api/v1/admin/users")

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert len(data["users"]) >= 5  # At least our 5 users
        assert data["total"] >= 5

    async def test_list_users_pagination(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test listing users with pagination."""
        # Create multiple users
        for i in range(10):
            user = User(
                auth_provider="auth0",
                auth_provider_user_id=f"auth0|pagination-test-{i:03d}",
                email=f"pag{i:03d}@example.com",
                role="user",
            )
            db_session.add(user)
        await db_session.commit()

        # List with limit
        response = await async_client.get("/api/v1/admin/users?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) <= 5
        assert data["limit"] == 5

    async def test_list_users_filter_by_role(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test filtering users by role."""
        # Create admin and regular users
        admin = User(
            auth_provider="auth0",
            auth_provider_user_id="auth0|admin-filter-001",
            email="admin.filter@example.com",
            role="admin",
        )
        user = User(
            auth_provider="auth0",
            auth_provider_user_id="auth0|user-filter-001",
            email="user.filter@example.com",
            role="user",
        )
        db_session.add(admin)
        db_session.add(user)
        await db_session.commit()

        # Filter by admin role
        response = await async_client.get("/api/v1/admin/users?role=admin")

        assert response.status_code == 200
        data = response.json()
        # All returned users should be admins
        for user in data["users"]:
            assert user["role"] == "admin"

    async def test_list_users_active_only(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test filtering to only active users."""
        # Create active and inactive users
        active_user = User(
            auth_provider="auth0",
            auth_provider_user_id="auth0|active-filter-001",
            email="active.filter@example.com",
            role="user",
            is_active=True,
        )
        inactive_user = User(
            auth_provider="auth0",
            auth_provider_user_id="auth0|inactive-filter-001",
            email="inactive.filter@example.com",
            role="user",
            is_active=False,
        )
        db_session.add(active_user)
        db_session.add(inactive_user)
        await db_session.commit()

        # Filter to active only
        response = await async_client.get("/api/v1/admin/users?active_only=true")

        assert response.status_code == 200
        data = response.json()
        # All returned users should be active
        for user in data["users"]:
            assert user["isActive"] is True


@pytest.mark.integration
@pytest.mark.db
class TestAdminGetUserEndpoint:
    """Tests for GET /api/v1/admin/users/{user_id} endpoint."""

    async def test_get_user_success(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test getting a user by ID successfully."""
        # Create user
        user = User(
            auth_provider="auth0",
            auth_provider_user_id="auth0|get-test-001",
            email="get.test@example.com",
            first_name="Get",
            last_name="Test",
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Get user
        response = await async_client.get(f"/api/v1/admin/users/{user.user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "get.test@example.com"
        assert data["firstName"] == "Get"
        assert data["lastName"] == "Test"

    async def test_get_user_not_found(self, async_client: AsyncClient):
        """Test getting a non-existent user returns 404."""
        from uuid import uuid4

        fake_id = uuid4()
        response = await async_client.get(f"/api/v1/admin/users/{fake_id}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


@pytest.mark.integration
@pytest.mark.db
class TestAdminUpdateUserEndpoint:
    """Tests for PUT /api/v1/admin/users/{user_id} endpoint."""

    async def test_update_user_success(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test updating a user successfully."""
        # Create user
        user = User(
            auth_provider="auth0",
            auth_provider_user_id="auth0|update-test-001",
            email="original@example.com",
            first_name="Original",
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Update user
        response = await async_client.put(
            f"/api/v1/admin/users/{user.user_id}",
            json={
                "email": "updated@example.com",
                "first_name": "Updated",
                "role": "admin",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"
        assert data["firstName"] == "Updated"
        assert data["role"] == "admin"

    async def test_update_user_email_conflict(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test updating user email to an existing email fails."""
        # Create two users
        user1 = User(
            auth_provider="auth0",
            auth_provider_user_id="auth0|conflict-001",
            email="existing@example.com",
            role="user",
        )
        user2 = User(
            auth_provider="auth0",
            auth_provider_user_id="auth0|conflict-002",
            email="other@example.com",
            role="user",
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user2)

        # Try to update user2's email to user1's email
        response = await async_client.put(
            f"/api/v1/admin/users/{user2.user_id}",
            json={"email": "existing@example.com"},
        )

        assert response.status_code == 409

    async def test_update_user_deactivate(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test deactivating a user."""
        # Create active user
        user = User(
            auth_provider="auth0",
            auth_provider_user_id="auth0|deactivate-test-001",
            email="deactivate@example.com",
            role="user",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Deactivate user
        response = await async_client.put(
            f"/api/v1/admin/users/{user.user_id}",
            json={"is_active": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["isActive"] is False

    async def test_update_user_not_found(self, async_client: AsyncClient):
        """Test updating non-existent user returns 404."""
        from uuid import uuid4

        fake_id = uuid4()
        response = await async_client.put(
            f"/api/v1/admin/users/{fake_id}",
            json={"first_name": "Updated"},
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.db
class TestAdminDeleteUserEndpoint:
    """Tests for DELETE /api/v1/admin/users/{user_id} endpoint."""

    async def test_delete_user_success(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test soft deleting a user successfully."""
        # Create user
        user = User(
            auth_provider="auth0",
            auth_provider_user_id="auth0|delete-test-001",
            email="delete@example.com",
            role="user",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        user_id = user.user_id

        # Delete user
        response = await async_client.delete(f"/api/v1/admin/users/{user_id}")

        assert response.status_code == 204

        # Verify user is now inactive
        from app.repositories.user_repository import UserRepository

        repo = UserRepository(db_session)
        deleted_user = await repo.get_by_id(user_id)
        assert deleted_user is not None
        assert deleted_user.is_active is False

    async def test_delete_user_not_found(self, async_client: AsyncClient):
        """Test deleting non-existent user returns 404."""
        from uuid import uuid4

        fake_id = uuid4()
        response = await async_client.delete(f"/api/v1/admin/users/{fake_id}")

        assert response.status_code == 404
