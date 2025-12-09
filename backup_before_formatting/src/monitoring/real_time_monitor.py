"""Real - time monitoring system for Hong Kong quantitative trading.

This module provides comprehensive real - time monitoring capabilities for
system health, performance metrics, and automated alerting.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

import numpy as np
import psutil
from pydantic import BaseModel, Field

from .alert_manager import AlertLevel, AlertManager, AlertType
from .anomaly_detector import AnomalyDetector, AnomalyType
from .health_checker import HealthChecker, HealthStatus
from .performance_tracker import MetricType, PerformanceMetrics, PerformanceTracker


class MonitoringConfig(BaseModel):
    """Configuration for real - time monitoring."""

    # Monitoring intervals
    system_metrics_interval: float = Field(
        5.0, description="System metrics collection interval (seconds)"
    )
    health_check_interval: float = Field(
        30.0, description="Health check interval (seconds)"
    )
    performance_tracking_interval: float = Field(
        10.0, description="Performance tracking interval (seconds)"
    )
    anomaly_detection_interval: float = Field(
        60.0, description="Anomaly detection interval (seconds)"
    )

    # Thresholds
    cpu_threshold: float = Field(80.0, description="CPU usage threshold (%)")
    memory_threshold: float = Field(85.0, description="Memory usage threshold (%)")
    disk_threshold: float = Field(90.0, description="Disk usage threshold (%)")
    network_latency_threshold: float = Field(
        100.0, description="Network latency threshold (ms)"
    )

    # Alert settings
    alert_cooldown: float = Field(300.0, description="Alert cooldown period (seconds)")
    max_alerts_per_hour: int = Field(50, description="Maximum alerts per hour")

    # Performance tracking
    performance_history_size: int = Field(1000, description="Performance history size")
    anomaly_detection_window: int = Field(
        100, description="Anomaly detection window size"
    )

    # Component monitoring
    monitor_agents: bool = Field(True, description="Monitor AI agents")
    monitor_system: bool = Field(True, description="Monitor system resources")
    monitor_network: bool = Field(True, description="Monitor network connectivity")
    monitor_database: bool = Field(True, description="Monitor database connections")

    class Config:
        env_prefix = "MONITORING_"


class SystemMetrics(BaseModel):
    """System metrics model."""

    timestamp: datetime = Field(
        default_factory=datetime.now, description="Metrics timestamp"
    )

    # CPU metrics
    cpu_percent: float = Field(0.0, description="CPU usage percentage")
    cpu_count: int = Field(0, description="CPU core count")
    cpu_freq: float = Field(0.0, description="CPU frequency (MHz)")
    load_average: List[float] = Field(default_factory=list, description="Load average")

    # Memory metrics
    memory_total: int = Field(0, description="Total memory (bytes)")
    memory_available: int = Field(0, description="Available memory (bytes)")
    memory_used: int = Field(0, description="Used memory (bytes)")
    memory_percent: float = Field(0.0, description="Memory usage percentage")
    swap_total: int = Field(0, description="Total swap (bytes)")
    swap_used: int = Field(0, description="Used swap (bytes)")
    swap_percent: float = Field(0.0, description="Swap usage percentage")

    # Disk metrics
    disk_total: int = Field(0, description="Total disk space (bytes)")
    disk_used: int = Field(0, description="Used disk space (bytes)")
    disk_free: int = Field(0, description="Free disk space (bytes)")
    disk_percent: float = Field(0.0, description="Disk usage percentage")
    disk_io_read: int = Field(0, description="Disk read I / O (bytes)")
    disk_io_write: int = Field(0, description="Disk write I / O (bytes)")

    # Network metrics
    network_bytes_sent: int = Field(0, description="Network bytes sent")
    network_bytes_recv: int = Field(0, description="Network bytes received")
    network_packets_sent: int = Field(0, description="Network packets sent")
    network_packets_recv: int = Field(0, description="Network packets received")
    network_latency: float = Field(0.0, description="Network latency (ms)")

    # Process metrics
    process_count: int = Field(0, description="Total process count")
    thread_count: int = Field(0, description="Total thread count")
    open_files: int = Field(0, description="Open file count")

    # Custom metrics
    custom_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Custom metrics"
    )


class RealTimeMonitor:
    """Real - time monitoring system for the trading platform."""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Monitoring components
        self.alert_manager = AlertManager()
        self.health_checker = HealthChecker()
        self.performance_tracker = PerformanceTracker()
        self.anomaly_detector = AnomalyDetector()

        # Monitoring state
        self.is_running = False
        self.monitoring_tasks: List[asyncio.Task] = []

        # Metrics storage
        self.metrics_history: List[SystemMetrics] = []
        self.alert_history: List[Dict[str, Any]] = []

        # Alert tracking
        self.alert_counts: Dict[str, int] = {}
        self.last_alert_time: Dict[str, datetime] = {}

        # Custom metrics callbacks
        self.custom_metrics_callbacks: List[Callable] = []

        # Statistics
        self.stats = {
            "metrics_collected": 0,
            "alerts_triggered": 0,
            "health_checks": 0,
            "anomalies_detected": 0,
            "start_time": None,
        }

    async def initialize(self) -> bool:
        """Initialize the real - time monitoring system."""
        try:
            self.logger.info("Initializing real - time monitoring system...")

            # Initialize components
            if not await self.alert_manager.initialize():
                self.logger.error("Failed to initialize alert manager")
                return False

            if not await self.health_checker.initialize():
                self.logger.error("Failed to initialize health checker")
                return False

            if not await self.performance_tracker.initialize():
                self.logger.error("Failed to initialize performance tracker")
                return False

            if not await self.anomaly_detector.initialize():
                self.logger.error("Failed to initialize anomaly detector")
                return False

            # Start monitoring tasks
            await self._start_monitoring_tasks()

            self.is_running = True
            self.stats["start_time"] = datetime.now()
            self.logger.info("Real - time monitoring system initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize real - time monitoring: {e}")
            return False

    async def _start_monitoring_tasks(self) -> None:
        """Start all monitoring tasks."""
        try:
            # System metrics collection
            if self.config.monitor_system:
                task = asyncio.create_task(self._monitor_system_metrics())
                self.monitoring_tasks.append(task)

            # Health checking
            task = asyncio.create_task(self._monitor_health())
            self.monitoring_tasks.append(task)

            # Performance tracking
            task = asyncio.create_task(self._monitor_performance())
            self.monitoring_tasks.append(task)

            # Anomaly detection
            task = asyncio.create_task(self._monitor_anomalies())
            self.monitoring_tasks.append(task)

            # Alert processing
            task = asyncio.create_task(self._process_alerts())
            self.monitoring_tasks.append(task)

            self.logger.info(f"Started {len(self.monitoring_tasks)} monitoring tasks")

        except Exception as e:
            self.logger.error(f"Error starting monitoring tasks: {e}")

    async def _monitor_system_metrics(self) -> None:
        """Monitor system metrics."""
        while self.is_running:
            try:
                # Collect system metrics
                metrics = await self._collect_system_metrics()

                # Store metrics
                self.metrics_history.append(metrics)

                # Trim history if too large
                if len(self.metrics_history) > self.config.performance_history_size:
                    self.metrics_history = self.metrics_history[
                        -self.config.performance_history_size :
                    ]

                # Check thresholds
                await self._check_metric_thresholds(metrics)

                # Update statistics
                self.stats["metrics_collected"] += 1

                # Wait for next interval
                await asyncio.sleep(self.config.system_metrics_interval)

            except Exception as e:
                self.logger.error(f"Error monitoring system metrics: {e}")
                await asyncio.sleep(5)

    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0
            load_average = (
                list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else []
            )

            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Disk metrics
            disk = psutil.disk_usage("/")
            disk_io = psutil.disk_io_counters()

            # Network metrics
            network = psutil.net_io_counters()

            # Process metrics
            process_count = len(psutil.pids())
            thread_count = sum(
                len(psutil.Process(p).threads())
                for p in psutil.pids()
                if psutil.pid_exists(p)
            )
            open_files = (
                len(psutil.Process().open_files())
                if hasattr(psutil.Process(), "open_files")
                else 0
            )

            # Network latency (simplified)
            network_latency = await self._measure_network_latency()

            # Custom metrics
            custom_metrics = await self._collect_custom_metrics()

            return SystemMetrics(
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                cpu_freq=cpu_freq,
                load_average=load_average,
                memory_total=memory.total,
                memory_available=memory.available,
                memory_used=memory.used,
                memory_percent=memory.percent,
                swap_total=swap.total,
                swap_used=swap.used,
                swap_percent=swap.percent,
                disk_total=disk.total,
                disk_used=disk.used,
                disk_free=disk.free,
                disk_percent=(disk.used / disk.total * 100) if disk.total > 0 else 0,
                disk_io_read=disk_io.read_bytes if disk_io else 0,
                disk_io_write=disk_io.write_bytes if disk_io else 0,
                network_bytes_sent=network.bytes_sent if network else 0,
                network_bytes_recv=network.bytes_recv if network else 0,
                network_packets_sent=network.packets_sent if network else 0,
                network_packets_recv=network.packets_recv if network else 0,
                network_latency=network_latency,
                process_count=process_count,
                thread_count=thread_count,
                open_files=open_files,
                custom_metrics=custom_metrics,
            )

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics()

    async def _measure_network_latency(self) -> float:
        """Measure network latency."""
        try:
            # Simplified latency measurement
            # In real implementation, this would ping a reliable server
            start_time = time.time()
            # Simulate network operation
            await asyncio.sleep(0.001)
            end_time = time.time()
            return (end_time - start_time) * 1000  # Convert to milliseconds
        except Exception:
            return 0.0

    async def _collect_custom_metrics(self) -> Dict[str, Any]:
        """Collect custom metrics from registered callbacks."""
        try:
            custom_metrics = {}

            for callback in self.custom_metrics_callbacks:
                try:
                    metrics = await callback()
                    if isinstance(metrics, dict):
                        custom_metrics.update(metrics)
                except Exception as e:
                    self.logger.error(f"Error in custom metrics callback: {e}")

            return custom_metrics

        except Exception as e:
            self.logger.error(f"Error collecting custom metrics: {e}")
            return {}

    async def _check_metric_thresholds(self, metrics: SystemMetrics) -> None:
        """Check metrics against thresholds and trigger alerts."""
        try:
            # CPU threshold check
            if metrics.cpu_percent > self.config.cpu_threshold:
                await self._trigger_alert(
                    alert_type=AlertType.SYSTEM_PERFORMANCE,
                    level=AlertLevel.WARNING,
                    message=f"High CPU usage: {metrics.cpu_percent:.1f}%",
                    details={
                        "metric": "cpu_percent",
                        "value": metrics.cpu_percent,
                        "threshold": self.config.cpu_threshold,
                    },
                )

            # Memory threshold check
            if metrics.memory_percent > self.config.memory_threshold:
                await self._trigger_alert(
                    alert_type=AlertType.SYSTEM_PERFORMANCE,
                    level=AlertLevel.WARNING,
                    message=f"High memory usage: {metrics.memory_percent:.1f}%",
                    details={
                        "metric": "memory_percent",
                        "value": metrics.memory_percent,
                        "threshold": self.config.memory_threshold,
                    },
                )

            # Disk threshold check
            if metrics.disk_percent > self.config.disk_threshold:
                await self._trigger_alert(
                    alert_type=AlertType.SYSTEM_PERFORMANCE,
                    level=AlertLevel.CRITICAL,
                    message=f"High disk usage: {metrics.disk_percent:.1f}%",
                    details={
                        "metric": "disk_percent",
                        "value": metrics.disk_percent,
                        "threshold": self.config.disk_threshold,
                    },
                )

            # Network latency check
            if metrics.network_latency > self.config.network_latency_threshold:
                await self._trigger_alert(
                    alert_type=AlertType.NETWORK_ISSUE,
                    level=AlertLevel.WARNING,
                    message=f"High network latency: {metrics.network_latency:.1f}ms",
                    details={
                        "metric": "network_latency",
                        "value": metrics.network_latency,
                        "threshold": self.config.network_latency_threshold,
                    },
                )

        except Exception as e:
            self.logger.error(f"Error checking metric thresholds: {e}")

    async def _monitor_health(self) -> None:
        """Monitor system health."""
        while self.is_running:
            try:
                # Perform health check
                health_status = await self.health_checker.check_system_health()

                # Process health status
                await self._process_health_status(health_status)

                # Update statistics
                self.stats["health_checks"] += 1

                # Wait for next interval
                await asyncio.sleep(self.config.health_check_interval)

            except Exception as e:
                self.logger.error(f"Error monitoring health: {e}")
                await asyncio.sleep(5)

    async def _process_health_status(self, health_status) -> None:
        """Process health check results."""
        try:
            # Check for unhealthy components
            for component, status in health_status.components.items():
                if status.status != HealthStatus.HEALTHY:
                    await self._trigger_alert(
                        alert_type=AlertType.SYSTEM_HEALTH,
                        level=(
                            AlertLevel.WARNING
                            if status.status == HealthStatus.DEGRADED
                            else AlertLevel.CRITICAL
                        ),
                        message=f"Component {component} is {status.status.value}",
                        details={
                            "component": component,
                            "status": status.status.value,
                            "message": status.message,
                        },
                    )

        except Exception as e:
            self.logger.error(f"Error processing health status: {e}")

    async def _monitor_performance(self) -> None:
        """Monitor system performance."""
        while self.is_running:
            try:
                # Collect performance metrics
                if self.metrics_history:
                    latest_metrics = self.metrics_history[-1]
                    performance_metrics = PerformanceMetrics(
                        timestamp=latest_metrics.timestamp,
                        cpu_usage=latest_metrics.cpu_percent,
                        memory_usage=latest_metrics.memory_percent,
                        disk_usage=latest_metrics.disk_percent,
                        network_latency=latest_metrics.network_latency,
                        process_count=latest_metrics.process_count,
                        thread_count=latest_metrics.thread_count,
                    )

                    # Track performance
                    await self.performance_tracker.track_metrics(performance_metrics)

                    # Check for performance alerts
                    await self._check_performance_alerts(performance_metrics)

                # Wait for next interval
                await asyncio.sleep(self.config.performance_tracking_interval)

            except Exception as e:
                self.logger.error(f"Error monitoring performance: {e}")
                await asyncio.sleep(5)

    async def _check_performance_alerts(self, metrics: PerformanceMetrics) -> None:
        """Check for performance - related alerts."""
        try:
            # Get performance trends
            trends = await self.performance_tracker.get_performance_trends()

            # Check for degrading performance
            if trends.get("cpu_trend", 0) > 0.1:  # CPU usage increasing
                await self._trigger_alert(
                    alert_type=AlertType.SYSTEM_PERFORMANCE,
                    level=AlertLevel.INFO,
                    message="CPU usage trend is increasing",
                    details={"trend": "cpu_trend", "value": trends["cpu_trend"]},
                )

            if trends.get("memory_trend", 0) > 0.1:  # Memory usage increasing
                await self._trigger_alert(
                    alert_type=AlertType.SYSTEM_PERFORMANCE,
                    level=AlertLevel.INFO,
                    message="Memory usage trend is increasing",
                    details={"trend": "memory_trend", "value": trends["memory_trend"]},
                )

        except Exception as e:
            self.logger.error(f"Error checking performance alerts: {e}")

    async def _monitor_anomalies(self) -> None:
        """Monitor for anomalies."""
        while self.is_running:
            try:
                # Detect anomalies in recent metrics
                if len(self.metrics_history) >= self.config.anomaly_detection_window:
                    recent_metrics = self.metrics_history[
                        -self.config.anomaly_detection_window :
                    ]

                    # Detect anomalies
                    anomalies = await self.anomaly_detector.detect_anomalies(
                        recent_metrics
                    )

                    # Process anomalies
                    for anomaly in anomalies:
                        await self._process_anomaly(anomaly)

                    # Update statistics
                    self.stats["anomalies_detected"] += len(anomalies)

                # Wait for next interval
                await asyncio.sleep(self.config.anomaly_detection_interval)

            except Exception as e:
                self.logger.error(f"Error monitoring anomalies: {e}")
                await asyncio.sleep(5)

    async def _process_anomaly(self, anomaly) -> None:
        """Process detected anomaly."""
        try:
            await self._trigger_alert(
                alert_type=AlertType.ANOMALY_DETECTED,
                level=AlertLevel.WARNING,
                message=f"Anomaly detected: {anomaly.description}",
                details={
                    "anomaly_type": anomaly.anomaly_type.value,
                    "severity": anomaly.severity,
                    "description": anomaly.description,
                    "timestamp": anomaly.timestamp.isoformat(),
                },
            )

        except Exception as e:
            self.logger.error(f"Error processing anomaly: {e}")

    async def _process_alerts(self) -> None:
        """Process and send alerts."""
        while self.is_running:
            try:
                # Process pending alerts
                await self.alert_manager.process_alerts()

                # Wait for next interval
                await asyncio.sleep(1.0)  # Process alerts every second

            except Exception as e:
                self.logger.error(f"Error processing alerts: {e}")
                await asyncio.sleep(5)

    async def _trigger_alert(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        message: str,
        details: Dict[str, Any],
    ) -> None:
        """Trigger an alert."""
        try:
            # Check alert cooldown
            alert_key = f"{alert_type.value}_{level.value}"
            now = datetime.now()

            if alert_key in self.last_alert_time:
                time_since_last = (
                    now - self.last_alert_time[alert_key]
                ).total_seconds()
                if time_since_last < self.config.alert_cooldown:
                    return  # Skip alert due to cooldown

            # Check alert rate limit
            if self.alert_counts.get(alert_key, 0) >= self.config.max_alerts_per_hour:
                return  # Skip alert due to rate limit

            # Create alert
            alert = {
                "id": f"alert_{int(now.timestamp())}_{alert_key}",
                "type": alert_type.value,
                "level": level.value,
                "message": message,
                "details": details,
                "timestamp": now,
                "status": "active",
            }

            # Send alert
            await self.alert_manager.send_alert(alert)

            # Update tracking
            self.last_alert_time[alert_key] = now
            self.alert_counts[alert_key] = self.alert_counts.get(alert_key, 0) + 1
            self.alert_history.append(alert)

            # Update statistics
            self.stats["alerts_triggered"] += 1

            self.logger.warning(f"Alert triggered: {level.value} - {message}")

        except Exception as e:
            self.logger.error(f"Error triggering alert: {e}")

    # Public methods
    def add_custom_metrics_callback(self, callback: Callable) -> None:
        """Add custom metrics collection callback."""
        self.custom_metrics_callbacks.append(callback)

    async def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get current system metrics."""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None

    async def get_metrics_history(self, limit: int = 100) -> List[SystemMetrics]:
        """Get metrics history."""
        return self.metrics_history[-limit:] if self.metrics_history else []

    async def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history."""
        return self.alert_history[-limit:] if self.alert_history else []

    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "is_running": self.is_running,
            "uptime_seconds": uptime,
            "metrics_count": len(self.metrics_history),
            "alerts_count": len(self.alert_history),
            "stats": self.stats.copy(),
        }

    async def shutdown(self) -> None:
        """Shutdown the monitoring system."""
        try:
            self.logger.info("Shutting down real - time monitoring system...")
            self.is_running = False

            # Cancel monitoring tasks
            for task in self.monitoring_tasks:
                task.cancel()

            # Wait for tasks to complete
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

            # Shutdown components
            await self.alert_manager.shutdown()
            await self.health_checker.shutdown()
            await self.performance_tracker.shutdown()
            await self.anomaly_detector.shutdown()

            self.logger.info("Real - time monitoring system shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during monitoring shutdown: {e}")
