"""
Performance metrics collection and analysis for parallel backtesting.

Provides comprehensive performance tracking including:
- Throughput metrics
- Latency measurements
- Efficiency calculations
- Benchmark comparisons
- Performance regression detection
"""

import time
import statistics
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
import logging


@dataclass
class ThroughputMetrics:
    """Throughput performance metrics."""
    tasks_per_second: float
    tasks_per_minute: float
    tasks_per_hour: float
    data_processed_mb: float
    peak_throughput: float
    average_throughput: float


@dataclass
class LatencyMetrics:
    """Latency performance metrics."""
    p50_latency_ms: float  # 50th percentile
    p95_latency_ms: float  # 95th percentile
    p99_latency_ms: float  # 99th percentile
    average_latency_ms: float
    max_latency_ms: float
    min_latency_ms: float


@dataclass
class EfficiencyMetrics:
    """Resource efficiency metrics."""
    cpu_efficiency: float  # tasks per CPU %
    memory_efficiency: float  # tasks per MB
    parallel_efficiency: float  # actual speedup vs theoretical
    scalability_factor: float  # performance improvement with more cores


@dataclass
class PerformanceSnapshot:
    """Complete performance snapshot at a point in time."""
    timestamp: datetime
    throughput: ThroughputMetrics
    latency: LatencyMetrics
    efficiency: EfficiencyMetrics
    active_workers: int
    queued_tasks: int
    completed_tasks: int
    failed_tasks: int


class TaskTimer:
    """Context manager for timing individual tasks."""

    def __init__(self, metrics_collector: 'PerformanceMetricsCollector', task_type: str = "unknown"):
        self.metrics_collector = metrics_collector
        self.task_type = task_type
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        if self.start_time and self.end_time:
            duration_ms = (self.end_time - self.start_time) * 1000
            success = exc_type is None
            self.metrics_collector.record_task_completion(
                task_type=self.task_type,
                duration_ms=duration_ms,
                success=success
            )


class PerformanceMetricsCollector:
    """Collects and analyzes performance metrics for parallel processing."""

    def __init__(self, history_size: int = 10000, sampling_interval: float = 1.0):
        self.history_size = history_size
        self.sampling_interval = sampling_interval

        # Task completion tracking
        self.task_completion_times = deque(maxlen=history_size)
        self.task_types = defaultdict(lambda: deque(maxlen=history_size))
        self.task_success_rate = defaultdict(lambda: deque(maxlen=1000))

        # Throughput tracking
        self.throughput_window = deque(maxlen=3600)  # 1 hour of samples
        self.completed_tasks_count = 0
        self.failed_tasks_count = 0
        self.data_processed_mb = 0.0

        # Latency tracking
        self.latency_samples = deque(maxlen=history_size)

        # Resource tracking
        self.resource_samples = deque(maxlen=history_size)

        # Benchmark data
        self.baseline_performance = None
        self.peak_performance = None

        # Background collection
        self._collecting = False
        self._collection_thread = None

    def start_collection(self):
        """Start background metrics collection."""
        if self._collecting:
            return

        self._collecting = True
        self._collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self._collection_thread.start()
        logging.info("Performance metrics collection started")

    def stop_collection(self):
        """Stop background metrics collection."""
        self._collecting = False
        if self._collection_thread:
            self._collection_thread.join(timeout=5.0)
        logging.info("Performance metrics collection stopped")

    def _collection_loop(self):
        """Background collection loop."""
        while self._collecting:
            try:
                self._collect_throughput_sample()
                time.sleep(self.sampling_interval)
            except Exception as e:
                logging.error(f"Metrics collection error: {e}")

    def _collect_throughput_sample(self):
        """Collect current throughput sample."""
        current_time = time.time()

        # Count tasks completed in the last second
        recent_tasks = [
            ct for ct in self.task_completion_times
            if current_time - ct <= 1.0
        ]

        tasks_per_second = len(recent_tasks)
        self.throughput_window.append({
            "timestamp": current_time,
            "tasks_per_second": tasks_per_second
        })

    def record_task_completion(self, task_type: str, duration_ms: float, success: bool, data_size_mb: float = 0.0):
        """Record completion of a task."""
        current_time = time.time()

        # Record completion time
        self.task_completion_times.append(current_time)
        self.task_types[task_type].append({
            "timestamp": current_time,
            "duration_ms": duration_ms,
            "success": success,
            "data_size_mb": data_size_mb
        })

        # Record latency
        self.latency_samples.append(duration_ms)

        # Update counters
        if success:
            self.completed_tasks_count += 1
        else:
            self.failed_tasks_count += 1

        # Update data processed
        self.data_processed_mb += data_size_mb

        # Record success rate
        self.task_success_rate[task_type].append(1 if success else 0)

        # Update peak performance
        self._update_peak_performance()

    def _update_peak_performance(self):
        """Update peak performance metrics."""
        if not self.throughput_window:
            return

        current_tps = max(sample["tasks_per_second"] for sample in self.throughput_window)

        if self.peak_performance is None or current_tps > self.peak_performance:
            self.peak_performance = current_tps
            logging.info(f"New peak throughput: {current_tps:.2f} tasks/sec")

    def calculate_throughput_metrics(self) -> ThroughputMetrics:
        """Calculate current throughput metrics."""
        if not self.throughput_window:
            return ThroughputMetrics(0, 0, 0, self.data_processed_mb, 0, 0)

        current_time = time.time()

        # Current TPS (last 5 samples)
        recent_samples = list(self.throughput_window)[-5:]
        current_tps = statistics.mean(s["tasks_per_second"] for s in recent_samples) if recent_samples else 0

        # Average TPS (last minute)
        minute_ago = current_time - 60
        recent_tasks = [
            ct for ct in self.task_completion_times
            if ct >= minute_ago
        ]
        average_tps = len(recent_tasks) / 60.0 if recent_tasks else 0

        # Peak TPS
        peak_tps = max(sample["tasks_per_second"] for sample in self.throughput_window)

        return ThroughputMetrics(
            tasks_per_second=current_tps,
            tasks_per_minute=current_tps * 60,
            tasks_per_hour=current_tps * 3600,
            data_processed_mb=self.data_processed_mb,
            peak_throughput=peak_tps,
            average_throughput=average_tps
        )

    def calculate_latency_metrics(self) -> LatencyMetrics:
        """Calculate latency metrics."""
        if not self.latency_samples:
            return LatencyMetrics(0, 0, 0, 0, 0, 0)

        sorted_latencies = sorted(self.latency_samples)

        return LatencyMetrics(
            p50_latency_ms=statistics.median(sorted_latencies),
            p95_latency_ms=sorted_latencies[int(len(sorted_latencies) * 0.95)],
            p99_latency_ms=sorted_latencies[int(len(sorted_latencies) * 0.99)],
            average_latency_ms=statistics.mean(sorted_latencies),
            max_latency_ms=max(sorted_latencies),
            min_latency_ms=min(sorted_latencies)
        )

    def calculate_efficiency_metrics(self, active_workers: int = 1, cpu_usage: float = 0.0, memory_usage_mb: float = 0.0) -> EfficiencyMetrics:
        """Calculate efficiency metrics."""
        throughput = self.calculate_throughput_metrics()

        # CPU efficiency (tasks per CPU %)
        cpu_efficiency = (throughput.tasks_per_second / cpu_usage) if cpu_usage > 0 else 0

        # Memory efficiency (tasks per MB)
        memory_efficiency = (throughput.tasks_per_second / memory_usage_mb) if memory_usage_mb > 0 else 0

        # Parallel efficiency (actual vs theoretical speedup)
        theoretical_speedup = active_workers
        actual_speedup = throughput.tasks_per_second / throughput.average_throughput if throughput.average_throughput > 0 else 1
        parallel_efficiency = (actual_speedup / theoretical_speedup) if theoretical_speedup > 0 else 0

        # Scalability factor (improvement with more cores)
        scalability_factor = actual_speedup

        return EfficiencyMetrics(
            cpu_efficiency=cpu_efficiency,
            memory_efficiency=memory_efficiency,
            parallel_efficiency=parallel_efficiency,
            scalability_factor=scalability_factor
        )

    def get_performance_snapshot(self, active_workers: int = 1, queued_tasks: int = 0,
                                cpu_usage: float = 0.0, memory_usage_mb: float = 0.0) -> PerformanceSnapshot:
        """Get complete performance snapshot."""
        return PerformanceSnapshot(
            timestamp=datetime.now(),
            throughput=self.calculate_throughput_metrics(),
            latency=self.calculate_latency_metrics(),
            efficiency=self.calculate_efficiency_metrics(active_workers, cpu_usage, memory_usage_mb),
            active_workers=active_workers,
            queued_tasks=queued_tasks,
            completed_tasks=self.completed_tasks_count,
            failed_tasks=self.failed_tasks_count
        )

    def get_task_type_performance(self, task_type: str) -> Dict[str, Any]:
        """Get performance metrics for specific task type."""
        if task_type not in self.task_types or not self.task_types[task_type]:
            return {}

        tasks = list(self.task_types[task_type])
        durations = [t["duration_ms"] for t in tasks]
        success_count = sum(1 for t in tasks if t["success"])
        data_sizes = [t["data_size_mb"] for t in tasks]

        return {
            "task_type": task_type,
            "total_tasks": len(tasks),
            "successful_tasks": success_count,
            "success_rate": (success_count / len(tasks)) * 100 if tasks else 0,
            "average_duration_ms": statistics.mean(durations),
            "median_duration_ms": statistics.median(durations),
            "p95_duration_ms": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
            "total_data_mb": sum(data_sizes),
            "average_data_mb": statistics.mean(data_sizes) if data_sizes else 0
        }

    def detect_performance_regression(self, threshold_percent: float = 10.0) -> List[Dict[str, Any]]:
        """Detect performance regressions compared to baseline."""
        regressions = []

        if not self.baseline_performance:
            return regressions

        current_throughput = self.calculate_throughput_metrics()
        current_latency = self.calculate_latency_metrics()

        # Check throughput regression
        if self.baseline_performance.get("throughput"):
            baseline_tps = self.baseline_performance["throughput"].get("tasks_per_second", 0)
            current_tps = current_throughput.tasks_per_second

            if baseline_tps > 0:
                change_percent = ((baseline_tps - current_tps) / baseline_tps) * 100
                if change_percent > threshold_percent:
                    regressions.append({
                        "type": "throughput_regression",
                        "severity": "warning" if change_percent < threshold_percent * 2 else "critical",
                        "baseline_tps": baseline_tps,
                        "current_tps": current_tps,
                        "degradation_percent": change_percent
                    })

        # Check latency regression
        if self.baseline_performance.get("latency"):
            baseline_p95 = self.baseline_performance["latency"].get("p95_latency_ms", 0)
            current_p95 = current_latency.p95_latency_ms

            if baseline_p95 > 0:
                change_percent = ((current_p95 - baseline_p95) / baseline_p95) * 100
                if change_percent > threshold_percent:
                    regressions.append({
                        "type": "latency_regression",
                        "severity": "warning" if change_percent < threshold_percent * 2 else "critical",
                        "baseline_p95_ms": baseline_p95,
                        "current_p95_ms": current_p95,
                        "increase_percent": change_percent
                    })

        return regressions

    def set_baseline_performance(self):
        """Set current performance as baseline for future comparisons."""
        current_snapshot = self.get_performance_snapshot()
        self.baseline_performance = {
            "throughput": asdict(current_snapshot.throughput),
            "latency": asdict(current_snapshot.latency),
            "efficiency": asdict(current_snapshot.efficiency)
        }
        logging.info("Performance baseline set")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        snapshot = self.get_performance_snapshot()

        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "throughput": asdict(snapshot.throughput),
            "latency": asdict(snapshot.latency),
            "efficiency": asdict(snapshot.efficiency),
            "counts": {
                "completed": snapshot.completed_tasks,
                "failed": snapshot.failed_tasks,
                "success_rate": (snapshot.completed_tasks / (snapshot.completed_tasks + snapshot.failed_tasks) * 100)
                               if (snapshot.completed_tasks + snapshot.failed_tasks) > 0 else 0
            },
            "status": {
                "active_workers": snapshot.active_workers,
                "queued_tasks": snapshot.queued_tasks,
                "peak_throughput": self.peak_performance or 0
            },
            "task_types": {
                task_type: self.get_task_type_performance(task_type)
                for task_type in list(self.task_types.keys())[:10]  # Top 10 task types
            },
            "regressions": self.detect_performance_regression()
        }

    def export_performance_data(self, filepath: str, format: str = "json", duration_hours: int = 24):
        """Export performance data for analysis."""
        cutoff_time = time.time() - (duration_hours * 3600)

        # Filter recent data
        recent_tasks = [
            task for task in self.task_completion_times
            if task >= cutoff_time
        ]

        recent_throughput = [
            sample for sample in self.throughput_window
            if sample["timestamp"] >= cutoff_time
        ]

        data = {
            "export_timestamp": datetime.now().isoformat(),
            "duration_hours": duration_hours,
            "task_completion_times": recent_tasks,
            "throughput_samples": recent_throughput,
            "summary": self.get_performance_summary()
        }

        if format.lower() == "json":
            import json
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logging.info(f"Performance data exported to {filepath}")


# Global metrics collector
_metrics_collector: Optional[PerformanceMetricsCollector] = None


def get_metrics_collector() -> PerformanceMetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = PerformanceMetricsCollector()
    return _metrics_collector


def start_metrics_collection():
    """Start global metrics collection."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = PerformanceMetricsCollector()
    _metrics_collector.start_collection()


def stop_metrics_collection():
    """Stop global metrics collection."""
    global _metrics_collector
    if _metrics_collector:
        _metrics_collector.stop_collection()


def time_task(task_type: str = "unknown"):
    """Decorator for timing task execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            with TaskTimer(metrics, task_type):
                return func(*args, **kwargs)
        return wrapper
    return decorator