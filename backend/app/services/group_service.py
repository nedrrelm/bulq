"""Service layer for group-related business logic."""

from uuid import UUID

from app.api.schemas import (
    CreateGroupResponse,
    GroupDetailResponse,
    GroupResponse,
    JoinGroupResponse,
    PreviewGroupResponse,
    RegenerateTokenResponse,
    RunResponse,
    RunSummary,
    SuccessResponse,
    ToggleJoiningResponse,
)
from app.api.websocket_manager import manager
from app.core.error_codes import (
    ALREADY_GROUP_MEMBER,
    CANNOT_REMOVE_GROUP_ADMIN,
    GROUP_INVITE_TOKEN_REGENERATION_FAILED,
    GROUP_JOIN_FAILED,
    GROUP_JOINING_DISABLED,
    GROUP_JOINING_SETTING_UPDATE_FAILED,
    GROUP_MAX_MEMBERS_EXCEEDED,
    GROUP_MEMBER_PROMOTION_FAILED,
    GROUP_MEMBER_REMOVAL_FAILED,
    GROUP_NOT_FOUND,
    LAST_ADMIN_CANNOT_LEAVE,
    NOT_A_GROUP_MEMBER,
    NOT_GROUP_ADMIN,
    NOT_GROUP_MEMBER,
    USER_ALREADY_GROUP_ADMIN,
    USER_MAX_GROUPS_EXCEEDED,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import Group, User
from app.core.run_state import RunState
from app.core.success_codes import GROUP_JOINED, GROUP_LEFT, MEMBER_PROMOTED, MEMBER_REMOVED
from app.events.domain_events import MemberJoinedEvent, MemberRemovedEvent
from app.events.event_bus import event_bus
from app.infrastructure.config import MAX_GROUPS_PER_USER, MAX_MEMBERS_PER_GROUP
from app.infrastructure.request_context import get_logger
from app.infrastructure.transaction import transaction
from app.utils.background_tasks import create_background_task
from app.utils.validation import validate_uuid

from .base_service import BaseService

logger = get_logger(__name__)


class GroupService(BaseService):
    """Service for managing groups and group operations."""

    def get_user_groups(self, user: User) -> list[GroupResponse]:
        """Get all groups the user is a member of with run counts.

        Args:
            user: The user to get groups for

        Returns:
            List of GroupResponse with active/completed run counts
        """
        logger.debug('Fetching groups for user', extra={'user_id': str(user.id)})

        # Get groups where the user is a member
        groups = self.repo.get_user_groups(user)

        # Get all stores for lookups
        all_stores = self.repo.get_all_stores()
        store_lookup = {store.id: store.name for store in all_stores}

        # State ordering for sorting (reverse order: distributing > adjusting > shopping > confirmed > active > planning)
        state_order = {
            RunState.DISTRIBUTING: 6,
            RunState.ADJUSTING: 5,
            RunState.SHOPPING: 4,
            RunState.CONFIRMED: 3,
            RunState.ACTIVE: 2,
            RunState.PLANNING: 1,
        }

        # Convert to response format
        group_responses = []
        for group in groups:
            # Get runs for this group
            runs = self.repo.get_runs_by_group(group.id)
            active_runs = [
                run for run in runs if run.state not in (RunState.COMPLETED, RunState.CANCELLED)
            ]
            completed_runs = [run for run in runs if run.state == RunState.COMPLETED]

            # Sort active runs by state (reverse state order)
            sorted_active_runs = sorted(
                active_runs, key=lambda r: state_order.get(r.state, 0), reverse=True
            )

            # Convert to run summary format
            active_runs_summary = [
                RunSummary(
                    id=str(run.id),
                    store_name=store_lookup.get(run.store_id, 'Unknown Store'),
                    state=run.state,
                )
                for run in sorted_active_runs
            ]

            group_responses.append(
                GroupResponse(
                    id=str(group.id),
                    name=group.name,
                    description=f'Group created by {group.creator.name}'
                    if group.creator
                    else 'Group',
                    member_count=len(group.members),
                    active_runs_count=len(active_runs),
                    completed_runs_count=len(completed_runs),
                    active_runs=active_runs_summary,
                    created_at=group.created_at.isoformat() if group.created_at else '',
                )
            )

        return group_responses

    def create_group(self, name: str, user: User) -> CreateGroupResponse:
        """Create a new group and add the creator as an admin member.

        Args:
            name: The name of the group
            user: The user creating the group

        Returns:
            CreateGroupResponse with group information
        """
        logger.info(f'Creating group: {name}', extra={'user_id': str(user.id), 'group_name': name})

        # Create the group
        group = self.repo.create_group(name, user.id)

        # Add the creator as an admin member
        self.repo.add_group_member(group.id, user, is_group_admin=True)

        logger.info(
            'Group created successfully', extra={'user_id': str(user.id), 'group_id': str(group.id)}
        )

        return CreateGroupResponse(
            id=str(group.id),
            name=group.name,
            member_count=1,
            active_runs_count=0,
            completed_runs_count=0,
            active_runs=[],
        )

    def get_group_details(self, group_id: str, user: User) -> GroupDetailResponse:
        """Get details of a specific group with authorization check.

        Args:
            group_id: The UUID string of the group
            user: The requesting user

        Returns:
            GroupDetailResponse with group details

        Raises:
            BadRequestError: If group ID format is invalid
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not a member of the group
        """
        # Verify group ID format
        group_uuid = validate_uuid(group_id, 'Group')

        # Get the group
        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        # Check if user is a member of the group
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == group_uuid for g in user_groups):
            logger.warning(
                "User attempted to access group they're not a member of",
                extra={'user_id': str(user.id), 'group_id': str(group_uuid)},
            )
            raise ForbiddenError(
                code=NOT_GROUP_MEMBER,
                message='Not a member of this group',
                group_id=str(group_uuid),
            )

        # Get members and admin status
        members = self.repo.get_group_members_with_admin_status(group_uuid)
        is_current_user_admin = self.repo.is_user_group_admin(group_uuid, user.id)

        return GroupDetailResponse(
            id=str(group.id),
            name=group.name,
            invite_token=group.invite_token,
            is_joining_allowed=group.is_joining_allowed,
            members=members,
            is_current_user_admin=is_current_user_admin,
        )

    def get_group_runs(self, group_id: str, user: User) -> list[RunResponse]:
        """Get all runs for a specific group with authorization check.

        Args:
            group_id: The UUID string of the group
            user: The requesting user

        Returns:
            List of RunResponse with store names

        Raises:
            BadRequestError: If group ID format is invalid
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not a member of the group
        """
        # Verify group ID format
        group_uuid = validate_uuid(group_id, 'Group')

        # Get the group
        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        # Check if user is a member of the group
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == group_uuid for g in user_groups):
            raise ForbiddenError(
                code=NOT_GROUP_MEMBER,
                message='Not a member of this group',
                group_id=str(group_uuid),
            )

        # Get runs for the group
        logger.debug(
            'Fetching runs for group', extra={'user_id': str(user.id), 'group_id': str(group_uuid)}
        )
        runs = self.repo.get_runs_by_group(group_uuid)

        # Convert to response format with store names
        all_stores = self.repo.get_all_stores()
        store_lookup = {store.id: store.name for store in all_stores}

        run_responses = []
        for run in runs:
            # Get leader from participations
            participations = self.repo.get_run_participations(run.id)
            leader = next((p for p in participations if p.is_leader), None)
            leader_name = leader.user.name if leader and leader.user else 'Unknown'
            leader_is_removed = leader.is_removed if leader else False

            run_responses.append(
                RunResponse(
                    id=str(run.id),
                    group_id=str(run.group_id),
                    store_id=str(run.store_id),
                    store_name=store_lookup.get(run.store_id, 'Unknown Store'),
                    state=run.state,
                    leader_name=leader_name,
                    leader_is_removed=leader_is_removed,
                    planned_on=run.planned_on.isoformat() if run.planned_on else None,
                )
            )

        return run_responses

    def get_group_completed_cancelled_runs(
        self, group_id: str, user: User, limit: int = 10, offset: int = 0
    ) -> list[RunResponse]:
        """Get completed and cancelled runs for a specific group with pagination.

        Args:
            group_id: The UUID string of the group
            user: The requesting user
            limit: Maximum number of runs to return (default 10)
            offset: Number of runs to skip (default 0)

        Returns:
            List of run dictionaries with store names

        Raises:
            BadRequestError: If group ID format is invalid
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not a member of the group
        """
        # Verify group ID format
        group_uuid = validate_uuid(group_id, 'Group')

        # Get the group
        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        # Check if user is a member of the group
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == group_uuid for g in user_groups):
            raise ForbiddenError(
                code=NOT_GROUP_MEMBER,
                message='Not a member of this group',
                group_id=str(group_uuid),
            )

        # Get paginated completed/cancelled runs for the group
        logger.debug(
            'Fetching completed/cancelled runs for group',
            extra={
                'user_id': str(user.id),
                'group_id': str(group_uuid),
                'limit': limit,
                'offset': offset,
            },
        )
        runs = self.repo.get_completed_cancelled_runs_by_group(group_uuid, limit, offset)

        # Convert to response format with store names
        all_stores = self.repo.get_all_stores()
        store_lookup = {store.id: store.name for store in all_stores}

        run_responses = []
        for run in runs:
            # Get leader from participations
            participations = self.repo.get_run_participations(run.id)
            leader = next((p for p in participations if p.is_leader), None)
            leader_name = leader.user.name if leader and leader.user else 'Unknown'

            run_responses.append(
                RunResponse(
                    id=str(run.id),
                    group_id=str(run.group_id),
                    store_id=str(run.store_id),
                    store_name=store_lookup.get(run.store_id, 'Unknown Store'),
                    state=run.state,
                    leader_name=leader_name,
                    leader_is_removed=False,
                    planned_on=run.planned_on.isoformat() if run.planned_on else None,
                )
            )

        return run_responses

    def regenerate_invite_token(self, group_id: str, user: User) -> RegenerateTokenResponse:
        """Regenerate the invite token for a group (only creator can do this).

        Args:
            group_id: The UUID string of the group
            user: The requesting user (must be creator)

        Returns:
            Dictionary with new invite token

        Raises:
            BadRequestError: If group ID format is invalid
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not the group creator
        """
        # Verify group ID format
        group_uuid = validate_uuid(group_id, 'Group')

        # Get the group
        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        # Check if user is the creator of the group
        if group.created_by != user.id:
            logger.warning(
                "User attempted to regenerate invite token for group they don't own",
                extra={'user_id': str(user.id), 'group_id': str(group_uuid)},
            )
            raise ForbiddenError(
                code=NOT_GROUP_ADMIN,
                message='Only the group creator can regenerate the invite token',
                group_id=str(group_uuid),
            )

        # Regenerate the token
        logger.info(
            'Regenerating invite token for group',
            extra={'user_id': str(user.id), 'group_id': str(group_uuid)},
        )
        new_token = self.repo.regenerate_group_invite_token(group_uuid)
        if not new_token:
            raise BadRequestError(
                code=GROUP_INVITE_TOKEN_REGENERATION_FAILED,
                message='Failed to regenerate invite token',
                group_id=str(group_uuid),
            )

        return RegenerateTokenResponse(invite_token=new_token)

    def preview_group(self, invite_token: str) -> PreviewGroupResponse:
        """Preview group information by invite token without joining.

        Args:
            invite_token: The invite token to preview

        Returns:
            Dictionary with group preview information

        Raises:
            NotFoundError: If group with invite token doesn't exist
        """
        logger.debug('Previewing group with invite token', extra={'invite_token': invite_token})

        # Find the group by invite token
        group = self.repo.get_group_by_invite_token(invite_token)
        if not group:
            logger.warning(
                'Invalid invite token used for preview', extra={'invite_token': invite_token}
            )
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', invite_token=invite_token
            )

        return PreviewGroupResponse(
            id=str(group.id),
            name=group.name,
            member_count=len(group.members),
            creator_name=group.creator.name if group.creator else 'Unknown',
        )

    def join_group(self, invite_token: str, user: User) -> JoinGroupResponse:
        """Join a group using an invite token.

        Args:
            invite_token: The invite token to use
            user: The user joining the group

        Returns:
            Dictionary with success message and group info

        Raises:
            NotFoundError: If group with invite token doesn't exist
            BadRequestError: If user is already a member or join fails
        """
        logger.info(
            'User attempting to join group via invite',
            extra={'user_id': str(user.id), 'invite_token': invite_token},
        )

        group = self._validate_group_invite(invite_token, user)
        self._check_membership_constraints(user, group)
        self._add_member_to_group_db(user, group)
        self._broadcast_member_joined(user, group)

        logger.info(
            'User joined group successfully',
            extra={'user_id': str(user.id), 'group_id': str(group.id)},
        )

        return JoinGroupResponse(code=GROUP_JOINED, group_id=str(group.id), group_name=group.name)

    def _validate_group_invite(self, invite_token: str, user: User) -> Group:
        """Validate invite token and check if joining is allowed."""
        group = self.repo.get_group_by_invite_token(invite_token)
        if not group:
            logger.warning(
                'Invalid invite token used for join',
                extra={'user_id': str(user.id), 'invite_token': invite_token},
            )
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', invite_token=invite_token
            )

        if not group.is_joining_allowed:
            logger.warning(
                'Attempted to join group with joining disabled',
                extra={'user_id': str(user.id), 'group_id': str(group.id)},
            )
            raise ForbiddenError(
                code=GROUP_JOINING_DISABLED,
                message='This group is not accepting new members',
                group_id=str(group.id),
            )

        return group

    def _check_membership_constraints(self, user: User, group: Group) -> None:
        """Check user/group limits and ensure user is not already a member."""
        user_groups = self.repo.get_user_groups(user)

        if any(g.id == group.id for g in user_groups):
            logger.info(
                'User already a member of group',
                extra={'user_id': str(user.id), 'group_id': str(group.id)},
            )
            raise BadRequestError(
                code=ALREADY_GROUP_MEMBER,
                message='Already a member of this group',
                group_id=str(group.id),
            )

        if len(user_groups) >= MAX_GROUPS_PER_USER:
            logger.warning(
                'User attempted to join group but already at maximum groups',
                extra={'user_id': str(user.id), 'group_id': str(group.id)},
            )
            raise BadRequestError(
                code=USER_MAX_GROUPS_EXCEEDED,
                message=f'Cannot join more than {MAX_GROUPS_PER_USER} groups',
                max_groups=MAX_GROUPS_PER_USER,
                current_groups=len(user_groups),
            )

        if len(group.members) >= MAX_MEMBERS_PER_GROUP:
            logger.warning(
                'User attempted to join group but group is full',
                extra={'user_id': str(user.id), 'group_id': str(group.id)},
            )
            raise BadRequestError(
                code=GROUP_MAX_MEMBERS_EXCEEDED,
                message=f'Group is full (maximum {MAX_MEMBERS_PER_GROUP} members)',
                max_members=MAX_MEMBERS_PER_GROUP,
                current_members=len(group.members),
            )

    def _add_member_to_group_db(self, user: User, group: Group) -> None:
        """Add user to the group in the database."""
        success = self.repo.add_group_member(group.id, user)
        if not success:
            logger.error(
                'Failed to add user to group',
                extra={'user_id': str(user.id), 'group_id': str(group.id)},
            )
            raise BadRequestError(
                code=GROUP_JOIN_FAILED, message='Failed to join group', group_id=str(group.id)
            )

    def _broadcast_member_joined(self, user: User, group: Group) -> None:
        """Emit member_joined domain event."""
        event_bus.emit(MemberJoinedEvent(group_id=group.id, user_id=user.id, user_name=user.name))

    def get_group_members(self, group_id: str, user: User) -> GroupDetailResponse:
        """Get all members of a group with their admin status.

        Args:
            group_id: The UUID string of the group
            user: The requesting user

        Returns:
            Dictionary with group info and member list

        Raises:
            BadRequestError: If group ID format is invalid
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not a member of the group
        """
        # Verify group ID format
        group_uuid = validate_uuid(group_id, 'Group')

        # Get the group
        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        # Check if user is a member of the group
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == group_uuid for g in user_groups):
            raise ForbiddenError(
                code=NOT_GROUP_MEMBER,
                message='Not a member of this group',
                group_id=str(group_uuid),
            )

        # Get members with admin status
        members = self.repo.get_group_members_with_admin_status(group_uuid)

        # Check if current user is admin
        is_current_user_admin = self.repo.is_user_group_admin(group_uuid, user.id)

        return GroupDetailResponse(
            id=str(group.id),
            name=group.name,
            invite_token=group.invite_token,
            is_joining_allowed=group.is_joining_allowed,
            members=members,
            is_current_user_admin=is_current_user_admin,
        )

    def remove_member(self, group_id: str, member_id: str, user: User) -> SuccessResponse:
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
            Dictionary with success message

        Raises:
            BadRequestError: If ID formats are invalid
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not a group admin or trying to remove admin
        """
        # Validate outside transaction to fail fast on bad input
        group_uuid, member_uuid = self._validate_member_removal_request(group_id, member_id, user)

        # Wrap all database modifications in a transaction
        with transaction(self.db, 'remove group member and cancel runs'):
            affected_runs, cancelled_runs = self._find_and_cancel_affected_runs(
                group_uuid, member_uuid
            )

        # Broadcast notifications after successful transaction
        self._broadcast_removal_notifications(
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

    def _validate_member_removal_request(
        self, group_id: str, member_id: str, user: User
    ) -> tuple[UUID, UUID]:
        """Validate member removal request and return UUIDs.

        NOTE: This only validates permissions. The actual removal happens
        within a transaction in the calling method.
        """
        group_uuid = validate_uuid(group_id, 'Group')
        member_uuid = validate_uuid(member_id, 'Member')

        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        if not self.repo.is_user_group_admin(group_uuid, user.id):
            logger.warning(
                'Non-admin user attempted to remove member',
                extra={'user_id': str(user.id), 'group_id': str(group_uuid)},
            )
            raise ForbiddenError(
                code=NOT_GROUP_ADMIN,
                message='Only group admins can remove members',
                group_id=str(group_uuid),
            )

        if self.repo.is_user_group_admin(group_uuid, member_uuid):
            raise ForbiddenError(
                code=CANNOT_REMOVE_GROUP_ADMIN,
                message='Cannot remove group admins',
                group_id=str(group_uuid),
                user_id=str(member_uuid),
            )

        # Verify member exists in group
        members = self.repo.get_group_members_with_admin_status(group_uuid)
        if not any(m['id'] == str(member_uuid) for m in members):
            raise BadRequestError(
                code=NOT_A_GROUP_MEMBER,
                message='User is not a member of this group',
                group_id=str(group_uuid),
                user_id=str(member_uuid),
            )

        return group_uuid, member_uuid

    def _find_and_cancel_affected_runs(
        self, group_id: UUID, member_id: UUID
    ) -> tuple[list[str], list[str]]:
        """Remove member from group and find/cancel affected runs.

        NOTE: This method MUST be called within a transaction context.
        It performs multiple database modifications that need to be atomic.
        """
        # First, remove the member from the group
        success = self.repo.remove_group_member(group_id, member_id)
        if not success:
            raise BadRequestError(
                code=GROUP_MEMBER_REMOVAL_FAILED,
                message='Failed to remove member from group',
                group_id=str(group_id),
                user_id=str(member_id),
            )

        # Now handle run participations and cancellations
        runs = self.repo.get_runs_by_group(group_id)
        cancelled_runs = []
        affected_runs = []

        for run in runs:
            participations = self.repo.get_run_participations(run.id)

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
                    bids = self.repo.get_bids_by_participation(user_participation_id)
                    for bid in bids:
                        self.repo.delete_bid(user_participation_id, bid.product_id)

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

    def _broadcast_removal_notifications(
        self,
        group_id: UUID,
        member_id: UUID,
        affected_runs: list[str],
        cancelled_runs: list[str],
        is_self_removal: bool = False,
    ) -> None:
        """Emit member removal domain event and broadcast to group WebSocket."""
        # Get member info for the notification
        member = self.repo.get_user_by_id(member_id)
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

    def leave_group(self, group_id: str, user: User) -> SuccessResponse:
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
            Dictionary with success message

        Raises:
            BadRequestError: If ID format is invalid or user is group admin
            NotFoundError: If group doesn't exist
        """
        group_uuid = validate_uuid(group_id, 'Group')

        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        # Check if user is a member
        members = self.repo.get_group_members_with_admin_status(group_uuid)
        if not any(m['id'] == str(user.id) for m in members):
            raise BadRequestError(
                code=NOT_A_GROUP_MEMBER,
                message='You are not a member of this group',
                group_id=str(group_uuid),
            )

        # Count how many admins there are
        admin_count = sum(1 for m in members if m['is_group_admin'])

        # Prevent the last admin from leaving
        if self.repo.is_user_group_admin(group_uuid, user.id) and admin_count <= 1:
            raise ForbiddenError(
                code=LAST_ADMIN_CANNOT_LEAVE,
                message='You are the only admin. Please promote another member to admin before leaving.',
                group_id=str(group_uuid),
            )

        # Wrap all database modifications in a transaction
        with transaction(self.db, 'leave group and cancel runs'):
            affected_runs, cancelled_runs = self._find_and_cancel_affected_runs(group_uuid, user.id)

        # Broadcast notifications after successful transaction
        self._broadcast_removal_notifications(
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

    def promote_member_to_admin(self, group_id: str, member_id: str, user: User) -> SuccessResponse:
        """Promote a member to group admin (admin only).

        Args:
            group_id: The UUID string of the group
            member_id: The UUID string of the member to promote
            user: The requesting user (must be group admin)

        Returns:
            Dictionary with success message

        Raises:
            BadRequestError: If ID formats are invalid or member doesn't exist
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not a group admin
        """
        group_uuid = validate_uuid(group_id, 'Group')
        member_uuid = validate_uuid(member_id, 'Member')

        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        # Check if requester is admin
        if not self.repo.is_user_group_admin(group_uuid, user.id):
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
        members = self.repo.get_group_members_with_admin_status(group_uuid)
        member_exists = any(m['id'] == str(member_uuid) for m in members)

        if not member_exists:
            raise BadRequestError(
                code=NOT_A_GROUP_MEMBER,
                message='User is not a member of this group',
                group_id=str(group_uuid),
                user_id=str(member_uuid),
            )

        # Check if member is already an admin
        if self.repo.is_user_group_admin(group_uuid, member_uuid):
            raise BadRequestError(
                code=USER_ALREADY_GROUP_ADMIN,
                message='User is already a group admin',
                group_id=str(group_uuid),
                user_id=str(member_uuid),
            )

        # Promote the member
        success = self.repo.set_group_member_admin(group_uuid, member_uuid, True)

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

    def toggle_joining_allowed(self, group_id: str, user: User) -> ToggleJoiningResponse:
        """Toggle whether a group allows joining via invite link (admin only).

        Args:
            group_id: The UUID string of the group
            user: The requesting user (must be group admin)

        Returns:
            Dictionary with new joining status

        Raises:
            BadRequestError: If group ID format is invalid
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not a group admin
        """
        # Verify group ID format
        group_uuid = validate_uuid(group_id, 'Group')

        # Get the group
        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        # Check if user is a group admin
        if not self.repo.is_user_group_admin(group_uuid, user.id):
            logger.warning(
                'Non-admin user attempted to toggle joining allowed',
                extra={'user_id': str(user.id), 'group_id': str(group_uuid)},
            )
            raise ForbiddenError(
                code=NOT_GROUP_ADMIN,
                message='Only group admins can change joining settings',
                group_id=str(group_uuid),
            )

        # Toggle the setting
        new_value = not group.is_joining_allowed
        updated_group = self.repo.update_group_joining_allowed(group_uuid, new_value)
        if not updated_group:
            raise BadRequestError(
                code=GROUP_JOINING_SETTING_UPDATE_FAILED,
                message='Failed to update joining setting',
                group_id=str(group_uuid),
            )

        logger.info(
            'Group joining setting toggled',
            extra={
                'user_id': str(user.id),
                'group_id': str(group_uuid),
                'is_joining_allowed': new_value,
            },
        )

        return ToggleJoiningResponse(is_joining_allowed=new_value)
