/**
 * 个人策略管理Dashboard - 常量定义
 * Personal Strategy Management Dashboard - Constants
 */

// API Configuration
export const API_CONFIG = {
    BASE_URL: 'http://localhost:3003',
    ENDPOINTS: {
        // Strategy endpoints
        STRATEGIES: '/api/strategies',
        STRATEGY_DETAIL: (id) => `/api/strategies/${id}`,
        STRATEGY_PERFORMANCE: (id) => `/api/strategies/${id}/performance`,
        STRATEGY_START: (id) => `/api/strategies/${id}/start`,
        STRATEGY_STOP: (id) => `/api/strategies/${id}/stop`,
        STRATEGY_DELETE: (id) => `/api/strategies/${id}/delete`,

        // Market data endpoints
        MARKET_DATA: '/api/market/data',
        MARKET_STATUS: '/api/market/status',

        // Statistics endpoints
        STATISTICS: '/api/statistics/summary',
        PORTFOLIO_STATS: '/api/statistics/portfolio',

        // Enhanced Sharpe Analysis endpoints (backtest system)
        SHARPE_ANALYSIS: '/api/backtest/sharpe-analysis',
        SHARPE_DISTRIBUTION: '/api/backtest/sharpe-distribution',
        ROLLING_SHARPE: '/api/backtest/rolling-sharpe',
        BENCHMARK_COMPARISON: '/api/backtest/benchmark-comparison',
        BENCHMARK_LIST: '/api/backtest/benchmarks'
    },
    TIMEOUT: 5000,
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 1000
};

// Local Storage Keys
export const STORAGE_KEYS = {
    STRATEGIES: 'strategy-dashboard-strategies',
    THEME: 'strategy-dashboard-theme',
    USER_PREFERENCES: 'strategy-dashboard-preferences',
    CACHE_TIMESTAMP: 'strategy-dashboard-cache-timestamp',
    MARKET_DATA: 'strategy-dashboard-market-data',
    PERFORMANCE_DATA: 'strategy-dashboard-performance-data'
};

// Chart Configuration
export const CHART_CONFIG = {
    // Common chart options
    COMMON: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    usePointStyle: true,
                    padding: 20
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: '#fff',
                bodyColor: '#fff',
                borderColor: '#ddd',
                borderWidth: 1,
                cornerRadius: 8,
                padding: 12
            }
        }
    },

    // Line chart specific
    LINE_CHART: {
        tension: 0.1,
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderWidth: 2
    },

    // Color palette
    COLORS: [
        '#4299e1', // Primary blue
        '#48bb78', // Success green
        '#ed8936', // Warning orange
        '#f56565', // Error red
        '#9f7aea', // Purple
        '#38b2ac', // Teal
        '#ed64a6', // Pink
        '#ecc94b'  // Yellow
    ]
};

// Strategy Types
export const STRATEGY_TYPES = {
    MOMENTUM: {
        value: 'momentum',
        label: '动量策略',
        description: '基于价格动量的交易策略',
        icon: 'trending-up'
    },
    MEAN_REVERSION: {
        value: 'mean_reversion',
        label: '均值回归',
        description: '价格回归均值的交易策略',
        icon: 'activity'
    },
    TREND_FOLLOWING: {
        value: 'trend_following',
        label: '趋势跟踪',
        description: '跟踪市场趋势的策略',
        icon: 'trending-up'
    },
    ARBITRAGE: {
        value: 'arbitrage',
        label: '套利策略',
        description: '跨市场套利策略',
        icon: 'zap'
    }
};

// Strategy Status
export const STRATEGY_STATUS = {
    RUNNING: {
        value: 'running',
        label: '运行中',
        color: '#48bb78',
        bgLight: '#c6f6d5'
    },
    STOPPED: {
        value: 'stopped',
        label: '已停止',
        color: '#f56565',
        bgLight: '#fed7d7'
    },
    ERROR: {
        value: 'error',
        label: '错误',
        color: '#ed8936',
        bgLight: '#feebc8'
    },
    PAUSED: {
        value: 'paused',
        label: '已暂停',
        color: '#a0aec0',
        bgLight: '#e2e8f0'
    }
};

// Time Periods for Charts
export const TIME_PERIODS = {
    ONE_DAY: { value: '1d', label: '1天', days: 1 },
    ONE_WEEK: { value: '1w', label: '1周', days: 7 },
    ONE_MONTH: { value: '1m', label: '1个月', days: 30 },
    THREE_MONTHS: { value: '3m', label: '3个月', days: 90 },
    SIX_MONTHS: { value: '6m', label: '6个月', days: 180 },
    ONE_YEAR: { value: '1y', label: '1年', days: 365 },
    ALL: { value: 'all', label: '全部', days: null }
};

// Performance Metrics
export const PERFORMANCE_METRICS = {
    TOTAL_RETURN: {
        key: 'total_return',
        label: '总收益率',
        unit: '%',
        format: (value) => `${(value * 100).toFixed(2)}%`,
        thresholds: {
            excellent: 0.20,
            good: 0.10,
            neutral: 0,
            poor: -0.10
        }
    },
    SHARPE_RATIO: {
        key: 'sharpe_ratio',
        label: 'Sharpe比率',
        unit: '',
        format: (value) => value.toFixed(2),
        thresholds: {
            excellent: 2.0,
            good: 1.5,
            neutral: 1.0,
            poor: 0.5
        }
    },
    MAX_DRAWDOWN: {
        key: 'max_drawdown',
        label: '最大回撤',
        unit: '%',
        format: (value) => `${Math.abs(value * 100).toFixed(2)}%`,
        thresholds: {
            excellent: -0.05,
            good: -0.10,
            neutral: -0.20,
            poor: -0.30
        }
    },
    WIN_RATE: {
        key: 'win_rate',
        label: '胜率',
        unit: '%',
        format: (value) => `${(value * 100).toFixed(1)}%`,
        thresholds: {
            excellent: 0.60,
            good: 0.55,
            neutral: 0.50,
            poor: 0.45
        }
    },
    PROFIT_FACTOR: {
        key: 'profit_factor',
        label: '盈利因子',
        unit: '',
        format: (value) => value.toFixed(2),
        thresholds: {
            excellent: 2.0,
            good: 1.5,
            neutral: 1.2,
            poor: 1.0
        }
    },
    // Enhanced Sharpe Analysis Metrics
    INFORMATION_RATIO: {
        key: 'information_ratio',
        label: '信息比率',
        unit: '',
        format: (value) => value.toFixed(2),
        thresholds: {
            excellent: 1.0,
            good: 0.5,
            neutral: 0,
            poor: -0.5
        }
    },
    TRACKING_ERROR: {
        key: 'tracking_error',
        label: '跟踪误差',
        unit: '%',
        format: (value) => `${(value * 100).toFixed(2)}%`,
        thresholds: {
            excellent: 0.05,
            good: 0.10,
            neutral: 0.15,
            poor: 0.20
        }
    },
    EXCESS_SHARPE: {
        key: 'excess_sharpe',
        label: '超额Sharpe',
        unit: '',
        format: (value) => value.toFixed(2),
        thresholds: {
            excellent: 1.0,
            good: 0.5,
            neutral: 0,
            poor: -0.5
        }
    }
};

// Benchmark Types for Sharpe Analysis
export const BENCHMARK_TYPES = {
    MARKET: {
        value: 'market',
        label: '市场指数',
        benchmarks: [
            { code: 'HSI', name: '恒生指数', description: '香港市场基准' },
            { code: 'SP500', name: '标普500', description: '美国市场基准' },
            { code: 'SSE', name: '上证综指', description: 'A股市场基准' },
            { code: 'NASDAQ', name: '纳斯达克', description: '科技股基准' },
            { code: 'FTSE', name: '富时100', description: '英国市场基准' }
        ]
    },
    BUY_AND_HOLD: {
        value: 'buy_and_hold',
        label: '买入持有',
        description: '买入持有策略基准'
    },
    CUSTOM: {
        value: 'custom',
        label: '自定义基准',
        description: '用户自定义基准'
    }
};

// Sharpe Analysis Configuration
export const SHARPE_CONFIG = {
    DEFAULT_WINDOW: 30, // Default rolling window in days
    DEFAULT_RISK_FREE_RATE: 0.03, // 3% annual risk-free rate
    TRADING_DAYS: 252, // Trading days per year
    MIN_DATA_POINTS: 30, // Minimum data points for calculation
    CONFIDENCE_LEVELS: [0.90, 0.95, 0.99], // Bootstrap confidence levels
    BOOTSTRAP_SAMPLES: 1000, // Default bootstrap samples
    ROLLING_WINDOWS: [21, 63, 126, 252], // Common rolling windows (1M, 3M, 6M, 1Y)
    BENCHMARK_COLORS: {
        HSI: '#FF6B6B',
        SP500: '#4ECDC4',
        SSE: '#45B7D1',
        NASDAQ: '#96CEB4',
        FTSE: '#FFEAA7',
        CUSTOM: '#DDA0DD'
    }
};

// Notification Types
export const NOTIFICATION_TYPES = {
    SUCCESS: {
        value: 'success',
        duration: 3000,
        icon: '✓'
    },
    ERROR: {
        value: 'error',
        duration: 5000,
        icon: '✕'
    },
    WARNING: {
        value: 'warning',
        duration: 4000,
        icon: '⚠'
    },
    INFO: {
        value: 'info',
        duration: 3000,
        icon: 'ℹ'
    }
};

// Error Messages
export const ERROR_MESSAGES = {
    NETWORK_ERROR: '网络连接失败，请检查网络设置',
    API_ERROR: 'API请求失败，请稍后重试',
    VALIDATION_ERROR: '输入数据验证失败',
    STRATEGY_NOT_FOUND: '策略不存在',
    STRATEGY_LIMIT_EXCEEDED: '策略数量已达上限（最多4个）',
    PERMISSION_DENIED: '权限不足',
    UNKNOWN_ERROR: '未知错误，请联系技术支持'
};

// Success Messages
export const SUCCESS_MESSAGES = {
    STRATEGY_CREATED: '策略创建成功',
    STRATEGY_UPDATED: '策略更新成功',
    STRATEGY_DELETED: '策略删除成功',
    STRATEGY_STARTED: '策略启动成功',
    STRATEGY_STOPPED: '策略停止成功',
    DATA_REFRESHED: '数据刷新成功',
    SETTINGS_SAVED: '设置保存成功'
};

// Validation Rules
export const VALIDATION_RULES = {
    STRATEGY_NAME: {
        required: true,
        minLength: 2,
        maxLength: 50,
        pattern: /^[a-zA-Z0-9\u4e00-\u9fa5\s\-_]+$/,
        message: '策略名称必须是2-50个字符，支持中英文、数字、空格、横线和下划线'
    },
    INITIAL_CAPITAL: {
        required: true,
        min: 10000,
        max: 100000000,
        step: 10000,
        message: '初始资金必须为10,000-100,000,000之间的10,000的倍数'
    },
    RISK_LIMIT: {
        required: true,
        min: 0.01,
        max: 1.0,
        step: 0.01,
        message: '风险限制必须在1%-100%之间'
    },
    STRATEGY_DESCRIPTION: {
        maxLength: 500,
        message: '策略描述不能超过500个字符'
    }
};

// Default Values
export const DEFAULT_VALUES = {
    STRATEGY: {
        name: '',
        description: '',
        strategy_type: 'momentum',
        initial_capital: 100000,
        risk_limit: 0.20,
        status: 'stopped'
    },
    CHART_PERIOD: '1m',
    THEME: 'light',
    AUTO_REFRESH_INTERVAL: 30000, // 30 seconds
    CACHE_DURATION: 300000 // 5 minutes
};

// Theme Configuration
export const THEMES = {
    LIGHT: 'light',
    DARK: 'dark'
};

// Breakpoints for Responsive Design
export const BREAKPOINTS = {
    XS: 0,
    SM: 576,
    MD: 768,
    LG: 992,
    XL: 1200,
    XXL: 1400
};

// Animation Durations
export const ANIMATIONS = {
    FAST: 150,
    NORMAL: 300,
    SLOW: 500
};

// Event Names
export const EVENTS = {
    STRATEGY_ADDED: 'strategy:added',
    STRATEGY_UPDATED: 'strategy:updated',
    STRATEGY_DELETED: 'strategy:deleted',
    STRATEGY_STARTED: 'strategy:started',
    STRATEGY_STOPPED: 'strategy:stopped',
    DATA_REFRESHED: 'data:refreshed',
    THEME_CHANGED: 'theme:changed',
    ERROR_OCCURRED: 'error:occurred'
};

// Cache Configuration
export const CACHE_CONFIG = {
    STRATEGIES_TTL: 300000, // 5 minutes
    PERFORMANCE_TTL: 60000, // 1 minute
    MARKET_DATA_TTL: 30000, // 30 seconds
    MAX_CACHE_SIZE: 100 // Maximum number of cached items
};

// WebSocket Configuration (optional)
export const WEBSOCKET_CONFIG = {
    URL: 'ws://localhost:3003/ws',
    RECONNECT_INTERVAL: 5000,
    MAX_RECONNECT_ATTEMPTS: 10,
    HEARTBEAT_INTERVAL: 30000
};