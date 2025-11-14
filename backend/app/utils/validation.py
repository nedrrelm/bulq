"""Validation helper functions for common validation patterns.

This module provides validation helpers that delegate to the state machine
for consistent state validation across the application.
"""

from uuid import UUID

from app.core import error_codes
from app.core.exceptions import BadRequestError


def validate_uuid(id_str: str, resource_name: str = 'ID') -> UUID:
    """Validate and convert a string to UUID.

    Args:
        id_str: The string to convert to UUID
        resource_name: Name of the resource for error message (e.g., "Group", "Run", "User")

    Returns:
        UUID object

    Raises:
        BadRequestError: If the string is not a valid UUID format
    """
    try:
        return UUID(id_str)
    except ValueError as e:
        raise BadRequestError(
            code=error_codes.INVALID_UUID_FORMAT,
            message=f'Invalid {resource_name} ID format',
            field=resource_name.lower(),
            value=id_str,
        ) from e
