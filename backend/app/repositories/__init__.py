"""Repository implementations and factory functions."""

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.exceptions import ConfigurationError
from app.infrastructure.config import REPO_MODE

# Import all domain repositories
from app.repositories.database import (
    DatabaseBidRepository,
    DatabaseGroupRepository,
    DatabaseNotificationRepository,
    DatabaseProductRepository,
    DatabaseReassignmentRepository,
    DatabaseRunRepository,
    DatabaseShoppingRepository,
    DatabaseStoreRepository,
    DatabaseUserRepository,
)
from app.repositories.memory import (
    MemoryBidRepository,
    MemoryGroupRepository,
    MemoryNotificationRepository,
    MemoryProductRepository,
    MemoryReassignmentRepository,
    MemoryRunRepository,
    MemoryShoppingRepository,
    MemoryStorage,
    MemoryStoreRepository,
    MemoryUserRepository,
)

__all__ = [
    # Database repositories
    'DatabaseBidRepository',
    'DatabaseGroupRepository',
    'DatabaseNotificationRepository',
    'DatabaseProductRepository',
    'DatabaseReassignmentRepository',
    'DatabaseRunRepository',
    'DatabaseShoppingRepository',
    'DatabaseStoreRepository',
    'DatabaseUserRepository',
    # Memory repositories
    'MemoryBidRepository',
    'MemoryGroupRepository',
    'MemoryNotificationRepository',
    'MemoryProductRepository',
    'MemoryReassignmentRepository',
    'MemoryRunRepository',
    'MemoryShoppingRepository',
    'MemoryStorage',
    'MemoryStoreRepository',
    'MemoryUserRepository',
    # Factory functions
    'get_user_repository',
    'get_group_repository',
    'get_store_repository',
    'get_product_repository',
    'get_run_repository',
    'get_bid_repository',
    'get_shopping_repository',
    'get_notification_repository',
    'get_reassignment_repository',
]

# Singleton storage for memory mode
_memory_storage = None


def _get_memory_storage() -> MemoryStorage:
    """Get or create singleton memory storage."""
    global _memory_storage
    if _memory_storage is None:
        _memory_storage = MemoryStorage()
    return _memory_storage


def _validate_database_session(db: Session | None):
    """Validate that database session is provided when in database mode."""
    if REPO_MODE == 'database' and db is None:
        raise ConfigurationError(
            code=error_codes.DATABASE_SESSION_REQUIRED,
            message='Database session required for database mode',
            repo_mode=REPO_MODE,
        )


def get_user_repository(db: Session = None):
    """Get user repository based on configuration mode."""
    if REPO_MODE == 'memory':
        return MemoryUserRepository(_get_memory_storage())
    else:
        _validate_database_session(db)
        return DatabaseUserRepository(db)


def get_group_repository(db: Session = None):
    """Get group repository based on configuration mode."""
    if REPO_MODE == 'memory':
        return MemoryGroupRepository(_get_memory_storage())
    else:
        _validate_database_session(db)
        return DatabaseGroupRepository(db)


def get_store_repository(db: Session = None):
    """Get store repository based on configuration mode."""
    if REPO_MODE == 'memory':
        return MemoryStoreRepository(_get_memory_storage())
    else:
        _validate_database_session(db)
        return DatabaseStoreRepository(db)


def get_product_repository(db: Session = None):
    """Get product repository based on configuration mode."""
    if REPO_MODE == 'memory':
        return MemoryProductRepository(_get_memory_storage())
    else:
        _validate_database_session(db)
        return DatabaseProductRepository(db)


def get_run_repository(db: Session = None):
    """Get run repository based on configuration mode."""
    if REPO_MODE == 'memory':
        return MemoryRunRepository(_get_memory_storage())
    else:
        _validate_database_session(db)
        return DatabaseRunRepository(db)


def get_bid_repository(db: Session = None):
    """Get bid repository based on configuration mode."""
    if REPO_MODE == 'memory':
        return MemoryBidRepository(_get_memory_storage())
    else:
        _validate_database_session(db)
        return DatabaseBidRepository(db)


def get_shopping_repository(db: Session = None):
    """Get shopping repository based on configuration mode."""
    if REPO_MODE == 'memory':
        return MemoryShoppingRepository(_get_memory_storage())
    else:
        _validate_database_session(db)
        return DatabaseShoppingRepository(db)


def get_notification_repository(db: Session = None):
    """Get notification repository based on configuration mode."""
    if REPO_MODE == 'memory':
        return MemoryNotificationRepository(_get_memory_storage())
    else:
        _validate_database_session(db)
        return DatabaseNotificationRepository(db)


def get_reassignment_repository(db: Session = None):
    """Get reassignment repository based on configuration mode."""
    if REPO_MODE == 'memory':
        return MemoryReassignmentRepository(_get_memory_storage())
    else:
        _validate_database_session(db)
        return DatabaseReassignmentRepository(db)
