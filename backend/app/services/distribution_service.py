"""Distribution service for handling distribution-related business logic."""

import logging
from typing import List, Dict, Any
from uuid import UUID
from ..models import User, Product, ProductBid
from ..run_state import RunState
from ..exceptions import (
    BadRequestError,
    NotFoundError,
    ForbiddenError,
)
from .base_service import BaseService

logger = logging.getLogger(__name__)


class DistributionService(BaseService):
    """Service for distribution operations."""

    def get_distribution_summary(
        self, run_id: UUID, current_user: User
    ) -> List[Dict[str, Any]]:
        """
        Get distribution data aggregated by user.

        Args:
            run_id: The run ID to get distribution for
            current_user: The authenticated user making the request

        Returns:
            List of user distribution data with products and totals

        Raises:
            NotFoundError: If run is not found
            ForbiddenError: If user doesn't have access to the run
            BadRequestError: If distribution not available in current state
        """
        # Get the run
        run = self.repo.get_run_by_id(run_id)
        if not run:
            raise NotFoundError("Run", run_id)

        # Verify user has access to this run
        user_groups = self.repo.get_user_groups(current_user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError("Not authorized to view this run")

        # Only allow viewing distribution in distributing or completed states
        if run.state not in ['distributing', 'completed']:
            raise BadRequestError("Distribution only available in distributing state")

        # Get all bids with participations and users eagerly loaded to avoid N+1 queries
        all_bids = self.repo.get_bids_by_run_with_participations(run_id)

        # Group bids by user
        users_data = {}

        for bid in all_bids:
            if bid.interested_only or not bid.distributed_quantity:
                continue

            # Participation and user are eagerly loaded on the bid object
            if not bid.participation or not bid.participation.user:
                continue

            user_id = str(bid.participation.user_id)

            # Initialize user data if not exists
            if user_id not in users_data:
                users_data[user_id] = {
                    'user_id': user_id,
                    'user_name': bid.participation.user.name,
                    'products': [],
                    'total_cost': 0.0
                }

            # Get product info
            product = self._get_product(bid.product_id)
            if not product:
                continue

            # Calculate subtotal
            price_per_unit = float(bid.distributed_price_per_unit) if bid.distributed_price_per_unit else 0.0
            subtotal = price_per_unit * bid.distributed_quantity

            users_data[user_id]['products'].append({
                'bid_id': str(bid.id),
                'product_id': str(bid.product_id),
                'product_name': product.name,
                'requested_quantity': bid.quantity,
                'distributed_quantity': bid.distributed_quantity,
                'price_per_unit': f"{price_per_unit:.2f}",
                'subtotal': f"{subtotal:.2f}",
                'is_picked_up': bid.is_picked_up if bid.is_picked_up is not None else False
            })

            users_data[user_id]['total_cost'] += subtotal

        # Convert to list and format
        result = []
        for user_data in users_data.values():
            all_picked_up = all(p['is_picked_up'] for p in user_data['products'])

            result.append({
                'user_id': user_data['user_id'],
                'user_name': user_data['user_name'],
                'products': user_data['products'],
                'total_cost': f"{user_data['total_cost']:.2f}",
                'all_picked_up': all_picked_up
            })

        # Sort: users who haven't picked up everything first, then alphabetically
        result.sort(key=lambda x: (x['all_picked_up'], x['user_name']))

        return result

    def mark_picked_up(
        self, run_id: UUID, bid_id: UUID, current_user: User
    ) -> Dict[str, str]:
        """
        Mark a product as picked up by a user.

        Args:
            run_id: The run ID
            bid_id: The bid ID to mark as picked up
            current_user: The authenticated user making the request

        Returns:
            Success message

        Raises:
            NotFoundError: If run or bid is not found
            ForbiddenError: If user is not the run leader
        """
        # Get the run
        run = self.repo.get_run_by_id(run_id)
        if not run:
            raise NotFoundError("Run", run_id)

        # Verify user is the run leader
        participation = self.repo.get_participation(current_user.id, run_id)
        if not participation or not participation.is_leader:
            raise ForbiddenError("Only the run leader can mark items as picked up")

        # Mark as picked up
        bid = self._get_bid(bid_id)
        if not bid:
            raise NotFoundError("Bid", bid_id)

        bid.is_picked_up = True
        self._commit_changes()

        logger.info(f"Bid {bid_id} marked as picked up by user {current_user.id}")
        return {"message": "Marked as picked up"}

    def complete_distribution(
        self, run_id: UUID, current_user: User
    ) -> Dict[str, str]:
        """
        Complete distribution - transition from distributing to completed state.

        Args:
            run_id: The run ID to complete
            current_user: The authenticated user making the request

        Returns:
            Success message with new state

        Raises:
            NotFoundError: If run is not found
            ForbiddenError: If user is not the run leader
            BadRequestError: If not in distributing state or items not picked up
        """
        # Get the run
        run = self.repo.get_run_by_id(run_id)
        if not run:
            raise NotFoundError("Run", run_id)

        # Verify user is the run leader
        participation = self.repo.get_participation(current_user.id, run_id)
        if not participation or not participation.is_leader:
            raise ForbiddenError("Only the run leader can complete distribution")

        # Only allow completing from distributing state
        if run.state != 'distributing':
            raise BadRequestError("Can only complete distribution from distributing state")

        # Verify all items are picked up
        all_bids = self.repo.get_bids_by_run(run_id)
        unpicked_bids = [
            bid for bid in all_bids
            if not bid.interested_only and bid.distributed_quantity and not bid.is_picked_up
        ]

        if unpicked_bids:
            raise BadRequestError("Cannot complete distribution - some items not picked up")

        # Transition to completed state
        old_state = run.state
        self.repo.update_run_state(run_id, RunState.COMPLETED)

        # Create notifications for all participants
        self._notify_run_state_change(run, old_state, RunState.COMPLETED)

        logger.info(f"Distribution completed for run {run_id} by user {current_user.id}")
        return {"message": "Distribution completed!", "state": RunState.COMPLETED}

    def _get_product(self, product_id: UUID) -> Product:
        """Get product from repository (handles both memory and database modes)."""
        if hasattr(self.repo, '_products'):
            return self.repo._products.get(product_id)
        else:
            return self.repo.get_product_by_id(product_id)

    def _get_bid(self, bid_id: UUID) -> ProductBid:
        """Get bid from repository (handles both memory and database modes)."""
        if hasattr(self.repo, '_bids'):
            return self.repo._bids.get(bid_id)
        else:
            # In database mode, we need to query directly
            # The repository doesn't have a get_bid_by_id method
            # We'll rely on the route layer to handle this for now
            # But for completeness, we could add a method to repository
            from ..database import get_db
            db = next(get_db())
            return db.query(ProductBid).filter(ProductBid.id == bid_id).first()

    def _commit_changes(self) -> None:
        """Commit changes (only needed in database mode)."""
        if not hasattr(self.repo, '_bids'):
            # Database mode - need to commit
            from ..database import get_db
            db = next(get_db())
            db.commit()

    def _notify_run_state_change(self, run, old_state: str, new_state: str) -> None:
        """
        Create notifications for all participants when run state changes.

        Args:
            run: The run that changed state
            old_state: Previous state
            new_state: New state
        """
        # Get store name for notification
        all_stores = self.repo.get_all_stores()
        store = next((s for s in all_stores if s.id == run.store_id), None)
        store_name = store.name if store else "Unknown Store"

        # Get all participants of this run
        participations = self.repo.get_run_participations(run.id)

        # Create notification data
        notification_data = {
            "run_id": str(run.id),
            "store_name": store_name,
            "old_state": old_state,
            "new_state": new_state,
            "group_id": str(run.group_id)
        }

        # Create notification for each participant and broadcast via WebSocket
        from ..websocket_manager import manager
        import asyncio

        for participation in participations:
            notification = self.repo.create_notification(
                user_id=participation.user_id,
                type="run_state_changed",
                data=notification_data
            )

            # Broadcast to user's WebSocket connection
            try:
                asyncio.create_task(manager.broadcast(f"user:{participation.user_id}", {
                    "type": "new_notification",
                    "data": {
                        "id": str(notification.id),
                        "type": notification.type,
                        "data": notification.data,
                        "read": notification.read,
                        "created_at": notification.created_at.isoformat() + 'Z' if notification.created_at else None
                    }
                }))
            except Exception as e:
                logger.warning(f"Failed to broadcast notification via WebSocket: {e}")

        logger.debug(
            f"Created notifications for run state change",
            extra={
                "run_id": str(run.id),
                "old_state": old_state,
                "new_state": new_state,
                "participant_count": len(participations)
            }
        )
