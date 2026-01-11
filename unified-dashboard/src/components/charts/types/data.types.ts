// Data type definitions for real-time chart components

// WebSocket message types for real-time data
export interface WebSocketMessage {
  type: 'data' | 'error' | 'subscription' | 'heartbeat'
  channel: string
  data?: any
  timestamp: number
  id?: string
}

// Real-time data subscription
export interface DataSubscription {
  id: string
  channel: string
  symbol: string
  indicator?: string
  timeframe?: string
  bufferSize?: number
  updateFrequency?: number // milliseconds
  isActive: boolean
  lastUpdate?: Date
}

// Market data types
export interface MarketData {
  symbol: string
  timestamp: Date
  open: number
  high: number
  low: number
  close: number
  volume: number
  vwap?: number
  bids?: Array<{ price: number; size: number }>
  asks?: Array<{ price: number; size: number }>
}

// Technical indicator data
export interface TechnicalIndicatorData {
  symbol: string
  timestamp: Date
  indicator: string
  timeframe: string
  values: Record<string, number>
  signals?: Array<{
    type: 'BUY' | 'SELL' | 'HOLD'
    strength: number
    reason?: string
  }>
}

// Aggregated data for performance
export interface AggregatedData {
  timestamp: Date
  open: number
  high: number
  low: number
  close: number
  volume: number
  indicators?: Record<string, number>
}

// Data buffer configuration
export interface DataBufferConfig {
  maxSize: number
  retentionPeriod: number // milliseconds
  aggregationLevel: 'tick' | '1m' | '5m' | '15m' | '1h' | '1d'
  compressionThreshold?: number
}

// Data validation
export interface DataValidationRule {
  field: string
  required: boolean
  type: 'number' | 'string' | 'date' | 'boolean'
  min?: number
  max?: number
  pattern?: RegExp
}

// Data transformation
export interface DataTransform {
  type: 'normalize' | 'smooth' | 'resample' | 'calculate'
  config: Record<string, any>
}

// Data source types
export type DataSourceType =
  | 'websocket'
  | 'rest-api'
  | 'file'
  | 'mock'
  | 'cache'

export interface DataSource {
  id: string
  type: DataSourceType
  url?: string
  config?: Record<string, any>
  status: 'connected' | 'disconnected' | 'connecting' | 'error'
  lastActivity?: Date
  errorCount?: number
}

// Performance metrics for data
export interface DataMetrics {
  latency: number // milliseconds
  throughput: number // messages per second
  errorRate: number // percentage
  bufferUtilization: number // percentage
  memoryUsage: number // bytes
  updateFrequency: number // milliseconds
}

// Data quality indicators
export interface DataQuality {
  completeness: number // percentage of expected data
  accuracy: number // percentage of valid data
  timeliness: number // percentage of on-time updates
  consistency: number // percentage of consistent values
  lastChecked: Date
}

// Historical data query
export interface HistoricalDataQuery {
  symbol: string
  indicator?: string
  timeframe: string
  startDate: Date
  endDate: Date
  limit?: number
  fields?: string[]
}

// Real-time data stream configuration
export interface DataStreamConfig {
  source: DataSource
  subscription: DataSubscription
  buffer: DataBufferConfig
  validation: DataValidationRule[]
  transformations: DataTransform[]
  qualityThreshold: {
    latency: number
    errorRate: number
  }
}

// Chart data state
export interface ChartDataState {
  isLive: boolean
  isPaused: boolean
  lastUpdate: Date
  updateCount: number
  errorCount: number
  buffer: {
    size: number
    maxSize: number
    utilization: number
  }
}

// Data export format
export interface DataExportFormat {
  format: 'csv' | 'json' | 'xlsx' | 'parquet'
  compression?: 'gzip' | 'zip'
  includeMetadata?: boolean
  dateRange?: {
    start: Date
    end: Date
  }
}

// Batch update data
export interface BatchUpdateData {
  updates: Array<{
    subscriptionId: string
    data: any[]
    timestamp: Date
  }>
  metadata?: {
    source: string
    version: string
  }
}