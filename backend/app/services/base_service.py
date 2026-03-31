"""Base service class for all services."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.error_codes import NOT_GROUP_MEMBER, NOT_RUN_PARTICIPANT
from app.core.exceptions import ForbiddenError
from app.core.models import Run, User


class BaseService:
    """Base service class with common functionality.

    Services should initialize only the repositories they need
    using the repository factory functions from app.repositories.
    """

    def __init__(self, db: Session):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def _is_group_member(self, user: User, target_group_id: UUID) -> bool:
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

        user_groups = self.user_repo.get_user_groups(user)
        return any(g.id == target_group_id for g in user_groups)

    def _verify_group_membership(
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
        if not self._is_group_member(user, target_group_id):
            raise ForbiddenError(code=error_code, message=error_message, **error_context)

    def _verify_run_access(
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
        self._verify_group_membership(
            user, run.group_id, error_code, error_message, **error_context
        )
