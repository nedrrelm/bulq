"""Memory group repository implementation."""

from uuid import UUID, uuid4

from app.core.models import Group, User
from app.repositories.abstract.group import AbstractGroupRepository
from app.repositories.memory.storage import MemoryStorage


class MemoryGroupRepository(AbstractGroupRepository):
    """Memory implementation of group repository."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    async def get_group_by_id(self, group_id: UUID) -> Group | None:
        group = self.storage.groups.get(group_id)
        if group:
            # Set up relationships
            group.creator = self.storage.users.get(group.created_by)
            member_ids = self.storage.group_memberships.get(group_id, [])
            group.members = [self.storage.users.get(uid) for uid in member_ids if uid in self.storage.users]
        return group

    async def get_group_by_invite_token(self, invite_token: str) -> Group | None:
        for group in self.storage.groups.values():
            if group.invite_token == invite_token:
                # Set up relationships
                group.creator = self.storage.users.get(group.created_by)
                member_ids = self.storage.group_memberships.get(group.id, [])
                group.members = [self.storage.users.get(uid) for uid in member_ids if uid in self.storage.users]
                return group
        return None

    async def regenerate_group_invite_token(self, group_id: UUID) -> str | None:
        group = self.storage.groups.get(group_id)
        if group:
            new_token = str(uuid4())
            group.invite_token = new_token
            return new_token
        return None

    async def create_group(self, name: str, created_by: UUID) -> Group:
        group = Group(
            id=uuid4(),
            name=name,
            created_by=created_by,
            invite_token=str(uuid4()),
            is_joining_allowed=True,
        )
        self.storage.groups[group.id] = group
        self.storage.group_memberships[group.id] = []
        return group

    async def add_group_member(self, group_id: UUID, user: User, is_group_admin: bool = False) -> bool:
        if group_id in self.storage.group_memberships and user.id not in self.storage.group_memberships[group_id]:
            self.storage.group_memberships[group_id].append(user.id)
            self.storage.group_admin_status[(group_id, user.id)] = is_group_admin
            return True
        return False

    async def remove_group_member(self, group_id: UUID, user_id: UUID) -> bool:
        """Remove a user from a group."""
        if group_id in self.storage.group_memberships and user_id in self.storage.group_memberships[group_id]:
            self.storage.group_memberships[group_id].remove(user_id)
            # Remove admin status
            key = (group_id, user_id)
            if key in self.storage.group_admin_status:
                del self.storage.group_admin_status[key]
            return True
        return False

    async def is_user_group_admin(self, group_id: UUID, user_id: UUID) -> bool:
        """Check if a user is an admin of a group."""
        return self.storage.group_admin_status.get((group_id, user_id), False)

    async def get_group_members_with_admin_status(self, group_id: UUID) -> list[dict]:
        """Get all members of a group with their admin status."""
        member_ids = self.storage.group_memberships.get(group_id, [])
        members = []
        for user_id in member_ids:
            user = self.storage.users.get(user_id)
            if user:
                members.append(
                    {
                        'id': str(user.id),
                        'name': user.name,
                        'username': user.username,
                        'is_group_admin': self.storage.group_admin_status.get((group_id, user_id), False),
                    }
                )
        return members

    async def update_group_joining_allowed(
        self, group_id: UUID, is_joining_allowed: bool
    ) -> Group | None:
        """Update whether a group allows joining via invite link."""
        group = self.storage.groups.get(group_id)
        if group:
            group.is_joining_allowed = is_joining_allowed
            return group
        return None

    async def set_group_member_admin(self, group_id: UUID, user_id: UUID, is_admin: bool) -> bool:
        """Set the admin status of a group member."""
        if group_id in self.storage.group_memberships and user_id in self.storage.group_memberships[group_id]:
            self.storage.group_admin_status[(group_id, user_id)] = is_admin
            return True
        return False
