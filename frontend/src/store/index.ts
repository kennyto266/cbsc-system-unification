// CBSC Trading System - Unified Redux Store Configuration
// Centralized state management with RTK Query

import { configureStore, combineReducers } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { useDispatch, useSelector } from 'react-redux';

// Import feature slices
import { authSlice } from './slices/authSlice';
import { strategySlice } from './slices/strategySlice';
import { dashboardSlice } from './slices/dashboardSlice';
import economicStrategySlice from './slices/economicStrategySlice';
import economicDataSlice from './slices/economicDataSlice';

// Import RTK Query API slice
import { apiSlice } from './api/apiSlice';
// Import Strategy API slice
import { strategyApi } from '../api/endpoints/strategyApi';
// Import Auth API slice
import { authApi } from '../api/endpoints/authApi';
// Import User API slice
import { userApi } from '../api/endpoints/userApi';
// Import Portfolio API slice
import { portfolioApi } from '../api/endpoints/portfolioApi';
// Import Backtest API slice
import { backtestApi } from '../api/endpoints/backtestApi';

// Root reducer combining all slices and API reducers
const rootReducer = combineReducers({
  // Feature slices
  auth: authSlice.reducer,
  strategy: strategySlice.reducer,
  dashboard: dashboardSlice.reducer,
  economicStrategy: economicStrategySlice,
  economicData: economicDataSlice,

  // RTK Query API reducer
  [apiSlice.reducerPath]: apiSlice.reducer,
  // Strategy API reducer
  [strategyApi.reducerPath]: strategyApi.reducer,
  // Auth API reducer
  [authApi.reducerPath]: authApi.reducer,
  // User API reducer
  [userApi.reducerPath]: userApi.reducer,
  // Portfolio API reducer
  [portfolioApi.reducerPath]: portfolioApi.reducer,
  // Backtest API reducer
  [backtestApi.reducerPath]: backtestApi.reducer,
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
      .concat(apiSlice.middleware)
      .concat(strategyApi.middleware)
      .concat(authApi.middleware)
      .concat(userApi.middleware)
      .concat(portfolioApi.middleware)
      .concat(backtestApi.middleware),
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
