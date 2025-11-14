"""Schemas for shopping-related requests and responses."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


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
    product_unit: str | None = None
    requested_quantity: float
    recent_prices: list[PriceObservation]
    purchased_quantity: float | None
    purchased_price_per_unit: str | None
    purchased_total: str | None
    is_purchased: bool
    purchase_order: int | None = None


class UpdateAvailabilityPriceRequest(BaseModel):
    """Request model for updating product availability price."""

    price: float = Field(gt=0, le=99999.99)
    notes: str = Field(default='', max_length=200)
    minimum_quantity: int | None = Field(default=None, ge=1, le=9999)

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: float) -> float:
        # Check max 2 decimal places
        if round(v, 2) != v:
            raise ValueError('INVALID_DECIMAL_PLACES')
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

    @field_validator('quantity', 'price_per_unit', 'total')
    @classmethod
    def validate_decimal_places(cls, v: float) -> float:
        # Check max 2 decimal places
        if round(v, 2) != v:
            raise ValueError('INVALID_DECIMAL_PLACES')
        return v


class MarkPurchasedResponse(BaseModel):
    """Response model for marking an item as purchased."""

    success: bool = True
    code: str  # Success code for frontend localization
    purchase_order: int
    details: dict[str, Any] = Field(default_factory=dict)


class AddMorePurchaseRequest(BaseModel):
    """Request model for adding more quantity to an already-purchased item."""

    quantity: float = Field(gt=0, le=9999)
    price_per_unit: float = Field(gt=0, le=99999.99)
    total: float = Field(gt=0, le=999999.99)

    @field_validator('quantity', 'price_per_unit', 'total')
    @classmethod
    def validate_decimal_places(cls, v: float) -> float:
        # Check max 2 decimal places
        if round(v, 2) != v:
            raise ValueError('INVALID_DECIMAL_PLACES')
        return v


class CompleteShoppingResponse(BaseModel):
    """Response model for completing shopping.

    The 'code' field contains a machine-readable success code for frontend localization.
    """

    success: bool = True
    code: str  # Success code for frontend localization
    state: str
    details: dict = {}
