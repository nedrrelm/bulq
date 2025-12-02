"""Global exception handlers for FastAPI application."""

import traceback

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import AppException
from app.errors.models import ErrorDetail, ErrorResponse, ValidationErrorResponse
from app.infrastructure.request_context import get_logger

logger = get_logger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions.

    Returns error codes for frontend localization instead of human-readable messages.
    The message is logged internally but not sent to the client.

    Args:
        request: The FastAPI request
        exc: The application exception

    Returns:
        JSONResponse with error code and details (no message)
    """
    logger.warning(
        f'Application error: {exc.message}',
        extra={
            'error_type': exc.__class__.__name__,
            'error_code': exc.code,
            'status_code': exc.status_code,
            'path': request.url.path,
            'method': request.method,
            'details': exc.details,
        },
    )

    error_response = ErrorResponse(
        error=exc.__class__.__name__,
        code=exc.code,
        message=exc.message,  # For internal logging/debugging only
        details=exc.details,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json'),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError | PydanticValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Args:
        request: The FastAPI request
        exc: The validation exception

    Returns:
        JSONResponse with validation error details
    """
    errors = []
    for error in exc.errors():
        field = '.'.join(str(loc) for loc in error['loc'][1:])  # Skip 'body' prefix
        errors.append(
            ErrorDetail(
                field=field if field else None,
                message=error['msg'],
                code=error['type'],
            )
        )

    # Log validation errors details for debugging
    error_details = [{'field': e.field, 'message': e.message, 'code': e.code} for e in errors]
    logger.warning(
        f'Validation error on {request.url.path}: {error_details}',
        extra={
            'path': request.url.path,
            'method': request.method,
            'error_count': len(errors),
            'errors': error_details,
        },
    )

    error_response = ValidationErrorResponse(
        error='ValidationError',
        code='VALIDATION_ERROR',
        message='Request validation failed',
        errors=errors,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode='json'),
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors.

    Args:
        request: The FastAPI request
        exc: The SQLAlchemy exception

    Returns:
        JSONResponse with error details
    """
    logger.error(
        f'Database error: {str(exc)}',
        extra={
            'error_type': exc.__class__.__name__,
            'path': request.url.path,
            'method': request.method,
        },
        exc_info=True,
    )

    # Don't expose internal database errors to clients
    error_response = ErrorResponse(
        error='DatabaseError',
        code='DATABASE_ERROR',
        message='A database error occurred while processing your request',
        details={'error_type': exc.__class__.__name__},
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json'),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.

    Args:
        request: The FastAPI request
        exc: The exception

    Returns:
        JSONResponse with error details
    """
    # Log full traceback for debugging
    logger.error(
        f'Unhandled exception: {str(exc)}',
        extra={
            'error_type': exc.__class__.__name__,
            'path': request.url.path,
            'method': request.method,
            # 'traceback': traceback.format_exc(),
            'error_message': str(exc),
        },
        exc_info=True,
    )

    # Don't expose internal errors to clients in production
    error_response = ErrorResponse(
        error='InternalServerError',
        code='INTERNAL_SERVER_ERROR',
        message='An unexpected error occurred while processing your request',
        details={'error_type': exc.__class__.__name__},
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json'),
    )
