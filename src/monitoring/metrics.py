#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prometheus Metrics Collection
Prometheus指标收集模块

用于收集CBSC Strategy API的业务和技术指标
"""

import time
import logging
from typing import Dict, Any
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# HTTP指标
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# 业务指标
active_strategies = Gauge(
    'active_strategies_count',
    'Number of active strategies'
)

strategy_executions_total = Counter(
    'strategy_executions_total',
    'Total strategy executions',
    ['strategy_type', 'status']
)

strategy_execution_duration = Histogram(
    'strategy_execution_duration_seconds',
    'Strategy execution duration in seconds',
    ['strategy_type'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0]
)

websocket_connections = Gauge(
    'websocket_connections_current',
    'Current number of WebSocket connections'
)

websocket_messages_total = Counter(
    'websocket_messages_total',
    'Total WebSocket messages',
    ['message_type', 'direction']
)

# 缓存指标
cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result']
)

cache_size = Gauge(
    'cache_size_bytes',
    'Cache size in bytes',
    ['cache_name']
)

# 数据库连接池指标
db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

db_connections_idle = Gauge(
    'db_connections_idle',
    'Idle database connections'
)

# 系统资源指标
system_memory_usage = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes'
)

system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Prometheus指标收集中间件"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录指标
        method = request.method
        path = request.url.path
        status_code = str(response.status_code)

        # 过滤健康检查端点
        if path not in ['/health', '/metrics']:
            http_requests_total.labels(
                method=method,
                endpoint=path,
                status_code=status_code
            ).inc()

            http_request_duration.labels(
                method=method,
                endpoint=path
            ).observe(process_time)

        return response


def track_strategy_execution(strategy_type: str):
    """策略执行时间跟踪装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'failed'
                logger.error(f"Strategy execution failed: {e}")
                raise
            finally:
                duration = time.time() - start_time
                strategy_executions_total.labels(
                    strategy_type=strategy_type,
                    status=status
                ).inc()
                strategy_execution_duration.labels(
                    strategy_type=strategy_type
                ).observe(duration)

        return wrapper
    return decorator


def update_cache_metrics(operation: str, result: str, cache_name: str = 'default'):
    """更新缓存指标"""
    cache_operations_total.labels(
        operation=operation,
        result=result
    ).inc()


def update_active_strategies(count: int):
    """更新活跃策略数"""
    active_strategies.set(count)


def update_websocket_connections(count: int):
    """更新WebSocket连接数"""
    websocket_connections.set(count)


def track_websocket_message(message_type: str, direction: str):
    """跟踪WebSocket消息"""
    websocket_messages_total.labels(
        message_type=message_type,
        direction=direction  # 'sent' or 'received'
    ).inc()


def update_db_pool_metrics(active: int, idle: int):
    """更新数据库连接池指标"""
    db_connections_active.set(active)
    db_connections_idle.set(idle)


def update_system_metrics():
    """更新系统指标"""
    try:
        import psutil

        # 内存使用
        memory = psutil.virtual_memory()
        system_memory_usage.set(memory.used)

        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        system_cpu_usage.set(cpu_percent)

    except ImportError:
        logger.warning("psutil not available, system metrics disabled")
    except Exception as e:
        logger.error(f"Failed to update system metrics: {e}")


def get_metrics() -> str:
    """获取Prometheus格式的指标"""
    # 更新系统指标
    update_system_metrics()

    # 生成指标数据
    return generate_latest()


def create_cache_size_gauges(cache_names: list):
    """为不同缓存创建大小指标"""
    for cache_name in cache_names:
        cache_size.labels(cache_name=cache_name)


# 指标导出端点处理
async def metrics_endpoint():
    """Prometheus指标导出端点"""
    from fastapi.responses import Response

    try:
        metrics_data = get_metrics()
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return Response(
            content="Error generating metrics",
            status_code=500
        )


# 指标初始化
def initialize_metrics():
    """初始化指标"""
    logger.info("Initializing Prometheus metrics...")

    # 创建缓存大小指标
    cache_names = ['strategy_cache', 'user_cache', 'market_data_cache']
    create_cache_size_gauges(cache_names)

    logger.info("Prometheus metrics initialized successfully")