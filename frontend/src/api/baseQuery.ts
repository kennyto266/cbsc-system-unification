// Base query configuration for RTK Query API
import { fetchBaseQuery, retry, BaseQueryFn } from '@reduxjs/toolkit/query/react'
import type { FetchArgs, FetchBaseQueryError, FetchBaseQueryMeta } from '@reduxjs/toolkit/query'
import type { RootState } from '../store'
import { logout } from '../store/slices/authSlice'
import type { ApiError } from '../types/api'

// Helper to get env vars safely in both Jest and Vite
const getEnvVar = (key: string, defaultValue: string): string => {
  if (typeof process !== 'undefined' && process.env?.[key]) {
    return process.env[key];
  }
  try {
    const metaEnv = (0, eval)('typeof import.meta !== "undefined" ? import.meta.env : undefined');
    if (metaEnv?.[key]) return metaEnv[key];
  } catch {
    // Fall through
  }
  return defaultValue;
};

// API base configuration - point to backend server
const API_BASE_URL = getEnvVar('VITE_API_BASE_URL', 'http://localhost:3005')

const baseQuery = fetchBaseQuery({
  baseUrl: `${API_BASE_URL}/api`,
  prepareHeaders: (headers, { getState }) => {
    // Get token from Redux store
    const token = (getState() as RootState).auth.token
    if (token) {
      headers.set('authorization', `Bearer ${token}`)
    }

    // Set default headers
    headers.set('Content-Type', 'application/json')
    return headers
  },
  timeout: 30000, // 30 seconds timeout
})

// Error messages mapping
const ERROR_MESSAGES: Record<string, string> = {
  NETWORK_ERROR: '網絡連接錯誤，請檢查您的網絡設置',
  TIMEOUT_ERROR: '請求超時，請稍後再試',
  VALIDATION_ERROR: '輸入驗證失敗，請檢查您的輸入',
  AUTHENTICATION_FAILED: '認證失敗，請重新登錄',
  PERMISSION_DENIED: '權限不足，無法執行此操作',
  RESOURCE_NOT_FOUND: '請求的資源不存在',
  INTERNAL_SERVER_ERROR: '服務器內部錯誤，請稍後再試',
}

// Transform error response to standardized format
function transformError(error: FetchBaseQueryError): ApiError {
  const status = error.status as number || 500
  const data = error.data as any || {}

  return {
    status,
    code: data.code || `HTTP_${status}`,
    message: data.message || ERROR_MESSAGES[data.code] || (typeof error === 'string' ? error : '未知錯誤'),
    details: data.details,
    timestamp: new Date().toISOString(),
  }
}

// Base query with authentication
export const baseQueryWithAuth: BaseQueryFn<string | FetchArgs, unknown, ApiError> = async (
  args,
  api,
  extraOptions
) => {
  try {
    const result = await baseQuery(args, api, extraOptions)

    // Handle successful response
    if (result.data) {
      return result
    }

    // Handle error response
    if (result.error) {
      return {
        error: transformError(result.error)
      }
    }

    return result
  } catch (error: any) {
    return {
      error: {
        code: 'NETWORK_ERROR',
        message: ERROR_MESSAGES.NETWORK_ERROR,
        timestamp: new Date().toISOString(),
      }
    }
  }
}

// Base query with re-authentication
// NOTE: Token refresh temporarily disabled - backend doesn't have /auth/refresh endpoint yet
export const baseQueryWithReauth: BaseQueryFn<string | FetchArgs, unknown, ApiError> = async (
  args,
  api,
  extraOptions
) => {
  // Direct call without refresh logic for now
  return await baseQueryWithAuth(args, api, extraOptions)

  // TODO: Enable refresh logic once backend implements /auth/refresh endpoint
  /*
  let result = await baseQueryWithAuth(args, api, extraOptions)

  // If token expired or invalid (401), try to refresh
  if (result.error?.status === 401) {
    console.log('Token expired, attempting refresh...')

    // Try to refresh the token
    const refreshResult = await baseQuery(
      {
        url: '/auth/refresh',
        method: 'POST',
        body: { refreshToken: (api.getState() as RootState).auth.refreshToken }
      },
      api,
      extraOptions
    )

    if (refreshResult.data) {
      // Store the new token
      const newToken = (refreshResult.data as any).token || (refreshResult.data as any).accessToken
      // Update token in store (this would need to be handled by the auth slice)
      console.log('Token refreshed successfully')

      // Retry the original request with new token
      result = await baseQueryWithAuth(args, api, extraOptions)
    } else {
      // Refresh failed, logout user
      api.dispatch(logout())
    }
  }

  return result
  */
}

// Enhanced base query with retry logic
export const baseQueryWithRetry = retry(
  baseQueryWithReauth,
  {
    maxRetries: 3,
    retryCondition: (error: FetchBaseQueryError) => {
      const status = typeof error.status === 'number' ? error.status : parseInt(String(error.status))

      // Don't retry on authentication errors
      if (status === 401 || status === 403) return false

      // Don't retry on validation errors
      if (status === 400 || status === 422) return false

      // Retry on network errors and server errors
      return !error.status || status >= 500
    },
    retryDelay: (attempt: number) => {
      // Exponential backoff with jitter
      const delay = Math.min(1000 * Math.pow(2, attempt), 30000)
      const jitter = Math.random() * 1000
      return delay + jitter
    },
  }
)

// Helper functions for cache tags
export const providesList = <T extends { id: string | number }, R extends string>(
  results: T[] | undefined,
  tagType: R
) => {
  return results
    ? [...results.map(({ id }) => ({ type: tagType, id } as const)), { type: tagType, id: 'LIST' }]
    : [{ type: tagType, id: 'LIST' }]
}

export const invalidatesList = <T extends { id: string | number }, R extends string>(
  results: T[] | undefined,
  tagType: R
) => {
  return results
    ? [...results.map(({ id }) => ({ type: tagType, id } as const)), { type: tagType, id: 'LIST' }]
    : [{ type: tagType, id: 'LIST' }]
}

export default baseQueryWithReauth