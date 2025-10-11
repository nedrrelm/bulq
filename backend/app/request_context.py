"""Request context management using contextvars for request ID propagation."""

import logging
from contextvars import ContextVar
from typing import Optional
from uuid import uuid4

# Context variable for request ID (thread-safe)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def set_request_id(request_id: str) -> None:
    """
    Set the request ID in the current context.

    Args:
        request_id: The request ID to set
    """
    request_id_var.set(request_id)


def get_request_id() -> Optional[str]:
    """
    Get the request ID from the current context.

    Returns:
        The request ID if set, None otherwise
    """
    return request_id_var.get()


def generate_request_id() -> str:
    """
    Generate a new request ID.

    Returns:
        A new UUID-based request ID
    """
    return str(uuid4())


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger that automatically includes request ID in logs.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return RequestContextLogger(logging.getLogger(name))


class RequestContextLogger:
    """
    Logger wrapper that automatically adds request_id to all log calls.

    This ensures request ID is included in all structured logs without
    manually adding it to every log call.
    """

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _add_request_id(self, extra: Optional[dict] = None) -> dict:
        """Add request_id to extra dict if available in context."""
        if extra is None:
            extra = {}

        request_id = get_request_id()
        if request_id and 'request_id' not in extra:
            extra['request_id'] = request_id

        return extra

    def debug(self, msg: str, *args, extra: Optional[dict] = None, **kwargs) -> None:
        """Log debug message with request_id."""
        self._logger.debug(msg, *args, extra=self._add_request_id(extra), **kwargs)

    def info(self, msg: str, *args, extra: Optional[dict] = None, **kwargs) -> None:
        """Log info message with request_id."""
        self._logger.info(msg, *args, extra=self._add_request_id(extra), **kwargs)

    def warning(self, msg: str, *args, extra: Optional[dict] = None, **kwargs) -> None:
        """Log warning message with request_id."""
        self._logger.warning(msg, *args, extra=self._add_request_id(extra), **kwargs)

    def error(self, msg: str, *args, extra: Optional[dict] = None, **kwargs) -> None:
        """Log error message with request_id."""
        self._logger.error(msg, *args, extra=self._add_request_id(extra), **kwargs)

    def critical(self, msg: str, *args, extra: Optional[dict] = None, **kwargs) -> None:
        """Log critical message with request_id."""
        self._logger.critical(msg, *args, extra=self._add_request_id(extra), **kwargs)

    def exception(self, msg: str, *args, extra: Optional[dict] = None, **kwargs) -> None:
        """Log exception with request_id."""
        self._logger.exception(msg, *args, extra=self._add_request_id(extra), **kwargs)

    # Delegate attribute access to underlying logger
    def __getattr__(self, name: str):
        return getattr(self._logger, name)
