"""Integration tests for DatabaseUserRepository."""

import uuid

import bcrypt
import pytest

from app.core.models import group_membership
from app.repositories.database.user import DatabaseUserRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(db_session):
    """Create DatabaseUserRepository with the test session."""
    return DatabaseUserRepository(db_session)


class TestCreateUser:
    """Test create_user method."""

    def test_creates_user_successfully(self, repo):
        """Test creating a user with valid data."""
        user = repo.create_user(name='Alice', username='alice', password_hash='hash123')
        assert user is not None
        assert user.id is not None
        assert user.name == 'Alice'
        assert user.username == 'alice'
        assert user.password_hash == 'hash123'

    def test_created_user_has_defaults(self, repo):
        """Test that a new user gets default field values."""
        user = repo.create_user(name='Bob', username='bob', password_hash='hash')
        assert user.is_admin is False
        assert user.verified is False
        assert user.dark_mode is False
        assert user.preferred_language == 'en'

    def test_create_user_duplicate_username_raises(self, repo):
        """Test that creating a user with duplicate username raises."""
        repo.create_user(name='First', username='dupe', password_hash='hash1')
        with pytest.raises(Exception):
            repo.create_user(name='Second', username='dupe', password_hash='hash2')


class TestGetUserById:
    """Test get_user_by_id method."""

    def test_returns_user_when_exists(self, repo):
        """Test retrieving an existing user by ID."""
        created = repo.create_user(name='Alice', username='alice', password_hash='h')
        found = repo.get_user_by_id(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.username == 'alice'

    def test_returns_none_when_not_found(self, repo):
        """Test returns None for non-existent ID."""
        result = repo.get_user_by_id(uuid.uuid4())
        assert result is None


class TestGetUserByUsername:
    """Test get_user_by_username method."""

    def test_returns_user_when_exists(self, repo):
        """Test retrieving user by username."""
        repo.create_user(name='Alice', username='alice_find', password_hash='h')
        found = repo.get_user_by_username('alice_find')
        assert found is not None
        assert found.username == 'alice_find'

    def test_returns_none_when_not_found(self, repo):
        """Test returns None for non-existent username."""
        result = repo.get_user_by_username('nonexistent_user_xyz')
        assert result is None


class TestGetUserGroups:
    """Test get_user_groups method."""

    def test_returns_empty_list_for_no_groups(self, repo, create_user):
        """Test user with no groups returns empty list."""
        user = create_user(username='loner')
        groups = repo.get_user_groups(user)
        assert groups == []

    def test_returns_groups_user_belongs_to(self, repo, db_session, create_user, create_group):
        """Test returns all groups user is a member of."""
        from sqlalchemy import insert

        user = create_user(username='member')
        group1 = create_group(name='Group A', creator=user)
        group2 = create_group(name='Group B', creator=user)

        # Add user as member
        db_session.execute(
            insert(group_membership).values(
                group_id=group1.id, user_id=user.id, is_group_admin=False
            )
        )
        db_session.execute(
            insert(group_membership).values(
                group_id=group2.id, user_id=user.id, is_group_admin=False
            )
        )
        db_session.flush()

        groups = repo.get_user_groups(user)
        assert len(groups) == 2
        group_names = {g.name for g in groups}
        assert 'Group A' in group_names
        assert 'Group B' in group_names


class TestGetAllUsers:
    """Test get_all_users method."""

    def test_returns_all_users(self, repo):
        """Test returns all created users."""
        repo.create_user(name='U1', username='u1_all', password_hash='h')
        repo.create_user(name='U2', username='u2_all', password_hash='h')
        users = repo.get_all_users()
        usernames = {u.username for u in users}
        assert 'u1_all' in usernames
        assert 'u2_all' in usernames


class TestUpdateUser:
    """Test update_user method."""

    def test_update_name(self, repo):
        """Test updating user name."""
        user = repo.create_user(name='Old', username='upd1', password_hash='h')
        updated = repo.update_user(user.id, name='New')
        assert updated.name == 'New'

    def test_update_username(self, repo):
        """Test updating username."""
        user = repo.create_user(name='U', username='old_name', password_hash='h')
        updated = repo.update_user(user.id, username='new_name')
        assert updated.username == 'new_name'

    def test_update_password(self, repo):
        """Test updating password hash."""
        user = repo.create_user(name='U', username='upd_pw', password_hash='old')
        updated = repo.update_user(user.id, password_hash='new_hash')
        assert updated.password_hash == 'new_hash'

    def test_update_dark_mode(self, repo):
        """Test updating dark_mode preference."""
        user = repo.create_user(name='U', username='upd_dm', password_hash='h')
        updated = repo.update_user(user.id, dark_mode=True)
        assert updated.dark_mode is True

    def test_update_language(self, repo):
        """Test updating preferred language."""
        user = repo.create_user(name='U', username='upd_lang', password_hash='h')
        updated = repo.update_user(user.id, preferred_language='de')
        assert updated.preferred_language == 'de'

    def test_update_multiple_fields(self, repo):
        """Test updating multiple fields at once."""
        user = repo.create_user(name='U', username='upd_multi', password_hash='h')
        updated = repo.update_user(user.id, name='Updated', dark_mode=True)
        assert updated.name == 'Updated'
        assert updated.dark_mode is True

    def test_update_nonexistent_user_returns_none(self, repo):
        """Test updating a non-existent user returns None."""
        result = repo.update_user(uuid.uuid4(), name='X')
        assert result is None


class TestDeleteUser:
    """Test delete_user method."""

    def test_delete_existing_user(self, repo):
        """Test deleting an existing user."""
        user = repo.create_user(name='ToDelete', username='del1', password_hash='h')
        result = repo.delete_user(user.id)
        assert result is True
        assert repo.get_user_by_id(user.id) is None

    def test_delete_nonexistent_user_returns_false(self, repo):
        """Test deleting non-existent user returns False."""
        result = repo.delete_user(uuid.uuid4())
        assert result is False


class TestVerifyPassword:
    """Test verify_password method."""

    def test_correct_password(self, repo):
        """Test verifying correct password against hash."""
        password = 'mysecretpassword'
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        assert repo.verify_password(password, hashed) is True

    def test_wrong_password(self, repo):
        """Test verifying wrong password returns False."""
        password = 'correctpassword'
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        assert repo.verify_password('wrongpassword', hashed) is False

    def test_malformed_hash_returns_false(self, repo):
        """Test that a malformed hash returns False."""
        result = repo.verify_password('password', 'not_a_valid_hash')
        assert result is False


class TestGetUserStats:
    """Test get_user_stats method."""

    def test_stats_for_user_with_no_activity(self, repo, create_user):
        """Test stats for a user with no participations."""
        user = create_user(username='no_activity')
        stats = repo.get_user_stats(user.id)
        assert stats['runs_participated'] == 0
        assert stats['total_money_spent'] == 0.0
        assert stats['total_quantity_bought'] == 0.0
        assert stats['runs_helped'] == 0
        assert stats['runs_led'] == 0
        assert stats['groups_count'] == 0

    def test_stats_counts_participations(self, repo, create_user, create_run):
        """Test that runs_participated is counted correctly."""
        user = create_user(username='participant')
        run, _ = create_run(leader=user)
        stats = repo.get_user_stats(user.id)
        assert stats['runs_participated'] == 1
        assert stats['runs_led'] == 1

    def test_stats_counts_groups(self, repo, db_session, create_user, create_group):
        """Test that groups_count is counted correctly."""
        from sqlalchemy import insert

        user = create_user(username='group_member')
        group = create_group(name='Stats Group', creator=user)
        db_session.execute(
            insert(group_membership).values(group_id=group.id, user_id=user.id, is_group_admin=True)
        )
        db_session.flush()
        stats = repo.get_user_stats(user.id)
        assert stats['groups_count'] == 1
