"""
WebSocket连接管理器

负责管理WebSocket连接和实时数据推送
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.websocket_manager")
        self.active_connections: List[WebSocket] = []
        self.connection_data: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket) -> None:
        """接受新的WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_data[websocket] = {
            "connected_at": datetime.now(),
            "last_ping": datetime.now(),
            "subscriptions": []
        }
        self.logger.info(f"WebSocket连接已建立，当前连接数: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            if websocket in self.connection_data:
                del self.connection_data[websocket]
            self.logger.info(f"WebSocket连接已断开，当前连接数: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """发送个人消息"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            self.logger.error(f"发送个人消息失败: {e}")
            await self.disconnect(websocket)
    
    async def broadcast(self, message: str) -> None:
        """广播消息给所有连接的客户端"""
        if not self.active_connections:
            return
        
        disconnected = []
        for websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                self.logger.error(f"广播消息失败: {e}")
                disconnected.append(websocket)
        
        # 清理断开的连接
        for websocket in disconnected:
            await self.disconnect(websocket)
    
    async def send_agent_update(self, agent_id: str, data: Dict[str, Any]) -> None:
        """发送Agent更新数据"""
        message = json.dumps({
            "type": "agent_update",
            "agent_id": agent_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        await self.broadcast(message)
    
    async def send_system_alert(self, alert_type: str, message: str, severity: str = "info") -> None:
        """发送系统告警"""
        alert_data = {
            "type": "system_alert",
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(json.dumps(alert_data))
    
    async def send_performance_data(self, performance_data: Dict[str, Any]) -> None:
        """发送性能数据"""
        message = json.dumps({
            "type": "performance_update",
            "data": performance_data,
            "timestamp": datetime.now().isoformat()
        })
        await self.broadcast(message)
    
    async def handle_client_message(self, websocket: WebSocket, message: str) -> None:
        """处理客户端消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                await self._handle_ping(websocket, data)
            elif message_type == "subscribe":
                await self._handle_subscribe(websocket, data)
            elif message_type == "unsubscribe":
                await self._handle_unsubscribe(websocket, data)
            else:
                self.logger.warning(f"未知消息类型: {message_type}")
                
        except json.JSONDecodeError:
            self.logger.error("无效的JSON消息")
        except Exception as e:
            self.logger.error(f"处理客户端消息失败: {e}")
    
    async def _handle_ping(self, websocket: WebSocket, data: Dict[str, Any]) -> None:
        """处理ping消息"""
        if websocket in self.connection_data:
            self.connection_data[websocket]["last_ping"] = datetime.now()
        
        pong_response = json.dumps({
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        })
        await self.send_personal_message(pong_response, websocket)
    
    async def _handle_subscribe(self, websocket: WebSocket, data: Dict[str, Any]) -> None:
        """处理订阅消息"""
        subscription = data.get("subscription")
        if subscription and websocket in self.connection_data:
            if subscription not in self.connection_data[websocket]["subscriptions"]:
                self.connection_data[websocket]["subscriptions"].append(subscription)
                self.logger.info(f"客户端订阅: {subscription}")
    
    async def _handle_unsubscribe(self, websocket: WebSocket, data: Dict[str, Any]) -> None:
        """处理取消订阅消息"""
        subscription = data.get("subscription")
        if subscription and websocket in self.connection_data:
            if subscription in self.connection_data[websocket]["subscriptions"]:
                self.connection_data[websocket]["subscriptions"].remove(subscription)
                self.logger.info(f"客户端取消订阅: {subscription}")
    
    async def cleanup_stale_connections(self) -> None:
        """清理过期的连接"""
        current_time = datetime.now()
        stale_connections = []
        
        for websocket, data in self.connection_data.items():
            # 如果超过5分钟没有ping，认为连接已过期
            if (current_time - data["last_ping"]).total_seconds() > 300:
                stale_connections.append(websocket)
        
        for websocket in stale_connections:
            await self.disconnect(websocket)
            self.logger.info("清理过期连接")
    
    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """获取连接信息"""
        info = []
        for websocket, data in self.connection_data.items():
            info.append({
                "connected_at": data["connected_at"].isoformat(),
                "last_ping": data["last_ping"].isoformat(),
                "subscriptions": data["subscriptions"]
            })
        return info
    
    async def start_heartbeat_task(self) -> None:
        """启动心跳任务"""
        while True:
            try:
                await self.cleanup_stale_connections()
                await asyncio.sleep(60)  # 每分钟检查一次
            except Exception as e:
                self.logger.error(f"心跳任务异常: {e}")
                await asyncio.sleep(60)