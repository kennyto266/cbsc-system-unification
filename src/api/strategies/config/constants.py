"""
常量定义
Constants Definition

职责：
- 系统常量
- 枚举值
- 配置常量
"""

from typing import Dict, Any

# API版本
API_V1 = "v1"
API_V2 = "v2"
CURRENT_API_VERSION = API_V2

# 默认分页
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
DEFAULT_PAGE = 1

# 缓存键前缀
CACHE_PREFIX = "cbsc:strategies"

# 策略类型配置
STRATEGY_TYPE_CONFIG = {
    "direct_rsi": {
        "name": "直接RSI",
        "description": "基于单一RSI指标的策略",
        "default_parameters": {
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "stop_loss": 0.05,
            "take_profit": 0.1
        }
    },
    "dual_rsi": {
        "name": "双RSI",
        "description": "基于双RSI指标的策略",
        "default_parameters": {
            "fast_rsi_period": 7,
            "slow_rsi_period": 21,
            "signal_threshold": 0.7,
            "stop_loss": 0.04,
            "take_profit": 0.08
        }
    },
    "composite": {
        "name": "复合策略",
        "description": "多指标复合策略",
        "default_parameters": {
            "rsi_weight": 0.4,
            "macd_weight": 0.3,
            "volume_weight": 0.3,
            "stop_loss": 0.06,
            "take_profit": 0.12
        }
    },
    "custom": {
        "name": "自定义策略",
        "description": "用户自定义策略",
        "default_parameters": {}
    }
}

# 风险等级配置
RISK_LEVEL_CONFIG = {
    "low": {
        "name": "低风险",
        "description": "保守型策略，注重资本保护",
        "max_position_size": 0.1,
        "max_leverage": 2,
        "recommended_stop_loss": 0.02
    },
    "medium": {
        "name": "中风险",
        "description": "平衡型策略，风险收益平衡",
        "max_position_size": 0.2,
        "max_leverage": 5,
        "recommended_stop_loss": 0.05
    },
    "high": {
        "name": "高风险",
        "description": "激进型策略，追求高收益",
        "max_position_size": 0.5,
        "max_leverage": 10,
        "recommended_stop_loss": 0.1
    }
}

# 执行模式配置
EXECUTION_MODE_CONFIG = {
    "backtest": {
        "name": "回测模式",
        "description": "历史数据回测",
        "max_data_range_days": 730,
        "default_timeframe": "1d"
    },
    "real_time": {
        "name": "实时模式",
        "description": "实时数据执行",
        "max_concurrent_strategies": 5,
        "heartbeat_interval": 30
    }
}

# 信号类型配置
SIGNAL_TYPE_CONFIG = {
    "buy": {
        "name": "买入信号",
        "description": "建议买入",
        "color": "#00ff00"
    },
    "sell": {
        "name": "卖出信号",
        "description": "建议卖出",
        "color": "#ff0000"
    },
    "hold": {
        "name": "持有信号",
        "description": "建议持有",
        "color": "#ffff00"
    }
}

# 性能指标阈值
PERFORMANCE_THRESHOLDS = {
    "excellent_sharpe_ratio": 2.0,
    "good_sharpe_ratio": 1.0,
    "excellent_return": 0.2,
    "good_return": 0.1,
    "max_acceptable_drawdown": 0.2,
    "min_win_rate": 0.5
}

# WebSocket消息类型
WS_MESSAGE_TYPES = {
    "connection_established": "连接建立",
    "strategy_update": "策略更新",
    "execution_update": "执行更新",
    "signal_generated": "信号生成",
    "performance_update": "性能更新",
    "market_data_update": "市场数据更新",
    "notification": "通知",
    "error": "错误",
    "ping": "心跳",
    "pong": "心跳响应"
}

# 通知类型
NOTIFICATION_TYPES = {
    "strategy_alert": "策略告警",
    "execution_complete": "执行完成",
    "performance_warning": "性能警告",
    "system_maintenance": "系统维护",
    "feature_update": "功能更新",
    "market_alert": "市场提醒"
}

# 错误码映射
ERROR_CODE_MAP = {
    1000: "INTERNAL_SERVER_ERROR",
    1001: "INVALID_REQUEST",
    1002: "VALIDATION_ERROR",
    1003: "NOT_FOUND",
    1004: "UNAUTHORIZED",
    1005: "FORBIDDEN",
    1006: "CONFLICT",
    1007: "RATE_LIMITED",
    1008: "TIMEOUT",
    2001: "STRATEGY_NOT_FOUND",
    2002: "STRATEGY_ALREADY_EXISTS",
    2003: "STRATEGY_INVALID_PARAMETERS",
    2004: "STRATEGY_INVALID_STATUS",
    2005: "STRATEGY_CANNOT_DELETE",
    2006: "STRATEGY_TEMPLATE_NOT_FOUND",
    2007: "STRATEGY_TYPE_MISMATCH",
    2008: "STRATEGY_EXECUTION_FAILED",
    2009: "STRATEGY_ALREADY_RUNNING",
    2010: "STRATEGY_OPTIMIZATION_FAILED",
    3001: "EXECUTION_NOT_FOUND",
    3002: "EXECUTION_ALREADY_COMPLETED",
    3003: "EXECUTION_CANNOT_STOP",
    3004: "EXECUTION_TIMEOUT",
    3005: "EXECUTION_RESOURCE_EXHAUSTED",
    3006: "EXECUTION_DATA_NOT_AVAILABLE",
    4001: "USER_NOT_FOUND",
    4002: "USER_ALREADY_EXISTS",
    4003: "USER_INVALID_CREDENTIALS",
    4004: "USER_ACCOUNT_LOCKED",
    4005: "USER_PREFERENCES_INVALID",
    4006: "USER_INSUFFICIENT_PERMISSIONS",
    5001: "DATA_NOT_FOUND",
    5002: "DATA_CORRUPTION",
    5003: "DATA_CONNECTION_FAILED",
    5004: "DATA_CONSTRAINT_VIOLATION",
    6001: "EXTERNAL_SERVICE_UNAVAILABLE",
    6002: "EXTERNAL_SERVICE_TIMEOUT",
    6003: "EXTERNAL_SERVICE_ERROR",
    6004: "MARKET_DATA_UNAVAILABLE",
    7001: "CACHE_CONNECTION_FAILED",
    7002: "CACHE_OPERATION_FAILED",
    8001: "WEBSOCKET_CONNECTION_FAILED",
    8002: "WEBSOCKET_AUTHENTICATION_FAILED",
    8003: "WEBSOCKET_MESSAGE_INVALID"
}

# 状态码描述
STATUS_DESCRIPTIONS = {
    "200": "OK - 请求成功",
    "201": "Created - 资源创建成功",
    "204": "No Content - 请求成功，无返回内容",
    "400": "Bad Request - 请求参数错误",
    "401": "Unauthorized - 未授权",
    "403": "Forbidden - 权限不足",
    "404": "Not Found - 资源未找到",
    "409": "Conflict - 资源冲突",
    "422": "Unprocessable Entity - 请求格式正确但语义错误",
    "429": "Too Many Requests - 请求过于频繁",
    "500": "Internal Server Error - 服务器内部错误",
    "502": "Bad Gateway - 网关错误",
    "503": "Service Unavailable - 服务不可用"
}

# 时间格式
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"

# 文件大小限制
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = [".json", ".csv", ".xlsx", ".txt"]

# 正则表达式模式
REGEX_PATTERNS = {
    "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    "username": r'^[a-zA-Z0-9_]{3,20}$',
    "strategy_name": r'^[a-zA-Z0-9_\-\u4e00-\u9fa5]{1,100}$',
    "uuid": r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    "token": r'^[A-Za-z0-9\-_\.]+$'
}

# 默认值
DEFAULT_VALUES = {
    "page_size": DEFAULT_PAGE_SIZE,
    "page": DEFAULT_PAGE,
    "risk_level": "medium",
    "strategy_type": "custom",
    "execution_mode": "backtest",
    "auto_refresh_interval": 30,
    "notification_enabled": True,
    "theme": "light"
}