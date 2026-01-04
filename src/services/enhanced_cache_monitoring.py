"""
Enhanced Cache Monitoring System
==============================

Advanced monitoring for multi-level Redis-InfluxDB cache system
with real-time dashboards, alerts, and performance analytics.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from enum import Enum
import statistics

import aioredis
import pandas as pd
import numpy as np
from websockets.server import WebSocketServerProtocol
from websockets import serve
import aiohttp
from prometheus_client import CollectorRegistry, Gauge, Histogram, Counter, generate_latest

from .multi_cache_integration import MultiLevelCacheManager, CacheTier

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CacheAlert:
    """Cache performance alert"""
    id: str
    timestamp: datetime
    severity: AlertSeverity
    tier: CacheTier
    metric: str
    message: str
    value: Any
    threshold: Any
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class PerformanceSnapshot:
    """Performance snapshot for time series analysis"""
    timestamp: datetime
    tier_metrics: Dict[CacheTier, Dict[str, Any]]
    overall_metrics: Dict[str, Any]
    system_metrics: Dict[str, Any]
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyDetection:
    """Anomaly detection result"""
    timestamp: datetime
    metric: str
    tier: Optional[CacheTier]
    anomaly_type: str  # spike, drop, trend
    severity: str
    description: str
    confidence: float
    context: Dict[str, Any]


class RealTimeMetricsCollector:
    """
    Real-time metrics collector for multi-level cache
    """

    def __init__(
        self,
        cache_manager: MultiLevelCacheManager,
        collection_interval: float = 1.0,
        history_size: int = 3600  # 1 hour at 1-second intervals
    ):
        self.cache_manager = cache_manager
        self.collection_interval = collection_interval
        self.history_size = history_size

        # Metrics storage
        self.metrics_history = deque(maxlen=history_size)
        self.real_time_metrics = {}
        self.aggregated_metrics = defaultdict(dict)

        # Background collection
        self._collecting = False
        self._collection_task: Optional[asyncio.Task] = None

        # Callbacks for real-time updates
        self._callbacks: List[Callable[[PerformanceSnapshot], None]] = []

        # Prometheus metrics
        self.registry = CollectorRegistry()
        self._setup_prometheus_metrics()

    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics collectors"""
        # Hit rate gauges
        self.hit_rate_gauge = Gauge(
            'cache_hit_rate',
            'Cache hit rate by tier',
            ['tier'],
            registry=self.registry
        )

        # Response time histograms
        self.response_time_hist = Histogram(
            'cache_response_time_ms',
            'Cache response time in milliseconds',
            ['tier', 'operation'],
            registry=self.registry
        )

        # Size gauges
        self.cache_size_gauge = Gauge(
            'cache_size_bytes',
            'Cache size in bytes',
            ['tier'],
            registry=self.registry
        )

        # Operation counters
        self.operation_counter = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['tier', 'operation'],
            registry=self.registry
        )

    async def start_collection(self):
        """Start real-time metrics collection"""
        if self._collecting:
            logger.warning("Metrics collection already running")
            return

        self._collecting = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Real-time metrics collection started")

    async def stop_collection(self):
        """Stop metrics collection"""
        self._collecting = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Real-time metrics collection stopped")

    def add_callback(self, callback: Callable[[PerformanceSnapshot], None]):
        """Add callback for real-time metric updates"""
        self._callbacks.append(callback)

    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        metrics = await self.cache_manager.get_metrics()

        # Add real-time calculations
        real_time = {
            'timestamp': datetime.now().isoformat(),
            'response_times': {},
            'throughput': {},
            'error_rates': {}
        }

        # Calculate real-time metrics for each tier
        for tier in CacheTier:
            tier_name = tier.value
            if tier_name in metrics:
                # Recent response times (last 10 seconds)
                recent_times = self._get_recent_response_times(tier, 10)
                if recent_times:
                    real_time['response_times'][tier_name] = {
                        'avg': statistics.mean(recent_times),
                        'p50': statistics.median(recent_times),
                        'p95': np.percentile(recent_times, 95),
                        'p99': np.percentile(recent_times, 99)
                    }

                # Throughput (operations per second)
                recent_ops = self._get_recent_operations(tier, 1)
                real_time['throughput'][tier_name] = len(recent_ops)

        return {**metrics, **{'real_time': real_time}}

    async def get_historical_metrics(
        self,
        tier: Optional[CacheTier] = None,
        minutes: int = 60
    ) -> List[Dict]:
        """Get historical metrics"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        historical = []

        for snapshot in reversed(self.metrics_history):
            if snapshot.timestamp < cutoff_time:
                break

            snapshot_data = asdict(snapshot)

            # Filter by tier if specified
            if tier:
                snapshot_data['tier_metrics'] = {
                    tier.value: snapshot.tier_metrics.get(tier, {})
                }

            historical.append(snapshot_data)

        return historical

    async def _collection_loop(self):
        """Main collection loop"""
        while self._collecting:
            try:
                snapshot = await self._collect_snapshot()
                self.metrics_history.append(snapshot)
                self._update_prometheus_metrics(snapshot)

                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(snapshot)
                    except Exception as e:
                        logger.error(f"Error in metrics callback: {e}")

                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_snapshot(self) -> PerformanceSnapshot:
        """Collect current performance snapshot"""
        # Get cache metrics
        cache_metrics = await self.cache_manager.get_metrics()

        # Get system metrics
        system_metrics = await self._collect_system_metrics()

        # Organize by tier
        tier_metrics = {}
        for tier in CacheTier:
            tier_metrics[tier] = cache_metrics.get(tier.value, {})

        # Overall metrics
        overall_metrics = cache_metrics.get('overall', {})

        return PerformanceSnapshot(
            timestamp=datetime.now(),
            tier_metrics=tier_metrics,
            overall_metrics=overall_metrics,
            system_metrics=system_metrics
        )

    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics"""
        system_metrics = {}

        try:
            import psutil
            process = psutil.Process()

            # Process memory
            memory_info = process.memory_info()
            system_metrics['process_memory_rss_mb'] = memory_info.rss / 1024 / 1024
            system_metrics['process_memory_vms_mb'] = memory_info.vms / 1024 / 1024
            system_metrics['process_memory_percent'] = process.memory_percent()

            # CPU
            system_metrics['process_cpu_percent'] = process.cpu_percent()

            # System memory
            system_memory = psutil.virtual_memory()
            system_metrics['system_memory_percent'] = system_memory.percent
            system_metrics['system_memory_available_gb'] = system_memory.available / 1024 / 1024 / 1024

        except ImportError:
            logger.warning("psutil not available, skipping system metrics")

        # Redis metrics
        if self.cache_manager.redis_client:
            try:
                info = await self.cache_manager.redis_client.info()
                system_metrics['redis_memory_used_mb'] = info.get('used_memory', 0) / 1024 / 1024
                system_metrics['redis_memory_peak_mb'] = info.get('used_memory_peak', 0) / 1024 / 1024
                system_metrics['redis_connected_clients'] = info.get('connected_clients', 0)
                system_metrics['redis_total_commands'] = info.get('total_commands_processed', 0)
            except Exception as e:
                logger.warning(f"Failed to collect Redis metrics: {e}")

        return system_metrics

    def _update_prometheus_metrics(self, snapshot: PerformanceSnapshot):
        """Update Prometheus metrics"""
        for tier, metrics in snapshot.tier_metrics.items():
            tier_name = tier.value

            # Hit rate
            if 'hit_rate' in metrics:
                self.hit_rate_gauge.labels(tier=tier_name).set(metrics['hit_rate'])

            # Cache size
            if 'size_mb' in metrics:
                self.cache_size_gauge.labels(tier=tier_name).set(metrics['size_mb'] * 1024 * 1024)

            # Operation counts
            for op in ['hits', 'misses', 'sets', 'deletes']:
                if op in metrics:
                    self.operation_counter.labels(tier=tier_name, operation=op).inc(metrics[op])

            # Response times
            if 'avg_response_time_ms' in metrics:
                self.response_time_hist.labels(
                    tier=tier_name,
                    operation='get'
                ).observe(metrics['avg_response_time_ms'])

    def _get_recent_response_times(self, tier: CacheTier, seconds: int) -> List[float]:
        """Get recent response times for tier"""
        cutoff_time = datetime.now() - timedelta(seconds=seconds)
        times = []

        for snapshot in self.metrics_history:
            if snapshot.timestamp < cutoff_time:
                break

            tier_metrics = snapshot.tier_metrics.get(tier, {})
            if 'avg_response_time_ms' in tier_metrics:
                times.append(tier_metrics['avg_response_time_ms'])

        return times

    def _get_recent_operations(self, tier: CacheTier, seconds: int) -> List[int]:
        """Get recent operation counts for tier"""
        cutoff_time = datetime.now() - timedelta(seconds=seconds)
        ops = []

        for snapshot in self.metrics_history:
            if snapshot.timestamp < cutoff_time:
                break

            tier_metrics = snapshot.tier_metrics.get(tier, {})
            total_ops = (
                tier_metrics.get('hits', 0) +
                tier_metrics.get('misses', 0) +
                tier_metrics.get('sets', 0)
            )
            ops.append(total_ops)

        return ops


class AnomalyDetector:
    """
    Detects anomalies in cache performance metrics
    """

    def __init__(
        self,
        window_size: int = 60,  # 1 minute at 1-second intervals
        z_threshold: float = 3.0,
        trend_threshold: float = 0.5
    ):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.trend_threshold = trend_threshold
        self.detected_anomalies = deque(maxlen=1000)

    async def analyze_metrics(
        self,
        metrics_history: List[PerformanceSnapshot]
    ) -> List[AnomalyDetection]:
        """Analyze metrics history for anomalies"""
        anomalies = []

        if len(metrics_history) < self.window_size:
            return anomalies

        # Get recent window
        recent_window = list(metrics_history)[-self.window_size:]

        # Analyze each metric
        for metric in ['hit_rate', 'avg_response_time_ms', 'size_mb']:
            anomalies.extend(
                await self._detect_metric_anomalies(recent_window, metric)
            )

        # Store anomalies
        for anomaly in anomalies:
            self.detected_anomalies.append(anomaly)

        return anomalies

    async def _detect_metric_anomalies(
        self,
        window: List[PerformanceSnapshot],
        metric: str
    ) -> List[AnomalyDetection]:
        """Detect anomalies in a specific metric"""
        anomalies = []

        # Extract metric values by tier
        tier_values = defaultdict(list)
        timestamps = []

        for snapshot in window:
            timestamps.append(snapshot.timestamp)
            for tier in CacheTier:
                value = snapshot.tier_metrics.get(tier, {}).get(metric)
                if value is not None:
                    tier_values[tier].append(value)

        # Detect anomalies for each tier
        for tier, values in tier_values.items():
            if len(values) < 10:
                continue

            # Convert to numpy array
            np_values = np.array(values)

            # Detect spikes (z-score)
            z_scores = np.abs((np_values - np_values.mean()) / np_values.std())
            spike_indices = np.where(z_scores > self.z_threshold)[0]

            for idx in spike_indices:
                anomalies.append(AnomalyDetection(
                    timestamp=timestamps[idx],
                    metric=metric,
                    tier=tier,
                    anomaly_type='spike',
                    severity='warning' if z_scores[idx] < 5 else 'error',
                    description=f'{metric} spike detected: {values[idx]:.2f} (z-score: {z_scores[idx]:.2f})',
                    confidence=min(z_scores[idx] / 5.0, 1.0),
                    context={
                        'value': values[idx],
                        'z_score': float(z_scores[idx]),
                        'mean': float(np_values.mean()),
                        'std': float(np_values.std())
                    }
                ))

            # Detect trends
            if len(values) >= 20:
                # Calculate trend over last 20 points
                recent_values = values[-20:]
                x = np.arange(len(recent_values))
                slope, intercept = np.polyfit(x, recent_values, 1)

                # Normalize slope
                normalized_slope = slope / np.mean(recent_values) if np.mean(recent_values) != 0 else 0

                if abs(normalized_slope) > self.trend_threshold:
                    trend_type = 'increasing' if slope > 0 else 'decreasing'
                    anomalies.append(AnomalyDetection(
                        timestamp=timestamps[-1],
                        metric=metric,
                        tier=tier,
                        anomaly_type='trend',
                        severity='warning',
                        description=f'{metric} shows {trend_type} trend (slope: {slope:.4f})',
                        confidence=min(abs(normalized_slope) / self.trend_threshold, 1.0),
                        context={
                            'slope': float(slope),
                            'trend_type': trend_type,
                            'normalized_slope': float(normalized_slope)
                        }
                    ))

        return anomalies


class AlertManager:
    """
    Manages cache performance alerts with rules and notifications
    """

    def __init__(self):
        self.alert_rules = []
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.alert_callbacks: List[Callable[[CacheAlert], None]] = []

        # Default alert rules
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default alert rules"""
        # Hit rate alerts
        self.add_alert_rule(
            name="low_hit_rate",
            condition=lambda m: m.get('hit_rate', 1.0) < 0.5,
            severity=AlertSeverity.WARNING,
            message="Cache hit rate is below 50%"
        )

        self.add_alert_rule(
            name="critical_hit_rate",
            condition=lambda m: m.get('hit_rate', 1.0) < 0.2,
            severity=AlertSeverity.CRITICAL,
            message="Cache hit rate is critically low"
        )

        # Response time alerts
        self.add_alert_rule(
            name="high_response_time",
            condition=lambda m: m.get('avg_response_time_ms', 0) > 100,
            severity=AlertSeverity.WARNING,
            message="Average response time exceeds 100ms"
        )

        self.add_alert_rule(
            name="critical_response_time",
            condition=lambda m: m.get('avg_response_time_ms', 0) > 500,
            severity=AlertSeverity.ERROR,
            message="Response time is critically high"
        )

        # Memory usage alerts
        self.add_alert_rule(
            name="high_memory_usage",
            condition=lambda m: m.get('size_mb', 0) > 800,
            severity=AlertSeverity.WARNING,
            message="Cache memory usage exceeds 800MB"
        )

        # Error rate alerts
        self.add_alert_rule(
            name="high_error_rate",
            condition=lambda m: m.get('error_rate', 0) > 0.05,
            severity=AlertSeverity.ERROR,
            message="Cache error rate exceeds 5%"
        )

    def add_alert_rule(
        self,
        name: str,
        condition: Callable[[Dict], bool],
        severity: AlertSeverity,
        message: str,
        tier: Optional[CacheTier] = None
    ):
        """Add an alert rule"""
        self.alert_rules.append({
            'name': name,
            'condition': condition,
            'severity': severity,
            'message': message,
            'tier': tier
        })

    def add_alert_callback(self, callback: Callable[[CacheAlert], None]):
        """Add callback for alert notifications"""
        self.alert_callbacks.append(callback)

    async def evaluate_metrics(
        self,
        metrics: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> List[CacheAlert]:
        """Evaluate metrics against alert rules"""
        if timestamp is None:
            timestamp = datetime.now()

        triggered_alerts = []

        # Evaluate overall metrics
        for rule in self.alert_rules:
            if rule['tier'] is None:  # Overall rule
                if rule['condition'](metrics.get('overall', {})):
                    alert = CacheAlert(
                        id=f"{rule['name']}_{int(timestamp.timestamp())}",
                        timestamp=timestamp,
                        severity=rule['severity'],
                        tier=CacheTier.L1_REALTIME,  # Default tier
                        metric=rule['name'],
                        message=rule['message'],
                        value=None,
                        threshold=None
                    )
                    triggered_alerts.append(alert)

        # Evaluate tier-specific metrics
        for tier_name, tier_metrics in metrics.items():
            if tier_name == 'overall':
                continue

            try:
                tier = CacheTier(tier_name)
            except ValueError:
                continue

            for rule in self.alert_rules:
                if rule['tier'] is None or rule['tier'] == tier:
                    if rule['condition'](tier_metrics):
                        alert = CacheAlert(
                            id=f"{rule['name']}_{tier_name}_{int(timestamp.timestamp())}",
                            timestamp=timestamp,
                            severity=rule['severity'],
                            tier=tier,
                            metric=rule['name'],
                            message=rule['message'],
                            value=tier_metrics,
                            threshold=None
                        )
                        triggered_alerts.append(alert)

        # Process alerts
        for alert in triggered_alerts:
            await self._process_alert(alert)

        return triggered_alerts

    async def _process_alert(self, alert: CacheAlert):
        """Process a new alert"""
        # Check if alert is already active
        alert_key = f"{alert.tier}:{alert.metric}"
        if alert_key in self.active_alerts:
            existing = self.active_alerts[alert_key]
            if existing.severity.value >= alert.severity.value:
                return  # Keep existing higher severity alert

        # Add to active alerts
        self.active_alerts[alert_key] = alert
        self.alert_history.append(alert)

        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

        logger.warning(
            f"Cache alert triggered: {alert.severity.value.upper()} - "
            f"{alert.message} (Tier: {alert.tier.value})"
        )

    async def resolve_alert(self, alert_id: str):
        """Manually resolve an alert"""
        # Find and remove from active alerts
        for key, alert in list(self.active_alerts.items()):
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                del self.active_alerts[key]
                logger.info(f"Alert resolved: {alert_id}")
                return True
        return False

    async def get_active_alerts(self) -> List[CacheAlert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())

    async def get_alert_history(
        self,
        hours: int = 24,
        severity: Optional[AlertSeverity] = None
    ) -> List[CacheAlert]:
        """Get alert history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        history = [a for a in self.alert_history if a.timestamp >= cutoff_time]

        if severity:
            history = [a for a in history if a.severity == severity]

        return sorted(history, key=lambda a: a.timestamp, reverse=True)


class WebSocketDashboard:
    """
    Real-time WebSocket dashboard for cache monitoring
    """

    def __init__(
        self,
        metrics_collector: RealTimeMetricsCollector,
        alert_manager: AlertManager,
        host: str = "0.0.0.0",
        port: int = 8765
    ):
        self.metrics_collector = metrics_collector
        self.alert_manager = alert_manager
        self.host = host
        self.port = port
        self.connected_clients = set()
        self._server: Optional[Any] = None

    async def start(self):
        """Start WebSocket server"""
        self._server = await serve(
            self._handle_client,
            self.host,
            self.port
        )
        logger.info(f"WebSocket dashboard started on ws://{self.host}:{self.port}")

    async def stop(self):
        """Stop WebSocket server"""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        logger.info("WebSocket dashboard stopped")

    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket client"""
        self.connected_clients.add(websocket)
        logger.info(f"Dashboard client connected: {websocket.remote_address}")

        try:
            # Send initial data
            await self._send_initial_data(websocket)

            # Keep connection alive and send updates
            async for message in websocket:
                # Handle client requests
                try:
                    data = json.loads(message)
                    await self._handle_request(websocket, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from client: {message}")

        except Exception as e:
            logger.error(f"WebSocket client error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info(f"Dashboard client disconnected: {websocket.remote_address}")

    async def _send_initial_data(self, websocket: WebSocketServerProtocol):
        """Send initial dashboard data"""
        # Current metrics
        current_metrics = await self.metrics_collector.get_current_metrics()

        # Active alerts
        active_alerts = await self.alert_manager.get_active_alerts()

        initial_data = {
            'type': 'initial',
            'timestamp': datetime.now().isoformat(),
            'metrics': current_metrics,
            'alerts': [asdict(a) for a in active_alerts]
        }

        await websocket.send(json.dumps(initial_data, default=str))

    async def _handle_request(self, websocket: WebSocketServerProtocol, data: Dict):
        """Handle client request"""
        request_type = data.get('type')

        if request_type == 'get_history':
            minutes = data.get('minutes', 60)
            tier = data.get('tier')
            history = await self.metrics_collector.get_historical_metrics(
                CacheTier(tier) if tier else None,
                minutes
            )

            response = {
                'type': 'history',
                'data': history
            }
            await websocket.send(json.dumps(response, default=str))

        elif request_type == 'get_alerts':
            hours = data.get('hours', 24)
            alerts = await self.alert_manager.get_alert_history(hours)

            response = {
                'type': 'alerts',
                'data': [asdict(a) for a in alerts]
            }
            await websocket.send(json.dumps(response, default=str))

    async def broadcast_update(self, data: Dict):
        """Broadcast update to all connected clients"""
        if not self.connected_clients:
            return

        message = json.dumps(data, default=str)
        disconnected = set()

        for client in self.connected_clients:
            try:
                await client.send(message)
            except Exception as e:
                logger.warning(f"Failed to send update to client: {e}")
                disconnected.add(client)

        # Remove disconnected clients
        self.connected_clients -= disconnected

    async def broadcast_metrics_update(self, snapshot: PerformanceSnapshot):
        """Broadcast metrics update"""
        data = {
            'type': 'metrics_update',
            'timestamp': snapshot.timestamp.isoformat(),
            'metrics': asdict(snapshot)
        }
        await self.broadcast_update(data)

    async def broadcast_alert(self, alert: CacheAlert):
        """Broadcast new alert"""
        data = {
            'type': 'alert',
            'alert': asdict(alert)
        }
        await self.broadcast_update(data)


class EnhancedMonitoringSystem:
    """
    Complete enhanced monitoring system for multi-level cache
    """

    def __init__(
        self,
        cache_manager: MultiLevelCacheManager,
        config: Optional[Dict] = None
    ):
        self.cache_manager = cache_manager
        self.config = config or {}

        # Initialize components
        self.metrics_collector = RealTimeMetricsCollector(
            cache_manager,
            collection_interval=self.config.get('metrics_interval', 1.0)
        )
        self.anomaly_detector = AnomalyDetector(
            window_size=self.config.get('anomaly_window', 60)
        )
        self.alert_manager = AlertManager()
        self.dashboard = WebSocketDashboard(
            self.metrics_collector,
            self.alert_manager,
            host=self.config.get('dashboard_host', '0.0.0.0'),
            port=self.config.get('dashboard_port', 8765)
        )

        # Setup callbacks
        self._setup_callbacks()

        # Background tasks
        self._background_tasks = set()
        self._running = False

    def _setup_callbacks(self):
        """Setup component callbacks"""
        # Metrics to dashboard
        self.metrics_collector.add_callback(
            self.dashboard.broadcast_metrics_update
        )

        # Metrics to anomaly detector
        async def check_anomalies(snapshot: PerformanceSnapshot):
            history = list(self.metrics_collector.metrics_history)
            anomalies = await self.anomaly_detector.analyze_metrics(history)

            # Convert anomalies to alerts
            for anomaly in anomalies:
                alert = CacheAlert(
                    id=f"anomaly_{int(datetime.now().timestamp())}",
                    timestamp=anomaly.timestamp,
                    severity=AlertSeverity.WARNING,
                    tier=anomaly.tier or CacheTier.L1_REALTIME,
                    metric=anomaly.metric,
                    message=anomaly.description,
                    value=anomaly.context,
                    threshold=None
                )
                await self.alert_manager._process_alert(alert)

        self.metrics_collector.add_callback(check_anomalies)

        # Alerts to dashboard
        self.alert_manager.add_alert_callback(
            self.dashboard.broadcast_alert
        )

    async def start(self):
        """Start monitoring system"""
        self._running = True

        # Start components
        await self.metrics_collector.start_collection()
        await self.dashboard.start()

        # Start background tasks
        self._background_tasks.add(
            asyncio.create_task(self._monitoring_loop())
        )

        logger.info("Enhanced monitoring system started")

    async def stop(self):
        """Stop monitoring system"""
        self._running = False

        # Stop components
        await self.metrics_collector.stop_collection()
        await self.dashboard.stop()

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info("Enhanced monitoring system stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                # Get current metrics
                current_metrics = await self.metrics_collector.get_current_metrics()

                # Evaluate alerts
                await self.alert_manager.evaluate_metrics(current_metrics)

                # Sleep for next check
                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    async def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics"""
        return generate_latest(self.metrics_collector.registry).decode('utf-8')

    async def get_dashboard_url(self) -> str:
        """Get dashboard URL"""
        return f"http://{self.dashboard.host}:{self.dashboard.port}"


# Global monitoring system instance
_monitoring_system: Optional[EnhancedMonitoringSystem] = None


async def get_monitoring_system(
    cache_manager: Optional[MultiLevelCacheManager] = None,
    config: Optional[Dict] = None
) -> EnhancedMonitoringSystem:
    """Get or create global monitoring system"""
    global _monitoring_system
    if _monitoring_system is None:
        if cache_manager is None:
            from .multi_cache_integration import get_cache_manager
            cache_manager = await get_cache_manager()
        _monitoring_system = EnhancedMonitoringSystem(cache_manager, config)
        await _monitoring_system.start()
    return _monitoring_system


async def setup_enhanced_monitoring(
    cache_manager: MultiLevelCacheManager,
    config: Optional[Dict] = None
) -> EnhancedMonitoringSystem:
    """
    Setup enhanced monitoring for cache system

    Args:
        cache_manager: Cache manager to monitor
        config: Monitoring configuration

    Returns:
        Configured monitoring system
    """
    monitoring = EnhancedMonitoringSystem(cache_manager, config)
    await monitoring.start()

    logger.info("Enhanced cache monitoring configured")
    return monitoring


__all__ = [
    'EnhancedMonitoringSystem',
    'RealTimeMetricsCollector',
    'AnomalyDetector',
    'AlertManager',
    'WebSocketDashboard',
    'get_monitoring_system',
    'setup_enhanced_monitoring'
]