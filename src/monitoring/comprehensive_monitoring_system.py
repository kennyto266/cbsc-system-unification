"""
Comprehensive Monitoring and Logging System for Unified Backtesting Framework
Integrates system monitoring, application metrics, and log management
"""

import asyncio
import json
import logging
import psutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque
import threading
import queue

# Third-party imports
import numpy as np
from prometheus_client import Counter, Gauge, Histogram, start_http_server
import redis
from redis.exceptions import ConnectionError as RedisConnectionError
import structlog

# Local imports
from ..core.base import Component
from ..logging_config import setup_logging


@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available: int
    memory_used: int
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_processes: int
    load_average: tuple


@dataclass
class ApplicationMetrics:
    """Application performance metrics"""
    timestamp: float
    active_backtests: int
    completed_backtests: int
    failed_backtests: int
    total_parameter_combinations: int
    processed_parameters: int
    cache_hit_rate: float
    average_processing_time: float
    queue_size: int
    error_rate: float


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: str
    component: str
    message: str
    context: Dict[str, Any]
    traceback: Optional[str] = None


class MetricsCollector:
    """Collects and manages system and application metrics"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.system_metrics_history = deque(maxlen=1000)
        self.app_metrics_history = deque(maxlen=1000)
        self.is_running = False
        self.collection_interval = 5  # seconds
        self._logger = setup_logging(self.__class__.__name__)

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            network = psutil.net_io_counters()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)

            metrics = SystemMetrics(
                timestamp=time.time(),
                cpu_percent=psutil.cpu_percent(interval=1),
                memory_percent=psutil.virtual_memory().percent,
                memory_available=psutil.virtual_memory().available,
                memory_used=psutil.virtual_memory().used,
                disk_usage_percent=psutil.disk_usage('/').percent,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                active_processes=len(psutil.pids()),
                load_average=load_avg
            )

            self.system_metrics_history.append(metrics)

            # Store in Redis if available
            if self.redis:
                self.redis.lpush(
                    'system_metrics',
                    json.dumps(asdict(metrics), default=str)
                )
                self.redis.ltrim('system_metrics', 0, 999)

            return metrics

        except Exception as e:
            self._logger.error(f"Error collecting system metrics: {e}")
            raise

    def get_system_metrics_summary(self, minutes: int = 5) -> Dict[str, float]:
        """Get summary statistics for recent system metrics"""
        cutoff_time = time.time() - (minutes * 60)
        recent_metrics = [
            m for m in self.system_metrics_history
            if m.timestamp > cutoff_time
        ]

        if not recent_metrics:
            return {}

        return {
            'avg_cpu_percent': np.mean([m.cpu_percent for m in recent_metrics]),
            'max_cpu_percent': np.max([m.cpu_percent for m in recent_metrics]),
            'avg_memory_percent': np.mean([m.memory_percent for m in recent_metrics]),
            'max_memory_percent': np.max([m.memory_percent for m in recent_metrics]),
            'current_memory_available': recent_metrics[-1].memory_available,
            'avg_disk_usage': np.mean([m.disk_usage_percent for m in recent_metrics]),
            'peak_load_avg': np.max([m.load_average[0] for m in recent_metrics])
        }

    def start_collection(self):
        """Start metrics collection thread"""
        self.is_running = True
        self.collection_thread = threading.Thread(target=self._collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        self._logger.info("Metrics collection started")

    def stop_collection(self):
        """Stop metrics collection"""
        self.is_running = False
        if hasattr(self, 'collection_thread'):
            self.collection_thread.join(timeout=5)
        self._logger.info("Metrics collection stopped")

    def _collection_loop(self):
        """Main collection loop"""
        while self.is_running:
            try:
                self.collect_system_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                self._logger.error(f"Error in metrics collection: {e}")
                time.sleep(self.collection_interval)


class PrometheusMetricsExporter:
    """Export metrics to Prometheus"""

    def __init__(self, port: int = 9090):
        self.port = port

        # Define Prometheus metrics
        self.system_cpu_percent = Gauge('system_cpu_percent', 'System CPU usage percentage')
        self.system_memory_percent = Gauge('system_memory_percent', 'System memory usage percentage')
        self.system_disk_usage = Gauge('system_disk_usage_percent', 'System disk usage percentage')

        self.app_active_backtests = Gauge('app_active_backtests', 'Number of active backtests')
        self.app_completed_backtests = Counter('app_completed_backtests_total', 'Total completed backtests')
        self.app_failed_backtests = Counter('app_failed_backtests_total', 'Total failed backtests')
        self.app_processing_time = Histogram('app_backtest_processing_seconds', 'Backtest processing time')
        self.app_cache_hit_rate = Gauge('app_cache_hit_rate', 'Application cache hit rate')
        self.app_error_rate = Gauge('app_error_rate', 'Application error rate')

        self._logger = setup_logging(self.__class__.__name__)

    def start_server(self):
        """Start Prometheus HTTP server"""
        try:
            start_http_server(self.port)
            self._logger.info(f"Prometheus metrics server started on port {self.port}")
        except Exception as e:
            self._logger.error(f"Failed to start Prometheus server: {e}")
            raise

    def update_system_metrics(self, metrics: SystemMetrics):
        """Update system metrics"""
        self.system_cpu_percent.set(metrics.cpu_percent)
        self.system_memory_percent.set(metrics.memory_percent)
        self.system_disk_usage.set(metrics.disk_usage_percent)

    def update_app_metrics(self, metrics: ApplicationMetrics):
        """Update application metrics"""
        self.app_active_backtests.set(metrics.active_backtests)
        self.app_cache_hit_rate.set(metrics.cache_hit_rate)
        self.app_error_rate.set(metrics.error_rate)


class StructuredLogger:
    """Enhanced structured logging with context and correlation"""

    def __init__(self, log_level: str = "INFO"):
        self.log_level = log_level
        self._setup_structlog()
        self._logger = setup_logging(self.__class__.__name__)

    def _setup_structlog(self):
        """Setup structlog configuration"""
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    def get_logger(self, component: str, **context) -> structlog.BoundLogger:
        """Get a structured logger with component binding"""
        return structlog.get_logger(component, **context)


class AlertManager:
    """Manages alerting based on metrics thresholds"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.logger = setup_logging(self.__class__.__name__)

        # Alert thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0,
            'error_rate': 5.0,
            'processing_time': 300.0,  # 5 minutes
            'queue_size': 100
        }

    def check_alerts(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """Check if any thresholds are exceeded"""
        current_time = datetime.now()

        # Check system metrics
        if system_metrics.cpu_percent > self.thresholds['cpu_percent']:
            self._trigger_alert(
                'system_cpu_high',
                f"CPU usage at {system_metrics.cpu_percent:.1f}%",
                severity='warning'
            )

        if system_metrics.memory_percent > self.thresholds['memory_percent']:
            self._trigger_alert(
                'system_memory_high',
                f"Memory usage at {system_metrics.memory_percent:.1f}%",
                severity='warning'
            )

        if system_metrics.disk_usage_percent > self.thresholds['disk_usage_percent']:
            self._trigger_alert(
                'system_disk_high',
                f"Disk usage at {system_metrics.disk_usage_percent:.1f}%",
                severity='critical'
            )

        # Check application metrics
        if app_metrics.error_rate > self.thresholds['error_rate']:
            self._trigger_alert(
                'app_error_rate_high',
                f"Error rate at {app_metrics.error_rate:.1f}%",
                severity='critical'
            )

        if app_metrics.queue_size > self.thresholds['queue_size']:
            self._trigger_alert(
                'app_queue_backlog',
                f"Queue size: {app_metrics.queue_size}",
                severity='warning'
            )

    def _trigger_alert(self, alert_type: str, message: str, severity: str = 'info'):
        """Trigger an alert"""
        alert = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'resolved': False
        }

        self.alerts[alert_type] = alert
        self.alert_history.append(alert)

        # Store in Redis if available
        if self.redis:
            self.redis.lpush('alerts', json.dumps(alert))
            self.redis.ltrim('alerts', 0, 999)

        # Log alert
        if severity == 'critical':
            self.logger.error(f"ALERT: {alert_type} - {message}")
        elif severity == 'warning':
            self.logger.warning(f"ALERT: {alert_type} - {message}")
        else:
            self.logger.info(f"ALERT: {alert_type} - {message}")

    def resolve_alert(self, alert_type: str):
        """Resolve an alert"""
        if alert_type in self.alerts:
            self.alerts[alert_type]['resolved'] = True
            self.alerts[alert_type]['resolved_at'] = datetime.now().isoformat()

            if self.redis:
                self.redis.hset(
                    'resolved_alerts',
                    alert_type,
                    json.dumps(self.alerts[alert_type])
                )

            self.logger.info(f"Resolved alert: {alert_type}")

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active (unresolved) alerts"""
        return [
            alert for alert in self.alerts.values()
            if not alert.get('resolved', False)
        ]


class ComprehensiveMonitoringSystem(Component):
    """Main monitoring system integrating all monitoring components"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__('ComprehensiveMonitoringSystem')
        self.config = config

        # Initialize Redis connection
        self.redis = self._init_redis()

        # Initialize monitoring components
        self.metrics_collector = MetricsCollector(self.redis)
        self.prometheus_exporter = PrometheusMetricsExporter(
            config.get('prometheus_port', 9090)
        )
        self.structured_logger = StructuredLogger(config.get('log_level', 'INFO'))
        self.alert_manager = AlertManager(self.redis)

        # Application metrics tracking
        self.app_metrics = ApplicationMetrics(
            timestamp=time.time(),
            active_backtests=0,
            completed_backtests=0,
            failed_backtests=0,
            total_parameter_combinations=0,
            processed_parameters=0,
            cache_hit_rate=0.0,
            average_processing_time=0.0,
            queue_size=0,
            error_rate=0.0
        )

        # Performance tracking
        self.start_times = {}
        self.processing_times = deque(maxlen=100)
        self.error_count = 0
        self.total_operations = 0

        self.logger.info("Comprehensive monitoring system initialized")

    def _init_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis connection"""
        try:
            redis_config = self.config.get('redis', {})
            redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                decode_responses=True
            )

            # Test connection
            redis_client.ping()
            self.logger.info("Redis connection established for monitoring")
            return redis_client

        except (RedisConnectionError, Exception) as e:
            self.logger.warning(f"Redis connection failed, running without persistent storage: {e}")
            return None

    def start_monitoring(self):
        """Start all monitoring components"""
        try:
            # Start metrics collection
            self.metrics_collector.start_collection()

            # Start Prometheus exporter
            self.prometheus_exporter.start_server()

            self.logger.info("Comprehensive monitoring system started")

        except Exception as e:
            self.logger.error(f"Failed to start monitoring system: {e}")
            raise

    def stop_monitoring(self):
        """Stop all monitoring components"""
        try:
            self.metrics_collector.stop_collection()
            self.logger.info("Comprehensive monitoring system stopped")

        except Exception as e:
            self.logger.error(f"Error stopping monitoring system: {e}")

    def get_logger(self, component: str, **context) -> structlog.BoundLogger:
        """Get a structured logger for a component"""
        return self.structured_logger.get_logger(component, **context)

    def track_backtest_start(self, backtest_id: str, total_params: int):
        """Track the start of a backtest"""
        self.start_times[backtest_id] = time.time()
        self.app_metrics.active_backtests += 1
        self.app_metrics.total_parameter_combinations += total_params
        self.total_operations += 1

    def track_backtest_complete(self, backtest_id: str, success: bool, processed_params: int):
        """Track the completion of a backtest"""
        if backtest_id in self.start_times:
            processing_time = time.time() - self.start_times[backtest_id]
            self.processing_times.append(processing_time)
            del self.start_times[backtest_id]

            # Update average processing time
            if self.processing_times:
                self.app_metrics.average_processing_time = np.mean(self.processing_times)

        self.app_metrics.active_backtests = max(0, self.app_metrics.active_backtests - 1)

        if success:
            self.app_metrics.completed_backtests += 1
            self.prometheus_exporter.app_completed_backtests.inc()
        else:
            self.app_metrics.failed_backtests += 1
            self.error_count += 1
            self.prometheus_exporter.app_failed_backtests.inc()

        self.app_metrics.processed_parameters += processed_params

        # Update error rate
        if self.total_operations > 0:
            self.app_metrics.error_rate = (self.error_count / self.total_operations) * 100

    def update_cache_metrics(self, hit_rate: float):
        """Update cache hit rate metrics"""
        self.app_metrics.cache_hit_rate = hit_rate
        self.prometheus_exporter.app_cache_hit_rate.set(hit_rate)

    def update_queue_size(self, size: int):
        """Update queue size metrics"""
        self.app_metrics.queue_size = size

    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        try:
            # Get latest system metrics
            system_metrics = self.metrics_collector.get_system_metrics_summary()

            # Get current application metrics
            app_metrics = asdict(self.app_metrics)

            # Get active alerts
            active_alerts = self.alert_manager.get_active_alerts()

            return {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': system_metrics,
                'application_metrics': app_metrics,
                'alerts': {
                    'active_count': len(active_alerts),
                    'active_alerts': active_alerts
                },
                'status': 'healthy' if len(active_alerts) == 0 else 'warning' if len(active_alerts) < 3 else 'critical'
            }

        except Exception as e:
            self.logger.error(f"Error generating monitoring dashboard: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'status': 'error'
            }

    async def run_monitoring_cycle(self):
        """Run a single monitoring cycle"""
        try:
            # Collect system metrics
            system_metrics = self.metrics_collector.collect_system_metrics()

            # Update Prometheus metrics
            self.prometheus_exporter.update_system_metrics(system_metrics)
            self.prometheus_exporter.update_app_metrics(self.app_metrics)

            # Check for alerts
            self.alert_manager.check_alerts(system_metrics, self.app_metrics)

            # Update timestamp
            self.app_metrics.timestamp = time.time()

        except Exception as e:
            self.logger.error(f"Error in monitoring cycle: {e}")

    def cleanup(self):
        """Cleanup resources"""
        self.stop_monitoring()
        if self.redis:
            self.redis.close()