import i18n from '../i18n/config'

/**
 * Translation utilities for error and success codes
 *
 * These functions translate backend error/success codes into user-friendly messages
 * with support for interpolation of dynamic values.
 */

/**
 * Convert error code to translation key
 *
 * Examples:
 * - AUTH_INVALID_CREDENTIALS → auth.invalid_credentials
 * - RUN_NOT_FOUND → not_found.run
 * - BID_QUANTITY_NEGATIVE → bid.quantity_negative
 */
function errorCodeToKey(code: string): string {
  const lowerCode = code.toLowerCase()

  // Handle special cases for NOT_FOUND errors
  if (lowerCode.endsWith('_not_found')) {
    const resource = lowerCode.replace('_not_found', '')
    return `not_found.${resource}`
  }

  // Handle prefixed codes (e.g., AUTH_*, RUN_*, BID_*)
  const parts = lowerCode.split('_')

  // Identify common prefixes
  const prefixes = ['auth', 'run', 'bid', 'group', 'product', 'store', 'shopping',
                    'distribution', 'notification', 'reassignment', 'password', 'helper']

  const firstPart = parts[0]
  if (firstPart && prefixes.includes(firstPart)) {
    const prefix = firstPart
    const rest = parts.slice(1).join('_')
    return `${prefix}.${rest}`
  }

  // Handle special error categories
  if (lowerCode.startsWith('not_')) {
    return `permissions.${parts.slice(1).join('_')}`
  }

  if (lowerCode.startsWith('invalid_')) {
    return `validation.${parts.slice(1).join('_')}`
  }

  if (lowerCode.startsWith('cannot_')) {
    // Try to infer category from the rest of the code
    if (lowerCode.includes('group')) return `group.${parts.join('_')}`
    if (lowerCode.includes('run')) return `run_actions.${parts.join('_')}`
    if (lowerCode.includes('bid')) return `bid.${parts.join('_')}`
    if (lowerCode.includes('admin')) return `admin.${parts.join('_')}`
    return `generic.${parts.join('_')}`
  }

  if (lowerCode.includes('registration')) {
    return `registration.${parts.slice(1).join('_')}`
  }

  if (lowerCode.includes('state')) {
    return `run_state.${parts.filter(p => p !== 'run').join('_')}`
  }

  // Generic fallback
  return `generic.${lowerCode}`
}

/**
 * Convert success code to translation key
 *
 * Examples:
 * - BID_PLACED → bid.placed
 * - RUN_CREATED → run.created
 * - USER_LOGGED_IN → auth.user_logged_in
 */
function successCodeToKey(code: string): string {
  const parts = code.toLowerCase().split('_')

  // Identify common prefixes
  const prefixes = ['user', 'run', 'bid', 'group', 'product', 'store', 'shopping',
                    'distribution', 'notification', 'reassignment', 'helper', 'password']

  const firstPart = parts[0]
  if (firstPart && prefixes.includes(firstPart)) {
    // Special handling for USER_* auth codes
    if (firstPart === 'user' && ['registered', 'logged', 'admin'].some(p => parts.includes(p))) {
      return `auth.${parts.join('_')}`
    }

    const prefix = firstPart
    const rest = parts.slice(1).join('_')
    return `${prefix}.${rest}`
  }

  // Generic success codes
  if (firstPart && ['operation', 'resource'].includes(firstPart)) {
    return `general.${parts.join('_')}`
  }

  // Fallback
  return `general.${code.toLowerCase()}`
}

/**
 * Translate error code to user-friendly message
 *
 * @param code - Error code from backend (e.g., 'AUTH_INVALID_CREDENTIALS')
 * @param details - Optional details object for interpolation (e.g., { min_length: 8 })
 * @returns Translated error message
 *
 * @example
 * translateError('AUTH_INVALID_CREDENTIALS')
 * // => "Invalid username or password"
 *
 * translateError('PASSWORD_TOO_SHORT', { min_length: 8 })
 * // => "Password must be at least 8 characters"
 */
export function translateError(code: string | undefined, details?: Record<string, any>): string {
  if (!code) {
    return i18n.t('errors:generic.unknown_error')
  }

  const key = errorCodeToKey(code)

  // Try translation with interpolation values
  const translated = i18n.t(`errors:${key}`, details)

  // If translation exists and is not just the key, return it
  if (i18n.exists(`errors:${key}`)) {
    return translated
  }

  // Fallback: return a formatted version of the code
  if (import.meta.env.DEV) {
    console.warn(`Missing error translation for code: ${code} (key: errors:${key})`)
  }

  // Return human-readable version of code as fallback
  return code.split('_').map(word =>
    word.charAt(0) + word.slice(1).toLowerCase()
  ).join(' ')
}

/**
 * Translate success code to user-friendly message
 *
 * @param code - Success code from backend (e.g., 'BID_PLACED')
 * @param details - Optional details object for interpolation (e.g., { member_name: 'John' })
 * @returns Translated success message
 *
 * @example
 * translateSuccess('BID_PLACED')
 * // => "Bid placed successfully"
 *
 * translateSuccess('MEMBER_PROMOTED', { member_name: 'John' })
 * // => "John is now a group admin"
 */
export function translateSuccess(code: string | undefined, details?: Record<string, any>): string {
  if (!code) {
    return i18n.t('success:general.operation_successful')
  }

  const key = successCodeToKey(code)

  // Try translation with interpolation values
  const translated = i18n.t(`success:${key}`, details)

  // If translation exists and is not just the key, return it
  if (i18n.exists(`success:${key}`)) {
    return translated
  }

  // Fallback: return a formatted version of the code
  if (import.meta.env.DEV) {
    console.warn(`Missing success translation for code: ${code} (key: success:${key})`)
  }

  // Return human-readable version of code as fallback
  return code.split('_').map(word =>
    word.charAt(0) + word.slice(1).toLowerCase()
  ).join(' ')
}

/**
 * Translate common UI text
 *
 * @param key - Translation key in common namespace (e.g., 'actions.save')
 * @param params - Optional interpolation parameters
 * @returns Translated text
 */
export function t(key: string, params?: Record<string, any>): string {
  return i18n.t(`common:${key}`, params)
}
