"""
Structured Logger for Observability

Provides structured logging with correlation IDs, user actions, and
consistent log formatting for observability.
"""

import json
import logging
import sys
import threading
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional


class ObservabilityFormatter(logging.Formatter):
    """Custom formatter for structured logs"""

    def format(self, record: logging.LogRecord) -> str:
        # Add timestamp if not present
        if not hasattr(record, "timestamp"):
            record.timestamp = datetime.utcnow().isoformat()

        # Create structured log entry
        log_entry = {
            "timestamp": record.timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "user_action"):
            log_entry["user_action"] = record.user_action
        if hasattr(record, "trace_id"):
            log_entry["trace_id"] = record.trace_id
        if hasattr(record, "span_id"):
            log_entry["span_id"] = record.span_id
        if hasattr(record, "execution_time_ms"):
            log_entry["execution_time_ms"] = record.execution_time_ms
        if hasattr(record, "memory_usage_mb"):
            log_entry["memory_usage_mb"] = record.memory_usage_mb

        # Add any extra fields from extra dict
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
                "timestamp",
            ] and not key.startswith("_"):
                log_entry[key] = value

        # Format as JSON
        return json.dumps(log_entry, default=str)


class ObservabilityLogger:
    """Wrapper around Python logger for structured logging"""

    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Add handler if not already added
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(ObservabilityFormatter())
            self.logger.addHandler(handler)

        # Thread - local storage for correlation ID
        self._local = threading.local()

    def _get_correlation_id(self) -> Optional[str]:
        """Get correlation ID from thread - local storage"""
        return getattr(self._local, "correlation_id", None)

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID in thread - local storage"""
        self._local.correlation_id = correlation_id

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log info message with structured data"""
        self._log(logging.INFO, message, extra)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message with structured data"""
        self._log(logging.WARNING, message, extra)

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log error message with structured data"""
        self._log(logging.ERROR, message, extra)

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message with structured data"""
        self._log(logging.DEBUG, message, extra)

    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log critical message with structured data"""
        self._log(logging.CRITICAL, message, extra)

    def _log(
        self, level: int, message: str, extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """Internal log method"""
        if extra is None:
            extra = {}

        # Get correlation ID from context
        correlation_id = self._get_correlation_id()
        if correlation_id:
            extra["correlation_id"] = correlation_id

        # Add timestamp
        extra["timestamp"] = datetime.utcnow().isoformat()

        # Log with extra data
        self.logger.log(level, message, extra=extra)

    def with_correlation_id(self, correlation_id: str):
        """Context manager for setting correlation ID"""
        return CorrelationIdContext(self, correlation_id)


class CorrelationIdContext:
    """Context manager for correlation ID"""

    def __init__(self, logger: ObservabilityLogger, correlation_id: str):
        self.logger = logger
        self.correlation_id = correlation_id
        self.old_correlation_id = None

    def __enter__(self):
        self.old_correlation_id = self.logger._get_correlation_id()
        self.logger.set_correlation_id(self.correlation_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.old_correlation_id:
            self.logger.set_correlation_id(self.old_correlation_id)
        else:
            # Clear the correlation ID
            self.logger._local.correlation_id = None


# Global logger instances cache
_loggers: Dict[str, ObservabilityLogger] = {}
_lock = threading.RLock()


def get_observability_logger(name: str) -> ObservabilityLogger:
    """Get or create an observability logger"""
    with _lock:
        if name not in _loggers:
            _loggers[name] = ObservabilityLogger(name)
        return _loggers[name]


# Convenience decorators
def log_entry_exit(func):
    """Decorator to log function entry and exit"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_observability_logger(func.__module__)
        logger.info(
            f"Entering {func.__name__}",
            extra={
                "function": func.__name__,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()),
            },
        )
        try:
            result = func(*args, **kwargs)
            logger.info(
                f"Exiting {func.__name__}",
                extra={"function": func.__name__, "status": "success"},
            )
            return result
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}",
                extra={
                    "function": func.__name__,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "status": "error",
                },
            )
            raise

    return wrapper


def log_performance(func):
    """Decorator to log function performance"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        import time

        start_time = time.time()

        logger = get_observability_logger(func.__module__)

        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000

            logger.info(
                f"Function {func.__name__} completed",
                extra={
                    "function": func.__name__,
                    "execution_time_ms": execution_time,
                    "status": "success",
                },
            )
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000

            logger.error(
                f"Function {func.__name__} failed",
                extra={
                    "function": func.__name__,
                    "execution_time_ms": execution_time,
                    "error": str(e),
                    "status": "error",
                },
            )
            raise

    return wrapper
