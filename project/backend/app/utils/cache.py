"""
Redis Cache Utilities

Provides async Redis connection and caching utilities.
"""

import json
import logging
from typing import Optional, Any
from functools import wraps

from redis.asyncio import Redis, ConnectionPool
from app.config import settings

logger = logging.getLogger(__name__)

# Global Redis connection pool
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[Redis] = None

# Cache hit/miss tracking for monitoring
_cache_stats = {
    "hits": 0,
    "misses": 0,
    "errors": 0,
}


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


async def cache_get(key: str) -> Optional[Any]:
    """
    Get value from cache.

    Args:
        key: Cache key

    Returns:
        Cached value (JSON deserialized) or None if not found
    """
    redis = await get_redis()
    if not redis:
        return None

    try:
        value = await redis.get(key)
        if value:
            _cache_stats["hits"] += 1
            logger.debug(f"Cache HIT: {key}")
            # Deserialize JSON
            return json.loads(value)
        else:
            _cache_stats["misses"] += 1
            logger.debug(f"Cache MISS: {key}")
            return None

    except Exception as e:
        _cache_stats["errors"] += 1
        logger.warning(f"Cache get error for key {key}: {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int = None) -> bool:
    """
    Set value in cache with optional TTL.

    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl: Time-to-live in seconds (uses default if None)

    Returns:
        True if set successfully, False otherwise
    """
    redis = await get_redis()
    if not redis:
        return False

    try:
        # Serialize to JSON
        serialized_value = json.dumps(
            value, default=str
        )  # default=str handles datetime, Decimal, etc.

        # Use provided TTL or default
        ttl_seconds = ttl if ttl is not None else settings.redis_ttl_default

        await redis.setex(key, ttl_seconds, serialized_value)
        logger.debug(f"Cache SET: {key} (TTL: {ttl_seconds}s)")
        return True

    except Exception as e:
        _cache_stats["errors"] += 1
        logger.warning(f"Cache set error for key {key}: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """
    Delete value from cache.

    Args:
        key: Cache key to delete

    Returns:
        True if deleted successfully, False otherwise
    """
    redis = await get_redis()
    if not redis:
        return False

    try:
        await redis.delete(key)
        logger.debug(f"Cache DELETE: {key}")
        return True

    except Exception as e:
        _cache_stats["errors"] += 1
        logger.warning(f"Cache delete error for key {key}: {e}")
        return False


async def cache_delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching pattern.

    Args:
        pattern: Pattern to match (e.g., "contract:*")

    Returns:
        Number of keys deleted
    """
    redis = await get_redis()
    if not redis:
        return 0

    try:
        # Find all matching keys
        keys = []
        async for key in redis.scan_iter(match=pattern):
            keys.append(key)

        # Delete all matching keys
        if keys:
            deleted_count = await redis.delete(*keys)
            logger.debug(f"Cache DELETE pattern: {pattern} ({deleted_count} keys)")
            return deleted_count

        return 0

    except Exception as e:
        _cache_stats["errors"] += 1
        logger.warning(f"Cache delete pattern error for {pattern}: {e}")
        return 0


def get_cache_stats() -> dict:
    """
    Get cache hit/miss statistics.

    Returns:
        dict with hits, misses, errors, and hit_rate
    """
    total = _cache_stats["hits"] + _cache_stats["misses"]
    hit_rate = (_cache_stats["hits"] / total * 100) if total > 0 else 0

    return {
        "hits": _cache_stats["hits"],
        "misses": _cache_stats["misses"],
        "errors": _cache_stats["errors"],
        "total_requests": total,
        "hit_rate": round(hit_rate, 2),
    }


def reset_cache_stats():
    """Reset cache statistics."""
    global _cache_stats
    _cache_stats = {
        "hits": 0,
        "misses": 0,
        "errors": 0,
    }
    logger.info("Cache statistics reset")
