// UI state types for CBSC Dashboard

// Main UI state interface
export interface UIState {
  // Theme and appearance
  theme: ThemeConfig

  // Layout
  layout: LayoutConfig

  // Screen responsiveness
  screenSize: ScreenSize

  // Loading states
  loading: LoadingState

  // Notifications
  notifications: Notification[]

  // Navigation
  navigation: NavigationState

  // Modal and dialog management
  modals: ModalState

  // User preferences
  preferences: UserPreferences

  // System status
  systemStatus: SystemStatus

  // Quick access
  quickAccess: QuickAccessState

  // Real-time updates
  realtime: RealtimeState

  // Error handling
  errors: ErrorState

  // Performance metrics
  performance: PerformanceState
}

// Theme configuration
export interface ThemeConfig {
  mode: 'light' | 'dark' | 'auto'
  primaryColor: string
  accentColor: string
  backgroundColor?: string
  surfaceColor?: string
  textColor?: string
  fontSize: 'small' | 'medium' | 'large'
  fontFamily: 'default' | 'serif' | 'mono'
  borderRadius: 'small' | 'medium' | 'large'
  custom?: Record<string, string>
}

// Layout configuration
export interface LayoutConfig {
  sidebar: {
    collapsed: boolean
    width: number
    minWidth: number
    maxWidth: number
  }
  header: {
    height: number
    fixed: boolean
    showBreadcrumb: boolean
  }
  content: {
    padding: number
    maxWidth?: number
    centered: boolean
  }
  footer: {
    height: number
    visible: boolean
  }
  density: 'compact' | 'default' | 'comfortable'
  customCSS?: string
}

// Screen size types
export type ScreenSize = 'mobile' | 'tablet' | 'desktop' | 'large-desktop'

// Loading state
export interface LoadingState {
  global: boolean
  message?: string
  components: Record<string, boolean>
  overlays: Record<string, boolean>
}

// Notification interface
export interface Notification {
  id: string
  type: 'success' | 'info' | 'warning' | 'error'
  title: string
  message: string
  description?: string
  duration?: number
  timestamp: number
  read: boolean
  persistent: boolean
  actions?: NotificationAction[]
  icon?: string
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
}

// Notification action
export interface NotificationAction {
  label: string
  action: string
  primary?: boolean
  danger?: boolean
}

// Navigation state
export interface NavigationState {
  activeMenu: string
  expandedMenus: string[]
  breadcrumbs: BreadcrumbItem[]
  history: HistoryItem[]
  favorites: string[]
  quickAccess: QuickAccessItem[]
}

// Breadcrumb item
export interface BreadcrumbItem {
  title: string
  path?: string
  icon?: string
  disabled?: boolean
}

// History item
export interface HistoryItem {
  title: string
  path: string
  timestamp: number
  icon?: string
}

// Quick access item
export interface QuickAccessItem {
  id: string
  label: string
  path: string
  icon: string
  order: number
}

// Modal state management
export interface ModalState {
  open: string[]
  data: Record<string, any>
  zIndex: Record<string, number>
  closable: Record<string, boolean>
  backdrop?: 'blur' | 'dark' | 'light'
}

// User preferences
export interface UserPreferences {
  language: string
  timezone: string
  dateFormat: string
  timeFormat: '12h' | '24h'
  numberFormat: 'en-US' | 'en-GB' | 'de-DE' | 'fr-FR' | 'ja-JP' | 'zh-CN'
  currency: string
  autoRefresh: {
    enabled: boolean
    interval: number
  }
  notifications: NotificationPreferences
  shortcuts: KeyboardShortcut[]
  widgets: WidgetPreferences
  charts: ChartPreferences
  tables: TablePreferences
}

// Notification preferences
export interface NotificationPreferences {
  email: boolean
  push: boolean
  sound: boolean
  types: {
    strategies: boolean
    alerts: boolean
    errors: boolean
    system: boolean
    market: boolean
  }
}

// Keyboard shortcut
export interface KeyboardShortcut {
  id: string
  label: string
  keys: string[]
  action: string
  enabled: boolean
  custom?: boolean
}

// Widget preferences
export interface WidgetPreferences {
  dashboard: {
    layout: string
    autoSave: boolean
    gridSize: number
  }
  widgets: Record<string, WidgetPreference>
}

// Widget preference
export interface WidgetPreference {
  visible: boolean
  config: Record<string, any>
  position?: {
    x: number
    y: number
    w: number
    h: number
  }
}

// Chart preferences
export interface ChartPreferences {
  defaultType: 'line' | 'area' | 'candlestick' | 'bar'
  colors: {
    bullish: string
    bearish: string
    grid: string
    text: string
  }
  indicators: string[]
  timeframes: string[]
  animations: boolean
}

// Table preferences
export interface TablePreferences {
  pageSize: number
  striped: boolean
  hoverable: boolean
  resizable: boolean
  sortable: boolean
  filterable: boolean
  exportable: boolean
}

// System status
export interface SystemStatus {
  status: 'online' | 'offline' | 'maintenance' | 'error'
  message?: string
  lastCheck: string
  uptime?: number
  version?: string
  features?: Record<string, boolean>
}

// Quick access state
export interface QuickAccessState {
  recentPages: string[]
  favoritePages: string[]
  recentSearches: string[]
  pinnedItems: PinnedItem[]
}

// Pinned item
export interface PinnedItem {
  id: string
  type: 'strategy' | 'symbol' | 'analysis' | 'report'
  label: string
  path: string
  metadata?: Record<string, any>
}

// Real-time state
export interface RealtimeState {
  websocket: {
    connected: boolean
    reconnecting: boolean
    reconnectAttempts: number
    lastConnected?: string
    lastError?: string
  }
  subscriptions: Subscription[]
  updates: RealtimeUpdate[]
  lastSync?: string
}

// Subscription
export interface Subscription {
  id: string
  channel: string
  params?: Record<string, any>
  active: boolean
  createdAt: string
  lastUpdate?: string
}

// Realtime update
export interface RealtimeUpdate {
  id: string
  type: string
  channel: string
  data: any
  timestamp: string
  processed: boolean
}

// Error state
export interface ErrorState {
  errors: AppError[]
  reported: string[]
  settings: ErrorSettings
}

// Application error
export interface AppError {
  id: string
  type: 'network' | 'validation' | 'business' | 'system' | 'permission'
  code: string
  message: string
  details?: any
  stack?: string
  timestamp: string
  userId?: string
  sessionId?: string
  userAgent?: string
  url?: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  reported: boolean
  resolved: boolean
}

// Error settings
export interface ErrorSettings {
  autoReport: boolean
  includeStackTrace: boolean
  logLevel: 'debug' | 'info' | 'warn' | 'error'
  maxErrors: number
  retentionDays: number
}

// Performance state
export interface PerformanceState {
  metrics: PerformanceMetric[]
  settings: PerformanceSettings
  alerts: PerformanceAlert[]
}

// Performance metric
export interface PerformanceMetric {
  name: string
  value: number
  unit: string
  timestamp: string
  threshold?: {
    warning: number
    critical: number
  }
}

// Performance settings
export interface PerformanceSettings {
  monitoring: boolean
  alerts: boolean
  sampling: number
  retention: number
}

// Performance alert
export interface PerformanceAlert {
  id: string
  metric: string
  value: number
  threshold: number
  severity: 'warning' | 'critical'
  message: string
  timestamp: string
  acknowledged: boolean
}

// UI action types
export interface UIActionType {
  // Theme actions
  SET_THEME: 'ui/setTheme'
  TOGGLE_THEME: 'ui/toggleTheme'
  UPDATE_THEME_CONFIG: 'ui/updateThemeConfig'

  // Layout actions
  SET_LAYOUT: 'ui/setLayout'
  TOGGLE_SIDEBAR: 'ui/toggleSidebar'
  SET_SCREEN_SIZE: 'ui/setScreenSize'
  UPDATE_LAYOUT_DENSITY: 'ui/updateLayoutDensity'

  // Loading actions
  SET_LOADING: 'ui/setLoading'
  SHOW_LOADING: 'ui/showLoading'
  HIDE_LOADING: 'ui/hideLoading'
  SET_COMPONENT_LOADING: 'ui/setComponentLoading'

  // Notification actions
  ADD_NOTIFICATION: 'ui/addNotification'
  REMOVE_NOTIFICATION: 'ui/removeNotification'
  MARK_NOTIFICATION_READ: 'ui/markNotificationRead'
  CLEAR_NOTIFICATIONS: 'ui/clearNotifications'

  // Navigation actions
  SET_ACTIVE_MENU: 'ui/setActiveMenu'
  SET_BREADCRUMBS: 'ui/setBreadcrumbs'
  ADD_HISTORY_ITEM: 'ui/addHistoryItem'
  TOGGLE_FAVORITE: 'ui/toggleFavorite'

  // Modal actions
  OPEN_MODAL: 'ui/openModal'
  CLOSE_MODAL: 'ui/closeModal'
  CLOSE_ALL_MODALS: 'ui/closeAllModals'
  UPDATE_MODAL_DATA: 'ui/updateModalData'

  // Preferences actions
  UPDATE_PREFERENCES: 'ui/updatePreferences'
  RESET_PREFERENCES: 'ui/resetPreferences'
  SET_LANGUAGE: 'ui/setLanguage'
  SET_TIMEZONE: 'ui/setTimezone'

  // System actions
  SET_SYSTEM_STATUS: 'ui/setSystemStatus'
  CHECK_SYSTEM_HEALTH: 'ui/checkSystemHealth'

  // Realtime actions
  SET_WEBSOCKET_STATUS: 'ui/setWebsocketStatus'
  ADD_SUBSCRIPTION: 'ui/addSubscription'
  REMOVE_SUBSCRIPTION: 'ui/removeSubscription'
  PROCESS_REALTIME_UPDATE: 'ui/processRealtimeUpdate'

  // Error actions
  ADD_ERROR: 'ui/addError'
  REPORT_ERROR: 'ui/reportError'
  RESOLVE_ERROR: 'ui/resolveError'
  CLEAR_ERRORS: 'ui/clearErrors'

  // Performance actions
  UPDATE_PERFORMANCE_METRIC: 'ui/updatePerformanceMetric'
  ADD_PERFORMANCE_ALERT: 'ui/addPerformanceAlert'
  ACKNOWLEDGE_ALERT: 'ui/acknowledgeAlert'
}