"""Unit tests for AdminService."""

from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.error_codes import (
    CANNOT_DELETE_ADMIN_USER,
    CANNOT_DELETE_OWN_ACCOUNT,
    CANNOT_MERGE_SAME_PRODUCT,
    CANNOT_REMOVE_OWN_ADMIN_STATUS,
    PRODUCT_HAS_ACTIVE_BIDS,
    USER_NOT_FOUND,
)
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.models import Product, User
from app.services.admin_service import AdminService


class TestGetUsers:
    """Test cases for AdminService.get_users()."""

    def test_get_users_success(self):
        """Test successfully getting all users."""
        # Arrange
        mock_db = Mock()
        user1 = Mock(spec=User)
        user1.id = uuid4()
        user1.name = 'Alice'
        user1.username = 'alice'
        user1.verified = True
        user1.is_admin = False
        user1.created_at = datetime.now()

        service = AdminService(mock_db)
        service.user_repo.get_all_users = Mock(return_value=[user1])

        # Act
        result = service.get_users()

        # Assert
        assert len(result) == 1
        assert result[0].name == 'Alice'

    def test_get_users_with_search(self):
        """Test getting users with search filter."""
        # Arrange
        mock_db = Mock()
        user1 = Mock(spec=User)
        user1.id = uuid4()
        user1.name = 'Alice'
        user1.username = 'alice'
        user1.verified = True
        user1.is_admin = False
        user1.created_at = datetime.now()

        user2 = Mock(spec=User)
        user2.id = uuid4()
        user2.name = 'Bob'
        user2.username = 'bob'
        user2.verified = True
        user2.is_admin = False
        user2.created_at = datetime.now()

        service = AdminService(mock_db)
        service.user_repo.get_all_users = Mock(return_value=[user1, user2])

        # Act
        result = service.get_users(search='alice')

        # Assert
        assert len(result) == 1
        assert result[0].name == 'Alice'

    def test_get_users_with_verified_filter(self):
        """Test getting users with verified filter."""
        # Arrange
        mock_db = Mock()
        user1 = Mock(spec=User)
        user1.id = uuid4()
        user1.name = 'Alice'
        user1.username = 'alice'
        user1.verified = True
        user1.is_admin = False
        user1.created_at = datetime.now()

        user2 = Mock(spec=User)
        user2.id = uuid4()
        user2.name = 'Bob'
        user2.username = 'bob'
        user2.verified = False
        user2.is_admin = False
        user2.created_at = datetime.now()

        service = AdminService(mock_db)
        service.user_repo.get_all_users = Mock(return_value=[user1, user2])

        # Act
        result = service.get_users(verified=True)

        # Assert
        assert len(result) == 1
        assert result[0].name == 'Alice'


class TestToggleUserVerification:
    """Test cases for AdminService.toggle_user_verification()."""

    def test_toggle_user_verification_success(self, test_user):
        """Test successfully toggling user verification."""
        # Arrange
        mock_db = Mock()
        user_id = uuid4()

        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.verified = False

        service = AdminService(mock_db)
        service.user_repo.get_user_by_id = Mock(return_value=mock_user)

        # Act
        result = service.toggle_user_verification(user_id, test_user)

        # Assert
        assert result.verified is True
        assert mock_user.verified is True

    def test_toggle_user_verification_user_not_found(self, test_user):
        """Test toggling verification for non-existent user."""
        # Arrange
        mock_db = Mock()
        user_id = uuid4()

        service = AdminService(mock_db)
        service.user_repo.get_user_by_id = Mock(return_value=None)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            service.toggle_user_verification(user_id, test_user)

        assert exc_info.value.code == USER_NOT_FOUND


class TestGetProducts:
    """Test cases for AdminService.get_products()."""

    def test_get_products_success(self):
        """Test successfully getting all products."""
        # Arrange
        mock_db = Mock()
        product1 = Mock(spec=Product)
        product1.id = uuid4()
        product1.name = 'Apple'
        product1.brand = 'Fresh'
        product1.unit = 'kg'
        product1.verified = False
        product1.created_at = datetime.now()

        service = AdminService(mock_db)
        service.product_repo.get_all_products = Mock(return_value=[product1])

        # Act
        result = service.get_products()

        # Assert
        assert len(result) == 1
        assert result[0].name == 'Apple'


class TestToggleProductVerification:
    """Test cases for AdminService.toggle_product_verification()."""

    def test_toggle_product_verification_success(self, test_user):
        """Test successfully toggling product verification."""
        # Arrange
        mock_db = Mock()
        product_id = uuid4()

        mock_product = Mock(spec=Product)
        mock_product.id = product_id
        mock_product.verified = False

        service = AdminService(mock_db)
        service.product_repo.get_product_by_id = Mock(return_value=mock_product)

        # Act
        result = service.toggle_product_verification(product_id, test_user)

        # Assert
        assert result.verified is True
        assert mock_product.verified is True
        assert mock_product.verified_by == test_user.id


class TestMergeProducts:
    """Test cases for AdminService.merge_products()."""

    def test_merge_products_success(self, test_user):
        """Test successfully merging products."""
        # Arrange
        mock_db = Mock()
        source_id = uuid4()
        target_id = uuid4()

        source_product = Mock(spec=Product)
        source_product.id = source_id
        source_product.name = 'Apple A'
        target_product = Mock(spec=Product)
        target_product.id = target_id
        target_product.name = 'Apple B'

        service = AdminService(mock_db)
        service.product_repo.get_product_by_id = Mock(side_effect=[source_product, target_product])
        service.product_repo.bulk_update_product_bids = Mock(return_value=5)
        service.product_repo.bulk_update_product_availabilities = Mock(return_value=3)
        service.product_repo.bulk_update_shopping_list_items = Mock(return_value=2)
        service.product_repo.delete_product = Mock()

        # Act
        result = service.merge_products(source_id, target_id, test_user)

        # Assert
        assert result.affected_records == 10
        service.product_repo.delete_product.assert_called_once_with(source_id)

    def test_merge_products_same_product(self, test_user):
        """Test merging product into itself."""
        # Arrange
        mock_db = Mock()
        product_id = uuid4()

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        service = AdminService(mock_db)
        service.product_repo.get_product_by_id = Mock(return_value=mock_product)

        # Act & Assert
        from app.core.exceptions import BadRequestError

        with pytest.raises(BadRequestError) as exc_info:
            service.merge_products(product_id, product_id, test_user)

        assert exc_info.value.code == CANNOT_MERGE_SAME_PRODUCT


class TestDeleteProduct:
    """Test cases for AdminService.delete_product()."""

    def test_delete_product_success(self, test_user):
        """Test successfully deleting a product."""
        # Arrange
        mock_db = Mock()
        product_id = uuid4()

        mock_product = Mock(spec=Product)
        mock_product.id = product_id
        mock_product.name = 'Apple'

        service = AdminService(mock_db)
        service.product_repo.get_product_by_id = Mock(return_value=mock_product)
        service.product_repo.count_product_bids = Mock(return_value=0)
        service.product_repo.delete_product = Mock()

        # Act
        result = service.delete_product(product_id, test_user)

        # Assert
        assert result.deleted_id == str(product_id)
        service.product_repo.delete_product.assert_called_once_with(product_id)

    def test_delete_product_with_bids(self, test_user):
        """Test deleting product with active bids."""
        # Arrange
        mock_db = Mock()
        product_id = uuid4()

        mock_product = Mock(spec=Product)
        mock_product.id = product_id

        service = AdminService(mock_db)
        service.product_repo.get_product_by_id = Mock(return_value=mock_product)
        service.product_repo.count_product_bids = Mock(return_value=5)

        # Act & Assert
        from app.core.exceptions import BadRequestError

        with pytest.raises(BadRequestError) as exc_info:
            service.delete_product(product_id, test_user)

        assert exc_info.value.code == PRODUCT_HAS_ACTIVE_BIDS


class TestDeleteUser:
    """Test cases for AdminService.delete_user()."""

    def test_delete_user_success(self, test_user):
        """Test successfully deleting a user."""
        # Arrange
        mock_db = Mock()
        user_id = uuid4()

        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.name = 'Bob'
        mock_user.is_admin = False

        service = AdminService(mock_db)
        service.user_repo.get_user_by_id = Mock(return_value=mock_user)
        service.user_repo.delete_user = Mock()

        # Act
        result = service.delete_user(user_id, test_user)

        # Assert
        assert result.deleted_id == str(user_id)
        service.user_repo.delete_user.assert_called_once_with(user_id)

    def test_delete_user_own_account(self, test_user):
        """Test deleting own account."""
        # Arrange
        mock_db = Mock()
        service = AdminService(mock_db)
        service.user_repo.get_user_by_id = Mock(return_value=test_user)

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            service.delete_user(test_user.id, test_user)

        assert exc_info.value.code == CANNOT_DELETE_OWN_ACCOUNT

    def test_delete_user_admin(self, test_user):
        """Test deleting admin user."""
        # Arrange
        mock_db = Mock()
        admin_id = uuid4()

        admin_user = Mock(spec=User)
        admin_user.id = admin_id
        admin_user.is_admin = True

        service = AdminService(mock_db)
        service.user_repo.get_user_by_id = Mock(return_value=admin_user)

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            service.delete_user(admin_id, test_user)

        assert exc_info.value.code == CANNOT_DELETE_ADMIN_USER


class TestUpdateUser:
    """Test cases for AdminService.update_user()."""

    def test_update_user_cannot_remove_own_admin(self, test_user):
        """Test that admin cannot remove their own admin status."""
        # Arrange
        mock_db = Mock()
        service = AdminService(mock_db)

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            service.update_user(test_user.id, {'is_admin': False}, test_user)

        assert exc_info.value.code == CANNOT_REMOVE_OWN_ADMIN_STATUS
