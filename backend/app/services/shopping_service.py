"""Shopping service for handling shopping list operations."""

import logging
import uuid
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import UUID

from .base_service import BaseService
from ..exceptions import NotFoundError, ForbiddenError, BadRequestError
from ..models import User
from ..run_state import RunState, state_machine
from ..websocket_manager import manager

logger = logging.getLogger(__name__)


class ShoppingService(BaseService):
    """Service for managing shopping list operations."""

    async def _update_product_availability_if_needed(
        self,
        product_id: UUID,
        store_id: UUID,
        price: float,
        user_id: UUID
    ) -> None:
        """
        Update ProductAvailability if the price differs from prices seen today.

        Args:
            product_id: Product UUID
            store_id: Store UUID
            price: The purchased price
            user_id: User who made the purchase
        """
        try:
            # Get existing availabilities for this product at this store
            availabilities = self.repo.get_product_availabilities(product_id, store_id)

            # Check if we have any prices from today
            today = datetime.now().date()
            today_prices = [
                float(avail.price) for avail in availabilities
                if avail.price is not None and avail.created_at.date() == today
            ]

            # If no prices today, or price differs from all today's prices, create new availability
            if not today_prices or price not in today_prices:
                self.repo.create_product_availability(
                    product_id=product_id,
                    store_id=store_id,
                    price=price,
                    notes="Purchased during shopping",
                    user_id=user_id
                )
                logger.info(
                    f"Created product availability for different price",
                    extra={
                        "product_id": str(product_id),
                        "store_id": str(store_id),
                        "price": price,
                        "user_id": str(user_id)
                    }
                )
        except Exception as e:
            # Don't fail the purchase if availability update fails
            logger.error(
                f"Failed to update product availability",
                extra={
                    "product_id": str(product_id),
                    "store_id": str(store_id),
                    "price": price,
                    "error": str(e)
                }
            )

    async def get_shopping_list(
        self,
        run_id: str,
        user: User
    ) -> List[Dict[str, Any]]:
        """
        Get shopping list for a run with auth check.

        Args:
            run_id: The run ID as string
            user: The authenticated user

        Returns:
            List of shopping list items with product details

        Raises:
            BadRequestError: If run ID format is invalid
            NotFoundError: If run is not found
            ForbiddenError: If user doesn't have access to the run
            BadRequestError: If shopping list is not available in current state
        """
        # Validate run ID
        try:
            run_uuid = uuid.UUID(run_id)
        except ValueError:
            raise BadRequestError("Invalid run ID format")

        # Get the run
        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError("Run", run_id)

        # Verify user has access to this run
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError("Not authorized to view this run")

        # Only allow viewing shopping list in shopping or later states
        if run.state not in ['shopping', 'distributing', 'completed']:
            raise BadRequestError("Shopping list only available in shopping state")

        # Get shopping list items
        items = self.repo.get_shopping_list_items(run_uuid)

        from datetime import datetime, timedelta

        # Convert to response format
        response_items = []
        for item in items:
            # Get product directly by ID
            product = self.repo.get_product_by_id(item.product_id)

            # Get all product availabilities for this product at this store
            all_availabilities = self.repo.get_product_availabilities(
                product_id=item.product_id,
                store_id=run.store_id
            )

            # Find the most recent price observation
            most_recent = None
            for avail in all_availabilities:
                if avail.price and avail.created_at:
                    if most_recent is None or avail.created_at > most_recent.created_at:
                        most_recent = avail

            # Get all prices from the same day as the most recent observation
            recent_day_prices = []
            if most_recent:
                # Get the day boundaries for the most recent price
                recent_date = most_recent.created_at.replace(hour=0, minute=0, second=0, microsecond=0)
                recent_date_end = recent_date + timedelta(days=1)

                # Filter to only prices from that day
                for avail in all_availabilities:
                    if avail.price and avail.created_at:
                        if recent_date <= avail.created_at < recent_date_end:
                            recent_day_prices.append({
                                "price": float(avail.price),
                                "notes": avail.notes or "",
                                "created_at": avail.created_at.isoformat() if avail.created_at else None
                            })

                # Sort by created_at descending (newest first)
                recent_day_prices.sort(key=lambda x: x["created_at"] if x["created_at"] else "", reverse=True)

            response_items.append({
                "id": str(item.id),
                "product_id": str(item.product_id),
                "product_name": product.name if product else "Unknown Product",
                "requested_quantity": item.requested_quantity,
                "recent_prices": recent_day_prices,
                "purchased_quantity": item.purchased_quantity,
                "purchased_price_per_unit": str(item.purchased_price_per_unit) if item.purchased_price_per_unit else None,
                "purchased_total": str(item.purchased_total) if item.purchased_total else None,
                "is_purchased": item.is_purchased,
                "purchase_order": item.purchase_order
            })

        # Sort: unpurchased first, then purchased by purchase order
        response_items.sort(key=lambda x: (x["is_purchased"], x["purchase_order"] if x["purchase_order"] else 999))

        return response_items

    async def add_availability_price(
        self,
        run_id: str,
        item_id: str,
        price: float,
        notes: str,
        user: User
    ) -> Dict[str, str]:
        """
        Update product availability price for a shopping list item.

        Args:
            run_id: The run ID as string
            item_id: The shopping list item ID as string
            price: The price to set
            notes: Optional notes about the price
            user: The authenticated user

        Returns:
            Success message dictionary

        Raises:
            BadRequestError: If ID format is invalid
            NotFoundError: If run or item is not found
            ForbiddenError: If user is not the run leader
        """
        # Validate IDs
        try:
            run_uuid = uuid.UUID(run_id)
            item_uuid = uuid.UUID(item_id)
        except ValueError:
            raise BadRequestError("Invalid ID format")

        # Get the run
        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError("Run", run_id)

        # Verify user is the run leader
        participation = self.repo.get_participation(user.id, run_uuid)
        if not participation or not participation.is_leader:
            raise ForbiddenError("Only the run leader can add prices")

        # Get the shopping list item to find the product
        item = self.repo.get_shopping_list_item(item_uuid)
        if not item:
            raise NotFoundError("Shopping list item", item_id)

        # Create or update product availability
        availability = self.repo.create_product_availability(
            product_id=item.product_id,
            store_id=run.store_id,
            price=price,
            notes=notes,
            user_id=user.id
        )

        return {"message": "Price updated successfully"}

    async def mark_purchased(
        self,
        run_id: str,
        item_id: str,
        quantity: float,
        price_per_unit: float,
        total: float,
        user: User
    ) -> Dict[str, Any]:
        """
        Mark a shopping list item as purchased.

        Args:
            run_id: The run ID as string
            item_id: The shopping list item ID as string
            quantity: The purchased quantity
            price_per_unit: The price per unit
            total: The total price
            user: The authenticated user

        Returns:
            Dictionary with success message and purchase order

        Raises:
            BadRequestError: If ID format is invalid
            NotFoundError: If run or item is not found
            ForbiddenError: If user is not the run leader
        """
        # Validate IDs
        try:
            run_uuid = uuid.UUID(run_id)
            item_uuid = uuid.UUID(item_id)
        except ValueError:
            raise BadRequestError("Invalid ID format")

        # Get the run
        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError("Run", run_id)

        # Verify user is the run leader
        participation = self.repo.get_participation(user.id, run_uuid)
        if not participation or not participation.is_leader:
            raise ForbiddenError("Only the run leader can mark items as purchased")

        # Get next purchase order number
        existing_items = self.repo.get_shopping_list_items(run_uuid)
        max_order = max([item.purchase_order for item in existing_items if item.purchase_order is not None], default=0)
        next_order = max_order + 1

        # Mark as purchased
        item = self.repo.mark_item_purchased(
            item_uuid,
            quantity,
            price_per_unit,
            total,
            next_order
        )
        if not item:
            raise NotFoundError("Shopping list item", item_id)

        # Update ProductAvailability if the price differs from today's prices
        await self._update_product_availability_if_needed(
            item.product_id,
            run.store_id,
            price_per_unit,
            user.id
        )

        return {"message": "Item marked as purchased", "purchase_order": next_order}

    async def complete_shopping(
        self,
        run_id: str,
        user: User,
        db: Any = None
    ) -> Dict[str, Any]:
        """
        Complete shopping and handle shortages/transitions.

        This method:
        1. Verifies the user is the run leader
        2. Checks if any items have insufficient quantities
        3. If insufficient: transitions to ADJUSTING state
        4. If sufficient: distributes items and transitions to DISTRIBUTING state
        5. Broadcasts state changes via websocket

        Args:
            run_id: The run ID as string
            user: The authenticated user
            db: Optional database session (for direct DB updates)

        Returns:
            Dictionary with message and new state

        Raises:
            BadRequestError: If run ID format is invalid or state is not 'shopping'
            NotFoundError: If run is not found
            ForbiddenError: If user is not the run leader
        """
        logger.info(
            f"Completing shopping for run",
            extra={"user_id": str(user.id), "run_id": run_id}
        )

        # Validate run ID
        try:
            run_uuid = uuid.UUID(run_id)
        except ValueError:
            raise BadRequestError("Invalid run ID format")

        # Get the run
        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError("Run", run_id)

        # Verify user is the run leader
        participation = self.repo.get_participation(user.id, run_uuid)
        if not participation or not participation.is_leader:
            raise ForbiddenError("Only the run leader can complete shopping")

        # Only allow completing from shopping state
        if run.state != 'shopping':
            raise BadRequestError("Can only complete shopping from shopping state")

        # Check if any items have insufficient quantities
        shopping_items = self.repo.get_shopping_list_items(run_uuid)
        all_bids = self.repo.get_bids_by_run(run_uuid)

        has_insufficient = False
        for shopping_item in shopping_items:
            if not shopping_item.is_purchased:
                continue

            # Check if purchased quantity is less than requested
            if shopping_item.purchased_quantity < shopping_item.requested_quantity:
                has_insufficient = True
                break

        # If we have insufficient quantities, transition to adjusting state
        if has_insufficient:
            old_state = run.state
            self.repo.update_run_state(run_uuid, RunState.ADJUSTING)

            # Create notifications for all participants
            self._notify_run_state_change(run, old_state, RunState.ADJUSTING)

            # Broadcast state change to both run and group
            await manager.broadcast(f"run:{run_uuid}", {
                "type": "state_changed",
                "data": {
                    "run_id": str(run_uuid),
                    "new_state": RunState.ADJUSTING
                }
            })
            await manager.broadcast(f"group:{run.group_id}", {
                "type": "run_state_changed",
                "data": {
                    "run_id": str(run_uuid),
                    "new_state": RunState.ADJUSTING
                }
            })

            return {
                "message": "Some items have insufficient quantities. Participants need to adjust their bids.",
                "state": RunState.ADJUSTING
            }

        # Otherwise, proceed with distribution
        # For each shopping item (purchased product), distribute to users who bid
        for shopping_item in shopping_items:
            if not shopping_item.is_purchased:
                continue

            # Get all bids for this product
            product_bids = [bid for bid in all_bids if bid.product_id == shopping_item.product_id and not bid.interested_only]

            # Distribute the purchased items to bidders (all quantities match)
            for bid in product_bids:
                if hasattr(self.repo, '_bids'):  # Memory mode
                    bid.distributed_quantity = bid.quantity
                    bid.distributed_price_per_unit = shopping_item.purchased_price_per_unit
                else:  # Database mode
                    from ..models import ProductBid
                    db_bid = db.query(ProductBid).filter(ProductBid.id == bid.id).first()
                    if db_bid:
                        db_bid.distributed_quantity = bid.quantity
                        db_bid.distributed_price_per_unit = shopping_item.purchased_price_per_unit

        if not hasattr(self.repo, '_bids'):  # Database mode
            db.commit()

        # Transition to distributing state
        old_state = run.state
        self.repo.update_run_state(run_uuid, RunState.DISTRIBUTING)

        # Create notifications for all participants
        self._notify_run_state_change(run, old_state, RunState.DISTRIBUTING)

        # Broadcast state change to both run and group
        await manager.broadcast(f"run:{run_uuid}", {
            "type": "state_changed",
            "data": {
                "run_id": str(run_uuid),
                "new_state": RunState.DISTRIBUTING
            }
        })
        await manager.broadcast(f"group:{run.group_id}", {
            "type": "run_state_changed",
            "data": {
                "run_id": str(run_uuid),
                "new_state": RunState.DISTRIBUTING
            }
        })

        return {"message": "Shopping completed! Moving to distribution.", "state": RunState.DISTRIBUTING}

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
