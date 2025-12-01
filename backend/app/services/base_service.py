"""Base service class for all services."""

from sqlalchemy.orm import Session


class BaseService:
    """Base service class with common functionality.

    Services should initialize only the repositories they need
    using the repository factory functions from app.repositories.
    """

    def __init__(self, db: Session):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
