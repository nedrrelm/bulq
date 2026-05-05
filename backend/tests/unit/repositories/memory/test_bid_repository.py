"""Unit tests for MemoryBidRepository.

Tests cover:
- Bid creation (create_or_update_bid)
- Bid retrieval by ID (get_bid_by_id)
- Bid retrieval by participation and product (get_bid)
- Bid updates (quantity, interested_only, comment)
- Bid deletion (delete_bid)
- Get bids by run (get_bids_by_run, get_bids_by_run_with_participations)
- Get bids by participation (get_bids_by_participation)
- Distribution tracking (update_bid_distributed_quantities)
- UUID generation and default values
- Edge cases and data integrity
"""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.repositories.memory.bid import MemoryBidRepository
from app.repositories.memory.group import MemoryGroupRepository
from app.repositories.memory.product import MemoryProductRepository
from app.repositories.memory.run import MemoryRunRepository
from app.repositories.memory.storage import MemoryStorage
from app.repositories.memory.store import MemoryStoreRepository
from app.repositories.memory.user import MemoryUserRepository


@pytest.fixture
def storage():
    """Create fresh memory storage for each test."""
    storage = MemoryStorage()
    # Clear all data
    storage.users.clear()
    storage.users_by_username.clear()
    storage.groups.clear()
    storage.group_memberships.clear()
    storage.group_admin_status.clear()
    storage.stores.clear()
    storage.runs.clear()
    storage.participations.clear()
    storage.bids.clear()
    storage.products.clear()
    storage.shopping_list_items.clear()
    yield storage
    # Clean up after test
    storage.users.clear()
    storage.users_by_username.clear()
    storage.groups.clear()
    storage.group_memberships.clear()
    storage.group_admin_status.clear()
    storage.stores.clear()
    storage.runs.clear()
    storage.participations.clear()
    storage.bids.clear()
    storage.products.clear()
    storage.shopping_list_items.clear()


@pytest.fixture
def repo(storage):
    """Create bid repository instance with fresh storage."""
    return MemoryBidRepository(storage)


@pytest.fixture
def user_repo(storage):
    """Create user repository instance with fresh storage."""
    return MemoryUserRepository(storage)


@pytest.fixture
def group_repo(storage):
    """Create group repository instance with fresh storage."""
    return MemoryGroupRepository(storage)


@pytest.fixture
def store_repo(storage):
    """Create store repository instance with fresh storage."""
    return MemoryStoreRepository(storage)


@pytest.fixture
def run_repo(storage):
    """Create run repository instance with fresh storage."""
    return MemoryRunRepository(storage)


@pytest.fixture
def product_repo(storage):
    """Create product repository instance with fresh storage."""
    return MemoryProductRepository(storage)


@pytest.fixture
async def sample_user(user_repo):
    """Create a sample user for testing."""
    return await user_repo.create_user('Test User', 'testuser', 'hashed_password')


@pytest.fixture
async def sample_users(user_repo):
    """Create multiple sample users for testing."""
    return [await user_repo.create_user(f'User {i}', f'user{i}', f'hash{i}') for i in range(1, 5)]


@pytest.fixture
async def sample_group(group_repo, sample_user):
    """Create a sample group for testing."""
    return await group_repo.create_group('Test Group', sample_user.id)


@pytest.fixture
async def sample_store(store_repo):
    """Create a sample store for testing."""
    return await store_repo.create_store('Test Store')


@pytest.fixture
async def sample_run(run_repo, sample_group, sample_store, sample_user):
    """Create a sample run for testing."""
    return await run_repo.create_run(sample_group.id, sample_store.id, sample_user.id)


@pytest.fixture
async def sample_product(product_repo):
    """Create a sample product for testing."""
    return await product_repo.create_product('Test Product', brand='Test Brand', unit='kg')


@pytest.fixture
async def sample_products(product_repo):
    """Create multiple sample products for testing."""
    return [
        await product_repo.create_product(f'Product {i}', brand=f'Brand {i}', unit='kg')
        for i in range(1, 5)
    ]


@pytest.fixture
async def sample_participation(run_repo, sample_run, sample_users):
    """Create a sample participation for testing."""
    return await run_repo.create_participation(sample_users[0].id, sample_run.id)


class TestCreateOrUpdateBid:
    """Test create_or_update_bid() method."""

    async def test_create_bid_with_required_fields(
        self, repo, sample_participation, sample_product
    ):
        """Test creating bid with all required fields."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        assert bid is not None
        assert bid.participation_id == sample_participation.id
        assert bid.product_id == sample_product.id
        assert bid.quantity == 10
        assert bid.interested_only is False

    async def test_create_bid_with_interested_only_flag(
        self, repo, sample_participation, sample_product
    ):
        """Test creating bid with interested_only flag."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=0,
            interested_only=True,
        )

        assert bid.interested_only is True
        assert bid.quantity == 0

    async def test_created_bid_has_uuid(self, repo, sample_participation, sample_product):
        """Test created bid has correct ID (UUID)."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=5,
            interested_only=False,
        )

        assert bid.id is not None
        assert isinstance(bid.id, UUID)

    async def test_default_distributed_quantity_is_none(
        self, repo, sample_participation, sample_product
    ):
        """Test default distributed_quantity is None."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        assert bid.distributed_quantity is None
        assert bid.distributed_price_per_unit is None

    async def test_default_picked_up_at_is_none(self, repo, sample_participation, sample_product):
        """Test default picked_up_at is None."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        assert hasattr(bid, 'is_picked_up')
        assert hasattr(bid, 'picked_up_at')
        assert bid.picked_up_at is None

    async def test_timestamps_are_set(self, repo, sample_participation, sample_product):
        """Test created_at and updated_at timestamps are set."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        assert bid.created_at is not None
        assert bid.updated_at is not None

    async def test_create_with_comment(self, repo, sample_participation, sample_product):
        """Test creating bid with optional comment."""
        comment = 'Need this urgently'
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
            comment=comment,
        )

        assert bid.comment == comment

    async def test_create_multiple_bids_for_same_participation(
        self, repo, sample_participation, sample_products
    ):
        """Test creating multiple bids for the same participation."""
        bids = []
        for product in sample_products[:3]:
            bid = await repo.create_or_update_bid(
                participation_id=sample_participation.id,
                product_id=product.id,
                quantity=5,
                interested_only=False,
            )
            bids.append(bid)

        # All bids should have unique IDs
        bid_ids = [b.id for b in bids]
        assert len(bid_ids) == len(set(bid_ids))

        # All bids should be for same participation
        for bid in bids:
            assert bid.participation_id == sample_participation.id

    async def test_update_existing_bid_quantity(self, repo, sample_participation, sample_product):
        """Test updating existing bid quantity."""
        # Create bid
        bid1 = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        # Update bid
        bid2 = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=20,
            interested_only=False,
        )

        # Should be same bid with updated quantity
        assert bid1.id == bid2.id
        assert bid2.quantity == 20

    async def test_update_existing_bid_interested_only(
        self, repo, sample_participation, sample_product
    ):
        """Test updating existing bid interested_only flag."""
        # Create bid
        await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        # Update to interested only
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=0,
            interested_only=True,
        )

        assert bid.interested_only is True
        assert bid.quantity == 0

    async def test_update_existing_bid_comment(self, repo, sample_participation, sample_product):
        """Test updating existing bid comment."""
        # Create bid
        await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
            comment='Initial comment',
        )

        # Update comment
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
            comment='Updated comment',
        )

        assert bid.comment == 'Updated comment'

    async def test_updated_at_timestamp_changes_on_update(
        self, repo, sample_participation, sample_product
    ):
        """Test updated_at timestamp changes on update."""
        bid1 = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        original_updated_at = bid1.updated_at

        # Update bid
        bid2 = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=20,
            interested_only=False,
        )

        assert bid2.updated_at >= original_updated_at

    async def test_bid_includes_participation_relationship(
        self, repo, sample_participation, sample_product
    ):
        """Test bid includes participation relationship."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        assert bid.participation is not None
        assert bid.participation.id == sample_participation.id

    async def test_bid_includes_product_relationship(
        self, repo, sample_participation, sample_product
    ):
        """Test bid includes product relationship."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        assert bid.product is not None
        assert bid.product.id == sample_product.id


class TestGetBidById:
    """Test get_bid_by_id() method."""

    async def test_get_existing_bid(self, repo, sample_participation, sample_product):
        """Test getting existing bid by ID."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        retrieved = await repo.get_bid_by_id(bid.id)

        assert retrieved is not None
        assert retrieved.id == bid.id
        assert retrieved.participation_id == bid.participation_id
        assert retrieved.product_id == bid.product_id
        assert retrieved.quantity == bid.quantity

    async def test_get_nonexistent_bid_returns_none(self, repo):
        """Test getting non-existent bid returns None."""
        fake_id = uuid4()

        result = await repo.get_bid_by_id(fake_id)

        assert result is None

    async def test_get_bid_with_invalid_uuid(self, repo):
        """Test getting bid with None ID."""
        result = await repo.get_bid_by_id(None)

        assert result is None


class TestGetBid:
    """Test get_bid() method."""

    async def test_get_existing_bid_by_participation_and_product(
        self, repo, sample_participation, sample_product
    ):
        """Test getting existing bid by participation and product."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        retrieved = await repo.get_bid(sample_participation.id, sample_product.id)

        assert retrieved is not None
        assert retrieved.id == bid.id
        assert retrieved.participation_id == sample_participation.id
        assert retrieved.product_id == sample_product.id

    async def test_get_nonexistent_bid_returns_none(
        self, repo, sample_participation, sample_product
    ):
        """Test getting non-existent bid returns None."""
        result = await repo.get_bid(sample_participation.id, sample_product.id)

        assert result is None

    async def test_get_bid_includes_relationships(self, repo, sample_participation, sample_product):
        """Test get_bid includes participation and product relationships."""
        await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        bid = await repo.get_bid(sample_participation.id, sample_product.id)

        assert bid.participation is not None
        assert bid.participation.id == sample_participation.id
        assert bid.product is not None
        assert bid.product.id == sample_product.id


class TestDeleteBid:
    """Test delete_bid() method."""

    async def test_delete_existing_bid(self, repo, sample_participation, sample_product):
        """Test deleting existing bid."""
        await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        result = await repo.delete_bid(sample_participation.id, sample_product.id)

        assert result is True

    async def test_bid_not_retrievable_after_deletion(
        self, repo, sample_participation, sample_product
    ):
        """Test bid is not retrievable after deletion."""
        await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        await repo.delete_bid(sample_participation.id, sample_product.id)

        bid = await repo.get_bid(sample_participation.id, sample_product.id)
        assert bid is None

    async def test_delete_nonexistent_bid_returns_false(
        self, repo, sample_participation, sample_product
    ):
        """Test deleting non-existent bid returns False."""
        result = await repo.delete_bid(sample_participation.id, sample_product.id)

        assert result is False

    async def test_delete_bid_multiple_times(self, repo, sample_participation, sample_product):
        """Test deleting bid multiple times."""
        await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        # First deletion succeeds
        result1 = await repo.delete_bid(sample_participation.id, sample_product.id)
        assert result1 is True

        # Second deletion returns False
        result2 = await repo.delete_bid(sample_participation.id, sample_product.id)
        assert result2 is False

    async def test_delete_one_bid_does_not_affect_others(
        self, repo, sample_participation, sample_products
    ):
        """Test deleting one bid does not affect others."""
        # Create multiple bids
        for product in sample_products[:3]:
            await repo.create_or_update_bid(
                participation_id=sample_participation.id,
                product_id=product.id,
                quantity=10,
                interested_only=False,
            )

        # Delete one bid
        await repo.delete_bid(sample_participation.id, sample_products[0].id)

        # Other bids should still exist
        bid2 = await repo.get_bid(sample_participation.id, sample_products[1].id)
        bid3 = await repo.get_bid(sample_participation.id, sample_products[2].id)

        assert bid2 is not None
        assert bid3 is not None


class TestGetBidsByRun:
    """Test get_bids_by_run() method."""

    async def test_get_all_bids_for_run(
        self, repo, run_repo, sample_run, sample_users, sample_product, sample_user
    ):
        """Test getting all bids for a run."""
        # Create participations and bids
        participations = []
        for user in sample_users[:3]:
            participation = await run_repo.create_participation(user.id, sample_run.id)
            participations.append(participation)
            await repo.create_or_update_bid(
                participation_id=participation.id,
                product_id=sample_product.id,
                quantity=5,
                interested_only=False,
            )

        bids = await repo.get_bids_by_run(sample_run.id)

        # Should include bids from all 3 participations
        assert len(bids) == 3

    async def test_empty_list_for_run_with_no_bids(self, repo, sample_run):
        """Test empty list for run with no bids."""
        bids = await repo.get_bids_by_run(sample_run.id)

        # Only leader participation exists, but no bids
        assert bids == []
        assert len(bids) == 0

    async def test_multiple_bids_per_participation(
        self, repo, run_repo, sample_run, sample_users, sample_products
    ):
        """Test multiple bids per participation."""
        participation = await run_repo.create_participation(sample_users[0].id, sample_run.id)

        # Create multiple bids for same participation
        for product in sample_products[:3]:
            await repo.create_or_update_bid(
                participation_id=participation.id,
                product_id=product.id,
                quantity=5,
                interested_only=False,
            )

        bids = await repo.get_bids_by_run(sample_run.id)

        assert len(bids) == 3

    async def test_bids_include_all_fields(
        self, repo, run_repo, sample_run, sample_users, sample_product
    ):
        """Test bids include all fields."""
        participation = await run_repo.create_participation(sample_users[0].id, sample_run.id)
        await repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
            comment='Test comment',
        )

        bids = await repo.get_bids_by_run(sample_run.id)

        assert len(bids) == 1
        bid = bids[0]
        assert bid.participation_id == participation.id
        assert bid.product_id == sample_product.id
        assert bid.quantity == 10
        assert bid.interested_only is False
        assert bid.comment == 'Test comment'

    async def test_only_returns_bids_for_specific_run(
        self,
        repo,
        run_repo,
        group_repo,
        store_repo,
        sample_user,
        sample_users,
        sample_product,
        sample_store,
    ):
        """Test only returns bids for specific run."""
        # Create two groups and two runs
        group1 = await group_repo.create_group('Group 1', sample_user.id)
        group2 = await group_repo.create_group('Group 2', sample_user.id)

        run1 = await run_repo.create_run(group1.id, sample_store.id, sample_user.id)
        run2 = await run_repo.create_run(group2.id, sample_store.id, sample_user.id)

        # Create bid for run1
        participation1 = await run_repo.create_participation(sample_users[0].id, run1.id)
        await repo.create_or_update_bid(
            participation_id=participation1.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        # Create bid for run2
        participation2 = await run_repo.create_participation(sample_users[1].id, run2.id)
        await repo.create_or_update_bid(
            participation_id=participation2.id,
            product_id=sample_product.id,
            quantity=20,
            interested_only=False,
        )

        bids_run1 = await repo.get_bids_by_run(run1.id)
        bids_run2 = await repo.get_bids_by_run(run2.id)

        assert len(bids_run1) == 1
        assert len(bids_run2) == 1
        assert bids_run1[0].quantity == 10
        assert bids_run2[0].quantity == 20

    async def test_get_bids_after_deletion(
        self, repo, run_repo, sample_run, sample_users, sample_products
    ):
        """Test get_bids_by_run after deleting a bid."""
        participation = await run_repo.create_participation(sample_users[0].id, sample_run.id)

        # Create multiple bids
        for product in sample_products[:3]:
            await repo.create_or_update_bid(
                participation_id=participation.id,
                product_id=product.id,
                quantity=5,
                interested_only=False,
            )

        # Delete one bid
        await repo.delete_bid(participation.id, sample_products[0].id)

        bids = await repo.get_bids_by_run(sample_run.id)

        # Should only have 2 bids left
        assert len(bids) == 2


class TestGetBidsByRunWithParticipations:
    """Test get_bids_by_run_with_participations() method."""

    async def test_get_bids_with_participations_eagerly_loaded(
        self, repo, run_repo, sample_run, sample_users, sample_product
    ):
        """Test getting bids with participations eagerly loaded."""
        # Create participations and bids
        for user in sample_users[:3]:
            participation = await run_repo.create_participation(user.id, sample_run.id)
            await repo.create_or_update_bid(
                participation_id=participation.id,
                product_id=sample_product.id,
                quantity=5,
                interested_only=False,
            )

        bids = await repo.get_bids_by_run_with_participations(sample_run.id)

        assert len(bids) == 3
        for bid in bids:
            assert bid.participation is not None
            assert bid.participation.user is not None
            assert bid.participation.run is not None

    async def test_participations_include_users(
        self, repo, run_repo, sample_run, sample_users, sample_product
    ):
        """Test participations include users."""
        participation = await run_repo.create_participation(sample_users[0].id, sample_run.id)
        await repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        bids = await repo.get_bids_by_run_with_participations(sample_run.id)

        assert len(bids) == 1
        bid = bids[0]
        assert bid.participation.user is not None
        assert bid.participation.user.id == sample_users[0].id

    async def test_empty_list_for_run_with_no_bids(self, repo, sample_run):
        """Test empty list for run with no bids."""
        bids = await repo.get_bids_by_run_with_participations(sample_run.id)

        assert bids == []


class TestGetBidsByParticipation:
    """Test get_bids_by_participation() method."""

    async def test_get_bids_for_participation(self, repo, sample_participation, sample_products):
        """Test getting all bids for a participation."""
        # Create multiple bids
        for product in sample_products[:3]:
            await repo.create_or_update_bid(
                participation_id=sample_participation.id,
                product_id=product.id,
                quantity=5,
                interested_only=False,
            )

        bids = await repo.get_bids_by_participation(sample_participation.id)

        assert len(bids) == 3
        for bid in bids:
            assert bid.participation_id == sample_participation.id

    async def test_empty_list_for_participation_with_no_bids(self, repo, sample_participation):
        """Test empty list for participation with no bids."""
        bids = await repo.get_bids_by_participation(sample_participation.id)

        assert bids == []
        assert len(bids) == 0

    async def test_multiple_bids_per_participation(
        self, repo, sample_participation, sample_products
    ):
        """Test multiple bids per participation."""
        # Create 4 bids
        for product in sample_products:
            await repo.create_or_update_bid(
                participation_id=sample_participation.id,
                product_id=product.id,
                quantity=10,
                interested_only=False,
            )

        bids = await repo.get_bids_by_participation(sample_participation.id)

        assert len(bids) == 4

    async def test_bids_include_product_details(self, repo, sample_participation, sample_products):
        """Test bids include product details."""
        for product in sample_products[:2]:
            await repo.create_or_update_bid(
                participation_id=sample_participation.id,
                product_id=product.id,
                quantity=5,
                interested_only=False,
            )

        bids = await repo.get_bids_by_participation(sample_participation.id)

        for bid in bids:
            assert bid.product is not None
            assert bid.product.name is not None

    async def test_get_bids_after_retraction(self, repo, sample_participation, sample_products):
        """Test get_bids_by_participation after retracting a bid."""
        # Create multiple bids
        for product in sample_products[:3]:
            await repo.create_or_update_bid(
                participation_id=sample_participation.id,
                product_id=product.id,
                quantity=5,
                interested_only=False,
            )

        # Delete (retract) one bid
        await repo.delete_bid(sample_participation.id, sample_products[0].id)

        bids = await repo.get_bids_by_participation(sample_participation.id)

        # Should only have 2 bids left
        assert len(bids) == 2


class TestUpdateBidDistributedQuantities:
    """Test update_bid_distributed_quantities() method."""

    async def test_update_distributed_quantity(self, repo, sample_participation, sample_product):
        """Test updating distributed quantity."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        await repo.update_bid_distributed_quantities(bid.id, 8.0, Decimal('2.50'))

        updated_bid = await repo.get_bid_by_id(bid.id)
        assert updated_bid.distributed_quantity == 8.0
        assert updated_bid.distributed_price_per_unit == Decimal('2.50')

    async def test_update_distributed_price_per_unit(
        self, repo, sample_participation, sample_product
    ):
        """Test updating distributed price per unit."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        price = Decimal('3.75')
        await repo.update_bid_distributed_quantities(bid.id, 10.0, price)

        updated_bid = await repo.get_bid_by_id(bid.id)
        assert updated_bid.distributed_price_per_unit == price

    async def test_update_both_distributed_fields(self, repo, sample_participation, sample_product):
        """Test updating both distributed quantity and price."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=20,
            interested_only=False,
        )

        quantity = 15.5
        price = Decimal('4.99')
        await repo.update_bid_distributed_quantities(bid.id, quantity, price)

        updated_bid = await repo.get_bid_by_id(bid.id)
        assert updated_bid.distributed_quantity == quantity
        assert updated_bid.distributed_price_per_unit == price

    async def test_update_distributed_quantities_for_nonexistent_bid(self, repo):
        """Test updating distributed quantities for non-existent bid."""
        fake_id = uuid4()

        # Should not raise error, just no-op
        await repo.update_bid_distributed_quantities(fake_id, 10.0, Decimal('2.50'))

    async def test_update_distributed_quantities_multiple_times(
        self, repo, sample_participation, sample_product
    ):
        """Test updating distributed quantities multiple times."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        # First update
        await repo.update_bid_distributed_quantities(bid.id, 8.0, Decimal('2.50'))
        bid1 = await repo.get_bid_by_id(bid.id)
        assert bid1.distributed_quantity == 8.0

        # Second update
        await repo.update_bid_distributed_quantities(bid.id, 9.0, Decimal('2.75'))
        bid2 = await repo.get_bid_by_id(bid.id)
        assert bid2.distributed_quantity == 9.0
        assert bid2.distributed_price_per_unit == Decimal('2.75')

    async def test_distributed_quantity_precision(self, repo, sample_participation, sample_product):
        """Test distributed quantity with decimal precision."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        await repo.update_bid_distributed_quantities(bid.id, 7.5, Decimal('3.33'))

        updated_bid = await repo.get_bid_by_id(bid.id)
        assert updated_bid.distributed_quantity == 7.5
        assert updated_bid.distributed_price_per_unit == Decimal('3.33')

    async def test_distribution_for_multiple_bids(
        self, repo, run_repo, sample_run, sample_users, sample_product
    ):
        """Test distribution for multiple bids."""
        # Create multiple bids
        bids = []
        for user in sample_users[:3]:
            participation = await run_repo.create_participation(user.id, sample_run.id)
            bid = await repo.create_or_update_bid(
                participation_id=participation.id,
                product_id=sample_product.id,
                quantity=10,
                interested_only=False,
            )
            bids.append(bid)

        # Update distribution for each bid
        for i, bid in enumerate(bids):
            quantity = 8.0 + i
            price = Decimal(f'{2.5 + i * 0.5:.2f}')
            await repo.update_bid_distributed_quantities(bid.id, quantity, price)

        # Verify each bid has correct distribution
        for i, bid in enumerate(bids):
            updated_bid = await repo.get_bid_by_id(bid.id)
            assert updated_bid.distributed_quantity == 8.0 + i
            assert updated_bid.distributed_price_per_unit == Decimal(f'{2.5 + i * 0.5:.2f}')

    async def test_zero_distributed_quantity(self, repo, sample_participation, sample_product):
        """Test setting distributed quantity to zero."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        await repo.update_bid_distributed_quantities(bid.id, 0.0, Decimal('0.00'))

        updated_bid = await repo.get_bid_by_id(bid.id)
        assert updated_bid.distributed_quantity == 0.0
        assert updated_bid.distributed_price_per_unit == Decimal('0.00')


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    async def test_very_large_quantity(self, repo, sample_participation, sample_product):
        """Test with very large quantity (e.g., 10000)."""
        large_quantity = 10000
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=large_quantity,
            interested_only=False,
        )

        assert bid.quantity == large_quantity
        retrieved = await repo.get_bid_by_id(bid.id)
        assert retrieved.quantity == large_quantity

    async def test_zero_quantity(self, repo, sample_participation, sample_product):
        """Test with zero quantity."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=0,
            interested_only=True,
        )

        assert bid.quantity == 0

    async def test_interested_only_with_zero_quantity(
        self, repo, sample_participation, sample_product
    ):
        """Test interested_only bids with zero quantity."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=0,
            interested_only=True,
        )

        assert bid.quantity == 0
        assert bid.interested_only is True

    async def test_concurrent_bid_operations(self, repo, sample_participation, sample_products):
        """Test creating multiple bids (simulating concurrent operations)."""
        bids = []
        for product in sample_products:
            bid = await repo.create_or_update_bid(
                participation_id=sample_participation.id,
                product_id=product.id,
                quantity=5,
                interested_only=False,
            )
            bids.append(bid)

        # Verify all bids exist
        retrieved_bids = await repo.get_bids_by_participation(sample_participation.id)
        assert len(retrieved_bids) == len(sample_products)

        # Verify all IDs are unique
        bid_ids = [b.id for b in retrieved_bids]
        assert len(bid_ids) == len(set(bid_ids))

    async def test_repository_isolation(self, storage):
        """Test fresh repository instance per test (via fixture)."""
        # This test verifies the fixture works correctly
        assert len(storage.bids) == 0

    async def test_unicode_in_comment(self, repo, sample_participation, sample_product):
        """Test with unicode characters in comment."""
        unicode_comment = '需要这个产品 🛒 Need this product!'
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
            comment=unicode_comment,
        )

        assert bid.comment == unicode_comment
        retrieved = await repo.get_bid_by_id(bid.id)
        assert retrieved.comment == unicode_comment

    async def test_very_long_comment(self, repo, sample_participation, sample_product):
        """Test with very long comment (1000+ chars)."""
        long_comment = 'a' * 1500
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
            comment=long_comment,
        )

        assert bid.comment == long_comment


class TestDataIntegrity:
    """Test data integrity and relationships."""

    async def test_bid_object_has_expected_fields(self, repo, sample_participation, sample_product):
        """Test bid object has expected fields."""
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        assert hasattr(bid, 'id')
        assert hasattr(bid, 'participation_id')
        assert hasattr(bid, 'product_id')
        assert hasattr(bid, 'quantity')
        assert hasattr(bid, 'interested_only')
        assert hasattr(bid, 'comment')
        assert hasattr(bid, 'distributed_quantity')
        assert hasattr(bid, 'distributed_price_per_unit')
        assert hasattr(bid, 'is_picked_up')
        assert hasattr(bid, 'created_at')
        assert hasattr(bid, 'updated_at')

    async def test_multiple_repositories_share_storage(
        self, storage, sample_participation, sample_product
    ):
        """Test multiple repository instances share the same storage."""
        repo1 = MemoryBidRepository(storage)
        repo2 = MemoryBidRepository(storage)

        bid = await repo1.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
        )

        # Both repositories should see the same bid
        assert await repo2.get_bid_by_id(bid.id) is not None

    async def test_commit_changes_is_noop(self, repo):
        """Test commit_changes() is no-op for memory repository."""
        # Should not raise any error
        await repo.commit_changes()


class TestComplexScenarios:
    """Test complex scenarios involving multiple operations."""

    async def test_full_bid_lifecycle(self, repo, sample_participation, sample_product):
        """Test full bid lifecycle from creation to distribution."""
        # Create bid
        bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=10,
            interested_only=False,
            comment='Initial bid',
        )

        assert bid.quantity == 10
        assert bid.distributed_quantity is None

        # Update bid quantity
        updated_bid = await repo.create_or_update_bid(
            participation_id=sample_participation.id,
            product_id=sample_product.id,
            quantity=15,
            interested_only=False,
            comment='Updated bid',
        )

        assert updated_bid.id == bid.id
        assert updated_bid.quantity == 15

        # Distribute quantities
        await repo.update_bid_distributed_quantities(bid.id, 12.0, Decimal('3.50'))

        final_bid = await repo.get_bid_by_id(bid.id)
        assert final_bid.quantity == 15
        assert final_bid.distributed_quantity == 12.0
        assert final_bid.distributed_price_per_unit == Decimal('3.50')

    async def test_multiple_users_bidding_on_same_product(
        self, repo, run_repo, sample_run, sample_users, sample_product
    ):
        """Test multiple users bidding on the same product."""
        bids = []
        for user in sample_users:
            participation = await run_repo.create_participation(user.id, sample_run.id)
            bid = await repo.create_or_update_bid(
                participation_id=participation.id,
                product_id=sample_product.id,
                quantity=5,
                interested_only=False,
            )
            bids.append(bid)

        # All bids should be for same product
        for bid in bids:
            assert bid.product_id == sample_product.id

        # All bids should have unique IDs
        bid_ids = [b.id for b in bids]
        assert len(bid_ids) == len(set(bid_ids))

    async def test_bid_workflow_with_run_participations(
        self, repo, run_repo, sample_run, sample_users, sample_products
    ):
        """Test bid workflow with run participations."""
        # Create participations
        participations = []
        for user in sample_users[:2]:
            participation = await run_repo.create_participation(user.id, sample_run.id)
            participations.append(participation)

        # Each user bids on multiple products
        for participation in participations:
            for product in sample_products[:3]:
                await repo.create_or_update_bid(
                    participation_id=participation.id,
                    product_id=product.id,
                    quantity=5,
                    interested_only=False,
                )

        # Get all bids for run
        all_bids = await repo.get_bids_by_run(sample_run.id)

        # Should have 2 users * 3 products = 6 bids
        assert len(all_bids) == 6

        # Get bids for each participation
        for participation in participations:
            bids = await repo.get_bids_by_participation(participation.id)
            assert len(bids) == 3
