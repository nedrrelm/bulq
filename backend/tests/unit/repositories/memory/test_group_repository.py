"""Unit tests for MemoryGroupRepository.

Tests cover:
- Group creation (create_group)
- Group retrieval by ID (get_group_by_id)
- Group retrieval by invite token (get_group_by_invite_token)
- Invite token regeneration (regenerate_group_invite_token)
- Joining allowed update (update_group_joining_allowed)
- List all groups (get_all_groups)
- Add member (add_group_member)
- Remove member (remove_group_member)
- Get members with admin status (get_group_members_with_admin_status)
- Is user group admin (is_user_group_admin)
- Set group member admin (set_group_member_admin)
- Edge cases and data integrity
"""

from uuid import UUID, uuid4

import pytest

from app.core.models import User
from app.repositories.memory.group import MemoryGroupRepository
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
    """Create group repository instance with fresh storage."""
    return MemoryGroupRepository(storage)


@pytest.fixture
def user_repo(storage):
    """Create user repository instance with fresh storage."""
    return MemoryUserRepository(storage)


@pytest.fixture
def sample_user(user_repo):
    """Create a sample user for testing."""
    return user_repo.create_user('Test User', 'testuser', 'hashed_password')


@pytest.fixture
def sample_users(user_repo):
    """Create multiple sample users for testing."""
    return [user_repo.create_user(f'User {i}', f'user{i}', f'hash{i}') for i in range(1, 4)]


class TestCreateGroup:
    """Test create_group() method."""

    def test_create_group_with_required_fields(self, repo, sample_user):
        """Test creating group with all required fields."""
        group = repo.create_group('Test Group', sample_user.id)

        assert group is not None
        assert group.name == 'Test Group'
        assert group.created_by == sample_user.id

    def test_created_group_has_uuid(self, repo, sample_user):
        """Test created group has correct ID (UUID)."""
        group = repo.create_group('Test Group', sample_user.id)

        assert group.id is not None
        assert isinstance(group.id, UUID)

    def test_created_group_is_stored_and_retrievable(self, repo, sample_user):
        """Test created group is stored and retrievable."""
        group = repo.create_group('Test Group', sample_user.id)

        retrieved = repo.get_group_by_id(group.id)
        assert retrieved is not None
        assert retrieved.id == group.id
        assert retrieved.name == group.name

    def test_created_group_has_default_values(self, repo, sample_user):
        """Test created group has default values (is_joining_allowed=True)."""
        group = repo.create_group('Test Group', sample_user.id)

        assert group.is_joining_allowed is True

    def test_invite_token_is_generated(self, repo, sample_user):
        """Test invite_token is generated."""
        group = repo.create_group('Test Group', sample_user.id)

        assert group.invite_token is not None
        assert len(group.invite_token) > 0

    def test_invite_token_is_unique(self, repo, sample_user):
        """Test invite_token is unique for each group."""
        group1 = repo.create_group('Group 1', sample_user.id)
        group2 = repo.create_group('Group 2', sample_user.id)

        assert group1.invite_token != group2.invite_token

    def test_creating_multiple_groups(self, repo, sample_user):
        """Test creating multiple groups generates different IDs."""
        group1 = repo.create_group('Group 1', sample_user.id)
        group2 = repo.create_group('Group 2', sample_user.id)
        group3 = repo.create_group('Group 3', sample_user.id)

        assert group1.id != group2.id
        assert group2.id != group3.id
        assert group1.id != group3.id

    def test_group_memberships_initialized(self, repo, storage, sample_user):
        """Test group memberships list is initialized on creation."""
        group = repo.create_group('Test Group', sample_user.id)

        assert group.id in storage.group_memberships
        assert storage.group_memberships[group.id] == []


class TestGetGroupById:
    """Test get_group_by_id() method."""

    def test_get_existing_group_by_id(self, repo, sample_user):
        """Test getting existing group by ID."""
        group = repo.create_group('Test Group', sample_user.id)

        retrieved = repo.get_group_by_id(group.id)
        assert retrieved is not None
        assert retrieved.id == group.id
        assert retrieved.name == group.name

    def test_get_nonexistent_group_returns_none(self, repo):
        """Test getting non-existent group returns None."""
        fake_id = uuid4()

        result = repo.get_group_by_id(fake_id)
        assert result is None

    def test_get_group_with_creator_relationship(self, repo, sample_user):
        """Test getting group includes creator relationship."""
        group = repo.create_group('Test Group', sample_user.id)

        retrieved = repo.get_group_by_id(group.id)
        assert retrieved.creator is not None
        assert retrieved.creator.id == sample_user.id
        assert retrieved.creator.name == sample_user.name

    def test_get_group_with_members_relationship(self, repo, sample_user, sample_users):
        """Test getting group includes members relationship."""
        group = repo.create_group('Test Group', sample_user.id)

        # Add members
        for user in sample_users:
            repo.add_group_member(group.id, user)

        retrieved = repo.get_group_by_id(group.id)
        assert retrieved.members is not None
        assert len(retrieved.members) == len(sample_users)
        member_ids = {m.id for m in retrieved.members}
        for user in sample_users:
            assert user.id in member_ids

    def test_get_group_with_none_id(self, repo):
        """Test getting group with None ID."""
        result = repo.get_group_by_id(None)
        assert result is None


class TestGetGroupByInviteToken:
    """Test get_group_by_invite_token() method."""

    def test_get_group_by_invite_token(self, repo, sample_user):
        """Test getting group by invite token."""
        group = repo.create_group('Test Group', sample_user.id)

        retrieved = repo.get_group_by_invite_token(group.invite_token)
        assert retrieved is not None
        assert retrieved.id == group.id
        assert retrieved.name == group.name
        assert retrieved.invite_token == group.invite_token

    def test_get_nonexistent_token_returns_none(self, repo):
        """Test non-existent token returns None."""
        result = repo.get_group_by_invite_token('nonexistent-token')
        assert result is None

    def test_get_group_by_empty_token(self, repo):
        """Test with empty string token."""
        result = repo.get_group_by_invite_token('')
        assert result is None

    def test_token_uniqueness(self, repo, sample_user):
        """Test each group has unique token."""
        groups = [repo.create_group(f'Group {i}', sample_user.id) for i in range(5)]
        tokens = [g.invite_token for g in groups]

        # All tokens should be unique
        assert len(tokens) == len(set(tokens))

        # Each token should retrieve correct group
        for group in groups:
            retrieved = repo.get_group_by_invite_token(group.invite_token)
            assert retrieved.id == group.id

    def test_get_group_with_creator_relationship(self, repo, sample_user):
        """Test getting group by token includes creator relationship."""
        group = repo.create_group('Test Group', sample_user.id)

        retrieved = repo.get_group_by_invite_token(group.invite_token)
        assert retrieved.creator is not None
        assert retrieved.creator.id == sample_user.id

    def test_get_group_with_members_relationship(self, repo, sample_user, sample_users):
        """Test getting group by token includes members relationship."""
        group = repo.create_group('Test Group', sample_user.id)

        # Add members
        for user in sample_users:
            repo.add_group_member(group.id, user)

        retrieved = repo.get_group_by_invite_token(group.invite_token)
        assert len(retrieved.members) == len(sample_users)


class TestRegenerateGroupInviteToken:
    """Test regenerate_group_invite_token() method."""

    def test_regenerate_invite_token(self, repo, sample_user):
        """Test regenerating invite token."""
        group = repo.create_group('Test Group', sample_user.id)
        old_token = group.invite_token

        new_token = repo.regenerate_group_invite_token(group.id)

        assert new_token is not None
        assert new_token != old_token

    def test_regenerated_token_is_persisted(self, repo, sample_user):
        """Test regenerated token is persisted."""
        group = repo.create_group('Test Group', sample_user.id)
        old_token = group.invite_token

        new_token = repo.regenerate_group_invite_token(group.id)

        # Old token should not work
        retrieved = repo.get_group_by_invite_token(old_token)
        assert retrieved is None

        # New token should work
        retrieved = repo.get_group_by_invite_token(new_token)
        assert retrieved is not None
        assert retrieved.id == group.id

    def test_regenerate_nonexistent_group_returns_none(self, repo):
        """Test regenerating token for non-existent group returns None."""
        fake_id = uuid4()

        result = repo.regenerate_group_invite_token(fake_id)
        assert result is None

    def test_regenerate_token_multiple_times(self, repo, sample_user):
        """Test regenerating token multiple times."""
        group = repo.create_group('Test Group', sample_user.id)
        tokens = [group.invite_token]

        for _ in range(3):
            new_token = repo.regenerate_group_invite_token(group.id)
            tokens.append(new_token)

        # All tokens should be unique
        assert len(tokens) == len(set(tokens))

        # Only last token should work
        for token in tokens[:-1]:
            assert repo.get_group_by_invite_token(token) is None
        assert repo.get_group_by_invite_token(tokens[-1]) is not None


class TestUpdateGroupJoiningAllowed:
    """Test update_group_joining_allowed() method."""

    def test_update_joining_allowed_to_false(self, repo, sample_user):
        """Test updating is_joining_allowed to False."""
        group = repo.create_group('Test Group', sample_user.id)
        assert group.is_joining_allowed is True

        updated = repo.update_group_joining_allowed(group.id, False)

        assert updated is not None
        assert updated.is_joining_allowed is False

    def test_update_joining_allowed_to_true(self, repo, sample_user):
        """Test updating is_joining_allowed to True."""
        group = repo.create_group('Test Group', sample_user.id)
        repo.update_group_joining_allowed(group.id, False)

        updated = repo.update_group_joining_allowed(group.id, True)

        assert updated is not None
        assert updated.is_joining_allowed is True

    def test_updated_field_is_persisted(self, repo, sample_user):
        """Test updated field is persisted."""
        group = repo.create_group('Test Group', sample_user.id)
        repo.update_group_joining_allowed(group.id, False)

        # Retrieve again to verify persistence
        retrieved = repo.get_group_by_id(group.id)
        assert retrieved.is_joining_allowed is False

    def test_update_nonexistent_group_returns_none(self, repo):
        """Test updating non-existent group returns None."""
        fake_id = uuid4()

        result = repo.update_group_joining_allowed(fake_id, False)
        assert result is None


class TestGetAllGroups:
    """Test get_all_groups() method."""

    def test_list_all_with_empty_repository(self, repo):
        """Test list_all with empty repository."""
        groups = repo.get_all_groups()

        assert groups == []
        assert len(groups) == 0

    def test_list_all_after_creating_multiple_groups(self, repo, sample_user):
        """Test list_all after creating multiple groups."""
        group1 = repo.create_group('Group 1', sample_user.id)
        group2 = repo.create_group('Group 2', sample_user.id)
        group3 = repo.create_group('Group 3', sample_user.id)

        groups = repo.get_all_groups()

        assert len(groups) == 3
        group_ids = {g.id for g in groups}
        assert group1.id in group_ids
        assert group2.id in group_ids
        assert group3.id in group_ids

    def test_list_all_includes_all_fields(self, repo, sample_user):
        """Test list_all includes all fields."""
        group = repo.create_group('Test Group', sample_user.id)

        groups = repo.get_all_groups()

        assert len(groups) == 1
        retrieved = groups[0]
        assert retrieved.id == group.id
        assert retrieved.name == group.name
        assert retrieved.created_by == group.created_by
        assert retrieved.invite_token == group.invite_token
        assert retrieved.is_joining_allowed == group.is_joining_allowed

    def test_list_all_count_matches_created(self, repo, sample_user):
        """Test list_all count matches number created."""
        count = 10
        for i in range(count):
            repo.create_group(f'Group {i}', sample_user.id)

        groups = repo.get_all_groups()

        assert len(groups) == count

    def test_list_all_includes_relationships(self, repo, sample_user, sample_users):
        """Test list_all includes creator and members relationships."""
        group = repo.create_group('Test Group', sample_user.id)
        for user in sample_users:
            repo.add_group_member(group.id, user)

        groups = repo.get_all_groups()

        assert len(groups) == 1
        retrieved = groups[0]
        assert retrieved.creator is not None
        assert retrieved.creator.id == sample_user.id
        assert len(retrieved.members) == len(sample_users)


class TestAddGroupMember:
    """Test add_group_member() method."""

    def test_add_user_to_group(self, repo, sample_user, sample_users):
        """Test adding user to group."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]

        result = repo.add_group_member(group.id, user)

        assert result is True

    def test_member_is_retrievable(self, repo, sample_user, sample_users, storage):
        """Test member is retrievable after adding."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]

        repo.add_group_member(group.id, user)

        assert user.id in storage.group_memberships[group.id]

    def test_adding_same_user_twice(self, repo, sample_user, sample_users):
        """Test adding same user twice returns False."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]

        first_add = repo.add_group_member(group.id, user)
        second_add = repo.add_group_member(group.id, user)

        assert first_add is True
        assert second_add is False

    def test_adding_with_group_admin_flag(self, repo, sample_user, sample_users, storage):
        """Test adding with group admin flag."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]

        repo.add_group_member(group.id, user, is_group_admin=True)

        assert storage.group_admin_status[(group.id, user.id)] is True

    def test_adding_without_group_admin_flag(self, repo, sample_user, sample_users, storage):
        """Test adding without group admin flag (default)."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]

        repo.add_group_member(group.id, user)

        assert storage.group_admin_status[(group.id, user.id)] is False

    def test_adding_to_nonexistent_group(self, repo, sample_users):
        """Test adding to non-existent group returns False."""
        fake_id = uuid4()
        user = sample_users[0]

        result = repo.add_group_member(fake_id, user)

        assert result is False

    def test_adding_multiple_users(self, repo, sample_user, sample_users):
        """Test adding multiple users to group."""
        group = repo.create_group('Test Group', sample_user.id)

        for user in sample_users:
            result = repo.add_group_member(group.id, user)
            assert result is True

        retrieved = repo.get_group_by_id(group.id)
        assert len(retrieved.members) == len(sample_users)


class TestRemoveGroupMember:
    """Test remove_group_member() method."""

    def test_remove_existing_member(self, repo, sample_user, sample_users):
        """Test removing existing member."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]
        repo.add_group_member(group.id, user)

        result = repo.remove_group_member(group.id, user.id)

        assert result is True

    def test_member_not_retrievable_after_removal(self, repo, sample_user, sample_users, storage):
        """Test member not retrievable after removal."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]
        repo.add_group_member(group.id, user)

        repo.remove_group_member(group.id, user.id)

        assert user.id not in storage.group_memberships[group.id]

    def test_removing_nonexistent_member(self, repo, sample_user, sample_users):
        """Test removing non-existent member returns False."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]

        result = repo.remove_group_member(group.id, user.id)

        assert result is False

    def test_removing_from_nonexistent_group(self, repo, sample_users):
        """Test removing from non-existent group returns False."""
        fake_id = uuid4()
        user = sample_users[0]

        result = repo.remove_group_member(fake_id, user.id)

        assert result is False

    def test_removing_group_admin(self, repo, sample_user, sample_users, storage):
        """Test removing group admin removes admin status."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]
        repo.add_group_member(group.id, user, is_group_admin=True)

        repo.remove_group_member(group.id, user.id)

        # Admin status should be removed
        assert (group.id, user.id) not in storage.group_admin_status

    def test_membership_count_decreases(self, repo, sample_user, sample_users):
        """Test membership count decreases after removal."""
        group = repo.create_group('Test Group', sample_user.id)

        # Add multiple users
        for user in sample_users:
            repo.add_group_member(group.id, user)

        # Remove one user
        repo.remove_group_member(group.id, sample_users[0].id)

        retrieved = repo.get_group_by_id(group.id)
        assert len(retrieved.members) == len(sample_users) - 1


class TestGetGroupMembersWithAdminStatus:
    """Test get_group_members_with_admin_status() method."""

    def test_get_members_of_group(self, repo, sample_user, sample_users):
        """Test getting members of group."""
        group = repo.create_group('Test Group', sample_user.id)
        for user in sample_users:
            repo.add_group_member(group.id, user)

        members = repo.get_group_members_with_admin_status(group.id)

        assert len(members) == len(sample_users)

    def test_empty_members_list_for_new_group(self, repo, sample_user):
        """Test empty members list for new group."""
        group = repo.create_group('Test Group', sample_user.id)

        members = repo.get_group_members_with_admin_status(group.id)

        assert members == []

    def test_members_after_adding_multiple_users(self, repo, sample_user, sample_users):
        """Test members after adding multiple users."""
        group = repo.create_group('Test Group', sample_user.id)
        for user in sample_users:
            repo.add_group_member(group.id, user)

        members = repo.get_group_members_with_admin_status(group.id)

        assert len(members) == len(sample_users)
        member_ids = {m['id'] for m in members}
        for user in sample_users:
            assert str(user.id) in member_ids

    def test_members_includes_all_user_details(self, repo, sample_user, sample_users):
        """Test members includes all user details."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]
        repo.add_group_member(group.id, user, is_group_admin=True)

        members = repo.get_group_members_with_admin_status(group.id)

        assert len(members) == 1
        member = members[0]
        assert member['id'] == str(user.id)
        assert member['name'] == user.name
        assert member['username'] == user.username
        assert member['is_group_admin'] is True

    def test_members_count_matches_added(self, repo, sample_user, sample_users):
        """Test members count matches added."""
        group = repo.create_group('Test Group', sample_user.id)
        count = 0
        for user in sample_users:
            repo.add_group_member(group.id, user)
            count += 1

        members = repo.get_group_members_with_admin_status(group.id)

        assert len(members) == count

    def test_members_after_removal(self, repo, sample_user, sample_users):
        """Test members after removal."""
        group = repo.create_group('Test Group', sample_user.id)
        for user in sample_users:
            repo.add_group_member(group.id, user)

        repo.remove_group_member(group.id, sample_users[0].id)

        members = repo.get_group_members_with_admin_status(group.id)
        assert len(members) == len(sample_users) - 1

    def test_members_with_mixed_admin_status(self, repo, sample_user, sample_users):
        """Test members with mixed admin status."""
        group = repo.create_group('Test Group', sample_user.id)
        repo.add_group_member(group.id, sample_users[0], is_group_admin=True)
        repo.add_group_member(group.id, sample_users[1], is_group_admin=False)
        repo.add_group_member(group.id, sample_users[2], is_group_admin=True)

        members = repo.get_group_members_with_admin_status(group.id)

        assert len(members) == 3
        admin_count = sum(1 for m in members if m['is_group_admin'])
        assert admin_count == 2

    def test_nonexistent_group_returns_empty_list(self, repo):
        """Test getting members of non-existent group returns empty list."""
        fake_id = uuid4()

        members = repo.get_group_members_with_admin_status(fake_id)

        assert members == []


class TestIsUserGroupAdmin:
    """Test is_user_group_admin() method."""

    def test_is_group_admin_returns_true_for_admin(self, repo, sample_user, sample_users):
        """Test is_user_group_admin returns True for admin."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]
        repo.add_group_member(group.id, user, is_group_admin=True)

        result = repo.is_user_group_admin(group.id, user.id)

        assert result is True

    def test_returns_false_for_non_admin_member(self, repo, sample_user, sample_users):
        """Test returns False for non-admin member."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]
        repo.add_group_member(group.id, user, is_group_admin=False)

        result = repo.is_user_group_admin(group.id, user.id)

        assert result is False

    def test_returns_false_for_non_member(self, repo, sample_user, sample_users):
        """Test returns False for non-member."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]

        result = repo.is_user_group_admin(group.id, user.id)

        assert result is False

    def test_with_none_user_id(self, repo, sample_user):
        """Test with None user_id."""
        group = repo.create_group('Test Group', sample_user.id)

        result = repo.is_user_group_admin(group.id, None)

        assert result is False

    def test_after_setting_admin_flag(self, repo, sample_user, sample_users):
        """Test after setting admin flag."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]
        repo.add_group_member(group.id, user, is_group_admin=False)

        # Initially not admin
        assert repo.is_user_group_admin(group.id, user.id) is False

        # Set as admin
        repo.set_group_member_admin(group.id, user.id, True)

        # Now should be admin
        assert repo.is_user_group_admin(group.id, user.id) is True


class TestSetGroupMemberAdmin:
    """Test set_group_member_admin() method."""

    def test_setting_user_as_group_admin(self, repo, sample_user, sample_users):
        """Test setting user as group admin."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]
        repo.add_group_member(group.id, user, is_group_admin=False)

        result = repo.set_group_member_admin(group.id, user.id, True)

        assert result is True

    def test_admin_flag_is_persisted(self, repo, sample_user, sample_users):
        """Test admin flag is persisted."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]
        repo.add_group_member(group.id, user, is_group_admin=False)

        repo.set_group_member_admin(group.id, user.id, True)

        # Check it's persisted
        assert repo.is_user_group_admin(group.id, user.id) is True

    def test_unsetting_admin_flag(self, repo, sample_user, sample_users):
        """Test unsetting admin flag."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]
        repo.add_group_member(group.id, user, is_group_admin=True)

        result = repo.set_group_member_admin(group.id, user.id, False)

        assert result is True
        assert repo.is_user_group_admin(group.id, user.id) is False

    def test_on_non_member(self, repo, sample_user, sample_users):
        """Test on non-member returns False."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]

        result = repo.set_group_member_admin(group.id, user.id, True)

        assert result is False

    def test_on_nonexistent_group(self, repo, sample_users):
        """Test on non-existent group returns False."""
        fake_id = uuid4()
        user = sample_users[0]

        result = repo.set_group_member_admin(fake_id, user.id, True)

        assert result is False


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_long_group_name(self, repo, sample_user):
        """Test with very long group name."""
        long_name = 'a' * 1000
        group = repo.create_group(long_name, sample_user.id)

        assert group.name == long_name
        retrieved = repo.get_group_by_id(group.id)
        assert retrieved.name == long_name

    def test_special_characters_in_name(self, repo, sample_user):
        """Test with special characters in name."""
        special_name = "O'Brien's Shopping Group (Pro)"
        group = repo.create_group(special_name, sample_user.id)

        assert group.name == special_name
        retrieved = repo.get_group_by_id(group.id)
        assert retrieved.name == special_name

    def test_unicode_characters(self, repo, sample_user):
        """Test with unicode characters."""
        unicode_name = '测试小组 🛒'
        group = repo.create_group(unicode_name, sample_user.id)

        assert group.name == unicode_name
        retrieved = repo.get_group_by_id(group.id)
        assert retrieved.name == unicode_name

    def test_concurrent_operations(self, repo, sample_user):
        """Test creating multiple groups (simulating concurrent operations)."""
        groups = []
        for i in range(100):
            group = repo.create_group(f'Group {i}', sample_user.id)
            groups.append(group)

        # Verify all groups exist
        all_groups = repo.get_all_groups()
        assert len(all_groups) == 100

        # Verify all IDs are unique
        ids = [g.id for g in all_groups]
        assert len(ids) == len(set(ids))

        # Verify all tokens are unique
        tokens = [g.invite_token for g in all_groups]
        assert len(tokens) == len(set(tokens))

    def test_repository_isolation(self, storage):
        """Test fresh repository instance per test (via fixture)."""
        # This test verifies the fixture works correctly
        assert len(storage.groups) == 0
        assert len(storage.group_memberships) == 0

    def test_invite_token_format(self, repo, sample_user):
        """Test invite token format (should be UUID-like)."""
        group = repo.create_group('Test Group', sample_user.id)

        # Token should be a valid UUID string
        try:
            UUID(group.invite_token)
            valid = True
        except ValueError:
            valid = False

        assert valid is True


class TestDataIntegrity:
    """Test data integrity and relationships."""

    def test_group_object_has_expected_fields(self, repo, sample_user):
        """Test group object has expected fields."""
        group = repo.create_group('Test Group', sample_user.id)

        assert hasattr(group, 'id')
        assert hasattr(group, 'name')
        assert hasattr(group, 'created_by')
        assert hasattr(group, 'invite_token')
        assert hasattr(group, 'is_joining_allowed')

    def test_group_object_includes_creator_info(self, repo, sample_user):
        """Test group object includes creator info."""
        group = repo.create_group('Test Group', sample_user.id)

        retrieved = repo.get_group_by_id(group.id)
        assert retrieved.creator is not None
        assert isinstance(retrieved.creator, User)
        assert retrieved.creator.id == sample_user.id
        assert retrieved.creator.name == sample_user.name

    def test_group_object_includes_member_list(self, repo, sample_user, sample_users):
        """Test group object includes member list."""
        group = repo.create_group('Test Group', sample_user.id)
        for user in sample_users:
            repo.add_group_member(group.id, user)

        retrieved = repo.get_group_by_id(group.id)
        assert hasattr(retrieved, 'members')
        assert isinstance(retrieved.members, list)
        assert len(retrieved.members) == len(sample_users)

    def test_membership_relationship_is_bidirectional(
        self, repo, storage, sample_user, sample_users
    ):
        """Test membership relationship is bidirectional."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]

        # Add member
        repo.add_group_member(group.id, user)

        # Check storage has the relationship
        assert user.id in storage.group_memberships[group.id]

        # Check retrieved group has the member
        retrieved = repo.get_group_by_id(group.id)
        member_ids = [m.id for m in retrieved.members]
        assert user.id in member_ids

    def test_multiple_repositories_share_storage(self, storage, sample_user):
        """Test multiple repository instances share the same storage."""
        repo1 = MemoryGroupRepository(storage)
        repo2 = MemoryGroupRepository(storage)

        group = repo1.create_group('Test Group', sample_user.id)

        # Both repositories should see the same group
        assert repo2.get_group_by_id(group.id) is not None
        assert repo2.get_group_by_invite_token(group.invite_token) is not None


class TestMembershipComplexScenarios:
    """Test complex membership scenarios."""

    def test_multiple_groups_same_user(self, repo, sample_user, sample_users):
        """Test user can be member of multiple groups."""
        user = sample_users[0]
        groups = [repo.create_group(f'Group {i}', sample_user.id) for i in range(3)]

        # Add user to all groups
        for group in groups:
            repo.add_group_member(group.id, user)

        # Verify membership in all groups
        for group in groups:
            members = repo.get_group_members_with_admin_status(group.id)
            member_ids = [m['id'] for m in members]
            assert str(user.id) in member_ids

    def test_admin_in_one_group_not_admin_in_another(self, repo, sample_user, sample_users):
        """Test user can be admin in one group but not another."""
        user = sample_users[0]
        group1 = repo.create_group('Group 1', sample_user.id)
        group2 = repo.create_group('Group 2', sample_user.id)

        repo.add_group_member(group1.id, user, is_group_admin=True)
        repo.add_group_member(group2.id, user, is_group_admin=False)

        assert repo.is_user_group_admin(group1.id, user.id) is True
        assert repo.is_user_group_admin(group2.id, user.id) is False

    def test_removing_from_one_group_keeps_other_memberships(self, repo, sample_user, sample_users):
        """Test removing from one group doesn't affect other memberships."""
        user = sample_users[0]
        group1 = repo.create_group('Group 1', sample_user.id)
        group2 = repo.create_group('Group 2', sample_user.id)

        repo.add_group_member(group1.id, user)
        repo.add_group_member(group2.id, user)

        # Remove from group1
        repo.remove_group_member(group1.id, user.id)

        # Should still be in group2
        members2 = repo.get_group_members_with_admin_status(group2.id)
        member_ids = [m['id'] for m in members2]
        assert str(user.id) in member_ids

    def test_all_users_as_admins(self, repo, sample_user, sample_users):
        """Test adding all users as admins."""
        group = repo.create_group('Test Group', sample_user.id)

        for user in sample_users:
            repo.add_group_member(group.id, user, is_group_admin=True)

        members = repo.get_group_members_with_admin_status(group.id)
        for member in members:
            assert member['is_group_admin'] is True

    def test_toggling_admin_status_multiple_times(self, repo, sample_user, sample_users):
        """Test toggling admin status multiple times."""
        group = repo.create_group('Test Group', sample_user.id)
        user = sample_users[0]
        repo.add_group_member(group.id, user, is_group_admin=False)

        # Toggle multiple times
        repo.set_group_member_admin(group.id, user.id, True)
        assert repo.is_user_group_admin(group.id, user.id) is True

        repo.set_group_member_admin(group.id, user.id, False)
        assert repo.is_user_group_admin(group.id, user.id) is False

        repo.set_group_member_admin(group.id, user.id, True)
        assert repo.is_user_group_admin(group.id, user.id) is True
