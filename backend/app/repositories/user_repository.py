"""Repository for user table"""
# @Todo split database.py into smaller files, like user.py, group.py, store.py, product.py, run.py, participation.py, shopping_list_item.py, product_availability.py, notification.py, reassignment_request.py, etc.
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,insert

from app.core.models import (
    Group,
    LeaderReassignmentRequest,
    Notification,
    Product,
    ProductAvailability,
    ProductBid,
    Run,
    RunParticipation,
    ShoppingListItem,
    Store,
    User,
)
from app.core.run_state import RunState, state_machine
from app.infrastructure.request_context import get_logger
from app.repositories.abstract import AbstractRepository

logger = get_logger(__name__)


class UserRepository(AbstractRepository):
    """Repository for user table"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        return await self.db.execute(select(User).filter(User.id == user_id).first())

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username."""
        return await self.db.execute(select(User).filter(User.username == username).first())

    async def create_user(self, name: str, username: str, password_hash: str) -> User:
        """Create a new user."""
        user = User(name=name, username=username, password_hash=password_hash)
        self.db.execute(insert(User).values(user))
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_user_groups(self, user: User) -> list[Group]:
        """Get all groups that a user is a member of."""
        return await self.db.execute(select(Group).join(Group.members).filter(User.id == user.id).all())

    async def get_all_users(self) -> list[User]:
        """Get all users."""
        return await self.db.execute(select(User).all())