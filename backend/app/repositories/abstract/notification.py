"""Abstract notification repository interface."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.core.models import Notification


class AbstractNotificationRepository(ABC):
    """Abstract base class for notification repository operations."""

    @abstractmethod
    def create_notification(self, user_id: UUID, type: str, data: dict[str, Any]) -> Notification:
        """Create a new notification for a user."""
        raise NotImplementedError('Subclass must implement create_notification')

    @abstractmethod
    def get_user_notifications(
        self, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[Notification]:
        """Get notifications for a user (paginated)."""
        raise NotImplementedError('Subclass must implement get_user_notifications')

    @abstractmethod
    def get_unread_notifications(self, user_id: UUID) -> list[Notification]:
        """Get all unread notifications for a user."""
        raise NotImplementedError('Subclass must implement get_unread_notifications')

    @abstractmethod
    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user."""
        raise NotImplementedError('Subclass must implement get_unread_count')

    @abstractmethod
    def mark_notification_as_read(self, notification_id: UUID) -> bool:
        """Mark a notification as read."""
        raise NotImplementedError('Subclass must implement mark_notification_as_read')

    @abstractmethod
    def mark_all_notifications_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user. Returns count of marked notifications."""
        raise NotImplementedError('Subclass must implement mark_all_notifications_as_read')

    @abstractmethod
    def get_notification_by_id(self, notification_id: UUID) -> Notification | None:
        """Get a notification by ID."""
        raise NotImplementedError('Subclass must implement get_notification_by_id')
