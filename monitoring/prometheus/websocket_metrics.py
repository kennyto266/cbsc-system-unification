#!/usr/bin/env python3
"""
WebSocket Prometheus监控指标
WebSocket Prometheus Metrics

为WebSocket连接池提供Prometheus监控指标导出
"""

import time
import logging
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class WebSocketMetrics:
    """WebSocket监控指标管理器"""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        初始化监控指标

        Args:
            registry: Prometheus注册器，如果为None则使用默认注册器
        """
        self.registry = registry or CollectorRegistry()

        # 创建指标
        self._create_metrics()

        logger.info("WebSocket Prometheus metrics initialized")

    def _create_metrics(self):
        """创建所有监控指标"""

        # 连接指标
        self.websocket_connections_active = Gauge(
            'websocket_connections_active',
            '当前活跃WebSocket连接数',
            ['channel', 'user_id'],
            registry=self.registry
        )

        self.websocket_connections_total = Counter(
            'websocket_connections_total',
            '总WebSocket连接数',
            ['status', 'channel'],
            registry=self.registry
        )

        self.websocket_connection_duration_seconds = Histogram(
            'websocket_connection_duration_seconds',
            'WebSocket连接持续时间',
            buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600],
            registry=self.registry
        )

        # 消息指标
        self.websocket_messages_total = Counter(
            'websocket_messages_total',
            '总WebSocket消息数',
            ['message_type', 'direction', 'channel'],
            registry=self.registry
        )

        self.websocket_message_duration_seconds = Histogram(
            'websocket_message_duration_seconds',
            'WebSocket消息处理延迟',
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=self.registry
        )

        self.websocket_message_size_bytes = Histogram(
            'websocket_message_size_bytes',
            'WebSocket消息大小',
            buckets=[10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000],
            registry=self.registry
        )

        # 错误指标
        self.websocket_errors_total = Counter(
            'websocket_errors_total',
            'WebSocket错误总数',
            ['error_type', 'channel'],
            registry=self.registry
        )

        self.websocket_reconnects_total = Counter(
            'websocket_reconnects_total',
            'WebSocket重连次数',
            ['user_id', 'channel'],
            registry=self.registry
        )

        # 系统资源指标
        self.websocket_memory_usage_bytes = Gauge(
            'websocket_memory_usage_bytes',
            'WebSocket服务内存使用量',
            registry=self.registry
        )

        self.websocket_cpu_usage_percent = Gauge(
            'websocket_cpu_usage_percent',
            'WebSocket服务CPU使用率',
            registry=self.registry
        )

        # 性能指标
        self.websocket_broadcast_duration_seconds = Histogram(
            'websocket_broadcast_duration_seconds',
            '广播消息处理时间',
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
            registry=self.registry
        )

        self.websocket_subscriptions_active = Gauge(
            'websocket_subscriptions_active',
            '当前活跃订阅数',
            ['subscription_type'],
            registry=self.registry
        )

    def record_connection_opened(self, channel: str, user_id: str = ""):
        """记录新连接打开"""
        self.websocket_connections_total.labels(status='opened', channel=channel).inc()
        self.websocket_connections_active.labels(channel=channel, user_id=user_id).set(
            self.websocket_connections_active.labels(channel=channel, user_id=user_id)._value.get() + 1
        )

    def record_connection_closed(self, channel: str, user_id: str = "", duration_seconds: float = 0):
        """记录连接关闭"""
        self.websocket_connections_total.labels(status='closed', channel=channel).inc()
        current_value = self.websocket_connections_active.labels(channel=channel, user_id=user_id)._value.get()
        if current_value > 0:
            self.websocket_connections_active.labels(channel=channel, user_id=user_id).set(current_value - 1)

        if duration_seconds > 0:
            self.websocket_connection_duration_seconds.observe(duration_seconds)

    def record_message_sent(self, message_type: str, channel: str, size_bytes: int = 0, duration_seconds: float = 0):
        """记录发送的消息"""
        self.websocket_messages_total.labels(
            message_type=message_type,
            direction='sent',
            channel=channel
        ).inc()

        if size_bytes > 0:
            self.websocket_message_size_bytes.observe(size_bytes)

        if duration_seconds > 0:
            self.websocket_message_duration_seconds.observe(duration_seconds)

    def record_message_received(self, message_type: str, channel: str, size_bytes: int = 0, duration_seconds: float = 0):
        """记录接收的消息"""
        self.websocket_messages_total.labels(
            message_type=message_type,
            direction='received',
            channel=channel
        ).inc()

        if size_bytes > 0:
            self.websocket_message_size_bytes.observe(size_bytes)

        if duration_seconds > 0:
            self.websocket_message_duration_seconds.observe(duration_seconds)

    def record_error(self, error_type: str, channel: str = "unknown"):
        """记录错误"""
        self.websocket_errors_total.labels(error_type=error_type, channel=channel).inc()

    def record_reconnection(self, user_id: str, channel: str):
        """记录重连"""
        self.websocket_reconnects_total.labels(user_id=user_id, channel=channel).inc()

    def update_memory_usage(self, bytes_used: int):
        """更新内存使用量"""
        self.websocket_memory_usage_bytes.set(bytes_used)

    def update_cpu_usage(self, percent: float):
        """更新CPU使用率"""
        self.websocket_cpu_usage_percent.set(percent)

    def record_broadcast_duration(self, duration_seconds: float):
        """记录广播处理时间"""
        self.websocket_broadcast_duration_seconds.observe(duration_seconds)

    def update_active_subscriptions(self, subscription_type: str, count: int):
        """更新活跃订阅数"""
        self.websocket_subscriptions_active.labels(subscription_type=subscription_type).set(count)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        try:
            # 这里需要从各个指标获取当前值
            # 由于prometheus_client的限制，我们只能通过内部方式获取
            summary = {
                "timestamp": datetime.now().isoformat(),
                "active_connections": self._get_gauge_value(self.websocket_connections_active),
                "total_messages_sent": self._get_counter_value(self.websocket_messages_total, direction='sent'),
                "total_messages_received": self._get_counter_value(self.websocket_messages_total, direction='received'),
                "total_errors": self._get_counter_value(self.websocket_errors_total),
                "memory_usage_bytes": self._get_gauge_value(self.websocket_memory_usage_bytes),
                "cpu_usage_percent": self._get_gauge_value(self.websocket_cpu_usage_percent),
                "active_subscriptions": self._get_gauge_value(self.websocket_subscriptions_active)
            }

            return summary
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def _get_gauge_value(self, gauge) -> float:
        """获取Gauge当前值（简化实现）"""
        try:
            # 这里需要实际获取gauge值的逻辑
            # 由于prometheus_client的限制，这是一个简化实现
            return 0.0
        except:
            return 0.0

    def _get_counter_value(self, counter, **labels) -> float:
        """获取Counter当前值（简化实现）"""
        try:
            # 这里需要实际获取counter值的逻辑
            # 由于prometheus_client的限制，这是一个简化实现
            return 0.0
        except:
            return 0.0

    def generate_metrics_response(self) -> str:
        """生成Prometheus格式的指标响应"""
        try:
            return generate_latest(self.registry).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to generate metrics: {e}")
            return ""

# 全局指标实例
websocket_metrics = WebSocketMetrics()

class WebSocketMetricsCollector:
    """WebSocket指标收集器 - 定期收集指标"""

    def __init__(self, websocket_pool, collection_interval: int = 30):
        """
        初始化指标收集器

        Args:
            websocket_pool: WebSocket连接池实例
            collection_interval: 收集间隔（秒）
        """
        self.websocket_pool = websocket_pool
        self.collection_interval = collection_interval
        self.running = False
        self.collection_task = None

    async def start_collection(self):
        """开始指标收集"""
        if self.running:
            logger.warning("Metrics collection already running")
            return

        self.running = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info(f"WebSocket metrics collection started (interval: {self.collection_interval}s)")

    async def stop_collection(self):
        """停止指标收集"""
        self.running = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass

        logger.info("WebSocket metrics collection stopped")

    async def _collection_loop(self):
        """指标收集循环"""
        import psutil

        process = psutil.Process()

        while self.running:
            try:
                # 收集连接池统计信息
                pool_stats = self.websocket_pool.get_pool_stats()

                # 更新连接数指标
                active_connections = pool_stats.get("active_connections", 0)
                websocket_metrics.websocket_connections_active.set(active_connections)

                # 更新订阅数指标
                channels = pool_stats.get("channels", {})
                for channel, count in channels.items():
                    websocket_metrics.update_active_subscriptions(channel, count)

                # 更新系统资源指标
                memory_info = process.memory_info()
                websocket_metrics.update_memory_usage(memory_info.rss)

                cpu_percent = process.cpu_percent()
                websocket_metrics.update_cpu_usage(cpu_percent)

                logger.debug(f"Metrics collected: {active_connections} connections, {memory_info.rss/1024/1024:.1f}MB memory")

            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")

            await asyncio.sleep(self.collection_interval)

# 便捷函数
def get_websocket_metrics() -> WebSocketMetrics:
    """获取WebSocket指标实例"""
    return websocket_metrics

def record_websocket_connection_opened(channel: str, user_id: str = ""):
    """记录WebSocket连接打开（便捷函数）"""
    websocket_metrics.record_connection_opened(channel, user_id)

def record_websocket_connection_closed(channel: str, user_id: str = "", duration_seconds: float = 0):
    """记录WebSocket连接关闭（便捷函数）"""
    websocket_metrics.record_connection_closed(channel, user_id, duration_seconds)

def record_websocket_message_sent(message_type: str, channel: str, size_bytes: int = 0, duration_seconds: float = 0):
    """记录WebSocket消息发送（便捷函数）"""
    websocket_metrics.record_message_sent(message_type, channel, size_bytes, duration_seconds)

def record_websocket_message_received(message_type: str, channel: str, size_bytes: int = 0, duration_seconds: float = 0):
    """记录WebSocket消息接收（便捷函数）"""
    websocket_metrics.record_message_received(message_type, channel, size_bytes, duration_seconds)

def record_websocket_error(error_type: str, channel: str = "unknown"):
    """记录WebSocket错误（便捷函数）"""
    websocket_metrics.record_error(error_type, channel)