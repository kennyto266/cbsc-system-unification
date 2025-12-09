"""
統一日誌記錄系統
Unified Logging System for Hong Kong Quantitative Trading System

This module provides structured logging with performance monitoring, correlation IDs,
and consistent formatting across the entire trading system.
"""

import logging
import logging.handlers
import sys
import time
import traceback
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Dict, Any, Optional, Union
from uuid import uuid4

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    print("Warning: structlog not available, using standard logging")

from .config import get_settings


class PerformanceLogger:
    """Performance monitoring and logging utility."""

    def __init__(self, logger: Union[logging.Logger, 'structlog.stdlib.BoundLogger']):
        self.logger = logger
        self.start_time = None
        self.operation_name = None

    def start(self, operation_name: str):
        """Start performance timing."""
        self.operation_name = operation_name
        self.start_time = time.perf_counter()
        self.logger.info(
            "Operation started",
            operation=operation_name,
            event_type="performance_start"
        )

    def end(self, success: bool = True, **kwargs):
        """End performance timing and log results."""
        if self.start_time is None:
            return

        duration = time.perf_counter() - self.start_time
        status = "success" if success else "failure"

        log_data = {
            "operation": self.operation_name,
            "duration_seconds": round(duration, 4),
            "status": status,
            "event_type": "performance_end",
            **kwargs
        }

        if success:
            self.logger.info("Operation completed successfully", **log_data)
        else:
            self.logger.error("Operation failed", **log_data)

        self.start_time = None
        self.operation_name = None


class RequestContextFilter(logging.Filter):
    """Filter to add request context to log records."""

    def __init__(self):
        super().__init__()
        self.request_context = {}

    def set_context(self, **kwargs):
        """Set request context."""
        self.request_context.update(kwargs)

    def clear_context(self):
        """Clear request context."""
        self.request_context.clear()

    def filter(self, record):
        """Add context to log record."""
        for key, value in self.request_context.items():
            setattr(record, key, value)
        return True


class PerformanceFilter(logging.Filter):
    """Filter to add performance context to log records."""

    def filter(self, record):
        """Add performance data to log record."""
        if not hasattr(record, 'duration_seconds'):
            record.duration_seconds = None
        if not hasattr(record, 'operation'):
            record.operation = None
        return True


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields
        if self.include_extra:
            for key, value in record.__dict__.items():
                if key not in {
                    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                    'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                    'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                    'thread', 'threadName', 'processName', 'process'
                }:
                    log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Import json here to avoid circular imports
        import json
        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console logging."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(
            fmt or '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt or '%Y-%m-%d %H:%M:%S'
        )

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']

        # Add color to level name
        record.levelname = f"{color}{record.levelname}{reset}"

        return super().format(record)


def setup_logging() -> Union[logging.Logger, 'structlog.stdlib.BoundLogger']:
    """Setup logging configuration based on settings."""
    settings = get_settings()
    log_settings = settings.logging

    # Create logs directory if it doesn't exist
    if log_settings.file_enabled:
        log_file_path = Path(log_settings.file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_settings.level))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_settings.level))

    if log_settings.structured:
        console_formatter = StructuredFormatter(include_extra=True)
    else:
        console_formatter = ColoredFormatter()

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler
    if log_settings.file_enabled:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_settings.file_path,
            maxBytes=log_settings.file_max_size,
            backupCount=log_settings.file_backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_settings.level))

        if log_settings.structured:
            file_formatter = StructuredFormatter(include_extra=True)
        else:
            file_formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Setup structlog if available
    if STRUCTLOG_AVAILABLE and log_settings.structured:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ]

        if log_settings.structured:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())

        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        return structlog.get_logger("quant_system")

    # Return standard logger
    return logging.getLogger("quant_system")


# Global request context filter
_request_filter = RequestContextFilter()


def get_logger(name: str) -> Union[logging.Logger, 'structlog.stdlib.BoundLogger']:
    """Get logger instance with proper configuration."""
    if STRUCTLOG_AVAILABLE and get_settings().logging.structured:
        return structlog.get_logger(name)
    else:
        logger = logging.getLogger(name)
        # Add request context filter if not already added
        if not any(isinstance(f, RequestContextFilter) for f in logger.filters):
            logger.addFilter(_request_filter)
        return logger


def set_request_context(**kwargs):
    """Set request context for logging."""
    _request_filter.set_context(**kwargs)


def clear_request_context():
    """Clear request context."""
    _request_filter.clear_context()


# Decorators
def log_performance(operation_name: Optional[str] = None):
    """Decorator to log function performance."""
    def decorator(func):
        name = operation_name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger("performance")
            perf_logger = PerformanceLogger(logger)

            perf_logger.start(name)
            try:
                result = func(*args, **kwargs)
                perf_logger.end(success=True)
                return result
            except Exception as e:
                perf_logger.end(success=False, error=str(e))
                raise

        return wrapper
    return decorator


def log_exceptions(
    logger_name: Optional[str] = None,
    reraise: bool = True,
    level: str = "ERROR"
):
    """Decorator to log exceptions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_data = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "exception_type": e.__class__.__name__,
                    "exception_message": str(e),
                    "traceback": traceback.format_exc()
                }

                getattr(logger, level.lower())("Function raised exception", **log_data)

                if reraise:
                    raise
                return None

        return wrapper
    return decorator


def log_function_calls(
    logger_name: Optional[str] = None,
    log_args: bool = True,
    log_result: bool = True
):
    """Decorator to log function calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)

            log_data = {
                "function": func.__name__,
                "module": func.__module__
            }

            if log_args:
                log_data.update({
                    "args_count": len(args),
                    "kwargs": list(kwargs.keys())
                })

            logger.info("Function called", **log_data)

            try:
                result = func(*args, **kwargs)

                if log_result:
                    result_type = type(result).__name__
                    logger.info(
                        "Function completed",
                        function=func.__name__,
                        result_type=result_type
                    )

                return result
            except Exception as e:
                logger.error(
                    "Function failed",
                    function=func.__name__,
                    error=str(e)
                )
                raise

        return wrapper
    return decorator


# Context managers
@contextmanager
def log_context(operation_name: str, **context_data):
    """Context manager for logging operation context."""
    logger = get_logger("context")
    correlation_id = str(uuid4())

    set_request_context(
        operation=operation_name,
        correlation_id=correlation_id,
        **context_data
    )

    logger.info(
        "Context started",
        operation=operation_name,
        correlation_id=correlation_id
    )

    try:
        yield
        logger.info(
            "Context completed",
            operation=operation_name,
            correlation_id=correlation_id
        )
    except Exception as e:
        logger.error(
            "Context failed",
            operation=operation_name,
            correlation_id=correlation_id,
            error=str(e)
        )
        raise
    finally:
        clear_request_context()


@contextmanager
def performance_context(operation_name: str, logger_name: str = "performance"):
    """Context manager for performance monitoring."""
    logger = get_logger(logger_name)
    perf_logger = PerformanceLogger(logger)

    perf_logger.start(operation_name)
    try:
        yield perf_logger
        perf_logger.end(success=True)
    except Exception as e:
        perf_logger.end(success=False, error=str(e))
        raise


# Utility functions
def log_system_info():
    """Log system information."""
    logger = get_logger("system")
    import platform
    import sys

    system_info = {
        "platform": platform.platform(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "environment": get_settings().environment
    }

    logger.info("System information", **system_info)


def log_component_status(component: str, status: str, **details):
    """Log component status."""
    logger = get_logger("components")

    logger.info(
        "Component status update",
        component=component,
        status=status,
        **details
    )


# Initialize logging on module import
_logger = setup_logging()
_log_system_info_on_startup = False

if not _log_system_info_on_startup:
    try:
        log_system_info()
        _log_system_info_on_startup = True
    except Exception:
        pass  # Silently ignore logging setup errors