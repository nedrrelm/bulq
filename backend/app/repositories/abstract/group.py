"""Abstract group repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.models import Group, User


class AbstractGroupRepository(ABC):
    """Abstract base class for group repository operations."""

    @abstractmethod
    async def get_group_by_id(self, group_id: UUID) -> Group | None:
        """Get group by ID."""
        raise NotImplementedError('Subclass must implement get_group_by_id')

    @abstractmethod
    async def get_group_by_invite_token(self, invite_token: str) -> Group | None:
        """Get group by invite token."""
        raise NotImplementedError('Subclass must implement get_group_by_invite_token')

    @abstractmethod
    async def regenerate_group_invite_token(self, group_id: UUID) -> str | None:
        """Regenerate invite token for a group."""
        raise NotImplementedError('Subclass must implement regenerate_group_invite_token')

    @abstractmethod
    async def create_group(self, name: str, created_by: UUID) -> Group:
        """Create a new group."""
        raise NotImplementedError('Subclass must implement create_group')

    @abstractmethod
    async def add_group_member(self, group_id: UUID, user: User, is_group_admin: bool = False) -> bool:
        """Add a user to a group."""
        raise NotImplementedError('Subclass must implement add_group_member')

    @abstractmethod
    async def remove_group_member(self, group_id: UUID, user_id: UUID) -> bool:
        """Remove a user from a group."""
        raise NotImplementedError('Subclass must implement remove_group_member')

    @abstractmethod
    async def is_user_group_admin(self, group_id: UUID, user_id: UUID) -> bool:
        """Check if a user is an admin of a group."""
        raise NotImplementedError('Subclass must implement is_user_group_admin')

    @abstractmethod
    async def get_group_members_with_admin_status(self, group_id: UUID) -> list[dict]:
        """Get all members of a group with their admin status."""
        raise NotImplementedError('Subclass must implement get_group_members_with_admin_status')

    @abstractmethod
    async def update_group_joining_allowed(
        self, group_id: UUID, is_joining_allowed: bool
    ) -> Group | None:
        """Update whether a group allows joining via invite link."""
        raise NotImplementedError('Subclass must implement update_group_joining_allowed')

    @abstractmethod
    async def set_group_member_admin(self, group_id: UUID, user_id: UUID, is_admin: bool) -> bool:
        """Set the admin status of a group member."""
        raise NotImplementedError('Subclass must implement set_group_member_admin')
