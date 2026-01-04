/**
 * Market Data Types
 * Types related to market data and trading information
 */

// Market Symbol
export interface MarketSymbol {
  symbol: string
  name: string
  type: 'stock' | 'crypto' | 'forex' | 'commodity' | 'index' | 'etf'
  exchange: string
  currency: string
  status: 'active' | 'inactive' | 'delisted'
  description?: string
  sector?: string
  industry?: string
  marketCap?: number
  volume24h?: number
  change24h?: number
  changePercent24h?: number
  high24h?: number
  low24h?: number
  logo?: string
  website?: string
  listingDate?: string
}

// Market Price
export interface MarketPrice {
  symbol: string
  price: number
  change: number
  changePercent: number
  high: number
  low: number
  volume: number
  quoteVolume: number
  open: number
  close: number
  timestamp: number
}

// Kline/Candlestick Data
export interface KlineData {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
  quoteVolume: number
  trades?: number
  takerBuyVolume?: number
  takerBuyQuoteVolume?: number
}

// Tick Data
export interface TickData {
  timestamp: number
  price: number
  volume: number
  side: 'buy' | 'sell'
  id: number
}

// Order Book
export interface OrderBook {
  symbol: string
  timestamp: number
  lastUpdateId: number
  bids: [number, number][]  // [price, quantity]
  asks: [number, number][]  // [price, quantity]
}

// Market Trade
export interface MarketTrade {
  id: string
  symbol: string
  price: number
  quantity: number
  side: 'buy' | 'sell'
  timestamp: number
  isBuyerMaker: boolean
}

// Market Statistics
export interface MarketStats {
  totalMarketCap: number
  marketCapChange24h: number
  volume24h: number
  volumeChange24h: number
  btcDominance: number
  ethDominance: number
  activeCryptocurrencies: number
  activePairs: number
  activeExchanges: number
  fearGreedIndex?: {
    value: number
    classification: string
    timestamp: number
  }
}

// Market Overview
export interface MarketOverview {
  gainers: ScreenerResult[]
  losers: ScreenerResult[]
  mostActive: ScreenerResult[]
  topCryptos: ScreenerResult[]
  indices: {
    name: string
    value: number
    change: number
    changePercent: number
  }[]
  sectors: {
    name: string
    change: number
    changePercent: number
  }[]
}

// Screener Result
export interface ScreenerResult {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
  marketCap?: number
  pe?: number
  eps?: number
  beta?: number
  week52High?: number
  week52Low?: number
  sector?: string
  industry?: string
}

// Market Event
export interface MarketEvent {
  id: string
  type: 'earnings' | 'dividend' | 'split' | 'ipo' | 'economic' | 'alert'
  title: string
  description: string
  symbol?: string
  datetime: string
  impact: 'low' | 'medium' | 'high'
  priority: number
  isRead: boolean
  metadata?: Record<string, any>
}

// Calendar Event
export interface CalendarEvent {
  id: string
  title: string
  description: string
  country: string
  date: string
  time?: string
  impact: 'low' | 'medium' | 'high'
  forecast?: number
  previous?: number
  actual?: number
  currency: string
  category: string
}

// News Item
export interface NewsItem {
  id: string
  title: string
  summary: string
  content: string
  source: string
  author?: string
  url: string
  imageUrl?: string
  publishedAt: string
  symbols: string[]
  categories: string[]
  sentiment?: 'positive' | 'negative' | 'neutral'
  relevanceScore?: number
}

// Market Sentiment Data
export interface MarketSentiment {
  symbol?: string
  timestamp: number
  overall: 'bullish' | 'bearish' | 'neutral'
  score: number  // -100 to 100
  factors: {
    technical: number
    fundamental: number
    news: number
    social: number
  }
  indicators: {
    rsi?: number
    macd?: {
      value: number
      signal: number
      histogram: number
    }
    movingAverages: {
      short: 'buy' | 'sell' | 'neutral'
      medium: 'buy' | 'sell' | 'neutral'
      long: 'buy' | 'sell' | 'neutral'
    }
  }
}

// Market Depth
export interface MarketDepth {
  symbol: string
  timestamp: number
  bids: {
    price: number
    quantity: number
    total: number
  }[]
  asks: {
    price: number
    quantity: number
    total: number
  }[]
}

// Funding Rate
export interface FundingRate {
  symbol: string
  rate: number
  nextFundingTime: number
  timestamp: number
}

// Open Interest
export interface OpenInterest {
  symbol: string
  openInterest: number
  change: number
  changePercent: number
  timestamp: number
}

// Long/Short Ratio
export interface LongShortRatio {
  symbol: string
  longShortRatio: number
  longAccount: number
  shortAccount: number
  timestamp: number
}

// Market Data Subscription
export interface MarketDataSubscription {
  id: string
  symbols: string[]
  channels: ('ticker' | 'depth' | 'kline' | 'trade' | 'ticker')[]
  interval?: string
  isActive: boolean
  createdAt: string
}

// Trade Data (WebSocket)
export interface TradeData {
  symbol: string
  price: number
  quantity: number
  side: 'buy' | 'sell'
  timestamp: number
  tradeId?: string
}

// Order Book Update (WebSocket)
export interface OrderBookUpdate {
  symbol: string
  bids: [number, number][]
  asks: [number, number][]
  timestamp: number
  lastUpdateId: number
  isSnapshot?: boolean
}

// Strategy Update (WebSocket)
export interface StrategyUpdate {
  strategyId: string
  status: 'active' | 'paused' | 'stopped' | 'error'
  signal?: 'buy' | 'sell' | 'hold'
  price?: number
  quantity?: number
  timestamp: number
  message?: string
  metrics?: {
    totalReturn?: number
    winRate?: number
    profitFactor?: number
  }
}