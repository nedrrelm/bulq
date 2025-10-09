import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models import User, Group, Store, Product, Run, ProductBid, Base


def test_user_creation(db):
    from app.database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    user = User(name="Model Test User", email="modeltest@example.com", password_hash="hashed_password")
    session.add(user)
    session.commit()

    assert user.id is not None
    assert user.name == "Model Test User"
    assert user.email == "modeltest@example.com"

    session.close()


def test_group_creation(db):
    from app.database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    user = User(name="Group Creator", email="groupcreator@example.com", password_hash="hashed_password")
    session.add(user)
    session.commit()

    group = Group(name="Model Test Group", created_by=user.id)
    session.add(group)
    session.commit()

    assert group.id is not None
    assert group.name == "Model Test Group"
    assert group.created_by == user.id

    session.close()


def test_store_and_product_creation(db):
    from app.database import engine
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
    assert float(product.base_price) == 29.99

    session.close()


def test_product_bid_creation(db):
    from app.database import engine
    from app.models import RunParticipation
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    # Create required entities
    user = User(name="Bid User", email="biduser@example.com", password_hash="hashed_password")
    creator = User(name="Bid Creator", email="bidcreator@example.com", password_hash="hashed_password")
    store = Store(name="Bid Test Store")
    session.add_all([user, creator, store])
    session.commit()

    group = Group(name="Bid Test Group", created_by=creator.id)
    session.add(group)
    session.commit()

    product = Product(store_id=store.id, name="Bid Test Product", base_price=19.99)
    session.add(product)
    session.commit()

    run = Run(group_id=group.id, store_id=store.id, state="planning")
    session.add(run)
    session.commit()

    # Create participation for user
    participation = RunParticipation(user_id=user.id, run_id=run.id, is_leader=False)
    session.add(participation)
    session.commit()

    # Create product bid (using participation_id instead of user_id)
    bid = ProductBid(
        participation_id=participation.id,
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