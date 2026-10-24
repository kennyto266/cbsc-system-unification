/**
 * Technical Indicators Types
 * Types related to technical indicators and calculations
 */

// Indicator Types
export enum IndicatorType {
  TREND = 'trend',
  MOMENTUM = 'momentum',
  VOLATILITY = 'volatility',
  VOLUME = 'volume',
  OSCILLATOR = 'oscillator',
  BOLLINGER = 'bollinger',
  CUSTOM = 'custom',
}

export enum IndicatorCategory {
  OVERLAY = 'overlay',
  OSCILLATOR = 'oscillator',
  VOLUME = 'volume',
  VOLATILITY = 'volatility',
  MOMENTUM = 'momentum',
  STATISTICAL = 'statistical',
  CUSTOM = 'custom',
}

// Base Indicator
export interface Indicator {
  id: string
  name: string
  displayName: string
  type: IndicatorType
  category: IndicatorCategory
  description: string
  parameters: IndicatorParameter[]
  inputs: IndicatorInput[]
  outputs: IndicatorOutput[]
  formula?: string
  developer?: string
  source: string
  documentation: {
    overview: string
    interpretation: string
    examples: string[]
  }
  tags: string[]
  isPopular: boolean
  isCBSCSpecific: boolean
  createdAt: string
  updatedAt: string
}

// Indicator Parameter
export interface IndicatorParameter {
  name: string
  type: 'number' | 'integer' | 'boolean' | 'string' | 'array'
  defaultValue: any
  min?: number
  max?: number
  step?: number
  options?: string[]
  required: boolean
  description: string
}

// Indicator Input
export interface IndicatorInput {
  name: string
  type: 'price' | 'volume' | 'indicator' | 'array'
  required: boolean
  description: string
  allowedValues?: string[]
}

// Indicator Output
export interface IndicatorOutput {
  name: string
  type: 'line' | 'histogram' | 'area' | 'dots' | 'shapes'
  description: string
}

// Indicator Category
export interface IndicatorCategory {
  id: string
  name: string
  displayName: string
  description: string
  icon?: string
  indicatorCount: number
}

// Indicator Preset
export interface IndicatorPreset {
  id: string
  name: string
  description: string
  category: string
  indicators: Array<{
    name: string
    parameters: Record<string, any>
    color?: string
    visible?: boolean
  }>
  strategy?: {
    name: string
    description: string
    rules: Array<{
      condition: string
      action: string
    }>
  }
  thumbnail?: string
  isPublic: boolean
  downloads: number
  rating: number
  author: string
  createdAt: string
  updatedAt: string
}

// Indicator Calculation Request
export interface IndicatorCalculation {
  symbol: string
  interval: string
  indicators: Array<{
    name: string
    parameters: Record<string, any>
  }>
  startDate?: string
  endDate?: string
  limit?: number
}

// Indicator Formula
export interface IndicatorFormula {
  indicatorId: string
  language: 'pine' | 'python' | 'javascript'
  code: string
  version: string
  documentation: {
    parameters: Record<string, string>
    returns: string
    examples: string[]
  }
  isValid: boolean
  validationErrors?: string[]
}

// Indicator Search Result
export interface IndicatorSearchResult {
  id: string
  name: string
  displayName: string
  category: string
  description: string
  relevanceScore: number
  matchType: 'exact' | 'partial' | 'fuzzy'
}

// CBSC Specific Indicator Types

// Warrant Indicator
export interface WarrantIndicator {
  id: string
  code: string
  type: 'call' | 'put' | 'bull' | 'bear'
  underlying: string
  strike: number
  expiry: string
  delta: number
  gamma: number
  theta: number
  vega: number
  rho: number
  impliedVolatility: number
  timeValue: number
  intrinsicValue: number
  moneyness: number
  leverage: number
}

// CBSC Market Sentiment
export interface CBSCSentiment {
  symbol: string
  timestamp: string
  sentiment: 'bullish' | 'bearish' | 'neutral'
  score: number  // -100 to 100
  factors: {
    putCallRatio: number
    impliedVolatilityIndex: number
    volumeRatio: number
    openInterestChange: number
    priceMomentum: number
  }
  warrants: {
    total: number
    calls: number
    puts: number
    bullish: number
    bearish: number
  }
}

// Indicator Value
export interface IndicatorValue {
  timestamp: string
  value: number | null
  metadata?: Record<string, any>
}

// Indicator Series
export interface IndicatorSeries {
  indicator: string
  symbol: string
  interval: string
  values: IndicatorValue[]
}

// Combined Indicators Result
export interface CombinedIndicatorsResult {
  symbol: string
  interval: string
  indicators: Record<string, IndicatorSeries>
  signals?: TradingSignal[]
}

// Trading Signal
export interface TradingSignal {
  timestamp: string
  signal: 'buy' | 'sell' | 'hold'
  strength: number  // 0-100
  indicators: Array<{
    name: string
    value: number
    signal: 'bullish' | 'bearish' | 'neutral'
  }>
  reason: string
  confidence: number  // 0-100
}

// Indicator Alert
export interface IndicatorAlert {
  id: string
  userId: string
  indicator: string
  symbol: string
  condition: IndicatorCondition
  isActive: boolean
  triggeredCount: number
  lastTriggered?: string
  createdAt: string
  updatedAt: string
}

// Indicator Condition
export interface IndicatorCondition {
  operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte' | 'cross_above' | 'cross_below'
  value: number
  timeframe?: string
}

// Indicator Performance
export interface IndicatorPerformance {
  indicator: string
  parameters: Record<string, any>
  backtestPeriod: {
    startDate: string
    endDate: string
  }
  performance: {
    totalReturn: number
    annualizedReturn: number
    sharpeRatio: number
    maxDrawdown: number
    winRate: number
    profitFactor: number
    totalTrades: number
  }
  signals: Array<{
    date: string
    signal: 'buy' | 'sell'
    price: number
    profit?: number
  }>
}

// Indicator Optimization Result
export interface IndicatorOptimization {
  indicator: string
  parameters: {
    [key: string]: {
      min: number
      max: number
      step: number
      optimal: number
    }
  }
  objective: string
  bestParameters: Record<string, number>
  bestPerformance: IndicatorPerformance['performance']
  allResults: Array<{
    parameters: Record<string, number>
    performance: IndicatorPerformance['performance']
  }>
}

// Custom Indicator
export interface CustomIndicator {
  id: string
  name: string
  description: string
  code: {
    language: 'python' | 'javascript' | 'pine'
    content: string
  }
  inputs: IndicatorInput[]
  parameters: IndicatorParameter[]
  outputs: IndicatorOutput[]
  isValid: boolean
  validationErrors?: string[]
  isPublic: boolean
  author: string
  version: string
  createdAt: string
  updatedAt: string
}

// Indicator Backtest Request
export interface IndicatorBacktestRequest {
  symbol: string
  interval: string
  startDate: string
  endDate: string
  indicators: Array<{
    name: string
    parameters: Record<string, any>
  }>
  strategy: {
    entry: Array<{
      indicator: string
      condition: string
      value?: number
    }>
    exit: Array<{
      indicator: string
      condition: string
      value?: number
    }>
  }
  initialCapital: number
  commission: number
  slippage: number
}

// Indicator Backtest Result
export interface IndicatorBacktestResult {
  summary: IndicatorPerformance['performance']
  trades: Array<{
    entryDate: string
    exitDate: string
    entryPrice: number
    exitPrice: number
    quantity: number
    profit: number
    profitPercent: number
    indicators: Record<string, number>
  }>
  equity: Array<{
    date: string
    equity: number
    returns: number
    drawdown: number
  }>
  monthlyReturns: Array<{
    month: string
    returns: number
  }>
}