"""Redis cache for frequently-read, rarely-written data."""

import contextlib
import json

from app.infrastructure.config import REDIS_URL
from app.infrastructure.request_context import get_logger

logger = get_logger(__name__)

_cache: RedisCache | None = None


class RedisCache:
    """Simple Redis cache with JSON serialization and pattern-based invalidation."""

    def __init__(self, redis_url: str, prefix: str = 'cache'):
        import redis

        self.prefix = prefix
        try:
            self.redis = redis.from_url(
                redis_url, decode_responses=True, socket_connect_timeout=5, socket_timeout=5
            )
            self.redis.ping()
            logger.info('Redis cache connected', extra={'redis_url': redis_url})
        except Exception as e:
            logger.warning(
                'Redis cache unavailable, caching disabled',
                extra={'error': str(e)},
            )
            self.redis = None

    def _key(self, key: str) -> str:
        return f'{self.prefix}:{key}'

    def get(self, key: str) -> dict | list | None:
        """Get a cached value. Returns None on miss or error."""
        if not self.redis:
            return None
        try:
            data = self.redis.get(self._key(key))
            if data:
                return json.loads(data)
        except Exception:
            pass
        return None

    def set(self, key: str, value: dict | list, ttl_seconds: int) -> None:
        """Cache a value with TTL. Silently fails on error."""
        if not self.redis:
            return
        with contextlib.suppress(Exception):
            self.redis.setex(self._key(key), ttl_seconds, json.dumps(value))

    def delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching a pattern. Used for cache invalidation."""
        if not self.redis:
            return
        try:
            full_pattern = self._key(pattern)
            cursor = 0
            while True:
                cursor, keys = self.redis.scan(cursor, match=full_pattern, count=100)
                if keys:
                    self.redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            pass


class NoOpCache:
    """No-op cache for when Redis is unavailable (memory mode)."""

    def get(self, key: str) -> None:
        return None

    def set(self, key: str, value: dict | list, ttl_seconds: int) -> None:
        pass

    def delete_pattern(self, pattern: str) -> None:
        pass


def init_cache() -> None:
    """Initialize the global cache instance."""
    global _cache
    if REDIS_URL:
        _cache = RedisCache(REDIS_URL)
    else:
        _cache = NoOpCache()
        logger.info('No REDIS_URL configured, using no-op cache')


def get_cache() -> RedisCache | NoOpCache:
    """Get the global cache instance."""
    if _cache is None:
        init_cache()
    return _cache


def invalidate_store_cache() -> None:
    """Invalidate all store-related cache entries."""
    get_cache().delete_pattern('store*')
