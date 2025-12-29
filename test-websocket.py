#!/usr/bin/env python3
"""
測試 WebSocket 連接
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_websocket_connection():
    """測試 WebSocket 連接並訂閱數據"""
    uri = "ws://localhost:3004/ws"

    try:
        logger.info(f"Connecting to {uri}...")

        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected successfully!")

            # 訂閱策略表現數據
            subscribe_msg = {
                "type": "subscribe",
                "channel": "strategy_performance"
            }
            await websocket.send(json.dumps(subscribe_msg))
            logger.info("Subscribed to strategy_performance channel")

            # 設閱市場數據
            subscribe_msg = {
                "type": "subscribe",
                "channel": "market_data"
            }
            await websocket.send(json.dumps(subscribe_msg))
            logger.info("Subscribed to market_data channel")

            # 監聽消息
            message_count = 0
            try:
                async for message in websocket:
                    data = json.loads(message)
                    message_count += 1

                    if data.get("type") == "subscribed":
                        logger.info(f"✅ Subscription confirmed: {data.get('channel')}")
                    elif data.get("type") in ["data", "update"]:
                        channel = data.get("channel")
                        logger.info(f"📊 Received {channel} data (message #{message_count})")

                        # 顯示部分數據
                        payload = data.get("payload", {})
                        if channel == "strategy_performance" and "strategies" in payload:
                            strategies = payload["strategies"]
                            for strategy in strategies[:2]:  # 只顯示前兩個策略
                                logger.info(f"  - {strategy['name']}: Sharpe={strategy.get('sharpe_ratio', 0):.2f}, Return={strategy.get('total_return', 0)*100:.1f}%")

                        elif channel == "market_data" and "data" in payload:
                            stocks = payload["data"][:2]  # 只顯示前兩只股票
                            for stock in stocks:
                                logger.info(f"  - {stock['symbol']}: ${stock.get('price', 0):.2f} ({stock.get('change_percent', 0):+.2f}%)")

                    elif data.get("type") == "ping":
                        # 韐應心跳
                        pong_msg = {"type": "pong"}
                        await websocket.send(json.dumps(pong_msg))

                    # 接收 10 條消息後測試取消訂閱
                    if message_count == 10:
                        unsubscribe_msg = {
                            "type": "unsubscribe",
                            "channel": "market_data"
                        }
                        await websocket.send(json.dumps(unsubscribe_msg))
                        logger.info("Unsubscribed from market_data channel")

                    # 接收 20 條消息後退出
                    if message_count >= 20:
                        logger.info(f"✅ Received {message_count} messages. Test completed!")
                        break

            except websockets.exceptions.ConnectionClosed:
                logger.info("WebSocket connection closed")

    except ConnectionRefusedError:
        logger.error("❌ Connection refused. Please make sure the WebSocket server is running on port 3004")
    except Exception as e:
        logger.error(f"❌ Error: {e}")


async def test_health_endpoint():
    """測試健康檢查端點"""
    import aiohttp
    import asyncio

    url = "http://localhost:3004/health"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ Health check passed")
                    logger.info(f"  Active connections: {data.get('active_connections', 0)}")
                    logger.info(f"  Channel subscriptions: {list(data.get('channel_subscriptions', {}).keys())}")
                else:
                    logger.error(f"❌ Health check failed with status {response.status}")
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")


async def main():
    """主函數"""
    print("=== CBSC WebSocket 連接測試 ===\n")

    # 首先測試健康檢查端點
    print("1. 測試健康檢查端點...")
    await test_health_endpoint()

    print("\n" + "="*50 + "\n")

    # 測試 WebSocket 連接
    print("2. 測試 WebSocket 連接...")
    print("   請確保後端服務已啟動在端口 3004\n")
    await test_websocket_connection()

    print("\n" + "="*50)
    print("測試完成！")


if __name__ == "__main__":
    asyncio.run(main())