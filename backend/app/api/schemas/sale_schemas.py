"""Schemas for sale-related requests and responses."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CreateSaleRequest(BaseModel):
    """Request model for creating a sale."""

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class UpdateSaleRequest(BaseModel):
    """Request model for updating a sale."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class AddSaleProductRequest(BaseModel):
    """Request model for adding a product to a sale."""

    product_id: str
    price: Decimal | None = Field(default=None, ge=0)
    available_quantity: Decimal | None = Field(default=None, gt=0)


class UpdateSaleProductRequest(BaseModel):
    """Request model for updating a sale product."""

    price: Decimal | None = None
    available_quantity: Decimal | None = None


class SaleProductResponse(BaseModel):
    """Sale product response."""

    id: str
    product_id: str
    product_name: str
    product_brand: str | None
    product_unit: str | None
    price: str | None
    available_quantity: str | None

    model_config = ConfigDict(from_attributes=True)


class SaleResponse(BaseModel):
    """Sale list item response."""

    id: str
    seller_id: str
    seller_name: str | None = None
    title: str
    description: str | None
    state: str
    product_count: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class SaleDetailResponse(BaseModel):
    """Full sale detail response."""

    id: str
    seller_id: str
    seller_name: str
    title: str
    description: str | None
    state: str
    invite_token: str
    products: list[SaleProductResponse]
    planning_at: str | None
    active_at: str | None
    confirmed_at: str | None
    shopping_at: str | None
    distributing_at: str | None
    completed_at: str | None
    cancelled_at: str | None
    created_at: str

    model_config = ConfigDict(from_attributes=True)
