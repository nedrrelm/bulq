"""Schemas for product-related requests and responses."""

from typing import List, Optional
from pydantic import BaseModel


class CreateProductRequest(BaseModel):
    """Request model for creating a new product."""
    name: str
    brand: Optional[str] = None
    unit: Optional[str] = None
    store_id: Optional[str] = None  # Optional: add availability if provided
    price: Optional[float] = None    # Optional: price for availability


class StoreInfo(BaseModel):
    """Store information for product."""
    store_id: str
    store_name: str
    price: Optional[float]


class ProductSearchResult(BaseModel):
    """Response model for product search results."""
    id: str
    name: str
    brand: Optional[str]
    stores: List[StoreInfo]


class AvailabilityInfo(BaseModel):
    """Product availability information."""
    store_id: str
    price: Optional[float]
    notes: Optional[str]


class CreateProductResponse(BaseModel):
    """Response model for creating a product."""
    id: str
    name: str
    brand: Optional[str]
    unit: Optional[str]
    availability: Optional[AvailabilityInfo] = None


class PricePoint(BaseModel):
    """Price point in product price history."""
    price: float
    notes: str
    timestamp: Optional[str]
    run_id: Optional[str] = None


class StoreDetail(BaseModel):
    """Store detail with price history."""
    store_id: str
    store_name: str
    current_price: Optional[float]
    price_history: List[PricePoint]


class ProductDetailResponse(BaseModel):
    """Response model for product details."""
    id: str
    name: str
    brand: Optional[str]
    unit: Optional[str]
    stores: List[StoreDetail]
