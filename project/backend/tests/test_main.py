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
    """Test readiness check endpoint returns 200."""
    response = await async_client.get("/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    # Note: Database and Redis checks not implemented yet
    assert "database" in data
    assert "redis" in data


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
