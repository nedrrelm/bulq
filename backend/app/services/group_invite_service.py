"""Service for group invite and joining operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    JoinGroupResponse,
    PreviewGroupResponse,
    RegenerateTokenResponse,
    ToggleJoiningResponse,
)
from app.core.error_codes import (
    ALREADY_GROUP_MEMBER,
    GROUP_INVITE_TOKEN_REGENERATION_FAILED,
    GROUP_JOIN_FAILED,
    GROUP_JOINING_DISABLED,
    GROUP_JOINING_SETTING_UPDATE_FAILED,
    GROUP_MAX_MEMBERS_EXCEEDED,
    GROUP_NOT_FOUND,
    NOT_GROUP_ADMIN,
    USER_MAX_GROUPS_EXCEEDED,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.models import Group, User
from app.core.success_codes import GROUP_JOINED
from app.events.domain_events import MemberJoinedEvent
from app.events.event_bus import event_bus
from app.infrastructure.config import MAX_GROUPS_PER_USER, MAX_MEMBERS_PER_GROUP
from app.infrastructure.request_context import get_logger
from app.infrastructure.transaction import transactional
from app.repositories import get_group_repository, get_user_repository
from app.utils.validation import validate_uuid

from .base_service import BaseService

logger = get_logger(__name__)


class GroupInviteService(BaseService):
    """Service for group invite token and joining operations.

    This service handles:
    - Regenerating invite tokens
    - Previewing groups before joining
    - Joining groups via invite token
    - Toggling whether joining is allowed

    Separate from queries and membership to maintain single responsibility.
    """

    def __init__(self, db: AsyncSession):
        """Initialize service with necessary repositories."""
        super().__init__(db)
        self.group_repo = get_group_repository(db)
        self.user_repo = get_user_repository(db)

    async def regenerate_invite_token(self, group_id: str, user: User) -> RegenerateTokenResponse:
        """Regenerate the invite token for a group (only creator can do this).

        Args:
            group_id: The UUID string of the group
            user: The requesting user (must be creator)

        Returns:
            RegenerateTokenResponse with new invite token

        Raises:
            BadRequestError: If group ID format is invalid
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not the group creator
        """
        # Verify group ID format
        group_uuid = validate_uuid(group_id, 'Group')

        # Get the group
        group = await self.group_repo.get_group_by_id(group_uuid)
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
        new_token = await self.group_repo.regenerate_group_invite_token(group_uuid)
        if not new_token:
            raise BadRequestError(
                code=GROUP_INVITE_TOKEN_REGENERATION_FAILED,
                message='Failed to regenerate invite token',
                group_id=str(group_uuid),
            )

        return RegenerateTokenResponse(invite_token=new_token)

    async def preview_group(self, invite_token: str) -> PreviewGroupResponse:
        """Preview group information by invite token without joining.

        Args:
            invite_token: The invite token to preview

        Returns:
            PreviewGroupResponse with group preview information

        Raises:
            NotFoundError: If group with invite token doesn't exist
        """
        logger.debug('Previewing group with invite token', extra={'invite_token': invite_token})

        # Find the group by invite token
        group = await self.group_repo.get_group_by_invite_token(invite_token)
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

    @transactional('join group')
    async def join_group(self, invite_token: str, user: User) -> JoinGroupResponse:
        """Join a group using an invite token.

        This operation is atomic - validation, member addition, and event broadcast succeed together or all roll back.

        Args:
            invite_token: The invite token to use
            user: The user joining the group

        Returns:
            JoinGroupResponse with success message and group info

        Raises:
            NotFoundError: If group with invite token doesn't exist
            BadRequestError: If user is already a member or join fails
        """
        logger.info(
            'User attempting to join group via invite',
            extra={'user_id': str(user.id), 'invite_token': invite_token},
        )

        group = await self._validate_group_invite(invite_token, user)
        await self._check_membership_constraints(user, group)
        await self._add_member_to_group_db(user, group)
        self._broadcast_member_joined(user, group)

        logger.info(
            'User joined group successfully',
            extra={'user_id': str(user.id), 'group_id': str(group.id)},
        )

        return JoinGroupResponse(code=GROUP_JOINED, group_id=str(group.id), group_name=group.name)

    async def toggle_joining_allowed(self, group_id: str, user: User) -> ToggleJoiningResponse:
        """Toggle whether a group allows joining via invite link (admin only).

        Args:
            group_id: The UUID string of the group
            user: The requesting user (must be group admin)

        Returns:
            ToggleJoiningResponse with new joining status

        Raises:
            BadRequestError: If group ID format is invalid
            NotFoundError: If group doesn't exist
            ForbiddenError: If user is not a group admin
        """
        # Verify group ID format
        group_uuid = validate_uuid(group_id, 'Group')

        # Get the group
        group = await self.group_repo.get_group_by_id(group_uuid)
        if not group:
            raise NotFoundError(
                code=GROUP_NOT_FOUND, message='Group not found', group_id=str(group_uuid)
            )

        # Check if user is a group admin
        if not await self.group_repo.is_user_group_admin(group_uuid, user.id):
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
        updated_group = await self.group_repo.update_group_joining_allowed(group_uuid, new_value)
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

    async def _validate_group_invite(self, invite_token: str, user: User) -> Group:
        """Validate invite token and check if joining is allowed.

        Args:
            invite_token: The invite token to validate
            user: The user attempting to join

        Returns:
            Group if valid

        Raises:
            NotFoundError: If group not found
            ForbiddenError: If joining is disabled
        """
        group = await self.group_repo.get_group_by_invite_token(invite_token)
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

    async def _check_membership_constraints(self, user: User, group: Group) -> None:
        """Check user/group limits and ensure user is not already a member.

        Args:
            user: The user attempting to join
            group: The group being joined

        Raises:
            BadRequestError: If constraints violated
        """
        user_groups = await self.user_repo.get_user_groups(user)

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

    async def _add_member_to_group_db(self, user: User, group: Group) -> None:
        """Add user to the group in the database.

        Args:
            user: The user to add
            group: The group to add them to

        Raises:
            BadRequestError: If database operation fails
        """
        success = await self.group_repo.add_group_member(group.id, user)
        if not success:
            logger.error(
                'Failed to add user to group',
                extra={'user_id': str(user.id), 'group_id': str(group.id)},
            )
            raise BadRequestError(
                code=GROUP_JOIN_FAILED, message='Failed to join group', group_id=str(group.id)
            )

    def _broadcast_member_joined(self, user: User, group: Group) -> None:
        """Emit member_joined domain event.

        Args:
            user: The user who joined
            group: The group they joined
        """
        event_bus.emit(MemberJoinedEvent(group_id=group.id, user_id=user.id, user_name=user.name))
