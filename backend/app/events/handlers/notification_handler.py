"""Notification event handler for creating database notifications from domain events."""

from typing import TYPE_CHECKING

from app.infrastructure.request_context import get_logger

from ..domain_events import RunStateChangedEvent

if TYPE_CHECKING:
    from app.repositories.database.notification import DatabaseNotificationRepository
    from app.repositories.memory.notification import MemoryNotificationRepository

logger = get_logger(__name__)


class NotificationEventHandler:
    """Handles domain events by creating database notifications.

    This handler translates domain events into user notifications
    stored in the database.
    """

    def __init__(self, notification_repo: "DatabaseNotificationRepository | MemoryNotificationRepository") -> None:
        """Initialize handler with notification repository.

        Args:
            notification_repo: Notification repository for database operations
        """
        self._notification_repo = notification_repo

    async def handle_run_state_changed(self, event: RunStateChangedEvent) -> None:
        """Create notifications for all participants when run state changes.

        Args:
            event: RunStateChangedEvent containing state change details
        """
        try:
            # Get all participants of this run
            participations = self._notification_repo.get_run_participations(event.run_id)

            notification_data = {
                'run_id': str(event.run_id),
                'store_name': event.store_name,
                'old_state': event.old_state,
                'new_state': event.new_state,
                'group_id': str(event.group_id),
            }

            # Create notification for each participant
            for participation in participations:
                self._notification_repo.create_notification(
                    user_id=participation.user_id, type='run_state_changed', data=notification_data
                )

            logger.debug(
                'Created notifications for run state change',
                extra={
                    'run_id': str(event.run_id),
                    'old_state': event.old_state,
                    'new_state': event.new_state,
                    'participant_count': len(participations),
                },
            )
        except Exception as e:
            logger.error(
                'Failed to create notifications for run state change',
                extra={
                    'run_id': str(event.run_id),
                    'old_state': event.old_state,
                    'new_state': event.new_state,
                    'error': str(e),
                },
                exc_info=True,
            )
