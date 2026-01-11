import { Middleware } from '@reduxjs/toolkit'
import { RootState } from './index'

// Session management middleware
export const sessionMiddleware: Middleware<{}, RootState> =
  (store) => (next) => (action) => {
    const result = next(action)

    // Check for session timeout on auth actions
    if (action.type?.startsWith('auth/')) {
      const state = store.getState()

      if (state.auth.isAuthenticated && state.auth.lastActivity) {
        const now = Date.now()
        const timeSinceLastActivity = now - state.auth.lastActivity
        const sessionTimeout = state.auth.sessionTimeout

        // Auto-logout if session has expired
        if (timeSinceLastActivity > sessionTimeout) {
          console.log('Session expired due to inactivity')
          store.dispatch({ type: 'auth/logout' })
          store.dispatch({
            type: 'ui/addNotification',
            payload: {
              type: 'warning',
              title: 'Session Expired',
              message: 'You have been logged out due to inactivity',
              duration: 5000,
            },
          })
        }
      }
    }

    return result
  }

// Error handling middleware
export const errorMiddleware: Middleware<{}, RootState> =
  (store) => (next) => (action) => {
    try {
      return next(action)
    } catch (error) {
      console.error('Redux action error:', error, action)

      // Dispatch error notification
      store.dispatch({
        type: 'ui/addNotification',
        payload: {
          type: 'error',
          title: 'System Error',
          message: 'An unexpected error occurred. Please try again.',
          duration: 5000,
          persistent: true,
        },
      })

      throw error
    }
  }

// Performance monitoring middleware
export const performanceMiddleware: Middleware<{}, RootState> =
  (store) => (next) => (action) => {
    const start = performance.now()

    const result = next(action)

    const end = performance.now()
    const duration = end - start

    // Log slow actions
    if (duration > 16) { // 16ms is one frame at 60fps
      console.warn(`Slow action detected: ${action.type} took ${duration.toFixed(2)}ms`)
    }

    // Store performance metrics in development
    if (process.env.NODE_ENV === 'development') {
      const metrics = store.getState().ui.performanceMetrics || {}
      metrics[action.type] = {
        duration,
        timestamp: Date.now(),
      }
    }

    return result
  }

// API request middleware
export const apiRequestMiddleware: Middleware<{}, RootState> =
  (store) => (next) => (action) => {
    // Handle API request actions
    if (action.type?.endsWith('/pending')) {
      const endpoint = action.type.replace('/pending', '')

      // Set loading state
      store.dispatch({
        type: 'ui/setLoading',
        payload: { key: endpoint, loading: true },
      })
    }

    // Handle API fulfilled actions
    if (action.type?.endsWith('/fulfilled')) {
      const endpoint = action.type.replace('/fulfilled', '')

      // Clear loading state
      store.dispatch({
        type: 'ui/setLoading',
        payload: { key: endpoint, loading: false },
      })

      // Show success notification for mutations
      if (action.meta?.arg?.type === 'mutation') {
        store.dispatch({
          type: 'ui/addNotification',
          payload: {
            type: 'success',
            title: 'Success',
            message: `${endpoint} completed successfully`,
            duration: 3000,
          },
        })
      }
    }

    // Handle API rejected actions
    if (action.type?.endsWith('/rejected')) {
      const endpoint = action.type.replace('/rejected', '')

      // Clear loading state
      store.dispatch({
        type: 'ui/setLoading',
        payload: { key: endpoint, loading: false },
      })

      // Show error notification
      const error = action.error?.message || 'An error occurred'
      store.dispatch({
        type: 'ui/addNotification',
        payload: {
          type: 'error',
          title: 'Error',
          message: `${endpoint} failed: ${error}`,
          duration: 5000,
        },
      })
    }

    return next(action)
  }

// Authentication middleware
export const authMiddleware: Middleware<{}, RootState> =
  (store) => (next) => (action) => {
    const result = next(action)

    // Handle authentication state changes
    switch (action.type) {
      case 'auth/loginSuccess':
        // Initialize user session
        store.dispatch({
          type: 'ui/addNotification',
          payload: {
            type: 'success',
            title: 'Login Successful',
            message: `Welcome back, ${action.payload.user.username}!`,
            duration: 3000,
          },
        })
        break

      case 'auth/loginFailure':
        // Handle login failure
        store.dispatch({
          type: 'ui/addNotification',
          payload: {
            type: 'error',
            title: 'Login Failed',
            message: action.payload,
            duration: 5000,
          },
        })
        break

      case 'auth/logout':
        // Handle logout
        store.dispatch({
          type: 'ui/addNotification',
          payload: {
            type: 'info',
            title: 'Logged Out',
            message: 'You have been successfully logged out',
            duration: 3000,
          },
        })
        break

      case 'auth/refreshTokenFailure':
        // Handle refresh token failure
        store.dispatch({
          type: 'ui/addNotification',
          payload: {
            type: 'warning',
            title: 'Session Expired',
            message: 'Please log in again to continue',
            duration: 5000,
          },
        })
        break
    }

    return result
  }

// WebSocket middleware
export const websocketMiddleware: Middleware<{}, RootState> =
  (store) => (next) => (action) => {
    const result = next(action)

    // Handle WebSocket-related actions
    if (action.type?.startsWith('websocket/')) {
      const state = store.getState()

      // Only process WebSocket actions if authenticated
      if (state.auth.isAuthenticated) {
        switch (action.type) {
          case 'websocket/connect':
            // Initialize WebSocket connection
            console.log('WebSocket connection initiated')
            break

          case 'websocket/disconnect':
            // Close WebSocket connection
            console.log('WebSocket connection closed')
            break

          case 'websocket/message':
            // Handle incoming WebSocket message
            const message = action.payload

            // Update relevant state based on message type
            switch (message.type) {
              case 'strategy_update':
                store.dispatch({
                  type: 'strategy/updateStrategy',
                  payload: message.data,
                })
                break

              case 'performance_update':
                store.dispatch({
                  type: 'dashboard/updatePerformance',
                  payload: message.data,
                })
                break

              case 'new_signals':
                store.dispatch({
                  type: 'ui/addNotification',
                  payload: {
                    type: 'info',
                    title: 'New Signals',
                    message: `Received ${message.data.length} new signals`,
                    duration: 3000,
                  },
                })
                break

              default:
                console.log('Unknown WebSocket message type:', message.type)
            }
            break
        }
      }
    }

    return result
  }

// Combine all middleware
export const middleware = [
  sessionMiddleware,
  errorMiddleware,
  performanceMiddleware,
  apiRequestMiddleware,
  authMiddleware,
  websocketMiddleware,
]