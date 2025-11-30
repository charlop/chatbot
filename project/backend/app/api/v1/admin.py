"""
Admin API endpoints for user management.
Admin-only operations for user CRUD.
"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.schemas.requests import UserCreateRequest, UserUpdateRequest
from app.schemas.responses import UserResponse, UserListResponse, ErrorResponse
from app.repositories.user_repository import UserRepository
from app.models.database.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/admin/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user with specified role and authentication provider. Admin-only operation.",
    responses={
        201: {
            "description": "User created successfully",
            "model": UserResponse,
        },
        400: {
            "description": "Invalid request or email already exists",
            "model": ErrorResponse,
        },
        409: {
            "description": "Email or auth provider ID already exists",
            "model": ErrorResponse,
        },
    },
)
async def create_user(
    user_request: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user.

    Args:
        user_request: User creation request with required fields
        db: Database session (injected)

    Returns:
        UserResponse with created user data

    Raises:
        HTTPException 400: If validation fails
        HTTPException 409: If email or auth provider ID already exists
    """
    logger.info(f"POST /admin/users - Creating user with email: {user_request.email}")

    repo = UserRepository(db)

    # Check if email already exists
    if await repo.email_exists(user_request.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email already exists: {user_request.email}",
        )

    # Check if auth provider user ID already exists
    existing_auth_user = await repo.get_by_auth_provider_id(
        user_request.auth_provider, user_request.auth_provider_user_id
    )
    if existing_auth_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Auth provider user ID already exists: {user_request.auth_provider_user_id}",
        )

    # Create user
    user = User(
        auth_provider=user_request.auth_provider,
        auth_provider_user_id=user_request.auth_provider_user_id,
        email=user_request.email,
        first_name=user_request.first_name,
        last_name=user_request.last_name,
        role=user_request.role,
    )

    try:
        created_user = await repo.create(user)
        logger.info(f"User created successfully: {created_user.user_id}")
        return UserResponse.model_validate(created_user)
    except IntegrityError as e:
        logger.error(f"Database integrity error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or auth provider ID already exists",
        )


@router.get(
    "/admin/users",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all users",
    description="Retrieve paginated list of all users. Admin-only operation.",
    responses={
        200: {
            "description": "Users retrieved successfully",
            "model": UserListResponse,
        },
    },
)
async def list_users(
    offset: int = 0,
    limit: int = 100,
    role: str | None = None,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """
    List all users with pagination and optional filters.

    Args:
        offset: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100)
        role: Optional filter by role ('admin' or 'user')
        active_only: Filter to only active users (default: False)
        db: Database session (injected)

    Returns:
        UserListResponse with paginated user list

    Raises:
        HTTPException 400: If role is invalid
    """
    logger.info(
        f"GET /admin/users - offset: {offset}, limit: {limit}, role: {role}, active_only: {active_only}"
    )

    repo = UserRepository(db)

    # Validate role filter
    if role and role not in {"admin", "user"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'admin' or 'user'",
        )

    # Get users based on filters
    if active_only:
        users = await repo.get_all_active(offset=offset, limit=limit)
    elif role:
        users = await repo.get_by_role(role, offset=offset, limit=limit)
    else:
        users = await repo.get_all(offset=offset, limit=limit)

    # Get total count
    total = await repo.count()

    return UserListResponse(
        users=[UserResponse.model_validate(user) for user in users],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/admin/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
    description="Retrieve a specific user by their UUID. Admin-only operation.",
    responses={
        200: {
            "description": "User found",
            "model": UserResponse,
        },
        404: {
            "description": "User not found",
            "model": ErrorResponse,
        },
    },
)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a user by their ID.

    Args:
        user_id: User's UUID
        db: Database session (injected)

    Returns:
        UserResponse with user data

    Raises:
        HTTPException 404: If user not found
    """
    logger.info(f"GET /admin/users/{user_id}")

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )

    return UserResponse.model_validate(user)


@router.put(
    "/admin/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user",
    description="Update user fields (email, name, role, status). Admin-only operation.",
    responses={
        200: {
            "description": "User updated successfully",
            "model": UserResponse,
        },
        404: {
            "description": "User not found",
            "model": ErrorResponse,
        },
        409: {
            "description": "Email already exists for another user",
            "model": ErrorResponse,
        },
    },
)
async def update_user(
    user_id: UUID,
    user_request: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a user's information.

    Args:
        user_id: User's UUID
        user_request: User update request with optional fields
        db: Database session (injected)

    Returns:
        UserResponse with updated user data

    Raises:
        HTTPException 404: If user not found
        HTTPException 409: If email already exists for another user
    """
    logger.info(f"PUT /admin/users/{user_id}")

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )

    # Check if email is being changed and already exists for another user
    if user_request.email and user_request.email != user.email:
        if await repo.email_exists(user_request.email, exclude_user_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email already exists: {user_request.email}",
            )

    # Update fields
    if user_request.email is not None:
        user.email = user_request.email
    if user_request.first_name is not None:
        user.first_name = user_request.first_name
    if user_request.last_name is not None:
        user.last_name = user_request.last_name
    if user_request.role is not None:
        user.role = user_request.role
    if user_request.is_active is not None:
        user.is_active = user_request.is_active

    try:
        updated_user = await repo.update(user)
        logger.info(f"User updated successfully: {user_id}")
        return UserResponse.model_validate(updated_user)
    except IntegrityError as e:
        logger.error(f"Database integrity error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists for another user",
        )


@router.delete(
    "/admin/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete user",
    description="Soft delete a user by setting is_active to False. User data is preserved. Admin-only operation.",
    responses={
        204: {
            "description": "User soft deleted successfully",
        },
        404: {
            "description": "User not found",
            "model": ErrorResponse,
        },
    },
)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete a user (set is_active = False).

    Args:
        user_id: User's UUID
        db: Database session (injected)

    Returns:
        204 No Content on success

    Raises:
        HTTPException 404: If user not found
    """
    logger.info(f"DELETE /admin/users/{user_id}")

    repo = UserRepository(db)
    result = await repo.soft_delete(user_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )

    logger.info(f"User soft deleted successfully: {user_id}")
    return None
