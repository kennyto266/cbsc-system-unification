"""
Unified Logging System
=====================

Complete logging solution combining all logging implementations:
- Structured logging with multiple handlers
- Rotating file logs with retention
- Audit logging for security events
- Compliance reporting
- Background async processing
"""

# Core logging - use get_logger from logging_utils
from ..logging_utils import get_logger

logger = get_logger(__name__)

# Audit logging - use relative import from src/security
try:
    from ..security.audit_logger import (
        AuditEventType,
        EventSeverity,
        AuditEntry,
        AuditLogger,
        audit_logger,
        log_security_event,
        log_strategy_access,
        log_non_price_strategy_execution,
    )
except ImportError:
    # Fallback if audit_logger is not available
    AuditEventType = None
    EventSeverity = None
    AuditEntry = None
    AuditLogger = None
    audit_logger = None
    log_security_event = None
    log_strategy_access = None
    log_non_price_strategy_execution = None
    logger.warning("Security audit logger not available")

__all__ = [
    # Core logging
    "logger",

    # Audit logging
    "AuditEventType",
    "EventSeverity",
    "AuditEntry",
    "AuditLogger",
    "audit_logger",
    "log_security_event",
    "log_strategy_access",
    "log_non_price_strategy_execution",
]
