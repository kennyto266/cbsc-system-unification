"""System health monitoring for Hong Kong quantitative trading system.

This module provides comprehensive system health monitoring capabilities including
component health checks, system - wide health assessment, and health reporting.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


class ComponentHealth(BaseModel):
    """Component health model."""

    component_id: str = Field(..., description="Component identifier")
    status: HealthStatus = Field(..., description="Health status")
    message: str = Field("", description="Health message")

    # Health metrics
    response_time: float = Field(0.0, description="Response time (ms)")
    memory_usage: float = Field(0.0, description="Memory usage (MB)")
    cpu_usage: float = Field(0.0, description="CPU usage (%)")
    error_rate: float = Field(0.0, description="Error rate (%)")

    # Health details
    last_check: datetime = Field(
        default_factory=datetime.now, description="Last health check"
    )
    uptime: float = Field(0.0, description="Uptime (seconds)")
    version: Optional[str] = Field(None, description="Component version")

    # Additional info
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional health details"
    )

    class Config:
        use_enum_values = True


class SystemHealth(BaseModel):
    """System health model."""

    system_id: str = Field(..., description="System identifier")
    overall_status: HealthStatus = Field(..., description="Overall system status")
    summary: str = Field("", description="Health summary")

    # System metrics
    total_components: int = Field(0, description="Total components")
    healthy_components: int = Field(0, description="Healthy components")
    warning_components: int = Field(0, description="Warning components")
    critical_components: int = Field(0, description="Critical components")
    unknown_components: int = Field(0, description="Unknown components")

    # System details
    system_uptime: float = Field(0.0, description="System uptime (seconds)")
    last_check: datetime = Field(
        default_factory=datetime.now, description="Last system check"
    )

    # Component health
    components: Dict[str, ComponentHealth] = Field(
        default_factory=dict, description="Component health details"
    )

    # Health recommendations
    recommendations: List[str] = Field(
        default_factory=list, description="Health recommendations"
    )

    class Config:
        use_enum_values = True


class HealthCheckResult(BaseModel):
    """Health check result model."""

    check_id: str = Field(..., description="Check identifier")
    component_id: str = Field(..., description="Component identifier")
    check_type: str = Field(..., description="Check type")

    # Check results
    status: HealthStatus = Field(..., description="Check status")
    message: str = Field("", description="Check message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Check details")

    # Timing
    start_time: datetime = Field(
        default_factory=datetime.now, description="Check start time"
    )
    end_time: Optional[datetime] = Field(None, description="Check end time")
    duration: float = Field(0.0, description="Check duration (seconds)")

    # Metadata
    success: bool = Field(False, description="Check success")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        use_enum_values = True


class SystemHealthMonitor:
    """System health monitoring manager."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Health monitoring state
        self.component_health: Dict[str, ComponentHealth] = {}
        self.health_check_results: List[HealthCheckResult] = []
        self.health_checkers: Dict[str, List[Callable]] = {}

        # Monitoring configuration
        self.health_check_interval: int = 30
        self.health_check_timeout: int = 10
        self.max_health_history: int = 1000

        # Health monitoring tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring: bool = False

        # Statistics
        self.stats = {
            "health_checks_performed": 0,
            "health_checks_successful": 0,
            "health_checks_failed": 0,
            "components_monitored": 0,
            "alerts_triggered": 0,
            "start_time": None,
        }

    async def initialize(self) -> bool:
        """Initialize the health monitor."""
        try:
            self.logger.info("Initializing system health monitor...")

            # Initialize health checkers
            await self._initialize_health_checkers()

            self.stats["start_time"] = datetime.now()
            self.logger.info("System health monitor initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize system health monitor: {e}")
            return False

    async def _initialize_health_checkers(self) -> None:
        """Initialize health checkers for different component types."""
        try:
            # Database health checker
            self.health_checkers["database"] = [self._check_database_health]

            # Cache health checker
            self.health_checkers["cache"] = [self._check_cache_health]

            # AI Agent health checker
            self.health_checkers["ai_agent"] = [self._check_ai_agent_health]

            # Strategy manager health checker
            self.health_checkers["strategy_manager"] = [
                self._check_strategy_manager_health
            ]

            # Monitoring system health checker
            self.health_checkers["monitoring"] = [self._check_monitoring_health]

            # Integration health checker
            self.health_checkers["integration"] = [self._check_integration_health]

            # Generic health checker
            self.health_checkers["generic"] = [self._check_generic_health]

            self.logger.info(
                f"Initialized {len(self.health_checkers)} health checker types"
            )

        except Exception as e:
            self.logger.error(f"Error initializing health checkers: {e}")

    async def start_monitoring(self) -> bool:
        """Start health monitoring."""
        try:
            if self.is_monitoring:
                self.logger.warning("Health monitoring is already running")
                return True

            self.logger.info("Starting health monitoring...")

            # Start monitoring task
            self.monitoring_task = asyncio.create_task(self._health_monitoring_loop())
            self.is_monitoring = True

            self.logger.info("Health monitoring started")
            return True

        except Exception as e:
            self.logger.error(f"Error starting health monitoring: {e}")
            return False

    async def stop_monitoring(self) -> bool:
        """Stop health monitoring."""
        try:
            if not self.is_monitoring:
                self.logger.warning("Health monitoring is not running")
                return True

            self.logger.info("Stopping health monitoring...")

            # Stop monitoring task
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass

            self.is_monitoring = False
            self.logger.info("Health monitoring stopped")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping health monitoring: {e}")
            return False

    async def _health_monitoring_loop(self) -> None:
        """Health monitoring loop."""
        while self.is_monitoring:
            try:
                # Perform health checks
                await self._perform_health_checks()

                # Wait for next check
                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _perform_health_checks(self) -> None:
        """Perform health checks for all components."""
        try:
            # Check each component
            for component_id, component_health in self.component_health.items():
                await self._check_component_health(component_id)

            # Update system health
            await self._update_system_health()

        except Exception as e:
            self.logger.error(f"Error performing health checks: {e}")

    async def _check_component_health(self, component_id: str) -> None:
        """Check health of a specific component."""
        try:
            # Get component health
            component_health = self.component_health.get(component_id)
            if not component_health:
                return

            # Determine component type
            component_type = self._get_component_type(component_id)

            # Get health checkers for component type
            checkers = self.health_checkers.get(
                component_type, self.health_checkers["generic"]
            )

            # Run health checkers
            health_results = []
            for checker in checkers:
                try:
                    result = await checker(component_id)
                    if result:
                        health_results.append(result)
                except Exception as e:
                    self.logger.error(f"Health checker failed for {component_id}: {e}")

            # Aggregate results
            if health_results:
                aggregated_result = await self._aggregate_health_results(health_results)
                await self._update_component_health(component_id, aggregated_result)

        except Exception as e:
            self.logger.error(f"Error checking component health {component_id}: {e}")

    def _get_component_type(self, component_id: str) -> str:
        """Get component type from component ID."""
        # Simple mapping based on component ID patterns
        if "database" in component_id.lower():
            return "database"
        elif "cache" in component_id.lower() or "redis" in component_id.lower():
            return "cache"
        elif "agent" in component_id.lower():
            return "ai_agent"
        elif "strategy" in component_id.lower():
            return "strategy_manager"
        elif "monitoring" in component_id.lower():
            return "monitoring"
        elif "integration" in component_id.lower():
            return "integration"
        else:
            return "generic"

    async def _aggregate_health_results(
        self, results: List[HealthCheckResult]
    ) -> HealthCheckResult:
        """Aggregate multiple health check results."""
        try:
            if not results:
                return None

            # Determine overall status
            statuses = [result.status for result in results]
            if HealthStatus.CRITICAL in statuses:
                overall_status = HealthStatus.CRITICAL
            elif HealthStatus.WARNING in statuses:
                overall_status = HealthStatus.WARNING
            elif HealthStatus.HEALTHY in statuses:
                overall_status = HealthStatus.HEALTHY
            else:
                overall_status = HealthStatus.UNKNOWN

            # Aggregate messages
            messages = [result.message for result in results if result.message]
            aggregated_message = (
                "; ".join(messages) if messages else "Health check completed"
            )

            # Aggregate details
            aggregated_details = {}
            for result in results:
                aggregated_details.update(result.details)

            # Create aggregated result
            aggregated_result = HealthCheckResult(
                check_id=f"aggregated_{int(datetime.now().timestamp())}",
                component_id=results[0].component_id,
                check_type="aggregated",
                status=overall_status,
                message=aggregated_message,
                details=aggregated_details,
                success=overall_status in [HealthStatus.HEALTHY, HealthStatus.WARNING],
            )

            return aggregated_result

        except Exception as e:
            self.logger.error(f"Error aggregating health results: {e}")
            return None

    async def _update_component_health(
        self, component_id: str, health_result: HealthCheckResult
    ) -> None:
        """Update component health based on check result."""
        try:
            if not health_result:
                return

            # Get or create component health
            if component_id not in self.component_health:
                self.component_health[component_id] = ComponentHealth(
                    component_id=component_id, status=HealthStatus.UNKNOWN
                )

            # Update component health
            component_health = self.component_health[component_id]
            component_health.status = health_result.status
            component_health.message = health_result.message
            component_health.last_check = datetime.now()
            component_health.details.update(health_result.details)

            # Update metrics if available
            if "response_time" in health_result.details:
                component_health.response_time = health_result.details["response_time"]
            if "memory_usage" in health_result.details:
                component_health.memory_usage = health_result.details["memory_usage"]
            if "cpu_usage" in health_result.details:
                component_health.cpu_usage = health_result.details["cpu_usage"]
            if "error_rate" in health_result.details:
                component_health.error_rate = health_result.details["error_rate"]

            # Store health check result
            self.health_check_results.append(health_result)

            # Trim history if needed
            if len(self.health_check_results) > self.max_health_history:
                self.health_check_results = self.health_check_results[
                    -self.max_health_history :
                ]

            self.stats["health_checks_performed"] += 1
            if health_result.success:
                self.stats["health_checks_successful"] += 1
            else:
                self.stats["health_checks_failed"] += 1

        except Exception as e:
            self.logger.error(f"Error updating component health: {e}")

    async def _update_system_health(self) -> None:
        """Update overall system health."""
        try:
            # Count components by status
            status_counts = {
                HealthStatus.HEALTHY: 0,
                HealthStatus.WARNING: 0,
                HealthStatus.CRITICAL: 0,
                HealthStatus.UNKNOWN: 0,
                HealthStatus.MAINTENANCE: 0,
            }

            for component_health in self.component_health.values():
                status_counts[component_health.status] += 1

            # Determine overall status
            if status_counts[HealthStatus.CRITICAL] > 0:
                overall_status = HealthStatus.CRITICAL
            elif status_counts[HealthStatus.WARNING] > 0:
                overall_status = HealthStatus.WARNING
            elif status_counts[HealthStatus.HEALTHY] > 0:
                overall_status = HealthStatus.HEALTHY
            else:
                overall_status = HealthStatus.UNKNOWN

            # Create system health summary
            total_components = len(self.component_health)
            summary = f"System health: {overall_status.value}. {total_components} components monitored."

            # Create recommendations
            recommendations = []
            if status_counts[HealthStatus.CRITICAL] > 0:
                recommendations.append(
                    "Critical components detected - immediate attention required"
                )
            if status_counts[HealthStatus.WARNING] > 0:
                recommendations.append("Warning components detected - monitor closely")
            if status_counts[HealthStatus.UNKNOWN] > 0:
                recommendations.append(
                    "Unknown status components detected - investigate"
                )

            # Update system health (would be stored in a system health object)
            self.logger.debug(f"System health updated: {overall_status.value}")

        except Exception as e:
            self.logger.error(f"Error updating system health: {e}")

    # Health checker implementations
    async def _check_database_health(
        self, component_id: str
    ) -> Optional[HealthCheckResult]:
        """Check database health."""
        try:
            # Placeholder implementation
            # In real implementation, would check database connection, query performance, etc.

            return HealthCheckResult(
                check_id=f"db_check_{int(datetime.now().timestamp())}",
                component_id=component_id,
                check_type="database",
                status=HealthStatus.HEALTHY,
                message="Database connection healthy",
                details={
                    "response_time": 10.5,
                    "connection_count": 5,
                    "query_performance": "good",
                },
                success=True,
            )

        except Exception as e:
            self.logger.error(f"Error checking database health: {e}")
            return None

    async def _check_cache_health(
        self, component_id: str
    ) -> Optional[HealthCheckResult]:
        """Check cache health."""
        try:
            # Placeholder implementation
            return HealthCheckResult(
                check_id=f"cache_check_{int(datetime.now().timestamp())}",
                component_id=component_id,
                check_type="cache",
                status=HealthStatus.HEALTHY,
                message="Cache system healthy",
                details={"response_time": 2.1, "hit_rate": 0.95, "memory_usage": 128.5},
                success=True,
            )

        except Exception as e:
            self.logger.error(f"Error checking cache health: {e}")
            return None

    async def _check_ai_agent_health(
        self, component_id: str
    ) -> Optional[HealthCheckResult]:
        """Check AI agent health."""
        try:
            # Placeholder implementation
            return HealthCheckResult(
                check_id=f"agent_check_{int(datetime.now().timestamp())}",
                component_id=component_id,
                check_type="ai_agent",
                status=HealthStatus.HEALTHY,
                message="AI agent healthy",
                details={
                    "response_time": 50.2,
                    "memory_usage": 256.0,
                    "cpu_usage": 15.5,
                    "error_rate": 0.01,
                },
                success=True,
            )

        except Exception as e:
            self.logger.error(f"Error checking AI agent health: {e}")
            return None

    async def _check_strategy_manager_health(
        self, component_id: str
    ) -> Optional[HealthCheckResult]:
        """Check strategy manager health."""
        try:
            # Placeholder implementation
            return HealthCheckResult(
                check_id=f"strategy_check_{int(datetime.now().timestamp())}",
                component_id=component_id,
                check_type="strategy_manager",
                status=HealthStatus.HEALTHY,
                message="Strategy manager healthy",
                details={
                    "active_strategies": 5,
                    "total_strategies": 10,
                    "performance_score": 0.85,
                },
                success=True,
            )

        except Exception as e:
            self.logger.error(f"Error checking strategy manager health: {e}")
            return None

    async def _check_monitoring_health(
        self, component_id: str
    ) -> Optional[HealthCheckResult]:
        """Check monitoring system health."""
        try:
            # Placeholder implementation
            return HealthCheckResult(
                check_id=f"monitoring_check_{int(datetime.now().timestamp())}",
                component_id=component_id,
                check_type="monitoring",
                status=HealthStatus.HEALTHY,
                message="Monitoring system healthy",
                details={
                    "metrics_collected": 150,
                    "alerts_active": 2,
                    "data_retention": "7 days",
                },
                success=True,
            )

        except Exception as e:
            self.logger.error(f"Error checking monitoring health: {e}")
            return None

    async def _check_integration_health(
        self, component_id: str
    ) -> Optional[HealthCheckResult]:
        """Check integration health."""
        try:
            # Placeholder implementation
            return HealthCheckResult(
                check_id=f"integration_check_{int(datetime.now().timestamp())}",
                component_id=component_id,
                check_type="integration",
                status=HealthStatus.HEALTHY,
                message="Integration healthy",
                details={
                    "connections_active": 3,
                    "last_sync": "2 minutes ago",
                    "sync_frequency": "1 minute",
                },
                success=True,
            )

        except Exception as e:
            self.logger.error(f"Error checking integration health: {e}")
            return None

    async def _check_generic_health(
        self, component_id: str
    ) -> Optional[HealthCheckResult]:
        """Check generic component health."""
        try:
            # Placeholder implementation
            return HealthCheckResult(
                check_id=f"generic_check_{int(datetime.now().timestamp())}",
                component_id=component_id,
                check_type="generic",
                status=HealthStatus.HEALTHY,
                message="Component healthy",
                details={"status": "running", "uptime": 3600.0},
                success=True,
            )

        except Exception as e:
            self.logger.error(f"Error checking generic health: {e}")
            return None

    # Public methods
    async def check_system_health(self) -> SystemHealth:
        """Check overall system health."""
        try:
            # Count components by status
            status_counts = {
                HealthStatus.HEALTHY: 0,
                HealthStatus.WARNING: 0,
                HealthStatus.CRITICAL: 0,
                HealthStatus.UNKNOWN: 0,
                HealthStatus.MAINTENANCE: 0,
            }

            for component_health in self.component_health.values():
                status_counts[component_health.status] += 1

            # Determine overall status
            if status_counts[HealthStatus.CRITICAL] > 0:
                overall_status = HealthStatus.CRITICAL
            elif status_counts[HealthStatus.WARNING] > 0:
                overall_status = HealthStatus.WARNING
            elif status_counts[HealthStatus.HEALTHY] > 0:
                overall_status = HealthStatus.HEALTHY
            else:
                overall_status = HealthStatus.UNKNOWN

            # Create system health
            system_health = SystemHealth(
                system_id="trading_system",
                overall_status=overall_status,
                summary=f"System health: {overall_status.value}",
                total_components=len(self.component_health),
                healthy_components=status_counts[HealthStatus.HEALTHY],
                warning_components=status_counts[HealthStatus.WARNING],
                critical_components=status_counts[HealthStatus.CRITICAL],
                unknown_components=status_counts[HealthStatus.UNKNOWN],
                system_uptime=0.0,  # Would calculate actual uptime
                components=self.component_health.copy(),
            )

            return system_health

        except Exception as e:
            self.logger.error(f"Error checking system health: {e}")
            return SystemHealth(
                system_id="trading_system",
                overall_status=HealthStatus.UNKNOWN,
                summary="Health check failed",
            )

    def get_component_health(self, component_id: str) -> Optional[ComponentHealth]:
        """Get component health."""
        return self.component_health.get(component_id)

    def get_all_component_health(self) -> Dict[str, ComponentHealth]:
        """Get all component health."""
        return self.component_health.copy()

    def get_health_check_history(self, limit: int = 100) -> List[HealthCheckResult]:
        """Get health check history."""
        return self.health_check_results[-limit:] if self.health_check_results else []

    def add_health_checker(self, component_type: str, checker: Callable) -> None:
        """Add health checker for component type."""
        if component_type not in self.health_checkers:
            self.health_checkers[component_type] = []
        self.health_checkers[component_type].append(checker)

    def get_statistics(self) -> Dict[str, Any]:
        """Get health monitor statistics."""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "is_monitoring": self.is_monitoring,
            "uptime_seconds": uptime,
            "components_monitored": len(self.component_health),
            "health_check_history_count": len(self.health_check_results),
            "stats": self.stats.copy(),
        }

    async def shutdown(self) -> None:
        """Shutdown the health monitor."""
        try:
            self.logger.info("Shutting down system health monitor...")

            # Stop monitoring
            await self.stop_monitoring()

            # Clear data
            self.component_health.clear()
            self.health_check_results.clear()
            self.health_checkers.clear()

            self.logger.info("System health monitor shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during system health monitor shutdown: {e}")
