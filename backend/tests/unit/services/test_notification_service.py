"""Unit tests for NotificationService."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.core.error_codes import (
    INVALID_UUID_FORMAT,
    NOT_NOTIFICATION_OWNER,
    NOTIFICATION_MARK_READ_FAILED,
    NOTIFICATION_NOT_FOUND,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import Notification
from app.services.notification_service import NotificationService


class TestGetUserNotifications:
    """Test cases for NotificationService.get_user_notifications()."""

    async def test_get_user_notifications_success(self, test_user):
        """Test successfully getting user notifications."""
        # Arrange
        mock_db = AsyncMock()
        notif_id = uuid4()

        mock_notification = Mock(spec=Notification)
        mock_notification.id = notif_id
        mock_notification.type = 'run_state_changed'
        mock_notification.data = {'run_id': str(uuid4())}
        mock_notification.read = False
        mock_notification.created_at = datetime.now()

        service = NotificationService(mock_db)
        service.notification_repo.get_user_notifications = AsyncMock(
            return_value=[mock_notification]
        )

        # Act
        result = await service.get_user_notifications(test_user, limit=20, offset=0)

        # Assert
        assert len(result) == 1
        assert result[0].id == str(notif_id)
        assert result[0].type == 'run_state_changed'
        assert result[0].read is False

    async def test_get_user_notifications_empty(self, test_user):
        """Test getting notifications when user has none."""
        # Arrange
        mock_db = AsyncMock()
        service = NotificationService(mock_db)
        service.notification_repo.get_user_notifications = AsyncMock(return_value=[])

        # Act
        result = await service.get_user_notifications(test_user, limit=20, offset=0)

        # Assert
        assert result == []


class TestGetUnreadNotifications:
    """Test cases for NotificationService.get_unread_notifications()."""

    async def test_get_unread_notifications_success(self, test_user):
        """Test successfully getting unread notifications."""
        # Arrange
        mock_db = AsyncMock()
        mock_notification = Mock(spec=Notification)
        mock_notification.id = uuid4()
        mock_notification.type = 'run_state_changed'
        mock_notification.data = {}
        mock_notification.read = False
        mock_notification.created_at = datetime.now()

        service = NotificationService(mock_db)
        service.notification_repo.get_unread_notifications = AsyncMock(
            return_value=[mock_notification]
        )

        # Act
        result = await service.get_unread_notifications(test_user)

        # Assert
        assert len(result) == 1
        assert result[0].read is False


class TestGetUnreadCount:
    """Test cases for NotificationService.get_unread_count()."""

    async def test_get_unread_count_success(self, test_user):
        """Test successfully getting unread count."""
        # Arrange
        mock_db = AsyncMock()
        service = NotificationService(mock_db)
        service.notification_repo.get_unread_count = AsyncMock(return_value=5)

        # Act
        result = await service.get_unread_count(test_user)

        # Assert
        assert result == 5

    async def test_get_unread_count_zero(self, test_user):
        """Test getting count when there are no unread notifications."""
        # Arrange
        mock_db = AsyncMock()
        service = NotificationService(mock_db)
        service.notification_repo.get_unread_count = AsyncMock(return_value=0)

        # Act
        result = await service.get_unread_count(test_user)

        # Assert
        assert result == 0


class TestMarkAsRead:
    """Test cases for NotificationService.mark_as_read()."""

    async def test_mark_as_read_success(self, test_user):
        """Test successfully marking notification as read."""
        # Arrange
        mock_db = AsyncMock()
        notif_id = uuid4()

        mock_notification = Mock(spec=Notification)
        mock_notification.id = notif_id
        mock_notification.user_id = test_user.id

        service = NotificationService(mock_db)
        service.notification_repo.get_notification_by_id = AsyncMock(return_value=mock_notification)
        service.notification_repo.mark_notification_as_read = AsyncMock(return_value=True)

        # Act
        result = await service.mark_as_read(str(notif_id), test_user)

        # Assert
        assert result.details['notification_id'] == str(notif_id)
        service.notification_repo.mark_notification_as_read.assert_called_once_with(notif_id)

    async def test_mark_as_read_invalid_uuid(self, test_user):
        """Test marking as read with invalid UUID."""
        # Arrange
        mock_db = AsyncMock()
        service = NotificationService(mock_db)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.mark_as_read('invalid-uuid', test_user)

        assert exc_info.value.code == INVALID_UUID_FORMAT

    async def test_mark_as_read_not_found(self, test_user):
        """Test marking as read for non-existent notification."""
        # Arrange
        mock_db = AsyncMock()
        notif_id = uuid4()

        service = NotificationService(mock_db)
        service.notification_repo.get_notification_by_id = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.mark_as_read(str(notif_id), test_user)

        assert exc_info.value.code == NOTIFICATION_NOT_FOUND

    async def test_mark_as_read_not_owner(self, test_user):
        """Test marking as read when user doesn't own notification."""
        # Arrange
        mock_db = AsyncMock()
        notif_id = uuid4()
        other_user_id = uuid4()

        mock_notification = Mock(spec=Notification)
        mock_notification.id = notif_id
        mock_notification.user_id = other_user_id

        service = NotificationService(mock_db)
        service.notification_repo.get_notification_by_id = AsyncMock(return_value=mock_notification)

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            await service.mark_as_read(str(notif_id), test_user)

        assert exc_info.value.code == NOT_NOTIFICATION_OWNER

    async def test_mark_as_read_fails(self, test_user):
        """Test handling when marking as read fails."""
        # Arrange
        mock_db = AsyncMock()
        notif_id = uuid4()

        mock_notification = Mock(spec=Notification)
        mock_notification.id = notif_id
        mock_notification.user_id = test_user.id

        service = NotificationService(mock_db)
        service.notification_repo.get_notification_by_id = AsyncMock(return_value=mock_notification)
        service.notification_repo.mark_notification_as_read = AsyncMock(return_value=False)

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await service.mark_as_read(str(notif_id), test_user)

        assert exc_info.value.code == NOTIFICATION_MARK_READ_FAILED


class TestMarkAllAsRead:
    """Test cases for NotificationService.mark_all_as_read()."""

    async def test_mark_all_as_read_success(self, test_user):
        """Test successfully marking all notifications as read."""
        # Arrange
        mock_db = AsyncMock()
        service = NotificationService(mock_db)
        service.notification_repo.mark_all_notifications_as_read = AsyncMock(return_value=5)

        # Act
        result = await service.mark_all_as_read(test_user)

        # Assert
        assert result.count == 5
        assert result.details['user_id'] == str(test_user.id)

    async def test_mark_all_as_read_zero_count(self, test_user):
        """Test marking all as read when there are no unread notifications."""
        # Arrange
        mock_db = AsyncMock()
        service = NotificationService(mock_db)
        service.notification_repo.mark_all_notifications_as_read = AsyncMock(return_value=0)

        # Act
        result = await service.mark_all_as_read(test_user)

        # Assert
        assert result.count == 0
