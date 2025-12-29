/**
 * Common API Types
 * Shared types used across all API services
 */

// Generic API Response wrapper
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message: string
  timestamp: string
  requestId?: string
}

// Paginated Response
export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
    hasNext: boolean
    hasPrev: boolean
  }
}

// API Error response
export interface ApiError {
  success: false
  error: {
    code: string
    message: string
    details?: any
    stack?: string
  }
  timestamp: string
  requestId?: string
}

// Base Request Parameters
export interface BaseParams {
  page?: number
  limit?: number
  sort?: string
  order?: 'asc' | 'desc'
  search?: string
  filters?: Record<string, any>
}

// File Upload Response
export interface UploadResponse {
  url: string
  filename: string
  size: number
  mimeType: string
}

// Export Data Request
export interface ExportRequest {
  format: 'csv' | 'xlsx' | 'json' | 'pdf'
  fields?: string[]
  filters?: Record<string, any>
  dateRange?: {
    start: string
    end: string
  }
}

// Export Response
export interface ExportResponse {
  downloadUrl: string
  filename: string
  expiresAt: string
  size: number
}

// Health Check Response
export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy' | 'degraded'
  services: {
    [serviceName: string]: {
      status: 'up' | 'down'
      latency?: number
      lastCheck: string
    }
  }
  version: string
  uptime: number
}

// Cache Entry
export interface CacheEntry<T = any> {
  key: string
  data: T
  expiresAt: number
  cachedAt: number
}

// Request Metadata
export interface RequestMetadata {
  startTime?: Date
  retryCount?: number
  cached?: boolean
  requestId?: string
}

// WebSocket Message
export interface WebSocketMessage<T = any> {
  type: string
  channel: string
  data: T
  timestamp: number
  id: string
}

// Notification Types
export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: string
  read: boolean
  metadata?: any
}

// Activity Log Entry
export interface ActivityLog {
  id: string
  userId: string
  action: string
  resource: string
  resourceId?: string
  details?: any
  ipAddress: string
  userAgent: string
  timestamp: string
}

// System Metrics
export interface SystemMetrics {
  cpu: {
    usage: number
    cores: number
  }
  memory: {
    used: number
    total: number
    usage: number
  }
  disk: {
    used: number
    total: number
    usage: number
  }
  network: {
    inbound: number
    outbound: number
  }
  uptime: number
  activeConnections: number
}