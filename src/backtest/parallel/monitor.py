"""
Real-time progress monitoring and resource tracking for parallel backtesting.

This module provides comprehensive monitoring capabilities including:
- Progress tracking with ETA calculations
- Resource utilization monitoring (CPU, memory, I/O)
- WebSocket server for live updates
- Performance metrics collection
- Alert management
"""

import asyncio
import json
import logging
import time
import os
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import psutil
import threading
from pathlib import Path


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ResourceMetrics:
    """System resource utilization metrics."""
    cpu_percent: float
    memory_percent: float
    memory_mb: int
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_recv_mb: float
    network_io_sent_mb: float
    timestamp: datetime


@dataclass
class TaskProgress:
    """Individual task progress information."""
    task_id: str
    task_type: str
    status: str  # pending, running, completed, failed
    progress_percent: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class Alert:
    """System alert information."""
    id: str
    level: AlertLevel
    message: str
    source: str
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False


class ResourceMonitor:
    """Monitors system resources and tracks utilization patterns."""

    def __init__(self, sampling_interval: float = 1.0, history_size: int = 3600):
        self.sampling_interval = sampling_interval
        self.history_size = history_size
        self.metrics_history = deque(maxlen=history_size)
        self._running = False
        self._thread = None
        self._last_io_counters = psutil.disk_io_counters()
        self._last_net_counters = psutil.net_io_counters()

    def start(self):
        """Start resource monitoring in background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logging.info("Resource monitoring started")

    def stop(self):
        """Stop resource monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logging.info("Resource monitoring stopped")

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._running:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                time.sleep(self.sampling_interval)
            except Exception as e:
                logging.error(f"Resource monitoring error: {e}")

    def _collect_metrics(self) -> ResourceMetrics:
        """Collect current system metrics."""
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()

        # Disk I/O
        current_io = psutil.disk_io_counters()
        disk_read_mb = 0.0
        disk_write_mb = 0.0
        if self._last_io_counters and current_io:
            disk_read_mb = (current_io.read_bytes - self._last_io_counters.read_bytes) / 1024 / 1024
            disk_write_mb = (current_io.write_bytes - self._last_io_counters.write_bytes) / 1024 / 1024
            self._last_io_counters = current_io

        # Network I/O
        current_net = psutil.net_io_counters()
        net_recv_mb = 0.0
        net_sent_mb = 0.0
        if self._last_net_counters and current_net:
            net_recv_mb = (current_net.bytes_recv - self._last_net_counters.bytes_recv) / 1024 / 1024
            net_sent_mb = (current_net.bytes_sent - self._last_net_counters.bytes_sent) / 1024 / 1024
            self._last_net_counters = current_net

        return ResourceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_mb=memory.used // 1024 // 1024,
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_io_recv_mb=net_recv_mb,
            network_io_sent_mb=net_sent_mb,
            timestamp=datetime.now()
        )

    def get_current_metrics(self) -> Optional[ResourceMetrics]:
        """Get the most recent metrics."""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_average_metrics(self, duration_minutes: int = 5) -> Optional[ResourceMetrics]:
        """Get average metrics over the specified duration."""
        if not self.metrics_history:
            return None

        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return None

        return ResourceMetrics(
            cpu_percent=sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            memory_percent=sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
            memory_mb=int(sum(m.memory_mb for m in recent_metrics) / len(recent_metrics)),
            disk_io_read_mb=sum(m.disk_io_read_mb for m in recent_metrics),
            disk_io_write_mb=sum(m.disk_io_write_mb for m in recent_metrics),
            network_io_recv_mb=sum(m.network_io_recv_mb for m in recent_metrics),
            network_io_sent_mb=sum(m.network_io_sent_mb for m in recent_metrics),
            timestamp=datetime.now()
        )


class ProgressTracker:
    """Enhanced progress tracker with intelligent ETA calculation and persistence."""

    def __init__(self, persistence_file: Optional[str] = None, enable_persistence: bool = True):
        self.tasks: Dict[str, TaskProgress] = {}
        self.task_history: List[TaskProgress] = []
        self._completion_times = defaultdict(list)  # task_type -> list of completion times
        self._task_durations = defaultdict(list)  # task_id -> list of duration samples
        self._eta_history = deque(maxlen=100)  # Recent ETA accuracy
        self.persistence_file = persistence_file
        self.enable_persistence = enable_persistence

        # Enhanced metrics
        self._total_tasks_registered = 0
        self._total_tasks_completed = 0
        self._total_execution_time = 0.0

        # Load persisted data if available
        if self.enable_persistence and self.persistence_file:
            self._load_persisted_state()

    def register_task(self, task_id: str, task_type: str, estimated_duration: Optional[float] = None):
        """Register a new task for tracking."""
        self._total_tasks_registered += 1

        # Check if task was persisted and restore state
        persisted_task = None
        if self.enable_persistence and self.persistence_file:
            persisted_task = self._get_persisted_task(task_id)

        if persisted_task:
            self.tasks[task_id] = persisted_task
            self.task_history.append(persisted_task)
        else:
            self.tasks[task_id] = TaskProgress(
                task_id=task_id,
                task_type=task_type,
                status="pending",
                progress_percent=0.0,
                estimated_completion=datetime.now() + timedelta(seconds=estimated_duration or 60) if estimated_duration else None
            )

        # Persist new task registration
        if self.enable_persistence:
            self._persist_task_state(task_id)

    def start_task(self, task_id: str):
        """Mark task as started."""
        if task_id in self.tasks:
            self.tasks[task_id].status = "running"
            self.tasks[task_id].started_at = datetime.now()

    def update_progress(self, task_id: str, progress_percent: float):
        """Update task progress and recalculate ETA."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.progress_percent = progress_percent

            # Calculate ETA based on progress rate
            if task.started_at and progress_percent > 0:
                elapsed = (datetime.now() - task.started_at).total_seconds()
                rate = progress_percent / elapsed
                if rate > 0:
                    remaining_seconds = (100 - progress_percent) / rate
                    task.estimated_completion = datetime.now() + timedelta(seconds=remaining_seconds)

    def complete_task(self, task_id: str, success: bool = True, error_message: Optional[str] = None):
        """Mark task as completed."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = "completed" if success else "failed"
            task.progress_percent = 100.0
            task.completed_at = datetime.now()

            if not success:
                task.error_message = error_message

            # Record completion time for future ETA estimates
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                self._completion_times[task.task_type].append(duration)
                # Keep only last 10 completion times
                if len(self._completion_times[task.task_type]) > 10:
                    self._completion_times[task.task_type].pop(0)

            # Move to history
            self.task_history.append(self.tasks.pop(task_id))

    def get_overall_progress(self) -> Dict[str, Any]:
        """Get overall progress summary."""
        total_tasks = len(self.tasks) + len(self.task_history)
        completed_tasks = len([t for t in self.task_history if t.status == "completed"])
        running_tasks = len([t for t in self.tasks.values() if t.status == "running"])

        overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Calculate overall ETA
        overall_eta = None
        running_task_etas = [t.estimated_completion for t in self.tasks.values()
                           if t.estimated_completion and t.status == "running"]
        if running_task_etas:
            overall_eta = max(running_task_etas)

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "running_tasks": running_tasks,
            "pending_tasks": len([t for t in self.tasks.values() if t.status == "pending"]),
            "failed_tasks": len([t for t in self.task_history if t.status == "failed"]),
            "overall_progress_percent": overall_progress,
            "estimated_completion": overall_eta.isoformat() if overall_eta else None
        }

    def get_task_status(self, task_id: str) -> Optional[TaskProgress]:
        """Get status of a specific task."""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[TaskProgress]:
        """Get all current tasks."""
        return list(self.tasks.values())

    def calculate_intelligent_eta(self, task_id: str) -> Optional[timedelta]:
        """Calculate intelligent ETA using multiple algorithms."""
        task = self.tasks.get(task_id)
        if not task or task.status != "running":
            return None

        # Method 1: Historical average for this task type
        eta_method1 = None
        if task.task_type in self._completion_times:
            avg_duration = sum(self._completion_times[task.task_type]) / len(self._completion_times[task.type])
            eta_method1 = timedelta(seconds=avg_duration)

        # Method 2: Current progress-based extrapolation
        eta_method2 = None
        if task.started_at and task.progress_percent > 0:
            elapsed = datetime.now() - task.started_at
            if task.progress_percent > 0:
                estimated_total = elapsed.total_seconds() / (task.progress_percent / 100)
                remaining_time = estimated_total - elapsed.total_seconds()
                eta_method2 = timedelta(seconds=remaining_time)

        # Method 3: Weighted combination
        if eta_method1 and eta_method2:
            # Weight historical more heavily as we get more data
            historical_weight = 0.7
            current_weight = 0.3
            combined_seconds = (eta_method1.total_seconds() * historical_weight +
                              eta_method2.total_seconds() * current_weight)
            return timedelta(seconds=combined_seconds)
        elif eta_method1:
            return eta_method1
        elif eta_method2:
            return eta_method2

        return None

    def get_eta_accuracy_stats(self) -> Dict[str, float]:
        """Calculate ETA prediction accuracy statistics."""
        if not self._eta_history:
            return {"accuracy": 0.0, "count": 0}

        accuracies = []
        for eta_actual, eta_predicted in self._eta_history:
            if eta_total_seconds > 0:
                accuracy = 1.0 - abs(eta_actual - eta_predicted) / eta_total_seconds
                accuracies.append(max(0, min(1, accuracy)))

        return {
            "accuracy": sum(accuracies) / len(accuracies) if accuracies else 0.0,
            "count": len(accuracies),
            "recent_accuracy": sum(accuracies[-10:]) / len(accuracies[-10:]) if len(accuracies) >= 10 else sum(accuracies) / len(accuracies)
        }

    def record_eta_accuracy(self, task_id: str, actual_duration: float, predicted_eta: Optional[timedelta]):
        """Record ETA prediction accuracy for learning."""
        if predicted_eta:
            self._eta_history.append((actual_duration, predicted_eta.total_seconds()))

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        task_type_stats = {}
        for task_type, durations in self._completion_times.items():
            if durations:
                task_type_stats[task_type] = {
                    "avg_duration": sum(durations) / len(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "count": len(durations)
                }

        return {
            "total_registered": self._total_tasks_registered,
            "total_completed": self._total_tasks_completed,
            "total_execution_time": self._total_execution_time,
            "avg_task_time": self._total_execution_time / max(1, self._total_tasks_completed),
            "task_type_stats": task_type_stats,
            "eta_accuracy": self.get_eta_accuracy_stats(),
            "persistence_enabled": self.enable_persistence,
            "persistence_file": self.persistence_file
        }

    # Persistence methods
    def _persist_task_state(self, task_id: str):
        """Persist individual task state."""
        if not self.enable_persistence or not self.persistence_file:
            return

        try:
            task = self.tasks.get(task_id)
            if task:
                state = {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "status": task.status,
                    "progress_percent": task.progress_percent,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "estimated_completion": task.estimated_completion.isoformat() if task.estimated_completion else None,
                    "error_message": task.error_message
                }

                with open(f"{self.persistence_file}.{task_id}", 'w') as f:
                    json.dump(state, f, indent=2)

        except Exception as e:
            logging.error(f"Error persisting task state for {task_id}: {e}")

    def _get_persisted_task(self, task_id: str) -> Optional[TaskProgress]:
        """Restore task state from persistence."""
        if not self.enable_persistence or not self.persistence_file:
            return None

        try:
            file_path = f"{self.persistence_file}.{task_id}"
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    state = json.load(f)

                return TaskProgress(
                    task_id=state["task_id"],
                    task_type=state["task_type"],
                    status=state["status"],
                    progress_percent=state["progress_percent"],
                    started_at=datetime.fromisoformat(state["started_at"]) if state.get("started_at") else None,
                    completed_at=datetime.fromisoformat(state["completed_at"]) if state.get("completed_at") else None,
                    estimated_completion=datetime.fromisoformat(state["estimated_completion"]) if state.get("estimated_completion") else None,
                    error_message=state.get("error_message")
                )

        except Exception as e:
            logging.error(f"Error restoring task state for {task_id}: {e}")
            return None

    def _load_persisted_state(self):
        """Load all persisted task states."""
        if not self.enable_persistence or not self.persistence_file:
            return

        try:
            # Find all task persistence files
            pattern = f"{self.persistence_file}.*"
            for file_path in Path('.').glob(pattern):
                if file_path.is_file() and file_path.name != self.persistence_file:
                    task_id = file_path.name.split('.', 1)[-1]
                    task = self._get_persisted_task(task_id)
                    if task:
                        self.tasks[task_id] = task
                        self._total_tasks_registered += 1
                        if task.status in ["completed", "failed"]:
                            self.task_history.append(task)
                            self._total_tasks_completed += 1

        except Exception as e:
            logging.error(f"Error loading persisted state: {e}")

    def cleanup_old_persisted_tasks(self, max_age_days: int = 30):
        """Clean up old persisted task files."""
        if not self.enable_persistence or not self.persistence_file:
            return

        try:
            cutoff_time = datetime.now() - timedelta(days=max_age_days)
            pattern = f"{self.persistence_file}.*"

            for file_path in Path('.').glob(pattern):
                if file_path.is_file():
                    # Get modification time
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff_time:
                        file_path.unlink()
                        logging.info(f"Cleaned up old persisted task: {file_path.name}")

        except Exception as e:
            logging.error(f"Error cleaning up old persisted tasks: {e}")

    def force_persist_all(self):
        """Force persist all current task states."""
        for task_id in list(self.tasks.keys()):
            self._persist_task_state(task_id)


class AlertManager:
    """Manages system alerts and notifications."""

    def __init__(self, alert_callbacks: Optional[List[Callable]] = None):
        self.alerts: Dict[str, Alert] = {}
        self.alert_callbacks = alert_callbacks or []
        self._alert_counter = 0

    def create_alert(self, level: AlertLevel, message: str, source: str = "system") -> str:
        """Create a new alert."""
        self._alert_counter += 1
        alert_id = f"alert_{self._alert_counter}"

        alert = Alert(
            id=alert_id,
            level=level,
            message=message,
            source=source,
            timestamp=datetime.now()
        )

        self.alerts[alert_id] = alert

        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logging.error(f"Alert callback error: {e}")

        return alert_id

    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert."""
        if alert_id in self.alerts:
            self.alerts[alert_id].acknowledged = True

    def resolve_alert(self, alert_id: str):
        """Mark an alert as resolved."""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True

    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """Get active (unresolved) alerts, optionally filtered by level."""
        alerts = [a for a in self.alerts.values() if not a.resolved]
        if level:
            alerts = [a for a in alerts if a.level == level]
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    def cleanup_old_alerts(self, hours: int = 24):
        """Remove resolved alerts older than specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        to_remove = [
            alert_id for alert_id, alert in self.alerts.items()
            if alert.resolved and alert.timestamp < cutoff_time
        ]

        for alert_id in to_remove:
            del self.alerts[alert_id]


class BacktestMonitor:
    """Main monitoring system that coordinates all monitoring components."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Initialize components
        self.resource_monitor = ResourceMonitor(
            sampling_interval=self.config.get("resource_sampling_interval", 1.0),
            history_size=self.config.get("resource_history_size", 3600)
        )

        self.progress_tracker = ProgressTracker()

        self.alert_manager = AlertManager(alert_callbacks=[self._default_alert_callback])

        # Performance thresholds
        self.thresholds = self.config.get("thresholds", {
            "cpu_warning": 80.0,
            "cpu_critical": 95.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "disk_io_warning": 100.0,  # MB/s
            "disk_io_critical": 500.0
        })

        self._monitoring = False
        self._alert_thread = None

    def start_monitoring(self):
        """Start all monitoring components."""
        if self._monitoring:
            return

        self.resource_monitor.start()
        self._monitoring = True
        self._alert_thread = threading.Thread(target=self._alert_monitoring_loop, daemon=True)
        self._alert_thread.start()

        logging.info("Backtest monitoring started")

    def stop_monitoring(self):
        """Stop all monitoring components."""
        self.resource_monitor.stop()
        self._monitoring = False

        if self._alert_thread:
            self._alert_thread.join(timeout=5.0)

        logging.info("Backtest monitoring stopped")

    def _default_alert_callback(self, alert: Alert):
        """Default alert callback that logs alerts."""
        level_str = alert.level.value.upper()
        logging.warning(f"[{level_str}] {alert.message}")

    def _alert_monitoring_loop(self):
        """Background loop for monitoring thresholds and generating alerts."""
        while self._monitoring:
            try:
                self._check_resource_thresholds()
                self._check_task_timeouts()
                time.sleep(5.0)  # Check every 5 seconds
            except Exception as e:
                logging.error(f"Alert monitoring error: {e}")

    def _check_resource_thresholds(self):
        """Check resource utilization against thresholds."""
        metrics = self.resource_monitor.get_current_metrics()
        if not metrics:
            return

        # CPU thresholds
        if metrics.cpu_percent >= self.thresholds["cpu_critical"]:
            self.alert_manager.create_alert(
                AlertLevel.CRITICAL,
                f"CPU usage critical: {metrics.cpu_percent:.1f}%",
                "resource_monitor"
            )
        elif metrics.cpu_percent >= self.thresholds["cpu_warning"]:
            self.alert_manager.create_alert(
                AlertLevel.WARNING,
                f"CPU usage high: {metrics.cpu_percent:.1f}%",
                "resource_monitor"
            )

        # Memory thresholds
        if metrics.memory_percent >= self.thresholds["memory_critical"]:
            self.alert_manager.create_alert(
                AlertLevel.CRITICAL,
                f"Memory usage critical: {metrics.memory_percent:.1f}%",
                "resource_monitor"
            )
        elif metrics.memory_percent >= self.thresholds["memory_warning"]:
            self.alert_manager.create_alert(
                AlertLevel.WARNING,
                f"Memory usage high: {metrics.memory_percent:.1f}%",
                "resource_monitor"
            )

    def _check_task_timeouts(self):
        """Check for tasks that have been running too long."""
        for task in self.progress_tracker.get_all_tasks():
            if task.status == "running" and task.started_at:
                runtime = (datetime.now() - task.started_at).total_seconds() / 60  # minutes

                # Check if task has been running more than 30 minutes
                if runtime > 30:
                    self.alert_manager.create_alert(
                        AlertLevel.WARNING,
                        f"Task {task.task_id} running for {runtime:.1f} minutes",
                        "progress_tracker"
                    )

    def register_tasks(self, tasks: List[Dict[str, Any]]):
        """Register multiple tasks for monitoring."""
        for task in tasks:
            self.progress_tracker.register_task(
                task_id=task["id"],
                task_type=task.get("type", "unknown"),
                estimated_duration=task.get("estimated_duration")
            )

    def get_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "resources": {
                "current": asdict(self.resource_monitor.get_current_metrics()) if self.resource_monitor.get_current_metrics() else None,
                "average_5min": asdict(self.resource_monitor.get_average_metrics(5)) if self.resource_monitor.get_average_metrics(5) else None
            },
            "progress": self.progress_tracker.get_overall_progress(),
            "tasks": [asdict(task) for task in self.progress_tracker.get_all_tasks()],
            "alerts": {
                "active": len(self.alert_manager.get_active_alerts()),
                "critical": len(self.alert_manager.get_active_alerts(AlertLevel.CRITICAL)),
                "warnings": len(self.alert_manager.get_active_alerts(AlertLevel.WARNING)),
                "recent": [asdict(alert) for alert in self.alert_manager.get_active_alerts()[:5]]
            }
        }

    def export_metrics(self, filepath: str, format: str = "json"):
        """Export monitoring metrics to file."""
        report = self.get_status_report()

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "json":
            with open(filepath, "w") as f:
                json.dump(report, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logging.info(f"Metrics exported to {filepath}")


# Global monitor instance
_monitor_instance: Optional[BacktestMonitor] = None


def get_monitor() -> BacktestMonitor:
    """Get the global monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = BacktestMonitor()
    return _monitor_instance


def start_monitoring(config: Optional[Dict[str, Any]] = None):
    """Start the global monitoring system."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = BacktestMonitor(config)
    _monitor_instance.start_monitoring()


def stop_monitoring():
    """Stop the global monitoring system."""
    global _monitor_instance
    if _monitor_instance:
        _monitor_instance.stop_monitoring()
        _monitor_instance = None