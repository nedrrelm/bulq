"""
Pytest configuration and shared fixtures for testing.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models import Base
from app.auth import sessions  # Import sessions dict to clear between tests

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db():
    """
    Create fresh database for each test.
    Creates all tables before test and drops them after.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db):
    """
    Provide a database session for tests that need direct database access.
    """
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db):
    """
    Provide a test client for making HTTP requests.
    Automatically handles database setup/teardown via db fixture.
    """
    # Clear sessions before each test
    sessions.clear()

    with TestClient(app) as c:
        yield c

    # Clear sessions after each test
    sessions.clear()


@pytest.fixture
def authenticated_client(client):
    """
    Provide a test client with an authenticated user.
    Useful for tests that require authentication.
    """
    # Register and login a user
    client.post("/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpassword123"
    })
    client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })

    yield client

    # Logout after test
    client.post("/auth/logout")


@pytest.fixture
def sample_user(db_session):
    """
    Create a sample user for testing.
    Returns the user object.
    """
    from app.models import User
    from app.auth import hash_password

    user = User(
        name="Sample User",
        email="sample@example.com",
        password_hash=hash_password("password123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def sample_group(db_session, sample_user):
    """
    Create a sample group with the sample user as creator and member.
    Returns the group object.
    """
    from app.models import Group, GroupMembership

    group = Group(
        name="Sample Group",
        created_by=sample_user.id,
        invite_token="sample_invite_token_123"
    )
    db_session.add(group)
    db_session.commit()

    # Add creator as member
    membership = GroupMembership(user_id=sample_user.id, group_id=group.id)
    db_session.add(membership)
    db_session.commit()

    db_session.refresh(group)
    return group


@pytest.fixture
def sample_store(db_session):
    """
    Create a sample store for testing.
    Returns the store object.
    """
    from app.models import Store

    store = Store(name="Sample Store")
    db_session.add(store)
    db_session.commit()
    db_session.refresh(store)

    return store


@pytest.fixture
def sample_product(db_session, sample_store):
    """
    Create a sample product for testing.
    Returns the product object.
    """
    from app.models import Product
    from decimal import Decimal

    product = Product(
        store_id=sample_store.id,
        name="Sample Product",
        base_price=Decimal("19.99")
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    return product


@pytest.fixture
def sample_run(db_session, sample_group, sample_store, sample_user):
    """
    Create a sample run with participation for testing.
    Returns tuple of (run, participation).
    """
    from app.models import Run, RunParticipation

    run = Run(
        group_id=sample_group.id,
        store_id=sample_store.id,
        state="planning"
    )
    db_session.add(run)
    db_session.commit()

    participation = RunParticipation(
        user_id=sample_user.id,
        run_id=run.id,
        is_leader=True,
        is_ready=False
    )
    db_session.add(participation)
    db_session.commit()

    db_session.refresh(run)
    db_session.refresh(participation)

    return run, participation


@pytest.fixture
def complete_test_setup(db_session, sample_user, sample_group, sample_store, sample_product, sample_run):
    """
    Provide a complete test setup with all entities created.
    Returns a dictionary with all entities.
    """
    run, participation = sample_run

    return {
        "user": sample_user,
        "group": sample_group,
        "store": sample_store,
        "product": sample_product,
        "run": run,
        "participation": participation,
        "db_session": db_session
    }


# Hooks for test execution

def pytest_configure(config):
    """
    Configure pytest with custom markers.
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "websocket: marks tests that require WebSocket support"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically mark tests based on their location or name.
    """
    for item in items:
        # Mark integration tests
        if "test_routes" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark unit tests
        if any(name in str(item.fspath) for name in ["test_models", "test_repository", "test_state_machine"]):
            item.add_marker(pytest.mark.unit)

        # Mark websocket tests
        if "websocket" in item.nodeid.lower():
            item.add_marker(pytest.mark.websocket)
