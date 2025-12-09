"""Strategy monitoring system for Hong Kong quantitative trading.

This module provides comprehensive strategy monitoring capabilities including
performance tracking, health monitoring, and alerting.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from .strategy_manager import StrategyInstance, StrategyStatus


class MonitoringConfig(BaseModel):
    """Monitoring configuration model."""

    strategy_instance_id: str = Field(..., description="Strategy instance identifier")

    # Monitoring settings
    performance_monitoring: bool = Field(
        True, description="Enable performance monitoring"
    )
    health_monitoring: bool = Field(True, description="Enable health monitoring")
    risk_monitoring: bool = Field(True, description="Enable risk monitoring")
    alerting_enabled: bool = Field(True, description="Enable alerting")

    # Monitoring intervals
    performance_check_interval: int = Field(
        60, description="Performance check interval (seconds)"
    )
    health_check_interval: int = Field(
        30, description="Health check interval (seconds)"
    )
    risk_check_interval: int = Field(120, description="Risk check interval (seconds)")

    # Alert thresholds
    performance_threshold: float = Field(
        0.05, description="Performance threshold for alerts"
    )
    risk_threshold: float = Field(0.02, description="Risk threshold for alerts")
    health_threshold: float = Field(0.8, description="Health threshold for alerts")

    # Alert settings
    alert_cooldown: int = Field(300, description="Alert cooldown period (seconds)")
    max_alerts_per_hour: int = Field(10, description="Maximum alerts per hour")

    class Config:
        use_enum_values = True


class PerformanceAlert(BaseModel):
    """Performance alert model."""

    alert_id: str = Field(..., description="Alert identifier")
    strategy_instance_id: str = Field(..., description="Strategy instance identifier")

    # Alert details
    alert_type: str = Field(..., description="Alert type")
    severity: str = Field("warning", description="Alert severity")
    message: str = Field(..., description="Alert message")

    # Performance metrics
    current_value: float = Field(0.0, description="Current metric value")
    threshold_value: float = Field(0.0, description="Threshold value")
    metric_name: str = Field(..., description="Metric name")

    # Timestamps
    triggered_at: datetime = Field(
        default_factory=datetime.now, description="Alert trigger time"
    )
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgment time")
    resolved_at: Optional[datetime] = Field(None, description="Resolution time")

    # Status
    status: str = Field("active", description="Alert status")
    acknowledged_by: Optional[str] = Field(None, description="Acknowledged by")
    resolved_by: Optional[str] = Field(None, description="Resolved by")

    class Config:
        use_enum_values = True


class StrategyHealth(BaseModel):
    """Strategy health model."""

    strategy_instance_id: str = Field(..., description="Strategy instance identifier")

    # Health status
    overall_health: str = Field("unknown", description="Overall health status")
    health_score: float = Field(0.0, description="Health score (0 - 1)")

    # Component health
    performance_health: str = Field("unknown", description="Performance health")
    risk_health: str = Field("unknown", description="Risk health")
    system_health: str = Field("unknown", description="System health")

    # Health metrics
    uptime_seconds: float = Field(0.0, description="Uptime in seconds")
    last_activity: Optional[datetime] = Field(None, description="Last activity time")
    error_count: int = Field(0, description="Error count")
    warning_count: int = Field(0, description="Warning count")

    # Performance indicators
    response_time: float = Field(0.0, description="Average response time (ms)")
    throughput: float = Field(0.0, description="Throughput (operations / sec)")
    error_rate: float = Field(0.0, description="Error rate (%)")

    # Timestamps
    checked_at: datetime = Field(
        default_factory=datetime.now, description="Health check time"
    )

    class Config:
        use_enum_values = True


class StrategyMonitor:
    """Strategy monitoring system."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Monitoring state
        self.monitoring_configs: Dict[str, MonitoringConfig] = {}
        self.active_monitors: Dict[str, asyncio.Task] = {}
        self.performance_alerts: List[PerformanceAlert] = []
        self.health_history: List[StrategyHealth] = []

        # Monitoring functions
        self.performance_checkers: List[Callable] = []
        self.health_checkers: List[Callable] = []
        self.risk_checkers: List[Callable] = []
        self.alert_handlers: List[Callable] = []

        # Statistics
        self.stats = {
            "monitors_active": 0,
            "alerts_triggered": 0,
            "health_checks_performed": 0,
            "performance_checks_performed": 0,
            "risk_checks_performed": 0,
            "start_time": None,
        }

        # Monitoring state
        self.is_running = False
        self.monitoring_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """Initialize the strategy monitor."""
        try:
            self.logger.info("Initializing strategy monitor...")

            # Start monitoring task
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())

            self.is_running = True
            self.stats["start_time"] = datetime.now()
            self.logger.info("Strategy monitor initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize strategy monitor: {e}")
            return False

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_running:
            try:
                # Monitor all active strategies
                await self._monitor_all_strategies()

                # Wait for next cycle
                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _monitor_all_strategies(self) -> None:
        """Monitor all active strategies."""
        try:
            for instance_id, config in self.monitoring_configs.items():
                # Check if monitoring is due
                if await self._is_monitoring_due(instance_id, config):
                    # Perform monitoring
                    await self._monitor_strategy(instance_id, config)

        except Exception as e:
            self.logger.error(f"Error monitoring strategies: {e}")

    async def _is_monitoring_due(
        self, instance_id: str, config: MonitoringConfig
    ) -> bool:
        """Check if monitoring is due for a strategy."""
        try:
            # Simple implementation: always monitor
            # In real implementation, would check last monitoring time
            return True

        except Exception as e:
            self.logger.error(f"Error checking monitoring due: {e}")
            return False

    async def _monitor_strategy(
        self, instance_id: str, config: MonitoringConfig
    ) -> None:
        """Monitor a specific strategy."""
        try:
            # Performance monitoring
            if config.performance_monitoring:
                await self._monitor_performance(instance_id, config)

            # Health monitoring
            if config.health_monitoring:
                await self._monitor_health(instance_id, config)

            # Risk monitoring
            if config.risk_monitoring:
                await self._monitor_risk(instance_id, config)

        except Exception as e:
            self.logger.error(f"Error monitoring strategy {instance_id}: {e}")

    async def _monitor_performance(
        self, instance_id: str, config: MonitoringConfig
    ) -> None:
        """Monitor strategy performance."""
        try:
            # Run performance checkers
            for checker in self.performance_checkers:
                try:
                    result = await checker(instance_id, config)
                    if result and result.get("alert_required", False):
                        await self._trigger_performance_alert(
                            instance_id, result, config
                        )
                except Exception as e:
                    self.logger.error(f"Performance checker failed: {e}")

            self.stats["performance_checks_performed"] += 1

        except Exception as e:
            self.logger.error(f"Error monitoring performance: {e}")

    async def _monitor_health(self, instance_id: str, config: MonitoringConfig) -> None:
        """Monitor strategy health."""
        try:
            # Run health checkers
            health_results = []
            for checker in self.health_checkers:
                try:
                    result = await checker(instance_id, config)
                    if result:
                        health_results.append(result)
                except Exception as e:
                    self.logger.error(f"Health checker failed: {e}")

            # Calculate overall health
            health = await self._calculate_strategy_health(instance_id, health_results)
            self.health_history.append(health)

            # Check for health alerts
            if health.health_score < config.health_threshold:
                await self._trigger_health_alert(instance_id, health, config)

            self.stats["health_checks_performed"] += 1

        except Exception as e:
            self.logger.error(f"Error monitoring health: {e}")

    async def _monitor_risk(self, instance_id: str, config: MonitoringConfig) -> None:
        """Monitor strategy risk."""
        try:
            # Run risk checkers
            for checker in self.risk_checkers:
                try:
                    result = await checker(instance_id, config)
                    if result and result.get("alert_required", False):
                        await self._trigger_risk_alert(instance_id, result, config)
                except Exception as e:
                    self.logger.error(f"Risk checker failed: {e}")

            self.stats["risk_checks_performed"] += 1

        except Exception as e:
            self.logger.error(f"Error monitoring risk: {e}")

    async def _calculate_strategy_health(
        self, instance_id: str, health_results: List[Dict[str, Any]]
    ) -> StrategyHealth:
        """Calculate overall strategy health."""
        try:
            if not health_results:
                return StrategyHealth(
                    strategy_instance_id=instance_id,
                    overall_health="unknown",
                    health_score=0.0,
                )

            # Calculate component health scores
            performance_score = 0.0
            risk_score = 0.0
            system_score = 0.0

            for result in health_results:
                if result.get("component") == "performance":
                    performance_score = result.get("score", 0.0)
                elif result.get("component") == "risk":
                    risk_score = result.get("score", 0.0)
                elif result.get("component") == "system":
                    system_score = result.get("score", 0.0)

            # Calculate overall health score
            overall_score = (performance_score + risk_score + system_score) / 3

            # Determine health status
            if overall_score >= 0.9:
                overall_health = "excellent"
            elif overall_score >= 0.7:
                overall_health = "good"
            elif overall_score >= 0.5:
                overall_health = "fair"
            elif overall_score >= 0.3:
                overall_health = "poor"
            else:
                overall_health = "critical"

            # Determine component health
            performance_health = (
                "excellent"
                if performance_score >= 0.9
                else (
                    "good"
                    if performance_score >= 0.7
                    else "fair" if performance_score >= 0.5 else "poor"
                )
            )
            risk_health = (
                "excellent"
                if risk_score >= 0.9
                else (
                    "good"
                    if risk_score >= 0.7
                    else "fair" if risk_score >= 0.5 else "poor"
                )
            )
            system_health = (
                "excellent"
                if system_score >= 0.9
                else (
                    "good"
                    if system_score >= 0.7
                    else "fair" if system_score >= 0.5 else "poor"
                )
            )

            return StrategyHealth(
                strategy_instance_id=instance_id,
                overall_health=overall_health,
                health_score=overall_score,
                performance_health=performance_health,
                risk_health=risk_health,
                system_health=system_health,
                uptime_seconds=0.0,  # Would calculate actual uptime
                last_activity=datetime.now(),
                error_count=0,  # Would count actual errors
                warning_count=0,  # Would count actual warnings
                response_time=0.0,  # Would calculate actual response time
                throughput=0.0,  # Would calculate actual throughput
                error_rate=0.0,  # Would calculate actual error rate
            )

        except Exception as e:
            self.logger.error(f"Error calculating strategy health: {e}")
            return StrategyHealth(
                strategy_instance_id=instance_id,
                overall_health="unknown",
                health_score=0.0,
            )

    async def _trigger_performance_alert(
        self, instance_id: str, result: Dict[str, Any], config: MonitoringConfig
    ) -> None:
        """Trigger performance alert."""
        try:
            # Check alert cooldown
            if await self._is_alert_cooldown_active(instance_id, "performance"):
                return

            # Create alert
            alert = PerformanceAlert(
                alert_id=f"perf_{int(datetime.now().timestamp())}_{instance_id[:8]}",
                strategy_instance_id=instance_id,
                alert_type="performance",
                severity=result.get("severity", "warning"),
                message=result.get("message", "Performance alert"),
                current_value=result.get("current_value", 0.0),
                threshold_value=result.get("threshold_value", 0.0),
                metric_name=result.get("metric_name", "unknown"),
            )

            # Store alert
            self.performance_alerts.append(alert)
            self.stats["alerts_triggered"] += 1

            # Send alert
            await self._send_alert(alert)

            self.logger.warning(
                f"Performance alert triggered: {instance_id} - {alert.message}"
            )

        except Exception as e:
            self.logger.error(f"Error triggering performance alert: {e}")

    async def _trigger_health_alert(
        self, instance_id: str, health: StrategyHealth, config: MonitoringConfig
    ) -> None:
        """Trigger health alert."""
        try:
            # Check alert cooldown
            if await self._is_alert_cooldown_active(instance_id, "health"):
                return

            # Create alert
            alert = PerformanceAlert(
                alert_id=f"health_{int(datetime.now().timestamp())}_{instance_id[:8]}",
                strategy_instance_id=instance_id,
                alert_type="health",
                severity="critical" if health.health_score < 0.3 else "warning",
                message=f"Strategy health is {health.overall_health} (score: {health.health_score:.2f})",
                current_value=health.health_score,
                threshold_value=config.health_threshold,
                metric_name="health_score",
            )

            # Store alert
            self.performance_alerts.append(alert)
            self.stats["alerts_triggered"] += 1

            # Send alert
            await self._send_alert(alert)

            self.logger.warning(
                f"Health alert triggered: {instance_id} - {alert.message}"
            )

        except Exception as e:
            self.logger.error(f"Error triggering health alert: {e}")

    async def _trigger_risk_alert(
        self, instance_id: str, result: Dict[str, Any], config: MonitoringConfig
    ) -> None:
        """Trigger risk alert."""
        try:
            # Check alert cooldown
            if await self._is_alert_cooldown_active(instance_id, "risk"):
                return

            # Create alert
            alert = PerformanceAlert(
                alert_id=f"risk_{int(datetime.now().timestamp())}_{instance_id[:8]}",
                strategy_instance_id=instance_id,
                alert_type="risk",
                severity=result.get("severity", "warning"),
                message=result.get("message", "Risk alert"),
                current_value=result.get("current_value", 0.0),
                threshold_value=result.get("threshold_value", 0.0),
                metric_name=result.get("metric_name", "unknown"),
            )

            # Store alert
            self.performance_alerts.append(alert)
            self.stats["alerts_triggered"] += 1

            # Send alert
            await self._send_alert(alert)

            self.logger.warning(
                f"Risk alert triggered: {instance_id} - {alert.message}"
            )

        except Exception as e:
            self.logger.error(f"Error triggering risk alert: {e}")

    async def _is_alert_cooldown_active(
        self, instance_id: str, alert_type: str
    ) -> bool:
        """Check if alert cooldown is active."""
        try:
            # Simple implementation: check if alert was sent recently
            # In real implementation, would check actual cooldown periods
            return False

        except Exception as e:
            self.logger.error(f"Error checking alert cooldown: {e}")
            return False

    async def _send_alert(self, alert: PerformanceAlert) -> None:
        """Send alert to registered handlers."""
        try:
            for handler in self.alert_handlers:
                try:
                    await handler(alert)
                except Exception as e:
                    self.logger.error(f"Alert handler failed: {e}")

        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")

    # Public methods
    async def start_monitoring(
        self, instance_id: str, config: MonitoringConfig
    ) -> bool:
        """Start monitoring a strategy instance."""
        try:
            self.logger.info(f"Starting monitoring for strategy {instance_id}")

            # Store monitoring config
            self.monitoring_configs[instance_id] = config

            # Start monitoring task
            monitor_task = asyncio.create_task(
                self._monitor_strategy_loop(instance_id, config)
            )
            self.active_monitors[instance_id] = monitor_task

            self.stats["monitors_active"] += 1
            self.logger.info(f"Monitoring started for strategy {instance_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error starting monitoring: {e}")
            return False

    async def _monitor_strategy_loop(
        self, instance_id: str, config: MonitoringConfig
    ) -> None:
        """Monitor strategy loop."""
        try:
            while instance_id in self.monitoring_configs:
                # Monitor strategy
                await self._monitor_strategy(instance_id, config)

                # Wait for next check
                await asyncio.sleep(
                    min(
                        config.performance_check_interval,
                        config.health_check_interval,
                        config.risk_check_interval,
                    )
                )

        except Exception as e:
            self.logger.error(f"Error in strategy monitoring loop: {e}")
        finally:
            # Cleanup
            if instance_id in self.active_monitors:
                del self.active_monitors[instance_id]
            if instance_id in self.monitoring_configs:
                del self.monitoring_configs[instance_id]
            self.stats["monitors_active"] -= 1

    async def stop_monitoring(self, instance_id: str) -> bool:
        """Stop monitoring a strategy instance."""
        try:
            self.logger.info(f"Stopping monitoring for strategy {instance_id}")

            # Remove monitoring config
            if instance_id in self.monitoring_configs:
                del self.monitoring_configs[instance_id]

            # Cancel monitoring task
            if instance_id in self.active_monitors:
                self.active_monitors[instance_id].cancel()
                del self.active_monitors[instance_id]

            self.stats["monitors_active"] -= 1
            self.logger.info(f"Monitoring stopped for strategy {instance_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping monitoring: {e}")
            return False

    def add_performance_checker(self, checker: Callable) -> None:
        """Add performance checker function."""
        self.performance_checkers.append(checker)

    def add_health_checker(self, checker: Callable) -> None:
        """Add health checker function."""
        self.health_checkers.append(checker)

    def add_risk_checker(self, checker: Callable) -> None:
        """Add risk checker function."""
        self.risk_checkers.append(checker)

    def add_alert_handler(self, handler: Callable) -> None:
        """Add alert handler function."""
        self.alert_handlers.append(handler)

    def get_performance_alerts(
        self, instance_id: Optional[str] = None, limit: int = 100
    ) -> List[PerformanceAlert]:
        """Get performance alerts."""
        alerts = self.performance_alerts
        if instance_id:
            alerts = [a for a in alerts if a.strategy_instance_id == instance_id]
        return alerts[-limit:] if alerts else []

    def get_health_history(
        self, instance_id: Optional[str] = None, limit: int = 100
    ) -> List[StrategyHealth]:
        """Get health history."""
        health = self.health_history
        if instance_id:
            health = [h for h in health if h.strategy_instance_id == instance_id]
        return health[-limit:] if health else []

    def get_active_monitors(self) -> List[str]:
        """Get list of active monitor instance IDs."""
        return list(self.active_monitors.keys())

    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "is_running": self.is_running,
            "uptime_seconds": uptime,
            "active_monitors": len(self.active_monitors),
            "monitoring_configs": len(self.monitoring_configs),
            "performance_alerts_count": len(self.performance_alerts),
            "health_history_count": len(self.health_history),
            "stats": self.stats.copy(),
        }

    async def shutdown(self) -> None:
        """Shutdown the strategy monitor."""
        try:
            self.logger.info("Shutting down strategy monitor...")
            self.is_running = False

            # Stop all active monitors
            for instance_id in list(self.active_monitors.keys()):
                await self.stop_monitoring(instance_id)

            # Cancel monitoring task
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass

            self.logger.info("Strategy monitor shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during strategy monitor shutdown: {e}")
