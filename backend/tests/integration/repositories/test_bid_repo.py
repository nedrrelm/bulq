"""Integration tests for DatabaseBidRepository."""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.models import Run, RunParticipation
from app.repositories.database.bid import DatabaseBidRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def bid_repo(db_session):
    return DatabaseBidRepository(db_session)


@pytest.fixture
def participation(db_session, create_user, create_group, create_store):
    """Create a run participation for testing bids."""
    user = create_user()
    group = create_group(creator=user)
    store = create_store(creator=user)
    run = Run(group_id=group.id, store_id=store.id, state='planning')
    db_session.add(run)
    db_session.flush()
    p = RunParticipation(user_id=user.id, run_id=run.id, is_leader=True)
    db_session.add(p)
    db_session.flush()
    return p


@pytest.fixture
def second_participation(db_session, create_user, create_group, create_store):
    """Create a second participation on a different run."""
    user = create_user()
    group = create_group(creator=user)
    store = create_store(creator=user)
    run = Run(group_id=group.id, store_id=store.id, state='planning')
    db_session.add(run)
    db_session.flush()
    p = RunParticipation(user_id=user.id, run_id=run.id, is_leader=False)
    db_session.add(p)
    db_session.flush()
    return p


@pytest.fixture
def product(create_product):
    return create_product()


@pytest.fixture
def product2(create_product):
    return create_product(name='Test Product 2')


class TestCreateOrUpdateBid:
    def test_create_new_bid(self, bid_repo, participation, product):
        bid = bid_repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=product.id,
            quantity=5,
            interested_only=False,
            comment='Need this',
        )
        assert bid.id is not None
        assert bid.participation_id == participation.id
        assert bid.product_id == product.id
        assert bid.quantity == 5
        assert bid.interested_only is False
        assert bid.comment == 'Need this'

    def test_update_existing_bid(self, bid_repo, participation, product):
        bid_repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=product.id,
            quantity=5,
            interested_only=False,
            comment='First',
        )
        updated = bid_repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=product.id,
            quantity=10,
            interested_only=True,
            comment='Updated',
        )
        assert updated.quantity == 10
        assert updated.interested_only is True
        assert updated.comment == 'Updated'

    def test_create_bid_without_comment(self, bid_repo, participation, product):
        bid = bid_repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=product.id,
            quantity=3,
            interested_only=True,
        )
        assert bid.comment is None


class TestGetBid:
    def test_get_bid_found(self, bid_repo, participation, product):
        created = bid_repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=product.id,
            quantity=2,
            interested_only=False,
        )
        found = bid_repo.get_bid(participation.id, product.id)
        assert found is not None
        assert found.id == created.id

    def test_get_bid_not_found(self, bid_repo, participation, product):
        result = bid_repo.get_bid(participation.id, product.id)
        assert result is None


class TestGetBidById:
    def test_found(self, bid_repo, participation, product):
        created = bid_repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=product.id,
            quantity=1,
            interested_only=False,
        )
        found = bid_repo.get_bid_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    def test_not_found(self, bid_repo):
        result = bid_repo.get_bid_by_id(uuid4())
        assert result is None


class TestGetBidsByRun:
    def test_with_bids(self, bid_repo, participation, product, product2):
        bid_repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=product.id,
            quantity=1,
            interested_only=False,
        )
        bid_repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=product2.id,
            quantity=2,
            interested_only=True,
        )
        run_id = participation.run_id
        bids = bid_repo.get_bids_by_run(run_id)
        assert len(bids) == 2

    def test_empty(self, bid_repo, participation):
        bids = bid_repo.get_bids_by_run(participation.run_id)
        assert bids == []


class TestGetBidsByRunWithParticipations:
    def test_eager_loading(self, bid_repo, participation, product):
        bid_repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=product.id,
            quantity=1,
            interested_only=False,
        )
        bids = bid_repo.get_bids_by_run_with_participations(participation.run_id)
        assert len(bids) == 1
        # Verify eager loading worked - accessing participation.user should not raise
        assert bids[0].participation is not None
        assert bids[0].participation.user is not None


class TestGetBidsByParticipation:
    def test_returns_bids(self, bid_repo, participation, product, product2):
        bid_repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=product.id,
            quantity=1,
            interested_only=False,
        )
        bid_repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=product2.id,
            quantity=3,
            interested_only=True,
        )
        bids = bid_repo.get_bids_by_participation(participation.id)
        assert len(bids) == 2

    def test_returns_empty_for_no_bids(self, bid_repo, participation):
        bids = bid_repo.get_bids_by_participation(participation.id)
        assert bids == []


class TestDeleteBid:
    def test_delete_existing(self, bid_repo, participation, product):
        bid_repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=product.id,
            quantity=1,
            interested_only=False,
        )
        result = bid_repo.delete_bid(participation.id, product.id)
        assert result is True
        assert bid_repo.get_bid(participation.id, product.id) is None

    def test_delete_nonexistent(self, bid_repo, participation, product):
        result = bid_repo.delete_bid(participation.id, product.id)
        assert result is False


class TestUpdateBidDistributedQuantities:
    def test_updates_distributed_fields(self, bid_repo, participation, product):
        bid = bid_repo.create_or_update_bid(
            participation_id=participation.id,
            product_id=product.id,
            quantity=10,
            interested_only=False,
        )
        bid_repo.update_bid_distributed_quantities(
            bid_id=bid.id,
            quantity=8.5,
            price_per_unit=Decimal('3.99'),
        )
        updated = bid_repo.get_bid_by_id(bid.id)
        assert float(updated.distributed_quantity) == 8.5
        assert updated.distributed_price_per_unit == Decimal('3.99')

    def test_nonexistent_bid_does_nothing(self, bid_repo):
        # Should not raise
        bid_repo.update_bid_distributed_quantities(
            bid_id=uuid4(),
            quantity=5.0,
            price_per_unit=Decimal('1.00'),
        )


class TestCommitChanges:
    def test_commit_does_not_raise(self, bid_repo):
        bid_repo.commit_changes()
