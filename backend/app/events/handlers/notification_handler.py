"""Notification event handler for creating database notifications from domain events."""

from typing import TYPE_CHECKING

from app.infrastructure.request_context import get_logger

from ..domain_events import BidModifiedByLeaderEvent, RunStateChangedEvent, SaleStateChangedEvent

if TYPE_CHECKING:
    from app.repositories.database.notification import DatabaseNotificationRepository
    from app.repositories.memory.notification import MemoryNotificationRepository

logger = get_logger(__name__)


class NotificationEventHandler:
    """Handles domain events by creating database notifications.

    This handler translates domain events into user notifications
    stored in the database.
    """

    def __init__(
        self, notification_repo: DatabaseNotificationRepository | MemoryNotificationRepository
    ) -> None:
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
            participations = await self._notification_repo.get_run_participations(event.run_id)

            notification_data = {
                'run_id': str(event.run_id),
                'store_name': event.store_name,
                'old_state': event.old_state,
                'new_state': event.new_state,
                'group_id': str(event.group_id),
            }

            # Create notification for each participant
            for participation in participations:
                await self._notification_repo.create_notification(
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

    async def handle_bid_modified_by_leader(self, event: BidModifiedByLeaderEvent) -> None:
        """Create notification for user whose bid was modified by leader."""
        try:
            notification_data = {
                'run_id': str(event.run_id),
                'product_name': event.product_name,
                'old_quantity': event.old_quantity,
                'new_quantity': event.new_quantity,
                'leader_name': event.leader_user_name,
            }
            await self._notification_repo.create_notification(
                user_id=event.target_user_id,
                type='bid_modified_by_leader',
                data=notification_data,
            )
            logger.debug(
                'Created notification for leader bid modification',
                extra={
                    'run_id': str(event.run_id),
                    'target_user_id': str(event.target_user_id),
                    'leader_user_id': str(event.leader_user_id),
                },
            )
        except Exception as e:
            logger.error(
                'Failed to create notification for leader bid modification',
                extra={
                    'run_id': str(event.run_id),
                    'target_user_id': str(event.target_user_id),
                    'error': str(e),
                },
                exc_info=True,
            )

    async def handle_sale_state_changed(self, event: SaleStateChangedEvent) -> None:
        """Create notifications for followers when sale state changes.

        Notifies members of all groups following this seller when a sale
        becomes active (new sale available).
        """
        try:
            # Only notify on activation (new sale available to bid on)
            if event.new_state != 'active':
                return

            from app.repositories import get_group_repository, get_seller_follower_repository

            follower_repo = get_seller_follower_repository(None)
            group_repo = get_group_repository(None)

            followers = await follower_repo.get_followers_by_seller(event.seller_id)
            notification_data = {
                'sale_id': str(event.sale_id),
                'sale_title': event.sale_title,
                'type': 'sale_activated',
            }

            notified_users = set()
            for follower in followers:
                members = await group_repo.get_group_members_with_admin_status(follower.group_id)
                for member in members:
                    user_id = member.get('user_id') or member.get('id')
                    if user_id and user_id not in notified_users:
                        await self._notification_repo.create_notification(
                            user_id=user_id,
                            type='sale_activated',
                            data=notification_data,
                        )
                        notified_users.add(user_id)

            logger.debug(
                'Created notifications for sale activation',
                extra={
                    'sale_id': str(event.sale_id),
                    'notified_count': len(notified_users),
                },
            )
        except Exception as e:
            logger.error(
                'Failed to create notifications for sale state change',
                extra={
                    'sale_id': str(event.sale_id),
                    'error': str(e),
                },
                exc_info=True,
            )
