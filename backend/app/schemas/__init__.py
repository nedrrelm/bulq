"""Pydantic schemas for request/response models."""

from .common import MessageResponse
from .run_schemas import (
    CreateRunRequest,
    CreateRunResponse,
    PlaceBidRequest,
    PlaceBidResponse,
    RetractBidResponse,
    UserBidResponse,
    ProductResponse,
    ParticipantResponse,
    RunDetailResponse,
    StateChangeResponse,
    ReadyToggleResponse,
    CancelRunResponse,
    AvailableProductResponse,
)
from .group_schemas import (
    CreateGroupRequest,
    CreateGroupResponse,
    GroupResponse,
    GroupDetailResponse,
    RunSummary,
    RunResponse,
    InviteTokenResponse,
    RegenerateTokenResponse,
    PreviewGroupResponse,
    JoinGroupResponse,
    ToggleJoiningResponse,
)
from .shopping_schemas import (
    PriceObservation,
    ShoppingListItemResponse,
    UpdateAvailabilityPriceRequest,
    MarkPurchasedRequest,
    MarkPurchasedResponse,
    CompleteShoppingResponse,
)
from .product_schemas import (
    CreateProductRequest,
    CreateProductResponse,
    ProductSearchResult,
    ProductDetailResponse,
    StoreInfo,
    AvailabilityInfo,
    PricePoint,
    StoreDetail,
)
from .distribution_schemas import (
    DistributionProduct,
    DistributionUser,
)

__all__ = [
    # Common
    "MessageResponse",
    # Run schemas
    "CreateRunRequest",
    "CreateRunResponse",
    "PlaceBidRequest",
    "PlaceBidResponse",
    "RetractBidResponse",
    "UserBidResponse",
    "ProductResponse",
    "ParticipantResponse",
    "RunDetailResponse",
    "StateChangeResponse",
    "ReadyToggleResponse",
    "CancelRunResponse",
    "AvailableProductResponse",
    # Group schemas
    "CreateGroupRequest",
    "CreateGroupResponse",
    "GroupResponse",
    "GroupDetailResponse",
    "RunSummary",
    "RunResponse",
    "InviteTokenResponse",
    "RegenerateTokenResponse",
    "PreviewGroupResponse",
    "JoinGroupResponse",
    "ToggleJoiningResponse",
    # Shopping schemas
    "PriceObservation",
    "ShoppingListItemResponse",
    "UpdateAvailabilityPriceRequest",
    "MarkPurchasedRequest",
    "MarkPurchasedResponse",
    "CompleteShoppingResponse",
    # Product schemas
    "CreateProductRequest",
    "CreateProductResponse",
    "ProductSearchResult",
    "ProductDetailResponse",
    "StoreInfo",
    "AvailabilityInfo",
    "PricePoint",
    "StoreDetail",
    # Distribution schemas
    "DistributionProduct",
    "DistributionUser",
]
