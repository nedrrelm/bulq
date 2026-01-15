"""Shopping service for handling shopping list operations."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.api.schemas import (
    CompleteShoppingResponse,
    MarkPurchasedResponse,
    PriceObservation,
    ShoppingListItemResponse,
    SuccessResponse,
)
from app.api.schemas.notification_data import RunStateChangedData
from app.api.websocket_manager import manager
from app.core.error_codes import (
    INVALID_ID_FORMAT,
    INVALID_RUN_STATE_TRANSITION,
    NOT_RUN_LEADER,
    NOT_RUN_LEADER_OR_HELPER,
    NOT_RUN_PARTICIPANT,
    RUN_NOT_FOUND,
    RUN_NOT_IN_SHOPPING_STATE,
    SHOPPING_ITEM_NOT_PURCHASED,
    SHOPPING_LIST_ITEM_NOT_FOUND,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import User
from app.core.run_state import RunState, state_machine
from app.core.success_codes import (
    ADDITIONAL_PURCHASE_ADDED,
    ITEM_MARKED_PURCHASED,
    PRICE_UPDATED,
    SHOPPING_COMPLETED_ADJUSTING_REQUIRED,
    SHOPPING_COMPLETED_DISTRIBUTING,
    SHOPPING_COMPLETED_NO_PURCHASES,
)
from app.infrastructure.request_context import get_logger
from app.infrastructure.transaction import transaction
from app.repositories import (
    get_bid_repository,
    get_notification_repository,
    get_product_repository,
    get_run_repository,
    get_shopping_repository,
    get_store_repository,
    get_user_repository,
)
from app.utils.background_tasks import create_background_task

from .base_service import BaseService

logger = get_logger(__name__)


class ShoppingService(BaseService):
    """Service for managing shopping list operations."""

    def __init__(self, db: Session):
        """Initialize service with necessary repositories."""
        super().__init__(db)
        self.bid_repo = get_bid_repository(db)
        self.notification_repo = get_notification_repository(db)
        self.product_repo = get_product_repository(db)
        self.run_repo = get_run_repository(db)
        self.shopping_repo = get_shopping_repository(db)
        self.store_repo = get_store_repository(db)
        self.user_repo = get_user_repository(db)

    def _is_leader_or_helper(self, participation) -> bool:
        """Check if participation is leader or helper."""
        return participation.is_leader or participation.is_helper

    async def _update_product_availability_if_needed(
        self, product_id: UUID, store_id: UUID, price: float, user_id: UUID
    ) -> None:
        """Update ProductAvailability if the price differs from prices seen today.

        Args:
            product_id: Product UUID
            store_id: Store UUID
            price: The purchased price
            user_id: User who made the purchase
        """
        try:
            # Get existing availabilities for this product at this store
            availabilities = self.product_repo.get_product_availabilities(product_id, store_id)

            # Check if we have any prices from today
            today = datetime.now(UTC).date()
            today_prices = [
                float(avail.price)
                for avail in availabilities
                if avail.price is not None and avail.created_at.date() == today
            ]

            # If no prices today, or price differs from all today's prices, create new availability
            if not today_prices or price not in today_prices:
                self.product_repo.create_product_availability(
                    product_id=product_id,
                    store_id=store_id,
                    price=price,
                    notes='Purchased during shopping',
                    user_id=user_id,
                )
                logger.info(
                    'Created product availability for different price',
                    extra={
                        'product_id': str(product_id),
                        'store_id': str(store_id),
                        'price': price,
                        'user_id': str(user_id),
                    },
                )
        except Exception as e:
            # Don't fail the purchase if availability update fails
            logger.error(
                'Failed to update product availability',
                extra={
                    'product_id': str(product_id),
                    'store_id': str(store_id),
                    'price': price,
                    'error': str(e),
                },
            )

    async def get_shopping_list(self, run_id: str, user: User) -> list[ShoppingListItemResponse]:
        """Get shopping list for a run with auth check.

        Args:
            run_id: The run ID as string
            user: The authenticated user

        Returns:
            List of ShoppingListItemResponse with product details

        Raises:
            BadRequestError: If run ID format is invalid
            NotFoundError: If run is not found
            ForbiddenError: If user doesn't have access to the run
            BadRequestError: If shopping list is not available in current state
        """
        # Validate run ID
        try:
            run_uuid = UUID(run_id)
        except ValueError as e:
            raise BadRequestError(code=INVALID_ID_FORMAT, message='Invalid run ID format') from e

        # Get the run
        run = self.run_repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError(code=RUN_NOT_FOUND, message='Run not found', run_id=run_id)

        # Verify user has access to this run
        user_groups = self.user_repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError(
                code=NOT_RUN_PARTICIPANT, message='Not authorized to view this run', run_id=run_id
            )

        # Only allow viewing shopping list in shopping or later states - use state machine
        run_state = RunState(run.state)
        if not state_machine.can_view_shopping_list(run_state):
            raise BadRequestError(
                code=INVALID_RUN_STATE_TRANSITION,
                current_state=run.state,
                action='view_shopping_list',
                allowed_states='shopping, adjusting, distributing, completed',
            )

        # Get shopping list items
        items = self.shopping_repo.get_shopping_list_items(run_uuid)

        # Convert to response format
        response_items = []
        for item in items:
            # Get product directly by ID
            product = self.product_repo.get_product_by_id(item.product_id)

            # Get all product availabilities for this product at this store
            all_availabilities = self.product_repo.get_product_availabilities(
                product_id=item.product_id, store_id=run.store_id
            )

            # Find the most recent price observation
            most_recent = None
            for avail in all_availabilities:
                if (
                    avail.price
                    and avail.created_at
                    and (most_recent is None or avail.created_at > most_recent.created_at)
                ):
                    most_recent = avail

            # Get all prices from the same day as the most recent observation
            recent_day_prices = []
            if most_recent:
                # Get the day boundaries for the most recent price
                recent_date = most_recent.created_at.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                recent_date_end = recent_date + timedelta(days=1)

                # Filter to only prices from that day
                for avail in all_availabilities:
                    if (
                        avail.price
                        and avail.created_at
                        and recent_date <= avail.created_at < recent_date_end
                    ):
                        recent_day_prices.append(
                            {
                                'price': float(avail.price),
                                'notes': avail.notes or '',
                                'created_at': avail.created_at.isoformat()
                                if avail.created_at
                                else None,
                            }
                        )

                # Sort by created_at descending (newest first)
                recent_day_prices.sort(
                    key=lambda x: x['created_at'] if x['created_at'] else '', reverse=True
                )

            recent_prices_models = [PriceObservation(**p) for p in recent_day_prices]

            response_items.append(
                ShoppingListItemResponse(
                    id=str(item.id),
                    product_id=str(item.product_id),
                    product_name=product.name if product else 'Unknown Product',
                    product_unit=product.unit if product else None,
                    requested_quantity=item.requested_quantity,
                    recent_prices=recent_prices_models,
                    purchased_quantity=item.purchased_quantity,
                    purchased_price_per_unit=str(item.purchased_price_per_unit)
                    if item.purchased_price_per_unit
                    else None,
                    purchased_total=str(item.purchased_total) if item.purchased_total else None,
                    is_purchased=item.is_purchased,
                    purchase_order=item.purchase_order,
                )
            )

        # Sort: unpurchased first, then purchased by purchase order
        response_items.sort(
            key=lambda x: (x.is_purchased, x.purchase_order if x.purchase_order else 999)
        )

        return response_items

    async def add_product_to_shopping_list(
        self, run_id: str, product_id: str, quantity: float, user: User
    ) -> SuccessResponse:
        """Add a product to the shopping list during shopping state.

        This method creates both a ProductBid and a ShoppingListItem to ensure
        proper tracking and distribution later.

        Args:
            run_id: The run ID as string
            product_id: The product ID as string
            quantity: The requested quantity
            user: The authenticated user

        Returns:
            SuccessResponse

        Raises:
            BadRequestError: If ID format invalid or run not in shopping state
            NotFoundError: If run or product not found
            ForbiddenError: If user is not leader or helper
        """
        # Validate IDs
        try:
            run_uuid = UUID(run_id)
            product_uuid = UUID(product_id)
        except ValueError as e:
            raise BadRequestError(code=INVALID_ID_FORMAT, message='Invalid ID format') from e

        # Get the run
        run = self.run_repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError(code=RUN_NOT_FOUND, message='Run not found', run_id=run_id)

        # Verify run is in shopping state
        if run.state != RunState.SHOPPING:
            raise BadRequestError(
                code=RUN_NOT_IN_SHOPPING_STATE,
                message='Can only add products to shopping list during shopping state',
                run_id=run_id,
                current_state=run.state.value,
            )

        # Verify user is leader or helper
        participation = self.run_repo.get_participation(user.id, run_uuid)
        if not participation or not self._is_leader_or_helper(participation):
            raise ForbiddenError(
                code=NOT_RUN_LEADER_OR_HELPER,
                message='Only the run leader or helpers can add products during shopping',
                run_id=run_id,
            )

        # Verify product exists
        product = self.product_repo.get_product_by_id(product_uuid)
        if not product:
            raise NotFoundError(
                code='PRODUCT_NOT_FOUND',
                message='Product not found',
                product_id=product_id,
            )

        # Create a ProductBid for the user who is adding the product
        # This ensures the product has a bid for distribution later
        bid = self.bid_repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=product_uuid,
            quantity=int(quantity),
            interested_only=False,
            comment=None,
        )

        # Create shopping list item
        item = self.shopping_repo.create_shopping_list_item(run_uuid, product_uuid, quantity)

        logger.info(
            'Added product to shopping list with bid',
            extra={
                'run_id': run_id,
                'product_id': product_id,
                'quantity': quantity,
                'user_id': str(user.id),
                'bid_id': str(bid.id),
                'item_id': str(item.id),
            },
        )

        return SuccessResponse(
            code='PRODUCT_ADDED_TO_SHOPPING_LIST',
            details={
                'run_id': str(run_id),
                'product_id': str(product_id),
                'item_id': str(item.id),
                'bid_id': str(bid.id),
            },
        )

    async def add_availability_price(
        self,
        run_id: str,
        item_id: str,
        price: float,
        notes: str,
        minimum_quantity: int | None,
        user: User,
    ) -> SuccessResponse:
        """Update product availability price for a shopping list item.

        Args:
            run_id: The run ID as string
            item_id: The shopping list item ID as string
            price: The price to set
            notes: Optional notes about the price
            minimum_quantity: Optional minimum quantity required for this price
            user: The authenticated user

        Returns:
            MessageResponse with success message

        Raises:
            BadRequestError: If ID format is invalid
            NotFoundError: If run or item is not found
            ForbiddenError: If user is not the run leader
        """
        # Validate IDs
        try:
            run_uuid = UUID(run_id)
            item_uuid = UUID(item_id)
        except ValueError as e:
            raise BadRequestError(code=INVALID_ID_FORMAT, message='Invalid ID format') from e

        # Get the run
        run = self.run_repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError(code=RUN_NOT_FOUND, message='Run not found', run_id=run_id)

        # Verify user is the run leader or helper
        participation = self.run_repo.get_participation(user.id, run_uuid)
        if not participation or not self._is_leader_or_helper(participation):
            raise ForbiddenError(
                code=NOT_RUN_LEADER_OR_HELPER,
                message='Only the run leader or helpers can add prices',
                run_id=run_id,
            )

        # Get the shopping list item to find the product
        item = self.shopping_repo.get_shopping_list_item(item_uuid)
        if not item:
            raise NotFoundError(
                code=SHOPPING_LIST_ITEM_NOT_FOUND,
                message='Shopping list item not found',
                item_id=item_id,
                run_id=run_id,
            )

        # Create or update product availability
        self.product_repo.create_product_availability(
            product_id=item.product_id,
            store_id=run.store_id,
            price=price,
            notes=notes,
            minimum_quantity=minimum_quantity,
            user_id=user.id,
        )

        return SuccessResponse(
            code=PRICE_UPDATED,
            details={
                'run_id': str(run_id),
                'item_id': str(item_id),
                'product_id': str(item.product_id),
            },
        )

    async def mark_purchased(
        self,
        run_id: str,
        item_id: str,
        quantity: float,
        price_per_unit: float,
        total: float,
        user: User,
    ) -> MarkPurchasedResponse:
        """Mark a shopping list item as purchased.

        Args:
            run_id: The run ID as string
            item_id: The shopping list item ID as string
            quantity: The purchased quantity
            price_per_unit: The price per unit
            total: The total price
            user: The authenticated user

        Returns:
            MarkPurchasedResponse with success message and purchase order

        Raises:
            BadRequestError: If ID format is invalid
            NotFoundError: If run or item is not found
            ForbiddenError: If user is not the run leader
        """
        # Validate IDs
        try:
            run_uuid = UUID(run_id)
            item_uuid = UUID(item_id)
        except ValueError as e:
            raise BadRequestError(code=INVALID_ID_FORMAT, message='Invalid ID format') from e

        # Get the run
        run = self.run_repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError(code=RUN_NOT_FOUND, message='Run not found', run_id=run_id)

        # Verify user is the run leader or helper
        participation = self.run_repo.get_participation(user.id, run_uuid)
        if not participation or not self._is_leader_or_helper(participation):
            raise ForbiddenError(
                code=NOT_RUN_LEADER_OR_HELPER,
                message='Only the run leader or helpers can mark items as purchased',
                run_id=run_id,
            )

        # Get next purchase order number
        existing_items = self.shopping_repo.get_shopping_list_items(run_uuid)
        max_order = max(
            [item.purchase_order for item in existing_items if item.purchase_order is not None],
            default=0,
        )
        next_order = max_order + 1

        # Mark as purchased
        item = self.shopping_repo.mark_item_purchased(item_uuid, quantity, price_per_unit, total, next_order)
        if not item:
            raise NotFoundError(
                code=SHOPPING_LIST_ITEM_NOT_FOUND,
                message='Shopping list item not found',
                item_id=item_id,
                run_id=run_id,
            )

        # Update ProductAvailability if the price differs from today's prices
        await self._update_product_availability_if_needed(
            item.product_id, run.store_id, price_per_unit, user.id
        )

        return MarkPurchasedResponse(
            code=ITEM_MARKED_PURCHASED,
            purchase_order=next_order,
            details={
                'run_id': str(run_id),
                'item_id': str(item_id),
                'product_id': str(item.product_id),
            },
        )

    async def add_more_purchased(
        self,
        run_id: str,
        item_id: str,
        quantity: float,
        price_per_unit: float,
        total: float,
        user: User,
    ) -> SuccessResponse:
        """Add more purchased quantity to an already-purchased item.

        This method:
        1. Verifies the user is the run leader or helper
        2. Calculates the new weighted average price per unit
        3. Updates the shopping list item with new totals
        4. Creates a new ProductAvailability if the price differs

        Args:
            run_id: The run ID as string
            item_id: The shopping list item ID as string
            quantity: The additional quantity purchased
            price_per_unit: The price per unit for this additional purchase
            total: The total price for this additional purchase
            user: The authenticated user

        Returns:
            MessageResponse with success message

        Raises:
            BadRequestError: If ID format is invalid or item is not purchased
            NotFoundError: If run or item is not found
            ForbiddenError: If user is not the run leader or helper
        """
        # Validate IDs
        try:
            run_uuid = UUID(run_id)
            item_uuid = UUID(item_id)
        except ValueError as e:
            raise BadRequestError(code=INVALID_ID_FORMAT, message='Invalid ID format') from e

        # Get the run
        run = self.run_repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError(code=RUN_NOT_FOUND, message='Run not found', run_id=run_id)

        # Verify user is the run leader or helper
        participation = self.run_repo.get_participation(user.id, run_uuid)
        if not participation or not self._is_leader_or_helper(participation):
            raise ForbiddenError(
                code=NOT_RUN_LEADER_OR_HELPER,
                message='Only the run leader or helpers can add more purchases',
                run_id=run_id,
            )

        # Get the shopping list item
        item = self.shopping_repo.get_shopping_list_item(item_uuid)
        if not item:
            raise NotFoundError(
                code=SHOPPING_LIST_ITEM_NOT_FOUND,
                message='Shopping list item not found',
                item_id=item_id,
                run_id=run_id,
            )

        if not item.is_purchased:
            raise BadRequestError(
                code=SHOPPING_ITEM_NOT_PURCHASED,
                message='Can only add more to already-purchased items',
                item_id=item_id,
                run_id=run_id,
            )

        # Calculate new weighted average price per unit
        current_quantity = float(item.purchased_quantity or 0)
        current_total = float(item.purchased_total or 0)
        new_quantity = current_quantity + quantity
        new_total = current_total + total
        new_price_per_unit = new_total / new_quantity if new_quantity > 0 else 0

        # Update the shopping list item
        updated_item = self.shopping_repo.add_more_purchased(item_uuid, quantity, total, new_price_per_unit)
        if not updated_item:
            raise NotFoundError(
                code=SHOPPING_LIST_ITEM_NOT_FOUND,
                message='Shopping list item not found',
                item_id=item_id,
                run_id=run_id,
            )

        # Update ProductAvailability if the price differs from today's prices
        await self._update_product_availability_if_needed(
            item.product_id, run.store_id, price_per_unit, user.id
        )

        logger.info(
            'Added more purchased quantity to shopping list item',
            extra={
                'run_id': run_id,
                'item_id': item_id,
                'additional_quantity': quantity,
                'additional_total': total,
                'new_total_quantity': new_quantity,
                'new_total': new_total,
                'user_id': str(user.id),
            },
        )

        return SuccessResponse(
            code=ADDITIONAL_PURCHASE_ADDED,
            details={
                'run_id': str(run_id),
                'item_id': str(item_id),
                'product_id': str(item.product_id),
                'additional_quantity': quantity,
            },
        )

    async def update_purchase(
        self,
        run_id: str,
        item_id: str,
        quantity: float,
        price_per_unit: float,
        total: float,
        user: User,
    ) -> SuccessResponse:
        """Update an existing purchase (replaces values, doesn't accumulate).

        Args:
            run_id: The run ID as string
            item_id: The shopping list item ID as string
            quantity: New purchased quantity
            price_per_unit: New price per unit
            total: New total price
            user: The authenticated user

        Returns:
            SuccessResponse with success message

        Raises:
            BadRequestError: If ID format is invalid or item is not purchased
            NotFoundError: If run or item is not found
            ForbiddenError: If user is not the run leader or helper
        """
        # Validate IDs
        try:
            run_uuid = UUID(run_id)
            item_uuid = UUID(item_id)
        except ValueError as e:
            raise BadRequestError(code=INVALID_ID_FORMAT, message='Invalid ID format') from e

        # Get the run
        run = self.run_repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError(code=RUN_NOT_FOUND, message='Run not found', run_id=run_id)

        # Verify user is the run leader or helper
        participation = self.run_repo.get_participation(user.id, run_uuid)
        if not participation or not self._is_leader_or_helper(participation):
            raise ForbiddenError(
                code=NOT_RUN_LEADER_OR_HELPER,
                message='Only the run leader or helpers can update purchases',
                run_id=run_id,
            )

        # Get the shopping list item
        item = self.shopping_repo.get_shopping_list_item(item_uuid)
        if not item:
            raise NotFoundError(
                code=SHOPPING_LIST_ITEM_NOT_FOUND,
                message='Shopping list item not found',
                item_id=item_id,
                run_id=run_id,
            )

        if not item.is_purchased:
            raise BadRequestError(
                code=SHOPPING_ITEM_NOT_PURCHASED,
                message='Can only update already-purchased items',
                item_id=item_id,
                run_id=run_id,
            )

        # Update the shopping list item
        updated_item = self.shopping_repo.update_item_purchase(item_uuid, quantity, price_per_unit, total)
        if not updated_item:
            raise NotFoundError(
                code=SHOPPING_LIST_ITEM_NOT_FOUND,
                message='Shopping list item not found',
                item_id=item_id,
                run_id=run_id,
            )

        # Update ProductAvailability if the price differs from today's prices
        await self._update_product_availability_if_needed(
            item.product_id, run.store_id, price_per_unit, user.id
        )

        logger.info(
            'Updated purchase for shopping list item',
            extra={
                'run_id': run_id,
                'item_id': item_id,
                'quantity': quantity,
                'price_per_unit': price_per_unit,
                'total': total,
                'user_id': str(user.id),
            },
        )

        return SuccessResponse(
            code='PURCHASE_UPDATED',
            details={
                'run_id': str(run_id),
                'item_id': str(item_id),
                'product_id': str(item.product_id),
            },
        )

    async def unpurchase_item(
        self,
        run_id: str,
        item_id: str,
        user: User,
    ) -> SuccessResponse:
        """Reset an item to unpurchased state.

        Args:
            run_id: The run ID as string
            item_id: The shopping list item ID as string
            user: The authenticated user

        Returns:
            SuccessResponse with success message

        Raises:
            BadRequestError: If ID format is invalid
            NotFoundError: If run or item is not found
            ForbiddenError: If user is not the run leader or helper
        """
        # Validate IDs
        try:
            run_uuid = UUID(run_id)
            item_uuid = UUID(item_id)
        except ValueError as e:
            raise BadRequestError(code=INVALID_ID_FORMAT, message='Invalid ID format') from e

        # Get the run
        run = self.run_repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError(code=RUN_NOT_FOUND, message='Run not found', run_id=run_id)

        # Verify user is the run leader or helper
        participation = self.run_repo.get_participation(user.id, run_uuid)
        if not participation or not self._is_leader_or_helper(participation):
            raise ForbiddenError(
                code=NOT_RUN_LEADER_OR_HELPER,
                message='Only the run leader or helpers can unpurchase items',
                run_id=run_id,
            )

        # Get the shopping list item
        item = self.shopping_repo.get_shopping_list_item(item_uuid)
        if not item:
            raise NotFoundError(
                code=SHOPPING_LIST_ITEM_NOT_FOUND,
                message='Shopping list item not found',
                item_id=item_id,
                run_id=run_id,
            )

        # Unpurchase the item
        unpurchased_item = self.shopping_repo.unpurchase_item(item_uuid)
        if not unpurchased_item:
            raise NotFoundError(
                code=SHOPPING_LIST_ITEM_NOT_FOUND,
                message='Shopping list item not found',
                item_id=item_id,
                run_id=run_id,
            )

        logger.info(
            'Unpurchased shopping list item',
            extra={
                'run_id': run_id,
                'item_id': item_id,
                'user_id': str(user.id),
            },
        )

        return SuccessResponse(
            code='ITEM_UNPURCHASED',
            details={
                'run_id': str(run_id),
                'item_id': str(item_id),
                'product_id': str(item.product_id),
            },
        )

    async def complete_shopping(
        self, run_id: str, user: User, db: Any = None
    ) -> CompleteShoppingResponse:
        """Complete shopping and handle shortages/transitions.

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
            CompleteShoppingResponse with message and new state

        Raises:
            BadRequestError: If run ID format is invalid or state is not 'shopping'
            NotFoundError: If run is not found
            ForbiddenError: If user is not the run leader
        """
        logger.info(
            'Completing shopping for run', extra={'user_id': str(user.id), 'run_id': run_id}
        )

        # Validate run ID
        try:
            run_uuid = UUID(run_id)
        except ValueError as e:
            raise BadRequestError(code=INVALID_ID_FORMAT, message='Invalid run ID format') from e

        # Get the run
        run = self.run_repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError(code=RUN_NOT_FOUND, message='Run not found', run_id=run_id)

        # Verify user is the run leader
        participation = self.run_repo.get_participation(user.id, run_uuid)
        if not participation or not participation.is_leader:
            raise ForbiddenError(
                code=NOT_RUN_LEADER,
                message='Only the run leader can complete shopping',
                run_id=run_id,
            )

        # Only allow completing from shopping state - use state machine
        run_state = RunState(run.state)
        if not state_machine.can_complete_shopping(run_state):
            raise BadRequestError(
                code=RUN_NOT_IN_SHOPPING_STATE,
                message='Can only complete shopping from shopping state',
                run_id=run_id,
                current_state=run.state,
                required_state=RunState.SHOPPING.value,
            )

        # Check if any items have insufficient quantities
        shopping_items = self.shopping_repo.get_shopping_list_items(run_uuid)
        all_bids = self.bid_repo.get_bids_by_run(run_uuid)

        # Check if nothing was actually purchased
        anything_purchased = any(
            item.is_purchased and item.purchased_quantity and item.purchased_quantity > 0
            for item in shopping_items
        )

        # If nothing was purchased, skip directly to distributing then completed state
        if not anything_purchased:
            with transaction(self.db, 'transition to completed state (nothing purchased)'):
                old_state = run.state
                # First transition to distributing (required by state machine)
                self.run_repo.update_run_state(run_uuid, RunState.DISTRIBUTING)
                # Then immediately to completed
                self.run_repo.update_run_state(run_uuid, RunState.COMPLETED)
                self._notify_run_state_change(run, old_state, RunState.COMPLETED)

            await manager.broadcast(
                f'run:{run_uuid}',
                {
                    'type': 'state_changed',
                    'data': {'run_id': str(run_uuid), 'new_state': RunState.COMPLETED},
                },
            )
            await manager.broadcast(
                f'group:{run.group_id}',
                {
                    'type': 'run_state_changed',
                    'data': {'run_id': str(run_uuid), 'new_state': RunState.COMPLETED},
                },
            )

            return CompleteShoppingResponse(
                code=SHOPPING_COMPLETED_NO_PURCHASES,
                state=RunState.COMPLETED,
            )

        needs_adjustment = False
        for shopping_item in shopping_items:
            if not shopping_item.is_purchased:
                continue

            # Skip items with 0 purchased quantity
            if not shopping_item.purchased_quantity or shopping_item.purchased_quantity == 0:
                continue

            # Check if purchased quantity differs from requested (either shortage or surplus)
            if shopping_item.purchased_quantity != shopping_item.requested_quantity:
                needs_adjustment = True
                break

        # If we have quantity mismatches (shortage or surplus), transition to adjusting state
        if needs_adjustment:
            # Wrap state change and notifications in transaction
            with transaction(self.db, 'transition to adjusting state'):
                old_state = run.state
                self.run_repo.update_run_state(run_uuid, RunState.ADJUSTING)

                # Create notifications for all participants
                self._notify_run_state_change(run, old_state, RunState.ADJUSTING)

            # Broadcast state change to both run and group
            await manager.broadcast(
                f'run:{run_uuid}',
                {
                    'type': 'state_changed',
                    'data': {'run_id': str(run_uuid), 'new_state': RunState.ADJUSTING},
                },
            )
            await manager.broadcast(
                f'group:{run.group_id}',
                {
                    'type': 'run_state_changed',
                    'data': {'run_id': str(run_uuid), 'new_state': RunState.ADJUSTING},
                },
            )

            return CompleteShoppingResponse(
                code=SHOPPING_COMPLETED_ADJUSTING_REQUIRED,
                state=RunState.ADJUSTING,
            )

        # Otherwise, proceed with distribution
        # Wrap distribution and state change in transaction
        with transaction(self.db, 'distribute items and transition to distributing state'):
            # For each shopping item (purchased product), distribute to users who bid
            for shopping_item in shopping_items:
                if not shopping_item.is_purchased:
                    continue

                # Skip items with 0 purchased quantity (not actually bought)
                if not shopping_item.purchased_quantity or shopping_item.purchased_quantity == 0:
                    continue

                # Get all bids for this product
                product_bids = [
                    bid
                    for bid in all_bids
                    if bid.product_id == shopping_item.product_id and not bid.interested_only
                ]

                # Distribute the purchased items to bidders (all quantities match)
                for bid in product_bids:
                    self.bid_repo.update_bid_distributed_quantities(
                        bid.id, bid.quantity, shopping_item.purchased_price_per_unit
                    )

            # Transition to distributing state
            old_state = run.state
            self.run_repo.update_run_state(run_uuid, RunState.DISTRIBUTING)

            # Create notifications for all participants
            self._notify_run_state_change(run, old_state, RunState.DISTRIBUTING)

        # Broadcast state change to both run and group
        await manager.broadcast(
            f'run:{run_uuid}',
            {
                'type': 'state_changed',
                'data': {'run_id': str(run_uuid), 'new_state': RunState.DISTRIBUTING},
            },
        )
        await manager.broadcast(
            f'group:{run.group_id}',
            {
                'type': 'run_state_changed',
                'data': {'run_id': str(run_uuid), 'new_state': RunState.DISTRIBUTING},
            },
        )

        return CompleteShoppingResponse(
            code=SHOPPING_COMPLETED_DISTRIBUTING, state=RunState.DISTRIBUTING
        )

    def _notify_run_state_change(self, run, old_state: str, new_state: str) -> None:
        """Create notifications for all participants when run state changes.

        Args:
            run: The run that changed state
            old_state: Previous state
            new_state: New state
        """
        # Get store name for notification
        all_stores = self.store_repo.get_all_stores()
        store = next((s for s in all_stores if s.id == run.store_id), None)
        store_name = store.name if store else 'Unknown Store'

        # Get all participants of this run
        participations = self.run_repo.get_run_participations(run.id)

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
            notification = self.notification_repo.create_notification(
                user_id=participation.user_id,
                type='run_state_changed',
                data=notification_data.model_dump(mode='json'),
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
                task_name=f'broadcast_shopping_notification_{participation.user_id}',
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
