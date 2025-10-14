// Validation utility functions

export interface ValidationResult {
  isValid: boolean
  error?: string
}

/**
 * Validate a required field
 */
export function validateRequired(value: string | number, fieldName: string = 'This field'): ValidationResult {
  const strValue = String(value).trim()
  if (!strValue || strValue.length === 0) {
    return { isValid: false, error: `${fieldName} is required` }
  }
  return { isValid: true }
}

/**
 * Validate string length
 */
export function validateLength(
  value: string,
  min: number,
  max: number,
  fieldName: string = 'This field'
): ValidationResult {
  const trimmed = value.trim()

  if (trimmed.length < min) {
    return { isValid: false, error: `${fieldName} must be at least ${min} characters` }
  }

  if (trimmed.length > max) {
    return { isValid: false, error: `${fieldName} must be at most ${max} characters` }
  }

  return { isValid: true }
}

/**
 * Validate a decimal number
 */
export function validateDecimal(
  value: string | number,
  min: number,
  max: number,
  maxDecimals: number = 2,
  fieldName: string = 'Value'
): ValidationResult {
  const numValue = typeof value === 'string' ? parseFloat(value) : value

  if (isNaN(numValue)) {
    return { isValid: false, error: `${fieldName} must be a valid number` }
  }

  if (numValue < min) {
    return { isValid: false, error: `${fieldName} must be at least ${min}` }
  }

  if (numValue > max) {
    return { isValid: false, error: `${fieldName} must be at most ${max}` }
  }

  // Check decimal places
  const decimalPart = String(value).split('.')[1]
  if (decimalPart && decimalPart.length > maxDecimals) {
    return { isValid: false, error: `${fieldName} can have at most ${maxDecimals} decimal places` }
  }

  return { isValid: true }
}

/**
 * Validate alphanumeric with allowed special characters
 */
export function validateAlphanumeric(
  value: string,
  allowedChars: string = '- _&\'',
  fieldName: string = 'This field'
): ValidationResult {
  const pattern = new RegExp(`^[a-zA-Z0-9${allowedChars.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s]+$`)

  if (!pattern.test(value.trim())) {
    return { isValid: false, error: `${fieldName} contains invalid characters` }
  }

  return { isValid: true }
}

/**
 * Format a number to a specific decimal precision
 */
export function formatDecimal(value: number | string, decimals: number = 2): string {
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return ''
  return num.toFixed(decimals)
}

/**
 * Parse a safe decimal from user input
 */
export function parseDecimal(value: string): number {
  const cleaned = value.trim()
  const num = parseFloat(cleaned)
  return isNaN(num) ? 0 : num
}

/**
 * Sanitize string for safe display (trim and limit length)
 */
export function sanitizeString(value: string, maxLength: number = 255): string {
  return value.trim().slice(0, maxLength)
}

/**
 * Debounce function for input handlers
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null
      func(...args)
    }

    if (timeout) {
      clearTimeout(timeout)
    }
    timeout = setTimeout(later, wait)
  }
}
