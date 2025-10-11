"""Service layer for group-related business logic."""

from typing import Any
from uuid import UUID

from .base_service import BaseService
from ..exceptions import NotFoundError, ForbiddenError, BadRequestError
from ..models import User, Group
from ..config import MAX_GROUPS_PER_USER, MAX_MEMBERS_PER_GROUP
from ..run_state import RunState
from ..websocket_manager import manager
from ..request_context import get_logger
from ..schemas import (
    GroupResponse,
    CreateGroupResponse,
    GroupDetailResponse,
    RunResponse,
    RunSummary,
    RegenerateTokenResponse,
    PreviewGroupResponse,
    JoinGroupResponse,
    MessageResponse,
    ToggleJoiningResponse,
)

logger = get_logger(__name__)


class GroupService(BaseService):
    """Service for managing groups and group operations."""

    def get_user_groups(self, user: User) -> list[GroupResponse]:
        """
        Get all groups the user is a member of with run counts.

        Args:
            user: The user to get groups for

        Returns:
            List of GroupResponse with active/completed run counts
        """
        logger.debug(f"Fetching groups for user", extra={"user_id": str(user.id)})

        # Get groups where the user is a member
        groups = self.repo.get_user_groups(user)

        # Get all stores for lookups
        all_stores = self.repo.get_all_stores()
        store_lookup = {store.id: store.name for store in all_stores}

        # State ordering for sorting (reverse order: distributing > adjusting > shopping > confirmed > active > planning)
        state_order = {
            'distributing': 6,
            'adjusting': 5,
            'shopping': 4,
            'confirmed': 3,
            'active': 2,
            'planning': 1
        }

        # Convert to response format
        group_responses = []
        for group in groups:
            # Get runs for this group
            runs = self.repo.get_runs_by_group(group.id)
            active_runs = [run for run in runs if run.state not in (RunState.COMPLETED, RunState.CANCELLED)]
            completed_runs = [run for run in runs if run.state == RunState.COMPLETED]

            # Sort active runs by state (reverse state order)
            sorted_active_runs = sorted(active_runs, key=lambda r: state_order.get(r.state, 0), reverse=True)

            # Convert to run summary format
            active_runs_summary = [
                RunSummary(
                    id=str(run.id),
                    store_name=store_lookup.get(run.store_id, "Unknown Store"),
                    state=run.state
                )
                for run in sorted_active_runs
            ]

            from datetime import datetime
            group_responses.append(GroupResponse(
                id=str(group.id),
                name=group.name,
                description=f"Group created by {group.creator.name}" if group.creator else "Group",
                member_count=len(group.members),
                active_runs_count=len(active_runs),
                completed_runs_count=len(completed_runs),
                active_runs=active_runs_summary,
                created_at=datetime.now().isoformat()  # Not available in model yet
            ))

        return group_responses

    def create_group(self, name: str, user: User) -> CreateGroupResponse:
        """
        Create a new group and add the creator as a member.

        Args:
            name: The name of the group
            user: The user creating the group

        Returns:
            CreateGroupResponse with group information
        """
        logger.info(
            f"Creating group: {name}",
            extra={"user_id": str(user.id), "group_name": name}
        )

        # Create the group
        group = self.repo.create_group(name, user.id)

        # Add the creator as a member
        self.repo.add_group_member(group.id, user)

        logger.info(
            f"Group created successfully",
            extra={"user_id": str(user.id), "group_id": str(group.id)}
        )

        return CreateGroupResponse(
            id=str(group.id),
            name=group.name,
            member_count=1,
            active_runs_count=0,
            completed_runs_count=0,
            active_runs=[]
        )

    def get_group_details(self, group_id: str, user: User) -> GroupDetailResponse:
        """
        Get details of a specific group with authorization check.

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
        try:
            group_uuid = UUID(group_id)
        except ValueError:
            raise BadRequestError("Invalid group ID format")

        # Get the group
        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError("Group", group_uuid)

        # Check if user is a member of the group
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == group_uuid for g in user_groups):
            logger.warning(
                f"User attempted to access group they're not a member of",
                extra={"user_id": str(user.id), "group_id": str(group_uuid)}
            )
            raise ForbiddenError("Not a member of this group")

        # Get members and admin status
        members = self.repo.get_group_members_with_admin_status(group_uuid)
        is_current_user_admin = self.repo.is_user_group_admin(group_uuid, user.id)

        return GroupDetailResponse(
            id=str(group.id),
            name=group.name,
            invite_token=group.invite_token,
            is_joining_allowed=group.is_joining_allowed,
            members=members,
            is_current_user_admin=is_current_user_admin
        )

    def get_group_runs(self, group_id: str, user: User) -> list[RunResponse]:
        """
        Get all runs for a specific group with authorization check.

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
        try:
            group_uuid = UUID(group_id)
        except ValueError:
            raise BadRequestError("Invalid group ID format")

        # Get the group
        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError("Group", group_uuid)

        # Check if user is a member of the group
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == group_uuid for g in user_groups):
            raise ForbiddenError("Not a member of this group")

        # Get runs for the group
        logger.debug(
            f"Fetching runs for group",
            extra={"user_id": str(user.id), "group_id": str(group_uuid)}
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
            leader_name = leader.user.name if leader and leader.user else "Unknown"
            leader_is_removed = leader.is_removed if leader else False

            run_responses.append(RunResponse(
                id=str(run.id),
                group_id=str(run.group_id),
                store_id=str(run.store_id),
                store_name=store_lookup.get(run.store_id, "Unknown Store"),
                state=run.state,
                leader_name=leader_name,
                leader_is_removed=leader_is_removed,
                planned_on=run.planned_on.isoformat() if run.planned_on else None
            ))

        return run_responses

    def get_group_completed_cancelled_runs(self, group_id: str, user: User, limit: int = 10, offset: int = 0) -> list[RunResponse]:
        """
        Get completed and cancelled runs for a specific group with pagination.

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
        try:
            group_uuid = UUID(group_id)
        except ValueError:
            raise BadRequestError("Invalid group ID format")

        # Get the group
        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError("Group", group_uuid)

        # Check if user is a member of the group
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == group_uuid for g in user_groups):
            raise ForbiddenError("Not a member of this group")

        # Get paginated completed/cancelled runs for the group
        logger.debug(
            f"Fetching completed/cancelled runs for group",
            extra={"user_id": str(user.id), "group_id": str(group_uuid), "limit": limit, "offset": offset}
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
            leader_name = leader.user.name if leader and leader.user else "Unknown"

            run_responses.append(RunResponse(
                id=str(run.id),
                group_id=str(run.group_id),
                store_id=str(run.store_id),
                store_name=store_lookup.get(run.store_id, "Unknown Store"),
                state=run.state,
                leader_name=leader_name,
                leader_is_removed=False,
                planned_on=run.planned_on.isoformat() if run.planned_on else None
            ))

        return run_responses

    def regenerate_invite_token(self, group_id: str, user: User) -> RegenerateTokenResponse:
        """
        Regenerate the invite token for a group (only creator can do this).

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
        try:
            group_uuid = UUID(group_id)
        except ValueError:
            raise BadRequestError("Invalid group ID format")

        # Get the group
        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError("Group", group_uuid)

        # Check if user is the creator of the group
        if group.created_by != user.id:
            logger.warning(
                f"User attempted to regenerate invite token for group they don't own",
                extra={"user_id": str(user.id), "group_id": str(group_uuid)}
            )
            raise ForbiddenError("Only the group creator can regenerate the invite token")

        # Regenerate the token
        logger.info(
            f"Regenerating invite token for group",
            extra={"user_id": str(user.id), "group_id": str(group_uuid)}
        )
        new_token = self.repo.regenerate_group_invite_token(group_uuid)
        if not new_token:
            raise BadRequestError("Failed to regenerate invite token")

        return RegenerateTokenResponse(invite_token=new_token)

    def preview_group(self, invite_token: str) -> PreviewGroupResponse:
        """
        Preview group information by invite token without joining.

        Args:
            invite_token: The invite token to preview

        Returns:
            Dictionary with group preview information

        Raises:
            NotFoundError: If group with invite token doesn't exist
        """
        logger.debug(
            "Previewing group with invite token",
            extra={"invite_token": invite_token}
        )

        # Find the group by invite token
        group = self.repo.get_group_by_invite_token(invite_token)
        if not group:
            logger.warning(
                "Invalid invite token used for preview",
                extra={"invite_token": invite_token}
            )
            raise NotFoundError("Group", invite_token)

        return PreviewGroupResponse(
            id=str(group.id),
            name=group.name,
            member_count=len(group.members),
            creator_name=group.creator.name if group.creator else "Unknown"
        )

    def join_group(self, invite_token: str, user: User) -> JoinGroupResponse:
        """
        Join a group using an invite token.

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
            "User attempting to join group via invite",
            extra={"user_id": str(user.id), "invite_token": invite_token}
        )

        group = self._validate_group_invite(invite_token, user)
        self._check_membership_constraints(user, group)
        self._add_member_to_group_db(user, group)
        self._broadcast_member_joined(user, group)

        logger.info(
            "User joined group successfully",
            extra={"user_id": str(user.id), "group_id": str(group.id)}
        )

        return JoinGroupResponse(
            message="Successfully joined group",
            group_id=str(group.id),
            group_name=group.name
        )

    def _validate_group_invite(self, invite_token: str, user: User) -> Group:
        """Validate invite token and check if joining is allowed."""
        group = self.repo.get_group_by_invite_token(invite_token)
        if not group:
            logger.warning(
                "Invalid invite token used for join",
                extra={"user_id": str(user.id), "invite_token": invite_token}
            )
            raise NotFoundError("Group", invite_token)

        if not group.is_joining_allowed:
            logger.warning(
                "Attempted to join group with joining disabled",
                extra={"user_id": str(user.id), "group_id": str(group.id)}
            )
            raise ForbiddenError("This group is not accepting new members")

        return group

    def _check_membership_constraints(self, user: User, group: Group) -> None:
        """Check user/group limits and ensure user is not already a member."""
        user_groups = self.repo.get_user_groups(user)

        if any(g.id == group.id for g in user_groups):
            logger.info(
                "User already a member of group",
                extra={"user_id": str(user.id), "group_id": str(group.id)}
            )
            raise BadRequestError("Already a member of this group")

        if len(user_groups) >= MAX_GROUPS_PER_USER:
            logger.warning(
                "User attempted to join group but already at maximum groups",
                extra={"user_id": str(user.id), "group_id": str(group.id)}
            )
            raise BadRequestError(f"Cannot join more than {MAX_GROUPS_PER_USER} groups")

        if len(group.members) >= MAX_MEMBERS_PER_GROUP:
            logger.warning(
                "User attempted to join group but group is full",
                extra={"user_id": str(user.id), "group_id": str(group.id)}
            )
            raise BadRequestError(f"Group is full (maximum {MAX_MEMBERS_PER_GROUP} members)")

    def _add_member_to_group_db(self, user: User, group: Group) -> None:
        """Add user to the group in the database."""
        success = self.repo.add_group_member(group.id, user)
        if not success:
            logger.error(
                "Failed to add user to group",
                extra={"user_id": str(user.id), "group_id": str(group.id)}
            )
            raise BadRequestError("Failed to join group")

    def _broadcast_member_joined(self, user: User, group: Group) -> None:
        """Broadcast member_joined event to group room."""
        room_id = f"group:{group.id}"
        import asyncio
        asyncio.create_task(manager.broadcast(room_id, {
            "type": "member_joined",
            "data": {
                "group_id": str(group.id),
                "user_id": str(user.id),
                "user_name": user.name,
                "user_email": user.email
            }
        }))

    def get_group_members(self, group_id: str, user: User) -> GroupDetailResponse:
        """
        Get all members of a group with their admin status.

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
        try:
            group_uuid = UUID(group_id)
        except ValueError:
            raise BadRequestError("Invalid group ID format")

        # Get the group
        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError("Group", group_uuid)

        # Check if user is a member of the group
        user_groups = self.repo.get_user_groups(user)
        if not any(g.id == group_uuid for g in user_groups):
            raise ForbiddenError("Not a member of this group")

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
            is_current_user_admin=is_current_user_admin
        )

    def remove_member(self, group_id: str, member_id: str, user: User) -> MessageResponse:
        """
        Remove a member from a group (admin only).

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
        group_uuid, member_uuid = self._validate_member_removal_request(group_id, member_id, user)
        affected_runs, cancelled_runs = self._find_and_cancel_affected_runs(group_uuid, member_uuid)
        self._broadcast_removal_notifications(group_uuid, member_uuid, affected_runs, cancelled_runs)

        logger.info(
            f"Member removed from group, cancelled {len(cancelled_runs)} runs",
            extra={"user_id": str(user.id), "group_id": str(group_uuid), "removed_user_id": str(member_uuid), "cancelled_runs": cancelled_runs}
        )

        return MessageResponse(message="Member removed successfully")

    def _validate_member_removal_request(
        self, group_id: str, member_id: str, user: User
    ) -> tuple[UUID, UUID]:
        """Validate member removal request and return UUIDs."""
        try:
            group_uuid = UUID(group_id)
            member_uuid = UUID(member_id)
        except ValueError:
            raise BadRequestError("Invalid ID format")

        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError("Group", group_uuid)

        if not self.repo.is_user_group_admin(group_uuid, user.id):
            logger.warning(
                "Non-admin user attempted to remove member",
                extra={"user_id": str(user.id), "group_id": str(group_uuid)}
            )
            raise ForbiddenError("Only group admins can remove members")

        if self.repo.is_user_group_admin(group_uuid, member_uuid):
            raise ForbiddenError("Cannot remove group admins")

        success = self.repo.remove_group_member(group_uuid, member_uuid)
        if not success:
            raise BadRequestError("Failed to remove member")

        return group_uuid, member_uuid

    def _find_and_cancel_affected_runs(
        self, group_id: UUID, member_id: UUID
    ) -> tuple[list[str], list[str]]:
        """Find affected runs and cancel runs led by removed member."""
        runs = self.repo.get_runs_by_group(group_id)
        cancelled_runs = []
        affected_runs = []

        for run in runs:
            participations = self.repo.get_run_participations(run.id)

            # Mark removed user's participation as removed
            user_participated = False
            for participation in participations:
                if participation.user_id == member_id:
                    participation.is_removed = True
                    user_participated = True

            if user_participated:
                affected_runs.append(str(run.id))

            # Cancel run if removed user is leader and run is not completed
            leader = next((p for p in participations if p.is_leader), None)
            if leader and leader.user_id == member_id and run.state != RunState.COMPLETED:
                run.state = RunState.CANCELLED
                cancelled_runs.append(str(run.id))

        return affected_runs, cancelled_runs

    def _broadcast_removal_notifications(
        self, group_id: UUID, member_id: UUID, affected_runs: list[str], cancelled_runs: list[str]
    ) -> None:
        """Broadcast WebSocket notifications for member removal."""
        import asyncio

        # Broadcast to group room
        asyncio.create_task(manager.broadcast(f"group:{group_id}", {
            "type": "member_removed",
            "data": {
                "group_id": str(group_id),
                "removed_user_id": str(member_id),
                "cancelled_runs": cancelled_runs
            }
        }))

        # Broadcast participant_removed events for all affected runs
        for run_id in affected_runs:
            asyncio.create_task(manager.broadcast(f"run:{run_id}", {
                "type": "participant_removed",
                "data": {
                    "run_id": run_id,
                    "removed_user_id": str(member_id)
                }
            }))

        # Broadcast run_cancelled events for cancelled runs
        for run_id in cancelled_runs:
            asyncio.create_task(manager.broadcast(f"run:{run_id}", {
                "type": "run_cancelled",
                "data": {
                    "run_id": run_id,
                    "state": "cancelled",
                    "new_state": "cancelled"
                }
            }))

    def toggle_joining_allowed(self, group_id: str, user: User) -> ToggleJoiningResponse:
        """
        Toggle whether a group allows joining via invite link (admin only).

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
        try:
            group_uuid = UUID(group_id)
        except ValueError:
            raise BadRequestError("Invalid group ID format")

        # Get the group
        group = self.repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError("Group", group_uuid)

        # Check if user is a group admin
        if not self.repo.is_user_group_admin(group_uuid, user.id):
            logger.warning(
                f"Non-admin user attempted to toggle joining allowed",
                extra={"user_id": str(user.id), "group_id": str(group_uuid)}
            )
            raise ForbiddenError("Only group admins can change joining settings")

        # Toggle the setting
        new_value = not group.is_joining_allowed
        updated_group = self.repo.update_group_joining_allowed(group_uuid, new_value)
        if not updated_group:
            raise BadRequestError("Failed to update joining setting")

        logger.info(
            f"Group joining setting toggled",
            extra={"user_id": str(user.id), "group_id": str(group_uuid), "is_joining_allowed": new_value}
        )

        return ToggleJoiningResponse(is_joining_allowed=new_value)
