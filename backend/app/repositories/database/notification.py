"""Database notification repository implementation."""

from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Notification
from app.repositories.abstract.notification import AbstractNotificationRepository


class DatabaseNotificationRepository(AbstractNotificationRepository):
    """Database implementation of notification repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(self, user_id: UUID, type: str, data: dict[str, Any]) -> Notification:
        """Create a new notification for a user."""
        notification = Notification(user_id=user_id, type=type, data=data, read=False)
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def get_user_notifications(
        self, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[Notification]:
        """Get notifications for a user (paginated)."""
        result = await self.db.execute(
            select(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_unread_notifications(self, user_id: UUID) -> list[Notification]:
        """Get all unread notifications for a user."""
        result = await self.db.execute(
            select(Notification)
            .filter(Notification.user_id == user_id, ~Notification.read)
            .order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user."""
        result = await self.db.execute(
            select(func.count()).select_from(Notification).filter(
                Notification.user_id == user_id, ~Notification.read
            )
        )
        return result.scalar() or 0

    async def mark_notification_as_read(self, notification_id: UUID) -> bool:
        """Mark a notification as read."""
        result = await self.db.execute(
            select(Notification).filter(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if notification:
            notification.read = True
            await self.db.commit()
            return True
        return False

    async def mark_all_notifications_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user. Returns count of marked notifications."""
        result = await self.db.execute(
            update(Notification)
            .filter(Notification.user_id == user_id, ~Notification.read)
            .values(read=True)
        )
        await self.db.commit()
        return result.rowcount

    async def get_notification_by_id(self, notification_id: UUID) -> Notification | None:
        """Get a notification by ID."""
        result = await self.db.execute(select(Notification).filter(Notification.id == notification_id))
        return result.scalar_one_or_none()
