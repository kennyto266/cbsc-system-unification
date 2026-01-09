# tui/api/websocket_client.py
import asyncio
import json
import websockets
from typing import Callable, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class CBSCWebSocketClient:
    """CBSC WebSocket 客戶端用於接收實時更新"""

    def __init__(self):
        self.ws_url = os.getenv(
            "CBSC_WS_URL",
            "ws://localhost:3004/ws"
        )
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.message_handlers: list[Callable] = []

    def on_message(self, handler: Callable):
        """註冊消息處理器"""
        self.message_handlers.append(handler)

    async def connect(self):
        """連接到 WebSocket 服務器"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.connected = True
        except Exception as e:
            print(f"WebSocket 連接失敗: {e}")
            self.connected = False

    async def disconnect(self):
        """斷開連接"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False

    async def listen(self):
        """監聽消息"""
        if not self.connected:
            await self.connect()

        try:
            async for message in self.websocket:
                data = json.loads(message)
                for handler in self.message_handlers:
                    await handler(data)
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
        except Exception as e:
            print(f"WebSocket 錯誤: {e}")
