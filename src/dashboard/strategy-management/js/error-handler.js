/**
 * 个人策略管理Dashboard - 错误处理模块
 * Personal Strategy Management Dashboard - Error Handler
 */

import { ERROR_MESSAGES, NOTIFICATION_TYPES } from './constants.js';

/**
 * 错误类型枚举
 */
export const ErrorTypes = {
    NETWORK: 'network',
    API: 'api',
    VALIDATION: 'validation',
    PERMISSION: 'permission',
    NOT_FOUND: 'not_found',
    TIMEOUT: 'timeout',
    UNKNOWN: 'unknown'
};

/**
 * 错误严重级别
 */
export const ErrorSeverity = {
    LOW: 'low',
    MEDIUM: 'medium',
    HIGH: 'high',
    CRITICAL: 'critical'
};

/**
 * 自定义错误类
 */
export class AppError extends Error {
    constructor(message, type = ErrorTypes.UNKNOWN, severity = ErrorSeverity.MEDIUM, details = null) {
        super(message);
        this.name = 'AppError';
        this.type = type;
        this.severity = severity;
        this.details = details;
        this.timestamp = Date.now();
        this.stack = (new Error()).stack;
    }
}

/**
 * 错误处理器类
 */
class ErrorHandler {
    constructor() {
        this.errorLog = [];
        this.maxLogSize = 1000;
        this.errorCallbacks = new Map();
        this.globalErrorHandlingEnabled = true;
    }

    /**
     * 处理错误
     * @param {Error|string} error - 错误对象或消息
     * @param {string} context - 错误上下文
     * @param {Object} options - 选项
     * @returns {AppError} 处理后的错误对象
     */
    handle(error, context = '', options = {}) {
        const {
            type = null,
            severity = null,
            details = null,
            showNotification = true,
            logError = true
        } = options;

        let appError;

        if (error instanceof AppError) {
            appError = error;
        } else if (error instanceof Error) {
            appError = this.convertToAppError(error, type, severity, details);
        } else if (typeof error === 'string') {
            appError = new AppError(error, type || ErrorTypes.UNKNOWN, severity || ErrorSeverity.MEDIUM, details);
        } else {
            appError = new AppError(String(error), type || ErrorTypes.UNKNOWN, severity || ErrorSeverity.MEDIUM, details);
        }

        // Add context
        appError.context = context;

        // Log error
        if (logError) {
            this.logError(appError);
        }

        // Show notification
        if (showNotification) {
            this.showErrorNotification(appError);
        }

        // Call callbacks
        this.callErrorCallbacks(appError);

        return appError;
    }

    /**
     * 转换普通错误为AppError
     * @param {Error} error - 普通错误
     * @param {string} type - 错误类型
     * @param {string} severity - 错误严重级别
     * @param {Object} details - 错误详情
     * @returns {AppError} 应用错误
     */
    convertToAppError(error, type, severity, details) {
        let errorType = type;
        let errorMessage = error.message;

        // Determine error type based on error properties
        if (!type) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorType = ErrorTypes.NETWORK;
            } else if (error.name === 'TimeoutError' || error.message.includes('timeout')) {
                errorType = ErrorTypes.TIMEOUT;
            } else if (error.status) {
                if (error.status === 404) {
                    errorType = ErrorTypes.NOT_FOUND;
                } else if (error.status === 401 || error.status === 403) {
                    errorType = ErrorTypes.PERMISSION;
                } else if (error.status >= 400 && error.status < 500) {
                    errorType = ErrorTypes.VALIDATION;
                } else if (error.status >= 500) {
                    errorType = ErrorTypes.API;
                }
            }
        }

        // Determine severity
        let errorSeverity = severity;
        if (!severity) {
            if (errorType === ErrorTypes.NETWORK || errorType === ErrorTypes.API) {
                errorSeverity = ErrorSeverity.HIGH;
            } else if (errorType === ErrorTypes.PERMISSION || errorType === ErrorTypes.NOT_FOUND) {
                errorSeverity = ErrorSeverity.MEDIUM;
            } else {
                errorSeverity = ErrorSeverity.LOW;
            }
        }

        // Use friendly error message
        if (ERROR_MESSAGES[errorType.toUpperCase()]) {
            errorMessage = ERROR_MESSAGES[errorType.toUpperCase()];
        }

        return new AppError(errorMessage, errorType, errorSeverity, details || error);
    }

    /**
     * 记录错误
     * @param {AppError} error - 错误对象
     */
    logError(error) {
        const logEntry = {
            id: this.generateErrorId(),
            timestamp: error.timestamp,
            type: error.type,
            severity: error.severity,
            message: error.message,
            context: error.context,
            details: error.details,
            stack: error.stack
        };

        this.errorLog.unshift(logEntry);

        // Keep log size limited
        if (this.errorLog.length > this.maxLogSize) {
            this.errorLog = this.errorLog.slice(0, this.maxLogSize);
        }

        // Console logging based on severity
        const logMethod = this.getConsoleMethod(error.severity);
        logMethod.call(console, `[${error.severity.toUpperCase()}] ${error.message}`, {
            type: error.type,
            context: error.context,
            details: error.details
        });
    }

    /**
     * 获取控制台方法
     * @param {string} severity - 错误严重级别
     * @returns {Function} 控制台方法
     */
    getConsoleMethod(severity) {
        switch (severity) {
            case ErrorSeverity.LOW:
                return console.info;
            case ErrorSeverity.MEDIUM:
                return console.warn;
            case ErrorSeverity.HIGH:
            case ErrorSeverity.CRITICAL:
                return console.error;
            default:
                return console.log;
        }
    }

    /**
     * 显示错误通知
     * @param {AppError} error - 错误对象
     */
    showErrorNotification(error) {
        if (typeof window !== 'undefined' && window.eventBus) {
            // Use event bus if available
            window.eventBus.emit('notification', {
                type: this.getNotificationType(error.severity),
                title: '错误',
                message: error.message,
                duration: this.getNotificationDuration(error.severity)
            });
        } else {
            // Fallback: Create notification element
            this.createNotificationElement(error);
        }
    }

    /**
     * 获取通知类型
     * @param {string} severity - 错误严重级别
     * @returns {string} 通知类型
     */
    getNotificationType(severity) {
        switch (severity) {
            case ErrorSeverity.LOW:
                return NOTIFICATION_TYPES.INFO.value;
            case ErrorSeverity.MEDIUM:
                return NOTIFICATION_TYPES.WARNING.value;
            case ErrorSeverity.HIGH:
            case ErrorSeverity.CRITICAL:
                return NOTIFICATION_TYPES.ERROR.value;
            default:
                return NOTIFICATION_TYPES.INFO.value;
        }
    }

    /**
     * 获取通知持续时间
     * @param {string} severity - 错误严重级别
     * @returns {number} 持续时间（毫秒）
     */
    getNotificationDuration(severity) {
        switch (severity) {
            case ErrorSeverity.LOW:
                return NOTIFICATION_TYPES.INFO.duration;
            case ErrorSeverity.MEDIUM:
                return NOTIFICATION_TYPES.WARNING.duration;
            case ErrorSeverity.HIGH:
            case ErrorSeverity.CRITICAL:
                return NOTIFICATION_TYPES.ERROR.duration;
            default:
                return 3000;
        }
    }

    /**
     * 创建通知元素
     * @param {AppError} error - 错误对象
     */
    createNotificationElement(error) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${this.getNotificationType(error.severity)}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${this.getNotificationTitle(error.severity)}</div>
                <div class="notification-message">${error.message}</div>
            </div>
            <button class="notification-close">&times;</button>
        `;

        // Add close button event
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            notification.remove();
        });

        // Auto remove after duration
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, this.getNotificationDuration(error.severity));

        // Add to document
        const container = document.querySelector('.notifications-container') || document.body;
        container.appendChild(notification);
    }

    /**
     * 获取通知标题
     * @param {string} severity - 错误严重级别
     * @returns {string} 通知标题
     */
    getNotificationTitle(severity) {
        switch (severity) {
            case ErrorSeverity.LOW:
                return '提示';
            case ErrorSeverity.MEDIUM:
                return '警告';
            case ErrorSeverity.HIGH:
                return '错误';
            case ErrorSeverity.CRITICAL:
                return '严重错误';
            default:
                return '通知';
        }
    }

    /**
     * 调用错误回调
     * @param {AppError} error - 错误对象
     */
    callErrorCallbacks(error) {
        const callbacks = this.errorCallbacks.get(error.type) || [];
        callbacks.forEach(callback => {
            try {
                callback(error);
            } catch (callbackError) {
                console.error('Error in error callback:', callbackError);
            }
        });
    }

    /**
     * 注册错误回调
     * @param {string} errorType - 错误类型
     * @param {Function} callback - 回调函数
     */
    onError(errorType, callback) {
        if (!this.errorCallbacks.has(errorType)) {
            this.errorCallbacks.set(errorType, []);
        }
        this.errorCallbacks.get(errorType).push(callback);
    }

    /**
     * 移除错误回调
     * @param {string} errorType - 错误类型
     * @param {Function} callback - 回调函数
     */
    offError(errorType, callback) {
        const callbacks = this.errorCallbacks.get(errorType);
        if (callbacks) {
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    /**
     * 获取错误日志
     * @param {string} type - 错误类型过滤
     * @param {string} severity - 严重级别过滤
     * @param {number} limit - 限制数量
     * @returns {Array} 错误日志
     */
    getErrorLog(type = null, severity = null, limit = null) {
        let log = [...this.errorLog];

        // Apply filters
        if (type) {
            log = log.filter(entry => entry.type === type);
        }
        if (severity) {
            log = log.filter(entry => entry.severity === severity);
        }

        // Apply limit
        if (limit) {
            log = log.slice(0, limit);
        }

        return log;
    }

    /**
     * 清空错误日志
     */
    clearErrorLog() {
        this.errorLog = [];
    }

    /**
     * 获取错误统计
     * @returns {Object} 错误统计信息
     */
    getErrorStats() {
        const stats = {
            total: this.errorLog.length,
            byType: {},
            bySeverity: {},
            recent: this.errorLog.filter(entry => Date.now() - entry.timestamp < 3600000).length // Last hour
        };

        this.errorLog.forEach(entry => {
            // Count by type
            stats.byType[entry.type] = (stats.byType[entry.type] || 0) + 1;

            // Count by severity
            stats.bySeverity[entry.severity] = (stats.bySeverity[entry.severity] || 0) + 1;
        });

        return stats;
    }

    /**
     * 启用/禁用全局错误处理
     * @param {boolean} enabled - 是否启用
     */
    setGlobalErrorHandling(enabled) {
        this.globalErrorHandlingEnabled = enabled;

        if (enabled && typeof window !== 'undefined') {
            // Add global error handlers
            window.addEventListener('error', this.handleGlobalError.bind(this));
            window.addEventListener('unhandledrejection', this.handleUnhandledRejection.bind(this));
        } else if (typeof window !== 'undefined') {
            // Remove global error handlers
            window.removeEventListener('error', this.handleGlobalError.bind(this));
            window.removeEventListener('unhandledrejection', this.handleUnhandledRejection.bind(this));
        }
    }

    /**
     * 处理全局错误
     * @param {ErrorEvent} event - 错误事件
     */
    handleGlobalError(event) {
        this.handle(new Error(event.message), 'Global Error', {
            type: ErrorTypes.UNKNOWN,
            severity: ErrorSeverity.MEDIUM,
            details: {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            }
        });
    }

    /**
     * 处理未捕获的Promise拒绝
     * @param {PromiseRejectionEvent} event - 拒绝事件
     */
    handleUnhandledRejection(event) {
        this.handle(event.reason, 'Unhandled Promise Rejection', {
            type: ErrorTypes.UNKNOWN,
            severity: ErrorSeverity.HIGH
        });
    }

    /**
     * 生成错误ID
     * @returns {string} 唯一ID
     */
    generateErrorId() {
        return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * 包装异步函数以捕获错误
     * @param {Function} fn - 异步函数
     * @param {string} context - 上下文
     * @param {Object} options - 选项
     * @returns {Function} 包装后的函数
     */
    wrapAsync(fn, context, options = {}) {
        return async (...args) => {
            try {
                return await fn(...args);
            } catch (error) {
                this.handle(error, context, options);
                throw error;
            }
        };
    }

    /**
     * 创建边界组件错误处理器
     * @param {Function} fallback - 错误回退函数
     * @returns {Function} 边界处理器
     */
    createErrorBoundary(fallback = null) {
        return (error, errorInfo) => {
            this.handle(error, 'React Error Boundary', {
                type: ErrorTypes.UNKNOWN,
                severity: ErrorSeverity.HIGH,
                details: errorInfo
            });

            if (fallback) {
                fallback(error, errorInfo);
            }
        };
    }
}

// Create default instance
export const errorHandler = new ErrorHandler();

// Enable global error handling by default
if (typeof window !== 'undefined') {
    errorHandler.setGlobalErrorHandling(true);
}

// Export classes and instance
export { ErrorHandler };
export default errorHandler;