/**
 * API related types
 */

// HTTP Methods
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

// Request Config
export interface RequestConfig {
  method?: HttpMethod
  url?: string
  data?: any
  params?: Record<string, any>
  headers?: Record<string, string>
  timeout?: number
  retries?: number
}

// API Endpoint
export interface ApiEndpoint {
  path: string
  method: HttpMethod
  description?: string
  parameters?: {
    path?: Record<string, string>
    query?: Record<string, string>
    body?: Record<string, string>
  }
  response?: any
}

// WebSocket Message
export interface WebSocketMessage {
  type: string
  data: any
  timestamp?: number
  id?: string
}

// WebSocket Event
export interface WebSocketEvent {
  event: string
  handler: (data: any) => void
}

// Rate Limit Info
export interface RateLimitInfo {
  limit: number
  remaining: number
  reset: number
  retryAfter?: number
}

// API Error
export interface ApiError {
  code: string
  message: string
  details?: any
  timestamp: string
  requestId?: string
  path?: string
  status: number
}

// Cache Options
export interface CacheOptions {
  ttl?: number // Time to live in milliseconds
  key?: string
  invalidateOn?: string[]
}

// Request Options
export interface RequestOptions extends RequestConfig {
  cache?: CacheOptions
  background?: boolean
  silent?: boolean
  onSuccess?: (data: any) => void
  onError?: (error: ApiError) => void
  onFinally?: () => void
}

// Response Metadata
export interface ResponseMeta {
  requestId: string
  timestamp: string
  duration: number
  version: string
  rateLimit?: RateLimitInfo
}