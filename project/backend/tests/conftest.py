"""
Pytest configuration and fixtures for testing.
"""

import pytest
from httpx import AsyncClient
from typing import AsyncGenerator
from decimal import Decimal

from app.main import app
from app.config import settings
from app.database import Base, get_async_engine, AsyncSessionLocal, init_database, close_database
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine


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


# Database fixtures
@pytest.fixture(scope="session")
async def test_db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create test database engine.
    Creates all tables before tests and cleans up after.
    """
    engine = get_async_engine(for_test=True)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create database session for each test.
    Automatically rolls back changes after each test.

    Usage:
        async def test_something(db_session: AsyncSession):
            # Use db_session here
            pass
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker

    # Create session factory from test engine
    TestSessionLocal = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestSessionLocal() as session:
        try:
            yield session
            await session.rollback()  # Rollback any changes
        finally:
            await session.close()


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    from app.models.database.user import User

    user = User(
        auth_provider="test_provider",
        auth_provider_user_id="test_user_123",
        email="testuser@example.com",
        username="testuser",
        role="user",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_contract(db_session: AsyncSession):
    """Create a test contract template."""
    from app.models.database.contract import Contract

    contract = Contract(
        contract_id="TEST-CONTRACT-001",
        s3_bucket="test-contracts",
        s3_key="contracts/TEST-CONTRACT-001.pdf",
        contract_type="GAP",
        template_version="1.0",
        is_active=True,
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)
    return contract


@pytest.fixture
async def test_extraction(db_session: AsyncSession, test_contract):
    """Create a test extraction."""
    from app.models.database.extraction import Extraction

    extraction = Extraction(
        contract_id=test_contract.contract_id,
        gap_insurance_premium=Decimal("500.00"),
        gap_premium_confidence=Decimal("95.00"),
        gap_premium_source={"page": 1, "section": "Pricing"},
        refund_calculation_method="Pro-rata",
        refund_method_confidence=Decimal("88.00"),
        refund_method_source={"page": 2, "section": "Terms"},
        cancellation_fee=Decimal("50.00"),
        cancellation_fee_confidence=Decimal("92.00"),
        cancellation_fee_source={"page": 3, "section": "Fees"},
        llm_model_version="gpt-4-turbo-preview",
        llm_provider="openai",
        status="pending",
    )
    db_session.add(extraction)
    await db_session.commit()
    await db_session.refresh(extraction)
    return extraction


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
