"""System integration and configuration management for Hong Kong quantitative trading.

This package provides comprehensive system integration capabilities including
component orchestration, configuration management, and system lifecycle management.
"""

from .component_orchestrator import (
    ComponentInfo,
    ComponentOrchestrator,
    ComponentType,
    OrchestrationPlan,
)
from .config_manager import (
    ConfigManager,
    ConfigValidationError,
    DatabaseConfig,
    EnvironmentConfig,
    LoggingConfig,
    RedisConfig,
)
from .health_monitor import (
    ComponentHealth,
    HealthCheckResult,
    SystemHealth,
    SystemHealthMonitor,
)
from .system_initializer import (
    DependencyGraph,
    InitializationStatus,
    InitializationStep,
    SystemInitializer,
)
from .system_integration import (
    ComponentStatus,
    IntegrationConfig,
    IntegrationError,
    SystemIntegration,
    SystemStatus,
)

__all__ = [
    # System integration
    "SystemIntegration",
    "IntegrationConfig",
    "SystemStatus",
    "ComponentStatus",
    "IntegrationError",
    # Configuration management
    "ConfigManager",
    "ConfigValidationError",
    "EnvironmentConfig",
    "DatabaseConfig",
    "RedisConfig",
    "LoggingConfig",
    # Component orchestration
    "ComponentOrchestrator",
    "ComponentType",
    "ComponentInfo",
    "OrchestrationPlan",
    # System initialization
    "SystemInitializer",
    "InitializationStep",
    "InitializationStatus",
    "DependencyGraph",
    # Health monitoring
    "SystemHealthMonitor",
    "HealthCheckResult",
    "ComponentHealth",
    "SystemHealth",
]
