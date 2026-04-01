"""Unit tests for StoreService."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.error_codes import STORE_NAME_EMPTY, STORE_NOT_FOUND
from app.core.exceptions import NotFoundError, ValidationError
from app.core.models import Group, Product, Run, Store
from app.core.run_state import RunState
from app.services.store_service import StoreService


class TestGetAllStores:
    """Test cases for StoreService.get_all_stores()."""

    def test_get_all_stores_success(self):
        """Test successfully getting all stores."""
        # Arrange
        mock_db = Mock()
        mock_stores = [Mock(spec=Store) for _ in range(3)]

        service = StoreService(mock_db)
        service.store_repo.get_all_stores = Mock(return_value=mock_stores)

        # Act
        result = service.get_all_stores(limit=100, offset=0)

        # Assert
        assert len(result) == 3
        service.store_repo.get_all_stores.assert_called_once_with(100, 0)


class TestGetSimilarStores:
    """Test cases for StoreService.get_similar_stores()."""

    def test_get_similar_stores_success(self):
        """Test successfully getting similar stores."""
        # Arrange
        mock_db = Mock()
        mock_stores = [Mock(spec=Store) for _ in range(5)]

        service = StoreService(mock_db)
        service.store_repo.search_stores = Mock(return_value=mock_stores)

        # Act
        result = service.get_similar_stores('Walmart', limit=5)

        # Assert
        assert len(result) == 5

    def test_get_similar_stores_empty_name(self):
        """Test with empty name."""
        # Arrange
        mock_db = Mock()
        service = StoreService(mock_db)

        # Act
        result = service.get_similar_stores('', limit=5)

        # Assert
        assert result == []

    def test_get_similar_stores_respects_limit(self):
        """Test that limit parameter is respected."""
        # Arrange
        mock_db = Mock()
        mock_stores = [Mock(spec=Store) for _ in range(10)]

        service = StoreService(mock_db)
        service.store_repo.search_stores = Mock(return_value=mock_stores)

        # Act
        result = service.get_similar_stores('Walmart', limit=3)

        # Assert
        assert len(result) == 3


class TestCreateStore:
    """Test cases for StoreService.create_store()."""

    def test_create_store_success(self):
        """Test successfully creating a store."""
        # Arrange
        mock_db = Mock()
        store_id = uuid4()

        mock_store = Mock(spec=Store)
        mock_store.id = store_id
        mock_store.name = 'Walmart'

        service = StoreService(mock_db)
        service.store_repo.create_store = Mock(return_value=mock_store)

        # Act
        result = service.create_store('Walmart')

        # Assert
        assert result.id == store_id
        assert result.name == 'Walmart'
        service.store_repo.create_store.assert_called_once_with('Walmart')

    def test_create_store_empty_name(self):
        """Test creating store with empty name."""
        # Arrange
        mock_db = Mock()
        service = StoreService(mock_db)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            service.create_store('')

        assert exc_info.value.code == STORE_NAME_EMPTY

    def test_create_store_whitespace_name(self):
        """Test creating store with whitespace-only name."""
        # Arrange
        mock_db = Mock()
        service = StoreService(mock_db)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            service.create_store('   ')

        assert exc_info.value.code == STORE_NAME_EMPTY

    def test_create_store_strips_whitespace(self):
        """Test that store name is stripped of whitespace."""
        # Arrange
        mock_db = Mock()
        mock_store = Mock(spec=Store)

        service = StoreService(mock_db)
        service.store_repo.create_store = Mock(return_value=mock_store)

        # Act
        service.create_store('  Walmart  ')

        # Assert
        service.store_repo.create_store.assert_called_once_with('Walmart')


class TestGetStoreById:
    """Test cases for StoreService.get_store_by_id()."""

    def test_get_store_by_id_success(self):
        """Test successfully getting store by ID."""
        # Arrange
        mock_db = Mock()
        store_id = uuid4()

        mock_store = Mock(spec=Store)
        mock_store.id = store_id
        mock_store.name = 'Walmart'

        service = StoreService(mock_db)
        service.store_repo.get_store_by_id = Mock(return_value=mock_store)

        # Act
        result = service.get_store_by_id(store_id)

        # Assert
        assert result.id == store_id
        assert result.name == 'Walmart'

    def test_get_store_by_id_not_found(self):
        """Test getting non-existent store."""
        # Arrange
        mock_db = Mock()
        store_id = uuid4()

        service = StoreService(mock_db)
        service.store_repo.get_store_by_id = Mock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            service.get_store_by_id(store_id)

        assert exc_info.value.code == STORE_NOT_FOUND


class TestGetStorePageData:
    """Test cases for StoreService.get_store_page_data()."""

    def test_get_store_page_data_success(self):
        """Test successfully getting store page data."""
        # Arrange
        mock_db = Mock()
        store_id = uuid4()
        user_id = uuid4()
        product_id = uuid4()
        run_id = uuid4()
        group_id = uuid4()

        mock_store = Mock(spec=Store)
        mock_store.id = store_id
        mock_store.name = 'Walmart'

        mock_product = Mock(spec=Product)
        mock_product.id = product_id
        mock_product.name = 'Apple'
        mock_product.brand = 'Fresh'
        mock_product.unit = 'kg'

        mock_availability = Mock()
        mock_availability.price = 1.99

        mock_run = Mock(spec=Run)
        mock_run.id = run_id
        mock_run.group_id = group_id
        mock_run.store_id = store_id
        mock_run.state = RunState.ACTIVE
        mock_run.planned_on = None

        mock_group = Mock(spec=Group)
        mock_group.id = group_id
        mock_group.name = 'Test Group'

        mock_participation = Mock()
        mock_participation.is_leader = True
        mock_user = Mock()
        mock_user.name = 'Leader'
        mock_participation.user = mock_user

        service = StoreService(mock_db)
        service.store_repo.get_store_by_id = Mock(return_value=mock_store)
        service.store_repo.get_products_by_store_from_availabilities = Mock(
            return_value=[mock_product]
        )
        service.product_repo.get_availability_by_product_and_store = Mock(
            return_value=mock_availability
        )
        service.store_repo.get_active_runs_by_store_for_user = Mock(return_value=[mock_run])
        service.group_repo.get_group_by_id = Mock(return_value=mock_group)
        service.run_repo.get_run_participations = Mock(return_value=[mock_participation])

        # Act
        result = service.get_store_page_data(store_id, user_id)

        # Assert
        assert result.store.id == str(store_id)
        assert result.store.name == 'Walmart'
        assert len(result.products) == 1
        assert result.products[0].name == 'Apple'
        assert result.products[0].current_price == '1.99'
        assert len(result.active_runs) == 1
        assert result.active_runs[0].group_name == 'Test Group'

    def test_get_store_page_data_no_products(self):
        """Test getting store page data with no products."""
        # Arrange
        mock_db = Mock()
        store_id = uuid4()
        user_id = uuid4()

        mock_store = Mock(spec=Store)
        mock_store.id = store_id
        mock_store.name = 'Walmart'

        service = StoreService(mock_db)
        service.store_repo.get_store_by_id = Mock(return_value=mock_store)
        service.store_repo.get_products_by_store_from_availabilities = Mock(return_value=[])
        service.store_repo.get_active_runs_by_store_for_user = Mock(return_value=[])

        # Act
        result = service.get_store_page_data(store_id, user_id)

        # Assert
        assert result.store.name == 'Walmart'
        assert len(result.products) == 0
        assert len(result.active_runs) == 0
