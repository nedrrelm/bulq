from app.core.models import Group, Product, ProductBid, Run, Store, User


def test_user_creation(db_session):
    user = User(name='Model Test User', username='modeltest', password_hash='hashed_password')
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.name == 'Model Test User'
    assert user.username == 'modeltest'


def test_group_creation(db_session):
    user = User(name='Group Creator', username='groupcreator', password_hash='hashed_password')
    db_session.add(user)
    db_session.commit()

    group = Group(name='Model Test Group', created_by=user.id)
    db_session.add(group)
    db_session.commit()

    assert group.id is not None
    assert group.name == 'Model Test Group'
    assert group.created_by == user.id


def test_store_and_product_creation(db_session):
    from decimal import Decimal

    from app.core.models import ProductAvailability

    store = Store(name='Test Store')
    db_session.add(store)
    db_session.commit()

    product = Product(name='Test Product')
    db_session.add(product)
    db_session.commit()

    # Create product availability at the store with price
    availability = ProductAvailability(
        product_id=product.id, store_id=store.id, price=Decimal('29.99')
    )
    db_session.add(availability)
    db_session.commit()

    assert store.id is not None
    assert product.id is not None
    assert availability.price == Decimal('29.99')
    assert availability.store_id == store.id
    assert availability.product_id == product.id


def test_product_bid_creation(db_session):
    from app.core.models import RunParticipation

    # Create required entities
    user = User(name='Bid User', username='biduser', password_hash='hashed_password')
    creator = User(name='Bid Creator', username='bidcreator', password_hash='hashed_password')
    store = Store(name='Bid Test Store')
    db_session.add_all([user, creator, store])
    db_session.commit()

    group = Group(name='Bid Test Group', created_by=creator.id)
    db_session.add(group)
    db_session.commit()

    product = Product(name='Bid Test Product')
    db_session.add(product)
    db_session.commit()

    run = Run(group_id=group.id, store_id=store.id, state='planning')
    db_session.add(run)
    db_session.commit()

    # Create participation for user
    participation = RunParticipation(user_id=user.id, run_id=run.id, is_leader=False)
    db_session.add(participation)
    db_session.commit()

    # Create product bid (using participation_id instead of user_id)
    bid = ProductBid(
        participation_id=participation.id, product_id=product.id, quantity=5, interested_only=False
    )
    db_session.add(bid)
    db_session.commit()

    assert bid.id is not None
    assert bid.quantity == 5
    assert bid.interested_only is False
