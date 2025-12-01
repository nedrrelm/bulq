"""Database user repository implementation."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.models import Group, LeaderReassignmentRequest, Notification, Product, ProductAvailability, ProductBid, Run, RunParticipation, Store, User, group_membership
from app.repositories.abstract.user import AbstractUserRepository


class DatabaseUserRepository(AbstractUserRepository):
    """Database implementation of user repository."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> User | None:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def create_user(self, name: str, username: str, password_hash: str) -> User:
        """Create a new user."""
        user = User(name=name, username=username, password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_groups(self, user: User) -> list[Group]:
        """Get all groups that a user is a member of."""
        return self.db.query(Group).join(Group.members).filter(User.id == user.id).all()

    def get_all_users(self) -> list[User]:
        """Get all users."""
        return self.db.query(User).all()

    def update_user(self, user_id: UUID, **fields) -> User | None:
        """Update user fields. Returns updated user or None if not found."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        for key, value in fields.items():
            if hasattr(user, key):
                setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: UUID) -> bool:
        """Delete a user. Returns True if deleted, False if not found."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        return True

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password against a hash."""
        import bcrypt

        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))

    def get_user_stats(self, user_id: UUID) -> dict:
        """Get user statistics including runs, bids, and spending."""
        from sqlalchemy import func

        # Get total quantity bought and money spent from picked-up bids
        bid_stats = (
            self.db.query(
                func.coalesce(func.sum(ProductBid.distributed_quantity), 0).label('total_quantity'),
                func.coalesce(
                    func.sum(
                        ProductBid.distributed_quantity * ProductBid.distributed_price_per_unit
                    ),
                    0,
                ).label('total_spent'),
            )
            .join(RunParticipation, ProductBid.participation_id == RunParticipation.id)
            .filter(RunParticipation.user_id == user_id, ProductBid.is_picked_up)
            .first()
        )

        total_quantity = float(bid_stats.total_quantity) if bid_stats else 0.0
        total_spent = float(bid_stats.total_spent) if bid_stats else 0.0

        # Get runs participated count (distinct runs)
        runs_participated = (
            self.db.query(func.count(func.distinct(RunParticipation.run_id)))
            .filter(RunParticipation.user_id == user_id)
            .scalar()
            or 0
        )

        # Get runs where user was helper
        runs_helped = (
            self.db.query(func.count(RunParticipation.id))
            .filter(RunParticipation.user_id == user_id, RunParticipation.is_helper)
            .scalar()
            or 0
        )

        # Get runs where user was leader
        runs_led = (
            self.db.query(func.count(RunParticipation.id))
            .filter(RunParticipation.user_id == user_id, RunParticipation.is_leader)
            .scalar()
            or 0
        )

        # Get groups count
        groups_count = (
            self.db.query(func.count(group_membership.c.group_id))
            .filter(group_membership.c.user_id == user_id)
            .scalar()
            or 0
        )

        return {
            'total_quantity_bought': total_quantity,
            'total_money_spent': total_spent,
            'runs_participated': runs_participated,
            'runs_helped': runs_helped,
            'runs_led': runs_led,
            'groups_count': groups_count,
        }

    def bulk_update_run_participations(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update all run participations from old user to new user. Returns count of updated records."""
        result = (
            self.db.query(RunParticipation)
            .filter(RunParticipation.user_id == old_user_id)
            .update({RunParticipation.user_id: new_user_id})
        )
        self.db.commit()
        return result

    def bulk_update_group_creator(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update group creator from old user to new user. Returns count of updated records."""
        result = (
            self.db.query(Group)
            .filter(Group.created_by == old_user_id)
            .update({Group.created_by: new_user_id})
        )
        self.db.commit()
        return result

    def bulk_update_product_creator(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update product creator from old user to new user. Returns count of updated records."""
        result = (
            self.db.query(Product)
            .filter(Product.created_by == old_user_id)
            .update({Product.created_by: new_user_id})
        )
        self.db.commit()
        return result

    def bulk_update_product_verifier(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update product verifier from old user to new user. Returns count of updated records."""
        result = (
            self.db.query(Product)
            .filter(Product.verified_by == old_user_id)
            .update({Product.verified_by: new_user_id})
        )
        self.db.commit()
        return result

    def bulk_update_store_creator(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update store creator from old user to new user. Returns count of updated records."""
        result = (
            self.db.query(Store)
            .filter(Store.created_by == old_user_id)
            .update({Store.created_by: new_user_id})
        )
        self.db.commit()
        return result

    def bulk_update_store_verifier(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update store verifier from old user to new user. Returns count of updated records."""
        result = (
            self.db.query(Store)
            .filter(Store.verified_by == old_user_id)
            .update({Store.verified_by: new_user_id})
        )
        self.db.commit()
        return result

    def bulk_update_product_availability_creator(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update product availability creator from old user to new user. Returns count of updated records."""
        result = (
            self.db.query(ProductAvailability)
            .filter(ProductAvailability.created_by == old_user_id)
            .update({ProductAvailability.created_by: new_user_id})
        )
        self.db.commit()
        return result

    def bulk_update_notifications(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update notifications from old user to new user. Returns count of updated records."""
        result = (
            self.db.query(Notification)
            .filter(Notification.user_id == old_user_id)
            .update({Notification.user_id: new_user_id})
        )
        self.db.commit()
        return result

    def bulk_update_reassignment_from_user(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update reassignment requests from_user from old user to new user. Returns count of updated records."""
        result = (
            self.db.query(LeaderReassignmentRequest)
            .filter(LeaderReassignmentRequest.from_user_id == old_user_id)
            .update({LeaderReassignmentRequest.from_user_id: new_user_id})
        )
        self.db.commit()
        return result

    def bulk_update_reassignment_to_user(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update reassignment requests to_user from old user to new user. Returns count of updated records."""
        result = (
            self.db.query(LeaderReassignmentRequest)
            .filter(LeaderReassignmentRequest.to_user_id == old_user_id)
            .update({LeaderReassignmentRequest.to_user_id: new_user_id})
        )
        self.db.commit()
        return result

    def transfer_group_admin_status(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Transfer group admin status from old user to new user. Returns count of updated groups."""
        # Find all groups where old user is admin
        old_user_admin_groups = (
            self.db.query(group_membership.c.group_id)
            .filter(
                group_membership.c.user_id == old_user_id,
                group_membership.c.is_group_admin == True
            )
            .all()
        )

        group_ids = [g[0] for g in old_user_admin_groups]

        if not group_ids:
            return 0

        # Make new user admin in those groups (if they're already a member)
        result = (
            self.db.query(group_membership)
            .filter(
                group_membership.c.user_id == new_user_id,
                group_membership.c.group_id.in_(group_ids)
            )
            .update({group_membership.c.is_group_admin: True}, synchronize_session=False)
        )

        self.db.commit()
        return result

    def check_overlapping_run_participations(self, user1_id: UUID, user2_id: UUID) -> list[UUID]:
        """Check if two users participate in any of the same runs. Returns list of overlapping run IDs."""
        user1_runs = (
            self.db.query(RunParticipation.run_id)
            .filter(RunParticipation.user_id == user1_id)
            .subquery()
        )
        overlapping_runs = (
            self.db.query(RunParticipation.run_id)
            .filter(
                RunParticipation.user_id == user2_id,
                RunParticipation.run_id.in_(user1_runs)
            )
            .all()
        )
        return [run_id for (run_id,) in overlapping_runs]
