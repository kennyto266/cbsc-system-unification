/**
 * Error Handling Utilities
 * Centralized error handling for API and application errors
 */

import type { ApiError } from '../types/api';

// Error severity levels
export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

// Error categories
export enum ErrorCategory {
  NETWORK = 'network',
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  VALIDATION = 'validation',
  BUSINESS_LOGIC = 'business_logic',
  SYSTEM = 'system',
  UNKNOWN = 'unknown',
}

// Error context interface
export interface ErrorContext {
  component?: string;
  action?: string;
  userId?: string;
  sessionId?: string;
  timestamp?: string;
  additionalData?: Record<string, any>;
}

// Enhanced error interface
export interface EnhancedError extends ApiError {
  severity: ErrorSeverity;
  category: ErrorCategory;
  context?: ErrorContext;
  userFriendlyMessage?: string;
  retryable?: boolean;
  reported?: boolean;
}

// Error handler function type
export type ErrorHandler = (error: EnhancedError) => void;

// Error reporting service interface
export interface ErrorReportingService {
  report(error: EnhancedError): Promise<void>;
  shouldReport(error: EnhancedError): boolean;
}

// Default error messages
export const DEFAULT_ERROR_MESSAGES: Record<string, string> = {
  NETWORK_ERROR: 'Unable to connect. Please check your internet connection.',
  TIMEOUT_ERROR: 'Request timed out. Please try again.',
  AUTHENTICATION_FAILED: 'Please log in to continue.',
  PERMISSION_DENIED: 'You don\'t have permission to perform this action.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  RESOURCE_NOT_FOUND: 'The requested resource was not found.',
  INTERNAL_SERVER_ERROR: 'Something went wrong. Please try again later.',
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again.',
};

// Error classifier
export const classifyError = (error: any): EnhancedError => {
  const enhancedError: EnhancedError = {
    status: error.status || 500,
    code: error.code || 'UNKNOWN_ERROR',
    message: error.message || DEFAULT_ERROR_MESSAGES.UNKNOWN_ERROR,
    details: error.details,
    timestamp: error.timestamp || new Date().toISOString(),
    severity: ErrorSeverity.MEDIUM,
    category: ErrorCategory.UNKNOWN,
    retryable: false,
    reported: false,
  };

  // Classify by status code
  if (error.status) {
    switch (error.status) {
      case 400:
      case 422:
        enhancedError.category = ErrorCategory.VALIDATION;
        enhancedError.severity = ErrorSeverity.LOW;
        enhancedError.userFriendlyMessage = DEFAULT_ERROR_MESSAGES.VALIDATION_ERROR;
        break;
      case 401:
        enhancedError.category = ErrorCategory.AUTHENTICATION;
        enhancedError.severity = ErrorSeverity.HIGH;
        enhancedError.userFriendlyMessage = DEFAULT_ERROR_MESSAGES.AUTHENTICATION_FAILED;
        break;
      case 403:
        enhancedError.category = ErrorCategory.AUTHORIZATION;
        enhancedError.severity = ErrorSeverity.HIGH;
        enhancedError.userFriendlyMessage = DEFAULT_ERROR_MESSAGES.PERMISSION_DENIED;
        break;
      case 404:
        enhancedError.category = ErrorCategory.BUSINESS_LOGIC;
        enhancedError.severity = ErrorSeverity.LOW;
        enhancedError.userFriendlyMessage = DEFAULT_ERROR_MESSAGES.RESOURCE_NOT_FOUND;
        break;
      case 500:
      case 502:
      case 503:
      case 504:
        enhancedError.category = ErrorCategory.SYSTEM;
        enhancedError.severity = ErrorSeverity.CRITICAL;
        enhancedError.userFriendlyMessage = DEFAULT_ERROR_MESSAGES.INTERNAL_SERVER_ERROR;
        enhancedError.retryable = true;
        break;
      default:
        if (error.status >= 400 && error.status < 500) {
          enhancedError.category = ErrorCategory.BUSINESS_LOGIC;
          enhancedError.severity = ErrorSeverity.MEDIUM;
        } else if (error.status >= 500) {
          enhancedError.category = ErrorCategory.SYSTEM;
          enhancedError.severity = ErrorSeverity.HIGH;
          enhancedError.retryable = true;
        }
    }
  }

  // Classify by error code
  if (error.code) {
    switch (error.code) {
      case 'NETWORK_ERROR':
      case 'TIMEOUT_ERROR':
        enhancedError.category = ErrorCategory.NETWORK;
        enhancedError.severity = ErrorSeverity.HIGH;
        enhancedError.retryable = true;
        enhancedError.userFriendlyMessage = DEFAULT_ERROR_MESSAGES[error.code];
        break;
      case 'VALIDATION_ERROR':
        enhancedError.category = ErrorCategory.VALIDATION;
        enhancedError.severity = ErrorSeverity.LOW;
        enhancedError.userFriendlyMessage = DEFAULT_ERROR_MESSAGES.VALIDATION_ERROR;
        break;
      case 'AUTHENTICATION_FAILED':
        enhancedError.category = ErrorCategory.AUTHENTICATION;
        enhancedError.severity = ErrorSeverity.HIGH;
        enhancedError.userFriendlyMessage = DEFAULT_ERROR_MESSAGES.AUTHENTICATION_FAILED;
        break;
    }
  }

  // Network-specific classification
  if (error.name === 'NetworkError' || !navigator.onLine) {
    enhancedError.category = ErrorCategory.NETWORK;
    enhancedError.severity = ErrorSeverity.HIGH;
    enhancedError.retryable = true;
    enhancedError.userFriendlyMessage = DEFAULT_ERROR_MESSAGES.NETWORK_ERROR;
  }

  return enhancedError;
};

// Error context builder
export const buildErrorContext = (
  component?: string,
  action?: string,
  additionalData?: Record<string, any>
): ErrorContext => {
  return {
    component,
    action,
    timestamp: new Date().toISOString(),
    additionalData,
  };
};

// Error boundary fallback component message
export const getErrorBoundaryMessage = (error: Error): string => {
  if (error.message.includes('Loading chunk')) {
    return 'A new version is available. Please refresh the page.';
  }
  return 'Something went wrong. Please refresh the page and try again.';
};

// Error reporting service implementation
export class ConsoleErrorReportingService implements ErrorReportingService {
  async report(error: EnhancedError): Promise<void> {
    console.group('🚨 Error Report');
    console.error('Error:', error);
    console.error('Context:', error.context);
    console.groupEnd();
  }

  shouldReport(error: EnhancedError): boolean {
    // Only report errors with medium severity or higher
    return (
      error.severity === ErrorSeverity.HIGH ||
      error.severity === ErrorSeverity.CRITICAL
    );
  }
}

// Production error reporting service (skeleton)
export class ProductionErrorReportingService implements ErrorReportingService {
  private apiKey: string;
  private endpoint: string;

  constructor(apiKey: string, endpoint: string) {
    this.apiKey = apiKey;
    this.endpoint = endpoint;
  }

  async report(error: EnhancedError): Promise<void> {
    try {
      await fetch(this.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey,
        },
        body: JSON.stringify({
          error: {
            code: error.code,
            message: error.message,
            severity: error.severity,
            category: error.category,
            status: error.status,
            details: error.details,
            timestamp: error.timestamp,
          },
          context: error.context,
          userAgent: navigator.userAgent,
          url: window.location.href,
        }),
      });
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  }

  shouldReport(error: EnhancedError): boolean {
    // Don't report low severity errors or already reported errors
    return (
      error.severity !== ErrorSeverity.LOW &&
      !error.reported &&
      this.isProductionEnvironment()
    );
  }

  private isProductionEnvironment(): boolean {
    return process.env.NODE_ENV === 'production';
  }
}

// Global error handler
export class GlobalErrorHandler {
  private handlers: ErrorHandler[] = [];
  private reportingService: ErrorReportingService;

  constructor(reportingService: ErrorReportingService = new ConsoleErrorReportingService()) {
    this.reportingService = reportingService;
    this.setupGlobalHandlers();
  }

  private setupGlobalHandlers(): void {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      const error = this.classifyAndEnhanceError(event.reason);
      this.handleError(error);
    });

    // Handle uncaught errors
    window.addEventListener('error', (event) => {
      const error = this.classifyAndEnhanceError(event.error);
      this.handleError(error);
    });
  }

  private classifyAndEnhanceError(error: any): EnhancedError {
    const enhancedError = classifyError(error);
    enhancedError.context = buildErrorContext(
      'GlobalErrorHandler',
      'unhandled_error'
    );
    return enhancedError;
  }

  public addHandler(handler: ErrorHandler): void {
    this.handlers.push(handler);
  }

  public removeHandler(handler: ErrorHandler): void {
    const index = this.handlers.indexOf(handler);
    if (index > -1) {
      this.handlers.splice(index, 1);
    }
  }

  public async handleError(error: EnhancedError): Promise<void> {
    // Report error if needed
    if (this.reportingService.shouldReport(error)) {
      try {
        await this.reportingService.report(error);
        error.reported = true;
      } catch (reportingError) {
        console.error('Failed to report error:', reportingError);
      }
    }

    // Call all registered handlers
    this.handlers.forEach(handler => {
      try {
        handler(error);
      } catch (handlerError) {
        console.error('Error in error handler:', handlerError);
      }
    });
  }
}

// Create global error handler instance
export const globalErrorHandler = new GlobalErrorHandler(
  process.env.NODE_ENV === 'production'
    ? new ProductionErrorReportingService(
        process.env.REACT_APP_ERROR_REPORTING_API_KEY || '',
        process.env.REACT_APP_ERROR_REPORTING_ENDPOINT || ''
      )
    : new ConsoleErrorReportingService()
);

// Error toast configuration for UI notifications
export interface ErrorToastConfig {
  title?: string;
  description?: string;
  variant?: 'default' | 'destructive';
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// Convert error to toast configuration
export const errorToToastConfig = (error: EnhancedError): ErrorToastConfig => {
  return {
    title: 'Error',
    description: error.userFriendlyMessage || error.message,
    variant: error.severity === ErrorSeverity.CRITICAL ? 'destructive' : 'default',
    duration: error.severity === ErrorSeverity.LOW ? 3000 : 5000,
    ...(error.retryable && {
      action: {
        label: 'Retry',
        onClick: () => {
          window.location.reload();
        },
      },
    }),
  };
};

// Common error handling patterns
export const handleAsyncError = async <T>(
  asyncFn: () => Promise<T>,
  errorHandler?: (error: EnhancedError) => void,
  context?: ErrorContext
): Promise<T | null> => {
  try {
    return await asyncFn();
  } catch (error) {
    const enhancedError = classifyError(error);
    if (context) {
      enhancedError.context = { ...enhancedError.context, ...context };
    }

    if (errorHandler) {
      errorHandler(enhancedError);
    } else {
      globalErrorHandler.handleError(enhancedError);
    }

    return null;
  }
};

// Error recovery strategies
export const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  maxAttempts: number = 3,
  baseDelay: number = 1000
): Promise<T> => {
  let lastError: any;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      const enhancedError = classifyError(error);

      // Don't retry if error is not retryable
      if (!enhancedError.retryable || attempt === maxAttempts) {
        throw enhancedError;
      }

      // Exponential backoff with jitter
      const delay = baseDelay * Math.pow(2, attempt - 1) + Math.random() * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError;
};