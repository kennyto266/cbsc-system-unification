"""
CBSC Security Module

Comprehensive security suite for the CBSC trading system,
including RBAC, encryption, audit logging, rate limiting,
and security monitoring.
"""

from .rbac import (
    UserRole,
    Permission,
    StrategyType,
    DataAccessLevel,
    RBACManager,
    require_permission,
    rbac_manager
)

from .encryption import (
    DataEncryption,
    DataMasking,
    encryption_service,
    data_masking
)

from .audit_logger import (
    AuditEventType,
    EventSeverity,
    AuditLogger,
    AuditEntry,
    audit_logger,
    log_security_event,
    log_strategy_access,
    log_non_price_strategy_execution
)

from .rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitMiddleware,
    rate_limiter
)

from .monitoring import (
    ThreatLevel,
    AlertType,
    SecurityAlert,
    SecurityMetrics,
    ThreatDetector,
    SecurityMonitor,
    security_monitor,
    monitor_security_event
)

# Security initialization functions
async def initialize_security():
    """Initialize all security components"""

    # Initialize encryption service
    from .encryption import initialize_encryption
    initialize_encryption()

    # Initialize rate limiter
    await rate_limiter.initialize_rate_limiter()

    # Initialize audit logger
    await audit_logger.cleanup_old_logs()

    # Start security monitoring
    await security_monitor.initialize_security_monitoring()

    import logging
    logger = logging.getLogger(__name__)
    logger.info("CBSC Security Module initialized successfully")


# Security configuration
class SecurityConfig:
    """Central security configuration"""

    # RBAC settings
    ENABLE_RBAC = True
    DEFAULT_ROLE = "basic"

    # Encryption settings
    ENCRYPT_AT_REST = True
    ENCRYPT_IN_TRANSIT = True

    # Audit settings
    AUDIT_ALL_EVENTS = True
    AUDIT_RETENTION_DAYS = 365

    # Rate limiting settings
    ENABLE_RATE_LIMITING = True
    ENABLE_DDOS_PROTECTION = True

    # Monitoring settings
    ENABLE_SECURITY_MONITORING = True
    ALERT_ON_CRITICAL_EVENTS = True

    # API security settings
    REQUIRE_HTTPS = True
    ENABLE_CORS = True
    VALIDATE_API_KEYS = True


# Export all security components
__all__ = [
    # RBAC
    "UserRole",
    "Permission",
    "StrategyType",
    "DataAccessLevel",
    "RBACManager",
    "require_permission",
    "rbac_manager",

    # Encryption
    "DataEncryption",
    "DataMasking",
    "encryption_service",
    "data_masking",

    # Audit Logging
    "AuditEventType",
    "EventSeverity",
    "AuditLogger",
    "AuditEntry",
    "audit_logger",
    "log_security_event",
    "log_strategy_access",
    "log_non_price_strategy_execution",

    # Rate Limiting
    "RateLimiter",
    "RateLimitConfig",
    "RateLimitMiddleware",
    "rate_limiter",

    # Security Monitoring
    "ThreatLevel",
    "AlertType",
    "SecurityAlert",
    "SecurityMetrics",
    "ThreatDetector",
    "SecurityMonitor",
    "security_monitor",
    "monitor_security_event",

    # Initialization
    "initialize_security",
    "SecurityConfig",
]