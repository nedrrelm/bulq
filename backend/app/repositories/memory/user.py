"""Memory user repository implementation."""

from uuid import UUID, uuid4

from app.core.models import Group, User
from app.repositories.abstract.user import AbstractUserRepository
from app.repositories.memory.storage import MemoryStorage


class MemoryUserRepository(AbstractUserRepository):
    """Memory implementation of user repository."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    def get_user_by_id(self, user_id: UUID) -> User | None:
        return self.storage.users.get(user_id)

    def get_user_by_username(self, username: str) -> User | None:
        return self.storage.users_by_username.get(username)

    def create_user(self, name: str, username: str, password_hash: str) -> User:
        user = User(
            id=uuid4(),
            name=name,
            username=username,
            password_hash=password_hash,
            verified=False,
            is_admin=False,
        )
        self.storage.users[user.id] = user
        self.storage.users_by_username[username] = user
        return user

    def get_all_users(self) -> list[User]:
        return list(self.storage.users.values())

    def get_user_groups(self, user: User) -> list[Group]:
        user_groups = []
        for group_id, member_ids in self.storage.group_memberships.items():
            if user.id in member_ids:
                group = self.storage.groups.get(group_id)
                if group:
                    # Set up relationships for compatibility
                    group.creator = self.storage.users.get(group.created_by)
                    group.members = [
                        self.storage.users.get(uid) for uid in member_ids if uid in self.storage.users
                    ]
                    user_groups.append(group)
        return user_groups

    def update_user(self, user_id: UUID, **fields) -> User | None:
        """Update user fields. Returns updated user or None if not found."""
        user = self.storage.users.get(user_id)
        if not user:
            return None

        # If username is being changed, update the username index
        if 'username' in fields:
            old_username = user.username
            new_username = fields['username']

            # Remove old username from index
            if old_username in self.storage.users_by_username:
                del self.storage.users_by_username[old_username]

            # Add new username to index
            self.storage.users_by_username[new_username] = user

        for key, value in fields.items():
            if hasattr(user, key):
                setattr(user, key, value)

        return user

    def delete_user(self, user_id: UUID) -> bool:
        """Delete a user. Returns True if deleted, False if not found."""
        if user_id not in self.storage.users:
            return False

        del self.storage.users[user_id]
        return True

    def verify_password(self, password: str, stored_hash: str) -> bool:
        # In memory mode, accept any password for ease of testing
        return True

    def get_user_stats(self, user_id: UUID) -> dict:
        """Get user statistics including runs, bids, and spending."""
        # Get total quantity bought and money spent from picked-up bids
        total_quantity = 0.0
        total_spent = 0.0

        for bid in self.storage.bids.values():
            participation = self.storage.participations.get(bid.participation_id)
            if (
                participation
                and participation.user_id == user_id
                and bid.is_picked_up
                and bid.distributed_quantity
                and bid.distributed_price_per_unit
            ):
                total_quantity += float(bid.distributed_quantity)
                total_spent += float(bid.distributed_quantity * bid.distributed_price_per_unit)

        # Get runs participated count (distinct runs)
        user_participations = [p for p in self.storage.participations.values() if p.user_id == user_id]
        runs_participated = len({p.run_id for p in user_participations})

        # Get runs where user was helper
        runs_helped = sum(1 for p in user_participations if p.is_helper)

        # Get runs where user was leader
        runs_led = sum(1 for p in user_participations if p.is_leader)

        # Get groups count
        groups_count = sum(
            1 for group_id, members in self.storage.group_memberships.items() if user_id in members
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
        count = 0
        for participation in self.storage.participations.values():
            if participation.user_id == old_user_id:
                participation.user_id = new_user_id
                count += 1
        return count

    def bulk_update_group_creator(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update group creator from old user to new user. Returns count of updated records."""
        count = 0
        for group in self.storage.groups.values():
            if group.created_by == old_user_id:
                group.created_by = new_user_id
                count += 1
        return count

    def bulk_update_product_creator(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update product creator from old user to new user. Returns count of updated records."""
        count = 0
        for product in self.storage.products.values():
            if product.created_by == old_user_id:
                product.created_by = new_user_id
                count += 1
        return count

    def bulk_update_product_verifier(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update product verifier from old user to new user. Returns count of updated records."""
        count = 0
        for product in self.storage.products.values():
            if product.verified_by == old_user_id:
                product.verified_by = new_user_id
                count += 1
        return count

    def bulk_update_store_creator(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update store creator from old user to new user. Returns count of updated records."""
        count = 0
        for store in self.storage.stores.values():
            if store.created_by == old_user_id:
                store.created_by = new_user_id
                count += 1
        return count

    def bulk_update_store_verifier(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update store verifier from old user to new user. Returns count of updated records."""
        count = 0
        for store in self.storage.stores.values():
            if store.verified_by == old_user_id:
                store.verified_by = new_user_id
                count += 1
        return count

    def bulk_update_product_availability_creator(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update product availability creator from old user to new user. Returns count of updated records."""
        count = 0
        for avail in self.storage.product_availabilities.values():
            if avail.created_by == old_user_id:
                avail.created_by = new_user_id
                count += 1
        return count

    def bulk_update_notifications(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update notifications from old user to new user. Returns count of updated records."""
        count = 0
        for notification in self.storage.notifications.values():
            if notification.user_id == old_user_id:
                notification.user_id = new_user_id
                count += 1
        return count

    def bulk_update_reassignment_from_user(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update reassignment requests from_user from old user to new user. Returns count of updated records."""
        count = 0
        for request in self.storage.reassignment_requests.values():
            if request.from_user_id == old_user_id:
                request.from_user_id = new_user_id
                count += 1
        return count

    def bulk_update_reassignment_to_user(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Update reassignment requests to_user from old user to new user. Returns count of updated records."""
        count = 0
        for request in self.storage.reassignment_requests.values():
            if request.to_user_id == old_user_id:
                request.to_user_id = new_user_id
                count += 1
        return count

    def transfer_group_admin_status(self, old_user_id: UUID, new_user_id: UUID) -> int:
        """Transfer group admin status from old user to new user. Returns count of updated groups."""
        count = 0
        # Find groups where old user is admin
        for group_id in list(self.storage.group_memberships.keys()):
            old_user_is_admin = self.storage.group_admin_status.get((group_id, old_user_id), False)
            if old_user_is_admin:
                # Check if new user is a member of this group
                if new_user_id in self.storage.group_memberships.get(group_id, []):
                    # Make new user admin in this group
                    self.storage.group_admin_status[(group_id, new_user_id)] = True
                    count += 1
        return count

    def check_overlapping_run_participations(self, user1_id: UUID, user2_id: UUID) -> list[UUID]:
        """Check if two users participate in any of the same runs. Returns list of overlapping run IDs."""
        user1_runs = {p.run_id for p in self.storage.participations.values() if p.user_id == user1_id}
        user2_runs = {p.run_id for p in self.storage.participations.values() if p.user_id == user2_id}
        return list(user1_runs & user2_runs)
