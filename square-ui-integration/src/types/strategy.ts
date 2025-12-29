/**
 * Strategy related types
 */

// Strategy
export interface Strategy {
  id: string
  name: string
  description?: string
  type: StrategyType
  status: StrategyStatus
  isActive: boolean
  parameters: StrategyParameter[]
  performance?: StrategyPerformance
  riskMetrics?: RiskMetrics
  createdBy: string
  createdAt: Date | string
  updatedAt: Date | string
  lastRunAt?: Date | string
  tags?: string[]
}

// Strategy Type
export type StrategyType =
  | 'trend_following'
  | 'mean_reversion'
  | 'momentum'
  | 'arbitrage'
  | 'market_making'
  | 'statistical'
  | 'custom'

// Strategy Status
export type StrategyStatus =
  | 'draft'
  | 'testing'
  | 'active'
  | 'paused'
  | 'stopped'
  | 'error'

// Strategy Parameter
export interface StrategyParameter {
  name: string
  value: any
  type: 'number' | 'string' | 'boolean' | 'array' | 'object'
  description?: string
  min?: number
  max?: number
  options?: string[]
  required: boolean
}

// Strategy Performance
export interface StrategyPerformance {
  totalReturn: number
  annualizedReturn: number
  sharpeRatio: number
  sortinoRatio: number
  maxDrawdown: number
  winRate: number
  profitFactor: number
  totalTrades: number
  winningTrades: number
  losingTrades: number
  averageWin: number
  averageLoss: number
  averageTradeDuration: string
  bestTrade: number
  worstTrade: number
  calmarRatio: number
  omegaRatio: number
  var95: number // Value at Risk 95%
  cvar95: number // Conditional Value at Risk 95%
}

// Risk Metrics
export interface RiskMetrics {
  beta: number
  alpha: number
  correlation: number
  volatility: number
  downsideDeviation: number
  informationRatio: number
  treynorRatio: number
  trackingError: number
  upCapture: number
  downCapture: number
}

// Backtest
export interface Backtest {
  id: string
  strategyId: string
  name: string
  parameters: Record<string, any>
  dateRange: {
    start: Date | string
    end: Date | string
  }
  initialCapital: number
  results: BacktestResult
  trades: Trade[]
  equityCurve: EquityPoint[]
  performance: StrategyPerformance
  status: BacktestStatus
  createdAt: Date | string
  completedAt?: Date | string
}

// Backtest Result
export interface BacktestResult {
  finalEquity: number
  totalReturn: number
  annualizedReturn: number
  maxDrawdown: number
  sharpeRatio: number
  winRate: number
  profitFactor: number
  totalTrades: number
}

// Backtest Status
export type BacktestStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'

// Trade
export interface Trade {
  id: string
  strategyId: string
  symbol: string
  type: TradeType
  direction: TradeDirection
  quantity: number
  price: number
  value: number
  commission: number
  timestamp: Date | string
  profit?: number
  profitPercent?: number
  exitPrice?: number
  exitTimestamp?: Date | string
  duration?: string
  notes?: string
}

// Trade Type
export type TradeType = 'market' | 'limit' | 'stop' | 'stop_limit'

// Trade Direction
export type TradeDirection = 'long' | 'short'

// Equity Point
export interface EquityPoint {
  date: Date | string
  equity: number
  drawdown: number
  returns: number
}

// Strategy Config
export interface StrategyConfig {
  name: string
  description?: string
  type: StrategyType
  parameters: StrategyParameter[]
  indicators: IndicatorConfig[]
  rules: StrategyRule[]
  riskManagement: RiskManagementConfig
}

// Indicator Config
export interface IndicatorConfig {
  name: string
  type: string
  parameters: Record<string, any>
  inputs: string[]
}

// Strategy Rule
export interface StrategyRule {
  name: string
  conditions: RuleCondition[]
  actions: RuleAction[]
  isEnabled: boolean
}

// Rule Condition
export interface RuleCondition {
  operator: 'AND' | 'OR'
  left: RuleExpression
  right?: RuleExpression
}

// Rule Expression
export interface RuleExpression {
  type: 'indicator' | 'price' | 'value' | 'function'
  operator: string
  value: any
}

// Rule Action
export interface RuleAction {
  type: 'buy' | 'sell' | 'close' | 'alert' | 'custom'
  parameters: Record<string, any>
}

// Risk Management Config
export interface RiskManagementConfig {
  maxPositionSize: number
  maxDrawdown: number
  maxLossPerTrade: number
  maxPositions: number
  stopLoss?: number
  takeProfit?: number
  trailingStop?: number
}

// Strategy State
export interface StrategyState {
  strategies: Strategy[]
  activeStrategies: string[]
  isLoading: boolean
  error: string | null
}