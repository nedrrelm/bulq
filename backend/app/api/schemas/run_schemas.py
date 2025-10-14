"""Schemas for run-related requests and responses."""

from pydantic import BaseModel, Field, field_validator


class CreateRunRequest(BaseModel):
    """Request model for creating a new run."""

    group_id: str
    store_id: str


class CreateRunResponse(BaseModel):
    """Response model for creating a new run."""

    id: str
    group_id: str
    store_id: str
    state: str
    store_name: str
    leader_name: str

    class Config:
        from_attributes = True


class PlaceBidRequest(BaseModel):
    """Request model for placing a bid on a product."""

    product_id: str
    quantity: float = Field(gt=0, le=9999)
    interested_only: bool = False

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        # Check max 2 decimal places
        if round(v, 2) != v:
            raise ValueError('Quantity can have at most 2 decimal places')
        return v


class UserBidResponse(BaseModel):
    """Response model for a user's bid on a product."""

    user_id: str
    user_name: str
    quantity: int
    interested_only: bool

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    """Response model for a product in a run."""

    id: str
    name: str
    brand: str | None = None
    current_price: str | None
    total_quantity: int
    interested_count: int
    user_bids: list[UserBidResponse]
    current_user_bid: UserBidResponse | None
    purchased_quantity: int | None = None  # For adjusting state

    class Config:
        from_attributes = True


class ParticipantResponse(BaseModel):
    """Response model for a run participant."""

    user_id: str
    user_name: str
    is_leader: bool
    is_ready: bool
    is_removed: bool = False

    class Config:
        from_attributes = True


class RunDetailResponse(BaseModel):
    """Response model for detailed run information."""

    id: str
    group_id: str
    group_name: str
    store_id: str
    store_name: str
    state: str
    products: list[ProductResponse]
    participants: list[ParticipantResponse]
    current_user_is_ready: bool
    current_user_is_leader: bool
    leader_name: str

    class Config:
        from_attributes = True


class StateChangeResponse(BaseModel):
    """Response model for state change operations."""

    message: str
    state: str
    run_id: str
    group_id: str


class ReadyToggleResponse(BaseModel):
    """Response model for toggling ready status."""

    message: str
    is_ready: bool
    state_changed: bool = False
    new_state: str | None = None
    run_id: str
    user_id: str
    group_id: str | None = None


class CancelRunResponse(BaseModel):
    """Response model for canceling a run."""

    message: str
    run_id: str
    group_id: str
    state: str


class AvailableProductResponse(BaseModel):
    """Response model for available products."""

    id: str
    name: str
    brand: str | None = None
    current_price: str | None
    has_store_availability: bool = False

    class Config:
        from_attributes = True


class PlaceBidResponse(BaseModel):
    """Response model for placing a bid."""

    message: str
    product_id: str
    user_id: str
    user_name: str
    quantity: float
    interested_only: bool
    new_total: float
    state_changed: bool
    new_state: str
    run_id: str
    group_id: str


class RetractBidResponse(BaseModel):
    """Response model for retracting a bid."""

    message: str
    run_id: str
    product_id: str
    user_id: str
    new_total: float
