"""Base service class for all services."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import NOT_GROUP_MEMBER, NOT_RUN_PARTICIPANT, PARTICIPATION_NOT_FOUND
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.models import Run, User


class BaseService:
    """Base service class with common functionality.

    Services should initialize only the repositories they need
    using the repository factory functions from app.repositories.
    """

    def __init__(self, db: AsyncSession):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    async def _is_group_member(self, user: User, target_group_id: UUID) -> bool:
        """Check if user is a member of a group.

        Args:
            user: User to check
            target_group_id: Group UUID to check membership in

        Returns:
            True if user is a member, False otherwise

        Raises:
            AttributeError: If service doesn't have user_repo
        """
        if not hasattr(self, 'user_repo'):
            raise AttributeError('Service must have user_repo to check group membership')

        user_groups = await self.user_repo.get_user_groups(user)
        return any(g.id == target_group_id for g in user_groups)

    async def _verify_group_membership(
        self,
        user: User,
        target_group_id: UUID,
        error_code: str = NOT_GROUP_MEMBER,
        error_message: str = 'Not authorized to access this group',
        **error_context,
    ) -> None:
        """Verify user is a member of a group, raise ForbiddenError if not.

        Args:
            user: User to check
            target_group_id: Group UUID to verify membership in
            error_code: Error code to use if not a member
            error_message: Error message to use if not a member
            **error_context: Additional context to include in error

        Raises:
            ForbiddenError: If user is not a member of the group
        """
        if not await self._is_group_member(user, target_group_id):
            raise ForbiddenError(code=error_code, message=error_message, **error_context)

    async def _verify_run_access(
        self,
        user: User,
        run: Run,
        error_code: str = NOT_RUN_PARTICIPANT,
        error_message: str = 'Not authorized to access this run',
        **error_context,
    ) -> None:
        """Verify user has access to a run (member of run's group).

        Args:
            user: User to check
            run: Run to verify access to
            error_code: Error code to use if no access
            error_message: Error message to use if no access
            **error_context: Additional context to include in error

        Raises:
            ForbiddenError: If user doesn't have access to the run
        """
        await self._verify_group_membership(
            user, run.group_id, error_code, error_message, **error_context
        )

    async def _get_store_name(self, store_id: UUID) -> str:
        """Get store name by ID, returning 'Unknown Store' if not found.

        Args:
            store_id: Store UUID

        Returns:
            Store name or 'Unknown Store'

        Raises:
            AttributeError: If service doesn't have store_repo
        """
        if not hasattr(self, 'store_repo'):
            raise AttributeError('Service must have store_repo to get store name')

        store = await self.store_repo.get_store_by_id(store_id)
        return store.name if store else 'Unknown Store'

    def _is_leader_or_helper(self, participation) -> bool:
        """Check if participation has leader or helper role.

        Args:
            participation: RunParticipation to check

        Returns:
            True if participation is leader or helper
        """
        return participation.is_leader or participation.is_helper

    async def _get_user_participation(self, user_id: UUID, run_id: UUID, run_id_str: str = ''):
        """Get user's participation in a run.

        Args:
            user_id: User UUID
            run_id: Run UUID
            run_id_str: Run ID as string for error messages

        Returns:
            RunParticipation

        Raises:
            AttributeError: If service doesn't have run_repo
            NotFoundError: If participation not found
        """
        if not hasattr(self, 'run_repo'):
            raise AttributeError('Service must have run_repo to get participation')

        participation = await self.run_repo.get_participation(user_id, run_id)
        if not participation:
            raise NotFoundError(
                code=PARTICIPATION_NOT_FOUND,
                message='Participation not found',
                user_id=str(user_id),
                run_id=run_id_str or str(run_id),
            )
        return participation
