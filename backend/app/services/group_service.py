"""Service layer for group-related business logic."""

import logging
import uuid
from typing import List, Dict, Any
from uuid import UUID

from .base_service import BaseService
from ..exceptions import NotFoundError, ForbiddenError, BadRequestError
from ..models import User

logger = logging.getLogger(__name__)


class GroupService(BaseService):
    """Service for managing groups and group operations."""

    def get_user_groups(self, user: User) -> List[Dict[str, Any]]:
        """
        Get all groups the user is a member of with run counts.

        Args:
            user: The user to get groups for

        Returns:
            List of group dictionaries with active/completed run counts
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
            active_runs = [run for run in runs if run.state not in ('completed', 'cancelled')]
            completed_runs = [run for run in runs if run.state == 'completed']

            # Sort active runs by state (reverse state order)
            sorted_active_runs = sorted(active_runs, key=lambda r: state_order.get(r.state, 0), reverse=True)

            # Convert to run summary format
            active_runs_summary = [
                {
                    "id": str(run.id),
                    "store_name": store_lookup.get(run.store_id, "Unknown Store"),
                    "state": run.state
                }
                for run in sorted_active_runs
            ]

            group_responses.append({
                "id": str(group.id),
                "name": group.name,
                "description": f"Group created by {group.creator.name}" if group.creator else "Group",
                "member_count": len(group.members),
                "active_runs_count": len(active_runs),
                "completed_runs_count": len(completed_runs),
                "active_runs": active_runs_summary,
                "created_at": None  # Not available in model yet
            })

        return group_responses

    def create_group(self, name: str, user: User) -> Dict[str, Any]:
        """
        Create a new group and add the creator as a member.

        Args:
            name: The name of the group
            user: The user creating the group

        Returns:
            Dictionary with group information
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

        return {
            "id": str(group.id),
            "name": group.name,
            "member_count": 1,
            "active_runs_count": 0,
            "completed_runs_count": 0,
            "active_runs": []
        }

    def get_group_details(self, group_id: str, user: User) -> Dict[str, Any]:
        """
        Get details of a specific group with authorization check.

        Args:
            group_id: The UUID string of the group
            user: The requesting user

        Returns:
            Dictionary with group details

        Raises:
            BadRequestError: If group ID format is invalid
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not a member of the group
        """
        # Verify group ID format
        try:
            group_uuid = uuid.UUID(group_id)
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

        return {
            "id": str(group.id),
            "name": group.name,
            "invite_token": group.invite_token
        }

    def get_group_runs(self, group_id: str, user: User) -> List[Dict[str, Any]]:
        """
        Get all runs for a specific group with authorization check.

        Args:
            group_id: The UUID string of the group
            user: The requesting user

        Returns:
            List of run dictionaries with store names

        Raises:
            BadRequestError: If group ID format is invalid
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not a member of the group
        """
        # Verify group ID format
        try:
            group_uuid = uuid.UUID(group_id)
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

            run_responses.append({
                "id": str(run.id),
                "group_id": str(run.group_id),
                "store_id": str(run.store_id),
                "store_name": store_lookup.get(run.store_id, "Unknown Store"),
                "state": run.state,
                "leader_name": leader_name,
                "planned_on": run.planned_on.isoformat() if run.planned_on else None
            })

        return run_responses

    def regenerate_invite_token(self, group_id: str, user: User) -> Dict[str, str]:
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
            group_uuid = uuid.UUID(group_id)
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

        return {
            "invite_token": new_token
        }

    def preview_group(self, invite_token: str) -> Dict[str, Any]:
        """
        Preview group information by invite token without joining.

        Args:
            invite_token: The invite token to preview

        Returns:
            Dictionary with group preview information

        Raises:
            NotFoundError: If group with invite token doesn't exist
        """
        logger.debug(f"Previewing group with invite token")

        # Find the group by invite token
        group = self.repo.get_group_by_invite_token(invite_token)
        if not group:
            logger.warning(f"Invalid invite token used for preview")
            raise NotFoundError("Group", invite_token)

        return {
            "id": str(group.id),
            "name": group.name,
            "member_count": len(group.members),
            "creator_name": group.creator.name if group.creator else "Unknown"
        }

    def join_group(self, invite_token: str, user: User) -> Dict[str, str]:
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
            f"User attempting to join group via invite",
            extra={"user_id": str(user.id)}
        )

        # Find the group by invite token
        group = self.repo.get_group_by_invite_token(invite_token)
        if not group:
            logger.warning(f"Invalid invite token used for join")
            raise NotFoundError("Group", invite_token)

        # Check if user is already a member
        user_groups = self.repo.get_user_groups(user)
        if any(g.id == group.id for g in user_groups):
            logger.info(
                f"User already a member of group",
                extra={"user_id": str(user.id), "group_id": str(group.id)}
            )
            raise BadRequestError("Already a member of this group")

        # Add user to the group
        success = self.repo.add_group_member(group.id, user)
        if not success:
            logger.error(
                f"Failed to add user to group",
                extra={"user_id": str(user.id), "group_id": str(group.id)}
            )
            raise BadRequestError("Failed to join group")

        logger.info(
            f"User joined group successfully",
            extra={"user_id": str(user.id), "group_id": str(group.id)}
        )

        return {
            "message": "Successfully joined group",
            "group_id": str(group.id),
            "group_name": group.name
        }
