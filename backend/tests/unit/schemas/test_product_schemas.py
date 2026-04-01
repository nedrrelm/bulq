"""Unit tests for product schemas."""

import pytest
from pydantic import ValidationError

from app.api.schemas.product_schemas import (
    AvailabilityInfo,
    CreateProductRequest,
    CreateProductResponse,
    PricePoint,
    ProductDetailResponse,
    ProductSearchResult,
    StoreDetail,
    StoreInfo,
)


class TestCreateProductRequest:
    """Tests for CreateProductRequest schema."""

    def test_valid_create_product_request_minimal(self):
        """Test creating product with minimal required fields."""
        data = {'name': 'Milk'}
        schema = CreateProductRequest(**data)
        assert schema.name == 'Milk'
        assert schema.brand is None
        assert schema.unit is None
        assert schema.store_id is None
        assert schema.price is None

    def test_valid_create_product_request_full(self):
        """Test creating product with all fields."""
        data = {
            'name': 'Milk',
            'brand': 'Organic',
            'unit': 'L',
            'store_id': 'store123',
            'price': 3.99,
            'minimum_quantity': 10,
        }
        schema = CreateProductRequest(**data)
        assert schema.name == 'Milk'
        assert schema.brand == 'Organic'
        assert schema.unit == 'L'
        assert schema.store_id == 'store123'
        assert schema.price == 3.99
        assert schema.minimum_quantity == 10

    def test_missing_name(self):
        """Test missing name raises ValidationError."""
        data = {'brand': 'Organic'}
        with pytest.raises(ValidationError) as exc_info:
            CreateProductRequest(**data)
        assert 'name' in str(exc_info.value)

    def test_optional_fields_default_to_none(self):
        """Test optional fields default to None."""
        data = {'name': 'Milk'}
        schema = CreateProductRequest(**data)
        assert schema.brand is None
        assert schema.unit is None
        assert schema.store_id is None


class TestStoreInfo:
    """Tests for StoreInfo schema."""

    def test_valid_store_info(self):
        """Test creating valid store info."""
        data = {'store_id': 'store123', 'store_name': 'Costco', 'price': 3.99}
        schema = StoreInfo(**data)
        assert schema.store_id == 'store123'
        assert schema.store_name == 'Costco'
        assert schema.price == 3.99

    def test_store_info_with_none_price(self):
        """Test store info with None price."""
        data = {'store_id': 'store123', 'store_name': 'Costco', 'price': None}
        schema = StoreInfo(**data)
        assert schema.price is None

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {'store_id': 'store123'}
        with pytest.raises(ValidationError) as exc_info:
            StoreInfo(**data)
        assert 'store_name' in str(exc_info.value)


class TestProductSearchResult:
    """Tests for ProductSearchResult schema."""

    def test_valid_product_search_result(self):
        """Test creating valid product search result."""
        data = {
            'id': 'prod123',
            'name': 'Milk',
            'brand': 'Organic',
            'stores': [{'store_id': 'store1', 'store_name': 'Costco', 'price': 3.99}],
        }
        schema = ProductSearchResult(**data)
        assert schema.id == 'prod123'
        assert schema.name == 'Milk'
        assert len(schema.stores) == 1

    def test_product_search_result_with_none_brand(self):
        """Test product search result with None brand."""
        data = {
            'id': 'prod123',
            'name': 'Milk',
            'brand': None,
            'stores': [],
        }
        schema = ProductSearchResult(**data)
        assert schema.brand is None

    def test_empty_stores_list(self):
        """Test product search result with empty stores list."""
        data = {
            'id': 'prod123',
            'name': 'Milk',
            'brand': 'Organic',
            'stores': [],
        }
        schema = ProductSearchResult(**data)
        assert schema.stores == []


class TestAvailabilityInfo:
    """Tests for AvailabilityInfo schema."""

    def test_valid_availability_info(self):
        """Test creating valid availability info."""
        data = {'store_id': 'store123', 'price': 3.99, 'notes': 'In stock'}
        schema = AvailabilityInfo(**data)
        assert schema.store_id == 'store123'
        assert schema.price == 3.99
        assert schema.notes == 'In stock'

    def test_availability_info_with_none_values(self):
        """Test availability info with None values."""
        data = {'store_id': 'store123', 'price': None, 'notes': None}
        schema = AvailabilityInfo(**data)
        assert schema.price is None
        assert schema.notes is None


class TestCreateProductResponse:
    """Tests for CreateProductResponse schema."""

    def test_valid_create_product_response(self):
        """Test creating valid create product response."""
        data = {
            'id': 'prod123',
            'name': 'Milk',
            'brand': 'Organic',
            'unit': 'L',
            'availability': {
                'store_id': 'store123',
                'price': 3.99,
                'notes': 'Available',
            },
        }
        schema = CreateProductResponse(**data)
        assert schema.id == 'prod123'
        assert schema.name == 'Milk'
        assert schema.availability is not None
        assert schema.availability.price == 3.99

    def test_create_product_response_without_availability(self):
        """Test create product response without availability."""
        data = {
            'id': 'prod123',
            'name': 'Milk',
            'brand': 'Organic',
            'unit': 'L',
            'availability': None,
        }
        schema = CreateProductResponse(**data)
        assert schema.availability is None


class TestPricePoint:
    """Tests for PricePoint schema."""

    def test_valid_price_point_full(self):
        """Test creating valid price point with all fields."""
        data = {
            'price': 3.99,
            'notes': 'Regular price',
            'timestamp': '2024-01-01T00:00:00Z',
            'run_id': 'run123',
        }
        schema = PricePoint(**data)
        assert schema.price == 3.99
        assert schema.notes == 'Regular price'
        assert schema.timestamp == '2024-01-01T00:00:00Z'
        assert schema.run_id == 'run123'

    def test_price_point_with_none_optional_fields(self):
        """Test price point with None optional fields."""
        data = {
            'price': 3.99,
            'notes': 'Regular price',
            'timestamp': None,
            'run_id': None,
        }
        schema = PricePoint(**data)
        assert schema.timestamp is None
        assert schema.run_id is None


class TestStoreDetail:
    """Tests for StoreDetail schema."""

    def test_valid_store_detail(self):
        """Test creating valid store detail."""
        data = {
            'store_id': 'store123',
            'store_name': 'Costco',
            'current_price': 3.99,
            'price_history': [
                {
                    'price': 3.99,
                    'notes': 'Regular',
                    'timestamp': '2024-01-01T00:00:00Z',
                    'run_id': None,
                }
            ],
            'notes': 'Available',
        }
        schema = StoreDetail(**data)
        assert schema.store_id == 'store123'
        assert schema.store_name == 'Costco'
        assert len(schema.price_history) == 1
        assert schema.notes == 'Available'

    def test_store_detail_with_none_current_price(self):
        """Test store detail with None current price."""
        data = {
            'store_id': 'store123',
            'store_name': 'Costco',
            'current_price': None,
            'price_history': [],
            'notes': 'Not available',
        }
        schema = StoreDetail(**data)
        assert schema.current_price is None
        assert schema.price_history == []


class TestProductDetailResponse:
    """Tests for ProductDetailResponse schema."""

    def test_valid_product_detail_response(self):
        """Test creating valid product detail response."""
        data = {
            'id': 'prod123',
            'name': 'Milk',
            'brand': 'Organic',
            'unit': 'L',
            'stores': [
                {
                    'store_id': 'store123',
                    'store_name': 'Costco',
                    'current_price': 3.99,
                    'price_history': [],
                    'notes': 'Available',
                }
            ],
        }
        schema = ProductDetailResponse(**data)
        assert schema.id == 'prod123'
        assert schema.name == 'Milk'
        assert len(schema.stores) == 1

    def test_product_detail_with_none_optional_fields(self):
        """Test product detail with None optional fields."""
        data = {
            'id': 'prod123',
            'name': 'Milk',
            'brand': None,
            'unit': None,
            'stores': [],
        }
        schema = ProductDetailResponse(**data)
        assert schema.brand is None
        assert schema.unit is None
        assert schema.stores == []

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {'name': 'Milk', 'brand': 'Organic'}
        with pytest.raises(ValidationError) as exc_info:
            ProductDetailResponse(**data)
        assert 'id' in str(exc_info.value)
