"""
WebSocket服務器 - 提供實時數據推送功能
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass
import random

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConnectionInfo:
    """連接信息"""
    websocket: WebSocket
    client_id: str
    subscriptions: Set[str]
    connected_at: datetime
    last_ping: datetime

class WebSocketManager:
    """WebSocket連接管理器"""

    def __init__(self):
        # 活躍連接 {client_id: ConnectionInfo}
        self.active_connections: Dict[str, ConnectionInfo] = {}

        # 訂閱管理 {channel: Set[client_id]}
        self.channel_subscriptions: Dict[str, Set[str]] = {
            'strategy_updates': set(),
            'performance_updates': set(),
            'signals_updates': set(),
            'system_health': set()
        }

        # 模擬策略數據
        self.mock_strategies = self._generate_mock_strategies()

        # 運行狀態
        self.running = False

    def _generate_mock_strategies(self) -> List[Dict]:
        """生成模擬策略數據"""
        strategies = []
        categories = [
            'monthly_low_frequency',
            'multi_strategy_validation',
            'multi_factor_model',
            'core_cbsc_technical',
            'core_cbsc_sentiment',
            'core_cbsc_aggressive',
            'portfolio_optimization'
        ]

        for i, category in enumerate(categories):
            for j in range(random.randint(1, 4)):  # 每個類別1-4個策略
                strategy = {
                    'id': f"{category}_{j+1}",
                    'name': f"{category.replace('_', ' ').title()} Strategy {j+1}",
                    'category': category,
                    'subcategory': f'Type {(j % 3) + 1}',
                    'annual_return': round(0.08 + random.random() * 0.25, 4),
                    'sharpe_ratio': round(0.5 + random.random() * 2.5, 2),
                    'max_drawdown': round(0.05 + random.random() * 0.15, 4),
                    'win_rate': round(0.4 + random.random() * 0.5, 3),
                    'volatility': round(0.08 + random.random() * 0.2, 4),
                    'trading_frequency': random.choice(['monthly', 'daily', 'weekly']),
                    'risk_level': random.choice(['low', 'medium', 'high']),
                    'grade': random.choice(['A+', 'A', 'A-', 'B+', 'B']),
                    'description': f'Advanced {category} trading strategy with optimized parameters',
                    'last_updated': datetime.now().isoformat()
                }
                strategies.append(strategy)

        return strategies

    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """接受新的WebSocket連接"""
        try:
            await websocket.accept()

            connection_info = ConnectionInfo(
                websocket=websocket,
                client_id=client_id,
                subscriptions=set(),
                connected_at=datetime.now(),
                last_ping=datetime.now()
            )

            self.active_connections[client_id] = connection_info
            logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

            # 發送初始狀態
            await self._send_initial_state(client_id)

            return True

        except Exception as e:
            logger.error(f"Failed to accept connection from {client_id}: {e}")
            return False

    async def disconnect(self, client_id: str):
        """斷開WebSocket連接"""
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]

            # 從所有訂閱中移除
            for channel in connection.subscriptions:
                if channel in self.channel_subscriptions:
                    self.channel_subscriptions[channel].discard(client_id)

            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, client_id: str, message: Dict):
        """發送個人消息"""
        if client_id in self.active_connections:
            try:
                connection = self.active_connections[client_id]
                await connection.websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                await self.disconnect(client_id)

    async def subscribe(self, client_id: str, channel: str) -> bool:
        """訂閱頻道"""
        if client_id not in self.active_connections:
            return False

        if channel not in self.channel_subscriptions:
            return False

        self.active_connections[client_id].subscriptions.add(channel)
        self.channel_subscriptions[channel].add(client_id)

        logger.info(f"Client {client_id} subscribed to {channel}")
        return True

    async def unsubscribe(self, client_id: str, channel: str) -> bool:
        """取消訂閱頻道"""
        if client_id not in self.active_connections:
            return False

        self.active_connections[client_id].subscriptions.discard(channel)
        if channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].discard(client_id)

        logger.info(f"Client {client_id} unsubscribed from {channel}")
        return True

    async def _send_initial_state(self, client_id: str):
        """發送初始狀態"""
        try:
            initial_state = {
                'type': 'initial_state',
                'data': {
                    'strategies': self.mock_strategies,
                    'system_info': {
                        'total_strategies': len(self.mock_strategies),
                        'server_time': datetime.now().isoformat(),
                        'version': '1.0.0'
                    }
                },
                'timestamp': datetime.now().isoformat()
            }

            await self.send_personal_message(client_id, initial_state)

        except Exception as e:
            logger.error(f"Failed to send initial state to {client_id}: {e}")

    async def handle_message(self, client_id: str, message: Dict):
        """處理客戶端消息"""
        message_type = message.get('type')

        if message_type == 'subscribe':
            channel = message.get('data', {}).get('channel')
            if channel:
                await self.subscribe(client_id, channel)
                await self.send_personal_message(client_id, {
                    'type': 'subscription_confirmed',
                    'channel': channel,
                    'timestamp': datetime.now().isoformat()
                })

        elif message_type == 'unsubscribe':
            channel = message.get('data', {}).get('channel')
            if channel:
                await self.unsubscribe(client_id, channel)

        elif message_type == 'request_state':
            await self._send_initial_state(client_id)

        elif message_type == 'heartbeat':
            # 更新最後ping時間
            if client_id in self.active_connections:
                self.active_connections[client_id].last_ping = datetime.now()
                # 回應心跳
                await self.send_personal_message(client_id, {
                    'type': 'heartbeat_response',
                    'timestamp': datetime.now().isoformat()
                })

        else:
            logger.warning(f"Unknown message type: {message_type}")

    async def broadcast_to_channel(self, channel: str, message: Dict):
        """向特定頻道廣播消息"""
        if channel not in self.channel_subscriptions:
            return

        disconnected_clients = []

        for client_id in self.channel_subscriptions[channel].copy():
            try:
                await self.send_personal_message(client_id, message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {client_id}: {e}")
                disconnected_clients.append(client_id)

        # 清理斷開的連接
        for client_id in disconnected_clients:
            await self.disconnect(client_id)

    async def start_data_simulation(self):
        """啟動數據模擬"""
        self.running = True

        while self.running:
            try:
                # 模擬策略性能更新
                if len(self.channel_subscriptions['performance_updates']) > 0:
                    await self._simulate_performance_updates()

                # 模擬信號更新
                if len(self.channel_subscriptions['signals_updates']) > 0:
                    await self._simulate_signals_updates()

                # 模擬系統健康檢查
                if len(self.channel_subscriptions['system_health']) > 0:
                    await self._broadcast_system_health()

                # 每5-15秒更新一次
                await asyncio.sleep(random.uniform(5, 15))

            except Exception as e:
                logger.error(f"Error in data simulation: {e}")
                await asyncio.sleep(5)

    async def _simulate_performance_updates(self):
        """模擬性能更新"""
        # 隨機選擇1-3個策略進行更新
        updated_strategies = random.sample(
            self.mock_strategies,
            min(3, len(self.mock_strategies))
        )

        for strategy in updated_strategies:
            # 模擬小幅變動
            strategy['annual_return'] += random.uniform(-0.001, 0.001)
            strategy['sharpe_ratio'] += random.uniform(-0.01, 0.01)
            strategy['win_rate'] = max(0.1, min(0.9, strategy['win_rate'] + random.uniform(-0.01, 0.01)))
            strategy['last_updated'] = datetime.now().isoformat()

            # 保持在合理範圍內
            strategy['annual_return'] = max(-0.1, min(0.5, strategy['annual_return']))
            strategy['sharpe_ratio'] = max(-0.5, min(5.0, strategy['sharpe_ratio']))

        message = {
            'type': 'performance_update',
            'data': {
                'updated_strategies': updated_strategies,
                'update_count': len(updated_strategies)
            },
            'timestamp': datetime.now().isoformat()
        }

        await self.broadcast_to_channel('performance_updates', message)

    async def _simulate_signals_updates(self):
        """模擬交易信號更新"""
        signals = {}

        # 為每個策略類別生成信號
        for category in set(s['category'] for s in self.mock_strategies):
            signal_types = ['BUY', 'SELL', 'HOLD']
            signal = random.choice(signal_types)
            confidence = round(random.uniform(0.6, 1.0), 2)

            signals[category] = {
                'signal': signal,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'strength': round(random.uniform(0.5, 1.0), 2)
            }

        message = {
            'type': 'signals_update',
            'data': signals,
            'timestamp': datetime.now().isoformat()
        }

        await self.broadcast_to_channel('signals_updates', message)

    async def _broadcast_system_health(self):
        """廣播系統健康狀態"""
        health_data = {
            'active_connections': len(self.active_connections),
            'total_strategies': len(self.mock_strategies),
            'server_uptime': 'N/A',  # 實際應用中計算真實運行時間
            'memory_usage': f"{random.uniform(30, 70):.1f}%",
            'cpu_usage': f"{random.uniform(10, 40):.1f}%",
            'last_update': datetime.now().isoformat()
        }

        message = {
            'type': 'system_health',
            'data': health_data,
            'timestamp': datetime.now().isoformat()
        }

        await self.broadcast_to_channel('system_health', message)

    def stop_data_simulation(self):
        """停止數據模擬"""
        self.running = False

# 全局WebSocket管理器
websocket_manager = WebSocketManager()

# 獲取WebSocket管理器實例
def get_websocket_manager() -> WebSocketManager:
    return websocket_manager