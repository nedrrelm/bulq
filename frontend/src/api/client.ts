import { API_BASE_URL } from '../config'

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

interface RequestOptions {
  method?: string
  headers?: Record<string, string>
  body?: any
  credentials?: RequestCredentials
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const {
    method = 'GET',
    headers = {},
    body,
    credentials = 'include'
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
      let errorData

      if (isJson) {
        try {
          errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
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

      throw new ApiError(errorMessage, response.status, errorData)
    }

    // Handle empty responses (204 No Content)
    if (response.status === 204) {
      return {} as T
    }

    if (isJson) {
      return await response.json()
    }

    // Return empty object for non-JSON successful responses
    return {} as T
  } catch (error) {
    if (error instanceof ApiError) {
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
  get: <T = any>(endpoint: string) =>
    request<T>(endpoint, { method: 'GET' }),

  post: <T = any>(endpoint: string, data?: any) =>
    request<T>(endpoint, { method: 'POST', body: data }),

  put: <T = any>(endpoint: string, data?: any) =>
    request<T>(endpoint, { method: 'PUT', body: data }),

  patch: <T = any>(endpoint: string, data?: any) =>
    request<T>(endpoint, { method: 'PATCH', body: data }),

  delete: <T = any>(endpoint: string) =>
    request<T>(endpoint, { method: 'DELETE' })
}
