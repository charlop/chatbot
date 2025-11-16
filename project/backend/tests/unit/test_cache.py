"""
Unit tests for Redis cache utilities.
Tests cache operations, statistics tracking, and error handling.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from app.utils.cache import (
    get_redis,
    cache_get,
    cache_set,
    cache_delete,
    cache_delete_pattern,
    get_cache_stats,
    reset_cache_stats,
)


@pytest.mark.unit
class TestCacheOperations:
    """Tests for basic cache operations."""

    @pytest.mark.asyncio
    async def test_cache_get_hit(self):
        """Test cache get with hit."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps({"test": "data"}).encode()

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            result = await cache_get("test_key")

        assert result == {"test": "data"}
        mock_redis.get.assert_awaited_once_with("test_key")

    @pytest.mark.asyncio
    async def test_cache_get_miss(self):
        """Test cache get with miss."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            result = await cache_get("test_key")

        assert result is None
        mock_redis.get.assert_awaited_once_with("test_key")

    @pytest.mark.asyncio
    async def test_cache_get_redis_unavailable(self):
        """Test cache get when Redis unavailable."""
        with patch("app.utils.cache.get_redis", return_value=None):
            result = await cache_get("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_get_error_handling(self):
        """Test cache get handles errors gracefully."""
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Redis error")

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            result = await cache_get("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_set_success(self):
        """Test cache set."""
        mock_redis = AsyncMock()
        mock_redis.setex.return_value = True

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            result = await cache_set("test_key", {"test": "data"}, ttl=300)

        assert result is True
        mock_redis.setex.assert_awaited_once()
        # Verify setex was called with key, ttl, and serialized value
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "test_key"
        assert call_args[0][1] == 300
        assert json.loads(call_args[0][2]) == {"test": "data"}

    @pytest.mark.asyncio
    async def test_cache_set_with_default_ttl(self):
        """Test cache set uses default TTL when not specified."""
        mock_redis = AsyncMock()
        mock_redis.setex.return_value = True

        with (
            patch("app.utils.cache.get_redis", return_value=mock_redis),
            patch("app.utils.cache.settings.redis_ttl_default", 900),
        ):
            result = await cache_set("test_key", {"test": "data"})

        assert result is True
        # Verify default TTL was used
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 900

    @pytest.mark.asyncio
    async def test_cache_set_redis_unavailable(self):
        """Test cache set when Redis unavailable."""
        with patch("app.utils.cache.get_redis", return_value=None):
            result = await cache_set("test_key", {"test": "data"})

        assert result is False

    @pytest.mark.asyncio
    async def test_cache_set_error_handling(self):
        """Test cache set handles errors gracefully."""
        mock_redis = AsyncMock()
        mock_redis.setex.side_effect = Exception("Redis error")

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            result = await cache_set("test_key", {"test": "data"})

        assert result is False

    @pytest.mark.asyncio
    async def test_cache_delete_success(self):
        """Test cache delete."""
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            result = await cache_delete("test_key")

        assert result is True
        mock_redis.delete.assert_awaited_once_with("test_key")

    @pytest.mark.asyncio
    async def test_cache_delete_redis_unavailable(self):
        """Test cache delete when Redis unavailable."""
        with patch("app.utils.cache.get_redis", return_value=None):
            result = await cache_delete("test_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_cache_delete_error_handling(self):
        """Test cache delete handles errors gracefully."""
        mock_redis = AsyncMock()
        mock_redis.delete.side_effect = Exception("Redis error")

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            result = await cache_delete("test_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_cache_delete_pattern_success(self):
        """Test cache delete pattern."""
        mock_redis = AsyncMock()

        # Mock scan_iter to return an async generator
        async def mock_scan_iter(match):
            keys = [b"contract:1", b"contract:2", b"contract:3"]
            for key in keys:
                yield key

        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete.return_value = 3

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            result = await cache_delete_pattern("contract:*")

        assert result == 3
        mock_redis.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cache_delete_pattern_no_matches(self):
        """Test cache delete pattern with no matches."""
        mock_redis = AsyncMock()

        # Mock scan_iter to return no keys
        async def async_iter(keys):
            for key in keys:
                yield key

        mock_redis.scan_iter.return_value = async_iter([])

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            result = await cache_delete_pattern("contract:*")

        assert result == 0
        mock_redis.scan_iter.assert_called_once()
        mock_redis.delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cache_delete_pattern_redis_unavailable(self):
        """Test cache delete pattern when Redis unavailable."""
        with patch("app.utils.cache.get_redis", return_value=None):
            result = await cache_delete_pattern("contract:*")

        assert result == 0

    @pytest.mark.asyncio
    async def test_cache_delete_pattern_error_handling(self):
        """Test cache delete pattern handles errors gracefully."""
        mock_redis = AsyncMock()
        mock_redis.scan_iter.side_effect = Exception("Redis error")

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            result = await cache_delete_pattern("contract:*")

        assert result == 0


@pytest.mark.unit
class TestCacheStatistics:
    """Tests for cache statistics tracking."""

    def test_get_cache_stats_initial(self):
        """Test getting cache stats when empty."""
        reset_cache_stats()  # Reset to ensure clean state
        stats = get_cache_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["errors"] == 0
        assert stats["total_requests"] == 0
        assert stats["hit_rate"] == 0

    @pytest.mark.asyncio
    async def test_cache_stats_track_hits(self):
        """Test cache stats track hits."""
        reset_cache_stats()

        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps({"test": "data"}).encode()

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            await cache_get("test_key")
            await cache_get("test_key")
            await cache_get("test_key")

        stats = get_cache_stats()
        assert stats["hits"] == 3
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 100.0

    @pytest.mark.asyncio
    async def test_cache_stats_track_misses(self):
        """Test cache stats track misses."""
        reset_cache_stats()

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            await cache_get("test_key")
            await cache_get("test_key")

        stats = get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_cache_stats_track_errors(self):
        """Test cache stats track errors."""
        reset_cache_stats()

        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Redis error")

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            await cache_get("test_key")
            await cache_get("test_key")

        stats = get_cache_stats()
        assert stats["errors"] == 2

    @pytest.mark.asyncio
    async def test_cache_stats_hit_rate_calculation(self):
        """Test cache stats hit rate calculation."""
        reset_cache_stats()

        mock_redis = AsyncMock()

        # 3 hits
        mock_redis.get.return_value = json.dumps({"test": "data"}).encode()
        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            await cache_get("key1")
            await cache_get("key2")
            await cache_get("key3")

        # 2 misses
        mock_redis.get.return_value = None
        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            await cache_get("key4")
            await cache_get("key5")

        stats = get_cache_stats()
        assert stats["hits"] == 3
        assert stats["misses"] == 2
        assert stats["total_requests"] == 5
        assert stats["hit_rate"] == 60.0  # 3/5 * 100

    def test_reset_cache_stats(self):
        """Test resetting cache stats."""
        reset_cache_stats()
        stats = get_cache_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["errors"] == 0


@pytest.mark.unit
class TestRedisConnection:
    """Tests for Redis connection management."""

    @pytest.mark.asyncio
    async def test_get_redis_not_configured(self):
        """Test get_redis when URL not configured."""
        with patch("app.utils.cache.settings.redis_url", "redis://localhost:6379/0"):
            result = await get_redis()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_redis_connection_failure(self):
        """Test get_redis handles connection failure gracefully."""
        with (
            patch("app.utils.cache.settings.redis_url", "redis://badhost:6379/0"),
            patch("app.utils.cache._redis_client", None),
            patch("app.utils.cache.Redis") as mock_redis_class,
        ):
            # Mock connection to fail
            mock_redis_instance = AsyncMock()
            mock_redis_instance.ping.side_effect = Exception("Connection failed")
            mock_redis_class.return_value = mock_redis_instance

            result = await get_redis()

        # Should return None on connection failure
        assert result is None
