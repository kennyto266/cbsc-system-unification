#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
監控和指標收集系統
Phase 4: Prometheus集成和系統性能監控
"""

import time
import asyncio
import psutil
import GPUtil
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import threading
from contextlib import asynccontextmanager

from prometheus_client import (
    Counter, Histogram, Gauge, CollectorRegistry, generate_latest,
    CONTENT_TYPE_LATEST
)
import redis.asyncio as redis
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """指標數據點"""
    name: str
    value: float
    labels: Dict[str, str]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat()
        }

class MetricsCollector:
    """指標收集器"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.gauges: Dict[str, float] = defaultdict(float)

        # Prometheus指標
        self.registry = CollectorRegistry()
        self._setup_prometheus_metrics()

        # 系統監控線程
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None

        # 自定義指標註冊
        self.custom_metrics: Dict[str, Callable] = {}

    def _setup_prometheus_metrics(self):
        """設置Prometheus指標"""
        # HTTP請求指標
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )

        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            registry=self.registry
        )

        # 系統資源指標
        self.cpu_usage = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )

        self.memory_usage = Gauge(
            'memory_usage_percent',
            'Memory usage percentage',
            registry=self.registry
        )

        self.disk_usage = Gauge(
            'disk_usage_percent',
            'Disk usage percentage',
            registry=self.registry
        )

        # GPU指標
        self.gpu_usage = Gauge(
            'gpu_usage_percent',
            'GPU usage percentage',
            ['gpu_id'],
            registry=self.registry
        )

        self.gpu_memory_usage = Gauge(
            'gpu_memory_usage_percent',
            'GPU memory usage percentage',
            ['gpu_id'],
            registry=self.registry
        )

        # 應用指標
        self.active_optimizations = Gauge(
            'active_optimizations',
            'Number of active optimization jobs',
            registry=self.registry
        )

        self.websocket_connections = Gauge(
            'websocket_connections',
            'Number of active WebSocket connections',
            registry=self.registry
        )

        self.optimization_duration = Histogram(
            'optimization_duration_seconds',
            'Optimization job duration',
            registry=self.registry
        )

        # 數據庫指標
        self.db_connections = Gauge(
            'db_connections_active',
            'Active database connections',
            registry=self.registry
        )

        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration',
            registry=self.registry
        )

        # 錯誤指標
        self.error_count = Counter(
            'errors_total',
            'Total errors',
            ['error_type', 'endpoint'],
            registry=self.registry
        )

        # 隊列指標
        self.queue_length = Gauge(
            'queue_length',
            'Length of job queue',
            ['queue_name'],
            registry=self.registry
        )

    def start_monitoring(self, interval: int = 30):
        """開始系統監控"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info("系統監控已啟動")

    def stop_monitoring(self):
        """停止系統監控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("系統監控已停止")

    def _monitoring_loop(self, interval: int):
        """監控循環"""
        while self.monitoring_active:
            try:
                # 收集系統指標
                self._collect_system_metrics()

                # 收集GPU指標
                self._collect_gpu_metrics()

                # 如果有Redis，收集Redis指標
                if self.redis_client:
                    asyncio.run(self._collect_redis_metrics())

                # 運行自定義指標
                for name, collector in self.custom_metrics.items():
                    try:
                        value = collector()
                        self.set_gauge(name, value)
                    except Exception as e:
                        logger.error(f"自定義指標 {name} 收集失敗: {e}")

                time.sleep(interval)

            except Exception as e:
                logger.error(f"監控循環錯誤: {e}")
                time.sleep(5)

    def _collect_system_metrics(self):
        """收集系統指標"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.set_gauge("cpu_usage", cpu_percent)
            self.cpu_usage.set(cpu_percent)

            # 內存使用率
            memory = psutil.virtual_memory()
            self.set_gauge("memory_usage", memory.percent)
            self.memory_usage.set(memory.percent)

            # 磁盤使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.set_gauge("disk_usage", disk_percent)
            self.disk_usage.set(disk_percent)

            # 網絡統計
            network = psutil.net_io_counters()
            self.set_counter("network_bytes_sent", network.bytes_sent)
            self.set_counter("network_bytes_recv", network.bytes_recv)

            # 進程數量
            process_count = len(psutil.pids())
            self.set_gauge("process_count", process_count)

        except Exception as e:
            logger.error(f"收集系統指標失敗: {e}")

    def _collect_gpu_metrics(self):
        """收集GPU指標"""
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_id = str(gpu.id)

                # GPU使用率
                self.set_gauge(f"gpu_{gpu_id}_usage", gpu.load * 100)
                self.gpu_usage.labels(gpu_id=gpu_id).set(gpu.load * 100)

                # GPU內存使用率
                memory_percent = (gpu.memoryUsed / gpu.memoryTotal) * 100
                self.set_gauge(f"gpu_{gpu_id}_memory_usage", memory_percent)
                self.gpu_memory_usage.labels(gpu_id=gpu_id).set(memory_percent)

                # GPU溫度
                self.set_gauge(f"gpu_{gpu_id}_temperature", gpu.temperature)

        except Exception as e:
            logger.debug(f"收集GPU指標失敗（可能無GPU）: {e}")

    async def _collect_redis_metrics(self):
        """收集Redis指標"""
        try:
            info = await self.redis_client.info()

            # 內存使用
            used_memory = info.get('used_memory', 0)
            self.set_gauge("redis_memory_used", used_memory)

            # 連接數
            connected_clients = info.get('connected_clients', 0)
            self.set_gauge("redis_connections", connected_clients)

            # 命令統計
            total_commands = info.get('total_commands_processed', 0)
            self.set_counter("redis_commands_total", total_commands)

            # 鍵空間統計
            keyspace_hits = info.get('keyspace_hits', 0)
            keyspace_misses = info.get('keyspace_misses', 0)
            self.set_counter("redis_keyspace_hits", keyspace_hits)
            self.set_counter("redis_keyspace_misses", keyspace_misses)

        except Exception as e:
            logger.error(f"收集Redis指標失敗: {e}")

    # 指標操作方法
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """增加計數器"""
        key = self._make_key(name, labels)
        self.counters[key] += value

        # 記錄時間序列
        self._record_metric(name, value, labels)

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """設置儀表值"""
        key = self._make_key(name, labels)
        self.gauges[key] = value

        # 記錄時間序列
        self._record_metric(name, value, labels)

    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """觀測直方圖值"""
        key = self._make_key(name, labels)
        self.histograms[key].append(value)

        # 限制直方圖大小
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-500:]

        # 記錄時間序列
        self._record_metric(name, value, labels)

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """生成指標鍵"""
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """記錄指標到時間序列"""
        point = MetricPoint(
            name=name,
            value=value,
            labels=labels or {},
            timestamp=datetime.now()
        )

        self.metrics[name].append(point)

        # 如果有Redis，也存儲到Redis
        if self.redis_client:
            asyncio.create_task(self._store_metric_to_redis(point))

    async def _store_metric_to_redis(self, point: MetricPoint):
        """存儲指標到Redis"""
        try:
            key = f"metrics:{point.name}:{int(point.timestamp.timestamp())}"
            await self.redis_client.setex(
                key,
                86400,  # 24小時過期
                json.dumps(point.to_dict())
            )
        except Exception as e:
            logger.error(f"存儲指標到Redis失敗: {e}")

    def register_custom_metric(self, name: str, collector: Callable[[], float]):
        """註冊自定義指標收集器"""
        self.custom_metrics[name] = collector
        logger.info(f"註冊自定義指標: {name}")

    # HTTP相關指標
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """記錄HTTP請求"""
        # Prometheus指標
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()

        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        # 自定義指標
        labels = {"method": method, "endpoint": endpoint, "status": str(status_code)}
        self.increment_counter("http_requests_total", 1.0, labels)
        self.observe_histogram("http_request_duration", duration, labels)

    def record_optimization_job(self, duration: float, success: bool):
        """記錄優化任務"""
        # Prometheus指標
        self.optimization_duration.observe(duration)

        # 自定義指標
        self.observe_histogram("optimization_duration", duration)
        self.increment_counter("optimization_jobs_total", 1.0, {"success": str(success)})

    # 隊列指標
    def set_queue_length(self, queue_name: str, length: int):
        """設置隊列長度"""
        self.queue_length.labels(queue_name=queue_name).set(length)
        self.set_gauge("queue_length", length, {"queue": queue_name})

    # 錯誤記錄
    def record_error(self, error_type: str, endpoint: str, error_message: str):
        """記錄錯誤"""
        self.error_count.labels(
            error_type=error_type,
            endpoint=endpoint
        ).inc()

        self.increment_counter("errors_total", 1.0, {
            "type": error_type,
            "endpoint": endpoint
        })

    # 指標查詢方法
    def get_metrics_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """獲取指標摘要"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        summary = {
            "time_range_minutes": minutes,
            "timestamp": datetime.now().isoformat(),
            "counters": {},
            "gauges": self.gauges.copy(),
            "histograms": {}
        }

        # 處理計數器
        for key, value in self.counters.items():
            summary["counters"][key] = value

        # 處理直方圖
        for name, values in self.histograms.items():
            if values:
                summary["histograms"][name] = {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "p50": self._percentile(values, 0.5),
                    "p95": self._percentile(values, 0.95),
                    "p99": self._percentile(values, 0.99)
                }

        return summary

    def _percentile(self, values: List[float], percentile: float) -> float:
        """計算百分位數"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def get_prometheus_metrics(self) -> str:
        """獲取Prometheus格式的指標"""
        return generate_latest(self.registry).decode('utf-8')

class MetricsMiddleware:
    """指標收集中間件"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """處理請求並收集指標"""
        start_time = time.time()

        try:
            response = await call_next(request)
            success = True
        except Exception as e:
            # 記錄錯誤
            self.metrics_collector.record_error(
                error_type=type(e).__name__,
                endpoint=request.url.path,
                error_message=str(e)
            )
            raise
        else:
            # 記錄成功請求
            duration = time.time() - start_time
            self.metrics_collector.record_http_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration=duration
            )

            return response

# 全局指標收集器實例
metrics_collector = None

def init_metrics(redis_client: Optional[redis.Redis] = None) -> MetricsCollector:
    """初始化指標收集器"""
    global metrics_collector
    metrics_collector = MetricsCollector(redis_client)
    metrics_collector.start_monitoring()
    return metrics_collector

async def get_metrics_collector() -> MetricsCollector:
    """獲取指標收集器實例"""
    return metrics_collector

# FastAPI端點工廠函數
def create_metrics_endpoint():
    """創建指標端點"""
    async def metrics():
        if metrics_collector is None:
            return PlainTextResponse("指標收集器未初始化", status_code=503)
        return PlainTextResponse(
            metrics_collector.get_prometheus_metrics(),
            media_type=CONTENT_TYPE_LATEST
        )
    return metrics

def create_health_endpoint():
    """創建健康檢查端點"""
    async def health():
        if metrics_collector is None:
            return {"status": "unhealthy", "reason": "指標收集器未初始化"}

        try:
            # 基本健康檢查
            cpu_ok = psutil.cpu_percent() < 95
            memory_ok = psutil.virtual_memory().percent < 95
            disk_ok = psutil.disk_usage('/').percent < 95

            status = "healthy" if all([cpu_ok, memory_ok, disk_ok]) else "degraded"

            return {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "checks": {
                    "cpu": "ok" if cpu_ok else "critical",
                    "memory": "ok" if memory_ok else "critical",
                    "disk": "ok" if disk_ok else "critical"
                }
            }

        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return {
                "status": "unhealthy",
                "reason": str(e),
                "timestamp": datetime.now().isoformat()
            }

    return health

# 上下文管理器用於自定義指標收集中間件
@asynccontextmanager
async def measure_time(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """測量執行時間的上下文管理器"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        if metrics_collector:
            metrics_collector.observe_histogram(metric_name, duration, labels)

def timed(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """裝飾器：測量函數執行時間"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            async with measure_time(metric_name, labels):
                return await func(*args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                if metrics_collector:
                    metrics_collector.observe_histogram(metric_name, duration, labels)
            return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator