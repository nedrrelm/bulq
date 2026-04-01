"""Unit tests for shopping schemas."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.api.schemas.shopping_schemas import (
    AddMorePurchaseRequest,
    CompleteShoppingResponse,
    MarkPurchasedRequest,
    MarkPurchasedResponse,
    PriceObservation,
    ShoppingListItemResponse,
    UpdateAvailabilityPriceRequest,
)


class TestPriceObservation:
    """Tests for PriceObservation schema."""

    def test_valid_price_observation(self):
        """Test creating valid price observation."""
        data = {
            'price': 3.99,
            'notes': 'Regular price',
            'created_at': '2024-01-01T00:00:00Z',
        }
        schema = PriceObservation(**data)
        assert schema.price == 3.99
        assert schema.notes == 'Regular price'
        assert schema.created_at == '2024-01-01T00:00:00Z'

    def test_price_observation_with_none_created_at(self):
        """Test price observation with None created_at."""
        data = {
            'price': 3.99,
            'notes': 'Regular price',
            'created_at': None,
        }
        schema = PriceObservation(**data)
        assert schema.created_at is None

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        data = {'price': 3.99}
        with pytest.raises(ValidationError) as exc_info:
            PriceObservation(**data)
        assert 'notes' in str(exc_info.value)


class TestShoppingListItemResponse:
    """Tests for ShoppingListItemResponse schema."""

    def test_valid_shopping_list_item_unpurchased(self):
        """Test creating valid unpurchased shopping list item."""
        data = {
            'id': 'item123',
            'product_id': 'prod123',
            'product_name': 'Milk',
            'product_unit': 'L',
            'requested_quantity': 5.0,
            'recent_prices': [],
            'purchased_quantity': None,
            'purchased_price_per_unit': None,
            'purchased_total': None,
            'is_purchased': False,
            'purchase_order': None,
        }
        schema = ShoppingListItemResponse(**data)
        assert schema.id == 'item123'
        assert schema.product_name == 'Milk'
        assert schema.is_purchased is False
        assert schema.purchased_quantity is None

    def test_valid_shopping_list_item_purchased(self):
        """Test creating valid purchased shopping list item."""
        data = {
            'id': 'item123',
            'product_id': 'prod123',
            'product_name': 'Milk',
            'product_unit': 'L',
            'requested_quantity': 5.0,
            'recent_prices': [
                {
                    'price': 3.99,
                    'notes': 'Regular',
                    'created_at': '2024-01-01T00:00:00Z',
                }
            ],
            'purchased_quantity': 5.0,
            'purchased_price_per_unit': '3.99',
            'purchased_total': '19.95',
            'is_purchased': True,
            'purchase_order': 1,
        }
        schema = ShoppingListItemResponse(**data)
        assert schema.is_purchased is True
        assert schema.purchased_quantity == 5.0
        assert schema.purchase_order == 1

    def test_default_product_unit_none(self):
        """Test default value for product_unit is None."""
        data = {
            'id': 'item123',
            'product_id': 'prod123',
            'product_name': 'Milk',
            'requested_quantity': 5.0,
            'recent_prices': [],
            'purchased_quantity': None,
            'purchased_price_per_unit': None,
            'purchased_total': None,
            'is_purchased': False,
        }
        schema = ShoppingListItemResponse(**data)
        assert schema.product_unit is None


class TestUpdateAvailabilityPriceRequest:
    """Tests for UpdateAvailabilityPriceRequest schema."""

    def test_valid_update_availability_price(self):
        """Test creating valid update availability price request."""
        data = {
            'price': Decimal('3.99'),
            'notes': 'In stock',
            'minimum_quantity': 10,
        }
        schema = UpdateAvailabilityPriceRequest(**data)
        assert schema.price == Decimal('3.99')
        assert schema.notes == 'In stock'
        assert schema.minimum_quantity == 10

    def test_default_notes_empty_string(self):
        """Test default notes value is empty string."""
        data = {'price': Decimal('3.99')}
        schema = UpdateAvailabilityPriceRequest(**data)
        assert schema.notes == ''

    def test_default_minimum_quantity_none(self):
        """Test default minimum_quantity value is None."""
        data = {'price': Decimal('3.99')}
        schema = UpdateAvailabilityPriceRequest(**data)
        assert schema.minimum_quantity is None

    def test_price_zero_or_negative(self):
        """Test price <= 0 raises ValidationError."""
        data = {'price': Decimal('0')}
        with pytest.raises(ValidationError) as exc_info:
            UpdateAvailabilityPriceRequest(**data)
        assert 'price' in str(exc_info.value)

    def test_price_too_large(self):
        """Test price exceeding 99999.99 raises ValidationError."""
        data = {'price': Decimal('100000')}
        with pytest.raises(ValidationError) as exc_info:
            UpdateAvailabilityPriceRequest(**data)
        assert 'price' in str(exc_info.value)

    def test_price_too_many_decimal_places(self):
        """Test price with more than 2 decimal places raises ValidationError."""
        data = {'price': Decimal('3.999')}
        with pytest.raises(ValidationError) as exc_info:
            UpdateAvailabilityPriceRequest(**data)
        assert 'price' in str(exc_info.value)

    def test_notes_strip_whitespace(self):
        """Test notes are stripped of whitespace."""
        data = {'price': Decimal('3.99'), 'notes': '  In stock  '}
        schema = UpdateAvailabilityPriceRequest(**data)
        assert schema.notes == 'In stock'

    def test_notes_max_length(self):
        """Test notes at maximum 200 characters."""
        data = {'price': Decimal('3.99'), 'notes': 'a' * 200}
        schema = UpdateAvailabilityPriceRequest(**data)
        assert len(schema.notes) == 200

    def test_minimum_quantity_too_small(self):
        """Test minimum_quantity less than 1 raises ValidationError."""
        data = {'price': Decimal('3.99'), 'minimum_quantity': 0}
        with pytest.raises(ValidationError) as exc_info:
            UpdateAvailabilityPriceRequest(**data)
        assert 'minimum_quantity' in str(exc_info.value)

    def test_minimum_quantity_too_large(self):
        """Test minimum_quantity exceeding 9999 raises ValidationError."""
        data = {'price': Decimal('3.99'), 'minimum_quantity': 10000}
        with pytest.raises(ValidationError) as exc_info:
            UpdateAvailabilityPriceRequest(**data)
        assert 'minimum_quantity' in str(exc_info.value)


class TestMarkPurchasedRequest:
    """Tests for MarkPurchasedRequest schema."""

    def test_valid_mark_purchased_request(self):
        """Test creating valid mark purchased request."""
        data = {
            'quantity': Decimal('5.00'),
            'price_per_unit': Decimal('3.99'),
            'total': Decimal('19.95'),
        }
        schema = MarkPurchasedRequest(**data)
        assert schema.quantity == Decimal('5.00')
        assert schema.price_per_unit == Decimal('3.99')
        assert schema.total == Decimal('19.95')

    def test_quantity_zero_or_negative(self):
        """Test quantity <= 0 raises ValidationError."""
        data = {
            'quantity': Decimal('0'),
            'price_per_unit': Decimal('3.99'),
            'total': Decimal('0'),
        }
        with pytest.raises(ValidationError) as exc_info:
            MarkPurchasedRequest(**data)
        assert 'quantity' in str(exc_info.value)

    def test_quantity_too_large(self):
        """Test quantity exceeding 9999 raises ValidationError."""
        data = {
            'quantity': Decimal('10000'),
            'price_per_unit': Decimal('3.99'),
            'total': Decimal('39990'),
        }
        with pytest.raises(ValidationError) as exc_info:
            MarkPurchasedRequest(**data)
        assert 'quantity' in str(exc_info.value)

    def test_total_too_large(self):
        """Test total exceeding 999999.99 raises ValidationError."""
        data = {
            'quantity': Decimal('5.00'),
            'price_per_unit': Decimal('200000'),
            'total': Decimal('1000000'),
        }
        with pytest.raises(ValidationError) as exc_info:
            MarkPurchasedRequest(**data)
        assert 'total' in str(exc_info.value)


class TestMarkPurchasedResponse:
    """Tests for MarkPurchasedResponse schema."""

    def test_valid_mark_purchased_response(self):
        """Test creating valid mark purchased response."""
        data = {
            'success': True,
            'code': 'ITEM_MARKED_PURCHASED',
            'purchase_order': 1,
            'details': {'key': 'value'},
        }
        schema = MarkPurchasedResponse(**data)
        assert schema.success is True
        assert schema.code == 'ITEM_MARKED_PURCHASED'
        assert schema.purchase_order == 1

    def test_default_success_value(self):
        """Test default success value."""
        data = {
            'code': 'ITEM_MARKED_PURCHASED',
            'purchase_order': 1,
        }
        schema = MarkPurchasedResponse(**data)
        assert schema.success is True

    def test_default_details_empty_dict(self):
        """Test default details value is empty dict."""
        data = {
            'code': 'ITEM_MARKED_PURCHASED',
            'purchase_order': 1,
        }
        schema = MarkPurchasedResponse(**data)
        assert schema.details == {}


class TestAddMorePurchaseRequest:
    """Tests for AddMorePurchaseRequest schema."""

    def test_valid_add_more_purchase_request(self):
        """Test creating valid add more purchase request."""
        data = {
            'quantity': Decimal('2.00'),
            'price_per_unit': Decimal('3.99'),
            'total': Decimal('7.98'),
        }
        schema = AddMorePurchaseRequest(**data)
        assert schema.quantity == Decimal('2.00')
        assert schema.price_per_unit == Decimal('3.99')
        assert schema.total == Decimal('7.98')

    def test_quantity_validation(self):
        """Test quantity validation rules."""
        data = {
            'quantity': Decimal('0'),
            'price_per_unit': Decimal('3.99'),
            'total': Decimal('0'),
        }
        with pytest.raises(ValidationError) as exc_info:
            AddMorePurchaseRequest(**data)
        assert 'quantity' in str(exc_info.value)


class TestCompleteShoppingResponse:
    """Tests for CompleteShoppingResponse schema."""

    def test_valid_complete_shopping_response(self):
        """Test creating valid complete shopping response."""
        data = {
            'success': True,
            'code': 'SHOPPING_COMPLETED',
            'state': 'adjusting',
            'details': {'items_purchased': 10},
        }
        schema = CompleteShoppingResponse(**data)
        assert schema.success is True
        assert schema.code == 'SHOPPING_COMPLETED'
        assert schema.state == 'adjusting'

    def test_default_success_value(self):
        """Test default success value."""
        data = {
            'code': 'SHOPPING_COMPLETED',
            'state': 'adjusting',
        }
        schema = CompleteShoppingResponse(**data)
        assert schema.success is True

    def test_default_details_empty_dict(self):
        """Test default details value is empty dict."""
        data = {
            'code': 'SHOPPING_COMPLETED',
            'state': 'adjusting',
        }
        schema = CompleteShoppingResponse(**data)
        assert schema.details == {}
