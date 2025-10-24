"""Schemas for product-related requests and responses."""

from pydantic import BaseModel


class CreateProductRequest(BaseModel):
    """Request model for creating a new product."""

    name: str
    brand: str | None = None
    unit: str | None = None
    store_id: str | None = None  # Optional: add availability if provided
    price: float | None = None  # Optional: price for availability
    minimum_quantity: int | None = None  # Optional: minimum quantity for availability


class StoreInfo(BaseModel):
    """Store information for product."""

    store_id: str
    store_name: str
    price: float | None


class ProductSearchResult(BaseModel):
    """Response model for product search results."""

    id: str
    name: str
    brand: str | None
    stores: list[StoreInfo]


class AvailabilityInfo(BaseModel):
    """Product availability information."""

    store_id: str
    price: float | None
    notes: str | None


class CreateProductResponse(BaseModel):
    """Response model for creating a product."""

    id: str
    name: str
    brand: str | None
    unit: str | None
    availability: AvailabilityInfo | None = None


class PricePoint(BaseModel):
    """Price point in product price history."""

    price: float
    notes: str
    timestamp: str | None
    run_id: str | None = None


class StoreDetail(BaseModel):
    """Store detail with price history."""

    store_id: str
    store_name: str
    current_price: float | None
    price_history: list[PricePoint]
    notes: str


class ProductDetailResponse(BaseModel):
    """Response model for product details."""

    id: str
    name: str
    brand: str | None
    unit: str | None
    stores: list[StoreDetail]
