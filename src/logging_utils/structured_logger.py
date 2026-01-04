"""
Structured Logger
結構化日誌記錄器

提供符合 ELK Stack 標準的結構化日誌記錄功能。

Usage:
    ```python
    from src.logging_utils import StructuredLogger, get_logger

    logger = get_logger("cbsc-trading", "production")

    # Log events
    logger.log_event(LogLevel.INFO, "user_login", user_id="123", ip="192.168.1.1")

    # Log errors
    try:
        ...
    except Exception as e:
        logger.log_error(e, context={"user_id": "123"})
    ```
"""

import json
import logging
import time
import uuid
import traceback
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict


class LogLevel(Enum):
    """日誌級別枚舉"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SecurityEventType(Enum):
    """安全事件類型"""
    LOGIN_ATTEMPT = "login_attempt"
    LOGOUT = "logout"
    DATA_ACCESS = "data_access"
    CONFIG_CHANGE = "config_change"
    PERMISSION_CHANGE = "permission_change"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    STRATEGY_ACCESS = "strategy_access"
    TRADE_EXECUTION = "trade_execution"


@dataclass
class SecurityAuditLog:
    """安全審計日誌"""
    timestamp: float
    event_type: SecurityEventType
    user_id: str
    user_ip: str
    action: str
    resource: str
    result: str
    details: Dict[str, Any]
    session_id: str
    risk_score: float = 0.0


class StructuredLogger:
    """
    結構化日誌記錄器

    提供符合 ELK Stack 標準的結構化日誌記錄功能，支持：
    - JSON 格式日誌輸出
    - 自動添加關聯 ID
    - 結構化查詢支持
    - ELK Stack 集成

    Attributes:
        app_name: 應用程序名稱
        environment: 環境名稱 (development/staging/production)
    """

    def __init__(self, app_name: str, environment: str = "production"):
        self.app_name = app_name
        self.environment = environment
        self.logger = logging.getLogger(app_name)
        self._setup_logger()

        # ELK integration
        self._elk_enabled = False
        self._elasticsearch_client = None

    def _setup_logger(self):
        """設置日誌記錄器"""
        # Clear existing handlers
        self.logger.handlers.clear()

        # Console handler with JSON formatting
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

        # Set log level based on environment
        if self.environment == "development":
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def log_event(self,
                  level: LogLevel,
                  event_type: str,
                  message: str = None,
                  **kwargs):
        """
        記錄事件日誌

        Args:
            level: 日誌級別
            event_type: 事件類型
            message: 日誌消息（可選）
            **kwargs: 額外的結構化字段
        """
        log_entry = {
            "timestamp": time.time(),
            "app": self.app_name,
            "environment": self.environment,
            "level": level.value,
            "event_type": event_type,
            "message_id": str(uuid.uuid4()),
            **kwargs
        }

        if message:
            log_entry["message"] = message

        # Log to console
        self.logger.log(
            getattr(logging, level.value),
            json.dumps(log_entry, ensure_ascii=False, default=str)
        )

        # Send to ELK
        self._send_to_elk(log_entry)

    def log_security_event(self, audit_log: SecurityAuditLog):
        """
        記錄安全審計日誌

        Args:
            audit_log: 安全審計日誌對象
        """
        log_entry = {
            "timestamp": audit_log.timestamp,
            "app": self.app_name,
            "environment": self.environment,
            "level": "INFO",
            "event_type": "security_audit",
            "message_id": str(uuid.uuid4()),
            **asdict(audit_log)
        }

        # Convert enum to string
        log_entry["event_type_enum"] = audit_log.event_type.value

        self.logger.info(json.dumps(log_entry, ensure_ascii=False, default=str))
        self._send_to_elk(log_entry)

    def log_performance_metric(self,
                                metric_name: str,
                                value: float,
                                unit: str = None,
                                **context):
        """
        記錄性能指標

        Args:
            metric_name: 指標名稱
            value: 指標值
            unit: 單位（可選）
            **context: 額外上下文信息
        """
        log_entry = {
            "timestamp": time.time(),
            "app": self.app_name,
            "environment": self.environment,
            "level": "INFO",
            "event_type": "performance_metric",
            "metric_name": metric_name,
            "metric_value": value,
            "metric_unit": unit,
            "message_id": str(uuid.uuid4()),
            **context
        }

        self.logger.info(json.dumps(log_entry, ensure_ascii=False, default=str))
        self._send_to_elk(log_entry)

    def log_error(self,
                  error: Exception,
                  context: Dict[str, Any] = None,
                  level: LogLevel = LogLevel.ERROR):
        """
        記錄錯誤日誌

        Args:
            error: 異常對象
            context: 上下文信息
            level: 日誌級別
        """
        log_entry = {
            "timestamp": time.time(),
            "app": self.app_name,
            "environment": self.environment,
            "level": level.value,
            "event_type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
            "message_id": str(uuid.uuid4()),
            "context": context or {}
        }

        self.logger.log(
            getattr(logging, level.value),
            json.dumps(log_entry, ensure_ascii=False, default=str)
        )
        self._send_to_elk(log_entry)

    def log_http_request(self,
                         method: str,
                         path: str,
                         status_code: int,
                         duration_ms: float,
                         user_id: str = None,
                         **kwargs):
        """
        記錄 HTTP 請求

        Args:
            method: HTTP 方法
            path: 請求路徑
            status_code: 響應狀態碼
            duration_ms: 請求耗時（毫秒）
            user_id: 用戶 ID（可選）
            **kwargs: 額外字段
        """
        self.log_event(
            LogLevel.INFO,
            "http_request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            **kwargs
        )

    def log_db_query(self,
                     database: str,
                     operation: str,
                     table: str,
                     duration_ms: float,
                     rows_affected: int = None,
                     **kwargs):
        """
        記錄數據庫查詢

        Args:
            database: 數據庫名稱
            operation: 操作類型 (SELECT/INSERT/UPDATE/DELETE)
            table: 表名
            duration_ms: 查詢耗時（毫秒）
            rows_affected: 影響行數
            **kwargs: 額外字段
        """
        self.log_event(
            LogLevel.INFO,
            "db_query",
            database=database,
            operation=operation,
            table=table,
            duration_ms=duration_ms,
            rows_affected=rows_affected,
            **kwargs
        )

    def log_cache_operation(self,
                            cache_layer: str,
                            operation: str,
                            key: str,
                            hit: bool,
                            duration_ms: float = None,
                            **kwargs):
        """
        記錄緩存操作

        Args:
            cache_layer: 緩存層 (memory/redis)
            operation: 操作類型 (get/set/delete)
            key: 緩存鍵
            hit: 是否命中
            duration_ms: 操作耗時（毫秒）
            **kwargs: 額外字段
        """
        self.log_event(
            LogLevel.DEBUG,
            "cache_operation",
            cache_layer=cache_layer,
            operation=operation,
            key=key,
            hit=hit,
            duration_ms=duration_ms,
            **kwargs
        )

    def log_strategy_execution(self,
                                strategy_type: str,
                                strategy_id: str,
                                status: str,
                                duration_seconds: float,
                                signals: int = 0,
                                trades: int = 0,
                                **kwargs):
        """
        記錄策略執行

        Args:
            strategy_type: 策略類型
            strategy_id: 策略 ID
            status: 執行狀態
            duration_seconds: 執行耗時（秒）
            signals: 信號數量
            trades: 交易數量
            **kwargs: 額外字段
        """
        self.log_event(
            LogLevel.INFO,
            "strategy_execution",
            strategy_type=strategy_type,
            strategy_id=strategy_id,
            status=status,
            duration_seconds=duration_seconds,
            signals=signals,
            trades=trades,
            **kwargs
        )

    def _send_to_elk(self, log_entry: Dict[str, Any]):
        """
        發送日誌到 ELK Stack

        Args:
            log_entry: 日誌條目
        """
        if not self._elk_enabled or self._elasticsearch_client is None:
            return

        try:
            # Index format: cbsc-logs-YYYY.MM.DD
            index_name = f"cbsc-logs-{time.strftime('%Y.%m.%d', time.gmtime(log_entry['timestamp']))}"
            self._elasticsearch_client.index(index=index_name, document=log_entry)
        except Exception as e:
            # Don't log errors from logging to avoid infinite loops
            pass

    def enable_elk(self, elasticsearch_hosts: list, index_prefix: str = "cbsc-logs"):
        """
        啟用 ELK Stack 集成

        Args:
            elasticsearch_hosts: Elasticsearch 主機列表
            index_prefix: 索引前綴
        """
        try:
            from elasticsearch import Elasticsearch
            self._elasticsearch_client = Elasticsearch(elasticsearch_hosts)
            self._elk_enabled = True
        except ImportError:
            self.logger.warning("elasticsearch-py not installed. ELK integration disabled.")


class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""

    def format(self, record):
        # If record.msg is already JSON, return as-is
        try:
            json.loads(record.msg)
            return record.msg
        except (json.JSONDecodeError, TypeError):
            pass

        # Otherwise, format as JSON
        log_entry = {
            "timestamp": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        if hasattr(record, 'exc_info') and record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


# Global singleton
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(app_name: str, environment: str = "production") -> StructuredLogger:
    """
    獲取結構化日誌記錄器單例

    Args:
        app_name: 應用程序名稱
        environment: 環境名稱

    Returns:
        StructuredLogger 實例
    """
    key = f"{app_name}:{environment}"
    if key not in _loggers:
        _loggers[key] = StructuredLogger(app_name, environment)
    return _loggers[key]
