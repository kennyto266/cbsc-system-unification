"""Real - time monitoring and alerting system for Hong Kong quantitative trading.

This package provides comprehensive monitoring, alerting, and system health
management for the AI Agent trading system.
"""

from .alert_manager import (
    AlertAction,
    AlertManager,
    AlertRule,
    AlertStatus,
    NotificationChannel,
)
from .anomaly_detector import (
    AnomalyAlert,
    AnomalyDetector,
    AnomalyType,
    DetectionMethod,
)
from .health_checker import ComponentHealth, HealthChecker, HealthStatus, SystemHealth
from .performance_tracker import (
    MetricType,
    PerformanceAlert,
    PerformanceMetrics,
    PerformanceTracker,
)
from .real_time_monitor import (
    AlertLevel,
    AlertType,
    MonitoringConfig,
    RealTimeMonitor,
    SystemMetrics,
)

__all__ = [
    # Real - time monitoring
    "RealTimeMonitor",
    "SystemMetrics",
    "AlertLevel",
    "AlertType",
    "MonitoringConfig",
    # Alert management
    "AlertManager",
    "AlertRule",
    "AlertAction",
    "NotificationChannel",
    "AlertStatus",
    # Health checking
    "HealthChecker",
    "HealthStatus",
    "ComponentHealth",
    "SystemHealth",
    # Performance tracking
    "PerformanceTracker",
    "PerformanceMetrics",
    "MetricType",
    "PerformanceAlert",
    # Anomaly detection
    "AnomalyDetector",
    "AnomalyType",
    "AnomalyAlert",
    "DetectionMethod",
]
