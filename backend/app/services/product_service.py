"""Product service for handling product-related business logic."""

from collections import defaultdict
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.api.schemas import (
    PricePoint,
    ProductDetailResponse,
    ProductSearchResult,
    StoreDetail,
    StoreInfo,
)
from app.core.error_codes import (
    PRODUCT_NAME_EMPTY,
    PRODUCT_PRICE_NEGATIVE,
    PRODUCT_PRICE_ZERO,
    STORE_NOT_FOUND,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.models import Product
from app.repositories import (
    get_product_repository,
    get_run_repository,
    get_shopping_repository,
    get_store_repository,
)

from .base_service import BaseService


class ProductService(BaseService):
    """Service for product operations."""

    def __init__(self, db: Session):
        """Initialize service with necessary repositories."""
        super().__init__(db)
        self.product_repo = get_product_repository(db)
        self.run_repo = get_run_repository(db)
        self.shopping_repo = get_shopping_repository(db)
        self.store_repo = get_store_repository(db)

    def search_products(self, query: str) -> list[ProductSearchResult]:
        """Search for products by name across all stores."""
        products = self.product_repo.search_products(query)

        result = []
        for product in products:
            # Get availabilities to show store information
            availabilities = self.product_repo.get_product_availabilities(product.id)
            stores_info = []
            for avail in availabilities:
                store = self.store_repo.get_store_by_id(avail.store_id)
                if store:
                    stores_info.append(
                        StoreInfo(
                            store_id=str(store.id),
                            store_name=store.name,
                            price=float(avail.price) if avail.price else None,
                        )
                    )

            result.append(
                ProductSearchResult(
                    id=str(product.id), name=product.name, brand=product.brand, stores=stores_info
                )
            )

        return result

    def get_similar_products(self, name: str, limit: int = 5) -> list[ProductSearchResult]:
        """Get products with similar names for duplicate detection.

        Uses case-insensitive search to find products with names similar to the input.
        Returns up to `limit` results, ordered by similarity.
        """
        if not name or not name.strip():
            return []

        # Use the search_products method which does case-insensitive matching
        results = self.search_products(name.strip())

        # Limit results
        return results[:limit]

    def get_product_details(self, product_id: UUID) -> ProductDetailResponse | None:
        """Get detailed product information including price history from shopping list items and availabilities.

        Shows the product across different stores with price history.
        """
        product = self.product_repo.get_product_by_id(product_id)
        if not product:
            return None

        # Get all availabilities for this product
        availabilities = self.product_repo.get_product_availabilities(product_id)

        # Group availabilities by store
        stores_map = defaultdict(list)
        for avail in availabilities:
            stores_map[avail.store_id].append(avail)

        # Collect price data by store
        stores_data = []
        all_stores = {s.id: s for s in self.store_repo.get_all_stores()}

        for store_id, store_availabilities in stores_map.items():
            store = all_stores.get(store_id)
            if not store:
                continue

            # Get shopping list items for this product at this store
            shopping_items = self.shopping_repo.get_shopping_list_items_by_product(product.id)

            # Extract price history from all availabilities at this store
            all_prices = []

            # Add all availability prices (multiple observations over time)
            for avail in store_availabilities:
                if avail.price:
                    all_prices.append(
                        PricePoint(
                            price=float(avail.price),
                            notes=avail.notes or '',
                            timestamp=avail.created_at.isoformat() if avail.created_at else None,
                            run_id=None,
                        )
                    )

            # Add purchased prices from shopping items
            for item in shopping_items:
                if item.purchased_price_per_unit:
                    # Check if this item's run was for this store
                    run = self.run_repo.get_run_by_id(item.run_id)
                    if run and run.store_id == store_id:
                        all_prices.append(
                            PricePoint(
                                price=float(item.purchased_price_per_unit),
                                notes='Purchased',
                                timestamp=item.updated_at.isoformat() if item.updated_at else None,
                                run_id=str(item.run_id),
                            )
                        )

            # Get most recent availability for current price
            most_recent = max(
                store_availabilities,
                key=lambda a: a.created_at if a.created_at else '',
                default=None,
            )
            current_price = float(most_recent.price) if most_recent and most_recent.price else None
            notes = most_recent.notes if most_recent and most_recent.notes else ''

            stores_data.append(
                StoreDetail(
                    store_id=str(store_id),
                    store_name=store.name,
                    current_price=current_price,
                    price_history=all_prices,
                    notes=notes,
                )
            )

        return ProductDetailResponse(
            id=str(product.id),
            name=product.name,
            brand=product.brand,
            unit=product.unit,
            stores=stores_data,
        )

    def create_product(
        self,
        name: str,
        brand: str | None = None,
        unit: str | None = None,
        store_id: UUID | None = None,
        price: float | None = None,
        minimum_quantity: int | None = None,
        user_id: UUID | None = None,
    ) -> tuple[Product, Any | None]:
        """Create a new product (store-agnostic).

        Optionally create a product availability if store_id is provided.
        Returns (product, availability) tuple.
        """
        # Validate inputs
        if not name or not name.strip():
            raise ValidationError(code=PRODUCT_NAME_EMPTY, message='Product name cannot be empty')

        if price is not None:
            if price < 0:
                raise ValidationError(
                    code=PRODUCT_PRICE_NEGATIVE,
                    message='Product price cannot be negative',
                    price=price,
                )
            if price == 0:
                raise ValidationError(
                    code=PRODUCT_PRICE_ZERO, message='Product price cannot be zero'
                )

        # Verify store exists if provided
        if store_id:
            store = self.store_repo.get_store_by_id(store_id)
            if not store:
                raise NotFoundError(
                    code=STORE_NOT_FOUND, message='Store not found', store_id=str(store_id)
                )

        # Create the product
        product = self.product_repo.create_product(name.strip(), brand, unit)

        # Create availability if store is provided
        availability = None
        if store_id:
            availability = self.product_repo.create_product_availability(
                product.id,
                store_id,
                price=price,
                minimum_quantity=minimum_quantity,
                user_id=user_id,
            )

        return product, availability
