// Enhanced strategy types for CBSC system

// Strategy base interface
export interface Strategy {
  id: string
  name: string
  description?: string
  type: StrategyType
  status: StrategyStatus
  riskLevel: RiskLevel
  createdBy: string
  createdAt: string
  updatedAt: string
  lastActive?: string
  tags?: string[]
  category?: string
  version: string

  // Configuration
  config: StrategyConfig

  // Performance metrics
  performance: PerformanceMetrics

  // Execution state
  execution?: ExecutionState

  // Risk management
  riskManagement?: RiskManagement

  // Optimization settings
  optimization?: OptimizationSettings
}

// Strategy types enum
export enum StrategyType {
  MOMENTUM = 'momentum',
  MEAN_REVERSION = 'mean_reversion',
  ARBITRAGE = 'arbitrage',
  TREND_FOLLOWING = 'trend_following',
  SENTIMENT = 'sentiment',
  TECHNICAL = 'technical',
  FUNDAMENTAL = 'fundamental',
  STATISTICAL = 'statistical',
  MACHINE_LEARNING = 'machine_learning',
  GRID = 'grid',
  DCA = 'dollar_cost_averaging',
  CUSTOM = 'custom'
}

// Strategy status enum
export enum StrategyStatus {
  DRAFT = 'draft',
  TESTING = 'testing',
  ACTIVE = 'active',
  PAUSED = 'paused',
  STOPPED = 'stopped',
  ARCHIVED = 'archived',
  ERROR = 'error'
}

// Risk level enum
export enum RiskLevel {
  VERY_LOW = 'very_low',
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  VERY_HIGH = 'very_high'
}

// Strategy configuration
export interface StrategyConfig {
  // General settings
  capital: {
    allocated: number
    maxAllocation: number
    minAllocation: number
    currency: string
  }

  // Trading parameters
  trading: {
    symbols: string[]
    exchanges: string[]
    timeframes: TimeFrame[]
    orderType: 'market' | 'limit' | 'stop'
    slippage: number
    commission: number
  }

  // Entry/exit rules
  rules: {
    entry: EntryRule[]
    exit: ExitRule[]
    positionSizing: PositionSizingRule[]
  }

  // Risk parameters
  risk: {
    maxDrawdown: number
    positionSize: number
    stopLoss: number
    takeProfit: number
    maxPositions: number
    leverage: number
  }

  // Technical indicators
  indicators: IndicatorConfig[]

  // Custom parameters
  custom?: Record<string, any>
}

// Time frame options
export type TimeFrame = '1m' | '3m' | '5m' | '15m' | '30m' | '1h' | '2h' | '4h' | '6h' | '8h' | '12h' | '1d' | '1w' | '1M'

// Entry rule interface
export interface EntryRule {
  id: string
  name: string
  type: 'technical' | 'fundamental' | 'custom'
  condition: string
  parameters: Record<string, any>
  enabled: boolean
}

// Exit rule interface
export interface ExitRule {
  id: string
  name: string
  type: 'stop_loss' | 'take_profit' | 'trailing_stop' | 'time_based' | 'custom'
  condition: string
  parameters: Record<string, any>
  enabled: boolean
}

// Position sizing rule interface
export interface PositionSizingRule {
  id: string
  name: string
  type: 'fixed' | 'percentage' | 'volatility' | 'kelly' | 'custom'
  parameters: Record<string, any>
  enabled: boolean
}

// Indicator configuration
export interface IndicatorConfig {
  name: string
  parameters: Record<string, any>
  timeframe?: TimeFrame
  source?: 'close' | 'open' | 'high' | 'low' | 'hl2' | 'hlc3' | 'ohlc4'
}

// Performance metrics
export interface PerformanceMetrics {
  // Return metrics
  totalReturn: number
  annualizedReturn: number
  monthlyReturn: number
  weeklyReturn: number
  dailyReturn: number

  // Risk metrics
  sharpeRatio: number
  sortinoRatio: number
  maxDrawdown: number
  avgDrawdown: number
  volatility: number
  beta: number
  alpha: number

  // Trade metrics
  totalTrades: number
  winningTrades: number
  losingTrades: number
  winRate: number
  profitFactor: number
  avgWin: number
  avgLoss: number
  largestWin: number
  largestLoss: number

  // Time-based metrics
  avgTradeDuration: number
  avgWinDuration: number
  avgLossDuration: number
  bestMonth: number
  worstMonth: number

  // Other metrics
  calmarRatio: number
  informationRatio: number
  winLossRatio: number
  expectancy: number

  // Historical data
  equity: EquityPoint[]
  returns: ReturnPoint[]
}

// Equity curve point
export interface EquityPoint {
  date: string
  value: number
  drawdown?: number
}

// Return point
export interface ReturnPoint {
  date: string
  value: number
  cumulative?: number
}

// Execution state
export interface ExecutionState {
  isRunning: boolean
  lastExecution: string
  nextExecution?: string
  executionMode: 'live' | 'paper' | 'backtest'
  logs: ExecutionLog[]
  positions: Position[]
  orders: Order[]
  alerts: Alert[]
}

// Execution log
export interface ExecutionLog {
  id: string
  timestamp: string
  level: 'debug' | 'info' | 'warning' | 'error'
  message: string
  data?: any
  source: string
}

// Position
export interface Position {
  id: string
  symbol: string
  exchange: string
  side: 'long' | 'short'
  size: number
  entryPrice: number
  currentPrice: number
  unrealizedPnl: number
  realizedPnl: number
  fees: number
  margin: number
  leverage: number
  openedAt: string
  updatedAt: string
  strategyId: string
}

// Order
export interface Order {
  id: string
  symbol: string
  exchange: string
  type: 'market' | 'limit' | 'stop' | 'stop_limit'
  side: 'buy' | 'sell'
  amount: number
  price?: number
  stopPrice?: number
  status: 'pending' | 'partial' | 'filled' | 'cancelled' | 'rejected'
  filledAmount: number
  averagePrice: number
  fees: number
  createdAt: string
  updatedAt: string
  expiresAt?: string
  strategyId: string
  positionId?: string
}

// Alert
export interface Alert {
  id: string
  type: 'info' | 'warning' | 'error' | 'success'
  title: string
  message: string
  timestamp: string
  read: boolean
  metadata?: Record<string, any>
  actions?: AlertAction[]
}

// Alert action
export interface AlertAction {
  label: string
  action: string
  params?: Record<string, any>
}

// Risk management
export interface RiskManagement {
  stopLoss: {
    type: 'fixed' | 'percentage' | 'atr' | 'custom'
    value: number
    trailing?: boolean
  }
  takeProfit: {
    type: 'fixed' | 'percentage' | 'risk_reward' | 'custom'
    value: number
  }
  positionSizing: {
    type: 'fixed' | 'percentage' | 'volatility' | 'kelly' | 'optimal_f'
    value: number
  }
  maxPositions: number
  maxExposure: number
  correlationLimit: number
}

// Optimization settings
export interface OptimizationSettings {
  enabled: boolean
  parameters: OptimizationParameter[]
  objective: 'sharpe_ratio' | 'total_return' | 'max_drawdown' | 'profit_factor' | 'custom'
  constraints: OptimizationConstraint[]
  iterations: number
  populationSize?: number
  algorithm?: 'genetic' | 'grid_search' | 'random_search' | 'bayesian'
}

// Optimization parameter
export interface OptimizationParameter {
  name: string
  min: number
  max: number
  step?: number
  type: 'continuous' | 'discrete'
}

// Optimization constraint
export interface OptimizationConstraint {
  name: string
  operator: '<' | '<=' | '>' | '>=' | '='
  value: number
}

// Strategy filter options
export interface StrategyFilters {
  status?: StrategyStatus[]
  type?: StrategyType[]
  riskLevel?: RiskLevel[]
  createdBy?: string[]
  tags?: string[]
  dateRange?: {
    start: string
    end: string
  }
  performanceRange?: {
    field: keyof PerformanceMetrics
    min: number
    max: number
  }
  searchTerm?: string
}

// Strategy sorting options
export interface StrategySorting {
  field: keyof Strategy | keyof PerformanceMetrics
  direction: 'asc' | 'desc'
}

// Strategy pagination
export interface StrategyPagination {
  page: number
  pageSize: number
  total: number
}

// Strategy backtest request
export interface BacktestRequest {
  strategyId: string
  config: {
    startDate: string
    endDate: string
    initialCapital: number
    commission: number
    slippage: number
  }
  parameters?: Record<string, any>
}

// Strategy backtest result
export interface BacktestResult {
  id: string
  strategyId: string
  config: BacktestRequest['config']
  parameters: Record<string, any>
  performance: PerformanceMetrics
  trades: Trade[]
  equity: EquityPoint[]
  benchmark?: EquityPoint[]
  createdAt: string
}

// Trade
export interface Trade {
  id: string
  symbol: string
  exchange: string
  type: 'long' | 'short'
  entryDate: string
  exitDate?: string
  entryPrice: number
  exitPrice?: number
  size: number
  pnl?: number
  pnlPercent?: number
  fees: number
  commission: number
  duration?: number
  strategyId: string
}

// Strategy performance analysis
export interface PerformanceAnalysis {
  strategyId: string
  period: string
  benchmark?: string
  metrics: {
    alpha: number
    beta: number
    sharpeRatio: number
    sortinoRatio: number
    treynorRatio: number
    informationRatio: number
    trackingError: number
    upCapture: number
    downCapture: number
  }
  attribution: AttributionAnalysis
}

// Attribution analysis
export interface AttributionAnalysis {
  sectors?: SectorAttribution[]
  factors?: FactorAttribution[]
  securities?: SecurityAttribution[]
}

// Sector attribution
export interface SectorAttribution {
  sector: string
  contribution: number
  weight: number
  return: number
}

// Factor attribution
export interface FactorAttribution {
  factor: string
  exposure: number
  contribution: number
}

// Security attribution
export interface SecurityAttribution {
  symbol: string
  contribution: number
  weight: number
  return: number
}