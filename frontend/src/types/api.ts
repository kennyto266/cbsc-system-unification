// API related types

import { ApiResponse } from './index'

// HTTP Methods
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'

// API Request/Response types
export interface ApiRequest {
  url: string
  method: HttpMethod
  data?: any
  params?: Record<string, any>
  headers?: Record<string, string>
  timeout?: number
}

export interface ApiError {
  status?: number
  code: string
  message: string
  details?: any
  stack?: string
  timestamp: string
}

// API Client Configuration
export interface ApiClientConfig {
  baseURL: string
  timeout: number
  headers?: Record<string, string>
  retryConfig?: {
    retries: number
    retryDelay: number
    retryCondition?: (error: ApiError) => boolean
  }
  interceptors?: {
    request?: (config: ApiRequest) => ApiRequest
    response?: (response: any) => any
    error?: (error: ApiError) => ApiError
  }
}

// RTK Query types
export interface ApiState {
  api: {
    queries: Record<string, any>
    mutations: Record<string, any>
    config: ApiClientConfig
    provided: Record<string, any>
    subscriptions: Record<string, any>
  }
}

// WebSocket API types
export interface WebSocketMessage<T = any> {
  type: string
  data: T
  timestamp: string
  id?: string
  channel?: string
}

export interface WebSocketConfig {
  url: string
  protocols?: string[]
  reconnectInterval: number
  maxReconnectAttempts: number
  heartbeatInterval?: number
  heartbeatMessage?: any
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
}

// Request/Response interceptor types
export interface RequestInterceptor {
  (config: ApiRequest): ApiRequest | Promise<ApiRequest>
}

export interface ResponseInterceptor {
  (response: any): any | Promise<any>
}

export interface ErrorInterceptor {
  (error: ApiError): ApiError | Promise<ApiError>
}

// Cache configuration
export interface CacheConfig {
  enabled: boolean
  ttl: number // Time to live in seconds
  maxSize: number // Maximum number of cached responses
  strategy: 'lru' | 'fifo' | 'custom'
  customStrategy?: {
    get: (key: string) => any
    set: (key: string, value: any, ttl?: number) => void
    delete: (key: string) => void
    clear: () => void
  }
}

// Pagination types
export interface PaginationParams {
  page: number
  pageSize: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

// Search parameters for strategies
export interface SearchParams extends PaginationParams {
  status?: string
  category?: string
  search?: string
}

export interface PaginationMeta {
  currentPage: number
  totalPages: number
  totalItems: number
  itemsPerPage: number
  hasNextPage: boolean
  hasPrevPage: boolean
}

// Rate limiting
export interface RateLimitConfig {
  enabled: boolean
  maxRequests: number
  windowMs: number
  message?: string
  skipSuccessfulRequests?: boolean
  skipFailedRequests?: boolean
}

// File upload API
export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
}

export interface UploadResponse {
  id: string
  filename: string
  originalName: string
  mimeType: string
  size: number
  url: string
  thumbnailUrl?: string
  metadata?: Record<string, any>
}

// Bulk operations
export interface BulkOperation<T> {
  action: 'create' | 'update' | 'delete'
  items: T[]
  options?: {
    continueOnError?: boolean
    batchSize?: number
  }
}

export interface BulkResult<T> {
  successful: T[]
  failed: Array<{
    item: T
    error: string
  }>
  summary: {
    total: number
    successful: number
    failed: number
  }
}

// Health check
export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy' | 'degraded'
  timestamp: string
  services: {
    database: {
      status: 'up' | 'down'
      responseTime?: number
    }
    redis: {
      status: 'up' | 'down'
      responseTime?: number
    }
    external: Array<{
      name: string
      status: 'up' | 'down'
      responseTime?: number
    }>
  }
  version: string
  uptime: number
}

// Metrics and monitoring
export interface ApiMetrics {
  requestCount: number
  errorCount: number
  averageResponseTime: number
  slowRequests: number
  endpoints: Array<{
    path: string
    method: HttpMethod
    count: number
    averageResponseTime: number
    errorRate: number
  }>
}

// Cache invalidation
export interface CacheInvalidation {
  pattern: string
  tags?: string[]
  invalidateAll?: boolean
}

// Request deduplication
export interface RequestDedupeConfig {
  enabled: boolean
  ttl: number
  keyGenerator?: (request: ApiRequest) => string
}

// Basic paginated response
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// Paginated response with full support
export interface FullPaginatedResponse<T> extends PaginatedResponse<T> {
  hasMore: boolean
  hasNextPage: boolean
  hasPrevPage: boolean
  pageIndex: number
  pageSize: number
  pageCount: number
  isFirstPage: boolean
  isLastPage: boolean
}