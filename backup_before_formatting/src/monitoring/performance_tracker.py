"""Performance tracking system for real - time monitoring.

This module provides comprehensive performance tracking capabilities for
system metrics, trends analysis, and performance - based alerting.
"""

import asyncio
import logging
import statistics
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Types of performance metrics."""

    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_LATENCY = "network_latency"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CUSTOM = "custom"


class PerformanceMetrics(BaseModel):
    """Performance metrics model."""

    timestamp: datetime = Field(
        default_factory=datetime.now, description="Metrics timestamp"
    )

    # System metrics
    cpu_usage: float = Field(0.0, description="CPU usage percentage")
    memory_usage: float = Field(0.0, description="Memory usage percentage")
    disk_usage: float = Field(0.0, description="Disk usage percentage")
    network_latency: float = Field(0.0, description="Network latency (ms)")

    # Application metrics
    response_time: float = Field(0.0, description="Response time (ms)")
    throughput: float = Field(0.0, description="Throughput (requests / sec)")
    error_rate: float = Field(0.0, description="Error rate (%)")

    # Process metrics
    process_count: int = Field(0, description="Process count")
    thread_count: int = Field(0, description="Thread count")

    # Custom metrics
    custom_metrics: Dict[str, float] = Field(
        default_factory=dict, description="Custom metrics"
    )

    class Config:
        use_enum_values = True


class PerformanceAlert(BaseModel):
    """Performance alert model."""

    alert_id: str = Field(..., description="Alert identifier")
    metric_type: MetricType = Field(..., description="Metric type")
    alert_type: str = Field(..., description="Alert type")
    message: str = Field(..., description="Alert message")

    # Alert details
    current_value: float = Field(..., description="Current metric value")
    threshold: float = Field(..., description="Alert threshold")
    severity: str = Field("warning", description="Alert severity")

    # Timestamps
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Alert timestamp"
    )

    class Config:
        use_enum_values = True


class PerformanceTracker:
    """Performance tracking system for monitoring system performance."""

    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.logger = logging.getLogger(__name__)

        # Performance data storage
        self.metrics_history: List[PerformanceMetrics] = []
        self.performance_alerts: List[PerformanceAlert] = []

        # Performance thresholds
        self.thresholds = {
            MetricType.CPU_USAGE: {"warning": 80.0, "critical": 90.0},
            MetricType.MEMORY_USAGE: {"warning": 85.0, "critical": 95.0},
            MetricType.DISK_USAGE: {"warning": 85.0, "critical": 95.0},
            MetricType.NETWORK_LATENCY: {"warning": 100.0, "critical": 500.0},
            MetricType.RESPONSE_TIME: {"warning": 1000.0, "critical": 5000.0},
            MetricType.THROUGHPUT: {
                "warning": 0.5,
                "critical": 0.1,
            },  # Minimum throughput
            MetricType.ERROR_RATE: {"warning": 5.0, "critical": 10.0},
        }

        # Performance analysis settings
        self.trend_window = 20  # Number of data points for trend analysis
        self.anomaly_threshold = 2.0  # Standard deviations for anomaly detection

        # Statistics
        self.stats = {
            "metrics_tracked": 0,
            "alerts_generated": 0,
            "trends_analyzed": 0,
            "anomalies_detected": 0,
            "start_time": None,
        }

        # Performance tracking task
        self.tracking_task: Optional[asyncio.Task] = None
        self.is_running = False

    async def initialize(self) -> bool:
        """Initialize the performance tracker."""
        try:
            self.logger.info("Initializing performance tracker...")

            # Start performance tracking task
            self.tracking_task = asyncio.create_task(self._performance_tracking_loop())

            self.is_running = True
            self.stats["start_time"] = datetime.now()
            self.logger.info("Performance tracker initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize performance tracker: {e}")
            return False

    async def _performance_tracking_loop(self) -> None:
        """Main performance tracking loop."""
        while self.is_running:
            try:
                # Analyze performance trends
                await self._analyze_performance_trends()

                # Check for performance anomalies
                await self._check_performance_anomalies()

                # Update statistics
                self.stats["trends_analyzed"] += 1

                # Wait for next analysis
                await asyncio.sleep(60)  # Analyze every minute

            except Exception as e:
                self.logger.error(f"Error in performance tracking loop: {e}")
                await asyncio.sleep(5)

    async def track_metrics(self, metrics: PerformanceMetrics) -> None:
        """Track performance metrics."""
        try:
            # Add metrics to history
            self.metrics_history.append(metrics)

            # Trim history if too large
            if len(self.metrics_history) > self.history_size:
                self.metrics_history = self.metrics_history[-self.history_size :]

            # Check for immediate alerts
            await self._check_immediate_alerts(metrics)

            # Update statistics
            self.stats["metrics_tracked"] += 1

        except Exception as e:
            self.logger.error(f"Error tracking metrics: {e}")

    async def _check_immediate_alerts(self, metrics: PerformanceMetrics) -> None:
        """Check for immediate performance alerts."""
        try:
            # Check CPU usage
            if metrics.cpu_usage > self.thresholds[MetricType.CPU_USAGE]["critical"]:
                await self._create_performance_alert(
                    MetricType.CPU_USAGE,
                    "critical",
                    f"Critical CPU usage: {metrics.cpu_usage:.1f}%",
                    metrics.cpu_usage,
                    self.thresholds[MetricType.CPU_USAGE]["critical"],
                )
            elif metrics.cpu_usage > self.thresholds[MetricType.CPU_USAGE]["warning"]:
                await self._create_performance_alert(
                    MetricType.CPU_USAGE,
                    "warning",
                    f"High CPU usage: {metrics.cpu_usage:.1f}%",
                    metrics.cpu_usage,
                    self.thresholds[MetricType.CPU_USAGE]["warning"],
                )

            # Check memory usage
            if (
                metrics.memory_usage
                > self.thresholds[MetricType.MEMORY_USAGE]["critical"]
            ):
                await self._create_performance_alert(
                    MetricType.MEMORY_USAGE,
                    "critical",
                    f"Critical memory usage: {metrics.memory_usage:.1f}%",
                    metrics.memory_usage,
                    self.thresholds[MetricType.MEMORY_USAGE]["critical"],
                )
            elif (
                metrics.memory_usage
                > self.thresholds[MetricType.MEMORY_USAGE]["warning"]
            ):
                await self._create_performance_alert(
                    MetricType.MEMORY_USAGE,
                    "warning",
                    f"High memory usage: {metrics.memory_usage:.1f}%",
                    metrics.memory_usage,
                    self.thresholds[MetricType.MEMORY_USAGE]["warning"],
                )

            # Check disk usage
            if metrics.disk_usage > self.thresholds[MetricType.DISK_USAGE]["critical"]:
                await self._create_performance_alert(
                    MetricType.DISK_USAGE,
                    "critical",
                    f"Critical disk usage: {metrics.disk_usage:.1f}%",
                    metrics.disk_usage,
                    self.thresholds[MetricType.DISK_USAGE]["critical"],
                )
            elif metrics.disk_usage > self.thresholds[MetricType.DISK_USAGE]["warning"]:
                await self._create_performance_alert(
                    MetricType.DISK_USAGE,
                    "warning",
                    f"High disk usage: {metrics.disk_usage:.1f}%",
                    metrics.disk_usage,
                    self.thresholds[MetricType.DISK_USAGE]["warning"],
                )

            # Check network latency
            if (
                metrics.network_latency
                > self.thresholds[MetricType.NETWORK_LATENCY]["critical"]
            ):
                await self._create_performance_alert(
                    MetricType.NETWORK_LATENCY,
                    "critical",
                    f"Critical network latency: {metrics.network_latency:.1f}ms",
                    metrics.network_latency,
                    self.thresholds[MetricType.NETWORK_LATENCY]["critical"],
                )
            elif (
                metrics.network_latency
                > self.thresholds[MetricType.NETWORK_LATENCY]["warning"]
            ):
                await self._create_performance_alert(
                    MetricType.NETWORK_LATENCY,
                    "warning",
                    f"High network latency: {metrics.network_latency:.1f}ms",
                    metrics.network_latency,
                    self.thresholds[MetricType.NETWORK_LATENCY]["warning"],
                )

            # Check response time
            if (
                metrics.response_time
                > self.thresholds[MetricType.RESPONSE_TIME]["critical"]
            ):
                await self._create_performance_alert(
                    MetricType.RESPONSE_TIME,
                    "critical",
                    f"Critical response time: {metrics.response_time:.1f}ms",
                    metrics.response_time,
                    self.thresholds[MetricType.RESPONSE_TIME]["critical"],
                )
            elif (
                metrics.response_time
                > self.thresholds[MetricType.RESPONSE_TIME]["warning"]
            ):
                await self._create_performance_alert(
                    MetricType.RESPONSE_TIME,
                    "warning",
                    f"High response time: {metrics.response_time:.1f}ms",
                    metrics.response_time,
                    self.thresholds[MetricType.RESPONSE_TIME]["warning"],
                )

            # Check error rate
            if metrics.error_rate > self.thresholds[MetricType.ERROR_RATE]["critical"]:
                await self._create_performance_alert(
                    MetricType.ERROR_RATE,
                    "critical",
                    f"Critical error rate: {metrics.error_rate:.1f}%",
                    metrics.error_rate,
                    self.thresholds[MetricType.ERROR_RATE]["critical"],
                )
            elif metrics.error_rate > self.thresholds[MetricType.ERROR_RATE]["warning"]:
                await self._create_performance_alert(
                    MetricType.ERROR_RATE,
                    "warning",
                    f"High error rate: {metrics.error_rate:.1f}%",
                    metrics.error_rate,
                    self.thresholds[MetricType.ERROR_RATE]["warning"],
                )

        except Exception as e:
            self.logger.error(f"Error checking immediate alerts: {e}")

    async def _create_performance_alert(
        self,
        metric_type: MetricType,
        severity: str,
        message: str,
        current_value: float,
        threshold: float,
    ) -> None:
        """Create a performance alert."""
        try:
            alert = PerformanceAlert(
                alert_id=f"perf_{metric_type.value}_{int(datetime.now().timestamp())}",
                metric_type=metric_type,
                alert_type=f"{severity}_threshold",
                message=message,
                current_value=current_value,
                threshold=threshold,
                severity=severity,
            )

            self.performance_alerts.append(alert)
            self.stats["alerts_generated"] += 1

            self.logger.warning(f"Performance alert: {message}")

        except Exception as e:
            self.logger.error(f"Error creating performance alert: {e}")

    async def _analyze_performance_trends(self) -> None:
        """Analyze performance trends."""
        try:
            if len(self.metrics_history) < self.trend_window:
                return

            # Get recent metrics for trend analysis
            recent_metrics = self.metrics_history[-self.trend_window :]

            # Analyze trends for each metric type
            trends = {}

            # CPU trend
            cpu_values = [m.cpu_usage for m in recent_metrics]
            trends["cpu_trend"] = self._calculate_trend(cpu_values)

            # Memory trend
            memory_values = [m.memory_usage for m in recent_metrics]
            trends["memory_trend"] = self._calculate_trend(memory_values)

            # Disk trend
            disk_values = [m.disk_usage for m in recent_metrics]
            trends["disk_trend"] = self._calculate_trend(disk_values)

            # Network latency trend
            latency_values = [m.network_latency for m in recent_metrics]
            trends["latency_trend"] = self._calculate_trend(latency_values)

            # Response time trend
            response_values = [m.response_time for m in recent_metrics]
            trends["response_trend"] = self._calculate_trend(response_values)

            # Store trends for external access
            self._current_trends = trends

        except Exception as e:
            self.logger.error(f"Error analyzing performance trends: {e}")

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend slope for a series of values."""
        try:
            if len(values) < 2:
                return 0.0

            # Use linear regression to calculate trend
            x = list(range(len(values)))
            y = values

            # Calculate slope using least squares
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))

            if n * sum_x2 - sum_x ** 2 == 0:
                return 0.0

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            return slope

        except Exception as e:
            self.logger.error(f"Error calculating trend: {e}")
            return 0.0

    async def _check_performance_anomalies(self) -> None:
        """Check for performance anomalies using statistical methods."""
        try:
            if len(self.metrics_history) < self.trend_window:
                return

            # Get recent metrics for anomaly detection
            recent_metrics = self.metrics_history[-self.trend_window :]

            # Check for anomalies in each metric
            await self._detect_metric_anomalies(
                recent_metrics,
                MetricType.CPU_USAGE,
                [m.cpu_usage for m in recent_metrics],
            )
            await self._detect_metric_anomalies(
                recent_metrics,
                MetricType.MEMORY_USAGE,
                [m.memory_usage for m in recent_metrics],
            )
            await self._detect_metric_anomalies(
                recent_metrics,
                MetricType.DISK_USAGE,
                [m.disk_usage for m in recent_metrics],
            )
            await self._detect_metric_anomalies(
                recent_metrics,
                MetricType.NETWORK_LATENCY,
                [m.network_latency for m in recent_metrics],
            )
            await self._detect_metric_anomalies(
                recent_metrics,
                MetricType.RESPONSE_TIME,
                [m.response_time for m in recent_metrics],
            )

        except Exception as e:
            self.logger.error(f"Error checking performance anomalies: {e}")

    async def _detect_metric_anomalies(
        self,
        metrics: List[PerformanceMetrics],
        metric_type: MetricType,
        values: List[float],
    ) -> None:
        """Detect anomalies in a specific metric."""
        try:
            if len(values) < 10:  # Need enough data for anomaly detection
                return

            # Calculate statistical measures
            mean = statistics.mean(values)
            stdev = statistics.stdev(values) if len(values) > 1 else 0

            if stdev == 0:
                return  # No variation, no anomalies

            # Check for anomalies (values more than threshold standard deviations from mean)
            for i, value in enumerate(values):
                z_score = abs(value - mean) / stdev

                if z_score > self.anomaly_threshold:
                    # Found an anomaly
                    await self._create_performance_alert(
                        metric_type,
                        "warning",
                        f"Performance anomaly detected in {metric_type.value}: {value:.2f} (z - score: {z_score:.2f})",
                        value,
                        mean + self.anomaly_threshold * stdev,
                    )

                    self.stats["anomalies_detected"] += 1

        except Exception as e:
            self.logger.error(
                f"Error detecting metric anomalies for {metric_type}: {e}"
            )

    async def get_performance_trends(self) -> Dict[str, float]:
        """Get current performance trends."""
        return getattr(self, "_current_trends", {})

    async def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance summary for the last N hours."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = [
                m for m in self.metrics_history if m.timestamp >= cutoff_time
            ]

            if not recent_metrics:
                return {"error": "No data available for the specified time period"}

            # Calculate summary statistics
            summary = {
                "time_period_hours": hours,
                "data_points": len(recent_metrics),
                "metrics": {},
            }

            # CPU summary
            cpu_values = [m.cpu_usage for m in recent_metrics]
            summary["metrics"]["cpu"] = {
                "min": min(cpu_values),
                "max": max(cpu_values),
                "avg": statistics.mean(cpu_values),
                "median": statistics.median(cpu_values),
                "p95": self._percentile(cpu_values, 95),
                "p99": self._percentile(cpu_values, 99),
            }

            # Memory summary
            memory_values = [m.memory_usage for m in recent_metrics]
            summary["metrics"]["memory"] = {
                "min": min(memory_values),
                "max": max(memory_values),
                "avg": statistics.mean(memory_values),
                "median": statistics.median(memory_values),
                "p95": self._percentile(memory_values, 95),
                "p99": self._percentile(memory_values, 99),
            }

            # Disk summary
            disk_values = [m.disk_usage for m in recent_metrics]
            summary["metrics"]["disk"] = {
                "min": min(disk_values),
                "max": max(disk_values),
                "avg": statistics.mean(disk_values),
                "median": statistics.median(disk_values),
                "p95": self._percentile(disk_values, 95),
                "p99": self._percentile(disk_values, 99),
            }

            # Network latency summary
            latency_values = [m.network_latency for m in recent_metrics]
            summary["metrics"]["network_latency"] = {
                "min": min(latency_values),
                "max": max(latency_values),
                "avg": statistics.mean(latency_values),
                "median": statistics.median(latency_values),
                "p95": self._percentile(latency_values, 95),
                "p99": self._percentile(latency_values, 99),
            }

            # Response time summary
            response_values = [m.response_time for m in recent_metrics]
            summary["metrics"]["response_time"] = {
                "min": min(response_values),
                "max": max(response_values),
                "avg": statistics.mean(response_values),
                "median": statistics.median(response_values),
                "p95": self._percentile(response_values, 95),
                "p99": self._percentile(response_values, 99),
            }

            return summary

        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}")
            return {"error": str(e)}

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values."""
        try:
            if not values:
                return 0.0

            sorted_values = sorted(values)
            index = int((percentile / 100) * len(sorted_values))
            index = min(index, len(sorted_values) - 1)
            return sorted_values[index]

        except Exception as e:
            self.logger.error(f"Error calculating percentile: {e}")
            return 0.0

    def get_performance_alerts(self, limit: int = 100) -> List[PerformanceAlert]:
        """Get recent performance alerts."""
        return self.performance_alerts[-limit:] if self.performance_alerts else []

    def get_metrics_history(self, limit: int = 100) -> List[PerformanceMetrics]:
        """Get recent performance metrics history."""
        return self.metrics_history[-limit:] if self.metrics_history else []

    def get_statistics(self) -> Dict[str, Any]:
        """Get performance tracker statistics."""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "is_running": self.is_running,
            "uptime_seconds": uptime,
            "metrics_count": len(self.metrics_history),
            "alerts_count": len(self.performance_alerts),
            "stats": self.stats.copy(),
        }

    async def shutdown(self) -> None:
        """Shutdown the performance tracker."""
        try:
            self.logger.info("Shutting down performance tracker...")
            self.is_running = False

            # Cancel tracking task
            if self.tracking_task:
                self.tracking_task.cancel()
                try:
                    await self.tracking_task
                except asyncio.CancelledError:
                    pass

            self.logger.info("Performance tracker shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during performance tracker shutdown: {e}")
