"""Anomaly detection system for real - time monitoring.

This module provides comprehensive anomaly detection capabilities using
various statistical and machine learning methods to identify unusual
patterns in system behavior and performance metrics.
"""

import asyncio
import logging
import statistics
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .real_time_monitor import SystemMetrics


class AnomalyType(str, Enum):
    """Types of anomalies."""

    STATISTICAL = "statistical"
    TREND = "trend"
    SEASONAL = "seasonal"
    PATTERN = "pattern"
    THRESHOLD = "threshold"
    MACHINE_LEARNING = "machine_learning"


class DetectionMethod(str, Enum):
    """Anomaly detection methods."""

    Z_SCORE = "z_score"
    IQR = "iqr"
    ISOLATION_FOREST = "isolation_forest"
    ONE_CLASS_SVM = "one_class_svm"
    LSTM_AUTOENCODER = "lstm_autoencoder"
    MOVING_AVERAGE = "moving_average"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"


class AnomalyAlert(BaseModel):
    """Anomaly alert model."""

    anomaly_id: str = Field(..., description="Anomaly identifier")
    anomaly_type: AnomalyType = Field(..., description="Anomaly type")
    detection_method: DetectionMethod = Field(..., description="Detection method used")

    # Anomaly details
    description: str = Field(..., description="Anomaly description")
    severity: str = Field("medium", description="Anomaly severity")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Detection confidence")

    # Affected metrics
    affected_metrics: List[str] = Field(
        default_factory=list, description="Affected metrics"
    )
    metric_values: Dict[str, float] = Field(
        default_factory=dict, description="Metric values at anomaly"
    )

    # Detection details
    detection_score: float = Field(0.0, description="Anomaly detection score")
    threshold: float = Field(0.0, description="Detection threshold")
    baseline_value: Optional[float] = Field(None, description="Baseline value")

    # Timestamps
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Detection timestamp"
    )
    start_time: Optional[datetime] = Field(None, description="Anomaly start time")
    end_time: Optional[datetime] = Field(None, description="Anomaly end time")

    class Config:
        use_enum_values = True


class AnomalyDetector:
    """Anomaly detection system for identifying unusual patterns in system metrics."""

    def __init__(self, window_size: int = 100, detection_threshold: float = 2.0):
        self.window_size = window_size
        self.detection_threshold = detection_threshold
        self.logger = logging.getLogger(__name__)

        # Anomaly detection state
        self.metrics_buffer: List["SystemMetrics"] = []
        self.anomaly_history: List[AnomalyAlert] = []
        self.baseline_metrics: Dict[str, float] = {}
        self.metric_trends: Dict[str, List[float]] = {}

        # Detection methods configuration
        self.detection_methods = {
            DetectionMethod.Z_SCORE: self._detect_z_score_anomalies,
            DetectionMethod.IQR: self._detect_iqr_anomalies,
            DetectionMethod.MOVING_AVERAGE: self._detect_moving_average_anomalies,
            DetectionMethod.SEASONAL_DECOMPOSITION: self._detect_seasonal_anomalies,
        }

        # Detection settings
        self.enabled_methods = [
            DetectionMethod.Z_SCORE,
            DetectionMethod.IQR,
            DetectionMethod.MOVING_AVERAGE,
        ]

        # Statistics
        self.stats = {
            "anomalies_detected": 0,
            "detection_methods_used": 0,
            "false_positives": 0,
            "true_positives": 0,
            "start_time": None,
        }

        # Detection task
        self.detection_task: Optional[asyncio.Task] = None
        self.is_running = False

    async def initialize(self) -> bool:
        """Initialize the anomaly detector."""
        try:
            self.logger.info("Initializing anomaly detector...")

            # Start detection task
            self.detection_task = asyncio.create_task(self._anomaly_detection_loop())

            self.is_running = True
            self.stats["start_time"] = datetime.now()
            self.logger.info("Anomaly detector initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize anomaly detector: {e}")
            return False

    async def _anomaly_detection_loop(self) -> None:
        """Main anomaly detection loop."""
        while self.is_running:
            try:
                # Update baseline metrics if we have enough data
                if len(self.metrics_buffer) >= self.window_size:
                    await self._update_baseline_metrics()

                # Wait for next detection cycle
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error in anomaly detection loop: {e}")
                await asyncio.sleep(5)

    async def detect_anomalies(
        self, metrics: List["SystemMetrics"]
    ) -> List[AnomalyAlert]:
        """Detect anomalies in a list of metrics."""
        try:
            if not metrics:
                return []

            # Add metrics to buffer
            self.metrics_buffer.extend(metrics)

            # Keep only recent metrics
            if len(self.metrics_buffer) > self.window_size * 2:
                self.metrics_buffer = self.metrics_buffer[-self.window_size * 2 :]

            # Detect anomalies using enabled methods
            all_anomalies = []

            for method in self.enabled_methods:
                if method in self.detection_methods:
                    try:
                        anomalies = await self.detection_methods[method](metrics)
                        all_anomalies.extend(anomalies)
                        self.stats["detection_methods_used"] += 1
                    except Exception as e:
                        self.logger.error(f"Error in detection method {method}: {e}")

            # Remove duplicate anomalies
            unique_anomalies = self._deduplicate_anomalies(all_anomalies)

            # Add to history
            self.anomaly_history.extend(unique_anomalies)
            self.stats["anomalies_detected"] += len(unique_anomalies)

            return unique_anomalies

        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            return []

    def _deduplicate_anomalies(
        self, anomalies: List[AnomalyAlert]
    ) -> List[AnomalyAlert]:
        """Remove duplicate anomalies based on timestamp and metric values."""
        try:
            unique_anomalies = []
            seen_anomalies = set()

            for anomaly in anomalies:
                # Create a key based on timestamp and affected metrics
                key = (
                    anomaly.timestamp.isoformat(),
                    tuple(sorted(anomaly.affected_metrics)),
                    tuple(sorted(anomaly.metric_values.items())),
                )

                if key not in seen_anomalies:
                    seen_anomalies.add(key)
                    unique_anomalies.append(anomaly)

            return unique_anomalies

        except Exception as e:
            self.logger.error(f"Error deduplicating anomalies: {e}")
            return anomalies

    async def _detect_z_score_anomalies(
        self, metrics: List["SystemMetrics"]
    ) -> List[AnomalyAlert]:
        """Detect anomalies using Z - score method."""
        try:
            anomalies = []

            # Extract metric values
            metric_data = self._extract_metric_values(metrics)

            for metric_name, values in metric_data.items():
                if len(values) < 10:  # Need enough data
                    continue

                # Calculate Z - scores
                mean = statistics.mean(values)
                stdev = statistics.stdev(values) if len(values) > 1 else 0

                if stdev == 0:
                    continue

                # Check for anomalies
                for i, value in enumerate(values):
                    z_score = abs(value - mean) / stdev

                    if z_score > self.detection_threshold:
                        anomaly = AnomalyAlert(
                            anomaly_id=f"zscore_{metric_name}_{int(datetime.now().timestamp())}_{i}",
                            anomaly_type=AnomalyType.STATISTICAL,
                            detection_method=DetectionMethod.Z_SCORE,
                            description=f"Statistical anomaly detected in {metric_name} (Z - score: {z_score:.2f})",
                            severity=(
                                "high"
                                if z_score > self.detection_threshold * 1.5
                                else "medium"
                            ),
                            confidence=min(
                                z_score / (self.detection_threshold * 2), 1.0
                            ),
                            affected_metrics=[metric_name],
                            metric_values={metric_name: value},
                            detection_score=z_score,
                            threshold=self.detection_threshold,
                            baseline_value=mean,
                        )
                        anomalies.append(anomaly)

            return anomalies

        except Exception as e:
            self.logger.error(f"Error in Z - score anomaly detection: {e}")
            return []

    async def _detect_iqr_anomalies(
        self, metrics: List["SystemMetrics"]
    ) -> List[AnomalyAlert]:
        """Detect anomalies using Interquartile Range (IQR) method."""
        try:
            anomalies = []

            # Extract metric values
            metric_data = self._extract_metric_values(metrics)

            for metric_name, values in metric_data.items():
                if len(values) < 10:  # Need enough data
                    continue

                # Calculate IQR
                sorted_values = sorted(values)
                q1 = self._percentile(sorted_values, 25)
                q3 = self._percentile(sorted_values, 75)
                iqr = q3 - q1

                if iqr == 0:
                    continue

                # Define outlier bounds
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                # Check for anomalies
                for i, value in enumerate(values):
                    if value < lower_bound or value > upper_bound:
                        distance = min(
                            abs(value - lower_bound), abs(value - upper_bound)
                        )
                        severity = "high" if distance > iqr else "medium"

                        anomaly = AnomalyAlert(
                            anomaly_id=f"iqr_{metric_name}_{int(datetime.now().timestamp())}_{i}",
                            anomaly_type=AnomalyType.STATISTICAL,
                            detection_method=DetectionMethod.IQR,
                            description=f"IQR anomaly detected in {metric_name} (value: {value:.2f}, bounds: [{lower_bound:.2f}, {upper_bound:.2f}])",
                            severity=severity,
                            confidence=min(distance / iqr, 1.0),
                            affected_metrics=[metric_name],
                            metric_values={metric_name: value},
                            detection_score=distance,
                            threshold=iqr,
                            baseline_value=(q1 + q3) / 2,
                        )
                        anomalies.append(anomaly)

            return anomalies

        except Exception as e:
            self.logger.error(f"Error in IQR anomaly detection: {e}")
            return []

    async def _detect_moving_average_anomalies(
        self, metrics: List["SystemMetrics"]
    ) -> List[AnomalyAlert]:
        """Detect anomalies using moving average method."""
        try:
            anomalies = []

            # Extract metric values
            metric_data = self._extract_metric_values(metrics)

            for metric_name, values in metric_data.items():
                if len(values) < 20:  # Need enough data for moving average
                    continue

                # Calculate moving average
                window_size = min(10, len(values) // 2)
                moving_avg = []

                for i in range(window_size, len(values)):
                    window_values = values[i - window_size : i]
                    avg = statistics.mean(window_values)
                    moving_avg.append(avg)

                # Calculate moving standard deviation
                moving_std = []
                for i in range(window_size, len(values)):
                    window_values = values[i - window_size : i]
                    std = (
                        statistics.stdev(window_values) if len(window_values) > 1 else 0
                    )
                    moving_std.append(std)

                # Check for anomalies
                for i, (value, avg, std) in enumerate(
                    zip(values[window_size:], moving_avg, moving_std)
                ):
                    if std == 0:
                        continue

                    deviation = abs(value - avg) / std

                    if deviation > self.detection_threshold:
                        anomaly = AnomalyAlert(
                            anomaly_id=f"ma_{metric_name}_{int(datetime.now().timestamp())}_{i}",
                            anomaly_type=AnomalyType.TREND,
                            detection_method=DetectionMethod.MOVING_AVERAGE,
                            description=f"Moving average anomaly detected in {metric_name} (deviation: {deviation:.2f})",
                            severity=(
                                "high"
                                if deviation > self.detection_threshold * 1.5
                                else "medium"
                            ),
                            confidence=min(
                                deviation / (self.detection_threshold * 2), 1.0
                            ),
                            affected_metrics=[metric_name],
                            metric_values={metric_name: value},
                            detection_score=deviation,
                            threshold=self.detection_threshold,
                            baseline_value=avg,
                        )
                        anomalies.append(anomaly)

            return anomalies

        except Exception as e:
            self.logger.error(f"Error in moving average anomaly detection: {e}")
            return []

    async def _detect_seasonal_anomalies(
        self, metrics: List["SystemMetrics"]
    ) -> List[AnomalyAlert]:
        """Detect anomalies using seasonal decomposition method."""
        try:
            anomalies = []

            # Extract metric values
            metric_data = self._extract_metric_values(metrics)

            for metric_name, values in metric_data.items():
                if len(values) < 50:  # Need enough data for seasonal analysis
                    continue

                # Simple seasonal decomposition (simplified)
                # In real implementation, would use more sophisticated methods

                # Calculate seasonal patterns
                seasonal_period = 24  # Assume daily patterns (24 hours)
                if len(values) < seasonal_period * 2:
                    continue

                # Calculate seasonal averages
                seasonal_avg = {}
                for i, value in enumerate(values):
                    hour = i % seasonal_period
                    if hour not in seasonal_avg:
                        seasonal_avg[hour] = []
                    seasonal_avg[hour].append(value)

                # Calculate seasonal means
                seasonal_means = {}
                for hour, hour_values in seasonal_avg.items():
                    seasonal_means[hour] = statistics.mean(hour_values)

                # Check for anomalies based on seasonal patterns
                for i, value in enumerate(values):
                    hour = i % seasonal_period
                    expected_value = seasonal_means.get(hour, statistics.mean(values))

                    # Calculate deviation from seasonal pattern
                    deviation = abs(value - expected_value)
                    seasonal_std = (
                        statistics.stdev(seasonal_avg.get(hour, []))
                        if len(seasonal_avg.get(hour, [])) > 1
                        else 0
                    )

                    if (
                        seasonal_std > 0
                        and deviation > seasonal_std * self.detection_threshold
                    ):
                        anomaly = AnomalyAlert(
                            anomaly_id=f"seasonal_{metric_name}_{int(datetime.now().timestamp())}_{i}",
                            anomaly_type=AnomalyType.SEASONAL,
                            detection_method=DetectionMethod.SEASONAL_DECOMPOSITION,
                            description=f"Seasonal anomaly detected in {metric_name} (deviation: {deviation:.2f})",
                            severity=(
                                "high"
                                if deviation
                                > seasonal_std * self.detection_threshold * 1.5
                                else "medium"
                            ),
                            confidence=min(
                                deviation
                                / (seasonal_std * self.detection_threshold * 2),
                                1.0,
                            ),
                            affected_metrics=[metric_name],
                            metric_values={metric_name: value},
                            detection_score=deviation,
                            threshold=seasonal_std * self.detection_threshold,
                            baseline_value=expected_value,
                        )
                        anomalies.append(anomaly)

            return anomalies

        except Exception as e:
            self.logger.error(f"Error in seasonal anomaly detection: {e}")
            return []

    def _extract_metric_values(
        self, metrics: List["SystemMetrics"]
    ) -> Dict[str, List[float]]:
        """Extract metric values from SystemMetrics objects."""
        try:
            metric_data = {
                "cpu_percent": [],
                "memory_percent": [],
                "disk_percent": [],
                "network_latency": [],
                "process_count": [],
                "thread_count": [],
            }

            for metric in metrics:
                metric_data["cpu_percent"].append(metric.cpu_percent)
                metric_data["memory_percent"].append(metric.memory_percent)
                metric_data["disk_percent"].append(metric.disk_percent)
                metric_data["network_latency"].append(metric.network_latency)
                metric_data["process_count"].append(float(metric.process_count))
                metric_data["thread_count"].append(float(metric.thread_count))

            return metric_data

        except Exception as e:
            self.logger.error(f"Error extracting metric values: {e}")
            return {}

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

    async def _update_baseline_metrics(self) -> None:
        """Update baseline metrics for anomaly detection."""
        try:
            if len(self.metrics_buffer) < self.window_size:
                return

            # Use recent metrics for baseline
            recent_metrics = self.metrics_buffer[-self.window_size :]
            metric_data = self._extract_metric_values(recent_metrics)

            # Update baseline for each metric
            for metric_name, values in metric_data.items():
                if values:
                    self.baseline_metrics[metric_name] = statistics.mean(values)
                    self.metric_trends[metric_name] = values[
                        -10:
                    ]  # Keep last 10 values for trend analysis

        except Exception as e:
            self.logger.error(f"Error updating baseline metrics: {e}")

    def get_anomaly_history(self, limit: int = 100) -> List[AnomalyAlert]:
        """Get recent anomaly history."""
        return self.anomaly_history[-limit:] if self.anomaly_history else []

    def get_anomaly_statistics(self) -> Dict[str, Any]:
        """Get anomaly detection statistics."""
        try:
            if not self.anomaly_history:
                return {
                    "total_anomalies": 0,
                    "anomalies_by_type": {},
                    "anomalies_by_severity": {},
                    "anomalies_by_method": {},
                }

            # Count by type
            anomalies_by_type = {}
            for anomaly in self.anomaly_history:
                anomaly_type = anomaly.anomaly_type.value
                anomalies_by_type[anomaly_type] = (
                    anomalies_by_type.get(anomaly_type, 0) + 1
                )

            # Count by severity
            anomalies_by_severity = {}
            for anomaly in self.anomaly_history:
                severity = anomaly.severity
                anomalies_by_severity[severity] = (
                    anomalies_by_severity.get(severity, 0) + 1
                )

            # Count by method
            anomalies_by_method = {}
            for anomaly in self.anomaly_history:
                method = anomaly.detection_method.value
                anomalies_by_method[method] = anomalies_by_method.get(method, 0) + 1

            return {
                "total_anomalies": len(self.anomaly_history),
                "anomalies_by_type": anomalies_by_type,
                "anomalies_by_severity": anomalies_by_severity,
                "anomalies_by_method": anomalies_by_method,
                "detection_threshold": self.detection_threshold,
                "window_size": self.window_size,
            }

        except Exception as e:
            self.logger.error(f"Error getting anomaly statistics: {e}")
            return {}

    def get_statistics(self) -> Dict[str, Any]:
        """Get anomaly detector statistics."""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "is_running": self.is_running,
            "uptime_seconds": uptime,
            "metrics_buffer_size": len(self.metrics_buffer),
            "anomaly_history_count": len(self.anomaly_history),
            "baseline_metrics_count": len(self.baseline_metrics),
            "enabled_methods": [method.value for method in self.enabled_methods],
            "stats": self.stats.copy(),
        }

    async def shutdown(self) -> None:
        """Shutdown the anomaly detector."""
        try:
            self.logger.info("Shutting down anomaly detector...")
            self.is_running = False

            # Cancel detection task
            if self.detection_task:
                self.detection_task.cancel()
                try:
                    await self.detection_task
                except asyncio.CancelledError:
                    pass

            self.logger.info("Anomaly detector shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during anomaly detector shutdown: {e}")
