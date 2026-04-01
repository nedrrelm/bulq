"""Unit tests for reassignment schemas."""

import pytest
from pydantic import ValidationError

from app.api.schemas.reassignment_schemas import (
    MyRequestsResponse,
    ReassignmentDetailResponse,
    ReassignmentRequestModel,
    ReassignmentResponse,
    RunRequestResponse,
)


class TestReassignmentRequestModel:
    """Tests for ReassignmentRequestModel schema."""

    def test_valid_reassignment_request(self):
        """Test creating valid reassignment request."""
        data = {
            'run_id': 'run123',
            'to_user_id': 'user456',
        }
        schema = ReassignmentRequestModel(**data)
        assert schema.run_id == 'run123'
        assert schema.to_user_id == 'user456'

    def test_missing_run_id(self):
        """Test missing run_id raises ValidationError."""
        data = {'to_user_id': 'user456'}
        with pytest.raises(ValidationError) as exc_info:
            ReassignmentRequestModel(**data)
        assert 'run_id' in str(exc_info.value)

    def test_missing_to_user_id(self):
        """Test missing to_user_id raises ValidationError."""
        data = {'run_id': 'run123'}
        with pytest.raises(ValidationError) as exc_info:
            ReassignmentRequestModel(**data)
        assert 'to_user_id' in str(exc_info.value)

    def test_serialization(self):
        """Test schema serialization."""
        schema = ReassignmentRequestModel(run_id='run123', to_user_id='user456')
        data = schema.model_dump()
        assert data == {'run_id': 'run123', 'to_user_id': 'user456'}


class TestReassignmentResponse:
    """Tests for ReassignmentResponse schema."""

    def test_valid_reassignment_response(self):
        """Test creating valid reassignment response."""
        data = {
            'id': 'request123',
            'run_id': 'run123',
            'from_user_id': 'user123',
            'to_user_id': 'user456',
            'status': 'pending',
            'created_at': '2024-01-01T00:00:00Z',
            'resolved_at': None,
        }
        schema = ReassignmentResponse(**data)
        assert schema.id == 'request123'
        assert schema.run_id == 'run123'
        assert schema.from_user_id == 'user123'
        assert schema.to_user_id == 'user456'
        assert schema.status == 'pending'
        assert schema.created_at == '2024-01-01T00:00:00Z'
        assert schema.resolved_at is None

    def test_reassignment_response_with_resolved_at(self):
        """Test reassignment response with resolved_at timestamp."""
        data = {
            'id': 'request123',
            'run_id': 'run123',
            'from_user_id': 'user123',
            'to_user_id': 'user456',
            'status': 'accepted',
            'created_at': '2024-01-01T00:00:00Z',
            'resolved_at': '2024-01-02T00:00:00Z',
        }
        schema = ReassignmentResponse(**data)
        assert schema.status == 'accepted'
        assert schema.resolved_at == '2024-01-02T00:00:00Z'

    def test_default_resolved_at_none(self):
        """Test default value for resolved_at is None."""
        data = {
            'id': 'request123',
            'run_id': 'run123',
            'from_user_id': 'user123',
            'to_user_id': 'user456',
            'status': 'pending',
            'created_at': '2024-01-01T00:00:00Z',
        }
        schema = ReassignmentResponse(**data)
        assert schema.resolved_at is None


class TestReassignmentDetailResponse:
    """Tests for ReassignmentDetailResponse schema."""

    def test_valid_reassignment_detail_response(self):
        """Test creating valid reassignment detail response."""
        data = {
            'id': 'request123',
            'run_id': 'run123',
            'from_user_id': 'user123',
            'from_user_name': 'John Doe',
            'to_user_id': 'user456',
            'to_user_name': 'Jane Smith',
            'store_name': 'Costco',
            'status': 'pending',
            'created_at': '2024-01-01T00:00:00Z',
        }
        schema = ReassignmentDetailResponse(**data)
        assert schema.id == 'request123'
        assert schema.run_id == 'run123'
        assert schema.from_user_name == 'John Doe'
        assert schema.to_user_name == 'Jane Smith'
        assert schema.store_name == 'Costco'
        assert schema.status == 'pending'

    def test_reassignment_detail_accepted_status(self):
        """Test reassignment detail with accepted status."""
        data = {
            'id': 'request123',
            'run_id': 'run123',
            'from_user_id': 'user123',
            'from_user_name': 'John Doe',
            'to_user_id': 'user456',
            'to_user_name': 'Jane Smith',
            'store_name': 'Costco',
            'status': 'accepted',
            'created_at': '2024-01-01T00:00:00Z',
        }
        schema = ReassignmentDetailResponse(**data)
        assert schema.status == 'accepted'

    def test_reassignment_detail_declined_status(self):
        """Test reassignment detail with declined status."""
        data = {
            'id': 'request123',
            'run_id': 'run123',
            'from_user_id': 'user123',
            'from_user_name': 'John Doe',
            'to_user_id': 'user456',
            'to_user_name': 'Jane Smith',
            'store_name': 'Costco',
            'status': 'declined',
            'created_at': '2024-01-01T00:00:00Z',
        }
        schema = ReassignmentDetailResponse(**data)
        assert schema.status == 'declined'

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'id': 'request123',
            'run_id': 'run123',
            'from_user_id': 'user123',
            'from_user_name': 'John Doe',
        }
        with pytest.raises(ValidationError) as exc_info:
            ReassignmentDetailResponse(**data)
        errors = str(exc_info.value)
        assert 'to_user_id' in errors or 'to_user_name' in errors


class TestMyRequestsResponse:
    """Tests for MyRequestsResponse schema."""

    def test_valid_my_requests_response(self):
        """Test creating valid my requests response."""
        data = {
            'sent': [
                {
                    'id': 'req1',
                    'run_id': 'run1',
                    'from_user_id': 'user123',
                    'from_user_name': 'John',
                    'to_user_id': 'user456',
                    'to_user_name': 'Jane',
                    'store_name': 'Costco',
                    'status': 'pending',
                    'created_at': '2024-01-01T00:00:00Z',
                }
            ],
            'received': [
                {
                    'id': 'req2',
                    'run_id': 'run2',
                    'from_user_id': 'user789',
                    'from_user_name': 'Bob',
                    'to_user_id': 'user123',
                    'to_user_name': 'John',
                    'store_name': 'Walmart',
                    'status': 'pending',
                    'created_at': '2024-01-02T00:00:00Z',
                }
            ],
        }
        schema = MyRequestsResponse(**data)
        assert len(schema.sent) == 1
        assert len(schema.received) == 1
        assert schema.sent[0].id == 'req1'
        assert schema.received[0].id == 'req2'

    def test_my_requests_response_empty_lists(self):
        """Test my requests response with empty lists."""
        data = {
            'sent': [],
            'received': [],
        }
        schema = MyRequestsResponse(**data)
        assert schema.sent == []
        assert schema.received == []

    def test_my_requests_response_only_sent(self):
        """Test my requests response with only sent requests."""
        data = {
            'sent': [
                {
                    'id': 'req1',
                    'run_id': 'run1',
                    'from_user_id': 'user123',
                    'from_user_name': 'John',
                    'to_user_id': 'user456',
                    'to_user_name': 'Jane',
                    'store_name': 'Costco',
                    'status': 'pending',
                    'created_at': '2024-01-01T00:00:00Z',
                }
            ],
            'received': [],
        }
        schema = MyRequestsResponse(**data)
        assert len(schema.sent) == 1
        assert len(schema.received) == 0

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'sent': [],
        }
        with pytest.raises(ValidationError) as exc_info:
            MyRequestsResponse(**data)
        assert 'received' in str(exc_info.value)


class TestRunRequestResponse:
    """Tests for RunRequestResponse schema."""

    def test_valid_run_request_response_with_request(self):
        """Test creating valid run request response with request."""
        data = {
            'request': {
                'id': 'req1',
                'run_id': 'run1',
                'from_user_id': 'user123',
                'from_user_name': 'John',
                'to_user_id': 'user456',
                'to_user_name': 'Jane',
                'store_name': 'Costco',
                'status': 'pending',
                'created_at': '2024-01-01T00:00:00Z',
            }
        }
        schema = RunRequestResponse(**data)
        assert schema.request is not None
        assert schema.request.id == 'req1'
        assert schema.request.status == 'pending'

    def test_valid_run_request_response_with_none(self):
        """Test creating valid run request response with None request."""
        data = {'request': None}
        schema = RunRequestResponse(**data)
        assert schema.request is None

    def test_serialization_with_none(self):
        """Test schema serialization with None request."""
        schema = RunRequestResponse(request=None)
        data = schema.model_dump()
        assert data == {'request': None}

    def test_serialization_with_request(self):
        """Test schema serialization with request."""
        schema = RunRequestResponse(
            request=ReassignmentDetailResponse(
                id='req1',
                run_id='run1',
                from_user_id='user123',
                from_user_name='John',
                to_user_id='user456',
                to_user_name='Jane',
                store_name='Costco',
                status='pending',
                created_at='2024-01-01T00:00:00Z',
            )
        )
        data = schema.model_dump()
        assert data['request']['id'] == 'req1'
        assert data['request']['status'] == 'pending'
