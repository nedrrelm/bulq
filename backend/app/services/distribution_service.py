"""Distribution service for handling distribution-related business logic."""

from typing import Any
from uuid import UUID

from app.utils.background_tasks import create_background_task
from app.core.exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
)
from app.core.models import Product, ProductBid, User
from app.infrastructure.request_context import get_logger
from app.core.run_state import RunState, state_machine
from app.api.schemas import (
    DistributionProduct,
    DistributionUser,
    MessageResponse,
    StateChangeResponse,
)
from app.infrastructure.transaction import transaction
from .base_service import BaseService

logger = get_logger(__name__)


class DistributionService(BaseService):
    """Service for distribution operations."""

    def _is_leader_or_helper(self, participation) -> bool:
        """Check if participation is leader or helper."""
        return participation.is_leader or participation.is_helper

    def get_distribution_summary(self, run_id: UUID, current_user: User) -> list[DistributionUser]:
        """Get distribution data aggregated by user.

        Args:
            run_id: The run ID to get distribution for
            current_user: The authenticated user making the request

        Returns:
            List of DistributionUser with products and totals

        Raises:
            NotFoundError: If run is not found
            ForbiddenError: If user doesn't have access to the run
            BadRequestError: If distribution not available in current state
        """
        self._validate_distribution_access(run_id, current_user)
        all_bids = self.repo.get_bids_by_run_with_participations(run_id)

        logger.info(f"Found {len(all_bids)} bids for distribution", extra={'run_id': str(run_id)})
        for bid in all_bids:
            logger.info(
                f"Bid: product={bid.product_id}, interested_only={bid.interested_only}, "
                f"distributed_qty={bid.distributed_quantity}, type={type(bid.distributed_quantity).__name__}",
                extra={'run_id': str(run_id), 'bid_id': str(bid.id)}
            )

        users_data = self._aggregate_bids_by_user(all_bids)
        logger.info(f"Aggregated into {len(users_data)} users", extra={'run_id': str(run_id)})

        distributions = []
        for user_data in users_data.values():
            # Skip users with no products (all bids were unpurchased)
            if not user_data['products']:
                logger.info(f"Skipping user {user_data['user_name']}: no purchased products",
                           extra={'run_id': str(run_id)})
                continue
            try:
                dist = self._build_user_distribution(user_data)
                logger.info(f"Built distribution for user {user_data['user_name']}: {len(user_data['products'])} products",
                           extra={'run_id': str(run_id)})
                distributions.append(dist)
            except Exception as e:
                logger.error(f"Error building distribution for user {user_data.get('user_name', 'unknown')}: {e}",
                            extra={'run_id': str(run_id)}, exc_info=True)

        logger.info(f"Returning {len(distributions)} distributions", extra={'run_id': str(run_id)})
        sorted_distributions = self._sort_distributions(distributions)

        # Log the actual data being returned
        for dist in sorted_distributions:
            logger.info(f"Distribution data: user={dist.user_name}, products={len(dist.products)}, total={dist.total_cost}",
                       extra={'run_id': str(run_id)})

        return sorted_distributions

    def _validate_distribution_access(self, run_id: UUID, current_user: User) -> None:
        """Validate user has access to view distribution."""
        run = self.repo.get_run_by_id(run_id)
        if not run:
            raise NotFoundError('Run', run_id)

        user_groups = self.repo.get_user_groups(current_user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError('Not authorized to view this run')

        # Check if viewing distribution is allowed using state machine
        run_state = RunState(run.state)
        if not state_machine.can_view_distribution(run_state):
            raise BadRequestError(
                state_machine.get_action_error_message(
                    'distribution', run_state, [RunState.DISTRIBUTING, RunState.COMPLETED]
                )
            )

    def _aggregate_bids_by_user(self, all_bids: list[ProductBid]) -> dict[str, dict[str, Any]]:
        """Group bids by user and aggregate totals."""
        users_data = {}

        for bid in all_bids:
            # Skip interested-only bids or bids with no distributed quantity
            if bid.interested_only:
                continue
            if bid.distributed_quantity is None or float(bid.distributed_quantity) <= 0:
                continue

            if not bid.participation or not bid.participation.user:
                continue

            user_id = str(bid.participation.user_id)

            if user_id not in users_data:
                users_data[user_id] = {
                    'user_id': user_id,
                    'user_name': bid.participation.user.name,
                    'products': [],
                    'total_cost': 0.0,
                }

            product = self._get_product(bid.product_id)
            if not product:
                continue

            price_per_unit = (
                float(bid.distributed_price_per_unit) if bid.distributed_price_per_unit else 0.0
            )
            subtotal = self._calculate_subtotal(price_per_unit, bid.distributed_quantity)

            users_data[user_id]['products'].append(
                DistributionProduct(
                    bid_id=str(bid.id),
                    product_id=str(bid.product_id),
                    product_name=product.name,
                    product_unit=product.unit,
                    requested_quantity=round(float(bid.quantity), 2),
                    distributed_quantity=round(float(bid.distributed_quantity), 2),
                    price_per_unit=f'{price_per_unit:.2f}',
                    subtotal=f'{subtotal:.2f}',
                    is_picked_up=bid.is_picked_up if bid.is_picked_up is not None else False,
                )
            )

            users_data[user_id]['total_cost'] += subtotal

        return users_data

    def _calculate_subtotal(self, price_per_unit: float, quantity: float) -> float:
        """Calculate subtotal for a product."""
        return price_per_unit * float(quantity)

    def _build_user_distribution(self, user_data: dict[str, Any]) -> DistributionUser:
        """Build DistributionUser from aggregated user data."""
        all_picked_up = all(p.is_picked_up for p in user_data['products'])
        return DistributionUser(
            user_id=user_data['user_id'],
            user_name=user_data['user_name'],
            products=user_data['products'],
            total_cost=f'{user_data["total_cost"]:.2f}',
            all_picked_up=all_picked_up,
        )

    def _sort_distributions(self, distributions: list[DistributionUser]) -> list[DistributionUser]:
        """Sort distributions by pickup status and name."""
        distributions.sort(key=lambda x: (x.all_picked_up, x.user_name))
        return distributions

    def mark_picked_up(self, run_id: UUID, bid_id: UUID, current_user: User) -> MessageResponse:
        """Mark a product as picked up by a user.

        Args:
            run_id: The run ID
            bid_id: The bid ID to mark as picked up
            current_user: The authenticated user making the request

        Returns:
            MessageResponse with success message

        Raises:
            NotFoundError: If run or bid is not found
            ForbiddenError: If user is not the run leader
        """
        # Get the run
        run = self.repo.get_run_by_id(run_id)
        if not run:
            raise NotFoundError('Run', run_id)

        # Verify user is the run leader or helper
        participation = self.repo.get_participation(current_user.id, run_id)
        if not participation or not self._is_leader_or_helper(participation):
            raise ForbiddenError('Only the run leader or helpers can mark items as picked up')

        # Mark as picked up
        bid = self._get_bid(bid_id)
        if not bid:
            raise NotFoundError('Bid', bid_id)

        bid.is_picked_up = True
        self._commit_changes()

        logger.info(
            'Bid marked as picked up',
            extra={
                'bid_id': str(bid_id),
                'user_id': str(current_user.id),
                'run_id': str(bid.participation.run_id),
            },
        )
        return MessageResponse(message='Marked as picked up')

    def complete_distribution(self, run_id: UUID, current_user: User) -> StateChangeResponse:
        """Complete distribution - transition from distributing to completed state.

        Args:
            run_id: The run ID to complete
            current_user: The authenticated user making the request

        Returns:
            StateChangeResponse with success message and new state

        Raises:
            NotFoundError: If run is not found
            ForbiddenError: If user is not the run leader
            BadRequestError: If not in distributing state or items not picked up
        """
        # Get the run
        run = self.repo.get_run_by_id(run_id)
        if not run:
            raise NotFoundError('Run', run_id)

        # Verify user is the run leader
        participation = self.repo.get_participation(current_user.id, run_id)
        if not participation or not participation.is_leader:
            raise ForbiddenError('Only the run leader can complete distribution')

        # Only allow completing from distributing state - use state machine
        run_state = RunState(run.state)
        if not state_machine.can_complete_distribution(run_state):
            raise BadRequestError('Can only complete distribution from distributing state')

        # Verify all items are picked up
        all_bids = self.repo.get_bids_by_run(run_id)
        unpicked_bids = [
            bid
            for bid in all_bids
            if not bid.interested_only and bid.distributed_quantity and not bid.is_picked_up
        ]

        if unpicked_bids:
            raise BadRequestError('Cannot complete distribution - some items not picked up')

        # Wrap state change and notifications in transaction
        with transaction(self.db, "complete distribution and transition to completed state"):
            # Transition to completed state
            old_state = run.state
            self.repo.update_run_state(run_id, RunState.COMPLETED)

            # Create notifications for all participants
            self._notify_run_state_change(run, old_state, RunState.COMPLETED)

        logger.info(
            'Distribution completed', extra={'run_id': str(run_id), 'user_id': str(current_user.id)}
        )
        return StateChangeResponse(
            message='Distribution completed!',
            state=RunState.COMPLETED,
            run_id=str(run_id),
            group_id=str(run.group_id),
        )

    def _get_product(self, product_id: UUID) -> Product:
        """Get product from repository."""
        return self.repo.get_product_by_id(product_id)

    def _get_bid(self, bid_id: UUID) -> ProductBid:
        """Get bid from repository."""
        return self.repo.get_bid_by_id(bid_id)

    def _commit_changes(self) -> None:
        """Commit changes."""
        self.repo.commit_changes()

    def _notify_run_state_change(self, run, old_state: str, new_state: str) -> None:
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

        # Create notification data
        notification_data = {
            'run_id': str(run.id),
            'store_name': store_name,
            'old_state': old_state,
            'new_state': new_state,
            'group_id': str(run.group_id),
        }

        # Create notification for each participant and broadcast via WebSocket

        from app.api.websocket_manager import manager

        for participation in participations:
            notification = self.repo.create_notification(
                user_id=participation.user_id, type='run_state_changed', data=notification_data
            )

            # Broadcast to user's WebSocket connection
            create_background_task(
                manager.broadcast(
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
                task_name=f'broadcast_distribution_notification_{participation.user_id}',
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
