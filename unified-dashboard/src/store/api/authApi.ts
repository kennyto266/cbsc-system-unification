import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type { User } from '@types/index'
import type { RootState } from '../index'

// Base query with authentication
const baseQuery = fetchBaseQuery({
  baseUrl: '/api/auth',
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.token
    if (token) {
      headers.set('authorization', `Bearer ${token}`)
    }
    headers.set('content-type', 'application/json')
    return headers
  },
})

export const authApi = createApi({
  reducerPath: 'authApi',
  baseQuery,
  tagTypes: ['User', 'Auth'],
  endpoints: (builder) => ({
    // Authentication
    login: builder.mutation<{
      user: User;
      token: string;
      expiresIn: number;
    }, {
      email: string;
      password: string;
      remember?: boolean;
    }>({
      query: (credentials) => ({
        url: '/login',
        method: 'POST',
        body: credentials,
      }),
      invalidatesTags: ['Auth'],
    }),

    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/logout',
        method: 'POST',
      }),
      invalidatesTags: ['Auth', 'User'],
    }),

    register: builder.mutation<{
      user: User;
      token: string;
      expiresIn: number;
    }, {
      username: string;
      email: string;
      password: string;
      firstName?: string;
      lastName?: string;
    }>({
      query: (userData) => ({
        url: '/register',
        method: 'POST',
        body: userData,
      }),
    }),

    refreshToken: builder.mutation<{
      token: string;
      expiresIn: number;
    }, void>({
      query: () => ({
        url: '/refresh',
        method: 'POST',
      }),
    }),

    // User management
    getCurrentUser: builder.query<User, void>({
      query: () => '/me',
      providesTags: ['User'],
    }),

    updateProfile: builder.mutation<User, {
      firstName?: string;
      lastName?: string;
      avatar?: string;
      preferences?: Record<string, any>;
    }>({
      query: (updates) => ({
        url: '/me',
        method: 'PUT',
        body: updates,
      }),
      invalidatesTags: ['User'],
    }),

    changePassword: builder.mutation<void, {
      currentPassword: string;
      newPassword: string;
      confirmPassword: string;
    }>({
      query: (passwordData) => ({
        url: '/me/password',
        method: 'PUT',
        body: passwordData,
      }),
    }),

    // Email verification
    verifyEmail: builder.mutation<void, {
      token: string;
    }>({
      query: ({ token }) => ({
        url: '/verify-email',
        method: 'POST',
        body: { token },
      }),
      invalidatesTags: ['User'],
    }),

    resendVerificationEmail: builder.mutation<void, void>({
      query: () => ({
        url: '/resend-verification',
        method: 'POST',
      }),
    }),

    // Password reset
    requestPasswordReset: builder.mutation<void, {
      email: string;
    }>({
      query: ({ email }) => ({
        url: '/request-password-reset',
        method: 'POST',
        body: { email },
      }),
    }),

    resetPassword: builder.mutation<void, {
      token: string;
      newPassword: string;
      confirmPassword: string;
    }>({
      query: (resetData) => ({
        url: '/reset-password',
        method: 'POST',
        body: resetData,
      }),
    }),

    // Multi-factor authentication
    enableMFA: builder.mutation<{
      secret: string;
      qrCode: string;
      backupCodes: string[];
    }, void>({
      query: () => ({
        url: '/mfa/enable',
        method: 'POST',
      }),
      invalidatesTags: ['User'],
    }),

    confirmMFA: builder.mutation<void, {
      token: string;
      backupCode?: string;
    }>({
      query: (confirmation) => ({
        url: '/mfa/confirm',
        method: 'POST',
        body: confirmation,
      }),
      invalidatesTags: ['User'],
    }),

    disableMFA: builder.mutation<void, {
      token: string;
      password: string;
    }>({
      query: (disablingData) => ({
        url: '/mfa/disable',
        method: 'POST',
        body: disablingData,
      }),
      invalidatesTags: ['User'],
    }),

    generateBackupCodes: builder.mutation<string[], void>({
      query: () => ({
        url: '/mfa/backup-codes',
        method: 'POST',
      }),
    }),

    // Social authentication
    getSocialAuthUrls: builder.query<Record<string, string>, void>({
      query: () => '/social',
    }),

    // Sessions and devices
    getActiveSessions: builder.query<Array<{
      id: string;
      device: string;
      browser: string;
      ip: string;
      location: string;
      lastActive: string;
      isCurrent: boolean;
    }>, void>({
      query: () => '/sessions',
    }),

    revokeSession: builder.mutation<void, {
      sessionId: string;
    }>({
      query: ({ sessionId }) => ({
        url: `/sessions/${sessionId}`,
        method: 'DELETE',
      }),
    }),

    revokeAllSessions: builder.mutation<void, void>({
      query: () => ({
        url: '/sessions',
        method: 'DELETE',
      }),
    }),
  }),
})

export const {
  // Authentication
  useLoginMutation,
  useLogoutMutation,
  useRegisterMutation,
  useRefreshTokenMutation,

  // User management
  useGetCurrentUserQuery,
  useUpdateProfileMutation,
  useChangePasswordMutation,

  // Email verification
  useVerifyEmailMutation,
  useResendVerificationEmailMutation,

  // Password reset
  useRequestPasswordResetMutation,
  useResetPasswordMutation,

  // Multi-factor authentication
  useEnableMFAMutation,
  useConfirmMFAMutation,
  useDisableMFAMutation,
  useGenerateBackupCodesMutation,

  // Social authentication
  useGetSocialAuthUrlsQuery,

  // Sessions and devices
  useGetActiveSessionsQuery,
  useRevokeSessionMutation,
  useRevokeAllSessionsMutation,
} = authApi

export default authApi