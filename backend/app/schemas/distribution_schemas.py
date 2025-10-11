"""Schemas for distribution-related requests and responses."""

from pydantic import BaseModel


class DistributionProduct(BaseModel):
    """Product information for distribution."""
    bid_id: str
    product_id: str
    product_name: str
    requested_quantity: int
    distributed_quantity: int
    price_per_unit: str
    subtotal: str
    is_picked_up: bool


class DistributionUser(BaseModel):
    """User's distribution information."""
    user_id: str
    user_name: str
    products: list[DistributionProduct]
    total_cost: str = "0.00"
    all_picked_up: bool = False
