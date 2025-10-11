"""Schemas for shopping-related requests and responses."""

from typing import List
from pydantic import BaseModel, field_validator, Field


class PriceObservation(BaseModel):
    """Price observation for a product at a store."""
    price: float
    notes: str
    created_at: str | None


class ShoppingListItemResponse(BaseModel):
    """Response model for a shopping list item."""
    id: str
    product_id: str
    product_name: str
    requested_quantity: int
    recent_prices: list[PriceObservation]
    purchased_quantity: int | None
    purchased_price_per_unit: str | None
    purchased_total: str | None
    is_purchased: bool
    purchase_order: int | None = None


class UpdateAvailabilityPriceRequest(BaseModel):
    """Request model for updating product availability price."""
    price: float = Field(gt=0, le=99999.99)
    notes: str = Field(default="", max_length=200)

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        # Check max 2 decimal places
        if round(v, 2) != v:
            raise ValueError('Price can have at most 2 decimal places')
        return v

    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v: str) -> str:
        return v.strip()[:200]


class MarkPurchasedRequest(BaseModel):
    """Request model for marking an item as purchased."""
    quantity: float = Field(gt=0, le=9999)
    price_per_unit: float = Field(gt=0, le=99999.99)
    total: float = Field(gt=0, le=999999.99)

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        # Check max 2 decimal places
        if round(v, 2) != v:
            raise ValueError('Quantity can have at most 2 decimal places')
        return v

    @field_validator('price_per_unit')
    @classmethod
    def validate_price_per_unit(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Price per unit must be greater than 0')
        # Check max 2 decimal places
        if round(v, 2) != v:
            raise ValueError('Price per unit can have at most 2 decimal places')
        return v

    @field_validator('total')
    @classmethod
    def validate_total(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Total must be greater than 0')
        # Check max 2 decimal places
        if round(v, 2) != v:
            raise ValueError('Total can have at most 2 decimal places')
        return v


class MarkPurchasedResponse(BaseModel):
    """Response model for marking an item as purchased."""
    message: str
    purchase_order: int


class CompleteShoppingResponse(BaseModel):
    """Response model for completing shopping."""
    message: str
    state: str
