import secrets
from datetime import UTC, datetime

import bcrypt

from app.infrastructure.config import SESSION_EXPIRY_HOURS
from app.infrastructure.request_context import get_logger
from app.infrastructure.session_store import get_store

logger = get_logger(__name__)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except ValueError, TypeError:
        return False


def create_session(user_id: str) -> str:
    """Create a new session and return session token."""
    session_token = secrets.token_urlsafe(32)
    session_data = {
        'user_id': user_id,
        'expires_at': datetime.now(UTC),
        'created_at': datetime.now(UTC),
    }

    # Store with TTL in seconds
    ttl_seconds = SESSION_EXPIRY_HOURS * 3600
    store = get_store()
    store.set(session_token, session_data, ttl_seconds)

    return session_token


def get_session(session_token: str) -> dict | None:
    """Get session data if valid, None if expired or invalid."""
    store = get_store()
    return store.get(session_token)


def delete_session(session_token: str) -> bool:
    """Delete a session (logout)."""
    store = get_store()
    return store.delete(session_token)
