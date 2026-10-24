"""
WebSocket连接池实现
WebSocket Connection Pool Implementation

提供高性能的WebSocket连接管理，支持：
- 连接池管理和复用
- 连接数限制（5/用户，1000总计）
- 健康检查和自动故障恢复
- 心跳机制
- 订阅/取消订阅功能
- 消息广播和单播
- 实时监控和指标收集
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
import weakref
from collections import defaultdict, deque
import statistics

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ConnectionStatus(str, Enum):
    """连接状态枚举"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    IDLE = "idle"
    CLOSING = "closing"
    CLOSED = "closed"
    ERROR = "error"


class MessageType(str, Enum):
    """消息类型枚举"""
    HEARTBEAT = "heartbeat"
    DATA = "data"
    ERROR = "error"
    SUBSCRIPTION = "subscription"
    BROADCAST = "broadcast"
    UNICAST = "unicast"
    SYSTEM = "system"


@dataclass
class ConnectionMetrics:
    """连接指标"""
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    last_activity: datetime = field(default_factory=datetime.now)
    connection_duration: float = 0.0
    average_latency: float = 0.0
    latency_samples: deque = field(default_factory=lambda: deque(maxlen=100))
    error_count: int = 0


@dataclass
class ConnectionInfo:
    """连接信息"""
    connection_id: str
    websocket: WebSocket
    user_id: int
    client_ip: str
    user_agent: str = ""
    connected_at: datetime = field(default_factory=datetime.now)
    last_ping: datetime = field(default_factory=datetime.now)
    status: ConnectionStatus = ConnectionStatus.CONNECTING
    subscriptions: Set[str] = field(default_factory=set)
    metrics: ConnectionMetrics = field(default_factory=ConnectionMetrics)
    is_authenticated: bool = False
    strategy_ids: Set[str] = field(default_factory=set)
    channel: str = "default"


class ConnectionPoolConfig(BaseModel):
    """连接池配置"""
    # Connection limits
    max_connections_per_user: int = 5
    max_total_connections: int = 1000

    # timeouts
    connection_timeout: int = 30  # seconds
    heartbeat_interval: int = 30  # seconds
    idle_timeout: int = 300  # 5 minutes

    # health check
    health_check_interval: int = 60  # seconds
    max_failed_pings: int = 3

    # performance
    message_queue_size: int = 1000
    broadcast_batch_size: int = 100

    # monitoring
    metrics_retention_hours: int = 24

    class Config:
        extra = "allow"


class WebSocketConnectionPool:
    """
    WebSocket连接池管理器

    Features:
    - 连接池管理和复用
    - 连接数限制
    - 健康检查和自动恢复
    - 心跳机制
    - 消息路由和广播
    - 实时监控
    """

    def __init__(self, config: Optional[ConnectionPoolConfig] = None):
        self.config = config or ConnectionPoolConfig()

        # Connection storage
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[int, Set[str]] = defaultdict(set)
        self.strategy_connections: Dict[str, Set[str]] = defaultdict(set)
        self.channel_subscriptions: Dict[str, Set[str]] = defaultdict(set)

        # Connection management
        self.connection_lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None

        # Metrics and monitoring
        self.pool_metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "peak_connections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "connection_errors": 0,
            "start_time": datetime.now(),
            "last_cleanup": datetime.now(),
            "avg_connection_duration": 0.0,
            "message_latency_p95": 0.0,
            "throughput_per_second": 0.0
        }

        # Message queues for efficient broadcasting
        self.message_queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self.broadcast_tasks: List[asyncio.Task] = []

        # Event callbacks
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)

        # Start background tasks
        self._start_background_tasks()

        logger.info("WebSocket连接池初始化完成", extra={
            "config": self.config.dict()
        })

    async def add_connection(
        self,
        websocket: WebSocket,
        user_id: int,
        client_ip: str,
        user_agent: str = "",
        channel: str = "default",
        strategy_ids: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """
        添加新连接到池中

        Returns:
            Tuple[success, connection_id]
        """
        async with self.connection_lock:
            # Check connection limits
            if not await self._check_connection_limits(user_id):
                logger.warning(f"用户 {user_id} 连接数超限")
                return False, "Connection limit exceeded"

            # Generate connection ID
            connection_id = str(uuid.uuid4())

            # Create connection info
            connection_info = ConnectionInfo(
                connection_id=connection_id,
                websocket=websocket,
                user_id=user_id,
                client_ip=client_ip,
                user_agent=user_agent,
                channel=channel,
                strategy_ids=set(strategy_ids or [])
            )

            # Add to pools
            self.connections[connection_id] = connection_info
            self.user_connections[user_id].add(connection_id)

            # Add to strategy subscriptions
            for strategy_id in connection_info.strategy_ids:
                self.strategy_connections[strategy_id].add(connection_id)

            # Add to channel
            self.channel_subscriptions[channel].add(connection_id)

            # Update metrics
            self._update_pool_metrics("connection_added", user_id)

            # Set connection status
            connection_info.status = ConnectionStatus.CONNECTED

            logger.info(f"连接已添加: {connection_id}", extra={
                "user_id": user_id,
                "client_ip": client_ip,
                "total_connections": len(self.connections)
            })

            # Trigger event
            await self._trigger_event("connection_added", connection_info)

            return True, connection_id

    async def remove_connection(self, connection_id: str, reason: str = "disconnect") -> bool:
        """
        从池中移除连接
        """
        async with self.connection_lock:
            connection_info = self.connections.get(connection_id)
            if not connection_info:
                return False

            # Update status
            connection_info.status = ConnectionStatus.CLOSING

            # Remove from all pools
            self.user_connections[connection_info.user_id].discard(connection_id)
            if not self.user_connections[connection_info.user_id]:
                del self.user_connections[connection_info.user_id]

            # Remove from strategy connections
            for strategy_id in connection_info.strategy_ids:
                self.strategy_connections[strategy_id].discard(connection_id)
                if not self.strategy_connections[strategy_id]:
                    del self.strategy_connections[strategy_id]

            # Remove from channel subscriptions
            self.channel_subscriptions[connection_info.channel].discard(connection_id)
            if not self.channel_subscriptions[connection_info.channel]:
                del self.channel_subscriptions[connection_info.channel]

            # Close WebSocket if still open
            try:
                if connection_info.websocket.client_state.name == "CONNECTED":
                    await connection_info.websocket.close(code=1000, reason=reason)
            except Exception as e:
                logger.warning(f"关闭WebSocket连接失败: {e}")

            # Calculate final metrics
            connection_duration = (datetime.now() - connection_info.connected_at).total_seconds()
            connection_info.metrics.connection_duration = connection_duration

            # Remove from connection pool
            del self.connections[connection_id]

            # Update pool metrics
            self._update_pool_metrics("connection_removed", connection_info.user_id)

            logger.info(f"连接已移除: {connection_id}", extra={
                "reason": reason,
                "duration": connection_duration,
                "total_connections": len(self.connections)
            })

            # Trigger event
            await self._trigger_event("connection_removed", connection_info)

            return True

    async def send_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
        message_type: MessageType = MessageType.DATA
    ) -> bool:
        """
        发送消息到指定连接
        """
        connection_info = self.connections.get(connection_id)
        if not connection_info:
            return False

        try:
            # Prepare message
            message_data = {
                "id": str(uuid.uuid4()),
                "type": message_type.value,
                "timestamp": datetime.now().isoformat(),
                "data": message
            }

            # Send message
            message_json = json.dumps(message_data, default=str)
            await connection_info.websocket.send_text(message_json)

            # Update metrics
            connection_info.metrics.messages_sent += 1
            connection_info.metrics.bytes_sent += len(message_json)
            connection_info.metrics.last_activity = datetime.now()

            self.pool_metrics["total_messages_sent"] += 1

            # Calculate latency (simplified - in real implementation,
            # you'd track round-trip time)
            latency_sample = time.time()
            connection_info.metrics.latency_samples.append(latency_sample)

            return True

        except Exception as e:
            logger.error(f"发送消息失败: {e}", extra={
                "connection_id": connection_id,
                "message_type": message_type.value
            })

            # Update error count
            connection_info.metrics.error_count += 1
            self.pool_metrics["connection_errors"] += 1

            # Remove connection on error
            await self.remove_connection(connection_id, "send_error")
            return False

    async def send_to_user(
        self,
        user_id: int,
        message: Dict[str, Any],
        message_type: MessageType = MessageType.UNICAST
    ) -> int:
        """
        发送消息到用户的所有连接
        """
        if user_id not in self.user_connections:
            return 0

        sent_count = 0
        failed_connections = []

        for connection_id in self.user_connections[user_id].copy():
            if await self.send_message(connection_id, message, message_type):
                sent_count += 1
            else:
                failed_connections.append(connection_id)

        # Clean up failed connections
        for connection_id in failed_connections:
            await self.remove_connection(connection_id, "send_failure")

        return sent_count

    async def broadcast_to_channel(
        self,
        channel: str,
        message: Dict[str, Any],
        exclude_connections: Optional[Set[str]] = None
    ) -> int:
        """
        广播消息到频道
        """
        if channel not in self.channel_subscriptions:
            return 0

        exclude_connections = exclude_connections or set()
        sent_count = 0
        failed_connections = []

        # Get connections for this channel
        connections = list(self.channel_subscriptions[channel])

        # Batch processing for performance
        batch_size = self.config.broadcast_batch_size

        for i in range(0, len(connections), batch_size):
            batch = connections[i:i + batch_size]

            # Create tasks for concurrent sending
            tasks = []
            for connection_id in batch:
                if connection_id not in exclude_connections:
                    tasks.append(self.send_message(connection_id, message, MessageType.BROADCAST))

            # Execute batch
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for j, result in enumerate(results):
                    if result is True:
                        sent_count += 1
                    else:
                        failed_connections.append(batch[j])

        # Clean up failed connections
        for connection_id in failed_connections:
            await self.remove_connection(connection_id, "broadcast_failure")

        logger.debug(f"广播完成: 频道 {channel}, 发送 {sent_count}, 失败 {len(failed_connections)}")

        return sent_count

    async def broadcast_to_strategy_subscribers(
        self,
        strategy_id: str,
        message: Dict[str, Any]
    ) -> int:
        """
        广播消息到策略订阅者
        """
        if strategy_id not in self.strategy_connections:
            return 0

        sent_count = 0
        failed_connections = []

        for connection_id in self.strategy_connections[strategy_id].copy():
            if await self.send_message(connection_id, message, MessageType.DATA):
                sent_count += 1
            else:
                failed_connections.append(connection_id)

        # Clean up failed connections
        for connection_id in failed_connections:
            await self.remove_connection(connection_id, "strategy_broadcast_failure")

        return sent_count

    async def subscribe_to_channel(
        self,
        connection_id: str,
        channel: str
    ) -> bool:
        """
        订阅连接到频道
        """
        connection_info = self.connections.get(connection_id)
        if not connection_info:
            return False

        # Remove from current channel if different
        if connection_info.channel != channel:
            self.channel_subscriptions[connection_info.channel].discard(connection_id)
            if not self.channel_subscriptions[connection_info.channel]:
                del self.channel_subscriptions[connection_info.channel]

        # Add to new channel
        connection_info.channel = channel
        connection_info.subscriptions.add(channel)
        self.channel_subscriptions[channel].add(connection_id)

        logger.info(f"连接 {connection_id} 订阅频道 {channel}")

        return True

    async def unsubscribe_from_channel(
        self,
        connection_id: str,
        channel: str
    ) -> bool:
        """
        取消频道订阅
        """
        connection_info = self.connections.get(connection_id)
        if not connection_info:
            return False

        connection_info.subscriptions.discard(channel)
        self.channel_subscriptions[channel].discard(connection_id)

        # Clean up empty channel
        if not self.channel_subscriptions[channel]:
            del self.channel_subscriptions[channel]

        logger.info(f"连接 {connection_id} 取消订阅频道 {channel}")

        return True

    async def _check_connection_limits(self, user_id: int) -> bool:
        """
        检查连接限制
        """
        # Check per-user limit
        user_connection_count = len(self.user_connections.get(user_id, set()))
        if user_connection_count >= self.config.max_connections_per_user:
            return False

        # Check total limit
        if len(self.connections) >= self.config.max_total_connections:
            return False

        return True

    async def _heartbeat_task(self):
        """
        心跳任务 - 定期发送心跳消息
        """
        while True:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)

                current_time = datetime.now()
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": current_time.isoformat()
                }

                # Send heartbeat to all connected clients
                for connection_id, connection_info in list(self.connections.items()):
                    if connection_info.status == ConnectionStatus.CONNECTED:
                        # Check if connection is idle
                        idle_time = (current_time - connection_info.last_ping).total_seconds()
                        if idle_time > self.config.idle_timeout:
                            logger.info(f"连接 {connection_id} 超时，移除")
                            await self.remove_connection(connection_id, "idle_timeout")
                            continue

                        # Send heartbeat
                        await self.send_message(connection_id, heartbeat_message, MessageType.HEARTBEAT)

            except Exception as e:
                logger.error(f"心跳任务错误: {e}")
                await asyncio.sleep(5)

    async def _health_check_task(self):
        """
        健康检查任务 - 检查连接状态
        """
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)

                current_time = datetime.now()
                unhealthy_connections = []

                for connection_id, connection_info in list(self.connections.items()):
                    # Check connection health
                    time_since_last_activity = (
                        current_time - connection_info.metrics.last_activity
                    ).total_seconds()

                    # Mark as unhealthy if no activity for too long
                    if time_since_last_activity > self.config.idle_timeout * 2:
                        connection_info.status = ConnectionStatus.ERROR
                        unhealthy_connections.append(connection_id)

                # Remove unhealthy connections
                for connection_id in unhealthy_connections:
                    await self.remove_connection(connection_id, "health_check_failed")

                self.pool_metrics["last_cleanup"] = current_time

            except Exception as e:
                logger.error(f"健康检查任务错误: {e}")
                await asyncio.sleep(10)

    def _update_pool_metrics(self, event_type: str, user_id: int = 0):
        """
        更新连接池指标
        """
        total_connections = len(self.connections)
        self.pool_metrics["total_connections"] = total_connections
        self.pool_metrics["active_connections"] = sum(
            1 for conn in self.connections.values()
            if conn.status == ConnectionStatus.CONNECTED
        )

        if total_connections > self.pool_metrics["peak_connections"]:
            self.pool_metrics["peak_connections"] = total_connections

        # Calculate average connection duration
        if self.connections:
            durations = [
                (datetime.now() - conn.connected_at).total_seconds()
                for conn in self.connections.values()
            ]
            self.pool_metrics["avg_connection_duration"] = statistics.mean(durations)

    async def _trigger_event(self, event_name: str, connection_info: ConnectionInfo):
        """
        触发事件处理器
        """
        if event_name in self.event_handlers:
            for handler in self.event_handlers[event_name]:
                try:
                    await handler(connection_info)
                except Exception as e:
                    logger.error(f"事件处理器错误: {e}")

    def _start_background_tasks(self):
        """
        启动后台任务
        """
        self._heartbeat_task = asyncio.create_task(self._heartbeat_task())
        self._health_check_task = asyncio.create_task(self._health_check_task())

        logger.info("后台任务已启动")

    def add_event_handler(self, event_name: str, handler: Callable):
        """
        添加事件处理器
        """
        self.event_handlers[event_name].append(handler)

    def remove_event_handler(self, event_name: str, handler: Callable):
        """
        移除事件处理器
        """
        if event_name in self.event_handlers:
            self.event_handlers[event_name].remove(handler)

    def get_pool_stats(self) -> Dict[str, Any]:
        """
        获取连接池统计信息
        """
        # Calculate additional metrics
        latency_samples = []
        for conn in self.connections.values():
            latency_samples.extend(conn.metrics.latency_samples)

        if latency_samples:
            self.pool_metrics["message_latency_p95"] = statistics.quantiles(
                latency_samples, n=20
            )[18]  # 95th percentile

        # Calculate throughput
        uptime = (datetime.now() - self.pool_metrics["start_time"]).total_seconds()
        if uptime > 0:
            self.pool_metrics["throughput_per_second"] = (
                self.pool_metrics["total_messages_sent"] / uptime
            )

        return {
            **self.pool_metrics,
            "config": self.config.dict(),
            "connections_by_user": {
                user_id: len(connections)
                for user_id, connections in self.user_connections.items()
            },
            "channels": list(self.channel_subscriptions.keys()),
            "strategies": list(self.strategy_connections.keys()),
        }

    def get_connection_details(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        获取连接详细信息
        """
        connection_info = self.connections.get(connection_id)
        if not connection_info:
            return None

        return {
            "connection_id": connection_info.connection_id,
            "user_id": connection_info.user_id,
            "client_ip": connection_info.client_ip,
            "status": connection_info.status.value,
            "connected_at": connection_info.connected_at.isoformat(),
            "last_activity": connection_info.metrics.last_activity.isoformat(),
            "subscriptions": list(connection_info.subscriptions),
            "strategy_ids": list(connection_info.strategy_ids),
            "channel": connection_info.channel,
            "metrics": {
                "messages_sent": connection_info.metrics.messages_sent,
                "messages_received": connection_info.metrics.messages_received,
                "bytes_sent": connection_info.metrics.bytes_sent,
                "bytes_received": connection_info.metrics.bytes_received,
                "error_count": connection_info.metrics.error_count,
                "average_latency": statistics.mean(connection_info.metrics.latency_samples) if connection_info.metrics.latency_samples else 0.0,
            }
        }

    async def shutdown(self):
        """
        关闭连接池
        """
        logger.info("关闭WebSocket连接池...")

        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._health_check_task:
            self._health_check_task.cancel()

        # Close all connections
        connections_to_close = list(self.connections.keys())
        for connection_id in connections_to_close:
            await self.remove_connection(connection_id, "shutdown")

        logger.info("WebSocket连接池已关闭")


# Global connection pool instance
_connection_pool: Optional[WebSocketConnectionPool] = None


def get_connection_pool(config: Optional[ConnectionPoolConfig] = None) -> WebSocketConnectionPool:
    """
    获取全局连接池实例
    """
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = WebSocketConnectionPool(config)
    return _connection_pool


async def cleanup_connection_pool():
    """
    清理全局连接池
    """
    global _connection_pool
    if _connection_pool:
        await _connection_pool.shutdown()
        _connection_pool = None