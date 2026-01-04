"""
Prometheus Metrics Collector
Prometheus 指標收集器

提供應用程序級別的 Prometheus 指標收集和暴露功能。

Core Metrics:
    - HTTP Requests: 請求計數、響應時間、狀態碼分布
    - Database: 連接數、查詢時間、慢查詢
    - Cache: 命中率、未命中數、驅逐數
    - Business: 策略執行、交易量、用戶活躍度

Usage:
    ```python
    from src.monitoring import PrometheusMetricsCollector, get_metrics_collector

    # Get singleton instance
    collector = get_metrics_collector()

    # Record metrics
    collector.record_http_request("GET", "/api/strategies", 200, 0.123)
    collector.record_strategy_execution("momentum", "success")

    # Start metrics server
    collector.start_metrics_server(port=8000)
    ```
"""

import time
import functools
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import asyncio

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Summary,
        CollectorRegistry, generate_latest,
        start_http_server, REGISTRY
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("Warning: prometheus_client not available. Install with: pip install prometheus_client")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. System metrics will be limited.")


class MetricType(Enum):
    """指標類型枚舉"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """指標值"""
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class PerformanceSnapshot:
    """性能快照"""
    timestamp: float
    total_requests: int
    avg_response_time: float
    error_rate: float
    active_connections: int
    memory_usage_mb: float
    cpu_usage_percent: float


class CounterMetric:
    """計數器指標包裝器"""

    def __init__(self, name: str, description: str, labels: List[str] = None, registry=None):
        self.name = name
        self.description = description
        self.labels = labels or []
        if PROMETHEUS_AVAILABLE:
            self.metric = Counter(name, description, self.labels, registry=registry)
        else:
            self.metric = None
            self._value = 0

    def inc(self, amount: float = 1, **labels):
        """增加計數"""
        if self.metric:
            if labels:
                self.metric.labels(**labels).inc(amount)
            else:
                self.metric.inc(amount)
        else:
            self._value += amount

    def get(self) -> float:
        """獲取當前值"""
        if self.metric:
            # Note: Counter doesn't have a simple get() in prometheus_client
            return 0  # Placeholder
        return self._value


class HistogramMetric:
    """直方圖指標包裝器"""

    def __init__(self, name: str, description: str, labels: List[str] = None,
                 buckets: List[float] = None, registry=None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
        if PROMETHEUS_AVAILABLE:
            self.metric = Histogram(name, description, self.labels, buckets=self.buckets, registry=registry)
        else:
            self.metric = None
            self._values: List[float] = []

    def observe(self, value: float, **labels):
        """觀測值"""
        if self.metric:
            if labels:
                self.metric.labels(**labels).observe(value)
            else:
                self.metric.observe(value)
        else:
            self._values.append(value)


class GaugeMetric:
    """儀表指標包裝器"""

    def __init__(self, name: str, description: str, labels: List[str] = None, registry=None):
        self.name = name
        self.description = description
        self.labels = labels or []
        if PROMETHEUS_AVAILABLE:
            self.metric = Gauge(name, description, self.labels, registry=registry)
        else:
            self.metric = None
            self._value = 0

    def set(self, value: float, **labels):
        """設置值"""
        if self.metric:
            if labels:
                self.metric.labels(**labels).set(value)
            else:
                self.metric.set(value)
        else:
            self._value = value

    def inc(self, amount: float = 1, **labels):
        """增加值"""
        if self.metric:
            if labels:
                self.metric.labels(**labels).inc(amount)
            else:
                self.metric.inc(amount)
        else:
            self._value += amount

    def dec(self, amount: float = 1, **labels):
        """減少值"""
        if self.metric:
            if labels:
                self.metric.labels(**labels).dec(amount)
            else:
                self.metric.dec(amount)
        else:
            self._value -= amount


class PrometheusMetricsCollector:
    """
    Prometheus 指標收集器

    提供應用程序級別的指標收集，包括 HTTP 請求、數據庫操作、緩存性能和業務指標。

    Attributes:
        app_name: 應用程序名稱
        registry: Prometheus 指標註冊表
    """

    def __init__(self, app_name: str = "cbsc-trading", environment: str = "production"):
        self.app_name = app_name
        self.environment = environment
        self._server_started = False

        # Create registry
        if PROMETHEUS_AVAILABLE:
            self.registry = CollectorRegistry()
        else:
            self.registry = None

        # Performance metrics storage (fallback when prometheus_client not available)
        self._response_times: deque = deque(maxlen=1000)
        self._request_counts: Dict[str, int] = {}
        self._error_counts: Dict[str, int] = {}

        # Initialize metrics
        self._init_http_metrics()
        self._init_db_metrics()
        self._init_cache_metrics()
        self._init_business_metrics()
        self._init_system_metrics()

    def _init_http_metrics(self):
        """初始化 HTTP 指標"""
        # Total HTTP requests
        self.http_requests_total = CounterMetric(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            self.registry
        )

        # HTTP request duration
        self.http_request_duration = HistogramMetric(
            'http_request_duration_seconds',
            'HTTP request latency',
            ['method', 'endpoint'],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )

        # HTTP requests in progress
        self.http_requests_in_progress = GaugeMetric(
            'http_requests_in_progress',
            'Number of HTTP requests in progress',
            registry=self.registry
        )

        # HTTP errors
        self.http_errors_total = CounterMetric(
            'http_errors_total',
            'Total HTTP errors',
            ['method', 'endpoint', 'error_type'],
            self.registry
        )

    def _init_db_metrics(self):
        """初始化數據庫指標"""
        # Database connections
        self.db_connections_active = GaugeMetric(
            'db_connections_active',
            'Active database connections',
            ['database'],
            self.registry
        )

        self.db_connections_idle = GaugeMetric(
            'db_connections_idle',
            'Idle database connections',
            ['database'],
            self.registry
        )

        # Database query duration
        self.db_query_duration = HistogramMetric(
            'db_query_duration_seconds',
            'Database query duration',
            ['database', 'operation'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=self.registry
        )

        # Database errors
        self.db_errors_total = CounterMetric(
            'db_errors_total',
            'Total database errors',
            ['database', 'error_type'],
            self.registry
        )

        # Slow queries
        self.db_slow_queries_total = CounterMetric(
            'db_slow_queries_total',
            'Total slow database queries (>1s)',
            ['database'],
            self.registry
        )

    def _init_cache_metrics(self):
        """初始化緩存指標"""
        # Cache hits
        self.cache_hits_total = CounterMetric(
            'cache_hits_total',
            'Total cache hits',
            ['cache_layer', 'cache_type'],
            self.registry
        )

        # Cache misses
        self.cache_misses_total = CounterMetric(
            'cache_misses_total',
            'Total cache misses',
            ['cache_layer', 'cache_type'],
            self.registry
        )

        # Cache hit ratio
        self.cache_hit_ratio = GaugeMetric(
            'cache_hit_ratio',
            'Cache hit ratio (0-1)',
            ['cache_layer'],
            self.registry
        )

        # Cache evictions
        self.cache_evictions_total = CounterMetric(
            'cache_evictions_total',
            'Total cache evictions',
            ['cache_layer'],
            self.registry
        )

        # Cache size
        self.cache_size_bytes = GaugeMetric(
            'cache_size_bytes',
            'Current cache size in bytes',
            ['cache_layer'],
            self.registry
        )

    def _init_business_metrics(self):
        """初始化業務指標"""
        # Strategy executions
        self.strategy_executions_total = CounterMetric(
            'strategy_executions_total',
            'Total strategy executions',
            ['strategy_type', 'status'],
            self.registry
        )

        # Strategy execution duration
        self.strategy_execution_duration = HistogramMetric(
            'strategy_execution_duration_seconds',
            'Strategy execution duration',
            ['strategy_type'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 300.0],
            registry=self.registry
        )

        # Active strategies
        self.active_strategies = GaugeMetric(
            'active_strategies_total',
            'Number of active strategies',
            self.registry
        )

        # Trading volume
        self.trading_volume_total = CounterMetric(
            'trading_volume_total',
            'Total trading volume',
            ['symbol', 'side'],
            self.registry
        )

        # Trading value
        self.trading_value_total = CounterMetric(
            'trading_value_total',
            'Total trading value',
            ['symbol', 'side', 'currency'],
            self.registry
        )

        # Active users
        self.active_users_total = GaugeMetric(
            'active_users_total',
            'Number of active users',
            ['user_type'],
            self.registry
        )

        # Backtest executions
        self.backtest_executions_total = CounterMetric(
            'backtest_executions_total',
            'Total backtest executions',
            ['status'],
            self.registry
        )

        # Backtest duration
        self.backtest_duration_seconds = HistogramMetric(
            'backtest_duration_seconds',
            'Backtest execution duration',
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0],
            registry=self.registry
        )

    def _init_system_metrics(self):
        """初始化系統指標"""
        # System memory
        self.system_memory_usage_bytes = GaugeMetric(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )

        self.system_memory_available_bytes = GaugeMetric(
            'system_memory_available_bytes',
            'System available memory in bytes',
            registry=self.registry
        )

        self.system_memory_usage_percent = GaugeMetric(
            'system_memory_usage_percent',
            'System memory usage percentage',
            registry=self.registry
        )

        # System CPU
        self.system_cpu_usage_percent = GaugeMetric(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            ['cpu_core'],
            registry=self.registry
        )

        # System disk
        self.system_disk_usage_bytes = GaugeMetric(
            'system_disk_usage_bytes',
            'System disk usage in bytes',
            ['mount_point'],
            registry=self.registry
        )

        self.system_disk_usage_percent = GaugeMetric(
            'system_disk_usage_percent',
            'System disk usage percentage',
            ['mount_point'],
            registry=self.registry
        )

        # System network
        self.system_network_bytes_sent = CounterMetric(
            'system_network_bytes_sent',
            'System network bytes sent',
            ['interface'],
            self.registry
        )

        self.system_network_bytes_received = CounterMetric(
            'system_network_bytes_received',
            'System network bytes received',
            ['interface'],
            self.registry
        )

        # Process info
        self.process_memory_usage_bytes = GaugeMetric(
            'process_memory_usage_bytes',
            'Process memory usage in bytes',
            registry=self.registry
        )

        self.process_cpu_usage_percent = GaugeMetric(
            'process_cpu_usage_percent',
            'Process CPU usage percentage',
            registry=self.registry
        )

        self.process_open_fds = GaugeMetric(
            'process_open_fds',
            'Number of open file descriptors',
            registry=self.registry
        )

        self.process_threads_count = GaugeMetric(
            'process_threads_count',
            'Number of threads',
            registry=self.registry
        )

    # HTTP Metrics Methods
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """記錄 HTTP 請求指標"""
        # Normalize endpoint
        endpoint = self._normalize_endpoint(endpoint)

        # Record request count
        self.http_requests_total.inc(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        )

        # Record duration
        self.http_request_duration.observe(duration, method=method, endpoint=endpoint)

        # Track in fallback storage
        if not PROMETHEUS_AVAILABLE:
            self._response_times.append(duration)
            key = f"{method}:{endpoint}"
            self._request_counts[key] = self._request_counts.get(key, 0) + 1
            if status_code >= 400:
                self._error_counts[key] = self._error_counts.get(key, 0) + 1

    def record_http_error(self, method: str, endpoint: str, error_type: str):
        """記錄 HTTP 錯誤"""
        endpoint = self._normalize_endpoint(endpoint)
        self.http_errors_total.inc(
            method=method,
            endpoint=endpoint,
            error_type=error_type
        )

    def _normalize_endpoint(self, endpoint: str) -> str:
        """規範化端點路徑，將路徑參數替換為佔位符"""
        # Common parameter replacements
        replacements = [
            (r'/\d+', '/{id}'),
            (r'/[a-f0-9-]{36}', '/{uuid}'),
            (r'/strategies/[a-zA-Z0-9_-]+', '/strategies/{id}'),
            (r'/users/[a-zA-Z0-9_-]+', '/users/{id}'),
            (r'/backtests/[a-zA-Z0-9_-]+', '/backtests/{id}'),
        ]
        import re
        for pattern, replacement in replacements:
            endpoint = re.sub(pattern, replacement, endpoint)
        return endpoint

    # Database Metrics Methods
    def record_db_query(self, database: str, operation: str, duration: float, slow_threshold: float = 1.0):
        """記錄數據庫查詢指標"""
        self.db_query_duration.observe(duration, database=database, operation=operation)

        # Track slow queries
        if duration > slow_threshold:
            self.db_slow_queries_total.inc(database=database)

    def record_db_error(self, database: str, error_type: str):
        """記錄數據庫錯誤"""
        self.db_errors_total.inc(database=database, error_type=error_type)

    def set_db_connections(self, database: str, active: int, idle: int):
        """設置數據庫連接數"""
        self.db_connections_active.set(active, database=database)
        self.db_connections_idle.set(idle, database=database)

    # Cache Metrics Methods
    def record_cache_hit(self, cache_layer: str, cache_type: str = "memory"):
        """記錄緩存命中"""
        self.cache_hits_total.inc(cache_layer=cache_layer, cache_type=cache_type)

    def record_cache_miss(self, cache_layer: str, cache_type: str = "memory"):
        """記錄緩存未命中"""
        self.cache_misses_total.inc(cache_layer=cache_layer, cache_type=cache_type)

    def set_cache_hit_ratio(self, cache_layer: str, ratio: float):
        """設置緩存命中率"""
        self.cache_hit_ratio.set(ratio, cache_layer=cache_layer)

    def record_cache_eviction(self, cache_layer: str):
        """記錄緩存驅逐"""
        self.cache_evictions_total.inc(cache_layer=cache_layer)

    def set_cache_size(self, cache_layer: str, size_bytes: int):
        """設置緩存大小"""
        self.cache_size_bytes.set(size_bytes, cache_layer=cache_layer)

    # Business Metrics Methods
    def record_strategy_execution(self, strategy_type: str, status: str, duration: float = None):
        """記錄策略執行"""
        self.strategy_executions_total.inc(strategy_type=strategy_type, status=status)
        if duration is not None:
            self.strategy_execution_duration.observe(duration, strategy_type=strategy_type)

    def set_active_strategies(self, count: int):
        """設置活躍策略數量"""
        self.active_strategies.set(count)

    def record_trading_volume(self, symbol: str, side: str, volume: float):
        """記錄交易量"""
        self.trading_volume_total.inc(volume, symbol=symbol, side=side)

    def record_trading_value(self, symbol: str, side: str, value: float, currency: str = "HKD"):
        """記錄交易金額"""
        self.trading_value_total.inc(value, symbol=symbol, side=side, currency=currency)

    def set_active_users(self, count: int, user_type: str = "authenticated"):
        """設置活躍用戶數"""
        self.active_users_total.set(count, user_type=user_type)

    def record_backtest_execution(self, status: str, duration: float = None):
        """記錄回測執行"""
        self.backtest_executions_total.inc(status=status)
        if duration is not None:
            self.backtest_duration_seconds.observe(duration)

    # System Metrics Methods
    def update_system_metrics(self):
        """更新系統指標"""
        if not PSUTIL_AVAILABLE:
            return

        import psutil

        # Memory metrics
        memory = psutil.virtual_memory()
        self.system_memory_usage_bytes.set(memory.used)
        self.system_memory_available_bytes.set(memory.available)
        self.system_memory_usage_percent.set(memory.percent)

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        for i, percent in enumerate(psutil.cpu_percent(interval=0.1, percpu=True)):
            self.system_cpu_usage_percent.set(percent, cpu_core=str(i))

        # Disk metrics
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                self.system_disk_usage_bytes.set(usage.used, mount_point=partition.mountpoint)
                self.system_disk_usage_percent.set(usage.percent, mount_point=partition.mountpoint)
            except PermissionError:
                continue

        # Network metrics
        net_io = psutil.net_io_counters()
        self.system_network_bytes_sent.inc(net_io.bytes_sent, interface='total')
        self.system_network_bytes_received.inc(net_io.bytes_recv, interface='total')

        # Process metrics
        process = psutil.Process()
        self.process_memory_usage_bytes.set(process.memory_info().rss)
        self.process_cpu_usage_percent.set(process.cpu_percent())
        try:
            self.process_open_fds.set(process.num_fds())
        except AttributeError:
            pass  # num_fds() not available on Windows
        self.process_threads_count.set(process.num_threads())

    # Utility Methods
    def get_metrics(self) -> str:
        """獲取 Prometheus 格式的指標"""
        self.update_system_metrics()

        if PROMETHEUS_AVAILABLE:
            return generate_latest(self.registry).decode('utf-8')
        else:
            # Fallback: simple text format
            return self._generate_simple_metrics()

    def _generate_simple_metrics(self) -> str:
        """生成簡單的指標格式（當 prometheus_client 不可用時）"""
        lines = []

        # HTTP request counts
        for key, count in self._request_counts.items():
            method, endpoint = key.split(':', 1)
            lines.append(f'http_requests_total{{method="{method}",endpoint="{endpoint}"}} {count}')

        # Response time stats
        if self._response_times:
            avg_time = sum(self._response_times) / len(self._response_times)
            lines.append(f'http_request_duration_seconds_avg {avg_time:.6f}')

        # System metrics
        if PSUTIL_AVAILABLE:
            import psutil
            memory = psutil.virtual_memory()
            lines.append(f'system_memory_usage_bytes {memory.used}')
            lines.append(f'system_memory_usage_percent {memory.percent}')

            cpu = psutil.cpu_percent()
            lines.append(f'system_cpu_usage_percent {cpu}')

        return '\n'.join(lines)

    def start_metrics_server(self, port: int = 8000):
        """啟動指標 HTTP 服務器"""
        if self._server_started:
            return

        if PROMETHEUS_AVAILABLE:
            start_http_server(port, registry=self.registry)
            self._server_started = True
        else:
            # Start simple HTTP server
            import http.server
            import socketserver

            class MetricsHandler(http.server.BaseHTTPRequestHandler):
                def __init__(self, collector, *args, **kwargs):
                    self.collector = collector
                    super().__init__(*args, **kwargs)

                def do_GET(self):
                    if self.path == '/metrics':
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(self.collector.get_metrics().encode())
                    else:
                        self.send_response(404)
                        self.end_headers()

                def log_message(self, format, *args):
                    pass  # Suppress logging

            def run_server():
                with socketserver.TCPServer(("", port), lambda *args, **kwargs: MetricsHandler(self, *args, **kwargs)) as httpd:
                    self._server_started = True
                    httpd.serve_forever()

            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()

    def get_performance_snapshot(self) -> PerformanceSnapshot:
        """獲取性能快照"""
        self.update_system_metrics()

        avg_response = 0
        if self._response_times:
            avg_response = sum(self._response_times) / len(self._response_times)

        total_requests = sum(self._request_counts.values())
        total_errors = sum(self._error_counts.values())
        error_rate = total_errors / total_requests if total_requests > 0 else 0

        memory_mb = 0
        if PSUTIL_AVAILABLE:
            import psutil
            memory_mb = psutil.virtual_memory().used / (1024 * 1024)

        cpu_percent = 0
        if PSUTIL_AVAILABLE:
            import psutil
            cpu_percent = psutil.cpu_percent()

        return PerformanceSnapshot(
            timestamp=time.time(),
            total_requests=total_requests,
            avg_response_time=avg_response,
            error_rate=error_rate,
            active_connections=0,  # Would be populated from actual connection tracking
            memory_usage_mb=memory_mb,
            cpu_usage_percent=cpu_percent
        )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """獲取指標摘要"""
        snapshot = self.get_performance_snapshot()

        return {
            "timestamp": snapshot.timestamp,
            "app_name": self.app_name,
            "environment": self.environment,
            "performance": {
                "total_requests": snapshot.total_requests,
                "avg_response_time_ms": snapshot.avg_response_time * 1000,
                "error_rate_percent": snapshot.error_rate * 100,
            },
            "system": {
                "memory_usage_mb": snapshot.memory_usage_mb,
                "cpu_usage_percent": snapshot.cpu_usage_percent,
            },
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "psutil_available": PSUTIL_AVAILABLE,
            "metrics_server_running": self._server_started,
        }


# Global singleton instance
_metrics_collector: Optional[PrometheusMetricsCollector] = None


def get_metrics_collector(app_name: str = "cbsc-trading",
                          environment: str = "production") -> PrometheusMetricsCollector:
    """獲取全局指標收集器單例"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = PrometheusMetricsCollector(app_name, environment)
    return _metrics_collector


# Decorators
def track_metrics(collector: PrometheusMetricsCollector = None):
    """指標收集裝飾器"""
    if collector is None:
        collector = get_metrics_collector()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            # Try to extract method and endpoint from args
            method = getattr(args[0], 'method', 'UNKNOWN') if args else 'UNKNOWN'
            endpoint = getattr(args[0], 'path', 'unknown') if args else 'unknown'

            status_code = 200
            try:
                result = await func(*args, **kwargs)
                status_code = getattr(result, 'status_code', 200)
                return result
            except Exception as e:
                status_code = 500
                collector.record_http_error(method, endpoint, type(e).__name__)
                raise
            finally:
                duration = time.time() - start_time
                collector.record_http_request(method, endpoint, status_code, duration)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            method = 'UNKNOWN'
            endpoint = 'unknown'

            status_code = 200
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                if collector:
                    collector.record_http_error(method, endpoint, type(e).__name__)
                raise
            finally:
                if collector:
                    duration = time.time() - start_time
                    collector.record_http_request(method, endpoint, status_code, duration)

        # Return appropriate wrapper based on whether func is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_http_request(method: str, endpoint: str):
    """HTTP 請求跟蹤上下文管理器"""
    import contextlib

    collector = get_metrics_collector()
    endpoint = collector._normalize_endpoint(endpoint)

    @contextlib.contextmanager
    def tracker():
        start_time = time.time()
        status_code = 200
        try:
            yield
        except Exception as e:
            status_code = 500
            collector.record_http_error(method, endpoint, type(e).__name__)
            raise
        finally:
            duration = time.time() - start_time
            collector.record_http_request(method, endpoint, status_code, duration)

    return tracker()


def track_db_query(database: str, operation: str, slow_threshold: float = 1.0):
    """數據庫查詢跟蹤上下文管理器"""
    import contextlib

    collector = get_metrics_collector()

    @contextlib.contextmanager
    def tracker():
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            collector.record_db_query(database, operation, duration, slow_threshold)

    return tracker()


def track_strategy_execution(strategy_type: str):
    """策略執行跟蹤上下文管理器"""
    import contextlib

    collector = get_metrics_collector()

    @contextlib.contextmanager
    def tracker():
        start_time = time.time()
        status = "success"
        try:
            yield
        except Exception as e:
            status = "failed"
            raise
        finally:
            duration = time.time() - start_time
            collector.record_strategy_execution(strategy_type, status, duration)

    return tracker()


# For backwards compatibility
def create_metrics_collector(app_name: str = "cbsc-trading",
                             environment: str = "production") -> PrometheusMetricsCollector:
    """創建新的指標收集器實例"""
    return PrometheusMetricsCollector(app_name, environment)
