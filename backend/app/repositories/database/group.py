"""Database group repository implementation."""

from uuid import UUID, uuid4

from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import Session

from app.core.models import Group, User, group_membership
from app.repositories.abstract.group import AbstractGroupRepository


class DatabaseGroupRepository(AbstractGroupRepository):
    """Database implementation of group repository."""

    def __init__(self, db: Session):
        self.db = db

    def get_group_by_id(self, group_id: UUID) -> Group | None:
        """Get group by ID."""
        return self.db.query(Group).filter(Group.id == group_id).first()

    def get_group_by_invite_token(self, invite_token: str) -> Group | None:
        """Get group by invite token."""
        return self.db.query(Group).filter(Group.invite_token == invite_token).first()

    def regenerate_group_invite_token(self, group_id: UUID) -> str | None:
        """Regenerate invite token for a group."""
        group = self.db.query(Group).filter(Group.id == group_id).first()
        if group:
            new_token = str(uuid4())
            group.invite_token = new_token
            self.db.commit()
            return new_token
        return None

    def create_group(self, name: str, created_by: UUID) -> Group:
        """Create a new group."""
        group = Group(
            name=name, created_by=created_by, invite_token=str(uuid4()), is_joining_allowed=True
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group

    def add_group_member(self, group_id: UUID, user: User, is_group_admin: bool = False) -> bool:
        """Add a user to a group."""
        # Check if already a member
        existing = self.db.execute(
            select(group_membership).where(
                group_membership.c.group_id == group_id, group_membership.c.user_id == user.id
            )
        ).first()

        if existing:
            return False

        # Insert into group_membership table
        self.db.execute(
            insert(group_membership).values(
                group_id=group_id, user_id=user.id, is_group_admin=is_group_admin
            )
        )
        self.db.commit()
        return True

    def remove_group_member(self, group_id: UUID, user_id: UUID) -> bool:
        """Remove a user from a group."""
        result = self.db.execute(
            delete(group_membership).where(
                group_membership.c.group_id == group_id, group_membership.c.user_id == user_id
            )
        )
        self.db.commit()
        return result.rowcount > 0

    def is_user_group_admin(self, group_id: UUID, user_id: UUID) -> bool:
        """Check if a user is an admin of a group."""
        result = self.db.execute(
            select(group_membership.c.is_group_admin).where(
                group_membership.c.group_id == group_id, group_membership.c.user_id == user_id
            )
        ).first()

        return result[0] if result else False

    def get_group_members_with_admin_status(self, group_id: UUID) -> list[dict]:
        """Get all members of a group with their admin status."""
        results = self.db.execute(
            select(User, group_membership.c.is_group_admin)
            .join(group_membership, User.id == group_membership.c.user_id)
            .where(group_membership.c.group_id == group_id)
        ).all()

        return [
            {
                'id': str(user.id),
                'name': user.name,
                'username': user.username,
                'is_group_admin': is_admin,
            }
            for user, is_admin in results
        ]

    def update_group_joining_allowed(
        self, group_id: UUID, is_joining_allowed: bool
    ) -> Group | None:
        """Update whether a group allows joining via invite link."""
        group = self.db.query(Group).filter(Group.id == group_id).first()
        if group:
            group.is_joining_allowed = is_joining_allowed
            self.db.commit()
            self.db.refresh(group)
            return group
        return None

    def set_group_member_admin(self, group_id: UUID, user_id: UUID, is_admin: bool) -> bool:
        """Set the admin status of a group member."""
        result = self.db.execute(
            update(group_membership)
            .where(group_membership.c.group_id == group_id, group_membership.c.user_id == user_id)
            .values(is_group_admin=is_admin)
        )
        self.db.commit()
        return result.rowcount > 0
