"""
Smoke tests for main application.
Tests basic FastAPI functionality and endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.unit
async def test_health_check(async_client: AsyncClient):
    """Test health check endpoint returns 200."""
    response = await async_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "environment" in data


@pytest.mark.unit
async def test_readiness_check(async_client: AsyncClient):
    """
    Test readiness check endpoint.
    Returns 200 if database is connected, 503 if not.
    """
    response = await async_client.get("/ready")

    # Accept either 200 (DB connected) or 503 (DB not connected)
    assert response.status_code in [200, 503]
    data = response.json()

    # Check response structure
    assert "status" in data
    assert "database" in data
    assert "redis" in data

    # If DB connected, status should be "ready"
    # If DB not connected, status should be "not_ready"
    if response.status_code == 200:
        assert data["status"] == "ready"
        assert data["database"] == "connected"
    else:
        assert data["status"] == "not_ready"
        assert data["database"] == "disconnected"


@pytest.mark.unit
async def test_root_endpoint(async_client: AsyncClient):
    """Test root endpoint returns API information."""
    response = await async_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data
    assert data["docs"] == "/docs"


@pytest.mark.unit
async def test_openapi_schema(async_client: AsyncClient):
    """Test OpenAPI schema is accessible."""
    response = await async_client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
