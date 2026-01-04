#!/usr/bin/env python3
"""
Task 9.2: Real-time Data Push - Subscription Manager Module
實時數據推送 - 客戶端訂閱管理模塊
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import redis.asyncio as redis
import hashlib

from .unified_websocket_manager import (
    UnifiedWebSocketManager,
    StreamType,
    MessageType
)

logger = logging.getLogger(__name__)

class SubscriptionStatus(str, Enum):
    """訂閱狀態"""
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    ERROR = "error"

class SubscriptionType(str, Enum):
    """訂閱類型"""
    MARKET_DATA = "market_data"
    STRATEGY_UPDATES = "strategy_updates"
    RISK_ALERTS = "risk_alerts"
    PERFORMANCE_METRICS = "performance_metrics"
    PORTFOLIO_UPDATES = "portfolio_updates"
    SYSTEM_NOTIFICATIONS = "system_notifications"

@dataclass
class SubscriptionFilter:
    """訂閱過濾器"""
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, nin, contains, regex
    value: Any

    def apply(self, data: Dict[str, Any]) -> bool:
        """應用過濾器"""
        field_value = data.get(self.field)

        if field_value is None:
            return False

        if self.operator == "eq":
            return field_value == self.value
        elif self.operator == "ne":
            return field_value != self.value
        elif self.operator == "gt":
            return field_value > self.value
        elif self.operator == "lt":
            return field_value < self.value
        elif self.operator == "gte":
            return field_value >= self.value
        elif self.operator == "lte":
            return field_value <= self.value
        elif self.operator == "in":
            return field_value in self.value
        elif self.operator == "nin":
            return field_value not in self.value
        elif self.operator == "contains":
            return str(self.value).lower() in str(field_value).lower()
        elif self.operator == "regex":
            import re
            return bool(re.search(str(self.value), str(field_value)))

        return False

@dataclass
class Subscription:
    """訂閱配置"""
    id: str
    user_id: str
    connection_id: str
    subscription_type: SubscriptionType
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    filters: List[SubscriptionFilter] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_count: int = 0
    error_count: int = 0
    rate_limit: Optional[float] = None  # 每秒最大消息數
    last_message_time: float = field(default_factory=lambda: datetime.now().timestamp())

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "connection_id": self.connection_id,
            "subscription_type": self.subscription_type.value,
            "status": self.status.value,
            "filters": [asdict(f) for f in self.filters],
            "parameters": self.parameters,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_activity": self.last_activity.isoformat(),
            "message_count": self.message_count,
            "error_count": self.error_count,
            "rate_limit": self.rate_limit
        }

    def should_send_message(self) -> bool:
        """檢查是否應該發送消息（基於速率限制）"""
        if not self.rate_limit:
            return True

        current_time = datetime.now().timestamp()
        time_diff = current_time - self.last_message_time

        if time_diff < 1.0 / self.rate_limit:
            return False

        self.last_message_time = current_time
        return True

    def apply_filters(self, data: Dict[str, Any]) -> bool:
        """應用所有過濾器"""
        for filter_obj in self.filters:
            if not filter_obj.apply(data):
                return False
        return True

@dataclass
class ConnectionInfo:
    """連接信息"""
    connection_id: str
    user_id: str
    websocket: Any
    subscriptions: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class SubscriptionManager:
    """訂閱管理器"""

    def __init__(self,
                 ws_manager: UnifiedWebSocketManager,
                 redis_client: Optional[redis.Redis] = None,
                 config: Dict[str, Any] = None):
        """
        初始化訂閱管理器

        Args:
            ws_manager: WebSocket管理器
            redis_client: Redis客戶端
            config: 配置信息
        """
        self.ws_manager = ws_manager
        self.redis_client = redis_client
        self.config = config or {}

        # 訂閱存儲
        self.subscriptions: Dict[str, Subscription] = {}
        self.connection_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self.user_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self.type_subscriptions: Dict[SubscriptionType, Set[str]] = defaultdict(set)

        # 連接管理
        self.connections: Dict[str, ConnectionInfo] = {}

        # 統計信息
        self.stats = {
            "total_subscriptions": 0,
            "active_subscriptions": 0,
            "connections_count": 0,
            "messages_filtered": 0,
            "messages_sent": 0,
            "errors_count": 0,
            "last_reset": datetime.now(timezone.utc)
        }

        # 速率限制跟蹤
        self.rate_limits: Dict[str, Tuple[float, int]] = defaultdict(lambda: (0, 0))

        # 啟動後台任務
        self._background_tasks: Set[asyncio.Task] = set()
        self._start_background_tasks()

    def _start_background_tasks(self):
        """啟動後台任務"""
        # 清理任務
        task = asyncio.create_task(self._cleanup_task())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        # 統計更新任務
        task = asyncio.create_task(self._stats_update_task())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        # 連接健康檢查
        task = asyncio.create_task(self._connection_health_check())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def register_connection(self,
                                connection_id: str,
                                user_id: str,
                                websocket: Any,
                                ip_address: Optional[str] = None,
                                user_agent: Optional[str] = None) -> bool:
        """
        註冊新連接

        Args:
            connection_id: 連接ID
            user_id: 用戶ID
            websocket: WebSocket對象
            ip_address: IP地址
            user_agent: 用戶代理

        Returns:
            bool: 註冊是否成功
        """
        try:
            # 檢查用戶連接數限制
            max_connections = self.config.get("max_connections_per_user", 10)
            user_connections = sum(1 for c in self.connections.values() if c.user_id == user_id)

            if user_connections >= max_connections:
                logger.warning(f"User {user_id} exceeded max connections limit")
                return False

            # 創建連接信息
            connection_info = ConnectionInfo(
                connection_id=connection_id,
                user_id=user_id,
                websocket=websocket,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # 註冊連接
            self.connections[connection_id] = connection_info
            self.stats["connections_count"] = len(self.connections)

            logger.info(f"Registered connection: {connection_id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error registering connection: {e}")
            return False

    async def unregister_connection(self, connection_id: str):
        """
        註銷連接

        Args:
            connection_id: 連接ID
        """
        try:
            connection_info = self.connections.get(connection_id)
            if not connection_info:
                return

            # 移除所有訂閱
            subscriptions_to_remove = list(self.connection_subscriptions[connection_id])
            for subscription_id in subscriptions_to_remove:
                await self.unsubscribe(subscription_id)

            # 清理連接信息
            del self.connections[connection_id]
            del self.connection_subscriptions[connection_id]
            self.stats["connections_count"] = len(self.connections)

            logger.info(f"Unregistered connection: {connection_id}")

        except Exception as e:
            logger.error(f"Error unregistering connection: {e}")

    async def create_subscription(self,
                                user_id: str,
                                connection_id: str,
                                subscription_type: SubscriptionType,
                                filters: Optional[List[SubscriptionFilter]] = None,
                                parameters: Optional[Dict[str, Any]] = None,
                                expires_at: Optional[datetime] = None,
                                rate_limit: Optional[float] = None) -> Optional[str]:
        """
        創建新訂閱

        Args:
            user_id: 用戶ID
            connection_id: 連接ID
            subscription_type: 訂閱類型
            filters: 過濾器列表
            parameters: 參數
            expires_at: 過期時間
            rate_limit: 速率限制

        Returns:
            str: 訂閱ID，失敗返回None
        """
        try:
            # 檢查連接是否存在
            if connection_id not in self.connections:
                logger.error(f"Connection {connection_id} not found")
                return None

            # 檢查用戶訂閱數限制
            max_subscriptions = self.config.get("max_subscriptions_per_user", 50)
            if len(self.user_subscriptions[user_id]) >= max_subscriptions:
                logger.warning(f"User {user_id} exceeded max subscriptions limit")
                return None

            # 生成訂閱ID
            subscription_id = self._generate_subscription_id(user_id, subscription_type)

            # 創建訂閱對象
            subscription = Subscription(
                id=subscription_id,
                user_id=user_id,
                connection_id=connection_id,
                subscription_type=subscription_type,
                filters=filters or [],
                parameters=parameters or {},
                expires_at=expires_at,
                rate_limit=rate_limit
            )

            # 存儲訂閱
            self.subscriptions[subscription_id] = subscription
            self.connection_subscriptions[connection_id].add(subscription_id)
            self.user_subscriptions[user_id].add(subscription_id)
            self.type_subscriptions[subscription_type].add(subscription_id)

            # 更新統計
            self.stats["total_subscriptions"] = len(self.subscriptions)
            self.stats["active_subscriptions"] = sum(1 for s in self.subscriptions.values()
                                                   if s.status == SubscriptionStatus.ACTIVE)

            # 發送訂閱確認
            await self._send_subscription_confirmation(connection_id, subscription, True)

            logger.info(f"Created subscription: {subscription_id} for user {user_id}")
            return subscription_id

        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            return None

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        取消訂閱

        Args:
            subscription_id: 訂閱ID

        Returns:
            bool: 取消是否成功
        """
        try:
            subscription = self.subscriptions.get(subscription_id)
            if not subscription:
                return False

            # 更新狀態
            subscription.status = SubscriptionStatus.EXPIRED
            subscription.updated_at = datetime.now(timezone.utc)

            # 從索引中移除
            self.connection_subscriptions[subscription.connection_id].discard(subscription_id)
            self.user_subscriptions[subscription.user_id].discard(subscription_id)
            self.type_subscriptions[subscription.subscription_type].discard(subscription_id)

            # 發送取消訂閱確認
            await self._send_subscription_confirmation(subscription.connection_id, subscription, False)

            # 延遲刪除（保留一段時間用於統計）
            asyncio.create_task(self._delayed_remove_subscription(subscription_id))

            # 更新統計
            self.stats["active_subscriptions"] = sum(1 for s in self.subscriptions.values()
                                                   if s.status == SubscriptionStatus.ACTIVE)

            logger.info(f"Unsubscribed: {subscription_id}")
            return True

        except Exception as e:
            logger.error(f"Error unsubscribing: {e}")
            return False

    async def pause_subscription(self, subscription_id: str) -> bool:
        """暫停訂閱"""
        subscription = self.subscriptions.get(subscription_id)
        if subscription:
            subscription.status = SubscriptionStatus.PAUSED
            subscription.updated_at = datetime.now(timezone.utc)
            return True
        return False

    async def resume_subscription(self, subscription_id: str) -> bool:
        """恢復訂閱"""
        subscription = self.subscriptions.get(subscription_id)
        if subscription:
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.updated_at = datetime.now(timezone.utc)
            return True
        return False

    async def update_subscription(self,
                                subscription_id: str,
                                filters: Optional[List[SubscriptionFilter]] = None,
                                parameters: Optional[Dict[str, Any]] = None,
                                rate_limit: Optional[float] = None) -> bool:
        """
        更新訂閱配置

        Args:
            subscription_id: 訂閱ID
            filters: 新的過濾器
            parameters: 新的參數
            rate_limit: 新的速率限制

        Returns:
            bool: 更新是否成功
        """
        try:
            subscription = self.subscriptions.get(subscription_id)
            if not subscription:
                return False

            # 更新配置
            if filters is not None:
                subscription.filters = filters
            if parameters is not None:
                subscription.parameters = parameters
            if rate_limit is not None:
                subscription.rate_limit = rate_limit

            subscription.updated_at = datetime.now(timezone.utc)

            logger.info(f"Updated subscription: {subscription_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            return False

    async def broadcast_message(self,
                              subscription_type: SubscriptionType,
                              data: Dict[str, Any],
                              target_users: Optional[List[str]] = None) -> Dict[str, int]:
        """
        廣播消息到訂閱者

        Args:
            subscription_type: 訂閱類型
            data: 消息數據
            target_users: 目標用戶列表（None表示所有訂閱者）

        Returns:
            Dict[str, int]: 每個連接的發送消息數
        """
        results = defaultdict(int)

        try:
            # 獲取相關訂閱
            relevant_subscriptions = self.type_subscriptions.get(subscription_type, set())

            for subscription_id in relevant_subscriptions:
                subscription = self.subscriptions.get(subscription_id)

                if not subscription or subscription.status != SubscriptionStatus.ACTIVE:
                    continue

                # 檢查目標用戶
                if target_users and subscription.user_id not in target_users:
                    continue

                # 檢查過期時間
                if subscription.expires_at and subscription.expires_at < datetime.now(timezone.utc):
                    await self.unsubscribe(subscription_id)
                    continue

                # 應用過濾器
                if not subscription.apply_filters(data):
                    self.stats["messages_filtered"] += 1
                    continue

                # 檢查速率限制
                if not subscription.should_send_message():
                    continue

                # 發送消息
                connection_info = self.connections.get(subscription.connection_id)
                if connection_info:
                    message = {
                        "subscription_id": subscription_id,
                        "type": subscription_type.value,
                        "data": data,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }

                    try:
                        await connection_info.websocket.send_json(message)
                        subscription.message_count += 1
                        subscription.last_activity = datetime.now(timezone.utc)
                        results[subscription.connection_id] += 1
                        self.stats["messages_sent"] += 1

                    except Exception as e:
                        logger.error(f"Error sending message to {subscription.connection_id}: {e}")
                        subscription.error_count += 1
                        self.stats["errors_count"] += 1

        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
            self.stats["errors_count"] += 1

        return dict(results)

    async def get_user_subscriptions(self, user_id: str) -> List[Subscription]:
        """獲取用戶的所有訂閱"""
        subscription_ids = self.user_subscriptions.get(user_id, set())
        return [self.subscriptions[sid] for sid in subscription_ids if sid in self.subscriptions]

    async def get_connection_subscriptions(self, connection_id: str) -> List[Subscription]:
        """獲取連接的所有訂閱"""
        subscription_ids = self.connection_subscriptions.get(connection_id, set())
        return [self.subscriptions[sid] for sid in subscription_ids if sid in self.subscriptions]

    async def get_subscription_stats(self) -> Dict[str, Any]:
        """獲取訂閱統計信息"""
        type_stats = defaultdict(int)
        status_stats = defaultdict(int)

        for subscription in self.subscriptions.values():
            type_stats[subscription.subscription_type.value] += 1
            status_stats[subscription.status.value] += 1

        return {
            **self.stats,
            "subscriptions_by_type": dict(type_stats),
            "subscriptions_by_status": dict(status_stats),
            "average_subscriptions_per_user": sum(len(s) for s in self.user_subscriptions.values()) / max(len(self.user_subscriptions), 1),
            "average_subscriptions_per_connection": sum(len(s) for s in self.connection_subscriptions.values()) / max(len(self.connection_subscriptions), 1)
        }

    def _generate_subscription_id(self, user_id: str, subscription_type: SubscriptionType) -> str:
        """生成訂閱ID"""
        timestamp = datetime.now(timezone.utc).timestamp()
        unique_string = f"{user_id}:{subscription_type.value}:{timestamp}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    async def _send_subscription_confirmation(self,
                                            connection_id: str,
                                            subscription: Subscription,
                                            subscribed: bool):
        """發送訂閱確認消息"""
        try:
            connection_info = self.connections.get(connection_id)
            if not connection_info:
                return

            message = {
                "type": "subscription_confirmation",
                "subscribed": subscribed,
                "subscription": subscription.to_dict(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            await connection_info.websocket.send_json(message)

        except Exception as e:
            logger.error(f"Error sending subscription confirmation: {e}")

    async def _delayed_remove_subscription(self, subscription_id: str, delay: int = 300):
        """延遲刪除訂閱"""
        await asyncio.sleep(delay)
        self.subscriptions.pop(subscription_id, None)

    async def _cleanup_task(self):
        """清理任務"""
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                expired_subscriptions = []

                # 查找過期訂閱
                for subscription in self.subscriptions.values():
                    if (subscription.expires_at and
                        subscription.expires_at < current_time and
                        subscription.status != SubscriptionStatus.EXPIRED):
                        expired_subscriptions.append(subscription.id)

                # 清理過期訂閱
                for subscription_id in expired_subscriptions:
                    await self.unsubscribe(subscription_id)

                # 清理非活躍連接
                inactive_connections = []
                for connection_id, connection_info in self.connections.items():
                    if current_time - connection_info.last_activity > timedelta(minutes=30):
                        inactive_connections.append(connection_id)

                for connection_id in inactive_connections:
                    await self.unregister_connection(connection_id)

                await asyncio.sleep(300)  # 5分鐘清理一次

            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)

    async def _stats_update_task(self):
        """統計更新任務"""
        while True:
            try:
                # 更新統計信息
                self.stats["active_subscriptions"] = sum(1 for s in self.subscriptions.values()
                                                       if s.status == SubscriptionStatus.ACTIVE)

                # 如果有Redis，存儲統計信息
                if self.redis_client:
                    await self.redis_client.hset(
                        "subscription:stats",
                        mapping={
                            "total_subscriptions": str(self.stats["total_subscriptions"]),
                            "active_subscriptions": str(self.stats["active_subscriptions"]),
                            "connections_count": str(self.stats["connections_count"]),
                            "messages_sent": str(self.stats["messages_sent"]),
                            "messages_filtered": str(self.stats["messages_filtered"]),
                            "errors_count": str(self.stats["errors_count"]),
                            "last_update": datetime.now(timezone.utc).isoformat()
                        }
                    )

                await asyncio.sleep(60)  # 1分鐘更新一次

            except Exception as e:
                logger.error(f"Error in stats update task: {e}")
                await asyncio.sleep(60)

    async def _connection_health_check(self):
        """連接健康檢查"""
        while True:
            try:
                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                # 發送ping到所有連接
                for connection_id, connection_info in self.connections.items():
                    try:
                        await connection_info.websocket.send_json(ping_message)
                        connection_info.last_activity = datetime.now(timezone.utc)
                    except Exception as e:
                        logger.warning(f"Connection {connection_id} health check failed: {e}")
                        await self.unregister_connection(connection_id)

                await asyncio.sleep(30)  # 30秒檢查一次

            except Exception as e:
                logger.error(f"Error in connection health check: {e}")
                await asyncio.sleep(30)

# 創建全局訂閱管理器實例
subscription_manager: Optional[SubscriptionManager] = None

async def get_subscription_manager(ws_manager: UnifiedWebSocketManager,
                                 redis_client: Optional[redis.Redis] = None,
                                 config: Dict[str, Any] = None) -> SubscriptionManager:
    """獲取或創建訂閱管理器實例"""
    global subscription_manager

    if subscription_manager is None:
        subscription_manager = SubscriptionManager(ws_manager, redis_client, config)

    return subscription_manager