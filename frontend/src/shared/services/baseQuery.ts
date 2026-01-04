// CBSC Trading System - Base Query with Re-auth
// Handles automatic token refresh and 401 responses

import {
  BaseQueryFn,
  FetchArgs,
  FetchBaseQueryError,
  fetchBaseQuery,
} from '@reduxjs/toolkit/query/react';
import type { RootState } from '@/store';
import { tokenActions } from '@/store/slices/authSlice';

/**
 * Base query configuration with automatic token refresh
 * Handles 401 responses by attempting to refresh the token
 */
export const baseQueryWithReauth = ({
  baseUrl = '',
  prepareHeaders,
}: {
  baseUrl?: string;
  prepareHeaders?: (
    headers: Headers,
    api: { getState: () => RootState }
  ) => Headers;
}): BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> => {
  const baseQuery = fetchBaseQuery({
    baseUrl,
    prepareHeaders: (headers, { getState }) => {
      // Get token from state
      const token = (getState() as RootState).auth.token;
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }

      // Call custom prepareHeaders if provided
      if (prepareHeaders) {
        return prepareHeaders(headers, { getState });
      }

      return headers;
    },
  });

  return async (args, api, extraOptions) => {
    let result = await baseQuery(args, api, extraOptions);

    // Handle 401 errors with token refresh
    if (result.error && result.error.status === 401) {
      console.log('Token expired, attempting refresh...');

      // Try to refresh the token
      const refreshResult = await baseQuery(
        {
          url: '/api/auth/refresh',
          method: 'POST',
          body: {
            refreshToken: (api.getState() as RootState).auth.refreshToken,
          },
        },
        api,
        extraOptions
      );

      if (refreshResult.data) {
        // Store new token
        const { token, refreshToken } = refreshResult.data as {
          token: string;
          refreshToken: string;
        };
        api.dispatch(tokenActions.setTokens({ token, refreshToken }));

        // Retry the original request with new token
        result = await baseQuery(args, api, extraOptions);
      } else {
        // Refresh failed, redirect to login
        api.dispatch(tokenActions.clearTokens());
        window.location.href = '/login';
      }
    }

    return result;
  };
};

/**
 * Simple base query without re-auth for public endpoints
 */
export const baseQuery = fetchBaseQuery({
  baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:3004',
  credentials: 'include',
});
