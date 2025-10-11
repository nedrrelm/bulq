"""Service layer for notification-related business logic."""

from typing import List, Dict, Any
from uuid import UUID
from collections import defaultdict
from datetime import datetime, timedelta

from .base_service import BaseService
from ..exceptions import NotFoundError, ForbiddenError, BadRequestError
from ..models import User
from ..request_context import get_logger

logger = get_logger(__name__)


class NotificationService(BaseService):
    """Service for managing notifications."""

    def get_user_notifications(self, user: User, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get notifications for a user (paginated) with grouping.

        Args:
            user: The user to get notifications for
            limit: Maximum number of notifications to return
            offset: Offset for pagination

        Returns:
            List of notification dictionaries (possibly grouped)
        """
        logger.debug(
            f"Fetching notifications for user",
            extra={"user_id": str(user.id), "limit": limit, "offset": offset}
        )

        notifications = self.repo.get_user_notifications(user.id, limit, offset)

        # Group similar notifications
        grouped = self._group_notifications(notifications)

        return grouped

    def get_unread_notifications(self, user: User) -> List[Dict[str, Any]]:
        """
        Get all unread notifications for a user.

        Args:
            user: The user to get unread notifications for

        Returns:
            List of notification dictionaries
        """
        logger.debug(
            f"Fetching unread notifications for user",
            extra={"user_id": str(user.id)}
        )

        notifications = self.repo.get_unread_notifications(user.id)
        return [self._notification_to_dict(n) for n in notifications]

    def get_unread_count(self, user: User) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user: The user to get count for

        Returns:
            Count of unread notifications
        """
        return self.repo.get_unread_count(user.id)

    def mark_as_read(self, notification_id: str, user: User) -> Dict[str, str]:
        """
        Mark a notification as read (with authorization check).

        Args:
            notification_id: The notification ID as string
            user: The user marking as read (must own the notification)

        Returns:
            Success message

        Raises:
            BadRequestError: If notification ID is invalid
            NotFoundError: If notification doesn't exist
            ForbiddenError: If user doesn't own the notification
        """
        try:
            notification_uuid = UUID(notification_id)
        except ValueError:
            raise BadRequestError("Invalid notification ID format")

        # Get notification and check ownership
        notification = self.repo.get_notification_by_id(notification_uuid)
        if not notification:
            raise NotFoundError("Notification", notification_id)

        if notification.user_id != user.id:
            logger.warning(
                f"User attempted to mark notification they don't own",
                extra={"user_id": str(user.id), "notification_id": notification_id}
            )
            raise ForbiddenError("Not authorized to modify this notification")

        success = self.repo.mark_notification_as_read(notification_uuid)
        if not success:
            raise BadRequestError("Failed to mark notification as read")

        logger.info(
            f"Notification marked as read",
            extra={"user_id": str(user.id), "notification_id": notification_id}
        )

        return {"message": "Notification marked as read"}

    def mark_all_as_read(self, user: User) -> Dict[str, Any]:
        """
        Mark all notifications as read for a user.

        Args:
            user: The user to mark all notifications for

        Returns:
            Dict with count of marked notifications
        """
        count = self.repo.mark_all_notifications_as_read(user.id)

        logger.info(
            f"Marked all notifications as read",
            extra={"user_id": str(user.id), "count": count}
        )

        return {"message": "All notifications marked as read", "count": count}

    def _notification_to_dict(self, notification) -> Dict[str, Any]:
        """Convert notification model to dictionary."""
        return {
            "id": str(notification.id),
            "type": notification.type,
            "data": notification.data,
            "read": notification.read,
            "created_at": notification.created_at.isoformat() + 'Z' if notification.created_at else None
        }

    def _group_notifications(self, notifications: List) -> List[Dict[str, Any]]:
        """
        Group similar notifications that occurred close together.

        Groups notifications of the same type with the same run_id
        that occurred within 5 minutes of each other.

        Args:
            notifications: List of notification objects

        Returns:
            List of notification dicts (some may be grouped)
        """
        if not notifications:
            return []

        # Group by (type, run_id) within time windows
        groups = defaultdict(list)

        for notif in notifications:
            # Create grouping key
            key = None
            if notif.type == "run_state_changed" and "run_id" in notif.data:
                # Group run state changes for the same run
                key = (notif.type, notif.data.get("run_id"))

            if key:
                groups[key].append(notif)
            else:
                # Don't group this type, keep it standalone
                groups[(notif.id,)].append(notif)

        # Build result list
        result = []
        for key, group_notifs in groups.items():
            if len(group_notifs) == 1:
                # Single notification, return as is
                result.append(self._notification_to_dict(group_notifs[0]))
            else:
                # Multiple notifications, check if they should be grouped by time
                # Sort by created_at
                group_notifs.sort(key=lambda n: n.created_at, reverse=True)

                # Check if all are within 5 minutes of each other
                time_window = timedelta(minutes=5)
                first_time = group_notifs[0].created_at
                last_time = group_notifs[-1].created_at

                if first_time - last_time <= time_window:
                    # Group them
                    result.append({
                        "id": str(group_notifs[0].id),  # Use first notification's ID
                        "type": group_notifs[0].type,
                        "data": group_notifs[0].data,
                        "read": all(n.read for n in group_notifs),
                        "created_at": group_notifs[0].created_at.isoformat() + 'Z',
                        "grouped": True,
                        "count": len(group_notifs),
                        "notification_ids": [str(n.id) for n in group_notifs]
                    })
                else:
                    # Too far apart, don't group
                    for notif in group_notifs:
                        result.append(self._notification_to_dict(notif))

        # Sort result by created_at (most recent first)
        result.sort(key=lambda n: n["created_at"], reverse=True)

        return result
