"""Pydantic schemas for request/response models."""

from .admin_schemas import (
    AdminProductResponse,
    AdminStoreResponse,
    AdminUserResponse,
    DeleteResponse,
    MergeResponse,
    UpdateProductRequest,
    UpdateStoreRequest,
    UpdateUserRequest,
    VerificationToggleResponse,
)
from .auth_schemas import (
    ChangeLanguageRequest,
    ChangeNameRequest,
    ChangePasswordRequest,
    ChangeUsernameRequest,
    UserLogin,
    UserRegister,
    UserResponse,
    UserStatsResponse,
)
from .common import SuccessResponse
from .distribution_schemas import (
    DistributionProduct,
    DistributionUser,
)
from .group_schemas import (
    CreateGroupRequest,
    CreateGroupResponse,
    GroupDetailResponse,
    GroupResponse,
    InviteTokenResponse,
    JoinGroupResponse,
    PreviewGroupResponse,
    RegenerateTokenResponse,
    RunResponse,
    RunSummary,
    ToggleJoiningResponse,
)
from .notification_schemas import (
    MarkAllReadResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from .product_schemas import (
    AvailabilityInfo,
    CreateProductRequest,
    CreateProductResponse,
    PricePoint,
    ProductDetailResponse,
    ProductSearchResult,
    StoreDetail,
    StoreInfo,
)
from .reassignment_schemas import (
    MyRequestsResponse,
    ReassignmentDetailResponse,
    ReassignmentRequestModel,
    ReassignmentResponse,
    RunRequestResponse,
)
from .run_schemas import (
    AvailableProductResponse,
    CancelRunResponse,
    CreateRunRequest,
    CreateRunResponse,
    ParticipantResponse,
    PlaceBidRequest,
    PlaceBidResponse,
    ProductResponse,
    ReadyToggleResponse,
    RetractBidResponse,
    RunDetailResponse,
    StateChangeResponse,
    UpdateRunCommentRequest,
    UserBidResponse,
)
from .search_schemas import (
    GroupSearchResult,
    SearchResponse,
    StoreSearchResult,
)
from .shopping_schemas import (
    AddMorePurchaseRequest,
    CompleteShoppingResponse,
    MarkPurchasedRequest,
    MarkPurchasedResponse,
    PriceObservation,
    ShoppingListItemResponse,
    UpdateAvailabilityPriceRequest,
)
from .store_schemas import (
    CreateStoreRequest,
    StorePageResponse,
    StoreProductResponse,
    StoreResponse,
    StoreRunResponse,
)

__all__ = [
    # Common
    'SuccessResponse',
    # Auth schemas
    'UserRegister',
    'UserLogin',
    'UserResponse',
    'UserStatsResponse',
    'ChangePasswordRequest',
    'ChangeUsernameRequest',
    'ChangeNameRequest',
    'ChangeLanguageRequest',
    # Notification schemas
    'NotificationResponse',
    'UnreadCountResponse',
    'MarkAllReadResponse',
    # Search schemas
    'StoreSearchResult',
    'GroupSearchResult',
    'SearchResponse',
    # Admin schemas
    'AdminUserResponse',
    'AdminProductResponse',
    'AdminStoreResponse',
    'VerificationToggleResponse',
    'UpdateProductRequest',
    'UpdateStoreRequest',
    'UpdateUserRequest',
    'MergeResponse',
    'DeleteResponse',
    # Store schemas
    'StoreResponse',
    'CreateStoreRequest',
    'StoreProductResponse',
    'StoreRunResponse',
    'StorePageResponse',
    # Reassignment schemas
    'ReassignmentRequestModel',
    'ReassignmentResponse',
    'ReassignmentDetailResponse',
    'MyRequestsResponse',
    'RunRequestResponse',
    # Run schemas
    'CreateRunRequest',
    'CreateRunResponse',
    'PlaceBidRequest',
    'PlaceBidResponse',
    'RetractBidResponse',
    'UserBidResponse',
    'ProductResponse',
    'ParticipantResponse',
    'RunDetailResponse',
    'StateChangeResponse',
    'ReadyToggleResponse',
    'CancelRunResponse',
    'AvailableProductResponse',
    'UpdateRunCommentRequest',
    # Group schemas
    'CreateGroupRequest',
    'CreateGroupResponse',
    'GroupResponse',
    'GroupDetailResponse',
    'RunSummary',
    'RunResponse',
    'InviteTokenResponse',
    'RegenerateTokenResponse',
    'PreviewGroupResponse',
    'JoinGroupResponse',
    'ToggleJoiningResponse',
    # Shopping schemas
    'PriceObservation',
    'ShoppingListItemResponse',
    'UpdateAvailabilityPriceRequest',
    'MarkPurchasedRequest',
    'MarkPurchasedResponse',
    'CompleteShoppingResponse',
    'AddMorePurchaseRequest',
    # Product schemas
    'CreateProductRequest',
    'CreateProductResponse',
    'ProductSearchResult',
    'ProductDetailResponse',
    'StoreInfo',
    'AvailabilityInfo',
    'PricePoint',
    'StoreDetail',
    # Distribution schemas
    'DistributionProduct',
    'DistributionUser',
]
