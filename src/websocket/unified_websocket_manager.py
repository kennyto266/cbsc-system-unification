#!/usr/bin/env python3
"""
Phase 8.1 WebSocket實時推送系統 - 統一WebSocket服務管理器
Unified WebSocket Service Manager for Real-time Push System
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import (
    Dict, List, Set, Optional, Any, Union, Callable,
    Type, AsyncGenerator, Tuple
)
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from enum import Enum
import weakref
import zlib
import hashlib
import jwt
from functools import wraps
from contextlib import asynccontextmanager

from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis.asyncio as redis
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamType(str, Enum):
    """數據流類型枚舉"""
    STRATEGY_EXECUTION = "strategy_execution"
    RISK_MONITORING = "risk_monitoring"
    PERFORMANCE_METRICS = "performance_metrics"
    MARKET_DATA = "market_data"
    SYSTEM_NOTIFICATIONS = "system_notifications"
    USER_ALERTS = "user_alerts"
    PORTFOLIO_UPDATES = "portfolio_updates"

class MessageType(str, Enum):
    """消息類型枚舉"""
    REALTIME_UPDATE = "realtime_update"
    SNAPSHOT = "snapshot"
    ALERT = "alert"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    SUBSCRIPTION_CONFIRMED = "subscription_confirmed"
    UNSUBSCRIPTION_CONFIRMED = "unsubscription_confirmed"
    RATE_LIMIT_WARNING = "rate_limit_warning"

@dataclass
class StreamMessage:
    """數據流消息"""
    stream_type: StreamType
    message_type: MessageType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "stream_type": self.stream_type.value,
            "message_type": self.message_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

@dataclass
class ClientSubscription:
    """客戶端訂閱信息"""
    stream_types: Set[StreamType]
    filters: Dict[str, Any] = field(default_factory=dict)
    frequency_limit: Optional[float] = None  # 每秒最大消息數
    last_message_time: float = field(default_factory=time.time)
    message_count: int = 0

    def should_throttle(self, current_time: float) -> bool:
        """檢查是否需要限流"""
        if not self.frequency_limit:
            return False

        time_diff = current_time - self.last_message_time
        if time_diff < 1.0 / self.frequency_limit:
            return True

        self.last_message_time = current_time
        return False

@dataclass
class ConnectionContext:
    """連接上下文"""
    websocket: WebSocket
    user_id: str
    permissions: List[str]
    subscriptions: Dict[str, ClientSubscription] = field(default_factory=dict)
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_authenticated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_activity(self):
        """更新活動時間"""
        self.last_activity = datetime.now(timezone.utc)

class DataProcessor:
    """數據處理器基類"""

    def __init__(self, stream_type: StreamType):
        self.stream_type = stream_type
        self.subscribers: weakref.WeakSet = weakref.WeakSet()
        self.last_sent_data: Dict[str, Any] = {}

    async def process_data(self, raw_data: Dict[str, Any]) -> StreamMessage:
        """處理原始數據"""
        raise NotImplementedError("Subclasses must implement process_data")

    async def subscribe(self, connection_context: ConnectionContext):
        """訂閱數據流"""
        self.subscribers.add(connection_context)

    async def unsubscribe(self, connection_context: ConnectionContext):
        """取消訂閱"""
        self.subscribers.discard(connection_context)

    def _should_send_update(self, data: Dict[str, Any]) -> bool:
        """檢查是否需要發送更新（增量更新邏輯）"""
        # 簡單的變化檢測
        current_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
        data_key = data.get('key', 'default')

        if data_key in self.last_sent_data:
            if self.last_sent_data[data_key] == current_hash:
                return False

        self.last_sent_data[data_key] = current_hash
        return True

class StrategyExecutionProcessor(DataProcessor):
    """策略執行數據處理器"""

    def __init__(self):
        super().__init__(StreamType.STRATEGY_EXECUTION)

    async def process_data(self, raw_data: Dict[str, Any]) -> StreamMessage:
        """處理策略執行數據"""
        processed_data = {
            "strategy_id": raw_data.get("strategy_id"),
            "status": raw_data.get("status"),  # running, paused, stopped, error
            "execution_time": raw_data.get("execution_time"),
            "performance": raw_data.get("performance", {}),
            "signals": raw_data.get("signals", []),
            "positions": raw_data.get("positions", []),
            "orders": raw_data.get("orders", []),
            "error_message": raw_data.get("error_message"),
            "progress": raw_data.get("progress", 0)
        }

        return StreamMessage(
            stream_type=self.stream_type,
            message_type=MessageType.REALTIME_UPDATE,
            data=processed_data
        )

class RiskMonitoringProcessor(DataProcessor):
    """風險監控數據處理器"""

    def __init__(self):
        super().__init__(StreamType.RISK_MONITORING)

    async def process_data(self, raw_data: Dict[str, Any]) -> StreamMessage:
        """處理風險監控數據"""
        processed_data = {
            "portfolio_id": raw_data.get("portfolio_id"),
            "risk_metrics": raw_data.get("risk_metrics", {}),
            "var_metrics": raw_data.get("var_metrics", {}),
            "exposure": raw_data.get("exposure", {}),
            "concentration": raw_data.get("concentration", {}),
            "alerts": raw_data.get("alerts", []),
            "risk_score": raw_data.get("risk_score"),
            "stop_loss_triggered": raw_data.get("stop_loss_triggered", False)
        }

        # 如果有風險警報，使用ALERT消息類型
        message_type = MessageType.ALERT if processed_data.get("alerts") else MessageType.REALTIME_UPDATE

        return StreamMessage(
            stream_type=self.stream_type,
            message_type=message_type,
            data=processed_data
        )

class PerformanceMetricsProcessor(DataProcessor):
    """性能指標數據處理器"""

    def __init__(self):
        super().__init__(StreamType.PERFORMANCE_METRICS)

    async def process_data(self, raw_data: Dict[str, Any]) -> StreamMessage:
        """處理性能指標數據"""
        processed_data = {
            "strategy_id": raw_data.get("strategy_id"),
            "portfolio_id": raw_data.get("portfolio_id"),
            "returns": raw_data.get("returns", {}),
            "sharpe_ratio": raw_data.get("sharpe_ratio"),
            "max_drawdown": raw_data.get("max_drawdown"),
            "win_rate": raw_data.get("win_rate"),
            "profit_factor": raw_data.get("profit_factor"),
            "calmar_ratio": raw_data.get("calmar_ratio"),
            "sortino_ratio": raw_data.get("sortino_ratio"),
            "beta": raw_data.get("beta"),
            "alpha": raw_data.get("alpha"),
            "volatility": raw_data.get("volatility"),
            "tracking_error": raw_data.get("tracking_error"),
            "information_ratio": raw_data.get("information_ratio")
        }

        return StreamMessage(
            stream_type=self.stream_type,
            message_type=MessageType.REALTIME_UPDATE,
            data=processed_data
        )

class MarketDataProcessor(DataProcessor):
    """市場數據處理器"""

    def __init__(self):
        super().__init__(StreamType.MARKET_DATA)

    async def process_data(self, raw_data: Dict[str, Any]) -> StreamMessage:
        """處理市場數據"""
        processed_data = {
            "symbol": raw_data.get("symbol"),
            "price": raw_data.get("price"),
            "volume": raw_data.get("volume"),
            "bid": raw_data.get("bid"),
            "ask": raw_data.get("ask"),
            "high": raw_data.get("high"),
            "low": raw_data.get("low"),
            "open": raw_data.get("open"),
            "close": raw_data.get("close"),
            "change": raw_data.get("change"),
            "change_percent": raw_data.get("change_percent"),
            "timestamp": raw_data.get("timestamp"),
            "market_cap": raw_data.get("market_cap"),
            "pe_ratio": raw_data.get("pe_ratio"),
            "dividend_yield": raw_data.get("dividend_yield")
        }

        return StreamMessage(
            stream_type=self.stream_type,
            message_type=MessageType.REALTIME_UPDATE,
            data=processed_data
        )

class SystemNotificationProcessor(DataProcessor):
    """系統通知處理器"""

    def __init__(self):
        super().__init__(StreamType.SYSTEM_NOTIFICATIONS)

    async def process_data(self, raw_data: Dict[str, Any]) -> StreamMessage:
        """處理系統通知數據"""
        processed_data = {
            "notification_id": raw_data.get("notification_id"),
            "type": raw_data.get("type"),  # info, warning, error, success
            "title": raw_data.get("title"),
            "message": raw_data.get("message"),
            "action_required": raw_data.get("action_required", False),
            "action_url": raw_data.get("action_url"),
            "expires_at": raw_data.get("expires_at"),
            "priority": raw_data.get("priority", "normal"),
            "target_users": raw_data.get("target_users", []),  # 空列表表示廣播
            "metadata": raw_data.get("metadata", {})
        }

        return StreamMessage(
            stream_type=self.stream_type,
            message_type=MessageType.NOTIFICATION,
            data=processed_data
        )

class UnifiedWebSocketManager:
    """統一WebSocket服務管理器"""

    def __init__(self,
                 redis_client: Optional[redis.Redis] = None,
                 secret_key: str = "unified-websocket-secret-key",
                 enable_compression: bool = True,
                 max_connections_per_user: int = 10):
        """
        初始化統一WebSocket管理器

        Args:
            redis_client: Redis客戶端實例
            secret_key: JWT簽名密鑰
            enable_compression: 是否啟用數據壓縮
            max_connections_per_user: 每個用戶的最大連接數
        """
        self.connections: Dict[WebSocket, ConnectionContext] = {}
        self.user_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.redis_client = redis_client
        self.secret_key = secret_key
        self.enable_compression = enable_compression
        self.max_connections_per_user = max_connections_per_user

        # 初始化數據處理器
        self.processors: Dict[StreamType, DataProcessor] = {
            StreamType.STRATEGY_EXECUTION: StrategyExecutionProcessor(),
            StreamType.RISK_MONITORING: RiskMonitoringProcessor(),
            StreamType.PERFORMANCE_METRICS: PerformanceMetricsProcessor(),
            StreamType.MARKET_DATA: MarketDataProcessor(),
            StreamType.SYSTEM_NOTIFICATIONS: SystemNotificationProcessor()
        }

        # 統計信息
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "errors_count": 0,
            "last_reset": datetime.now(timezone.utc)
        }

        # 速率限制
        self.rate_limits: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            "last_reset": time.time(),
            "message_count": 0
        })

        # 消息隊列（用於批處理）
        self.message_queues: Dict[StreamType, deque] = defaultdict(lambda: deque(maxlen=1000))

        # 啟動後台任務
        self._background_tasks: Set[asyncio.Task] = set()
        self._start_background_tasks()

    def _start_background_tasks(self):
        """啟動後台任務"""
        # 消息批處理任務
        task = asyncio.create_task(self._batch_message_processor())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        # 連接健康檢查任務
        task = asyncio.create_task(self._connection_health_checker())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        # 統計信息更新任務
        task = asyncio.create_task(self._stats_updater())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def authenticate_connection(self, websocket: WebSocket, token: str) -> Optional[ConnectionContext]:
        """
        驗證WebSocket連接

        Args:
            websocket: WebSocket連接對象
            token: JWT token

        Returns:
            ConnectionContext: 連接上下文，驗證失敗返回None
        """
        try:
            # 解析JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            user_id = payload.get("user_id")
            permissions = payload.get("permissions", [])

            if not user_id:
                logger.warning("JWT token missing user_id")
                return None

            # 檢查用戶連接數限制
            if len(self.user_connections[user_id]) >= self.max_connections_per_user:
                logger.warning(f"User {user_id} exceeded max connections limit")
                return None

            # 創建連接上下文
            context = ConnectionContext(
                websocket=websocket,
                user_id=user_id,
                permissions=permissions,
                is_authenticated=True,
                metadata=payload.get("metadata", {})
            )

            # 註冊連接
            self.connections[websocket] = context
            self.user_connections[user_id].add(websocket)

            # 更新統計信息
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.connections)

            logger.info(f"WebSocket authenticated: user_id={user_id}, permissions={permissions}")
            return context

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    async def disconnect(self, websocket: WebSocket):
        """斷開WebSocket連接"""
        context = self.connections.get(websocket)
        if not context:
            return

        # 從所有訂閱中移除
        for processor in self.processors.values():
            await processor.unsubscribe(context)

        # 移除連接
        user_id = context.user_id
        del self.connections[websocket]
        self.user_connections[user_id].discard(websocket)

        # 更新統計信息
        self.stats["active_connections"] = len(self.connections)

        logger.info(f"WebSocket disconnected: user_id={user_id}")

    async def subscribe_to_stream(self,
                                websocket: WebSocket,
                                stream_type: str,
                                filters: Optional[Dict[str, Any]] = None,
                                frequency_limit: Optional[float] = None) -> bool:
        """
        訂閱數據流

        Args:
            websocket: WebSocket連接對象
            stream_type: 數據流類型
            filters: 過濾條件
            frequency_limit: 頻率限制（每秒消息數）

        Returns:
            bool: 訂閱是否成功
        """
        context = self.connections.get(websocket)
        if not context or not context.is_authenticated:
            return False

        try:
            stream_enum = StreamType(stream_type)
        except ValueError:
            logger.error(f"Invalid stream type: {stream_type}")
            return False

        # 檢查權限
        if not self._check_permission(context, stream_enum):
            logger.warning(f"User {context.user_id} lacks permission for {stream_type}")
            return False

        # 創建訂閱
        subscription = ClientSubscription(
            stream_types={stream_enum},
            filters=filters or {},
            frequency_limit=frequency_limit
        )

        context.subscriptions[stream_type] = subscription

        # 註冊到處理器
        processor = self.processors[stream_enum]
        await processor.subscribe(context)

        # 發送確認消息
        await self._send_subscription_confirmation(websocket, stream_type, True)

        logger.info(f"Subscribed {context.user_id} to {stream_type}")
        return True

    async def unsubscribe_from_stream(self, websocket: WebSocket, stream_type: str) -> bool:
        """
        取消訂閱數據流

        Args:
            websocket: WebSocket連接對象
            stream_type: 數據流類型

        Returns:
            bool: 取消訂閱是否成功
        """
        context = self.connections.get(websocket)
        if not context:
            return False

        if stream_type not in context.subscriptions:
            return False

        try:
            stream_enum = StreamType(stream_type)
        except ValueError:
            return False

        # 移除訂閱
        del context.subscriptions[stream_type]

        # 從處理器移除
        processor = self.processors[stream_enum]
        await processor.unsubscribe(context)

        # 發送確認消息
        await self._send_subscription_confirmation(websocket, stream_type, False)

        logger.info(f"Unsubscribed {context.user_id} from {stream_type}")
        return True

    async def broadcast_to_stream(self,
                                stream_type: str,
                                raw_data: Dict[str, Any],
                                target_users: Optional[List[str]] = None) -> int:
        """
        廣播數據到指定流的所有訂閱者

        Args:
            stream_type: 數據流類型
            raw_data: 原始數據
            target_users: 目標用戶列表（None表示廣播給所有訂閱者）

        Returns:
            int: 成功發送的消息數量
        """
        try:
            stream_enum = StreamType(stream_type)
        except ValueError:
            logger.error(f"Invalid stream type: {stream_type}")
            return 0

        processor = self.processors[stream_enum]

        # 處理數據
        try:
            message = await processor.process_data(raw_data)
        except Exception as e:
            logger.error(f"Error processing data for {stream_type}: {e}")
            return 0

        # 檢查是否需要發送更新
        if not processor._should_send_update(raw_data):
            return 0

        # 添加到消息隊列（用於批處理）
        self.message_queues[stream_enum].append((message, target_users))

        # 直接發送（實時模式）
        return await self._send_message_to_subscribers(message, target_users)

    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]) -> bool:
        """
        發送個人消息

        Args:
            websocket: WebSocket連接對象
            message: 消息內容

        Returns:
            bool: 發送是否成功
        """
        context = self.connections.get(websocket)
        if not context:
            return False

        try:
            # 序列化消息
            json_data = json.dumps(message, default=str)

            # 壓縮（如果啟用）
            if self.enable_compression and len(json_data) > 1024:
                json_data = self._compress_data(json_data)
                message_header = {"compressed": True}
            else:
                message_header = {"compressed": False}

            # 發送消息
            await websocket.send_text(json_data)

            # 更新統計
            self.stats["messages_sent"] += 1
            context.update_activity()

            return True

        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            return False

    async def get_connection_stats(self) -> Dict[str, Any]:
        """獲取連接統計信息"""
        return {
            **self.stats,
            "active_connections": len(self.connections),
            "user_connections": {uid: len(conns) for uid, conns in self.user_connections.items()},
            "subscriptions": self._get_subscription_stats(),
            "processor_stats": self._get_processor_stats()
        }

    def _check_permission(self, context: ConnectionContext, stream_type: StreamType) -> bool:
        """檢查用戶權限"""
        required_permissions = {
            StreamType.STRATEGY_EXECUTION: ["strategy.execute"],
            StreamType.RISK_MONITORING: ["risk.view"],
            StreamType.PERFORMANCE_METRICS: ["performance.view"],
            StreamType.MARKET_DATA: ["market.view"],
            StreamType.SYSTEM_NOTIFICATIONS: ["system.notifications"]
        }

        required = required_permissions.get(stream_type, [])
        return any(perm in context.permissions for perm in required)

    async def _send_subscription_confirmation(self, websocket: WebSocket, stream_type: str, subscribed: bool):
        """發送訂閱確認消息"""
        message_type = MessageType.SUBSCRIPTION_CONFIRMED if subscribed else MessageType.UNSUBSCRIPTION_CONFIRMED

        message = {
            "stream_type": stream_type,
            "message_type": message_type.value,
            "data": {
                "stream": stream_type,
                "subscribed": subscribed,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

        await self.send_personal_message(websocket, message)

    async def _send_message_to_subscribers(self,
                                        message: StreamMessage,
                                        target_users: Optional[List[str]] = None) -> int:
        """發送消息給訂閱者"""
        message_dict = message.to_dict()
        sent_count = 0

        for websocket, context in self.connections.items():
            # 檢查是否為目標用戶
            if target_users and context.user_id not in target_users:
                continue

            # 檢查是否訂閱了該流
            if message.stream_type.value not in context.subscriptions:
                continue

            # 檢查頻率限制
            subscription = context.subscriptions[message.stream_type.value]
            if subscription.should_throttle(time.time()):
                continue

            # 應用過濾器
            if not self._apply_filters(message.data, subscription.filters):
                continue

            # 發送消息
            if await self.send_personal_message(websocket, message_dict):
                sent_count += 1

        return sent_count

    def _apply_filters(self, data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """應用過濾條件"""
        if not filters:
            return True

        for key, value in filters.items():
            if key in data and data[key] != value:
                return False

        return True

    def _compress_data(self, data: str) -> str:
        """壓縮數據"""
        compressed = zlib.compress(data.encode())
        return compressed.hex()

    def _get_subscription_stats(self) -> Dict[str, int]:
        """獲取訂閱統計信息"""
        stats = defaultdict(int)
        for context in self.connections.values():
            for stream_type in context.subscriptions:
                stats[stream_type] += 1
        return dict(stats)

    def _get_processor_stats(self) -> Dict[str, int]:
        """獲取處理器統計信息"""
        return {
            stream_type.value: len(processor.subscribers)
            for stream_type, processor in self.processors.items()
        }

    async def _batch_message_processor(self):
        """批處理消息處理器"""
        while True:
            try:
                for stream_type, queue in self.message_queues.items():
                    if queue:
                        # 批量處理消息
                        batch_size = min(10, len(queue))
                        batch = [queue.popleft() for _ in range(batch_size)]

                        # 合併消息（如果可能）
                        if len(batch) > 1:
                            await self._process_message_batch(stream_type, batch)
                        else:
                            message, target_users = batch[0]
                            await self._send_message_to_subscribers(message, target_users)

                await asyncio.sleep(0.1)  # 100ms批處理間隔

            except Exception as e:
                logger.error(f"Error in batch message processor: {e}")
                await asyncio.sleep(1)

    async def _process_message_batch(self, stream_type: StreamType, batch: List[Tuple[StreamMessage, Optional[List[str]]]]):
        """處理消息批次"""
        # 簡單的合併策略：只發送最新的消息
        if batch:
            latest_message, target_users = batch[-1]
            await self._send_message_to_subscribers(latest_message, target_users)

    async def _connection_health_checker(self):
        """連接健康檢查器"""
        while True:
            try:
                disconnected = []

                for websocket, context in list(self.connections.items()):
                    try:
                        # 發送心跳
                        heartbeat = {
                            "stream_type": "system",
                            "message_type": MessageType.HEARTBEAT.value,
                            "data": {
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        }

                        await websocket.send_json(heartbeat)
                        context.update_activity()

                    except Exception as e:
                        logger.warning(f"Connection health check failed: {e}")
                        disconnected.append(websocket)

                # 清理斷開的連接
                for websocket in disconnected:
                    await self.disconnect(websocket)

                await asyncio.sleep(30)  # 30秒心跳間隔

            except Exception as e:
                logger.error(f"Error in connection health checker: {e}")
                await asyncio.sleep(30)

    async def _stats_updater(self):
        """統計信息更新器"""
        while True:
            try:
                # 將統計信息存儲到Redis
                if self.redis_client:
                    await self.redis_client.hset(
                        "websocket:stats",
                        mapping={
                            "active_connections": str(self.stats["active_connections"]),
                            "total_connections": str(self.stats["total_connections"]),
                            "messages_sent": str(self.stats["messages_sent"]),
                            "last_update": datetime.now(timezone.utc).isoformat()
                        }
                    )

                await asyncio.sleep(60)  # 60秒更新間隔

            except Exception as e:
                logger.error(f"Error in stats updater: {e}")
                await asyncio.sleep(60)

# Singleton instance
unified_ws_manager = UnifiedWebSocketManager()