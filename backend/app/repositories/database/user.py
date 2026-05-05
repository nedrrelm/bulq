"""Database user repository implementation."""

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    Group,
    LeaderReassignmentRequest,
    Notification,
    Product,
    ProductAvailability,
    ProductBid,
    RunParticipation,
    Store,
    User,
    group_membership,
)
from app.repositories.abstract.user import AbstractUserRepository


class DatabaseUserRepository(AbstractUserRepository):
    """Database implementation of user repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username."""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create_user(self, name: str, username: str, password_hash: str) -> User:
        """Create a new user."""
        user = User(name=name, username=username, password_hash=password_hash)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_user_groups(self, user: User) -> list[Group]:
        """Get all groups that a user is a member of."""
        result = await self.db.execute(select(Group).join(Group.members).where(User.id == user.id))
        return list(result.scalars().all())

    async def get_all_users(self) -> list[User]:
        """Get all users."""
        result = await self.db.execute(select(User))
        return list(result.scalars().all())

    async def update_user(self, user_id: UUID, **fields) -> User | None:
        """Update user fields. Returns updated user or None if not found."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None

        for key, value in fields.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: UUID) -> bool:
        """Delete a user. Returns True if deleted, False if not found."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()
        return True

    async def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password against a hash."""
        import bcrypt

        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))

    async def get_user_stats(self, user_id: UUID) -> dict:
        """Get user statistics including runs, bids, and spending."""
        bid_stats_result = await self.db.execute(
            select(
                func.coalesce(func.sum(ProductBid.distributed_quantity), 0).label('total_quantity'),
                func.coalesce(
                    func.sum(
                        ProductBid.distributed_quantity * ProductBid.distributed_price_per_unit
                    ),
                    0,
                ).label('total_spent'),
            )
            .join(RunParticipation, ProductBid.participation_id == RunParticipation.id)
            .where(RunParticipation.user_id == user_id, ProductBid.is_picked_up)
        )
        bid_stats = bid_stats_result.first()

        total_quantity = float(bid_stats.total_quantity) if bid_stats else 0.0
        total_spent = float(bid_stats.total_spent) if bid_stats else 0.0

        runs_participated_result = await self.db.execute(
            select(func.count(func.distinct(RunParticipation.run_id))).where(
                RunParticipation.user_id == user_id
            )
        )
        runs_participated = runs_participated_result.scalar_one() or 0

        runs_helped_result = await self.db.execute(
            select(func.count(RunParticipation.id)).where(
                RunParticipation.user_id == user_id, RunParticipation.is_helper
            )
        )
        runs_helped = runs_helped_result.scalar_one() or 0

        runs_led_result = await self.db.execute(
            select(func.count(RunParticipation.id)).where(
                RunParticipation.user_id == user_id, RunParticipation.is_leader
            )
        )
        runs_led = runs_led_result.scalar_one() or 0

        groups_count_result = await self.db.execute(
            select(func.count(group_membership.c.group_id)).where(
                group_membership.c.user_id == user_id
            )
        )
        groups_count = groups_count_result.scalar_one() or 0

        return {
            'total_quantity_bought': total_quantity,
            'total_money_spent': total_spent,
            'runs_participated': runs_participated,
            'runs_helped': runs_helped,
            'runs_led': runs_led,
            'groups_count': groups_count,
        }

    async def bulk_update_run_participations(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update all run participations from old user to new user. Returns count of updated records."""
        result = await self.db.execute(
            update(RunParticipation)
            .where(RunParticipation.user_id == old_user_id)
            .values(user_id=new_user_id)
        )
        await self.db.commit()
        return result.rowcount

    async def bulk_update_group_creator(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update group creator from old user to new user. Returns count of updated records."""
        result = await self.db.execute(
            update(Group).where(Group.created_by == old_user_id).values(created_by=new_user_id)
        )
        await self.db.commit()
        return result.rowcount

    async def bulk_update_product_creator(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update product creator from old user to new user. Returns count of updated records."""
        result = await self.db.execute(
            update(Product).where(Product.created_by == old_user_id).values(created_by=new_user_id)
        )
        await self.db.commit()
        return result.rowcount

    async def bulk_update_product_verifier(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update product verifier from old user to new user. Returns count of updated records."""
        result = await self.db.execute(
            update(Product)
            .where(Product.verified_by == old_user_id)
            .values(verified_by=new_user_id)
        )
        await self.db.commit()
        return result.rowcount

    async def bulk_update_store_creator(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update store creator from old user to new user. Returns count of updated records."""
        result = await self.db.execute(
            update(Store).where(Store.created_by == old_user_id).values(created_by=new_user_id)
        )
        await self.db.commit()
        return result.rowcount

    async def bulk_update_store_verifier(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update store verifier from old user to new user. Returns count of updated records."""
        result = await self.db.execute(
            update(Store).where(Store.verified_by == old_user_id).values(verified_by=new_user_id)
        )
        await self.db.commit()
        return result.rowcount

    async def bulk_update_product_availability_creator(
        self, old_user_id: UUID, new_user_id: UUID
    ) -> int:
        """Update product availability creator from old user to new user. Returns count of updated records."""
        result = await self.db.execute(
            update(ProductAvailability)
            .where(ProductAvailability.created_by == old_user_id)
            .values(created_by=new_user_id)
        )
        await self.db.commit()
        return result.rowcount

    async def bulk_update_notifications(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update notifications from old user to new user. Returns count of updated records."""
        result = await self.db.execute(
            update(Notification)
            .where(Notification.user_id == old_user_id)
            .values(user_id=new_user_id)
        )
        await self.db.commit()
        return result.rowcount

    async def bulk_update_reassignment_from_user(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update reassignment requests from_user from old user to new user. Returns count of updated records."""
        result = await self.db.execute(
            update(LeaderReassignmentRequest)
            .where(LeaderReassignmentRequest.from_user_id == old_user_id)
            .values(from_user_id=new_user_id)
        )
        await self.db.commit()
        return result.rowcount

    async def bulk_update_reassignment_to_user(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update reassignment requests to_user from old user to new user. Returns count of updated records."""
        result = await self.db.execute(
            update(LeaderReassignmentRequest)
            .where(LeaderReassignmentRequest.to_user_id == old_user_id)
            .values(to_user_id=new_user_id)
        )
        await self.db.commit()
        return result.rowcount

    async def transfer_group_admin_status(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Transfer group admin status from old user to new user. Returns count of updated groups."""
        result = await self.db.execute(
            select(group_membership.c.group_id).where(
                group_membership.c.user_id == old_user_id, group_membership.c.is_group_admin
            )
        )
        old_user_admin_groups = result.all()

        group_ids = [g[0] for g in old_user_admin_groups]

        if not group_ids:
            return 0

        result = await self.db.execute(
            update(group_membership)
            .where(
                group_membership.c.user_id == new_user_id,
                group_membership.c.group_id.in_(group_ids),
            )
            .values(is_group_admin=True)
        )

        await self.db.commit()
        return result.rowcount

    async def check_overlapping_run_participations(
        self, user1_id: UUID, user2_id: UUID
    ) -> list[UUID]:
        """Check if two users participate in any of the same runs. Returns list of overlapping run IDs."""
        user1_runs = (
            select(RunParticipation.run_id).where(RunParticipation.user_id == user1_id).subquery()
        )
        result = await self.db.execute(
            select(RunParticipation.run_id).where(
                RunParticipation.user_id == user2_id,
                RunParticipation.run_id.in_(select(user1_runs)),
            )
        )
        overlapping_runs = result.all()
        return [run_id for (run_id,) in overlapping_runs]
