"""Store service for handling store-related business logic."""

from typing import List
from ..models import Store
from .base_service import BaseService


class StoreService(BaseService):
    """Service for store operations."""

    def get_all_stores(self) -> List[Store]:
        """Get all available stores."""
        return self.repo.get_all_stores()
