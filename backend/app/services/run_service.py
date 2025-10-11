"""Run service for managing run business logic."""

from decimal import Decimal
from typing import Any
from uuid import UUID

from ..exceptions import NotFoundError, ForbiddenError, ValidationError, ConflictError, BadRequestError
from ..models import Run, Store, Group, User, Product, ProductBid, RunParticipation, ShoppingListItem
from ..run_state import RunState, state_machine
from ..config import MAX_ACTIVE_RUNS_PER_GROUP, MAX_PRODUCTS_PER_RUN
from ..request_context import get_logger
from .base_service import BaseService
from ..schemas import (
    CreateRunResponse,
    RunDetailResponse,
    ProductResponse,
    UserBidResponse,
    ParticipantResponse,
    PlaceBidResponse,
    ReadyToggleResponse,
    StateChangeResponse,
    CancelRunResponse,
    AvailableProductResponse,
    RetractBidResponse,
)

logger = get_logger(__name__)


class RunService(BaseService):
    """Service for managing run operations."""

    def create_run(self, group_id: str, store_id: str, user: User) -> CreateRunResponse:
        """
        Create a new run for a group.

        Args:
            group_id: Group ID as string
            store_id: Store ID as string
            user: Current user creating the run

        Returns:
            CreateRunResponse with run data

        Raises:
            BadRequestError: If ID format is invalid
            NotFoundError: If group or store not found
            ForbiddenError: If user is not a member of the group
        """
        logger.info(
            f"Creating run for group",
            extra={"user_id": str(user.id), "group_id": group_id, "store_id": store_id}
        )

        # Validate IDs
        try:
            group_uuid = UUID(group_id)
            store_uuid = UUID(store_id)
        except ValueError:
            raise BadRequestError("Invalid ID format")

        # Verify group exists and user is a member
        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError("Group", group_id)

        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == group_uuid for g in user_groups):
            raise ForbiddenError("Not authorized to create runs for this group")

        # Verify store exists
        all_stores = self.repo.get_all_stores()
        store = next((s for s in all_stores if s.id == store_uuid), None)
        if not store:
            raise NotFoundError("Store", store_id)

        # Check active runs limit for the group
        group_runs = self.repo.get_runs_by_group(group_uuid)
        active_runs = [r for r in group_runs if r.state not in (RunState.COMPLETED, RunState.CANCELLED)]
        if len(active_runs) >= MAX_ACTIVE_RUNS_PER_GROUP:
            logger.warning(
                f"Group has reached maximum active runs limit",
                extra={"user_id": str(user.id), "group_id": str(group_uuid), "active_runs": len(active_runs)}
            )
            raise BadRequestError(f"Group has reached maximum of {MAX_ACTIVE_RUNS_PER_GROUP} active runs")

        # Create the run with current user as leader
        run = self.repo.create_run(group_uuid, store_uuid, user.id)

        logger.info(
            f"Run created successfully",
            extra={"user_id": str(user.id), "run_id": str(run.id), "group_id": str(group_uuid)}
        )

        return CreateRunResponse(
            id=str(run.id),
            group_id=str(run.group_id),
            store_id=str(run.store_id),
            state=run.state,
            store_name=store.name,
            leader_name=user.name
        )

    def get_run_details(self, run_id: str, user: User) -> RunDetailResponse:
        """
        Get detailed information about a specific run.

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
            raise NotFoundError("Group or Store", str(run.group_id) + " or " + str(run.store_id))

        # Get participants data
        participants, current_user_is_ready, current_user_is_leader, leader_name = self._get_participants_data(
            run.id, user.id
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
            products=products,
            participants=participants,
            current_user_is_ready=current_user_is_ready,
            current_user_is_leader=current_user_is_leader,
            leader_name=leader_name
        )

    def _validate_run_id(self, run_id: str) -> UUID:
        """Validate and convert run ID string to UUID."""
        try:
            return UUID(run_id)
        except ValueError:
            raise BadRequestError("Invalid run ID format")

    def _get_run_with_auth_check(self, run_uuid: UUID, user: User) -> Run:
        """Get run and verify user has access to it."""
        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError("Run", str(run_uuid))

        # Verify user has access to this run (member of the group)
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError("Not authorized to view this run")

        return run

    def _get_participants_data(
        self, run_id: UUID, current_user_id: UUID
    ) -> tuple[list[ParticipantResponse], bool, bool, str]:
        """
        Get participants data for a run.

        Returns:
            Tuple of (participants_list, current_user_is_ready, current_user_is_leader, leader_name)
        """
        participants_data = []
        current_user_is_ready = False
        current_user_is_leader = False
        leader_name = "Unknown"

        participations = self.repo.get_run_participations_with_users(run_id)

        for participation in participations:
            # Check if this is the current user's participation
            if participation.user_id == current_user_id:
                current_user_is_ready = participation.is_ready
                current_user_is_leader = participation.is_leader

            # Find the leader
            if participation.is_leader and participation.user:
                leader_name = participation.user.name

            # Add to participants list if user data is available
            if participation.user:
                participants_data.append(ParticipantResponse(
                    user_id=str(participation.user_id),
                    user_name=participation.user.name,
                    is_leader=participation.is_leader,
                    is_ready=participation.is_ready,
                    is_removed=participation.is_removed
                ))

        return participants_data, current_user_is_ready, current_user_is_leader, leader_name

    def _get_products_data(self, run: Run, current_user_id: UUID) -> list[ProductResponse]:
        """Get products data with bids for a run."""
        # Get all products for the store
        store_products = self.repo.get_products_by_store(run.store_id)
        # Get bids with participations and users eagerly loaded to avoid N+1 queries
        run_bids = self.repo.get_bids_by_run_with_participations(run.id)

        # Get shopping list items if in adjusting state
        shopping_list_map = self._get_shopping_list_map(run) if run.state == RunState.ADJUSTING else {}

        # Calculate product statistics
        products_data = []
        for product in store_products:
            product_bids = [bid for bid in run_bids if bid.product_id == product.id]

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
        shopping_list_map: dict[UUID, Any]
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
            current_price=current_price,
            total_quantity=total_quantity,
            interested_count=interested_count,
            user_bids=user_bids_data,
            current_user_bid=current_user_bid,
            purchased_quantity=purchased_qty
        )

    def _calculate_product_statistics(self, product_bids: list[ProductBid]) -> tuple[int, int]:
        """Calculate total quantity and interested count for product bids."""
        total_quantity = sum(bid.quantity for bid in product_bids)
        interested_count = len([bid for bid in product_bids if bid.interested_only or bid.quantity > 0])
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
                    interested_only=bid.interested_only
                )
                user_bids_data.append(bid_response)

                # Check if this is the current user's bid
                if bid.participation.user_id == current_user_id:
                    current_user_bid = bid_response

        return user_bids_data, current_user_bid

    def place_bid(
        self,
        run_id: str,
        product_id: str,
        quantity: float,
        interested_only: bool,
        user: User
    ) -> PlaceBidResponse:
        """
        Place or update a bid on a product in a run.

        This is a complex method with state-based logic:
        - In planning/active states: Allow normal bidding
        - In adjusting state: Only allow downward adjustments
        - Handles auto-transitions from planning to active
        - Creates participation if needed

        Args:
            run_id: Run ID as string
            product_id: Product ID as string
            quantity: Quantity to bid
            interested_only: Whether this is an interest-only bid
            user: Current user placing the bid

        Returns:
            PlaceBidResponse with status and calculated totals for broadcasting

        Raises:
            BadRequestError: If IDs are invalid or state doesn't allow bidding
            NotFoundError: If run or product not found
            ForbiddenError: If user not authorized
        """
        logger.info(
            f"Placing bid on product",
            extra={"user_id": str(user.id), "run_id": run_id, "product_id": product_id, "quantity": quantity}
        )

        # Validate and get entities
        run_uuid, product_uuid, run, product = self._validate_bid_request(run_id, product_id, user)

        # Get or create user participation
        participation, is_new_participant = self._ensure_user_participation(run_uuid, run, user)

        # Validate the bid based on current state
        existing_bid = self._validate_bid_for_state(run, product_uuid, quantity, participation)

        # Create or update the bid
        self.repo.create_or_update_bid(participation.id, product_uuid, quantity, interested_only)

        # Handle automatic state transition (planning → active)
        state_changed = self._check_planning_to_active_transition(run, is_new_participant, participation)

        # Calculate new totals for response
        new_total = self._calculate_product_total(run_uuid, product_uuid)

        return PlaceBidResponse(
            message="Bid placed successfully",
            product_id=str(product_uuid),
            user_id=str(user.id),
            user_name=user.name,
            quantity=quantity,
            interested_only=interested_only,
            new_total=new_total,
            state_changed=state_changed,
            new_state=RunState.ACTIVE if state_changed else run.state,
            run_id=str(run_uuid),
            group_id=str(run.group_id)
        )

    def _validate_bid_request(
        self, run_id: str, product_id: str, user: User
    ) -> tuple[UUID, UUID, Run, Product]:
        """Validate bid request and return validated entities."""
        # Validate IDs
        try:
            run_uuid = UUID(run_id)
            product_uuid = UUID(product_id)
        except ValueError:
            raise BadRequestError("Invalid ID format")

        # Verify run exists and user has access
        run = self._get_run_with_auth_check(run_uuid, user)

        # Check if run allows bidding
        if run.state not in [RunState.PLANNING, RunState.ACTIVE, RunState.ADJUSTING]:
            raise BadRequestError("Bidding not allowed in current run state")

        # Verify product exists in store
        store_products = self.repo.get_products_by_store(run.store_id)
        product = next((p for p in store_products if p.id == product_uuid), None)
        if not product:
            raise NotFoundError("Product", product_id)

        return run_uuid, product_uuid, run, product

    def _ensure_user_participation(
        self, run_uuid: UUID, run: Run, user: User
    ) -> tuple[RunParticipation, bool]:
        """Get or create user participation in run."""
        participation = self.repo.get_participation(user.id, run_uuid)
        is_new_participant = False

        if not participation:
            # Don't allow new participants in adjusting state
            if run.state == RunState.ADJUSTING:
                raise BadRequestError("Cannot join run in adjusting state")
            # Create participation (not as leader)
            participation = self.repo.create_participation(user.id, run_uuid, is_leader=False)
            is_new_participant = True

        return participation, is_new_participant

    def _validate_bid_for_state(
        self, run: Run, product_uuid: UUID, quantity: float, participation: RunParticipation
    ) -> ProductBid | None:
        """Validate bid based on run state and return existing bid if any."""
        # Basic quantity validation
        if quantity < 0:
            raise BadRequestError("Quantity cannot be negative")

        # Check for existing bid
        existing_bid = self.repo.get_bid(participation.id, product_uuid)

        # Check product limit for new products
        if not existing_bid:
            self._check_product_limit(run.id)

        # State-specific validation
        if run.state == RunState.ADJUSTING:
            if not existing_bid:
                raise BadRequestError("Cannot bid on new products in adjusting state")
            self._validate_adjusting_bid(run.id, product_uuid, quantity, existing_bid)

        return existing_bid

    def _check_product_limit(self, run_id: UUID) -> None:
        """Check if run has reached maximum product limit."""
        all_bids = self.repo.get_bids_by_run(run_id)
        unique_products = set(bid.product_id for bid in all_bids)
        if len(unique_products) >= MAX_PRODUCTS_PER_RUN:
            logger.warning(
                f"Run has reached maximum product limit",
                extra={"run_id": str(run_id), "unique_products": len(unique_products)}
            )
            raise BadRequestError(f"Run has reached maximum of {MAX_PRODUCTS_PER_RUN} products")

    def _validate_adjusting_bid(
        self, run_id: UUID, product_uuid: UUID, quantity: float, existing_bid: ProductBid
    ) -> None:
        """Validate bid adjustments during adjusting state."""
        # Get shopping list to check purchased quantity
        shopping_items = self.repo.get_shopping_list_items(run_id)
        shopping_item = next((item for item in shopping_items if item.product_id == product_uuid), None)

        if not shopping_item:
            raise BadRequestError("Product not in shopping list")

        # Calculate shortage
        purchased_qty = shopping_item.purchased_quantity or 0
        requested_qty = shopping_item.requested_quantity
        shortage = requested_qty - purchased_qty

        # Can only reduce, and at most to accommodate the shortage
        min_allowed = max(0, existing_bid.quantity - shortage)

        if quantity > existing_bid.quantity:
            raise BadRequestError(
                f"Can only reduce bids in adjusting state (current: {existing_bid.quantity}, new: {quantity})"
            )
        if quantity < min_allowed:
            raise BadRequestError(
                f"Cannot reduce bid below {min_allowed} "
                f"(current: {existing_bid.quantity}, shortage: {shortage}, would remove more than needed)"
            )

    def _check_planning_to_active_transition(
        self, run: Run, is_new_participant: bool, participation: RunParticipation
    ) -> bool:
        """Check if run should transition from planning to active."""
        # Automatic state transition: planning → active
        # When a non-leader places their first bid, transition from planning to active
        if is_new_participant and not participation.is_leader and run.state == RunState.PLANNING:
            self._transition_run_state(run, RunState.ACTIVE)
            return True
        return False

    def _calculate_product_total(self, run_id: UUID, product_id: UUID) -> float:
        """Calculate total quantity for a product (excluding interested-only bids)."""
        all_bids = self.repo.get_bids_by_run(run_id)
        product_bids = [bid for bid in all_bids if bid.product_id == product_id]
        return sum(bid.quantity for bid in product_bids if not bid.interested_only)

    def toggle_ready(self, run_id: str, user: User) -> ReadyToggleResponse:
        """
        Toggle the current user's ready status for a run.

        Can trigger auto-transition to confirmed state if all participants are ready.

        Args:
            run_id: Run ID as string
            user: Current user toggling ready status

        Returns:
            ReadyToggleResponse with ready status and whether state changed

        Raises:
            BadRequestError: If run ID invalid or state doesn't allow toggling ready
            NotFoundError: If run not found or user not participating
            ForbiddenError: If user not authorized
        """
        run_uuid, run = self._validate_toggle_ready_request(run_id, user)
        participation = self._get_user_participation(user.id, run_uuid, run_id)
        new_ready_status = self._toggle_user_ready_status(participation)

        if self._check_all_participants_ready(run_uuid):
            self._transition_run_state(run, RunState.CONFIRMED)
            return ReadyToggleResponse(
                message="All participants ready! Run confirmed.",
                is_ready=new_ready_status,
                state_changed=True,
                new_state=RunState.CONFIRMED,
                run_id=str(run_uuid),
                group_id=str(run.group_id),
                user_id=str(user.id)
            )

        return ReadyToggleResponse(
            message=f"Ready status updated to {new_ready_status}",
            is_ready=new_ready_status,
            state_changed=False,
            new_state=None,
            run_id=str(run_uuid),
            user_id=str(user.id),
            group_id=None
        )

    def _validate_toggle_ready_request(self, run_id: str, user: User) -> tuple[UUID, Run]:
        """Validate toggle ready request and return run UUID and run object."""
        try:
            run_uuid = UUID(run_id)
        except ValueError:
            raise BadRequestError("Invalid run ID format")

        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError("Run", run_id)

        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError("Not authorized to modify this run")

        if run.state != RunState.ACTIVE:
            raise BadRequestError("Can only mark ready in active state")

        return run_uuid, run

    def _get_user_participation(self, user_id: UUID, run_id: UUID, run_id_str: str) -> RunParticipation:
        """Get user's participation in a run."""
        participation = self.repo.get_participation(user_id, run_id)
        if not participation:
            raise NotFoundError("Participation", f"user_id: {user_id}, run_id: {run_id_str}")
        return participation

    def _toggle_user_ready_status(self, participation: RunParticipation) -> bool:
        """Toggle ready status and return new status."""
        new_ready_status = not participation.is_ready
        self.repo.update_participation_ready(participation.id, new_ready_status)
        return new_ready_status

    def _check_all_participants_ready(self, run_id: UUID) -> bool:
        """Check if all participants are ready."""
        all_participations = self.repo.get_run_participations(run_id)
        return len(all_participations) > 0 and all(p.is_ready for p in all_participations)

    def start_run(self, run_id: str, user: User) -> StateChangeResponse:
        """
        Start shopping - transition from confirmed to shopping state (leader only).

        Generates shopping list items from bids.

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            StateChangeResponse with success message and new state

        Raises:
            BadRequestError: If run ID invalid or state doesn't allow starting
            NotFoundError: If run not found
            ForbiddenError: If user is not the leader
        """
        # Validate run ID
        try:
            run_uuid = UUID(run_id)
        except ValueError:
            raise BadRequestError("Invalid run ID format")

        # Get the run
        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError("Run", run_id)

        # Verify user has access to this run (member of the group)
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError("Not authorized to modify this run")

        # Only allow starting shopping from confirmed state
        if run.state != RunState.CONFIRMED:
            raise BadRequestError("Can only start shopping from confirmed state")

        # Check if user is the run leader
        participation = self.repo.get_participation(user.id, run_uuid)
        if not participation or not participation.is_leader:
            raise ForbiddenError("Only the run leader can start shopping")

        # Generate shopping list items from bids
        # Get all bids for this run and aggregate by product
        bids = self.repo.get_bids_by_run(run_uuid)
        product_quantities = {}

        for bid in bids:
            if not bid.interested_only and bid.quantity > 0:
                product_id = bid.product_id
                if product_id not in product_quantities:
                    product_quantities[product_id] = 0
                product_quantities[product_id] += bid.quantity

        # Create shopping list items
        for product_id, quantity in product_quantities.items():
            self.repo.create_shopping_list_item(run_uuid, product_id, quantity)

        # Transition to shopping state
        old_state = run.state
        self.repo.update_run_state(run_uuid, RunState.SHOPPING)

        # Create notifications for all participants
        self._notify_run_state_change(run, old_state, RunState.SHOPPING)

        return StateChangeResponse(
            message="Shopping started!",
            state=RunState.SHOPPING,
            run_id=str(run_uuid),
            group_id=str(run.group_id)
        )

    def get_available_products(self, run_id: str, user: User) -> list[AvailableProductResponse]:
        """
        Get products available for bidding (all products without bids yet).
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
        try:
            run_uuid = UUID(run_id)
        except ValueError:
            raise BadRequestError("Invalid run ID format")

        # Verify run exists and user has access
        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError("Run", run_id)

        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError("Not authorized to view this run")

        # Get all products
        all_products = self.repo.get_all_products()
        run_bids = self.repo.get_bids_by_run(run.id)

        # Get products that have bids
        products_with_bids = set(bid.product_id for bid in run_bids)

        # Return products that don't have bids, sorted by availability at run's store
        available_products = []
        for product in all_products:
            if product.id not in products_with_bids:
                # Get product availability/price for this store
                availability = self.repo.get_availability_by_product_and_store(product.id, run.store_id)
                current_price = str(availability.price) if availability and availability.price else None
                has_store_availability = availability is not None

                available_products.append(AvailableProductResponse(
                    id=str(product.id),
                    name=product.name,
                    brand=product.brand,
                    current_price=current_price,
                    has_store_availability=has_store_availability
                ))

        # Sort: products with store availability first, then alphabetically by name
        available_products.sort(key=lambda p: (not p.has_store_availability, p.name.lower()))

        return available_products

    def transition_to_shopping(self, run_id: str, user: User) -> StateChangeResponse:
        """
        Transition from confirmed to shopping state.

        This is an alias for start_run() to match the expected method name.

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            StateChangeResponse with success message and new state

        Raises:
            BadRequestError: If run ID invalid or state doesn't allow transition
            NotFoundError: If run not found
            ForbiddenError: If user is not the leader
        """
        return self.start_run(run_id, user)

    def finish_adjusting(self, run_id: str, user: User) -> StateChangeResponse:
        """
        Finish adjusting bids - transition from adjusting to distributing state (leader only).

        Validates that quantities match purchased quantities and distributes items to bidders.

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            StateChangeResponse with success message and new state

        Raises:
            BadRequestError: If run ID invalid, state doesn't allow, or quantities don't match
            NotFoundError: If run not found
            ForbiddenError: If user is not the leader
        """
        run_uuid, run = self._validate_finish_adjusting_request(run_id, user)
        self._verify_quantities_match(run_uuid)
        self._distribute_items_to_bidders(run_uuid)
        self._transition_run_state(run, RunState.DISTRIBUTING)

        return StateChangeResponse(
            message="Adjustments complete! Moving to distribution.",
            state=RunState.DISTRIBUTING,
            run_id=str(run_uuid),
            group_id=str(run.group_id)
        )

    def _validate_finish_adjusting_request(self, run_id: str, user: User) -> tuple[UUID, Run]:
        """Validate finish adjusting request and return run UUID and run object."""
        try:
            run_uuid = UUID(run_id)
        except ValueError:
            raise BadRequestError("Invalid run ID format")

        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError("Run", run_id)

        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError("Not authorized to modify this run")

        if run.state != RunState.ADJUSTING:
            raise BadRequestError("Can only finish adjusting from adjusting state")

        participation = self.repo.get_participation(user.id, run_uuid)
        if not participation or not participation.is_leader:
            raise ForbiddenError("Only the run leader can finish adjusting")

        return run_uuid, run

    def _verify_quantities_match(self, run_id: UUID) -> None:
        """Verify that bid quantities match purchased quantities."""
        shopping_items = self.repo.get_shopping_list_items(run_id)
        all_bids = self.repo.get_bids_by_run(run_id)

        for shopping_item in shopping_items:
            if not shopping_item.is_purchased:
                continue

            product_bids = [bid for bid in all_bids if bid.product_id == shopping_item.product_id and not bid.interested_only]
            total_requested = sum(bid.quantity for bid in product_bids)

            if total_requested != shopping_item.purchased_quantity:
                shortage = total_requested - shopping_item.purchased_quantity
                raise BadRequestError(
                    f"Quantities still don't match. Need to reduce {shortage} more items across all bids."
                )

    def _distribute_items_to_bidders(self, run_id: UUID) -> None:
        """Distribute purchased items to bidders."""
        shopping_items = self.repo.get_shopping_list_items(run_id)
        all_bids = self.repo.get_bids_by_run(run_id)

        for shopping_item in shopping_items:
            if not shopping_item.is_purchased:
                continue

            product_bids = [bid for bid in all_bids if bid.product_id == shopping_item.product_id and not bid.interested_only]
            total_requested = sum(bid.quantity for bid in product_bids)
            self.repo.update_shopping_list_item_requested_quantity(shopping_item.id, total_requested)

            for bid in product_bids:
                self.repo.update_bid_distributed_quantities(
                    bid.id,
                    bid.quantity,
                    shopping_item.purchased_price_per_unit
                )

    def cancel_run(self, run_id: str, user: User) -> CancelRunResponse:
        """
        Cancel a run. Can be called by leader from any state except completed/cancelled.

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            CancelRunResponse with success message

        Raises:
            BadRequestError: If run ID format is invalid or run already in terminal state
            NotFoundError: If run not found
            ForbiddenError: If user is not the leader
        """
        # Validate run ID
        try:
            run_uuid = UUID(run_id)
        except ValueError:
            raise BadRequestError("Invalid run ID format")

        # Get the run
        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError("Run", run_id)

        # Check if run is already in a terminal state
        if run.state == RunState.COMPLETED:
            raise BadRequestError("Cannot cancel a completed run")
        if run.state == RunState.CANCELLED:
            raise BadRequestError("Run is already cancelled")

        # Verify user has access to this run (member of the group)
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError("Not authorized to cancel this run")

        # Check if user is the run leader
        participation = self.repo.get_participation(user.id, run_uuid)
        if not participation or not participation.is_leader:
            raise ForbiddenError("Only the run leader can cancel the run")

        # Transition to cancelled state
        old_state = run.state
        self.repo.update_run_state(run_uuid, RunState.CANCELLED)

        # Create notifications for all participants
        self._notify_run_state_change(run, old_state, RunState.CANCELLED)

        logger.info(
            f"Run cancelled by leader",
            extra={
                "run_id": str(run_uuid),
                "user_id": str(user.id),
                "previous_state": old_state
            }
        )

        return CancelRunResponse(
            message="Run cancelled successfully",
            run_id=str(run_uuid),
            group_id=str(run.group_id),
            state=RunState.CANCELLED.value
        )

    def delete_run(self, run_id: str, user: User) -> CancelRunResponse:
        """
        Delete a run (alias for cancel_run for backward compatibility).

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            CancelRunResponse with success message

        Raises:
            BadRequestError: If run ID format is invalid
            NotFoundError: If run not found
            ForbiddenError: If user is not the leader or not authorized
        """
        return self.cancel_run(run_id, user)

    def retract_bid(self, run_id: str, product_id: str, user: User) -> RetractBidResponse:
        """
        Retract a user's bid on a product in a run.

        Args:
            run_id: Run ID as string
            product_id: Product ID as string
            user: Current user retracting the bid

        Returns:
            RetractBidResponse with success message and updated totals

        Raises:
            BadRequestError: If ID format is invalid or bid modification not allowed in current state
            NotFoundError: If run, product, or bid not found
            ForbiddenError: If user is not authorized to modify bids on this run
        """
        logger.info(
            "Retracting bid",
            extra={"user_id": str(user.id), "run_id": run_id, "product_id": product_id}
        )

        run_uuid, product_uuid, run = self._validate_retract_request(run_id, product_id, user)
        self._check_adjusting_constraints_for_retraction(run, run_uuid, product_uuid, user.id)
        participation = self._get_user_participation(user.id, run_uuid, run_id)
        self._remove_bid_and_recalculate(participation, product_uuid, product_id)
        new_total = self._calculate_product_total(run_uuid, product_uuid)

        logger.info(
            "Bid retracted successfully",
            extra={
                "user_id": str(user.id),
                "run_id": str(run_uuid),
                "product_id": str(product_uuid),
                "new_total": new_total
            }
        )

        return RetractBidResponse(
            message="Bid retracted successfully",
            run_id=str(run_uuid),
            product_id=str(product_uuid),
            user_id=str(user.id),
            new_total=new_total
        )

    def _validate_retract_request(self, run_id: str, product_id: str, user: User) -> tuple[UUID, UUID, Run]:
        """Validate retract request and return UUIDs and run object."""
        try:
            run_uuid = UUID(run_id)
            product_uuid = UUID(product_id)
        except ValueError:
            raise BadRequestError("Invalid ID format")

        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError("Run", run_id)

        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError("Not authorized to modify bids on this run")

        if run.state not in [RunState.PLANNING, RunState.ACTIVE, RunState.ADJUSTING]:
            raise BadRequestError("Bid modification not allowed in current run state")

        return run_uuid, product_uuid, run

    def _check_adjusting_constraints_for_retraction(
        self, run: Run, run_id: UUID, product_id: UUID, user_id: UUID
    ) -> None:
        """Check if retraction is allowed in adjusting state."""
        if run.state != RunState.ADJUSTING:
            return

        shopping_items = self.repo.get_shopping_list_items(run_id)
        shopping_item = next((item for item in shopping_items if item.product_id == product_id), None)

        if not shopping_item:
            return

        purchased_qty = shopping_item.purchased_quantity or 0
        requested_qty = shopping_item.requested_quantity
        shortage = requested_qty - purchased_qty

        participation = self.repo.get_participation(user_id, run_id)
        if not participation:
            return

        current_bid = self.repo.get_bid(participation.id, product_id)
        if current_bid and current_bid.quantity > shortage:
            raise BadRequestError(
                f"Cannot fully retract bid. You can reduce it by at most {shortage} items."
            )

    def _remove_bid_and_recalculate(
        self, participation: RunParticipation, product_id: UUID, product_id_str: str
    ) -> None:
        """Remove bid from database."""
        bid = self.repo.get_bid(participation.id, product_id)
        if not bid:
            raise NotFoundError("Bid", f"product_id: {product_id_str}")

        self.repo.delete_bid(participation.id, product_id)

    def _transition_run_state(
        self,
        run: Run,
        new_state: RunState,
        notify: bool = True
    ) -> str:
        """
        Safely transition run to new state with validation and notifications.

        Uses the state machine to validate transitions before applying them.
        Optionally creates notifications for all participants.

        Args:
            run: The run to transition
            new_state: Target state
            notify: Whether to create notifications (default True)

        Returns:
            old_state string for caller use

        Raises:
            ValueError: If transition is invalid according to state machine
        """
        # Validate transition using state machine
        state_machine.validate_transition(
            RunState(run.state),
            new_state,
            str(run.id)
        )

        old_state = run.state
        self.repo.update_run_state(run.id, new_state)

        if notify:
            self._notify_run_state_change(run, old_state, new_state)

        logger.info(
            f"Run state transitioned",
            extra={
                "run_id": str(run.id),
                "old_state": old_state,
                "new_state": new_state
            }
        )

        return old_state

    def _notify_run_state_change(self, run: Run, old_state: str, new_state: str) -> None:
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
                logger.warning(
                    "Failed to broadcast notification via WebSocket",
                    extra={
                        "error": str(e),
                        "user_id": str(participant.user_id),
                        "notification_id": str(notification.id)
                    }
                )

        logger.debug(
            f"Created notifications for run state change",
            extra={
                "run_id": str(run.id),
                "old_state": old_state,
                "new_state": new_state,
                "participant_count": len(participations)
            }
        )
