"""
策略管理Dashboard - 实时服务

WebSocket连接管理，提供实时数据推送功能。
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any, List
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect


class RealtimeService:
    """实时服务管理器"""

    def __init__(self):
        self.logger = logging.getLogger("strategy_dashboard.realtime_service")
        self.active_connections: Set[WebSocket] = set()
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, metadata: Optional[Dict[str, Any]] = None):
        """建立WebSocket连接"""
        try:
            await websocket.accept()
            self.active_connections.add(websocket)

            if not metadata:
                metadata = {}

            metadata.update({
                "connected_at": datetime.now(),
                "subscriptions": set(),
                "last_activity": datetime.now(),
                "client_id": f"client_{len(self.active_connections)}_{int(datetime.now().timestamp())}"
            })

            self.connection_metadata[websocket] = metadata

            self.logger.info(f"WebSocket连接已建立，当前连接数: {len(self.active_connections)}")

            # 发送欢迎消息
            await self.send_personal_message({
                "type": "connection_established",
                "client_id": metadata["client_id"],
                "timestamp": datetime.now().isoformat(),
                "message": "连接已建立"
            }, websocket)

        except Exception as e:
            self.logger.error(f"建立WebSocket连接失败: {e}")
            raise

    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        if websocket in self.connection_metadata:
            client_id = self.connection_metadata[websocket].get("client_id", "unknown")
            del self.connection_metadata[websocket]

            self.logger.info(f"WebSocket连接已断开，客户端ID: {client_id}，当前连接数: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(json.dumps(message, default=str, ensure_ascii=False))

            # 更新最后活动时间
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["last_activity"] = datetime.now()

        except Exception as e:
            self.logger.error(f"发送个人消息失败: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any], message_type: str = "update"):
        """广播消息给所有连接"""
        if not self.active_connections:
            return

        message_data = {
            "type": message_type,
            "timestamp": datetime.now().isoformat(),
            "data": message
        }

        # 创建副本以避免在迭代过程中修改
        connections = list(self.active_connections)
        disconnected = []

        for connection in connections:
            try:
                await connection.send_text(json.dumps(message_data, default=str, ensure_ascii=False))

                # 更新最后活动时间
                if connection in self.connection_metadata:
                    self.connection_metadata[connection]["last_activity"] = datetime.now()

            except Exception as e:
                self.logger.warning(f"广播消息失败，可能连接已断开: {e}")
                disconnected.append(connection)

        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)

    async def send_strategy_update(self, strategy_data: Dict[str, Any]):
        """发送策略更新"""
        await self.broadcast(strategy_data, "strategy_update")

    async def send_performance_update(self, performance_data: Dict[str, Any]):
        """发送性能更新"""
        await self.broadcast(performance_data, "performance_update")

    async def send_system_status(self, status_data: Dict[str, Any]):
        """发送系统状态"""
        await self.broadcast(status_data, "system_status")

    async def subscribe_to_updates(self, websocket: WebSocket, subscription_types: List[str]):
        """订阅更新"""
        if websocket in self.connection_metadata:
            current_subscriptions = self.connection_metadata[websocket]["subscriptions"]
            current_subscriptions.update(subscription_types)

            await self.send_personal_message({
                "type": "subscription_confirmed",
                "subscriptions": list(current_subscriptions),
                "timestamp": datetime.now().isoformat()
            }, websocket)

    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.active_connections)

    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        connections_info = []
        for websocket, metadata in self.connection_metadata.items():
            connections_info.append({
                "client_id": metadata.get("client_id", "unknown"),
                "connected_at": metadata["connected_at"].isoformat(),
                "last_activity": metadata["last_activity"].isoformat(),
                "subscriptions": list(metadata["subscriptions"])
            })

        return {
            "total_connections": len(self.active_connections),
            "connections": connections_info
        }

    async def ping_all_connections(self):
        """检查所有连接状态"""
        ping_message = {
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        }

        connections = list(self.active_connections)
        disconnected = []

        for connection in connections:
            try:
                await connection.send_text(json.dumps(ping_message, default=str, ensure_ascii=False))
            except Exception as e:
                self.logger.warning(f"Ping失败，连接可能已断开: {e}")
                disconnected.append(connection)

        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)

        return len(disconnected)

    async def cleanup_inactive_connections(self, max_inactive_minutes: int = 30):
        """清理不活跃的连接"""
        current_time = datetime.now()
        disconnected = []

        for websocket, metadata in list(self.connection_metadata.items()):
            inactive_time = (current_time - metadata["last_activity"]).total_seconds() / 60

            if inactive_time > max_inactive_minutes:
                try:
                    await websocket.close()
                except:
                    pass
                finally:
                    self.disconnect(websocket)
                    disconnected.append(metadata.get("client_id", "unknown"))

        if disconnected:
            self.logger.info(f"清理了 {len(disconnected)} 个不活跃的连接")

        return len(disconnected)