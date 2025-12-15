import { createApi } from '@reduxjs/toolkit/query/react'
import type { RootState } from '../index'
import {
  baseQueryWithReauth,
  providesList,
  invalidatesList,
} from '../../api/baseQuery'
import type { AuthResponse, User } from '../../types/auth'
import { Strategy } from '../../types/strategy'
import type { PaginatedResponse } from '../../types/api'

// Create API slice with enhanced configuration
export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: [
    'User',
    'Strategy',
    'Execution',
    'Backtest',
    'Signal',
    'Performance',
    'Settings',
    'Notification',
    'MarketData',
    'WebSocket',
    'Role',
    'Permission',
    'Portfolio',
  ],
  keepUnusedDataFor: 60, // Keep unused data for 1 minute
  refetchOnMountOrArgChange: 30, // Refetch after 30 seconds
  refetchOnFocus: true,
  refetchOnReconnect: true,
  endpoints: (builder) => ({
    // Authentication endpoints
    login: builder.mutation<AuthResponse, {
      username: string
      password: string
      rememberMe?: boolean
    }>({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
      }),
      invalidatesTags: [{ type: 'User', id: 'LIST' }],
    }),

    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/api/auth/logout',
        method: 'POST',
      }),
    }),

    refreshToken: builder.mutation<AuthResponse, {
      refreshToken: string
    }>({
      query: ({ refreshToken }) => ({
        url: '/api/auth/refresh',
        method: 'POST',
        body: { refreshToken },
      }),
    }),

    getCurrentUser: builder.query<User, void>({
      query: () => '/api/auth/me',
      providesTags: ['User'],
    }),

    updateProfile: builder.mutation<User, Partial<User>>({
      query: (userData) => ({
        url: '/api/auth/profile',
        method: 'PUT',
        body: userData,
      }),
      invalidatesTags: ['User'],
    }),

    changePassword: builder.mutation<void, {
      currentPassword: string
      newPassword: string
    }>({
      query: (passwordData) => ({
        url: '/api/auth/change-password',
        method: 'POST',
        body: passwordData,
      }),
    }),

    // Strategy endpoints with enhanced caching
    getStrategies: builder.query<PaginatedResponse<Strategy>, {
      page?: number
      pageSize?: number
      status?: string
      category?: string
      search?: string
    }>({
      query: (params) => ({
        url: '/strategies',
        params,
      }),
      providesTags: (result) => providesList(result?.items || [], 'Strategy'),
      transformResponse: (response: any) => ({
        items: response.strategies || response.data || [],
        total: response.total || response.count || 0,
        page: response.page || 1,
        pageSize: response.pageSize || 20,
        totalPages: Math.ceil((response.total || 0) / 20),
      }),
    }),

    getStrategy: builder.query<Strategy, string>({
      query: (id) => `/strategies/${id}`,
      providesTags: (result, error, id) => [{ type: 'Strategy', id }],
    }),

    createStrategy: builder.mutation<Strategy, Partial<Strategy>>({
      query: (strategy) => ({
        url: '/strategies',
        method: 'POST',
        body: strategy,
      }),
      invalidatesTags: [{ type: 'Strategy', id: 'LIST' }],
    }),

    updateStrategy: builder.mutation<Strategy, {
      id: string
      data: Partial<Strategy>
    }>({
      query: ({ id, data }) => ({
        url: `/strategies/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Strategy', id },
        { type: 'Strategy', id: 'LIST' },
      ],
    }),

    deleteStrategy: builder.mutation<void, string>({
      query: (id) => ({
        url: `/strategies/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: [{ type: 'Strategy', id }, { type: 'Strategy', id: 'LIST' }],
    }),

    // Portfolio endpoints
    getPortfolio: builder.query<any, void>({
      query: () => '/api/portfolio',
      providesTags: ['Portfolio'],
    }),

    // Signals endpoints
    getSignals: builder.query<any[], {
      strategyId?: string
      limit?: number
      offset?: number
    }>({
      query: (params) => ({
        url: '/api/signals',
        params,
      }),
      providesTags: ['Signal'],
    }),

    // Performance endpoints
    getPerformance: builder.query<any, {
      strategyId?: string
      timeframe?: string
    }>({
      query: (params) => ({
        url: '/api/performance',
        params,
      }),
      providesTags: ['Performance'],
    }),

    // Settings endpoints
    getSettings: builder.query<any, void>({
      query: () => '/api/settings',
      providesTags: ['Settings'],
    }),

    updateSettings: builder.mutation<any, Partial<any>>({
      query: (settings) => ({
        url: '/api/settings',
        method: 'PUT',
        body: settings,
      }),
      invalidatesTags: ['Settings'],
    }),

    // Notifications endpoints
    getNotifications: builder.query<any[], {
      unread?: boolean
      limit?: number
    }>({
      query: (params) => ({
        url: '/api/notifications',
        params,
      }),
      providesTags: ['Notification'],
    }),

    markNotificationRead: builder.mutation<void, string>({
      query: (id) => ({
        url: `/api/notifications/${id}/read`,
        method: 'POST',
      }),
      invalidatesTags: ['Notification'],
    }),

    // Health check endpoint
    healthCheck: builder.query<any, void>({
      query: () => '/api/health',
    }),
  }),
})

// Export hooks for usage in functional components
export const {
  // Authentication
  useLoginMutation,
  useLogoutMutation,
  useRefreshTokenMutation,
  useGetCurrentUserQuery,
  useUpdateProfileMutation,
  useChangePasswordMutation,

  // Strategies
  useGetStrategiesQuery,
  useGetStrategyQuery,
  useCreateStrategyMutation,
  useUpdateStrategyMutation,
  useDeleteStrategyMutation,

  // Portfolio
  useGetPortfolioQuery,

  // Signals
  useGetSignalsQuery,

  // Performance
  useGetPerformanceQuery,

  // Settings
  useGetSettingsQuery,
  useUpdateSettingsMutation,

  // Notifications
  useGetNotificationsQuery,
  useMarkNotificationReadMutation,

  // Health
  useHealthCheckQuery,
} = apiSlice