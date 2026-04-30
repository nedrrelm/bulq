"""Service for group read-only query operations."""

from sqlalchemy.orm import Session

from app.api.schemas import GroupDetailResponse, GroupResponse, RunResponse, RunSummary
from app.core.error_codes import GROUP_NOT_FOUND, NOT_GROUP_MEMBER
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.models import User
from app.core.run_state import RunState
from app.infrastructure.request_context import get_logger
from app.repositories import (
    get_group_repository,
    get_run_repository,
    get_store_repository,
    get_user_repository,
)
from app.utils.validation import validate_uuid

from .base_service import BaseService

logger = get_logger(__name__)


class GroupQueryService(BaseService):
    """Service for read-only group query operations.

    This service handles all read operations for groups including:
    - Getting user's groups with run summaries
    - Getting group details and members
    - Getting group runs (active and historical)

    All methods are read-only and do not modify state.
    """

    def __init__(self, db: Session):
        """Initialize service with necessary repositories."""
        super().__init__(db)
        self.group_repo = get_group_repository(db)
        self.run_repo = get_run_repository(db)
        self.store_repo = get_store_repository(db)
        self.user_repo = get_user_repository(db)

    def _get_run_store_name(self, run) -> str:
        """Get store name from run, handling both database and memory repositories.

        For database repository: Uses already-joined store relationship
        For memory repository: Fetches store by ID via BaseService._get_store_name

        Args:
            run: Run object with store_id

        Returns:
            Store name or 'Unknown Store' if not found
        """
        try:
            # Try to access joined store (works for database repository)
            if hasattr(run, 'store') and run.store is not None:
                return run.store.name
        except AttributeError:
            pass

        # Fallback: fetch store by ID (for memory repository or unjoined data)
        return self._get_store_name(run.store_id)

    def get_user_groups(self, user: User) -> list[GroupResponse]:
        """Get all groups the user is a member of with run counts.

        Args:
            user: The user to get groups for

        Returns:
            List of GroupResponse with active/completed run counts
        """
        logger.debug('Fetching groups for user', extra={'user_id': str(user.id)})

        # Get groups where the user is a member
        groups = self.user_repo.get_user_groups(user)

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
            runs = self.run_repo.get_runs_by_group(group.id)
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
                    store_name=self._get_run_store_name(run),
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
        group = self.group_repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        # Check if user is a member of the group
        if not self._is_group_member(user, group_uuid):
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
        members = self.group_repo.get_group_members_with_admin_status(group_uuid)
        is_current_user_admin = self.group_repo.is_user_group_admin(group_uuid, user.id)

        return GroupDetailResponse(
            id=str(group.id),
            name=group.name,
            invite_token=group.invite_token,
            is_joining_allowed=group.is_joining_allowed,
            members=members,
            is_current_user_admin=is_current_user_admin,
        )

    def get_group_members(self, group_id: str, user: User) -> GroupDetailResponse:
        """Get members of a specific group (alias for get_group_details).

        Args:
            group_id: The UUID string of the group
            user: The requesting user

        Returns:
            GroupDetailResponse with group details and members

        Raises:
            BadRequestError: If group ID format is invalid
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not a member of the group
        """
        return self.get_group_details(group_id, user)

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
        group = self.group_repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        # Check if user is a member of the group
        self._verify_group_membership(
            user,
            group_uuid,
            NOT_GROUP_MEMBER,
            'Not a member of this group',
            group_id=str(group_uuid),
        )

        # Get runs for the group
        logger.debug(
            'Fetching runs for group', extra={'user_id': str(user.id), 'group_id': str(group_uuid)}
        )
        runs = self.run_repo.get_runs_by_group(group_uuid)

        # Convert to response format with store names
        run_responses = []
        for run in runs:
            # Get leader from participations
            participations = self.run_repo.get_run_participations(run.id)
            leader = next((p for p in participations if p.is_leader), None)
            leader_name = leader.user.name if leader and leader.user else 'Unknown'
            leader_is_removed = leader.is_removed if leader else False

            run_responses.append(
                RunResponse(
                    id=str(run.id),
                    group_id=str(run.group_id),
                    store_id=str(run.store_id),
                    store_name=self._get_run_store_name(run),
                    state=run.state,
                    leader_name=leader_name,
                    leader_is_removed=leader_is_removed,
                    planned_on=run.planned_on.isoformat() if run.planned_on else None,
                    planning_at=run.planning_at.isoformat() if run.planning_at else None,
                    active_at=run.active_at.isoformat() if run.active_at else None,
                    confirmed_at=run.confirmed_at.isoformat() if run.confirmed_at else None,
                    shopping_at=run.shopping_at.isoformat() if run.shopping_at else None,
                    adjusting_at=run.adjusting_at.isoformat() if run.adjusting_at else None,
                    distributing_at=run.distributing_at.isoformat()
                    if run.distributing_at
                    else None,
                    completed_at=run.completed_at.isoformat() if run.completed_at else None,
                    cancelled_at=run.cancelled_at.isoformat() if run.cancelled_at else None,
                )
            )

        return run_responses

    def get_group_completed_cancelled_runs(
        self, group_id: str, user: User, limit: int = 10, offset: int = 0
    ) -> list[RunResponse]:
        """Get completed and cancelled runs for a group (paginated).

        Args:
            group_id: The UUID string of the group
            user: The requesting user
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip (default: 0)

        Returns:
            List of RunResponse ordered by completion/cancellation time (most recent first)

        Raises:
            BadRequestError: If group ID format is invalid
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not a member of the group
        """
        # Verify group ID format
        group_uuid = validate_uuid(group_id, 'Group')

        # Get the group
        group = self.group_repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        # Check if user is a member of the group
        self._verify_group_membership(
            user,
            group_uuid,
            NOT_GROUP_MEMBER,
            'Not a member of this group',
            group_id=str(group_uuid),
        )

        # Get completed/cancelled runs for the group
        logger.debug(
            'Fetching completed/cancelled runs for group',
            extra={
                'user_id': str(user.id),
                'group_id': str(group_uuid),
                'limit': limit,
                'offset': offset,
            },
        )
        runs = self.run_repo.get_completed_cancelled_runs_by_group(group_uuid, limit, offset)

        # Convert to response format with store names
        run_responses = []
        for run in runs:
            # Get leader from participations
            participations = self.run_repo.get_run_participations(run.id)
            leader = next((p for p in participations if p.is_leader), None)
            leader_name = leader.user.name if leader and leader.user else 'Unknown'

            run_responses.append(
                RunResponse(
                    id=str(run.id),
                    group_id=str(run.group_id),
                    store_id=str(run.store_id),
                    store_name=self._get_run_store_name(run),
                    state=run.state,
                    leader_name=leader_name,
                    leader_is_removed=False,
                    planned_on=run.planned_on.isoformat() if run.planned_on else None,
                    planning_at=run.planning_at.isoformat() if run.planning_at else None,
                    active_at=run.active_at.isoformat() if run.active_at else None,
                    confirmed_at=run.confirmed_at.isoformat() if run.confirmed_at else None,
                    shopping_at=run.shopping_at.isoformat() if run.shopping_at else None,
                    adjusting_at=run.adjusting_at.isoformat() if run.adjusting_at else None,
                    distributing_at=run.distributing_at.isoformat()
                    if run.distributing_at
                    else None,
                    completed_at=run.completed_at.isoformat() if run.completed_at else None,
                    cancelled_at=run.cancelled_at.isoformat() if run.cancelled_at else None,
                )
            )

        return run_responses
