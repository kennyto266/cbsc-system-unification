/**
 * Redux Store Configuration
 * 版本: 1.0.0
 * 描述: Redux Toolkit store 配置和設置
 */

import { configureStore } from '@reduxjs/toolkit';
import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';
import { setupListeners } from '@reduxjs/toolkit/query';

// Import slices
import authSlice from './slices/authSlice';
import uiSlice from './slices/uiSlice';
import dashboardSlice from './slices/dashboardSlice';
import strategySlice from './slices/strategySlice';

// Import API services
import { authApi, strategyApi, dashboardApi, userApi, marketDataApi, realtimeApi } from './services';

// Store configuration
export const store = configureStore({
  reducer: {
    // UI state
    auth: authSlice,
    ui: uiSlice,
    dashboard: dashboardSlice,
    strategy: strategySlice,

    // API services
    [authApi.reducerPath]: authApi.reducer,
    [strategyApi.reducerPath]: strategyApi.reducer,
    [dashboardApi.reducerPath]: dashboardApi.reducer,
    [userApi.reducerPath]: userApi.reducer,
    [marketDataApi.reducerPath]: marketDataApi.reducer,
    [realtimeApi.reducerPath]: realtimeApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types
        ignoredActions: [
          // RTK Query actions
          'authApi/executeQuery/pending',
          'authApi/executeQuery/fulfilled',
          'authApi/executeQuery/rejected',
          'strategyApi/executeQuery/pending',
          'strategyApi/executeQuery/fulfilled',
          'strategyApi/executeQuery/rejected',
          'dashboardApi/executeQuery/pending',
          'dashboardApi/executeQuery/fulfilled',
          'dashboardApi/executeQuery/rejected',
          'userApi/executeQuery/pending',
          'userApi/executeQuery/fulfilled',
          'userApi/executeQuery/rejected',
          'marketDataApi/executeQuery/pending',
          'marketDataApi/executeQuery/fulfilled',
          'marketDataApi/executeQuery/rejected',
          'realtimeApi/executeQuery/pending',
          'realtimeApi/executeQuery/fulfilled',
          'realtimeApi/executeQuery/rejected',
        ],
        // Ignore these field paths in all actions
        ignoredPaths: [
          'api',
          'strategyApi',
          'dashboardApi',
          'userApi',
          'marketDataApi',
          'realtimeApi',
        ],
      },
    })
      .concat(
        authApi.middleware,
        strategyApi.middleware,
        dashboardApi.middleware,
        userApi.middleware,
        marketDataApi.middleware,
        realtimeApi.middleware
      ),
  devTools: process.env.NODE_ENV !== 'production',
});

// Setup listeners for refetchOnFocus/refetchOnReconnect behaviors
setupListeners(store.dispatch);

// Export types
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Export typed hooks
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

// Export store instance
export default store;