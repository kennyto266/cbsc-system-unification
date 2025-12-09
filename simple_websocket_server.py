#!/usr/bin/env python3
import asyncio
import json
import random
from datetime import datetime
import websockets

# 模拟策略数据
def generate_strategy_data():
    strategies = ['DirectRSI', 'SentimentMomentum', 'CompositeIndex', 'VolatilityAdjusted']
    return {
        'timestamp': datetime.now().isoformat(),
        'strategies': [
            {
                'name': strategy,
                'signal': random.choice(['BUY', 'SELL', 'HOLD']),
                'strength': round(random.uniform(0.3, 1.0), 2),
                'confidence': round(random.uniform(0.6, 0.95), 2),
                'performance': {
                    'sharpe_ratio': round(random.uniform(0.8, 2.5), 2),
                    'max_drawdown': round(random.uniform(-0.15, -0.02), 3),
                    'win_rate': round(random.uniform(0.45, 0.75), 2)
                }
            }
            for strategy in strategies
        ]
    }

async def websocket_handler(websocket):
    print(f'New WebSocket connection: {websocket.remote_address}')

    try:
        # 发送欢迎消息
        welcome_msg = {
            'type': 'welcome',
            'message': 'CBSC WebSocket Server connected successfully!',
            'timestamp': datetime.now().isoformat()
        }
        await websocket.send(json.dumps(welcome_msg))

        # 持续发送数据
        while True:
            data = generate_strategy_data()
            await websocket.send(json.dumps(data))
            await asyncio.sleep(2)  # 每2秒发送一次数据

    except websockets.exceptions.ConnectionClosed:
        print(f'WebSocket connection closed: {websocket.remote_address}')
    except Exception as e:
        print(f'WebSocket error: {e}')
    finally:
        print(f'Connection handling completed: {websocket.remote_address}')

async def main():
    print("Starting CBSC WebSocket Server on port 3005...")
    server = await websockets.serve(websocket_handler, "localhost", 3005)
    print("WebSocket server started, listening on ws://localhost:3005")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())