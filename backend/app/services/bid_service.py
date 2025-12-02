"""Bid service for managing bid operations."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import PlaceBidResponse, RetractBidResponse
from app.core.error_codes import (
    BID_NOT_FOUND,
    BID_PRODUCT_NOT_IN_SHOPPING_LIST,
    BID_QUANTITY_BELOW_DISTRIBUTED,
    BID_QUANTITY_EXCEEDS_PURCHASED,
    BID_QUANTITY_NEGATIVE,
    CANNOT_BID_NEW_PRODUCT_IN_ADJUSTING,
    CANNOT_JOIN_RUN_IN_ADJUSTING_STATE,
    CANNOT_RETRACT_BID_IN_ADJUSTING,
    INVALID_RUN_STATE_TRANSITION,
    NOT_RUN_PARTICIPANT,
    PARTICIPATION_NOT_FOUND,
    PRODUCT_NOT_FOUND,
    RUN_MAX_PRODUCTS_EXCEEDED,
    RUN_NOT_FOUND,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import Product, ProductBid, Run, RunParticipation, User
from app.core.run_state import RunState, state_machine
from app.core.success_codes import BID_PLACED, BID_RETRACTED
from app.events.domain_events import BidPlacedEvent, BidRetractedEvent
from app.events.event_bus import event_bus
from app.infrastructure.config import MAX_PRODUCTS_PER_RUN
from app.infrastructure.request_context import get_logger
from app.repositories import (
    get_bid_repository,
    get_product_repository,
    get_run_repository,
    get_shopping_repository,
    get_user_repository,
)
from app.utils.validation import validate_uuid

from .base_service import BaseService

logger = get_logger(__name__)


class BidService(BaseService):
    """Service for managing bid operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with necessary repositories."""
        super().__init__(db)
        self.bid_repo = get_bid_repository(db)
        self.product_repo = get_product_repository(db)
        self.run_repo = get_run_repository(db)
        self.shopping_repo = get_shopping_repository(db)
        self.user_repo = get_user_repository(db)

    async def place_bid(
        self,
        run_id: str,
        product_id: str,
        quantity: float,
        interested_only: bool,
        user: User,
        comment: str | None = None,
    ) -> PlaceBidResponse:
        """Place or update a bid on a product in a run.

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
            comment: Optional comment to add to the bid

        Returns:
            PlaceBidResponse with status and calculated totals for broadcasting

        Raises:
            BadRequestError: If IDs are invalid or state doesn't allow bidding
            NotFoundError: If run or product not found
            ForbiddenError: If user not authorized
        """
        logger.info(
            'Placing bid on product',
            extra={
                'user_id': str(user.id),
                'run_id': run_id,
                'product_id': product_id,
                'quantity': quantity,
            },
        )

        # Validate and get entities
        run_uuid, product_uuid, run, product = await self._validate_bid_request(run_id, product_id, user)

        # Get or create user participation
        participation, is_new_participant = await self._ensure_user_participation(run_uuid, run, user)

        # Validate the bid based on current state
        await self._validate_bid_for_state(run, product_uuid, quantity, participation)

        # Create or update the bid
        await self.bid_repo.create_or_update_bid(
            participation.id, product_uuid, quantity, interested_only, comment
        )

        # Handle automatic state transition (planning → active)
        state_changed = await self._check_planning_to_active_transition(
            run, is_new_participant, participation
        )

        # Calculate new totals for response
        new_total = await self.calculate_product_total(run_uuid, product_uuid)

        # Emit domain event for bid placement
        event_bus.emit(
            BidPlacedEvent(
                run_id=run_uuid,
                product_id=product_uuid,
                user_id=user.id,
                user_name=user.name,
                quantity=quantity,
                interested_only=interested_only,
                new_total=new_total,
                group_id=run.group_id,
            )
        )

        return PlaceBidResponse(
            code=BID_PLACED,
            product_id=str(product_uuid),
            user_id=str(user.id),
            user_name=user.name,
            quantity=quantity,
            interested_only=interested_only,
            new_total=new_total,
            state_changed=state_changed,
            new_state=RunState.ACTIVE if state_changed else run.state,
            run_id=str(run_uuid),
            group_id=str(run.group_id),
        )

    async def retract_bid(self, run_id: str, product_id: str, user: User) -> RetractBidResponse:
        """Retract a user's bid on a product in a run.

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
            'Retracting bid',
            extra={'user_id': str(user.id), 'run_id': run_id, 'product_id': product_id},
        )

        run_uuid, product_uuid, run = await self._validate_retract_request(run_id, product_id, user)
        await self._check_adjusting_constraints_for_retraction(run, run_uuid, product_uuid, user.id)
        participation = await self._get_user_participation(user.id, run_uuid, run_id)
        await self._remove_bid_and_recalculate(participation, product_uuid, product_id)
        new_total = await self.calculate_product_total(run_uuid, product_uuid)

        logger.info(
            'Bid retracted successfully',
            extra={
                'user_id': str(user.id),
                'run_id': str(run_uuid),
                'product_id': str(product_uuid),
                'new_total': new_total,
            },
        )

        # Emit domain event for bid retraction
        event_bus.emit(
            BidRetractedEvent(
                run_id=run_uuid,
                product_id=product_uuid,
                user_id=user.id,
                new_total=new_total,
                group_id=run.group_id,
            )
        )

        return RetractBidResponse(
            code=BID_RETRACTED,
            run_id=str(run_uuid),
            product_id=str(product_uuid),
            user_id=str(user.id),
            new_total=new_total,
        )

    async def calculate_product_total(self, run_id: UUID, product_id: UUID) -> float:
        """Calculate total quantity for a product (excluding interested-only bids).

        Args:
            run_id: Run UUID
            product_id: Product UUID

        Returns:
            Total quantity across all bids for the product
        """
        all_bids = await self.bid_repo.get_bids_by_run(run_id)
        product_bids = [bid for bid in all_bids if bid.product_id == product_id]
        return sum(bid.quantity for bid in product_bids if not bid.interested_only)

    async def _validate_bid_request(
        self, run_id: str, product_id: str, user: User
    ) -> tuple[UUID, UUID, Run, Product]:
        """Validate bid request and return validated entities."""
        # Validate IDs
        run_uuid = validate_uuid(run_id, 'Run')
        product_uuid = validate_uuid(product_id, 'Product')

        # Verify run exists and user has access
        run = await self._get_run_with_auth_check(run_uuid, user)

        # Check if run allows bidding using state machine
        run_state = RunState(run.state)
        if not state_machine.can_place_bid(run_state):
            raise BadRequestError(
                code=INVALID_RUN_STATE_TRANSITION,
                current_state=run.state,
                action='place_bid',
                allowed_states='planning, active, adjusting',
            )

        # Verify product exists (products don't need store availability to be bid on)
        product = await self.product_repo.get_product_by_id(product_uuid)
        if not product:
            raise NotFoundError(
                code=PRODUCT_NOT_FOUND, message='Product not found', product_id=product_id
            )

        return run_uuid, product_uuid, run, product

    async def _get_run_with_auth_check(self, run_uuid: UUID, user: User) -> Run:
        """Get run and verify user has access to it."""
        run = await self.run_repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError(code=RUN_NOT_FOUND, message='Run not found', run_id=str(run_uuid))

        # Verify user has access to this run (member of the group)
        user_groups = await self.user_repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError(
                code=NOT_RUN_PARTICIPANT,
                message='Not authorized to view this run',
                run_id=str(run_uuid),
            )

        return run

    async def _ensure_user_participation(
        self, run_uuid: UUID, run: Run, user: User
    ) -> tuple[RunParticipation, bool]:
        """Get or create user participation in run."""
        participation = await self.run_repo.get_participation(user.id, run_uuid)
        is_new_participant = False

        if not participation:
            # Don't allow new participants in adjusting state - check using state machine
            run_state = RunState(run.state)
            if not state_machine.can_join_run(run_state):
                raise BadRequestError(
                    code=CANNOT_JOIN_RUN_IN_ADJUSTING_STATE,
                    message='Cannot join run in adjusting state',
                    run_id=str(run_uuid),
                    current_state=run.state,
                )
            # Create participation (not as leader)
            participation = await self.run_repo.create_participation(user.id, run_uuid, is_leader=False)
            is_new_participant = True

        return participation, is_new_participant

    async def _validate_bid_for_state(
        self, run: Run, product_uuid: UUID, quantity: float, participation: RunParticipation
    ) -> ProductBid | None:
        """Validate bid based on run state and return existing bid if any."""
        # Basic quantity validation
        if quantity < 0:
            raise BadRequestError(
                code=BID_QUANTITY_NEGATIVE, message='Quantity cannot be negative', quantity=quantity
            )

        # Check for existing bid
        existing_bid = await self.bid_repo.get_bid(participation.id, product_uuid)

        # Check product limit for new products
        if not existing_bid:
            await self._check_product_limit(run.id)

        # State-specific validation
        if run.state == RunState.ADJUSTING:
            if not existing_bid:
                raise BadRequestError(
                    code=CANNOT_BID_NEW_PRODUCT_IN_ADJUSTING,
                    message='Cannot bid on new products in adjusting state',
                    run_id=str(run.id),
                    product_id=str(product_uuid),
                )
            await self._validate_adjusting_bid(run.id, product_uuid, quantity, existing_bid)

        return existing_bid

    async def _check_product_limit(self, run_id: UUID) -> None:
        """Check if run has reached maximum product limit."""
        all_bids = await self.bid_repo.get_bids_by_run(run_id)
        unique_products = {bid.product_id for bid in all_bids}
        if len(unique_products) >= MAX_PRODUCTS_PER_RUN:
            logger.warning(
                'Run has reached maximum product limit',
                extra={'run_id': str(run_id), 'unique_products': len(unique_products)},
            )
            raise BadRequestError(
                code=RUN_MAX_PRODUCTS_EXCEEDED,
                message=f'Run has reached maximum of {MAX_PRODUCTS_PER_RUN} products',
                run_id=str(run_id),
                max_products=MAX_PRODUCTS_PER_RUN,
                current_products=len(unique_products),
            )

    async def _validate_adjusting_bid(
        self, run_id: UUID, product_uuid: UUID, quantity: float, existing_bid: ProductBid
    ) -> None:
        """Validate bid adjustments during adjusting state.

        Allows:
        - Downward adjustments when purchased < requested (shortage)
        - Upward adjustments when purchased > requested (surplus)
        """
        # Get shopping list to check purchased quantity
        shopping_items = await self.shopping_repo.get_shopping_list_items(run_id)
        shopping_item = next(
            (item for item in shopping_items if item.product_id == product_uuid), None
        )

        if not shopping_item:
            raise BadRequestError(
                code=BID_PRODUCT_NOT_IN_SHOPPING_LIST,
                message='Product not in shopping list',
                product_id=str(product_uuid),
                run_id=str(run_id),
            )

        purchased_qty = shopping_item.purchased_quantity or 0
        requested_qty = shopping_item.requested_quantity
        difference = purchased_qty - requested_qty  # positive = surplus, negative = shortage

        if difference < 0:
            # Shortage scenario: can only reduce bids
            shortage = abs(difference)
            min_allowed = max(0, existing_bid.quantity - shortage)

            if quantity > existing_bid.quantity:
                raise BadRequestError(
                    code=BID_QUANTITY_EXCEEDS_PURCHASED,
                    message=f'Can only reduce bids when there is a shortage (current: {existing_bid.quantity}, new: {quantity})',
                    current_quantity=existing_bid.quantity,
                    new_quantity=quantity,
                )
            if quantity < min_allowed:
                raise BadRequestError(
                    code=BID_QUANTITY_BELOW_DISTRIBUTED,
                    message=f'Cannot reduce bid below {min_allowed} '
                    f'(current: {existing_bid.quantity}, shortage: {shortage}, would remove more than needed)',
                    current_quantity=existing_bid.quantity,
                    new_quantity=quantity,
                    min_allowed=min_allowed,
                    shortage=shortage,
                )
        elif difference > 0:
            # Surplus scenario: can only increase bids
            surplus = difference
            max_allowed = existing_bid.quantity + surplus

            if quantity < existing_bid.quantity:
                raise BadRequestError(
                    code=BID_QUANTITY_BELOW_DISTRIBUTED,
                    message=f'Can only increase bids when there is a surplus (current: {existing_bid.quantity}, new: {quantity})',
                    current_quantity=existing_bid.quantity,
                    new_quantity=quantity,
                )
            if quantity > max_allowed:
                raise BadRequestError(
                    code=BID_QUANTITY_EXCEEDS_PURCHASED,
                    message=f'Cannot increase bid above {max_allowed} '
                    f'(current: {existing_bid.quantity}, surplus: {surplus}, would take more than available)',
                    current_quantity=existing_bid.quantity,
                    new_quantity=quantity,
                    max_allowed=max_allowed,
                    surplus=surplus,
                )
        # If difference == 0, quantities already match, no adjustment needed (shouldn't reach here)

    async def _check_planning_to_active_transition(
        self, run: Run, is_new_participant: bool, participation: RunParticipation
    ) -> bool:
        """Check if run should transition from planning to active.

        Returns:
            True if state changed, False otherwise
        """
        # Automatic state transition: planning → active
        # When a non-leader places their first bid, transition from planning to active
        if is_new_participant and not participation.is_leader and run.state == RunState.PLANNING:
            await self.run_repo.update_run_state(run.id, RunState.ACTIVE)
            return True
        return False

    async def _validate_retract_request(
        self, run_id: str, product_id: str, user: User
    ) -> tuple[UUID, UUID, Run]:
        """Validate retract request and return UUIDs and run object."""
        run_uuid = validate_uuid(run_id, 'Run')
        product_uuid = validate_uuid(product_id, 'Product')

        run = await self.run_repo.get_run_by_id(run_uuid)
        if not run:
            raise NotFoundError(code=RUN_NOT_FOUND, message='Run not found', run_id=run_id)

        user_groups = await self.user_repo.get_user_groups(user)
        if not any(g.id == run.group_id for g in user_groups):
            raise ForbiddenError(
                code=NOT_RUN_PARTICIPANT,
                message='Not authorized to modify bids on this run',
                run_id=run_id,
            )

        # Check if run allows bid retraction using state machine
        run_state = RunState(run.state)
        if not state_machine.can_retract_bid(run_state):
            raise BadRequestError(
                code=CANNOT_RETRACT_BID_IN_ADJUSTING,
                current_state=run.state,
                action='retract_bid',
                allowed_states='planning, active, adjusting',
            )

        return run_uuid, product_uuid, run

    async def _check_adjusting_constraints_for_retraction(
        self, run: Run, run_id: UUID, product_id: UUID, user_id: UUID
    ) -> None:
        """Check if retraction is allowed in adjusting state.

        - For shortage: cannot retract (would make shortage worse)
        - For surplus: cannot retract at all (need to increase bids, not reduce)
        """
        if run.state != RunState.ADJUSTING:
            return

        shopping_items = await self.shopping_repo.get_shopping_list_items(run_id)
        shopping_item = next(
            (item for item in shopping_items if item.product_id == product_id), None
        )

        if not shopping_item:
            return

        purchased_qty = shopping_item.purchased_quantity or 0
        requested_qty = shopping_item.requested_quantity
        difference = purchased_qty - requested_qty  # positive = surplus, negative = shortage

        participation = await self.run_repo.get_participation(user_id, run_id)
        if not participation:
            return

        current_bid = await self.bid_repo.get_bid(participation.id, product_id)
        if not current_bid:
            return

        if difference < 0:
            # Shortage scenario: cannot retract at all (would make shortage worse)
            raise BadRequestError(
                code=BID_QUANTITY_EXCEEDS_PURCHASED,
                message=f'Cannot retract bid when there is a shortage. Please reduce your bid instead.',
                current_quantity=current_bid.quantity,
            )
        elif difference > 0:
            # Surplus scenario: cannot retract at all (need to increase bids, not reduce)
            raise BadRequestError(
                code=BID_QUANTITY_EXCEEDS_PURCHASED,
                message=f'Cannot retract bid when there is a surplus. Please increase your bid instead.',
                current_quantity=current_bid.quantity,
            )

    async def _get_user_participation(
        self, user_id: UUID, run_id: UUID, run_id_str: str
    ) -> RunParticipation:
        """Get user's participation in a run."""
        participation = await self.run_repo.get_participation(user_id, run_id)
        if not participation:
            raise NotFoundError(
                code=PARTICIPATION_NOT_FOUND,
                message='Participation not found',
                user_id=str(user_id),
                run_id=run_id_str,
            )
        return participation

    async def _remove_bid_and_recalculate(
        self, participation: RunParticipation, product_id: UUID, product_id_str: str
    ) -> None:
        """Remove bid from database."""
        bid = await self.bid_repo.get_bid(participation.id, product_id)
        if not bid:
            raise NotFoundError(
                code=BID_NOT_FOUND, message='Bid not found', product_id=product_id_str
            )

        await self.bid_repo.delete_bid(participation.id, product_id)
