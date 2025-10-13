"""Custom exception classes for the application.

This module provides a hierarchy of custom exceptions with automatic
status code mapping and simplified construction.
"""

from typing import Any

from fastapi import status


class AppException(Exception):
    """Base exception for all application errors.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code for the error
        details: Additional context about the error
    """

    # Default status code (can be overridden by subclasses)
    default_status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize application exception.

        Args:
            message: Error message
            status_code: Optional HTTP status code (uses default if not provided)
            details: Optional additional error context
        """
        self.message = message
        self.status_code = status_code or self.default_status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """Raised when a resource is not found (HTTP 404)."""

    default_status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, resource: str, identifier: Any = None, details: dict[str, Any] | None = None):
        """Initialize NotFoundError.

        Args:
            resource: Type of resource not found (e.g., "User", "Run")
            identifier: Optional identifier that was searched for
            details: Optional additional context
        """
        message = f'{resource} not found'
        error_details = {'resource': resource}
        if identifier is not None:
            error_details['identifier'] = str(identifier)
        if details:
            error_details.update(details)
        super().__init__(message=message, details=error_details)


class UnauthorizedError(AppException):
    """Raised when authentication is required but not provided (HTTP 401)."""

    default_status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(
        self, message: str = 'Authentication required', details: dict[str, Any] | None = None
    ):
        """Initialize UnauthorizedError.

        Args:
            message: Error message
            details: Optional additional context
        """
        super().__init__(message=message, details=details)


class ForbiddenError(AppException):
    """Raised when user doesn't have permission to perform an action (HTTP 403)."""

    default_status_code = status.HTTP_403_FORBIDDEN

    def __init__(
        self, message: str = 'Insufficient permissions', details: dict[str, Any] | None = None
    ):
        """Initialize ForbiddenError.

        Args:
            message: Error message
            details: Optional additional context
        """
        super().__init__(message=message, details=details)


class ValidationError(AppException):
    """Raised when business logic validation fails (HTTP 422)."""

    default_status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    def __init__(
        self, message: str, field: str | None = None, details: dict[str, Any] | None = None
    ):
        """Initialize ValidationError.

        Args:
            message: Error message
            field: Optional field name that failed validation
            details: Optional additional context
        """
        error_details = details.copy() if details else {}
        if field:
            error_details['field'] = field
        super().__init__(message=message, details=error_details)


class ConflictError(AppException):
    """Raised when an operation conflicts with current state (HTTP 409)."""

    default_status_code = status.HTTP_409_CONFLICT

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """Initialize ConflictError.

        Args:
            message: Error message
            details: Optional additional context
        """
        super().__init__(message=message, details=details)


class BadRequestError(AppException):
    """Raised when request data is invalid (HTTP 400)."""

    default_status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """Initialize BadRequestError.

        Args:
            message: Error message
            details: Optional additional context
        """
        super().__init__(message=message, details=details)
