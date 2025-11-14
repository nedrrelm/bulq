# Error Codes Reference

This document lists all error codes returned by the Bulq API. These codes should be used by the frontend for localization and user-friendly error messages.

## Error Response Format

All API errors follow this structure:

```json
{
  "success": false,
  "error": "NotFoundError",
  "code": "RUN_NOT_FOUND",
  "message": "Run not found",  // For backward compatibility, don't use for UI
  "details": {
    "run_id": "123e4567-e89b-12d3-a456-426614174000"
  },
  "timestamp": "2025-10-06T12:34:56.789Z",
  "path": "/api/runs/123"
}
```

**Important:** The `message` field is kept for backward compatibility and logging but should NOT be displayed to users. Always use the `code` field for frontend localization.

## Translation Key Mapping

Error codes map directly to translation keys. Recommended format:

```
ERROR_CODE → errors.{domain}.{error_name}

Examples:
AUTH_INVALID_CREDENTIALS → errors.auth.invalid_credentials
RUN_NOT_FOUND → errors.run.not_found
BID_QUANTITY_NEGATIVE → errors.bid.quantity_negative
```

## Error Codes by Category

### Authentication & Authorization

#### Authentication (HTTP 401)
| Code | HTTP Status | Description | Details |
|------|-------------|-------------|---------|
| `AUTH_REQUIRED` | 401 | User must be authenticated | - |
| `AUTH_INVALID_CREDENTIALS` | 401 | Email or password is incorrect | - |
| `AUTH_SESSION_EXPIRED` | 401 | Session has expired | - |

#### Registration (HTTP 400/409)
| Code | HTTP Status | Description | Details |
|------|-------------|-------------|---------|
| `REGISTRATION_DISABLED` | 400 | Registration is not allowed | - |
| `USERNAME_TAKEN` | 409 | Username already registered | `username` |
| `EMAIL_TAKEN` | 409 | Email already registered | `email` |
| `PASSWORD_TOO_SHORT` | 422 | Password doesn't meet minimum length | `min_length` |
| `PASSWORD_TOO_WEAK` | 422 | Password doesn't meet complexity requirements | - |

#### Password Management (HTTP 400/422)
| Code | HTTP Status | Description | Details |
|------|-------------|-------------|---------|
| `PASSWORD_MISMATCH` | 422 | Passwords do not match | - |
| `PASSWORD_INCORRECT` | 400 | Current password is incorrect | - |
| `PASSWORD_SAME_AS_OLD` | 422 | New password must differ from old | - |

#### Permissions (HTTP 403)
| Code | HTTP Status | Description | Details |
|------|-------------|-------------|---------|
| `INSUFFICIENT_PERMISSIONS` | 403 | User lacks required permissions | - |
| `NOT_GROUP_MEMBER` | 403 | User is not a member of the group | `group_id` |
| `NOT_GROUP_ADMIN` | 403 | User is not a group admin | `group_id` |
| `NOT_RUN_PARTICIPANT` | 403 | User is not participating in the run | `run_id` |
| `NOT_RUN_LEADER` | 403 | User is not the run leader | `run_id` |
| `NOT_RUN_LEADER_OR_HELPER` | 403 | User is neither run leader nor helper | `run_id` |
| `NOT_SYSTEM_ADMIN` | 403 | User is not a system admin | - |

---

### Resource Not Found (HTTP 404)

| Code | Description | Details |
|------|-------------|---------|
| `USER_NOT_FOUND` | User does not exist | `user_id` |
| `GROUP_NOT_FOUND` | Group does not exist | `group_id` |
| `RUN_NOT_FOUND` | Run does not exist | `run_id` |
| `STORE_NOT_FOUND` | Store does not exist | `store_id` |
| `PRODUCT_NOT_FOUND` | Product does not exist | `product_id` |
| `BID_NOT_FOUND` | Bid does not exist | `bid_id` |
| `PARTICIPATION_NOT_FOUND` | Participation record not found | `participation_id` |
| `SHOPPING_LIST_ITEM_NOT_FOUND` | Shopping list item not found | `item_id` |
| `NOTIFICATION_NOT_FOUND` | Notification not found | `notification_id` |
| `REASSIGNMENT_REQUEST_NOT_FOUND` | Reassignment request not found | `request_id` |
| `PRODUCT_AVAILABILITY_NOT_FOUND` | Product availability not found | `availability_id` |

---

### Run State & Lifecycle

#### State Transitions (HTTP 422)
| Code | Description | Details |
|------|-------------|---------|
| `INVALID_RUN_STATE_TRANSITION` | Cannot transition between these states | `current_state`, `target_state` |
| `RUN_NOT_IN_PLANNING_STATE` | Action requires run to be in planning state | `current_state` |
| `RUN_NOT_IN_ACTIVE_STATE` | Action requires run to be in active state | `current_state` |
| `RUN_NOT_IN_CONFIRMED_STATE` | Action requires run to be in confirmed state | `current_state` |
| `RUN_NOT_IN_SHOPPING_STATE` | Action requires run to be in shopping state | `current_state` |
| `RUN_NOT_IN_ADJUSTING_STATE` | Action requires run to be in adjusting state | `current_state` |
| `RUN_NOT_IN_DISTRIBUTING_STATE` | Action requires run to be in distributing state | `current_state` |
| `RUN_ALREADY_CANCELLED` | Run has been cancelled | `run_id` |
| `RUN_ALREADY_COMPLETED` | Run has been completed | `run_id` |
| `CANNOT_CANCEL_COMPLETED_RUN` | Cannot cancel a completed run | `run_id` |

#### Run Actions (HTTP 400/422)
| Code | Description | Details |
|------|-------------|---------|
| `CANNOT_JOIN_RUN_IN_ADJUSTING_STATE` | Cannot join run during adjustment | `run_id` |
| `CANNOT_MODIFY_CANCELLED_RUN` | Cannot modify a cancelled run | `run_id` |
| `CANNOT_MODIFY_COMPLETED_RUN` | Cannot modify a completed run | `run_id` |
| `RUN_MAX_PRODUCTS_EXCEEDED` | Too many products in run | `max_products`, `current_count` |
| `RUN_EXPORT_INVALID_STATE` | Cannot export run in current state | `current_state` |

---

### Bids & Shopping

#### Bid Validation (HTTP 422)
| Code | Description | Details |
|------|-------------|---------|
| `BID_QUANTITY_NEGATIVE` | Bid quantity cannot be negative | `quantity` |
| `BID_QUANTITY_EXCEEDS_PURCHASED` | Bid exceeds purchased quantity | `bid_quantity`, `purchased_quantity` |
| `BID_QUANTITY_BELOW_DISTRIBUTED` | Cannot reduce below distributed amount | `bid_quantity`, `distributed_quantity` |
| `BID_PRODUCT_NOT_IN_SHOPPING_LIST` | Product not on shopping list | `product_id` |
| `CANNOT_BID_NEW_PRODUCT_IN_ADJUSTING` | Cannot add new products during adjustment | `product_id` |
| `CANNOT_RETRACT_BID_IN_ADJUSTING` | Cannot retract bids during adjustment | `bid_id` |

#### Shopping Actions (HTTP 409/422)
| Code | Description | Details |
|------|-------------|---------|
| `SHOPPING_ITEM_ALREADY_PURCHASED` | Item already marked as purchased | `item_id` |
| `SHOPPING_ITEM_NOT_PURCHASED` | Item not yet purchased | `item_id` |
| `CANNOT_ADD_MORE_TO_UNPURCHASED_ITEM` | Cannot increase unpurchased items | `item_id` |

---

### Distribution (HTTP 422)

| Code | Description | Details |
|------|-------------|---------|
| `DISTRIBUTION_TOTAL_EXCEEDS_PURCHASED` | Total distribution exceeds purchased quantity | `total_distributed`, `purchased_quantity` |
| `BID_ALREADY_PICKED_UP` | Bid already marked as picked up | `bid_id` |
| `BID_NOT_PICKED_UP` | Bid not marked as picked up | `bid_id` |
| `CANNOT_COMPLETE_DISTRIBUTION_UNPURCHASED_ITEMS` | Cannot complete with unpurchased items | `unpurchased_count` |

---

### Groups

#### Group Membership (HTTP 403/409/422)
| Code | Description | Details |
|------|-------------|---------|
| `GROUP_JOINING_DISABLED` | Group is not accepting new members | `group_id` |
| `ALREADY_GROUP_MEMBER` | User is already a member | `group_id`, `user_id` |
| `NOT_A_GROUP_MEMBER` | User is not a group member | `group_id`, `user_id` |
| `USER_MAX_GROUPS_EXCEEDED` | User has joined too many groups | `max_groups` |
| `GROUP_MAX_MEMBERS_EXCEEDED` | Group has too many members | `max_members` |
| `CANNOT_REMOVE_GROUP_ADMIN` | Cannot remove group admin | `user_id` |
| `CANNOT_REMOVE_SELF_AS_ADMIN` | Cannot remove own admin status | - |
| `LAST_ADMIN_CANNOT_LEAVE` | Last admin cannot leave group | `group_id` |
| `USER_ALREADY_GROUP_ADMIN` | User is already a group admin | `user_id` |

#### Group Operations (HTTP 400/500)
| Code | Description | Details |
|------|-------------|---------|
| `GROUP_INVITE_TOKEN_REGENERATION_FAILED` | Failed to regenerate invite token | `group_id` |
| `GROUP_JOIN_FAILED` | Failed to join group | `group_id` |
| `GROUP_MEMBER_REMOVAL_FAILED` | Failed to remove member | `group_id`, `user_id` |
| `GROUP_MEMBER_PROMOTION_FAILED` | Failed to promote member | `group_id`, `user_id` |
| `GROUP_JOINING_SETTING_UPDATE_FAILED` | Failed to update joining setting | `group_id` |

---

### Leader Reassignment (HTTP 403/409/422)

| Code | Description | Details |
|------|-------------|---------|
| `REASSIGNMENT_NOT_CURRENT_LEADER` | Only current leader can reassign | `run_id`, `user_id` |
| `REASSIGNMENT_TARGET_NOT_PARTICIPANT` | Target user not a participant | `run_id`, `target_user_id` |
| `REASSIGNMENT_CANNOT_TRANSFER_TO_SELF` | Cannot transfer to yourself | `run_id` |
| `REASSIGNMENT_REQUEST_ALREADY_EXISTS` | Pending request already exists | `request_id` |
| `REASSIGNMENT_REQUEST_ALREADY_RESOLVED` | Request already resolved | `request_id`, `status` |
| `REASSIGNMENT_NOT_TARGET_USER` | Only target user can respond | `request_id`, `user_id` |
| `REASSIGNMENT_INVALID_ACTION` | Invalid action for request | `action` |
| `REASSIGNMENT_INVALID_RUN_STATE` | Cannot reassign in current state | `current_state` |

---

### Products & Stores

#### Product Validation (HTTP 422)
| Code | Description | Details |
|------|-------------|---------|
| `PRODUCT_NAME_EMPTY` | Product name cannot be empty | - |
| `PRODUCT_PRICE_NEGATIVE` | Product price cannot be negative | `price` |
| `PRODUCT_PRICE_ZERO` | Product price cannot be zero | `price` |

#### Store Validation (HTTP 422)
| Code | Description | Details |
|------|-------------|---------|
| `STORE_NAME_EMPTY` | Store name cannot be empty | - |

#### Admin Operations (HTTP 409/422)
| Code | Description | Details |
|------|-------------|---------|
| `CANNOT_MERGE_SAME_PRODUCT` | Cannot merge product with itself | `product_id` |
| `CANNOT_MERGE_SAME_STORE` | Cannot merge store with itself | `store_id` |
| `PRODUCT_HAS_ACTIVE_BIDS` | Cannot delete product with active bids | `product_id`, `bid_count` |
| `STORE_HAS_ACTIVE_RUNS` | Cannot delete store with active runs | `store_id`, `run_count` |

---

### Admin & User Management (HTTP 403)

| Code | Description | Details |
|------|-------------|---------|
| `CANNOT_DELETE_OWN_ACCOUNT` | Cannot delete your own account | `user_id` |
| `CANNOT_DELETE_ADMIN_USER` | Cannot delete admin users | `user_id` |
| `CANNOT_REMOVE_OWN_ADMIN_STATUS` | Cannot remove own admin status | `user_id` |

---

### Notifications (HTTP 403)

| Code | Description | Details |
|------|-------------|---------|
| `NOTIFICATION_MARK_READ_FAILED` | Failed to mark notification as read | `notification_id` |
| `NOT_NOTIFICATION_OWNER` | User does not own this notification | `notification_id` |

---

### Validation & Format Errors (HTTP 400/422)

| Code | Description | Details |
|------|-------------|---------|
| `INVALID_ID_FORMAT` | ID format is invalid | `field`, `value` |
| `INVALID_UUID_FORMAT` | UUID format is invalid | `field`, `value` |
| `INVALID_DATE_FORMAT` | Date format is invalid | `field`, `value` |
| `INVALID_REQUEST_FORMAT` | Request format is invalid | - |

**Note:** `INVALID_UUID_FORMAT` is raised by the `validate_uuid()` utility function in `app/utils/validation.py` when a string cannot be parsed as a valid UUID. The `field` detail indicates which resource type was being validated (e.g., "run", "group", "user").

---

### Helper Errors (HTTP 403/422)

| Code | Description | Details |
|------|-------------|---------|
| `CANNOT_ASSIGN_LEADER_AS_HELPER` | Leader cannot be assigned as helper | `user_id`, `run_id` |
| `HELPER_NOT_GROUP_MEMBER` | Helper must be a group member | `user_id`, `group_id` |

---

### Configuration & System Errors (HTTP 500)

| Code | Description | Details |
|------|-------------|---------|
| `DATABASE_SESSION_REQUIRED` | Database session not provided when required | `repo_mode` |
| `INVALID_REPO_MODE` | Invalid repository mode configured | `repo_mode` |
| `CONFIGURATION_ERROR` | Generic configuration error | Varies |

**Note:** These are internal server errors that indicate misconfiguration. They should not occur in normal operation and usually require fixes to environment variables or application setup.

---

## Validation Utilities

The `app/utils/validation.py` module provides helper functions that automatically use error codes:

### `validate_uuid(id_str: str, resource_name: str) -> UUID`

Validates and converts a string to UUID format.

**Raises:**
- `INVALID_UUID_FORMAT` (HTTP 400) - When the string is not a valid UUID

**Details returned:**
- `field`: Resource type (lowercase of resource_name, e.g., "run", "group")
- `value`: The invalid string that was provided

**Example usage:**
```python
from app.utils.validation import validate_uuid

run_uuid = validate_uuid(run_id, 'Run')  # Raises INVALID_UUID_FORMAT if invalid
```

### State Machine Validation

For state transition validation, use the state machine directly:

```python
from app.core.run_state import RunState, state_machine

# Validate a state transition (raises BadRequestError if invalid)
state_machine.validate_transition(RunState.ACTIVE, RunState.CONFIRMED, run_id=str(run.id))
```

**Raises:**
- `INVALID_RUN_STATE_TRANSITION` (HTTP 422) - When transition is not allowed

**Details returned:**
- `current_state`: The current state
- `target_state`: The requested target state
- `allowed_states`: Comma-separated list of valid transitions from current state

---

## Notification Types

Notifications use structured data for frontend rendering. All notification types:

### `run_state_changed`

Run state has changed.

**Data structure:**
```typescript
{
  run_id: string
  store_name: string
  old_state: string
  new_state: string
  group_id: string
}
```

### `leader_reassignment_request`

Run leader has requested to transfer leadership.

**Data structure:**
```typescript
{
  run_id: string
  from_user_id: string
  from_user_name: string
  request_id: string
  store_name: string
}
```

### `leader_reassignment_accepted`

Leadership transfer request has been accepted.

**Data structure:**
```typescript
{
  run_id: string
  new_leader_id: string
  new_leader_name: string
  store_name: string
}
```

### `leader_reassignment_declined`

Leadership transfer request has been declined.

**Data structure:**
```typescript
{
  run_id: string
  declined_by_id: string
  declined_by_name: string
  store_name: string
}
```

---

## WebSocket Message Types

WebSocket messages use structured data for real-time updates.

### `bid_updated`

A user placed or updated a bid.

**Data structure:**
```typescript
{
  product_id: string
  user_id: string
  user_name: string
  quantity: number
  interested_only: boolean
  new_total: number
}
```

### `bid_retracted`

A user retracted their bid.

**Data structure:**
```typescript
{
  product_id: string
  user_id: string
  new_total: number
}
```

### `ready_toggled`

A user toggled their ready status.

**Data structure:**
```typescript
{
  user_id: string
  is_ready: boolean
}
```

### `state_changed`

Run state changed (sent to run room).

**Data structure:**
```typescript
{
  run_id: string
  new_state: string
}
```

### `run_state_changed`

Run state changed (sent to group room).

**Data structure:**
```typescript
{
  run_id: string
  new_state: string
}
```

### `run_created`

A new run was created.

**Data structure:**
```typescript
{
  run_id: string
  store_id: string
  store_name: string
  state: string
  leader_name: string
}
```

### `new_notification`

A new notification was created for the user.

**Data structure:**
```typescript
{
  id: string
  type: string  // One of the notification types above
  data: object  // Notification-specific data
  read: boolean
  created_at: string
}
```

---

## Frontend Implementation Guide

### 1. Create Translation Files

```json
// en.json
{
  "errors": {
    "auth": {
      "invalid_credentials": "Invalid email or password",
      "session_expired": "Your session has expired. Please log in again."
    },
    "run": {
      "not_found": "Run not found",
      "invalid_state_transition": "Cannot perform this action in the current state"
    },
    "bid": {
      "quantity_negative": "Quantity cannot be negative",
      "quantity_exceeds_purchased": "Cannot bid more than purchased quantity"
    }
    // ... more translations
  }
}
```

### 2. Error Handler

```typescript
function translateError(error: ApiError): string {
  const key = `errors.${getDomain(error.code)}.${getErrorName(error.code)}`
  return i18n.t(key, error.details)
}

function getDomain(code: string): string {
  if (code.startsWith('AUTH_')) return 'auth'
  if (code.startsWith('RUN_')) return 'run'
  if (code.startsWith('BID_')) return 'bid'
  // ... etc
  return 'general'
}

function getErrorName(code: string): string {
  return code.toLowerCase().replace(/_/g, '.')
}
```

### 3. Usage Example

```typescript
try {
  await api.placeBid(runId, productId, quantity)
} catch (error) {
  const message = translateError(error)
  toast.error(message)
}
```

---

## Notes

1. **Never use the `message` field for UI display** - it's for backward compatibility and internal logging only
2. **Always translate error codes** - this ensures consistent UX across all languages
3. **Use `details` for interpolation** - error details contain dynamic values to include in messages
4. **HTTP status codes remain unchanged** - error codes are supplementary, not replacements for HTTP status codes
5. **All notification and WebSocket data is structured** - no pre-formatted messages, always render on frontend

---

## Migration Guide

If you're updating existing frontend code:

1. Replace all message-based error handling with code-based handling
2. Add translation keys for all error codes
3. Update notification rendering to use structured data
4. Update WebSocket message handlers to use structured data
5. Test all error scenarios to ensure proper localization

---

**Last Updated:** 2025-11-13
**Backend Version:** v1.0.0

---

## Success Response Format

All successful API operations that don't return specific data use this structure:

```json
{
  "success": true,
  "code": "BID_PLACED",
  "details": {
    "run_id": "123e4567-e89b-12d3-a456-426614174000",
    "product_id": "123e4567-e89b-12d3-a456-426614174001",
    "quantity": 5.0
  }
}
```

**Important:** Success responses use machine-readable codes for frontend localization, just like error responses.

---

## Success Codes by Category

### Authentication & User Management

| Code | Description | Details |
|------|-------------|---------|
| `USER_REGISTERED` | User registration completed | `user_id` |
| `USER_LOGGED_IN` | User logged in successfully | `user_id` |
| `USER_LOGGED_OUT` | User logged out successfully | - |
| `PASSWORD_CHANGED` | Password changed successfully | `user_id` |
| `PROFILE_UPDATED` | User profile updated | `user_id` |

---

### Run Management

| Code | Description | Details |
|------|-------------|---------|
| `RUN_CREATED` | Run created successfully | `run_id`, `group_id` |
| `RUN_UPDATED` | Run details updated | `run_id` |
| `RUN_DELETED` | Run deleted/cancelled | `run_id` |
| `RUN_CANCELLED` | Run cancelled | `run_id` |
| `RUN_STATE_CHANGED` | Run state transitioned | `run_id`, `old_state`, `new_state` |
| `RUN_COMMENT_UPDATED` | Run comment/description updated | `run_id` |
| `HELPER_ADDED` | User added as run helper | `run_id`, `user_id`, `is_helper` |
| `HELPER_REMOVED` | User removed as run helper | `run_id`, `user_id`, `is_helper` |

---

### Bid Management

| Code | Description | Details |
|------|-------------|---------|
| `BID_PLACED` | Bid placed or updated | `run_id`, `product_id`, `quantity` |
| `BID_UPDATED` | Bid quantity/details updated | `run_id`, `product_id`, `quantity` |
| `BID_RETRACTED` | Bid retracted/removed | `run_id`, `product_id` |
| `READY_TOGGLED` | User ready status toggled | `run_id`, `user_id`, `is_ready` |

---

### Shopping

| Code | Description | Details |
|------|-------------|---------|
| `ITEM_MARKED_PURCHASED` | Shopping item marked as purchased | `run_id`, `item_id`, `product_id` |
| `ITEM_MARKED_UNPURCHASED` | Shopping item marked as not purchased | `run_id`, `item_id` |
| `PRICE_UPDATED` | Product price updated | `run_id`, `item_id`, `product_id` |
| `ADDITIONAL_PURCHASE_ADDED` | Additional quantity added to purchased item | `run_id`, `item_id`, `product_id`, `additional_quantity` |
| `SHOPPING_COMPLETED` | Shopping phase completed | `run_id`, `new_state` |

---

### Distribution

| Code | Description | Details |
|------|-------------|---------|
| `BID_MARKED_PICKED_UP` | Bid marked as picked up | `run_id`, `bid_id`, `user_id` |
| `BID_MARKED_NOT_PICKED_UP` | Bid marked as not picked up | `run_id`, `bid_id` |
| `DISTRIBUTION_UPDATED` | Distribution quantities updated | `run_id` |
| `DISTRIBUTION_COMPLETED` | Distribution phase completed | `run_id`, `new_state` |

---

### Group Management

| Code | Description | Details |
|------|-------------|---------|
| `GROUP_CREATED` | Group created successfully | `group_id` |
| `GROUP_UPDATED` | Group details updated | `group_id` |
| `GROUP_DELETED` | Group deleted | `group_id` |
| `GROUP_JOINED` | User joined group | `group_id`, `user_id` |
| `GROUP_LEFT` | User left group | `group_id` |
| `MEMBER_REMOVED` | Member removed from group | `group_id`, `member_id` |
| `MEMBER_PROMOTED` | Member promoted to admin | `group_id`, `member_id`, `member_name` |
| `INVITE_TOKEN_REGENERATED` | Group invite token regenerated | `group_id`, `new_token` |
| `GROUP_JOINING_TOGGLED` | Group joining setting toggled | `group_id`, `joining_allowed` |

---

### Notifications

| Code | Description | Details |
|------|-------------|---------|
| `NOTIFICATION_MARKED_READ` | Notification marked as read | `notification_id` |
| `NOTIFICATIONS_MARKED_READ` | All notifications marked as read | `count` |
| `NOTIFICATION_DELETED` | Notification deleted | `notification_id` |

---

### Reassignment

| Code | Description | Details |
|------|-------------|---------|
| `REASSIGNMENT_REQUEST_CREATED` | Leadership transfer request created | `run_id`, `request_id`, `to_user_id` |
| `REASSIGNMENT_REQUEST_ACCEPTED` | Leadership transfer accepted | `run_id`, `request_id`, `new_leader_id` |
| `REASSIGNMENT_REQUEST_DECLINED` | Leadership transfer declined | `run_id`, `request_id` |
| `REASSIGNMENT_REQUEST_CANCELLED` | Leadership transfer request cancelled | `run_id`, `request_id` |

---

### Product & Store Management

| Code | Description | Details |
|------|-------------|---------|
| `PRODUCT_CREATED` | Product created | `product_id` |
| `PRODUCT_UPDATED` | Product details updated | `product_id` |
| `PRODUCT_DELETED` | Product deleted | `product_id` |
| `PRODUCT_VERIFIED` | Product verified by admin | `product_id` |
| `PRODUCT_UNVERIFIED` | Product unverified | `product_id` |
| `PRODUCTS_MERGED` | Products merged | `kept_product_id`, `merged_product_id` |
| `STORE_CREATED` | Store created | `store_id` |
| `STORE_UPDATED` | Store details updated | `store_id` |
| `STORE_DELETED` | Store deleted | `store_id` |
| `STORE_VERIFIED` | Store verified by admin | `store_id` |
| `STORE_UNVERIFIED` | Store unverified | `store_id` |
| `STORES_MERGED` | Stores merged | `kept_store_id`, `merged_store_id` |

---

### Admin Operations

| Code | Description | Details |
|------|-------------|---------|
| `USER_ADMIN_STATUS_UPDATED` | User admin status changed | `user_id`, `is_admin` |
| `USER_DELETED` | User account deleted | `user_id` |

---

## Pydantic Validation Error Codes

Pydantic validators now return machine-readable error codes instead of human-readable messages:

| Code | Description | Triggered By |
|------|-------------|--------------|
| `INVALID_DECIMAL_PLACES` | Number has too many decimal places (max 2) | Quantity, price, total fields |
| `GROUP_NAME_TOO_SHORT` | Group name is too short (min 2 chars) | Group creation/update |
| `GROUP_NAME_TOO_LONG` | Group name is too long (max 100 chars) | Group creation/update |
| `GROUP_NAME_INVALID_CHARACTERS` | Group name contains invalid characters | Group creation/update |

**Note:** Pydantic also uses built-in Field validators for common constraints:
- `gt=0` → "Value must be greater than 0"
- `ge=0` → "Value must be greater than or equal to 0"
- `min_length=X` → "String must be at least X characters"
- `max_length=X` → "String must be at most X characters"
- `pattern=regex` → "String must match pattern"

---

## Frontend Success Code Translation

### Translation Files

```json
// en.json
{
  "success": {
    "bid": {
      "placed": "Bid placed successfully!",
      "retracted": "Bid removed"
    },
    "run": {
      "created": "Run created successfully!",
      "comment_updated": "Comment updated",
      "state_changed": "Run status changed"
    },
    "group": {
      "left": "You left the group",
      "member_removed": "Member removed from group",
      "member_promoted": "{member_name} is now a group admin"
    },
    "auth": {
      "logged_out": "Logged out successfully",
      "password_changed": "Password changed successfully"
    }
    // ... more translations
  }
}
```

### Success Handler Example

```typescript
function translateSuccess(response: SuccessResponse): string {
  const key = `success.${getDomain(response.code)}.${getAction(response.code)}`
  return i18n.t(key, response.details)
}

function getDomain(code: string): string {
  if (code.startsWith('BID_')) return 'bid'
  if (code.startsWith('RUN_')) return 'run'
  if (code.startsWith('GROUP_')) return 'group'
  // ... etc
  return 'general'
}

function getAction(code: string): string {
  return code.toLowerCase().replace(/_/g, '.')
}

// Usage
try {
  const response = await api.placeBid(runId, productId, quantity)
  const message = translateSuccess(response)
  toast.success(message)
} catch (error) {
  const message = translateError(error)
  toast.error(message)
}
```

---

**Last Updated:** 2025-11-13  
**Backend Version:** v2.0.0 - Fully Language-Agnostic
