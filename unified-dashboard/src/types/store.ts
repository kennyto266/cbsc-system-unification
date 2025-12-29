// Enhanced Store type definitions for Redux
export interface RootState {
  auth: AuthState
  ui: UIState
  market: MarketState
  strategies: StrategiesState
  dashboard: DashboardState
  api: ApiState
}

// UI State Interface
export interface UIState {
  theme: 'light' | 'dark'
  sidebarCollapsed: boolean
  notifications: Notification[]
  loading: {
    global: boolean
    components: Record<string, boolean>
  }
  layout: {
    headerHeight: number
    sidebarWidth: number
    contentPadding: number
  }
  modals: {
    createStrategy: boolean
    editStrategy: boolean
    confirmDialog: boolean
  }
  preferences: {
    language: string
    timezone: string
    dateFormat: string
    autoRefresh: boolean
    refreshInterval: number
  }
}

// Market State Interface
export interface MarketState {
  data: MarketData[]
  selectedSymbol: string | null
  timeFrame: '1m' | '5m' | '15m' | '1h' | '4h' | '1d'
  indicators: IndicatorState
  websocket: WebSocketState
  lastUpdate: string | null
  loading: boolean
  error: string | null
}

export interface MarketData {
  symbol: string
  price: number
  change: number
  changePercent: number
  volume: number
  high24h: number
  low24h: number
  timestamp: string
  // Ohlc data for charts
  ohlc?: Array<{
    time: number
    open: number
    high: number
    low: number
    close: number
    volume: number
  }>
}

export interface IndicatorState {
  sma: Record<string, number[]>
  ema: Record<string, number[]>
  rsi: Record<string, number[]>
  macd: Record<string, MACDData>
  bollinger: Record<string, BollingerData>
  volume: Record<string, number[]>
}

export interface MACDData {
  macd: number[]
  signal: number[]
  histogram: number[]
}

export interface BollingerData {
  upper: number[]
  middle: number[]
  lower: number[]
}

export interface WebSocketState {
  connected: boolean
  reconnecting: boolean
  error: string | null
  reconnectAttempts: number
  subscriptions: string[]
}

// Enhanced Strategies State
export interface StrategiesState {
  items: Strategy[]
  selected: string | null
  filters: StrategyFilters
  sorting: {
    field: string
    direction: 'asc' | 'desc'
  }
  pagination: {
    page: number
    pageSize: number
    total: number
  }
  execution: ExecutionState
  backtest: BacktestState
}

export interface StrategyFilters {
  status: StrategyStatus | 'all'
  type: StrategyType | 'all'
  riskLevel: RiskLevel | 'all'
  searchTerm: string
  dateRange?: {
    start: string
    end: string
  }
}

export interface ExecutionState {
  running: Record<string, boolean>
  logs: ExecutionLog[]
  positions: Position[]
  orders: Order[]
  performance: ExecutionPerformance
}

export interface ExecutionLog {
  id: string
  strategyId: string
  timestamp: string
  level: 'info' | 'warning' | 'error'
  message: string
  data?: any
}

export interface Position {
  id: string
  symbol: string
  side: 'long' | 'short'
  size: number
  entryPrice: number
  currentPrice: number
  pnl: number
  pnlPercent: number
  strategyId: string
  openedAt: string
}

export interface Order {
  id: string
  symbol: string
  type: 'market' | 'limit' | 'stop'
  side: 'buy' | 'sell'
  amount: number
  price?: number
  status: 'pending' | 'filled' | 'cancelled'
  strategyId: string
  createdAt: string
  filledAt?: string
}

export interface ExecutionPerformance {
  totalTrades: number
  winRate: number
  profitFactor: number
  sharpeRatio: number
  maxDrawdown: number
  totalPnl: number
  dailyPnl: Array<{
    date: string
    pnl: number
  }>
}

export interface BacktestState {
  results: BacktestResult[]
  running: boolean
  progress: number
  config: BacktestConfig | null
}

export interface BacktestResult {
  id: string
  strategyId: string
  config: BacktestConfig
  performance: {
    totalReturn: number
    sharpeRatio: number
    maxDrawdown: number
    winRate: number
    profitFactor: number
    calmarRatio: number
  }
  trades: Array<{
    entry: string
    exit: string
    type: 'long' | 'short'
    pnl: number
    pnlPercent: number
  }>
  equity: Array<{
    date: string
    equity: number
  }>
  createdAt: string
}

export interface BacktestConfig {
  startDate: string
  endDate: string
  initialCapital: number
  commission: number
  slippage: number
  symbols: string[]
}

// Dashboard State
export interface DashboardState {
  layout: DashboardLayout
  widgets: WidgetState[]
  timeRange: TimeRange
  refreshRate: number
  alerts: Alert[]
  quickActions: QuickAction[]
}

export interface DashboardLayout {
  columns: number
  rowHeight: number
  margin: [number, number]
  containerPadding: [number, number]
}

export interface WidgetState {
  id: string
  type: WidgetType
  title: string
  position: {
    x: number
    y: number
    w: number
    h: number
  }
  config: Record<string, any>
  data?: any
  loading?: boolean
  error?: string
  lastUpdate?: string
}

export type WidgetType =
  | 'metric-card'
  | 'chart'
  | 'strategy-list'
  | 'market-overview'
  | 'system-health'
  | 'recent-signals'
  | 'quick-actions'
  | 'news-feed'
  | 'calendar'
  | 'custom'

export type TimeRange = '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | 'ALL'

export interface Alert {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: string
  read: boolean
  action?: {
    label: string
    onClick: () => void
  }
}

export interface QuickAction {
  id: string
  label: string
  icon: string
  action: string
  params?: Record<string, any>
  disabled?: boolean
  tooltip?: string
}

// API State
export interface ApiState {
  requests: Record<string, RequestState>
  cache: {
    [key: string]: {
      data: any
      timestamp: number
      ttl: number
    }
  }
  errors: ApiError[]
}

export interface RequestState {
  loading: boolean
  data?: any
  error?: string
  lastFetch?: number
}

export interface ApiError {
  id: string
  endpoint: string
  method: string
  message: string
  code?: number
  timestamp: string
}

// Notification Interface
export interface Notification {
  id: string
  type: 'success' | 'info' | 'warning' | 'error'
  title: string
  message: string
  duration?: number
  timestamp: string
  persistent?: boolean
  actions?: Array<{
    label: string
    action: () => void
  }>
}

// Redux Action Types
export interface ReduxAction<T = any> {
  type: string
  payload?: T
  meta?: any
  error?: boolean
}

// Store Configuration
export interface StoreConfig {
  persist: {
    key: string
    storage: 'localStorage' | 'sessionStorage'
    whitelist: string[]
    blacklist: string[]
  }
  devTools: boolean
  middleware: string[]
}