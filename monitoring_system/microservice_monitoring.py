#!/usr/bin/env python3
"""
微服務監控和鏈路追蹤模塊
Microservice Monitoring and Distributed Tracing Module

監控量化交易微服務、收集鏈路追蹤數據、分析服務依賴關係
"""

import time
import uuid
import json
import logging
import asyncio
import aiohttp
import psutil
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict, field
from contextlib import asynccontextmanager
from functools import wraps
import threading
from datetime import datetime, timedelta
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, generate_latest
import requests
import socket

logger = logging.getLogger(__name__)

@dataclass
class ServiceEndpoint:
    """服務端點定義"""
    name: str
    host: str
    port: int
    health_endpoint: str = "/health"
    metrics_endpoint: str = "/metrics"
    timeout: int = 5

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def health_url(self) -> str:
        return f"{self.base_url}{self.health_endpoint}"

    @property
    def metrics_url(self) -> str:
        return f"{self.base_url}{self.metrics_endpoint}"

@dataclass
class ServiceMetrics:
    """服務指標數據"""
    service_name: str
    instance_id: str
    timestamp: float

    # 基本指標
    is_healthy: bool
    response_time: float
    uptime: float

    # 請求指標
    requests_total: int
    requests_per_second: float
    error_rate: float
    average_response_time: float

    # 資源指標
    cpu_usage: float
    memory_usage: float
    disk_io: Dict[str, float]
    network_io: Dict[str, float]

    # 業務指標
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TraceSpan:
    """鏈路追蹤Span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: float
    end_time: float
    duration: float

    # 服務信息
    service_name: str
    component: str

    # 標籤和日誌
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)

    # 狀態
    status: str = "success"  # success, error, timeout
    error_message: Optional[str] = None

class ServiceMonitor:
    """微服務監控器"""

    def __init__(self):
        """初始化服務監控器"""
        self.service_endpoints = {
            "data-service": ServiceEndpoint("data-service", "localhost", 8001),
            "analytics-service": ServiceEndpoint("analytics-service", "localhost", 8002),
            "backtest-service": ServiceEndpoint("backtest-service", "localhost", 8003),
            "notification-service": ServiceEndpoint("notification-service", "localhost", 8004),
            "config-service": ServiceEndpoint("config-service", "localhost", 8005),
        }

        self.active_traces = {}
        self.trace_spans = []

        # 初始化Prometheus指標
        self.registry = CollectorRegistry()

        # 服務可用性指標
        self.service_up = Gauge('service_up', 'Service availability', ['service_name', 'instance'], registry=self.registry)
        self.service_response_time = Gauge('service_response_time_seconds', 'Service response time', ['service_name', 'instance'], registry=self.registry)

        # 請求指標
        self.http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['service_name', 'method', 'status'], registry=self.registry)
        self.http_request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['service_name', 'method'], registry=self.registry)

        # 業務指標
        self.business_metric = Gauge('business_metric_value', 'Business metric value', ['service_name', 'metric_name'], registry=self.registry)
        self.operation_duration = Histogram('operation_duration_seconds', 'Operation duration', ['service_name', 'operation'], registry=self.registry)

        # 監控狀態
        self.monitoring_active = True
        self.service_health_cache = {}
        self.metrics_collection_thread = None

        logger.info("Service monitor initialized")

    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """
        檢查單個服務健康狀態

        Args:
            service_name: 服務名稱

        Returns:
            Dict[str, Any]: 健康檢查結果
        """
        endpoint = self.service_endpoints.get(service_name)
        if not endpoint:
            return {
                "service": service_name,
                "healthy": False,
                "error": "Service not configured",
                "timestamp": time.time()
            }

        try:
            start_time = time.time()

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=endpoint.timeout)) as session:
                async with session.get(endpoint.health_url) as response:
                    response_time = time.time() - start_time

                    # 檢查HTTP狀態
                    if response.status == 200:
                        try:
                            # 嘗試解析響應體
                            health_data = await response.json()
                            is_healthy = health_data.get('status', 'ok').lower() == 'ok'
                        except:
                            # 如果無法解析JSON，認為健康狀態未知但服務可用
                            is_healthy = True
                            health_data = {}

                        result = {
                            "service": service_name,
                            "healthy": is_healthy,
                            "status_code": response.status,
                            "response_time": response_time,
                            "health_data": health_data,
                            "timestamp": time.time()
                        }

                        # 更新緩存
                        self.service_health_cache[service_name] = result

                        # 更新Prometheus指標
                        self.service_up.labels(service_name=service_name, instance=socket.gethostname()).set(1 if is_healthy else 0)
                        self.service_response_time.labels(service_name=service_name, instance=socket.gethostname()).set(response_time)

                        return result
                    else:
                        result = {
                            "service": service_name,
                            "healthy": False,
                            "status_code": response.status,
                            "response_time": response_time,
                            "error": f"HTTP {response.status}",
                            "timestamp": time.time()
                        }

                        self.service_health_cache[service_name] = result
                        self.service_up.labels(service_name=service_name, instance=socket.gethostname()).set(0)

                        return result

        except asyncio.TimeoutError:
            result = {
                "service": service_name,
                "healthy": False,
                "error": "Timeout",
                "timestamp": time.time()
            }
            self.service_health_cache[service_name] = result
            self.service_up.labels(service_name=service_name, instance=socket.gethostname()).set(0)
            return result

        except Exception as e:
            result = {
                "service": service_name,
                "healthy": False,
                "error": str(e),
                "timestamp": time.time()
            }
            self.service_health_cache[service_name] = result
            self.service_up.labels(service_name=service_name, instance=socket.gethostname()).set(0)
            return result

    async def check_all_services_health(self) -> Dict[str, Any]:
        """
        檢查所有服務健康狀態

        Returns:
            Dict[str, Any]: 所有服務健康狀態
        """
        tasks = []
        for service_name in self.service_endpoints.keys():
            tasks.append(self.check_service_health(service_name))

        health_results = await asyncio.gather(*tasks, return_exceptions=True)

        health_summary = {}
        healthy_count = 0
        total_count = len(self.service_endpoints)

        for i, service_name in enumerate(self.service_endpoints.keys()):
            result = health_results[i]
            if isinstance(result, Exception):
                health_summary[service_name] = {
                    "service": service_name,
                    "healthy": False,
                    "error": str(result),
                    "timestamp": time.time()
                }
            else:
                health_summary[service_name] = result
                if result.get("healthy", False):
                    healthy_count += 1

        return {
            "timestamp": time.time(),
            "total_services": total_count,
            "healthy_services": healthy_count,
            "unhealthy_services": total_count - healthy_count,
            "health_percentage": (healthy_count / total_count) * 100,
            "services": health_summary
        }

    async def collect_service_metrics(self, service_name: str) -> ServiceMetrics:
        """
        收集單個服務指標

        Args:
            service_name: 服務名稱

        Returns:
            ServiceMetrics: 服務指標數據
        """
        endpoint = self.service_endpoints.get(service_name)
        if not endpoint:
            raise ValueError(f"Service {service_name} not configured")

        try:
            # 獲取健康狀態
            health_result = await self.check_service_health(service_name)
            is_healthy = health_result.get("healthy", False)
            response_time = health_result.get("response_time", 0)

            # 獲取Prometheus指標
            metrics_data = {}
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=endpoint.timeout)) as session:
                    async with session.get(endpoint.metrics_url) as response:
                        if response.status == 200:
                            metrics_text = await response.text()
                            # 解析Prometheus指標格式
                            metrics_data = self._parse_prometheus_metrics(metrics_text)
            except Exception as e:
                logger.debug(f"Failed to collect metrics from {service_name}: {e}")

            # 解析指標
            requests_total = self._extract_metric_value(metrics_data, 'http_requests_total', 0)
            error_rate = self._extract_metric_value(metrics_data, 'http_requests_error_rate', 0)
            avg_response_time = self._extract_metric_value(metrics_data, 'http_request_duration_seconds_avg', response_time)

            # 計算RPS (需要時間窗口數據)
            requests_per_second = self._calculate_rps(requests_total, service_name)

            # 獲取進程資源使用情況
            process_info = self._get_process_info(service_name)

            metrics = ServiceMetrics(
                service_name=service_name,
                instance_id=socket.gethostname(),
                timestamp=time.time(),
                is_healthy=is_healthy,
                response_time=response_time,
                uptime=process_info.get('uptime', 0),
                requests_total=requests_total,
                requests_per_second=requests_per_second,
                error_rate=error_rate,
                average_response_time=avg_response_time,
                cpu_usage=process_info.get('cpu_percent', 0),
                memory_usage=process_info.get('memory_percent', 0),
                disk_io=process_info.get('disk_io', {}),
                network_io=process_info.get('network_io', {}),
                custom_metrics=self._extract_custom_metrics(metrics_data)
            )

            # 更新Prometheus指標
            self._update_service_prometheus_metrics(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect metrics for {service_name}: {e}")
            # 返回默認指標
            return ServiceMetrics(
                service_name=service_name,
                instance_id=socket.gethostname(),
                timestamp=time.time(),
                is_healthy=False,
                response_time=0,
                uptime=0,
                requests_total=0,
                requests_per_second=0,
                error_rate=100,
                average_response_time=0,
                cpu_usage=0,
                memory_usage=0,
                disk_io={},
                network_io={}
            )

    async def collect_all_service_metrics(self) -> Dict[str, ServiceMetrics]:
        """
        收集所有服務指標

        Returns:
            Dict[str, ServiceMetrics]: 所有服務指標數據
        """
        tasks = []
        for service_name in self.service_endpoints.keys():
            tasks.append(self.collect_service_metrics(service_name))

        metrics_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_metrics = {}
        for i, service_name in enumerate(self.service_endpoints.keys()):
            result = metrics_results[i]
            if isinstance(result, Exception):
                logger.error(f"Failed to collect metrics for {service_name}: {result}")
                continue
            all_metrics[service_name] = result

        return all_metrics

    def start_trace(self, operation_name: str, service_name: str, component: str = "unknown",
                   parent_span_id: Optional[str] = None, tags: Optional[Dict[str, Any]] = None) -> str:
        """
        開始鏈路追蹤

        Args:
            operation_name: 操作名稱
            service_name: 服務名稱
            component: 組件名稱
            parent_span_id: 父Span ID
            tags: 標籤

        Returns:
            str: Trace ID
        """
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())

        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=time.time(),
            end_time=0,
            duration=0,
            service_name=service_name,
            component=component,
            tags=tags or {}
        )

        self.active_traces[span_id] = span

        logger.debug(f"Started trace: {operation_name} (trace_id: {trace_id}, span_id: {span_id})")
        return span_id

    def finish_trace(self, span_id: str, status: str = "success", error_message: Optional[str] = None,
                    logs: Optional[List[Dict[str, Any]]] = None):
        """
        完成鏈路追蹤

        Args:
            span_id: Span ID
            status: 完成狀態
            error_message: 錯誤信息
            logs: 日誌信息
        """
        if span_id not in self.active_traces:
            logger.warning(f"Span {span_id} not found in active traces")
            return

        span = self.active_traces[span_id]
        span.end_time = time.time()
        span.duration = span.end_time - span.start_time
        span.status = status
        span.error_message = error_message
        span.logs = logs or []

        # 移動到完成的追蹤列表
        self.trace_spans.append(span)
        del self.active_traces[span_id]

        # 更新Prometheus指標
        self.operation_duration.labels(
            service_name=span.service_name,
            operation=span.operation_name
        ).observe(span.duration)

        logger.debug(f"Finished trace: {span.operation_name} (duration: {span.duration:.3f}s)")

    def get_trace_metrics(self, time_window: int = 300) -> Dict[str, Any]:
        """
        獲取鏈路追蹤指標

        Args:
            time_window: 時間窗口(秒)

        Returns:
            Dict[str, Any]: 鏈路追蹤指標
        """
        cutoff_time = time.time() - time_window
        recent_spans = [span for span in self.trace_spans if span.start_time > cutoff_time]

        # 統計指標
        total_spans = len(recent_spans)
        successful_spans = len([s for s in recent_spans if s.status == "success"])
        error_spans = len([s for s in recent_spans if s.status == "error"])

        # 按服務統計
        service_stats = {}
        for span in recent_spans:
            service = span.service_name
            if service not in service_stats:
                service_stats[service] = {
                    "total": 0,
                    "successful": 0,
                    "error": 0,
                    "avg_duration": 0,
                    "operations": {}
                }

            stats = service_stats[service]
            stats["total"] += 1
            if span.status == "success":
                stats["successful"] += 1
            elif span.status == "error":
                stats["error"] += 1

            # 操作統計
            op = span.operation_name
            if op not in stats["operations"]:
                stats["operations"][op] = {
                    "count": 0,
                    "total_duration": 0,
                    "avg_duration": 0
                }

            op_stats = stats["operations"][op]
            op_stats["count"] += 1
            op_stats["total_duration"] += span.duration
            op_stats["avg_duration"] = op_stats["total_duration"] / op_stats["count"]

        # 計算平均持續時間
        for service_name, stats in service_stats.items():
            if stats["total"] > 0:
                total_duration = sum(
                    span.duration for span in recent_spans
                    if span.service_name == service_name
                )
                stats["avg_duration"] = total_duration / stats["total"]

        return {
            "time_window": time_window,
            "timestamp": time.time(),
            "total_spans": total_spans,
            "successful_spans": successful_spans,
            "error_spans": error_spans,
            "error_rate": (error_spans / total_spans * 100) if total_spans > 0 else 0,
            "active_spans": len(self.active_traces),
            "service_statistics": service_stats
        }

    def _parse_prometheus_metrics(self, metrics_text: str) -> Dict[str, Any]:
        """解析Prometheus指標文本"""
        metrics = {}
        lines = metrics_text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if line.startswith('#') or not line:
                continue

            if '{' in line:
                # 複雜指標格式
                try:
                    name_part, value_part = line.split(' ', 1)
                    name = name_part.split('{')[0]
                    value = float(value_part.split(' ')[0])
                    metrics[name] = value
                except:
                    continue
            else:
                # 簡單指標格式
                try:
                    name, value = line.split(' ', 1)
                    metrics[name] = float(value)
                except:
                    continue

        return metrics

    def _extract_metric_value(self, metrics_data: Dict[str, Any], metric_name: str, default: float = 0) -> float:
        """提取指標值"""
        for key, value in metrics_data.items():
            if key.startswith(metric_name):
                return float(value)
        return default

    def _calculate_rps(self, requests_total: int, service_name: str) -> float:
        """計算每秒請求數"""
        # 這裡需要實現基於時間窗口的RPS計算
        # 簡化實現，實際應用中需要維護歷史數據
        return 0.0

    def _get_process_info(self, service_name: str) -> Dict[str, Any]:
        """獲取進程信息"""
        try:
            # 這裡可以通過進程名或端口查找進程
            # 簡化實現，返回當前進程信息
            process = psutil.Process()
            with process.oneshot():
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()

                # 獲取進程運行時間
                create_time = process.create_time()
                uptime = time.time() - create_time

                return {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "memory_bytes": memory_info.rss,
                    "uptime": uptime,
                    "pid": process.pid,
                    "disk_io": {},  # 需要實現磁盤IO統計
                    "network_io": {}  # 需要實現網絡IO統計
                }

        except Exception as e:
            logger.debug(f"Failed to get process info for {service_name}: {e}")
            return {}

    def _extract_custom_metrics(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取自定義業務指標"""
        custom_metrics = {}

        # 定義業務指標模式
        business_patterns = [
            'data_quality_score',
            'sharpe_calculation_errors_total',
            'backtest_execution_duration_seconds',
            'gpu_acceleration_enabled',
            'notification_delivery_duration_seconds'
        ]

        for pattern in business_patterns:
            for key, value in metrics_data.items():
                if key.startswith(pattern):
                    custom_metrics[key] = value

        return custom_metrics

    def _update_service_prometheus_metrics(self, metrics: ServiceMetrics):
        """更新服務Prometheus指標"""
        try:
            # 更新業務指標
            for metric_name, value in metrics.custom_metrics.items():
                self.business_metric.labels(
                    service_name=metrics.service_name,
                    metric_name=metric_name
                ).set(value)

        except Exception as e:
            logger.error(f"Failed to update service Prometheus metrics: {e}")

    def get_prometheus_metrics(self) -> str:
        """
        獲取Prometheus格式的指標

        Returns:
            str: Prometheus格式指標數據
        """
        return generate_latest(self.registry).decode('utf-8')

    @asynccontextmanager
    async def trace_operation(self, operation_name: str, service_name: str, component: str = "unknown",
                             tags: Optional[Dict[str, Any]] = None):
        """
        鏈路追蹤上下文管理器

        Args:
            operation_name: 操作名稱
            service_name: 服務名稱
            component: 組件名稱
            tags: 標籤
        """
        span_id = self.start_trace(operation_name, service_name, component, tags=tags)
        try:
            yield span_id
            self.finish_trace(span_id, status="success")
        except Exception as e:
            logs = [{"error": str(e), "timestamp": time.time()}]
            self.finish_trace(span_id, status="error", error_message=str(e), logs=logs)
            raise

# 全局服務監控器實例
service_monitor = ServiceMonitor()

def get_service_monitor() -> ServiceMonitor:
    """獲取服務監控器實例"""
    return service_monitor

# 裝飾器
def trace_service_call(operation_name: str, service_name: str):
    """服務調用鏈路追蹤裝飾器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with service_monitor.trace_operation(operation_name, service_name):
                return await func(*args, **kwargs)
        return wrapper
    return decorator

if __name__ == "__main__":
    async def main():
        """測試監控功能"""
        monitor = ServiceMonitor()

        print("Testing service monitoring...")

        # 測試健康檢查
        print("\n=== Health Check ===")
        health_result = await monitor.check_all_services_health()
        print(f"Services: {health_result['healthy_services']}/{health_result['total_services']} healthy")

        for service_name, result in health_result['services'].items():
            status = "✅" if result['healthy'] else "❌"
            print(f"  {status} {service_name}: {result.get('error', 'OK')}")

        # 測試指標收集
        print("\n=== Metrics Collection ===")
        metrics = await monitor.collect_all_service_metrics()
        for service_name, metric in metrics.items():
            print(f"  {service_name}: CPU={metric.cpu_usage:.1f}%, Memory={metric.memory_usage:.1f}%")

        # 測試鏈路追蹤
        print("\n=== Distributed Tracing ===")
        span_id = monitor.start_trace("test_operation", "analytics-service", "test_component")
        await asyncio.sleep(0.1)  # 模擬操作時間
        monitor.finish_trace(span_id, status="success")

        trace_metrics = monitor.get_trace_metrics()
        print(f"Trace metrics: {trace_metrics['total_spans']} spans, {trace_metrics['error_rate']:.1f}% error rate")

        # 獲取Prometheus指標
        prometheus_metrics = monitor.get_prometheus_metrics()
        print(f"\nPrometheus metrics generated: {len(prometheus_metrics)} bytes")

        print("\nService monitoring test completed!")

    asyncio.run(main())