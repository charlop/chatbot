"""
Pytest configuration and fixtures for testing.
"""

import pytest
from httpx import AsyncClient
from typing import AsyncGenerator

from app.main import app
from app.config import settings


@pytest.fixture
def anyio_backend():
    """
    Specify the async backend for pytest-asyncio.
    """
    return "asyncio"


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for testing FastAPI endpoints.

    Usage:
        async def test_endpoint(async_client):
            response = await async_client.get("/health")
            assert response.status_code == 200
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
def test_settings():
    """
    Test-specific settings override.
    """
    # Override settings for testing
    original_env = settings.app_env
    settings.app_env = "development"  # Use development settings for tests

    yield settings

    # Restore original settings
    settings.app_env = original_env


# TODO: Database fixtures (Day 2)
# @pytest.fixture(scope="session")
# async def test_db_engine():
#     """Create test database engine."""
#     pass
#
# @pytest.fixture
# async def db_session(test_db_engine):
#     """Create database session for tests."""
#     pass


# TODO: Redis fixtures (Day 10)
# @pytest.fixture
# async def redis_client():
#     """Create Redis client for tests."""
#     pass


# TODO: Mock LLM provider (Day 5)
# @pytest.fixture
# def mock_llm_response():
#     """Mock LLM API response."""
#     pass
