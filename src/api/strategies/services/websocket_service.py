"""
WebSocket服务
WebSocket Service

职责：
- WebSocket连接管理
- 消息路由和分发
- 实时数据推送
- 连接状态维护
"""

from typing import Dict, List, Optional, Set, Any
import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
import uuid

from fastapi import WebSocket
from ..models import User

logger = logging.getLogger(__name__)


class ConnectionType(str, Enum):
    """连接类型"""
    REALTIME = "realtime"
    STRATEGY = "strategy"
    MARKET = "market"
    NOTIFICATIONS = "notifications"


class ConnectionStatus(str, Enum):
    """连接状态"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class WebSocketConnection:
    """WebSocket连接封装"""

    def __init__(
        self,
        websocket: WebSocket,
        user_id: int,
        connection_type: ConnectionType,
        connection_id: Optional[str] = None,
        strategy_id: Optional[str] = None
    ):
        self.websocket = websocket
        self.user_id = user_id
        self.connection_type = connection_type
        self.connection_id = connection_id or str(uuid.uuid4())
        self.strategy_id = strategy_id
        self.status = ConnectionStatus.CONNECTING
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.subscriptions: Set[str] = set()

    async def send_message(self, message: dict) -> bool:
        """
        发送消息
        """
        try:
            await self.websocket.send_text(json.dumps(message, default=str))
            self.last_activity = datetime.now()
            return True
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")
            self.status = ConnectionStatus.ERROR
            return False

    async def close(self, code: int = 1000, reason: str = ""):
        """
        关闭连接
        """
        try:
            self.status = ConnectionStatus.DISCONNECTED
            await self.websocket.close(code=code, reason=reason)
        except Exception as e:
            logger.error(f"关闭WebSocket连接失败: {e}")


class WebSocketManager:
    """WebSocket管理器"""

    def __init__(self):
        """
        初始化WebSocket管理器
        """
        # 所有活动连接
        self.connections: Dict[str, WebSocketConnection] = {}

        # 用户到连接的映射
        self.user_connections: Dict[int, Set[str]] = {}

        # 策略订阅映射
        self.strategy_subscribers: Dict[str, Set[str]] = {}

        # 频道订阅映射
        self.channel_subscribers: Dict[str, Set[str]] = {}

        # 消息统计
        self.message_stats = {
            "total_sent": 0,
            "total_failed": 0,
            "by_type": {}
        }

    async def add_connection(
        self,
        websocket: WebSocket,
        user_id: int,
        connection_type: ConnectionType,
        strategy_id: Optional[str] = None
    ) -> str:
        """
        添加连接
        """
        connection = WebSocketConnection(
            websocket=websocket,
            user_id=user_id,
            connection_type=connection_type,
            strategy_id=strategy_id
        )

        # 添加到连接池
        self.connections[connection.connection_id] = connection

        # 添加到用户连接映射
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection.connection_id)

        # 添加到策略订阅（如果是策略连接）
        if strategy_id:
            if strategy_id not in self.strategy_subscribers:
                self.strategy_subscribers[strategy_id] = set()
            self.strategy_subscribers[strategy_id].add(connection.connection_id)
            connection.subscriptions.add(f"strategy:{strategy_id}")

        # 添加到频道订阅
        channel_name = connection_type.value
        if channel_name not in self.channel_subscribers:
            self.channel_subscribers[channel_name] = set()
        self.channel_subscribers[channel_name].add(connection.connection_id)
        connection.subscriptions.add(f"channel:{channel_name}")

        # 更新连接状态
        connection.status = ConnectionStatus.CONNECTED

        logger.info(f"添加WebSocket连接: {connection.connection_id}, 用户: {user_id}, 类型: {connection_type}")

        return connection.connection_id

    async def remove_connection(self, connection_id: str) -> bool:
        """
        移除连接
        """
        connection = self.connections.get(connection_id)
        if not connection:
            return False

        # 从用户连接映射中移除
        if connection.user_id in self.user_connections:
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]

        # 从策略订阅中移除
        if connection.strategy_id:
            if connection.strategy_id in self.strategy_subscribers:
                self.strategy_subscribers[connection.strategy_id].discard(connection_id)

        # 从频道订阅中移除
        for subscription in connection.subscriptions:
            if subscription.startswith("channel:"):
                channel = subscription.split(":", 1)[1]
                if channel in self.channel_subscribers:
                    self.channel_subscribers[channel].discard(connection_id)

        # 从连接池中移除
        del self.connections[connection_id]

        logger.info(f"移除WebSocket连接: {connection_id}")
        return True

    async def send_to_user(self, user_id: int, message: dict) -> bool:
        """
        发送消息给指定用户的所有连接
        """
        if user_id not in self.user_connections:
            return False

        sent = False
        failed_connections = []

        for connection_id in self.user_connections[user_id].copy():
            connection = self.connections.get(connection_id)
            if connection:
                if await connection.send_message(message):
                    sent = True
                else:
                    failed_connections.append(connection_id)

        # 清理失败的连接
        for failed_id in failed_connections:
            await self.remove_connection(failed_id)

        return sent

    async def broadcast_to_all(self, message: dict) -> int:
        """
        广播消息给所有连接
        """
        sent_count = 0
        failed_connections = []

        for connection_id, connection in self.connections.items():
            if await connection.send_message(message):
                sent_count += 1
            else:
                failed_connections.append(connection_id)

        # 清理失败的连接
        for failed_id in failed_connections:
            await self.remove_connection(failed_id)

        # 更新统计
        self._update_message_stats("broadcast", sent_count, len(failed_connections))

        return sent_count

    async def broadcast_to_users(
        self,
        user_ids: List[int],
        message: dict
    ) -> int:
        """
        广播消息给指定用户列表
        """
        sent_count = 0
        failed_users = []

        for user_id in user_ids:
            if await self.send_to_user(user_id, message):
                sent_count += 1
            else:
                failed_users.append(user_id)

        return sent_count

    async def broadcast_to_channel(self, channel: str, message: dict) -> int:
        """
        广播消息给指定频道的所有订阅者
        """
        if channel not in self.channel_subscribers:
            return 0

        sent_count = 0
        failed_connections = []

        for connection_id in self.channel_subscribers[channel].copy():
            connection = self.connections.get(connection_id)
            if connection and await connection.send_message(message):
                sent_count += 1
            else:
                failed_connections.append(connection_id)

        # 清理失败的连接
        for failed_id in failed_connections:
            await self.remove_connection(failed_id)

        return sent_count

    async def notify_strategy_subscribers(
        self,
        strategy_id: str,
        message: dict
    ) -> int:
        """
        通知策略订阅者
        """
        if strategy_id not in self.strategy_subscribers:
            return 0

        sent_count = 0
        failed_connections = []

        for connection_id in self.strategy_subscribers[strategy_id].copy():
            connection = self.connections.get(connection_id)
            if connection and await connection.send_message(message):
                sent_count += 1
            else:
                failed_connections.append(connection_id)

        # 清理失败的连接
        for failed_id in failed_connections:
            await self.remove_connection(failed_id)

        return sent_count

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        获取连接统计信息
        """
        stats = {
            "total_connections": len(self.connections),
            "connections_by_type": {},
            "connections_by_status": {},
            "unique_users": len(self.user_connections),
            "strategy_subscriptions": len(self.strategy_subscribers),
            "channel_subscriptions": {
                channel: len(subscribers)
                for channel, subscribers in self.channel_subscribers.items()
            }
        }

        # 按类型统计
        for connection in self.connections.values():
            type_name = connection.connection_type.value
            stats["connections_by_type"][type_name] = stats["connections_by_type"].get(type_name, 0) + 1

        # 按状态统计
        for connection in self.connections.values():
            status_name = connection.status.value
            stats["connections_by_status"][status_name] = stats["connections_by_status"].get(status_name, 0) + 1

        return stats

    def get_analytics(self) -> Dict[str, Any]:
        """
        获取分析数据
        """
        return {
            "message_stats": self.message_stats.copy(),
            "peak_connections": max(len(self.connections), 1),  # 简化实现
            "average_session_duration": 300,  # 简化实现（秒）
            "most_active_hour": 14,  # 简化实现
            "top_channels": sorted(
                [(channel, len(subscribers)) for channel, subscribers in self.channel_subscribers.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }

    def get_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有连接信息
        """
        connections_info = {}
        for conn_id, connection in self.connections.items():
            connections_info[conn_id] = {
                "user_id": connection.user_id,
                "channel": connection.connection_type.value,
                "strategy_id": connection.strategy_id,
                "status": connection.status.value,
                "connected_at": connection.connected_at.isoformat(),
                "last_activity": connection.last_activity.isoformat(),
                "subscriptions": list(connection.subscriptions)
            }

        return connections_info

    def _update_message_stats(self, message_type: str, sent: int, failed: int):
        """
        更新消息统计
        """
        self.message_stats["total_sent"] += sent
        self.message_stats["total_failed"] += failed

        if message_type not in self.message_stats["by_type"]:
            self.message_stats["by_type"][message_type] = {"sent": 0, "failed": 0}

        self.message_stats["by_type"][message_type]["sent"] += sent
        self.message_stats["by_type"][message_type]["failed"] += failed

    async def cleanup_inactive_connections(self, timeout_minutes: int = 30):
        """
        清理非活动连接
        """
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        inactive_connections = []

        for connection_id, connection in self.connections.items():
            if connection.last_activity < cutoff_time:
                inactive_connections.append(connection_id)

        for connection_id in inactive_connections:
            await self.remove_connection(connection_id)

        if inactive_connections:
            logger.info(f"清理非活动连接: {len(inactive_connections)} 个")


class WebSocketService:
    """WebSocket服务"""

    def __init__(self):
        """
        初始化WebSocket服务
        """
        self.manager = WebSocketManager()
        self._cleanup_task_started = False

    def _ensure_cleanup_task(self):
        """确保清理任务已启动"""
        if not self._cleanup_task_started:
            try:
                # 尝试创建清理任务
                asyncio.create_task(self._cleanup_task())
                self._cleanup_task_started = True
            except RuntimeError:
                # 没有运行的事件循环，延迟初始化
                pass

    async def handle_connection(
        self,
        websocket: WebSocket,
        user_id: int,
        connection_type: str,
        strategy_id: Optional[str] = None
    ):
        """
        处理WebSocket连接
        """
        try:
            # 接受WebSocket连接
            await websocket.accept()

            # 转换连接类型
            conn_type = ConnectionType(connection_type)

            # 添加连接到管理器
            connection_id = await self.manager.add_connection(
                websocket,
                user_id,
                conn_type,
                strategy_id
            )

            # 发送欢迎消息
            welcome_message = {
                "type": "connection_established",
                "connection_id": connection_id,
                "channel": connection_type,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(welcome_message, default=str))

            # 监听消息
            await self._listen_for_messages(connection_id)

        except Exception as e:
            logger.error(f"处理WebSocket连接失败: {e}")

    async def check_strategy_permission(self, user: User, strategy_id: str) -> bool:
        """
        检查用户是否有权限访问策略
        """
        # 简化实现，实际应该查询数据库
        return True

    async def _listen_for_messages(self, connection_id: str):
        """
        监听客户端消息
        """
        connection = self.manager.connections.get(connection_id)
        if not connection:
            return

        try:
            while True:
                # 接收消息
                data = await connection.websocket.receive_text()

                try:
                    message = json.loads(data)
                    await self._handle_client_message(connection_id, message)
                except json.JSONDecodeError:
                    # 发送错误响应
                    error_message = {
                        "type": "error",
                        "message": "无效的JSON格式",
                        "timestamp": datetime.now().isoformat()
                    }
                    await connection.send_message(error_message)

        except Exception as e:
            if not isinstance(e, Exception):  # WebSocketDisconnect的特殊处理
                logger.error(f"监听WebSocket消息失败: {e}")
        finally:
            # 连接断开时清理
            await self.manager.remove_connection(connection_id)

    async def _handle_client_message(self, connection_id: str, message: dict):
        """
        处理客户端消息
        """
        connection = self.manager.connections.get(connection_id)
        if not connection:
            return

        message_type = message.get("type", "")

        if message_type == "ping":
            # 处理心跳
            pong_message = {
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }
            await connection.send_message(pong_message)

        elif message_type == "subscribe":
            # 处理订阅请求
            await self._handle_subscription(connection, message)

        elif message_type == "unsubscribe":
            # 处理取消订阅请求
            await self._handle_unsubscription(connection, message)

        else:
            # 未知消息类型
            error_message = {
                "type": "error",
                "message": f"未知的消息类型: {message_type}",
                "timestamp": datetime.now().isoformat()
            }
            await connection.send_message(error_message)

    async def _handle_subscription(self, connection: WebSocketConnection, message: dict):
        """
        处理订阅请求
        """
        target = message.get("target")
        if not target:
            return

        # 添加到订阅
        connection.subscriptions.add(target)

        # 发送确认
        confirm_message = {
            "type": "subscription_confirmed",
            "target": target,
            "timestamp": datetime.now().isoformat()
        }
        await connection.send_message(confirm_message)

    async def _handle_unsubscription(self, connection: WebSocketConnection, message: dict):
        """
        处理取消订阅请求
        """
        target = message.get("target")
        if not target:
            return

        # 从订阅中移除
        connection.subscriptions.discard(target)

        # 发送确认
        confirm_message = {
            "type": "unsubscription_confirmed",
            "target": target,
            "timestamp": datetime.now().isoformat()
        }
        await connection.send_message(confirm_message)

    async def _cleanup_task(self):
        """
        定期清理任务
        """
        while True:
            try:
                await asyncio.sleep(300)  # 5分钟
                await self.manager.cleanup_inactive_connections()
            except Exception as e:
                logger.error(f"清理任务失败: {e}")


# 全局WebSocket管理器实例
websocket_manager = WebSocketManager()

# 全局WebSocket服务实例（延迟初始化）
websocket_service = None

def get_websocket_service():
    """获取WebSocket服务实例（延迟初始化）"""
    global websocket_service
    if websocket_service is None:
        websocket_service = WebSocketService()
        websocket_service._ensure_cleanup_task()
    return websocket_service