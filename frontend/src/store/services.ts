/**
 * API Services Export
 * Centralizes all RTK Query API services for the Redux store
 */

// Import available APIs
export { authApi } from '../api/endpoints/authApi'
export { strategyApi } from '../api/endpoints/strategyApi'
export { userApi } from '../api/endpoints/userApi'
export { realtimeApi } from '../api/endpoints/realtimeApi'

// Placeholder exports for missing APIs (to be implemented)
// These are minimal API slices that won't break the store
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

// Dashboard API placeholder
export const dashboardApi = createApi({
  reducerPath: 'dashboardApi',
  baseQuery: fetchBaseQuery({ baseUrl: '/api' }),
  tagTypes: ['Dashboard'],
  endpoints: (builder) => ({
    getDashboard: builder.query({
      query: () => '/dashboard',
      providesTags: ['Dashboard'],
    }),
  }),
})

// Market Data API placeholder
export const marketDataApi = createApi({
  reducerPath: 'marketDataApi',
  baseQuery: fetchBaseQuery({ baseUrl: '/api' }),
  tagTypes: ['Market'],
  endpoints: (builder) => ({
    getMarketData: builder.query({
      query: () => '/market',
      providesTags: ['Market'],
    }),
  }),
})

// Export hooks for placeholder APIs
export const { useGetDashboardQuery } = dashboardApi
export const { useGetMarketDataQuery } = marketDataApi
