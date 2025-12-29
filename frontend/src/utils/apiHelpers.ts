/**
 * API Helper Utilities
 * Common utilities for API operations
 */

import type { ApiError, PaginatedResponse } from '../types/api';

// API Error handling utilities
export const isApiError = (error: any): error is ApiError => {
  return error && typeof error === 'object' && 'code' in error && 'message' in error;
};

// Extract error message from API response
export const getErrorMessage = (error: any): string => {
  if (isApiError(error)) {
    return error.message;
  }

  if (error?.data?.message) {
    return error.data.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  return 'An unexpected error occurred';
};

// Check if error is a network error
export const isNetworkError = (error: any): boolean => {
  return error?.code === 'NETWORK_ERROR' ||
         error?.status === 0 ||
         error?.name === 'NetworkError' ||
         error?.message?.includes('Network Error');
};

// Check if error is an authentication error
export const isAuthError = (error: any): boolean => {
  return error?.status === 401 ||
         error?.code === 'AUTHENTICATION_FAILED' ||
         error?.code === 'TOKEN_EXPIRED';
};

// Check if error is a permission error
export const isPermissionError = (error: any): boolean => {
  return error?.status === 403 ||
         error?.code === 'PERMISSION_DENIED';
};

// Check if error is a validation error
export const isValidationError = (error: any): boolean => {
  return error?.status === 400 ||
         error?.status === 422 ||
         error?.code === 'VALIDATION_ERROR';
};

// Pagination utilities
export const getPageInfo = (response: PaginatedResponse<any> | undefined) => {
  if (!response) {
    return {
      currentPage: 1,
      totalPages: 0,
      hasNextPage: false,
      hasPrevPage: false,
    };
  }

  return {
    currentPage: response.page || 1,
    totalPages: response.totalPages || 0,
    hasNextPage: response.page < response.totalPages,
    hasPrevPage: response.page > 1,
  };
};

// Build query string from params
export const buildQueryString = (params: Record<string, any>): string => {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach(v => searchParams.append(key, String(v)));
      } else {
        searchParams.append(key, String(value));
      }
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
};

// API Response transformation utilities
export const transformPaginatedResponse = <T>(
  response: any,
  page: number = 1,
  pageSize: number = 20
): PaginatedResponse<T> => {
  const items = response.data || response.items || response.results || [];
  const total = response.total || response.count || items.length;

  return {
    items,
    total,
    page,
    pageSize,
    totalPages: Math.ceil(total / pageSize),
  };
};

// File upload utilities
export const createFormData = (data: Record<string, any>): FormData => {
  const formData = new FormData();

  Object.entries(data).forEach(([key, value]) => {
    if (value instanceof File) {
      formData.append(key, value);
    } else if (Array.isArray(value)) {
      value.forEach((item, index) => {
        formData.append(`${key}[${index}]`, String(item));
      });
    } else if (typeof value === 'object' && value !== null) {
      formData.append(key, JSON.stringify(value));
    } else if (value !== undefined && value !== null) {
      formData.append(key, String(value));
    }
  });

  return formData;
};

// Progress tracking utilities
export const createProgressHandler = (
  onProgress?: (progress: number) => void
) => {
  return (event: ProgressEvent) => {
    if (event.lengthComputable && onProgress) {
      const progress = Math.round((event.loaded / event.total) * 100);
      onProgress(progress);
    }
  };
};

// Cache utilities
export const getCacheKey = (endpoint: string, params?: Record<string, any>): string => {
  const paramsStr = params ? JSON.stringify(params) : '';
  return `${endpoint}${paramsStr ? `:${paramsStr}` : ''}`;
};

// Request debounce utility
export const createDebouncedRequest = <T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: NodeJS.Timeout;

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
};

// Request retry utility
export const retryRequest = async <T>(
  requestFn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> => {
  let lastError: any;

  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error;

      // Don't retry on authentication or permission errors
      if (isAuthError(error) || isPermissionError(error)) {
        throw error;
      }

      // Don't retry on last attempt
      if (i === maxRetries) {
        throw error;
      }

      // Wait before retrying with exponential backoff
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
    }
  }

  throw lastError;
};

// Batch request utility
export const batchRequests = async <T>(
  requests: Array<() => Promise<T>>,
  concurrency: number = 5
): Promise<T[]> => {
  const results: T[] = [];

  for (let i = 0; i < requests.length; i += concurrency) {
    const batch = requests.slice(i, i + concurrency);
    const batchResults = await Promise.allSettled(
      batch.map(request => request())
    );

    batchResults.forEach(result => {
      if (result.status === 'fulfilled') {
        results.push(result.value);
      } else {
        // Handle rejected promise
        console.error('Batch request failed:', result.reason);
        throw result.reason;
      }
    });
  }

  return results;
};

// Local storage cache utilities
export const storage = {
  set: (key: string, value: any, ttl?: number) => {
    try {
      const item = {
        value,
        timestamp: Date.now(),
        ttl: ttl ? Date.now() + ttl * 1000 : null,
      };
      localStorage.setItem(key, JSON.stringify(item));
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
    }
  },

  get: (key: string): any | null => {
    try {
      const item = localStorage.getItem(key);
      if (!item) return null;

      const parsed = JSON.parse(item);

      // Check TTL if exists
      if (parsed.ttl && Date.now() > parsed.ttl) {
        localStorage.removeItem(key);
        return null;
      }

      return parsed.value;
    } catch (error) {
      console.error('Failed to read from localStorage:', error);
      return null;
    }
  },

  remove: (key: string) => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Failed to remove from localStorage:', error);
    }
  },

  clear: () => {
    try {
      localStorage.clear();
    } catch (error) {
      console.error('Failed to clear localStorage:', error);
    }
  },
};

// Date formatting utilities
export const formatDateForAPI = (date: Date): string => {
  return date.toISOString();
};

export const parseDateFromAPI = (dateString: string): Date => {
  return new Date(dateString);
};

// Common API endpoints
export const API_ENDPOINTS = {
  // Auth
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    REGISTER: '/auth/register',
    PROFILE: '/auth/profile',
  },

  // Users
  USERS: {
    LIST: '/users',
    DETAIL: (id: string) => `/users/${id}`,
    ROLES: '/roles',
  },

  // Strategies
  STRATEGIES: {
    LIST: '/strategies',
    DETAIL: (id: string) => `/strategies/${id}`,
    EXECUTE: (id: string) => `/strategies/${id}/execute`,
    BACKTEST: (id: string) => `/strategies/${id}/backtest`,
  },

  // Market Data
  MARKET: {
    OVERVIEW: '/market/overview',
    TICKER: '/market/ticker',
    OHLC: (symbol: string) => `/market/ohlc/${symbol}`,
    NEWS: '/market/news',
  },

  // Dashboard
  DASHBOARD: {
    CONFIG: '/dashboard/config',
    WIDGETS: '/dashboard/widgets',
    QUICK_ACTIONS: '/dashboard/quick-actions',
  },

  // WebSocket
  WEBSOCKET: {
    STATUS: '/websocket/status',
    INIT: '/websocket/init',
  },
} as const;