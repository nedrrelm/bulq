import { ApiError } from '../api'

/**
 * Standardized error handling utilities
 */

/**
 * Extract a user-friendly error message from any error type
 */
export function getErrorMessage(error: unknown, fallback = 'An unexpected error occurred'): string {
  if (error instanceof ApiError) {
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
 * Log error to console with context
 */
export function logError(context: string, error: unknown): void {
  console.error(`[${context}]`, error)
}

/**
 * Handle error with logging and return user-friendly message
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
