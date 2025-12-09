#!/usr/bin/env python3
"""
Simplified System - WebSocket Server for Real-time Data
简化系统 - 实时数据WebSocket服务器

提供实时股票数据和技术指标的WebSocket接口
Provides WebSocket interface for real-time stock data and technical indicators
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Set, Any, Optional
from datetime import datetime
from dataclasses import asdict

import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed, WebSocketException

from .data_stream import RealTimeDataStreamer, get_streamer

logger = logging.getLogger(__name__)

class WebSocketConnection:
    """WebSocket连接封装"""

    def __init__(self, websocket: WebSocketServerProtocol, connection_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.subscribed_symbols: Set[str] = set()
        self.last_ping = time.time()
        self.message_count = 0
        self.created_at = datetime.now()
        self.is_authenticated = False

    async def send_message(self, message_type: str, data: Any) -> None:
        """发送消息"""
        try:
            message = {
                'type': message_type,
                'timestamp': datetime.now().isoformat(),
                'connection_id': self.connection_id,
                'data': data
            }
            await self.websocket.send(json.dumps(message))
            self.message_count += 1
        except (ConnectionClosed, WebSocketException) as e:
            logger.warning(f"Failed to send message to {self.connection_id}: {e}")
            raise

    def subscribe_symbol(self, symbol: str) -> None:
        """订阅股票代码"""
        self.subscribed_symbols.add(symbol)

    def unsubscribe_symbol(self, symbol: str) -> None:
        """取消订阅股票代码"""
        self.subscribed_symbols.discard(symbol)

    def get_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        return {
            'connection_id': self.connection_id,
            'subscribed_symbols': list(self.subscribed_symbols),
            'message_count': self.message_count,
            'created_at': self.created_at.isoformat(),
            'last_ping': self.last_ping,
            'is_authenticated': self.is_authenticated
        }

class WebSocketServer:
    """
    实时数据WebSocket服务器
    支持股票价格和技术指标的实时推送
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8002):
        self.host = host
        self.port = port
        self.streamer = get_streamer()
        self.connections: Dict[str, WebSocketConnection] = {}
        self.connection_counter = 0
        self.server = None
        self._running = False

        # 性能统计
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'start_time': None
        }

        logger.info(f"WebSocket server initialized on {host}:{port}")

    async def start(self) -> None:
        """启动WebSocket服务器"""
        if self._running:
            logger.warning("WebSocket server is already running")
            return

        self._running = True
        self.stats['start_time'] = datetime.now()

        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")

        # 启动WebSocket服务器
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10,
            max_size=10**7,  # 10MB max message size
            compression=None  # 禁用压缩以减少延迟
        )

        # 启动后台任务
        asyncio.create_task(self.connection_monitor())
        asyncio.create_task(self.broadcast_stats())

        logger.info(f"WebSocket server started successfully on ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        """停止WebSocket服务器"""
        if not self._running:
            return

        self._running = False

        # 关闭所有连接
        for connection in list(self.connections.values()):
            try:
                await connection.websocket.close()
            except Exception:
                pass

        # 停止服务器
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        logger.info("WebSocket server stopped")

    async def handle_client(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """
        处理客户端连接

        Args:
            websocket: WebSocket连接
            path: 连接路径
        """
        self.connection_counter += 1
        connection_id = f"conn_{self.connection_counter}_{int(time.time())}"

        # 创建连接对象
        connection = WebSocketConnection(websocket, connection_id)
        self.connections[connection_id] = connection
        self.stats['total_connections'] += 1
        self.stats['active_connections'] += 1

        logger.info(f"New WebSocket connection: {connection_id} from {websocket.remote_address}")

        try:
            # 发送欢迎消息
            await connection.send_message("welcome", {
                'message': 'Welcome to Simplified System Real-time Data Server',
                'server_version': '1.0.0',
                'supported_commands': ['subscribe', 'unsubscribe', 'get_data', 'get_stats']
            })

            # 处理客户端消息
            async for message in websocket:
                await self.handle_message(connection, message)

        except ConnectionClosed:
            logger.info(f"Client {connection_id} disconnected normally")
        except Exception as e:
            logger.error(f"Error handling client {connection_id}: {e}")
        finally:
            # 清理连接
            await self.cleanup_connection(connection_id)

    async def handle_message(self, connection: WebSocketConnection, message: str) -> None:
        """
        处理客户端消息

        Args:
            connection: WebSocket连接
            message: 客户端消息
        """
        try:
            data = json.loads(message)
            command = data.get('command')
            payload = data.get('payload', {})

            if command == 'ping':
                await connection.send_message('pong', {'timestamp': datetime.now().isoformat()})
                connection.last_ping = time.time()

            elif command == 'subscribe':
                await self.handle_subscribe(connection, payload)

            elif command == 'unsubscribe':
                await self.handle_unsubscribe(connection, payload)

            elif command == 'get_data':
                await self.handle_get_data(connection, payload)

            elif command == 'get_stats':
                await self.handle_get_stats(connection)

            elif command == 'get_symbols':
                await self.handle_get_symbols(connection)

            else:
                await connection.send_message('error', {'message': f'Unknown command: {command}'})

        except json.JSONDecodeError:
            await connection.send_message('error', {'message': 'Invalid JSON format'})
        except Exception as e:
            logger.error(f"Error handling message from {connection.connection_id}: {e}")
            await connection.send_message('error', {'message': 'Internal server error'})

    async def handle_subscribe(self, connection: WebSocketConnection, payload: Dict[str, Any]) -> None:
        """处理订阅请求"""
        symbols = payload.get('symbols', [])
        if isinstance(symbols, str):
            symbols = [symbols]

        subscribed_symbols = []
        for symbol in symbols:
            # 标准化股票代码格式
            symbol = symbol.upper()
            if not symbol.endswith('.HK'):
                symbol += '.HK'

            connection.subscribe_symbol(symbol)
            subscribed_symbols.append(symbol)

            # 订阅数据流
            self.streamer.subscribe(symbol, lambda data, conn=connection, sym=symbol:
                                 self.broadcast_to_connection(conn, 'price_update', data))

        await connection.send_message('subscribe_response', {
            'subscribed_symbols': subscribed_symbols,
            'total_subscriptions': len(connection.subscribed_symbols)
        })

        logger.info(f"Connection {connection.connection_id} subscribed to: {subscribed_symbols}")

    async def handle_unsubscribe(self, connection: WebSocketConnection, payload: Dict[str, Any]) -> None:
        """处理取消订阅请求"""
        symbols = payload.get('symbols', [])
        if isinstance(symbols, str):
            symbols = [symbols]

        unsubscribed_symbols = []
        for symbol in symbols:
            symbol = symbol.upper()
            if not symbol.endswith('.HK'):
                symbol += '.HK'

            connection.unsubscribe_symbol(symbol)
            unsubscribed_symbols.append(symbol)

        await connection.send_message('unsubscribe_response', {
            'unsubscribed_symbols': unsubscribed_symbols,
            'total_subscriptions': len(connection.subscribed_symbols)
        })

        logger.info(f"Connection {connection.connection_id} unsubscribed from: {unsubscribed_symbols}")

    async def handle_get_data(self, connection: WebSocketConnection, payload: Dict[str, Any]) -> None:
        """处理获取数据请求"""
        symbols = payload.get('symbols', list(connection.subscribed_symbols))
        include_indicators = payload.get('include_indicators', True)

        all_data = {}
        for symbol in symbols:
            symbol_data = {}

            # 获取最新价格数据
            tick = self.streamer.get_latest_tick(symbol)
            if tick:
                symbol_data['tick'] = tick.to_dict()

            # 获取技术指标
            if include_indicators:
                indicators = self.streamer.get_latest_indicators(symbol)
                if indicators:
                    symbol_data['indicators'] = asdict(indicators)
                    symbol_data['indicators']['timestamp'] = indicators.timestamp.isoformat()

            if symbol_data:
                all_data[symbol] = symbol_data

        await connection.send_message('data_response', {
            'symbols': all_data,
            'request_time': datetime.now().isoformat()
        })

    async def handle_get_stats(self, connection: WebSocketConnection) -> None:
        """处理获取统计信息请求"""
        streamer_stats = self.streamer.get_performance_stats()
        server_stats = self.get_server_stats()

        await connection.send_message('stats_response', {
            'streamer': streamer_stats,
            'server': server_stats,
            'connection': connection.get_info()
        })

    async def handle_get_symbols(self, connection: WebSocketConnection) -> None:
        """处理获取可用股票列表请求"""
        # 这里可以返回系统支持的股票列表
        # 目前返回一些常用的港股
        available_symbols = [
            '0700.HK',  # 腾讯
            '0941.HK',  # 中国移动
            '1299.HK',  # 友邦保险
            '0388.HK',  # 港交所
            '2318.HK',  # 中国平安
            '1398.HK',  # 工商银行
            '0005.HK',  # 汇丰控股
            '0939.HK',  # 建设银行
            '2628.HK',  # 中国人寿
            '0003.HK'   # 香港中旅
        ]

        await connection.send_message('symbols_response', {
            'available_symbols': available_symbols,
            'total_count': len(available_symbols)
        })

    async def broadcast_to_connection(self, connection: WebSocketConnection, message_type: str, data: Any) -> None:
        """向特定连接广播消息"""
        try:
            if connection.connection_id in self.connections:
                await connection.send_message(message_type, data)
                self.stats['messages_sent'] += 1
        except Exception as e:
            logger.warning(f"Failed to broadcast to {connection.connection_id}: {e}")

    async def broadcast_to_all(self, message_type: str, data: Any) -> None:
        """向所有连接广播消息"""
        message = {
            'type': message_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        # 并发发送给所有连接
        tasks = []
        for connection in list(self.connections.values()):
            task = asyncio.create_task(
                connection.websocket.send(json.dumps(message)),
                name=f"broadcast_{connection.connection_id}"
            )
            tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self.stats['messages_sent'] += len(tasks)

    async def cleanup_connection(self, connection_id: str) -> None:
        """清理连接"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]

            # 取消所有订阅
            for symbol in connection.subscribed_symbols:
                # 这里可以添加取消订阅数据流的逻辑
                pass

            # 删除连接
            del self.connections[connection_id]
            self.stats['active_connections'] -= 1

            logger.info(f"Cleaned up connection {connection_id}")

    async def connection_monitor(self) -> None:
        """连接监控任务"""
        logger.info("Starting connection monitor")

        while self._running:
            try:
                current_time = time.time()
                dead_connections = []

                for connection_id, connection in self.connections.items():
                    # 检查连接是否超时（60秒无活动）
                    if current_time - connection.last_ping > 60:
                        dead_connections.append(connection_id)

                # 清理死连接
                for connection_id in dead_connections:
                    logger.info(f"Removing dead connection: {connection_id}")
                    await self.cleanup_connection(connection_id)

                await asyncio.sleep(30)  # 每30秒检查一次

            except Exception as e:
                logger.error(f"Error in connection monitor: {e}")
                await asyncio.sleep(30)

    async def broadcast_stats(self) -> None:
        """定期广播服务器统计信息"""
        logger.info("Starting stats broadcaster")

        while self._running:
            try:
                server_stats = self.get_server_stats()
                streamer_stats = self.streamer.get_performance_stats()

                stats_message = {
                    'server': server_stats,
                    'streamer': streamer_stats
                }

                await self.broadcast_to_all('server_stats', stats_message)
                await asyncio.sleep(60)  # 每分钟广播一次

            except Exception as e:
                logger.error(f"Error broadcasting stats: {e}")
                await asyncio.sleep(60)

    def get_server_stats(self) -> Dict[str, Any]:
        """获取服务器统计信息"""
        uptime = None
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()

        return {
            **self.stats,
            'uptime_seconds': uptime,
            'host': self.host,
            'port': self.port,
            'active_connections': len(self.connections),
            'memory_usage': 'N/A'  # 可以添加内存使用情况
        }

    def get_connection_info(self) -> List[Dict[str, Any]]:
        """获取所有连接信息"""
        return [connection.get_info() for connection in self.connections.values()]

# 全局WebSocket服务器实例
_ws_server = None

def get_websocket_server() -> WebSocketServer:
    """获取全局WebSocket服务器实例"""
    global _ws_server
    if _ws_server is None:
        _ws_server = WebSocketServer()
    return _ws_server

if __name__ == "__main__":
    async def main():
        """测试WebSocket服务器"""
        # 启动数据流
        streamer = get_streamer()
        symbols = ["0700.hk", "0941.hk", "1398.hk"]
        await streamer.start_streaming(symbols)

        # 启动WebSocket服务器
        ws_server = get_websocket_server()
        await ws_server.start()

        try:
            logger.info("WebSocket server running. Press Ctrl+C to stop.")
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            await ws_server.stop()
            await streamer.stop_streaming()

    # 运行服务器
    asyncio.run(main())