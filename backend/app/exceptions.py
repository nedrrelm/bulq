"""Custom exception classes for the application."""

from typing import Any

from fastapi import status


class AppException(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any | None] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: Any, details: dict[str, Any | None] = None):
        message = f'{resource} not found'
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details={'resource': resource, 'identifier': str(identifier), **(details or {})},
        )


class UnauthorizedError(AppException):
    """Raised when authentication is required but not provided."""

    def __init__(
        self, message: str = 'Authentication required', details: dict[str, Any | None] = None
    ):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED, details=details)


class ForbiddenError(AppException):
    """Raised when user doesn't have permission to perform an action."""

    def __init__(
        self, message: str = 'Insufficient permissions', details: dict[str, Any | None] = None
    ):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN, details=details)


class ValidationError(AppException):
    """Raised when business logic validation fails."""

    def __init__(
        self, message: str, field: str | None = None, details: dict[str, Any | None] = None
    ):
        extra_details = details or {}
        if field:
            extra_details['field'] = field
        super().__init__(
            message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=extra_details
        )


class ConflictError(AppException):
    """Raised when an operation conflicts with current state."""

    def __init__(self, message: str, details: dict[str, Any | None] = None):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT, details=details)


class BadRequestError(AppException):
    """Raised when request data is invalid."""

    def __init__(self, message: str, details: dict[str, Any | None] = None):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details)
