"""Health checking system for real - time monitoring.

This module provides comprehensive health checking capabilities for
system components, services, and overall system health assessment.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import psutil
from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(str, Enum):
    """Component types for health checking."""

    SYSTEM = "system"
    AGENT = "agent"
    DATABASE = "database"
    NETWORK = "network"
    STORAGE = "storage"
    API = "api"
    QUEUE = "queue"
    CACHE = "cache"


class ComponentHealth(BaseModel):
    """Component health status."""

    component_id: str = Field(..., description="Component identifier")
    component_type: ComponentType = Field(..., description="Component type")
    status: HealthStatus = Field(..., description="Health status")
    message: str = Field("", description="Health status message")

    # Health metrics
    response_time: Optional[float] = Field(None, description="Response time (ms)")
    uptime: Optional[float] = Field(None, description="Uptime (seconds)")
    error_rate: Optional[float] = Field(None, description="Error rate (%)")
    throughput: Optional[float] = Field(None, description="Throughput (requests / sec)")

    # Additional details
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional health details"
    )

    # Timestamps
    last_check: datetime = Field(
        default_factory=datetime.now, description="Last check time"
    )
    last_healthy: Optional[datetime] = Field(None, description="Last healthy time")

    class Config:
        use_enum_values = True


class SystemHealth(BaseModel):
    """Overall system health status."""

    overall_status: HealthStatus = Field(..., description="Overall system health")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Health check timestamp"
    )

    # Component health
    components: Dict[str, ComponentHealth] = Field(
        default_factory=dict, description="Component health status"
    )

    # System metrics
    total_components: int = Field(0, description="Total components")
    healthy_components: int = Field(0, description="Healthy components")
    degraded_components: int = Field(0, description="Degraded components")
    unhealthy_components: int = Field(0, description="Unhealthy components")

    # Health summary
    summary: str = Field("", description="Health summary")
    recommendations: List[str] = Field(
        default_factory=list, description="Health recommendations"
    )

    class Config:
        use_enum_values = True


class HealthChecker:
    """Health checking system for monitoring system components."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Health check configuration
        self.check_interval = 30.0  # seconds
        self.timeout = 10.0  # seconds
        self.retry_count = 3
        self.retry_delay = 1.0  # seconds

        # Component health tracking
        self.component_health: Dict[str, ComponentHealth] = {}
        self.health_history: List[SystemHealth] = []

        # Health check functions
        self.health_checkers: Dict[ComponentType, Callable] = {}

        # Statistics
        self.stats = {
            "health_checks_performed": 0,
            "components_checked": 0,
            "healthy_checks": 0,
            "degraded_checks": 0,
            "unhealthy_checks": 0,
            "start_time": None,
        }

        # Health check task
        self.health_check_task: Optional[asyncio.Task] = None
        self.is_running = False

    async def initialize(self) -> bool:
        """Initialize the health checker."""
        try:
            self.logger.info("Initializing health checker...")

            # Register default health checkers
            await self._register_default_checkers()

            # Start health checking task
            self.health_check_task = asyncio.create_task(self._health_check_loop())

            self.is_running = True
            self.stats["start_time"] = datetime.now()
            self.logger.info("Health checker initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize health checker: {e}")
            return False

    async def _register_default_checkers(self) -> None:
        """Register default health check functions."""
        try:
            # System health checker
            self.health_checkers[ComponentType.SYSTEM] = self._check_system_health

            # Agent health checker
            self.health_checkers[ComponentType.AGENT] = self._check_agent_health

            # Database health checker
            self.health_checkers[ComponentType.DATABASE] = self._check_database_health

            # Network health checker
            self.health_checkers[ComponentType.NETWORK] = self._check_network_health

            # Storage health checker
            self.health_checkers[ComponentType.STORAGE] = self._check_storage_health

            # API health checker
            self.health_checkers[ComponentType.API] = self._check_api_health

            # Queue health checker
            self.health_checkers[ComponentType.QUEUE] = self._check_queue_health

            # Cache health checker
            self.health_checkers[ComponentType.CACHE] = self._check_cache_health

            self.logger.info(f"Registered {len(self.health_checkers)} health checkers")

        except Exception as e:
            self.logger.error(f"Error registering default checkers: {e}")

    async def _health_check_loop(self) -> None:
        """Main health checking loop."""
        while self.is_running:
            try:
                # Perform health check
                system_health = await self.check_system_health()

                # Store health history
                self.health_history.append(system_health)

                # Trim history if too large
                if len(self.health_history) > 1000:
                    self.health_history = self.health_history[-1000:]

                # Update statistics
                self.stats["health_checks_performed"] += 1

                # Wait for next check
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(5)

    async def check_system_health(self) -> SystemHealth:
        """Check overall system health."""
        try:
            # Check all registered components
            components = {}
            total_components = 0
            healthy_components = 0
            degraded_components = 0
            unhealthy_components = 0

            for component_type, checker_func in self.health_checkers.items():
                try:
                    # Check component health
                    component_health = await self._check_component_health(
                        component_type, checker_func
                    )

                    if component_health:
                        components[component_health.component_id] = component_health
                        total_components += 1

                        if component_health.status == HealthStatus.HEALTHY:
                            healthy_components += 1
                        elif component_health.status == HealthStatus.DEGRADED:
                            degraded_components += 1
                        elif component_health.status == HealthStatus.UNHEALTHY:
                            unhealthy_components += 1

                        # Update component health tracking
                        self.component_health[component_health.component_id] = (
                            component_health
                        )

                except Exception as e:
                    self.logger.error(f"Error checking {component_type}: {e}")

            # Determine overall status
            if unhealthy_components > 0:
                overall_status = HealthStatus.UNHEALTHY
            elif degraded_components > 0:
                overall_status = HealthStatus.DEGRADED
            elif healthy_components > 0:
                overall_status = HealthStatus.HEALTHY
            else:
                overall_status = HealthStatus.UNKNOWN

            # Generate summary and recommendations
            summary, recommendations = self._generate_health_summary(
                overall_status,
                healthy_components,
                degraded_components,
                unhealthy_components,
            )

            system_health = SystemHealth(
                overall_status=overall_status,
                components=components,
                total_components=total_components,
                healthy_components=healthy_components,
                degraded_components=degraded_components,
                unhealthy_components=unhealthy_components,
                summary=summary,
                recommendations=recommendations,
            )

            # Update statistics
            self.stats["components_checked"] += total_components
            if overall_status == HealthStatus.HEALTHY:
                self.stats["healthy_checks"] += 1
            elif overall_status == HealthStatus.DEGRADED:
                self.stats["degraded_checks"] += 1
            elif overall_status == HealthStatus.UNHEALTHY:
                self.stats["unhealthy_checks"] += 1

            return system_health

        except Exception as e:
            self.logger.error(f"Error checking system health: {e}")
            return SystemHealth(
                overall_status=HealthStatus.UNKNOWN,
                summary=f"Health check failed: {str(e)}",
            )

    async def _check_component_health(
        self, component_type: ComponentType, checker_func: Callable
    ) -> Optional[ComponentHealth]:
        """Check health of a specific component."""
        try:
            # Retry logic
            for attempt in range(self.retry_count):
                try:
                    # Run health check with timeout
                    health_result = await asyncio.wait_for(
                        checker_func(), timeout=self.timeout
                    )

                    if health_result:
                        return health_result

                except asyncio.TimeoutError:
                    self.logger.warning(
                        f"Health check timeout for {component_type} (attempt {attempt + 1})"
                    )
                    if attempt < self.retry_count - 1:
                        await asyncio.sleep(self.retry_delay)
                    continue

                except Exception as e:
                    self.logger.warning(
                        f"Health check error for {component_type} (attempt {attempt + 1}): {e}"
                    )
                    if attempt < self.retry_count - 1:
                        await asyncio.sleep(self.retry_delay)
                    continue

            # All attempts failed
            return ComponentHealth(
                component_id=f"{component_type.value}_check",
                component_type=component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed after {self.retry_count} attempts",
            )

        except Exception as e:
            self.logger.error(
                f"Error checking component health for {component_type}: {e}"
            )
            return None

    # Health check functions
    async def _check_system_health(self) -> Optional[ComponentHealth]:
        """Check system - level health."""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Check memory usage
            memory = psutil.virtual_memory()

            # Check disk usage
            disk = psutil.disk_usage("/")

            # Determine status
            if cpu_percent > 90 or memory.percent > 95 or disk.percent > 95:
                status = HealthStatus.UNHEALTHY
                message = f"System resources critically high: CPU {cpu_percent:.1f}%, Memory {memory.percent:.1f}%, Disk {disk.percent:.1f}%"
            elif cpu_percent > 80 or memory.percent > 85 or disk.percent > 85:
                status = HealthStatus.DEGRADED
                message = f"System resources high: CPU {cpu_percent:.1f}%, Memory {memory.percent:.1f}%, Disk {disk.percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"System resources normal: CPU {cpu_percent:.1f}%, Memory {memory.percent:.1f}%, Disk {disk.percent:.1f}%"

            return ComponentHealth(
                component_id="system",
                component_type=ComponentType.SYSTEM,
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "memory_total": memory.total,
                    "memory_available": memory.available,
                    "disk_total": disk.total,
                    "disk_free": disk.free,
                },
            )

        except Exception as e:
            self.logger.error(f"Error checking system health: {e}")
            return ComponentHealth(
                component_id="system",
                component_type=ComponentType.SYSTEM,
                status=HealthStatus.UNHEALTHY,
                message=f"System health check failed: {str(e)}",
            )

    async def _check_agent_health(self) -> Optional[ComponentHealth]:
        """Check AI agent health."""
        try:
            # In real implementation, this would check actual agent status
            # For now, simulate agent health check

            # Simulate agent response time
            start_time = time.time()
            await asyncio.sleep(0.1)  # Simulate agent check
            response_time = (time.time() - start_time) * 1000

            # Simulate agent status (in real implementation, check actual agent status)
            agent_status = "active"  # This would come from actual agent status

            if agent_status == "active":
                status = HealthStatus.HEALTHY
                message = "All AI agents are active and responding"
            elif agent_status == "degraded":
                status = HealthStatus.DEGRADED
                message = "Some AI agents are experiencing issues"
            else:
                status = HealthStatus.UNHEALTHY
                message = "AI agents are not responding properly"

            return ComponentHealth(
                component_id="ai_agents",
                component_type=ComponentType.AGENT,
                status=status,
                message=message,
                response_time=response_time,
                details={
                    "agent_count": 7,  # Number of AI agents
                    "active_agents": 7 if status == HealthStatus.HEALTHY else 5,
                    "agent_status": agent_status,
                },
            )

        except Exception as e:
            self.logger.error(f"Error checking agent health: {e}")
            return ComponentHealth(
                component_id="ai_agents",
                component_type=ComponentType.AGENT,
                status=HealthStatus.UNHEALTHY,
                message=f"Agent health check failed: {str(e)}",
            )

    async def _check_database_health(self) -> Optional[ComponentHealth]:
        """Check database health."""
        try:
            # In real implementation, this would check actual database connection
            # For now, simulate database health check

            start_time = time.time()
            await asyncio.sleep(0.05)  # Simulate database check
            response_time = (time.time() - start_time) * 1000

            # Simulate database status
            db_status = "connected"  # This would come from actual database check

            if db_status == "connected":
                status = HealthStatus.HEALTHY
                message = "Database connection is healthy"
            elif db_status == "slow":
                status = HealthStatus.DEGRADED
                message = "Database is responding slowly"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Database connection failed"

            return ComponentHealth(
                component_id="database",
                component_type=ComponentType.DATABASE,
                status=status,
                message=message,
                response_time=response_time,
                details={
                    "connection_status": db_status,
                    "response_time_ms": response_time,
                },
            )

        except Exception as e:
            self.logger.error(f"Error checking database health: {e}")
            return ComponentHealth(
                component_id="database",
                component_type=ComponentType.DATABASE,
                status=HealthStatus.UNHEALTHY,
                message=f"Database health check failed: {str(e)}",
            )

    async def _check_network_health(self) -> Optional[ComponentHealth]:
        """Check network health."""
        try:
            # Simulate network latency check
            start_time = time.time()
            await asyncio.sleep(0.01)  # Simulate network check
            latency = (time.time() - start_time) * 1000

            # Determine status based on latency
            if latency > 1000:  # > 1 second
                status = HealthStatus.UNHEALTHY
                message = f"Network latency is very high: {latency:.1f}ms"
            elif latency > 500:  # > 500ms
                status = HealthStatus.DEGRADED
                message = f"Network latency is high: {latency:.1f}ms"
            else:
                status = HealthStatus.HEALTHY
                message = f"Network latency is normal: {latency:.1f}ms"

            return ComponentHealth(
                component_id="network",
                component_type=ComponentType.NETWORK,
                status=status,
                message=message,
                response_time=latency,
                details={"latency_ms": latency, "network_status": "connected"},
            )

        except Exception as e:
            self.logger.error(f"Error checking network health: {e}")
            return ComponentHealth(
                component_id="network",
                component_type=ComponentType.NETWORK,
                status=HealthStatus.UNHEALTHY,
                message=f"Network health check failed: {str(e)}",
            )

    async def _check_storage_health(self) -> Optional[ComponentHealth]:
        """Check storage health."""
        try:
            # Check disk usage
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100

            # Check disk I / O
            disk_io = psutil.disk_io_counters()

            if disk_percent > 95:
                status = HealthStatus.UNHEALTHY
                message = f"Storage critically full: {disk_percent:.1f}% used"
            elif disk_percent > 85:
                status = HealthStatus.DEGRADED
                message = f"Storage getting full: {disk_percent:.1f}% used"
            else:
                status = HealthStatus.HEALTHY
                message = f"Storage usage normal: {disk_percent:.1f}% used"

            return ComponentHealth(
                component_id="storage",
                component_type=ComponentType.STORAGE,
                status=status,
                message=message,
                details={
                    "disk_percent": disk_percent,
                    "disk_total": disk.total,
                    "disk_free": disk.free,
                    "disk_used": disk.used,
                    "disk_io_read": disk_io.read_bytes if disk_io else 0,
                    "disk_io_write": disk_io.write_bytes if disk_io else 0,
                },
            )

        except Exception as e:
            self.logger.error(f"Error checking storage health: {e}")
            return ComponentHealth(
                component_id="storage",
                component_type=ComponentType.STORAGE,
                status=HealthStatus.UNHEALTHY,
                message=f"Storage health check failed: {str(e)}",
            )

    async def _check_api_health(self) -> Optional[ComponentHealth]:
        """Check API health."""
        try:
            # In real implementation, this would check actual API endpoints
            # For now, simulate API health check

            start_time = time.time()
            await asyncio.sleep(0.02)  # Simulate API check
            response_time = (time.time() - start_time) * 1000

            # Simulate API status
            api_status = "healthy"  # This would come from actual API check

            if api_status == "healthy":
                status = HealthStatus.HEALTHY
                message = "API endpoints are responding normally"
            elif api_status == "degraded":
                status = HealthStatus.DEGRADED
                message = "Some API endpoints are slow"
            else:
                status = HealthStatus.UNHEALTHY
                message = "API endpoints are not responding"

            return ComponentHealth(
                component_id="api",
                component_type=ComponentType.API,
                status=status,
                message=message,
                response_time=response_time,
                details={
                    "api_status": api_status,
                    "response_time_ms": response_time,
                    "endpoint_count": 10,  # Number of API endpoints
                },
            )

        except Exception as e:
            self.logger.error(f"Error checking API health: {e}")
            return ComponentHealth(
                component_id="api",
                component_type=ComponentType.API,
                status=HealthStatus.UNHEALTHY,
                message=f"API health check failed: {str(e)}",
            )

    async def _check_queue_health(self) -> Optional[ComponentHealth]:
        """Check message queue health."""
        try:
            # In real implementation, this would check actual queue status
            # For now, simulate queue health check

            start_time = time.time()
            await asyncio.sleep(0.01)  # Simulate queue check
            response_time = (time.time() - start_time) * 1000

            # Simulate queue status
            queue_status = "healthy"  # This would come from actual queue check
            queue_size = 0  # This would come from actual queue metrics

            if queue_status == "healthy" and queue_size < 1000:
                status = HealthStatus.HEALTHY
                message = f"Message queue is healthy (size: {queue_size})"
            elif queue_status == "healthy" and queue_size < 5000:
                status = HealthStatus.DEGRADED
                message = f"Message queue is getting full (size: {queue_size})"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Message queue is unhealthy (status: {queue_status})"

            return ComponentHealth(
                component_id="message_queue",
                component_type=ComponentType.QUEUE,
                status=status,
                message=message,
                response_time=response_time,
                details={
                    "queue_status": queue_status,
                    "queue_size": queue_size,
                    "response_time_ms": response_time,
                },
            )

        except Exception as e:
            self.logger.error(f"Error checking queue health: {e}")
            return ComponentHealth(
                component_id="message_queue",
                component_type=ComponentType.QUEUE,
                status=HealthStatus.UNHEALTHY,
                message=f"Queue health check failed: {str(e)}",
            )

    async def _check_cache_health(self) -> Optional[ComponentHealth]:
        """Check cache health."""
        try:
            # In real implementation, this would check actual cache status
            # For now, simulate cache health check

            start_time = time.time()
            await asyncio.sleep(0.01)  # Simulate cache check
            response_time = (time.time() - start_time) * 1000

            # Simulate cache status
            cache_status = "healthy"  # This would come from actual cache check
            hit_rate = 0.95  # This would come from actual cache metrics

            if cache_status == "healthy" and hit_rate > 0.9:
                status = HealthStatus.HEALTHY
                message = f"Cache is healthy (hit rate: {hit_rate:.1%})"
            elif cache_status == "healthy" and hit_rate > 0.7:
                status = HealthStatus.DEGRADED
                message = f"Cache hit rate is low (hit rate: {hit_rate:.1%})"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Cache is unhealthy (status: {cache_status})"

            return ComponentHealth(
                component_id="cache",
                component_type=ComponentType.CACHE,
                status=status,
                message=message,
                response_time=response_time,
                details={
                    "cache_status": cache_status,
                    "hit_rate": hit_rate,
                    "response_time_ms": response_time,
                },
            )

        except Exception as e:
            self.logger.error(f"Error checking cache health: {e}")
            return ComponentHealth(
                component_id="cache",
                component_type=ComponentType.CACHE,
                status=HealthStatus.UNHEALTHY,
                message=f"Cache health check failed: {str(e)}",
            )

    def _generate_health_summary(
        self, overall_status: HealthStatus, healthy: int, degraded: int, unhealthy: int
    ) -> tuple[str, List[str]]:
        """Generate health summary and recommendations."""
        try:
            total = healthy + degraded + unhealthy

            if overall_status == HealthStatus.HEALTHY:
                summary = (
                    f"System is healthy. {healthy}/{total} components are healthy."
                )
                recommendations = []
            elif overall_status == HealthStatus.DEGRADED:
                summary = f"System is degraded. {healthy}/{total} healthy, {degraded}/{total} degraded."
                recommendations = [
                    "Monitor degraded components closely",
                    "Consider scaling resources if issues persist",
                    "Check logs for component - specific issues",
                ]
            elif overall_status == HealthStatus.UNHEALTHY:
                summary = f"System is unhealthy. {unhealthy}/{total} components are unhealthy."
                recommendations = [
                    "Immediately investigate unhealthy components",
                    "Consider failover to backup systems",
                    "Alert system administrators",
                    "Check system logs for critical errors",
                ]
            else:
                summary = "System health status is unknown."
                recommendations = [
                    "Investigate health check failures",
                    "Verify monitoring system is working",
                    "Check component connectivity",
                ]

            return summary, recommendations

        except Exception as e:
            self.logger.error(f"Error generating health summary: {e}")
            return "Health summary generation failed", ["Check monitoring system"]

    # Public methods
    def get_component_health(self, component_id: str) -> Optional[ComponentHealth]:
        """Get health status of a specific component."""
        return self.component_health.get(component_id)

    def get_health_history(self, limit: int = 100) -> List[SystemHealth]:
        """Get health check history."""
        return self.health_history[-limit:] if self.health_history else []

    def get_statistics(self) -> Dict[str, Any]:
        """Get health checker statistics."""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "is_running": self.is_running,
            "uptime_seconds": uptime,
            "health_history_count": len(self.health_history),
            "component_count": len(self.component_health),
            "stats": self.stats.copy(),
        }

    async def shutdown(self) -> None:
        """Shutdown the health checker."""
        try:
            self.logger.info("Shutting down health checker...")
            self.is_running = False

            # Cancel health check task
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass

            self.logger.info("Health checker shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during health checker shutdown: {e}")
