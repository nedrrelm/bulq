"""Database group repository implementation."""

from uuid import UUID, uuid4

from sqlalchemy import delete, insert, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Group, User, group_membership
from app.repositories.abstract.group import AbstractGroupRepository


class DatabaseGroupRepository(AbstractGroupRepository):
    """Database implementation of group repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_group_by_id(self, group_id: UUID) -> Group | None:
        """Get group by ID."""
        result = await self.db.execute(select(Group).filter(Group.id == group_id))
        return result.scalar_one_or_none()

    async def get_group_member_count(self, group_id: UUID) -> int:
        """Get the number of members in a group."""
        result = await self.db.execute(select(func.count()).select_from(group_membership).where(group_membership.c.group_id == group_id))
        return result.scalar() or 0

    async def is_user_member_of_a_group(self, user_id: UUID, group_id: UUID) -> bool:
        """Check if a user is a member of a group."""
        result = await self.db.execute(select(group_membership).where(group_membership.c.user_id == user_id, group_membership.c.group_id == group_id))
        return result.scalar_one_or_none() is not None

    async def get_group_by_invite_token(self, invite_token: str) -> Group | None:
        """Get group by invite token."""
        result = await self.db.execute(select(Group).filter(Group.invite_token == invite_token))
        return result.scalar_one_or_none()

    async def regenerate_group_invite_token(self, group_id: UUID) -> str | None:
        """Regenerate invite token for a group."""
        result = await self.db.execute(select(Group).filter(Group.id == group_id))
        group = result.scalar_one_or_none()
        if group:
            new_token = str(uuid4())
            group.invite_token = new_token
            await self.db.commit()
            return new_token
        return None

    async def create_group(self, name: str, created_by: UUID) -> Group:
        """Create a new group."""
        group = Group(
            name=name, created_by=created_by, invite_token=str(uuid4()), is_joining_allowed=True
        )
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def add_group_member(self, group_id: UUID, user: User, is_group_admin: bool = False) -> bool:
        """Add a user to a group."""
        # Check if already a member
        result = await self.db.execute(
            select(group_membership).where(
                group_membership.c.group_id == group_id, group_membership.c.user_id == user.id
            )
        )
        existing = result.first()

        if existing:
            return False

        # Insert into group_membership table
        await self.db.execute(
            insert(group_membership).values(
                group_id=group_id, user_id=user.id, is_group_admin=is_group_admin
            )
        )
        await self.db.commit()
        return True

    async def remove_group_member(self, group_id: UUID, user_id: UUID) -> bool:
        """Remove a user from a group."""
        result = await self.db.execute(
            delete(group_membership).where(
                group_membership.c.group_id == group_id, group_membership.c.user_id == user_id
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def is_user_group_admin(self, group_id: UUID, user_id: UUID) -> bool:
        """Check if a user is an admin of a group."""
        result = await self.db.execute(
            select(group_membership.c.is_group_admin).where(
                group_membership.c.group_id == group_id, group_membership.c.user_id == user_id
            )
        )
        row = result.first()
        return row[0] if row else False

    async def get_group_members_with_admin_status(self, group_id: UUID) -> list[dict]:
        """Get all members of a group with their admin status."""
        result = await self.db.execute(
            select(User, group_membership.c.is_group_admin)
            .join(group_membership, User.id == group_membership.c.user_id)
            .where(group_membership.c.group_id == group_id)
        )
        results = result.all()

        return [
            {
                'id': str(user.id),
                'name': user.name,
                'username': user.username,
                'is_group_admin': is_admin,
            }
            for user, is_admin in results
        ]

    async def update_group_joining_allowed(
        self, group_id: UUID, is_joining_allowed: bool
    ) -> Group | None:
        """Update whether a group allows joining via invite link."""
        result = await self.db.execute(update(Group).where(Group.id == group_id).values(is_joining_allowed=is_joining_allowed).returning(Group))
        await self.db.commit()
        return result.scalar_one_or_none()

    async def set_group_member_admin(self, group_id: UUID, user_id: UUID, is_admin: bool) -> bool:
        """Set the admin status of a group member."""
        result = await self.db.execute(
            update(group_membership)
            .where(group_membership.c.group_id == group_id, group_membership.c.user_id == user_id)
            .values(is_group_admin=is_admin)
        )
        await self.db.commit()
        return result.rowcount > 0
