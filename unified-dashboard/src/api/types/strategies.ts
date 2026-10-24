/**
 * Strategy Types
 * Types related to trading strategies
 */

// Strategy enumeration types
export enum StrategyType {
  MEAN_REVERSION = 'mean_reversion',
  MOMENTUM = 'momentum',
  ARBITRAGE = 'arbitrage',
  TECHNICAL = 'technical',
  FUNDAMENTAL = 'fundamental',
  SENTIMENT = 'sentiment',
  MARKET_MAKING = 'market_making',
  STATISTICAL = 'statistical',
  CUSTOM = 'custom',
}

export enum StrategyStatus {
  DRAFT = 'draft',
  TESTING = 'testing',
  ACTIVE = 'active',
  PAUSED = 'paused',
  STOPPED = 'stopped',
  ARCHIVED = 'archived',
}

export enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  EXTREME = 'extreme',
}

// Base Strategy
export interface Strategy {
  id: string
  name: string
  description: string
  type: StrategyType
  status: StrategyStatus
  riskLevel: RiskLevel
  tags: string[]
  parameters: Record<string, any>
  performance: StrategyPerformance
  createdAt: string
  updatedAt: string
  createdBy: string
  isActive: boolean
  lastRunAt?: string
  nextRunAt?: string
  totalRuns: number
  version: string
  parentId?: string
  isTemplate: boolean
  category?: string
}

// Strategy creation request
export interface CreateStrategyRequest {
  name: string
  description: string
  type: StrategyType
  riskLevel: RiskLevel
  tags?: string[]
  parameters: Record<string, any>
  category?: string
  code?: {
    language: 'python' | 'javascript'
    content: string
  }
  indicators?: string[]
  symbols?: string[]
}

// Strategy update request
export interface UpdateStrategyRequest {
  name?: string
  description?: string
  status?: StrategyStatus
  riskLevel?: RiskLevel
  tags?: string[]
  parameters?: Record<string, any>
  code?: {
    language: 'python' | 'javascript'
    content: string
  }
  indicators?: string[]
  symbols?: string[]
}

// Strategy Performance
export interface StrategyPerformance {
  totalReturn: number
  annualizedReturn: number
  sharpeRatio: number
  sortinoRatio: number
  maxDrawdown: number
  calmarRatio: number
  winRate: number
  profitFactor: number
  totalTrades: number
  winningTrades: number
  losingTrades: number
  averageWin: number
  averageLoss: number
  largestWin: number
  largestLoss: number
  averageTradeDuration: number
  expectancy: number
  sqn: number // System Quality Number
  kellyCriterion: number
  volatility: number
  beta: number
  alpha: number
  informationRatio: number
  treynorRatio: number
  var95: number // Value at Risk 95%
  cvar95: number // Conditional Value at Risk 95%
  monthlyReturns: number[]
  yearlyReturns: number[]
  correlation?: number
  benchmarkComparison?: {
    benchmarkReturn: number
    excessReturn: number
    trackingError: number
    upCapture: number
    downCapture: number
  }
}

// Strategy Backtest
export interface StrategyBacktest {
  id: string
  strategyId: string
  name: string
  status: 'running' | 'completed' | 'failed'
  progress: number
  startTime: string
  endTime?: string
  parameters: Record<string, any>
  symbols: string[]
  startDate: string
  endDate: string
  initialCapital: number
  finalCapital: number
  performance: StrategyPerformance
  trades: BacktestTrade[]
  equityCurve: EquityPoint[]
  monthlyReturns: MonthlyReturn[]
  drawdowns: DrawdownPeriod[]
  statistics: {
    totalDays: number
    tradingDays: number
    winDays: number
    lossDays: number
    maxConsecutiveWins: number
    maxConsecutiveLosses: number
    avgDailyReturn: number
    volatility: number
    skewness: number
    kurtosis: number
  }
  charts: {
    equity: ChartData
    drawdown: ChartData
    returns: ChartData
    rollingReturns: ChartData
    monthlyHeatmap: ChartData
  }
}

// Backtest Trade
export interface BacktestTrade {
  id: string
  symbol: string
  type: 'buy' | 'sell'
  side: 'long' | 'short'
  entryDate: string
  exitDate?: string
  entryPrice: number
  exitPrice?: number
  quantity: number
  value: number
  commission: number
  pnl?: number
  pnlPercent?: number
  duration?: number
  exitReason?: 'take_profit' | 'stop_loss' | 'signal' | 'timeout' | 'manual'
  tags?: string[]
}

// Equity Point
export interface EquityPoint {
  date: string
  equity: number
  drawdown: number
  return: number
  benchmark?: number
}

// Monthly Return
export interface MonthlyReturn {
  month: string
  return: number
  benchmark?: number
  excess: number
}

// Drawdown Period
export interface DrawdownPeriod {
  startDate: string
  endDate?: string
  depth: number
  duration: number
  recoveryDuration?: number
  highPoint: number
  lowPoint: number
}

// Chart Data
export interface ChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor?: string
    borderColor?: string
    fill?: boolean
  }[]
}

// Strategy Optimization
export interface StrategyOptimization {
  id: string
  strategyId: string
  name: string
  status: 'running' | 'completed' | 'failed'
  progress: number
  startTime: string
  endTime?: string
  parameters: {
    [key: string]: {
      min: number
      max: number
      step: number
      type: 'continuous' | 'discrete'
    }
  }
  objective: 'sharpe_ratio' | 'total_return' | 'max_drawdown' | 'profit_factor'
  optimizationType: 'grid' | 'genetic' | 'bayesian' | 'random'
  iterations: number
  maxIterations: number
  results: OptimizationResult[]
  bestResult: OptimizationResult
  convergence: ConvergencePoint[]
  parameterHeatmap: ParameterHeatmap
}

// Optimization Result
export interface OptimizationResult {
  id: string
  parameters: Record<string, any>
  performance: Partial<StrategyPerformance>
  rank: number
  score: number
}

// Convergence Point
export interface ConvergencePoint {
  iteration: number
  bestScore: number
  averageScore: number
  worstScore: number
}

// Parameter Heatmap
export interface ParameterHeatmap {
  x: string
  y: string
  z: number[][]
  xValues: string[]
  yValues: string[]
}

// Strategy Execution
export interface StrategyExecution {
  id: string
  strategyId: string
  name: string
  status: 'initializing' | 'running' | 'paused' | 'stopped' | 'error'
  startTime: string
  stopTime?: string
  runtime: number
  symbols: string[]
  initialCapital: number
  currentCapital: number
  realizedPnL: number
  unrealizedPnL: number
  totalReturn: number
  openPositions: number
  totalTrades: number
  lastSignal?: StrategySignal
  lastTrade?: any
  error?: string
  metrics: {
    ordersPerSecond: number
    signalsPerMinute: number
    latency: number
    cpuUsage: number
    memoryUsage: number
  }
}

// Strategy Signal
export interface StrategySignal {
  id: string
  strategyId: string
  symbol: string
  type: 'buy' | 'sell' | 'hold'
  strength: number
  confidence: number
  price: number
  timestamp: string
  metadata: {
    indicators: Record<string, number>
    reason: string
    parameters: Record<string, any>
  }
  isExecuted: boolean
  orderId?: string
  tradeId?: string
}

// Strategy Parameters
export interface StrategyParameters {
  id: string
  strategyId: string
  parameters: ParameterDefinition[]
  version: number
  isActive: boolean
  createdAt: string
  updatedAt: string
}

// Parameter Definition
export interface ParameterDefinition {
  name: string
  type: 'number' | 'boolean' | 'string' | 'array' | 'object'
  value: any
  defaultValue: any
  min?: number
  max?: number
  step?: number
  options?: string[]
  description: string
  required: boolean
  validation?: {
    pattern?: string
    minLength?: number
    maxLength?: number
  }
}

// Strategy History
export interface StrategyHistory {
  id: string
  strategyId: string
  action: 'created' | 'updated' | 'executed' | 'stopped' | 'paused' | 'resumed' | 'deleted'
  timestamp: string
  userId: string
  details: Record<string, any>
  oldValues?: Record<string, any>
  newValues?: Record<string, any>
}

// Strategy Template
export interface StrategyTemplate {
  id: string
  name: string
  description: string
  category: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  type: StrategyType
  riskLevel: RiskLevel
  tags: string[]
  estimatedReturns: {
    min: number
    max: number
  }
  timeHorizon: 'short' | 'medium' | 'long'
  capitalRequired: 'low' | 'medium' | 'high'
  parameters: ParameterDefinition[]
  indicators: string[]
  code: {
    language: 'python' | 'javascript'
    content: string
  }
  documentation: {
    overview: string
    strategy: string
    implementation: string
    riskManagement: string
    optimization: string
  }
  backtestResults?: {
    profit: number
    sharpe: number
    maxDrawdown: number
    winRate: number
  }
  examples: {
    name: string
    description: string
    parameters: Record<string, any>
  }[]
  author: string
  version: string
  downloads: number
  rating: number
  isPublic: boolean
  createdAt: string
  updatedAt: string
}

// Strategy Update (WebSocket)
export interface StrategyUpdate {
  type: 'signal' | 'trade' | 'position' | 'performance' | 'status' | 'error'
  strategyId: string
  timestamp: string
  data: any
}