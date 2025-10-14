"""WebSocket event handler for broadcasting domain events via WebSocket."""

from app.infrastructure.request_context import get_logger
from app.api.websocket_manager import ConnectionManager
from ..domain_events import (
    BidPlacedEvent,
    BidRetractedEvent,
    MemberJoinedEvent,
    MemberLeftEvent,
    MemberRemovedEvent,
    ReadyToggledEvent,
    RunCancelledEvent,
    RunCreatedEvent,
    RunStateChangedEvent,
)

logger = get_logger(__name__)


class WebSocketEventHandler:
    """Handles domain events by broadcasting via WebSocket.

    This handler translates domain events into WebSocket messages
    and broadcasts them to relevant rooms (runs, groups).
    """

    def __init__(self, ws_manager: ConnectionManager) -> None:
        """Initialize handler with WebSocket manager.

        Args:
            ws_manager: WebSocket connection manager for broadcasting
        """
        self._ws_manager = ws_manager

    async def handle_bid_placed(self, event: BidPlacedEvent) -> None:
        """Broadcast bid placement to run participants.

        Args:
            event: BidPlacedEvent containing bid details
        """
        try:
            await self._ws_manager.broadcast(
                f'run:{event.run_id}',
                {
                    'type': 'bid_updated',
                    'data': {
                        'product_id': str(event.product_id),
                        'user_id': str(event.user_id),
                        'user_name': event.user_name,
                        'quantity': event.quantity,
                        'interested_only': event.interested_only,
                        'new_total': event.new_total,
                    },
                },
            )
            logger.debug(
                'Broadcast bid placed event',
                extra={'run_id': str(event.run_id), 'product_id': str(event.product_id)},
            )
        except Exception as e:
            logger.error(
                'Failed to broadcast bid placed event',
                extra={
                    'run_id': str(event.run_id),
                    'product_id': str(event.product_id),
                    'error': str(e),
                },
                exc_info=True,
            )

    async def handle_bid_retracted(self, event: BidRetractedEvent) -> None:
        """Broadcast bid retraction to run participants.

        Args:
            event: BidRetractedEvent containing retraction details
        """
        try:
            await self._ws_manager.broadcast(
                f'run:{event.run_id}',
                {
                    'type': 'bid_retracted',
                    'data': {
                        'product_id': str(event.product_id),
                        'user_id': str(event.user_id),
                        'new_total': event.new_total,
                    },
                },
            )
            logger.debug(
                'Broadcast bid retracted event',
                extra={'run_id': str(event.run_id), 'product_id': str(event.product_id)},
            )
        except Exception as e:
            logger.error(
                'Failed to broadcast bid retracted event',
                extra={
                    'run_id': str(event.run_id),
                    'product_id': str(event.product_id),
                    'error': str(e),
                },
                exc_info=True,
            )

    async def handle_ready_toggled(self, event: ReadyToggledEvent) -> None:
        """Broadcast ready status toggle to run participants.

        Args:
            event: ReadyToggledEvent containing ready status
        """
        try:
            await self._ws_manager.broadcast(
                f'run:{event.run_id}',
                {
                    'type': 'ready_toggled',
                    'data': {'user_id': str(event.user_id), 'is_ready': event.is_ready},
                },
            )
            logger.debug(
                'Broadcast ready toggled event',
                extra={'run_id': str(event.run_id), 'user_id': str(event.user_id)},
            )
        except Exception as e:
            logger.error(
                'Failed to broadcast ready toggled event',
                extra={'run_id': str(event.run_id), 'user_id': str(event.user_id), 'error': str(e)},
                exc_info=True,
            )

    async def handle_run_state_changed(self, event: RunStateChangedEvent) -> None:
        """Broadcast state change to run and group rooms.

        Args:
            event: RunStateChangedEvent containing state change details
        """
        try:
            # Broadcast to run room
            await self._ws_manager.broadcast(
                f'run:{event.run_id}',
                {
                    'type': 'state_changed',
                    'data': {'run_id': str(event.run_id), 'new_state': event.new_state},
                },
            )

            # Broadcast to group room
            await self._ws_manager.broadcast(
                f'group:{event.group_id}',
                {
                    'type': 'run_state_changed',
                    'data': {'run_id': str(event.run_id), 'new_state': event.new_state},
                },
            )

            logger.debug(
                'Broadcast run state changed event',
                extra={
                    'run_id': str(event.run_id),
                    'old_state': event.old_state,
                    'new_state': event.new_state,
                },
            )
        except Exception as e:
            logger.error(
                'Failed to broadcast run state changed event',
                extra={
                    'run_id': str(event.run_id),
                    'old_state': event.old_state,
                    'new_state': event.new_state,
                    'error': str(e),
                },
                exc_info=True,
            )

    async def handle_run_created(self, event: RunCreatedEvent) -> None:
        """Broadcast run creation to group participants.

        Args:
            event: RunCreatedEvent containing run creation details
        """
        try:
            await self._ws_manager.broadcast(
                f'group:{event.group_id}',
                {
                    'type': 'run_created',
                    'data': {
                        'run_id': str(event.run_id),
                        'store_id': str(event.store_id),
                        'store_name': event.store_name,
                        'state': event.state,
                        'leader_name': event.leader_name,
                    },
                },
            )
            logger.debug(
                'Broadcast run created event',
                extra={'run_id': str(event.run_id), 'group_id': str(event.group_id)},
            )
        except Exception as e:
            logger.error(
                'Failed to broadcast run created event',
                extra={
                    'run_id': str(event.run_id),
                    'group_id': str(event.group_id),
                    'error': str(e),
                },
                exc_info=True,
            )

    async def handle_run_cancelled(self, event: RunCancelledEvent) -> None:
        """Broadcast run cancellation to group participants.

        Args:
            event: RunCancelledEvent containing cancellation details
        """
        try:
            await self._ws_manager.broadcast(
                f'group:{event.group_id}',
                {
                    'type': 'run_cancelled',
                    'data': {'run_id': str(event.run_id), 'store_name': event.store_name},
                },
            )
            logger.debug(
                'Broadcast run cancelled event',
                extra={'run_id': str(event.run_id), 'group_id': str(event.group_id)},
            )
        except Exception as e:
            logger.error(
                'Failed to broadcast run cancelled event',
                extra={
                    'run_id': str(event.run_id),
                    'group_id': str(event.group_id),
                    'error': str(e),
                },
                exc_info=True,
            )

    async def handle_member_joined(self, event: MemberJoinedEvent) -> None:
        """Broadcast member join to group participants.

        Args:
            event: MemberJoinedEvent containing join details
        """
        try:
            await self._ws_manager.broadcast(
                f'group:{event.group_id}',
                {
                    'type': 'member_joined',
                    'data': {'user_id': str(event.user_id), 'user_name': event.user_name},
                },
            )
            logger.debug(
                'Broadcast member joined event',
                extra={'group_id': str(event.group_id), 'user_id': str(event.user_id)},
            )
        except Exception as e:
            logger.error(
                'Failed to broadcast member joined event',
                extra={
                    'group_id': str(event.group_id),
                    'user_id': str(event.user_id),
                    'error': str(e),
                },
                exc_info=True,
            )

    async def handle_member_removed(self, event: MemberRemovedEvent) -> None:
        """Broadcast member removal to group participants.

        Args:
            event: MemberRemovedEvent containing removal details
        """
        try:
            await self._ws_manager.broadcast(
                f'group:{event.group_id}',
                {'type': 'member_removed', 'data': {'user_id': str(event.user_id)}},
            )
            logger.debug(
                'Broadcast member removed event',
                extra={'group_id': str(event.group_id), 'user_id': str(event.user_id)},
            )
        except Exception as e:
            logger.error(
                'Failed to broadcast member removed event',
                extra={
                    'group_id': str(event.group_id),
                    'user_id': str(event.user_id),
                    'error': str(e),
                },
                exc_info=True,
            )

    async def handle_member_left(self, event: MemberLeftEvent) -> None:
        """Broadcast member departure to group participants.

        Args:
            event: MemberLeftEvent containing departure details
        """
        try:
            await self._ws_manager.broadcast(
                f'group:{event.group_id}',
                {'type': 'member_left', 'data': {'user_id': str(event.user_id)}},
            )
            logger.debug(
                'Broadcast member left event',
                extra={'group_id': str(event.group_id), 'user_id': str(event.user_id)},
            )
        except Exception as e:
            logger.error(
                'Failed to broadcast member left event',
                extra={
                    'group_id': str(event.group_id),
                    'user_id': str(event.user_id),
                    'error': str(e),
                },
                exc_info=True,
            )
