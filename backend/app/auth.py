import secrets
from datetime import datetime, timedelta

import bcrypt

from app.config import SESSION_EXPIRY_HOURS
from app.request_context import get_logger

logger = get_logger(__name__)

# In-memory session storage (use Redis in production)
sessions: dict[str, dict] = {}


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


def create_session(user_id: str) -> str:
    """Create a new session and return session token."""
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=SESSION_EXPIRY_HOURS)

    sessions[session_token] = {
        'user_id': user_id,
        'expires_at': expires_at,
        'created_at': datetime.now(),
    }

    return session_token


def get_session(session_token: str) -> dict | None:
    """Get session data if valid, None if expired or invalid."""
    if session_token not in sessions:
        return None

    session = sessions[session_token]

    # Check if session is expired
    if datetime.now() > session['expires_at']:
        del sessions[session_token]
        return None

    return session


def delete_session(session_token: str) -> bool:
    """Delete a session (logout)."""
    if session_token in sessions:
        del sessions[session_token]
        return True
    return False


def cleanup_expired_sessions() -> int:
    """Remove expired sessions from memory.

    Returns:
        Number of sessions cleaned up
    """
    now = datetime.now()
    expired_tokens = [token for token, session in sessions.items() if now > session['expires_at']]

    for token in expired_tokens:
        del sessions[token]

    if expired_tokens:
        logger.info(
            'Cleaned up expired sessions',
            extra={'expired_count': len(expired_tokens), 'active_count': len(sessions)},
        )

    return len(expired_tokens)
