"""Unit tests for success code constants.

Tests cover:
- All success codes are strings
- Known success codes exist in the module
- No duplicate success code values
- Success code constants follow naming conventions
"""

import pytest

from app.core import success_codes


class TestSuccessCodesExist:
    """Test that known success codes exist and are strings."""

    @pytest.mark.parametrize(
        'success_code_name',
        [
            'OPERATION_SUCCESSFUL',
            'RESOURCE_CREATED',
            'USER_REGISTERED',
            'RUN_CREATED',
            'BID_PLACED',
            'GROUP_JOINED',
            'NOTIFICATION_MARKED_READ',
            'DISTRIBUTION_COMPLETED',
        ],
    )
    def test_known_success_code_exists(self, success_code_name):
        """Test that specific known success codes exist in the module."""
        assert hasattr(success_codes, success_code_name)

    @pytest.mark.parametrize(
        'success_code_name',
        [
            'OPERATION_SUCCESSFUL',
            'RESOURCE_CREATED',
            'USER_REGISTERED',
            'RUN_CREATED',
            'BID_PLACED',
            'GROUP_JOINED',
            'NOTIFICATION_MARKED_READ',
            'DISTRIBUTION_COMPLETED',
        ],
    )
    def test_known_success_code_is_string(self, success_code_name):
        """Test that specific known success codes are strings."""
        success_code_value = getattr(success_codes, success_code_name)
        assert isinstance(success_code_value, str)

    def test_all_success_codes_are_strings(self):
        """Test that all success code constants in the module are strings."""
        # Get all constants (uppercase attributes that don't start with underscore)
        constants = [
            name for name in dir(success_codes) if name.isupper() and not name.startswith('_')
        ]

        # Filter out SUCCESS_CODE_GROUPS which is a dict
        success_code_constants = [name for name in constants if name != 'SUCCESS_CODE_GROUPS']

        assert len(success_code_constants) > 0, 'No success code constants found'

        for constant_name in success_code_constants:
            constant_value = getattr(success_codes, constant_name)
            assert isinstance(constant_value, str), (
                f'{constant_name} is not a string: {type(constant_value)}'
            )

    def test_success_code_groups_is_dict(self):
        """Test that SUCCESS_CODE_GROUPS exists and is a dictionary."""
        assert hasattr(success_codes, 'SUCCESS_CODE_GROUPS')
        assert isinstance(success_codes.SUCCESS_CODE_GROUPS, dict)


class TestSuccessCodeUniqueness:
    """Test that success code values are unique (no duplicates)."""

    def test_no_duplicate_success_code_values(self):
        """Test that all success code values are unique across the module."""
        # Get all success code constants
        constants = [
            name
            for name in dir(success_codes)
            if name.isupper() and not name.startswith('_') and name != 'SUCCESS_CODE_GROUPS'
        ]

        # Collect all values
        success_code_values = []
        for constant_name in constants:
            value = getattr(success_codes, constant_name)
            if isinstance(value, str):
                success_code_values.append((constant_name, value))

        # Check for duplicates
        seen_values = {}
        duplicates = []

        for constant_name, value in success_code_values:
            if value in seen_values:
                duplicates.append(f'{value}: {seen_values[value]} and {constant_name}')
            else:
                seen_values[value] = constant_name

        assert len(duplicates) == 0, f'Found duplicate success code values: {duplicates}'

    def test_success_code_count(self):
        """Test that we have a reasonable number of success codes defined."""
        constants = [
            name
            for name in dir(success_codes)
            if name.isupper() and not name.startswith('_') and name != 'SUCCESS_CODE_GROUPS'
        ]

        success_code_count = len(constants)
        # Based on the success_codes.py file, we should have many success codes
        assert success_code_count > 30, (
            f'Expected more than 30 success codes, found {success_code_count}'
        )


class TestSuccessCodeNamingConventions:
    """Test that success codes follow naming conventions."""

    def test_success_codes_use_screaming_snake_case(self):
        """Test that success code constant names use SCREAMING_SNAKE_CASE."""
        constants = [
            name
            for name in dir(success_codes)
            if name.isupper() and not name.startswith('_') and name != 'SUCCESS_CODE_GROUPS'
        ]

        for constant_name in constants:
            # Should only contain uppercase letters, numbers, and underscores
            assert constant_name.replace('_', '').isalnum(), (
                f'{constant_name} does not follow SCREAMING_SNAKE_CASE convention'
            )
            assert constant_name.isupper(), f'{constant_name} is not all uppercase'

    def test_success_code_values_match_constant_names(self):
        """Test that success code values match their constant names."""
        constants = [
            name
            for name in dir(success_codes)
            if name.isupper() and not name.startswith('_') and name != 'SUCCESS_CODE_GROUPS'
        ]

        for constant_name in constants:
            value = getattr(success_codes, constant_name)
            if isinstance(value, str):
                assert value == constant_name, (
                    f'{constant_name} value "{value}" does not match constant name'
                )


class TestSuccessCodeGroups:
    """Test the SUCCESS_CODE_GROUPS documentation structure."""

    def test_success_code_groups_structure(self):
        """Test that SUCCESS_CODE_GROUPS has the expected structure."""
        groups = success_codes.SUCCESS_CODE_GROUPS

        assert len(groups) > 0, 'SUCCESS_CODE_GROUPS should not be empty'

        for group_name, success_list in groups.items():
            assert isinstance(group_name, str), f'Group name {group_name} is not a string'
            assert isinstance(success_list, list), f'Group {group_name} value is not a list'
            assert len(success_list) > 0, f'Group {group_name} is empty'

    def test_success_code_groups_contain_valid_codes(self):
        """Test that all codes in SUCCESS_CODE_GROUPS are valid success codes."""
        groups = success_codes.SUCCESS_CODE_GROUPS

        for group_name, success_list in groups.items():
            for success_code in success_list:
                assert isinstance(success_code, str), (
                    f'Success code in group {group_name} is not a string: {success_code}'
                )
                # The success code should exist as a module constant
                assert hasattr(success_codes, success_code), (
                    f'Success code {success_code} in group {group_name} does not exist in module'
                )
