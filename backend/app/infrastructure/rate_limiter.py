"""Rate limiting configuration using slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.infrastructure.config import REDIS_URL
from app.infrastructure.request_context import get_logger

logger = get_logger(__name__)


def _get_client_ip(request: Request) -> str:
    """Extract client IP from X-Forwarded-For header or fall back to remote address."""
    forwarded_for = request.headers.get('x-forwarded-for')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return get_remote_address(request)


# Initialize limiter with Redis backend if available, otherwise in-memory
_storage_uri = REDIS_URL if REDIS_URL else 'memory://'

limiter = Limiter(
    key_func=_get_client_ip,
    storage_uri=_storage_uri,
    default_limits=['100/minute'],
)

logger.info('Rate limiter initialized', extra={'storage': 'redis' if REDIS_URL else 'memory'})
