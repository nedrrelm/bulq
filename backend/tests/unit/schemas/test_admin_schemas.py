"""Unit tests for admin schemas."""

import pytest
from pydantic import ValidationError

from app.api.schemas.admin_schemas import (
    AdminGroupResponse,
    AdminProductResponse,
    AdminStoreResponse,
    AdminUserResponse,
    DeleteResponse,
    MergeResponse,
    UpdateProductRequest,
    UpdateStoreRequest,
    UpdateUserRequest,
    VerificationToggleResponse,
)


class TestAdminUserResponse:
    """Tests for AdminUserResponse schema."""

    def test_valid_admin_user_response(self):
        """Test creating valid admin user response."""
        data = {
            'id': 'user123',
            'name': 'John Doe',
            'username': 'johndoe',
            'verified': True,
            'is_admin': False,
            'created_at': '2024-01-01T00:00:00Z',
        }
        schema = AdminUserResponse(**data)
        assert schema.id == 'user123'
        assert schema.name == 'John Doe'
        assert schema.verified is True
        assert schema.is_admin is False

    def test_admin_user_response_with_none_created_at(self):
        """Test admin user response with None created_at."""
        data = {
            'id': 'user123',
            'name': 'John Doe',
            'username': 'johndoe',
            'verified': False,
            'is_admin': True,
            'created_at': None,
        }
        schema = AdminUserResponse(**data)
        assert schema.created_at is None


class TestAdminProductResponse:
    """Tests for AdminProductResponse schema."""

    def test_valid_admin_product_response(self):
        """Test creating valid admin product response."""
        data = {
            'id': 'prod123',
            'name': 'Milk',
            'brand': 'Organic',
            'unit': 'L',
            'verified': True,
            'created_at': '2024-01-01T00:00:00Z',
        }
        schema = AdminProductResponse(**data)
        assert schema.id == 'prod123'
        assert schema.name == 'Milk'
        assert schema.brand == 'Organic'
        assert schema.verified is True

    def test_admin_product_response_with_none_optional_fields(self):
        """Test admin product response with None optional fields."""
        data = {
            'id': 'prod123',
            'name': 'Milk',
            'brand': None,
            'unit': None,
            'verified': False,
            'created_at': None,
        }
        schema = AdminProductResponse(**data)
        assert schema.brand is None
        assert schema.unit is None
        assert schema.created_at is None


class TestAdminStoreResponse:
    """Tests for AdminStoreResponse schema."""

    def test_valid_admin_store_response(self):
        """Test creating valid admin store response."""
        data = {
            'id': 'store123',
            'name': 'Costco',
            'address': '123 Main St',
            'chain': 'Costco',
            'verified': True,
            'created_at': '2024-01-01T00:00:00Z',
        }
        schema = AdminStoreResponse(**data)
        assert schema.id == 'store123'
        assert schema.name == 'Costco'
        assert schema.address == '123 Main St'
        assert schema.verified is True

    def test_admin_store_response_with_none_optional_fields(self):
        """Test admin store response with None optional fields."""
        data = {
            'id': 'store123',
            'name': 'Costco',
            'address': None,
            'chain': None,
            'verified': False,
            'created_at': None,
        }
        schema = AdminStoreResponse(**data)
        assert schema.address is None
        assert schema.chain is None
        assert schema.created_at is None


class TestAdminGroupResponse:
    """Tests for AdminGroupResponse schema."""

    def test_valid_admin_group_response(self):
        """Test creating valid admin group response."""
        data = {
            'id': 'group123',
            'name': 'Test Group',
            'created_by': 'user123',
            'creator_name': 'John Doe',
            'member_count': 5,
            'created_at': '2024-01-01T00:00:00Z',
        }
        schema = AdminGroupResponse(**data)
        assert schema.id == 'group123'
        assert schema.name == 'Test Group'
        assert schema.created_by == 'user123'
        assert schema.creator_name == 'John Doe'
        assert schema.member_count == 5

    def test_admin_group_response_with_none_created_at(self):
        """Test admin group response with None created_at."""
        data = {
            'id': 'group123',
            'name': 'Test Group',
            'created_by': 'user123',
            'creator_name': 'John Doe',
            'member_count': 5,
            'created_at': None,
        }
        schema = AdminGroupResponse(**data)
        assert schema.created_at is None


class TestVerificationToggleResponse:
    """Tests for VerificationToggleResponse schema."""

    def test_valid_verification_toggle_response(self):
        """Test creating valid verification toggle response."""
        data = {
            'success': True,
            'code': 'VERIFICATION_TOGGLED',
            'id': 'entity123',
            'verified': True,
        }
        schema = VerificationToggleResponse(**data)
        assert schema.success is True
        assert schema.code == 'VERIFICATION_TOGGLED'
        assert schema.id == 'entity123'
        assert schema.verified is True

    def test_default_success_value(self):
        """Test default value for success is True."""
        data = {
            'code': 'VERIFICATION_TOGGLED',
            'id': 'entity123',
            'verified': False,
        }
        schema = VerificationToggleResponse(**data)
        assert schema.success is True


class TestUpdateProductRequest:
    """Tests for UpdateProductRequest schema."""

    def test_valid_update_product_request(self):
        """Test creating valid update product request."""
        data = {
            'name': 'Milk',
            'brand': 'Organic',
            'unit': 'L',
        }
        schema = UpdateProductRequest(**data)
        assert schema.name == 'Milk'
        assert schema.brand == 'Organic'
        assert schema.unit == 'L'

    def test_update_product_with_none_optional_fields(self):
        """Test update product with None optional fields."""
        data = {
            'name': 'Milk',
            'brand': None,
            'unit': None,
        }
        schema = UpdateProductRequest(**data)
        assert schema.brand is None
        assert schema.unit is None

    def test_name_too_short(self):
        """Test name with length 0 raises ValidationError."""
        data = {
            'name': '',
            'brand': 'Organic',
            'unit': 'L',
        }
        with pytest.raises(ValidationError) as exc_info:
            UpdateProductRequest(**data)
        assert 'name' in str(exc_info.value)

    def test_name_too_long(self):
        """Test name exceeding 255 characters raises ValidationError."""
        data = {
            'name': 'a' * 256,
            'brand': 'Organic',
            'unit': 'L',
        }
        with pytest.raises(ValidationError) as exc_info:
            UpdateProductRequest(**data)
        assert 'name' in str(exc_info.value)

    def test_brand_too_long(self):
        """Test brand exceeding 255 characters raises ValidationError."""
        data = {
            'name': 'Milk',
            'brand': 'a' * 256,
            'unit': 'L',
        }
        with pytest.raises(ValidationError) as exc_info:
            UpdateProductRequest(**data)
        assert 'brand' in str(exc_info.value)

    def test_unit_too_long(self):
        """Test unit exceeding 50 characters raises ValidationError."""
        data = {
            'name': 'Milk',
            'brand': 'Organic',
            'unit': 'a' * 51,
        }
        with pytest.raises(ValidationError) as exc_info:
            UpdateProductRequest(**data)
        assert 'unit' in str(exc_info.value)


class TestUpdateStoreRequest:
    """Tests for UpdateStoreRequest schema."""

    def test_valid_update_store_request(self):
        """Test creating valid update store request."""
        data = {
            'name': 'Costco',
            'address': '123 Main St',
            'chain': 'Costco',
            'opening_hours': {'monday': '9-18'},
        }
        schema = UpdateStoreRequest(**data)
        assert schema.name == 'Costco'
        assert schema.address == '123 Main St'
        assert schema.chain == 'Costco'
        assert schema.opening_hours == {'monday': '9-18'}

    def test_update_store_with_none_optional_fields(self):
        """Test update store with None optional fields."""
        data = {
            'name': 'Costco',
            'address': None,
            'chain': None,
            'opening_hours': None,
        }
        schema = UpdateStoreRequest(**data)
        assert schema.address is None
        assert schema.chain is None
        assert schema.opening_hours is None


class TestUpdateUserRequest:
    """Tests for UpdateUserRequest schema."""

    def test_valid_update_user_request(self):
        """Test creating valid update user request."""
        data = {
            'name': 'John Doe',
            'username': 'johndoe',
            'is_admin': True,
            'verified': True,
        }
        schema = UpdateUserRequest(**data)
        assert schema.name == 'John Doe'
        assert schema.username == 'johndoe'
        assert schema.is_admin is True
        assert schema.verified is True

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'name': 'John Doe',
            'username': 'johndoe',
        }
        with pytest.raises(ValidationError) as exc_info:
            UpdateUserRequest(**data)
        errors = str(exc_info.value)
        assert 'is_admin' in errors or 'verified' in errors


class TestMergeResponse:
    """Tests for MergeResponse schema."""

    def test_valid_merge_response(self):
        """Test creating valid merge response."""
        data = {
            'success': True,
            'code': 'MERGE_COMPLETED',
            'source_id': 'source123',
            'target_id': 'target123',
            'affected_records': 10,
            'details': {'merged_type': 'product'},
        }
        schema = MergeResponse(**data)
        assert schema.success is True
        assert schema.code == 'MERGE_COMPLETED'
        assert schema.source_id == 'source123'
        assert schema.target_id == 'target123'
        assert schema.affected_records == 10

    def test_default_success_value(self):
        """Test default value for success is True."""
        data = {
            'code': 'MERGE_COMPLETED',
            'source_id': 'source123',
            'target_id': 'target123',
            'affected_records': 10,
        }
        schema = MergeResponse(**data)
        assert schema.success is True

    def test_default_details_empty_dict(self):
        """Test default value for details is empty dict."""
        data = {
            'code': 'MERGE_COMPLETED',
            'source_id': 'source123',
            'target_id': 'target123',
            'affected_records': 10,
        }
        schema = MergeResponse(**data)
        assert schema.details == {}


class TestDeleteResponse:
    """Tests for DeleteResponse schema."""

    def test_valid_delete_response(self):
        """Test creating valid delete response."""
        data = {
            'success': True,
            'code': 'DELETE_COMPLETED',
            'deleted_id': 'entity123',
            'details': {'deleted_type': 'product'},
        }
        schema = DeleteResponse(**data)
        assert schema.success is True
        assert schema.code == 'DELETE_COMPLETED'
        assert schema.deleted_id == 'entity123'
        assert schema.details == {'deleted_type': 'product'}

    def test_default_success_value(self):
        """Test default value for success is True."""
        data = {
            'code': 'DELETE_COMPLETED',
            'deleted_id': 'entity123',
        }
        schema = DeleteResponse(**data)
        assert schema.success is True

    def test_default_details_empty_dict(self):
        """Test default value for details is empty dict."""
        data = {
            'code': 'DELETE_COMPLETED',
            'deleted_id': 'entity123',
        }
        schema = DeleteResponse(**data)
        assert schema.details == {}
