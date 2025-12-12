"""
FastAPI WebSocket连接池集成
FastAPI WebSocket Pool Integration

提供与FastAPI的WebSocket集成，包括：
- WebSocket路由处理器
- 身份验证和授权
- 请求验证和错误处理
- 与现有API系统的集成
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import (
    WebSocket, WebSocketDisconnect, Depends, HTTPException, status,
    Query, Path, Header
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.requests import Request
from starlette.websockets import WebSocketState
import jwt
from pydantic import BaseModel, validator

from ...services.websocket_pool import (
    WebSocketConnectionPool, ConnectionPoolConfig, MessageType, get_connection_pool
)

logger = logging.getLogger(__name__)


class WebSocketAuthError(Exception):
    """WebSocket认证错误"""
    pass


class WebSocketValidationError(Exception):
    """WebSocket验证错误"""
    pass


class ConnectionRequest(BaseModel):
    """连接请求模型"""
    channel: str = "default"
    strategy_ids: Optional[List[str]] = None
    subscriptions: Optional[List[str]] = None

    @validator('channel')
    def validate_channel(cls, v):
        allowed_channels = [
            'default', 'strategies', 'market_data', 'notifications',
            'performance', 'signals', 'system', 'realtime'
        ]
        if v not in allowed_channels:
            raise ValueError(f"Channel must be one of: {allowed_channels}")
        return v


class MessageRequest(BaseModel):
    """消息请求模型"""
    type: str
    data: Dict[str, Any]
    target: Optional[str] = None
    timestamp: Optional[datetime] = None

    @validator('type')
    def validate_type(cls, v):
        allowed_types = ['subscribe', 'unsubscribe', 'ping', 'data', 'broadcast']
        if v not in allowed_types:
            raise ValueError(f"Type must be one of: {allowed_types}")
        return v


class WebSocketPoolManager:
    """
    WebSocket连接池管理器
    负责处理WebSocket连接的生命周期和消息处理
    """

    def __init__(self, pool: Optional[WebSocketConnectionPool] = None):
        self.pool = pool or get_connection_pool()
        self.jwt_secret = "your-secret-key"  # 从配置获取
        self.jwt_algorithm = "HS256"

        # 添加事件处理器
        self.pool.add_event_handler("connection_added", self._on_connection_added)
        self.pool.add_event_handler("connection_removed", self._on_connection_removed)

    async def authenticate_websocket(
        self,
        websocket: WebSocket,
        token: str,
        authorization: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        认证WebSocket连接
        """
        try:
            # 从Authorization header或query parameter获取token
            if authorization and authorization.startswith("Bearer "):
                token = authorization.split(" ")[1]

            if not token:
                raise WebSocketAuthError("No authentication token provided")

            # 验证JWT token
            try:
                payload = jwt.decode(
                    token,
                    self.jwt_secret,
                    algorithms=[self.jwt_algorithm]
                )
            except jwt.ExpiredSignatureError:
                raise WebSocketAuthError("Token has expired")
            except jwt.InvalidTokenError as e:
                raise WebSocketAuthError(f"Invalid token: {str(e)}")

            # 验证用户
            user_id = payload.get("user_id")
            if not user_id:
                raise WebSocketAuthError("Invalid user in token")

            return {
                "user_id": user_id,
                "username": payload.get("username"),
                "permissions": payload.get("permissions", []),
                "is_authenticated": True
            }

        except WebSocketAuthError:
            raise
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            raise WebSocketAuthError("Authentication failed")

    async def handle_websocket_connection(
        self,
        websocket: WebSocket,
        connection_request: ConnectionRequest,
        client_info: Dict[str, Any]
    ) -> str:
        """
        处理WebSocket连接
        """
        try:
            # Accept WebSocket connection
            await websocket.accept()

            # Add connection to pool
            success, connection_id = await self.pool.add_connection(
                websocket=websocket,
                user_id=client_info["user_id"],
                client_ip=client_info.get("client_ip", "unknown"),
                user_agent=client_info.get("user_agent", ""),
                channel=connection_request.channel,
                strategy_ids=connection_request.strategy_ids
            )

            if not success:
                await websocket.close(code=4000, reason="Connection rejected")
                raise WebSocketValidationError("Failed to add connection to pool")

            # Send welcome message
            welcome_message = {
                "type": "connection_established",
                "data": {
                    "connection_id": connection_id,
                    "channel": connection_request.channel,
                    "user_id": client_info["user_id"],
                    "server_time": datetime.now().isoformat()
                }
            }
            await self.pool.send_message(connection_id, welcome_message)

            # Handle subscriptions
            if connection_request.subscriptions:
                for subscription in connection_request.subscriptions:
                    await self.pool.subscribe_to_channel(connection_id, subscription)

            logger.info(f"WebSocket connection established: {connection_id}")

            return connection_id

        except Exception as e:
            logger.error(f"Failed to handle WebSocket connection: {e}")
            await websocket.close(code=4000, reason=str(e))
            raise

    async def handle_client_message(
        self,
        connection_id: str,
        message_data: Dict[str, Any]
    ):
        """
        处理客户端消息
        """
        try:
            # Validate message
            message_request = MessageRequest(**message_data)

            # Handle different message types
            if message_request.type == "ping":
                await self._handle_ping(connection_id)

            elif message_request.type == "subscribe":
                await self._handle_subscribe(connection_id, message_request)

            elif message_request.type == "unsubscribe":
                await self._handle_unsubscribe(connection_id, message_request)

            elif message_request.type == "data":
                await self._handle_data_message(connection_id, message_request)

            elif message_request.type == "broadcast":
                await self._handle_broadcast(connection_id, message_request)

            else:
                await self._send_error(connection_id, f"Unknown message type: {message_request.type}")

        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            await self._send_error(connection_id, str(e))

    async def _handle_ping(self, connection_id: str):
        """
        处理ping消息
        """
        pong_message = {
            "type": "pong",
            "data": {
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.pool.send_message(connection_id, pong_message)

    async def _handle_subscribe(
        self,
        connection_id: str,
        message: MessageRequest
    ):
        """
        处理订阅请求
        """
        if not message.target:
            await self._send_error(connection_id, "Subscription target is required")
            return

        success = await self.pool.subscribe_to_channel(connection_id, message.target)

        if success:
            response = {
                "type": "subscription_confirmed",
                "data": {
                    "target": message.target,
                    "timestamp": datetime.now().isoformat()
                }
            }
            await self.pool.send_message(connection_id, response)
        else:
            await self._send_error(connection_id, f"Failed to subscribe to {message.target}")

    async def _handle_unsubscribe(
        self,
        connection_id: str,
        message: MessageRequest
    ):
        """
        处理取消订阅请求
        """
        if not message.target:
            await self._send_error(connection_id, "Unsubscription target is required")
            return

        success = await self.pool.unsubscribe_from_channel(connection_id, message.target)

        if success:
            response = {
                "type": "unsubscription_confirmed",
                "data": {
                    "target": message.target,
                    "timestamp": datetime.now().isoformat()
                }
            }
            await self.pool.send_message(connection_id, response)
        else:
            await self._send_error(connection_id, f"Failed to unsubscribe from {message.target}")

    async def _handle_data_message(
        self,
        connection_id: str,
        message: MessageRequest
    ):
        """
        处理数据消息
        """
        # 这里可以实现自定义的数据处理逻辑
        # 例如：策略参数更新、交易指令等

        connection_info = self.pool.connections.get(connection_id)
        if not connection_info:
            return

        # Log data message for monitoring
        logger.debug(f"Data message received from {connection_id}", extra={
            "user_id": connection_info.user_id,
            "message_size": len(str(message.data))
        })

        # Echo back for debugging (optional)
        response = {
            "type": "data_received",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "size": len(str(message.data))
            }
        }
        await self.pool.send_message(connection_id, response)

    async def _handle_broadcast(
        self,
        connection_id: str,
        message: MessageRequest
    ):
        """
        处理广播消息（需要管理员权限）
        """
        connection_info = self.pool.connections.get(connection_id)
        if not connection_info:
            return

        # 检查权限（简化实现）
        # 实际应用中应该检查用户的广播权限
        if "admin" not in connection_info.subscriptions:
            await self._send_error(connection_id, "Insufficient permissions for broadcast")
            return

        target_channel = message.target or connection_info.channel
        await self.pool.broadcast_to_channel(target_channel, message.data)

    async def _send_error(self, connection_id: str, error_message: str):
        """
        发送错误消息
        """
        error_response = {
            "type": "error",
            "data": {
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.pool.send_message(connection_id, error_response)

    async def _on_connection_added(self, connection_info):
        """
        连接添加事件处理器
        """
        logger.info(f"New connection added: {connection_info.connection_id}")

        # 可以在这里触发其他业务逻辑
        # 例如：通知其他用户、更新在线状态等

    async def _on_connection_removed(self, connection_info):
        """
        连接移除事件处理器
        """
        logger.info(f"Connection removed: {connection_info.connection_id}")

        # 可以在这里触发其他业务逻辑
        # 例如：通知其他用户、更新在线状态等


# Global WebSocket pool manager
_pool_manager: Optional[WebSocketPoolManager] = None


def get_pool_manager() -> WebSocketPoolManager:
    """
    获取全局WebSocket池管理器
    """
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = WebSocketPoolManager()
    return _pool_manager


# WebSocket路由处理器
async def websocket_endpoint_handler(
    websocket: WebSocket,
    token: str = Query(..., description="Authentication token"),
    channel: str = Query("default", description="Channel name"),
    strategy_ids: Optional[str] = Query(None, description="Comma-separated strategy IDs"),
    authorization: Optional[str] = Header(None, description="Authorization header")
):
    """
    WebSocket端点处理器
    """
    pool_manager = get_pool_manager()
    connection_id = None

    try:
        # 获取客户端信息
        client_info = {
            "client_ip": websocket.client.host if websocket.client else "unknown",
            "user_agent": websocket.headers.get("user-agent", ""),
        }

        # 认证
        auth_info = await pool_manager.authenticate_websocket(
            websocket, token, authorization
        )
        client_info.update(auth_info)

        # 解析策略ID
        parsed_strategy_ids = None
        if strategy_ids:
            parsed_strategy_ids = [s.strip() for s in strategy_ids.split(",") if s.strip()]

        # 创建连接请求
        connection_request = ConnectionRequest(
            channel=channel,
            strategy_ids=parsed_strategy_ids
        )

        # 处理连接
        connection_id = await pool_manager.handle_websocket_connection(
            websocket, connection_request, client_info
        )

        # 监听客户端消息
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                message_data = json.loads(data)

                # 处理消息
                await pool_manager.handle_client_message(connection_id, message_data)

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {connection_id}")
                break
            except json.JSONDecodeError:
                await pool_manager._send_error(connection_id, "Invalid JSON format")
            except Exception as e:
                logger.error(f"Error in WebSocket message loop: {e}")
                await pool_manager._send_error(connection_id, "Internal server error")

    except WebSocketAuthError as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=4001, reason=str(e))

    except WebSocketValidationError as e:
        logger.warning(f"WebSocket validation failed: {e}")
        await websocket.close(code=4002, reason=str(e))

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected during handshake")

    except Exception as e:
        logger.error(f"Unexpected error in WebSocket handler: {e}")
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=4000, reason="Internal server error")

    finally:
        # 清理连接
        if connection_id:
            await pool_manager.pool.remove_connection(connection_id, "handler_cleanup")