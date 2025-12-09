"""
数据隐私与安全审计监控模块
Phase 5: Data Privacy & Security - 审计与监控

此模块提供完整的数据隐私保护和安全审计功能，包括：
- 审计日志系统
- 数据访问跟踪
- 隐私合规报告
- 安全仪表板
"""

from .access_tracking import (
    AccessEvent,
    AccessStatus,
    AccessTracker,
    AccessType,
    create_access_tracker,
)
from .audit_logger import AuditEvent, AuditLogger, LogLevel, create_audit_logger
from .compliance_reporting import (
    ComplianceReport,
    ComplianceReporter,
    ComplianceStandard,
    create_compliance_reporter,
)
from .config import get_config
from .security_dashboard import (
    AlertSeverity,
    AlertStatus,
    SecurityAlert,
    SecurityDashboard,
    create_security_dashboard,
)

__all__ = [
    "AuditLogger",
    "AuditEvent",
    "LogLevel",
    "create_audit_logger",
    "AccessTracker",
    "AccessEvent",
    "AccessType",
    "AccessStatus",
    "create_access_tracker",
    "ComplianceReporter",
    "ComplianceReport",
    "ComplianceStandard",
    "create_compliance_reporter",
    "SecurityDashboard",
    "SecurityAlert",
    "AlertSeverity",
    "AlertStatus",
    "create_security_dashboard",
    "get_config",
]

__version__ = "1.0.0"
