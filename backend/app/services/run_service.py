"""Run service for managing run business logic."""

import logging
import uuid
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID

from ..exceptions import NotFoundError, ForbiddenError, ValidationError, ConflictError, BadRequestError
from ..models import Run, Store, Group, User, Product, ProductBid, RunParticipation, ShoppingListItem
from ..run_state import RunState, state_machine
from .base_service import BaseService

logger = logging.getLogger(__name__)


class RunService(BaseService):
    """Service for managing run operations."""

    def create_run(self, group_id: str, store_id: str, user: User) -> Dict[str, Any]:
        """
        Create a new run for a group.

        Args:
            group_id: Group ID as string
            store_id: Store ID as string
            user: Current user creating the run

        Returns:
            Dict with run data (id, group_id, store_id, state)

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
            group_uuid = uuid.UUID(group_id)
            store_uuid = uuid.UUID(store_id)
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

        # Check active runs limit for the group (100 max)
        group_runs = self.repo.get_runs_by_group(group_uuid)
        active_runs = [r for r in group_runs if r.state not in ('completed', 'cancelled')]
        if len(active_runs) >= 100:
            logger.warning(
                f"Group has reached maximum active runs limit",
                extra={"user_id": str(user.id), "group_id": str(group_uuid), "active_runs": len(active_runs)}
            )
            raise BadRequestError("Group has reached maximum of 100 active runs")

        # Create the run with current user as leader
        run = self.repo.create_run(group_uuid, store_uuid, user.id)

        logger.info(
            f"Run created successfully",
            extra={"user_id": str(user.id), "run_id": str(run.id), "group_id": str(group_uuid)}
        )

        return {
            "id": str(run.id),
            "group_id": str(run.group_id),
            "store_id": str(run.store_id),
            "state": run.state,
            "store_name": store.name,
            "leader_name": user.name
        }

    def get_run_details(self, run_id: str, user: User) -> Dict[str, Any]:
        """
        Get detailed information about a specific run.

        Args:
            run_id: Run ID as string
            user: Current user requesting details

        Returns:
            Dict with run details including products, participants, etc.

        Raises:
            BadRequestError: If run ID format is invalid
            NotFoundError: If run not found
            ForbiddenError: If user is not authorized to view the run
        """
        # Validate run ID format
        try:
            run_uuid = uuid.UUID(run_id)
        except ValueError:
            raise BadRequestError("Invalid run ID format")

        # Find the run
        runs = [run for run in self.repo._runs.values() if run.id == run_uuid] if hasattr(self.repo, '_runs') else []
        if not runs:
            raise NotFoundError("Run", run_id)

        run = runs[0]

        # Verify user has access to this run (member of the group)
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError("Not authorized to view this run")

        # Get group and store information
        group = self.repo.get_group_by_id(run.group_id)
        all_stores = self.repo.get_all_stores()
        store = next((s for s in all_stores if s.id == run.store_id), None)

        if not group or not store:
            raise NotFoundError("Group or Store", str(run.group_id) + " or " + str(run.store_id))

        # Get participants with users eagerly loaded to avoid N+1 queries
        participants_data = []
        current_user_is_ready = False
        current_user_is_leader = False
        leader_name = "Unknown"
        participations = self.repo.get_run_participations_with_users(run.id)

        for participation in participations:
            # Check if this is the current user's participation
            if participation.user_id == user.id:
                current_user_is_ready = participation.is_ready
                current_user_is_leader = participation.is_leader

            # Find the leader
            if participation.is_leader and participation.user:
                leader_name = participation.user.name

            # Add to participants list if user data is available
            if participation.user:
                participants_data.append({
                    "user_id": str(participation.user_id),
                    "user_name": participation.user.name,
                    "is_leader": participation.is_leader,
                    "is_ready": participation.is_ready,
                    "is_removed": participation.is_removed
                })

        # Get products and bids for this run
        if hasattr(self.repo, '_runs'):  # Memory mode
            # Get all products for the store
            store_products = self.repo.get_products_by_store(run.store_id)
            # Get bids with participations and users eagerly loaded to avoid N+1 queries
            run_bids = self.repo.get_bids_by_run_with_participations(run.id)

            # Get shopping list items if in adjusting state
            shopping_list_map = {}
            if run.state == 'adjusting':
                shopping_items = self.repo.get_shopping_list_items(run.id)
                for item in shopping_items:
                    shopping_list_map[item.product_id] = item

            # Calculate product statistics
            products_data = []
            for product in store_products:
                product_bids = [bid for bid in run_bids if bid.product_id == product.id]

                if len(product_bids) > 0:  # Only include products with bids
                    total_quantity = sum(bid.quantity for bid in product_bids)
                    interested_count = len([bid for bid in product_bids if bid.interested_only or bid.quantity > 0])

                    # Get user details for each bid
                    user_bids_data = []
                    current_user_bid = None

                    for bid in product_bids:
                        # Participation and user are eagerly loaded on the bid object
                        if bid.participation and bid.participation.user:
                            bid_response = {
                                "user_id": str(bid.participation.user_id),
                                "user_name": bid.participation.user.name,
                                "quantity": bid.quantity,
                                "interested_only": bid.interested_only
                            }
                            user_bids_data.append(bid_response)

                            # Check if this is the current user's bid
                            if bid.participation.user_id == user.id:
                                current_user_bid = bid_response

                    # Get purchased quantity if in adjusting state
                    purchased_qty = None
                    if run.state == 'adjusting' and product.id in shopping_list_map:
                        purchased_qty = shopping_list_map[product.id].purchased_quantity

                    # Get product availability/price for this store
                    availability = self.repo.get_availability_by_product_and_store(product.id, run.store_id)
                    current_price = str(availability.price) if availability and availability.price else None

                    products_data.append({
                        "id": str(product.id),
                        "name": product.name,
                        "brand": product.brand,
                        "current_price": current_price,
                        "total_quantity": total_quantity,
                        "interested_count": interested_count,
                        "user_bids": user_bids_data,
                        "current_user_bid": current_user_bid,
                        "purchased_quantity": purchased_qty
                    })
        else:
            # Database mode - would need proper joins
            products_data = []

        return {
            "id": str(run.id),
            "group_id": str(run.group_id),
            "group_name": group.name,
            "store_id": str(run.store_id),
            "store_name": store.name,
            "state": run.state,
            "products": products_data,
            "participants": participants_data,
            "current_user_is_ready": current_user_is_ready,
            "current_user_is_leader": current_user_is_leader,
            "leader_name": leader_name
        }

    def place_bid(
        self,
        run_id: str,
        product_id: str,
        quantity: float,
        interested_only: bool,
        user: User
    ) -> Dict[str, Any]:
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
            Dict with status and calculated totals for broadcasting

        Raises:
            BadRequestError: If IDs are invalid or state doesn't allow bidding
            NotFoundError: If run or product not found
            ForbiddenError: If user not authorized
        """
        logger.info(
            f"Placing bid on product",
            extra={"user_id": str(user.id), "run_id": run_id, "product_id": product_id, "quantity": quantity}
        )

        # Validate IDs
        try:
            run_uuid = uuid.UUID(run_id)
            product_uuid = uuid.UUID(product_id)
        except ValueError:
            raise BadRequestError("Invalid ID format")

        # Verify run exists and user has access
        runs = [run for run in self.repo._runs.values() if run.id == run_uuid] if hasattr(self.repo, '_runs') else []
        if not runs:
            raise NotFoundError("Run", run_id)

        run = runs[0]
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError("Not authorized to bid on this run")

        # Check if run allows bidding
        if run.state not in ['planning', 'active', 'adjusting']:
            raise BadRequestError("Bidding not allowed in current run state")

        # Verify product exists
        store_products = self.repo.get_products_by_store(run.store_id)
        product = next((p for p in store_products if p.id == product_uuid), None)
        if not product:
            raise NotFoundError("Product", product_id)

        # Check if this is a new product and enforce product limit (100 max)
        participation = self.repo.get_participation(user.id, run_uuid)
        existing_bid = None
        if participation and hasattr(self.repo, '_bids'):
            for bid in self.repo._bids.values():
                if (bid.participation_id == participation.id and
                    bid.product_id == product_uuid):
                    existing_bid = bid
                    break

        if not existing_bid:  # New product being added to run
            # Count unique products in this run
            all_bids = self.repo.get_bids_by_run(run_uuid)
            unique_products = set(bid.product_id for bid in all_bids)
            if len(unique_products) >= 100:
                logger.warning(
                    f"Run has reached maximum product limit",
                    extra={"user_id": str(user.id), "run_id": str(run_uuid), "unique_products": len(unique_products)}
                )
                raise BadRequestError("Run has reached maximum of 100 products")

        # Validate quantity
        if quantity < 0:
            raise BadRequestError("Quantity cannot be negative")

        # In adjusting state, only allow downward adjustments
        if run.state == 'adjusting':
            # Get shopping list to check purchased quantity
            shopping_items = self.repo.get_shopping_list_items(run_uuid)
            shopping_item = next((item for item in shopping_items if item.product_id == product_uuid), None)

            if not shopping_item:
                raise BadRequestError("Product not in shopping list")

            # Calculate how much we need to reduce
            purchased_qty = shopping_item.purchased_quantity or 0
            requested_qty = shopping_item.requested_quantity
            shortage = requested_qty - purchased_qty

            # Get current bid (only in memory mode for now)
            participation = self.repo.get_participation(user.id, run_uuid)
            existing_bid = None
            if participation and hasattr(self.repo, '_bids'):
                for bid in self.repo._bids.values():
                    if (bid.participation_id == participation.id and
                        bid.product_id == product_uuid):
                        existing_bid = bid
                        break

                if existing_bid:
                    # Can only reduce, and at most to accommodate the shortage
                    min_allowed = max(0, existing_bid.quantity - shortage)
                    if quantity > existing_bid.quantity:
                        raise BadRequestError(f"Can only reduce bids in adjusting state (current: {existing_bid.quantity}, new: {quantity})")
                    if quantity < min_allowed:
                        raise BadRequestError(f"Cannot reduce bid below {min_allowed} (current: {existing_bid.quantity}, shortage: {shortage}, would remove more than needed)")

        if hasattr(self.repo, '_bids'):  # Memory mode
            # Get or create participation for this user in this run
            participation = self.repo.get_participation(user.id, run_uuid)
            is_new_participant = False
            if not participation:
                # Don't allow new participants in adjusting state
                if run.state == 'adjusting':
                    raise BadRequestError("Cannot join run in adjusting state")
                # Create participation (not as leader)
                participation = self.repo.create_participation(user.id, run_uuid, is_leader=False)
                is_new_participant = True

            # Check if user already has a bid for this product
            existing_bid = None
            for bid in self.repo._bids.values():
                if (bid.participation_id == participation.id and
                    bid.product_id == product_uuid):
                    existing_bid = bid
                    break

            if existing_bid:
                # Update existing bid
                existing_bid.quantity = quantity
                existing_bid.interested_only = interested_only
            else:
                # Don't allow new bids on products in adjusting state
                if run.state == 'adjusting':
                    raise BadRequestError("Cannot bid on new products in adjusting state")
                # Create new bid
                from uuid import uuid4
                new_bid = ProductBid(
                    id=uuid4(),
                    participation_id=participation.id,
                    product_id=product_uuid,
                    quantity=quantity,
                    interested_only=interested_only
                )
                # Set up relationships
                new_bid.participation = participation
                new_bid.product = product
                self.repo._bids[new_bid.id] = new_bid

            # Automatic state transition: planning → active
            # When a non-leader places their first bid, transition from planning to active
            state_changed = False
            if is_new_participant and not participation.is_leader and run.state == RunState.PLANNING:
                old_state = run.state
                self.repo.update_run_state(run_uuid, RunState.ACTIVE)
                state_changed = True

                # Create notifications for all participants
                self._notify_run_state_change(run, old_state, RunState.ACTIVE)

            # Calculate new totals for broadcasting
            all_bids = self.repo.get_bids_by_run(run_uuid)
            product_bids = [bid for bid in all_bids if bid.product_id == product_uuid]
            new_total = sum(bid.quantity for bid in product_bids if not bid.interested_only)

            return {
                "message": "Bid placed successfully",
                "product_id": str(product_uuid),
                "user_id": str(user.id),
                "user_name": user.name,
                "quantity": quantity,
                "interested_only": interested_only,
                "new_total": new_total,
                "state_changed": state_changed,
                "new_state": RunState.ACTIVE if state_changed else run.state,
                "run_id": str(run_uuid),
                "group_id": str(run.group_id)
            }

        return {"message": "Bid placed successfully"}

    def toggle_ready(self, run_id: str, user: User) -> Dict[str, Any]:
        """
        Toggle the current user's ready status for a run.

        Can trigger auto-transition to confirmed state if all participants are ready.

        Args:
            run_id: Run ID as string
            user: Current user toggling ready status

        Returns:
            Dict with ready status and whether state changed

        Raises:
            BadRequestError: If run ID invalid or state doesn't allow toggling ready
            NotFoundError: If run not found or user not participating
            ForbiddenError: If user not authorized
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

        # Verify user has access to this run (member of the group)
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError("Not authorized to modify this run")

        # Only allow toggling ready in active state
        if run.state != 'active':
            raise BadRequestError("Can only mark ready in active state")

        # Get user's participation
        participation = self.repo.get_participation(user.id, run_uuid)
        if not participation:
            raise NotFoundError("Participation", f"user_id: {user.id}, run_id: {run_id}")

        # Toggle ready status
        new_ready_status = not participation.is_ready
        self.repo.update_participation_ready(participation.id, new_ready_status)

        # Check if all participants are ready
        all_participations = self.repo.get_run_participations(run_uuid)
        all_ready = all(p.is_ready for p in all_participations)

        # Automatic state transition: active → confirmed
        # When all participants mark themselves as ready
        state_changed = False
        if all_ready and len(all_participations) > 0:
            old_state = run.state
            self.repo.update_run_state(run_uuid, RunState.CONFIRMED)
            state_changed = True

            # Create notifications for all participants
            self._notify_run_state_change(run, old_state, RunState.CONFIRMED)

            return {
                "message": "All participants ready! Run confirmed.",
                "is_ready": new_ready_status,
                "state_changed": True,
                "new_state": RunState.CONFIRMED,
                "run_id": str(run_uuid),
                "group_id": str(run.group_id),
                "user_id": str(user.id)
            }

        return {
            "message": f"Ready status updated to {new_ready_status}",
            "is_ready": new_ready_status,
            "state_changed": False,
            "run_id": str(run_uuid),
            "user_id": str(user.id)
        }

    def start_run(self, run_id: str, user: User) -> Dict[str, Any]:
        """
        Start shopping - transition from confirmed to shopping state (leader only).

        Generates shopping list items from bids.

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            Dict with success message and new state

        Raises:
            BadRequestError: If run ID invalid or state doesn't allow starting
            NotFoundError: If run not found
            ForbiddenError: If user is not the leader
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

        # Verify user has access to this run (member of the group)
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError("Not authorized to modify this run")

        # Only allow starting shopping from confirmed state
        if run.state != 'confirmed':
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

        return {
            "message": "Shopping started!",
            "state": RunState.SHOPPING,
            "run_id": str(run_uuid),
            "group_id": str(run.group_id)
        }

    def get_available_products(self, run_id: str, user: User) -> List[Dict[str, Any]]:
        """
        Get products available for bidding (products from the store that don't have bids yet).

        Args:
            run_id: Run ID as string
            user: Current user

        Returns:
            List of available product dicts

        Raises:
            BadRequestError: If run ID format is invalid
            NotFoundError: If run not found
            ForbiddenError: If user not authorized
        """
        # Validate run ID
        try:
            run_uuid = uuid.UUID(run_id)
        except ValueError:
            raise BadRequestError("Invalid run ID format")

        # Verify run exists and user has access
        runs = [run for run in self.repo._runs.values() if run.id == run_uuid] if hasattr(self.repo, '_runs') else []
        if not runs:
            raise NotFoundError("Run", run_id)

        run = runs[0]
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError("Not authorized to view this run")

        if hasattr(self.repo, '_runs'):  # Memory mode
            # Get all products for the store
            store_products = self.repo.get_products_by_store(run.store_id)
            run_bids = self.repo.get_bids_by_run(run.id)

            # Get products that have bids
            products_with_bids = set(bid.product_id for bid in run_bids)

            # Return products that don't have bids
            available_products = []
            for product in store_products:
                if product.id not in products_with_bids:
                    # Get product availability/price for this store
                    availability = self.repo.get_availability_by_product_and_store(product.id, run.store_id)
                    current_price = str(availability.price) if availability and availability.price else None

                    available_products.append({
                        "id": str(product.id),
                        "name": product.name,
                        "brand": product.brand,
                        "current_price": current_price
                    })

            return available_products
        else:
            # Database mode - would need proper joins
            return []

    def transition_to_shopping(self, run_id: str, user: User) -> Dict[str, Any]:
        """
        Transition from confirmed to shopping state.

        This is an alias for start_run() to match the expected method name.

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            Dict with success message and new state

        Raises:
            BadRequestError: If run ID invalid or state doesn't allow transition
            NotFoundError: If run not found
            ForbiddenError: If user is not the leader
        """
        return self.start_run(run_id, user)

    def finish_adjusting(self, run_id: str, user: User) -> Dict[str, Any]:
        """
        Finish adjusting bids - transition from adjusting to distributing state (leader only).

        Validates that quantities match purchased quantities and distributes items to bidders.

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            Dict with success message and new state

        Raises:
            BadRequestError: If run ID invalid, state doesn't allow, or quantities don't match
            NotFoundError: If run not found
            ForbiddenError: If user is not the leader
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

        # Verify user has access to this run (member of the group)
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError("Not authorized to modify this run")

        # Only allow finishing adjusting from adjusting state
        if run.state != 'adjusting':
            raise BadRequestError("Can only finish adjusting from adjusting state")

        # Check if user is the run leader
        participation = self.repo.get_participation(user.id, run_uuid)
        if not participation or not participation.is_leader:
            raise ForbiddenError("Only the run leader can finish adjusting")

        # Verify that quantities now match
        shopping_items = self.repo.get_shopping_list_items(run_uuid)
        all_bids = self.repo.get_bids_by_run(run_uuid)

        for shopping_item in shopping_items:
            if not shopping_item.is_purchased:
                continue

            # Calculate new total from bids
            product_bids = [bid for bid in all_bids if bid.product_id == shopping_item.product_id and not bid.interested_only]
            total_requested = sum(bid.quantity for bid in product_bids)

            # Check if it matches purchased quantity
            if total_requested != shopping_item.purchased_quantity:
                shortage = total_requested - shopping_item.purchased_quantity
                raise BadRequestError(
                    f"Quantities still don't match. Need to reduce {shortage} more items across all bids."
                )

        # All quantities match, proceed with distribution
        for shopping_item in shopping_items:
            if not shopping_item.is_purchased:
                continue

            # Get all bids for this product
            product_bids = [bid for bid in all_bids if bid.product_id == shopping_item.product_id and not bid.interested_only]

            # Update shopping list item's requested_quantity to match adjusted bids
            total_requested = sum(bid.quantity for bid in product_bids)
            if hasattr(self.repo, '_shopping_list_items'):  # Memory mode
                shopping_item.requested_quantity = total_requested

            # Distribute the purchased items to bidders
            for bid in product_bids:
                if hasattr(self.repo, '_bids'):  # Memory mode
                    bid.distributed_quantity = bid.quantity
                    bid.distributed_price_per_unit = shopping_item.purchased_price_per_unit

        # Transition to distributing state
        old_state = run.state
        self.repo.update_run_state(run_uuid, RunState.DISTRIBUTING)

        # Create notifications for all participants
        self._notify_run_state_change(run, old_state, RunState.DISTRIBUTING)

        return {
            "message": "Adjustments complete! Moving to distribution.",
            "state": RunState.DISTRIBUTING,
            "run_id": str(run_uuid),
            "group_id": str(run.group_id)
        }

    def cancel_run(self, run_id: str, user: User) -> Dict[str, Any]:
        """
        Cancel a run. Can be called by leader from any state except completed/cancelled.

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            Dict with success message

        Raises:
            BadRequestError: If run ID format is invalid or run already in terminal state
            NotFoundError: If run not found
            ForbiddenError: If user is not the leader
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

        # Check if run is already in a terminal state
        if run.state == RunState.COMPLETED.value:
            raise BadRequestError("Cannot cancel a completed run")
        if run.state == RunState.CANCELLED.value:
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

        return {
            "message": "Run cancelled successfully",
            "run_id": str(run_uuid),
            "group_id": str(run.group_id),
            "state": RunState.CANCELLED.value
        }

    def delete_run(self, run_id: str, user: User) -> Dict[str, Any]:
        """
        Delete a run (alias for cancel_run for backward compatibility).

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            Dict with success message

        Raises:
            BadRequestError: If run ID format is invalid
            NotFoundError: If run not found
            ForbiddenError: If user is not the leader or not authorized
        """
        return self.cancel_run(run_id, user)

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
