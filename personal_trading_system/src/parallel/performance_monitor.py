#!/usr/bin/env python3
"""
Performance Monitor for Parallel Processing System
Real-time monitoring and analysis of 32-core parallel processing performance
"""

import os
import sys
import time
import json
import threading
import logging
import psutil
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import deque
import queue

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .multi_process_scheduler import MultiProcessScheduler
from .process_pool_manager import ProcessPoolManager
from .parallel_data_processor import ParallelDataProcessor
from .memory_optimizer import MemoryOptimizer
from .result_aggregator import ResultAggregator

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Performance alert levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class PerformanceMetric(Enum):
    """Types of performance metrics"""
    CPU_UTILIZATION = "cpu_utilization"
    MEMORY_USAGE = "memory_usage"
    TASK_THROUGHPUT = "task_throughput"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    QUEUE_DEPTH = "queue_depth"
    WORKER_UTILIZATION = "worker_utilization"
    CACHE_HIT_RATE = "cache_hit_rate"
    GC_FREQUENCY = "gc_frequency"
    IOPS = "iops"
    NETWORK_IO = "network_io"


@dataclass
class PerformanceSnapshot:
    """Snapshot of system performance at a point in time"""
    timestamp: datetime
    cpu_utilization: float
    memory_usage_mb: float
    memory_usage_percent: float
    active_tasks: int
    pending_tasks: int
    completed_tasks: int
    failed_tasks: int
    worker_utilization: float
    average_task_time: float
    tasks_per_second: float
    error_rate: float
    system_load_average: List[float]
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_recv_mb: float
    network_io_sent_mb: float
    gc_collections: int
    thread_count: int
    process_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class PerformanceAlert:
    """Performance alert"""
    alert_id: str
    level: AlertLevel
    metric: PerformanceMetric
    message: str
    timestamp: datetime
    current_value: float
    threshold: float
    duration_seconds: float = 0.0
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['metric'] = self.metric.value
        data['level'] = self.level.value
        return data


@dataclass
class PerformanceThreshold:
    """Performance threshold configuration"""
    metric: PerformanceMetric
    warning_threshold: float
    critical_threshold: float
    duration_seconds: float = 60.0
    enabled: bool = True
    comparison_operator: str = ">"  # ">", "<", ">=", "<=", "=="

    def is_violated(self, current_value: float) -> Tuple[bool, AlertLevel]:
        """Check if threshold is violated"""
        if not self.enabled:
            return False, AlertLevel.INFO

        if self.comparison_operator == ">":
            if current_value >= self.critical_threshold:
                return True, AlertLevel.CRITICAL
            elif current_value >= self.warning_threshold:
                return True, AlertLevel.WARNING
        elif self.comparison_operator == "<":
            if current_value <= self.critical_threshold:
                return True, AlertLevel.CRITICAL
            elif current_value <= self.warning_threshold:
                return True, AlertLevel.WARNING
        elif self.comparison_operator == ">=":
            if current_value >= self.critical_threshold:
                return True, AlertLevel.CRITICAL
            elif current_value >= self.warning_threshold:
                return True, AlertLevel.WARNING
        elif self.comparison_operator == "<=":
            if current_value <= self.critical_threshold:
                return True, AlertLevel.CRITICAL
            elif current_value <= self.warning_threshold:
                return True, AlertLevel.WARNING

        return False, AlertLevel.INFO


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system for parallel processing

    Features:
    - Real-time monitoring of CPU, memory, I/O, and application metrics
    - Configurable performance thresholds and alerting
    - Historical data collection and trend analysis
    - Performance profiling and bottleneck identification
    - Automated alerting and notifications
    - Performance optimization recommendations
    - Resource utilization analysis
    - Scalability metrics and capacity planning
    - Custom metrics and monitoring plugins
    - Performance dashboards and reporting
    """

    def __init__(
        self,
        sampling_interval: float = 1.0,
        history_size: int = 1000,
        alert_cooldown: float = 300.0,
        enable_file_logging: bool = True,
        log_directory: str = "logs/performance",
        enable_profiling: bool = False
    ):
        self.sampling_interval = sampling_interval
        self.history_size = history_size
        self.alert_cooldown = alert_cooldown
        self.enable_file_logging = enable_file_logging
        self.log_directory = Path(log_directory)
        self.enable_profiling = enable_profiling

        # Monitoring components
        self.monitored_components: Dict[str, Any] = {}

        # Performance data
        self.performance_history: deque = deque(maxlen=history_size)
        self.current_snapshot: Optional[PerformanceSnapshot] = None
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: List[PerformanceAlert] = []

        # Thresholds and alerting
        self.thresholds: Dict[PerformanceMetric, PerformanceThreshold] = {}
        self.alert_callbacks: List[Callable] = []
        self.last_alert_times: Dict[str, datetime] = {}

        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.alert_thread: Optional[threading.Thread] = None
        self.profiling_thread: Optional[threading.Thread] = None

        # Statistics
        self.stats = {
            'total_snapshots': 0,
            'total_alerts': 0,
            'peak_cpu_usage': 0.0,
            'peak_memory_usage_mb': 0.0,
            'peak_tasks_per_second': 0.0,
            'average_response_time': 0.0,
            'uptime_seconds': 0.0,
            'monitoring_start_time': None
        }

        # Initialize default thresholds
        self._initialize_default_thresholds()

        # Setup logging
        if self.enable_file_logging:
            self._setup_file_logging()

        logger.info(f"PerformanceMonitor initialized with {sampling_interval}s interval")

    def start(self):
        """Start performance monitoring"""
        if self.is_monitoring:
            logger.warning("PerformanceMonitor is already running")
            return

        self.is_monitoring = True
        self.stats['monitoring_start_time'] = datetime.now()

        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        # Start alert processing thread
        self.alert_thread = threading.Thread(target=self._alert_processing_loop, daemon=True)
        self.alert_thread.start()

        # Start profiling thread if enabled
        if self.enable_profiling:
            self.profiling_thread = threading.Thread(target=self._profiling_loop, daemon=True)
            self.profiling_thread.start()

        logger.info("PerformanceMonitor started")

    def stop(self):
        """Stop performance monitoring"""
        if not self.is_monitoring:
            return

        logger.info("Stopping PerformanceMonitor...")
        self.is_monitoring = False

        # Wait for threads to finish
        for thread in [self.monitoring_thread, self.alert_thread, self.profiling_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=5.0)

        # Final statistics update
        if self.stats['monitoring_start_time']:
            self.stats['uptime_seconds'] = (datetime.now() - self.stats['monitoring_start_time']).total_seconds()

        logger.info("PerformanceMonitor stopped")

    def register_component(self, name: str, component: Any):
        """
        Register a component for monitoring

        Args:
            name: Component name
            component: Component instance (must have get_statistics() method)
        """
        if not hasattr(component, 'get_statistics'):
            logger.warning(f"Component {name} does not have get_statistics() method")
            return

        self.monitored_components[name] = component
        logger.info(f"Registered component for monitoring: {name}")

    def set_threshold(self, threshold: PerformanceThreshold):
        """Set a performance threshold"""
        self.thresholds[threshold.metric] = threshold
        logger.info(f"Set threshold for {threshold.metric.value}: warning={threshold.warning_threshold}, critical={threshold.critical_threshold}")

    def add_alert_callback(self, callback: Callable):
        """Add a callback function for alerts"""
        self.alert_callbacks.append(callback)

    def take_snapshot(self) -> PerformanceSnapshot:
        """Take a performance snapshot"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            net_io = psutil.net_io_counters()
            load_avg = list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0.0, 0.0, 0.0]

            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            thread_count = process.num_threads()
            process_count = len(psutil.pids())

            # Component metrics
            active_tasks = 0
            pending_tasks = 0
            completed_tasks = 0
            failed_tasks = 0
            worker_utilization = 0.0
            average_task_time = 0.0
            tasks_per_second = 0.0

            for name, component in self.monitored_components.items():
                try:
                    stats = component.get_statistics()
                    # Extract common metrics (adjust based on actual component structure)
                    if 'scheduler_stats' in stats:
                        sched_stats = stats['scheduler_stats']
                        active_tasks += sched_stats.get('completed_tasks', 0)
                        completed_tasks += sched_stats.get('completed_tasks', 0)
                        failed_tasks += sched_stats.get('failed_tasks', 0)
                        tasks_per_second = sched_stats.get('throughput_tasks_per_second', 0.0)
                        average_task_time = sched_stats.get('average_task_time', 0.0)

                    if 'pool_stats' in stats:
                        pool_stats = stats['pool_stats']
                        pending_tasks += pool_stats.get('pending_tasks', 0)
                        worker_utilization = max(worker_utilization, pool_stats.get('average_worker_utilization', 0.0))

                except Exception as e:
                    logger.debug(f"Failed to get stats for component {name}: {e}")

            # Calculate derived metrics
            error_rate = failed_tasks / max(1, completed_tasks + failed_tasks) * 100
            gc_collections = 0  # Would need access to GC stats

            snapshot = PerformanceSnapshot(
                timestamp=datetime.now(),
                cpu_utilization=cpu_percent,
                memory_usage_mb=process_memory.rss / (1024 * 1024),
                memory_usage_percent=memory.percent,
                active_tasks=active_tasks,
                pending_tasks=pending_tasks,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                worker_utilization=worker_utilization,
                average_task_time=average_task_time,
                tasks_per_second=tasks_per_second,
                error_rate=error_rate,
                system_load_average=load_avg,
                disk_io_read_mb=(disk_io.read_bytes / (1024 * 1024)) if disk_io else 0.0,
                disk_io_write_mb=(disk_io.write_bytes / (1024 * 1024)) if disk_io else 0.0,
                network_io_recv_mb=(net_io.bytes_recv / (1024 * 1024)) if net_io else 0.0,
                network_io_sent_mb=(net_io.bytes_sent / (1024 * 1024)) if net_io else 0.0,
                gc_collections=gc_collections,
                thread_count=thread_count,
                process_count=process_count
            )

            # Update statistics
            self._update_statistics(snapshot)

            return snapshot

        except Exception as e:
            logger.error(f"Failed to take performance snapshot: {e}")
            # Return empty snapshot on error
            return PerformanceSnapshot(
                timestamp=datetime.now(),
                cpu_utilization=0.0, memory_usage_mb=0.0, memory_usage_percent=0.0,
                active_tasks=0, pending_tasks=0, completed_tasks=0, failed_tasks=0,
                worker_utilization=0.0, average_task_time=0.0, tasks_per_second=0.0,
                error_rate=0.0, system_load_average=[0.0, 0.0, 0.0],
                disk_io_read_mb=0.0, disk_io_write_mb=0.0, network_io_recv_mb=0.0,
                network_io_sent_mb=0.0, gc_collections=0, thread_count=0, process_count=0
            )

    def check_thresholds(self, snapshot: PerformanceSnapshot) -> List[PerformanceAlert]:
        """Check performance thresholds and generate alerts"""
        alerts = []

        for metric, threshold in self.thresholds.items():
            if not threshold.enabled:
                continue

            # Get current value for metric
            current_value = self._get_metric_value(snapshot, metric)
            if current_value is None:
                continue

            # Check threshold violation
            is_violated, alert_level = threshold.is_violated(current_value)

            if is_violated:
                # Check alert cooldown
                alert_key = f"{metric.value}_{alert_level.value}"
                current_time = datetime.now()

                last_alert_time = self.last_alert_times.get(alert_key)
                if last_alert_time and (current_time - last_alert_time).total_seconds() < self.alert_cooldown:
                    continue  # Still in cooldown period

                # Create alert
                alert = PerformanceAlert(
                    alert_id=f"alert_{int(current_time.timestamp())}_{metric.value}",
                    level=alert_level,
                    metric=metric,
                    message=f"{metric.value.replace('_', ' ').title()} is {current_value:.2f} (threshold: {threshold.warning_threshold})",
                    timestamp=current_time,
                    current_value=current_value,
                    threshold=threshold.warning_threshold if alert_level == AlertLevel.WARNING else threshold.critical_threshold,
                    metadata={'threshold_config': asdict(threshold)}
                )

                alerts.append(alert)
                self.active_alerts[alert.alert_id] = alert
                self.last_alert_times[alert_key] = current_time

        return alerts

    def get_performance_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """Get performance summary for the last N minutes"""
        if not self.performance_history:
            return {}

        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_snapshots = [
            snapshot for snapshot in self.performance_history
            if snapshot.timestamp >= cutoff_time
        ]

        if not recent_snapshots:
            return {}

        # Calculate aggregates
        cpu_values = [s.cpu_utilization for s in recent_snapshots]
        memory_values = [s.memory_usage_percent for s in recent_snapshots]
        throughput_values = [s.tasks_per_second for s in recent_snapshots]
        response_time_values = [s.average_task_time for s in recent_snapshots]
        error_rate_values = [s.error_rate for s in recent_snapshots]

        summary = {
            'period_minutes': minutes,
            'snapshot_count': len(recent_snapshots),
            'time_range': {
                'start': recent_snapshots[0].timestamp.isoformat(),
                'end': recent_snapshots[-1].timestamp.isoformat()
            },
            'cpu_utilization': {
                'average': np.mean(cpu_values),
                'min': np.min(cpu_values),
                'max': np.max(cpu_values),
                'std': np.std(cpu_values)
            },
            'memory_usage_percent': {
                'average': np.mean(memory_values),
                'min': np.min(memory_values),
                'max': np.max(memory_values),
                'std': np.std(memory_values)
            },
            'task_throughput': {
                'average': np.mean(throughput_values),
                'min': np.min(throughput_values),
                'max': np.max(throughput_values),
                'total': sum(throughput_values) * self.sampling_interval
            },
            'response_time': {
                'average': np.mean(response_time_values),
                'min': np.min(response_time_values),
                'max': np.max(response_time_values),
                'p95': np.percentile(response_time_values, 95)
            },
            'error_rate': {
                'average': np.mean(error_rate_values),
                'max': np.max(error_rate_values),
                'total_errors': sum(s.failed_tasks for s in recent_snapshots)
            },
            'active_alerts': len(self.active_alerts),
            'total_alerts_in_period': len([
                alert for alert in self.alert_history
                if alert.timestamp >= cutoff_time
            ])
        }

        return summary

    def generate_performance_report(self, format: str = 'json') -> str:
        """Generate comprehensive performance report"""
        report_data = {
            'report_timestamp': datetime.now().isoformat(),
            'monitoring_uptime_seconds': self.stats['uptime_seconds'],
            'statistics': self.stats,
            'current_status': self.current_snapshot.to_dict() if self.current_snapshot else None,
            'performance_summary_1h': self.get_performance_summary(60),
            'performance_summary_24h': self.get_performance_summary(1440),
            'active_alerts': [alert.to_dict() for alert in self.active_alerts.values()],
            'recent_alerts': [alert.to_dict() for alert in self.alert_history[-10:]],
            'component_status': {
                name: component.get_statistics() if hasattr(component, 'get_statistics') else {}
                for name, component in self.monitored_components.items()
            },
            'thresholds': {
                metric.value: asdict(threshold)
                for metric, threshold in self.thresholds.items()
            }
        }

        if format.lower() == 'json':
            return json.dumps(report_data, indent=2, default=str)
        else:
            # Simple text report
            return self._format_text_report(report_data)

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Take performance snapshot
                snapshot = self.take_snapshot()
                self.current_snapshot = snapshot
                self.performance_history.append(snapshot)

                # Check thresholds and generate alerts
                alerts = self.check_thresholds(snapshot)
                for alert in alerts:
                    self._handle_alert(alert)

                # File logging if enabled
                if self.enable_file_logging:
                    self._log_snapshot_to_file(snapshot)

                time.sleep(self.sampling_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.sampling_interval)

    def _alert_processing_loop(self):
        """Alert processing and notification loop"""
        while self.is_monitoring:
            try:
                # Check for resolved alerts
                current_time = datetime.now()
                resolved_alerts = []

                for alert_id, alert in list(self.active_alerts.items()):
                    # Check if alert condition is still present
                    current_value = self._get_metric_value(self.current_snapshot, alert.metric)
                    if current_value is None:
                        continue

                    threshold = self.thresholds.get(alert.metric)
                    if not threshold:
                        continue

                    is_violated, _ = threshold.is_violated(current_value)
                    if not is_violated:
                        # Alert resolved
                        alert.resolved = True
                        alert.resolved_at = current_time
                        resolved_alerts.append(alert)
                        del self.active_alerts[alert_id]

                # Move resolved alerts to history
                for alert in resolved_alerts:
                    self.alert_history.append(alert)
                    self._handle_alert_resolved(alert)

                # Limit alert history size
                if len(self.alert_history) > 1000:
                    self.alert_history = self.alert_history[-1000:]

                time.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Error in alert processing loop: {e}")
                time.sleep(10)

    def _profiling_loop(self):
        """Performance profiling loop"""
        while self.is_monitoring:
            try:
                # Perform periodic profiling
                if self.enable_profiling:
                    self._perform_profiling_analysis()

                time.sleep(300)  # Profile every 5 minutes

            except Exception as e:
                logger.error(f"Error in profiling loop: {e}")
                time.sleep(300)

    def _get_metric_value(self, snapshot: PerformanceSnapshot, metric: PerformanceMetric) -> Optional[float]:
        """Get value for a specific metric from snapshot"""
        mapping = {
            PerformanceMetric.CPU_UTILIZATION: snapshot.cpu_utilization,
            PerformanceMetric.MEMORY_USAGE: snapshot.memory_usage_percent,
            PerformanceMetric.TASK_THROUGHPUT: snapshot.tasks_per_second,
            PerformanceMetric.RESPONSE_TIME: snapshot.average_task_time,
            PerformanceMetric.ERROR_RATE: snapshot.error_rate,
            PerformanceMetric.QUEUE_DEPTH: snapshot.pending_tasks,
            PerformanceMetric.WORKER_UTILIZATION: snapshot.worker_utilization,
            PerformanceMetric.GC_FREQUENCY: snapshot.gc_collections,
        }
        return mapping.get(metric)

    def _handle_alert(self, alert: PerformanceAlert):
        """Handle a new performance alert"""
        self.stats['total_alerts'] += 1

        # Log alert
        log_level = logging.WARNING if alert.level == AlertLevel.WARNING else logging.ERROR
        logger.log(log_level, f"Performance Alert [{alert.level.value.upper()}]: {alert.message}")

        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

        # Add to history
        self.alert_history.append(alert)

    def _handle_alert_resolved(self, alert: PerformanceAlert):
        """Handle an alert resolution"""
        duration = (alert.resolved_at - alert.timestamp).total_seconds()
        logger.info(f"Alert resolved: {alert.message} (duration: {duration:.1f}s)")

    def _update_statistics(self, snapshot: PerformanceSnapshot):
        """Update monitoring statistics"""
        self.stats['total_snapshots'] += 1
        self.stats['peak_cpu_usage'] = max(self.stats['peak_cpu_usage'], snapshot.cpu_utilization)
        self.stats['peak_memory_usage_mb'] = max(self.stats['peak_memory_usage_mb'], snapshot.memory_usage_mb)
        self.stats['peak_tasks_per_second'] = max(self.stats['peak_tasks_per_second'], snapshot.tasks_per_second)

        # Update average response time
        if snapshot.average_task_time > 0:
            total_responses = self.stats.get('total_responses', 0) + 1
            current_avg = self.stats.get('average_response_time', 0)
            new_avg = ((current_avg * (total_responses - 1)) + snapshot.average_task_time) / total_responses
            self.stats['average_response_time'] = new_avg
            self.stats['total_responses'] = total_responses

    def _initialize_default_thresholds(self):
        """Initialize default performance thresholds"""
        default_thresholds = [
            PerformanceThreshold(
                metric=PerformanceMetric.CPU_UTILIZATION,
                warning_threshold=80.0,
                critical_threshold=95.0,
                duration_seconds=60.0
            ),
            PerformanceThreshold(
                metric=PerformanceMetric.MEMORY_USAGE,
                warning_threshold=75.0,
                critical_threshold=90.0,
                duration_seconds=60.0
            ),
            PerformanceThreshold(
                metric=PerformanceMetric.ERROR_RATE,
                warning_threshold=5.0,
                critical_threshold=10.0,
                duration_seconds=30.0
            ),
            PerformanceThreshold(
                metric=PerformanceMetric.RESPONSE_TIME,
                warning_threshold=5.0,
                critical_threshold=10.0,
                duration_seconds=60.0
            ),
            PerformanceThreshold(
                metric=PerformanceMetric.WORKER_UTILIZATION,
                warning_threshold=85.0,
                critical_threshold=95.0,
                duration_seconds=120.0
            )
        ]

        for threshold in default_thresholds:
            self.thresholds[threshold.metric] = threshold

    def _setup_file_logging(self):
        """Setup file logging for performance data"""
        try:
            self.log_directory.mkdir(parents=True, exist_ok=True)

            # Create performance log file
            perf_log_file = self.log_directory / f"performance_{datetime.now().strftime('%Y%m%d')}.log"
            self.performance_file_handler = logging.FileHandler(perf_log_file)
            self.performance_file_handler.setLevel(logging.INFO)

            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            self.performance_file_handler.setFormatter(formatter)

            # Add to logger
            performance_logger = logging.getLogger('performance_monitor')
            performance_logger.addHandler(self.performance_file_handler)
            performance_logger.setLevel(logging.INFO)

        except Exception as e:
            logger.error(f"Failed to setup file logging: {e}")

    def _log_snapshot_to_file(self, snapshot: PerformanceSnapshot):
        """Log performance snapshot to file"""
        try:
            performance_logger = logging.getLogger('performance_monitor')
            performance_logger.info(
                f"CPU={snapshot.cpu_utilization:.1f}% "
                f"Memory={snapshot.memory_usage_percent:.1f}% "
                f"Tasks={snapshot.active_tasks}/{snapshot.pending_tasks} "
                f"Throughput={snapshot.tasks_per_second:.1f}/s "
                f"Response={snapshot.average_task_time:.3f}s "
                f"Errors={snapshot.error_rate:.1f}%"
            )
        except Exception as e:
            logger.error(f"Failed to log snapshot to file: {e}")

    def _perform_profiling_analysis(self):
        """Perform performance profiling analysis"""
        # This is a placeholder for profiling analysis
        # In practice, this would use cProfile, memory_profiler, etc.
        pass

    def _format_text_report(self, report_data: Dict[str, Any]) -> str:
        """Format performance report as text"""
        lines = [
            "PERFORMANCE MONITORING REPORT",
            "=" * 50,
            f"Report Time: {report_data['report_timestamp']}",
            f"Monitoring Uptime: {report_data['monitoring_uptime_seconds']:.1f} seconds",
            "",
            "CURRENT STATUS:",
            "-" * 20,
        ]

        if report_data['current_status']:
            status = report_data['current_status']
            lines.extend([
                f"CPU Utilization: {status['cpu_utilization']:.1f}%",
                f"Memory Usage: {status['memory_usage_percent']:.1f}% ({status['memory_usage_mb']:.1f}MB)",
                f"Active Tasks: {status['active_tasks']}",
                f"Pending Tasks: {status['pending_tasks']}",
                f"Task Throughput: {status['tasks_per_second']:.1f}/s",
                f"Average Response Time: {status['average_task_time']:.3f}s",
                f"Error Rate: {status['error_rate']:.2f}%"
            ])

        lines.extend([
            "",
            f"ACTIVE ALERTS: {report_data['active_alerts']}",
            "",
            "RECENT STATISTICS:",
            "-" * 20,
        ])

        if report_data['performance_summary_1h']:
            summary_1h = report_data['performance_summary_1h']
            lines.extend([
                f"Last Hour Average CPU: {summary_1h['cpu_utilization']['average']:.1f}%",
                f"Last Hour Average Memory: {summary_1h['memory_usage_percent']['average']:.1f}%",
                f"Last Hour Total Tasks: {summary_1h['task_throughput']['total']:.0f}",
                f"Last Hour Average Response Time: {summary_1h['response_time']['average']:.3f}s"
            ])

        return "\n".join(lines)

    def get_real_time_metrics(self) -> Dict[str, float]:
        """Get current real-time metrics"""
        if not self.current_snapshot:
            return {}

        snapshot = self.current_snapshot
        return {
            'cpu_utilization': snapshot.cpu_utilization,
            'memory_usage_percent': snapshot.memory_usage_percent,
            'memory_usage_mb': snapshot.memory_usage_mb,
            'active_tasks': float(snapshot.active_tasks),
            'pending_tasks': float(snapshot.pending_tasks),
            'tasks_per_second': snapshot.tasks_per_second,
            'average_task_time': snapshot.average_task_time,
            'error_rate': snapshot.error_rate,
            'worker_utilization': snapshot.worker_utilization,
            'disk_io_read_mb': snapshot.disk_io_read_mb,
            'disk_io_write_mb': snapshot.disk_io_write_mb,
            'network_io_recv_mb': snapshot.network_io_recv_mb,
            'network_io_sent_mb': snapshot.network_io_sent_mb
        }

    def export_performance_data(self, filename: str, format: str = 'csv'):
        """Export performance data to file"""
        if not self.performance_history:
            logger.warning("No performance data to export")
            return

        try:
            # Convert history to DataFrame
            data = [snapshot.to_dict() for snapshot in self.performance_history]
            df = pd.DataFrame(data)

            # Export based on format
            if format.lower() == 'csv':
                df.to_csv(filename, index=False)
            elif format.lower() == 'json':
                df.to_json(filename, orient='records', date_format='iso', indent=2)
            elif format.lower() == 'excel':
                df.to_excel(filename, index=False)
            else:
                raise ValueError(f"Unsupported export format: {format}")

            logger.info(f"Exported {len(data)} performance records to {filename}")

        except Exception as e:
            logger.error(f"Failed to export performance data: {e}")