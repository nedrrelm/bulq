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
 * @param value - The string value to validate
 * @param allowedChars - Additional characters to allow (e.g., '- _&\'')
 * @param fieldName - The field name for error messages
 * @param allowUnicode - Whether to allow unicode letters and numbers (default: false)
 */
export function validateAlphanumeric(
  value: string,
  allowedChars: string = '- _&\'',
  fieldName: string = 'This field',
  allowUnicode: boolean = false
): ValidationResult {
  const trimmed = value.trim()

  if (allowUnicode) {
    // Use alternation: unicode letter OR unicode number OR allowed special char OR whitespace
    // \p{L} = any unicode letter, \p{N} = any unicode number
    // Must use alternation because \p{} cannot be used inside character classes with other chars
    const escapedChars = allowedChars.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const pattern = new RegExp(`^(\\p{L}|\\p{N}|[${escapedChars}\\s])+$`, 'u')

    if (!pattern.test(trimmed)) {
      return { isValid: false, error: `${fieldName} contains invalid characters` }
    }
  } else {
    // Original ASCII-only pattern
    const escapedChars = allowedChars.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const pattern = new RegExp(`^[a-zA-Z0-9${escapedChars}\\s]+$`)

    if (!pattern.test(trimmed)) {
      return { isValid: false, error: `${fieldName} contains invalid characters` }
    }
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
