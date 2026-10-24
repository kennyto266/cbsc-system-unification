import { createApi, fetchBaseQuery, BaseQueryFn } from '@reduxjs/toolkit/query/react'
import { RootState } from '../../types/store'
import { refreshAuth } from '../slices/authSlice'
import { logout } from '../slices/authSlice'

// Enhanced base query with auth and error handling
const baseQuery = fetchBaseQuery({
  baseUrl: '/api',
  prepareHeaders: (headers, { getState, endpoint }) => {
    // Get token from auth state
    const token = (getState() as RootState).auth.token
    if (token) {
      headers.set('authorization', `Bearer ${token}`)
    }

    // Add custom headers for specific endpoints
    if (endpoint === 'uploadFile') {
      headers.set('Content-Type', 'multipart/form-data')
    }

    return headers
  },
  // Response timeout in milliseconds
  timeout: 30000,
})

// Base query with automatic token refresh
const baseQueryWithReauth: BaseQueryFn = async (args, api, extraOptions) => {
  let result = await baseQuery(args, api, extraOptions)

  // Handle 401 Unauthorized - attempt to refresh token
  if (result.error && result.error.status === 401) {
    console.log('Token expired, attempting to refresh...')

    // Try to refresh the token
    const refreshResult = await baseQuery(
      {
        url: '/auth/refresh',
        method: 'POST',
        body: {
          refreshToken: localStorage.getItem('cbsc_refresh_token'),
        },
      },
      api,
      extraOptions
    )

    if (refreshResult.data) {
      // Token refresh successful, retry the original request
      const { token } = refreshResult.data as any
      api.dispatch(refreshAuth(token))

      // Retry the original request with new token
      result = await baseQuery(args, api, extraOptions)
    } else {
      // Token refresh failed, logout user
      api.dispatch(logout())
      localStorage.removeItem('cbsc_token')
      localStorage.removeItem('cbsc_refresh_token')
    }
  }

  // Handle 403 Forbidden
  if (result.error && result.error.status === 403) {
    console.error('Access forbidden:', result.error.data)
    // Could dispatch an action to show a permission denied notification
  }

  // Handle 429 Rate Limit
  if (result.error && result.error.status === 429) {
    console.warn('Rate limit exceeded, backing off...')
    // Implement exponential backoff for retries
  }

  return result
}

// Create base API slice
export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: [
    // Auth tags
    'User',
    'UserProfile',
    'Security',
    // Strategy tags
    'Strategy',
    'StrategyList',
    'StrategyPerformance',
    'StrategyExecution',
    'Backtest',
    // Market tags
    'MarketData',
    'Ticker',
    'OHLC',
    'Indicator',
    // Analytics tags
    'Analytics',
    'Portfolio',
    'Performance',
    'Risk',
    // Dashboard tags
    'Dashboard',
    'Alert',
    'Widget',
    // System tags
    'SystemHealth',
    'Log',
  ],
  // Global configuration
  keepUnusedDataFor: 60, // Keep unused data for 60 seconds
  refetchOnMountOrArgChange: 30, // Refetch after 30 seconds
  refetchOnFocus: true,
  refetchOnReconnect: true,
  // Endpoints are defined in separate API files
  endpoints: () => ({}),
})

// Export hooks for using the API
export const {
  useGetQuery,
  useGetAllQuery,
  useGetEntityQuery,
  useCreateMutation,
  useUpdateMutation,
  usePatchMutation,
  useDeleteMutation,
} = baseApi

export default baseApi