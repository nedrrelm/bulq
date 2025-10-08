import { useState, useEffect, useCallback } from 'react'
import { API_BASE_URL } from '../config'

interface UseApiOptions {
  immediate?: boolean
  onSuccess?: (data: any) => void
  onError?: (error: Error) => void
}

interface UseApiResult<T> {
  data: T | null
  loading: boolean
  error: string
  refetch: () => Promise<void>
  setData: (data: T | null) => void
}

export function useApi<T = any>(
  endpoint: string,
  options: RequestInit & UseApiOptions = {}
): UseApiResult<T> {
  const { immediate = true, onSuccess, onError, ...fetchOptions } = options

  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(immediate)
  const [error, setError] = useState('')

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError('')

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        credentials: 'include',
        ...fetchOptions
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`)
      }

      const result: T = await response.json()
      setData(result)

      if (onSuccess) {
        onSuccess(result)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch data'
      setError(errorMessage)

      if (onError && err instanceof Error) {
        onError(err)
      }
    } finally {
      setLoading(false)
    }
  }, [endpoint, fetchOptions, onSuccess, onError])

  useEffect(() => {
    if (immediate) {
      fetchData()
    }
  }, [immediate, fetchData])

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    setData
  }
}
