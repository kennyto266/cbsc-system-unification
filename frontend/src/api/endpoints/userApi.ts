import { createApi } from '@reduxjs/toolkit/query/react'
import {
  baseQueryWithReauth,
  createApiTag,
  providesList,
} from '../baseQuery'
import type { User, Role, Permission } from '../../types/auth'
import type { PaginatedResponse } from '../../types/api'

// User management API slice
export const userApi = createApi({
  reducerPath: 'userApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['User', 'Role', 'Permission', 'Notification', 'Preference'],
  keepUnusedDataFor: 300, // Keep user data for 5 minutes
  endpoints: (builder) => ({
    // Get users with pagination
    getUsers: builder.query<PaginatedResponse<User>, {
      page?: number
      pageSize?: number
      search?: string
      role?: string
      status?: string
      sortBy?: string
      sortOrder?: 'asc' | 'desc'
    }>({
      query: (params) => ({
        url: '/users',
        params,
      }),
      providesTags: (result) => providesList(result?.items || [], 'User'),
      transformResponse: (response: any, meta, arg) => {
        return {
          items: response.users || response.data || [],
          total: response.total || response.count || 0,
          page: arg.page || 1,
          pageSize: arg.pageSize || 20,
          totalPages: Math.ceil((response.total || 0) / (arg.pageSize || 20)),
        }
      },
    }),

    // Get user details
    getUser: builder.query<User, string>({
      query: (id) => `/users/${id}`,
      providesTags: (result, error, id) => [{ type: 'User', id }],
    }),

    // Create user
    createUser: builder.mutation<User, Partial<User> & {
      password: string
      sendInvite?: boolean
    }>({
      query: (userData) => ({
        url: '/users',
        method: 'POST',
        body: userData,
      }),
      invalidatesTags: [{ type: 'User', id: 'LIST' }],
    }),

    // Update user
    updateUser: builder.mutation<User, {
      id: string
      data: Partial<User>
    }>({
      query: ({ id, data }) => ({
        url: `/users/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'User', id },
        { type: 'User', id: 'LIST' },
      ],
    }),

    // Delete user
    deleteUser: builder.mutation<void, string>({
      query: (id) => ({
        url: `/users/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: [{ type: 'User', id: 'LIST' }],
    }),

    // Update user status (activate/deactivate)
    updateUserStatus: builder.mutation<User, {
      id: string
      status: 'active' | 'inactive'
    }>({
      query: ({ id, status }) => ({
        url: `/users/${id}/status`,
        method: 'PATCH',
        body: { status },
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'User', id },
        { type: 'User', id: 'LIST' },
      ],
    }),

    // Assign roles to user
    assignRoles: builder.mutation<User, {
      id: string
      roleIds: string[]
    }>({
      query: ({ id, roleIds }) => ({
        url: `/users/${id}/roles`,
        method: 'POST',
        body: { roleIds },
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'User', id },
        { type: 'User', id: 'LIST' },
      ],
    }),

    // Remove role from user
    removeRole: builder.mutation<User, {
      id: string
      roleId: string
    }>({
      query: ({ id, roleId }) => ({
        url: `/users/${id}/roles/${roleId}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'User', id },
        { type: 'User', id: 'LIST' },
      ],
    }),

    // Get user permissions
    getUserPermissions: builder.query<Permission[], string>({
      query: (id) => `/users/${id}/permissions`,
      providesTags: (result, error, id) => [{ type: 'Permission', id: `user-${id}` }],
    }),

    // Get user activity log
    getUserActivity: builder.query<any[], {
      id: string
      limit?: number
      offset?: number
      startDate?: string
      endDate?: string
    }>({
      query: ({ id, limit = 50, offset = 0, startDate, endDate }) => ({
        url: `/users/${id}/activity`,
        params: { limit, offset, startDate, endDate },
      }),
      providesTags: (result, error, { id }) => [{ type: 'User', id: `${id}-activity` }],
    }),

    // Update user password (admin)
    updateUserPassword: builder.mutation<void, {
      id: string
      password: string
      forceChange?: boolean
    }>({
      query: ({ id, password, forceChange }) => ({
        url: `/users/${id}/password`,
        method: 'POST',
        body: { password, forceChange },
      }),
    }),

    // Lock/Unlock user account
    lockAccount: builder.mutation<User, {
      id: string
      reason?: string
      duration?: number // in hours
    }>({
      query: ({ id, reason, duration }) => ({
        url: `/users/${id}/lock`,
        method: 'POST',
        body: { reason, duration },
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'User', id },
        { type: 'User', id: 'LIST' },
      ],
    }),

    // Unlock account
    unlockAccount: builder.mutation<User, string>({
      query: (id) => ({
        url: `/users/${id}/unlock`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'User', id },
        { type: 'User', id: 'LIST' },
      ],
    }),

    // Get roles
    getRoles: builder.query<PaginatedResponse<Role>, {
      page?: number
      pageSize?: number
      search?: string
    }>({
      query: (params) => ({
        url: '/roles',
        params,
      }),
      providesTags: (result) => providesList(result?.items || [], 'Role'),
      transformResponse: (response: any, meta, arg) => {
        return {
          items: response.roles || response.data || [],
          total: response.total || response.count || 0,
          page: arg.page || 1,
          pageSize: arg.pageSize || 20,
          totalPages: Math.ceil((response.total || 0) / (arg.pageSize || 20)),
        }
      },
    }),

    // Create role
    createRole: builder.mutation<Role, Omit<Role, 'id' | 'createdAt' | 'updatedAt'>>({
      query: (roleData) => ({
        url: '/roles',
        method: 'POST',
        body: roleData,
      }),
      invalidatesTags: [{ type: 'Role', id: 'LIST' }],
    }),

    // Update role
    updateRole: builder.mutation<Role, {
      id: string
      data: Partial<Role>
    }>({
      query: ({ id, data }) => ({
        url: `/roles/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Role', id },
        { type: 'Role', id: 'LIST' },
      ],
    }),

    // Delete role
    deleteRole: builder.mutation<void, string>({
      query: (id) => ({
        url: `/roles/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: [{ type: 'Role', id: 'LIST' }],
    }),

    // Get permissions
    getPermissions: builder.query<Permission[], {
      resource?: string
      action?: string
    }>({
      query: (params) => ({
        url: '/permissions',
        params,
      }),
      providesTags: ['Permission'],
    }),

    // Get user preferences
    getUserPreferences: builder.query<any, string>({
      query: (id) => `/users/${id}/preferences`,
      providesTags: (result, error, id) => [{ type: 'Preference', id }],
    }),

    // Update user preferences
    updateUserPreferences: builder.mutation<any, {
      id: string
      preferences: Record<string, any>
    }>({
      query: ({ id, preferences }) => ({
        url: `/users/${id}/preferences`,
        method: 'PUT',
        body: preferences,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Preference', id },
      ],
    }),

    // Get user notifications
    getUserNotifications: builder.query<any[], {
      id: string
      unread?: boolean
      limit?: number
    }>({
      query: ({ id, unread, limit = 20 }) => ({
        url: `/users/${id}/notifications`,
        params: { unread, limit },
      }),
      providesTags: (result, error, { id }) => [{ type: 'Notification', id }],
    }),

    // Mark notification as read
    markNotificationRead: builder.mutation<void, {
      userId: string
      notificationId: string
    }>({
      query: ({ userId, notificationId }) => ({
        url: `/users/${userId}/notifications/${notificationId}/read`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, { userId }) => [
        { type: 'Notification', id: userId },
      ],
    }),

    // Mark all notifications as read
    markAllNotificationsRead: builder.mutation<void, string>({
      query: (userId) => ({
        url: `/users/${userId}/notifications/read-all`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, { userId }) => [
        { type: 'Notification', id: userId },
      ],
    }),

    // Delete notification
    deleteNotification: builder.mutation<void, {
      userId: string
      notificationId: string
    }>({
      query: ({ userId, notificationId }) => ({
        url: `/users/${userId}/notifications/${notificationId}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, { userId }) => [
        { type: 'Notification', id: userId },
      ],
    }),

    // Get user statistics
    getUserStatistics: builder.query<any, string>({
      query: (id) => `/users/${id}/statistics`,
      providesTags: (result, error, id) => [{ type: 'User', id: `${id}-stats` }],
    }),
  }),
})

// Export hooks
export const {
  // User management
  useGetUsersQuery,
  useGetUserQuery,
  useCreateUserMutation,
  useUpdateUserMutation,
  useDeleteUserMutation,
  useUpdateUserStatusMutation,

  // Role management
  useAssignRolesMutation,
  useRemoveRoleMutation,
  useGetUserPermissionsQuery,
  useGetRolesQuery,
  useCreateRoleMutation,
  useUpdateRoleMutation,
  useDeleteRoleMutation,
  useGetPermissionsQuery,

  // User activity and security
  useGetUserActivityQuery,
  useUpdateUserPasswordMutation,
  useLockAccountMutation,
  useUnlockAccountMutation,

  // Preferences and notifications
  useGetUserPreferencesQuery,
  useUpdateUserPreferencesMutation,
  useGetUserNotificationsQuery,
  useMarkNotificationReadMutation,
  useMarkAllNotificationsReadMutation,
  useDeleteNotificationMutation,
  useGetUserStatisticsQuery,
} = userApi

// Utility hooks
export const useUsersWithFilters = (filters: any) => {
  return useGetUsersQuery(filters, {
    selectFromResult: ({ data, isLoading, error }) => ({
      users: data?.items || [],
      total: data?.total || 0,
      isLoading,
      error,
      hasMore: (data?.page || 1) * (data?.pageSize || 20) < (data?.total || 0),
    }),
  })
}

export const useUserManagement = (userId: string) => {
  const { data: user, isLoading: userLoading } = useGetUserQuery(userId)
  const { data: permissions, isLoading: permissionsLoading } = useGetUserPermissionsQuery(userId)
  const { data: activity, isLoading: activityLoading } = useGetUserActivityQuery({ id: userId })
  const { data: stats, isLoading: statsLoading } = useGetUserStatisticsQuery(userId)

  return {
    user,
    permissions: permissions || [],
    activity: activity || [],
    statistics: stats,
    isLoading: userLoading || permissionsLoading || activityLoading || statsLoading,
  }
}