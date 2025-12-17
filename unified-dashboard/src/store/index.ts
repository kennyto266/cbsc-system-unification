import { configureStore } from '@reduxjs/toolkit'
import { setupListeners } from '@reduxjs/toolkit/query'
import { persistStore, persistReducer } from 'redux-persist'
import { combineReducers } from '@reduxjs/toolkit'

// Import persist configuration
import { persistConfig, authPersistConfig, uiPersistConfig } from './persistConfig'

// Import reducers
import authReducer from './slices/authSlice'
import uiReducer from './slices/uiSlice'
import marketReducer from './slices/marketSlice'
import strategiesReducer from './slices/strategiesSlice'
import monitoringReducer from './slices/monitoringSlice'
import analyticsReducer from './slices/analyticsSlice'
import dashboardReducer from './slices/dashboardSlice'
import technicalIndicatorsReducer from './slices/technicalIndicatorsSlice'

// Import RTK Query APIs
import { authApi } from './api/authApi'
import { marketApi } from './api/marketApi'
import { strategiesApi } from './api/strategiesApi'
import { monitoringApi } from './api/monitoringApi'
import { analyticsApi } from './api/analyticsApi'

// Import middleware
import {
  errorMiddleware,
  loadingMiddleware,
  websocketMiddleware,
  performanceMiddleware,
  apiLogger,
  cacheMiddleware,
  activityMiddleware,
} from './middleware'

// Combine reducers
const rootReducer = combineReducers({
  // Persisted reducers
  auth: persistReducer(authPersistConfig, authReducer),
  ui: persistReducer(uiPersistConfig, uiReducer),

  // Non-persisted reducers
  market: marketReducer,
  strategies: strategiesReducer,
  monitoring: monitoringReducer,
  analytics: analyticsReducer,
  dashboard: dashboardReducer,
  technicalIndicators: technicalIndicatorsReducer,
})

// Create persisted root reducer
const persistedReducer = persistReducer(persistConfig, rootReducer)

// Configure store with persistence and optimization
export const store = configureStore({
  reducer: {
    persisted: persistedReducer,
    // RTK Query APIs
    [authApi.reducerPath]: authApi.reducer,
    [marketApi.reducerPath]: marketApi.reducer,
    [strategiesApi.reducerPath]: strategiesApi.reducer,
    [monitoringApi.reducerPath]: monitoringApi.reducer,
    [analyticsApi.reducerPath]: analyticsApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [
          // Redux persist actions
          'persist/PERSIST',
          'persist/REHYDRATE',
          'persist/REGISTER',
          'persist/PURGE',
          'persist/FLUSH',
          'persist/PAUSE',
          'persist/PERSIST_REHYDRATE',
          // RTK Query actions
          'api/executeQuery/pending',
          'api/executeQuery/fulfilled',
          'api/executeQuery/rejected',
          // WebSocket actions
          'websocket/connect',
          'websocket/disconnect',
          'websocket/message',
          // Redux Persist REHYDRATE action
          'persist/REHYDRATE',
          'persist/PERSIST',
        ],
        ignoredPaths: [
          'api', // RTK Query internal state
          'persisted', // Persisted state from redux-persist
          'persisted.market.websocket', // WebSocket state
          'persisted.market.indicators', // Indicator data
          'persisted.monitoring.marketData', // Real-time market data
          'persisted.strategies.execution.positions', // Trading positions
          'persisted.strategies.execution.orders', // Trading orders
          'persisted.auth.token', // Sensitive data
          '_persist', // Redux Persist internal state
        ],
      },
      immutableCheck: {
        ignoredPaths: [
          'api', // RTK Query state is mutable internally
          'persisted.market.websocket', // WebSocket state updates frequently
          'persisted.market.indicators', // Real-time indicator updates
          '_persist', // Redux Persist internal state
        ],
      },
    })
      // Add custom middleware
      .concat(errorMiddleware)
      .concat(loadingMiddleware)
      .concat(websocketMiddleware)
      .concat(performanceMiddleware)
      .concat(apiLogger)
      .concat(cacheMiddleware)
      .concat(activityMiddleware)
      // Add RTK Query middleware
      .concat(authApi.middleware)
      .concat(marketApi.middleware)
      .concat(strategiesApi.middleware)
      .concat(monitoringApi.middleware)
      .concat(analyticsApi.middleware),
  devTools: {
    name: 'CBSC Trading Dashboard',
    trace: process.env.NODE_ENV !== 'production',
    traceLimit: 25,
    // In production, only show if explicitly enabled
    ...(process.env.NODE_ENV === 'production' && {
      maxAge: 100, // Keep only last 100 actions in production
      serialize: true, // Enable serialization for large states
    }),
  },
  // Preload some state if needed
  preloadedState: {},
})

// Create persistor for Redux Persist
export const persistor = persistStore(store)

// Enable refetchOnFocus/refetchOnReconnect behaviors
setupListeners(store.dispatch, {
  dispatch: store.dispatch,
  // Custom effect for background refetch
  effect: (action, listenerApi) => {
    // Add custom logic for refetch on focus/reconnect
    console.log('Refetching on focus/reconnect:', action.type)
  },
})

// Export types
export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

// Development helper: expose store to window for debugging
if (process.env.NODE_ENV === 'development') {
  (window as any).__REDUX_STORE__ = store
}

export default store