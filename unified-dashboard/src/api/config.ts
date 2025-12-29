/**
 * API Configuration
 * Centralized configuration for API endpoints and settings
 */

// API Base Configuration
export const API_CONFIG = {
  // Base URL for the API
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:3004',

  // Request timeout in milliseconds
  timeout: parseInt(process.env.REACT_APP_API_TIMEOUT || '30000'),

  // API version
  version: process.env.REACT_APP_API_VERSION || 'v1',

  // WebSocket URL
  wsURL: process.env.REACT_APP_WS_URL || 'ws://localhost:3004/ws',

  // Retry configuration
  retry: {
    attempts: parseInt(process.env.REACT_APP_API_RETRY_ATTEMPTS || '3'),
    delay: parseInt(process.env.REACT_APP_API_RETRY_DELAY || '1000'),
  },

  // Cache configuration
  cache: {
    ttl: parseInt(process.env.REACT_APP_CACHE_TTL || '300000'), // 5 minutes
    maxSize: parseInt(process.env.REACT_APP_CACHE_MAX_SIZE || '100'),
  },
}

// API Endpoints
export const API_ENDPOINTS = {
  // Authentication endpoints
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REGISTER: '/auth/register',
    REFRESH: '/auth/refresh',
    VERIFY: '/auth/verify',
    FORGOT_PASSWORD: '/auth/forgot-password',
    RESET_PASSWORD: '/auth/reset-password',
    CHANGE_PASSWORD: '/auth/change-password',
    MFA_SETUP: '/auth/mfa/setup',
    MFA_VERIFY: '/auth/mfa/verify',
  },

  // User management endpoints
  USERS: {
    LIST: '/users',
    DETAIL: (id: string) => `/users/${id}`,
    CREATE: '/users',
    UPDATE: (id: string) => `/users/${id}`,
    DELETE: (id: string) => `/users/${id}`,
    PROFILE: '/users/profile',
    SETTINGS: '/users/settings',
    AVATAR: '/users/avatar',
    SEARCH: '/users/search',
    ROLES: '/users/roles',
    PERMISSIONS: '/users/permissions',
  },

  // Strategy management endpoints
  STRATEGIES: {
    LIST: '/strategies',
    DETAIL: (id: string) => `/strategies/${id}`,
    CREATE: '/strategies',
    UPDATE: (id: string) => `/strategies/${id}`,
    DELETE: (id: string) => `/strategies/${id}`,
    EXECUTE: (id: string) => `/strategies/${id}/execute`,
    STOP: (id: string) => `/strategies/${id}/stop`,
    PAUSE: (id: string) => `/strategies/${id}/pause`,
    RESUME: (id: string) => `/strategies/${id}/resume`,
    BACKTEST: '/strategies/backtest',
    OPTIMIZE: '/strategies/optimize',
    PERFORMANCE: (id: string) => `/strategies/${id}/performance`,
    HISTORY: (id: string) => `/strategies/${id}/history`,
    PARAMETERS: (id: string) => `/strategies/${id}/parameters`,
  },

  // Technical indicators endpoints
  INDICATORS: {
    LIST: '/indicators',
    DETAIL: (id: string) => `/indicators/${id}`,
    CALCULATE: '/indicators/calculate',
    BATCH_CALCULATE: '/indicators/batch-calculate',
    PRESETS: '/indicators/presets',
    CATEGORIES: '/indicators/categories',
    SEARCH: '/indicators/search',
    FORMULAS: '/indicators/formulas',
  },

  // Market data endpoints
  MARKET: {
    SYMBOLS: '/market/symbols',
    PRICE: (symbol: string) => `/market/price/${symbol}`,
    KLINE: '/market/kline',
    TICK: (symbol: string) => `/market/tick/${symbol}`,
    DEPTH: (symbol: string) => `/market/depth/${symbol}`,
    TRADES: (symbol: string) => `/market/trades/${symbol}`,
    STATS: '/market/stats',
    OVERVIEW: '/market/overview',
    SCREENER: '/market/screener',
    CALENDAR: '/market/calendar',
    NEWS: '/market/news',
  },

  // CBSC specific endpoints
  CBSC: {
    WARRANTS: '/cbsc/warrants',
    WARRANT_DETAIL: (id: string) => `/cbsc/warrants/${id}`,
    CALLABLE_BULLS: '/cbsc/callable-bulls',
    CALLABLE_BEARS: '/cbsc/callable-bears',
    TRACKERS: '/cbsc/trackers',
    SYNTHETICS: '/cbsc/synthetics',
    QUOTE: (code: string) => `/cbsc/quote/${code}`,
    SEARCH: '/cbsc/search',
    CALCULATOR: '/cbsc/calculator',
    STRATEGY: '/cbsc/strategy',
  },

  // Analytics and monitoring endpoints
  ANALYTICS: {
    DASHBOARD: '/analytics/dashboard',
    PERFORMANCE: '/analytics/performance',
    RISK: '/analytics/risk',
    CORRELATION: '/analytics/correlation',
    ALLOCATION: '/analytics/allocation',
    REPORTS: '/analytics/reports',
    EXPORT: '/analytics/export',
  },

  // WebSocket channels
  WS_CHANNELS: {
    MARKET_DATA: 'market_data',
    STRATEGY_UPDATES: 'strategy_updates',
    ORDER_BOOK: 'order_book',
    TRADES: 'trades',
    ALERTS: 'alerts',
    SYSTEM_STATUS: 'system_status',
  },
}

// API Error Codes
export const API_ERROR_CODES = {
  // General errors
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',

  // Authentication errors
  UNAUTHORIZED: 'UNAUTHORIZED',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
  MFA_REQUIRED: 'MFA_REQUIRED',
  MFA_INVALID: 'MFA_INVALID',

  // Authorization errors
  FORBIDDEN: 'FORBIDDEN',
  INSUFFICIENT_PERMISSIONS: 'INSUFFICIENT_PERMISSIONS',

  // Validation errors
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  INVALID_INPUT: 'INVALID_INPUT',
  MISSING_REQUIRED_FIELD: 'MISSING_REQUIRED_FIELD',

  // Resource errors
  NOT_FOUND: 'NOT_FOUND',
  ALREADY_EXISTS: 'ALREADY_EXISTS',
  RESOURCE_CONFLICT: 'RESOURCE_CONFLICT',

  // Rate limiting
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',

  // Server errors
  INTERNAL_SERVER_ERROR: 'INTERNAL_SERVER_ERROR',
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
  DATABASE_ERROR: 'DATABASE_ERROR',
}

// HTTP Status Codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  VALIDATION_ERROR: 422,
  RATE_LIMIT: 429,
  INTERNAL_SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,
} as const

// Export WS_CHANNELS separately for convenience
export const WS_CHANNELS = API_ENDPOINTS.WS_CHANNELS