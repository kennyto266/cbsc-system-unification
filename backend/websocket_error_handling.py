"""
WebSocket 错误处理增强模块

为 main_v2.py 提供增强的 WebSocket 错误处理功能
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set

from fastapi import WebSocket, WebSocketDisconnect

# Import error handling utilities
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.error_handler import handle_exception, NetworkError, ErrorCategory
from utils.retry_manager import RetryManager, RetryConfig
from utils.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, get_circuit_breaker

logger = logging.getLogger(__name__)


class EnhancedConnectionManager:
    """
    增强的 WebSocket 连接管理器
    包含错误处理、重连逻辑和状态监控
    """

    def __init__(self):
        self.active_connections: Dict[WebSocket, Dict] = {}
        self.channel_subscriptions: Dict[str, Set[WebSocket]] = {}
        self.connection_errors: Dict[WebSocket, list] = {}  # Track errors per connection

        # Circuit breaker for data pushing
        self.data_pusher_breaker = get_circuit_breaker(
            "data-pusher",
            CircuitBreakerConfig(failure_threshold=3, timeout=30.0)
        )

    async def connect(self, websocket: WebSocket):
        """接受新的 WebSocket 连接 - 带错误处理"""
        try:
            await websocket.accept()
            self.active_connections[websocket] = {
                "subscriptions": set(),
                "last_pong": datetime.now(),
                "connected_at": datetime.now(),
                "error_count": 0
            }
            self.connection_errors[websocket] = []
            logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")

        except Exception as e:
            cba_error = handle_exception(e, extra_context={"action": "websocket_accept"})
            logger.error(f"Failed to accept WebSocket connection: {cba_error.user_message}")
            # Try to close the connection if it was partially opened
            try:
                await websocket.close(code=1011, reason="Connection failed")
            except:
                pass
            raise

    def disconnect(self, websocket: WebSocket, reason: str = "Client disconnected"):
        """断开 WebSocket 连接 - 清理资源"""
        if websocket in self.active_connections:
            subscriptions = self.active_connections[websocket]["subscriptions"]
            for channel in subscriptions:
                if channel in self.channel_subscriptions:
                    self.channel_subscriptions[channel].discard(websocket)
                    if not self.channel_subscriptions[channel]:
                        del self.channel_subscriptions[channel]

            del self.active_connections[websocket]
            if websocket in self.connection_errors:
                error_count = len(self.connection_errors[websocket])
                del self.connection_errors[websocket]

            logger.info(
                f"WebSocket disconnected: {reason}. "
                f"Total: {len(self.active_connections)}, "
                f"Errors: {error_count}"
            )

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息 - 带错误处理和重试"""
        if websocket not in self.active_connections:
            logger.warning("Attempted to send message to disconnected websocket")
            return

        retry_config = RetryConfig(max_attempts=2, base_delay=0.5)
        retry_manager = RetryManager(retry_config)

        async def _send():
            await websocket.send_text(message)

        try:
            await retry_manager.retry_async(_send)
        except Exception as e:
            cba_error = handle_exception(
                e,
                extra_context={"action": "send_personal_message", "message_length": len(message)}
            )
            self._track_error(websocket, cba_error)

            # If still can't send, disconnect
            if websocket in self.active_connections:
                self.disconnect(websocket, reason=f"Send failed: {cba_error.user_message}")

    async def broadcast(self, message: str, channel: str):
        """广播消息到频道订阅者 - 带错误处理"""
        if channel not in self.channel_subscriptions:
            return

        try:
            message_dict = json.loads(message)
            message_dict["timestamp"] = datetime.now().isoformat()
            message_json = json.dumps(message_dict)
        except json.JSONDecodeError:
            message_json = message

        disconnected = set()
        success_count = 0
        error_count = 0

        for connection in self.channel_subscriptions[channel]:
            try:
                await connection.send_text(message_json)
                success_count += 1
            except Exception as e:
                error_count += 1
                cba_error = handle_exception(
                    e,
                    extra_context={"channel": channel, "action": "broadcast"}
                )
                self._track_error(connection, cba_error)
                disconnected.add(connection)

        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn, reason="Broadcast failed")

        if error_count > 0:
            logger.warning(
                f"Broadcast to {channel}: {success_count} success, "
                f"{error_count} errors, {len(disconnected)} disconnected"
            )

    async def ping_all(self):
        """Ping 所有连接 - 清理死连接"""
        now = datetime.now()
        disconnected = set()

        for websocket, info in self.active_connections.items():
            # Check for timeout (60 seconds without pong)
            if (now - info["last_pong"]).seconds > 60:
                logger.info(f"WebSocket timeout, disconnecting")
                disconnected.add(websocket)
                continue

            # Send ping with error handling
            try:
                await websocket.send_text(json.dumps({"type": "ping"}))
            except Exception:
                disconnected.add(websocket)

        for conn in disconnected:
            self.disconnect(conn, reason="Ping failed or timeout")

        if disconnected:
            logger.info(f"Cleaned up {len(disconnected)} stale connections")

    def subscribe(self, websocket: WebSocket, channel: str):
        """订阅频道"""
        if websocket in self.active_connections:
            self.active_connections[websocket]["subscriptions"].add(channel)
            if channel not in self.channel_subscriptions:
                self.channel_subscriptions[channel] = set()
            self.channel_subscriptions[channel].add(websocket)
            logger.info(
                f"Subscribed to {channel}. "
                f"Total subscribers: {len(self.channel_subscriptions.get(channel, []))}"
            )

    def unsubscribe(self, websocket: WebSocket, channel: str):
        """取消订阅频道"""
        if websocket in self.active_connections:
            self.active_connections[websocket]["subscriptions"].discard(channel)
            if channel in self.channel_subscriptions:
                self.channel_subscriptions[channel].discard(websocket)
                if not self.channel_subscriptions[channel]:
                    del self.channel_subscriptions[channel]
            logger.info(f"Unsubscribed from {channel}")

    def _track_error(self, websocket: WebSocket, error):
        """跟踪连接错误"""
        if websocket in self.active_connections:
            self.active_connections[websocket]["error_count"] += 1
        if websocket in self.connection_errors:
            self.connection_errors[websocket].append({
                "timestamp": datetime.now().isoformat(),
                "error": str(error),
                "category": error.category.value if hasattr(error, 'category') else 'unknown'
            })

    def get_stats(self) -> dict:
        """获取连接统计"""
        total_errors = sum(len(errors) for errors in self.connection_errors.values())

        return {
            "active_connections": len(self.active_connections),
            "total_subscriptions": sum(
                len(info["subscriptions"]) for info in self.active_connections.values()
            ),
            "channels": {
                channel: len(subscribers)
                for channel, subscribers in self.channel_subscriptions.items()
            },
            "total_errors": total_errors,
            "data_pusher_breaker": self.data_pusher_breaker.get_stats()
        }


async def enhanced_data_pusher(manager: EnhancedConnectionManager):
    """
    增强的数据推送后端任务
    包含断路器保护和错误恢复
    """
    while True:
        try:
            # Use circuit breaker to protect data pushing
            await manager.data_pusher_breaker.call_async(_push_data, manager)

            await asyncio.sleep(15)
            await manager.ping_all()

        except Exception as e:
            cba_error = handle_exception(e, extra_context={"task": "data_pusher"})
            logger.error(f"Error in data pusher: {cba_error.user_message}")
            await asyncio.sleep(5)  # Wait before retry


async def _push_data(manager: EnhancedConnectionManager):
    """实际的数据推送逻辑"""
    from main_v2 import DataGenerator

    strategy_data = DataGenerator.generate_strategy_data()
    await manager.broadcast(
        json.dumps({"type": "update", "channel": "strategy_performance", "payload": strategy_data}),
        "strategy_performance"
    )

    market_data = DataGenerator.generate_market_data()
    await manager.broadcast(
        json.dumps({"type": "data", "channel": "market_data", "payload": market_data}),
        "market_data"
    )


def handle_websocket_message(websocket: WebSocket, data: str, manager: EnhancedConnectionManager):
    """
    处理 WebSocket 消息 - 带错误处理

    Args:
        websocket: WebSocket 连接
        data: 接收到的消息数据
        manager: 连接管理器
    """
    try:
        message = json.loads(data)

        if message.get("type") == "subscribe":
            channel = message.get("channel")
            if channel:
                manager.subscribe(websocket, channel)
                # Send confirmation with error handling
                try:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "channel": channel,
                            "message": f"Successfully subscribed to {channel}"
                        }),
                        websocket
                    )
                except Exception as e:
                    logger.error(f"Failed to send subscription confirmation: {e}")

        elif message.get("type") == "unsubscribe":
            channel = message.get("channel")
            if channel:
                manager.unsubscribe(websocket, channel)

        elif message.get("type") == "pong":
            if websocket in manager.active_connections:
                manager.active_connections[websocket]["last_pong"] = datetime.now()

    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON message from WebSocket: {data[:100]}")
        try:
            await manager.send_personal_message(
                json.dumps({
                    "type": "error",
                    "message": "Invalid message format"
                }),
                websocket
            )
        except:
            pass

    except Exception as e:
        cba_error = handle_exception(e, extra_context={"message_type": "websocket_message"})
        logger.error(f"Error handling WebSocket message: {cba_error.user_message}")


# 替换 main_v2.py 中的 WebSocket 端点
async def enhanced_websocket_endpoint(websocket: WebSocket, manager: EnhancedConnectionManager):
    """
    增强的 WebSocket 端点 - 包含完整的错误处理

    Usage in main_v2.py:
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await enhanced_websocket_endpoint(websocket, manager)
    """
    try:
        await manager.connect(websocket)

        while True:
            data = await websocket.receive_text()
            handle_websocket_message(websocket, data, manager)

    except WebSocketDisconnect:
        manager.disconnect(websocket, reason="Client disconnected")
    except Exception as e:
        cba_error = handle_exception(e, extra_context={"action": "websocket_receive"})
        logger.error(f"WebSocket error: {cba_error.user_message}")
        manager.disconnect(websocket, reason=f"Error: {cba_error.user_message}")
