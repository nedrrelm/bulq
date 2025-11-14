"""Custom exception classes for the application.

This module provides a hierarchy of custom exceptions with automatic
status code mapping and simplified construction.

All exceptions now use error codes for frontend localization instead of
human-readable messages. Messages are kept for internal logging only.
"""

from typing import Any

from fastapi import status


class AppException(Exception):
    """Base exception for all application errors.

    Attributes:
        code: Machine-readable error code for frontend localization
        message: Human-readable error message (for logging only, not sent to frontend)
        status_code: HTTP status code for the error
        details: Additional context about the error
    """

    # Default status code (can be overridden by subclasses)
    default_status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(
        self,
        code: str,
        message: str | None = None,
        status_code: int | None = None,
        **details: Any,
    ):
        """Initialize application exception.

        Args:
            code: Error code for frontend localization (required)
            message: Optional error message for internal logging (auto-generated if not provided)
            status_code: Optional HTTP status code (uses default if not provided)
            **details: Additional error context as keyword arguments
        """
        self.code = code
        self.message = message or f'Error: {code}'
        self.status_code = status_code or self.default_status_code
        self.details = details
        super().__init__(self.message)


class NotFoundError(AppException):
    """Raised when a resource is not found (HTTP 404).

    Usage:
        raise NotFoundError(code='RUN_NOT_FOUND', run_id=str(run_id))
        raise NotFoundError(code='USER_NOT_FOUND', user_id=str(user_id))
    """

    default_status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, code: str, message: str | None = None, **details: Any):
        """Initialize NotFoundError.

        Args:
            code: Error code (e.g., 'RUN_NOT_FOUND', 'USER_NOT_FOUND')
            message: Optional message for logging
            **details: Additional context (e.g., run_id="123", user_id="456")
        """
        super().__init__(code=code, message=message, **details)


class UnauthorizedError(AppException):
    """Raised when authentication is required but not provided (HTTP 401).

    Usage:
        raise UnauthorizedError(code='AUTH_REQUIRED')
        raise UnauthorizedError(code='AUTH_SESSION_EXPIRED')
    """

    default_status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self, code: str = 'AUTH_REQUIRED', message: str | None = None, **details: Any):
        """Initialize UnauthorizedError.

        Args:
            code: Error code (defaults to 'AUTH_REQUIRED')
            message: Optional message for logging
            **details: Additional context
        """
        super().__init__(code=code, message=message, **details)


class ForbiddenError(AppException):
    """Raised when user doesn't have permission to perform an action (HTTP 403).

    Usage:
        raise ForbiddenError(code='NOT_RUN_LEADER', run_id=str(run_id))
        raise ForbiddenError(code='NOT_GROUP_ADMIN', group_id=str(group_id))
    """

    default_status_code = status.HTTP_403_FORBIDDEN

    def __init__(
        self, code: str = 'INSUFFICIENT_PERMISSIONS', message: str | None = None, **details: Any
    ):
        """Initialize ForbiddenError.

        Args:
            code: Error code (defaults to 'INSUFFICIENT_PERMISSIONS')
            message: Optional message for logging
            **details: Additional context
        """
        super().__init__(code=code, message=message, **details)


class ValidationError(AppException):
    """Raised when business logic validation fails (HTTP 422).

    Usage:
        raise ValidationError(code='PRODUCT_NAME_EMPTY')
        raise ValidationError(code='BID_QUANTITY_NEGATIVE', quantity=-5)
    """

    default_status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    def __init__(self, code: str, message: str | None = None, **details: Any):
        """Initialize ValidationError.

        Args:
            code: Error code (e.g., 'PRODUCT_NAME_EMPTY', 'BID_QUANTITY_NEGATIVE')
            message: Optional message for logging
            **details: Additional context (e.g., field='name', quantity=-5)
        """
        super().__init__(code=code, message=message, **details)


class ConflictError(AppException):
    """Raised when an operation conflicts with current state (HTTP 409).

    Usage:
        raise ConflictError(code='ALREADY_GROUP_MEMBER', group_id=str(group_id))
        raise ConflictError(code='USERNAME_TAKEN', username=username)
    """

    default_status_code = status.HTTP_409_CONFLICT

    def __init__(self, code: str, message: str | None = None, **details: Any):
        """Initialize ConflictError.

        Args:
            code: Error code (e.g., 'ALREADY_GROUP_MEMBER', 'USERNAME_TAKEN')
            message: Optional message for logging
            **details: Additional context
        """
        super().__init__(code=code, message=message, **details)


class BadRequestError(AppException):
    """Raised when request data is invalid (HTTP 400).

    Usage:
        raise BadRequestError(code='INVALID_ID_FORMAT')
        raise BadRequestError(code='RUN_MAX_PRODUCTS_EXCEEDED', max_products=50)
    """

    default_status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, code: str, message: str | None = None, **details: Any):
        """Initialize BadRequestError.

        Args:
            code: Error code (e.g., 'INVALID_ID_FORMAT', 'RUN_MAX_PRODUCTS_EXCEEDED')
            message: Optional message for logging
            **details: Additional context
        """
        super().__init__(code=code, message=message, **details)


class ConfigurationError(AppException):
    """Raised when application configuration is invalid (HTTP 500).

    This is for internal configuration errors during app initialization or setup,
    not user-facing errors.

    Usage:
        raise ConfigurationError(code='INVALID_REPO_MODE', repo_mode='invalid')
        raise ConfigurationError(code='DATABASE_SESSION_REQUIRED')
    """

    default_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, code: str, message: str | None = None, **details: Any):
        """Initialize ConfigurationError.

        Args:
            code: Error code (e.g., 'DATABASE_SESSION_REQUIRED', 'INVALID_REPO_MODE')
            message: Optional message for logging
            **details: Additional context
        """
        super().__init__(code=code, message=message, **details)
