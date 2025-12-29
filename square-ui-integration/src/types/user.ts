/**
 * User related types (extended from auth types)
 */

// User Preferences
export interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  language: 'zh-CN' | 'en-US'
  timezone: string
  dateFormat: string
  numberFormat: string
  currency: string
  notifications: NotificationPreferences
  dashboard: DashboardPreferences
  trading: TradingPreferences
}

// Notification Preferences
export interface NotificationPreferences {
  email: boolean
  push: boolean
  sms: boolean
  inApp: boolean
  types: {
    trades: boolean
    alerts: boolean
    news: boolean
    reports: boolean
    system: boolean
  }
}

// Dashboard Preferences
export interface DashboardPreferences {
  layout: DashboardLayout[]
  theme: {
    primaryColor: string
    mode: 'light' | 'dark'
  }
  widgets: WidgetPreference[]
}

// Dashboard Layout
export interface DashboardLayout {
  id: string
  x: number
  y: number
  w: number
  h: number
  minW?: number
  minH?: number
  maxW?: number
  maxH?: number
  isDraggable?: boolean
  isResizable?: boolean
}

// Widget Preference
export interface WidgetPreference {
  id: string
  type: string
  title: string
  config: Record<string, any>
  isVisible: boolean
}

// Trading Preferences
export interface TradingPreferences {
  defaultOrderType: 'market' | 'limit' | 'stop' | 'stop_limit'
  defaultQuantity: number
  confirmOrders: boolean
  showPositionSize: boolean
  riskWarning: boolean
  autoRefreshQuotes: boolean
  refreshInterval: number
}

// User Activity
export interface UserActivity {
  id: string
  userId: string
  type: ActivityType
  description: string
  metadata?: Record<string, any>
  ipAddress?: string
  userAgent?: string
  timestamp: Date | string
}

// Activity Type
export type ActivityType =
  | 'login'
  | 'logout'
  | 'trade'
  | 'strategy_created'
  | 'strategy_updated'
  | 'strategy_deleted'
  | 'backtest_run'
  | 'view_report'
  | 'settings_updated'
  | 'profile_updated'
  | 'password_changed'
  | 'mfa_enabled'
  | 'mfa_disabled'

// User Session (extended from auth)
export interface UserSession {
  id: string
  userId: string
  token: string
  refreshToken: string
  deviceInfo: {
    type: 'desktop' | 'tablet' | 'mobile'
    os: string
    browser: string
    version: string
  }
  ipAddress: string
  location?: {
    country: string
    city: string
    lat: number
    lng: number
  }
  isActive: boolean
  createdAt: Date | string
  expiresAt: Date | string
  lastActivityAt: Date | string
}

// User Alert
export interface UserAlert {
  id: string
  userId: string
  type: AlertType
  title: string
  message: string
  data?: Record<string, any>
  isRead: boolean
  priority: 'low' | 'medium' | 'high' | 'urgent'
  category: 'system' | 'trading' | 'strategy' | 'market' | 'account'
  actions?: AlertAction[]
  createdAt: Date | string
  readAt?: Date | string
}

// Alert Type
export type AlertType =
  | 'info'
  | 'success'
  | 'warning'
  | 'error'
  | 'trade_executed'
  | 'strategy_alert'
  | 'price_alert'
  | 'volume_alert'
  | 'news_alert'

// Alert Action
export interface AlertAction {
  label: string
  action: string
  url?: string
  style?: 'primary' | 'secondary' | 'danger'
}

// User Watchlist
export interface UserWatchlist {
  id: string
  userId: string
  name: string
  description?: string
  symbols: WatchlistSymbol[]
  isDefault: boolean
  isPublic: boolean
  createdAt: Date | string
  updatedAt: Date | string
}

// Watchlist Symbol
export interface WatchlistSymbol {
  symbol: string
  name: string
  exchange: string
  addedAt: Date | string
  alert?: {
    enabled: boolean
    type: 'price_above' | 'price_below' | 'percent_change'
    value: number
  }
}

// User Note
export interface UserNote {
  id: string
  userId: string
  title: string
  content: string
  category?: string
  tags: string[]
  isPinned: boolean
  isPublic: boolean
  relatedTo?: {
    type: 'symbol' | 'strategy' | 'trade'
    id: string
  }
  createdAt: Date | string
  updatedAt: Date | string
}

// User Report
export interface UserReport {
  id: string
  userId: string
  name: string
  type: ReportType
  parameters: Record<string, any>
  schedule?: ReportSchedule
  format: 'pdf' | 'excel' | 'csv' | 'json'
  recipients: string[]
  isActive: boolean
  lastGeneratedAt?: Date | string
  createdAt: Date | string
}

// Report Type
export type ReportType =
  | 'performance'
  | 'trades'
  | 'tax'
  | 'risk'
  | 'compliance'
  | 'custom'

// Report Schedule
export interface ReportSchedule {
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'
  dayOfWeek?: number // 0-6
  dayOfMonth?: number // 1-31
  time: string // HH:mm
  timezone: string
}