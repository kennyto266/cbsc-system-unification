import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type { RootState } from '../../store'
import {
  baseQueryWithReauth,
  providesList,
  invalidatesList,
} from '../baseQuery'
import type {
  LoginCredentials,
  RegisterData,
  AuthResponse,
  User,
  ResetPasswordRequest,
  ResetPasswordConfirm,
  ChangePasswordData,
  UpdateProfileData,
} from '../../types/auth'

// Authentication API slice
export const authApi = createApi({
  reducerPath: 'authApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['User', 'Auth'],
  keepUnusedDataFor: 300, // Keep auth data for 5 minutes
  endpoints: (builder) => ({
    // Login
    login: builder.mutation<AuthResponse, LoginCredentials>({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
      }),
      invalidatesTags: ['User'],
      transformResponse: (response: AuthResponse) => {
        // Store tokens in localStorage as backup
        if (response.token) {
          localStorage.setItem('auth_token', response.token)
        }
        if (response.refreshToken) {
          localStorage.setItem('refresh_token', response.refreshToken)
        }
        return response
      },
    }),

    // Logout
    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/auth/logout',
        method: 'POST',
      }),
      onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
        try {
          await queryFulfilled
          // Clear local storage
          localStorage.removeItem('auth_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
        } catch (error) {
          // Even if logout fails on server, clear local data
          localStorage.removeItem('auth_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
        }
        // Clear auth state
        dispatch({ type: 'auth/logout' })
      },
    }),

    // Refresh token
    refreshToken: builder.mutation<AuthResponse, { refreshToken: string }>({
      query: ({ refreshToken }) => ({
        url: '/auth/refresh',
        method: 'POST',
        body: { refreshToken },
      }),
    }),

    // Register
    register: builder.mutation<AuthResponse, RegisterData>({
      query: (userData) => ({
        url: '/auth/register',
        method: 'POST',
        body: userData,
      }),
      invalidatesTags: ['User'],
    }),

    // Get current user
    getCurrentUser: builder.query<User, void>({
      query: () => '/auth/me',
      providesTags: ['User'],
      transformResponse: (response: User) => {
        // Store user data in localStorage as backup
        try {
          localStorage.setItem('user', JSON.stringify(response))
        } catch (error) {
          console.error('Failed to store user data:', error)
        }
        return response
      },
    }),

    // Update profile
    updateProfile: builder.mutation<User, UpdateProfileData>({
      query: (userData) => ({
        url: '/auth/profile',
        method: 'PUT',
        body: userData,
      }),
      invalidatesTags: ['User'],
      transformResponse: (response: User) => {
        // Update stored user data
        try {
          localStorage.setItem('user', JSON.stringify(response))
        } catch (error) {
          console.error('Failed to update stored user data:', error)
        }
        return response
      },
    }),

    // Change password
    changePassword: builder.mutation<void, ChangePasswordData>({
      query: (passwordData) => ({
        url: '/auth/change-password',
        method: 'POST',
        body: passwordData,
      }),
    }),

    // Reset password request
    resetPassword: builder.mutation<void, ResetPasswordRequest>({
      query: (resetData) => ({
        url: '/auth/reset-password',
        method: 'POST',
        body: resetData,
      }),
    }),

    // Reset password confirmation
    resetPasswordConfirm: builder.mutation<void, ResetPasswordConfirm>({
      query: (confirmData) => ({
        url: '/auth/reset-password/confirm',
        method: 'POST',
        body: confirmData,
      }),
    }),

    // Verify email
    verifyEmail: builder.mutation<void, { token: string }>({
      query: ({ token }) => ({
        url: '/auth/verify-email',
        method: 'POST',
        body: { token },
      }),
    }),

    // Resend verification email
    resendVerification: builder.mutation<void, { email: string }>({
      query: ({ email }) => ({
        url: '/auth/resend-verification',
        method: 'POST',
        body: { email },
      }),
    }),

    // Enable 2FA
    enable2FA: builder.mutation<any, void>({
      query: () => ({
        url: '/auth/2fa/enable',
        method: 'POST',
      }),
    }),

    // Verify 2FA
    verify2FA: builder.mutation<any, { code: string }>({
      query: ({ code }) => ({
        url: '/auth/2fa/verify',
        method: 'POST',
        body: { code },
      }),
    }),

    // Disable 2FA
    disable2FA: builder.mutation<void, { code: string }>({
      query: ({ code }) => ({
        url: '/auth/2fa/disable',
        method: 'POST',
        body: { code },
      }),
    }),

    // Get backup codes
    getBackupCodes: builder.mutation<string[], void>({
      query: () => ({
        url: '/auth/2fa/backup-codes',
        method: 'POST',
      }),
    }),

    // Get user sessions
    getSessions: builder.query<any[], void>({
      query: () => '/auth/sessions',
      providesTags: ['Auth'],
    }),

    // Revoke session
    revokeSession: builder.mutation<void, { sessionId: string }>({
      query: ({ sessionId }) => ({
        url: `/auth/sessions/${sessionId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Auth'],
    }),

    // Revoke all sessions
    revokeAllSessions: builder.mutation<void, void>({
      query: () => ({
        url: '/auth/sessions/revoke-all',
        method: 'POST',
      }),
      invalidatesTags: ['Auth'],
    }),

    // Get security settings
    getSecuritySettings: builder.query<any, void>({
      query: () => '/auth/security/settings',
      providesTags: ['Auth'],
    }),

    // Update security settings
    updateSecuritySettings: builder.mutation<any, Partial<any>>({
      query: (settings) => ({
        url: '/auth/security/settings',
        method: 'PUT',
        body: settings,
      }),
      invalidatesTags: ['Auth'],
    }),
  }),
})

// Export hooks
export const {
  // Authentication
  useLoginMutation,
  useLogoutMutation,
  useRefreshTokenMutation,
  useRegisterMutation,
  useGetCurrentUserQuery,

  // Profile management
  useUpdateProfileMutation,
  useChangePasswordMutation,

  // Password reset
  useResetPasswordMutation,
  useResetPasswordConfirmMutation,

  // Email verification
  useVerifyEmailMutation,
  useResendVerificationMutation,

  // Two-factor authentication
  useEnable2FAMutation,
  useVerify2FAMutation,
  useDisable2FAMutation,
  useGetBackupCodesMutation,

  // Session management
  useGetSessionsQuery,
  useRevokeSessionMutation,
  useRevokeAllSessionsMutation,

  // Security settings
  useGetSecuritySettingsQuery,
  useUpdateSecuritySettingsMutation,
} = authApi

// Utility hooks
export const useAuthState = () => {
  const { data: user, isLoading, error } = useGetCurrentUserQuery(undefined, {
    skip: !localStorage.getItem('auth_token'), // Skip if no token
  })

  return {
    user,
    isAuthenticated: !!user && !isLoading,
    isLoading,
    error,
  }
}

export const useAuthActions = () => {
  const [login] = useLoginMutation()
  const [logout] = useLogoutMutation()
  const [refreshToken] = useRefreshTokenMutation()

  return {
    login,
    logout,
    refreshToken,
  }
}