import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import {
  UIState,
  ThemeConfig,
  LayoutConfig,
  LoadingState,
  Notification,
  NavigationState,
  ModalState,
  UserPreferences,
  SystemStatus,
  QuickAccessState,
  RealtimeState,
  ErrorState,
  PerformanceState,
  ScreenSize,
  NotificationAction,
  BreadcrumbItem,
  KeyboardShortcut,
  WidgetPreferences,
  ChartPreferences,
  TablePreferences,
  NotificationPreferences,
  Subscription,
  RealtimeUpdate,
  AppError,
  PerformanceMetric,
  PerformanceAlert,
} from '../../types/ui'
import { WebSocketStatus, StrategyUpdate, TradingSignal, SystemHealth } from '../../types'

// Initial state
const initialState: UIState = {
  theme: {
    mode: 'light',
    primaryColor: '#1890ff',
    accentColor: '#52c41a',
    fontSize: 'medium',
    fontFamily: 'default',
    borderRadius: 'medium',
  },
  layout: {
    sidebar: {
      collapsed: false,
      width: 256,
      minWidth: 200,
      maxWidth: 400,
    },
    header: {
      height: 64,
      fixed: true,
      showBreadcrumb: true,
    },
    content: {
      padding: 24,
      centered: false,
    },
    footer: {
      height: 48,
      visible: true,
    },
    density: 'default',
  },
  screenSize: 'desktop',
  loading: {
    global: false,
    components: {},
    overlays: {},
  },
  notifications: [],
  navigation: {
    activeMenu: '',
    expandedMenus: [],
    breadcrumbs: [],
    history: [],
    favorites: [],
    quickAccess: [],
  },
  modals: {
    open: [],
    data: {},
    zIndex: {},
    closable: {},
    backdrop: 'dark',
  },
  preferences: {
    language: 'en',
    timezone: 'UTC',
    dateFormat: 'MM/DD/YYYY',
    timeFormat: '12h',
    numberFormat: 'en-US',
    currency: 'USD',
    autoRefresh: {
      enabled: true,
      interval: 30000,
    },
    notifications: {
      email: true,
      push: true,
      sound: false,
      types: {
        strategies: true,
        alerts: true,
        errors: true,
        system: true,
        market: false,
      },
    },
    shortcuts: [],
    widgets: {
      dashboard: {
        layout: 'default',
        autoSave: true,
        gridSize: 12,
      },
      widgets: {},
    },
    charts: {
      defaultType: 'candlestick',
      colors: {
        bullish: '#26a69a',
        bearish: '#ef5350',
        grid: '#f0f0f0',
        text: '#333333',
      },
      indicators: [],
      timeframes: ['1m', '5m', '15m', '1h', '4h', '1d'],
      animations: true,
    },
    tables: {
      pageSize: 20,
      striped: true,
      hoverable: true,
      resizable: true,
      sortable: true,
      filterable: true,
      exportable: true,
    },
  },
  systemStatus: {
    status: 'online',
    lastCheck: new Date().toISOString(),
    features: {},
  },
  quickAccess: {
    recentPages: [],
    favoritePages: [],
    recentSearches: [],
    pinnedItems: [],
  },
  realtime: {
    websocket: {
      connected: false,
      reconnecting: false,
      reconnectAttempts: 0,
    },
    subscriptions: [],
    updates: [],
  },
  errors: {
    errors: [],
    reported: [],
    settings: {
      autoReport: false,
      includeStackTrace: true,
      logLevel: 'error',
      maxErrors: 100,
      retentionDays: 30,
    },
  },
  performance: {
    metrics: [],
    settings: {
      monitoring: false,
      alerts: false,
      sampling: 1000,
      retention: 3600,
    },
    alerts: [],
  },

  // Legacy properties for backward compatibility (values only —
  // type annotations live in the UIState interface in types/ui.ts)
  themeMode: 'light',
  sidebarCollapsed: false,
  layoutDensity: 'default',

  // Loading message (extra field beyond the loading object above)
  loadingMessage: undefined,

  // Page meta
  breadcrumbs: [],

  // Quick access
  recentPages: [],
  favoritePages: [],

  // Modal states
  activeModals: [],

  // WebSocket相關狀態
  webSocketStatus: { connected: false, reconnecting: false, reconnectAttempts: 0 } as WebSocketStatus,
  realtimeStrategies: [],
  realtimeSignals: [],
  systemHealth: null,
}

interface Notification {
  id: string
  type: 'success' | 'warning' | 'error' | 'info'
  title: string
  message?: string
  timestamp: number
  read: boolean
  autoClose?: boolean
  duration?: number
}

interface BreadcrumbItem {
  title: string
  path?: string
  icon?: string
}

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // Sidebar actions
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed
    },
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload
    },

    // Theme actions
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload
      state.themeMode = action.payload
    },
    setThemeMode: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.themeMode = action.payload
    },
    toggleTheme: (state) => {
      state.themeMode = state.themeMode === 'light' ? 'dark' : 'light'
      state.theme = state.themeMode
    },

    // Screen size actions
    setScreenSize: (state, action: PayloadAction<'mobile' | 'tablet' | 'desktop'>) => {
      state.screenSize = action.payload
      // Auto-collapse sidebar on mobile
      if (action.payload === 'mobile' && !state.sidebarCollapsed) {
        state.sidebarCollapsed = true
      }
    },

    // Loading actions
    setLoading: (state, action: PayloadAction<{ loading: boolean; message?: string }>) => {
      state.loading = action.payload.loading
      state.loadingMessage = action.payload.message
    },
    showLoading: (state, action?: PayloadAction<string>) => {
      state.loading = true
      state.loadingMessage = action?.payload
    },
    hideLoading: (state) => {
      state.loading = false
      state.loadingMessage = undefined
    },

    // Notification actions
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id' | 'timestamp' | 'read'>>) => {
      const notification: Notification = {
        ...action.payload,
        id: Date.now().toString(),
        timestamp: Date.now(),
        read: false,
      }
      state.notifications.unshift(notification)
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload)
    },
    markNotificationRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload)
      if (notification) {
        notification.read = true
      }
    },
    markAllNotificationsRead: (state) => {
      state.notifications.forEach(n => {
        n.read = true
      })
    },
    clearNotifications: (state) => {
      state.notifications = []
    },

    // Page meta actions
    setPageTitle: (state, action: PayloadAction<string>) => {
      state.pageTitle = action.payload
    },
    setBreadcrumbs: (state, action: PayloadAction<BreadcrumbItem[]>) => {
      state.breadcrumbs = action.payload
    },
    addBreadcrumb: (state, action: PayloadAction<BreadcrumbItem>) => {
      state.breadcrumbs.push(action.payload)
    },

    // Layout density
    setLayoutDensity: (state, action: PayloadAction<'compact' | 'default' | 'comfortable'>) => {
      state.layoutDensity = action.payload
    },

    // Recent pages
    addRecentPage: (state, action: PayloadAction<string>) => {
      // Remove if already exists
      state.recentPages = state.recentPages.filter(p => p !== action.payload)
      // Add to beginning
      state.recentPages.unshift(action.payload)
      // Keep only last 10
      state.recentPages = state.recentPages.slice(0, 10)
    },
    removeRecentPage: (state, action: PayloadAction<string>) => {
      state.recentPages = state.recentPages.filter(p => p !== action.payload)
    },
    clearRecentPages: (state) => {
      state.recentPages = []
    },

    // Favorite pages
    toggleFavoritePage: (state, action: PayloadAction<string>) => {
      const index = state.favoritePages.indexOf(action.payload)
      if (index > -1) {
        state.favoritePages.splice(index, 1)
      } else {
        state.favoritePages.push(action.payload)
      }
    },

    // System status
    setSystemStatus: (state, action: PayloadAction<'online' | 'offline' | 'maintenance'>) => {
      state.systemStatus = action.payload
    },

    // Modal management
    openModal: (state, action: PayloadAction<string>) => {
      if (!state.activeModals.includes(action.payload)) {
        state.activeModals.push(action.payload)
      }
    },
    closeModal: (state, action: PayloadAction<string>) => {
      state.activeModals = state.activeModals.filter(m => m !== action.payload)
    },
    closeAllModals: (state) => {
      state.activeModals = []
    },
    // WebSocket相關actions
    setWebSocketStatus: (state, action: PayloadAction<Partial<WebSocketStatus>>) => {
      state.webSocketStatus = { ...state.webSocketStatus, ...action.payload }
    },
    updateStrategyData: (state, action: PayloadAction<StrategyUpdate[]>) => {
      state.realtimeStrategies = action.payload
    },
    updatePerformanceMetrics: (state, action: PayloadAction<any>) => {
      // 更新策略性能數據
      if (action.payload.updated_strategies) {
        action.payload.updated_strategies.forEach((updatedStrategy: StrategyUpdate) => {
          const index = state.realtimeStrategies.findIndex(s => s.id === updatedStrategy.id)
          if (index !== -1) {
            state.realtimeStrategies[index] = { ...state.realtimeStrategies[index], ...updatedStrategy }
          } else {
            state.realtimeStrategies.push(updatedStrategy)
          }
        })
      }
    },
    addNewSignal: (state, action: PayloadAction<TradingSignal>) => {
      // 限制信號數量，保持最新的100條
      state.realtimeSignals.unshift(action.payload)
      if (state.realtimeSignals.length > 100) {
        state.realtimeSignals = state.realtimeSignals.slice(0, 100)
      }
    },
    updateSystemHealth: (state, action: PayloadAction<SystemHealth>) => {
      state.systemHealth = action.payload
    },
    clearRealtimeData: (state) => {
      state.realtimeStrategies = []
      state.realtimeSignals = []
      state.systemHealth = null
    },
    addError: (state, action: PayloadAction<{ message: string; endpoint?: string; method?: string }>) => {
      state.notifications.unshift({
        id: Date.now().toString(),
        type: 'error',
        title: 'Error',
        message: action.payload.message,
        timestamp: Date.now(),
        read: false,
        autoClose: true,
        duration: 5000,
      })
    }
  },
})

export const {
  // Sidebar
  toggleSidebar,
  setSidebarCollapsed,
  // Theme
  setTheme,
  setThemeMode,
  toggleTheme,
  // Screen
  setScreenSize,
  // Loading
  setLoading,
  showLoading,
  hideLoading,
  // Notifications
  addNotification,
  removeNotification,
  markNotificationRead,
  markAllNotificationsRead,
  clearNotifications,
  // Page meta
  setPageTitle,
  setBreadcrumbs,
  addBreadcrumb,
  // Layout
  setLayoutDensity,
  // Recent pages
  addRecentPage,
  removeRecentPage,
  clearRecentPages,
  // Favorites
  toggleFavoritePage,
  // System
  setSystemStatus,
  // Modals
  openModal,
  closeModal,
  closeAllModals,
  // WebSocket
  setWebSocketStatus,
  updateStrategyData,
  updatePerformanceMetrics,
  // Error handling
  addError,
  addNewSignal,
  updateSystemHealth,
  clearRealtimeData
} = uiSlice.actions

export default uiSlice.reducer

// Selectors
export const selectUI = (state: { ui: UIState }) => state.ui
export const selectTheme = (state: { ui: UIState }) => state.ui.theme
export const selectThemeMode = (state: { ui: UIState }) => state.ui.themeMode
export const selectSidebarCollapsed = (state: { ui: UIState }) => state.ui.sidebarCollapsed
export const selectScreenSize = (state: { ui: UIState }) => state.ui.screenSize
export const selectLayoutDensity = (state: { ui: UIState }) => state.ui.layoutDensity
export const selectLoading = (state: { ui: UIState }) => state.ui.loading
export const selectLoadingMessage = (state: { ui: UIState }) => state.ui.loadingMessage
export const selectNotifications = (state: { ui: UIState }) => state.ui.notifications
export const selectUnreadNotifications = (state: { ui: UIState }) =>
  state.ui.notifications.filter(n => !n.read)
export const selectUnreadNotificationCount = (state: { ui: UIState }) =>
  state.ui.notifications.filter(n => !n.read).length
export const selectBreadcrumbs = (state: { ui: UIState }) => state.ui.breadcrumbs
export const selectRecentPages = (state: { ui: UIState }) => state.ui.recentPages
export const selectFavoritePages = (state: { ui: UIState }) => state.ui.favoritePages
export const selectSystemStatus = (state: { ui: UIState }) => state.ui.systemStatus
export const selectActiveModals = (state: { ui: UIState }) => state.ui.activeModals
export const selectWebSocketStatus = (state: { ui: UIState }) => state.ui.webSocketStatus
export const selectRealtimeStrategies = (state: { ui: UIState }) => state.ui.realtimeStrategies
export const selectRealtimeSignals = (state: { ui: UIState }) => state.ui.realtimeSignals
export const selectSystemHealth = (state: { ui: UIState }) => state.ui.systemHealth
