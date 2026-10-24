/**
 * API Initialization
 * Initializes the API layer with configuration and interceptors
 */

import { apiClient } from './client'
import { API_CONFIG } from './config'
import { authService } from './services/auth'
import { wsService } from './services/websocket'
import { apiCache } from './utils/cache'
import { getToken, getRefreshToken, setToken, removeToken } from '../utils/auth'

/**
 * Initialize API layer
 */
export const initializeApi = async (): Promise<void> => {
  try {
    // Initialize authentication if token exists
    const token = getToken()
    const refreshToken = getRefreshToken()

    if (token && refreshToken) {
      try {
        // Verify token is still valid
        await authService.getCurrentUser()
        console.log('API initialized with existing authentication')
      } catch (error) {
        // Token might be expired, try to refresh
        try {
          const response = await authService.refreshToken()
          setToken(response.token)
          localStorage.setItem('refreshToken', response.refreshToken)
          console.log('API initialized with refreshed token')
        } catch (refreshError) {
          // Refresh failed, clear tokens
          removeToken()
          localStorage.removeItem('refreshToken')
          console.log('API initialized without authentication')
        }
      }
    } else {
      console.log('API initialized without authentication')
    }

    // Initialize WebSocket connection
    if (token) {
      wsService.connect().catch((error) => {
        console.warn('Failed to initialize WebSocket:', error)
      })
    }

    // Initialize cache cleanup
    if (apiCache) {
      // Cache is already initialized in its constructor
      console.log('API cache initialized')
    }

    // Setup global error handler
    setupGlobalErrorHandler()

    // Setup performance monitoring
    setupPerformanceMonitoring()

    console.log('API layer initialized successfully')
  } catch (error) {
    console.error('Failed to initialize API layer:', error)
    throw error
  }
}

/**
 * Setup global error handler
 */
const setupGlobalErrorHandler = (): void => {
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    if (event.reason?.response?.status === 401) {
      // Unauthorized, redirect to login
      removeToken()
      localStorage.removeItem('refreshToken')
      window.location.href = '/login'
    }
  })

  // Handle API response errors globally
  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      // Log error for debugging
      console.error('API Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        message: error.response?.data?.message || error.message,
      })

      // Handle specific error cases
      if (error.response?.status === 429) {
        // Rate limit exceeded
        const retryAfter = error.response.headers['retry-after']
        console.warn(`Rate limit exceeded. Retry after ${retryAfter || 60} seconds`)
      }

      if (error.response?.status === 503) {
        // Service unavailable
        console.warn('Service temporarily unavailable')
      }

      return Promise.reject(error)
    }
  )
}

/**
 * Setup performance monitoring
 */
const setupPerformanceMonitoring = (): void => {
  // Monitor API response times
  apiClient.interceptors.request.use((config) => {
    config.metadata = { startTime: new Date() }
    return config
  })

  apiClient.interceptors.response.use((response) => {
    if (response.config.metadata?.startTime) {
      const duration = new Date().getTime() - response.config.metadata.startTime.getTime()

      // Log slow requests
      if (duration > 2000) {
        console.warn(`Slow API request: ${response.config.url} took ${duration}ms`)
      }

      // Send to monitoring service if available
      if (window.gtag) {
        window.gtag('event', 'api_response_time', {
          event_category: 'API',
          event_label: response.config.url,
          value: Math.round(duration),
        })
      }
    }

    return response
  })
}

/**
 * Cleanup API resources
 */
export const cleanupApi = (): void => {
  // Disconnect WebSocket
  wsService.disconnect()

  // Clear cache
  apiCache.clear()

  // Remove event listeners
  window.removeEventListener('unhandledrejection', () => {})

  console.log('API layer cleaned up')
}

/**
 * Check API health
 */
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    const response = await apiClient.get('/health')
    return response.status === '200' || response.status === 200
  } catch (error) {
    console.error('API health check failed:', error)
    return false
  }
}

/**
 * Reset API state
 */
export const resetApi = (): void => {
  // Clear authentication
  removeToken()
  localStorage.removeItem('refreshToken')

  // Clear cache
  apiCache.clear()

  // Reset any state
  console.log('API state reset')
}