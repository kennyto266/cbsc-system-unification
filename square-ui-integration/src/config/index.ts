// App configuration
export const APP_CONFIG = {
  name: import.meta.env.VITE_APP_NAME || 'CBSC Square UI Dashboard',
  version: import.meta.env.VITE_APP_VERSION || '1.0.0',
  description: import.meta.env.VITE_APP_DESCRIPTION || 'CBSC量化交易策略管理系统',
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:3003',
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:3003',
}

// Feature flags
export const FEATURES = {
  analytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  pwa: import.meta.env.VITE_ENABLE_PWA !== 'false',
  storybook: import.meta.env.VITE_ENABLE_STORYBOOK === 'true',
}

// Pagination defaults
export const PAGINATION = {
  defaultPageSize: 20,
  pageSizeOptions: [10, 20, 50, 100],
}

// Date formats
export const DATE_FORMATS = {
  display: 'YYYY-MM-DD HH:mm:ss',
  date: 'YYYY-MM-DD',
  time: 'HH:mm:ss',
  iso: 'YYYY-MM-DDTHH:mm:ssZ',
}

// Chart configurations
export const CHART_CONFIG = {
  defaultHeight: 400,
  responsive: true,
  maintainAspectRatio: false,
  animation: {
    duration: 750,
    easing: 'easeInOutQuart' as const,
  },
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        usePointStyle: true,
        padding: 20,
      },
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#fff',
      bodyColor: '#fff',
      borderColor: '#ddd',
      borderWidth: 1,
      cornerRadius: 8,
      displayColors: false,
    },
  },
}

// Theme configurations
export const THEME = {
  colors: {
    primary: '#0284c7',
    secondary: '#64748b',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6',
  },
  breakpoints: {
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280,
    '2xl': 1536,
  },
}

// WebSocket configuration
export const WS_CONFIG = {
  reconnectInterval: 3000,
  maxReconnectAttempts: 5,
  heartbeatInterval: 30000,
}

// Cache configuration
export const CACHE = {
  defaultTTL: 5 * 60 * 1000, // 5 minutes
  maxAge: 24 * 60 * 60 * 1000, // 24 hours
}