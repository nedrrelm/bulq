"""Unit tests for notification data schemas."""

import pytest
from pydantic import ValidationError

from app.api.schemas.notification_data import (
    BidRetractedData,
    BidUpdatedData,
    LeaderReassignmentAcceptedData,
    LeaderReassignmentDeclinedData,
    LeaderReassignmentRequestData,
    ReadyToggledData,
    RunCreatedData,
    RunStateChangedData,
    StateChangedData,
)


class TestRunStateChangedData:
    """Tests for RunStateChangedData schema."""

    def test_valid_run_state_changed_data(self):
        """Test creating valid run state changed data."""
        data = {
            'run_id': 'run123',
            'store_name': 'Costco',
            'old_state': 'planning',
            'new_state': 'active',
            'group_id': 'group123',
        }
        schema = RunStateChangedData(**data)
        assert schema.run_id == 'run123'
        assert schema.store_name == 'Costco'
        assert schema.old_state == 'planning'
        assert schema.new_state == 'active'
        assert schema.group_id == 'group123'

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'run_id': 'run123',
            'store_name': 'Costco',
        }
        with pytest.raises(ValidationError) as exc_info:
            RunStateChangedData(**data)
        errors = str(exc_info.value)
        assert 'old_state' in errors or 'new_state' in errors

    def test_serialization(self):
        """Test schema serialization."""
        schema = RunStateChangedData(
            run_id='run123',
            store_name='Costco',
            old_state='planning',
            new_state='active',
            group_id='group123',
        )
        data = schema.model_dump()
        assert data['run_id'] == 'run123'
        assert data['old_state'] == 'planning'
        assert data['new_state'] == 'active'


class TestLeaderReassignmentRequestData:
    """Tests for LeaderReassignmentRequestData schema."""

    def test_valid_leader_reassignment_request_data(self):
        """Test creating valid leader reassignment request data."""
        data = {
            'run_id': 'run123',
            'from_user_id': 'user123',
            'from_user_name': 'John Doe',
            'request_id': 'req123',
            'store_name': 'Costco',
        }
        schema = LeaderReassignmentRequestData(**data)
        assert schema.run_id == 'run123'
        assert schema.from_user_id == 'user123'
        assert schema.from_user_name == 'John Doe'
        assert schema.request_id == 'req123'
        assert schema.store_name == 'Costco'

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'run_id': 'run123',
            'from_user_id': 'user123',
        }
        with pytest.raises(ValidationError) as exc_info:
            LeaderReassignmentRequestData(**data)
        errors = str(exc_info.value)
        assert 'from_user_name' in errors or 'request_id' in errors


class TestLeaderReassignmentAcceptedData:
    """Tests for LeaderReassignmentAcceptedData schema."""

    def test_valid_leader_reassignment_accepted_data(self):
        """Test creating valid leader reassignment accepted data."""
        data = {
            'run_id': 'run123',
            'new_leader_id': 'user456',
            'new_leader_name': 'Jane Smith',
            'store_name': 'Costco',
        }
        schema = LeaderReassignmentAcceptedData(**data)
        assert schema.run_id == 'run123'
        assert schema.new_leader_id == 'user456'
        assert schema.new_leader_name == 'Jane Smith'
        assert schema.store_name == 'Costco'

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'run_id': 'run123',
            'new_leader_id': 'user456',
        }
        with pytest.raises(ValidationError) as exc_info:
            LeaderReassignmentAcceptedData(**data)
        errors = str(exc_info.value)
        assert 'new_leader_name' in errors or 'store_name' in errors


class TestLeaderReassignmentDeclinedData:
    """Tests for LeaderReassignmentDeclinedData schema."""

    def test_valid_leader_reassignment_declined_data(self):
        """Test creating valid leader reassignment declined data."""
        data = {
            'run_id': 'run123',
            'declined_by_id': 'user456',
            'declined_by_name': 'Jane Smith',
            'store_name': 'Costco',
        }
        schema = LeaderReassignmentDeclinedData(**data)
        assert schema.run_id == 'run123'
        assert schema.declined_by_id == 'user456'
        assert schema.declined_by_name == 'Jane Smith'
        assert schema.store_name == 'Costco'

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'run_id': 'run123',
            'declined_by_id': 'user456',
        }
        with pytest.raises(ValidationError) as exc_info:
            LeaderReassignmentDeclinedData(**data)
        errors = str(exc_info.value)
        assert 'declined_by_name' in errors or 'store_name' in errors


class TestBidUpdatedData:
    """Tests for BidUpdatedData schema."""

    def test_valid_bid_updated_data(self):
        """Test creating valid bid updated data."""
        data = {
            'product_id': 'prod123',
            'user_id': 'user123',
            'user_name': 'John Doe',
            'quantity': 5.0,
            'interested_only': False,
            'new_total': 15.0,
        }
        schema = BidUpdatedData(**data)
        assert schema.product_id == 'prod123'
        assert schema.user_id == 'user123'
        assert schema.user_name == 'John Doe'
        assert schema.quantity == 5.0
        assert schema.interested_only is False
        assert schema.new_total == 15.0

    def test_bid_updated_interested_only(self):
        """Test bid updated data with interested_only=True."""
        data = {
            'product_id': 'prod123',
            'user_id': 'user123',
            'user_name': 'John Doe',
            'quantity': 0.0,
            'interested_only': True,
            'new_total': 10.0,
        }
        schema = BidUpdatedData(**data)
        assert schema.interested_only is True
        assert schema.quantity == 0.0

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'product_id': 'prod123',
            'user_id': 'user123',
        }
        with pytest.raises(ValidationError) as exc_info:
            BidUpdatedData(**data)
        errors = str(exc_info.value)
        assert 'user_name' in errors or 'quantity' in errors


class TestBidRetractedData:
    """Tests for BidRetractedData schema."""

    def test_valid_bid_retracted_data(self):
        """Test creating valid bid retracted data."""
        data = {
            'product_id': 'prod123',
            'user_id': 'user123',
            'new_total': 10.0,
        }
        schema = BidRetractedData(**data)
        assert schema.product_id == 'prod123'
        assert schema.user_id == 'user123'
        assert schema.new_total == 10.0

    def test_bid_retracted_zero_total(self):
        """Test bid retracted with zero new total."""
        data = {
            'product_id': 'prod123',
            'user_id': 'user123',
            'new_total': 0.0,
        }
        schema = BidRetractedData(**data)
        assert schema.new_total == 0.0

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'product_id': 'prod123',
        }
        with pytest.raises(ValidationError) as exc_info:
            BidRetractedData(**data)
        errors = str(exc_info.value)
        assert 'user_id' in errors or 'new_total' in errors

    def test_serialization(self):
        """Test schema serialization."""
        schema = BidRetractedData(product_id='prod123', user_id='user123', new_total=10.0)
        data = schema.model_dump()
        assert data == {
            'product_id': 'prod123',
            'user_id': 'user123',
            'new_total': 10.0,
        }


class TestReadyToggledData:
    """Tests for ReadyToggledData schema."""

    def test_valid_ready_toggled_data_true(self):
        """Test creating valid ready toggled data with is_ready=True."""
        data = {
            'user_id': 'user123',
            'is_ready': True,
        }
        schema = ReadyToggledData(**data)
        assert schema.user_id == 'user123'
        assert schema.is_ready is True

    def test_valid_ready_toggled_data_false(self):
        """Test creating valid ready toggled data with is_ready=False."""
        data = {
            'user_id': 'user123',
            'is_ready': False,
        }
        schema = ReadyToggledData(**data)
        assert schema.user_id == 'user123'
        assert schema.is_ready is False

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'user_id': 'user123',
        }
        with pytest.raises(ValidationError) as exc_info:
            ReadyToggledData(**data)
        assert 'is_ready' in str(exc_info.value)


class TestStateChangedData:
    """Tests for StateChangedData schema."""

    def test_valid_state_changed_data(self):
        """Test creating valid state changed data."""
        data = {
            'run_id': 'run123',
            'new_state': 'active',
        }
        schema = StateChangedData(**data)
        assert schema.run_id == 'run123'
        assert schema.new_state == 'active'

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'run_id': 'run123',
        }
        with pytest.raises(ValidationError) as exc_info:
            StateChangedData(**data)
        assert 'new_state' in str(exc_info.value)

    def test_serialization(self):
        """Test schema serialization."""
        schema = StateChangedData(run_id='run123', new_state='confirmed')
        data = schema.model_dump()
        assert data == {'run_id': 'run123', 'new_state': 'confirmed'}


class TestRunCreatedData:
    """Tests for RunCreatedData schema."""

    def test_valid_run_created_data(self):
        """Test creating valid run created data."""
        data = {
            'run_id': 'run123',
            'store_id': 'store123',
            'store_name': 'Costco',
            'state': 'planning',
            'leader_name': 'John Doe',
        }
        schema = RunCreatedData(**data)
        assert schema.run_id == 'run123'
        assert schema.store_id == 'store123'
        assert schema.store_name == 'Costco'
        assert schema.state == 'planning'
        assert schema.leader_name == 'John Doe'

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'run_id': 'run123',
            'store_id': 'store123',
        }
        with pytest.raises(ValidationError) as exc_info:
            RunCreatedData(**data)
        errors = str(exc_info.value)
        assert 'store_name' in errors or 'state' in errors or 'leader_name' in errors

    def test_serialization(self):
        """Test schema serialization."""
        schema = RunCreatedData(
            run_id='run123',
            store_id='store123',
            store_name='Costco',
            state='planning',
            leader_name='John Doe',
        )
        data = schema.model_dump()
        assert data['run_id'] == 'run123'
        assert data['store_name'] == 'Costco'
        assert data['leader_name'] == 'John Doe'

    def test_deserialization(self):
        """Test schema deserialization from dict."""
        data = {
            'run_id': 'run123',
            'store_id': 'store123',
            'store_name': 'Costco',
            'state': 'planning',
            'leader_name': 'John Doe',
        }
        schema = RunCreatedData.model_validate(data)
        assert schema.run_id == 'run123'
        assert schema.store_id == 'store123'
        assert schema.state == 'planning'
