"""Base service class for all services."""

from ..repository import AbstractRepository


class BaseService:
    """Base service class with common functionality."""

    def __init__(self, repo: AbstractRepository):
        """Initialize service with repository."""
        self.repo = repo
