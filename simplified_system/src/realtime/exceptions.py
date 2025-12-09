#!/usr/bin/env python3
"""
Phase 3 Real-time Infrastructure Exception Hierarchy
Phase 3 實時基礎設施異常層次
提供精確的錯誤處理和類型安全的異常管理
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ErrorContext:
    """錯誤上下文信息"""
    operation: str
    component: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

class RealtimeInfraError(Exception):
    """Phase 3 實時基礎設施異常基類"""

    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.context = context or ErrorContext(
            operation="unknown",
            component="unknown"
        )
        self.cause = cause
        self.timestamp = datetime.now()

        # 自動記錄異常
        self._log_exception()

    def _log_exception(self) -> None:
        """記錄異常日誌"""
        log_data = {
            "error_type": self.__class__.__name__,
            "error_message": self.message,
            "operation": self.context.operation,
            "component": self.context.component,
            "user_id": self.context.user_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.context.metadata
        }

        if self.cause:
            log_data["cause"] = str(self.cause)

        logger.error(f"Realtime Infrastructure Error: {self.message}", extra=log_data)

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": {
                "operation": self.context.operation,
                "component": self.context.component,
                "user_id": self.context.user_id,
                "timestamp": self.context.timestamp.isoformat(),
                "metadata": self.context.metadata
            },
            "timestamp": self.timestamp.isoformat(),
            "cause": str(self.cause) if self.cause else None
        }

class WebSocketError(RealtimeInfraError):
    """WebSocket相關錯誤"""
    pass

class WebSocketConnectionError(WebSocketError):
    """WebSocket連接錯誤"""
    pass

class WebSocketMessageError(WebSocketError):
    """WebSocket消息錯誤"""
    pass

class WebSocketAuthenticationError(WebSocketError):
    """WebSocket身份驗證錯誤"""
    pass

class WebSocketAuthorizationError(WebSocketError):
    """WebSocket授權錯誤"""
    pass

class WebSocketRateLimitError(WebSocketError):
    """WebSocket速率限制錯誤"""
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after

class DataPipelineError(RealtimeInfraError):
    """數據管道錯誤"""
    pass

class DataValidationError(DataPipelineError):
    """數據驗證錯誤"""
    def __init__(
        self,
        message: str,
        validation_errors: List[str] = None,
        invalid_fields: List[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.validation_errors = validation_errors or []
        self.invalid_fields = invalid_fields or []

class DataTransformationError(DataPipelineError):
    """數據轉換錯誤"""
    pass

class DataAggregationError(DataPipelineError):
    """數據聚合錯誤"""
    pass

class CacheError(RealtimeInfraError):
    """緩存相關錯誤"""
    pass

class CacheConnectionError(CacheError):
    """緩存連接錯誤"""
    pass

class CacheSerializationError(CacheError):
    """緩存序列化錯誤"""
    pass

class CacheTimeoutError(CacheError):
    """緩存超時錯誤"""
    def __init__(self, message: str, timeout_seconds: float = None, **kwargs):
        super().__init__(message, **kwargs)
        self.timeout_seconds = timeout_seconds

class CacheKeyError(CacheError):
    """緩存鍵錯誤"""
    def __init__(self, message: str, key: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.key = key

class ValidationError(RealtimeInfraError):
    """通用驗證錯誤"""
    def __init__(
        self,
        message: str,
        field: str = None,
        value: Any = None,
        allowed_values: List[Any] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.field = field
        self.value = value
        self.allowed_values = allowed_values or []

class ConfigurationError(RealtimeInfraError):
    """配置錯誤"""
    pass

class ResourceExhaustionError(RealtimeInfraError):
    """資源耗盡錯誤"""
    def __init__(
        self,
        message: str,
        resource_type: str = None,
        current_usage: int = None,
        max_limit: int = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.resource_type = resource_type
        self.current_usage = current_usage
        self.max_limit = max_limit

class ConcurrencyError(RealtimeInfraError):
    """併發錯誤"""
    pass

class DeadlockError(ConcurrencyError):
    """死鎖錯誤"""
    pass

class TimeoutError(RealtimeInfraError):
    """超時錯誤"""
    def __init__(
        self,
        message: str,
        timeout_seconds: float = None,
        operation: str = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.timeout_seconds = timeout_seconds
        self.operation = operation

class ExternalServiceError(RealtimeInfraError):
    """外部服務錯誤"""
    def __init__(
        self,
        message: str,
        service_name: str = None,
        service_url: str = None,
        status_code: int = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.service_name = service_name
        self.service_url = service_url
        self.status_code = status_code

class DataQualityError(RealtimeInfraError):
    """數據質量錯誤"""
    def __init__(
        self,
        message: str,
        quality_issues: List[str] = None,
        affected_records: int = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.quality_issues = quality_issues or []
        self.affected_records = affected_records

class MonitoringError(RealtimeInfraError):
    """監控相關錯誤"""
    pass

class MetricsCollectionError(MonitoringError):
    """指標收集錯誤"""
    pass

class HealthCheckError(MonitoringError):
    """健康檢查錯誤"""
    def __init__(
        self,
        message: str,
        component_name: str = None,
        health_status: str = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.component_name = component_name
        self.health_status = health_status

# Error handling utilities
class ErrorRecovery:
    """錯誤恢復工具類"""

    @staticmethod
    def should_retry(exception: Exception, attempt: int, max_attempts: int = 3) -> bool:
        """判斷是否應該重試"""
        if attempt >= max_attempts:
            return False

        # 不重試的錯誤類型
        non_retryable_errors = (
            ValidationError,
            AuthenticationError,
            AuthorizationError,
            ConfigurationError
        )

        if isinstance(exception, non_retryable_errors):
            return False

        # 可重試的錯誤類型
        retryable_errors = (
            TimeoutError,
            ConnectionError,
            CacheTimeoutError,
            ExternalServiceError
        )

        return isinstance(exception, retryable_errors)

    @staticmethod
    def get_retry_delay(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """計算重試延遲（指數退避）"""
        delay = base_delay * (2 ** attempt)
        return min(delay, max_delay)

# Error context builders
def create_websocket_context(
    operation: str,
    user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
    **kwargs
) -> ErrorContext:
    """創建WebSocket錯誤上下文"""
    metadata = kwargs.get("metadata", {})
    if client_ip:
        metadata["client_ip"] = client_ip

    return ErrorContext(
        operation=operation,
        component="websocket_server",
        user_id=user_id,
        metadata=metadata
    )

def create_cache_context(
    operation: str,
    key: Optional[str] = None,
    cache_type: str = "redis",
    **kwargs
) -> ErrorContext:
    """創建緩存錯誤上下文"""
    metadata = kwargs.get("metadata", {})
    if key:
        metadata["cache_key"] = key
    metadata["cache_type"] = cache_type

    return ErrorContext(
        operation=operation,
        component="redis_cache",
        metadata=metadata
    )

def create_pipeline_context(
    operation: str,
    data_source: Optional[str] = None,
    **kwargs
) -> ErrorContext:
    """創建數據管道錯誤上下文"""
    metadata = kwargs.get("metadata", {})
    if data_source:
        metadata["data_source"] = data_source

    return ErrorContext(
        operation=operation,
        component="data_pipeline",
        metadata=metadata
    )

# Exception testing utilities
def create_test_context(operation: str = "test_operation") -> ErrorContext:
    """創建測試用錯誤上下文"""
    return ErrorContext(
        operation=operation,
        component="test",
        metadata={"test": True}
    )

# Testing function
def test_exception_hierarchy():
    """測試異常層次"""
    print("Testing Exception Hierarchy...")

    # 測試基礎異常
    try:
        base_error = RealtimeInfraError("Test error")
        print(f"  RealtimeInfraError: {base_error.message}")
    except Exception as e:
        print(f"  Error creating base exception: {e}")

    # 測試WebSocket異常
    try:
        ws_error = WebSocketConnectionError(
            "Connection failed",
            context=create_websocket_context("connect", "user_123", "127.0.0.1")
        )
        print(f"  WebSocketConnectionError: {ws_error.message}")
        print(f"  Context operation: {ws_error.context.operation}")
    except Exception as e:
        print(f"  Error creating WebSocket exception: {e}")

    # 測試緩存異常
    try:
        cache_error = CacheTimeoutError(
            "Cache timeout",
            timeout_seconds=5.0,
            context=create_cache_context("get", "test_key")
        )
        print(f"  CacheTimeoutError: {cache_error.message}")
        print(f"  Timeout seconds: {cache_error.timeout_seconds}")
    except Exception as e:
        print(f"  Error creating cache exception: {e}")

    # 測試驗證異常
    try:
        validation_error = ValidationError(
            "Invalid field value",
            field="symbol",
            value="INVALID",
            allowed_values=["0700.HK", "0941.HK"]
        )
        print(f"  ValidationError: {validation_error.message}")
        print(f"  Field: {validation_error.field}")
        print(f"  Value: {validation_error.value}")
    except Exception as e:
        print(f"  Error creating validation exception: {e}")

    print("Exception hierarchy test completed!")

if __name__ == "__main__":
    test_exception_hierarchy()