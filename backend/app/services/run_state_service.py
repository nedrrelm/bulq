"""Run state service for managing run state transitions."""

from typing import TYPE_CHECKING
from uuid import UUID

from app.events.domain_events import ReadyToggledEvent, RunCancelledEvent, RunStateChangedEvent
from app.events.event_bus import event_bus
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import Run, User
from app.infrastructure.request_context import get_logger
from app.core.run_state import RunState, state_machine
from app.api.schemas import CancelRunResponse, ReadyToggleResponse, StateChangeResponse
from app.infrastructure.transaction import transaction
from app.utils.validation import validate_uuid
from .base_service import BaseService

if TYPE_CHECKING:
    from .run_notification_service import RunNotificationService

logger = get_logger(__name__)


class RunStateService(BaseService):
    """Service for managing run state transitions."""

    def __init__(self, db, notification_service: 'RunNotificationService | None' = None):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session
            notification_service: Optional notification service for broadcasting state changes
        """
        super().__init__(db)
        self._notification_service = notification_service

    def set_notification_service(self, notification_service: 'RunNotificationService') -> None:
        """Set the notification service (for dependency injection after creation).

        Args:
            notification_service: Notification service instance
        """
        self._notification_service = notification_service

    def toggle_ready(self, run_id: str, user: User) -> ReadyToggleResponse:
        """Toggle the current user's ready status for a run.

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

        # Emit ready toggled event
        event_bus.emit(
            ReadyToggledEvent(
                run_id=run_uuid,
                user_id=user.id,
                is_ready=new_ready_status,
                group_id=run.group_id,
            )
        )

        if self._check_all_participants_ready(run_uuid):
            self._transition_run_state(run, RunState.CONFIRMED)
            return ReadyToggleResponse(
                message='All participants ready! Run confirmed.',
                is_ready=new_ready_status,
                state_changed=True,
                new_state=RunState.CONFIRMED,
                run_id=str(run_uuid),
                group_id=str(run.group_id),
                user_id=str(user.id),
            )

        return ReadyToggleResponse(
            message=f'Ready status updated to {new_ready_status}',
            is_ready=new_ready_status,
            state_changed=False,
            new_state=None,
            run_id=str(run_uuid),
            user_id=str(user.id),
            group_id=None,
        )

    def force_confirm(self, run_id: str, user: User) -> StateChangeResponse:
        """Force confirm run - transition from active to confirmed without waiting for all users (leader only).

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)

        Returns:
            StateChangeResponse with success message and new state

        Raises:
            BadRequestError: If run ID invalid or not in active state
            NotFoundError: If run not found
            ForbiddenError: If user is not the leader
        """
        from app.core.exceptions import BadRequestError, ForbiddenError

        # Validate run ID
        run_uuid = validate_uuid(run_id, 'Run')

        # Get the run
        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError('Run', run_id)

        # Verify user has access to this run (member of the group)
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError('Not authorized to modify this run')

        # Check if user is the run leader
        participation = self.repo.get_participation(user.id, run_uuid)
        if not participation or not participation.is_leader:
            raise ForbiddenError('Only the run leader can force confirm the run')

        # Check if run is in active state
        if run.state != RunState.ACTIVE:
            raise BadRequestError(f'Run must be in active state to force confirm, currently in {run.state}')

        # Transition to confirmed state
        self._transition_run_state(run, RunState.CONFIRMED)

        return StateChangeResponse(
            message='Run force confirmed successfully',
            state=RunState.CONFIRMED,
            run_id=str(run_uuid),
            group_id=str(run.group_id),
        )

    def start_shopping(self, run_id: str, user: User) -> StateChangeResponse:
        """Start shopping - transition from confirmed to shopping state (leader only).

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
        run_uuid = validate_uuid(run_id, 'Run')

        # Get the run
        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError('Run', run_id)

        # Verify user has access to this run (member of the group)
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError('Not authorized to modify this run')

        # Only allow starting shopping from confirmed state - use state machine
        run_state = RunState(run.state)
        if not state_machine.can_start_shopping(run_state):
            raise BadRequestError('Can only start shopping from confirmed state')

        # Check if user is the run leader
        participation = self.repo.get_participation(user.id, run_uuid)
        if not participation or not participation.is_leader:
            raise ForbiddenError('Only the run leader can start shopping')

        # Wrap shopping list generation and state change in transaction
        with transaction(self.db, "generate shopping list and start shopping"):
            # Generate shopping list items from bids
            self._generate_shopping_list(run_uuid)

            # Transition to shopping state
            self._transition_run_state(run, RunState.SHOPPING)

        return StateChangeResponse(
            message='Shopping started!',
            state=RunState.SHOPPING,
            run_id=str(run_uuid),
            group_id=str(run.group_id),
        )

    def finish_adjusting(self, run_id: str, user: User, force: bool = False) -> StateChangeResponse:
        """Finish adjusting bids - transition from adjusting to distributing state (leader only).

        Validates that quantities match purchased quantities and distributes items to bidders.
        All operations are wrapped in a transaction for atomicity.

        Args:
            run_id: Run ID as string
            user: Current user (must be leader)
            force: If True, skip quantity verification and distribute as-is

        Returns:
            StateChangeResponse with success message and new state

        Raises:
            BadRequestError: If run ID invalid, state doesn't allow, or quantities don't match (when not forced)
            NotFoundError: If run not found
            ForbiddenError: If user is not the leader
        """
        run_uuid, run = self._validate_finish_adjusting_request(run_id, user)

        # Wrap verification, distribution, and state change in transaction
        with transaction(self.db, "finish adjusting and distribute items"):
            if not force:
                self._verify_quantities_match(run_uuid)
            self._distribute_items_to_bidders(run_uuid)
            self._transition_run_state(run, RunState.DISTRIBUTING)

        message = 'Distribution started!' if force else 'Adjustments complete! Moving to distribution.'
        return StateChangeResponse(
            message=message,
            state=RunState.DISTRIBUTING,
            run_id=str(run_uuid),
            group_id=str(run.group_id),
        )

    def cancel_run(self, run_id: str, user: User) -> CancelRunResponse:
        """Cancel a run. Can be called by leader from any state except completed/cancelled.

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
        run_uuid = validate_uuid(run_id, 'Run')

        # Get the run
        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError('Run', run_id)

        # Check if run is already in a terminal state using state machine
        run_state = RunState(run.state)
        if state_machine.is_terminal_state(run_state):
            if run_state == RunState.COMPLETED:
                raise BadRequestError('Cannot cancel a completed run')
            raise BadRequestError('Run is already cancelled')

        # Verify user has access to this run (member of the group)
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError('Not authorized to cancel this run')

        # Check if user is the run leader
        participation = self.repo.get_participation(user.id, run_uuid)
        if not participation or not participation.is_leader:
            raise ForbiddenError('Only the run leader can cancel the run')

        # Transition to cancelled state
        old_state = run.state
        self._transition_run_state(run, RunState.CANCELLED)

        # Get store name for event
        all_stores = self.repo.get_all_stores()
        store = next((s for s in all_stores if s.id == run.store_id), None)
        store_name = store.name if store else 'Unknown Store'

        # Emit run cancelled event
        event_bus.emit(
            RunCancelledEvent(run_id=run.id, group_id=run.group_id, store_name=store_name)
        )

        logger.info(
            'Run cancelled by leader',
            extra={'run_id': str(run_uuid), 'user_id': str(user.id), 'previous_state': old_state},
        )

        return CancelRunResponse(
            message='Run cancelled successfully',
            run_id=str(run_uuid),
            group_id=str(run.group_id),
            state=RunState.CANCELLED.value,
        )

    def _transition_run_state(self, run: Run, new_state: RunState, notify: bool = True) -> str:
        """Safely transition run to new state with validation and notifications.

        Uses the state machine to validate transitions before applying them.
        Optionally emits events for all participants.

        Args:
            run: The run to transition
            new_state: Target state
            notify: Whether to emit state change events (default True)

        Returns:
            old_state string for caller use

        Raises:
            ValueError: If transition is invalid according to state machine
        """
        # Validate transition using state machine
        state_machine.validate_transition(RunState(run.state), new_state, str(run.id))

        old_state = run.state
        self.repo.update_run_state(run.id, new_state)

        if notify:
            # Get store name for event
            all_stores = self.repo.get_all_stores()
            store = next((s for s in all_stores if s.id == run.store_id), None)
            store_name = store.name if store else 'Unknown Store'

            # Emit domain event for state change
            event_bus.emit(
                RunStateChangedEvent(
                    run_id=run.id,
                    group_id=run.group_id,
                    old_state=old_state,
                    new_state=new_state,
                    store_name=store_name,
                )
            )

        logger.info(
            'Run state transitioned',
            extra={'run_id': str(run.id), 'old_state': old_state, 'new_state': new_state},
        )

        return old_state

    def _validate_toggle_ready_request(self, run_id: str, user: User) -> tuple[UUID, Run]:
        """Validate toggle ready request and return run UUID and run object."""
        run_uuid = validate_uuid(run_id, 'Run')

        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError('Run', run_id)

        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError('Not authorized to modify this run')

        # Check if toggling ready is allowed using state machine
        run_state = RunState(run.state)
        if not state_machine.can_toggle_ready(run_state):
            raise BadRequestError('Can only mark ready in active state')

        return run_uuid, run

    def _get_user_participation(self, user_id: UUID, run_id: UUID, run_id_str: str):
        """Get user's participation in a run."""
        participation = self.repo.get_participation(user_id, run_id)
        if not participation:
            raise NotFoundError('Participation', f'user_id: {user_id}, run_id: {run_id_str}')
        return participation

    def _toggle_user_ready_status(self, participation) -> bool:
        """Toggle ready status and return new status."""
        new_ready_status = not participation.is_ready
        self.repo.update_participation_ready(participation.id, new_ready_status)
        return new_ready_status

    def _check_all_participants_ready(self, run_id: UUID) -> bool:
        """Check if all participants are ready."""
        all_participations = self.repo.get_run_participations(run_id)
        return len(all_participations) > 0 and all(p.is_ready for p in all_participations)

    def _generate_shopping_list(self, run_uuid: UUID) -> None:
        """Generate shopping list items from bids.

        Args:
            run_uuid: Run UUID
        """
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

    def _validate_finish_adjusting_request(self, run_id: str, user: User) -> tuple[UUID, Run]:
        """Validate finish adjusting request and return run UUID and run object."""
        run_uuid = validate_uuid(run_id, 'Run')

        run = self.repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError('Run', run_id)

        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError('Not authorized to modify this run')

        # Check if finishing adjusting is allowed using state machine
        run_state = RunState(run.state)
        if not state_machine.can_finish_adjusting(run_state):
            raise BadRequestError('Can only finish adjusting from adjusting state')

        participation = self.repo.get_participation(user.id, run_uuid)
        if not participation or not participation.is_leader:
            raise ForbiddenError('Only the run leader can finish adjusting')

        return run_uuid, run

    def _verify_quantities_match(self, run_id: UUID) -> None:
        """Verify that bid quantities match purchased quantities."""
        shopping_items = self.repo.get_shopping_list_items(run_id)
        all_bids = self.repo.get_bids_by_run(run_id)

        for shopping_item in shopping_items:
            if not shopping_item.is_purchased:
                continue

            product_bids = [
                bid
                for bid in all_bids
                if bid.product_id == shopping_item.product_id and not bid.interested_only
            ]
            total_requested = sum(bid.quantity for bid in product_bids)

            # Skip items that were not purchased (purchased_quantity is None or 0)
            # Bids for unpurchased items are kept for record-keeping but not distributed
            if shopping_item.purchased_quantity is None or shopping_item.purchased_quantity == 0:
                continue

            if total_requested != shopping_item.purchased_quantity:
                shortage = total_requested - shopping_item.purchased_quantity
                raise BadRequestError(
                    f"Quantities still don't match. Need to reduce {shortage} more items across all bids."
                )

    def _distribute_items_to_bidders(self, run_id: UUID) -> None:
        """Distribute purchased items to bidders.

        When quantities match exactly, each bidder gets their full bid quantity.
        When quantities don't match (force mode), distribute proportionally.
        """
        shopping_items = self.repo.get_shopping_list_items(run_id)
        all_bids = self.repo.get_bids_by_run(run_id)

        for shopping_item in shopping_items:
            if not shopping_item.is_purchased:
                continue

            # Skip items with 0 purchased quantity (not actually bought)
            if not shopping_item.purchased_quantity or shopping_item.purchased_quantity == 0:
                continue

            product_bids = [
                bid
                for bid in all_bids
                if bid.product_id == shopping_item.product_id and not bid.interested_only
            ]
            total_requested = sum(bid.quantity for bid in product_bids)
            self.repo.update_shopping_list_item_requested_quantity(
                shopping_item.id, total_requested
            )

            # Check if we need proportional distribution
            if total_requested > shopping_item.purchased_quantity:
                # Proportional distribution: scale down each bid
                ratio = shopping_item.purchased_quantity / total_requested
                for bid in product_bids:
                    distributed_qty = bid.quantity * ratio
                    self.repo.update_bid_distributed_quantities(
                        bid.id, distributed_qty, shopping_item.purchased_price_per_unit
                    )
            else:
                # Exact match or over-purchased: give everyone their full bid
                for bid in product_bids:
                    self.repo.update_bid_distributed_quantities(
                        bid.id, bid.quantity, shopping_item.purchased_price_per_unit
                    )
