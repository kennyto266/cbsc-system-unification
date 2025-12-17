// 策略類型枚舉
export enum StrategyType {
  MEAN_REVERSION = 'mean_reversion',
  MOMENTUM = 'momentum',
  TECHNICAL = 'technical',
  SENTIMENT = 'sentiment',
  ARBITRAGE = 'arbitrage',
  GRID = 'grid',
  DCA = 'dca',
  CUSTOM = 'custom',
}

// 策略狀態枚舉
export enum StrategyStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  PAUSED = 'paused',
  TESTING = 'testing',
  ERROR = 'error',
}

// 風險等級枚舉
export enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  EXTREME = 'extreme',
}

// 信號類型枚舉
export enum SignalType {
  BUY = 'buy',
  SELL = 'sell',
  HOLD = 'hold',
}

// 時間範圍類型
export type TimeRange = '1d' | '1w' | '1m' | '3m' | '6m' | '1y' | 'all'

// 圖表時間範圍類型
export type ChartTimeRange = '1D' | '1W' | '1M' | '3M' | '6M' | '1Y'

// 比較指標類型
export type ComparisonMetric =
  | 'totalReturn'
  | 'sharpeRatio'
  | 'maxDrawdown'
  | 'winRate'
  | 'profitFactor'
  | 'calmarRatio'
  | 'sortinoRatio'
  | 'informationRatio'

// 基礎策略接口
export interface Strategy {
  id: string
  name: string
  type: StrategyType
  status: StrategyStatus
  riskLevel: RiskLevel
  description: string
  parameters: Record<string, any>
  performance: StrategyPerformance
  createdAt: string
  updatedAt: string
}

// 策略性能指標
export interface StrategyPerformance {
  totalReturn: number
  sharpeRatio: number
  maxDrawdown: number
  winRate: number
  profitFactor: number
  annualizedReturn?: number
  volatility?: number
  calmarRatio?: number
  sortinoRatio?: number
  var95?: number
  cvar95?: number
  beta?: number
  alpha?: number
  informationRatio?: number
  trackingError?: number
}

// 執行記錄
export interface Execution {
  id: string
  strategyId: string
  symbol: string
  type: SignalType
  quantity: number
  price: number
  timestamp: string
  status: 'pending' | 'executed' | 'failed' | 'cancelled'
  fee: number
  pnl?: number
  commission: number
  slippage: number
}

// 信號
export interface Signal {
  id: string
  strategyId: string
  symbol: string
  type: SignalType
  strength: number
  price: number
  timestamp: string
  indicators: Record<string, number>
  confidence: number
  reason: string
  metadata?: Record<string, any>
}

// 資產配置
export interface AssetAllocation {
  byStrategy: Array<{
    name: string
    value: number
    percentage: number
    color?: string
  }>
  byAsset: Array<{
    name: string
    value: number
    percentage: number
    color?: string
  }>
  byRisk: Array<{
    name: string
    value: number
    percentage: number
    color?: string
  }>
}

// 圖表數據點
export interface ChartDataPoint {
  x: string | number
  y: number
  label?: string
  color?: string
  metadata?: Record<string, any>
}

// 圖表數據
export interface ChartData {
  labels: string[]
  datasets: Array<{
    label: string
    data: number[]
    borderColor?: string
    backgroundColor?: string
    fill?: boolean
    tension?: number
    metadata?: Record<string, any>
  }>
}

// 市場數據
export interface MarketData {
  symbol: string
  price: number
  change: number
  changePercent: number
  volume: number
  high24h: number
  low24h: number
  timestamp: string
}

// 投資組合指標
export interface PortfolioMetrics {
  totalValue: number
  totalReturn: number
  annualizedReturn: number
  volatility: number
  sharpeRatio: number
  maxDrawdown: number
  calmarRatio: number
  winRate: number
  profitFactor: number
  var95: number
  cvar95: number
  beta: number
  alpha: number
  correlation: number
  trackingError: number
  informationRatio: number
}

// 用戶信息
export interface User {
  id: string
  username: string
  email: string
  avatar?: string
  role: 'admin' | 'user' | 'viewer'
  isActive: boolean
  lastLoginAt?: string
  createdAt: string
  updatedAt: string
}

// 用戶偏好設置
export interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  language: 'zh-CN' | 'en-US'
  timezone: string
  currency: 'CNY' | 'USD' | 'EUR'
  notifications: {
    email: boolean
    push: boolean
    sms: boolean
  }
  dashboard: {
    defaultTimeRange: TimeRange
    refreshInterval: number
    showAdvancedMetrics: boolean
  }
}

// 系統健康指標
export interface SystemHealth {
  cpu: number
  memory: number
  disk: number
  network: number
  services: Array<{
    name: string
    status: 'healthy' | 'warning' | 'error'
    uptime: number
    responseTime?: number
  }>
  lastUpdated: string
}

// 警報
export interface Alert {
  id: string
  type: 'info' | 'warning' | 'error' | 'success'
  title: string
  message: string
  timestamp: string
  isRead: boolean
  category: 'system' | 'strategy' | 'market' | 'execution'
  metadata?: Record<string, any>
}

// API響應基類
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
    details?: Record<string, any>
  }
  timestamp: string
}

// 分頁參數
export interface PaginationParams {
  page: number
  limit: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

// 分頁響應
export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
    hasNext: boolean
    hasPrev: boolean
  }
}

// WebSocket消息類型
export interface WebSocketMessage {
  type: 'price_update' | 'signal' | 'execution' | 'alert' | 'system_status'
  data: any
  timestamp: string
}

// CBSC牛熊證數據
export interface CBBCData {
  id: string
  code: string
  name: string
  underlying: string
  type: 'bull' | 'bear'
  strikePrice: number
  currentPrice: number
  change: number
  changePercent: number
  volume: number
  turnover: number
  expiryDate: string
  gearing: number
  callPrice?: number
  killPrice?: number
  status: 'active' | 'expired' | 'called' | 'killed'
  lastUpdated: string
}

// 市場情感數據
export interface MarketSentiment {
  overall: 'bullish' | 'bearish' | 'neutral'
  score: number
  trends: Array<{
    period: string
    sentiment: 'bullish' | 'bearish' | 'neutral'
    score: number
    change: number
  }>
  factors: Array<{
    name: string
    weight: number
    value: number
    impact: 'positive' | 'negative' | 'neutral'
  }>
}

// 風險分析數據
export interface RiskAnalysis {
  varAnalysis: {
    var95: number
    var99: number
    cvar95: number
    cvar99: number
    timeHorizon: string
  }
  stressTest: Array<{
    scenario: string
    impact: number
    probability: number
    description: string
  }>
  riskContribution: Array<{
    strategy: string
    contribution: number
    percentage: number
  }>
  concentrationRisk: {
    hhi: number
    top10Concentration: number
    diversificationRatio: number
  }
}

// 回測結果
export interface BacktestResult {
  strategyId: string
  startDate: string
  endDate: string
  initialCapital: number
  finalValue: number
  totalReturn: number
  annualizedReturn: number
  maxDrawdown: number
  sharpeRatio: number
  winRate: number
  profitFactor: number
  totalTrades: number
  equityCurve: Array<{
    date: string
    value: number
    drawdown: number
  }>
  trades: Execution[]
  monthlyReturns: Array<{
    month: string
    return: number
  }>
}

// 報告配置
export interface ReportConfig {
  type: 'performance' | 'risk' | 'attribution' | 'custom'
  format: 'pdf' | 'excel' | 'csv'
  dateRange: {
    start: string
    end: string
  }
  strategies?: string[]
  metrics?: string[]
  includeCharts: boolean
  template?: string
}