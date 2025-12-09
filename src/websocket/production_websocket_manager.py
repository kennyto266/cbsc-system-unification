"""
生產級WebSocket管理器
基於專家審查建議實現的企業級WebSocket連接管理

Features:
- 連接池管理和自動清理
- 性能監控和統計
- 異常處理和資源管理
- 速率限制和安全檢查
- 消息隊列和廣播功能

Author: CBSC Quantitative Trading System
Version: 1.0.0
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Callable

from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.websockets import WebSocketState

from src.api.production_parameter_controls import (
    SecureParameterUpdate, process_parameter_update, session_manager
)
from src.security.enterprise_security import rate_limiter, SecurityValidationError

# 配置日誌
logger = logging.getLogger(__name__)


class WebSocketConnection:
    """
    WebSocket連接包裝器

    提供連接管理和狀態追蹤功能
    """

    def __init__(self, websocket: WebSocket, connection_id: str, session_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.session_id = session_id
        self.connected_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.message_count = 0
        self.error_count = 0
        self.status = "connecting"

    async def send_json(self, data: dict) -> None:
        """安全發送JSON消息"""
        try:
            if self.websocket.client_state == WebSocketState.CONNECTED:
                await self.websocket.send_json(data)
                self.last_activity = datetime.utcnow()
                self.message_count += 1
            else:
                logger.warning(f"WebSocket連接已斷開，無法發送消息: {self.connection_id}")
                raise ConnectionError("WebSocket連接已斷開")

        except Exception as e:
            self.error_count += 1
            logger.error(f"WebSocket發送消息失敗: {self.connection_id} - {str(e)}")
            raise

    async def send_text(self, message: str) -> None:
        """安全發送文本消息"""
        try:
            if self.websocket.client_state == WebSocketState.CONNECTED:
                await self.websocket.send_text(message)
                self.last_activity = datetime.utcnow()
                self.message_count += 1
            else:
                raise ConnectionError("WebSocket連接已斷開")

        except Exception as e:
            self.error_count += 1
            logger.error(f"WebSocket發送消息失敗: {self.connection_id} - {str(e)}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """獲取連接統計信息"""
        return {
            "connection_id": self.connection_id,
            "session_id": self.session_id,
            "connected_at": self.connected_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": self.message_count,
            "error_count": self.error_count,
            "status": self.status,
            "duration_seconds": (datetime.utcnow() - self.connected_at).total_seconds()
        }


class ProductionWebSocketManager:
    """
    生產級WebSocket管理器

    提供企業級WebSocket連接管理功能
    """

    def __init__(self):
        # 連接管理
        self.connections: Dict[str, WebSocketConnection] = {}
        self.session_connections: Dict[str, Set[str]] = {}  # session_id -> connection_ids

        # 消息隊列
        self.message_queue = asyncio.Queue(maxsize=1000)
        self.broadcast_queue = asyncio.Queue(maxsize=1000)

        # 統計信息
        self.stats = {
            "total_connections": 0,
            "current_connections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "total_errors": 0,
            "peak_connections": 0
        }

        # 清理任務
        self.cleanup_task: Optional[asyncio.Task] = None
        self.message_processor_task: Optional[asyncio.Task] = None
        self.broadcast_processor_task: Optional[asyncio.Task] = None

        # 啟動後台任務
        self._start_background_tasks()

    def _start_background_tasks(self) -> None:
        """啟動後台處理任務"""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_connections())

        if self.message_processor_task is None or self.message_processor_task.done():
            self.message_processor_task = asyncio.create_task(self._process_messages())

        if self.broadcast_processor_task is None or self.broadcast_processor_task.done():
            self.broadcast_processor_task = asyncio.create_task(self._process_broadcasts())

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: Optional[str] = None
    ) -> str:
        """
        建立WebSocket連接

        Args:
            websocket: WebSocket連接
            session_id: 會話ID
            user_id: 用戶ID

        Returns:
            連接ID

        Raises:
            HTTPException: 連接失敗
        """
        connection_id = str(uuid.uuid4())
        connection = WebSocketConnection(websocket, connection_id, session_id)

        try:
            # 檢查會話是否存在
            if session_id not in session_manager.active_sessions:
                await session_manager.create_session(session_id, user_id)

            # 速率限制檢查
            await rate_limiter.check_rate_limit(
                identifier=session_id,
                limit_type='websocket_messages',
                ip_address=websocket.client.host if websocket.client else None
            )

            # 接受連接
            await websocket.accept()

            # 註冊連接
            self.connections[connection_id] = connection
            if session_id not in self.session_connections:
                self.session_connections[session_id] = set()
            self.session_connections[session_id].add(connection_id)

            # 更新統計
            self.stats["total_connections"] += 1
            self.stats["current_connections"] = len(self.connections)
            self.stats["peak_connections"] = max(self.stats["peak_connections"], self.stats["current_connections"])

            connection.status = "connected"

            # 發送歡迎消息
            await self._send_welcome_message(connection)

            logger.info(f"WebSocket連接建立: {connection_id} (session: {session_id})")
            return connection_id

        except Exception as e:
            connection.status = "error"
            logger.error(f"WebSocket連接建立失敗: {connection_id} - {str(e)}")

            # 清理失敗的連接
            if connection_id in self.connections:
                del self.connections[connection_id]

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"WebSocket連接建立失敗: {str(e)}"
            )

    async def disconnect(self, connection_id: str) -> None:
        """
        斷開WebSocket連接

        Args:
            connection_id: 連接ID
        """
        if connection_id not in self.connections:
            return

        connection = self.connections[connection_id]
        session_id = connection.session_id

        try:
            # 發送斷開消息
            if connection.websocket.client_state == WebSocketState.CONNECTED:
                await self._send_disconnect_message(connection)

            # 關閉連接
            try:
                await connection.websocket.close()
            except Exception:
                pass  # 連接可能已經關閉

        except Exception as e:
            logger.error(f"WebSocket斷開時發送消息失敗: {connection_id} - {str(e)}")

        finally:
            # 清理連接記錄
            del self.connections[connection_id]

            if session_id in self.session_connections:
                self.session_connections[session_id].discard(connection_id)
                if not self.session_connections[session_id]:
                    del self.session_connections[session_id]

            # 更新統計
            self.stats["current_connections"] = len(self.connections)

            connection.status = "disconnected"

            logger.info(f"WebSocket連接斷開: {connection_id}")

    async def send_to_connection(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """
        向特定連接發送消息

        Args:
            connection_id: 連接ID
            message: 消息內容

        Returns:
            是否發送成功
        """
        if connection_id not in self.connections:
            logger.warning(f"連接不存在: {connection_id}")
            return False

        connection = self.connections[connection_id]
        if connection.status != "connected":
            logger.warning(f"連接未激活: {connection_id} (status: {connection.status})")
            return False

        try:
            await connection.send_json(message)
            self.stats["total_messages_sent"] += 1
            return True

        except Exception as e:
            self.stats["total_errors"] += 1
            logger.error(f"發送消息失敗: {connection_id} - {str(e)}")

            # 連接可能已斷開，標記為錯誤
            if connection.error_count > 3:
                connection.status = "error"
                # 異步斷開連接
                asyncio.create_task(self.disconnect(connection_id))

            return False

    async def broadcast_to_session(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> int:
        """
        向會話所有連接廣播消息

        Args:
            session_id: 會話ID
            message: 消息內容

        Returns:
            成功發送的連接數量
        """
        if session_id not in self.session_connections:
            return 0

        connection_ids = list(self.session_connections[session_id])
        success_count = 0

        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                success_count += 1

        logger.debug(f"會話廣播完成: {session_id} - {success_count}/{len(connection_ids)} 連接")
        return success_count

    async def handle_message(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """
        處理收到的消息

        Args:
            connection_id: 連接ID
            message: 消息內容

        Returns:
            是否處理成功
        """
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]

        try:
            # 更新活動時間
            connection.last_activity = datetime.utcnow()
            self.stats["total_messages_received"] += 1

            # 速率限制檢查
            await rate_limiter.check_rate_limit(
                identifier=connection.session_id,
                limit_type='websocket_messages',
                ip_address=connection.websocket.client.host if connection.websocket.client else None
            )

            # 添加到消息隊列
            await self.message_queue.put({
                "connection_id": connection_id,
                "session_id": connection.session_id,
                "message": message,
                "timestamp": datetime.utcnow()
            })

            return True

        except SecurityValidationError as e:
            logger.warning(f"安全驗證失敗: {connection_id} - {str(e)}")
            await self._send_error_message(connection, str(e), "SECURITY_ERROR")
            return False

        except Exception as e:
            self.stats["total_errors"] += 1
            logger.error(f"消息處理失敗: {connection_id} - {str(e)}")
            await self._send_error_message(connection, "消息處理失敗", "INTERNAL_ERROR")
            return False

    async def _process_messages(self) -> None:
        """處理消息隊列"""
        while True:
            try:
                # 獲取消息（阻塞等待）
                message_data = await self.message_queue.get()

                # 處理消息
                await self._process_single_message(message_data)

                # 標記任務完成
                self.message_queue.task_done()

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"消息隊列處理錯誤: {str(e)}")

    async def _process_single_message(self, message_data: Dict[str, Any]) -> None:
        """處理單條消息"""
        connection_id = message_data["connection_id"]
        session_id = message_data["session_id"]
        message = message_data["message"]
        timestamp = message_data["timestamp"]

        try:
            # 檢查連接是否還存在
            if connection_id not in self.connections:
                return

            # 處理參數更新消息
            if message.get("type") == "parameter_update":
                response = await process_parameter_update(session_id, message.get("data", {}))

                # 發送響應
                await self.send_to_connection(connection_id, response.dict())

                # 如果是成功的參數更新，廣播給會話其他連接
                if response.success:
                    broadcast_message = {
                        "type": "parameter_broadcast",
                        "session_id": session_id,
                        "parameter_update": response.data.get("parameter_update"),
                        "timestamp": timestamp.isoformat()
                    }
                    await self.broadcast_to_session(session_id, broadcast_message)

            # 處理心跳消息
            elif message.get("type") == "ping":
                await self._send_pong_response(connection_id, timestamp)

            # 處理狀態查詢
            elif message.get("type") == "status_query":
                await self._send_status_response(connection_id)

            else:
                await self._send_error_message(
                    self.connections[connection_id],
                    f"未知消息類型: {message.get('type')}",
                    "UNKNOWN_MESSAGE_TYPE"
                )

        except Exception as e:
            logger.error(f"處理消息失敗: {connection_id} - {str(e)}")
            if connection_id in self.connections:
                await self._send_error_message(
                    self.connections[connection_id],
                    "消息處理失敗",
                    "MESSAGE_PROCESSING_ERROR"
                )

    async def _process_broadcasts(self) -> None:
        """處理廣播隊列"""
        while True:
            try:
                broadcast_data = await self.broadcast_queue.get()

                # 處理廣播
                await self._process_single_broadcast(broadcast_data)

                # 標記任務完成
                self.broadcast_queue.task_done()

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"廣播隊列處理錯誤: {str(e)}")

    async def _process_single_broadcast(self, broadcast_data: Dict[str, Any]) -> None:
        """處理單條廣播"""
        try:
            session_id = broadcast_data["session_id"]
            message = broadcast_data["message"]

            await self.broadcast_to_session(session_id, message)

        except Exception as e:
            logger.error(f"處理廣播失敗: {str(e)}")

    async def _cleanup_connections(self) -> None:
        """清理斷開的連接"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分鐘清理一次

                current_time = datetime.utcnow()
                disconnected_connections = []

                for connection_id, connection in self.connections.items():
                    # 檢查連接超時（5分鐘無活動）
                    if (current_time - connection.last_activity).total_seconds() > 300:
                        logger.info(f"連接超時，準備斷開: {connection_id}")
                        disconnected_connections.append(connection_id)

                    # 檢查連接狀態
                    elif connection.websocket.client_state != WebSocketState.CONNECTED:
                        logger.info(f"連接已斷開，準備清理: {connection_id}")
                        disconnected_connections.append(connection_id)

                # 斷開過期連接
                for connection_id in disconnected_connections:
                    await self.disconnect(connection_id)

                if disconnected_connections:
                    logger.info(f"清理了 {len(disconnected_connections)} 個過期連接")

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"連接清理任務錯誤: {str(e)}")

    async def _send_welcome_message(self, connection: WebSocketConnection) -> None:
        """發送歡迎消息"""
        welcome_message = {
            "type": "welcome",
            "connection_id": connection.connection_id,
            "session_id": connection.session_id,
            "server_time": datetime.utcnow().isoformat(),
            "message": "WebSocket連接建立成功"
        }
        await connection.send_json(welcome_message)

    async def _send_disconnect_message(self, connection: WebSocketConnection) -> None:
        """發送斷開消息"""
        disconnect_message = {
            "type": "disconnect",
            "connection_id": connection.connection_id,
            "reason": "server_shutdown",
            "timestamp": datetime.utcnow().isoformat()
        }
        await connection.send_json(disconnect_message)

    async def _send_pong_response(self, connection_id: str, timestamp: datetime) -> None:
        """發送pong響應"""
        pong_message = {
            "type": "pong",
            "timestamp": timestamp.isoformat(),
            "server_time": datetime.utcnow().isoformat()
        }
        await self.send_to_connection(connection_id, pong_message)

    async def _send_status_response(self, connection_id: str) -> None:
        """發送狀態響應"""
        if connection_id not in self.connections:
            return

        connection = self.connections[connection_id]
        status_message = {
            "type": "status_response",
            "connection_stats": connection.get_stats(),
            "session_stats": await session_manager.get_session_parameters(connection.session_id),
            "server_stats": self.get_server_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }
        await connection.send_json(status_message)

    async def _send_error_message(
        self,
        connection: WebSocketConnection,
        error_message: str,
        error_code: str
    ) -> None:
        """發送錯誤消息"""
        error_response = {
            "type": "error",
            "error": error_message,
            "error_code": error_code,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            await connection.send_json(error_response)
        except Exception:
            pass  # 連接可能已斷開

    def get_server_stats(self) -> Dict[str, Any]:
        """獲取服務器統計信息"""
        # 活躍會話統計
        active_sessions = {}
        for session_id, connection_ids in self.session_connections.items():
            active_sessions[session_id] = len(connection_ids)

        return {
            "connections": {
                "current": len(self.connections),
                "peak": self.stats["peak_connections"],
                "total": self.stats["total_connections"]
            },
            "messages": {
                "sent": self.stats["total_messages_sent"],
                "received": self.stats["total_messages_received"],
                "errors": self.stats["total_errors"]
            },
            "sessions": {
                "active": len(self.session_connections),
                "details": active_sessions
            },
            "tasks": {
                "cleanup_running": self.cleanup_task is not None and not self.cleanup_task.done(),
                "message_processor_running": self.message_processor_task is not None and not self.message_processor_task.done(),
                "broadcast_processor_running": self.broadcast_processor_task is not None and not self.broadcast_processor_task.done()
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    async def shutdown(self) -> None:
        """關閉管理器"""
        logger.info("開始關閉WebSocket管理器")

        # 取消後台任務
        tasks_to_cancel = [
            self.cleanup_task,
            self.message_processor_task,
            self.broadcast_processor_task
        ]

        for task in tasks_to_cancel:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # 斷開所有連接
        connection_ids = list(self.connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id)

        logger.info("WebSocket管理器已關閉")


# 全局WebSocket管理器實例
websocket_manager = ProductionWebSocketManager()