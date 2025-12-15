import { configureStore } from '@reduxjs/toolkit'
import { setupListeners } from '@reduxjs/toolkit/query'
import { authSlice } from './slices/authSlice'
import { strategySlice } from './slices/strategySlice'
import { dashboardSlice } from './slices/dashboardSlice'
import { uiSlice } from './slices/uiSlice'
import { apiSlice } from './api/apiSlice'

// Configure store with enhanced middleware
export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    strategy: strategySlice.reducer,
    dashboard: dashboardSlice.reducer,
    ui: uiSlice.reducer,
    api: apiSlice.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types
        ignoredActions: [
          'persist/PERSIST',
          'persist/REHYDRATE',
          'persist/PAUSE',
          'persist/PURGE',
          'persist/REGISTER',
        ],
        // Ignore these paths in the state
        ignoredPaths: ['api'],
      },
      // Configure immutable check
      immutableCheck: {
        ignoredPaths: ['api'],
      },
    })
      .concat(apiSlice.middleware)
      .concat(
        // Custom middleware for session management
        (store) => (next) => (action) => {
          // Handle auth-related session management
          if (action.type?.startsWith('auth/')) {
            // Update last activity timestamp
            const currentState = store.getState()
            if (currentState.auth?.isAuthenticated) {
              store.dispatch({
                type: 'auth/updateLastActivity',
                payload: undefined
              })
            }
          }

          return next(action)
        }
      )
      .concat(
        // Custom middleware for notifications
        (store) => (next) => (action) => {
          const result = next(action)

          // Auto-remove success notifications after 3 seconds
          if (action.type === 'ui/addNotification' &&
              action.payload?.type === 'success' &&
              !action.payload?.persistent) {
            setTimeout(() => {
              const currentState = store.getState()
              const notification = currentState.ui.notifications.find(
                (n: any) => n.timestamp === action.payload.timestamp
              )
              if (notification) {
                store.dispatch({
                  type: 'ui/removeNotification',
                  payload: notification.id
                })
              }
            }, 3000)
          }

          return result
        }
      ),
  devTools: process.env.NODE_ENV !== 'production',
})

// Enable refetchOnFocus/refetchOnReconnect behaviors
setupListeners(store.dispatch)

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

// Export specific actions to avoid conflicts
export { authSlice } from './slices/authSlice'
export { strategySlice } from './slices/strategySlice'
export { uiSlice } from './slices/uiSlice'
export { dashboardSlice } from './slices/dashboardSlice'
export { apiSlice } from './api/apiSlice'

// Types are already exported above