import { API_BASE_URL } from '../config'
import { z } from 'zod'

export class ApiError extends Error {
  status: number
  code?: string
  details?: any
  data?: any

  constructor(
    message: string,
    status: number,
    code?: string,
    details?: any,
    data?: any
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
    this.data = data
  }
}

export class ValidationError extends Error {
  zodError: z.ZodError
  endpoint: string

  constructor(
    message: string,
    zodError: z.ZodError,
    endpoint: string
  ) {
    super(message)
    this.name = 'ValidationError'
    this.zodError = zodError
    this.endpoint = endpoint
  }

  override toString(): string {
    return this.message
  }
}

interface RequestOptions {
  method?: string
  headers?: Record<string, string>
  body?: any
  credentials?: RequestCredentials
  schema?: z.ZodSchema
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const {
    method = 'GET',
    headers = {},
    body,
    credentials = 'include',
    schema
  } = options

  const config: RequestInit = {
    method,
    credentials,
    headers: {
      'Content-Type': 'application/json',
      ...headers
    }
  }

  if (body) {
    config.body = JSON.stringify(body)
  }

  const url = `${API_BASE_URL}${endpoint}`

  try {
    const response = await fetch(url, config)

    // Handle non-JSON responses
    const contentType = response.headers.get('content-type')
    const isJson = contentType?.includes('application/json')

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`
      let errorCode: string | undefined
      let errorDetails: any
      let errorData: any

      if (isJson) {
        try {
          errorData = await response.json()
          // Extract code and details from standardized error response
          errorCode = errorData.code
          errorDetails = errorData.details
          // Fallback to message from response (for backward compatibility)
          errorMessage = errorData.message || errorData.detail || errorMessage
        } catch {
          // Failed to parse error JSON
        }
      } else {
        try {
          errorMessage = await response.text()
        } catch {
          // Failed to read error text
        }
      }

      throw new ApiError(errorMessage, response.status, errorCode, errorDetails, errorData)
    }

    // Handle empty responses (204 No Content)
    if (response.status === 204) {
      return {} as T
    }

    if (isJson) {
      const data = await response.json()

      // Validate response data if schema is provided
      if (schema) {
        try {
          return schema.parse(data) as T
        } catch (error) {
          if (error instanceof z.ZodError) {
            const issues = error.issues || []

            const errorDetails = issues.length > 0
              ? issues.map(e =>
                  `  - ${e.path.join('.') || 'root'}: ${e.message}`
                ).join('\n')
              : `Unknown validation error`

            throw new ValidationError(
              `Invalid response from ${endpoint}:\n${errorDetails}`,
              error,
              endpoint
            )
          }
          throw error
        }
      }

      return data
    }

    // Return empty object for non-JSON successful responses
    return {} as T
  } catch (error) {
    if (error instanceof ApiError || error instanceof ValidationError) {
      throw error
    }

    // Network error or other fetch failure
    throw new ApiError(
      error instanceof Error ? error.message : 'Network request failed',
      0
    )
  }
}

export const api = {
  get: <T = any>(endpoint: string, schema?: z.ZodSchema) =>
    request<T>(endpoint, { method: 'GET', schema }),

  post: <T = any>(endpoint: string, data?: any, schema?: z.ZodSchema) =>
    request<T>(endpoint, { method: 'POST', body: data, schema }),

  put: <T = any>(endpoint: string, data?: any, schema?: z.ZodSchema) =>
    request<T>(endpoint, { method: 'PUT', body: data, schema }),

  patch: <T = any>(endpoint: string, data?: any, schema?: z.ZodSchema) =>
    request<T>(endpoint, { method: 'PATCH', body: data, schema }),

  delete: <T = any>(endpoint: string, schema?: z.ZodSchema) =>
    request<T>(endpoint, { method: 'DELETE', schema })
}
