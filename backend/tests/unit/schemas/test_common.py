"""Unit tests for common schemas."""

import pytest
from pydantic import ValidationError

from app.api.schemas.common import SuccessResponse


class TestSuccessResponse:
    """Tests for SuccessResponse schema."""

    def test_valid_success_response(self):
        """Test creating valid success response."""
        data = {
            'success': True,
            'code': 'BID_PLACED',
            'details': {'run_id': 'run123', 'product_id': 'prod123', 'quantity': 5.0},
        }
        schema = SuccessResponse(**data)
        assert schema.success is True
        assert schema.code == 'BID_PLACED'
        assert schema.details == {
            'run_id': 'run123',
            'product_id': 'prod123',
            'quantity': 5.0,
        }

    def test_success_response_with_empty_details(self):
        """Test success response with empty details dict."""
        data = {
            'success': True,
            'code': 'OPERATION_SUCCESS',
            'details': {},
        }
        schema = SuccessResponse(**data)
        assert schema.details == {}

    def test_default_success_value(self):
        """Test default value for success is True."""
        data = {
            'code': 'OPERATION_SUCCESS',
            'details': {},
        }
        schema = SuccessResponse(**data)
        assert schema.success is True

    def test_default_details_empty_dict(self):
        """Test default value for details is empty dict."""
        data = {
            'success': True,
            'code': 'OPERATION_SUCCESS',
        }
        schema = SuccessResponse(**data)
        assert schema.details == {}

    def test_success_false(self):
        """Test success response with success=False (should still validate)."""
        data = {
            'success': False,
            'code': 'OPERATION_FAILED',
            'details': {'error': 'Some error'},
        }
        schema = SuccessResponse(**data)
        assert schema.success is False
        assert schema.code == 'OPERATION_FAILED'

    def test_missing_code(self):
        """Test missing code raises ValidationError."""
        data = {
            'success': True,
            'details': {},
        }
        with pytest.raises(ValidationError) as exc_info:
            SuccessResponse(**data)
        assert 'code' in str(exc_info.value)

    def test_complex_details_structure(self):
        """Test success response with complex details structure."""
        data = {
            'success': True,
            'code': 'STATE_CHANGED',
            'details': {
                'run_id': 'run123',
                'old_state': 'planning',
                'new_state': 'active',
                'participants': ['user1', 'user2', 'user3'],
                'metadata': {'timestamp': '2024-01-01T00:00:00Z', 'trigger': 'auto'},
            },
        }
        schema = SuccessResponse(**data)
        assert schema.details['run_id'] == 'run123'
        assert schema.details['participants'] == ['user1', 'user2', 'user3']
        assert schema.details['metadata']['timestamp'] == '2024-01-01T00:00:00Z'

    def test_serialization(self):
        """Test schema serialization."""
        schema = SuccessResponse(success=True, code='OPERATION_SUCCESS', details={'key': 'value'})
        data = schema.model_dump()
        assert data == {
            'success': True,
            'code': 'OPERATION_SUCCESS',
            'details': {'key': 'value'},
        }

    def test_deserialization(self):
        """Test schema deserialization from dict."""
        data = {
            'success': True,
            'code': 'TEST_CODE',
            'details': {'test': 'data'},
        }
        schema = SuccessResponse.model_validate(data)
        assert schema.success is True
        assert schema.code == 'TEST_CODE'
        assert schema.details == {'test': 'data'}
