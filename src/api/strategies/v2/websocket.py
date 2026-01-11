"""
Strategy WebSocket v2
策略管理 WebSocket v2 實現

提供實時數據推送，包括：
- 策略執行狀態更新
- 性能指標變化
- 系統通知
- 市場數據更新
"""

import json
import asyncio
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.websockets import WebSocketState
import uuid

from ..services.websocket_service import WebSocketService
from ..utils.permissions import get_current_user_ws
from ..models import User

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """消息類型枚舉"""
    STRATEGY_UPDATE = "strategy_update"
    EXECUTION_UPDATE = "execution_update"
    PERFORMANCE_UPDATE = "performance_update"
    SYSTEM_NOTIFICATION = "system_notification"
    MARKET_DATA = "market_data"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


class WebSocketManager:
    """
    WebSocket 連接管理器
    管理所有客戶端連接和消息分發
    """

    def __init__(self):
        # 存储活躍連接 {connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}

        # 用戶連接映射 {user_id: Set[connection_id]}
        self.user_connections: Dict[int, Set[str]] = {}

        # 策略訂閱 {strategy_id: Set[connection_id]}
        self.strategy_subscriptions: Dict[str, Set[str]] = {}

        # 執行訂閱 {execution_id: Set[connection_id]}
        self.execution_subscriptions: Dict[str, Set[str]] = {}

        # 連接元數據 {connection_id: metadata}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}

        # 廣播訂閱（所有連接）
        self.broadcast_subscribers: Set[str] = set()

        # 心跳任務
        self._heartbeat_task: Optional[asyncio.Task] = None

        # 消息隊列
        self.message_queue: asyncio.Queue = asyncio.Queue()

        # 消息處理器
        self._message_processor_task: Optional[asyncio.Task] = None

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        connection_id: Optional[str] = None
    ) -> str:
        """
        建立 WebSocket 連接
        """
        if connection_id is None:
            connection_id = str(uuid.uuid4())

        # 接受連接
        await websocket.accept()

        # 存储連接
        self.active_connections[connection_id] = websocket

        # 更新用戶連接映射
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)

        # 存储連接元數據
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow(),
            "subscriptions": {
                "strategies": set(),
                "executions": set(),
                "broadcast": False
            }
        }

        # 發送歡迎消息
        await self.send_personal_message(
            connection_id,
            {
                "type": MessageType.SYSTEM_NOTIFICATION,
                "data": {
                    "message": "連接成功",
                    "connection_id": connection_id,
                    "connected_at": self.connection_metadata[connection_id]["connected_at"].isoformat()
                }
            }
        )

        logger.info(f"WebSocket 連接建立: {connection_id} (用戶: {user_id})")

        # 啟動心跳任務（如果尚未啟動）
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        # 啟動消息處理器（如果尚未啟動）
        if self._message_processor_task is None:
            self._message_processor_task = asyncio.create_task(self._message_processor_loop())

        return connection_id

    async def disconnect(self, connection_id: str):
        """
        斷開 WebSocket 連接
        """
        if connection_id not in self.active_connections:
            return

        # 獲取連接信息
        metadata = self.connection_metadata.get(connection_id, {})
        user_id = metadata.get("user_id")

        # 關閉連接
        websocket = self.active_connections[connection_id]
        if websocket.state == WebSocketState.CONNECTED:
            await websocket.close()

        # 清理連接記錄
        del self.active_connections[connection_id]

        # 清理用戶連接映射
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # 清理訂閱
        self._cleanup_subscriptions(connection_id)

        # 清理元數據
        self.connection_metadata.pop(connection_id, None)

        logger.info(f"WebSocket 連接斷開: {connection_id} (用戶: {user_id})")

    async def send_personal_message(self, connection_id: str, message: Dict[str, Any]):
        """
        發送個人消息
        """
        if connection_id not in self.active_connections:
            return

        websocket = self.active_connections[connection_id]
        if websocket.state != WebSocketState.CONNECTED:
            return

        try:
            # 添加時間戳
            message["timestamp"] = datetime.utcnow().isoformat()

            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"發送個人消息失敗 {connection_id}: {e}")
            # 連接可能已斷開，清理它
            await self.disconnect(connection_id)

    async def send_user_message(self, user_id: int, message: Dict[str, Any]):
        """
        發送給特定用戶的所有連接
        """
        if user_id not in self.user_connections:
            return

        # 並發發送給用戶的所有連接
        tasks = []
        for connection_id in self.user_connections[user_id]:
            tasks.append(self.send_personal_message(connection_id, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_message(self, message: Dict[str, Any], exclude_connections: Set[str] = None):
        """
        廣播消息給所有訂閱者
        """
        exclude_connections = exclude_connections or set()
        tasks = []

        for connection_id in self.broadcast_subscribers:
            if connection_id in exclude_connections:
                continue
            if connection_id in self.active_connections:
                tasks.append(self.send_personal_message(connection_id, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def subscribe_strategy(self, connection_id: str, strategy_id: str):
        """
        訂閱策略更新
        """
        if connection_id not in self.active_connections:
            return

        # 添加到策略訂閱
        if strategy_id not in self.strategy_subscriptions:
            self.strategy_subscriptions[strategy_id] = set()
        self.strategy_subscriptions[strategy_id].add(connection_id)

        # 更新連接元數據
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["subscriptions"]["strategies"].add(strategy_id)

        logger.info(f"連接 {connection_id} 訂閱策略 {strategy_id}")

    async def unsubscribe_strategy(self, connection_id: str, strategy_id: str):
        """
        取消訂閱策略更新
        """
        if strategy_id in self.strategy_subscriptions:
            self.strategy_subscriptions[strategy_id].discard(connection_id)

        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["subscriptions"]["strategies"].discard(strategy_id)

        logger.info(f"連接 {connection_id} 取消訂閱策略 {strategy_id}")

    async def notify_strategy_update(self, strategy_id: str, update_data: Dict[str, Any]):
        """
        通知策略更新
        """
        message = {
            "type": MessageType.STRATEGY_UPDATE,
            "data": {
                "strategy_id": strategy_id,
                "update": update_data
            }
        }

        # 發送給訂閱該策略的連接
        if strategy_id in self.strategy_subscriptions:
            tasks = []
            for connection_id in self.strategy_subscriptions[strategy_id]:
                tasks.append(self.send_personal_message(connection_id, message))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def subscribe_execution(self, connection_id: str, execution_id: str):
        """
        訂閱執行更新
        """
        if connection_id not in self.active_connections:
            return

        if execution_id not in self.execution_subscriptions:
            self.execution_subscriptions[execution_id] = set()
        self.execution_subscriptions[execution_id].add(connection_id)

        # 更新連接元數據
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["subscriptions"]["executions"].add(execution_id)

        logger.info(f"連接 {connection_id} 訂閱執行 {execution_id}")

    async def notify_execution_update(self, execution_id: str, update_data: Dict[str, Any]):
        """
        通知執行更新
        """
        message = {
            "type": MessageType.EXECUTION_UPDATE,
            "data": {
                "execution_id": execution_id,
                "update": update_data
            }
        }

        # 發送給訂閱該執行的連接
        if execution_id in self.execution_subscriptions:
            tasks = []
            for connection_id in self.execution_subscriptions[execution_id]:
                tasks.append(self.send_personal_message(connection_id, message))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def notify_performance_update(self, strategy_id: str, performance_data: Dict[str, Any]):
        """
        通知性能指標更新
        """
        message = {
            "type": MessageType.PERFORMANCE_UPDATE,
            "data": {
                "strategy_id": strategy_id,
                "performance": performance_data
            }
        }

        # 發送給訂閱該策略的連接
        if strategy_id in self.strategy_subscriptions:
            tasks = []
            for connection_id in self.strategy_subscriptions[strategy_id]:
                tasks.append(self.send_personal_message(connection_id, message))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def notify_system_notification(self, notification: Dict[str, Any], target_users: Optional[List[int]] = None):
        """
        發送系統通知
        """
        message = {
            "type": MessageType.SYSTEM_NOTIFICATION,
            "data": notification
        }

        if target_users:
            # 發送給特定用戶
            for user_id in target_users:
                await self.send_user_message(user_id, message)
        else:
            # 廣播給所有用戶
            await self.broadcast_message(message)

    def _cleanup_subscriptions(self, connection_id: str):
        """
        清理連接的所有訂閱
        """
        # 從策略訂閱中移除
        for strategy_id, subscribers in self.strategy_subscriptions.items():
            subscribers.discard(connection_id)

        # 從執行訂閱中移除
        for execution_id, subscribers in self.execution_subscriptions.items():
            subscribers.discard(connection_id)

        # 從廣播訂閱中移除
        self.broadcast_subscribers.discard(connection_id)

    async def _heartbeat_loop(self):
        """
        心跳循環
        """
        while True:
            try:
                await asyncio.sleep(30)  # 30秒心跳間隔

                # 檢查所有連接
                disconnected = []
                for connection_id, websocket in self.active_connections.items():
                    if websocket.state != WebSocketState.CONNECTED:
                        disconnected.append(connection_id)
                        continue

                    try:
                        # 發送心跳
                        await websocket.send_text(json.dumps({
                            "type": MessageType.PING,
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                    except:
                        disconnected.append(connection_id)

                # 清理斷開的連接
                for connection_id in disconnected:
                    await self.disconnect(connection_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳循環錯誤: {e}")

    async def _message_processor_loop(self):
        """
        消息處理循環
        """
        while True:
            try:
                # 從隊列獲取消息
                message_data = await self.message_queue.get()

                # 處理消息
                message_type = message_data.get("type")
                target = message_data.get("target")
                content = message_data.get("content")

                if message_type == "strategy_update":
                    await self.notify_strategy_update(target, content)
                elif message_type == "execution_update":
                    await self.notify_execution_update(target, content)
                elif message_type == "performance_update":
                    await self.notify_performance_update(target, content)
                elif message_type == "system_notification":
                    await self.notify_system_notification(content)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"消息處理錯誤: {e}")

    async def shutdown(self):
        """
        關閉 WebSocket 管理器
        """
        # 取消心跳任務
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # 取消消息處理器任務
        if self._message_processor_task:
            self._message_processor_task.cancel()
            try:
                await self._message_processor_task
            except asyncio.CancelledError:
                pass

        # 關閉所有連接
        for connection_id in list(self.active_connections.keys()):
            await self.disconnect(connection_id)


# 全局 WebSocket 管理器實例
websocket_manager = WebSocketManager()


# ============================================================================
# WebSocket Endpoints
# ============================================================================

async def websocket_endpoint(
    websocket: WebSocket,
    user: User = Depends(get_current_user_ws),
    token: str = Query(..., description="Authentication token")
):
    """
    WebSocket 連接端點
    """
    connection_id = await websocket_manager.connect(websocket, user.id)

    try:
        while True:
            # 接收客戶端消息
            data = await websocket.receive_text()
            message = json.loads(data)

            # 處理消息
            await handle_websocket_message(connection_id, message, user.id)

    except WebSocketDisconnect:
        await websocket_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket 錯誤: {e}")
        await websocket_manager.disconnect(connection_id)


async def handle_websocket_message(connection_id: str, message: Dict[str, Any], user_id: int):
    """
    處理 WebSocket 消息
    """
    message_type = message.get("type")

    if message_type == MessageType.PONG:
        # 更新最後心跳時間
        if connection_id in websocket_manager.connection_metadata:
            websocket_manager.connection_metadata[connection_id]["last_ping"] = datetime.utcnow()

    elif message_type == "subscribe_strategy":
        strategy_id = message.get("strategy_id")
        if strategy_id:
            await websocket_manager.subscribe_strategy(connection_id, strategy_id)

    elif message_type == "unsubscribe_strategy":
        strategy_id = message.get("strategy_id")
        if strategy_id:
            await websocket_manager.unsubscribe_strategy(connection_id, strategy_id)

    elif message_type == "subscribe_execution":
        execution_id = message.get("execution_id")
        if execution_id:
            await websocket_manager.subscribe_execution(connection_id, execution_id)

    elif message_type == "subscribe_broadcast":
        # 訂閱廣播消息
        websocket_manager.broadcast_subscribers.add(connection_id)
        if connection_id in websocket_manager.connection_metadata:
            websocket_manager.connection_metadata[connection_id]["subscriptions"]["broadcast"] = True

    elif message_type == "unsubscribe_broadcast":
        websocket_manager.broadcast_subscribers.discard(connection_id)
        if connection_id in websocket_manager.connection_metadata:
            websocket_manager.connection_metadata[connection_id]["subscriptions"]["broadcast"] = False

    else:
        # 未知消息類型
        await websocket_manager.send_personal_message(connection_id, {
            "type": MessageType.ERROR,
            "data": {
                "error": f"Unknown message type: {message_type}"
            }
        })


# ============================================================================
# WebSocket Utilities
# ============================================================================

async def get_websocket_manager() -> WebSocketManager:
    """
    獲取 WebSocket 管理器實例
    """
    return websocket_manager


def enqueue_message(message_type: str, target: Any, content: Dict[str, Any]):
    """
    將消息加入隊列（用於異步處理）
    """
    websocket_manager.message_queue.put_nowait({
        "type": message_type,
        "target": target,
        "content": content
    })


# 便捷函數
async def notify_strategy_created(strategy_id: str, strategy_data: Dict[str, Any]):
    """通知策略已創建"""
    await websocket_manager.notify_strategy_update(strategy_id, {
        "event": "created",
        "data": strategy_data
    })


async def notify_strategy_updated(strategy_id: str, update_data: Dict[str, Any]):
    """通知策略已更新"""
    await websocket_manager.notify_strategy_update(strategy_id, {
        "event": "updated",
        "data": update_data
    })


async def notify_strategy_deleted(strategy_id: str):
    """通知策略已刪除"""
    await websocket_manager.notify_strategy_update(strategy_id, {
        "event": "deleted",
        "deleted_at": datetime.utcnow().isoformat()
    })


async def notify_execution_started(execution_id: str, execution_data: Dict[str, Any]):
    """通知執行已開始"""
    await websocket_manager.notify_execution_update(execution_id, {
        "event": "started",
        "data": execution_data
    })


async def notify_execution_progress(execution_id: str, progress: Dict[str, Any]):
    """通知執行進度"""
    await websocket_manager.notify_execution_update(execution_id, {
        "event": "progress",
        "data": progress
    })


async def notify_execution_completed(execution_id: str, results: Dict[str, Any]):
    """通知執行已完成"""
    await websocket_manager.notify_execution_update(execution_id, {
        "event": "completed",
        "data": results
    })


async def notify_execution_failed(execution_id: str, error: str):
    """通知執行失敗"""
    await websocket_manager.notify_execution_update(execution_id, {
        "event": "failed",
        "error": error,
        "failed_at": datetime.utcnow().isoformat()
    })