"""Unit tests for store schemas."""

import pytest
from pydantic import ValidationError

from app.api.schemas.store_schemas import (
    CreateStoreRequest,
    StorePageResponse,
    StoreProductResponse,
    StoreResponse,
    StoreRunResponse,
)


class TestStoreResponse:
    """Tests for StoreResponse schema."""

    def test_valid_store_response(self):
        """Test creating valid store response."""
        data = {'id': 'store123', 'name': 'Costco'}
        schema = StoreResponse(**data)
        assert schema.id == 'store123'
        assert schema.name == 'Costco'

    def test_missing_id(self):
        """Test missing id raises ValidationError."""
        data = {'name': 'Costco'}
        with pytest.raises(ValidationError) as exc_info:
            StoreResponse(**data)
        assert 'id' in str(exc_info.value)

    def test_missing_name(self):
        """Test missing name raises ValidationError."""
        data = {'id': 'store123'}
        with pytest.raises(ValidationError) as exc_info:
            StoreResponse(**data)
        assert 'name' in str(exc_info.value)

    def test_serialization(self):
        """Test schema serialization."""
        schema = StoreResponse(id='store123', name='Costco')
        data = schema.model_dump()
        assert data == {'id': 'store123', 'name': 'Costco'}


class TestCreateStoreRequest:
    """Tests for CreateStoreRequest schema."""

    def test_valid_create_store_request(self):
        """Test creating valid store request."""
        data = {'name': 'Costco Downtown'}
        schema = CreateStoreRequest(**data)
        assert schema.name == 'Costco Downtown'

    def test_name_at_min_length(self):
        """Test name at minimum length of 1."""
        data = {'name': 'A'}
        schema = CreateStoreRequest(**data)
        assert schema.name == 'A'

    def test_name_at_max_length(self):
        """Test name at maximum length of 200."""
        data = {'name': 'A' * 200}
        schema = CreateStoreRequest(**data)
        assert len(schema.name) == 200

    def test_name_empty_string(self):
        """Test empty name raises ValidationError."""
        data = {'name': ''}
        with pytest.raises(ValidationError) as exc_info:
            CreateStoreRequest(**data)
        assert 'name' in str(exc_info.value)

    def test_name_too_long(self):
        """Test name exceeding 200 characters raises ValidationError."""
        data = {'name': 'A' * 201}
        with pytest.raises(ValidationError) as exc_info:
            CreateStoreRequest(**data)
        assert 'name' in str(exc_info.value)

    def test_missing_name(self):
        """Test missing name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CreateStoreRequest()
        assert 'name' in str(exc_info.value)


class TestStoreProductResponse:
    """Tests for StoreProductResponse schema."""

    def test_valid_store_product_response(self):
        """Test creating valid store product response."""
        data = {
            'id': 'prod123',
            'name': 'Milk',
            'brand': 'Organic',
            'unit': 'L',
            'current_price': '3.99',
        }
        schema = StoreProductResponse(**data)
        assert schema.id == 'prod123'
        assert schema.name == 'Milk'
        assert schema.brand == 'Organic'
        assert schema.unit == 'L'
        assert schema.current_price == '3.99'

    def test_store_product_with_none_optional_fields(self):
        """Test store product with None optional fields."""
        data = {
            'id': 'prod123',
            'name': 'Milk',
            'brand': None,
            'unit': None,
            'current_price': None,
        }
        schema = StoreProductResponse(**data)
        assert schema.brand is None
        assert schema.unit is None
        assert schema.current_price is None


class TestStoreRunResponse:
    """Tests for StoreRunResponse schema."""

    def test_valid_store_run_response(self):
        """Test creating valid store run response."""
        data = {
            'id': 'run123',
            'state': 'active',
            'group_id': 'group123',
            'group_name': 'Test Group',
            'store_name': 'Costco',
            'leader_name': 'John Doe',
            'planned_on': '2024-01-01T00:00:00Z',
        }
        schema = StoreRunResponse(**data)
        assert schema.id == 'run123'
        assert schema.state == 'active'
        assert schema.group_name == 'Test Group'
        assert schema.planned_on == '2024-01-01T00:00:00Z'

    def test_store_run_with_none_planned_on(self):
        """Test store run with None planned_on."""
        data = {
            'id': 'run123',
            'state': 'planning',
            'group_id': 'group123',
            'group_name': 'Test Group',
            'store_name': 'Costco',
            'leader_name': 'John Doe',
            'planned_on': None,
        }
        schema = StoreRunResponse(**data)
        assert schema.planned_on is None


class TestStorePageResponse:
    """Tests for StorePageResponse schema."""

    def test_valid_store_page_response(self):
        """Test creating valid store page response."""
        data = {
            'store': {'id': 'store123', 'name': 'Costco'},
            'products': [
                {
                    'id': 'prod1',
                    'name': 'Milk',
                    'brand': 'Organic',
                    'unit': 'L',
                    'current_price': '3.99',
                }
            ],
            'active_runs': [
                {
                    'id': 'run1',
                    'state': 'active',
                    'group_id': 'group1',
                    'group_name': 'Test Group',
                    'store_name': 'Costco',
                    'leader_name': 'John',
                    'planned_on': None,
                }
            ],
        }
        schema = StorePageResponse(**data)
        assert schema.store.id == 'store123'
        assert len(schema.products) == 1
        assert len(schema.active_runs) == 1

    def test_store_page_with_empty_lists(self):
        """Test store page with empty products and runs lists."""
        data = {
            'store': {'id': 'store123', 'name': 'Costco'},
            'products': [],
            'active_runs': [],
        }
        schema = StorePageResponse(**data)
        assert schema.products == []
        assert schema.active_runs == []

    def test_missing_store(self):
        """Test missing store raises ValidationError."""
        data = {
            'products': [],
            'active_runs': [],
        }
        with pytest.raises(ValidationError) as exc_info:
            StorePageResponse(**data)
        assert 'store' in str(exc_info.value)
