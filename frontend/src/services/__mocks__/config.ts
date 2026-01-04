/**
 * Mock config file for Jest tests
 * Provides fallback values for import.meta.env
 */

// Mock API URLs
export const API_BASE_URL = 'http://localhost:3005';
export const WS_BASE_URL = 'ws://localhost:3005';

// API endpoints
export const API_ENDPOINTS = {
  // 认证相关
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    REGISTER: '/auth/register',
    VERIFY: '/auth/verify',
  },
  // 用户管理
  USERS: {
    LIST: '/users',
    CREATE: '/users',
    DETAIL: (id: string) => `/users/${id}`,
    UPDATE: (id: string) => `/users/${id}`,
    DELETE: (id: string) => `/users/${id}`,
    PROFILE: '/users/profile',
    CHANGE_PASSWORD: '/users/change-password',
    RESET_PASSWORD: '/users/reset-password',
  },
  // 策略管理
  STRATEGIES: {
    LIST: '/strategies',
    CREATE: '/strategies',
    DETAIL: (id: string) => `/strategies/${id}`,
    UPDATE: (id: string) => `/strategies/${id}`,
    DELETE: (id: string) => `/strategies/${id}`,
    ACTIVATE: (id: string) => `/strategies/${id}/activate`,
    DEACTIVATE: (id: string) => `/strategies/${id}/deactivate`,
    BACKTEST: (id: string) => `/strategies/${id}/backtest`,
    PARAMETERS: (id: string) => `/strategies/${id}/parameters`,
    PERFORMANCE: (id: string) => `/strategies/${id}/performance`,
  },
  // 回测
  BACKTEST: {
    RUN: '/backtest/run',
    RESULTS: (id: string) => `/backtest/results/${id}`,
    COMPARE: '/backtest/compare',
    OPTIMIZATION: '/backtest/optimization',
  },
  // 市场数据
  MARKET_DATA: {
    STOCKS: '/market/stocks',
    CBBC: '/market/cbbc',
    FUNDAMENTAL: '/market/fundamental',
    TECHNICAL: '/market/technical',
    REALTIME: '/market/realtime',
  },
  // 经济数据
  ECONOMIC_DATA: {
    EXCHANGE_RATE: '/economic/exchange-rate',
    HIBOR: '/economic/hibor',
    MONETARY_BASE: '/economic/monetary-base',
    INTEREST_RATE: '/economic/interest-rate',
  },
  // 交易
  TRADING: {
    ORDER: '/trading/order',
    ORDERS: '/trading/orders',
    POSITIONS: '/trading/positions',
    CANCEL_ORDER: (id: string) => `/trading/orders/${id}/cancel`,
  },
  // 风险管理
  RISK: {
    CHECK: '/risk/check',
    LIMITS: '/risk/limits',
    ALERTS: '/risk/alerts',
    METRICS: '/risk/metrics',
  },
  // 通知
  NOTIFICATIONS: {
    LIST: '/notifications',
    MARK_READ: (id: string) => `/notifications/${id}/read`,
    PREFERENCES: '/notifications/preferences',
  },
  // WebSocket
  WEBSOCKET: {
    CONNECT: '/ws/connect',
    SUBSCRIBE: '/ws/subscribe',
    UNSUBSCRIBE: '/ws/unsubscribe',
  },
};

// 缓存配置
export const CACHE_CONFIG = {
  ENABLED: true,
  TTL: {
    SHORT: 5 * 60 * 1000,    // 5 minutes
    MEDIUM: 15 * 60 * 1000,  // 15 minutes
    LONG: 60 * 60 * 1000,    // 1 hour
    VERY_LONG: 24 * 60 * 60 * 1000, // 24 hours
  },
};

// 请求配置
export const REQUEST_CONFIG = {
  TIMEOUT: 30000, // 30 seconds
  RETRY: {
    MAX_RETRIES: 3,
    RETRY_DELAY: 1000,
  },
};

// WebSocket 配置
export const WS_CONFIG = {
  RECONNECT_INTERVAL: 3000,
  MAX_RECONNECT_ATTEMPTS: 5,
  HEARTBEAT_INTERVAL: 30000,
};
