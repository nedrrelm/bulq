"""Integration tests for DatabaseGroupRepository."""

import uuid

import pytest

from app.repositories.database.group import DatabaseGroupRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(db_session):
    """Create DatabaseGroupRepository with the test session."""
    return DatabaseGroupRepository(db_session)


class TestCreateGroup:
    """Test create_group method."""

    def test_creates_group_successfully(self, repo, create_user):
        """Test creating a group with valid data."""
        user = create_user(username='creator')
        group = repo.create_group(name='My Group', created_by=user.id)
        assert group is not None
        assert group.id is not None
        assert group.name == 'My Group'
        assert group.created_by == user.id
        assert group.invite_token is not None
        assert group.is_joining_allowed is True

    def test_creates_group_with_unique_invite_token(self, repo, create_user):
        """Test that each group gets a unique invite token."""
        user = create_user(username='creator2')
        g1 = repo.create_group(name='G1', created_by=user.id)
        g2 = repo.create_group(name='G2', created_by=user.id)
        assert g1.invite_token != g2.invite_token


class TestGetGroupById:
    """Test get_group_by_id method."""

    def test_returns_group_when_exists(self, repo, create_user):
        """Test retrieving an existing group."""
        user = create_user(username='get_grp')
        group = repo.create_group(name='Found', created_by=user.id)
        found = repo.get_group_by_id(group.id)
        assert found is not None
        assert found.name == 'Found'

    def test_returns_none_when_not_found(self, repo):
        """Test returns None for non-existent group."""
        result = repo.get_group_by_id(uuid.uuid4())
        assert result is None


class TestGetGroupByInviteToken:
    """Test get_group_by_invite_token method."""

    def test_returns_group_when_token_exists(self, repo, create_user):
        """Test finding group by valid invite token."""
        user = create_user(username='token_u')
        group = repo.create_group(name='Token Group', created_by=user.id)
        found = repo.get_group_by_invite_token(group.invite_token)
        assert found is not None
        assert found.id == group.id

    def test_returns_none_for_invalid_token(self, repo):
        """Test returns None for non-existent token."""
        result = repo.get_group_by_invite_token('nonexistent-token-xyz')
        assert result is None


class TestAddGroupMember:
    """Test add_group_member method."""

    def test_adds_member_successfully(self, repo, create_user):
        """Test adding a user to a group."""
        creator = create_user(username='grp_creator')
        member = create_user(username='new_member')
        group = repo.create_group(name='Grp', created_by=creator.id)
        result = repo.add_group_member(group.id, member, is_group_admin=False)
        assert result is True

    def test_add_member_as_admin(self, repo, create_user):
        """Test adding a member with admin privileges."""
        creator = create_user(username='adm_creator')
        member = create_user(username='admin_member')
        group = repo.create_group(name='Admin Grp', created_by=creator.id)
        result = repo.add_group_member(group.id, member, is_group_admin=True)
        assert result is True
        assert repo.is_user_group_admin(group.id, member.id) is True

    def test_adding_existing_member_returns_false(self, repo, create_user):
        """Test that adding an already existing member returns False."""
        creator = create_user(username='dup_creator')
        member = create_user(username='dup_member')
        group = repo.create_group(name='Dup Grp', created_by=creator.id)
        repo.add_group_member(group.id, member)
        result = repo.add_group_member(group.id, member)
        assert result is False


class TestRemoveGroupMember:
    """Test remove_group_member method."""

    def test_removes_member_successfully(self, repo, create_user):
        """Test removing an existing member."""
        creator = create_user(username='rm_creator')
        member = create_user(username='rm_member')
        group = repo.create_group(name='Rm Grp', created_by=creator.id)
        repo.add_group_member(group.id, member)
        result = repo.remove_group_member(group.id, member.id)
        assert result is True

    def test_remove_non_member_returns_false(self, repo, create_user):
        """Test removing a user who is not a member returns False."""
        creator = create_user(username='rm_creator2')
        non_member = create_user(username='rm_non_member')
        group = repo.create_group(name='Rm Grp2', created_by=creator.id)
        result = repo.remove_group_member(group.id, non_member.id)
        assert result is False


class TestIsUserGroupAdmin:
    """Test is_user_group_admin method."""

    def test_returns_true_for_admin(self, repo, create_user):
        """Test returns True for group admin."""
        creator = create_user(username='adm_check')
        group = repo.create_group(name='Adm Check', created_by=creator.id)
        repo.add_group_member(group.id, creator, is_group_admin=True)
        assert repo.is_user_group_admin(group.id, creator.id) is True

    def test_returns_false_for_regular_member(self, repo, create_user):
        """Test returns False for non-admin member."""
        creator = create_user(username='reg_adm')
        member = create_user(username='reg_member')
        group = repo.create_group(name='Reg Grp', created_by=creator.id)
        repo.add_group_member(group.id, member, is_group_admin=False)
        assert repo.is_user_group_admin(group.id, member.id) is False

    def test_returns_false_for_non_member(self, repo, create_user):
        """Test returns False for user not in the group."""
        creator = create_user(username='non_m')
        non_member = create_user(username='outsider')
        group = repo.create_group(name='NM Grp', created_by=creator.id)
        assert repo.is_user_group_admin(group.id, non_member.id) is False


class TestSetGroupMemberAdmin:
    """Test set_group_member_admin method."""

    def test_promote_to_admin(self, repo, create_user):
        """Test promoting a member to admin."""
        creator = create_user(username='promo_creator')
        member = create_user(username='promo_member')
        group = repo.create_group(name='Promo', created_by=creator.id)
        repo.add_group_member(group.id, member, is_group_admin=False)
        result = repo.set_group_member_admin(group.id, member.id, is_admin=True)
        assert result is True
        assert repo.is_user_group_admin(group.id, member.id) is True

    def test_demote_from_admin(self, repo, create_user):
        """Test demoting an admin to regular member."""
        creator = create_user(username='demo_creator')
        member = create_user(username='demo_member')
        group = repo.create_group(name='Demo', created_by=creator.id)
        repo.add_group_member(group.id, member, is_group_admin=True)
        result = repo.set_group_member_admin(group.id, member.id, is_admin=False)
        assert result is True
        assert repo.is_user_group_admin(group.id, member.id) is False

    def test_set_admin_for_non_member_returns_false(self, repo, create_user):
        """Test setting admin for non-member returns False."""
        creator = create_user(username='nm_admin')
        non_member = create_user(username='nm_outsider')
        group = repo.create_group(name='NM Admin', created_by=creator.id)
        result = repo.set_group_member_admin(group.id, non_member.id, is_admin=True)
        assert result is False


class TestGetGroupMembersWithAdminStatus:
    """Test get_group_members_with_admin_status method."""

    def test_returns_members_with_status(self, repo, create_user):
        """Test returns list of members with admin status."""
        creator = create_user(username='members_creator')
        member1 = create_user(username='mem1')
        member2 = create_user(username='mem2')
        group = repo.create_group(name='Members Grp', created_by=creator.id)
        repo.add_group_member(group.id, member1, is_group_admin=True)
        repo.add_group_member(group.id, member2, is_group_admin=False)

        members = repo.get_group_members_with_admin_status(group.id)
        assert len(members) == 2
        usernames = {m['username'] for m in members}
        assert 'mem1' in usernames
        assert 'mem2' in usernames

        admin_member = next(m for m in members if m['username'] == 'mem1')
        assert admin_member['is_group_admin'] is True

    def test_returns_empty_for_group_with_no_members(self, repo, create_user):
        """Test returns empty list for group with no members."""
        creator = create_user(username='empty_grp')
        group = repo.create_group(name='Empty', created_by=creator.id)
        members = repo.get_group_members_with_admin_status(group.id)
        assert members == []


class TestRegenerateGroupInviteToken:
    """Test regenerate_group_invite_token method."""

    def test_regenerates_token(self, repo, create_user):
        """Test that the invite token changes."""
        creator = create_user(username='regen_creator')
        group = repo.create_group(name='Regen', created_by=creator.id)
        old_token = group.invite_token
        new_token = repo.regenerate_group_invite_token(group.id)
        assert new_token is not None
        assert new_token != old_token

    def test_returns_none_for_nonexistent_group(self, repo):
        """Test returns None for non-existent group."""
        result = repo.regenerate_group_invite_token(uuid.uuid4())
        assert result is None


class TestUpdateGroupJoiningAllowed:
    """Test update_group_joining_allowed method."""

    def test_disable_joining(self, repo, create_user):
        """Test disabling joining for a group."""
        creator = create_user(username='join_creator')
        group = repo.create_group(name='Join Grp', created_by=creator.id)
        updated = repo.update_group_joining_allowed(group.id, False)
        assert updated is not None
        assert updated.is_joining_allowed is False

    def test_enable_joining(self, repo, create_user):
        """Test enabling joining for a group."""
        creator = create_user(username='join_creator2')
        group = repo.create_group(name='Join Grp2', created_by=creator.id)
        repo.update_group_joining_allowed(group.id, False)
        updated = repo.update_group_joining_allowed(group.id, True)
        assert updated.is_joining_allowed is True

    def test_returns_none_for_nonexistent_group(self, repo):
        """Test returns None for non-existent group."""
        result = repo.update_group_joining_allowed(uuid.uuid4(), True)
        assert result is None


class TestGetAllGroups:
    """Test get_all_groups method."""

    def test_returns_all_groups(self, repo, create_user):
        """Test returns all created groups."""
        creator = create_user(username='all_grp')
        repo.create_group(name='All1', created_by=creator.id)
        repo.create_group(name='All2', created_by=creator.id)
        groups = repo.get_all_groups()
        names = {g.name for g in groups}
        assert 'All1' in names
        assert 'All2' in names
