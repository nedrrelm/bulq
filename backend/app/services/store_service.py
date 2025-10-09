"""Store service for handling store-related business logic."""

from typing import List
from ..models import Store
from .base_service import BaseService
from ..exceptions import ValidationError


class StoreService(BaseService):
    """Service for store operations."""

    def get_all_stores(self) -> List[Store]:
        """Get all available stores."""
        return self.repo.get_all_stores()

    def create_store(self, name: str) -> Store:
        """Create a new store."""
        if not name or not name.strip():
            raise ValidationError("Store name cannot be empty")
        return self.repo.create_store(name.strip())
