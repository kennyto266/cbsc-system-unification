"""
Resource Monitor for VectorBT Multiprocess Engine
==============================================

Monitors system resources and handles errors intelligently.
Provides real-time resource tracking and automatic error recovery.
"""

import asyncio
import psutil
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    FATAL = "fatal"


@dataclass
class ResourceMetrics:
    """Resource metrics snapshot"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    memory_available: int
    disk_usage: float
    network_io: Dict[str, int]
    active_processes: int
    task_queue_size: int = 0
    failed_tasks: int = 0


@dataclass
class Alert:
    """System alert"""
    level: AlertLevel
    message: str
    timestamp: datetime
    metrics: ResourceMetrics
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None


class ResourceMonitor:
    """System resource monitor with intelligent error handling"""

    def __init__(self, check_interval: float = 5.0):
        self.check_interval = check_interval
        self.metrics_history: List[ResourceMetrics] = []
        self.active_alerts: List[Alert] = []
        self.alert_handlers: Dict[AlertLevel, List[Callable]] = {
            AlertLevel.INFO: [],
            AlertLevel.WARNING: [],
            AlertLevel.CRITICAL: [],
            AlertLevel.FATAL: []
        }

        # Resource thresholds
        self.thresholds = {
            'cpu_usage': 0.90,
            'memory_usage': 0.85,
            'disk_usage': 0.80,
            'task_failure_rate': 0.10,
            'response_time': 5.0
        }

        # Monitoring state
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable] = []

        # Error recovery
        self.error_counts = {}
        self.last_errors = {}
        self.recovery_strategies = {
            'high_cpu': self._handle_high_cpu,
            'high_memory': self._handle_high_memory,
            'disk_space': self._handle_disk_space,
            'task_failure': self._handle_task_failure
        }

    async def start_monitoring(self):
        """Start resource monitoring"""
        if self._monitoring:
            logger.warning("Resource monitoring already running")
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Resource monitoring started")

    async def stop_monitoring(self):
        """Stop resource monitoring"""
        if not self._monitoring:
            return

        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Resource monitoring stopped")

    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)

                # Keep only last 1000 metrics
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]

                # Analyze metrics and create alerts
                await self._analyze_metrics(metrics)

                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        await callback(metrics)
                    except Exception as e:
                        logger.error(f"Error in monitoring callback: {e}")

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            await asyncio.sleep(self.check_interval)

    async def _collect_metrics(self) -> ResourceMetrics:
        """Collect system resource metrics"""
        # CPU metrics
        cpu_usage = psutil.cpu_percent(interval=1)

        # Memory metrics
        memory = psutil.virtual_memory()
        memory_usage = memory.percent / 100.0
        memory_available = memory.available

        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent / 100.0

        # Network I/O
        network = psutil.net_io_counters()
        network_io = {
            'bytes_sent': network.bytes_sent,
            'bytes_recv': network.bytes_recv,
            'packets_sent': network.packets_sent,
            'packets_recv': network.packets_recv
        }

        # Process metrics
        active_processes = len(psutil.pids())

        return ResourceMetrics(
            timestamp=datetime.now(),
            cpu_usage=cpu_usage / 100.0,
            memory_usage=memory_usage,
            memory_available=memory_available,
            disk_usage=disk_usage,
            network_io=network_io,
            active_processes=active_processes
        )

    async def _analyze_metrics(self, metrics: ResourceMetrics):
        """Analyze metrics and create alerts if needed"""
        # CPU usage alert
        if metrics.cpu_usage > self.thresholds['cpu_usage']:
            await self._create_alert(
                AlertLevel.WARNING,
                f"High CPU usage: {metrics.cpu_usage:.1%}",
                metrics
            )
            await self.recovery_strategies['high_cpu'](metrics)

        # Memory usage alert
        if metrics.memory_usage > self.thresholds['memory_usage']:
            await self._create_alert(
                AlertLevel.WARNING,
                f"High memory usage: {metrics.memory_usage:.1%}",
                metrics
            )
            await self.recovery_strategies['high_memory'](metrics)

        # Disk usage alert
        if metrics.disk_usage > self.thresholds['disk_usage']:
            await self._create_alert(
                AlertLevel.CRITICAL,
                f"High disk usage: {metrics.disk_usage:.1%}",
                metrics
            )
            await self.recovery_strategies['disk_space'](metrics)

    async def _create_alert(self, level: AlertLevel, message: str, metrics: ResourceMetrics):
        """Create and handle alert"""
        alert = Alert(
            level=level,
            message=message,
            timestamp=metrics.timestamp,
            metrics=metrics
        )

        # Check for duplicate alerts
        recent_alerts = [
            a for a in self.active_alerts
            if a.level == level and a.message == message
            and (datetime.now() - a.timestamp).seconds < 60
        ]

        if recent_alerts:
            return  # Skip duplicate alert

        self.active_alerts.append(alert)
        logger.warning(f"ALERT [{level.value.upper()}]: {message}")

        # Call alert handlers
        for handler in self.alert_handlers[level]:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    async def _handle_high_cpu(self, metrics: ResourceMetrics):
        """Handle high CPU usage"""
        logger.info("Initiating high CPU recovery strategy")

        # Find CPU-intensive processes
        cpu_intensive = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                if proc.info['cpu_percent'] > 50:
                    cpu_intensive.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if cpu_intensive:
            logger.warning(f"Found {len(cpu_intensive)} CPU-intensive processes")

        # Trigger garbage collection
        import gc
        gc.collect()

        # Notify for potential task throttling
        await self._notify_recovery_action("cpu_throttling", {
            "cpu_usage": metrics.cpu_usage,
            "cpu_intensive_processes": cpu_intensive[:5]  # Top 5
        })

    async def _handle_high_memory(self, metrics: ResourceMetrics):
        """Handle high memory usage"""
        logger.info("Initiating high memory recovery strategy")

        # Find memory-intensive processes
        memory_intensive = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                if proc.info['memory_percent'] > 5:
                    memory_intensive.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Clear caches
        if hasattr(self, 'clear_caches'):
            await self.clear_caches()

        # Trigger garbage collection multiple times
        import gc
        for _ in range(3):
            gc.collect()
            await asyncio.sleep(0.1)

        await self._notify_recovery_action("memory_cleanup", {
            "memory_usage": metrics.memory_usage,
            "memory_available": metrics.memory_available,
            "memory_intensive_processes": memory_intensive[:5]
        })

    async def _handle_disk_space(self, metrics: ResourceMetrics):
        """Handle low disk space"""
        logger.critical("Low disk space detected - immediate action required")

        await self._notify_recovery_action("disk_cleanup", {
            "disk_usage": metrics.disk_usage,
            "available_space": metrics.disk_usage
        })

    async def _handle_task_failure(self, error_info: Dict):
        """Handle task failure"""
        error_type = error_info.get('type', 'unknown')

        # Track error frequency
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1

        # Check if error rate is too high
        total_tasks = error_info.get('total_tasks', 100)
        failure_rate = self.error_counts[error_type] / total_tasks

        if failure_rate > self.thresholds['task_failure_rate']:
            await self._create_alert(
                AlertLevel.CRITICAL,
                f"High task failure rate for {error_type}: {failure_rate:.1%}",
                await self._collect_metrics()
            )

    async def _notify_recovery_action(self, action: str, details: Dict):
        """Notify about recovery action"""
        logger.info(f"Recovery action '{action}': {details}")

        # Send to WebSocket if available
        if hasattr(self, 'websocket_manager'):
            await self.websocket_manager.broadcast({
                'type': 'recovery_action',
                'action': action,
                'details': details,
                'timestamp': datetime.now().isoformat()
            })

    def add_callback(self, callback: Callable[[ResourceMetrics], None]):
        """Add monitoring callback"""
        self._callbacks.append(callback)

    def add_alert_handler(self, level: AlertLevel, handler: Callable[[Alert], None]):
        """Add alert handler for specific level"""
        self.alert_handlers[level].append(handler)

    def get_current_metrics(self) -> Optional[ResourceMetrics]:
        """Get most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """Get active alerts"""
        if level:
            return [a for a in self.active_alerts if a.level == level]
        return self.active_alerts.copy()

    def resolve_alert(self, alert_id: str, resolution: str):
        """Mark alert as resolved"""
        for alert in self.active_alerts:
            if id(alert) == int(alert_id):
                alert.resolution = resolution
                alert.resolved_at = datetime.now()
                logger.info(f"Alert resolved: {alert.message}")
                break

    def get_metrics_summary(self, minutes: int = 60) -> Dict:
        """Get metrics summary for the last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff
        ]

        if not recent_metrics:
            return {}

        return {
            'count': len(recent_metrics),
            'avg_cpu': sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics),
            'avg_memory': sum(m.memory_usage for m in recent_metrics) / len(recent_metrics),
            'max_cpu': max(m.cpu_usage for m in recent_metrics),
            'max_memory': max(m.memory_usage for m in recent_metrics),
            'alerts': len([a for a in self.active_alerts if a.timestamp >= cutoff])
        }