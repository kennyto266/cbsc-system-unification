import { configureStore } from '@reduxjs/toolkit'
import { setupListeners } from '@reduxjs/toolkit/query'

// Import reducers
import authReducer from './slices/authSlice'
import strategiesReducer from './slices/strategiesSlice'
import monitoringReducer from './slices/monitoringSlice'
import analyticsReducer from './slices/analyticsSlice'
import uiReducer from './slices/uiSlice'

// Import RTK Query APIs
import { authApi } from './api/authApi'
import { strategiesApi } from './api/strategiesApi'
import { monitoringApi } from './api/monitoringApi'
import { analyticsApi } from './api/analyticsApi'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    strategies: strategiesReducer,
    monitoring: monitoringReducer,
    analytics: analyticsReducer,
    ui: uiReducer,
    // RTK Query APIs
    [authApi.reducerPath]: authApi.reducer,
    [strategiesApi.reducerPath]: strategiesApi.reducer,
    [monitoringApi.reducerPath]: monitoringApi.reducer,
    [analyticsApi.reducerPath]: analyticsApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [
          // Ignore these action types
          'persist/PERSIST',
          'persist/REHYDRATE',
          'persist/REGISTER',
        ],
        ignoredPaths: ['api', 'monitoring.marketData'],
      },
    })
      .concat(authApi.middleware)
      .concat(strategiesApi.middleware)
      .concat(monitoringApi.middleware)
      .concat(analyticsApi.middleware),
  devTools: process.env.NODE_ENV !== 'production',
})

// Enable refetchOnFocus/refetchOnReconnect behaviors
setupListeners(store.dispatch)

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

export default store