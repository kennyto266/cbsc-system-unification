import type { ApiError } from '../../types/api'

// Standard error handler
export const handleApiError = (error: ApiError): string => {
  const errorMessages: Record<string, string> = {
    'VALIDATION_ERROR': '輸入驗證失敗，請檢查您的輸入',
    'AUTHENTICATION_FAILED': '認證失敗，請重新登錄',
    'PERMISSION_DENIED': '權限不足，無法執行此操作',
    'RESOURCE_NOT_FOUND': '請求的資源不存在',
    'STRATEGY_NOT_FOUND': '策略不存在',
    'DUPLICATE_STRATEGY': '策略名稱已存在',
    'STRATEGY_EXECUTION_FAILED': '策略執行失敗',
    'RATE_LIMIT_EXCEEDED': '請求過於頻繁，請稍後再試',
    'INTERNAL_SERVER_ERROR': '服務器內部錯誤，請稍後再試',
    'NETWORK_ERROR': '網絡連接錯誤，請檢查您的網絡',
    'TIMEOUT_ERROR': '請求超時，請稍後再試',
    'CONNECTION_REFUSED': '無法連接到服務器，請稍後再試',
    'SSL_ERROR': 'SSL連接錯誤，請檢查網絡設置',
    'JSON_PARSE_ERROR': '數據格式錯誤，請聯繫管理員',
  }

  return errorMessages[error.code] || error.message || '未知錯誤'
}

// Extract error details for debugging
export const getErrorDetails = (error: ApiError): any => {
  return {
    status: error.status,
    code: error.code,
    message: error.message,
    details: error.details,
    timestamp: error.timestamp,
    stack: error.stack,
  }
}

// Determine if error is recoverable
export const isRecoverableError = (error: ApiError): boolean => {
  // Network errors are usually recoverable
  if (error.code === 'NETWORK_ERROR' || error.code === 'TIMEOUT_ERROR') {
    return true
  }

  // Server errors (5xx) might be recoverable
  if (error.status >= 500 && error.status < 600) {
    return true
  }

  // Rate limit errors are recoverable after waiting
  if (error.code === 'RATE_LIMIT_EXCEEDED') {
    return true
  }

  // 4xx errors are usually not recoverable without user action
  return false
}

// Get user-friendly error action suggestion
export const getErrorAction = (error: ApiError): string => {
  const actionMap: Record<string, string> = {
    'AUTHENTICATION_FAILED': '請重新登錄',
    'PERMISSION_DENIED': '請聯繫管理員獲取權限',
    'VALIDATION_ERROR': '請檢查輸入數據並重試',
    'RATE_LIMIT_EXCEEDED': '請稍後再試',
    'NETWORK_ERROR': '請檢查網絡連接',
    'TIMEOUT_ERROR': '請稍後再試',
    'STRATEGY_EXECUTION_FAILED': '請檢查策略配置',
    'CONNECTION_REFUSED': '請檢查服務器狀態',
  }

  return actionMap[error.code] || '請重試操作'
}

// Format error for display in UI
export const formatErrorForDisplay = (error: ApiError): {
  title: string
  message: string
  action: string
  canRetry: boolean
  severity: 'error' | 'warning' | 'info'
} => {
  const isRecoverable = isRecoverableError(error)

  return {
    title: error.status ? `錯誤 ${error.status}` : '操作失敗',
    message: handleApiError(error),
    action: getErrorAction(error),
    canRetry: isRecoverable,
    severity: isRecoverable ? 'warning' : 'error',
  }
}

// Error logging utility
export const logError = (error: ApiError, context?: string) => {
  const errorInfo = {
    ...getErrorDetails(error),
    context,
    userAgent: navigator.userAgent,
    url: window.location.href,
    timestamp: new Date().toISOString(),
  }

  // In production, send to error tracking service
  if (process.env.NODE_ENV === 'production') {
    // Send to Sentry, LogRocket, etc.
    console.error('API Error:', errorInfo)
  } else {
    // In development, log to console with more details
    console.group(`API Error: ${error.code}`)
    console.error('Error details:', errorInfo)
    console.groupEnd()
  }

  // Store in localStorage for debugging
  try {
    const errors = JSON.parse(localStorage.getItem('api_errors') || '[]')
    errors.push(errorInfo)
    // Keep only last 50 errors
    if (errors.length > 50) {
      errors.splice(0, errors.length - 50)
    }
    localStorage.setItem('api_errors', JSON.stringify(errors))
  } catch (e) {
    console.warn('Failed to store error in localStorage:', e)
  }
}

// Get stored errors for debugging
export const getStoredErrors = (): any[] => {
  try {
    return JSON.parse(localStorage.getItem('api_errors') || '[]')
  } catch (e) {
    console.warn('Failed to retrieve stored errors:', e)
    return []
  }
}

// Clear stored errors
export const clearStoredErrors = (): void => {
  try {
    localStorage.removeItem('api_errors')
  } catch (e) {
    console.warn('Failed to clear stored errors:', e)
  }
}

// Error boundary helper
export const createErrorBoundary = (fallbackComponent?: React.ComponentType) => {
  return {
    getDerivedStateFromError(error: Error) {
      return { hasError: true, error }
    },
    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
      logError({
        status: 500,
        code: 'REACT_ERROR',
        message: error.message,
        details: errorInfo,
        timestamp: new Date().toISOString(),
      })
    },
    FallbackComponent: fallbackComponent,
  }
}

// Retry with exponential backoff
export const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  maxAttempts: number = 3,
  baseDelay: number = 1000
): Promise<T> => {
  let lastError: Error

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn()
    } catch (error: any) {
      lastError = error

      if (attempt === maxAttempts) {
        throw lastError
      }

      // Calculate delay with exponential backoff
      const delay = baseDelay * Math.pow(2, attempt - 1)
      console.warn(`Attempt ${attempt} failed, retrying in ${delay}ms:`, error)

      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }

  throw lastError
}

// Circuit breaker pattern
export class CircuitBreaker {
  private failures = 0
  private lastFailureTime = 0
  private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED'

  constructor(
    private threshold: number = 5,
    private timeout: number = 60000, // 1 minute
    private monitor: any
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime > this.timeout) {
        this.state = 'HALF_OPEN'
      } else {
        throw new Error('Circuit breaker is OPEN')
      }
    }

    try {
      const result = await fn()
      this.onSuccess()
      return result
    } catch (error) {
      this.onFailure()
      throw error
    }
  }

  private onSuccess() {
    this.failures = 0
    this.state = 'CLOSED'
    this.monitor?.onSuccess?.()
  }

  private onFailure() {
    this.failures++
    this.lastFailureTime = Date.now()

    if (this.failures >= this.threshold) {
      this.state = 'OPEN'
      this.monitor?.onOpen?.()
    }
  }

  getState() {
    return this.state
  }

  reset() {
    this.failures = 0
    this.state = 'CLOSED'
    this.lastFailureTime = 0
  }
}