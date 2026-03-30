"""Session storage implementations for user authentication."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from typing import Any

from app.infrastructure.request_context import get_logger

logger = get_logger(__name__)


class SessionStore(ABC):
    """Abstract base class for session storage."""

    @abstractmethod
    def set(self, session_token: str, session_data: dict[str, Any], ttl_seconds: int) -> None:
        """Store session data with TTL."""
        pass

    @abstractmethod
    def get(self, session_token: str) -> dict[str, Any] | None:
        """Retrieve session data if exists and not expired."""
        pass

    @abstractmethod
    def delete(self, session_token: str) -> bool:
        """Delete session data. Returns True if existed, False otherwise."""
        pass


class InMemorySessionStore(SessionStore):
    """In-memory session storage (for development/testing)."""

    def __init__(self):
        """Initialize in-memory storage."""
        self.sessions: dict[str, dict[str, Any]] = {}

    def set(self, session_token: str, session_data: dict[str, Any], ttl_seconds: int) -> None:
        """Store session data with expiration."""
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        self.sessions[session_token] = {
            **session_data,
            'expires_at': expires_at,
        }

    def get(self, session_token: str) -> dict[str, Any] | None:
        """Retrieve session if exists and not expired."""
        if session_token not in self.sessions:
            return None

        session = self.sessions[session_token]

        # Check if expired
        if datetime.now(UTC) > session['expires_at']:
            del self.sessions[session_token]
            return None

        return session

    def delete(self, session_token: str) -> bool:
        """Delete session."""
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False


class RedisSessionStore(SessionStore):
    """Redis-backed session storage (for production)."""

    def __init__(self, redis_url: str):
        """Initialize Redis connection.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
        """
        import redis

        try:
            self.redis = redis.from_url(
                redis_url, decode_responses=True, socket_connect_timeout=5, socket_timeout=5
            )
            # Test connection
            self.redis.ping()
            logger.info('Redis session store connected', extra={'redis_url': redis_url})
        except Exception as e:
            logger.error(
                'Failed to connect to Redis',
                extra={'redis_url': redis_url, 'error': str(e)},
                exc_info=True,
            )
            raise

    def set(self, session_token: str, session_data: dict[str, Any], ttl_seconds: int) -> None:
        """Store session data with TTL using Redis hash."""
        try:
            # Store as Redis hash with expiration
            key = f'session:{session_token}'
            # Convert datetime objects to ISO format strings
            serialized_data = {}
            for k, v in session_data.items():
                if isinstance(v, datetime):
                    serialized_data[k] = v.isoformat()
                else:
                    serialized_data[k] = str(v)

            self.redis.hset(key, mapping=serialized_data)
            self.redis.expire(key, ttl_seconds)
        except Exception as e:
            logger.error(
                'Failed to store session in Redis',
                extra={'session_token': session_token[:8] + '...', 'error': str(e)},
                exc_info=True,
            )
            raise

    def get(self, session_token: str) -> dict[str, Any] | None:
        """Retrieve session data from Redis."""
        try:
            key = f'session:{session_token}'
            data = self.redis.hgetall(key)

            if not data:
                return None

            # Convert ISO strings back to datetime objects
            if 'expires_at' in data:
                data['expires_at'] = datetime.fromisoformat(data['expires_at'])
            if 'created_at' in data:
                data['created_at'] = datetime.fromisoformat(data['created_at'])

            return data
        except Exception as e:
            logger.error(
                'Failed to retrieve session from Redis',
                extra={'session_token': session_token[:8] + '...', 'error': str(e)},
                exc_info=True,
            )
            return None

    def delete(self, session_token: str) -> bool:
        """Delete session from Redis."""
        try:
            key = f'session:{session_token}'
            deleted = self.redis.delete(key)
            return deleted > 0
        except Exception as e:
            logger.error(
                'Failed to delete session from Redis',
                extra={'session_token': session_token[:8] + '...', 'error': str(e)},
                exc_info=True,
            )
            return False


def get_session_store() -> SessionStore:
    """Factory function to get appropriate session store based on configuration.

    Returns:
        SessionStore instance (Redis or in-memory)
    """
    from app.infrastructure.config import REDIS_URL, SESSION_STORE_TYPE

    if SESSION_STORE_TYPE == 'redis':
        if not REDIS_URL:
            logger.warning(
                'REDIS_URL not configured, falling back to in-memory session store',
                extra={'session_store_type': SESSION_STORE_TYPE},
            )
            return InMemorySessionStore()

        try:
            return RedisSessionStore(REDIS_URL)
        except Exception as e:
            logger.error(
                'Failed to initialize Redis session store, falling back to in-memory',
                extra={'error': str(e)},
                exc_info=True,
            )
            return InMemorySessionStore()
    else:
        return InMemorySessionStore()


# Global session store instance (initialized on first import)
_session_store: SessionStore | None = None


def init_session_store() -> SessionStore:
    """Initialize and return the global session store instance."""
    global _session_store
    if _session_store is None:
        _session_store = get_session_store()
    return _session_store


def get_store() -> SessionStore:
    """Get the global session store instance."""
    if _session_store is None:
        return init_session_store()
    return _session_store
