# i18n Setup Complete

This document describes the internationalization (i18n) infrastructure that has been set up for the Bulq frontend.

## What Was Done

### 1. Packages Installed
- `i18next` - Core i18n library
- `react-i18next` - React bindings for i18next

### 2. Files Created

#### Configuration
- **`src/i18n/config.ts`** - i18next initialization and configuration
  - Sets up English as default language
  - Configures namespaces for errors, success, and common translations
  - Imports translation files

#### Translation Files
- **`src/i18n/locales/en/errors.json`** - Error code translations
  - Organized by category (auth, run, bid, group, etc.)
  - Includes placeholder examples for all major error types
  - Supports interpolation (e.g., `{{min_length}}`, `{{user_id}}`)

- **`src/i18n/locales/en/success.json`** - Success code translations
  - Organized by category (auth, run, bid, group, etc.)
  - Includes success messages for all major operations

- **`src/i18n/locales/en/common.json`** - Common UI text
  - Actions (save, cancel, delete, etc.)
  - Validation messages
  - General UI states

#### Utilities
- **`src/utils/translation.ts`** - Translation helper functions
  - `translateError(code, details)` - Translate error codes to messages
  - `translateSuccess(code, details)` - Translate success codes to messages
  - `t(key, params)` - Translate common UI text
  - Automatic code-to-key mapping logic
  - Fallback to formatted code if translation missing

### 3. Files Modified

#### API Client
- **`src/api/client.ts`** - Enhanced ApiError class
  - Added `code` and `details` fields to ApiError
  - Extracts error code from backend response: `{ success: false, code: "ERROR_CODE", details: {...} }`
  - Maintains backward compatibility with `message` field

#### Error Handling
- **`src/utils/errorHandling.ts`** - Updated to use translations
  - `getErrorMessage()` now translates error codes when available
  - Falls back to raw message for backward compatibility

#### App Entry Point
- **`src/main.tsx`** - Imports i18n config
  - Ensures i18n is initialized before app starts

## How It Works

### Backend → Frontend Flow

1. **Backend sends error/success response:**
```json
{
  "success": false,
  "code": "AUTH_INVALID_CREDENTIALS",
  "message": "Invalid credentials",
  "details": {}
}
```

2. **API client extracts code:**
```typescript
throw new ApiError(message, status, code, details, data)
```

3. **Error handling translates code:**
```typescript
getErrorMessage(error) // Returns translated message
```

4. **Translation function maps code to key:**
```typescript
AUTH_INVALID_CREDENTIALS → errors:auth.invalid_credentials
```

5. **i18next looks up translation:**
```json
{
  "auth": {
    "invalid_credentials": "Invalid username or password"
  }
}
```

### Using Translations in Components

```typescript
import { translateError, translateSuccess, t } from '../utils/translation'

// Error handling
try {
  await api.someAction()
} catch (err) {
  const message = getErrorMessage(err) // Automatically translates
  showToast(message, 'error')
}

// Direct translation
const errorMsg = translateError('BID_QUANTITY_NEGATIVE')
const successMsg = translateSuccess('BID_PLACED')
const buttonText = t('actions.save')
```

## Next Steps

### Phase 2: Update Components
- Replace hardcoded `error.message` usage with `getErrorMessage(error)`
- Update success message handling to use translated codes
- ~100 component files need updates

### Phase 3: Complete Translation Files
- Add all 226+ error codes from `backend/app/core/error_codes.py`
- Add all 60+ success codes from `backend/app/core/success_codes.py`
- Verify all translations match backend codes

### Phase 4: Add More Languages
- Create `src/i18n/locales/ru/` for Russian translations
- Create `src/i18n/locales/sr/` for Serbian translations
- Add language switcher component
- Update config to load new languages

## Translation Key Mapping Logic

### Error Codes
- `AUTH_INVALID_CREDENTIALS` → `errors:auth.invalid_credentials`
- `RUN_NOT_FOUND` → `errors:not_found.run`
- `BID_QUANTITY_NEGATIVE` → `errors:bid.quantity_negative`
- `CANNOT_MODIFY_CANCELLED_RUN` → `errors:run_actions.cannot_modify_cancelled_run`

### Success Codes
- `BID_PLACED` → `success:bid.placed`
- `RUN_CREATED` → `success:run.created`
- `USER_LOGGED_IN` → `success:auth.user_logged_in`
- `MEMBER_PROMOTED` → `success:group.member_promoted`

## Benefits

✅ **Language-agnostic backend** - Backend already returns machine-readable codes
✅ **Easy to add languages** - Just add new translation files
✅ **Type-safe** - TypeScript support throughout
✅ **Backward compatible** - Falls back to message field if no translation
✅ **Developer-friendly** - Clear warnings for missing translations in dev mode
✅ **Interpolation support** - Dynamic values like `{{user_name}}` work out of the box

## Testing

The build completes successfully with no TypeScript errors. The translation infrastructure is ready to use.

To test:
1. Component will catch ApiError with code
2. `getErrorMessage()` will translate the code
3. User sees localized message instead of raw backend message
