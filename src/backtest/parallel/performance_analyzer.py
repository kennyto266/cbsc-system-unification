#!/usr/bin/env python3
"""
Performance Analysis and Monitoring System

Comprehensive performance monitoring, analysis, and optimization recommendations
for the parallel backtesting engine.
"""

import time
import logging
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
import threading
from enum import Enum

logger = logging.getLogger(__name__)


class PerformanceMetricType(Enum):
    """Types of performance metrics."""
    EXECUTION_TIME = "execution_time"
    THROUGHPUT = "throughput"
    RESOURCE_UTILIZATION = "resource_utilization"
    EFFICIENCY = "efficiency"
    ERROR_RATE = "error_rate"
    LATENCY = "latency"
    QUEUE_DEPTH = "queue_depth"


@dataclass
class PerformanceMetric:
    """Individual performance metric data point."""
    metric_type: PerformanceMetricType
    value: float
    timestamp: datetime
    task_id: Optional[str] = None
    process_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a point in time."""
    timestamp: datetime
    metrics: Dict[PerformanceMetricType, float]
    system_load: Dict[str, float]
    active_tasks: int
    queue_depth: int
    completed_tasks: int
    failed_tasks: int


@dataclass
class PerformanceTrend:
    """Analysis of performance trends over time."""
    metric_type: PerformanceMetricType
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1, higher = stronger trend
    average_value: float
    volatility: float
    anomaly_count: int


@dataclass
class BottleneckAnalysis:
    """Analysis of performance bottlenecks."""
    bottleneck_type: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    affected_metrics: List[str]
    recommendations: List[str]
    potential_impact: str


class PerformanceAnalyzer:
    """
    Advanced performance analysis system.

    Features:
    - Real-time metric collection
    - Trend analysis and anomaly detection
    - Bottleneck identification
    - Performance optimization recommendations
    - Predictive analysis
    """

    def __init__(
        self,
        history_size: int = 10000,
        analysis_window: timedelta = timedelta(minutes=30),
        anomaly_threshold: float = 2.0
    ):
        self.history_size = history_size
        self.analysis_window = analysis_window
        self.anomaly_threshold = anomaly_threshold

        # Data storage
        self.metrics_history = deque(maxlen=history_size)
        self.performance_snapshots = deque(maxlen=1000)
        self.trends = {}
        self.bottlenecks = []

        # Metric aggregations
        self.metric_aggregates = defaultdict(lambda: deque(maxlen=1000))
        self.process_metrics = defaultdict(lambda: defaultdict(deque))
        self.task_metrics = defaultdict(dict)

        # Analysis cache
        self._last_analysis_time = 0
        self._analysis_interval = 60  # seconds
        self._lock = threading.Lock()

        logger.info("Performance analyzer initialized")

    def record_metric(self, metric: PerformanceMetric) -> None:
        """
        Record a performance metric.

        Args:
            metric: Performance metric to record
        """
        with self._lock:
            self.metrics_history.append(metric)

            # Update aggregations
            self.metric_aggregates[metric.metric_type].append(metric.value)

            if metric.process_id:
                self.process_metrics[metric.process_id][metric.metric_type].append(metric.value)

            if metric.task_id:
                if metric.task_id not in self.task_metrics:
                    self.task_metrics[metric.task_id] = {}
                self.task_metrics[metric.task_id][metric.metric_type] = metric.value

            # Check for anomalies
            self._check_for_anomalies(metric)

    def take_snapshot(
        self,
        system_load: Dict[str, float],
        active_tasks: int,
        queue_depth: int,
        completed_tasks: int,
        failed_tasks: int
    ) -> None:
        """
        Take a performance snapshot.

        Args:
            system_load: Current system load metrics
            active_tasks: Number of active tasks
            queue_depth: Current queue depth
            completed_tasks: Number of completed tasks
            failed_tasks: Number of failed tasks
        """
        with self._lock:
            # Calculate current metrics
            current_metrics = self._calculate_current_metrics()

            snapshot = PerformanceSnapshot(
                timestamp=datetime.now(timezone.utc),
                metrics=current_metrics,
                system_load=system_load,
                active_tasks=active_tasks,
                queue_depth=queue_depth,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks
            )

            self.performance_snapshots.append(snapshot)

            # Trigger analysis if needed
            current_time = time.time()
            if current_time - self._last_analysis_time > self._analysis_interval:
                self._analyze_performance()
                self._last_analysis_time = current_time

    def _calculate_current_metrics(self) -> Dict[PerformanceMetricType, float]:
        """Calculate current performance metrics from recent data."""
        current_time = datetime.now(timezone.utc)
        window_start = current_time - timedelta(minutes=5)

        # Filter recent metrics
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= window_start
        ]

        if not recent_metrics:
            return {}

        # Calculate metrics by type
        metrics_by_type = defaultdict(list)
        for metric in recent_metrics:
            metrics_by_type[metric.metric_type].append(metric.value)

        current_metrics = {}
        for metric_type, values in metrics_by_type.items():
            if values:
                current_metrics[metric_type] = statistics.mean(values)

        return current_metrics

    def _check_for_anomalies(self, metric: PerformanceMetric) -> None:
        """Check if a metric value is anomalous."""
        if metric.metric_type not in self.metric_aggregates:
            return

        values = list(self.metric_aggregates[metric.metric_type])
        if len(values) < 10:  # Need enough data for anomaly detection
            return

        # Calculate statistics
        mean = statistics.mean(values[:-1])  # Exclude current value
        stdev = statistics.stdev(values[:-1]) if len(values) > 1 else 0

        if stdev == 0:
            return

        # Check for anomaly (Z-score > threshold)
        z_score = abs(metric.value - mean) / stdev
        if z_score > self.anomaly_threshold:
            logger.warning(
                f"Performance anomaly detected: {metric.metric_type.value} = {metric.value:.2f} "
                f"(Z-score: {z_score:.2f})"
            )

            # Record anomaly
            anomaly_metric = PerformanceMetric(
                metric_type=PerformanceMetricType.ERROR_RATE,
                value=z_score,
                timestamp=datetime.now(timezone.utc),
                metadata={
                    "anomaly_type": metric.metric_type.value,
                    "anomaly_value": metric.value,
                    "expected_mean": mean,
                    "z_score": z_score
                }
            )
            self.metrics_history.append(anomaly_metric)

    def _analyze_performance(self) -> None:
        """Perform comprehensive performance analysis."""
        logger.info("Starting performance analysis")

        # Analyze trends
        self._analyze_trends()

        # Identify bottlenecks
        self._identify_bottlenecks()

        # Generate recommendations
        self._generate_recommendations()

        logger.info("Performance analysis completed")

    def _analyze_trends(self) -> None:
        """Analyze performance trends over time."""
        current_time = datetime.now(timezone.utc)
        window_start = current_time - self.analysis_window

        # Filter metrics within analysis window
        window_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= window_start
        ]

        if not window_metrics:
            return

        # Group by metric type
        metrics_by_type = defaultdict(list)
        for metric in window_metrics:
            metrics_by_type[metric.metric_type].append(metric)

        # Analyze each metric type
        for metric_type, metrics in metrics_by_type.items():
            if len(metrics) < 5:  # Need enough data points
                continue

            trend = self._calculate_trend(metric_type, metrics)
            self.trends[metric_type] = trend

    def _calculate_trend(
        self,
        metric_type: PerformanceMetricType,
        metrics: List[PerformanceMetric]
    ) -> PerformanceTrend:
        """Calculate trend for a specific metric type."""
        # Extract values and timestamps
        values = [m.value for m in metrics]
        timestamps = [(m.timestamp - metrics[0].timestamp).total_seconds() for m in metrics]

        # Simple linear regression for trend
        if len(values) >= 2:
            # Calculate slope using least squares
            n = len(values)
            sum_x = sum(timestamps)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(timestamps, values))
            sum_x2 = sum(x * x for x in timestamps)

            if n * sum_x2 - sum_x * sum_x != 0:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            else:
                slope = 0

            # Determine trend direction
            if abs(slope) < 0.001:
                trend_direction = "stable"
            elif slope > 0:
                trend_direction = "increasing"
            else:
                trend_direction = "decreasing"

            # Calculate trend strength (normalized)
            trend_strength = min(abs(slope) / (statistics.stdev(values) + 0.001), 1.0)

        else:
            trend_direction = "stable"
            trend_strength = 0.0

        # Calculate other statistics
        average_value = statistics.mean(values)
        volatility = statistics.stdev(values) if len(values) > 1 else 0

        # Count anomalies
        anomaly_count = sum(
            1 for m in metrics
            if m.metadata.get("anomaly_type") == metric_type.value
        )

        return PerformanceTrend(
            metric_type=metric_type,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            average_value=average_value,
            volatility=volatility,
            anomaly_count=anomaly_count
        )

    def _identify_bottlenecks(self) -> None:
        """Identify performance bottlenecks."""
        self.bottlenecks.clear()

        if not self.performance_snapshots:
            return

        # Get recent snapshots
        recent_snapshots = list(self.performance_snapshots)[-10:]

        # Check for various bottleneck types
        bottlenecks = []

        # CPU bottleneck
        avg_cpu = statistics.mean([s.system_load.get("cpu_percent", 0) for s in recent_snapshots])
        if avg_cpu > 85:
            bottlenecks.append(BottleneckAnalysis(
                bottleneck_type="cpu",
                severity="critical" if avg_cpu > 95 else "high",
                description=f"High CPU utilization ({avg_cpu:.1f}%)",
                affected_metrics=["execution_time", "throughput"],
                recommendations=[
                    "Consider increasing CPU resources",
                    "Optimize task scheduling",
                    "Review algorithmic efficiency"
                ],
                potential_impact="Reduced task throughput and increased latency"
            ))

        # Memory bottleneck
        avg_memory = statistics.mean([s.system_load.get("memory_percent", 0) for s in recent_snapshots])
        if avg_memory > 85:
            bottlenecks.append(BottleneckAnalysis(
                bottleneck_type="memory",
                severity="critical" if avg_memory > 95 else "high",
                description=f"High memory utilization ({avg_memory:.1f}%)",
                affected_metrics=["execution_time", "efficiency"],
                recommendations=[
                    "Increase available memory",
                    "Implement memory optimization",
                    "Review data structures and algorithms"
                ],
                potential_impact="Reduced performance and potential out-of-memory errors"
            ))

        # Queue depth bottleneck
        avg_queue_depth = statistics.mean([s.queue_depth for s in recent_snapshots])
        if avg_queue_depth > 50:
            bottlenecks.append(BottleneckAnalysis(
                bottleneck_type="queue",
                severity="medium" if avg_queue_depth < 100 else "high",
                description=f"High task queue depth ({avg_queue_depth:.1f} tasks)",
                affected_metrics=["latency", "throughput"],
                recommendations=[
                    "Increase worker processes",
                    "Optimize task distribution",
                    "Implement priority-based scheduling"
                ],
                potential_impact="Increased task latency and reduced responsiveness"
            ))

        # Error rate bottleneck
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= datetime.now(timezone.utc) - timedelta(minutes=10)]
        error_metrics = [m for m in recent_metrics if m.metric_type == PerformanceMetricType.ERROR_RATE]
        if error_metrics:
            avg_error_rate = statistics.mean([m.value for m in error_metrics])
            if avg_error_rate > 0.1:  # 10% error rate
                bottlenecks.append(BottleneckAnalysis(
                    bottleneck_type="error_rate",
                    severity="high" if avg_error_rate > 0.2 else "medium",
                    description=f"High error rate ({avg_error_rate:.1%})",
                    affected_metrics=["throughput", "efficiency"],
                    recommendations=[
                        "Review error handling and recovery mechanisms",
                        "Implement circuit breaker patterns",
                        "Add comprehensive logging and monitoring"
                    ],
                    potential_impact="Reduced reliability and increased resource waste"
                ))

        self.bottlenecks = bottlenecks

    def _generate_recommendations(self) -> None:
        """Generate performance optimization recommendations."""
        # This would integrate with the bottleneck analysis
        # to provide actionable recommendations
        pass

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        with self._lock:
            if not self.performance_snapshots:
                return {"status": "no_data"}

            # Get latest snapshot
            latest = self.performance_snapshots[-1]

            # Calculate summary statistics
            summary = {
                "timestamp": latest.timestamp.isoformat(),
                "current_metrics": latest.metrics,
                "system_load": latest.system_load,
                "task_statistics": {
                    "active_tasks": latest.active_tasks,
                    "queue_depth": latest.queue_depth,
                    "completed_tasks": latest.completed_tasks,
                    "failed_tasks": latest.failed_tasks,
                    "success_rate": (
                        latest.completed_tasks / max(latest.completed_tasks + latest.failed_tasks, 1) * 100
                    )
                },
                "trends": {},
                "bottlenecks": [],
                "recommendations": []
            }

            # Add trend analysis
            for metric_type, trend in self.trends.items():
                summary["trends"][metric_type.value] = {
                    "direction": trend.trend_direction,
                    "strength": trend.trend_strength,
                    "average": trend.average_value,
                    "volatility": trend.volatility,
                    "anomalies": trend.anomaly_count
                }

            # Add bottleneck analysis
            for bottleneck in self.bottlenecks:
                summary["bottlenecks"].append({
                    "type": bottleneck.bottleneck_type,
                    "severity": bottleneck.severity,
                    "description": bottleneck.description,
                    "recommendations": bottleneck.recommendations,
                    "impact": bottleneck.potential_impact
                })

            return summary

    def get_metric_history(
        self,
        metric_type: Optional[PerformanceMetricType] = None,
        time_window: Optional[timedelta] = None
    ) -> List[PerformanceMetric]:
        """
        Get historical metric data.

        Args:
            metric_type: Type of metric to retrieve
            time_window: Time window to filter data

        Returns:
            List of performance metrics
        """
        with self._lock:
            metrics = list(self.metrics_history)

            # Filter by metric type
            if metric_type:
                metrics = [m for m in metrics if m.metric_type == metric_type]

            # Filter by time window
            if time_window:
                cutoff_time = datetime.now(timezone.utc) - time_window
                metrics = [m for m in metrics if m.timestamp >= cutoff_time]

            return metrics

    def get_process_performance(self, process_id: int) -> Dict[str, Any]:
        """Get performance statistics for a specific process."""
        with self._lock:
            if process_id not in self.process_metrics:
                return {"status": "no_data"}

            process_data = self.process_metrics[process_id]
            stats = {}

            for metric_type, values in process_data.items():
                if values:
                    stats[metric_type.value] = {
                        "count": len(values),
                        "average": statistics.mean(values),
                        "min": min(values),
                        "max": max(values),
                        "latest": values[-1] if values else None
                    }

            return {
                "process_id": process_id,
                "metrics": stats,
                "last_activity": max(
                    (m.timestamp for m in self.metrics_history if m.process_id == process_id),
                    default=None
                )
            }

    def predict_performance(
        self,
        horizon_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        Predict future performance based on trends.

        Args:
            horizon_minutes: Time horizon for predictions in minutes

        Returns:
            Performance predictions
        """
        predictions = {}

        for metric_type, trend in self.trends.items():
            if trend.trend_direction == "stable":
                predicted_value = trend.average_value
            else:
                # Simple linear extrapolation
                rate_of_change = (
                    trend.trend_strength * trend.average_value *
                    (1 if trend.trend_direction == "increasing" else -1)
                )
                predicted_value = trend.average_value + (rate_of_change * horizon_minutes / 60)

            predictions[metric_type.value] = {
                "predicted_value": predicted_value,
                "confidence": max(0, 1.0 - trend.volatility / (trend.average_value + 0.001)),
                "trend_basis": trend.trend_direction
            }

        return {
            "horizon_minutes": horizon_minutes,
            "predictions": predictions,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    def export_performance_data(
        self,
        format_type: str = "json",
        time_window: Optional[timedelta] = None
    ) -> str:
        """
        Export performance data in specified format.

        Args:
            format_type: Export format ("json", "csv")
            time_window: Time window for data export

        Returns:
            Exported data as string
        """
        metrics = self.get_metric_history(time_window=time_window)

        if format_type.lower() == "json":
            import json
            data = [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "metric_type": m.metric_type.value,
                    "value": m.value,
                    "task_id": m.task_id,
                    "process_id": m.process_id,
                    "metadata": m.metadata
                }
                for m in metrics
            ]
            return json.dumps(data, indent=2)

        elif format_type.lower() == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow([
                "timestamp", "metric_type", "value", "task_id", "process_id", "metadata"
            ])

            # Data rows
            for m in metrics:
                writer.writerow([
                    m.timestamp.isoformat(),
                    m.metric_type.value,
                    m.value,
                    m.task_id or "",
                    m.process_id or "",
                    json.dumps(m.metadata)
                ])

            return output.getvalue()

        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def clear_history(self, older_than: Optional[timedelta] = None) -> None:
        """
        Clear performance history.

        Args:
            older_than: Clear data older than this duration
        """
        with self._lock:
            if older_than is None:
                # Clear all
                self.metrics_history.clear()
                self.performance_snapshots.clear()
                self.metric_aggregates.clear()
                self.process_metrics.clear()
                self.task_metrics.clear()
                logger.info("Cleared all performance history")
            else:
                # Clear old data
                cutoff_time = datetime.now(timezone.utc) - older_than

                # Filter metrics
                self.metrics_history = deque(
                    (m for m in self.metrics_history if m.timestamp >= cutoff_time),
                    maxlen=self.history_size
                )

                # Filter snapshots
                self.performance_snapshots = deque(
                    (s for s in self.performance_snapshots if s.timestamp >= cutoff_time),
                    maxlen=1000
                )

                # Rebuild aggregations
                self._rebuild_aggregations()

                logger.info(f"Cleared performance history older than {older_than}")

    def _rebuild_aggregations(self) -> None:
        """Rebuild metric aggregations from current metrics history."""
        self.metric_aggregates.clear()
        self.process_metrics.clear()
        self.task_metrics.clear()

        for metric in self.metrics_history:
            # Update aggregations
            self.metric_aggregates[metric.metric_type].append(metric.value)

            if metric.process_id:
                self.process_metrics[metric.process_id][metric.metric_type].append(metric.value)

            if metric.task_id:
                if metric.task_id not in self.task_metrics:
                    self.task_metrics[metric.task_id] = {}
                self.task_metrics[metric.task_id][metric.metric_type] = metric.value