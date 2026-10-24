import { Middleware, MiddlewareAPI, isRejectedWithValue } from '@reduxjs/toolkit'
import { createLogger } from 'redux-logger'
import { persistStore } from 'redux-persist'
import { RootState } from '../types/store'
import { addError } from './slices/uiSlice'

// Error handling middleware
export const errorMiddleware: Middleware<{}, RootState> =
  (api: MiddlewareAPI) => (next) => (action) => {
    if (isRejectedWithValue(action)) {
      // Handle rejected actions
      const error = action.payload?.data?.message || action.payload?.message || action.error?.message || 'Unknown error'

      // Dispatch error notification to UI slice
      api.dispatch(addError({
        message: error,
        endpoint: action.meta?.arg?.endpointName || 'unknown',
        method: action.meta?.baseQueryMeta?.request?.method || 'unknown',
      }))
    }

    return next(action)
  }

// Loading state middleware
export const loadingMiddleware: Middleware<{}, RootState> =
  (api: MiddlewareAPI) => (next) => (action) => {
    // Track API loading states
    if (action.type.startsWith('api/') && action.type.endsWith('/pending')) {
      const endpointName = action.meta?.arg?.endpointName
      if (endpointName) {
        // Set loading state for specific endpoint
        api.dispatch({
          type: 'ui/setComponentLoading',
          payload: { component: endpointName, loading: true }
        })
      }
    }

    if (action.type.startsWith('api/') && (action.type.endsWith('/fulfilled') || action.type.endsWith('/rejected'))) {
      const endpointName = action.meta?.arg?.endpointName
      if (endpointName) {
        // Clear loading state for specific endpoint
        api.dispatch({
          type: 'ui/setComponentLoading',
          payload: { component: endpointName, loading: false }
        })
      }
    }

    return next(action)
  }

// WebSocket middleware for real-time updates
export const websocketMiddleware: Middleware<{}, RootState> =
  (api: MiddlewareAPI) => (next) => (action) => {
    // Handle WebSocket messages
    if (action.type === 'websocket/message') {
      const { channel, data } = action.payload

      // Route WebSocket messages to appropriate slices
      switch (channel) {
        case 'market_data':
          return next({
            type: 'market/updateRealTimeData',
            payload: data
          })
        case 'strategy_update':
          return next({
            type: 'strategies/updateStrategy',
            payload: data
          })
        case 'execution_update':
          return next({
            type: 'strategies/updateExecution',
            payload: data
          })
        case 'system_alert':
          return next({
            type: 'ui/addAlert',
            payload: data
          })
        default:
          return next(action)
      }
    }

    return next(action)
  }

// Performance monitoring middleware
export const performanceMiddleware: Middleware<{}, RootState> =
  (api: MiddlewareAPI) => (next) => (action) => {
    const startTime = performance.now()

    const result = next(action)

    const endTime = performance.now()
    const duration = endTime - startTime

    // Log slow actions in development
    if (process.env.NODE_ENV === 'development' && duration > 100) {
      console.warn(`Slow action detected: ${action.type} took ${duration.toFixed(2)}ms`)
    }

    return result
  }

// API request logging middleware
export const apiLogger: Middleware<{}, RootState> =
  (api: MiddlewareAPI) => (next) => (action) => {
    if (action.type.startsWith('api/')) {
      const state = api.getState()
      const isPending = action.type.endsWith('/pending')
      const isFulfilled = action.type.endsWith('/fulfilled')
      const isRejected = action.type.endsWith('/rejected')

      if (isPending) {
        console.log(`API Request Started:`, {
          type: action.type,
          endpoint: action.meta?.arg?.endpointName,
          args: action.meta?.arg?.originalArgs,
          timestamp: new Date().toISOString()
        })
      } else if (isFulfilled) {
        console.log(`API Request Succeeded:`, {
          type: action.type,
          endpoint: action.meta?.arg?.endpointName,
          timestamp: new Date().toISOString()
        })
      } else if (isRejected) {
        console.error(`API Request Failed:`, {
          type: action.type,
          endpoint: action.meta?.arg?.endpointName,
          error: action.payload,
          timestamp: new Date().toISOString()
        })
      }
    }

    return next(action)
  }

// Create logger for development
export const logger = createLogger({
  collapsed: true,
  duration: true,
  timestamp: true,
  diff: true,
  // Only log in development and skip certain actions
  predicate: (getState, action) => {
    if (process.env.NODE_ENV !== 'development') return false

    // Skip verbose actions
    const skipActions = [
      'market/updateRealTimeData', // Skip high-frequency updates
      'ui/setComponentLoading',    // Skip loading state changes
    ]

    return !skipActions.includes(action.type)
  }
})

// Cache invalidation middleware
export const cacheMiddleware: Middleware<{}, RootState> =
  (api: MiddlewareAPI) => (next) => (action) => {
    const result = next(action)

    // Invalidate relevant caches after certain actions
    if (action.type === 'strategies/updateStrategy/fulfilled') {
      // Invalidate strategy-related cache
      api.dispatch({ type: 'api/util/invalidateTags', payload: ['Strategy', 'StrategyPerformance'] })
    }

    if (action.type === 'strategies/executeStrategy/fulfilled') {
      // Invalidate execution-related cache
      api.dispatch({ type: 'api/util/invalidateTags', payload: ['Execution', 'Positions'] })
    }

    return result
  }

// User activity tracking middleware
export const activityMiddleware: Middleware<{}, RootState> =
  (api: MiddlewareAPI) => (next) => (action) => {
    // Track user interactions
    const userActions = [
      'strategies/createStrategy',
      'strategies/updateStrategy',
      'strategies/deleteStrategy',
      'strategies/executeStrategy',
      'strategies/stopStrategy',
      'market/placeOrder',
    ]

    if (userActions.some(ua => action.type.includes(ua))) {
      // Log user activity
      api.dispatch({
        type: 'auth/trackActivity',
        payload: {
          action: action.type,
          timestamp: new Date().toISOString(),
          data: action.payload
        }
      })
    }

    return next(action)
  }

// Export all middlewares as an array for easy configuration
export const middlewares = [
  errorMiddleware,
  loadingMiddleware,
  websocketMiddleware,
  performanceMiddleware,
  apiLogger,
  cacheMiddleware,
  activityMiddleware,
  // Add logger only in development
  ...(process.env.NODE_ENV === 'development' ? [logger] : [])
]

// Create and export the persistor
export const createPersistor = (store: any) => {
  return persistStore(store)
}