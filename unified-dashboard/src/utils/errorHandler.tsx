// Enhanced error handling utilities

interface ErrorInfo {
  name: string
  message: string
  stack?: string
  timestamp: number
  userAgent: string
  url: string
  userId?: string
  additionalData?: Record<string, any>
}

interface ErrorHandlerOptions {
  enableConsoleLog?: boolean
  enableRemoteReporting?: boolean
  remoteEndpoint?: string
  maxErrors?: number
  samplingRate?: number
}

class ErrorHandler {
  private static instance: ErrorHandler
  private errors: ErrorInfo[] = []
  private options: ErrorHandlerOptions = {
    enableConsoleLog: true,
    enableRemoteReporting: false,
    maxErrors: 100,
    samplingRate: 1.0
  }

  constructor(options: ErrorHandlerOptions = {}) {
    this.options = { ...this.options, ...options }
    this.setupGlobalHandlers()
  }

  static getInstance(options?: ErrorHandlerOptions): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler(options)
    }
    return ErrorHandler.instance
  }

  private setupGlobalHandlers() {
    // Handle uncaught JavaScript errors
    window.addEventListener('error', (event) => {
      this.handleError({
        name: event.error?.name || 'Error',
        message: event.error?.message || event.message,
        stack: event.error?.stack,
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        additionalData: {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno
        }
      })
    })

    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.handleError({
        name: 'UnhandledPromiseRejection',
        message: event.reason?.message || String(event.reason),
        stack: event.reason?.stack,
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        additionalData: {
          reason: event.reason
        }
      })
    })

    // Handle resource loading errors
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        const target = event.target as HTMLElement
        this.handleError({
          name: 'ResourceLoadError',
          message: `Failed to load ${target.tagName}`,
          timestamp: Date.now(),
          userAgent: navigator.userAgent,
          url: window.location.href,
          additionalData: {
            element: target.tagName,
            source: target.getAttribute('src') || target.getAttribute('href')
          }
        })
      }
    }, true)
  }

  public handleError(error: ErrorInfo) {
    // Apply sampling
    if (Math.random() > (this.options.samplingRate || 1)) {
      return
    }

    // Log to console if enabled
    if (this.options.enableConsoleLog) {
      console.error('Application Error:', error)
    }

    // Store error
    this.errors.push(error)

    // Limit stored errors
    if (this.errors.length > (this.options.maxErrors || 100)) {
      this.errors.shift()
    }

    // Report to remote endpoint if enabled
    if (this.options.enableRemoteReporting && this.options.remoteEndpoint) {
      this.reportError(error)
    }
  }

  private async reportError(error: ErrorInfo) {
    try {
      await fetch(this.options.remoteEndpoint!, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(error)
      })
    } catch (e) {
      // Avoid infinite loop of error reporting
      if (this.options.enableConsoleLog) {
        console.error('Failed to report error:', e)
      }
    }
  }

  public getErrors(): ErrorInfo[] {
    return [...this.errors]
  }

  public clearErrors(): void {
    this.errors = []
  }

  public getErrorStats() {
    const errorsByType = new Map<string, number>()
    const errorsByUrl = new Map<string, number>()

    this.errors.forEach(error => {
      errorsByType.set(error.name, (errorsByType.get(error.name) || 0) + 1)
      errorsByUrl.set(error.url, (errorsByUrl.get(error.url) || 0) + 1)
    })

    return {
      total: this.errors.length,
      byType: Object.fromEntries(errorsByType),
      byUrl: Object.fromEntries(errorsByUrl)
    }
  }
}

// Custom error classes
export class ApplicationError extends Error {
  public readonly code: string
  public readonly statusCode?: number
  public readonly isRetryable: boolean
  public readonly additionalData?: Record<string, any>

  constructor(
    message: string,
    code: string = 'UNKNOWN_ERROR',
    statusCode?: number,
    isRetryable: boolean = false,
    additionalData?: Record<string, any>
  ) {
    super(message)
    this.name = 'ApplicationError'
    this.code = code
    this.statusCode = statusCode
    this.isRetryable = isRetryable
    this.additionalData = additionalData
  }
}

export class NetworkError extends ApplicationError {
  constructor(message: string, statusCode?: number, isRetryable: boolean = true) {
    super(message, 'NETWORK_ERROR', statusCode, isRetryable)
    this.name = 'NetworkError'
  }
}

export class ValidationError extends ApplicationError {
  public readonly field: string

  constructor(message: string, field: string) {
    super(message, 'VALIDATION_ERROR', 400, false, { field })
    this.name = 'ValidationError'
    this.field = field
  }
}

export class AuthenticationError extends ApplicationError {
  constructor(message: string = 'Authentication failed') {
    super(message, 'AUTHENTICATION_ERROR', 401, false)
    this.name = 'AuthenticationError'
  }
}

export class AuthorizationError extends ApplicationError {
  constructor(message: string = 'Access denied') {
    super(message, 'AUTHORIZATION_ERROR', 403, false)
    this.name = 'AuthorizationError'
  }
}

// Error boundary utilities
export const createErrorFallback = (error: Error, resetError: () => void) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
        <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
          <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-center mb-2">Something went wrong</h2>
        <p className="text-gray-600 text-center mb-6">
          {error.message || 'An unexpected error occurred. Please try again.'}
        </p>
        <div className="flex space-x-3">
          <button
            onClick={resetError}
            className="flex-1 bg-primary text-white px-4 py-2 rounded-md hover:bg-primary-600 transition-colors"
          >
            Try Again
          </button>
          <button
            onClick={() => window.location.reload()}
            className="flex-1 bg-gray-200 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-300 transition-colors"
          >
            Reload Page
          </button>
        </div>
      </div>
    </div>
  )
}

// Async error wrapper
export const withErrorHandling = async <T extends any>(
  asyncFn: () => Promise<T>,
  errorHandler?: (error: Error) => void
): Promise<T | null> => {
  try {
    return await asyncFn()
  } catch (error) {
    const errorHandlerInstance = ErrorHandler.getInstance()

    if (error instanceof Error) {
      errorHandlerInstance.handleError({
        name: error.name,
        message: error.message,
        stack: error.stack,
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        url: window.location.href
      })
    }

    if (errorHandler) {
      errorHandler(error as Error)
    }

    return null
  }
}

// Retry utility
export const retryAsync = async <T extends any>(
  asyncFn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000,
  backoff: number = 2
): Promise<T> => {
  let lastError: Error

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await asyncFn()
    } catch (error) {
      lastError = error as Error

      if (attempt === maxRetries) {
        break
      }

      // Calculate delay with exponential backoff
      const currentDelay = delay * Math.pow(backoff, attempt)
      await new Promise(resolve => setTimeout(resolve, currentDelay))
    }
  }

  throw lastError!
}

// Error type guard utilities
export const isNetworkError = (error: Error): error is NetworkError => {
  return error instanceof NetworkError ||
    (error.name === 'NetworkError' || error.name === 'TypeError') ||
    (error.message.includes('Network') || error.message.includes('fetch'))
}

export const isAuthenticationError = (error: Error): boolean => {
  return error instanceof AuthenticationError ||
    (error as any).statusCode === 401 ||
    error.message.toLowerCase().includes('unauthorized')
}

export const isRetryableError = (error: Error): boolean => {
  if (error instanceof ApplicationError) {
    return error.isRetryable
  }

  // Network errors are typically retryable
  return isNetworkError(error)
}

// Initialize error handler
export const initializeErrorHandler = (options?: ErrorHandlerOptions) => {
  return ErrorHandler.getInstance(options)
}

// Export default instance
export const errorHandler = ErrorHandler.getInstance()