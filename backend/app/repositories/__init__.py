"""Repository implementations."""

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.exceptions import ConfigurationError
from app.infrastructure.config import REPO_MODE
from app.repositories.abstract import AbstractRepository
from app.repositories.database import DatabaseRepository
from app.repositories.memory import MemoryRepository

__all__ = ['AbstractRepository', 'DatabaseRepository', 'MemoryRepository', 'get_repository']


def get_repository(db: Session = None) -> AbstractRepository:
    """Get the appropriate repository implementation based on config.

    Args:
        db: Database session (required when REPO_MODE is 'database')

    Returns:
        Repository implementation

    Raises:
        ConfigurationError: If database session is not provided when REPO_MODE is 'database'
    """
    if REPO_MODE == 'memory':
        # MemoryRepository is a singleton - just call constructor
        return MemoryRepository()
    else:
        # DatabaseRepository requires a database session
        if db is None:
            raise ConfigurationError(
                code=error_codes.DATABASE_SESSION_REQUIRED,
                message='Database session required for database mode',
                repo_mode=REPO_MODE,
            )
        return DatabaseRepository(db)
