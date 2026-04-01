"""Unit tests for run schemas."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.api.schemas.run_schemas import (
    AvailableProductResponse,
    CancelRunResponse,
    CreateRunRequest,
    CreateRunResponse,
    ParticipantResponse,
    PlaceBidRequest,
    PlaceBidResponse,
    ProductResponse,
    ReadyToggleResponse,
    RetractBidResponse,
    RunDetailResponse,
    StateChangeResponse,
    UpdateRunCommentRequest,
    UserBidResponse,
)


class TestCreateRunRequest:
    """Tests for CreateRunRequest schema."""

    def test_valid_create_run_request(self):
        """Test creating valid run request."""
        data = {
            'group_id': 'group123',
            'store_id': 'store123',
            'comment': 'Test comment',
        }
        schema = CreateRunRequest(**data)
        assert schema.group_id == 'group123'
        assert schema.store_id == 'store123'
        assert schema.comment == 'Test comment'

    def test_create_run_without_comment(self):
        """Test creating run without comment."""
        data = {'group_id': 'group123', 'store_id': 'store123'}
        schema = CreateRunRequest(**data)
        assert schema.comment is None

    def test_comment_too_long(self):
        """Test comment exceeding 500 characters raises ValidationError."""
        data = {
            'group_id': 'group123',
            'store_id': 'store123',
            'comment': 'a' * 501,
        }
        with pytest.raises(ValidationError) as exc_info:
            CreateRunRequest(**data)
        assert 'comment' in str(exc_info.value)

    def test_missing_group_id(self):
        """Test missing group_id raises ValidationError."""
        data = {'store_id': 'store123'}
        with pytest.raises(ValidationError) as exc_info:
            CreateRunRequest(**data)
        assert 'group_id' in str(exc_info.value)


class TestCreateRunResponse:
    """Tests for CreateRunResponse schema."""

    def test_valid_create_run_response(self):
        """Test creating valid create run response."""
        data = {
            'id': 'run123',
            'group_id': 'group123',
            'store_id': 'store123',
            'state': 'planning',
            'store_name': 'Costco',
            'leader_name': 'John Doe',
        }
        schema = CreateRunResponse(**data)
        assert schema.id == 'run123'
        assert schema.state == 'planning'
        assert schema.store_name == 'Costco'


class TestPlaceBidRequest:
    """Tests for PlaceBidRequest schema."""

    def test_valid_place_bid_request(self):
        """Test creating valid place bid request."""
        data = {
            'product_id': 'prod123',
            'quantity': Decimal('5.50'),
            'interested_only': False,
            'comment': 'Need this',
        }
        schema = PlaceBidRequest(**data)
        assert schema.product_id == 'prod123'
        assert schema.quantity == Decimal('5.50')
        assert schema.interested_only is False
        assert schema.comment == 'Need this'

    def test_place_bid_without_comment(self):
        """Test creating bid without comment."""
        data = {
            'product_id': 'prod123',
            'quantity': Decimal('5.50'),
        }
        schema = PlaceBidRequest(**data)
        assert schema.comment is None
        assert schema.interested_only is False

    def test_quantity_zero_or_negative(self):
        """Test quantity <= 0 raises ValidationError."""
        data = {
            'product_id': 'prod123',
            'quantity': Decimal('0'),
        }
        with pytest.raises(ValidationError) as exc_info:
            PlaceBidRequest(**data)
        assert 'quantity' in str(exc_info.value)

    def test_quantity_too_large(self):
        """Test quantity exceeding 9999 raises ValidationError."""
        data = {
            'product_id': 'prod123',
            'quantity': Decimal('10000'),
        }
        with pytest.raises(ValidationError) as exc_info:
            PlaceBidRequest(**data)
        assert 'quantity' in str(exc_info.value)

    def test_quantity_too_many_decimal_places(self):
        """Test quantity with more than 2 decimal places raises ValidationError."""
        data = {
            'product_id': 'prod123',
            'quantity': Decimal('5.555'),
        }
        with pytest.raises(ValidationError) as exc_info:
            PlaceBidRequest(**data)
        assert 'quantity' in str(exc_info.value)


class TestUserBidResponse:
    """Tests for UserBidResponse schema."""

    def test_valid_user_bid_response(self):
        """Test creating valid user bid response."""
        data = {
            'user_id': 'user123',
            'user_name': 'John Doe',
            'quantity': 5.5,
            'interested_only': False,
            'comment': 'Need this',
        }
        schema = UserBidResponse(**data)
        assert schema.user_id == 'user123'
        assert schema.user_name == 'John Doe'
        assert schema.quantity == 5.5

    def test_default_comment_none(self):
        """Test default comment value is None."""
        data = {
            'user_id': 'user123',
            'user_name': 'John Doe',
            'quantity': 5.5,
            'interested_only': False,
        }
        schema = UserBidResponse(**data)
        assert schema.comment is None


class TestProductResponse:
    """Tests for ProductResponse schema."""

    def test_valid_product_response(self):
        """Test creating valid product response."""
        data = {
            'id': 'prod123',
            'name': 'Milk',
            'brand': 'Organic',
            'unit': 'L',
            'current_price': '3.99',
            'total_quantity': 10.0,
            'interested_count': 2,
            'user_bids': [],
            'current_user_bid': None,
            'purchased_quantity': None,
        }
        schema = ProductResponse(**data)
        assert schema.id == 'prod123'
        assert schema.name == 'Milk'
        assert schema.total_quantity == 10.0

    def test_product_with_optional_fields_none(self):
        """Test product response with optional fields as None."""
        data = {
            'id': 'prod123',
            'name': 'Milk',
            'brand': None,
            'unit': None,
            'current_price': None,
            'total_quantity': 10.0,
            'interested_count': 2,
            'user_bids': [],
            'current_user_bid': None,
        }
        schema = ProductResponse(**data)
        assert schema.brand is None
        assert schema.unit is None


class TestParticipantResponse:
    """Tests for ParticipantResponse schema."""

    def test_valid_participant_response(self):
        """Test creating valid participant response."""
        data = {
            'user_id': 'user123',
            'user_name': 'John Doe',
            'is_leader': True,
            'is_helper': False,
            'is_ready': True,
            'is_removed': False,
        }
        schema = ParticipantResponse(**data)
        assert schema.user_id == 'user123'
        assert schema.is_leader is True
        assert schema.is_ready is True

    def test_default_values(self):
        """Test default values for optional fields."""
        data = {
            'user_id': 'user123',
            'user_name': 'John Doe',
        }
        schema = ParticipantResponse(**data)
        assert schema.is_leader is False
        assert schema.is_helper is False
        assert schema.is_ready is False
        assert schema.is_removed is False


class TestRunDetailResponse:
    """Tests for RunDetailResponse schema."""

    def test_valid_run_detail_response(self):
        """Test creating valid run detail response."""
        data = {
            'id': 'run123',
            'group_id': 'group123',
            'group_name': 'Test Group',
            'store_id': 'store123',
            'store_name': 'Costco',
            'state': 'active',
            'comment': None,
            'products': [],
            'participants': [],
            'current_user_is_ready': False,
            'current_user_is_leader': True,
            'current_user_is_helper': False,
            'leader_name': 'John Doe',
            'helpers': [],
        }
        schema = RunDetailResponse(**data)
        assert schema.id == 'run123'
        assert schema.state == 'active'
        assert schema.current_user_is_leader is True


class TestStateChangeResponse:
    """Tests for StateChangeResponse schema."""

    def test_valid_state_change_response(self):
        """Test creating valid state change response."""
        data = {
            'success': True,
            'code': 'STATE_CHANGED',
            'state': 'confirmed',
            'run_id': 'run123',
            'group_id': 'group123',
        }
        schema = StateChangeResponse(**data)
        assert schema.success is True
        assert schema.code == 'STATE_CHANGED'
        assert schema.state == 'confirmed'

    def test_default_success_value(self):
        """Test default success value."""
        data = {
            'code': 'STATE_CHANGED',
            'state': 'confirmed',
            'run_id': 'run123',
            'group_id': 'group123',
        }
        schema = StateChangeResponse(**data)
        assert schema.success is True


class TestReadyToggleResponse:
    """Tests for ReadyToggleResponse schema."""

    def test_valid_ready_toggle_response(self):
        """Test creating valid ready toggle response."""
        data = {
            'success': True,
            'code': 'READY_TOGGLED',
            'is_ready': True,
            'state_changed': True,
            'new_state': 'active',
            'run_id': 'run123',
            'user_id': 'user123',
            'group_id': 'group123',
        }
        schema = ReadyToggleResponse(**data)
        assert schema.is_ready is True
        assert schema.state_changed is True
        assert schema.new_state == 'active'

    def test_default_values(self):
        """Test default values for optional fields."""
        data = {
            'code': 'READY_TOGGLED',
            'is_ready': True,
            'run_id': 'run123',
            'user_id': 'user123',
        }
        schema = ReadyToggleResponse(**data)
        assert schema.success is True
        assert schema.state_changed is False
        assert schema.new_state is None
        assert schema.group_id is None


class TestCancelRunResponse:
    """Tests for CancelRunResponse schema."""

    def test_valid_cancel_run_response(self):
        """Test creating valid cancel run response."""
        data = {
            'success': True,
            'code': 'RUN_CANCELLED',
            'run_id': 'run123',
            'group_id': 'group123',
            'state': 'cancelled',
        }
        schema = CancelRunResponse(**data)
        assert schema.success is True
        assert schema.code == 'RUN_CANCELLED'
        assert schema.state == 'cancelled'


class TestAvailableProductResponse:
    """Tests for AvailableProductResponse schema."""

    def test_valid_available_product_response(self):
        """Test creating valid available product response."""
        data = {
            'id': 'prod123',
            'name': 'Milk',
            'brand': 'Organic',
            'current_price': '3.99',
            'has_store_availability': True,
        }
        schema = AvailableProductResponse(**data)
        assert schema.id == 'prod123'
        assert schema.has_store_availability is True

    def test_default_has_store_availability(self):
        """Test default value for has_store_availability."""
        data = {
            'id': 'prod123',
            'name': 'Milk',
            'brand': 'Organic',
            'current_price': '3.99',
        }
        schema = AvailableProductResponse(**data)
        assert schema.has_store_availability is False


class TestPlaceBidResponse:
    """Tests for PlaceBidResponse schema."""

    def test_valid_place_bid_response(self):
        """Test creating valid place bid response."""
        data = {
            'success': True,
            'code': 'BID_PLACED',
            'product_id': 'prod123',
            'user_id': 'user123',
            'user_name': 'John Doe',
            'quantity': 5.0,
            'interested_only': False,
            'new_total': 15.0,
            'state_changed': True,
            'details': {'key': 'value'},
            'new_state': 'active',
            'run_id': 'run123',
            'group_id': 'group123',
        }
        schema = PlaceBidResponse(**data)
        assert schema.product_id == 'prod123'
        assert schema.quantity == 5.0
        assert schema.state_changed is True


class TestRetractBidResponse:
    """Tests for RetractBidResponse schema."""

    def test_valid_retract_bid_response(self):
        """Test creating valid retract bid response."""
        data = {
            'success': True,
            'code': 'BID_RETRACTED',
            'run_id': 'run123',
            'product_id': 'prod123',
            'user_id': 'user123',
            'new_total': 10.0,
            'details': {},
        }
        schema = RetractBidResponse(**data)
        assert schema.product_id == 'prod123'
        assert schema.new_total == 10.0


class TestUpdateRunCommentRequest:
    """Tests for UpdateRunCommentRequest schema."""

    def test_valid_update_comment_request(self):
        """Test creating valid update comment request."""
        data = {'comment': 'Updated comment'}
        schema = UpdateRunCommentRequest(**data)
        assert schema.comment == 'Updated comment'

    def test_update_comment_to_none(self):
        """Test updating comment to None."""
        data = {'comment': None}
        schema = UpdateRunCommentRequest(**data)
        assert schema.comment is None

    def test_default_comment_none(self):
        """Test default comment value is None."""
        schema = UpdateRunCommentRequest()
        assert schema.comment is None

    def test_comment_too_long(self):
        """Test comment exceeding 500 characters raises ValidationError."""
        data = {'comment': 'a' * 501}
        with pytest.raises(ValidationError) as exc_info:
            UpdateRunCommentRequest(**data)
        assert 'comment' in str(exc_info.value)
