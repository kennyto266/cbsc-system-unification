"""
Metrics Registry for Observability System

This module provides a centralized metrics collection and storage system
for monitoring application performance, resource usage, and business metrics.
"""

import json
import logging
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("observability.metrics_registry")


class MetricsRegistry:
    """Central registry for collecting and storing metrics"""

    def __init__(self):
        self._counters: Dict[str, Dict] = defaultdict(
            lambda: {"value": 0, "labels": set()}
        )
        self._gauges: Dict[str, Dict] = defaultdict(
            lambda: {"value": 0.0, "labels": set()}
        )
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._histogram_labels: Dict[str, Dict] = defaultdict(dict)
        self._lock = threading.RLock()
        self._export_callbacks: List[Callable] = []
        self._retention_hours = 24  # Keep metrics for 24 hours

    def increment_counter(
        self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric"""
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[name]["value"] += value
            if labels:
                self._counters[name]["labels"].add(json.dumps(labels, sort_keys=True))

            # Export to callbacks
            for callback in self._export_callbacks:
                try:
                    callback("counter", name, value, labels or {})
                except Exception as e:
                    logger.error(f"Error in export callback: {e}")

    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric value"""
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[name]["value"] = value
            if labels:
                self._gauges[name]["labels"].add(json.dumps(labels, sort_keys=True))

            # Export to callbacks
            for callback in self._export_callbacks:
                try:
                    callback("gauge", name, value, labels or {})
                except Exception as e:
                    logger.error(f"Error in export callback: {e}")

    def record_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram value"""
        with self._lock:
            key = self._make_key(name, labels)

            if labels:
                histogram_key = json.dumps(labels, sort_keys=True)
                if histogram_key not in self._histogram_labels[name]:
                    self._histogram_labels[name][histogram_key] = []
                self._histogram_labels[name][histogram_key].append(value)
            else:
                self._histograms[name].append(value)

            # Limit histogram size to prevent memory issues
            if not labels and len(self._histograms[name]) > 10000:
                self._histograms[name] = self._histograms[name][-5000:]

            # Export to callbacks
            for callback in self._export_callbacks:
                try:
                    callback("histogram", name, value, labels or {})
                except Exception as e:
                    logger.error(f"Error in export callback: {e}")

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> int:
        """Get current counter value"""
        with self._lock:
            return self._counters[name]["value"]

    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value"""
        with self._lock:
            return self._gauges[name]["value"]

    def get_histogram_stats(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Get histogram statistics"""
        with self._lock:
            if labels:
                histogram_key = json.dumps(labels, sort_keys=True)
                values = self._histogram_labels[name].get(histogram_key, [])
            else:
                values = self._histograms[name]

            if not values:
                return {
                    "count": 0,
                    "sum": 0.0,
                    "avg": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "p50": 0.0,
                    "p95": 0.0,
                    "p99": 0.0,
                }

            sorted_values = sorted(values)
            count = len(values)
            sum_values = sum(values)

            return {
                "count": count,
                "sum": sum_values,
                "avg": sum_values / count,
                "min": sorted_values[0],
                "max": sorted_values[-1],
                "p50": self._percentile(sorted_values, 0.5),
                "p95": self._percentile(sorted_values, 0.95),
                "p99": self._percentile(sorted_values, 0.99),
            }

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics snapshot"""
        with self._lock:
            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "counters": {},
                "gauges": {},
                "histograms": {},
            }

            # Get counters
            for name, data in self._counters.items():
                if data["value"] > 0:
                    result["counters"][name] = {
                        "value": data["value"],
                        "labels": list(data["labels"]),
                    }

            # Get gauges
            for name, data in self._gauges.items():
                if data["value"] != 0:
                    result["gauges"][name] = {
                        "value": data["value"],
                        "labels": list(data["labels"]),
                    }

            # Get histograms
            for name, values in self._histograms.items():
                if values:
                    result["histograms"][name] = self.get_histogram_stats(name)

            return result

    def reset(self) -> None:
        """Reset all metrics"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._histogram_labels.clear()

    def add_export_callback(self, callback: Callable) -> None:
        """Add a callback for exporting metrics"""
        self._export_callbacks.append(callback)

    def export_to_log(
        self, metric_type: str, name: str, value: Any, labels: Dict[str, str]
    ) -> None:
        """Export metrics to structured logs"""
        logger.info(
            f"Metric: {name}",
            extra={
                "metric_type": metric_type,
                "metric_name": name,
                "metric_value": value,
                "metric_labels": labels,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def export_to_json_file(self, filepath: str = "metrics_export.json") -> None:
        """Export all metrics to JSON file"""
        with self._lock:
            metrics = self.get_all_metrics()

        try:
            with open(filepath, "w") as f:
                json.dump(metrics, f, indent=2)
            logger.info(f"Metrics exported to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting metrics to {filepath}: {e}")

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create a unique key for metric"""
        if labels:
            return f"{name}:{json.dumps(labels, sort_keys=True)}"
        return name

    @staticmethod
    def _percentile(sorted_values: List[float], percentile: float) -> float:
        """Calculate percentile from sorted values"""
        if not sorted_values:
            return 0.0

        index = int(len(sorted_values) * percentile)
        if index >= len(sorted_values):
            index = len(sorted_values) - 1

        return sorted_values[index]

    def cleanup_old_metrics(self) -> None:
        """Clean up old metrics (placeholder for future implementation)"""
        # In a real implementation, you would track timestamps and remove old entries
        pass


# Global metrics registry instance
_metrics_registry = MetricsRegistry()

# Add default export callback to log all metrics
_metrics_registry.add_export_callback(_metrics_registry.export_to_log)


def get_metrics_registry() -> MetricsRegistry:
    """Get the global metrics registry instance"""
    return _metrics_registry


# Predefined metric names for consistency
class MetricNames:
    # API metrics
    API_REQUESTS_TOTAL = "api_requests_total"
    API_REQUEST_DURATION_MS = "api_request_duration_ms"
    API_REQUEST_MEMORY_USAGE_MB = "api_request_memory_usage_mb"
    API_SLOW_REQUESTS_TOTAL = "api_slow_requests_total"
    API_HIGH_MEMORY_REQUESTS_TOTAL = "api_high_memory_requests_total"

    # Function metrics
    FUNCTION_EXECUTION_DURATION_MS = "function_execution_duration_ms"
    FUNCTION_MEMORY_DELTA_MB = "function_memory_delta_mb"

    # Backtest metrics
    BACKTEST_DURATION_MS = "backtest_duration_ms"
    BACKTEST_OPTIMIZATION_DURATION_MS = "backtest_optimization_duration_ms"
    BACKTEST_STRATEGIES_TESTED = "backtest_strategies_tested"

    # System metrics
    SYSTEM_CPU_USAGE_PERCENT = "system_cpu_usage_percent"
    SYSTEM_MEMORY_USAGE_MB = "system_memory_usage_mb"
    SYSTEM_DISK_USAGE_PERCENT = "system_disk_usage_percent"

    # Business metrics
    TRADING_SIGNALS_GENERATED = "trading_signals_generated"
    STRATEGIES_OPTIMIZED = "strategies_optimized"
    DATA_FETCHES_TOTAL = "data_fetches_total"
