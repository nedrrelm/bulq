"""Repository implementations."""

from sqlalchemy.orm import Session

from app.infrastructure.config import REPO_MODE
from app.repositories.abstract import AbstractRepository
from app.repositories.database import DatabaseRepository
from app.repositories.memory import MemoryRepository

__all__ = ['AbstractRepository', 'DatabaseRepository', 'MemoryRepository', 'get_repository']


def get_repository(db: Session = None) -> AbstractRepository:
    """Get the appropriate repository implementation based on config."""
    if REPO_MODE == 'memory':
        # MemoryRepository is a singleton - just call constructor
        return MemoryRepository()
    else:
        # DatabaseRepository is not yet implemented
        if db is None:
            raise ValueError('Database session required for database mode')
        return DatabaseRepository(db)
