"""
Database connection and session management using SQLAlchemy 2.0 async.
Provides async engine, session factory, and FastAPI dependency injection.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from app.config import settings

# Declarative base for all ORM models
Base = declarative_base()

# Global async engine instance
_engine: AsyncEngine | None = None


def get_async_engine(for_test: bool = False) -> AsyncEngine:
    """
    Get or create the async SQLAlchemy engine.

    Args:
        for_test: If True, use test database URL and disable pooling

    Returns:
        AsyncEngine instance configured with connection pooling
    """
    global _engine

    if _engine is None:
        # Get database URL from settings
        database_url = settings.get_database_url(for_test=for_test)

        # Convert postgresql:// to postgresql+asyncpg://
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Engine configuration
        engine_kwargs = {
            "echo": settings.debug,  # Log SQL statements in debug mode
            "future": True,  # Use SQLAlchemy 2.0 style
        }

        # Connection pooling settings (disabled for tests)
        if for_test:
            engine_kwargs["poolclass"] = NullPool
        else:
            engine_kwargs.update(
                {
                    "pool_size": settings.database_pool_size,
                    "max_overflow": settings.database_max_overflow,
                    "pool_timeout": settings.database_pool_timeout,
                    "pool_recycle": settings.database_pool_recycle,
                    "pool_pre_ping": True,  # Verify connections before using
                }
            )

        _engine = create_async_engine(database_url, **engine_kwargs)

    return _engine


# Async session factory (will be initialized when engine is created)
AsyncSessionLocal = None


def get_session_local():
    """
    Get or create the session factory.
    This ensures the engine is created before the session factory.
    """
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        AsyncSessionLocal = async_sessionmaker(
            bind=get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            # Use db session here
            pass

    Yields:
        AsyncSession: Database session that will be automatically closed
    """
    session_local = get_session_local()
    async with session_local() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_health() -> bool:
    """
    Check if database connection is healthy.

    Returns:
        True if database is accessible, False otherwise
    """
    try:
        engine = get_async_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        # Log error in production
        print(f"Database health check failed: {e}")
        return False


async def init_database() -> None:
    """
    Initialize database by creating all tables.

    Note: In production, use Alembic migrations instead.
    This is useful for testing and initial setup.
    """
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    """
    Close database engine and cleanup connections.
    Should be called on application shutdown.
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
