"""Service for group membership management operations."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import SuccessResponse
from app.api.websocket_manager import manager
from app.core.error_codes import (
    CANNOT_REMOVE_GROUP_ADMIN,
    GROUP_MEMBER_PROMOTION_FAILED,
    GROUP_MEMBER_REMOVAL_FAILED,
    GROUP_NOT_FOUND,
    LAST_ADMIN_CANNOT_LEAVE,
    NOT_A_GROUP_MEMBER,
    NOT_GROUP_ADMIN,
    USER_ALREADY_GROUP_ADMIN,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import User
from app.core.run_state import RunState
from app.core.success_codes import GROUP_LEFT, MEMBER_PROMOTED, MEMBER_REMOVED
from app.events.domain_events import MemberRemovedEvent
from app.events.event_bus import event_bus
from app.infrastructure.request_context import get_logger
from app.infrastructure.transaction import transaction
from app.repositories import (
    get_bid_repository,
    get_group_repository,
    get_run_repository,
    get_user_repository,
)
from app.utils.background_tasks import create_background_task
from app.utils.validation import validate_uuid

from .base_service import BaseService

logger = get_logger(__name__)


class GroupMembershipService(BaseService):
    """Service for group membership management.

    This service handles:
    - Removing members from groups
    - Members leaving groups
    - Promoting members to admin
    - Broadcasting membership changes

    Separate from queries and membership to maintain single responsibility.
    """

    def __init__(self, db: AsyncSession):
        """Initialize service with necessary repositories."""
        super().__init__(db)
        self.bid_repo = get_bid_repository(db)
        self.group_repo = get_group_repository(db)
        self.run_repo = get_run_repository(db)
        self.user_repo = get_user_repository(db)

    async def remove_member(self, group_id: str, member_id: str, user: User) -> SuccessResponse:
        """Remove a member from a group (admin only).

        This operation is wrapped in a transaction to ensure atomicity:
        - Remove member from group
        - Mark participations as removed
        - Cancel runs led by removed member
        All operations succeed together or all fail together.

        Args:
            group_id: The UUID string of the group
            member_id: The UUID string of the member to remove
            user: The requesting user (must be group admin)

        Returns:
            SuccessResponse with details

        Raises:
            BadRequestError: If ID formats are invalid
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not a group admin or trying to remove admin
        """
        # Validate outside transaction to fail fast on bad input
        group_uuid, member_uuid = await self._validate_member_removal_request(
            group_id, member_id, user
        )

        # Wrap all database modifications in a transaction
        async with transaction(self.db, 'remove group member and cancel runs'):
            affected_runs, cancelled_runs = await self._find_and_cancel_affected_runs(
                group_uuid, member_uuid
            )

        # Broadcast notifications after successful transaction
        await self._broadcast_removal_notifications(
            group_uuid, member_uuid, affected_runs, cancelled_runs, is_self_removal=False
        )

        logger.info(
            f'Member removed from group, cancelled {len(cancelled_runs)} runs',
            extra={
                'user_id': str(user.id),
                'group_id': str(group_uuid),
                'removed_user_id': str(member_uuid),
                'cancelled_runs': cancelled_runs,
            },
        )

        return SuccessResponse(
            code=MEMBER_REMOVED,
            details={
                'group_id': group_id,
                'member_id': member_id,
            },
        )

    async def leave_group(self, group_id: str, user: User) -> SuccessResponse:
        """Leave a group.

        This operation is similar to remove_member but initiated by the user themselves:
        - Remove user from group
        - Mark participations as removed
        - Cancel runs led by the user
        All operations succeed together or all fail together.

        Args:
            group_id: The UUID string of the group
            user: The user leaving the group

        Returns:
            SuccessResponse with details

        Raises:
            BadRequestError: If ID format is invalid or user is group admin
            NotFoundError: If group doesn't exist
        """
        group_uuid = validate_uuid(group_id, 'Group')

        group = await self.group_repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        # Check if user is a member
        members = await self.group_repo.get_group_members_with_admin_status(group_uuid)
        if not any(m['id'] == str(user.id) for m in members):
            raise BadRequestError(
                code=NOT_A_GROUP_MEMBER,
                message='You are not a member of this group',
                group_id=str(group_uuid),
            )

        # Count how many admins there are
        admin_count = sum(1 for m in members if m['is_group_admin'])

        # Prevent the last admin from leaving
        if await self.group_repo.is_user_group_admin(group_uuid, user.id) and admin_count <= 1:
            raise ForbiddenError(
                code=LAST_ADMIN_CANNOT_LEAVE,
                message='You are the only admin. Please promote another member to admin before leaving.',
                group_id=str(group_uuid),
            )

        # Wrap all database modifications in a transaction
        async with transaction(self.db, 'leave group and cancel runs'):
            affected_runs, cancelled_runs = await self._find_and_cancel_affected_runs(
                group_uuid, user.id
            )

        # Broadcast notifications after successful transaction
        await self._broadcast_removal_notifications(
            group_uuid, user.id, affected_runs, cancelled_runs, is_self_removal=True
        )

        logger.info(
            f'User left group, cancelled {len(cancelled_runs)} runs',
            extra={
                'user_id': str(user.id),
                'group_id': str(group_uuid),
                'cancelled_runs': cancelled_runs,
            },
        )

        return SuccessResponse(
            code=GROUP_LEFT,
            details={'group_id': group_id},
        )

    async def promote_member_to_admin(
        self, group_id: str, member_id: str, user: User
    ) -> SuccessResponse:
        """Promote a member to group admin (admin only).

        Args:
            group_id: The UUID string of the group
            member_id: The UUID string of the member to promote
            user: The requesting user (must be group admin)

        Returns:
            SuccessResponse with details

        Raises:
            BadRequestError: If ID formats are invalid or member doesn't exist
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not a group admin
        """
        group_uuid = validate_uuid(group_id, 'Group')
        member_uuid = validate_uuid(member_id, 'Member')

        group = await self.group_repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        # Check if requester is admin
        if not await self.group_repo.is_user_group_admin(group_uuid, user.id):
            logger.warning(
                'Non-admin user attempted to promote member',
                extra={'user_id': str(user.id), 'group_id': str(group_uuid)},
            )
            raise ForbiddenError(
                code=NOT_GROUP_ADMIN,
                message='Only group admins can promote members',
                group_id=str(group_uuid),
            )

        # Check if member exists in group
        members = await self.group_repo.get_group_members_with_admin_status(group_uuid)
        member_exists = any(m['id'] == str(member_uuid) for m in members)

        if not member_exists:
            raise BadRequestError(
                code=NOT_A_GROUP_MEMBER,
                message='User is not a member of this group',
                group_id=str(group_uuid),
                user_id=str(member_uuid),
            )

        # Check if member is already an admin
        if await self.group_repo.is_user_group_admin(group_uuid, member_uuid):
            raise BadRequestError(
                code=USER_ALREADY_GROUP_ADMIN,
                message='User is already a group admin',
                group_id=str(group_uuid),
                user_id=str(member_uuid),
            )

        # Promote the member
        success = await self.group_repo.set_group_member_admin(group_uuid, member_uuid, True)

        if not success:
            raise BadRequestError(
                code=GROUP_MEMBER_PROMOTION_FAILED,
                message='Failed to promote member',
                group_id=str(group_uuid),
                user_id=str(member_uuid),
            )

        # Get member info for logging
        member_info = next((m for m in members if m['id'] == str(member_uuid)), None)
        member_name = member_info['name'] if member_info else 'Unknown'

        logger.info(
            'Member promoted to admin',
            extra={
                'user_id': str(user.id),
                'group_id': str(group_uuid),
                'promoted_user_id': str(member_uuid),
            },
        )

        # Broadcast member_promoted event via WebSocket
        create_background_task(
            manager.broadcast(
                f'group:{group_uuid}',
                {
                    'type': 'member_promoted',
                    'data': {
                        'group_id': str(group_uuid),
                        'promoted_user_id': str(member_uuid),
                        'promoted_user_name': member_name,
                    },
                },
            ),
            task_name=f'broadcast_member_promoted_{group_uuid}_{member_uuid}',
        )

        return SuccessResponse(
            code=MEMBER_PROMOTED,
            details={
                'group_id': group_id,
                'member_id': member_id,
                'member_name': member_name,
            },
        )

    async def _validate_member_removal_request(
        self, group_id: str, member_id: str, user: User
    ) -> tuple[UUID, UUID]:
        """Validate member removal request and return UUIDs.

        NOTE: This only validates permissions. The actual removal happens
        within a transaction in the calling method.

        Args:
            group_id: The group ID string
            member_id: The member ID string
            user: The requesting user

        Returns:
            Tuple of (group_uuid, member_uuid)

        Raises:
            BadRequestError: If validation fails
            NotFoundError: If group not found
            ForbiddenError: If not authorized
        """
        group_uuid = validate_uuid(group_id, 'Group')
        member_uuid = validate_uuid(member_id, 'Member')

        group = await self.group_repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        if not await self.group_repo.is_user_group_admin(group_uuid, user.id):
            logger.warning(
                'Non-admin user attempted to remove member',
                extra={'user_id': str(user.id), 'group_id': str(group_uuid)},
            )
            raise ForbiddenError(
                code=NOT_GROUP_ADMIN,
                message='Only group admins can remove members',
                group_id=str(group_uuid),
            )

        if await self.group_repo.is_user_group_admin(group_uuid, member_uuid):
            raise ForbiddenError(
                code=CANNOT_REMOVE_GROUP_ADMIN,
                message='Cannot remove group admins',
                group_id=str(group_uuid),
                user_id=str(member_uuid),
            )

        # Verify member exists in group
        members = await self.group_repo.get_group_members_with_admin_status(group_uuid)
        if not any(m['id'] == str(member_uuid) for m in members):
            raise BadRequestError(
                code=NOT_A_GROUP_MEMBER,
                message='User is not a member of this group',
                group_id=str(group_uuid),
                user_id=str(member_uuid),
            )

        return group_uuid, member_uuid

    async def _find_and_cancel_affected_runs(
        self, group_id: UUID, member_id: UUID
    ) -> tuple[list[str], list[str]]:
        """Remove member from group and find/cancel affected runs.

        NOTE: This method MUST be called within a transaction context.
        It performs multiple database modifications that need to be atomic.

        Args:
            group_id: The group UUID
            member_id: The member UUID

        Returns:
            Tuple of (affected_runs, cancelled_runs) as lists of run ID strings

        Raises:
            BadRequestError: If removal fails
        """
        # First, remove the member from the group
        success = await self.group_repo.remove_group_member(group_id, member_id)
        if not success:
            raise BadRequestError(
                code=GROUP_MEMBER_REMOVAL_FAILED,
                message='Failed to remove member from group',
                group_id=str(group_id),
                user_id=str(member_id),
            )

        # Now handle run participations and cancellations
        runs = await self.run_repo.get_runs_by_group(group_id)
        cancelled_runs = []
        affected_runs = []

        for run in runs:
            participations = await self.run_repo.get_run_participations(run.id)

            # Mark removed user's participation as removed and delete their bids from active runs
            user_participated = False
            user_participation_id = None
            for participation in participations:
                if participation.user_id == member_id:
                    participation.is_removed = True
                    user_participated = True
                    user_participation_id = participation.id

            if user_participated:
                affected_runs.append(str(run.id))

                # Delete all bids for this user in active runs (not completed/cancelled)
                if (
                    run.state not in [RunState.COMPLETED, RunState.CANCELLED]
                    and user_participation_id
                ):
                    bids = await self.bid_repo.get_bids_by_participation(user_participation_id)
                    for bid in bids:
                        await self.bid_repo.delete_bid(user_participation_id, bid.product_id)

                    logger.info(
                        f'Deleted {len(bids)} bids from active run',
                        extra={
                            'run_id': str(run.id),
                            'user_id': str(member_id),
                            'run_state': run.state,
                        },
                    )

            # Cancel run if removed user is leader and run is not completed
            leader = next((p for p in participations if p.is_leader), None)
            if leader and leader.user_id == member_id and run.state != RunState.COMPLETED:
                run.state = RunState.CANCELLED
                cancelled_runs.append(str(run.id))

        return affected_runs, cancelled_runs

    async def _broadcast_removal_notifications(
        self,
        group_id: UUID,
        member_id: UUID,
        affected_runs: list[str],
        cancelled_runs: list[str],
        is_self_removal: bool = False,
    ) -> None:
        """Emit member removal domain event and broadcast to group WebSocket.

        Args:
            group_id: The group UUID
            member_id: The member UUID
            affected_runs: List of affected run IDs
            cancelled_runs: List of cancelled run IDs
            is_self_removal: Whether this is a self-removal (leave) vs admin removal
        """
        # Get member info for the notification
        member = await self.user_repo.get_user_by_id(member_id)
        member_name = member.name if member else 'Unknown'

        # Emit domain event
        event_bus.emit(
            MemberRemovedEvent(
                group_id=group_id,
                user_id=member_id,
                removed_by_id=member_id,  # Should be admin_id
            )
        )

        # Broadcast to group WebSocket channel
        message_type = 'member_left' if is_self_removal else 'member_removed'
        user_id_field = 'user_id' if is_self_removal else 'removed_user_id'

        create_background_task(
            manager.broadcast(
                f'group:{group_id}',
                {
                    'type': message_type,
                    'data': {
                        'group_id': str(group_id),
                        user_id_field: str(member_id),
                        'user_name': member_name,
                    },
                },
            ),
            task_name=f'broadcast_{message_type}_{group_id}_{member_id}',
        )

        # Broadcast participant_removed events for all affected runs
        for run_id in affected_runs:
            create_background_task(
                manager.broadcast(
                    f'run:{run_id}',
                    {
                        'type': 'participant_removed',
                        'data': {'run_id': run_id, 'removed_user_id': str(member_id)},
                    },
                ),
                task_name=f'broadcast_participant_removed_{run_id}',
            )

        # Broadcast run_cancelled events for cancelled runs
        for run_id in cancelled_runs:
            create_background_task(
                manager.broadcast(
                    f'run:{run_id}',
                    {
                        'type': 'run_cancelled',
                        'data': {
                            'run_id': run_id,
                            'state': RunState.CANCELLED,
                            'new_state': RunState.CANCELLED,
                        },
                    },
                ),
                task_name=f'broadcast_run_cancelled_{run_id}',
            )
