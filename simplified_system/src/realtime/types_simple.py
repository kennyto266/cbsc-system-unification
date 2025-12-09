#!/usr/bin/env python3
"""
Simplified Phase 3 Type Definitions
簡化的Phase 3類型定義
避免循環導入問題
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Callable, Awaitable, TypeVar, Generic
from enum import Enum

# Generic Type Variables
T = TypeVar('T')

# Result Type (Functional Programming Pattern)
@dataclass
class Result(Generic[T]):
    """Result類型 - 函數式編程錯誤處理"""
    success: bool
    value: Optional[T] = None
    error: Optional[Exception] = None
    message: Optional[str] = None

    @classmethod
    def ok(cls, value: T) -> 'Result[T]':
        """創建成功的Result"""
        return cls(success=True, value=value)

    @classmethod
    def error(cls, error: Exception, message: Optional[str] = None) -> 'Result[T]':
        """創建錯誤的Result"""
        return cls(success=False, error=error, message=message)

    def is_ok(self) -> bool:
        """檢查是否成功"""
        return self.success

    def is_error(self) -> bool:
        """檢查是否失敗"""
        return not self.success

    def unwrap(self) -> T:
        """獲取成功值，如果失敗則拋出異常"""
        if self.is_ok() and self.value is not None:
            return self.value
        raise self.error or Exception("Result contains no value")

    def unwrap_or(self, default: T) -> T:
        """獲取成功值，失敗時返回默認值"""
        return self.value if self.is_ok() and self.value is not None else default

# Data Types
@dataclass
class RealtimePriceData:
    """實時價格數據類型"""
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    bid: Optional[float] = None
    ask: Optional[float] = None
    change: float = 0.0
    change_percent: float = 0.0

@dataclass
class WebSocketMessage:
    """WebSocket消息類型"""
    message_type: str
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None

    def to_json(self) -> str:
        """轉換為JSON字符串"""
        import json
        message_dict = {
            "type": self.message_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }
        if self.user_id:
            message_dict["user_id"] = self.user_id
        return json.dumps(message_dict, default=str)

# Enums
class WebSocketState(Enum):
    """WebSocket連接狀態"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    DISCONNECTED = "disconnected"
    ERROR = "error"

class HealthStatus(Enum):
    """健康狀態"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

# Validation Types
@dataclass
class ValidationResult:
    """驗證結果類型"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    timestamp: datetime

    def has_errors(self) -> bool:
        """檢查是否有錯誤"""
        return len(self.errors) > 0

# Configuration Types
@dataclass
class WebSocketConfig:
    """WebSocket配置類型"""
    host: str = "localhost"
    port: int = 8000
    max_connections: int = 1000
    heartbeat_interval: int = 30

@dataclass
class CacheConfig:
    """緩存配置類型"""
    default_ttl: int = 300
    max_connections: int = 20
    socket_timeout: int = 5

# Type aliases
PriceDataDict = Dict[str, Union[str, int, float, datetime]]
MessageHandler = Callable[[Dict[str, Any]], Awaitable[None]]
CacheKey = str
CacheValue = Union[str, bytes, Dict[str, Any]]

# Function signatures with complete typing
def create_websocket_message(
    message_type: str,
    data: Dict[str, Any],
    user_id: Optional[str] = None
) -> WebSocketMessage:
    """創建WebSocket消息"""
    return WebSocketMessage(
        message_type=message_type,
        data=data,
        timestamp=datetime.now(),
        user_id=user_id
    )

def create_validation_result(
    is_valid: bool,
    errors: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None
) -> ValidationResult:
    """創建驗證結果"""
    return ValidationResult(
        is_valid=is_valid,
        errors=errors or [],
        warnings=warnings or [],
        timestamp=datetime.now()
    )

# Type checking utilities
def is_valid_symbol(symbol: str) -> bool:
    """檢查股票代碼是否有效"""
    return (
        isinstance(symbol, str) and
        3 <= len(symbol) <= 10 and
        symbol.replace('.', '').replace('-', '').isalnum()
    )

def is_valid_price(price: Any) -> bool:
    """檢查價格是否有效"""
    return (
        isinstance(price, (int, float)) and
        price > 0 and
        not isinstance(price, bool)
    )

def is_valid_volume(volume: Any) -> bool:
    """檢查成交量是否有效"""
    return (
        isinstance(volume, int) and
        volume >= 0 and
        not isinstance(volume, bool)
    )

# Testing function
def test_type_definitions():
    """測試類型定義"""
    print("Testing Type Definitions...")

    # 測試Result類型
    try:
        success_result: Result[str] = Result.ok("test_value")
        print(f"  Result.ok: {success_result.is_ok()}")

        error_result: Result[str] = Result.error(Exception("test error"))
        print(f"  Result.error: {error_result.is_error()}")

        mapped_result = success_result.map(str.upper)
        print(f"  Result.map: {mapped_result.unwrap()}")

    except Exception as e:
        print(f"  Error testing Result type: {e}")

    # 測試數據類型
    try:
        price_data = RealtimePriceData(
            symbol="0700.HK",
            timestamp=datetime.now(),
            price=300.5,
            volume=15000
        )
        print(f"  RealtimePriceData: {price_data.symbol} @ {price_data.price}")

    except Exception as e:
        print(f"  Error testing data types: {e}")

    # 測試消息類型
    try:
        message = WebSocketMessage(
            message_type="subscription",
            data={"symbols": ["0700.HK"]},
            timestamp=datetime.now()
        )
        json_data = message.to_json()
        print(f"  WebSocketMessage JSON: {len(json_data)} chars")

    except Exception as e:
        print(f"  Error testing message type: {e}")

    # 測試類型檢查
    try:
        print(f"  Valid symbol test: {is_valid_symbol('0700.HK')}")
        print(f"  Invalid symbol test: {is_valid_symbol('INVALID SYMBOL!')}")
        print(f"  Valid price test: {is_valid_price(300.5)}")
        print(f"  Invalid price test: {is_valid_price(-10)}")

    except Exception as e:
        print(f"  Error testing type checks: {e}")

    print("Type definitions test completed!")

if __name__ == "__main__":
    test_type_definitions()