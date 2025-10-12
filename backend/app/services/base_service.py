"""Base service class for all services."""

from sqlalchemy.orm import Session

from ..repository import AbstractRepository, get_repository


class BaseService:
    """Base service class with common functionality."""

    def __init__(self, db: Session):
        """
        Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.repo: AbstractRepository = get_repository(db)
        self.db = db
