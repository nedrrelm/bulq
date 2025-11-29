"""Database notification repository implementation."""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.models import Notification
from app.repositories.abstract.notification import AbstractNotificationRepository


class DatabaseNotificationRepository(AbstractNotificationRepository):
    """Database implementation of notification repository."""

    def __init__(self, db: Session):
        self.db = db

    def create_notification(self, user_id: UUID, type: str, data: dict[str, Any]) -> Notification:
        """Create a new notification for a user."""
        notification = Notification(user_id=user_id, type=type, data=data, read=False)
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_user_notifications(
        self, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[Notification]:
        """Get notifications for a user (paginated)."""
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_unread_notifications(self, user_id: UUID) -> list[Notification]:
        """Get all unread notifications for a user."""
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, ~Notification.read)
            .order_by(Notification.created_at.desc())
            .all()
        )

    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user."""
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, ~Notification.read)
            .count()
        )

    def mark_notification_as_read(self, notification_id: UUID) -> bool:
        """Mark a notification as read."""
        notification = (
            self.db.query(Notification).filter(Notification.id == notification_id).first()
        )
        if notification:
            notification.read = True
            self.db.commit()
            return True
        return False

    def mark_all_notifications_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user. Returns count of marked notifications."""
        count = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, ~Notification.read)
            .update({Notification.read: True})
        )
        self.db.commit()
        return count

    def get_notification_by_id(self, notification_id: UUID) -> Notification | None:
        """Get a notification by ID."""
        return self.db.query(Notification).filter(Notification.id == notification_id).first()
