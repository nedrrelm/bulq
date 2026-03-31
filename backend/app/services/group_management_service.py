"""Service for group lifecycle management operations."""

from sqlalchemy.orm import Session

from app.api.schemas import CreateGroupResponse
from app.core.models import User
from app.infrastructure.request_context import get_logger
from app.infrastructure.transaction import transactional
from app.repositories import get_group_repository

from .base_service import BaseService

logger = get_logger(__name__)


class GroupManagementService(BaseService):
    """Service for group lifecycle management.

    This service handles group CRUD operations including:
    - Creating new groups
    - (Future: Updating group settings, deleting groups)

    Separate from queries and membership to maintain single responsibility.
    """

    def __init__(self, db: Session):
        """Initialize service with necessary repositories."""
        super().__init__(db)
        self.group_repo = get_group_repository(db)

    @transactional('create group')
    def create_group(self, name: str, user: User) -> CreateGroupResponse:
        """Create a new group and add the creator as an admin member.

        This operation is atomic - group creation and member addition succeed together or all roll back.

        Args:
            name: The name of the group
            user: The user creating the group

        Returns:
            CreateGroupResponse with group information
        """
        logger.info(f'Creating group: {name}', extra={'user_id': str(user.id), 'group_name': name})

        # Create the group
        group = self.group_repo.create_group(name, user.id)

        # Add the creator as an admin member
        self.group_repo.add_group_member(group.id, user, is_group_admin=True)

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
