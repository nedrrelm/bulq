"""Distribution group service for managing pickup point groups."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import SuccessResponse
from app.core.error_codes import (
    CANNOT_DELETE_DEFAULT_DISTRIBUTION_GROUP,
    DISTRIBUTION_GROUP_NOT_FOUND,
    NOT_RUN_LEADER,
    NOT_RUN_LEADER_OR_HELPER,
    PARTICIPATION_NOT_FOUND,
    RUN_NOT_FOUND,
    RUN_NOT_IN_DISTRIBUTING_STATE,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import User
from app.core.run_state import RunState
from app.core.success_codes import (
    DISTRIBUTION_GROUP_CREATED,
    DISTRIBUTION_GROUP_DELETED,
    DISTRIBUTION_GROUP_MARKED_DONE,
    USER_ASSIGNED_TO_DISTRIBUTION_GROUP,
)
from app.events.domain_events import DistributionUpdatedEvent
from app.events.event_bus import event_bus
from app.infrastructure.request_context import get_logger
from app.repositories import (
    get_bid_repository,
    get_distribution_group_repository,
    get_run_repository,
    get_user_repository,
)

from .base_service import BaseService

logger = get_logger(__name__)


class DistributionGroupService(BaseService):
    """Service for distribution group operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.dist_group_repo = get_distribution_group_repository(db)
        self.run_repo = get_run_repository(db)
        self.bid_repo = get_bid_repository(db)
        self.user_repo = get_user_repository(db)

    async def ensure_default_group(self, run_id: UUID) -> None:
        """Create a default distribution group for a run if none exists.

        Also assigns any unassigned participations to the default group.
        """
        default_group = await self.dist_group_repo.get_default_group(run_id)
        if not default_group:
            default_group = await self.dist_group_repo.create_group(
                run_id=run_id, name='1', is_default=True, sort_order=0
            )
            logger.info(
                'Created default distribution group',
                extra={'run_id': str(run_id), 'group_id': str(default_group.id)},
            )

        # Assign any unassigned participations to the default group
        participations = await self.run_repo.get_run_participations(run_id)
        for p in participations:
            if p.distribution_group_id is None:
                await self.dist_group_repo.assign_participation_to_group(p.id, default_group.id)

    async def create_group(self, run_id: UUID, current_user: User) -> SuccessResponse:
        """Create a new numbered distribution group for a run.

        Only available in distributing state, leader only.
        """
        run = await self._get_run_or_raise(run_id)
        await self._verify_leader(current_user, run_id)
        self._verify_distributing_state(run)

        # Ensure default group exists
        await self.ensure_default_group(run_id)

        # Auto-name as next number
        existing_groups = await self.dist_group_repo.get_groups_by_run(run_id)
        next_number = len(existing_groups) + 1
        sort_order = next_number - 1

        group = await self.dist_group_repo.create_group(
            run_id=run_id, name=str(next_number), is_default=False, sort_order=sort_order
        )

        logger.info(
            'Distribution group created',
            extra={'run_id': str(run_id), 'group_id': str(group.id), 'group_name': group.name},
        )

        # Emit event for WebSocket broadcast
        event_bus.emit(
            DistributionUpdatedEvent(run_id=run_id, bid_id=group.id, action='group_created')
        )

        return SuccessResponse(
            code=DISTRIBUTION_GROUP_CREATED,
            details={'run_id': str(run_id), 'group_id': str(group.id), 'name': group.name},
        )

    async def delete_group(
        self, run_id: UUID, group_id: UUID, current_user: User
    ) -> SuccessResponse:
        """Delete a distribution group and reassign its users to the default group.

        Cannot delete the default group.
        """
        run = await self._get_run_or_raise(run_id)
        await self._verify_leader(current_user, run_id)
        self._verify_distributing_state(run)

        group = await self.dist_group_repo.get_group_by_id(group_id)
        if not group or group.run_id != run_id:
            raise NotFoundError(
                code=DISTRIBUTION_GROUP_NOT_FOUND,
                message='Distribution group not found',
                group_id=str(group_id),
            )

        if group.is_default:
            raise BadRequestError(
                code=CANNOT_DELETE_DEFAULT_DISTRIBUTION_GROUP,
                message='Cannot delete the default distribution group',
            )

        # Reassign users to default group
        default_group = await self.dist_group_repo.get_default_group(run_id)
        participations = await self.run_repo.get_run_participations(run_id)
        for p in participations:
            if p.distribution_group_id == group_id:
                await self.dist_group_repo.assign_participation_to_group(p.id, default_group.id)

        await self.dist_group_repo.delete_group(group_id)

        logger.info(
            'Distribution group deleted',
            extra={'run_id': str(run_id), 'group_id': str(group_id)},
        )

        event_bus.emit(
            DistributionUpdatedEvent(run_id=run_id, bid_id=group_id, action='group_deleted')
        )

        return SuccessResponse(
            code=DISTRIBUTION_GROUP_DELETED,
            details={'run_id': str(run_id), 'group_id': str(group_id)},
        )

    async def assign_user_to_group(
        self, run_id: UUID, group_id: UUID, user_id: UUID, current_user: User
    ) -> SuccessResponse:
        """Assign a user to a distribution group."""
        run = await self._get_run_or_raise(run_id)
        await self._verify_leader(current_user, run_id)
        self._verify_distributing_state(run)

        group = await self.dist_group_repo.get_group_by_id(group_id)
        if not group or group.run_id != run_id:
            raise NotFoundError(
                code=DISTRIBUTION_GROUP_NOT_FOUND,
                message='Distribution group not found',
                group_id=str(group_id),
            )

        participation = await self.run_repo.get_participation(user_id, run_id)
        if not participation:
            raise NotFoundError(
                code=PARTICIPATION_NOT_FOUND,
                message='User is not a participant of this run',
                user_id=str(user_id),
            )

        await self.dist_group_repo.assign_participation_to_group(participation.id, group_id)

        logger.info(
            'User assigned to distribution group',
            extra={
                'run_id': str(run_id),
                'group_id': str(group_id),
                'user_id': str(user_id),
            },
        )

        event_bus.emit(
            DistributionUpdatedEvent(run_id=run_id, bid_id=group_id, action='user_assigned')
        )

        return SuccessResponse(
            code=USER_ASSIGNED_TO_DISTRIBUTION_GROUP,
            details={
                'run_id': str(run_id),
                'group_id': str(group_id),
                'user_id': str(user_id),
            },
        )

    async def mark_group_done(
        self, run_id: UUID, group_id: UUID, current_user: User
    ) -> SuccessResponse:
        """Mark all bids in a distribution group as picked up."""
        run = await self._get_run_or_raise(run_id)

        # Leader or helper can mark group done
        participation = await self.run_repo.get_participation(current_user.id, run_id)
        if not participation or not self._is_leader_or_helper(participation):
            raise ForbiddenError(
                code=NOT_RUN_LEADER_OR_HELPER,
                message='Only the run leader or helpers can mark groups as done',
                run_id=str(run_id),
            )

        self._verify_distributing_state(run)

        group = await self.dist_group_repo.get_group_by_id(group_id)
        if not group or group.run_id != run_id:
            raise NotFoundError(
                code=DISTRIBUTION_GROUP_NOT_FOUND,
                message='Distribution group not found',
                group_id=str(group_id),
            )

        # Mark all bids for users in this group as picked up
        all_participations = await self.run_repo.get_run_participations(run_id)
        group_participations = [
            p for p in all_participations if p.distribution_group_id == group_id
        ]

        all_bids = await self.bid_repo.get_bids_by_run(run_id)
        group_participation_ids = {p.id for p in group_participations}

        for bid in all_bids:
            if (
                bid.participation_id in group_participation_ids
                and not bid.interested_only
                and bid.distributed_quantity
                and not bid.is_picked_up
            ):
                bid.is_picked_up = True

        await self.bid_repo.commit_changes()

        # Mark the group itself as done
        await self.dist_group_repo.mark_group_done(group_id, is_done=True)

        logger.info(
            'Distribution group marked as done',
            extra={'run_id': str(run_id), 'group_id': str(group_id)},
        )

        event_bus.emit(
            DistributionUpdatedEvent(run_id=run_id, bid_id=group_id, action='group_marked_done')
        )

        return SuccessResponse(
            code=DISTRIBUTION_GROUP_MARKED_DONE,
            details={'run_id': str(run_id), 'group_id': str(group_id)},
        )

    async def _get_run_or_raise(self, run_id: UUID):
        """Get run or raise NotFoundError."""
        run = await self.run_repo.get_run_by_id(run_id)
        if not run:
            raise NotFoundError(code=RUN_NOT_FOUND, message='Run not found', run_id=str(run_id))
        return run

    async def _verify_leader(self, user: User, run_id: UUID) -> None:
        """Verify user is the run leader."""
        participation = await self.run_repo.get_participation(user.id, run_id)
        if not participation or not participation.is_leader:
            raise ForbiddenError(
                code=NOT_RUN_LEADER,
                message='Only the run leader can manage distribution groups',
                run_id=str(run_id),
            )

    def _verify_distributing_state(self, run) -> None:
        """Verify run is in distributing state."""
        if run.state != RunState.DISTRIBUTING:
            raise BadRequestError(
                code=RUN_NOT_IN_DISTRIBUTING_STATE,
                message='Distribution groups can only be managed in distributing state',
                current_state=run.state,
            )
