"""Unit tests for MemoryUserRepository.

Tests cover:
- User creation (create_user)
- User retrieval by ID (get_user_by_id)
- User retrieval by username (get_user_by_username)
- User updates (update_user)
- User deletion (delete_user)
- List all users (get_all_users)
- Get user groups (get_user_groups)
- Get user stats (get_user_stats)
- Bulk update operations
- Edge cases and data integrity
"""

from uuid import UUID, uuid4

import pytest

from app.core.models import (
    Group,
    RunParticipation,
)
from app.repositories.memory.storage import MemoryStorage
from app.repositories.memory.user import MemoryUserRepository


@pytest.fixture
def storage():
    """Create fresh memory storage for each test."""
    storage = MemoryStorage()
    # Clear all data
    storage.users.clear()
    storage.users_by_username.clear()
    storage.groups.clear()
    storage.group_memberships.clear()
    storage.group_admin_status.clear()
    storage.participations.clear()
    storage.bids.clear()
    storage.runs.clear()
    yield storage
    # Clean up after test
    storage.users.clear()
    storage.users_by_username.clear()
    storage.groups.clear()
    storage.group_memberships.clear()
    storage.group_admin_status.clear()
    storage.participations.clear()
    storage.bids.clear()
    storage.runs.clear()


@pytest.fixture
def repo(storage):
    """Create repository instance with fresh storage."""
    return MemoryUserRepository(storage)


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'name': 'John Doe',
        'username': 'johndoe',
        'password_hash': 'hashed_password_123',
    }


class TestCreateUser:
    """Test create_user() method."""

    def test_create_user_with_required_fields(self, repo, sample_user_data):
        """Test creating user with all required fields."""
        user = repo.create_user(**sample_user_data)

        assert user is not None
        assert user.name == sample_user_data['name']
        assert user.username == sample_user_data['username']
        assert user.password_hash == sample_user_data['password_hash']

    def test_created_user_has_uuid(self, repo, sample_user_data):
        """Test created user has correct ID (UUID)."""
        user = repo.create_user(**sample_user_data)

        assert user.id is not None
        assert isinstance(user.id, UUID)

    def test_created_user_is_stored_and_retrievable(self, repo, sample_user_data):
        """Test created user is stored and retrievable."""
        user = repo.create_user(**sample_user_data)

        retrieved = repo.get_user_by_id(user.id)
        assert retrieved is not None
        assert retrieved.id == user.id
        assert retrieved.username == user.username

    def test_created_user_has_default_values(self, repo, sample_user_data):
        """Test created user has default values (is_admin=False, verified=False)."""
        user = repo.create_user(**sample_user_data)

        assert user.is_admin is False
        assert user.verified is False

    def test_password_hash_is_stored(self, repo, sample_user_data):
        """Test password_hash is stored correctly."""
        user = repo.create_user(**sample_user_data)

        assert user.password_hash == sample_user_data['password_hash']
        retrieved = repo.get_user_by_id(user.id)
        assert retrieved.password_hash == sample_user_data['password_hash']

    def test_creating_multiple_users_different_ids(self, repo):
        """Test creating multiple users generates different IDs."""
        user1 = repo.create_user('User One', 'user1', 'hash1')
        user2 = repo.create_user('User Two', 'user2', 'hash2')

        assert user1.id != user2.id
        assert user1.username != user2.username

    def test_create_user_username_index_updated(self, repo, sample_user_data):
        """Test user is indexed by username."""
        user = repo.create_user(**sample_user_data)

        retrieved = repo.get_user_by_username(sample_user_data['username'])
        assert retrieved is not None
        assert retrieved.id == user.id


class TestGetUserById:
    """Test get_user_by_id() method."""

    def test_get_existing_user_by_id(self, repo, sample_user_data):
        """Test getting existing user by ID."""
        user = repo.create_user(**sample_user_data)

        retrieved = repo.get_user_by_id(user.id)
        assert retrieved is not None
        assert retrieved.id == user.id
        assert retrieved.username == user.username

    def test_get_nonexistent_user_returns_none(self, repo):
        """Test getting non-existent user returns None."""
        fake_id = uuid4()

        result = repo.get_user_by_id(fake_id)
        assert result is None

    def test_get_user_by_id_after_creation(self, repo, sample_user_data):
        """Test getting user immediately after creation."""
        user = repo.create_user(**sample_user_data)
        retrieved = repo.get_user_by_id(user.id)

        assert retrieved is not None
        assert retrieved.id == user.id

    def test_get_user_by_id_after_update(self, repo, sample_user_data):
        """Test getting user after update returns updated data."""
        user = repo.create_user(**sample_user_data)
        repo.update_user(user.id, name='Updated Name')

        retrieved = repo.get_user_by_id(user.id)
        assert retrieved.name == 'Updated Name'


class TestGetUserByUsername:
    """Test get_user_by_username() method."""

    def test_get_user_by_username(self, repo, sample_user_data):
        """Test getting user by username."""
        user = repo.create_user(**sample_user_data)

        retrieved = repo.get_user_by_username(sample_user_data['username'])
        assert retrieved is not None
        assert retrieved.id == user.id
        assert retrieved.username == sample_user_data['username']

    def test_get_nonexistent_username_returns_none(self, repo):
        """Test non-existent username returns None."""
        result = repo.get_user_by_username('nonexistent')
        assert result is None

    def test_username_case_sensitive(self, repo):
        """Test username lookup is case-sensitive."""
        repo.create_user('User', 'TestUser', 'hash')

        # Exact match should work
        assert repo.get_user_by_username('TestUser') is not None

        # Different case should not match
        assert repo.get_user_by_username('testuser') is None
        assert repo.get_user_by_username('TESTUSER') is None

    def test_get_user_by_username_after_update(self, repo, sample_user_data):
        """Test getting user by new username after update."""
        user = repo.create_user(**sample_user_data)
        new_username = 'newusername'

        repo.update_user(user.id, username=new_username)

        # Old username should not work
        assert repo.get_user_by_username(sample_user_data['username']) is None

        # New username should work
        retrieved = repo.get_user_by_username(new_username)
        assert retrieved is not None
        assert retrieved.id == user.id


class TestUpdateUser:
    """Test update_user() method."""

    def test_update_user_name(self, repo, sample_user_data):
        """Test updating user name."""
        user = repo.create_user(**sample_user_data)
        new_name = 'Jane Smith'

        updated = repo.update_user(user.id, name=new_name)

        assert updated is not None
        assert updated.name == new_name
        assert updated.id == user.id

    def test_update_user_password_hash(self, repo, sample_user_data):
        """Test updating user password_hash."""
        user = repo.create_user(**sample_user_data)
        new_hash = 'new_hashed_password'

        updated = repo.update_user(user.id, password_hash=new_hash)

        assert updated.password_hash == new_hash

    def test_update_user_is_admin(self, repo, sample_user_data):
        """Test updating user is_admin flag."""
        user = repo.create_user(**sample_user_data)

        updated = repo.update_user(user.id, is_admin=True)

        assert updated.is_admin is True

    def test_update_user_verified(self, repo, sample_user_data):
        """Test updating user verified flag."""
        user = repo.create_user(**sample_user_data)

        updated = repo.update_user(user.id, verified=True)

        assert updated.verified is True

    def test_update_nonexistent_user_returns_none(self, repo):
        """Test updating non-existent user returns None."""
        fake_id = uuid4()

        result = repo.update_user(fake_id, name='New Name')
        assert result is None

    def test_update_partial_fields(self, repo, sample_user_data):
        """Test partial updates (only some fields)."""
        user = repo.create_user(**sample_user_data)
        original_username = user.username

        updated = repo.update_user(user.id, name='New Name')

        assert updated.name == 'New Name'
        assert updated.username == original_username  # Unchanged

    def test_update_multiple_fields(self, repo, sample_user_data):
        """Test updating multiple fields at once."""
        user = repo.create_user(**sample_user_data)

        updated = repo.update_user(user.id, name='New Name', is_admin=True, verified=True)

        assert updated.name == 'New Name'
        assert updated.is_admin is True
        assert updated.verified is True

    def test_update_username_updates_index(self, repo, sample_user_data):
        """Test updating username properly updates username index."""
        user = repo.create_user(**sample_user_data)
        new_username = 'new_username'

        repo.update_user(user.id, username=new_username)

        # Old username should not work
        assert repo.get_user_by_username(sample_user_data['username']) is None

        # New username should work
        retrieved = repo.get_user_by_username(new_username)
        assert retrieved is not None
        assert retrieved.id == user.id

    def test_updated_fields_are_persisted(self, repo, sample_user_data):
        """Test updated fields are persisted."""
        user = repo.create_user(**sample_user_data)
        repo.update_user(user.id, name='Updated Name', is_admin=True)

        # Retrieve again to verify persistence
        retrieved = repo.get_user_by_id(user.id)
        assert retrieved.name == 'Updated Name'
        assert retrieved.is_admin is True


class TestDeleteUser:
    """Test delete_user() method."""

    def test_delete_existing_user(self, repo, sample_user_data):
        """Test deleting existing user."""
        user = repo.create_user(**sample_user_data)

        result = repo.delete_user(user.id)

        assert result is True

    def test_user_not_retrievable_after_deletion(self, repo, sample_user_data):
        """Test user not retrievable after deletion."""
        user = repo.create_user(**sample_user_data)
        repo.delete_user(user.id)

        retrieved = repo.get_user_by_id(user.id)
        assert retrieved is None

    def test_delete_nonexistent_user_returns_false(self, repo):
        """Test deleting non-existent user returns False."""
        fake_id = uuid4()

        result = repo.delete_user(fake_id)
        assert result is False

    def test_deleting_twice_returns_false_second_time(self, repo, sample_user_data):
        """Test deleting twice returns False second time."""
        user = repo.create_user(**sample_user_data)

        first_delete = repo.delete_user(user.id)
        second_delete = repo.delete_user(user.id)

        assert first_delete is True
        assert second_delete is False

    def test_delete_by_id(self, repo, sample_user_data):
        """Test delete by ID."""
        user = repo.create_user(**sample_user_data)
        user_id = user.id

        repo.delete_user(user_id)

        assert repo.get_user_by_id(user_id) is None


class TestGetAllUsers:
    """Test get_all_users() method."""

    def test_list_all_with_empty_repository(self, repo):
        """Test list_all with empty repository."""
        users = repo.get_all_users()

        assert users == []
        assert len(users) == 0

    def test_list_all_after_creating_multiple_users(self, repo):
        """Test list_all after creating multiple users."""
        user1 = repo.create_user('User 1', 'user1', 'hash1')
        user2 = repo.create_user('User 2', 'user2', 'hash2')
        user3 = repo.create_user('User 3', 'user3', 'hash3')

        users = repo.get_all_users()

        assert len(users) == 3
        user_ids = {u.id for u in users}
        assert user1.id in user_ids
        assert user2.id in user_ids
        assert user3.id in user_ids

    def test_list_all_returns_all_users(self, repo):
        """Test list_all returns all users."""
        created_users = []
        for i in range(5):
            user = repo.create_user(f'User {i}', f'user{i}', f'hash{i}')
            created_users.append(user)

        users = repo.get_all_users()

        assert len(users) == 5
        for created in created_users:
            assert any(u.id == created.id for u in users)

    def test_list_all_includes_all_user_fields(self, repo, sample_user_data):
        """Test list_all includes all user fields."""
        user = repo.create_user(**sample_user_data)

        users = repo.get_all_users()

        assert len(users) == 1
        retrieved = users[0]
        assert retrieved.id == user.id
        assert retrieved.name == user.name
        assert retrieved.username == user.username
        assert retrieved.password_hash == user.password_hash
        assert retrieved.is_admin == user.is_admin
        assert retrieved.verified == user.verified

    def test_list_all_count_matches_created(self, repo):
        """Test list_all count matches number created."""
        count = 10
        for i in range(count):
            repo.create_user(f'User {i}', f'user{i}', f'hash{i}')

        users = repo.get_all_users()

        assert len(users) == count

    def test_list_all_after_deletion(self, repo):
        """Test list_all after deletion (count decreases)."""
        user1 = repo.create_user('User 1', 'user1', 'hash1')
        user2 = repo.create_user('User 2', 'user2', 'hash2')
        user3 = repo.create_user('User 3', 'user3', 'hash3')

        assert len(repo.get_all_users()) == 3

        repo.delete_user(user2.id)

        users = repo.get_all_users()
        assert len(users) == 2
        user_ids = {u.id for u in users}
        assert user1.id in user_ids
        assert user2.id not in user_ids
        assert user3.id in user_ids


class TestGetUserGroups:
    """Test get_user_groups() method."""

    def test_get_user_groups_empty(self, repo, storage, sample_user_data):
        """Test getting groups for user with no groups."""
        user = repo.create_user(**sample_user_data)

        groups = repo.get_user_groups(user)

        assert groups == []

    def test_get_user_groups_single_group(self, repo, storage, sample_user_data):
        """Test getting groups for user in one group."""
        user = repo.create_user(**sample_user_data)

        # Create a group
        group_id = uuid4()
        group = Group(id=group_id, name='Test Group', created_by=user.id)
        storage.groups[group_id] = group
        storage.group_memberships[group_id] = [user.id]

        groups = repo.get_user_groups(user)

        assert len(groups) == 1
        assert groups[0].id == group_id
        assert groups[0].name == 'Test Group'

    def test_get_user_groups_multiple_groups(self, repo, storage, sample_user_data):
        """Test getting groups for user in multiple groups."""
        user = repo.create_user(**sample_user_data)

        # Create multiple groups
        group1_id = uuid4()
        group2_id = uuid4()
        group1 = Group(id=group1_id, name='Group 1', created_by=user.id)
        group2 = Group(id=group2_id, name='Group 2', created_by=user.id)

        storage.groups[group1_id] = group1
        storage.groups[group2_id] = group2
        storage.group_memberships[group1_id] = [user.id]
        storage.group_memberships[group2_id] = [user.id]

        groups = repo.get_user_groups(user)

        assert len(groups) == 2
        group_names = {g.name for g in groups}
        assert 'Group 1' in group_names
        assert 'Group 2' in group_names


class TestGetUserStats:
    """Test get_user_stats() method."""

    def test_get_user_stats_empty(self, repo, sample_user_data):
        """Test getting stats for user with no activity."""
        user = repo.create_user(**sample_user_data)

        stats = repo.get_user_stats(user.id)

        assert stats['total_quantity_bought'] == 0.0
        assert stats['total_money_spent'] == 0.0
        assert stats['runs_participated'] == 0
        assert stats['runs_helped'] == 0
        assert stats['runs_led'] == 0
        assert stats['groups_count'] == 0

    def test_get_user_stats_with_groups(self, repo, storage, sample_user_data):
        """Test stats include groups count."""
        user = repo.create_user(**sample_user_data)

        # Add user to groups
        group1_id = uuid4()
        group2_id = uuid4()
        storage.group_memberships[group1_id] = [user.id]
        storage.group_memberships[group2_id] = [user.id]

        stats = repo.get_user_stats(user.id)

        assert stats['groups_count'] == 2

    def test_get_user_stats_with_participations(self, repo, storage, sample_user_data):
        """Test stats include participation counts."""
        user = repo.create_user(**sample_user_data)

        # Create run participations
        run1_id = uuid4()
        run2_id = uuid4()
        part1_id = uuid4()
        part2_id = uuid4()

        part1 = RunParticipation(
            id=part1_id, user_id=user.id, run_id=run1_id, is_helper=False, is_leader=True
        )
        part2 = RunParticipation(
            id=part2_id, user_id=user.id, run_id=run2_id, is_helper=True, is_leader=False
        )

        storage.participations[part1_id] = part1
        storage.participations[part2_id] = part2

        stats = repo.get_user_stats(user.id)

        assert stats['runs_participated'] == 2
        assert stats['runs_helped'] == 1
        assert stats['runs_led'] == 1


class TestBulkUpdateRunParticipations:
    """Test bulk_update_run_participations() method."""

    def test_bulk_update_run_participations(self, repo, storage):
        """Test bulk updating run participations."""
        old_user = repo.create_user('Old User', 'olduser', 'hash1')
        new_user = repo.create_user('New User', 'newuser', 'hash2')

        # Create participations for old user
        part1_id = uuid4()
        part2_id = uuid4()
        part1 = RunParticipation(
            id=part1_id, user_id=old_user.id, run_id=uuid4(), is_helper=False, is_leader=False
        )
        part2 = RunParticipation(
            id=part2_id, user_id=old_user.id, run_id=uuid4(), is_helper=False, is_leader=False
        )

        storage.participations[part1_id] = part1
        storage.participations[part2_id] = part2

        count = repo.bulk_update_run_participations(old_user.id, new_user.id)

        assert count == 2
        assert storage.participations[part1_id].user_id == new_user.id
        assert storage.participations[part2_id].user_id == new_user.id

    def test_bulk_update_run_participations_no_matches(self, repo, storage):
        """Test bulk update with no matching participations."""
        user1 = repo.create_user('User 1', 'user1', 'hash1')
        user2 = repo.create_user('User 2', 'user2', 'hash2')

        count = repo.bulk_update_run_participations(user1.id, user2.id)

        assert count == 0


class TestBulkUpdateGroupCreator:
    """Test bulk_update_group_creator() method."""

    def test_bulk_update_group_creator(self, repo, storage):
        """Test bulk updating group creators."""
        old_user = repo.create_user('Old User', 'olduser', 'hash1')
        new_user = repo.create_user('New User', 'newuser', 'hash2')

        # Create groups created by old user
        group1_id = uuid4()
        group2_id = uuid4()
        group1 = Group(id=group1_id, name='Group 1', created_by=old_user.id)
        group2 = Group(id=group2_id, name='Group 2', created_by=old_user.id)

        storage.groups[group1_id] = group1
        storage.groups[group2_id] = group2

        count = repo.bulk_update_group_creator(old_user.id, new_user.id)

        assert count == 2
        assert storage.groups[group1_id].created_by == new_user.id
        assert storage.groups[group2_id].created_by == new_user.id


class TestCheckOverlappingRunParticipations:
    """Test check_overlapping_run_participations() method."""

    def test_no_overlapping_participations(self, repo, storage):
        """Test users with no overlapping run participations."""
        user1 = repo.create_user('User 1', 'user1', 'hash1')
        user2 = repo.create_user('User 2', 'user2', 'hash2')

        overlaps = repo.check_overlapping_run_participations(user1.id, user2.id)

        assert overlaps == []

    def test_overlapping_participations(self, repo, storage):
        """Test users with overlapping run participations."""
        user1 = repo.create_user('User 1', 'user1', 'hash1')
        user2 = repo.create_user('User 2', 'user2', 'hash2')

        # Create overlapping runs
        run1_id = uuid4()
        run2_id = uuid4()
        run3_id = uuid4()

        # User1 in runs 1 and 2
        part1 = RunParticipation(
            id=uuid4(), user_id=user1.id, run_id=run1_id, is_helper=False, is_leader=False
        )
        part2 = RunParticipation(
            id=uuid4(), user_id=user1.id, run_id=run2_id, is_helper=False, is_leader=False
        )

        # User2 in runs 2 and 3
        part3 = RunParticipation(
            id=uuid4(), user_id=user2.id, run_id=run2_id, is_helper=False, is_leader=False
        )
        part4 = RunParticipation(
            id=uuid4(), user_id=user2.id, run_id=run3_id, is_helper=False, is_leader=False
        )

        storage.participations[part1.id] = part1
        storage.participations[part2.id] = part2
        storage.participations[part3.id] = part3
        storage.participations[part4.id] = part4

        overlaps = repo.check_overlapping_run_participations(user1.id, user2.id)

        assert len(overlaps) == 1
        assert run2_id in overlaps


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_long_username(self, repo):
        """Test with very long username."""
        long_username = 'a' * 1000
        repo.create_user('User', long_username, 'hash')

        retrieved = repo.get_user_by_username(long_username)
        assert retrieved is not None
        assert retrieved.username == long_username

    def test_special_characters_in_name(self, repo):
        """Test with special characters in names."""
        special_name = "O'Brien-Smith (Jr.)"
        user = repo.create_user(special_name, 'obrien', 'hash')

        assert user.name == special_name
        retrieved = repo.get_user_by_id(user.id)
        assert retrieved.name == special_name

    def test_unicode_characters(self, repo):
        """Test with unicode characters."""
        unicode_name = '测试用户'
        unicode_username = 'user_测试'
        user = repo.create_user(unicode_name, unicode_username, 'hash')

        assert user.name == unicode_name
        assert user.username == unicode_username
        retrieved = repo.get_user_by_username(unicode_username)
        assert retrieved is not None

    def test_concurrent_operations(self, repo):
        """Test creating multiple users (simulating concurrent operations)."""
        users = []
        for i in range(100):
            user = repo.create_user(f'User {i}', f'user{i}', f'hash{i}')
            users.append(user)

        # Verify all users exist
        all_users = repo.get_all_users()
        assert len(all_users) == 100

        # Verify all IDs are unique
        ids = [u.id for u in all_users]
        assert len(ids) == len(set(ids))


class TestDataIntegrity:
    """Test data integrity and isolation."""

    def test_user_object_has_expected_fields(self, repo, sample_user_data):
        """Test user object has all expected fields."""
        user = repo.create_user(**sample_user_data)

        assert hasattr(user, 'id')
        assert hasattr(user, 'name')
        assert hasattr(user, 'username')
        assert hasattr(user, 'password_hash')
        assert hasattr(user, 'is_admin')
        assert hasattr(user, 'verified')

    def test_user_object_is_not_none(self, repo, sample_user_data):
        """Test user object is not None."""
        user = repo.create_user(**sample_user_data)

        assert user is not None
        retrieved = repo.get_user_by_id(user.id)
        assert retrieved is not None

    def test_repository_isolation(self, storage):
        """Test fresh repository instance per test (via fixture)."""
        # This test verifies the fixture works correctly
        assert len(storage.users) == 0
        assert len(storage.users_by_username) == 0

    def test_multiple_repositories_share_storage(self, storage):
        """Test multiple repository instances share the same storage."""
        repo1 = MemoryUserRepository(storage)
        repo2 = MemoryUserRepository(storage)

        user = repo1.create_user('User', 'username', 'hash')

        # Both repositories should see the same user
        assert repo2.get_user_by_id(user.id) is not None
        assert repo2.get_user_by_username('username') is not None


class TestVerifyPassword:
    """Test verify_password() method."""

    def test_verify_password_correct(self, repo):
        """Test verifying correct password."""
        # This method delegates to auth module, just test it's callable
        from app.infrastructure.auth import hash_password

        password = 'mypassword'
        hashed = hash_password(password)

        result = repo.verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self, repo):
        """Test verifying incorrect password."""
        from app.infrastructure.auth import hash_password

        password = 'mypassword'
        hashed = hash_password(password)

        result = repo.verify_password('wrongpassword', hashed)
        assert result is False


class TestTransferGroupAdminStatus:
    """Test transfer_group_admin_status() method."""

    def test_transfer_group_admin_status(self, repo, storage):
        """Test transferring group admin status."""
        old_admin = repo.create_user('Old Admin', 'oldadmin', 'hash1')
        new_admin = repo.create_user('New Admin', 'newadmin', 'hash2')

        # Create a group where old_admin is admin
        group_id = uuid4()
        group = Group(id=group_id, name='Test Group', created_by=old_admin.id)
        storage.groups[group_id] = group
        storage.group_memberships[group_id] = [old_admin.id, new_admin.id]
        storage.group_admin_status[(group_id, old_admin.id)] = True

        count = repo.transfer_group_admin_status(old_admin.id, new_admin.id)

        assert count == 1
        assert storage.group_admin_status[(group_id, new_admin.id)] is True

    def test_transfer_group_admin_status_not_member(self, repo, storage):
        """Test transfer fails if new user not in group."""
        old_admin = repo.create_user('Old Admin', 'oldadmin', 'hash1')
        new_admin = repo.create_user('New Admin', 'newadmin', 'hash2')

        # Create a group where new_admin is NOT a member
        group_id = uuid4()
        group = Group(id=group_id, name='Test Group', created_by=old_admin.id)
        storage.groups[group_id] = group
        storage.group_memberships[group_id] = [old_admin.id]
        storage.group_admin_status[(group_id, old_admin.id)] = True

        count = repo.transfer_group_admin_status(old_admin.id, new_admin.id)

        # Should not transfer since new_admin is not a member
        assert count == 0
