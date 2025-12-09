#!/usr / bin / env python3
"""
API標準化規範
港股量化交易系統 - API設計和實現標準

定義統一的API設計原則、命名規範、響應格式、
錯誤處理和安全標準。

內容:
- RESTful API設計原則
- 統一響應格式標準
- 錯誤處理規範
- 認證授權標準
- API版本管理策略
- 限流和安全規範
- 文檔標準
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class HTTPStatusCodes:
    """HTTP狀態碼標準"""

    # 成功響應
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204

    # 重定向
    MOVED_PERMANENTLY = 301
    FOUND = 302
    NOT_MODIFIED = 304

    # 客戶端錯誤
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429

    # 服務器錯誤
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


class APIErrorCodes:
    """API錯誤代碼標準"""

    # 通用錯誤
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # 業務錯誤
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    INVALID_SYMBOL = "INVALID_SYMBOL"
    MARKET_CLOSED = "MARKET_CLOSED"
    ORDER_REJECTED = "ORDER_REJECTED"
    STRATEGY_NOT_FOUND = "STRATEGY_NOT_FOUND"
    BACKTEST_FAILED = "BACKTEST_FAILED"

    # 系統錯誤
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"


class UserRole(str, Enum):
    """用戶角色枚舉"""

    ADMIN = "admin"
    TRADER = "trader"
    ANALYST = "analyst"
    VIEWER = "viewer"


class APIPermissions:
    """API權限定義"""

    # 系統管理
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_MONITOR = "system:monitor"

    # 交易權限
    TRADE_READ = "trade:read"
    TRADE_WRITE = "trade:write"
    TRADE_EXECUTE = "trade:execute"

    # 分析權限
    ANALYSIS_READ = "analysis:read"
    ANALYSIS_WRITE = "analysis:write"
    ANALYSIS_ADVANCED = "analysis:advanced"

    # 策略權限
    STRATEGY_READ = "strategy:read"
    STRATEGY_WRITE = "strategy:write"
    STRATEGY_BACKTEST = "strategy:backtest"

    # 數據權限
    DATA_READ = "data:read"
    DATA_EXPORT = "data:export"

    # 風控權限
    RISK_READ = "risk:read"
    RISK_MANAGE = "risk:manage"


class StandardResponse(BaseModel):
    """標準API響應格式"""

    success: bool = Field(..., description="請求是否成功", example=True)

    data: Optional[Any] = Field(
        None, description="響應數據", example={"id": 1, "name": "example"}
    )

    error: Optional["StandardError"] = Field(
        None, description="錯誤信息（僅在失敗時存在）"
    )

    meta: Optional["ResponseMetadata"] = Field(None, description="響應元數據")

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="響應時間戳",
        example="2025 - 01 - 19T10:30:00Z",
    )


class StandardError(BaseModel):
    """標準錯誤格式"""

    code: str = Field(
        ..., description="錯誤代碼", example=APIErrorCodes.INVALID_REQUEST
    )

    message: str = Field(..., description="錯誤消息", example="請求參數無效")

    details: Optional[Dict[str, Any]] = Field(
        None,
        description="錯誤詳情",
        example={"field": "symbol", "reason": "invalid stock symbol"},
    )

    request_id: Optional[str] = Field(
        None, description="請求ID", example="req_1642594200000_123456"
    )

    stack_trace: Optional[str] = Field(None, description="堆棧跟蹤（僅開發環境）")


class ResponseMetadata(BaseModel):
    """響應元數據"""

    version: str = Field(..., description="API版本", example="v1")

    request_id: str = Field(
        ..., description="請求ID", example="req_1642594200000_123456"
    )

    processing_time: float = Field(..., description="處理時間(秒)", example=0.123)

    endpoint: str = Field(..., description="端點路徑", example="/api / v1 / stocks / 0700.hk")

    method: str = Field(..., description="HTTP方法", example="GET")

    pagination: Optional["PaginationInfo"] = Field(None, description="分頁信息")

    rate_limit: Optional["RateLimitInfo"] = Field(None, description="限流信息")


class PaginationInfo(BaseModel):
    """分頁信息"""

    page: int = Field(..., description="當前頁碼", example=1)
    page_size: int = Field(..., description="每頁大小", example=20)
    total_items: int = Field(..., description="總條目數", example=100)
    total_pages: int = Field(..., description="總頁數", example=5)
    has_next: bool = Field(..., description="是否有下一頁", example=True)
    has_prev: bool = Field(..., description="是否有上一頁", example=False)


class RateLimitInfo(BaseModel):
    """限流信息"""

    limit: int = Field(..., description="請求限制數", example=1000)
    remaining: int = Field(..., description="剩餘請求數", example=999)
    reset: int = Field(..., description="重置時間(秒)", example=60)


class APIDocumentation:
    """API文檔標準"""

    @staticmethod
    def get_openapi_tags() -> List[Dict[str, Any]]:
        """獲取OpenAPI標籤定義"""
        return [
            {"name": "認證", "description": "用戶認證和授權相關接口"},
            {"name": "系統", "description": "系統狀態和監控接口"},
            {"name": "股票數據", "description": "股票基礎數據和實時行情接口"},
            {"name": "技術分析", "description": "技術指標計算和分析接口"},
            {"name": "策略回測", "description": "量化策略開發和回測接口"},
            {"name": "交易執行", "description": "訂單執行和交易管理接口"},
            {"name": "投資組合", "description": "投資組合管理和分析接口"},
            {"name": "風險管理", "description": "風險監控和管理接口"},
            {"name": "機器學習", "description": "AI模型訓練和預測接口"},
            {"name": "數據導出", "description": "數據查詢和導出接口"},
        ]

    @staticmethod
    def get_security_schemes() -> Dict[str, Any]:
        """獲取安全認證方案"""
        return {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "輸入JWT令牌進行認證",
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X - API - Key",
                "description": "API密鑰認證",
            },
        }


class APIValidationRules:
    """API驗證規則"""

    # 股票代碼格式
    STOCK_SYMBOL_PATTERN = r"^[0 - 9]{4}\.hk$"

    # 日期格式
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%Y-%m-%dT % H:%M:%SZ"

    # 數值範圍
    PRICE_MIN = 0.0
    PRICE_MAX = 999999.99
    QUANTITY_MIN = 1
    QUANTITY_MAX = 10000000

    # 字符串長度限制
    STRATEGY_NAME_MAX_LENGTH = 100
    DESCRIPTION_MAX_LENGTH = 1000

    # 分頁限制
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100


class APIRateLimits:
    """API限流標準"""

    # 基礎限流 (每分鐘)
    BASIC_LIMIT = 100

    # 高級用戶限流 (每分鐘)
    PREMIUM_LIMIT = 1000

    # 企業用戶限流 (每分鐘)
    ENTERPRISE_LIMIT = 10000

    # 特殊接口限流
    AUTH_LIMIT = 10  # 登錄接口
    TRADE_LIMIT = 100  # 交易接口
    BACKTEST_LIMIT = 20  # 回測接口


class APICaching:
    """API緩存標準"""

    # 緩存時間 (秒)
    CACHE_DURATION = {
        "stock_quote": 5,  # 股票報價
        "market_overview": 30,  # 市場概覽
        "technical_indicators": 300,  # 技術指標
        "company_info": 3600,  # 公司信息
        "historical_data": 86400,  # 歷史數據
    }

    # 緩存鍵格式
    CACHE_KEY_PATTERNS = {
        "stock_quote": "quote:{symbol}",
        "technical_indicators": "indicators:{symbol}:{indicator}:{period}",
        "historical_data": "history:{symbol}:{start_date}:{end_date}",
    }


class APISecurity:
    """API安全標準"""

    # JWT配置
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_HOURS = 24

    # 密碼策略
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SYMBOLS = True

    # API密鑰長度
    API_KEY_LENGTH = 32

    # HTTPS要求
    REQUIRE_HTTPS = True

    # CORS配置
    CORS_ALLOWED_ORIGINS = ["https://app.codex - quant.com"]
    CORS_ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOWED_HEADERS = ["*"]
    CORS_MAX_AGE = 86400


class APIVersioning:
    """API版本管理標準"""

    # 版本策略
    VERSION_STRATEGY = "URL_PATH"  # URL_PATH, HEADER, QUERY_PARAM

    # 當前版本
    CURRENT_VERSION = "v1"

    # 支持的版本
    SUPPORTED_VERSIONS = ["v1"]

    # 版本棄用策略
    DEPRECATION_NOTICE_MONTHS = 6
    VERSION_SUPPORT_YEARS = 2

    # 版本兼容性
    BACKWARD_COMPATIBILITY = True


class APIEndpointStandards:
    """API端點設計標準"""

    # URL命名規範
    NAMING_CONVENTIONS = {
        "use_lowercase": True,
        "use_hyphens": True,
        "use_plural_nouns": True,
        "avoid_underscores": True,
        "avoid_verbs": True,  # 使用HTTP方法表示動作
    }

    # 資源命名
    RESOURCE_NAMES = {
        "stocks": "股票",
        "strategies": "策略",
        "backtests": "回測",
        "orders": "訂單",
        "portfolios": "投資組合",
        "users": "用戶",
        "alerts": "告警",
    }

    # 標準端點模式
    STANDARD_ENDPOINTS = {
        "list": "GET /{resource}",
        "get": "GET /{resource}/{id}",
        "create": "POST /{resource}",
        "update": "PUT /{resource}/{id}",
        "patch": "PATCH /{resource}/{id}",
        "delete": "DELETE /{resource}/{id}",
        "bulk_create": "POST /{resource}/bulk",
        "bulk_update": "PUT /{resource}/bulk",
        "bulk_delete": "DELETE /{resource}/bulk",
    }


class APITesting:
    """API測試標準"""

    # 測試類型
    TEST_TYPES = {
        "unit": "單元測試",
        "integration": "集成測試",
        "performance": "性能測試",
        "security": "安全測試",
        "load": "負載測試",
    }

    # 測試覆蓋率要求
    COVERAGE_REQUIREMENTS = {
        "unit_tests": 90,
        "integration_tests": 80,
        "api_coverage": 100,  # 所有API端點都應有測試
    }

    # 性能要求
    PERFORMANCE_REQUIREMENTS = {
        "response_time_p95": 2000,  # 95 % 請求在2秒內響應
        "response_time_p99": 5000,  # 99 % 請求在5秒內響應
        "throughput_min": 100,  # 最小吞吐量 (請求 / 秒)
        "error_rate_max": 0.01,  # 最大錯誤率 (1%)
    }


# 便利函數
def create_success_response(
    data: Any,
    request_id: str,
    processing_time: float,
    endpoint: str,
    method: str,
    pagination: Optional[PaginationInfo] = None,
    rate_limit: Optional[RateLimitInfo] = None,
) -> StandardResponse:
    """創建成功響應"""
    return StandardResponse(
        success=True,
        data=data,
        meta=ResponseMetadata(
            version=APIVersioning.CURRENT_VERSION,
            request_id=request_id,
            processing_time=processing_time,
            endpoint=endpoint,
            method=method,
            pagination=pagination,
            rate_limit=rate_limit,
        ),
    )


def create_error_response(
    error_code: str,
    error_message: str,
    request_id: str,
    processing_time: float,
    endpoint: str,
    method: str,
    error_details: Optional[Dict[str, Any]] = None,
) -> StandardResponse:
    """創建錯誤響應"""
    return StandardResponse(
        success=False,
        error=StandardError(
            code=error_code,
            message=error_message,
            details=error_details,
            request_id=request_id,
        ),
        meta=ResponseMetadata(
            version=APIVersioning.CURRENT_VERSION,
            request_id=request_id,
            processing_time=processing_time,
            endpoint=endpoint,
            method=method,
        ),
    )


def validate_user_permission(user_roles: List[str], required_permission: str) -> bool:
    """驗證用戶權限"""
    role_permissions = {
        UserRole.ADMIN: [APIPermissions.SYSTEM_ADMIN, APIPermissions.TRADE_EXECUTE],
        UserRole.TRADER: [
            APIPermissions.TRADE_READ,
            APIPermissions.TRADE_WRITE,
            APIPermissions.TRADE_EXECUTE,
        ],
        UserRole.ANALYST: [
            APIPermissions.ANALYSIS_READ,
            APIPermissions.ANALYSIS_WRITE,
            APIPermissions.STRATEGY_BACKTEST,
        ],
        UserRole.VIEWER: [
            APIPermissions.TRADE_READ,
            APIPermissions.ANALYSIS_READ,
            APIPermissions.DATA_READ,
        ],
    }

    for role in user_roles:
        if required_permission in role_permissions.get(role, []):
            return True

    return False
