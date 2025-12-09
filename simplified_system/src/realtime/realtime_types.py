#!/usr/bin/env python3
"""
Phase 3 Real-time Infrastructure Type Definitions
Phase 3 實時基礎設施類型定義
提供完整的類型提示和類型安全的數據結構
"""

from typing import (
    Dict, List, Optional, Any, Union, Tuple, Callable,
    Set, FrozenSet, Sequence, Mapping, MutableMapping,
    Iterator, AsyncIterator, Awaitable, TypeVar, Generic,
    Protocol, runtime_checkable
)
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import asyncio

# Generic Type Variables
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')
R = TypeVar('R')

# Common Types
JSONType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
MessageHandler = Callable[[Dict[str, Any]], Awaitable[None]]
WebSocketCallback = Callable[[str], None]

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
    high: Optional[float] = None
    low: Optional[float] = None
    change: float = 0.0
    change_percent: float = 0.0

@dataclass
class MarketData:
    """市場數據類型"""
    timestamp: datetime
    hsi_index: float
    hsi_change: float
    market_sentiment: str
    trading_volume: float
    top_gainers: List[str]
    top_losers: List[str]

@dataclass
class SignalData:
    """信號數據類型"""
    signal_type: str
    symbol: str
    timestamp: datetime
    strength: float
    direction: str  # 'buy', 'sell', 'hold'
    confidence: float
    metadata: Dict[str, Any]

# Cache Types
@dataclass
class CacheEntry:
    """緩存條目類型"""
    key: str
    value: Any
    ttl: Optional[int] = None
    created_at: datetime = None
    accessed_at: datetime = None
    access_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.accessed_at is None:
            self.accessed_at = datetime.now()

# Connection Types
@dataclass
class ConnectionStats:
    """連接統計類型"""
    total_connections: int
    current_connections: int
    authenticated_connections: int
    messages_sent: int
    messages_received: int
    last_update: datetime

# WebSocket Types
class WebSocketState(Enum):
    """WebSocket連接狀態"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"

@dataclass
class WebSocketMessage:
    """WebSocket消息類型"""
    message_type: str
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None

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
        if self.session_id:
            message_dict["session_id"] = self.session_id
        return json.dumps(message_dict, default=str)

# Pipeline Types
class PipelineStage(Enum):
    """數據管道階段"""
    INGESTION = "ingestion"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    AGGREGATION = "aggregation"
    DISTRIBUTION = "distribution"
    STORAGE = "storage"

@dataclass
class PipelineMetrics:
    """管道指標類型"""
    stage: PipelineStage
    processing_time_ms: float
    records_processed: int
    errors_count: int
    throughput_per_second: float
    timestamp: datetime

@dataclass
class DataQualityMetrics:
    """數據質量指標類型"""
    completeness: float  # 0-1
    accuracy: float     # 0-1
    timeliness: float   # 0-1
    consistency: float  # 0-1
    validity: float     # 0-1
    total_score: float  # 0-1

# Validation Types
@dataclass
class ValidationResult:
    """驗證結果類型"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    validated_fields: List[str]
    timestamp: datetime

    def has_errors(self) -> bool:
        """檢查是否有錯誤"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """檢查是否有警告"""
        return len(self.warnings) > 0

# Monitoring Types
class HealthStatus(Enum):
    """健康狀態"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    """健康檢查結果"""
    component: str
    status: HealthStatus
    response_time_ms: float
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]

# Configuration Types
@dataclass
class WebSocketConfig:
    """WebSocket配置類型"""
    host: str = "localhost"
    port: int = 8000
    max_connections: int = 1000
    heartbeat_interval: int = 30
    message_timeout: int = 60
    compression_enabled: bool = True

@dataclass
class CacheConfig:
    """緩存配置類型"""
    default_ttl: int = 300
    max_connections: int = 20
    socket_timeout: int = 5
    health_check_interval: int = 30
    compression_threshold: int = 1024

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

    def map(self, func: Callable[[T], R]) -> 'Result[R]':
        """映射成功值"""
        if self.is_ok() and self.value is not None:
            try:
                return Result.ok(func(self.value))
            except Exception as e:
                return Result.error(e)
        return Result.error(self.error or Exception("No value to map"), self.message)

# Async Result Type
@dataclass
class AsyncResult(Generic[T]):
    """異步Result類型"""
    success: bool
    value: Optional[T] = None
    error: Optional[Exception] = None
    message: Optional[str] = None

    @classmethod
    def ok(cls, value: T) -> 'AsyncResult[T]':
        """創建成功的AsyncResult"""
        return cls(success=True, value=value)

    @classmethod
    def error(cls, error: Exception, message: Optional[str] = None) -> 'AsyncResult[T]':
        """創建錯誤的AsyncResult"""
        return cls(success=False, error=error, message=message)

# Protocol definitions for type safety
@runtime_checkable
class CacheProtocol(Protocol):
    """緩存協議"""
    async def get(self, key: str) -> Optional[Any]: ...
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool: ...
    async def delete(self, key: str) -> bool: ...
    async def exists(self, key: str) -> bool: ...

@runtime_checkable
class DataProcessorProtocol(Protocol):
    """數據處理器協議"""
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    def validate_input(self, data: Dict[str, Any]) -> bool: ...

@runtime_checkable
class MessageHandlerProtocol(Protocol):
    """消息處理器協議"""
    async def handle_message(self, message: WebSocketMessage) -> None: ...
    def can_handle(self, message_type: str) -> bool: ...

# Type aliases for better readability
PriceDataDict = Dict[str, Union[str, int, float, datetime]]
MarketDataDict = Dict[str, Union[float, str, List[str]]]
CacheKey = str
CacheValue = Union[str, bytes, Dict[str, Any]]

# Complex type definitions
type ConfigDict = Dict[str, Any]
type SymbolList = List[str]
type PermissionList = List[str]
type ErrorMessage = str
type LogLevel = str

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
        validated_fields=[],
        timestamp=datetime.now()
    )

# Generic type utilities
def safe_get(dictionary: Mapping[K, V], key: K, default: Optional[V] = None) -> Optional[V]:
    """安全獲取字典值"""
    return dictionary.get(key, default)

def safe_cast(value: Any, target_type: type[T]) -> Optional[T]:
    """安全類型轉換"""
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return None

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
        success_result = Result.ok("test_value")
        print(f"  Result.ok: {success_result.is_ok()}")

        error_result = Result.error(Exception("test error"))
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