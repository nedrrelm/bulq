"""
Tests for service layer business logic.
"""
import pytest
from app.services.run_service import RunService
from app.services.group_service import GroupService
from app.services.product_service import ProductService
from app.services.store_service import StoreService
from app.services.shopping_service import ShoppingService
from app.services.distribution_service import DistributionService
from app.exceptions import NotFoundError, ForbiddenError, ValidationError, BadRequestError
from app.repository import MemoryRepository


@pytest.fixture
def repo():
    """Create fresh in-memory repository"""
    return MemoryRepository()


@pytest.fixture
def user(repo):
    """Create a test user"""
    return repo.create_user(name="Test User", email="test@example.com", password_hash="hash")


@pytest.fixture
def group(repo, user):
    """Create a test group"""
    group = repo.create_group(name="Test Group", created_by=user.id)
    repo.add_user_to_group(user.id, group.id)
    return group


@pytest.fixture
def store(repo):
    """Create a test store"""
    return repo.create_store(name="Test Store")


@pytest.fixture
def product(repo, store):
    """Create a test product"""
    return repo.create_product(store_id=store.id, name="Test Product", base_price=19.99)


class TestRunService:
    """Tests for RunService"""

    def test_create_run_success(self, repo, user, group, store):
        """Test successful run creation"""
        service = RunService(repo)
        result = service.create_run(str(group.id), str(store.id), user)

        assert result["group_id"] == str(group.id)
        assert result["store_id"] == str(store.id)
        assert result["state"] == "planning"
        assert "id" in result

    def test_create_run_invalid_group_id(self, repo, user, store):
        """Test run creation with invalid group ID format"""
        service = RunService(repo)
        with pytest.raises(BadRequestError):
            service.create_run("not-a-uuid", str(store.id), user)

    def test_create_run_nonexistent_group(self, repo, user, store):
        """Test run creation with non-existent group"""
        service = RunService(repo)
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        with pytest.raises(NotFoundError) as exc:
            service.create_run(fake_uuid, str(store.id), user)
        assert "Group" in str(exc.value)

    def test_create_run_user_not_member(self, repo, user, store):
        """Test run creation when user is not a group member"""
        other_user = repo.create_user(name="Other", email="other@example.com", password_hash="hash")
        group = repo.create_group(name="Other Group", created_by=other_user.id)
        repo.add_user_to_group(other_user.id, group.id)

        service = RunService(repo)
        with pytest.raises(ForbiddenError):
            service.create_run(str(group.id), str(store.id), user)

    def test_get_run_details_success(self, repo, user, group, store):
        """Test getting run details"""
        service = RunService(repo)
        run_result = service.create_run(str(group.id), str(store.id), user)
        run_id = run_result["id"]

        details = service.get_run_details(run_id, user)

        assert details["id"] == run_id
        assert details["state"] == "planning"
        assert "store" in details
        assert "participants" in details

    def test_get_run_details_invalid_id(self, repo, user):
        """Test getting run with invalid ID format"""
        service = RunService(repo)
        with pytest.raises(BadRequestError):
            service.get_run_details("not-a-uuid", user)

    def test_place_bid_success(self, repo, user, group, store, product):
        """Test placing a bid"""
        service = RunService(repo)
        run_result = service.create_run(str(group.id), str(store.id), user)
        run_id = run_result["id"]

        bid_result = service.place_bid(
            run_id=run_id,
            product_id=str(product.id),
            quantity=5,
            interested_only=False,
            user=user
        )

        assert bid_result["quantity"] == 5
        assert bid_result["interested_only"] is False

    def test_place_bid_negative_quantity(self, repo, user, group, store, product):
        """Test placing bid with negative quantity"""
        service = RunService(repo)
        run_result = service.create_run(str(group.id), str(store.id), user)

        with pytest.raises(ValidationError):
            service.place_bid(
                run_id=run_result["id"],
                product_id=str(product.id),
                quantity=-5,
                interested_only=False,
                user=user
            )

    def test_retract_bid_success(self, repo, user, group, store, product):
        """Test retracting a bid"""
        service = RunService(repo)
        run_result = service.create_run(str(group.id), str(store.id), user)
        run_id = run_result["id"]

        # Place bid
        service.place_bid(run_id, str(product.id), quantity=5, interested_only=False, user=user)

        # Retract bid
        result = service.retract_bid(run_id, str(product.id), user)
        assert result["success"] is True

    def test_toggle_ready_success(self, repo, user, group, store):
        """Test toggling ready status"""
        service = RunService(repo)
        run_result = service.create_run(str(group.id), str(store.id), user)

        # Toggle to ready
        result = service.toggle_ready(run_result["id"], user)
        assert result["is_ready"] is True

        # Toggle back to not ready
        result = service.toggle_ready(run_result["id"], user)
        assert result["is_ready"] is False


class TestGroupService:
    """Tests for GroupService"""

    def test_create_group_success(self, repo, user):
        """Test successful group creation"""
        service = GroupService(repo)
        result = service.create_group("New Group", user)

        assert result["name"] == "New Group"
        assert result["created_by"] == str(user.id)
        assert "invite_token" in result
        assert "id" in result

    def test_create_group_empty_name(self, repo, user):
        """Test group creation with empty name"""
        service = GroupService(repo)
        with pytest.raises(ValidationError):
            service.create_group("", user)

    def test_get_user_groups(self, repo, user, group):
        """Test getting user's groups"""
        service = GroupService(repo)
        groups = service.get_user_groups(user)

        assert len(groups) >= 1
        assert any(g["id"] == str(group.id) for g in groups)

    def test_get_group_details(self, repo, user, group):
        """Test getting group details"""
        service = GroupService(repo)
        details = service.get_group_details(str(group.id), user)

        assert details["id"] == str(group.id)
        assert details["name"] == group.name
        assert "members" in details
        assert "runs" in details

    def test_get_group_details_not_member(self, repo, user):
        """Test getting group details when not a member"""
        other_user = repo.create_user(name="Other", email="other@example.com", password_hash="hash")
        other_group = repo.create_group(name="Other Group", created_by=other_user.id)
        repo.add_user_to_group(other_user.id, other_group.id)

        service = GroupService(repo)
        with pytest.raises(ForbiddenError):
            service.get_group_details(str(other_group.id), user)

    def test_regenerate_invite_token(self, repo, user, group):
        """Test regenerating invite token"""
        service = GroupService(repo)
        original_token = group.invite_token

        result = service.regenerate_invite_token(str(group.id), user)

        assert result["invite_token"] != original_token
        assert len(result["invite_token"]) > 0

    def test_join_group_by_token_success(self, repo, user, group):
        """Test joining group by invite token"""
        new_user = repo.create_user(name="New User", email="new@example.com", password_hash="hash")
        service = GroupService(repo)

        result = service.join_group_by_token(group.invite_token, new_user)

        assert result["group_id"] == str(group.id)
        assert result["user_id"] == str(new_user.id)

    def test_join_group_invalid_token(self, repo, user):
        """Test joining group with invalid token"""
        service = GroupService(repo)
        with pytest.raises(NotFoundError):
            service.join_group_by_token("invalid-token", user)

    def test_join_group_already_member(self, repo, user, group):
        """Test joining group when already a member"""
        service = GroupService(repo)
        with pytest.raises(ValidationError):
            service.join_group_by_token(group.invite_token, user)


class TestProductService:
    """Tests for ProductService"""

    def test_create_product_success(self, repo, store):
        """Test successful product creation"""
        service = ProductService(repo)
        result = service.create_product(
            store_id=str(store.id),
            name="New Product",
            base_price=29.99
        )

        assert result["name"] == "New Product"
        assert result["base_price"] == 29.99
        assert result["store_id"] == str(store.id)

    def test_create_product_negative_price(self, repo, store):
        """Test product creation with negative price"""
        service = ProductService(repo)
        with pytest.raises(ValidationError):
            service.create_product(
                store_id=str(store.id),
                name="Product",
                base_price=-10.00
            )

    def test_create_product_zero_price(self, repo, store):
        """Test product creation with zero price"""
        service = ProductService(repo)
        with pytest.raises(ValidationError):
            service.create_product(
                store_id=str(store.id),
                name="Product",
                base_price=0.00
            )

    def test_search_products(self, repo, store):
        """Test product search"""
        service = ProductService(repo)
        # Create some products
        service.create_product(store.id, "Olive Oil", 15.99)
        service.create_product(store.id, "Coconut Oil", 12.99)
        service.create_product(store.id, "Butter", 8.99)

        results = service.search_products("oil")

        assert len(results) == 2
        names = [p["name"] for p in results]
        assert "Olive Oil" in names
        assert "Coconut Oil" in names

    def test_get_product_details(self, repo, product):
        """Test getting product details"""
        service = ProductService(repo)
        details = service.get_product_details(str(product.id))

        assert details["id"] == str(product.id)
        assert details["name"] == product.name
        assert details["base_price"] == float(product.base_price)


class TestStoreService:
    """Tests for StoreService"""

    def test_get_all_stores(self, repo, store):
        """Test getting all stores"""
        service = StoreService(repo)
        stores = service.get_all_stores()

        assert len(stores) >= 1
        assert any(s["id"] == str(store.id) for s in stores)

    def test_create_store(self, repo):
        """Test creating a store"""
        service = StoreService(repo)
        result = service.create_store("New Store")

        assert result["name"] == "New Store"
        assert "id" in result

    def test_create_store_empty_name(self, repo):
        """Test creating store with empty name"""
        service = StoreService(repo)
        with pytest.raises(ValidationError):
            service.create_store("")


class TestShoppingService:
    """Tests for ShoppingService"""

    def test_get_shopping_list(self, repo, user, group, store, product):
        """Test getting shopping list"""
        # Create run and place bids
        run = repo.create_run(group.id, store.id, user.id)
        participation = repo.create_participation(user.id, run.id, is_leader=True)
        repo.create_or_update_bid(participation.id, product.id, quantity=5, interested_only=False)

        # Generate shopping list
        repo.create_shopping_list_item(run.id, product.id, requested_quantity=5)

        service = ShoppingService(repo)
        shopping_list = service.get_shopping_list(str(run.id), user)

        assert len(shopping_list) >= 1
        assert shopping_list[0]["product_id"] == str(product.id)
        assert shopping_list[0]["requested_quantity"] == 5

    def test_log_encountered_price(self, repo, user, group, store, product):
        """Test logging encountered price"""
        run = repo.create_run(group.id, store.id, user.id)
        repo.create_participation(user.id, run.id, is_leader=True)
        item = repo.create_shopping_list_item(run.id, product.id, requested_quantity=5)

        service = ShoppingService(repo)
        result = service.log_encountered_price(
            item_id=str(item.id),
            price=18.99,
            notes="On sale",
            user=user
        )

        assert result["success"] is True

    def test_mark_item_purchased(self, repo, user, group, store, product):
        """Test marking item as purchased"""
        run = repo.create_run(group.id, store.id, user.id)
        repo.create_participation(user.id, run.id, is_leader=True)
        item = repo.create_shopping_list_item(run.id, product.id, requested_quantity=5)

        service = ShoppingService(repo)
        result = service.mark_item_purchased(
            item_id=str(item.id),
            purchased_quantity=5,
            purchased_price_per_unit=18.99,
            purchased_total=94.95,
            purchase_order=1,
            user=user
        )

        assert result["is_purchased"] is True
        assert result["purchased_quantity"] == 5


class TestDistributionService:
    """Tests for DistributionService"""

    def test_get_distribution_data(self, repo, user, group, store, product):
        """Test getting distribution data"""
        # Setup run with purchases
        run = repo.create_run(group.id, store.id, user.id)
        repo.update_run_state(run.id, "distributing")
        participation = repo.create_participation(user.id, run.id, is_leader=True)
        bid = repo.create_or_update_bid(participation.id, product.id, quantity=5, interested_only=False)

        service = DistributionService(repo)
        data = service.get_distribution_data(str(run.id), user)

        assert "participants" in data
        assert "products" in data

    def test_toggle_pickup_status(self, repo, user, group, store, product):
        """Test toggling pickup status"""
        run = repo.create_run(group.id, store.id, user.id)
        repo.update_run_state(run.id, "distributing")
        participation = repo.create_participation(user.id, run.id, is_leader=True)
        bid = repo.create_or_update_bid(participation.id, product.id, quantity=5, interested_only=False)

        service = DistributionService(repo)
        result = service.toggle_pickup_status(
            run_id=str(run.id),
            participation_id=str(participation.id),
            product_id=str(product.id),
            user=user
        )

        assert "is_picked_up" in result
