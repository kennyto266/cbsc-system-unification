"""
Logging Module
日誌模塊

提供結構化日誌記錄、安全審計和 ELK Stack 集成。

Available Components:
    - StructuredLogger: 結構化日誌記錄器
    - SecurityAuditManager: 安全審計管理器
    - AlertManager: 告警管理器
"""

from .structured_logger import (
    StructuredLogger,
    get_logger,
    LogLevel,
    SecurityEventType,
    SecurityAuditLog,
    JSONFormatter,
)

from .audit_manager import (
    SecurityAuditManager,
    get_audit_manager,
)

from .alert_manager import (
    AlertManager,
    get_alert_manager,
    AlertLevel,
    AlertChannel,
    AlertRule,
    Alert,
)

__all__ = [
    # ========== Structured Logger ==========
    "StructuredLogger",
    "get_logger",
    "LogLevel",
    "SecurityEventType",
    "SecurityAuditLog",
    "JSONFormatter",

    # ========== Security Audit Manager ==========
    "SecurityAuditManager",
    "get_audit_manager",

    # ========== Alert Manager ==========
    "AlertManager",
    "get_alert_manager",
    "AlertLevel",
    "AlertChannel",
    "AlertRule",
    "Alert",
]
