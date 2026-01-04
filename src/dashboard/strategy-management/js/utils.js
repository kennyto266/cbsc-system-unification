/**
 * 个人策略管理Dashboard - 工具函数
 * Personal Strategy Management Dashboard - Utility Functions
 */

import { VALIDATION_RULES, ERROR_MESSAGES, PERFORMANCE_METRICS } from './constants.js';

/**
 * 格式化数字
 * @param {number} value - 要格式化的数字
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的字符串
 */
export function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) {
        return '--';
    }
    return Number(value).toFixed(decimals);
}

/**
 * 格式化货币
 * @param {number} value - 货币值
 * @param {string} currency - 货币符号
 * @returns {string} 格式化后的货币字符串
 */
export function formatCurrency(value, currency = '¥') {
    if (value === null || value === undefined || isNaN(value)) {
        return '--';
    }
    const formatted = Math.abs(value).toLocaleString('zh-CN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });
    return `${value < 0 ? '-' : ''}${currency}${formatted}`;
}

/**
 * 格式化百分比
 * @param {number} value - 小数值 (0.1 表示 10%)
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的百分比字符串
 */
export function formatPercentage(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) {
        return '--%';
    }
    return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * 格式化日期
 * @param {Date|string} date - 日期对象或字符串
 * @param {string} format - 格式类型 ('date', 'datetime', 'time')
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date, format = 'date') {
    if (!date) return '--';

    const d = new Date(date);
    if (isNaN(d.getTime())) return '--';

    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');

    switch (format) {
        case 'datetime':
            return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        case 'time':
            return `${hours}:${minutes}:${seconds}`;
        case 'date':
        default:
            return `${year}-${month}-${day}`;
    }
}

/**
 * 计算时间差
 * @param {Date|string} date1 - 第一个日期
 * @param {Date|string} date2 - 第二个日期（默认为当前时间）
 * @returns {Object} 包含天、小时、分钟、秒的时间差对象
 */
export function timeDiff(date1, date2 = new Date()) {
    const d1 = new Date(date1);
    const d2 = new Date(date2);
    const diff = Math.abs(d2 - d1);

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    return { days, hours, minutes, seconds };
}

/**
 * 防抖函数
 * @param {Function} func - 要防抖的函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 节流函数
 * @param {Function} func - 要节流的函数
 * @param {number} limit - 时间限制（毫秒）
 * @returns {Function} 节流后的函数
 */
export function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * 深度克隆对象
 * @param {any} obj - 要克隆的对象
 * @returns {any} 克隆后的对象
 */
export function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') {
        return obj;
    }

    if (obj instanceof Date) {
        return new Date(obj);
    }

    if (obj instanceof Array) {
        return obj.map(item => deepClone(item));
    }

    if (typeof obj === 'object') {
        const cloned = {};
        Object.keys(obj).forEach(key => {
            cloned[key] = deepClone(obj[key]);
        });
        return cloned;
    }

    return obj;
}

/**
 * 表单验证
 * @param {Object} data - 要验证的数据
 * @param {Object} rules - 验证规则
 * @returns {Object} 验证结果 { valid: boolean, errors: string[] }
 */
export function validate(data, rules) {
    const errors = [];

    Object.keys(rules).forEach(field => {
        const value = data[field];
        const rule = rules[field];

        // Required validation
        if (rule.required && (!value || value.toString().trim() === '')) {
            errors.push(`${field} 是必填项`);
            return;
        }

        // Skip other validations if field is empty and not required
        if (!value && !rule.required) {
            return;
        }

        // Type validation
        if (rule.type && typeof value !== rule.type) {
            errors.push(`${field} 必须是 ${rule.type} 类型`);
            return;
        }

        // Min/Max validation for numbers
        if (typeof value === 'number') {
            if (rule.min !== undefined && value < rule.min) {
                errors.push(`${field} 不能小于 ${rule.min}`);
            }
            if (rule.max !== undefined && value > rule.max) {
                errors.push(`${field} 不能大于 ${rule.max}`);
            }
        }

        // Length validation for strings
        if (typeof value === 'string') {
            if (rule.minLength !== undefined && value.length < rule.minLength) {
                errors.push(`${field} 长度不能少于 ${rule.minLength} 个字符`);
            }
            if (rule.maxLength !== undefined && value.length > rule.maxLength) {
                errors.push(`${field} 长度不能超过 ${rule.maxLength} 个字符`);
            }
            if (rule.pattern && !rule.pattern.test(value)) {
                errors.push(rule.message || `${field} 格式不正确`);
            }
        }

        // Array validation
        if (Array.isArray(value)) {
            if (rule.minItems !== undefined && value.length < rule.minItems) {
                errors.push(`${field} 至少需要 ${rule.minItems} 项`);
            }
            if (rule.maxItems !== undefined && value.length > rule.maxItems) {
                errors.push(`${field} 最多只能有 ${rule.maxItems} 项`);
            }
        }
    });

    return {
        valid: errors.length === 0,
        errors
    };
}

/**
 * 生成唯一ID
 * @param {string} prefix - ID前缀
 * @returns {string} 唯一ID
 */
export function generateId(prefix = 'id') {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 获取性能指标的颜色
 * @param {string} metric - 指标名称
 * @param {number} value - 指标值
 * @returns {string} 颜色值
 */
export function getPerformanceColor(metric, value) {
    const metricConfig = PERFORMANCE_METRICS[metric.toUpperCase()];
    if (!metricConfig) return '#4a5568';

    const { thresholds } = metricConfig;

    if (value >= thresholds.excellent) return '#22c55e'; // green-500
    if (value >= thresholds.good) return '#84cc16'; // lime-500
    if (value >= thresholds.neutral) return '#eab308'; // yellow-500
    return '#ef4444'; // red-500
}

/**
 * 计算数组的统计信息
 * @param {number[]} arr - 数字数组
 * @returns {Object} 统计信息对象
 */
export function calculateStats(arr) {
    if (!arr || arr.length === 0) {
        return {
            count: 0,
            sum: 0,
            mean: 0,
            median: 0,
            min: 0,
            max: 0,
            std: 0
        };
    }

    const sorted = [...arr].sort((a, b) => a - b);
    const count = arr.length;
    const sum = arr.reduce((a, b) => a + b, 0);
    const mean = sum / count;

    // Median calculation
    const mid = Math.floor(count / 2);
    const median = count % 2 === 0
        ? (sorted[mid - 1] + sorted[mid]) / 2
        : sorted[mid];

    // Standard deviation
    const variance = arr.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / count;
    const std = Math.sqrt(variance);

    return {
        count,
        sum,
        mean,
        median,
        min: sorted[0],
        max: sorted[count - 1],
        std
    };
}

/**
 * 数据聚合函数
 * @param {Array} data - 数据数组
 * @param {string} groupBy - 分组字段
 * @param {string} aggregate - 聚合方式 ('sum', 'avg', 'count', 'min', 'max')
 * @param {string} valueField - 值字段（用于 sum, avg, min, max）
 * @returns {Object} 聚合后的数据
 */
export function aggregateData(data, groupBy, aggregate, valueField) {
    const grouped = {};

    data.forEach(item => {
        const key = item[groupBy];
        if (!grouped[key]) {
            grouped[key] = [];
        }
        grouped[key].push(item[valueField]);
    });

    const result = {};
    Object.keys(grouped).forEach(key => {
        const values = grouped[key];
        switch (aggregate) {
            case 'sum':
                result[key] = values.reduce((a, b) => a + b, 0);
                break;
            case 'avg':
                result[key] = values.reduce((a, b) => a + b, 0) / values.length;
                break;
            case 'count':
                result[key] = values.length;
                break;
            case 'min':
                result[key] = Math.min(...values);
                break;
            case 'max':
                result[key] = Math.max(...values);
                break;
            default:
                result[key] = values;
        }
    });

    return result;
}

/**
 * 生成颜色渐变
 * @param {string} startColor - 起始颜色
 * @param {string} endColor - 结束颜色
 * @param {number} steps - 步数
 * @returns {string[]} 颜色数组
 */
export function generateGradient(startColor, endColor, steps) {
    const start = hexToRgb(startColor);
    const end = hexToRgb(endColor);

    const gradient = [];
    for (let i = 0; i < steps; i++) {
        const ratio = i / (steps - 1);
        const r = Math.round(start.r + (end.r - start.r) * ratio);
        const g = Math.round(start.g + (end.g - start.g) * ratio);
        const b = Math.round(start.b + (end.b - start.b) * ratio);
        gradient.push(rgbToHex(r, g, b));
    }

    return gradient;
}

/**
 * 十六进制颜色转RGB
 * @param {string} hex - 十六进制颜色
 * @returns {Object} RGB对象
 */
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

/**
 * RGB转十六进制颜色
 * @param {number} r - 红色值
 * @param {number} g - 绿色值
 * @param {number} b - 蓝色值
 * @returns {string} 十六进制颜色
 */
function rgbToHex(r, g, b) {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

/**
 * 下载文件
 * @param {string} data - 文件内容
 * @param {string} filename - 文件名
 * @param {string} type - MIME类型
 */
export function downloadFile(data, filename, type = 'text/plain') {
    const blob = new Blob([data], { type });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(url);
}

/**
 * 复制到剪贴板
 * @param {string} text - 要复制的文本
 * @returns {Promise<boolean>} 是否成功
 */
export async function copyToClipboard(text) {
    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
            return true;
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            const result = document.execCommand('copy');
            document.body.removeChild(textArea);
            return result;
        }
    } catch (error) {
        console.error('Failed to copy text: ', error);
        return false;
    }
}

/**
 * 获取设备信息
 * @returns {Object} 设备信息对象
 */
export function getDeviceInfo() {
    return {
        isMobile: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
        isTablet: /iPad|Android|webOS|BlackBerry|PlayBook/i.test(navigator.userAgent) && window.innerWidth > 768,
        isDesktop: !/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
        screenWidth: window.innerWidth,
        screenHeight: window.innerHeight,
        pixelRatio: window.devicePixelRatio || 1,
        language: navigator.language || navigator.userLanguage,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
    };
}

/**
 * 错误处理
 * @param {Error} error - 错误对象
 * @param {string} context - 错误上下文
 * @returns {string} 用户友好的错误消息
 */
export function handleError(error, context = '') {
    console.error(`Error in ${context}:`, error);

    // Network errors
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
        return ERROR_MESSAGES.NETWORK_ERROR;
    }

    // API errors
    if (error.status) {
        switch (error.status) {
            case 400:
                return ERROR_MESSAGES.VALIDATION_ERROR;
            case 401:
                return ERROR_MESSAGES.PERMISSION_DENIED;
            case 404:
                return ERROR_MESSAGES.STRATEGY_NOT_FOUND;
            case 429:
                return '请求过于频繁，请稍后重试';
            case 500:
                return ERROR_MESSAGES.API_ERROR;
            default:
                return ERROR_MESSAGES.UNKNOWN_ERROR;
        }
    }

    // Return custom error message if available
    if (error.message && error.message !== 'Failed to fetch') {
        return error.message;
    }

    return ERROR_MESSAGES.UNKNOWN_ERROR;
}

/**
 * 安全的JSON解析
 * @param {string} str - JSON字符串
 * @param {any} defaultValue - 默认值
 * @returns {any} 解析后的对象或默认值
 */
export function safeJsonParse(str, defaultValue = null) {
    try {
        return JSON.parse(str);
    } catch (error) {
        return defaultValue;
    }
}

/**
 * 获取随机颜色
 * @returns {string} 随机的十六进制颜色
 */
export function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

// Export all utility functions as default for easy importing
export default {
    formatNumber,
    formatCurrency,
    formatPercentage,
    formatDate,
    timeDiff,
    debounce,
    throttle,
    deepClone,
    validate,
    generateId,
    getPerformanceColor,
    calculateStats,
    aggregateData,
    generateGradient,
    downloadFile,
    copyToClipboard,
    getDeviceInfo,
    handleError,
    safeJsonParse,
    getRandomColor
};