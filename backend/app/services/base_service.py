"""Base service class for all services."""

from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    """Base service class with common functionality.

    Services should initialize only the repositories they need
    using the repository factory functions from app.repositories.
    """

    def __init__(self, db: AsyncSession):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy async database session
        """
        self.db = db
