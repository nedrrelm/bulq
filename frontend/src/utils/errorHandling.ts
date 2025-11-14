import { ApiError } from '../api'
import { translateError } from './translation'

/**
 * Standardized error handling utilities
 *
 * This module provides consistent error handling across the application.
 * All error handling should use these utilities to ensure consistent
 * user-facing messages and proper logging.
 */

/**
 * Extract a user-friendly error message from any error type
 *
 * @param error - The error object (can be Error, ApiError, string, or unknown)
 * @param fallback - Default message if error cannot be parsed
 * @returns A user-friendly error message string
 *
 * @example
 * ```typescript
 * try {
 *   await apiCall()
 * } catch (err) {
 *   const message = getErrorMessage(err, 'Failed to load data')
 *   showToast(message, 'error')
 * }
 * ```
 */
export function getErrorMessage(error: unknown, fallback = 'An unexpected error occurred'): string {
  if (error instanceof ApiError) {
    // Use translated error code if available
    if (error.code) {
      return translateError(error.code, error.details)
    }
    // Fallback to raw message for backward compatibility
    return error.message
  }

  if (error instanceof Error) {
    return error.message
  }

  if (typeof error === 'string') {
    return error
  }

  return fallback
}

/**
 * Log error to console with context information
 *
 * @param context - Description of where/when the error occurred
 * @param error - The error object to log
 *
 * @example
 * ```typescript
 * logError('Fetch user data', error)
 * // Output: [Fetch user data] Error: Network failure
 * ```
 */
export function logError(context: string, error: unknown): void {
  console.error(`[${context}]`, error)
}

/**
 * Handle error with logging and return user-friendly message
 *
 * Combines logging and message extraction in one call for convenience.
 *
 * @param context - Description of where/when the error occurred
 * @param error - The error object
 * @param fallback - Optional fallback message
 * @returns User-friendly error message
 *
 * @example
 * ```typescript
 * const message = handleError('Save settings', error, 'Failed to save')
 * showToast(message, 'error')
 * ```
 */
export function handleError(context: string, error: unknown, fallback?: string): string {
  logError(context, error)
  return getErrorMessage(error, fallback)
}

/**
 * Check if error indicates authentication failure
 */
export function isAuthError(error: unknown): boolean {
  if (error instanceof ApiError) {
    return error.status === 401 || error.status === 403
  }
  return false
}

/**
 * Check if error indicates network failure
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof Error) {
    return error.message.includes('network') ||
           error.message.includes('fetch') ||
           error.message.includes('offline')
  }
  return false
}

/**
 * Format error for display in toast/alert
 */
export function formatErrorForDisplay(error: unknown, action: string): string {
  const message = getErrorMessage(error)

  if (isNetworkError(error)) {
    return `Network error while ${action}. Please check your connection and try again.`
  }

  if (isAuthError(error)) {
    return 'Your session has expired. Please log in again.'
  }

  return `Failed to ${action}: ${message}`
}
