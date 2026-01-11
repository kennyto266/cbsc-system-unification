import { configureStore } from '@reduxjs/toolkit'
import { rootReducer } from './rootReducer'
import { persistConfig } from './persistConfig'
import { persistReducer } from 'redux-persist'
import storage from 'redux-persist/lib/storage'
import authReducer from './slices/authSlice'
import strategiesReducer from './slices/strategiesSlice'
import uiReducer from './slices/uiSlice'

// Create a test store
export const createTestStore = (initialState = {}) => {
  const persistedReducer = persistReducer(
    {
      ...persistConfig,
      storage: storage,
      // Blacklist persist for tests
      blacklist: ['persist/FLUSH', 'persist/REHYDRATE', 'persist/PAUSE', 'persist/PERSIST', 'persist/PURGE', 'persist/REGISTER'],
    },
    rootReducer
  )

  return configureStore({
    reducer: persistedReducer,
    preloadedState: initialState,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: {
          ignoredActions: [
            // Redux persist actions
            'persist/PERSIST',
            'persist/REHYDRATE',
            'persist/REGISTER',
            'persist/PURGE',
            'persist/FLUSH',
            'persist/PAUSE',
            'persist/PERSIST_REHYDRATE',
          ],
          ignoredPaths: ['_persist'],
        },
      }),
    devTools: false, // Disable devTools in tests
  })
}

// Example test suite
describe('Redux Store Configuration', () => {
  let store: ReturnType<typeof createTestStore>

  beforeEach(() => {
    store = createTestStore()
  })

  it('should create a store with the correct initial state', () => {
    const state = store.getState()

    // Check that all reducers are present
    expect(state).toHaveProperty('persisted')
    expect(state.persisted).toHaveProperty('auth')
    expect(state.persisted).toHaveProperty('ui')
    expect(state.persisted).toHaveProperty('strategies')
  })

  it('should handle auth slice actions', () => {
    const initialState = store.getState()

    // Dispatch login start action
    store.dispatch({
      type: 'auth/loginStart',
    })

    let state = store.getState()
    expect(state.persisted.auth.isLoading).toBe(true)
    expect(state.persisted.auth.error).toBe(null)

    // Dispatch login success action
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      createdAt: '2023-01-01T00:00:00Z',
      updatedAt: '2023-01-01T00:00:00Z',
    }

    store.dispatch({
      type: 'auth/loginSuccess',
      payload: {
        user: mockUser,
        token: 'test-token',
      },
    })

    state = store.getState()
    expect(state.persisted.auth.isAuthenticated).toBe(true)
    expect(state.persisted.auth.user).toEqual(mockUser)
    expect(state.persisted.auth.token).toBe('test-token')
    expect(state.persisted.auth.isLoading).toBe(false)

    // Dispatch logout action
    store.dispatch({
      type: 'auth/logout',
    })

    state = store.getState()
    expect(state.persisted.auth.isAuthenticated).toBe(false)
    expect(state.persisted.auth.user).toBe(null)
    expect(state.persisted.auth.token).toBe(null)
  })

  it('should handle strategies slice actions', () => {
    const mockStrategy = {
      id: '1',
      name: 'Test Strategy',
      type: 'momentum',
      status: 'active',
      riskLevel: 'medium',
      createdBy: '1',
      createdAt: '2023-01-01T00:00:00Z',
      updatedAt: '2023-01-01T00:00:00Z',
      config: {
        capital: {
          allocated: 10000,
          maxAllocation: 50000,
          minAllocation: 1000,
          currency: 'USD',
        },
        trading: {
          symbols: ['AAPL', 'GOOGL'],
          exchanges: ['NYSE'],
          timeframes: ['1h'],
          orderType: 'market',
          slippage: 0.001,
          commission: 0.001,
        },
        rules: {
          entry: [],
          exit: [],
          positionSizing: [],
        },
        risk: {
          maxDrawdown: 0.2,
          positionSize: 0.1,
          stopLoss: 0.05,
          takeProfit: 0.1,
          maxPositions: 5,
          leverage: 1,
        },
        indicators: [],
      },
      performance: {
        totalReturn: 0.15,
        sharpeRatio: 1.2,
        maxDrawdown: 0.05,
        winRate: 0.6,
        profitFactor: 1.5,
        totalTrades: 50,
        winningTrades: 30,
        losingTrades: 20,
        annualizedReturn: 0.18,
        monthlyReturn: 0.015,
        weeklyReturn: 0.003,
        dailyReturn: 0.001,
        sortinoRatio: 1.7,
        volatility: 0.1,
        beta: 0.8,
        alpha: 0.02,
        avgTradeDuration: 5,
        avgWinDuration: 4,
        avgLossDuration: 2,
        avgWin: 200,
        avgLoss: 100,
        largestWin: 1000,
        largestLoss: 500,
        calmarRatio: 0.9,
        winLossRatio: 2,
        expectancy: 0.02,
        equity: [],
        returns: [],
      },
      version: '1.0.0',
    }

    // Dispatch add strategy action
    store.dispatch({
      type: 'strategies/addStrategy',
      payload: mockStrategy,
    })

    let state = store.getState()
    expect(state.persisted.strategies.items).toHaveLength(1)
    expect(state.persisted.strategies.items[0]).toEqual(mockStrategy)

    // Dispatch update strategy action
    const updates = { name: 'Updated Test Strategy' }
    store.dispatch({
      type: 'strategies/updateStrategy',
      payload: {
        id: '1',
        updates,
      },
    })

    state = store.getState()
    expect(state.persisted.strategies.items[0].name).toBe('Updated Test Strategy')

    // Dispatch delete strategy action
    store.dispatch({
      type: 'strategies/deleteStrategy',
      payload: '1',
    })

    state = store.getState()
    expect(state.persisted.strategies.items).toHaveLength(0)
  })

  it('should handle UI slice actions', () => {
    // Dispatch toggle theme action
    store.dispatch({
      type: 'ui/toggleTheme',
    })

    let state = store.getState()
    expect(state.persisted.ui.theme.mode).toBe('dark')
    expect(state.persisted.ui.themeMode).toBe('dark')

    // Dispatch toggle sidebar action
    store.dispatch({
      type: 'ui/toggleSidebar',
    })

    state = store.getState()
    expect(state.persisted.ui.layout.sidebar.collapsed).toBe(true)

    // Dispatch add notification action
    const notification = {
      type: 'success',
      title: 'Test Notification',
      message: 'This is a test notification',
    }

    store.dispatch({
      type: 'ui/addNotification',
      payload: notification,
    })

    state = store.getState()
    expect(state.persisted.ui.notifications).toHaveLength(1)
    expect(state.persisted.ui.notifications[0].title).toBe('Test Notification')

    // Dispatch set screen size action
    store.dispatch({
      type: 'ui/setScreenSize',
      payload: 'mobile',
    })

    state = store.getState()
    expect(state.persisted.ui.screenSize).toBe('mobile')
  })

  it('should handle loading state correctly', () => {
    // Dispatch global loading
    store.dispatch({
      type: 'ui/setLoading',
      payload: { loading: true, message: 'Loading...' },
    })

    let state = store.getState()
    expect(state.persisted.ui.loading.global).toBe(true)
    expect(state.persisted.ui.loading.message).toBe('Loading...')

    // Dispatch component loading
    store.dispatch({
      type: 'ui/setComponentLoading',
      payload: { component: 'strategies', loading: true },
    })

    state = store.getState()
    expect(state.persisted.ui.loading.components.strategies).toBe(true)
  })

  it('should handle error states', () => {
    // Dispatch error to auth slice
    store.dispatch({
      type: 'auth/loginFailure',
      payload: {
        message: 'Invalid credentials',
        code: 'INVALID_CREDENTIALS',
      },
    })

    let state = store.getState()
    expect(state.persisted.auth.error).toBe('Invalid credentials')

    // Dispatch error to strategies slice
    store.dispatch({
      type: 'strategies/setError',
      payload: 'Failed to load strategies',
    })

    state = store.getState()
    expect(state.persisted.strategies.error).toBe('Failed to load strategies')
  })
})

// Export test utilities
export const getMockAuthState = () => ({
  user: {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    createdAt: '2023-01-01T00:00:00Z',
    updatedAt: '2023-01-01T00:00:00Z',
  },
  token: 'test-token',
  isAuthenticated: true,
  isLoading: false,
  error: null,
  refreshToken: null,
  tokenExpiresAt: null,
  permissions: [],
  roles: [],
})

export const getMockStrategiesState = () => ({
  items: [],
  selected: null,
  editing: null,
  loading: false,
  error: null,
  filters: {
    status: [],
    type: [],
    riskLevel: [],
    searchTerm: '',
  },
  sorting: {
    field: 'updatedAt',
    direction: 'desc',
  },
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },
  execution: {
    running: {},
    logs: [],
    positions: [],
    orders: [],
    performance: {
      totalTrades: 0,
      winRate: 0,
      profitFactor: 0,
      sharpeRatio: 0,
      maxDrawdown: 0,
      totalPnl: 0,
      dailyPnl: [],
    },
  },
  backtest: {
    results: [],
    running: false,
    progress: 0,
    config: null,
  },
})

export const getMockUIState = () => ({
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

  // Legacy properties for backward compatibility
  themeMode: 'light',
  sidebarCollapsed: false,
  loadingMessage: undefined,
  pageTitle: undefined,
  breadcrumbs: [],
  recentPages: [],
  favoritePages: [],
  systemStatus: 'online',
  activeModals: [],
  webSocketStatus: {
    connected: false,
    reconnecting: false,
    reconnectAttempts: 0,
  },
  realtimeStrategies: [],
  realtimeSignals: [],
  systemHealth: null,
})