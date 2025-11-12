"""Run service for managing run business logic."""

from typing import Any
from uuid import UUID

from app.api.schemas import (
    AvailableProductResponse,
    CancelRunResponse,
    CreateRunResponse,
    MessageResponse,
    ParticipantResponse,
    PlaceBidResponse,
    ProductResponse,
    ReadyToggleResponse,
    RetractBidResponse,
    RunDetailResponse,
    StateChangeResponse,
    UserBidResponse,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import Product, ProductBid, Run, User
from app.core.run_state import RunState, state_machine
from app.events.domain_events import RunCreatedEvent
from app.events.event_bus import event_bus
from app.infrastructure.config import MAX_ACTIVE_RUNS_PER_GROUP
from app.infrastructure.request_context import get_logger
from app.utils.validation import validate_uuid

from .base_service import BaseService
from .bid_service import BidService
from .run_notification_service import RunNotificationService
from .run_state_service import RunStateService

logger = get_logger(__name__)


class RunService(BaseService):
    """Service for managing run operations.

    This service coordinates between BidService, RunStateService, and RunNotificationService
    for complex run operations.
    """

    def __init__(self, db):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db)
        self.bid_service = BidService(db)
        self.notification_service = RunNotificationService(db)
        self.state_service = RunStateService(db, self.notification_service)

    def create_run(self, group_id: str, store_id: str, user: User, comment: str | None = None) -> CreateRunResponse:
        """Create a new run for a group.

        Args:
            group_id: Group ID as string
            store_id: Store ID as string
            user: Current user creating the run
            comment: Optional comment/description for the run

        Returns:
            CreateRunResponse with run data

        Raises:
            BadRequestError: If ID format is invalid
            NotFoundError: If group or store not found
            ForbiddenError: If user is not a member of the group
        """
        logger.info(
            'Creating run for group',
            extra={'user_id': str(user.id), 'group_id': group_id, 'store_id': store_id},
        )

        # Validate IDs
        group_uuid = validate_uuid(group_id, 'Group')
        store_uuid = validate_uuid(store_id, 'Store')

        # Verify group exists and user is a member
        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError('Group', group_id)

        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == group_uuid for g in user_groups):
            raise ForbiddenError('Not authorized to create runs for this group')

        # Verify store exists
        all_stores = self.repo.get_all_stores()
        store = next((s for s in all_stores if s.id == store_uuid), None)
        if not store:
            raise NotFoundError('Store', store_id)

        # Check active runs limit for the group - use state machine
        group_runs = self.repo.get_runs_by_group(group_uuid)
        active_runs = [r for r in group_runs if state_machine.is_active_run(RunState(r.state))]
        if len(active_runs) >= MAX_ACTIVE_RUNS_PER_GROUP:
            logger.warning(
                'Group has reached maximum active runs limit',
                extra={
                    'user_id': str(user.id),
                    'group_id': str(group_uuid),
                    'active_runs': len(active_runs),
                },
            )
            raise BadRequestError(
                f'Group has reached maximum of {MAX_ACTIVE_RUNS_PER_GROUP} active runs'
            )

        # Create the run with current user as leader
        run = self.repo.create_run(group_uuid, store_uuid, user.id, comment)

        logger.info(
            'Run created successfully',
            extra={'user_id': str(user.id), 'run_id': str(run.id), 'group_id': str(group_uuid)},
        )

        # Emit domain event for run creation
        event_bus.emit(
            RunCreatedEvent(
                run_id=run.id,
                group_id=run.group_id,
                store_id=run.store_id,
                store_name=store.name,
                state=run.state,
                leader_name=user.name,
            )
        )

        return CreateRunResponse(
            id=str(run.id),
            group_id=str(run.group_id),
            store_id=str(run.store_id),
            state=run.state,
            store_name=store.name,
            leader_name=user.name,
        )

    def get_run_details(self, run_id: str, user: User) -> RunDetailResponse:
        """Get detailed information about a specific run.

        Args:
            run_id: Run ID as string
            user: Current user requesting details

        Returns:
            RunDetailResponse with run details including products, participants, etc.

        Raises:
            BadRequestError: If run ID format is invalid
            NotFoundError: If run not found
            ForbiddenError: If user is not authorized to view the run
        """
        # Validate and get run with authorization check
        run_uuid = self._validate_run_id(run_id)
        run = self._get_run_with_auth_check(run_uuid, user)

        # Get related entities
        group = self.repo.get_group_by_id(run.group_id)
        all_stores = self.repo.get_all_stores()
        store = next((s for s in all_stores if s.id == run.store_id), None)

        if not group or not store:
            raise NotFoundError('Group or Store', str(run.group_id) + ' or ' + str(run.store_id))

        # Get participants data
        participants, current_user_is_ready, current_user_is_leader, current_user_is_helper, leader_name, helpers = (
            self._get_participants_data(run.id, user.id)
        )

        # Get products data
        products = self._get_products_data(run, user.id)

        return RunDetailResponse(
            id=str(run.id),
            group_id=str(run.group_id),
            group_name=group.name,
            store_id=str(run.store_id),
            store_name=store.name,
            state=run.state,
            comment=run.comment,
            products=products,
            participants=participants,
            current_user_is_ready=current_user_is_ready,
            current_user_is_leader=current_user_is_leader,
            current_user_is_helper=current_user_is_helper,
            leader_name=leader_name,
            helpers=helpers,
        )

    def place_bid(
        self, run_id: str, product_id: str, quantity: float, interested_only: bool, user: User, comment: str | None = None
    ) -> PlaceBidResponse:
        """Place or update a bid on a product in a run.

        Delegates to BidService.

        Args:
            run_id: Run ID as string
            product_id: Product ID as string
            quantity: Quantity to bid
            interested_only: Whether this is an interest-only bid
            user: Current user placing the bid
            comment: Optional comment/note for the bid

        Returns:
            PlaceBidResponse with status and calculated totals for broadcasting
        """
        return self.bid_service.place_bid(run_id, product_id, quantity, interested_only, user, comment)

    def retract_bid(self, run_id: str, product_id: str, user: User) -> RetractBidResponse:
        """Retract a user's bid on a product in a run.

        Delegates to BidService.

        Args:
            run_id: Run ID as string
            product_id: Product ID as string
            user: Current user retracting the bid

        Returns:
            RetractBidResponse with success message and updated totals
        """
        return self.bid_service.retract_bid(run_id, product_id, user)

    def toggle_ready(self, run_id: str, user: User) -> ReadyToggleResponse:
        """Toggle the current user's ready status for a run.

        Delegates to RunStateService.

        Args:
            run_id: Run ID as string
            user: Current user toggling ready status

        Returns:
            ReadyToggleResponse with ready status and whether state changed
        """
        return self.state_service.toggle_ready(run_id, user)

    def force_confirm_run(self, run_id: str, user: User) -> StateChangeResponse:
        """Force confirm run - transition from active to confirmed without waiting for all users (leader only).

        Delegates to RunStateService.

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            StateChangeResponse with success message and new state
        """
        return self.state_service.force_confirm(run_id, user)

    def start_run(self, run_id: str, user: User) -> StateChangeResponse:
        """Start shopping - transition from confirmed to shopping state (leader only).

        Delegates to RunStateService.

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            StateChangeResponse with success message and new state
        """
        return self.state_service.start_shopping(run_id, user)

    def transition_to_shopping(self, run_id: str, user: User) -> StateChangeResponse:
        """Transition from confirmed to shopping state.

        This is an alias for start_run() to match the expected method name.

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            StateChangeResponse with success message and new state
        """
        return self.start_run(run_id, user)

    def finish_adjusting(self, run_id: str, user: User, force: bool = False) -> StateChangeResponse:
        """Finish adjusting bids - transition from adjusting to distributing state (leader only).

        Delegates to RunStateService.

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)
            force: If True, skip quantity verification

        Returns:
            StateChangeResponse with success message and new state
        """
        return self.state_service.finish_adjusting(run_id, user, force)

    def cancel_run(self, run_id: str, user: User) -> CancelRunResponse:
        """Cancel a run.

        Delegates to RunStateService.

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            CancelRunResponse with success message
        """
        return self.state_service.cancel_run(run_id, user)

    def update_run_comment(self, run_id: str, comment: str | None, user: User) -> MessageResponse:
        """Update the comment/description for a run.

        Args:
            run_id: Run ID as string
            comment: New comment (or None to clear)
            user: Current user (must be leader)

        Returns:
            MessageResponse with success message

        Raises:
            BadRequestError: If run ID format is invalid
            NotFoundError: If run not found
            ForbiddenError: If user is not the run leader
        """
        # Validate and get run with authorization check
        run_uuid = self._validate_run_id(run_id)
        run = self._get_run_with_auth_check(run_uuid, user)

        # Check if user is the leader
        participation = self.repo.get_participation(user.id, run_uuid)
        if not participation or not participation.is_leader:
            raise ForbiddenError('Only the run leader can update the comment')

        # Update the comment
        updated_run = self.repo.update_run_comment(run_uuid, comment)
        if not updated_run:
            raise NotFoundError('Run', run_id)

        logger.info(
            'Run comment updated',
            extra={'run_id': run_id, 'user_id': str(user.id)},
        )

        return MessageResponse(message='Comment updated successfully')

    def delete_run(self, run_id: str, user: User) -> CancelRunResponse:
        """Delete a run (alias for cancel_run for backward compatibility).

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            CancelRunResponse with success message
        """
        return self.cancel_run(run_id, user)

    def get_available_products(self, run_id: str, user: User) -> list[AvailableProductResponse]:
        """Get products available for bidding (all products without bids yet).

        Products with availability at the run's store are sorted first.

        Args:
            run_id: Run ID as string
            user: Current user

        Returns:
            List of AvailableProductResponse, sorted with store products first

        Raises:
            BadRequestError: If run ID format is invalid
            NotFoundError: If run not found
            ForbiddenError: If user not authorized
        """
        # Validate run ID
        run_uuid = validate_uuid(run_id, 'Run')

        # Verify run exists and user has access
        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError('Run', run_id)

        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError('Not authorized to view this run')

        # Get all products
        all_products = self.repo.get_all_products()
        run_bids = self.repo.get_bids_by_run(run.id)

        # Get products that have bids
        products_with_bids = {bid.product_id for bid in run_bids}

        # Return products that don't have bids, sorted by availability at run's store
        available_products = []
        for product in all_products:
            if product.id not in products_with_bids:
                # Get product availability/price for this store
                availability = self.repo.get_availability_by_product_and_store(
                    product.id, run.store_id
                )
                current_price = (
                    str(availability.price) if availability and availability.price else None
                )
                has_store_availability = availability is not None

                available_products.append(
                    AvailableProductResponse(
                        id=str(product.id),
                        name=product.name,
                        brand=product.brand,
                        current_price=current_price,
                        has_store_availability=has_store_availability,
                    )
                )

        # Sort: products with store availability first, then alphabetically by name
        available_products.sort(key=lambda p: (not p.has_store_availability, p.name.lower()))

        return available_products

    def _validate_run_id(self, run_id: str) -> UUID:
        """Validate and convert run ID string to UUID."""
        return validate_uuid(run_id, 'Run')

    def _get_run_with_auth_check(self, run_uuid: UUID, user: User) -> Run:
        """Get run and verify user has access to it."""
        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError('Run', str(run_uuid))

        # Verify user has access to this run (member of the group)
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError('Not authorized to view this run')

        return run

    def _get_participants_data(
        self, run_id: UUID, current_user_id: UUID
    ) -> tuple[list[ParticipantResponse], bool, bool, bool, str, list[str]]:
        """Get participants data for a run.

        Returns:
            Tuple of (participants_list, current_user_is_ready, current_user_is_leader, current_user_is_helper, leader_name, helpers)
        """
        participants_data = []
        current_user_is_ready = False
        current_user_is_leader = False
        leader_name = 'Unknown'
        current_user_is_helper = False
        helpers = []

        participations = self.repo.get_run_participations_with_users(run_id)

        for participation in participations:
            # Check if this is the current user's participation
            if participation.user_id == current_user_id:
                current_user_is_ready = participation.is_ready
                current_user_is_leader = participation.is_leader
                current_user_is_helper = participation.is_helper

            # Find the leader
            if participation.is_leader and participation.user:
                leader_name = participation.user.name

            # Collect helpers
            if participation.is_helper and participation.user:
                helpers.append(participation.user.name)

            # Add to participants list if user data is available
            if participation.user:
                participants_data.append(
                    ParticipantResponse(
                        user_id=str(participation.user_id),
                        user_name=participation.user.name,
                        is_leader=participation.is_leader,
                        is_helper=participation.is_helper,
                        is_ready=participation.is_ready,
                        is_removed=participation.is_removed,
                    )
                )

        return participants_data, current_user_is_ready, current_user_is_leader, current_user_is_helper, leader_name, helpers

    def _get_products_data(self, run: Run, current_user_id: UUID) -> list[ProductResponse]:
        """Get products data with bids for a run."""
        # Get bids with participations and users eagerly loaded to avoid N+1 queries
        run_bids = self.repo.get_bids_by_run_with_participations(run.id)

        # Get shopping list items if in adjusting, distributing, or completed state
        shopping_list_map = (
            self._get_shopping_list_map(run)
            if run.state in [RunState.ADJUSTING, RunState.DISTRIBUTING, RunState.COMPLETED]
            else {}
        )

        # Get all unique product IDs that have bids
        product_ids_with_bids = {bid.product_id for bid in run_bids}

        # Fetch all products that have bids (whether or not they have store availability)
        products_map = {}
        for product_id in product_ids_with_bids:
            product = self.repo.get_product_by_id(product_id)
            if product:
                products_map[product_id] = product

        # Calculate product statistics
        products_data = []
        for product_id, product in products_map.items():
            product_bids = [bid for bid in run_bids if bid.product_id == product_id]

            if len(product_bids) > 0:  # Only include products with bids
                product_response = self._build_product_response(
                    product, product_bids, current_user_id, run, shopping_list_map
                )
                products_data.append(product_response)

        return products_data

    def _get_shopping_list_map(self, run: Run) -> dict[UUID, Any]:
        """Get shopping list items mapped by product ID."""
        shopping_items = self.repo.get_shopping_list_items(run.id)
        return {item.product_id: item for item in shopping_items}

    def _build_product_response(
        self,
        product: Product,
        product_bids: list[ProductBid],
        current_user_id: UUID,
        run: Run,
        shopping_list_map: dict[UUID, Any],
    ) -> ProductResponse:
        """Build a ProductResponse from product and its bids."""
        # Calculate statistics
        total_quantity, interested_count = self._calculate_product_statistics(product_bids)

        # Get user bids
        user_bids_data, current_user_bid = self._get_user_bids_data(product_bids, current_user_id)

        # Get purchased quantity if in adjusting state
        purchased_qty = None
        if product.id in shopping_list_map:
            purchased_qty = shopping_list_map[product.id].purchased_quantity

        # Get product availability/price for this store
        availability = self.repo.get_availability_by_product_and_store(product.id, run.store_id)
        current_price = str(availability.price) if availability and availability.price else None

        return ProductResponse(
            id=str(product.id),
            name=product.name,
            brand=product.brand,
            unit=product.unit,
            current_price=current_price,
            total_quantity=total_quantity,
            interested_count=interested_count,
            user_bids=user_bids_data,
            current_user_bid=current_user_bid,
            purchased_quantity=purchased_qty,
        )

    def _calculate_product_statistics(self, product_bids: list[ProductBid]) -> tuple[int, int]:
        """Calculate total quantity and interested count for product bids."""
        total_quantity = sum(bid.quantity for bid in product_bids)
        interested_count = len(
            [bid for bid in product_bids if bid.interested_only or bid.quantity > 0]
        )
        return total_quantity, interested_count

    def _get_user_bids_data(
        self, product_bids: list[ProductBid], current_user_id: UUID
    ) -> tuple[list[UserBidResponse], UserBidResponse | None]:
        """Get user bids data and identify current user's bid."""
        user_bids_data = []
        current_user_bid = None

        for bid in product_bids:
            # Participation and user are eagerly loaded on the bid object
            if bid.participation and bid.participation.user:
                bid_response = UserBidResponse(
                    user_id=str(bid.participation.user_id),
                    user_name=bid.participation.user.name,
                    quantity=bid.quantity,
                    interested_only=bid.interested_only,
                    comment=bid.comment,
                )
                user_bids_data.append(bid_response)

                # Check if this is the current user's bid
                if bid.participation.user_id == current_user_id:
                    current_user_bid = bid_response

        return user_bids_data, current_user_bid

    def toggle_helper(self, run_id: str, target_user_id: str, current_user: User) -> MessageResponse:
        """Toggle helper status for a run participant.

        Args:
            run_id: The run ID as string
            target_user_id: The user ID to toggle helper status for
            current_user: The authenticated user (must be leader)

        Returns:
            MessageResponse with success message

        Raises:
            BadRequestError: If ID format is invalid
            NotFoundError: If run or user is not found
            ForbiddenError: If current user is not the run leader
            BadRequestError: If trying to make leader a helper
        """
        from uuid import UUID

        # Validate IDs
        try:
            run_uuid = UUID(run_id)
            target_user_uuid = UUID(target_user_id)
        except ValueError as e:
            raise BadRequestError('Invalid ID format') from e

        # Get the run
        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError('Run', run_id)

        # Verify current user is the run leader
        current_participation = self.repo.get_participation(current_user.id, run_uuid)
        if not current_participation or not current_participation.is_leader:
            raise ForbiddenError('Only the run leader can manage helpers')

        # Verify target user is a member of the group
        target_user = self.repo.get_user_by_id(target_user_uuid)
        if not target_user:
            raise NotFoundError('User', target_user_id)

        target_user_groups = self.repo.get_user_groups(target_user)
        if not any(g.id == run.group_id for g in target_user_groups):
            raise BadRequestError('User is not a member of this group')

        # Get or create target user's participation
        target_participation = self.repo.get_participation(target_user_uuid, run_uuid)

        # Cannot make leader a helper
        if target_participation and target_participation.is_leader:
            raise BadRequestError('Cannot assign helper status to the run leader')

        if not target_participation:
            # Create participation as helper for this user if they're not yet a participant
            target_participation = self.repo.create_participation(
                user_id=target_user_uuid,
                run_id=run_uuid,
                is_leader=False,
                is_helper=True
            )
            new_helper_status = True
        else:
            # Toggle helper status
            new_helper_status = not target_participation.is_helper
            self.repo.update_participation_helper(target_user_uuid, run_uuid, new_helper_status)

        action = 'added as' if new_helper_status else 'removed as'
        return MessageResponse(message=f'User {action} helper')

    def export_run_state(self, run_id: str, user: User) -> dict[str, Any]:
        """Export the current state of a run as structured JSON.

        Available for runs in confirmed, shopping, adjusting, or distributing states.
        Only accessible by run leader or helpers.

        Args:
            run_id: Run ID as string
            user: Current user requesting export

        Returns:
            Dictionary with run state including per_product and per_user breakdowns

        Raises:
            BadRequestError: If run ID format is invalid or run not in exportable state
            NotFoundError: If run not found
            ForbiddenError: If user is not leader or helper
        """
        # Validate and get run with authorization check
        run_uuid = self._validate_run_id(run_id)
        run = self._get_run_with_auth_check(run_uuid, user)

        # Check if user is leader or helper
        participation = self.repo.get_participation(user.id, run_uuid)
        if not participation or not (participation.is_leader or participation.is_helper):
            raise ForbiddenError('Only run leader and helpers can export run state')

        # Check if run is in an exportable state
        exportable_states = [RunState.CONFIRMED, RunState.SHOPPING, RunState.ADJUSTING, RunState.DISTRIBUTING]
        if RunState(run.state) not in exportable_states:
            raise BadRequestError(f'Run state export is only available in {", ".join(s.value for s in exportable_states)} states')

        # Get all bids with participations and users
        run_bids = self.repo.get_bids_by_run_with_participations(run.id)

        # Get shopping list items if in adjusting or distributing state
        shopping_list_map = {}
        if RunState(run.state) in [RunState.ADJUSTING, RunState.DISTRIBUTING]:
            shopping_items = self.repo.get_shopping_list_items(run.id)
            shopping_list_map = {item.product_id: item for item in shopping_items}

        # Build the export data structure
        per_product = {}
        per_user = {}
        total_price = 0.0

        # Group bids by product
        products_map = {}
        for bid in run_bids:
            if bid.interested_only:
                continue

            if bid.product_id not in products_map:
                products_map[bid.product_id] = []
            products_map[bid.product_id].append(bid)

        # Process each product
        for product_id, product_bids in products_map.items():
            product = self.repo.get_product_by_id(product_id)
            if not product:
                continue

            total_quantity_requested = sum(bid.quantity for bid in product_bids)

            # Get shopping list data if available
            shopping_item = shopping_list_map.get(product_id)
            total_quantity_purchased = float(shopping_item.purchased_quantity) if shopping_item and shopping_item.purchased_quantity else None
            purchased_price_per_unit = float(shopping_item.purchased_price_per_unit) if shopping_item and shopping_item.purchased_price_per_unit else None

            # Build per-user data for this product
            per_user_product = {}
            for bid in product_bids:
                if not bid.participation or not bid.participation.user:
                    continue

                username = bid.participation.user.name
                quantity_requested = float(bid.quantity)

                # For distributing state, use distributed quantities and prices
                if RunState(run.state) == RunState.DISTRIBUTING:
                    quantity_purchased = float(bid.distributed_quantity) if bid.distributed_quantity else 0.0
                    price_per_unit = float(bid.distributed_price_per_unit) if bid.distributed_price_per_unit else 0.0
                    item_price = quantity_purchased * price_per_unit
                else:
                    quantity_purchased = quantity_requested if purchased_price_per_unit is not None else None
                    item_price = (quantity_purchased * purchased_price_per_unit) if (quantity_purchased is not None and purchased_price_per_unit is not None) else None

                per_user_product[username] = {
                    'quantity_requested': quantity_requested,
                    'quantity_purchased': quantity_purchased,
                    'price': item_price,
                    'is_picked_up': bid.is_picked_up
                }

                # Add to per-user total
                if username not in per_user:
                    per_user[username] = {
                        'total_price': 0.0,
                        'per_product': {}
                    }

                per_user[username]['per_product'][str(product_id)] = {
                    'product_name': product.name,
                    'quantity_requested': quantity_requested,
                    'quantity_purchased': quantity_purchased,
                    'price': item_price,
                    'is_picked_up': bid.is_picked_up
                }

                if item_price is not None:
                    per_user[username]['total_price'] += item_price
                    total_price += item_price

            # Build product entry
            per_product[str(product_id)] = {
                'name': product.name,
                'total_quantity_requested': total_quantity_requested,
                'total_quantity_purchased': total_quantity_purchased,
                'purchased_price_per_unit': purchased_price_per_unit,
                'per_user': per_user_product
            }

        logger.info(
            'Run state exported',
            extra={'run_id': run_id, 'user_id': str(user.id), 'state': run.state}
        )

        return {
            'total_price': total_price,
            'per_product': per_product,
            'per_user': per_user
        }
