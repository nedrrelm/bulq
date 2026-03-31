"""Unit tests for error code constants.

Tests cover:
- All error codes are strings
- Known error codes exist in the module
- No duplicate error code values
- Error code constants follow naming conventions
"""

import pytest

from app.core import error_codes


class TestErrorCodesExist:
    """Test that known error codes exist and are strings."""

    @pytest.mark.parametrize(
        'error_code_name',
        [
            'INVALID_UUID_FORMAT',
            'RUN_NOT_FOUND',
            'GROUP_NOT_FOUND',
            'USER_NOT_FOUND',
            'AUTH_REQUIRED',
            'INSUFFICIENT_PERMISSIONS',
            'INVALID_RUN_STATE_TRANSITION',
            'BID_QUANTITY_NEGATIVE',
            'RESOURCE_NOT_FOUND',
            'VALIDATION_FAILED',
        ],
    )
    def test_known_error_code_exists(self, error_code_name):
        """Test that specific known error codes exist in the module."""
        assert hasattr(error_codes, error_code_name)

    @pytest.mark.parametrize(
        'error_code_name',
        [
            'INVALID_UUID_FORMAT',
            'RUN_NOT_FOUND',
            'GROUP_NOT_FOUND',
            'USER_NOT_FOUND',
            'AUTH_REQUIRED',
            'INSUFFICIENT_PERMISSIONS',
            'INVALID_RUN_STATE_TRANSITION',
            'BID_QUANTITY_NEGATIVE',
            'RESOURCE_NOT_FOUND',
            'VALIDATION_FAILED',
        ],
    )
    def test_known_error_code_is_string(self, error_code_name):
        """Test that specific known error codes are strings."""
        error_code_value = getattr(error_codes, error_code_name)
        assert isinstance(error_code_value, str)

    def test_all_error_codes_are_strings(self):
        """Test that all error code constants in the module are strings."""
        # Get all constants (uppercase attributes that don't start with underscore)
        constants = [
            name for name in dir(error_codes) if name.isupper() and not name.startswith('_')
        ]

        # Filter out ERROR_CODE_GROUPS which is a dict
        error_code_constants = [name for name in constants if name != 'ERROR_CODE_GROUPS']

        assert len(error_code_constants) > 0, 'No error code constants found'

        for constant_name in error_code_constants:
            constant_value = getattr(error_codes, constant_name)
            assert isinstance(constant_value, str), (
                f'{constant_name} is not a string: {type(constant_value)}'
            )

    def test_error_code_groups_is_dict(self):
        """Test that ERROR_CODE_GROUPS exists and is a dictionary."""
        assert hasattr(error_codes, 'ERROR_CODE_GROUPS')
        assert isinstance(error_codes.ERROR_CODE_GROUPS, dict)


class TestErrorCodeUniqueness:
    """Test that error code values are unique (no duplicates)."""

    def test_no_duplicate_error_code_values(self):
        """Test that all error code values are unique across the module."""
        # Get all error code constants
        constants = [
            name
            for name in dir(error_codes)
            if name.isupper() and not name.startswith('_') and name != 'ERROR_CODE_GROUPS'
        ]

        # Collect all values
        error_code_values = []
        for constant_name in constants:
            value = getattr(error_codes, constant_name)
            if isinstance(value, str):
                error_code_values.append((constant_name, value))

        # Check for duplicates
        seen_values = {}
        duplicates = []

        for constant_name, value in error_code_values:
            if value in seen_values:
                duplicates.append(f'{value}: {seen_values[value]} and {constant_name}')
            else:
                seen_values[value] = constant_name

        assert len(duplicates) == 0, f'Found duplicate error code values: {duplicates}'

    def test_error_code_count(self):
        """Test that we have a reasonable number of error codes defined."""
        constants = [
            name
            for name in dir(error_codes)
            if name.isupper() and not name.startswith('_') and name != 'ERROR_CODE_GROUPS'
        ]

        error_code_count = len(constants)
        # Based on the error_codes.py file, we should have many error codes
        assert error_code_count > 50, f'Expected more than 50 error codes, found {error_code_count}'


class TestErrorCodeNamingConventions:
    """Test that error codes follow naming conventions."""

    def test_error_codes_use_screaming_snake_case(self):
        """Test that error code constant names use SCREAMING_SNAKE_CASE."""
        constants = [
            name
            for name in dir(error_codes)
            if name.isupper() and not name.startswith('_') and name != 'ERROR_CODE_GROUPS'
        ]

        for constant_name in constants:
            # Should only contain uppercase letters, numbers, and underscores
            assert constant_name.replace('_', '').isalnum(), (
                f'{constant_name} does not follow SCREAMING_SNAKE_CASE convention'
            )
            assert constant_name.isupper(), f'{constant_name} is not all uppercase'

    def test_error_code_values_match_constant_names(self):
        """Test that error code values match their constant names."""
        constants = [
            name
            for name in dir(error_codes)
            if name.isupper() and not name.startswith('_') and name != 'ERROR_CODE_GROUPS'
        ]

        for constant_name in constants:
            value = getattr(error_codes, constant_name)
            if isinstance(value, str):
                assert value == constant_name, (
                    f'{constant_name} value "{value}" does not match constant name'
                )


class TestErrorCodeGroups:
    """Test the ERROR_CODE_GROUPS documentation structure."""

    def test_error_code_groups_structure(self):
        """Test that ERROR_CODE_GROUPS has the expected structure."""
        groups = error_codes.ERROR_CODE_GROUPS

        assert len(groups) > 0, 'ERROR_CODE_GROUPS should not be empty'

        for group_name, error_list in groups.items():
            assert isinstance(group_name, str), f'Group name {group_name} is not a string'
            assert isinstance(error_list, list), f'Group {group_name} value is not a list'
            assert len(error_list) > 0, f'Group {group_name} is empty'

    def test_error_code_groups_contain_valid_codes(self):
        """Test that all codes in ERROR_CODE_GROUPS are valid error codes."""
        groups = error_codes.ERROR_CODE_GROUPS

        for group_name, error_list in groups.items():
            for error_code in error_list:
                assert isinstance(error_code, str), (
                    f'Error code in group {group_name} is not a string: {error_code}'
                )
                # The error code should exist as a module constant
                assert hasattr(error_codes, error_code), (
                    f'Error code {error_code} in group {group_name} does not exist in module'
                )
