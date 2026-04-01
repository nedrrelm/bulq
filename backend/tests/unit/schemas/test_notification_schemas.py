"""Unit tests for notification schemas."""

import pytest
from pydantic import ValidationError

from app.api.schemas.notification_schemas import (
    MarkAllReadResponse,
    NotificationResponse,
    UnreadCountResponse,
)


class TestNotificationResponse:
    """Tests for NotificationResponse schema."""

    def test_valid_notification_response(self):
        """Test creating valid notification response."""
        data = {
            'id': 'notif123',
            'type': 'run_state_changed',
            'data': {'run_id': 'run123', 'new_state': 'active'},
            'read': False,
            'created_at': '2024-01-01T00:00:00Z',
        }
        schema = NotificationResponse(**data)
        assert schema.id == 'notif123'
        assert schema.type == 'run_state_changed'
        assert schema.data == {'run_id': 'run123', 'new_state': 'active'}
        assert schema.read is False
        assert schema.created_at == '2024-01-01T00:00:00Z'

    def test_notification_response_read(self):
        """Test notification response marked as read."""
        data = {
            'id': 'notif123',
            'type': 'run_state_changed',
            'data': {},
            'read': True,
            'created_at': '2024-01-01T00:00:00Z',
        }
        schema = NotificationResponse(**data)
        assert schema.read is True

    def test_notification_response_empty_data(self):
        """Test notification response with empty data dict."""
        data = {
            'id': 'notif123',
            'type': 'custom_type',
            'data': {},
            'read': False,
            'created_at': '2024-01-01T00:00:00Z',
        }
        schema = NotificationResponse(**data)
        assert schema.data == {}

    def test_notification_response_complex_data(self):
        """Test notification response with complex data structure."""
        data = {
            'id': 'notif123',
            'type': 'run_state_changed',
            'data': {
                'run_id': 'run123',
                'old_state': 'planning',
                'new_state': 'active',
                'group_id': 'group123',
                'store_name': 'Costco',
            },
            'read': False,
            'created_at': '2024-01-01T00:00:00Z',
        }
        schema = NotificationResponse(**data)
        assert schema.data['run_id'] == 'run123'
        assert schema.data['old_state'] == 'planning'
        assert schema.data['new_state'] == 'active'

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'id': 'notif123',
            'type': 'run_state_changed',
            'data': {},
        }
        with pytest.raises(ValidationError) as exc_info:
            NotificationResponse(**data)
        errors = str(exc_info.value)
        assert 'read' in errors or 'created_at' in errors

    def test_serialization(self):
        """Test schema serialization."""
        schema = NotificationResponse(
            id='notif123',
            type='run_state_changed',
            data={'run_id': 'run123'},
            read=False,
            created_at='2024-01-01T00:00:00Z',
        )
        data = schema.model_dump()
        assert data['id'] == 'notif123'
        assert data['type'] == 'run_state_changed'
        assert data['read'] is False


class TestUnreadCountResponse:
    """Tests for UnreadCountResponse schema."""

    def test_valid_unread_count_response_zero(self):
        """Test creating valid unread count response with zero count."""
        data = {'count': 0}
        schema = UnreadCountResponse(**data)
        assert schema.count == 0

    def test_valid_unread_count_response_positive(self):
        """Test creating valid unread count response with positive count."""
        data = {'count': 5}
        schema = UnreadCountResponse(**data)
        assert schema.count == 5

    def test_valid_unread_count_response_large_number(self):
        """Test creating valid unread count response with large count."""
        data = {'count': 9999}
        schema = UnreadCountResponse(**data)
        assert schema.count == 9999

    def test_missing_count(self):
        """Test missing count raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UnreadCountResponse()
        assert 'count' in str(exc_info.value)

    def test_serialization(self):
        """Test schema serialization."""
        schema = UnreadCountResponse(count=10)
        data = schema.model_dump()
        assert data == {'count': 10}


class TestMarkAllReadResponse:
    """Tests for MarkAllReadResponse schema."""

    def test_valid_mark_all_read_response(self):
        """Test creating valid mark all read response."""
        data = {
            'success': True,
            'code': 'ALL_NOTIFICATIONS_MARKED_READ',
            'count': 5,
            'details': {'marked_count': 5},
        }
        schema = MarkAllReadResponse(**data)
        assert schema.success is True
        assert schema.code == 'ALL_NOTIFICATIONS_MARKED_READ'
        assert schema.count == 5
        assert schema.details == {'marked_count': 5}

    def test_mark_all_read_response_zero_count(self):
        """Test mark all read response with zero count."""
        data = {
            'success': True,
            'code': 'NO_NOTIFICATIONS_TO_MARK',
            'count': 0,
            'details': {},
        }
        schema = MarkAllReadResponse(**data)
        assert schema.count == 0
        assert schema.details == {}

    def test_default_success_value(self):
        """Test default value for success is True."""
        data = {
            'code': 'ALL_NOTIFICATIONS_MARKED_READ',
            'count': 5,
        }
        schema = MarkAllReadResponse(**data)
        assert schema.success is True

    def test_default_details_empty_dict(self):
        """Test default value for details is empty dict."""
        data = {
            'code': 'ALL_NOTIFICATIONS_MARKED_READ',
            'count': 5,
        }
        schema = MarkAllReadResponse(**data)
        assert schema.details == {}

    def test_mark_all_read_response_with_empty_details(self):
        """Test mark all read response with explicit empty details."""
        data = {
            'success': True,
            'code': 'ALL_NOTIFICATIONS_MARKED_READ',
            'count': 10,
            'details': {},
        }
        schema = MarkAllReadResponse(**data)
        assert schema.details == {}

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'success': True,
        }
        with pytest.raises(ValidationError) as exc_info:
            MarkAllReadResponse(**data)
        errors = str(exc_info.value)
        assert 'code' in errors or 'count' in errors

    def test_serialization(self):
        """Test schema serialization."""
        schema = MarkAllReadResponse(
            success=True,
            code='ALL_NOTIFICATIONS_MARKED_READ',
            count=3,
            details={'key': 'value'},
        )
        data = schema.model_dump()
        assert data['success'] is True
        assert data['code'] == 'ALL_NOTIFICATIONS_MARKED_READ'
        assert data['count'] == 3
        assert data['details'] == {'key': 'value'}
