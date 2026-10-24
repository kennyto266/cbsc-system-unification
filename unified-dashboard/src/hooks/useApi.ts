/**
 * API Hook
 * Provides a convenient way to use API services with loading states and error handling
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { message } from 'antd'
import { authService } from '../api/services/auth'
import { marketService } from '../api/services/market'
import { strategyService } from '../api/services/strategies'
import { wsService } from '../api/services/websocket'
import { apiCache } from '../api/utils/cache'

// Hook return type
interface UseApiReturn<T, P extends any[]> {
  data: T | null
  loading: boolean
  error: Error | null
  execute: (...params: P) => Promise<T>
  reset: () => void
  refetch: () => Promise<T>
}

// Options for useApi hook
interface UseApiOptions {
  immediate?: boolean
  cache?: boolean
  cacheTTL?: number
  onSuccess?: (data: any) => void
  onError?: (error: Error) => void
  retries?: number
  retryDelay?: number
}

/**
 * Generic API hook
 */
export function useApi<T, P extends any[]>(
  apiFunction: (...params: P) => Promise<T>,
  options: UseApiOptions = {}
): UseApiReturn<T, P> {
  const {
    immediate = false,
    cache = false,
    cacheTTL,
    onSuccess,
    onError,
    retries = 0,
    retryDelay = 1000,
  } = options

  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [params, setParams] = useState<P | null>(null)
  const retryCount = useRef(0)

  const execute = useCallback(
    async (...args: P) => {
      setParams(args)
      setLoading(true)
      setError(null)

      try {
        // Check cache first if enabled
        if (cache && args.length > 0) {
          const cacheKey = `${apiFunction.name}:${JSON.stringify(args)}`
          const cached = apiCache.get<T>(cacheKey)
          if (cached) {
            setData(cached)
            setLoading(false)
            onSuccess?.(cached)
            return cached
          }
        }

        const result = await apiFunction(...args)

        // Cache result if enabled
        if (cache && args.length > 0) {
          const cacheKey = `${apiFunction.name}:${JSON.stringify(args)}`
          apiCache.set(cacheKey, result, cacheTTL)
        }

        setData(result)
        onSuccess?.(result)
        retryCount.current = 0
        return result
      } catch (err) {
        const error = err as Error

        // Retry logic
        if (retryCount.current < retries) {
          retryCount.current++
          setTimeout(() => {
            execute(...args)
          }, retryDelay * retryCount.current)
          return
        }

        setError(error)
        onError?.(error)
        throw error
      } finally {
        setLoading(false)
      }
    },
    [apiFunction, cache, cacheTTL, onSuccess, onError, retries, retryDelay]
  )

  const reset = useCallback(() => {
    setData(null)
    setLoading(false)
    setError(null)
    setParams(null)
    retryCount.current = 0
  }, [])

  const refetch = useCallback(async () => {
    if (params) {
      return execute(...params)
    }
    throw new Error('No parameters to refetch with')
  }, [execute, params])

  // Execute immediately if requested
  useEffect(() => {
    if (immediate) {
      execute()
    }
  }, [immediate, execute])

  return {
    data,
    loading,
    error,
    execute,
    reset,
    refetch,
  }
}

/**
 * API hooks for specific services
 */

// Auth hooks
export function useLogin() {
  return useApi(authService.login.bind(authService))
}

export function useLogout() {
  return useApi(authService.logout.bind(authService), {
    onSuccess: () => {
      message.success('退出登录成功')
    },
  })
}

export function useRegister() {
  return useApi(authService.register.bind(authService), {
    onSuccess: () => {
      message.success('注册成功')
    },
  })
}

// Market data hooks
export function useMarketSymbols(params?: any) {
  return useApi(marketService.getSymbols.bind(marketService), {
    immediate: true,
    cache: true,
    cacheTTL: 300000, // 5 minutes
  })
}

export function useMarketPrice(symbol: string) {
  return useApi(() => marketService.getPrice(symbol), {
    cache: true,
    cacheTTL: 5000, // 5 seconds for live prices
  })
}

export function useKlineData(params: any) {
  return useApi(() => marketService.getKlineData(params), {
    cache: true,
    cacheTTL: 60000, // 1 minute
  })
}

// Strategy hooks
export function useStrategies(params?: any) {
  return useApi(() => strategyService.getStrategies(params), {
    immediate: true,
    cache: true,
    cacheTTL: 30000, // 30 seconds
  })
}

export function useStrategy(id: string) {
  return useApi(() => strategyService.getStrategy(id), {
    cache: true,
    cacheTTL: 60000, // 1 minute
  })
}

export function useCreateStrategy() {
  return useApi(strategyService.createStrategy.bind(strategyService), {
    onSuccess: () => {
      message.success('策略创建成功')
    },
  })
}

export function useUpdateStrategy() {
  return useApi(strategyService.updateStrategy.bind(strategyService), {
    onSuccess: () => {
      message.success('策略更新成功')
    },
  })
}

export function useDeleteStrategy() {
  return useApi(strategyService.deleteStrategy.bind(strategyService), {
    onSuccess: () => {
      message.success('策略删除成功')
    },
  })
}

export function useExecuteStrategy() {
  return useApi(strategyService.executeStrategy.bind(strategyService), {
    onSuccess: () => {
      message.success('策略执行已启动')
    },
  })
}

export function useStopStrategy() {
  return useApi(strategyService.stopStrategy.bind(strategyService), {
    onSuccess: () => {
      message.success('策略已停止')
    },
  })
}

// WebSocket hook
export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    // Connect to WebSocket
    wsService.connect()
      .then(() => {
        setIsConnected(true)
        setError(null)
      })
      .catch((err) => {
        setIsConnected(false)
        setError(err)
      })

    // Listen to connection events
    const handleOpen = () => setIsConnected(true)
    const handleClose = () => setIsConnected(false)
    const handleError = (err: Error) => {
      setIsConnected(false)
      setError(err)
    }

    wsService.on('open', handleOpen)
    wsService.on('close', handleClose)
    wsService.on('error', handleError)

    // Cleanup
    return () => {
      wsService.off('open', handleOpen)
      wsService.off('close', handleClose)
      wsService.off('error', handleError)
    }
  }, [])

  return {
    isConnected,
    error,
    subscribe: wsService.subscribe.bind(wsService),
    unsubscribe: wsService.unsubscribe.bind(wsService),
    send: wsService.send.bind(wsService),
  }
}

/**
 * Debounced API hook
 */
export function useDebouncedApi<T, P extends any[]>(
  apiFunction: (...params: P) => Promise<T>,
  delay: number,
  options: UseApiOptions = {}
) {
  const [debouncedParams, setDebouncedParams] = useState<P | null>(null)
  const { execute, ...rest } = useApi(apiFunction, options)

  useEffect(() => {
    const timer = setTimeout(() => {
      if (debouncedParams) {
        execute(...debouncedParams)
      }
    }, delay)

    return () => clearTimeout(timer)
  }, [debouncedParams, delay, execute])

  const debouncedExecute = useCallback((...args: P) => {
    setDebouncedParams(args)
  }, [])

  return {
    ...rest,
    execute: debouncedExecute,
  }
}

/**
 * Paginated API hook
 */
export function usePaginatedApi<T, P extends any[]>(
  apiFunction: (...params: P) => Promise<any>,
  initialParams: P,
  options: UseApiOptions = {}
) {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [total, setTotal] = useState(0)

  const { data, loading, error, execute } = useApi(apiFunction, {
    ...options,
    onSuccess: (response) => {
      setTotal(response.pagination?.total || 0)
      options.onSuccess?.(response)
    },
  })

  const loadPage = useCallback((newPage: number, newSize?: number) => {
    const actualSize = newSize || pageSize
    setPage(newPage)
    setPageSize(actualSize)
    return execute(
      ...[
        ...initialParams.slice(0, -1),
        { ...initialParams[initialParams.length - 1], page: newPage, limit: actualSize },
      ]
    )
  }, [execute, initialParams, pageSize])

  const nextPage = useCallback(() => {
    return loadPage(page + 1)
  }, [loadPage, page])

  const prevPage = useCallback(() => {
    return loadPage(page - 1)
  }, [loadPage, page])

  return {
    data: data?.data || [],
    loading,
    error,
    total,
    page,
    pageSize,
    setPage,
    setPageSize,
    loadPage,
    nextPage,
    prevPage,
    execute,
  }
}