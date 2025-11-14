"""Error response models for consistent API error responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed error information."""

    field: str | None = Field(None, description='Field that caused the error, if applicable')
    message: str = Field(..., description='Human-readable error message')
    code: str | None = Field(None, description='Machine-readable error code')


class ErrorResponse(BaseModel):
    """Standardized error response structure.

    The 'code' field contains a machine-readable error code for frontend localization.
    The 'message' field is kept for backward compatibility but should not be used
    for user-facing text - the frontend should translate the code instead.
    """

    success: bool = Field(False, description='Always false for errors')
    error: str = Field(..., description='Error type or category')
    code: str = Field(..., description='Machine-readable error code for frontend localization')
    message: str = Field(
        ..., description='Human-readable error message (for logging/debugging only)'
    )
    details: dict[str, Any] = Field(default_factory=dict, description='Additional error context')
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description='When the error occurred'
    )
    path: str | None = Field(None, description='Request path that caused the error')

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            'example': {
                'success': False,
                'error': 'NotFoundError',
                'code': 'RUN_NOT_FOUND',
                'message': 'Run not found',
                'details': {
                    'run_id': '123e4567-e89b-12d3-a456-426614174000',
                },
                'timestamp': '2025-10-06T12:34:56.789Z',
                'path': '/api/runs/123e4567-e89b-12d3-a456-426614174000',
            }
        }


class ValidationErrorResponse(ErrorResponse):
    """Error response for validation errors with field-specific details."""

    errors: list[ErrorDetail] = Field(default_factory=list, description='List of validation errors')

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            'example': {
                'success': False,
                'error': 'ValidationError',
                'message': 'Request validation failed',
                'errors': [
                    {
                        'field': 'quantity',
                        'message': 'Quantity must be non-negative',
                        'code': 'value_error.number.not_ge',
                    }
                ],
                'timestamp': '2025-10-06T12:34:56.789Z',
                'path': '/runs/123/bids',
            }
        }
