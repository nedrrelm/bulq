"""Unit tests for ProductService."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.error_codes import (
    PRODUCT_NAME_EMPTY,
    PRODUCT_PRICE_NEGATIVE,
    PRODUCT_PRICE_ZERO,
    STORE_NOT_FOUND,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.models import Product, ProductAvailability, Store
from app.services.product_service import ProductService


class TestSearchProducts:
    """Test cases for ProductService.search_products()."""

    def test_search_products_success(self):
        """Test successfully searching for products."""
        # Arrange
        mock_db = Mock()
        product_id = uuid4()
        store_id = uuid4()

        mock_product = Mock(spec=Product)
        mock_product.id = product_id
        mock_product.name = 'Apple'
        mock_product.brand = 'Fresh'

        mock_store = Mock(spec=Store)
        mock_store.id = store_id
        mock_store.name = 'Test Store'

        mock_availability = Mock(spec=ProductAvailability)
        mock_availability.store_id = store_id
        mock_availability.price = 1.99

        service = ProductService(mock_db)
        service.product_repo.search_products = Mock(return_value=[mock_product])
        service.product_repo.get_product_availabilities = Mock(return_value=[mock_availability])
        service.store_repo.get_store_by_id = Mock(return_value=mock_store)

        # Act
        result = service.search_products('apple')

        # Assert
        assert len(result) == 1
        assert result[0].id == str(product_id)
        assert result[0].name == 'Apple'
        assert result[0].brand == 'Fresh'
        assert len(result[0].stores) == 1
        assert result[0].stores[0].store_name == 'Test Store'
        assert result[0].stores[0].price == 1.99

    def test_search_products_empty_results(self):
        """Test searching with no results."""
        # Arrange
        mock_db = Mock()
        service = ProductService(mock_db)
        service.product_repo.search_products = Mock(return_value=[])

        # Act
        result = service.search_products('nonexistent')

        # Assert
        assert result == []

    def test_search_products_multiple_stores(self):
        """Test product available at multiple stores."""
        # Arrange
        mock_db = Mock()
        product_id = uuid4()
        store1_id = uuid4()
        store2_id = uuid4()

        mock_product = Mock(spec=Product)
        mock_product.id = product_id
        mock_product.name = 'Apple'
        mock_product.brand = 'Fresh'

        mock_store1 = Mock(spec=Store)
        mock_store1.id = store1_id
        mock_store1.name = 'Store A'

        mock_store2 = Mock(spec=Store)
        mock_store2.id = store2_id
        mock_store2.name = 'Store B'

        mock_avail1 = Mock(spec=ProductAvailability)
        mock_avail1.store_id = store1_id
        mock_avail1.price = 1.99

        mock_avail2 = Mock(spec=ProductAvailability)
        mock_avail2.store_id = store2_id
        mock_avail2.price = 2.49

        service = ProductService(mock_db)
        service.product_repo.search_products = Mock(return_value=[mock_product])
        service.product_repo.get_product_availabilities = Mock(
            return_value=[mock_avail1, mock_avail2]
        )
        service.store_repo.get_store_by_id = Mock(
            side_effect=lambda sid: mock_store1 if sid == store1_id else mock_store2
        )

        # Act
        result = service.search_products('apple')

        # Assert
        assert len(result) == 1
        assert len(result[0].stores) == 2


class TestGetSimilarProducts:
    """Test cases for ProductService.get_similar_products()."""

    def test_get_similar_products_success(self):
        """Test successfully getting similar products."""
        # Arrange
        mock_db = Mock()
        product_id = uuid4()

        mock_product = Mock(spec=Product)
        mock_product.id = product_id
        mock_product.name = 'Apple'
        mock_product.brand = 'Fresh'

        service = ProductService(mock_db)
        service.product_repo.search_products = Mock(return_value=[mock_product])
        service.product_repo.get_product_availabilities = Mock(return_value=[])

        # Act
        result = service.get_similar_products('apple', limit=5)

        # Assert
        assert len(result) == 1
        assert result[0].name == 'Apple'

    def test_get_similar_products_empty_name(self):
        """Test with empty name."""
        # Arrange
        mock_db = Mock()
        service = ProductService(mock_db)

        # Act
        result = service.get_similar_products('', limit=5)

        # Assert
        assert result == []

    def test_get_similar_products_respects_limit(self):
        """Test that limit parameter is respected."""
        # Arrange
        mock_db = Mock()

        # Create 10 mock products
        mock_products = []
        for i in range(10):
            p = Mock(spec=Product)
            p.id = uuid4()
            p.name = f'Apple {i}'
            p.brand = 'Fresh'
            mock_products.append(p)

        service = ProductService(mock_db)
        service.product_repo.search_products = Mock(return_value=mock_products)
        service.product_repo.get_product_availabilities = Mock(return_value=[])
        service.store_repo.get_store_by_id = Mock(return_value=None)

        # Act
        result = service.get_similar_products('apple', limit=3)

        # Assert
        assert len(result) == 3


class TestGetProductDetails:
    """Test cases for ProductService.get_product_details()."""

    def test_get_product_details_success(self):
        """Test successfully getting product details."""
        # Arrange
        mock_db = Mock()
        product_id = uuid4()
        store_id = uuid4()

        mock_product = Mock(spec=Product)
        mock_product.id = product_id
        mock_product.name = 'Apple'
        mock_product.brand = 'Fresh'
        mock_product.unit = 'kg'

        mock_store = Mock(spec=Store)
        mock_store.id = store_id
        mock_store.name = 'Test Store'

        mock_availability = Mock(spec=ProductAvailability)
        mock_availability.store_id = store_id
        mock_availability.price = 1.99
        mock_availability.notes = 'Fresh today'
        mock_availability.created_at = None

        service = ProductService(mock_db)
        service.product_repo.get_product_by_id = Mock(return_value=mock_product)
        service.product_repo.get_product_availabilities = Mock(return_value=[mock_availability])
        service.store_repo.get_store_by_id = Mock(return_value=mock_store)
        service.shopping_repo.get_shopping_list_items_by_product = Mock(return_value=[])

        # Act
        result = service.get_product_details(product_id)

        # Assert
        assert result is not None
        assert result.id == str(product_id)
        assert result.name == 'Apple'
        assert result.brand == 'Fresh'
        assert result.unit == 'kg'
        assert len(result.stores) == 1
        assert result.stores[0].store_name == 'Test Store'
        assert result.stores[0].current_price == 1.99

    def test_get_product_details_not_found(self):
        """Test getting details for non-existent product."""
        # Arrange
        mock_db = Mock()
        product_id = uuid4()

        service = ProductService(mock_db)
        service.product_repo.get_product_by_id = Mock(return_value=None)

        # Act
        result = service.get_product_details(product_id)

        # Assert
        assert result is None


class TestCreateProduct:
    """Test cases for ProductService.create_product()."""

    def test_create_product_success_minimal(self):
        """Test successfully creating a product with minimal data."""
        # Arrange
        mock_db = Mock()
        product_id = uuid4()

        mock_product = Mock(spec=Product)
        mock_product.id = product_id
        mock_product.name = 'Apple'
        mock_product.brand = None
        mock_product.unit = None

        service = ProductService(mock_db)
        service.product_repo.create_product = Mock(return_value=mock_product)

        # Act
        result, availability = service.create_product(name='Apple')

        # Assert
        assert result.id == product_id
        service.product_repo.create_product.assert_called_once_with('Apple', None, None)
        assert availability is None

    def test_create_product_with_store_and_price(self):
        """Test creating product with store and price."""
        # Arrange
        mock_db = Mock()
        product_id = uuid4()
        store_id = uuid4()
        user_id = uuid4()

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        mock_store = Mock(spec=Store)
        mock_store.id = store_id

        mock_availability = Mock(spec=ProductAvailability)
        mock_availability.id = uuid4()

        service = ProductService(mock_db)
        service.product_repo.create_product = Mock(return_value=mock_product)
        service.store_repo.get_store_by_id = Mock(return_value=mock_store)
        service.product_repo.create_product_availability = Mock(return_value=mock_availability)

        # Act
        result, availability = service.create_product(
            name='Apple', brand='Fresh', unit='kg', store_id=store_id, price=1.99, user_id=user_id
        )

        # Assert
        assert result.id == product_id
        assert availability is not None
        service.product_repo.create_product_availability.assert_called_once_with(
            product_id, store_id, price=1.99, minimum_quantity=None, user_id=user_id
        )

    def test_create_product_empty_name(self):
        """Test creating product with empty name."""
        # Arrange
        mock_db = Mock()
        service = ProductService(mock_db)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            service.create_product(name='')

        assert exc_info.value.code == PRODUCT_NAME_EMPTY

    def test_create_product_whitespace_name(self):
        """Test creating product with whitespace-only name."""
        # Arrange
        mock_db = Mock()
        service = ProductService(mock_db)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            service.create_product(name='   ')

        assert exc_info.value.code == PRODUCT_NAME_EMPTY

    def test_create_product_negative_price(self):
        """Test creating product with negative price."""
        # Arrange
        mock_db = Mock()
        service = ProductService(mock_db)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            service.create_product(name='Apple', price=-1.0)

        assert exc_info.value.code == PRODUCT_PRICE_NEGATIVE

    def test_create_product_zero_price(self):
        """Test creating product with zero price."""
        # Arrange
        mock_db = Mock()
        service = ProductService(mock_db)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            service.create_product(name='Apple', price=0.0)

        assert exc_info.value.code == PRODUCT_PRICE_ZERO

    def test_create_product_store_not_found(self):
        """Test creating product with non-existent store."""
        # Arrange
        mock_db = Mock()
        store_id = uuid4()

        service = ProductService(mock_db)
        service.store_repo.get_store_by_id = Mock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            service.create_product(name='Apple', store_id=store_id, price=1.99)

        assert exc_info.value.code == STORE_NOT_FOUND

    def test_create_product_strips_whitespace(self):
        """Test that product name is stripped of whitespace."""
        # Arrange
        mock_db = Mock()
        product_id = uuid4()

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        service = ProductService(mock_db)
        service.product_repo.create_product = Mock(return_value=mock_product)

        # Act
        service.create_product(name='  Apple  ')

        # Assert
        service.product_repo.create_product.assert_called_once_with('Apple', None, None)
