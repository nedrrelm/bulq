"""Distribution service for handling distribution-related business logic."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    DistributionGroupResponse,
    DistributionProduct,
    DistributionSummary,
    DistributionUser,
    StateChangeResponse,
    SuccessResponse,
)
from app.api.schemas.notification_data import RunStateChangedData
from app.core.error_codes import (
    BID_NOT_FOUND,
    CANNOT_COMPLETE_DISTRIBUTION_UNPURCHASED_ITEMS,
    INVALID_RUN_STATE_TRANSITION,
    NOT_RUN_LEADER,
    NOT_RUN_LEADER_OR_HELPER,
    NOT_RUN_PARTICIPANT,
    RUN_NOT_FOUND,
    RUN_NOT_IN_DISTRIBUTING_STATE,
)
from app.core.exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
)
from app.core.models import Product, ProductBid, User
from app.core.run_state import RunState, state_machine
from app.core.success_codes import BID_MARKED_PICKED_UP, DISTRIBUTION_COMPLETED
from app.events.domain_events import DistributionUpdatedEvent
from app.events.event_bus import event_bus
from app.infrastructure.request_context import get_logger
from app.infrastructure.transaction import transaction
from app.repositories import (
    get_bid_repository,
    get_distribution_group_repository,
    get_notification_repository,
    get_product_repository,
    get_run_repository,
    get_store_repository,
    get_user_repository,
)
from app.utils.background_tasks import create_background_task

from .base_service import BaseService

logger = get_logger(__name__)


class DistributionService(BaseService):
    """Service for distribution operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with necessary repositories."""
        super().__init__(db)
        self.bid_repo = get_bid_repository(db)
        self.dist_group_repo = get_distribution_group_repository(db)
        self.notification_repo = get_notification_repository(db)
        self.product_repo = get_product_repository(db)
        self.run_repo = get_run_repository(db)
        self.store_repo = get_store_repository(db)
        self.user_repo = get_user_repository(db)

    async def get_distribution_summary(
        self, run_id: UUID, current_user: User
    ) -> DistributionSummary:
        """Get distribution data organized by groups, then by user within each group.

        Args:
            run_id: The run ID to get distribution for
            current_user: The authenticated user making the request

        Returns:
            DistributionSummary with groups containing users and products
        """
        await self._validate_distribution_access(run_id, current_user)

        # Ensure default group exists for legacy runs
        await self._ensure_groups_exist(run_id)

        all_bids = await self.bid_repo.get_bids_by_run_with_participations(run_id)
        users_data = await self._aggregate_bids_by_user(all_bids)

        # Build per-user distributions
        all_distributions: dict[str, DistributionUser] = {}
        for user_data in users_data.values():
            if not user_data['products']:
                continue
            try:
                dist = self._build_user_distribution(user_data)
                all_distributions[dist.user_id] = dist
            except Exception as e:
                logger.error(
                    f'Error building distribution for user {user_data.get("user_name", "unknown")}: {e}',
                    extra={'run_id': str(run_id)},
                    exc_info=True,
                )

        # Apply leader fee split across all users
        await self._apply_leader_fee(run_id, list(all_distributions.values()))

        # Group users by distribution group
        groups = await self.dist_group_repo.get_groups_by_run(run_id)
        participations = await self.run_repo.get_run_participations(run_id)

        # Build mapping: group_id -> list of user_ids
        group_user_map: dict[UUID, list[str]] = {g.id: [] for g in groups}
        for p in participations:
            if p.distribution_group_id and p.distribution_group_id in group_user_map:
                group_user_map[p.distribution_group_id].append(str(p.user_id))

        group_responses = []
        for group in groups:
            group_user_ids = group_user_map.get(group.id, [])
            group_users = []
            for uid in group_user_ids:
                if uid in all_distributions:
                    group_users.append(all_distributions[uid])

            # Sort: unpicked first, then by name
            group_users.sort(key=lambda x: (x.all_picked_up, x.user_name))

            group_total = sum(float(u.total_cost) for u in group_users)

            group_responses.append(
                DistributionGroupResponse(
                    id=str(group.id),
                    name=group.name,
                    is_default=group.is_default,
                    is_done=group.is_done,
                    sort_order=group.sort_order,
                    users=group_users,
                    total_cost=f'{group_total:.2f}',
                )
            )

        return DistributionSummary(groups=group_responses)

    async def _ensure_groups_exist(self, run_id: UUID) -> None:
        """Ensure distribution groups exist for a run (handles legacy runs)."""
        groups = await self.dist_group_repo.get_groups_by_run(run_id)
        if not groups:
            # Create default group for legacy run
            default_group = await self.dist_group_repo.create_group(
                run_id=run_id, name='1', is_default=True, sort_order=0
            )
            # Assign all participations to default group
            participations = await self.run_repo.get_run_participations(run_id)
            for p in participations:
                await self.dist_group_repo.assign_participation_to_group(p.id, default_group.id)

    async def _validate_distribution_access(self, run_id: UUID, current_user: User) -> None:
        """Validate user has access to view distribution."""
        run = await self.run_repo.get_run_by_id(run_id)
        if not run:
            raise NotFoundError(code=RUN_NOT_FOUND, message='Run not found', run_id=run_id)

        await self._verify_run_access(
            current_user, run, NOT_RUN_PARTICIPANT, 'Not authorized to view this run', run_id=run_id
        )

        # Check if viewing distribution is allowed using state machine
        run_state = RunState(run.state)
        if not state_machine.can_view_distribution(run_state):
            raise BadRequestError(
                code=INVALID_RUN_STATE_TRANSITION,
                current_state=run.state,
                action='view_distribution',
                allowed_states='distributing, completed',
            )

    async def _aggregate_bids_by_user(
        self, all_bids: list[ProductBid]
    ) -> dict[str, dict[str, Any]]:
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

            product = await self._get_product(bid.product_id)
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

    async def _apply_leader_fee(self, run_id: UUID, distributions: list[DistributionUser]) -> None:
        """Apply leader fee split to distributions in-place."""
        run = await self.run_repo.get_run_by_id(run_id)
        if not run or not run.leader_fee or float(run.leader_fee) <= 0:
            return

        fee = float(run.leader_fee)

        participations = await self.run_repo.get_run_participations(run_id)
        exempt_user_ids = set()
        for p in participations:
            if p.is_leader or p.is_helper:
                exempt_user_ids.add(str(p.user_id))

        fee_paying_users = [d for d in distributions if d.user_id not in exempt_user_ids]
        if not fee_paying_users:
            return

        fee_share = round(fee / len(fee_paying_users), 2)

        for dist in distributions:
            if dist.user_id not in exempt_user_ids:
                dist.fee_share = f'{fee_share:.2f}'
                current_total = float(dist.total_cost)
                dist.total_cost = f'{current_total + fee_share:.2f}'

    async def mark_picked_up(
        self, run_id: UUID, bid_id: UUID, current_user: User
    ) -> SuccessResponse:
        """Mark a product as picked up by a user."""
        run = await self.run_repo.get_run_by_id(run_id)
        if not run:
            raise NotFoundError(code=RUN_NOT_FOUND, message='Run not found', run_id=run_id)

        participation = await self.run_repo.get_participation(current_user.id, run_id)
        if not participation or not self._is_leader_or_helper(participation):
            raise ForbiddenError(
                code=NOT_RUN_LEADER_OR_HELPER,
                message='Only the run leader or helpers can mark items as picked up',
                run_id=run_id,
            )

        bid = await self._get_bid(bid_id)
        if not bid:
            raise NotFoundError(
                code=BID_NOT_FOUND, message='Bid not found', bid_id=bid_id, run_id=run_id
            )

        bid.is_picked_up = True
        await self._commit_changes()

        logger.info(
            'Bid marked as picked up',
            extra={
                'bid_id': str(bid_id),
                'user_id': str(current_user.id),
                'run_id': str(bid.participation.run_id),
            },
        )

        event_bus.emit(
            DistributionUpdatedEvent(run_id=run_id, bid_id=bid_id, action='marked_picked_up')
        )

        return SuccessResponse(
            code=BID_MARKED_PICKED_UP,
            details={
                'run_id': str(run_id),
                'bid_id': str(bid_id),
                'user_id': str(bid.participation.user_id),
            },
        )

    async def complete_distribution(self, run_id: UUID, current_user: User) -> StateChangeResponse:
        """Complete distribution - transition from distributing to completed state."""
        run = await self.run_repo.get_run_by_id(run_id)
        if not run:
            raise NotFoundError(code=RUN_NOT_FOUND, message='Run not found', run_id=run_id)

        participation = await self.run_repo.get_participation(current_user.id, run_id)
        if not participation or not participation.is_leader:
            raise ForbiddenError(
                code=NOT_RUN_LEADER,
                message='Only the run leader can complete distribution',
                run_id=run_id,
            )

        run_state = RunState(run.state)
        if not state_machine.can_complete_distribution(run_state):
            raise BadRequestError(
                code=RUN_NOT_IN_DISTRIBUTING_STATE,
                message='Can only complete distribution from distributing state',
                run_id=run_id,
                current_state=run.state,
                required_state=RunState.DISTRIBUTING.value,
            )

        all_bids = await self.bid_repo.get_bids_by_run(run_id)
        unpicked_bids = [
            bid
            for bid in all_bids
            if not bid.interested_only and bid.distributed_quantity and not bid.is_picked_up
        ]

        if unpicked_bids:
            raise BadRequestError(
                code=CANNOT_COMPLETE_DISTRIBUTION_UNPURCHASED_ITEMS,
                message='Cannot complete distribution - some items not picked up',
                run_id=run_id,
            )

        async with transaction(self.db, 'complete distribution and transition to completed state'):
            old_state = run.state
            await self.run_repo.update_run_state(run_id, RunState.COMPLETED)
            await self._notify_run_state_change(run, old_state, RunState.COMPLETED)

        logger.info(
            'Distribution completed', extra={'run_id': str(run_id), 'user_id': str(current_user.id)}
        )
        return StateChangeResponse(
            code=DISTRIBUTION_COMPLETED,
            state=RunState.COMPLETED,
            run_id=str(run_id),
            group_id=str(run.group_id),
        )

    async def _get_product(self, product_id: UUID) -> Product:
        """Get product from repository."""
        return await self.product_repo.get_product_by_id(product_id)

    async def _get_bid(self, bid_id: UUID) -> ProductBid:
        """Get bid from repository."""
        return await self.bid_repo.get_bid_by_id(bid_id)

    async def _commit_changes(self) -> None:
        """Commit changes."""
        await self.bid_repo.commit_changes()

    async def _notify_run_state_change(self, run, old_state: str, new_state: str) -> None:
        """Create notifications for all participants when run state changes."""
        store_name = await self._get_store_name(run.store_id)
        participations = await self.run_repo.get_run_participations(run.id)

        notification_data = RunStateChangedData(
            run_id=str(run.id),
            store_name=store_name,
            old_state=old_state,
            new_state=new_state,
            group_id=str(run.group_id),
        )

        from app.api.websocket_manager import manager

        for participation in participations:
            notification = await self.notification_repo.create_notification(
                user_id=participation.user_id,
                type='run_state_changed',
                data=notification_data.model_dump(mode='json'),
            )

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
