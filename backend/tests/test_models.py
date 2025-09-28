import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import User, Group, Store, Product, Run, ProductBid, Base


def test_user_creation(db):
    from database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    user = User(name="Test User", email="test@example.com")
    session.add(user)
    session.commit()

    assert user.id is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"

    session.close()


def test_group_creation(db):
    from database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    user = User(name="Creator", email="creator@example.com")
    session.add(user)
    session.commit()

    group = Group(name="Test Group", created_by=user.id)
    session.add(group)
    session.commit()

    assert group.id is not None
    assert group.name == "Test Group"
    assert group.created_by == user.id

    session.close()


def test_store_and_product_creation(db):
    from database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    store = Store(name="Test Store")
    session.add(store)
    session.commit()

    product = Product(
        store_id=store.id,
        name="Test Product",
        base_price=29.99
    )
    session.add(product)
    session.commit()

    assert store.id is not None
    assert product.store_id == store.id
    assert product.base_price == 29.99

    session.close()


def test_product_bid_creation(db):
    from database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    # Create required entities
    user = User(name="Bidder", email="bidder@example.com")
    creator = User(name="Creator", email="creator@example.com")
    store = Store(name="Test Store")
    session.add_all([user, creator, store])
    session.commit()

    group = Group(name="Test Group", created_by=creator.id)
    session.add(group)
    session.commit()

    product = Product(store_id=store.id, name="Test Product", base_price=19.99)
    session.add(product)
    session.commit()

    run = Run(group_id=group.id, store_id=store.id, state="planning")
    session.add(run)
    session.commit()

    # Create product bid
    bid = ProductBid(
        user_id=user.id,
        run_id=run.id,
        product_id=product.id,
        quantity=5,
        interested_only=False
    )
    session.add(bid)
    session.commit()

    assert bid.id is not None
    assert bid.quantity == 5
    assert bid.interested_only is False

    session.close()