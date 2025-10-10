import { z } from 'zod'

/**
 * Common Zod schemas and utilities for API validation
 */

// UUID validation
export const uuidSchema = z.string().uuid()

// Nullable helper
export const nullable = <T extends z.ZodTypeAny>(schema: T) => schema.nullable()

// Optional nullable helper (for fields that can be null or undefined)
export const optionalNullable = <T extends z.ZodTypeAny>(schema: T) => schema.nullable().optional()

// ISO date string
export const isoDateSchema = z.string().datetime()

// Positive number
export const positiveNumberSchema = z.number().positive()

// Non-negative number
export const nonNegativeNumberSchema = z.number().nonnegative()

// Email validation
export const emailSchema = z.string().email()

// Common validation error messages
export const validationMessages = {
  required: 'This field is required',
  invalidUuid: 'Invalid UUID format',
  invalidEmail: 'Invalid email format',
  invalidDate: 'Invalid date format',
  positiveNumber: 'Must be a positive number',
  nonNegativeNumber: 'Must be zero or greater'
}
