"""Memory notification repository implementation."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.core.models import Notification
from app.repositories.abstract.notification import AbstractNotificationRepository
from app.repositories.memory.storage import MemoryStorage


class MemoryNotificationRepository(AbstractNotificationRepository):
    """Memory implementation of notification repository."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    def create_notification(self, user_id: UUID, type: str, data: dict[str, Any]) -> Notification:
        """Create a new notification for a user."""
        notification = Notification(
            id=uuid4(),
            user_id=user_id,
            type=type,
            data=data,
            read=False,
            created_at=datetime.now(UTC),
        )
        self.storage.notifications[notification.id] = notification
        return notification

    def get_user_notifications(
        self, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[Notification]:
        """Get notifications for a user (paginated)."""
        user_notifications = [n for n in self.storage.notifications.values() if n.user_id == user_id]
        user_notifications.sort(
            key=lambda n: n.created_at or datetime.min.replace(tzinfo=UTC), reverse=True
        )
        return user_notifications[offset : offset + limit]

    def get_unread_notifications(self, user_id: UUID) -> list[Notification]:
        """Get all unread notifications for a user."""
        unread = [n for n in self.storage.notifications.values() if n.user_id == user_id and not n.read]
        unread.sort(key=lambda n: n.created_at, reverse=True)
        return unread

    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user."""
        return sum(1 for n in self.storage.notifications.values() if n.user_id == user_id and not n.read)

    def mark_notification_as_read(self, notification_id: UUID) -> bool:
        """Mark a notification as read."""
        notification = self.storage.notifications.get(notification_id)
        if notification:
            notification.read = True
            return True
        return False

    def mark_all_notifications_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user. Returns count of marked notifications."""
        count = 0
        for notification in self.storage.notifications.values():
            if notification.user_id == user_id and not notification.read:
                notification.read = True
                count += 1
        return count

    def get_notification_by_id(self, notification_id: UUID) -> Notification | None:
        """Get a notification by ID."""
        return self.storage.notifications.get(notification_id)
