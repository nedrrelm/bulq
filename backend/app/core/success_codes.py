"""Success code constants for API responses.

This module defines all success codes used across the application for successful operations.
These codes are returned to the frontend for localization and should never contain
human-readable messages.

Success Code Naming Convention:
- Use SCREAMING_SNAKE_CASE
- Be descriptive but concise
- Past tense for completed actions (e.g., MEMBER_REMOVED, BID_PLACED)

Frontend Translation Keys:
Success codes map directly to translation keys in the frontend.
Example: SUCCESS_CODE.BID_PLACED → "success.bid.placed"
"""


# ============================================================================
# General Success Codes
# ============================================================================

OPERATION_SUCCESSFUL = 'OPERATION_SUCCESSFUL'
RESOURCE_CREATED = 'RESOURCE_CREATED'
RESOURCE_UPDATED = 'RESOURCE_UPDATED'
RESOURCE_DELETED = 'RESOURCE_DELETED'


# ============================================================================
# Authentication & User Management
# ============================================================================

USER_REGISTERED = 'USER_REGISTERED'
USER_LOGGED_IN = 'USER_LOGGED_IN'
USER_LOGGED_OUT = 'USER_LOGGED_OUT'
PASSWORD_CHANGED = 'PASSWORD_CHANGED'
PROFILE_UPDATED = 'PROFILE_UPDATED'


# ============================================================================
# Run Management
# ============================================================================

RUN_CREATED = 'RUN_CREATED'
RUN_UPDATED = 'RUN_UPDATED'
RUN_DELETED = 'RUN_DELETED'
RUN_CANCELLED = 'RUN_CANCELLED'
RUN_STATE_CHANGED = 'RUN_STATE_CHANGED'
RUN_COMMENT_UPDATED = 'RUN_COMMENT_UPDATED'
HELPER_ADDED = 'HELPER_ADDED'
HELPER_REMOVED = 'HELPER_REMOVED'

# Run state transitions
RUN_FORCE_CONFIRMED = 'RUN_FORCE_CONFIRMED'
SHOPPING_STARTED = 'SHOPPING_STARTED'
ADJUSTING_FINISHED = 'ADJUSTING_FINISHED'
READY_TOGGLED_RUN_CONFIRMED = 'READY_TOGGLED_RUN_CONFIRMED'


# ============================================================================
# Bid Management
# ============================================================================

BID_PLACED = 'BID_PLACED'
BID_UPDATED = 'BID_UPDATED'
BID_RETRACTED = 'BID_RETRACTED'
READY_TOGGLED = 'READY_TOGGLED'


# ============================================================================
# Shopping
# ============================================================================

ITEM_MARKED_PURCHASED = 'ITEM_MARKED_PURCHASED'
ITEM_MARKED_UNPURCHASED = 'ITEM_MARKED_UNPURCHASED'
PRICE_UPDATED = 'PRICE_UPDATED'
ADDITIONAL_PURCHASE_ADDED = 'ADDITIONAL_PURCHASE_ADDED'
SHOPPING_COMPLETED = 'SHOPPING_COMPLETED'


# ============================================================================
# Distribution
# ============================================================================

BID_MARKED_PICKED_UP = 'BID_MARKED_PICKED_UP'
BID_MARKED_NOT_PICKED_UP = 'BID_MARKED_NOT_PICKED_UP'
DISTRIBUTION_UPDATED = 'DISTRIBUTION_UPDATED'
DISTRIBUTION_COMPLETED = 'DISTRIBUTION_COMPLETED'


# ============================================================================
# Group Management
# ============================================================================

GROUP_CREATED = 'GROUP_CREATED'
GROUP_UPDATED = 'GROUP_UPDATED'
GROUP_DELETED = 'GROUP_DELETED'
GROUP_JOINED = 'GROUP_JOINED'
GROUP_LEFT = 'GROUP_LEFT'
MEMBER_REMOVED = 'MEMBER_REMOVED'
MEMBER_PROMOTED = 'MEMBER_PROMOTED'
INVITE_TOKEN_REGENERATED = 'INVITE_TOKEN_REGENERATED'
GROUP_JOINING_TOGGLED = 'GROUP_JOINING_TOGGLED'


# ============================================================================
# Notifications
# ============================================================================

NOTIFICATION_MARKED_READ = 'NOTIFICATION_MARKED_READ'
NOTIFICATIONS_MARKED_READ = 'NOTIFICATIONS_MARKED_READ'
NOTIFICATION_DELETED = 'NOTIFICATION_DELETED'


# ============================================================================
# Reassignment
# ============================================================================

REASSIGNMENT_REQUEST_CREATED = 'REASSIGNMENT_REQUEST_CREATED'
REASSIGNMENT_REQUEST_ACCEPTED = 'REASSIGNMENT_REQUEST_ACCEPTED'
REASSIGNMENT_REQUEST_DECLINED = 'REASSIGNMENT_REQUEST_DECLINED'
REASSIGNMENT_REQUEST_CANCELLED = 'REASSIGNMENT_REQUEST_CANCELLED'


# ============================================================================
# Product & Store Management
# ============================================================================

PRODUCT_CREATED = 'PRODUCT_CREATED'
PRODUCT_UPDATED = 'PRODUCT_UPDATED'
PRODUCT_DELETED = 'PRODUCT_DELETED'
PRODUCT_VERIFIED = 'PRODUCT_VERIFIED'
PRODUCT_UNVERIFIED = 'PRODUCT_UNVERIFIED'
PRODUCTS_MERGED = 'PRODUCTS_MERGED'

STORE_CREATED = 'STORE_CREATED'
STORE_UPDATED = 'STORE_UPDATED'
STORE_DELETED = 'STORE_DELETED'
STORE_VERIFIED = 'STORE_VERIFIED'
STORE_UNVERIFIED = 'STORE_UNVERIFIED'
STORES_MERGED = 'STORES_MERGED'

# Shopping completion codes
SHOPPING_COMPLETED_NO_PURCHASES = 'SHOPPING_COMPLETED_NO_PURCHASES'
SHOPPING_COMPLETED_ADJUSTING_REQUIRED = 'SHOPPING_COMPLETED_ADJUSTING_REQUIRED'
SHOPPING_COMPLETED_DISTRIBUTING = 'SHOPPING_COMPLETED_DISTRIBUTING'


# ============================================================================
# Admin Operations
# ============================================================================

USER_ADMIN_STATUS_UPDATED = 'USER_ADMIN_STATUS_UPDATED'
USER_DELETED = 'USER_DELETED'
USER_VERIFIED = 'USER_VERIFIED'
USER_UNVERIFIED = 'USER_UNVERIFIED'


# ============================================================================
# Success Code Groups for Documentation
# ============================================================================

SUCCESS_CODE_GROUPS = {
    'General': [
        OPERATION_SUCCESSFUL,
        RESOURCE_CREATED,
        RESOURCE_UPDATED,
        RESOURCE_DELETED,
    ],
    'Authentication': [
        USER_REGISTERED,
        USER_LOGGED_IN,
        USER_LOGGED_OUT,
        PASSWORD_CHANGED,
        PROFILE_UPDATED,
    ],
    'Runs': [
        RUN_CREATED,
        RUN_UPDATED,
        RUN_DELETED,
        RUN_CANCELLED,
        RUN_STATE_CHANGED,
        RUN_COMMENT_UPDATED,
        HELPER_ADDED,
        HELPER_REMOVED,
        RUN_FORCE_CONFIRMED,
        SHOPPING_STARTED,
        ADJUSTING_FINISHED,
        READY_TOGGLED_RUN_CONFIRMED,
    ],
    'Bids': [
        BID_PLACED,
        BID_UPDATED,
        BID_RETRACTED,
        READY_TOGGLED,
    ],
    'Shopping': [
        ITEM_MARKED_PURCHASED,
        ITEM_MARKED_UNPURCHASED,
        PRICE_UPDATED,
        ADDITIONAL_PURCHASE_ADDED,
        SHOPPING_COMPLETED,
        SHOPPING_COMPLETED_NO_PURCHASES,
        SHOPPING_COMPLETED_ADJUSTING_REQUIRED,
        SHOPPING_COMPLETED_DISTRIBUTING,
    ],
    'Distribution': [
        BID_MARKED_PICKED_UP,
        BID_MARKED_NOT_PICKED_UP,
        DISTRIBUTION_UPDATED,
        DISTRIBUTION_COMPLETED,
    ],
    'Groups': [
        GROUP_CREATED,
        GROUP_UPDATED,
        GROUP_DELETED,
        GROUP_JOINED,
        GROUP_LEFT,
        MEMBER_REMOVED,
        MEMBER_PROMOTED,
        INVITE_TOKEN_REGENERATED,
        GROUP_JOINING_TOGGLED,
    ],
    'Notifications': [
        NOTIFICATION_MARKED_READ,
        NOTIFICATIONS_MARKED_READ,
        NOTIFICATION_DELETED,
    ],
    'Reassignment': [
        REASSIGNMENT_REQUEST_CREATED,
        REASSIGNMENT_REQUEST_ACCEPTED,
        REASSIGNMENT_REQUEST_DECLINED,
        REASSIGNMENT_REQUEST_CANCELLED,
    ],
    'Products & Stores': [
        PRODUCT_CREATED,
        PRODUCT_UPDATED,
        PRODUCT_DELETED,
        PRODUCT_VERIFIED,
        PRODUCT_UNVERIFIED,
        PRODUCTS_MERGED,
        STORE_CREATED,
        STORE_UPDATED,
        STORE_DELETED,
        STORE_VERIFIED,
        STORE_UNVERIFIED,
        STORES_MERGED,
    ],
    'Admin': [
        USER_ADMIN_STATUS_UPDATED,
        USER_DELETED,
        USER_VERIFIED,
        USER_UNVERIFIED,
    ],
}
