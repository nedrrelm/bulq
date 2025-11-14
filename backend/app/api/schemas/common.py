"""Common schemas used across multiple domains."""

from typing import Any

from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    """Standardized success response structure.

    The 'code' field contains a machine-readable success code for frontend localization.
    The frontend should translate the code into user-facing text.
    """

    success: bool = Field(True, description='Always true for success responses')
    code: str = Field(..., description='Machine-readable success code for frontend localization')
    details: dict[str, Any] = Field(default_factory=dict, description='Additional context data')

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            'example': {
                'success': True,
                'code': 'BID_PLACED',
                'details': {
                    'run_id': '123e4567-e89b-12d3-a456-426614174000',
                    'product_id': '123e4567-e89b-12d3-a456-426614174001',
                    'quantity': 5.0,
                },
            }
        }
