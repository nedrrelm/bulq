"""Pydantic schemas for request/response models."""

from .common import MessageResponse
from .auth_schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
)
from .notification_schemas import (
    NotificationResponse,
    UnreadCountResponse,
    MarkAllReadResponse,
)
from .search_schemas import (
    StoreSearchResult,
    GroupSearchResult,
    SearchResponse,
)
from .admin_schemas import (
    AdminUserResponse,
    AdminProductResponse,
    AdminStoreResponse,
    VerificationToggleResponse,
)
from .store_schemas import (
    StoreResponse,
    CreateStoreRequest,
    StoreProductResponse,
    StoreRunResponse,
    StorePageResponse,
)
from .reassignment_schemas import (
    ReassignmentRequestModel,
    ReassignmentResponse,
    ReassignmentDetailResponse,
    MyRequestsResponse,
    RunRequestResponse,
)
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
    # Auth schemas
    "UserRegister",
    "UserLogin",
    "UserResponse",
    # Notification schemas
    "NotificationResponse",
    "UnreadCountResponse",
    "MarkAllReadResponse",
    # Search schemas
    "StoreSearchResult",
    "GroupSearchResult",
    "SearchResponse",
    # Admin schemas
    "AdminUserResponse",
    "AdminProductResponse",
    "AdminStoreResponse",
    "VerificationToggleResponse",
    # Store schemas
    "StoreResponse",
    "CreateStoreRequest",
    "StoreProductResponse",
    "StoreRunResponse",
    "StorePageResponse",
    # Reassignment schemas
    "ReassignmentRequestModel",
    "ReassignmentResponse",
    "ReassignmentDetailResponse",
    "MyRequestsResponse",
    "RunRequestResponse",
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
