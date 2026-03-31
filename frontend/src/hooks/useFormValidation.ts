import { useState, useCallback, useMemo } from 'react'
import {
  validateLength,
  validateAlphanumeric,
  validateDecimal,
  validateRequired,
  sanitizeString,
  type ValidationResult
} from '../utils/validation'

// ============================================================================
// Types
// ============================================================================

export type Validator = (value: string) => ValidationResult | string | boolean

export interface FieldConfig {
  value: string
  onChange: (value: string) => void
  validators?: Validator[]
  sanitize?: (value: string) => string
  validateOnBlur?: boolean
}

export interface UseFormValidationOptions {
  // Single field mode
  value?: string
  onChange?: (value: string) => void
  validators?: Validator[]
  sanitize?: (value: string) => string
  validateOnBlur?: boolean

  // Multi-field mode
  fields?: Record<string, FieldConfig>
}

// ============================================================================
// Built-in Validators Library
// ============================================================================

export const validators = {
  /**
   * Validate required field
   */
  required: (message?: string): Validator => (value: string) => {
    const trimmed = value.trim()
    if (!trimmed || trimmed.length === 0) {
      return message || 'This field is required'
    }
    return true
  },

  /**
   * Validate string length
   */
  length: (min: number, max: number, fieldName: string = 'This field'): Validator => (value: string) => {
    const result = validateLength(value, min, max, fieldName)
    return result.isValid ? true : result.error || `Invalid length`
  },

  /**
   * Validate alphanumeric with allowed special characters
   */
  alphanumeric: (
    allowedChars: string = '- _&\'',
    fieldName: string = 'This field',
    allowUnicode: boolean = false
  ): Validator => (value: string) => {
    const result = validateAlphanumeric(value, allowedChars, fieldName, allowUnicode)
    return result.isValid ? true : result.error || 'Invalid characters'
  },

  /**
   * Validate decimal number
   */
  decimal: (
    min: number,
    max: number,
    decimals: number = 2,
    fieldName: string = 'Value'
  ): Validator => (value: string) => {
    // Allow empty for optional fields
    if (!value.trim()) return true

    const result = validateDecimal(value, min, max, decimals, fieldName)
    return result.isValid ? true : result.error || 'Invalid number'
  },

  /**
   * Validate using regex pattern
   */
  pattern: (regex: RegExp, message: string): Validator => (value: string) => {
    return regex.test(value.trim()) ? true : message
  },

  /**
   * Custom validator function
   */
  custom: (validatorFn: (value: string) => boolean | string): Validator => (value: string) => {
    return validatorFn(value)
  },

  /**
   * Validate password minimum length
   */
  minLength: (min: number, fieldName: string = 'This field'): Validator => (value: string) => {
    if (value.length < min) {
      return `${fieldName} must be at least ${min} characters`
    }
    return true
  },

  /**
   * Validate that two fields match (for password confirmation)
   */
  match: (otherValue: string, fieldName: string = 'Fields'): Validator => (value: string) => {
    if (value !== otherValue) {
      return `${fieldName} do not match`
    }
    return true
  }
}

// ============================================================================
// Single Field Hook
// ============================================================================

function useSingleFieldValidation({
  value = '',
  onChange = () => {},
  validators: fieldValidators = [],
  sanitize,
  validateOnBlur = false
}: Exclude<UseFormValidationOptions, 'fields'>) {
  const [error, setError] = useState<string>('')

  /**
   * Run all validators for the field
   */
  const validate = useCallback((): boolean => {
    setError('')

    for (const validator of fieldValidators) {
      const result = validator(value)

      if (result === false || (typeof result === 'string' && result.length > 0)) {
        const errorMessage = typeof result === 'string' ? result : 'Validation failed'
        setError(errorMessage)
        return false
      }

      if (typeof result === 'object' && !result.isValid) {
        setError(result.error || 'Validation failed')
        return false
      }
    }

    return true
  }, [value, fieldValidators])

  /**
   * Clear validation error
   */
  const clearError = useCallback(() => {
    setError('')
  }, [])

  /**
   * Handle input change with optional sanitization and error clearing
   */
  const handleChange = useCallback((newValue: string) => {
    const finalValue = sanitize ? sanitize(newValue) : newValue
    onChange(finalValue)
    setError('') // Always clear error on change
  }, [onChange, sanitize])

  /**
   * Handle blur event with optional validation
   */
  const handleBlur = useCallback(() => {
    if (validateOnBlur && value.trim()) {
      validate()
    }
  }, [validate, validateOnBlur, value])

  return {
    error,
    validate,
    clearError,
    handleChange,
    handleBlur
  }
}

// ============================================================================
// Multi-Field Hook
// ============================================================================

function useMultiFieldValidation(fields: Record<string, FieldConfig> = {}) {
  const [errors, setErrors] = useState<Record<string, string>>({})

  /**
   * Validate a specific field
   */
  const validateField = useCallback((fieldName: string): boolean => {
    const field = fields[fieldName]
    if (!field || !field.validators) return true

    setErrors(prev => ({ ...prev, [fieldName]: '' }))

    for (const validator of field.validators) {
      const result = validator(field.value)

      if (result === false || (typeof result === 'string' && result.length > 0)) {
        const errorMessage = typeof result === 'string' ? result : 'Validation failed'
        setErrors(prev => ({ ...prev, [fieldName]: errorMessage }))
        return false
      }

      if (typeof result === 'object' && !result.isValid) {
        setErrors(prev => ({ ...prev, [fieldName]: result.error || 'Validation failed' }))
        return false
      }
    }

    return true
  }, [fields])

  /**
   * Validate all fields
   */
  const validateAll = useCallback((): boolean => {
    let allValid = true

    for (const fieldName of Object.keys(fields)) {
      const isValid = validateField(fieldName)
      if (!isValid) allValid = false
    }

    return allValid
  }, [fields, validateField])

  /**
   * Clear error for a specific field
   */
  const clearFieldError = useCallback((fieldName: string) => {
    setErrors(prev => ({ ...prev, [fieldName]: '' }))
  }, [])

  /**
   * Clear all errors
   */
  const clearAllErrors = useCallback(() => {
    setErrors({})
  }, [])

  /**
   * Get props for a specific field (onChange, onBlur, error)
   */
  const getFieldProps = useCallback((fieldName: string) => {
    const field = fields[fieldName]
    if (!field) return {}

    return {
      value: field.value,
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const newValue = e.target.value
        const finalValue = field.sanitize ? field.sanitize(newValue) : newValue
        field.onChange(finalValue)
        clearFieldError(fieldName)
      },
      onBlur: () => {
        if (field.validateOnBlur && field.value.trim()) {
          validateField(fieldName)
        }
      },
      error: errors[fieldName]
    }
  }, [fields, errors, validateField, clearFieldError])

  return {
    errors,
    validateField,
    validateAll,
    clearFieldError,
    clearAllErrors,
    getFieldProps
  }
}

// ============================================================================
// Main Hook Export
// ============================================================================

/**
 * Form validation hook with built-in validators
 *
 * Single field usage:
 * ```ts
 * const { error, validate, handleChange, handleBlur } = useFormValidation({
 *   value: productName,
 *   onChange: setProductName,
 *   validators: [
 *     validators.required(),
 *     validators.length(2, 100, 'Product name')
 *   ]
 * })
 * ```
 *
 * Multi-field usage:
 * ```ts
 * const { errors, validateAll, getFieldProps } = useFormValidation({
 *   fields: {
 *     productName: {
 *       value: productName,
 *       onChange: setProductName,
 *       validators: [validators.required(), validators.length(2, 100)]
 *     }
 *   }
 * })
 * ```
 */
export function useFormValidation(options: UseFormValidationOptions) {
  // Multi-field mode
  if (options.fields) {
    return useMultiFieldValidation(options.fields)
  }

  // Single field mode
  return useSingleFieldValidation(options)
}

// Export validators library
export { sanitizeString }
