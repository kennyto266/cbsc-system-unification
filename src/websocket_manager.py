from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger('quant_system')

class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            'market_data': set(),
            'strategy_signals': set(),
            'system_status': set()
        }
        self.background_tasks = set()

    async def connect(self, websocket: WebSocket, channel: str = 'market_data'):
        """连接到指定频道"""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()

        self.active_connections[channel].add(websocket)
        logger.info(f"WebSocket connected to channel: {channel}")

        try:
            while True:
                # 保持连接活跃，等待客户端消息
                data = await websocket.receive_text()
                # 可以处理客户端发送的消息
                await self.handle_client_message(channel, websocket, data)

        except WebSocketDisconnect:
            self.disconnect(websocket, channel)

    def disconnect(self, websocket: WebSocket, channel: str):
        """断开连接"""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            logger.info(f"WebSocket disconnected from channel: {channel}")

    async def handle_client_message(self, channel: str, websocket: WebSocket, message: str):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            # 处理订阅请求等
            if data.get('type') == 'subscribe':
                # 可以添加更多频道订阅逻辑
                pass
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON message from client: {message}")

    async def broadcast(self, channel: str, message: Dict):
        """广播消息到指定频道"""
        if channel not in self.active_connections:
            return

        # 添加时间戳
        message['timestamp'] = datetime.utcnow().isoformat()

        disconnected = set()
        for websocket in self.active_connections[channel]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to websocket: {e}")
                disconnected.add(websocket)

        # 清理断开的连接
        for websocket in disconnected:
            self.disconnect(websocket, channel)

    async def send_market_data(self, symbol: str, data: Dict):
        """发送市场数据"""
        message = {
            'type': 'market_data',
            'symbol': symbol,
            'data': data
        }
        await self.broadcast('market_data', message)

    async def send_strategy_signal(self, signal: Dict):
        """发送策略信号"""
        message = {
            'type': 'strategy_signal',
            'signal': signal
        }
        await self.broadcast('strategy_signals', message)

    async def send_system_status(self, status: Dict):
        """发送系统状态"""
        message = {
            'type': 'system_status',
            'status': status
        }
        await self.broadcast('system_status', message)

    async def start_realtime_updates(self):
        """启动实时更新任务"""
        task = asyncio.create_task(self._realtime_update_loop())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def _realtime_update_loop(self):
        """实时更新循环"""
        while True:
            try:
                # 发送系统状态更新
                status = {
                    'active_connections': {
                        channel: len(connections)
                        for channel, connections in self.active_connections.items()
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
                await self.send_system_status(status)

                # 每30秒发送一次状态更新
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Realtime update loop error: {e}")
                await asyncio.sleep(5)  # 出错后等待5秒重试

# 全局实例
ws_manager = WebSocketManager()