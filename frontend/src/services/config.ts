/**
 * API配置文件
 * 包含所有API端点和配置参数
 */

// API基础URL - 根据环境变量或构建模式自动切换
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3004';

// WebSocket URL
export const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:3004';

// API端点配置
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
  },

  // 策略管理
  STRATEGIES: {
    LIST: '/strategies',
    CREATE: '/strategies',
    DETAIL: (id: string) => `/strategies/${id}`,
    UPDATE: (id: string) => `/strategies/${id}`,
    DELETE: (id: string) => `/strategies/${id}`,
    CONTROL: (id: string) => `/strategies/${id}/control`,
    BATCH_CONTROL: '/strategies/batch-control',
    METRICS: (id: string) => `/strategies/${id}/metrics`,
    HISTORY: (id: string) => `/strategies/${id}/operation-history`,
  },

  // 个人策略管理
  PERSONAL_STRATEGIES: {
    DASHBOARD: '/personal-strategies/dashboard',
    LIST: '/personal-strategies/strategies',
    CREATE: '/personal-strategies/strategies',
    DETAIL: (id: string) => `/personal-strategies/strategies/${id}`,
    UPDATE: (id: string) => `/personal-strategies/strategies/${id}`,
    DELETE: (id: string) => `/personal-strategies/strategies/${id}`,
    CONTROL: (id: string) => `/personal-strategies/strategies/${id}/control`,
    BATCH_CONTROL: '/personal-strategies/strategies/batch-control',
    METRICS: (id: string) => `/personal-strategies/strategies/${id}/metrics`,
    HISTORY: (id: string) => `/personal-strategies/strategies/${id}/operation-history`,
    PREFERENCES: '/personal-strategies/preferences',
    WEBSOCKET: (userId: string) => `/personal-strategies/ws/${userId}`,
  },

  // 实时数据
  REALTIME: {
    WEBSOCKET: '/ws',
    MARKET_DATA: '/market/data',
    SIGNALS: '/signals',
    ALERTS: '/alerts',
  },

  // 分析和报告
  ANALYTICS: {
    PERFORMANCE: '/analytics/performance',
    RISK: '/analytics/risk',
    CORRELATION: '/analytics/correlation',
    REPORTS: '/reports',
  },

  // 系统监控
  MONITORING: {
    STATUS: '/monitoring/status',
    HEALTH: '/monitoring/health',
    LOGS: '/monitoring/logs',
    METRICS: '/monitoring/metrics',
  },
};

// 请求配置
export const REQUEST_CONFIG = {
  TIMEOUT: 30000, // 30秒超时
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1秒延迟
};

// WebSocket配置
export const WS_CONFIG = {
  RECONNECT_INTERVAL: 5000, // 5秒重连间隔
  MAX_RECONNECT_ATTEMPTS: 10,
  HEARTBEAT_INTERVAL: 30000, // 30秒心跳间隔
};

// 分页配置
export const PAGINATION_CONFIG = {
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
};

// 缓存配置
export const CACHE_CONFIG = {
  STRATEGY_DATA_TTL: 60000, // 1分钟
  USER_DATA_TTL: 300000,   // 5分钟
  METRICS_DATA_TTL: 30000, // 30秒
};

// 错误消息映射
export const ERROR_MESSAGES: Record<number, string> = {
  400: '请求参数错误',
  401: '未授权，请重新登录',
  403: '禁止访问',
  404: '请求的资源不存在',
  409: '资源冲突',
  422: '数据验证失败',
  429: '请求过于频繁，请稍后再试',
  500: '服务器内部错误',
  502: '网关错误',
  503: '服务暂时不可用',
  504: '网关超时',
};

// HTTP状态码分类
export const HTTP_STATUS = {
  SUCCESS: [200, 201, 204],
  CLIENT_ERROR: [400, 401, 403, 404, 409, 422, 429],
  SERVER_ERROR: [500, 502, 503, 504],
};

// 文件上传配置
export const UPLOAD_CONFIG = {
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_TYPES: [
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/pdf',
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  ],
};

// 主题配置
export const THEME_CONFIG = {
  COLORS: {
    PRIMARY: '#3B82F6',
    SECONDARY: '#10B981',
    DANGER: '#EF4444',
    WARNING: '#F59E0B',
    INFO: '#6B7280',
    SUCCESS: '#10B981',
  },
  BREAKPOINTS: {
    SM: '640px',
    MD: '768px',
    LG: '1024px',
    XL: '1280px',
    '2XL': '1536px',
  },
};

// 默认导出配置对象
export default {
  API_BASE_URL,
  WS_BASE_URL,
  API_ENDPOINTS,
  REQUEST_CONFIG,
  WS_CONFIG,
  PAGINATION_CONFIG,
  CACHE_CONFIG,
  ERROR_MESSAGES,
  HTTP_STATUS,
  UPLOAD_CONFIG,
  THEME_CONFIG,
};