"""Run notification service for managing notifications and WebSocket broadcasting."""

from app.api.schemas.notification_data import (
    BidRetractedData,
    BidUpdatedData,
    ReadyToggledData,
    RunCreatedData,
    RunStateChangedData,
    StateChangedData,
)
from app.api.websocket_manager import ConnectionManager
from app.core.models import Run
from app.core.run_state import RunState
from app.infrastructure.request_context import get_logger
from app.utils.background_tasks import create_background_task

from .base_service import BaseService

logger = get_logger(__name__)


class RunNotificationService(BaseService):
    """Service for managing run notifications and WebSocket broadcasting."""

    def __init__(self, db, websocket_manager: ConnectionManager | None = None):
        """Initialize service with database session and WebSocket manager.

        Args:
            db: SQLAlchemy database session
            websocket_manager: Optional WebSocket manager for broadcasting
        """
        super().__init__(db)
        self._ws_manager = websocket_manager

    def set_websocket_manager(self, ws_manager: ConnectionManager) -> None:
        """Set the WebSocket manager (for dependency injection after creation).

        Args:
            ws_manager: WebSocket manager instance
        """
        self._ws_manager = ws_manager

    async def broadcast_bid_update(
        self,
        run_id: str,
        product_id: str,
        user_id: str,
        user_name: str,
        quantity: float,
        interested_only: bool,
        new_total: float,
    ) -> None:
        """Broadcast bid update to run participants.

        Args:
            run_id: Run ID
            product_id: Product ID
            user_id: User ID who placed the bid
            user_name: User name who placed the bid
            quantity: Bid quantity
            interested_only: Whether bid is interest-only
            new_total: New total quantity for product
        """
        if not self._ws_manager:
            return

        data = BidUpdatedData(
            product_id=product_id,
            user_id=user_id,
            user_name=user_name,
            quantity=quantity,
            interested_only=interested_only,
            new_total=new_total,
        )

        await self._ws_manager.broadcast(
            f'run:{run_id}',
            {
                'type': 'bid_updated',
                'data': data.model_dump(mode='json'),
            },
        )

    async def broadcast_bid_retraction(
        self, run_id: str, product_id: str, user_id: str, new_total: float
    ) -> None:
        """Broadcast bid retraction to run participants.

        Args:
            run_id: Run ID
            product_id: Product ID
            user_id: User ID who retracted the bid
            new_total: New total quantity for product
        """
        if not self._ws_manager:
            return

        data = BidRetractedData(
            product_id=product_id,
            user_id=user_id,
            new_total=new_total,
        )

        await self._ws_manager.broadcast(
            f'run:{run_id}',
            {
                'type': 'bid_retracted',
                'data': data.model_dump(mode='json'),
            },
        )

    async def broadcast_ready_toggle(self, run_id: str, user_id: str, is_ready: bool) -> None:
        """Broadcast ready status toggle to run participants.

        Args:
            run_id: Run ID
            user_id: User ID who toggled ready
            is_ready: New ready status
        """
        if not self._ws_manager:
            return

        data = ReadyToggledData(user_id=user_id, is_ready=is_ready)

        await self._ws_manager.broadcast(
            f'run:{run_id}',
            {'type': 'ready_toggled', 'data': data.model_dump(mode='json')},
        )

    async def broadcast_state_change(
        self, run_id: str, group_id: str, new_state: RunState | str
    ) -> None:
        """Broadcast run state change to both run and group rooms.

        Args:
            run_id: Run ID
            group_id: Group ID
            new_state: New run state
        """
        if not self._ws_manager:
            return

        # Convert RunState enum to string if needed
        state_str = new_state.value if isinstance(new_state, RunState) else new_state

        # Broadcast to run room
        data_run = StateChangedData(run_id=run_id, new_state=state_str)
        await self._ws_manager.broadcast(
            f'run:{run_id}',
            {'type': 'state_changed', 'data': data_run.model_dump(mode='json')},
        )

        # Broadcast to group room
        data_group = StateChangedData(run_id=run_id, new_state=state_str)
        await self._ws_manager.broadcast(
            f'group:{group_id}',
            {'type': 'run_state_changed', 'data': data_group.model_dump(mode='json')},
        )

    async def broadcast_run_created(
        self,
        group_id: str,
        run_id: str,
        store_id: str,
        store_name: str,
        state: str,
        leader_name: str,
    ) -> None:
        """Broadcast run creation to group participants.

        Args:
            group_id: Group ID
            run_id: Run ID
            store_id: Store ID
            store_name: Store name
            state: Run state
            leader_name: Leader name
        """
        if not self._ws_manager:
            return

        data = RunCreatedData(
            run_id=run_id,
            store_id=store_id,
            store_name=store_name,
            state=state,
            leader_name=leader_name,
        )

        await self._ws_manager.broadcast(
            f'group:{group_id}',
            {
                'type': 'run_created',
                'data': data.model_dump(mode='json'),
            },
        )

    def notify_run_state_change(self, run: Run, old_state: str, new_state: str) -> None:
        """Create notifications for all participants when run state changes.

        Args:
            run: The run that changed state
            old_state: Previous state
            new_state: New state
        """
        # Get store name for notification
        all_stores = self.repo.get_all_stores()
        store = next((s for s in all_stores if s.id == run.store_id), None)
        store_name = store.name if store else 'Unknown Store'

        # Get all participants of this run
        participations = self.repo.get_run_participations(run.id)

        # Create notification data using Pydantic model for type safety
        notification_data = RunStateChangedData(
            run_id=str(run.id),
            store_name=store_name,
            old_state=old_state,
            new_state=new_state,
            group_id=str(run.group_id),
        )

        # Create notification for each participant and broadcast via WebSocket
        for participation in participations:
            notification = self.repo.create_notification(
                user_id=participation.user_id,
                type='run_state_changed',
                data=notification_data.model_dump(mode='json'),
            )

            # Broadcast to user's WebSocket connection
            if self._ws_manager:
                create_background_task(
                    self._ws_manager.broadcast(
                        f'user:{participation.user_id}',
                        {
                            'type': 'new_notification',
                            'data': {
                                'id': str(notification.id),
                                'type': notification.type,
                                'data': notification.data,
                                'read': notification.read,
                                'created_at': notification.created_at.isoformat() + 'Z'
                                if notification.created_at
                                else None,
                            },
                        },
                    ),
                    task_name=f'broadcast_notification_to_user_{participation.user_id}',
                )

        logger.debug(
            'Created notifications for run state change',
            extra={
                'run_id': str(run.id),
                'old_state': old_state,
                'new_state': new_state,
                'participant_count': len(participations),
            },
        )
