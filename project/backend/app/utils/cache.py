"""
Redis Cache Utilities

Provides async Redis connection and caching utilities.
"""

import logging
from typing import Optional

from redis.asyncio import Redis, ConnectionPool
from app.config import settings

logger = logging.getLogger(__name__)

# Global Redis connection pool
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[Redis] = None


async def get_redis() -> Optional[Redis]:
    """
    Get Redis client (async).

    Returns None if Redis is not configured or connection fails.
    This allows graceful degradation when Redis is unavailable.

    Returns:
        Redis client instance or None if not available
    """
    global _redis_client, _redis_pool

    # Return None if Redis URL not configured
    if not settings.redis_url or settings.redis_url == "redis://localhost:6379/0":
        logger.debug("Redis not configured, caching disabled")
        return None

    # Return existing client if already connected
    if _redis_client:
        return _redis_client

    # Create new connection
    try:
        if not _redis_pool:
            _redis_pool = ConnectionPool.from_url(
                settings.redis_url,
                decode_responses=False,  # Keep as bytes for PDF caching
                max_connections=20,
            )

        _redis_client = Redis(connection_pool=_redis_pool)

        # Test connection
        await _redis_client.ping()
        logger.info("Redis connection established")

        return _redis_client

    except Exception as e:
        logger.warning(f"Redis connection failed: {e}, caching disabled")
        _redis_client = None
        return None


async def close_redis():
    """Close Redis connection and cleanup resources."""
    global _redis_client, _redis_pool

    if _redis_client:
        try:
            await _redis_client.aclose()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")
        finally:
            _redis_client = None

    if _redis_pool:
        try:
            await _redis_pool.aclose()
        except Exception as e:
            logger.warning(f"Error closing Redis pool: {e}")
        finally:
            _redis_pool = None
