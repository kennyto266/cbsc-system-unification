// Technical Indicators Types for Dashboard Enhancement

export enum IndicatorCategory {
  TREND = 'trend',
  MOMENTUM = 'momentum',
  VOLATILITY = 'volatility',
  VOLUME = 'volume',
  OSCILLATOR = 'oscillator',
  BOLLINGER = 'bollinger',
  MOVING_AVERAGE = 'moving_average',
  SUPPORT_RESISTANCE = 'support_resistance',
  STATISTICAL = 'statistical',
  CUSTOM = 'custom'
}

export enum IndicatorType {
  // Trend Indicators
  ADX = 'ADX',
  AROON = 'AROON',
  CCI = 'CCI',
  DMI = 'DMI',
  MACD = 'MACD',
  PARABOLIC_SAR = 'PARABOLIC_SAR',
  PLUS_DI = 'PLUS_DI',
  MINUS_DI = 'MINUS_DI',

  // Momentum Indicators
  RSI = 'RSI',
  STOCHASTIC = 'STOCHASTIC',
  WILLIAMS_R = 'WILLIAMS_R',
  MOMENTUM = 'MOMENTUM',
  RATE_OF_CHANGE = 'RATE_OF_CHANGE',
  COMMODITY_CHANNEL = 'COMMODITY_CHANNEL',

  // Volatility Indicators
  AVERAGE_TRUE_RANGE = 'AVERAGE_TRUE_RANGE',
  BOLLINGER_BANDS = 'BOLLINGER_BANDS',
  STANDARD_DEVIATION = 'STANDARD_DEVIATION',
  CHAIKIN_VOLATILITY = 'CHAIKIN_VOLATILITY',

  // Volume Indicators
  VOLUME = 'VOLUME',
  ON_BALANCE_VOLUME = 'ON_BALANCE_VOLUME',
  VOLUME_WEIGHTED_AVERAGE_PRICE = 'VOLUME_WEIGHTED_AVERAGE_PRICE',
  ACCUMULATION_DISTRIBUTION = 'ACCUMULATION_DISTRIBUTION',
  MONEY_FLOW_INDEX = 'MONEY_FLOW_INDEX',

  // Moving Averages
  SMA = 'SMA',
  EMA = 'EMA',
  WMA = 'WMA',
  DEMA = 'DEMA',
  TEMA = 'TEMA',
  HULL_MA = 'HULL_MA',

  // Oscillators
  ULTIMATE_OSCILLATOR = 'ULTIMATE_OSCILLATOR',
  STOCHASTIC_RSI = 'STOCHASTIC_RSI',
  DETRENDED_PRICE = 'DETRENDED_PRICE',
  PREMIUM_DISCOUNT = 'PREMIUM_DISCOUNT',

  // Support/Resistance
  PIVOT_POINTS = 'PIVOT_POINTS',
  FIBONACCI_RETRACEMENT = 'FIBONACCI_RETRACEMENT',
  FIBONACCI_EXTENSIONS = 'FIBONACCI_EXTENSIONS',
  GANN_FAN = 'GANN_FAN',

  // Statistical
  Z_SCORE = 'Z_SCORE',
  LINEAR_REGRESSION = 'LINEAR_REGRESSION',
  STANDARD_ERROR = 'STANDARD_ERROR',
  CORRELATION = 'CORRELATION'
}

export interface IndicatorParameter {
  name: string
  type: 'number' | 'boolean' | 'string' | 'array'
  value: any
  defaultValue: any
  min?: number
  max?: number
  step?: number
  options?: string[]
  description: string
  validation?: {
    required: boolean
    pattern?: string
  }
}

export interface TechnicalIndicator {
  id: string
  name: string
  type: IndicatorType
  category: IndicatorCategory
  description: string
  formula?: string
  parameters: IndicatorParameter[]
  signals?: {
    buy: string[]
    sell: string[]
    neutral: string[]
  }
  visualSettings: {
    color: string
    lineWidth: number
    style: 'line' | 'histogram' | 'dots' | 'area'
    opacity: number
  }
  favorite: boolean
  custom: boolean
  tags: string[]
  documentation?: {
    usage: string
    examples: string[]
    bestPractices: string[]
  }
}

export interface IndicatorGroup {
  id: string
  name: string
  description: string
  indicators: string[] // Indicator IDs
  color: string
  icon?: string
}

export interface IndicatorConfiguration {
  id: string
  userId: string
  name: string
  indicators: Array<{
    indicatorId: string
    parameters: Record<string, any>
    enabled: boolean
    visualSettings: Partial<TechnicalIndicator['visualSettings']>
  }>
  layout: {
    grid: number
    charts: Array<{
      id: string
      indicators: string[]
      height: number
      position: number
    }>
  }
  timeframe: string
  symbol: string
  createdAt: string
  updatedAt: string
  isPublic: boolean
  tags: string[]
}

export interface IndicatorPerformance {
  indicatorId: string
  symbol: string
  timeframe: string
  period: {
    start: string
    end: string
  }
  signals: Array<{
    timestamp: string
    type: 'BUY' | 'SELL' | 'HOLD'
    price: number
    confidence: number
    strength: number
  }>
  statistics: {
    totalSignals: number
    successRate: number
    profitFactor: number
    maxDrawdown: number
    sharpeRatio: number
    averageHoldTime: number
  }
}

export interface IndicatorSearchFilter {
  category?: IndicatorCategory
  type?: IndicatorType
  tags?: string[]
  favorite?: boolean
  custom?: boolean
  search?: string
}

export interface IndicatorLibraryState {
  indicators: TechnicalIndicator[]
  groups: IndicatorGroup[]
  configurations: IndicatorConfiguration[]
  performance: IndicatorPerformance[]
  searchFilter: IndicatorSearchFilter
  selectedIndicator: TechnicalIndicator | null
  isLoading: boolean
  error: string | null
}

export interface IndicatorPanelState {
  activeConfiguration: string | null
  chartLayout: Array<{
    id: string
    indicators: string[]
    visible: boolean
  }>
  parameters: Record<string, Record<string, any>>
  realTimeData: boolean
  autoRefresh: boolean
  refreshInterval: number
}