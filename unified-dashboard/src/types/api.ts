// API type definitions for RTK Query

// Base API Types
export interface BaseQueryParams {
  [key: string]: any
}

export interface BaseApiResponse<T = any> {
  data: T
  success: boolean
  message?: string
  timestamp: string
}

export interface PaginationParams {
  page: number
  pageSize: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  items: T[]
  pagination: {
    page: number
    pageSize: number
    total: number
    totalPages: number
  }
}

// Auth API Types
export interface LoginRequest {
  username: string
  password: string
  remember?: boolean
  captcha?: string
}

export interface LoginResponse {
  user: User
  token: string
  refreshToken: string
  expiresIn: number
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirmPassword: string
  captcha?: string
  agreeTerms: boolean
}

export interface RefreshTokenRequest {
  refreshToken: string
}

export interface RefreshTokenResponse {
  token: string
  expiresIn: number
}

// User Profile Types
export interface UserProfile extends User {
  firstName?: string
  lastName?: string
  phone?: string
  timezone: string
  language: string
  preferences: UserPreferences
  subscription: UserSubscription
  security: UserSecurity
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto'
  language: string
  timezone: string
  dateFormat: string
  timeFormat: '12h' | '24h'
  notifications: NotificationPreferences
  dashboard: DashboardPreferences
}

export interface NotificationPreferences {
  email: boolean
  sms: boolean
  push: boolean
  types: {
    signals: boolean
    executions: boolean
    alerts: boolean
    system: boolean
  }
}

export interface DashboardPreferences {
  layout: string
  widgets: Array<{
    id: string
    type: string
    position: any
    config: any
  }>
  refreshInterval: number
}

export interface UserSubscription {
  plan: 'free' | 'basic' | 'premium' | 'enterprise'
  status: 'active' | 'inactive' | 'cancelled' | 'expired'
  startDate: string
  endDate: string
  features: string[]
  limits: {
    strategies: number
    apiCalls: number
    dataPoints: number
  }
}

export interface UserSecurity {
  twoFactorEnabled: boolean
  lastLogin: string
  loginHistory: Array<{
    ip: string
    location: string
    timestamp: string
    userAgent: string
  }>
  apiKeys: Array<{
    id: string
    name: string
    key: string
    permissions: string[]
    lastUsed?: string
    createdAt: string
  }>
}

// Market Data API Types
export interface MarketDataRequest {
  symbol: string
  interval: string
  startTime?: string
  endTime?: string
  limit?: number
}

export interface MarketDataResponse {
  symbol: string
  interval: string
  data: Array<{
    timestamp: string
    open: number
    high: number
    low: number
    close: number
    volume: number
  }>
}

export interface TickerResponse {
  symbol: string
  price: number
  change: number
  changePercent: number
  volume: number
  quoteVolume: number
  high24h: number
  low24h: number
  open24h: number
  timestamp: string
}

export interface OrderBookResponse {
  symbol: string
  bids: Array<[number, number]>
  asks: Array<[number, number]>
  timestamp: string
}

export interface RecentTradesResponse {
  symbol: string
  trades: Array<{
    id: string
    price: number
    quantity: number
    side: 'buy' | 'sell'
    timestamp: string
  }>
}

// Strategy API Types
export interface CreateStrategyRequest {
  name: string
  description?: string
  type: StrategyType
  parameters: Record<string, any>
  symbols: string[]
  timeframe: string
  riskSettings: RiskSettings
}

export interface UpdateStrategyRequest {
  name?: string
  description?: string
  parameters?: Record<string, any>
  symbols?: string[]
  timeframe?: string
  riskSettings?: RiskSettings
  status?: StrategyStatus
}

export interface RiskSettings {
  maxPositionSize: number
  maxDailyLoss: number
  stopLoss: number
  takeProfit: number
  leverage: number
}

export interface StrategyPerformanceResponse {
  strategyId: string
  period: string
  metrics: {
    totalReturn: number
    annualizedReturn: number
    sharpeRatio: number
    sortinoRatio: number
    maxDrawdown: number
    calmarRatio: number
    winRate: number
    profitFactor: number
    avgWin: number
    avgLoss: number
    totalTrades: number
  }
  equity: Array<{
    date: string
    value: number
  }>
  drawdown: Array<{
    date: string
    value: number
  }>
  monthlyReturns: Array<{
    month: string
    return: number
  }>
}

export interface BacktestRequest {
  strategyId: string
  config: BacktestConfig
}

export interface BacktestResponse {
  id: string
  status: 'running' | 'completed' | 'failed'
  progress: number
  result?: BacktestResult
  error?: string
}

// Execution API Types
export interface StartStrategyRequest {
  strategyId: string
  mode: 'paper' | 'live'
  allocation?: number
}

export interface StopStrategyRequest {
  strategyId: string
  reason?: string
}

export interface StrategyExecutionResponse {
  strategyId: string
  status: 'running' | 'stopped' | 'error'
  mode: 'paper' | 'live'
  startTime: string
  uptime: string
  trades: number
  pnl: number
  positions: number
  error?: string
}

export interface ManualOrderRequest {
  symbol: string
  side: 'buy' | 'sell'
  type: 'market' | 'limit' | 'stop' | 'stop_limit'
  quantity: number
  price?: number
  stopPrice?: number
  timeInForce?: 'GTC' | 'IOC' | 'FOK' | 'DAY'
}

export interface OrderResponse {
  orderId: string
  symbol: string
  side: 'buy' | 'sell'
  type: string
  quantity: number
  price?: number
  status: 'pending' | 'filled' | 'partial' | 'cancelled' | 'rejected'
  filledQuantity: number
  averagePrice?: number
  createdAt: string
  updatedAt: string
  fees: {
    amount: number
    currency: string
  }
}

// Analytics API Types
export interface AnalyticsRequest {
  type: 'performance' | 'risk' | 'correlation' | 'attribution'
  filters?: {
    strategies?: string[]
    symbols?: string[]
    dateRange?: {
      start: string
      end: string
    }
  }
  groupBy?: 'day' | 'week' | 'month' | 'quarter'
}

export interface AnalyticsResponse {
  type: string
  period: string
  data: any
  metadata: {
    generatedAt: string
    dataSource: string
    currency: string
  }
}

export interface PortfolioAnalyticsResponse {
  totalValue: number
  totalReturn: number
  dailyReturn: number
  volatility: number
  sharpeRatio: number
  maxDrawdown: number
  var: {
    daily95: number
    weekly95: number
    monthly95: number
  }
  correlation: Array<{
    asset1: string
    asset2: string
    correlation: number
  }>
  allocation: Array<{
    strategy: string
    value: number
    percentage: number
  }>
}

// Indicators API Types
export interface IndicatorRequest {
  symbol: string
  indicator: string
  parameters: Record<string, any>
  interval?: string
  limit?: number
}

export interface IndicatorResponse {
  symbol: string
  indicator: string
  parameters: Record<string, any>
  data: Array<{
    timestamp: string
    value: number | Array<number>
  }>
}

// WebSocket API Types
export interface WebSocketSubscriptionRequest {
  channel: string
  symbol?: string
  params?: Record<string, any>
}

export interface WebSocketMessage {
  channel: string
  data: any
  timestamp: string
}

// Technical Indicators Types
export interface TechnicalIndicator {
  name: string
  type: 'trend' | 'momentum' | 'volatility' | 'volume' | 'oscillator'
  description: string
  parameters: IndicatorParameter[]
  overlays: boolean
}

export interface IndicatorParameter {
  name: string
  type: 'number' | 'boolean' | 'select'
  value: any
  min?: number
  max?: number
  step?: number
  options?: Array<{
    label: string
    value: any
  }>
}

// Import existing types
import { User, Strategy, StrategyType, StrategyStatus, RiskLevel, BacktestResult, BacktestConfig } from './index'