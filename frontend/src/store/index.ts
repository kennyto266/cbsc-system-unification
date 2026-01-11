// CBSC Trading System - Unified Redux Store Configuration
// Centralized state management with RTK Query

import { configureStore, combineReducers } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { useDispatch, useSelector } from 'react-redux';

// Import feature slices
import authReducer from './slices/authSlice';
import strategiesReducer from './slices/strategiesSlice';
import strategySlice from './slices/strategySlice';
import dashboardSlice from './slices/dashboardSlice';
import economicDataReducer from './slices/economicDataSlice';
import monitoringReducer from './slices/monitoringSlice';
import performanceAnalyticsReducer from './slices/performanceAnalyticsSlice';

// Import RTK Query API slice
import { apiSlice, apiReducer, apiMiddleware } from './api/apiSlice';

// Root reducer combining all slices and API reducers
const rootReducer = combineReducers({
  // Feature slices
  auth: authReducer,
  strategies: strategiesReducer,
  strategy: strategySlice,
  dashboard: dashboardSlice,
  economicData: economicDataReducer,
  monitoring: monitoringReducer,
  performanceAnalytics: performanceAnalyticsReducer,

  // RTK Query API reducer
  [apiSlice.reducerPath]: apiReducer,
});

// Configure store with middleware
export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore RTK Query action types and some specific paths
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
        ignoredPaths: ['auth.token', 'auth.refreshToken'],
      },
    })
      .concat(apiMiddleware),
  devTools: import.meta.env.DEV,
});

// Enable refetchOnFocus/refetchOnReconnect behaviors
setupListeners(store.dispatch);

// Export types for use in components
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Export typed hooks - re-export from hooks to maintain single source of truth
export { useAppDispatch, useAppSelector } from '../hooks/redux';

// Re-export the API slice as 'api' for convenience
export { api } from './api/apiSlice';
