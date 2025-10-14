"""Schemas for store-related requests and responses."""

from pydantic import BaseModel, Field


class StoreResponse(BaseModel):
    """Basic store information response."""

    id: str
    name: str

    class Config:
        from_attributes = True


class CreateStoreRequest(BaseModel):
    """Request model for creating a new store."""

    name: str = Field(min_length=1, max_length=200)


class StoreProductResponse(BaseModel):
    """Product information for store page."""

    id: str
    name: str
    brand: str | None
    unit: str | None
    current_price: str | None

    class Config:
        from_attributes = True


class StoreRunResponse(BaseModel):
    """Run information for store page."""

    id: str
    state: str
    group_id: str
    group_name: str
    store_name: str
    leader_name: str
    planned_on: str | None

    class Config:
        from_attributes = True


class StorePageResponse(BaseModel):
    """Complete store page response with products and runs."""

    store: StoreResponse
    products: list[StoreProductResponse]
    active_runs: list[StoreRunResponse]
