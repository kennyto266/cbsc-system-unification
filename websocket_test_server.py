"""
簡化的WebSocket測試服務器
Simplified WebSocket Test Server for Real-time Data
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime
from typing import Dict, Set
import random

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleWebSocketServer:
    def __init__(self):
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.running = True

    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """註冊新的客戶端"""
        self.clients.add(websocket)
        logger.info(f"客戶端已連接。當前連接數: {len(self.clients)}")

        try:
            # 發送初始狀態
            await self.send_initial_state(websocket)

            # 處理客戶端消息
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    logger.warning(f"收到無效的JSON消息: {message}")
                except Exception as e:
                    logger.error(f"處理消息時出錯: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("客戶端斷開連接")
        finally:
            self.clients.discard(websocket)
            logger.info(f"客戶端已移除。當前連接數: {len(self.clients)}")

    async def handle_message(self, websocket, data):
        """處理客戶端消息"""
        message_type = data.get('type')

        if message_type == 'subscribe':
            channel = data.get('data', {}).get('channel')
            logger.info(f"客戶端訂閱頻道: {channel}")
            await websocket.send(json.dumps({
                'type': 'subscription_confirmed',
                'channel': channel,
                'timestamp': datetime.now().isoformat()
            }))
        elif message_type == 'heartbeat':
            await websocket.send(json.dumps({
                'type': 'heartbeat_response',
                'timestamp': datetime.now().isoformat()
            }))
        elif message_type == 'request_state':
            await self.send_initial_state(websocket)

    async def send_initial_state(self, websocket):
        """發送初始狀態"""
        mock_strategies = self.generate_mock_strategies()

        initial_state = {
            'type': 'initial_state',
            'data': {
                'strategies': mock_strategies,
                'system_info': {
                    'total_strategies': len(mock_strategies),
                    'server_time': datetime.now().isoformat(),
                    'version': '1.0.0'
                }
            },
            'timestamp': datetime.now().isoformat()
        }

        await websocket.send(json.dumps(initial_state))

    def generate_mock_strategies(self):
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
            for j in range(random.randint(1, 3)):
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

    async def broadcast(self, message):
        """廣播消息給所有客戶端"""
        if self.clients:
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )

    async def simulate_data_updates(self):
        """模擬實時數據更新"""
        while self.running:
            try:
                await asyncio.sleep(random.uniform(5, 15))

                if not self.clients:
                    continue

                # 模擬策略性能更新
                if random.random() < 0.7:  # 70% 機率更新性能
                    updated_strategies = []
                    for _ in range(random.randint(1, 3)):
                        strategy_id = f"strategy_{random.randint(1, 10)}"
                        updated_strategies.append({
                            'id': strategy_id,
                            'annual_return': round(random.uniform(0.05, 0.35), 4),
                            'sharpe_ratio': round(random.uniform(0.5, 3.0), 2),
                            'win_rate': round(random.uniform(0.4, 0.8), 3),
                            'max_drawdown': round(random.uniform(0.02, 0.18), 4),
                            'last_updated': datetime.now().isoformat()
                        })

                    performance_message = {
                        'type': 'performance_update',
                        'data': {
                            'updated_strategies': updated_strategies,
                            'update_count': len(updated_strategies)
                        },
                        'timestamp': datetime.now().isoformat()
                    }
                    await self.broadcast(json.dumps(performance_message))

                # 模擬交易信號
                if random.random() < 0.5:  # 50% 機率發送信號
                    signals = {}
                    categories = ['core_cbsc_technical', 'multi_factor_model', 'core_cbsc_sentiment']

                    for category in random.sample(categories, random.randint(1, 2)):
                        signal_types = ['BUY', 'SELL', 'HOLD']
                        signals[category] = {
                            'signal': random.choice(signal_types),
                            'confidence': round(random.uniform(0.6, 1.0), 2),
                            'timestamp': datetime.now().isoformat(),
                            'strength': round(random.uniform(0.5, 1.0), 2)
                        }

                    signals_message = {
                        'type': 'signals_update',
                        'data': signals,
                        'timestamp': datetime.now().isoformat()
                    }
                    await self.broadcast(json.dumps(signals_message))

                # 模擬系統健康狀態
                if random.random() < 0.3:  # 30% 機率更新系統狀態
                    health_data = {
                        'active_connections': len(self.clients),
                        'total_strategies': 15,
                        'memory_usage': f"{random.uniform(30, 70):.1f}%",
                        'cpu_usage': f"{random.uniform(10, 40):.1f}%",
                        'last_update': datetime.now().isoformat()
                    }

                    health_message = {
                        'type': 'system_health',
                        'data': health_data,
                        'timestamp': datetime.now().isoformat()
                    }
                    await self.broadcast(json.dumps(health_message))

            except Exception as e:
                logger.error(f"模擬數據更新時出錯: {e}")
                await asyncio.sleep(5)

    async def stop(self):
        """停止服務器"""
        self.running = False

async def main():
    """主函數"""
    server = SimpleWebSocketServer()

    # 啟動數據模擬任務
    simulation_task = asyncio.create_task(server.simulate_data_updates())

    try:
        # 啟動WebSocket服務器
        logger.info("🚀 啟動WebSocket測試服務器...")
        logger.info("📡 WebSocket地址: ws://localhost:3004")

        async with websockets.serve(server.register, "localhost", 3004):
            logger.info("✅ WebSocket服務器已啟動")
            await asyncio.Future()  # 運行直到被手動停止

    except KeyboardInterrupt:
        logger.info("👋 收到中斷信號，正在關閉服務器...")
    except Exception as e:
        logger.error(f"❌ 服務器啟動失敗: {e}")
    finally:
        server.stop()
        simulation_task.cancel()
        logger.info("✅ 服務器已關閉")

if __name__ == "__main__":
    asyncio.run(main())