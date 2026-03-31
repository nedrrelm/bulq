"""Tests for service layer business logic.

Tests the service layer which coordinates business logic using domain-specific repositories.
"""

import pytest

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError, ValidationError
from app.repositories import (
    get_group_repository,
    get_product_repository,
    get_store_repository,
    get_user_repository,
)
from app.services.group_service import GroupService
from app.services.product_service import ProductService
from app.services.run_service import RunService
from app.services.store_service import StoreService

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def user(db_session):
    """Create a test user."""
    user_repo = get_user_repository(db_session)
    return user_repo.create_user(name='Test User', username='testuser', password_hash='hash')


@pytest.fixture
def group(db_session, user):
    """Create a test group with user as member."""
    group_repo = get_group_repository(db_session)
    group = group_repo.create_group(name='Test Group', created_by=user.id)
    group_repo.add_group_member(group.id, user, is_group_admin=False)
    return group


@pytest.fixture
def store(db_session):
    """Create a test store."""
    store_repo = get_store_repository(db_session)
    return store_repo.create_store(name='Test Store')


@pytest.fixture
def product(db_session, store):
    """Create a test product with availability at store."""
    product_repo = get_product_repository(db_session)
    product = product_repo.create_product(name='Test Product', brand='Test Brand')
    product_repo.create_product_availability(product.id, store.id, price=19.99)
    return product


# =============================================================================
# TestRunService
# =============================================================================


class TestRunService:
    """Tests for RunService"""

    @pytest.mark.asyncio
    async def test_create_run_success(self, db_session, user, group, store):
        """Test successful run creation"""
        service = RunService(db_session)
        result = service.create_run(str(group.id), str(store.id), user)

        assert result.group_id == str(group.id)
        assert result.store_id == str(store.id)
        assert result.state == 'planning'
        assert result.id is not None

    def test_create_run_invalid_group_id(self, db_session, user, store):
        """Test run creation with invalid group ID format"""
        service = RunService(db_session)
        with pytest.raises(BadRequestError):
            service.create_run('not-a-uuid', str(store.id), user)

    def test_create_run_nonexistent_group(self, db_session, user, store):
        """Test run creation with non-existent group"""
        service = RunService(db_session)
        fake_uuid = '00000000-0000-0000-0000-000000000000'
        with pytest.raises(NotFoundError) as exc:
            service.create_run(fake_uuid, str(store.id), user)
        assert 'Group' in str(exc.value)

    def test_create_run_user_not_member(self, db_session, user, store):
        """Test run creation when user is not a group member"""
        user_repo = get_user_repository(db_session)
        group_repo = get_group_repository(db_session)

        other_user = user_repo.create_user(name='Other', username='otheruser', password_hash='hash')
        group = group_repo.create_group(name='Other Group', created_by=other_user.id)
        group_repo.add_group_member(group.id, other_user, is_group_admin=False)

        service = RunService(db_session)
        with pytest.raises(ForbiddenError):
            service.create_run(str(group.id), str(store.id), user)

    @pytest.mark.asyncio
    async def test_get_run_details_success(self, db_session, user, group, store):
        """Test getting run details"""
        service = RunService(db_session)
        run_result = service.create_run(str(group.id), str(store.id), user)
        run_id = run_result.id

        details = service.get_run_details(run_id, user)

        assert details.id == run_id
        assert details.state == 'planning'
        assert details.store_name is not None
        assert details.participants is not None

    def test_get_run_details_invalid_id(self, db_session, user):
        """Test getting run with invalid ID format"""
        service = RunService(db_session)
        with pytest.raises(BadRequestError):
            service.get_run_details('not-a-uuid', user)

    @pytest.mark.asyncio
    async def test_place_bid_success(self, db_session, user, group, store, product):
        """Test placing a bid"""
        service = RunService(db_session)
        run_result = service.create_run(str(group.id), str(store.id), user)
        run_id = run_result.id

        bid_result = service.place_bid(
            run_id=run_id, product_id=str(product.id), quantity=5, interested_only=False, user=user
        )

        assert bid_result.quantity == 5
        assert bid_result.interested_only is False

    @pytest.mark.asyncio
    async def test_place_bid_negative_quantity(self, db_session, user, group, store, product):
        """Test placing bid with negative quantity"""
        service = RunService(db_session)
        run_result = service.create_run(str(group.id), str(store.id), user)

        with pytest.raises(BadRequestError):
            service.place_bid(
                run_id=run_result.id,
                product_id=str(product.id),
                quantity=-5,
                interested_only=False,
                user=user,
            )


# =============================================================================
# TestGroupService
# =============================================================================


class TestGroupService:
    """Tests for GroupService"""

    @pytest.mark.asyncio
    async def test_create_group_success(self, db_session, user):
        """Test successful group creation"""
        service = GroupService(db_session)
        result = service.create_group('New Group', user)

        assert result.name == 'New Group'
        assert result.id is not None
        assert result.member_count == 1

    def test_get_user_groups(self, db_session, user, group):
        """Test getting user's groups"""
        service = GroupService(db_session)
        groups = service.get_user_groups(user)

        assert len(groups) >= 1
        assert any(g.id == str(group.id) for g in groups)

    def test_get_group_details(self, db_session, user, group):
        """Test getting group details"""
        service = GroupService(db_session)
        details = service.get_group_details(str(group.id), user)

        assert details.id == str(group.id)
        assert details.name == group.name
        assert details.invite_token is not None

    def test_get_group_details_not_member(self, db_session, user):
        """Test getting group details when not a member"""
        user_repo = get_user_repository(db_session)
        group_repo = get_group_repository(db_session)

        other_user = user_repo.create_user(name='Other', username='otheruser', password_hash='hash')
        other_group = group_repo.create_group(name='Other Group', created_by=other_user.id)
        group_repo.add_group_member(other_group.id, other_user, is_group_admin=False)

        service = GroupService(db_session)
        with pytest.raises(ForbiddenError):
            service.get_group_details(str(other_group.id), user)

    @pytest.mark.asyncio
    async def test_regenerate_invite_token(self, db_session, user, group):
        """Test regenerating invite token"""
        service = GroupService(db_session)
        original_token = group.invite_token

        result = service.regenerate_invite_token(str(group.id), user)

        assert result.invite_token != original_token
        assert len(result.invite_token) > 0

    @pytest.mark.asyncio
    async def test_join_group_by_token_success(self, db_session, user, group):
        """Test joining group by invite token"""
        user_repo = get_user_repository(db_session)
        new_user = user_repo.create_user(name='New User', username='newuser', password_hash='hash')

        service = GroupService(db_session)
        result = service.join_group(group.invite_token, new_user)

        assert result.group_id == str(group.id)
        assert result.group_name == 'Test Group'
        assert result.success is True

    def test_join_group_invalid_token(self, db_session, user):
        """Test joining group with invalid token"""
        service = GroupService(db_session)
        with pytest.raises(NotFoundError):
            service.join_group('invalid-token', user)

    @pytest.mark.asyncio
    async def test_join_group_already_member(self, db_session, user, group):
        """Test joining group when already a member"""
        service = GroupService(db_session)
        with pytest.raises(BadRequestError):
            service.join_group(group.invite_token, user)


# =============================================================================
# TestProductService
# =============================================================================


class TestProductService:
    """Tests for ProductService"""

    def test_create_product_success(self, db_session, store):
        """Test successful product creation with store availability"""
        service = ProductService(db_session)
        product, availability = service.create_product(
            name='New Product', brand='Test Brand', store_id=store.id, price=29.99
        )

        assert product.name == 'New Product'
        assert product.brand == 'Test Brand'
        assert availability is not None
        assert float(availability.price) == 29.99

    def test_create_product_negative_price(self, db_session, store):
        """Test product creation with negative price"""
        service = ProductService(db_session)
        with pytest.raises(ValidationError):
            service.create_product(name='Product', store_id=store.id, price=-10.00)

    def test_create_product_zero_price(self, db_session, store):
        """Test product creation with zero price"""
        service = ProductService(db_session)
        with pytest.raises(ValidationError):
            service.create_product(name='Product', store_id=store.id, price=0.00)

    def test_search_products(self, db_session, store):
        """Test product search"""
        service = ProductService(db_session)
        # Create some products (returns tuple, so unpack)
        product1, _ = service.create_product(name='Olive Oil', store_id=store.id, price=15.99)
        product2, _ = service.create_product(name='Coconut Oil', store_id=store.id, price=12.99)
        product3, _ = service.create_product(name='Butter', store_id=store.id, price=8.99)

        results = service.search_products('oil')

        # search_products returns list of ProductSearchResult objects
        assert len(results) >= 2
        names = [p.name for p in results]
        assert 'Olive Oil' in names
        assert 'Coconut Oil' in names

    def test_get_product_details(self, db_session, product):
        """Test getting product details"""
        service = ProductService(db_session)
        details = service.get_product_details(product.id)

        # get_product_details returns ProductDetailResponse (Pydantic model)
        assert details.id == str(product.id)
        assert details.name == product.name


# =============================================================================
# TestStoreService
# =============================================================================


class TestStoreService:
    """Tests for StoreService"""

    def test_get_all_stores(self, db_session):
        """Test getting all stores"""
        service = StoreService(db_session)
        # Create a store within the test
        service.create_store('Test Store for Get All')

        stores = service.get_all_stores()

        # Should return a list of stores (there are seed stores in the DB)
        assert len(stores) >= 1
        assert all(hasattr(s, 'id') and hasattr(s, 'name') for s in stores)

    def test_create_store(self, db_session):
        """Test creating a store"""
        service = StoreService(db_session)
        result = service.create_store('New Store')

        assert result.name == 'New Store'
        assert result.id is not None

    def test_create_store_empty_name(self, db_session):
        """Test creating store with empty name"""
        service = StoreService(db_session)
        with pytest.raises(ValidationError):
            service.create_store('')
