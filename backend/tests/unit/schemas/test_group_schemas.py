"""Unit tests for group schemas."""

import pytest
from pydantic import ValidationError

from app.api.schemas.group_schemas import (
    CreateGroupRequest,
    CreateGroupResponse,
    GroupDetailResponse,
    GroupResponse,
    InviteTokenResponse,
    JoinGroupResponse,
    PreviewGroupResponse,
    RegenerateTokenResponse,
    RunResponse,
    RunSummary,
    ToggleJoiningResponse,
)


class TestCreateGroupRequest:
    """Tests for CreateGroupRequest schema."""

    def test_valid_group_creation(self):
        """Test creating valid group request."""
        data = {'name': 'Test Group'}
        schema = CreateGroupRequest(**data)
        assert schema.name == 'Test Group'

    def test_name_with_valid_special_characters(self):
        """Test group name with valid special characters."""
        data = {'name': "John's Group - Team & Friends"}
        schema = CreateGroupRequest(**data)
        assert schema.name == "John's Group - Team & Friends"

    def test_name_strip_whitespace(self):
        """Test group name strips leading/trailing whitespace."""
        data = {'name': '  Test Group  '}
        schema = CreateGroupRequest(**data)
        assert schema.name == 'Test Group'

    def test_name_too_short(self):
        """Test name shorter than 2 characters raises ValidationError."""
        data = {'name': 'A'}
        with pytest.raises(ValidationError) as exc_info:
            CreateGroupRequest(**data)
        assert 'name' in str(exc_info.value)

    def test_name_too_long(self):
        """Test name exceeding 100 characters raises ValidationError."""
        data = {'name': 'a' * 101}
        with pytest.raises(ValidationError) as exc_info:
            CreateGroupRequest(**data)
        assert 'name' in str(exc_info.value)

    def test_name_invalid_characters(self):
        """Test name with invalid characters raises ValidationError."""
        data = {'name': 'Test@Group#123'}
        with pytest.raises(ValidationError) as exc_info:
            CreateGroupRequest(**data)
        assert 'name' in str(exc_info.value)

    def test_missing_name(self):
        """Test missing name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CreateGroupRequest()
        assert 'name' in str(exc_info.value)


class TestRunSummary:
    """Tests for RunSummary schema."""

    def test_valid_run_summary(self):
        """Test creating valid run summary."""
        data = {'id': 'run123', 'store_name': 'Costco', 'state': 'active'}
        schema = RunSummary(**data)
        assert schema.id == 'run123'
        assert schema.store_name == 'Costco'
        assert schema.state == 'active'

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {'id': 'run123', 'store_name': 'Costco'}
        with pytest.raises(ValidationError) as exc_info:
            RunSummary(**data)
        assert 'state' in str(exc_info.value)


class TestGroupResponse:
    """Tests for GroupResponse schema."""

    def test_valid_group_response(self):
        """Test creating valid group response."""
        data = {
            'id': 'group123',
            'name': 'Test Group',
            'description': 'A test group',
            'member_count': 5,
            'active_runs_count': 2,
            'completed_runs_count': 10,
            'active_runs': [{'id': 'run1', 'store_name': 'Costco', 'state': 'active'}],
            'created_at': '2024-01-01T00:00:00Z',
        }
        schema = GroupResponse(**data)
        assert schema.id == 'group123'
        assert schema.name == 'Test Group'
        assert schema.member_count == 5
        assert len(schema.active_runs) == 1

    def test_empty_active_runs(self):
        """Test group response with empty active runs list."""
        data = {
            'id': 'group123',
            'name': 'Test Group',
            'description': 'A test group',
            'member_count': 5,
            'active_runs_count': 0,
            'completed_runs_count': 10,
            'active_runs': [],
            'created_at': '2024-01-01T00:00:00Z',
        }
        schema = GroupResponse(**data)
        assert schema.active_runs == []


class TestCreateGroupResponse:
    """Tests for CreateGroupResponse schema."""

    def test_valid_create_group_response(self):
        """Test creating valid create group response."""
        data = {
            'id': 'group123',
            'name': 'Test Group',
            'member_count': 1,
            'active_runs_count': 0,
            'completed_runs_count': 0,
            'active_runs': [],
        }
        schema = CreateGroupResponse(**data)
        assert schema.id == 'group123'
        assert schema.name == 'Test Group'
        assert schema.member_count == 1


class TestRunResponse:
    """Tests for RunResponse schema."""

    def test_valid_run_response(self):
        """Test creating valid run response."""
        data = {
            'id': 'run123',
            'group_id': 'group123',
            'store_id': 'store123',
            'store_name': 'Costco',
            'state': 'active',
            'leader_name': 'John Doe',
            'leader_is_removed': False,
            'planned_on': '2024-01-01T00:00:00Z',
            'planning_at': None,
            'active_at': '2024-01-01T00:00:00Z',
            'confirmed_at': None,
            'shopping_at': None,
            'adjusting_at': None,
            'distributing_at': None,
            'completed_at': None,
            'cancelled_at': None,
        }
        schema = RunResponse(**data)
        assert schema.id == 'run123'
        assert schema.state == 'active'
        assert schema.leader_is_removed is False

    def test_default_leader_is_removed(self):
        """Test default value for leader_is_removed."""
        data = {
            'id': 'run123',
            'group_id': 'group123',
            'store_id': 'store123',
            'store_name': 'Costco',
            'state': 'active',
            'leader_name': 'John Doe',
            'planned_on': None,
            'planning_at': None,
            'active_at': None,
            'confirmed_at': None,
            'shopping_at': None,
            'adjusting_at': None,
            'distributing_at': None,
            'completed_at': None,
            'cancelled_at': None,
        }
        schema = RunResponse(**data)
        assert schema.leader_is_removed is False


class TestGroupDetailResponse:
    """Tests for GroupDetailResponse schema."""

    def test_valid_group_detail_response(self):
        """Test creating valid group detail response."""
        data = {
            'id': 'group123',
            'name': 'Test Group',
            'invite_token': 'abc123',
            'is_joining_allowed': True,
            'members': [{'id': 'user1', 'name': 'John'}],
            'is_current_user_admin': True,
        }
        schema = GroupDetailResponse(**data)
        assert schema.id == 'group123'
        assert schema.invite_token == 'abc123'
        assert schema.is_joining_allowed is True
        assert len(schema.members) == 1


class TestInviteTokenResponse:
    """Tests for InviteTokenResponse schema."""

    def test_valid_invite_token_response(self):
        """Test creating valid invite token response."""
        data = {'invite_token': 'abc123def456'}
        schema = InviteTokenResponse(**data)
        assert schema.invite_token == 'abc123def456'


class TestRegenerateTokenResponse:
    """Tests for RegenerateTokenResponse schema."""

    def test_valid_regenerate_token_response(self):
        """Test creating valid regenerate token response."""
        data = {'invite_token': 'new_token_xyz'}
        schema = RegenerateTokenResponse(**data)
        assert schema.invite_token == 'new_token_xyz'


class TestPreviewGroupResponse:
    """Tests for PreviewGroupResponse schema."""

    def test_valid_preview_group_response(self):
        """Test creating valid preview group response."""
        data = {
            'id': 'group123',
            'name': 'Test Group',
            'member_count': 5,
            'creator_name': 'John Doe',
        }
        schema = PreviewGroupResponse(**data)
        assert schema.id == 'group123'
        assert schema.name == 'Test Group'
        assert schema.member_count == 5
        assert schema.creator_name == 'John Doe'


class TestJoinGroupResponse:
    """Tests for JoinGroupResponse schema."""

    def test_valid_join_group_response(self):
        """Test creating valid join group response."""
        data = {
            'success': True,
            'code': 'JOINED_GROUP',
            'group_id': 'group123',
            'group_name': 'Test Group',
        }
        schema = JoinGroupResponse(**data)
        assert schema.success is True
        assert schema.code == 'JOINED_GROUP'
        assert schema.group_id == 'group123'
        assert schema.group_name == 'Test Group'

    def test_default_success_value(self):
        """Test default value for success field."""
        data = {
            'code': 'JOINED_GROUP',
            'group_id': 'group123',
            'group_name': 'Test Group',
        }
        schema = JoinGroupResponse(**data)
        assert schema.success is True


class TestToggleJoiningResponse:
    """Tests for ToggleJoiningResponse schema."""

    def test_valid_toggle_joining_response_true(self):
        """Test creating valid toggle joining response with True."""
        data = {'is_joining_allowed': True}
        schema = ToggleJoiningResponse(**data)
        assert schema.is_joining_allowed is True

    def test_valid_toggle_joining_response_false(self):
        """Test creating valid toggle joining response with False."""
        data = {'is_joining_allowed': False}
        schema = ToggleJoiningResponse(**data)
        assert schema.is_joining_allowed is False
