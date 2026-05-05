"""Redis cache for frequently-read, rarely-written data."""

import contextlib
import json

from app.infrastructure.config import REDIS_URL
from app.infrastructure.request_context import get_logger

logger = get_logger(__name__)

_cache: RedisCache | NoOpCache | None = None


class RedisCache:
    """Simple Redis cache with JSON serialization and pattern-based invalidation."""

    def __init__(self, redis_url: str, prefix: str = 'cache'):
        import redis.asyncio as redis

        self.prefix = prefix
        self.redis = redis.from_url(
            redis_url, decode_responses=True, socket_connect_timeout=5, socket_timeout=5
        )

    async def connect(self) -> None:
        """Test the Redis connection."""
        try:
            await self.redis.ping()
            logger.info('Redis cache connected')
        except Exception as e:
            logger.warning(
                'Redis cache unavailable, caching disabled',
                extra={'error': str(e)},
            )
            self.redis = None

    def _key(self, key: str) -> str:
        return f'{self.prefix}:{key}'

    async def get(self, key: str) -> dict | list | None:
        """Get a cached value. Returns None on miss or error."""
        if not self.redis:
            return None
        try:
            data = await self.redis.get(self._key(key))
            if data:
                return json.loads(data)
        except Exception:
            pass
        return None

    async def set(self, key: str, value: dict | list, ttl_seconds: int) -> None:
        """Cache a value with TTL. Silently fails on error."""
        if not self.redis:
            return
        with contextlib.suppress(Exception):
            await self.redis.setex(self._key(key), ttl_seconds, json.dumps(value))

    async def delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching a pattern. Used for cache invalidation."""
        if not self.redis:
            return
        try:
            full_pattern = self._key(pattern)
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=full_pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            pass


class NoOpCache:
    """No-op cache for when Redis is unavailable (memory mode)."""

    async def get(self, key: str) -> None:
        return None

    async def set(self, key: str, value: dict | list, ttl_seconds: int) -> None:
        pass

    async def delete_pattern(self, pattern: str) -> None:
        pass


async def init_cache() -> None:
    """Initialize the global cache instance."""
    global _cache
    if REDIS_URL:
        _cache = RedisCache(REDIS_URL)
        await _cache.connect()
    else:
        _cache = NoOpCache()
        logger.info('No REDIS_URL configured, using no-op cache')


def get_cache() -> RedisCache | NoOpCache:
    """Get the global cache instance."""
    if _cache is None:
        raise RuntimeError('Cache not initialized. Call init_cache() first.')
    return _cache


async def invalidate_store_cache() -> None:
    """Invalidate all store-related cache entries."""
    await get_cache().delete_pattern('store*')
