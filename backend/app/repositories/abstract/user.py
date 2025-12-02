"""Abstract user repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.models import Group, User


class AbstractUserRepository(ABC):
    """Abstract base class for user repository operations."""

    @abstractmethod
    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        raise NotImplementedError('Subclass must implement get_user_by_id')

    @abstractmethod
    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username."""
        raise NotImplementedError('Subclass must implement get_user_by_username')

    @abstractmethod
    async def create_user(self, name: str, username: str, password_hash: str) -> User:
        """Create a new user."""
        raise NotImplementedError('Subclass must implement create_user')

    @abstractmethod
    async def get_user_groups(self, user: User) -> list[Group]:
        """Get all groups that a user is a member of."""
        raise NotImplementedError('Subclass must implement get_user_groups')

    @abstractmethod
    async def get_all_users(self) -> list[User]:
        """Get all users."""
        raise NotImplementedError('Subclass must implement get_all_users')

    @abstractmethod
    async def update_user(self, user_id: UUID, **fields) -> User | None:
        """Update user fields. Returns updated user or None if not found."""
        raise NotImplementedError('Subclass must implement update_user')

    @abstractmethod
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete a user. Returns True if deleted, False if not found."""
        raise NotImplementedError('Subclass must implement delete_user')

    @abstractmethod
    async def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password."""
        raise NotImplementedError('Subclass must implement verify_password')

    @abstractmethod
    async def get_user_stats(self, user_id: UUID) -> dict:
        """Get user statistics including runs, bids, and spending.

        Returns:
            Dictionary with keys:
                - total_quantity_bought: Sum of distributed quantities from picked up bids
                - total_money_spent: Sum of (distributed_quantity * distributed_price_per_unit)
                - runs_participated: Count of distinct runs user participated in
                - runs_helped: Count of runs where user was helper
                - runs_led: Count of runs where user was leader
                - groups_count: Count of groups user is member of
        """
        raise NotImplementedError('Subclass must implement get_user_stats')

    @abstractmethod
    async def bulk_update_run_participations(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update all run participations from old user to new user. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_run_participations')

    @abstractmethod
    async def bulk_update_group_creator(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update group creator from old user to new user. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_group_creator')

    @abstractmethod
    async def bulk_update_product_creator(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update product creator from old user to new user. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_product_creator')

    @abstractmethod
    async def bulk_update_product_verifier(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update product verifier from old user to new user. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_product_verifier')

    @abstractmethod
    async def bulk_update_store_creator(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update store creator from old user to new user. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_store_creator')

    @abstractmethod
    async def bulk_update_store_verifier(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update store verifier from old user to new user. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_store_verifier')

    @abstractmethod
    async def bulk_update_product_availability_creator(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update product availability creator from old user to new user. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_product_availability_creator')

    @abstractmethod
    async def bulk_update_notifications(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update notifications from old user to new user. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_notifications')

    @abstractmethod
    async def bulk_update_reassignment_from_user(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update reassignment requests from_user from old user to new user. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_reassignment_from_user')

    @abstractmethod
    async def bulk_update_reassignment_to_user(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update reassignment requests to_user from old user to new user. Returns count of updated records."""
        raise NotImplementedError('Subclass must implement bulk_update_reassignment_to_user')

    @abstractmethod
    async def transfer_group_admin_status(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Transfer group admin status from old user to new user. Returns count of updated groups."""
        raise NotImplementedError('Subclass must implement transfer_group_admin_status')

    @abstractmethod
    async def check_overlapping_run_participations(self, user1_id: UUID, user2_id: UUID) -> list[UUID]:
        """Check if two users participate in any of the same runs. Returns list of overlapping run IDs."""
        raise NotImplementedError('Subclass must implement check_overlapping_run_participations')
