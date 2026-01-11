// Retry utility functions
import type { BaseQueryFn } from '@reduxjs/toolkit/query/react'
import type { ApiError } from '../../types/api'

// Retry configuration interface
export interface RetryConfig {
  maxAttempts?: number
  baseDelay?: number
  maxDelay?: number
  backoffFactor?: number
  jitter?: boolean
  retryCondition?: (error: ApiError, attempt: number) => boolean
  onRetry?: (error: ApiError, attempt: number) => void
}

// Default retry configuration
const DEFAULT_RETRY_CONFIG: Required<RetryConfig> = {
  maxAttempts: 3,
  baseDelay: 1000,
  maxDelay: 30000,
  backoffFactor: 2,
  jitter: true,
  retryCondition: (error, attempt) => {
    // Default retry condition
    if (attempt >= 3) return false

    // Retry on network errors
    if (error.code === 'NETWORK_ERROR' || error.code === 'TIMEOUT_ERROR') return true

    // Retry on server errors (5xx)
    if (error.status >= 500 && error.status < 600) return true

    // Retry on rate limit errors
    if (error.code === 'RATE_LIMIT_EXCEEDED') return true

    // Don't retry on client errors (4xx)
    if (error.status >= 400 && error.status < 500) return false

    return false
  },
  onRetry: (error, attempt) => {
    console.warn(`Retry attempt ${attempt} for error:`, error.message)
  },
}

// Calculate delay with exponential backoff and jitter
export const calculateDelay = (
  attempt: number,
  config: RetryConfig
): number => {
  const {
    baseDelay,
    maxDelay,
    backoffFactor,
    jitter,
  } = { ...DEFAULT_RETRY_CONFIG, ...config }

  // Calculate exponential backoff delay
  let delay = baseDelay * Math.pow(backoffFactor, attempt - 1)

  // Apply maximum delay limit
  delay = Math.min(delay, maxDelay)

  // Add jitter to prevent thundering herd
  if (jitter) {
    delay = delay * (0.5 + Math.random() * 0.5)
  }

  return Math.floor(delay)
}

// Create retry wrapper for baseQuery
export const createRetryWrapper = (
  config: RetryConfig = {}
): <Result, Arg>(
  baseQuery: BaseQueryFn<Result, Arg, ApiError>
) => BaseQueryFn<Result, Arg, ApiError> => {
  const retryConfig = { ...DEFAULT_RETRY_CONFIG, ...config }

  return async (args, api, extraOptions) => {
    let lastError: ApiError | undefined

    for (let attempt = 1; attempt <= retryConfig.maxAttempts!; attempt++) {
      try {
        const result = await baseQuery(args, api, extraOptions)

        // If successful, return result
        if (result.data) {
          return result
        }

        // If there's an error, check if we should retry
        if (result.error) {
          lastError = result.error

          // Check custom retry condition
          if (!retryConfig.retryCondition!(lastError, attempt)) {
            break
          }

          // Don't retry on the last attempt
          if (attempt === retryConfig.maxAttempts) {
            break
          }

          // Call onRetry callback
          retryConfig.onRetry!(lastError, attempt)

          // Calculate delay and wait
          const delay = calculateDelay(attempt, retryConfig)
          await new Promise(resolve => setTimeout(resolve, delay))

          // Continue to next attempt
          continue
        }

        return result
      } catch (error: any) {
        // Handle unexpected errors
        lastError = {
          status: 'NETWORK_ERROR',
          code: 'NETWORK_ERROR',
          message: error.message || 'Network error',
          timestamp: new Date().toISOString(),
        }

        if (attempt === retryConfig.maxAttempts) {
          break
        }

        const delay = calculateDelay(attempt, retryConfig)
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }

    // Return the last error
    return {
      error: lastError!,
    }
  }
}

// Adaptive retry strategy based on error type
export const createAdaptiveRetry = (): RetryConfig => ({
  maxAttempts: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  backoffFactor: 2,
  jitter: true,
  retryCondition: (error, attempt) => {
    if (attempt >= 3) return false

    // More aggressive retry for network errors
    if (error.code === 'NETWORK_ERROR' || error.code === 'TIMEOUT_ERROR') {
      return attempt <= 5 // Allow more attempts for network issues
    }

    // Conservative retry for server errors
    if (error.status >= 500 && error.status < 600) {
      return attempt <= 2
    }

    // Quick retry for rate limit errors
    if (error.code === 'RATE_LIMIT_EXCEEDED') {
      return attempt <= 2
    }

    return false
  },
  onRetry: (error, attempt) => {
    const delay = calculateDelay(attempt, {
      baseDelay: error.code === 'RATE_LIMIT_EXCEEDED' ? 5000 : 1000,
      maxDelay: 30000,
      backoffFactor: 2,
      jitter: true,
    })

    console.warn(`Retry attempt ${attempt} in ${delay}ms for:`, error.code)
  },
})

// Retry with circuit breaker
export const createCircuitBreakerRetry = (
  threshold: number = 5,
  timeout: number = 60000
): RetryConfig => {
  let failures = 0
  let lastFailureTime = 0

  return {
    maxAttempts: 3,
    baseDelay: 1000,
    maxDelay: 5000,
    backoffFactor: 1.5,
    jitter: true,
    retryCondition: (error, attempt) => {
      const now = Date.now()

      // Check if circuit breaker is open
      if (failures >= threshold && now - lastFailureTime < timeout) {
        console.error('Circuit breaker is OPEN, skipping retry')
        return false
      }

      // Allow retry with normal conditions
      return attempt <= 2 && error.status !== 401
    },
    onRetry: (error, attempt) => {
      failures++
      lastFailureTime = Date.now()

      console.warn(`Circuit breaker retry attempt ${attempt}, failures: ${failures}`)
    },
  }
}

// Request deduplication wrapper
export const createDeduplicationWrapper = <Result, Arg>(
  baseQuery: BaseQueryFn<Result, Arg, ApiError>,
  keyGenerator?: (args: Arg) => string,
  ttl: number = 5000 // 5 seconds TTL
): BaseQueryFn<Result, Arg, ApiError> => {
  const pendingRequests = new Map<string, Promise<Result>>()

  return async (args, api, extraOptions) => {
    // Generate cache key
    const key = keyGenerator ? keyGenerator(args) : JSON.stringify(args)

    // Check if request is already pending
    if (pendingRequests.has(key)) {
      return pendingRequests.get(key)!
    }

    // Create new request
    const request = baseQuery(args, api, extraOptions)

    // Store pending request
    pendingRequests.set(key, request)

    try {
      const result = await request

      // Clear from pending requests
      pendingRequests.delete(key)

      return result
    } catch (error) {
      // Clear from pending requests even on error
      pendingRequests.delete(key)
      throw error
    }
  }
}

// Request timeout wrapper
export const createTimeoutWrapper = <Result, Arg>(
  baseQuery: BaseQueryFn<Result, Arg, ApiError>,
  timeoutMs: number = 30000
): BaseQueryFn<Result, Arg, ApiError> => {
  return async (args, api, extraOptions) => {
    // Create timeout promise
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => {
        reject(new Error(`Request timeout after ${timeoutMs}ms`))
      }, timeoutMs)
    })

    // Create request promise
    const requestPromise = baseQuery(args, api, extraOptions)

    try {
      // Race between request and timeout
      return await Promise.race([requestPromise, timeoutPromise])
    } catch (error: any) {
      // Return formatted timeout error
      if (error.message.includes('timeout')) {
        return {
          error: {
            status: 'TIMEOUT_ERROR',
            code: 'TIMEOUT_ERROR',
            message: `Request timeout after ${timeoutMs}ms`,
            timestamp: new Date().toISOString(),
          },
        }
      }

      throw error
    }
  }
}

// Batch request wrapper
export const createBatchWrapper = <Result, Arg>(
  baseQuery: BaseQueryFn<Result, Arg, ApiError>,
  batchSize: number = 10,
  batchDelay: number = 100
): BaseQueryFn<Result[], Arg[], ApiError> => {
  const batchQueue: Array<{
    args: Arg
    api: any
    extraOptions: any
    resolve: (value: any) => void
    reject: (error: any) => void
  }> = []

  let batchTimeout: NodeJS.Timeout | null = null

  const processBatch = async () => {
    if (batchQueue.length === 0) return

    const batch = batchQueue.splice(0, batchSize)
    const promises = batch.map(({ args, api, extraOptions }) =>
      baseQuery(args, api, extraOptions)
    )

    try {
      const results = await Promise.allSettled(promises)

      batch.forEach(({ resolve, reject }, index) => {
        const result = results[index]

        if (result.status === 'fulfilled') {
          resolve(result.value)
        } else {
          reject(result.reason)
        }
      })
    } catch (error) {
      batch.forEach(({ reject }) => reject(error))
    }

    // Schedule next batch if there are pending requests
    if (batchQueue.length > 0) {
      batchTimeout = setTimeout(processBatch, batchDelay)
    } else {
      batchTimeout = null
    }
  }

  return async (argsArray, api, extraOptions) => {
    return new Promise((resolve, reject) => {
      // Add to batch queue
      batchQueue.push({
        args: argsArray,
        api,
        extraOptions,
        resolve,
        reject,
      })

      // Start batch processing if not already running
      if (!batchTimeout) {
        batchTimeout = setTimeout(processBatch, batchDelay)
      }
    })
  }
}