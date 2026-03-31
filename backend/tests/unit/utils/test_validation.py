"""Unit tests for validation utility functions.

Tests cover:
- validate_uuid() function with valid and invalid inputs
- Error handling and BadRequestError raising with proper error codes
- Custom resource_name parameter behavior
- UUID object return type and usability
"""

from uuid import UUID

import pytest

from app.core import error_codes
from app.core.exceptions import BadRequestError
from app.utils.validation import validate_uuid


class TestValidateUuid:
    """Test the validate_uuid() validation function."""

    def test_valid_uuid_returns_uuid_object(self):
        """Test that a valid UUID string returns a UUID object."""
        valid_uuid_str = 'f47ac10b-58cc-4372-a567-0e02b2c3d479'
        result = validate_uuid(valid_uuid_str)

        assert isinstance(result, UUID)
        assert str(result) == valid_uuid_str

    def test_valid_uuid_object_is_usable(self):
        """Test that the returned UUID object can be used normally."""
        valid_uuid_str = '550e8400-e29b-41d4-a716-446655440000'
        result = validate_uuid(valid_uuid_str)

        # Should be able to convert back to string
        assert str(result) == valid_uuid_str
        # Should be able to compare with another UUID
        assert result == UUID(valid_uuid_str)

    @pytest.mark.parametrize(
        'invalid_uuid',
        [
            'invalid-uuid-string',
            'not-a-uuid',
            '12345',
            'g47ac10b-58cc-4372-a567-0e02b2c3d479',  # Invalid hex character 'g'
            'f47ac10b-58cc-4372-a567-0e02b2c3d479-extra',  # Extra characters
            'f47ac10b-58cc-4372-a567',  # Too short
        ],
    )
    def test_invalid_uuid_raises_bad_request_error(self, invalid_uuid):
        """Test that invalid UUID strings raise BadRequestError."""
        with pytest.raises(BadRequestError) as exc_info:
            validate_uuid(invalid_uuid)

        # Verify it's a BadRequestError with correct error code
        assert exc_info.value.code == error_codes.INVALID_UUID_FORMAT

    def test_empty_string_raises_bad_request_error(self):
        """Test that an empty string raises BadRequestError."""
        with pytest.raises(BadRequestError) as exc_info:
            validate_uuid('')

        assert exc_info.value.code == error_codes.INVALID_UUID_FORMAT

    def test_none_raises_exception(self):
        """Test that None raises an exception (not BadRequestError)."""
        # None will raise AttributeError or TypeError before UUID validation
        with pytest.raises((AttributeError, TypeError)):
            validate_uuid(None)

    def test_error_includes_invalid_value_in_details(self):
        """Test that the error includes the invalid value in details."""
        invalid_uuid = 'definitely-not-a-uuid'

        with pytest.raises(BadRequestError) as exc_info:
            validate_uuid(invalid_uuid)

        # Check that the invalid value is included in the error
        error = exc_info.value
        assert error.details.get('value') == invalid_uuid

    def test_error_includes_correct_error_code(self):
        """Test that the error includes INVALID_UUID_FORMAT error code."""
        with pytest.raises(BadRequestError) as exc_info:
            validate_uuid('bad-uuid')

        assert exc_info.value.code == error_codes.INVALID_UUID_FORMAT

    def test_default_resource_name_in_error_message(self):
        """Test that the default resource_name 'ID' is used in error message."""
        with pytest.raises(BadRequestError) as exc_info:
            validate_uuid('invalid')

        error = exc_info.value
        assert 'ID' in error.message
        assert error.details.get('field') == 'id'

    def test_custom_resource_name_in_error_message(self):
        """Test that custom resource_name is used in error message and field."""
        with pytest.raises(BadRequestError) as exc_info:
            validate_uuid('invalid', resource_name='Group')

        error = exc_info.value
        assert 'Group' in error.message
        assert error.details.get('field') == 'group'

    @pytest.mark.parametrize(
        'resource_name,expected_field',
        [
            ('Group', 'group'),
            ('Run', 'run'),
            ('User', 'user'),
            ('Product', 'product'),
        ],
    )
    def test_various_resource_names(self, resource_name, expected_field):
        """Test that various resource names are properly used in error details."""
        with pytest.raises(BadRequestError) as exc_info:
            validate_uuid('bad-uuid', resource_name=resource_name)

        error = exc_info.value
        assert resource_name in error.message
        assert error.details.get('field') == expected_field

    def test_uppercase_uuid_is_valid(self):
        """Test that uppercase UUID strings are valid."""
        uppercase_uuid = 'F47AC10B-58CC-4372-A567-0E02B2C3D479'
        result = validate_uuid(uppercase_uuid)

        assert isinstance(result, UUID)
        # UUID normalizes to lowercase
        assert str(result) == uppercase_uuid.lower()

    def test_mixed_case_uuid_is_valid(self):
        """Test that mixed case UUID strings are valid."""
        mixed_case_uuid = 'F47ac10b-58CC-4372-A567-0e02b2c3d479'
        result = validate_uuid(mixed_case_uuid)

        assert isinstance(result, UUID)
        assert str(result) == mixed_case_uuid.lower()
