#!/usr/bin/env python3
"""
WebSocket測試客戶端
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws/test_client"

    try:
        async with websockets.connect(uri) as websocket:
            print("WebSocket連接成功")

            # 測試歡迎消息
            welcome_msg = await websocket.recv()
            welcome_data = json.loads(welcome_msg)
            print(f"歡迎消息: {welcome_data}")

            # 測試ping/pong
            print("發送ping...")
            await websocket.send("ping")
            pong_response = await websocket.recv()
            pong_data = json.loads(pong_response)
            print(f"Pong回應: {pong_data}")

            # 測試echo功能
            test_message = "Hello WebSocket"
            print(f"發送測試消息: {test_message}")
            await websocket.send(test_message)
            echo_response = await websocket.recv()
            echo_data = json.loads(echo_response)
            print(f"Echo回應: {echo_data}")

            print("WebSocket測試完成")

    except Exception as e:
        print(f"WebSocket連接失敗: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())