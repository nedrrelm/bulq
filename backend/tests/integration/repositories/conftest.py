"""Database fixtures and factory helpers for integration tests."""

import os
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.models import Base, Group, Product, Run, RunParticipation, Store, User
from app.core.run_state import RunState

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture(scope='session')
async def db_engine():
    """Create a database engine from DATABASE_URL, skip if not set."""
    url = os.getenv('DATABASE_URL')
    if not url:
        pytest.skip('DATABASE_URL not set')
    if url.startswith('postgresql://'):
        url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Provide a session using nested transactions (savepoints) for test isolation.

    The outer transaction is never committed — it's rolled back after each test.
    Repository commit() calls hit the savepoint, not the real transaction.
    """
    connection = await db_engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)

    # Start a nested savepoint
    nested = await connection.begin_nested()

    # When the session commits (via repo.commit()), restart the savepoint
    @event.listens_for(session.sync_session, 'after_transaction_end')
    def restart_savepoint(sync_session, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.sync_connection.begin_nested()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest.fixture
def create_user(db_session):
    """Factory fixture for creating test users with unique usernames."""
    counter = [0]

    async def _create_user(
        name='Test User',
        username=None,
        password_hash='$2b$12$LJ3m4sMKfXzUBnYMoAdYIez/RiGEMTOppuEFNO2FMTmCizzWa6JIu',
    ):
        counter[0] += 1
        if username is None:
            username = f'testuser_{counter[0]}_{uuid4().hex[:8]}'
        user = User(name=name, username=username, password_hash=password_hash)
        db_session.add(user)
        await db_session.flush()
        return user

    return _create_user


@pytest.fixture
def create_group(db_session, create_user):
    """Factory fixture for creating test groups."""

    async def _create_group(name='Test Group', creator=None):
        if creator is None:
            creator = await create_user()
        group = Group(
            name=name,
            created_by=creator.id,
            invite_token=str(uuid4()),
            is_joining_allowed=True,
        )
        db_session.add(group)
        await db_session.flush()
        return group

    return _create_group


@pytest.fixture
def create_store(db_session, create_user):
    """Factory fixture for creating test stores."""

    async def _create_store(name='Test Store', creator=None):
        if creator is None:
            creator = await create_user()
        store = Store(name=name, created_by=creator.id)
        db_session.add(store)
        await db_session.flush()
        return store

    return _create_store


@pytest.fixture
def create_product(db_session, create_user):
    """Factory fixture for creating test products."""

    async def _create_product(name='Test Product', creator=None):
        if creator is None:
            creator = await create_user()
        product = Product(name=name, created_by=creator.id)
        db_session.add(product)
        await db_session.flush()
        return product

    return _create_product


@pytest.fixture
def create_run(db_session, create_group, create_store, create_user):
    """Factory fixture for creating test runs."""

    async def _create_run(
        group=None, store=None, leader=None, state=RunState.PLANNING, comment=None
    ):
        if leader is None:
            leader = await create_user()
        if group is None:
            group = await create_group(creator=leader)
        if store is None:
            store = await create_store(creator=leader)
        run = Run(
            group_id=group.id,
            store_id=store.id,
            state=state,
            comment=comment,
        )
        db_session.add(run)
        await db_session.flush()
        # Create leader participation
        participation = RunParticipation(
            user_id=leader.id,
            run_id=run.id,
            is_leader=True,
            is_removed=False,
        )
        db_session.add(participation)
        await db_session.flush()
        return run, leader

    return _create_run


@pytest.fixture
def create_participation(db_session):
    """Factory fixture for creating run participations."""

    async def _create_participation(user, run, is_leader=False, is_helper=False):
        participation = RunParticipation(
            user_id=user.id,
            run_id=run.id,
            is_leader=is_leader,
            is_helper=is_helper,
            is_removed=False,
        )
        db_session.add(participation)
        await db_session.flush()
        return participation

    return _create_participation
