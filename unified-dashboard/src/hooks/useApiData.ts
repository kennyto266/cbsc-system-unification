import { useState, useEffect, useCallback } from 'react'
import { apiClientInstance } from '../api/client'
import type { ApiResponse } from '../types'

interface UseApiDataOptions<T> {
  immediate?: boolean
  onSuccess?: (data: T) => void
  onError?: (error: Error) => void
  retryCount?: number
  retryDelay?: number
}

interface UseApiDataResult<T> {
  data: T | null
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
  mutate: (newData: T) => void
}

export function useApiData<T = any>(
  endpoint: string,
  params?: Record<string, any>,
  options: UseApiDataOptions<T> = {}
): UseApiDataResult<T> {
  const {
    immediate = true,
    onSuccess,
    onError,
    retryCount = 3,
    retryDelay = 1000,
  } = options

  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [retryAttempts, setRetryAttempts] = useState(0)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await apiClientInstance.get<ApiResponse<T>>(endpoint, params)

      if (response.success && response.data) {
        setData(response.data)
        onSuccess?.(response.data)
        setRetryAttempts(0)
      } else {
        throw new Error(response.error?.message || 'API request failed')
      }
    } catch (err) {
      const error = err as Error

      // Retry logic
      if (retryAttempts < retryCount) {
        setRetryAttempts(prev => prev + 1)
        setTimeout(() => {
          fetchData()
        }, retryDelay * Math.pow(2, retryAttempts)) // Exponential backoff
        return
      }

      setError(error)
      onError?.(error)
    } finally {
      setLoading(false)
    }
  }, [endpoint, params, immediate, onSuccess, onError, retryCount, retryDelay, retryAttempts])

  useEffect(() => {
    if (immediate) {
      fetchData()
    }
  }, [immediate, fetchData])

  const refetch = useCallback(async () => {
    setRetryAttempts(0)
    await fetchData()
  }, [fetchData])

  const mutate = useCallback((newData: T) => {
    setData(newData)
  }, [])

  return {
    data,
    loading,
    error,
    refetch,
    mutate,
  }
}

// Specific hooks for common API calls
export function useStrategies(params?: Record<string, any>) {
  return useApiData('/strategies', params)
}

export function useAnalyticsData(timeRange = '1m') {
  return useApiData('/analysis/dashboard', { time_range: timeRange })
}

export function useMarketData(symbols?: string[]) {
  return useApiData('/market/overview', { symbols: symbols?.join(',') })
}

export function useSystemHealth() {
  return useApiData('/system/health')
}

export function useRecentSignals(limit = 10) {
  return useApiData('/signals/recent', { limit })
}