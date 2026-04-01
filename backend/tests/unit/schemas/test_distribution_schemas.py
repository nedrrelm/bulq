"""Unit tests for distribution schemas."""

import pytest
from pydantic import ValidationError

from app.api.schemas.distribution_schemas import DistributionProduct, DistributionUser


class TestDistributionProduct:
    """Tests for DistributionProduct schema."""

    def test_valid_distribution_product(self):
        """Test creating valid distribution product."""
        data = {
            'bid_id': 'bid123',
            'product_id': 'prod123',
            'product_name': 'Milk',
            'product_unit': 'L',
            'requested_quantity': 5.0,
            'distributed_quantity': 5.0,
            'price_per_unit': '3.99',
            'subtotal': '19.95',
            'is_picked_up': False,
        }
        schema = DistributionProduct(**data)
        assert schema.bid_id == 'bid123'
        assert schema.product_id == 'prod123'
        assert schema.product_name == 'Milk'
        assert schema.requested_quantity == 5.0
        assert schema.distributed_quantity == 5.0
        assert schema.price_per_unit == '3.99'
        assert schema.subtotal == '19.95'
        assert schema.is_picked_up is False

    def test_distribution_product_with_none_unit(self):
        """Test distribution product with None product_unit."""
        data = {
            'bid_id': 'bid123',
            'product_id': 'prod123',
            'product_name': 'Milk',
            'product_unit': None,
            'requested_quantity': 5.0,
            'distributed_quantity': 5.0,
            'price_per_unit': '3.99',
            'subtotal': '19.95',
            'is_picked_up': False,
        }
        schema = DistributionProduct(**data)
        assert schema.product_unit is None

    def test_default_product_unit_none(self):
        """Test default value for product_unit is None."""
        data = {
            'bid_id': 'bid123',
            'product_id': 'prod123',
            'product_name': 'Milk',
            'requested_quantity': 5.0,
            'distributed_quantity': 5.0,
            'price_per_unit': '3.99',
            'subtotal': '19.95',
            'is_picked_up': False,
        }
        schema = DistributionProduct(**data)
        assert schema.product_unit is None

    def test_distribution_product_picked_up(self):
        """Test distribution product marked as picked up."""
        data = {
            'bid_id': 'bid123',
            'product_id': 'prod123',
            'product_name': 'Milk',
            'product_unit': 'L',
            'requested_quantity': 5.0,
            'distributed_quantity': 4.5,
            'price_per_unit': '3.99',
            'subtotal': '17.96',
            'is_picked_up': True,
        }
        schema = DistributionProduct(**data)
        assert schema.is_picked_up is True
        assert schema.distributed_quantity == 4.5

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'bid_id': 'bid123',
            'product_id': 'prod123',
            'product_name': 'Milk',
        }
        with pytest.raises(ValidationError) as exc_info:
            DistributionProduct(**data)
        errors = str(exc_info.value)
        assert 'requested_quantity' in errors or 'distributed_quantity' in errors

    def test_serialization(self):
        """Test schema serialization."""
        schema = DistributionProduct(
            bid_id='bid123',
            product_id='prod123',
            product_name='Milk',
            product_unit='L',
            requested_quantity=5.0,
            distributed_quantity=5.0,
            price_per_unit='3.99',
            subtotal='19.95',
            is_picked_up=False,
        )
        data = schema.model_dump()
        assert data['bid_id'] == 'bid123'
        assert data['product_name'] == 'Milk'
        assert data['is_picked_up'] is False


class TestDistributionUser:
    """Tests for DistributionUser schema."""

    def test_valid_distribution_user(self):
        """Test creating valid distribution user."""
        data = {
            'user_id': 'user123',
            'user_name': 'John Doe',
            'products': [
                {
                    'bid_id': 'bid1',
                    'product_id': 'prod1',
                    'product_name': 'Milk',
                    'product_unit': 'L',
                    'requested_quantity': 5.0,
                    'distributed_quantity': 5.0,
                    'price_per_unit': '3.99',
                    'subtotal': '19.95',
                    'is_picked_up': False,
                }
            ],
            'total_cost': '19.95',
            'all_picked_up': False,
        }
        schema = DistributionUser(**data)
        assert schema.user_id == 'user123'
        assert schema.user_name == 'John Doe'
        assert len(schema.products) == 1
        assert schema.total_cost == '19.95'
        assert schema.all_picked_up is False

    def test_distribution_user_empty_products(self):
        """Test distribution user with empty products list."""
        data = {
            'user_id': 'user123',
            'user_name': 'John Doe',
            'products': [],
            'total_cost': '0.00',
            'all_picked_up': False,
        }
        schema = DistributionUser(**data)
        assert schema.products == []
        assert schema.total_cost == '0.00'

    def test_default_total_cost(self):
        """Test default value for total_cost is 0.00."""
        data = {
            'user_id': 'user123',
            'user_name': 'John Doe',
            'products': [],
        }
        schema = DistributionUser(**data)
        assert schema.total_cost == '0.00'

    def test_default_all_picked_up(self):
        """Test default value for all_picked_up is False."""
        data = {
            'user_id': 'user123',
            'user_name': 'John Doe',
            'products': [],
        }
        schema = DistributionUser(**data)
        assert schema.all_picked_up is False

    def test_distribution_user_all_picked_up(self):
        """Test distribution user with all products picked up."""
        data = {
            'user_id': 'user123',
            'user_name': 'John Doe',
            'products': [
                {
                    'bid_id': 'bid1',
                    'product_id': 'prod1',
                    'product_name': 'Milk',
                    'product_unit': 'L',
                    'requested_quantity': 5.0,
                    'distributed_quantity': 5.0,
                    'price_per_unit': '3.99',
                    'subtotal': '19.95',
                    'is_picked_up': True,
                }
            ],
            'total_cost': '19.95',
            'all_picked_up': True,
        }
        schema = DistributionUser(**data)
        assert schema.all_picked_up is True
        assert schema.products[0].is_picked_up is True

    def test_distribution_user_multiple_products(self):
        """Test distribution user with multiple products."""
        data = {
            'user_id': 'user123',
            'user_name': 'John Doe',
            'products': [
                {
                    'bid_id': 'bid1',
                    'product_id': 'prod1',
                    'product_name': 'Milk',
                    'product_unit': 'L',
                    'requested_quantity': 5.0,
                    'distributed_quantity': 5.0,
                    'price_per_unit': '3.99',
                    'subtotal': '19.95',
                    'is_picked_up': True,
                },
                {
                    'bid_id': 'bid2',
                    'product_id': 'prod2',
                    'product_name': 'Bread',
                    'product_unit': None,
                    'requested_quantity': 2.0,
                    'distributed_quantity': 2.0,
                    'price_per_unit': '2.50',
                    'subtotal': '5.00',
                    'is_picked_up': False,
                },
            ],
            'total_cost': '24.95',
            'all_picked_up': False,
        }
        schema = DistributionUser(**data)
        assert len(schema.products) == 2
        assert schema.total_cost == '24.95'
        assert schema.products[0].product_name == 'Milk'
        assert schema.products[1].product_name == 'Bread'

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {
            'user_name': 'John Doe',
            'products': [],
        }
        with pytest.raises(ValidationError) as exc_info:
            DistributionUser(**data)
        assert 'user_id' in str(exc_info.value)

    def test_serialization(self):
        """Test schema serialization."""
        schema = DistributionUser(
            user_id='user123',
            user_name='John Doe',
            products=[],
            total_cost='0.00',
            all_picked_up=False,
        )
        data = schema.model_dump()
        assert data['user_id'] == 'user123'
        assert data['user_name'] == 'John Doe'
        assert data['products'] == []
