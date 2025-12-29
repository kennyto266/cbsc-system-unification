/**
 * Market data related types
 */

// Market Data
export interface MarketData {
  symbol: string
  name: string
  type: MarketType
  exchange: string
  currency: string
  price: number
  change: number
  changePercent: number
  volume: number
  turnover: number
  high: number
  low: number
  open: number
  close: number
  prevClose: number
  marketCap: number
  pe?: number
  pb?: number
  timestamp: Date | string
}

// Market Type
export type MarketType = 'stock' | 'etf' | 'bond' | 'futures' | 'options' | 'forex' | 'crypto'

// OHLCV Data
export interface OHLCV {
  timestamp: Date | string
  open: number
  high: number
  low: number
  close: number
  volume: number
  turnover?: number
}

// Timeframe
export type Timeframe =
  | '1m'
  | '5m'
  | '15m'
  | '30m'
  | '1h'
  | '4h'
  | '1d'
  | '1w'
  | '1M'

// Market Quote
export interface MarketQuote {
  symbol: string
  bid: number
  ask: number
  bidSize: number
  askSize: number
  last: number
  timestamp: Date | string
}

// Order Book
export interface OrderBook {
  symbol: string
  bids: [price: number, size: number][]
  asks: [price: number, size: number][]
  timestamp: Date | string
}

// Market Depth
export interface MarketDepth {
  price: number
  buyVolume: number
  sellVolume: number
  cumulativeVolume: number
}

// Technical Indicator
export interface TechnicalIndicator {
  name: string
  value: number
  signal?: 'buy' | 'sell' | 'neutral'
  timestamp: Date | string
}

// Market News
export interface MarketNews {
  id: string
  title: string
  summary: string
  content?: string
  source: string
  author?: string
  symbols: string[]
  categories: string[]
  sentiment?: 'positive' | 'negative' | 'neutral'
  importance: 'low' | 'medium' | 'high'
  publishedAt: Date | string
  url?: string
  imageUrl?: string
}

// Market Event
export interface MarketEvent {
  id: string
  title: string
  description: string
  type: EventType
  impact: EventImpact
  country: string
  currency: string
  actual?: number
  forecast?: number
  previous?: number
  timestamp: Date | string
}

// Event Type
export type EventType =
  | 'gdp'
  | 'cpi'
  | 'ppi'
  | 'employment'
  | 'interest_rate'
  | 'trade_balance'
  | 'retail_sales'
  | 'pmi'
  | 'custom'

// Event Impact
export type EventImpact = 'low' | 'medium' | 'high'

// Market Calendar
export interface MarketCalendar {
  date: Date | string
  market: string
  status: 'open' | 'closed' | 'half_day'
  notes?: string
}

// Corporate Action
export interface CorporateAction {
  id: string
  symbol: string
  type: CorporateActionType
  description: string
  exDate: Date | string
  recordDate: Date | string
  paymentDate?: Date | string
  details?: Record<string, any>
}

// Corporate Action Type
export type CorporateActionType =
  | 'dividend'
  | 'split'
  | 'bonus'
  | 'rights'
  | 'merger'
  | 'acquisition'
  | 'spinoff'

// Market Index
export interface MarketIndex {
  symbol: string
  name: string
  value: number
  change: number
  changePercent: number
  constituents: string[]
  weightings?: Record<string, number>
  timestamp: Date | string
}

// Market Sector
export interface MarketSector {
  name: string
  performance: number
  marketCap: number
  pe?: number
  pb?: number
  dividendYield?: number
}

// Economic Indicator
export interface EconomicIndicator {
  name: string
  value: number
  change: number
  changePercent: number
  unit: string
  country: string
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'
  timestamp: Date | string
}

// Commodity
export interface Commodity {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  unit: string
  exchange: string
  timestamp: Date | string
}

// Currency Pair
export interface CurrencyPair {
  symbol: string
  baseCurrency: string
  quoteCurrency: string
  price: number
  change: number
  changePercent: number
  pip: number
  timestamp: Date | string
}

// Market Sentiment
export interface MarketSentiment {
  fearGreedIndex: number
  vix?: number
  putCallRatio?: number
  advanceDeclineRatio?: number
  newHighs: number
  newLows: number
  timestamp: Date | string
}

// Market Scanner
export interface MarketScanner {
  id: string
  name: string
  criteria: ScannerCriteria[]
  results: string[]
  createdAt: Date | string
  updatedAt: Date | string
}

// Scanner Criteria
export interface ScannerCriteria {
  field: string
  operator: ScannerOperator
  value: any
  valueType: 'number' | 'string' | 'boolean'
}

// Scanner Operator
export type ScannerOperator =
  | 'eq'
  | 'ne'
  | 'gt'
  | 'gte'
  | 'lt'
  | 'lte'
  | 'contains'
  | 'startsWith'
  | 'endsWith'
  | 'in'
  | 'notIn'

// Market Data State
export interface MarketDataState {
  quotes: Record<string, MarketData>
  watchlist: string[]
  isLoading: boolean
}