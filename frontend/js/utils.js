/**
 * Utility Functions Module - 工具函數模塊
 * 通用工具函數集合，用於數據處理、格式化、驗證等
 */

/**
 * Data Models - 數據模型定義
 */

// 策略表現模型
class StrategyPerformance {
    constructor(name, sharpeRatio, maxDrawdown, totalReturn, winRate, status) {
        this.name = name;
        this.sharpeRatio = sharpeRatio;
        this.maxDrawdown = maxDrawdown;
        this.totalReturn = totalReturn;
        this.winRate = winRate;
        this.status = status;
        this.lastUpdated = new Date();

        // Additional default properties
        this.annualReturn = totalReturn;
        this.profitFactor = 0;
        this.calmarRatio = 0;
        this.totalTrades = 0;
        this.profitTrades = 0;
    }

    // Calculate derived metrics
    get profitLoss() {
        return this.totalReturn;
    }

    get lossRate() {
        return 1 - this.winRate;
    }

    get grade() {
        // Calculate grade based on Sharpe ratio and returns
        if (this.sharpeRatio >= 1.5 && this.totalReturn >= 0.15) return 'A+';
        if (this.sharpeRatio >= 1.2 && this.totalReturn >= 0.10) return 'A';
        if (this.sharpeRatio >= 1.0 && this.totalReturn >= 0.08) return 'B+';
        if (this.sharpeRatio >= 0.8 && this.totalReturn >= 0.05) return 'B';
        if (this.sharpeRatio >= 0.5 && this.totalReturn >= 0.03) return 'C+';
        return 'C';
    }

    get riskLevel() {
        if (this.maxDrawdown <= 0.05) return 'low';
        if (this.maxDrawdown <= 0.10) return 'medium';
        return 'high';
    }

    // Update performance data
    update(data) {
        Object.assign(this, data);
        this.lastUpdated = new Date();
    }

    // Serialize to plain object
    toJSON() {
        return {
            name: this.name,
            sharpeRatio: this.sharpeRatio,
            maxDrawdown: this.maxDrawdown,
            totalReturn: this.totalReturn,
            winRate: this.winRate,
            status: this.status,
            annualReturn: this.annualReturn,
            profitFactor: this.profitFactor,
            calmarRatio: this.calmarRatio,
            totalTrades: this.totalTrades,
            profitTrades: this.profitTrades,
            grade: this.grade,
            riskLevel: this.riskLevel,
            lastUpdated: this.lastUpdated.toISOString()
        };
    }
}

// 策略配置模型
class StrategyConfig {
    constructor(name, enabled, parameters, description) {
        this.name = name;
        this.enabled = enabled;
        this.parameters = parameters || {};
        this.description = description || '';
        this.strategyType = 'unknown';
        this.category = 'default';
        this.riskLevel = 'medium';
        this.lastUpdated = new Date();
    }

    // Enable/disable strategy
    toggle() {
        this.enabled = !this.enabled;
        this.lastUpdated = new Date();
        return this.enabled;
    }

    // Update parameters
    updateParameters(newParams) {
        this.parameters = { ...this.parameters, ...newParams };
        this.lastUpdated = new Date();
    }

    // Validate parameters
    validateParameters() {
        const errors = [];

        // Common validations
        if (this.parameters.rsi_period && (this.parameters.rsi_period < 2 || this.parameters.rsi_period > 50)) {
            errors.push('RSI period must be between 2 and 50');
        }

        if (this.parameters.oversold_threshold && this.parameters.overbought_threshold) {
            if (this.parameters.oversold_threshold >= this.parameters.overbought_threshold) {
                errors.push('Oversold threshold must be less than overbought threshold');
            }
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    // Serialize to plain object
    toJSON() {
        return {
            name: this.name,
            enabled: this.enabled,
            parameters: this.parameters,
            description: this.description,
            strategyType: this.strategyType,
            category: this.category,
            riskLevel: this.riskLevel,
            lastUpdated: this.lastUpdated.toISOString()
        };
    }
}

/**
 * Utility Functions - 工具函數
 */

/**
 * Format percentage value
 * @param {number} value - Value to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted percentage string
 */
function formatPercentage(value, decimals = 2) {
    if (typeof value !== 'number' || isNaN(value)) {
        return '0.00%';
    }
    return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format number with thousand separators
 * @param {number} value - Value to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted number string
 */
function formatNumber(value, decimals = 2) {
    if (typeof value !== 'number' || isNaN(value)) {
        return '0';
    }
    return value.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Format currency value
 * @param {number} value - Value to format
 * @param {string} currency - Currency code
 * @returns {string} Formatted currency string
 */
function formatCurrency(value, currency = 'USD') {
    if (typeof value !== 'number' || isNaN(value)) {
        return `${currency} 0`;
    }
    return `${currency} ${formatNumber(value, 2)}`;
}

/**
 * Format date/time string
 * @param {Date|string} date - Date to format
 * @param {boolean} includeTime - Whether to include time
 * @returns {string} Formatted date string
 */
function formatDate(date, includeTime = true) {
    const d = new Date(date);
    if (isNaN(d.getTime())) {
        return 'Invalid Date';
    }

    const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    };

    if (includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
        options.second = '2-digit';
    }

    return d.toLocaleString('en-US', options);
}

/**
 * Get relative time string
 * @param {Date|string} date - Date to compare
 * @returns {string} Relative time string
 */
function getRelativeTime(date) {
    const d = new Date(date);
    if (isNaN(d.getTime())) {
        return 'Unknown';
    }

    const now = new Date();
    const diffMs = now - d;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 60) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

    return formatDate(date, false);
}

/**
 * Generate color based on value
 * @param {number} value - Value to evaluate
 * @param {boolean} inverted - Whether to invert color logic
 * @returns {string} CSS color class
 */
function getValueColor(value, inverted = false) {
    if (typeof value !== 'number') return 'text-gray-500';

    if (inverted) {
        if (value < 0) return 'text-green-600';
        if (value > 0) return 'text-red-600';
        return 'text-gray-600';
    } else {
        if (value > 0) return 'text-green-600';
        if (value < 0) return 'text-red-600';
        return 'text-gray-600';
    }
}

/**
 * Get status badge styling
 * @param {string} status - Status value
 * @returns {Object} CSS classes and text
 */
function getStatusBadge(status) {
    const statusConfig = {
        'enabled': {
            class: 'bg-green-100 text-green-800 border-green-200',
            text: 'Enabled',
            icon: '✓'
        },
        'active': {
            class: 'bg-green-100 text-green-800 border-green-200',
            text: 'Active',
            icon: '✓'
        },
        'disabled': {
            class: 'bg-red-100 text-red-800 border-red-200',
            text: 'Disabled',
            icon: '✗'
        },
        'inactive': {
            class: 'bg-gray-100 text-gray-800 border-gray-200',
            text: 'Inactive',
            icon: '○'
        },
        'running': {
            class: 'bg-blue-100 text-blue-800 border-blue-200',
            text: 'Running',
            icon: '▶'
        },
        'stopped': {
            class: 'bg-yellow-100 text-yellow-800 border-yellow-200',
            text: 'Stopped',
            icon: '■'
        },
        'error': {
            class: 'bg-red-100 text-red-800 border-red-200',
            text: 'Error',
            icon: '⚠'
        },
        'pending': {
            class: 'bg-yellow-100 text-yellow-800 border-yellow-200',
            text: 'Pending',
            icon: '⏳'
        }
    };

    return statusConfig[status] || {
        class: 'bg-gray-100 text-gray-800 border-gray-200',
        text: status,
        icon: '?'
    };
}

/**
 * Get grade badge styling
 * @param {string} grade - Grade value (A+, A, B+, etc.)
 * @returns {Object} CSS classes
 */
function getGradeBadge(grade) {
    const gradeConfig = {
        'A+': 'bg-purple-100 text-purple-800 border-purple-200',
        'A': 'bg-blue-100 text-blue-800 border-blue-200',
        'A-': 'bg-blue-100 text-blue-700 border-blue-200',
        'B+': 'bg-green-100 text-green-800 border-green-200',
        'B': 'bg-green-100 text-green-700 border-green-200',
        'B-': 'bg-yellow-100 text-yellow-700 border-yellow-200',
        'C+': 'bg-yellow-100 text-yellow-600 border-yellow-200',
        'C': 'bg-orange-100 text-orange-700 border-orange-200',
        'C-': 'bg-red-100 text-red-700 border-red-200'
    };

    return gradeConfig[grade] || 'bg-gray-100 text-gray-800 border-gray-200';
}

/**
 * Get risk level styling
 * @param {string} riskLevel - Risk level (low, medium, high)
 * @returns {Object} CSS classes and indicator
 */
function getRiskLevelBadge(riskLevel) {
    const riskConfig = {
        'low': {
            class: 'bg-green-100 text-green-800 border-green-200',
            text: 'Low Risk',
            indicator: '🟢'
        },
        'medium': {
            class: 'bg-yellow-100 text-yellow-800 border-yellow-200',
            text: 'Medium Risk',
            indicator: '🟡'
        },
        'high': {
            class: 'bg-red-100 text-red-800 border-red-200',
            text: 'High Risk',
            indicator: '🔴'
        }
    };

    return riskConfig[riskLevel] || {
        class: 'bg-gray-100 text-gray-800 border-gray-200',
        text: 'Unknown',
        indicator: '⚪'
    };
}

/**
 * Debounce function to limit function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
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
 * Throttle function to limit function calls
 * @param {Function} func - Function to throttle
 * @param {number} limit - Limit time in milliseconds
 * @returns {Function} Throttled function
 */
function throttle(func, limit) {
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
 * Deep clone object
 * @param {any} obj - Object to clone
 * @returns {any} Cloned object
 */
function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') return obj;
    if (obj instanceof Date) return new Date(obj);
    if (obj instanceof Array) return obj.map(item => deepClone(item));
    if (typeof obj === 'object') {
        const clonedObj = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                clonedObj[key] = deepClone(obj[key]);
            }
        }
        return clonedObj;
    }
    return obj;
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} Is valid email
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Generate random ID
 * @param {number} length - ID length
 * @returns {string} Random ID
 */
function generateId(length = 8) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

/**
 * Calculate statistics for array of numbers
 * @param {Array<number>} values - Array of numbers
 * @returns {Object} Statistics object
 */
function calculateStats(values) {
    if (!Array.isArray(values) || values.length === 0) {
        return { min: 0, max: 0, mean: 0, median: 0, stdDev: 0 };
    }

    const sorted = [...values].sort((a, b) => a - b);
    const sum = values.reduce((a, b) => a + b, 0);
    const mean = sum / values.length;

    const median = sorted.length % 2 === 0
        ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
        : sorted[Math.floor(sorted.length / 2)];

    const variance = values.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);

    return {
        min: sorted[0],
        max: sorted[sorted.length - 1],
        mean: mean,
        median: median,
        stdDev: stdDev,
        count: values.length
    };
}

/**
 * Export classes and functions
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        StrategyPerformance,
        StrategyConfig,
        formatPercentage,
        formatNumber,
        formatCurrency,
        formatDate,
        getRelativeTime,
        getValueColor,
        getStatusBadge,
        getGradeBadge,
        getRiskLevelBadge,
        debounce,
        throttle,
        deepClone,
        isValidEmail,
        generateId,
        calculateStats
    };
}

// Global assignment for browser
window.StrategyPerformance = StrategyPerformance;
window.StrategyConfig = StrategyConfig;
window.formatPercentage = formatPercentage;
window.formatNumber = formatNumber;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.getRelativeTime = getRelativeTime;
window.getValueColor = getValueColor;
window.getStatusBadge = getStatusBadge;
window.getGradeBadge = getGradeBadge;
window.getRiskLevelBadge = getRiskLevelBadge;
window.debounce = debounce;
window.throttle = throttle;
window.deepClone = deepClone;
window.isValidEmail = isValidEmail;
window.generateId = generateId;
window.calculateStats = calculateStats;