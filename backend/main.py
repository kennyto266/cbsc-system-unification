"""
CBSC WebSocket 服務器
為前端提供實時數據推送服務
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set
import uvicorn

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CBSC WebSocket API",
    description="CBSC 量化交易系統 WebSocket 實時數據服務",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001"],  # 允許前端訪問
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    """管理 WebSocket 連接的類"""

    def __init__(self):
        # 存儲活躍的連接: {websocket: {subscriptions: set(), last_pong: datetime}}
        self.active_connections: Dict[WebSocket, Dict] = {}
        # 存儲頻道訂閱: {channel: set(websockets)}
        self.channel_subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        """接受新的 WebSocket 連接"""
        await websocket.accept()
        self.active_connections[websocket] = {
            "subscriptions": set(),
            "last_pong": datetime.now()
        }
        logger.info(f"New connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """斷開連接並清理訂閱"""
        if websocket in self.active_connections:
            # 移除所有頻道訂閱
            subscriptions = self.active_connections[websocket]["subscriptions"]
            for channel in subscriptions:
                if channel in self.channel_subscriptions:
                    self.channel_subscriptions[channel].discard(websocket)
                    if not self.channel_subscriptions[channel]:
                        del self.channel_subscriptions[channel]

            # 移除連接
            del self.active_connections[websocket]
            logger.info(f"Connection closed. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """發送個人消息"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str, channel: str):
        """廣播消息到指定頻道"""
        if channel not in self.channel_subscriptions:
            return

        # 創建消息副本
        message_dict = json.loads(message)
        message_dict["timestamp"] = datetime.now().isoformat()
        message_json = json.dumps(message_dict)

        # 發送給訂閱該頻道的所有連接
        disconnected = set()
        for connection in self.channel_subscriptions[channel]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error broadcasting to channel {channel}: {e}")
                disconnected.add(connection)

        # 清理斷開的連接
        for conn in disconnected:
            self.disconnect(conn)

    async def ping_all(self):
        """心跳檢測所有連接"""
        now = datetime.now()
        disconnected = set()

        for websocket, info in self.active_connections.items():
            # 檢查超時
            if (now - info["last_pong"]).seconds > 60:
                disconnected.add(websocket)
                continue

            # 發送 ping
            try:
                await websocket.send_text(json.dumps({"type": "ping"}))
            except Exception:
                disconnected.add(websocket)

        # 清理超時連接
        for conn in disconnected:
            self.disconnect(conn)

    def subscribe(self, websocket: WebSocket, channel: str):
        """訂閱頻道"""
        if websocket in self.active_connections:
            self.active_connections[websocket]["subscriptions"].add(channel)
            if channel not in self.channel_subscriptions:
                self.channel_subscriptions[channel] = set()
            self.channel_subscriptions[channel].add(websocket)
            logger.info(f"Subscribed to {channel}. Total subscribers: {len(self.channel_subscriptions.get(channel, []))}")

    def unsubscribe(self, websocket: WebSocket, channel: str):
        """取消訂閱頻道"""
        if websocket in self.active_connections:
            self.active_connections[websocket]["subscriptions"].discard(channel)
            if channel in self.channel_subscriptions:
                self.channel_subscriptions[channel].discard(websocket)
                if not self.channel_subscriptions[channel]:
                    del self.channel_subscriptions[channel]
            logger.info(f"Unsubscribed from {channel}")


manager = ConnectionManager()

# 數據生成器
class DataGenerator:
    """生成實時策略和市場數據"""

    @staticmethod
    def generate_strategy_data():
        """生成策略表現數據"""
        import random

        strategies = [
            {
                "name": "DirectRSIStrategy",
                "sharpe_ratio": 1.23 + random.uniform(-0.1, 0.1),
                "max_drawdown": 0.15 + random.uniform(-0.02, 0.02),
                "total_return": 0.25 + random.uniform(-0.05, 0.05),
                "win_rate": 0.68 + random.uniform(-0.05, 0.05),
                "signal_count": random.randint(100, 200),
                "status": "enabled"
            },
            {
                "name": "MACDCrossStrategy",
                "sharpe_ratio": 0.95 + random.uniform(-0.1, 0.1),
                "max_drawdown": 0.12 + random.uniform(-0.02, 0.02),
                "total_return": 0.18 + random.uniform(-0.05, 0.05),
                "win_rate": 0.62 + random.uniform(-0.05, 0.05),
                "signal_count": random.randint(80, 150),
                "status": "enabled"
            },
            {
                "name": "BollingerBandsStrategy",
                "sharpe_ratio": 1.45 + random.uniform(-0.1, 0.1),
                "max_drawdown": 0.18 + random.uniform(-0.02, 0.02),
                "total_return": 0.32 + random.uniform(-0.05, 0.05),
                "win_rate": 0.72 + random.uniform(-0.05, 0.05),
                "signal_count": random.randint(120, 180),
                "status": "disabled"
            },
            {
                "name": "VWAPStrategy",
                "sharpe_ratio": 1.12 + random.uniform(-0.1, 0.1),
                "max_drawdown": 0.14 + random.uniform(-0.02, 0.02),
                "total_return": 0.22 + random.uniform(-0.05, 0.05),
                "win_rate": 0.65 + random.uniform(-0.05, 0.05),
                "signal_count": random.randint(90, 160),
                "status": "enabled"
            }
        ]

        return {"strategies": strategies}

    @staticmethod
    def generate_market_data():
        """生成市場數據"""
        import random

        data = [
            {"symbol": "0700.HK", "price": 385.20 + random.uniform(-2, 2), "change": random.uniform(-3, 3)},
            {"symbol": "0941.HK", "price": 52.15 + random.uniform(-1, 1), "change": random.uniform(-2, 2)},
            {"symbol": "2318.HK", "price": 145.60 + random.uniform(-5, 5), "change": random.uniform(-5, 5)},
            {"symbol": "1299.HK", "price": 282.40 + random.uniform(-3, 3), "change": random.uniform(-4, 4)},
        ]

        # 計算漲跌幅
        for item in data:
            item["change_percent"] = (item["change"] / item["price"]) * 100

        return {"data": data}

    @staticmethod
    def generate_hibor_data():
        """生成 HIBOR 數據"""
        import random

        rates = [
            {"tenor": "ON", "rate": 5.52 + random.uniform(-0.05, 0.05)},
            {"tenor": "1W", "rate": 5.68 + random.uniform(-0.05, 0.05)},
            {"tenor": "1M", "rate": 5.73 + random.uniform(-0.05, 0.05)},
            {"tenor": "3M", "rate": 5.78 + random.uniform(-0.05, 0.05)},
            {"tenor": "6M", "rate": 5.82 + random.uniform(-0.05, 0.05)},
            {"tenor": "12M", "rate": 5.88 + random.uniform(-0.05, 0.05)},
        ]

        return {"rates": rates}

    @staticmethod
    def generate_cbsc_data():
        """生成 CBSC 數據"""
        import random

        bull_count = 120 + random.randint(-20, 20)
        bear_count = 80 + random.randint(-20, 20)

        return {
            "bull_bear_ratio": {
                "bull_count": bull_count,
                "bear_count": bear_count,
                "ratio": bull_count / (bull_count + bear_count)
            }
        }


# WebSocket 端點
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """主要的 WebSocket 端點"""
    await manager.connect(websocket)

    try:
        while True:
            # 接收客戶端消息
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "subscribe":
                # 處理訂閱請求
                channel = message.get("channel")
                if channel:
                    manager.subscribe(websocket, channel)
                    # 發送訂閱確認
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "channel": channel,
                            "message": f"Successfully subscribed to {channel}"
                        }),
                        websocket
                    )

            elif message.get("type") == "unsubscribe":
                # 處理取消訂閱請求
                channel = message.get("channel")
                if channel:
                    manager.unsubscribe(websocket, channel)
                    # 發送取消訂閱確認
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "unsubscribed",
                            "channel": channel,
                            "message": f"Successfully unsubscribed from {channel}"
                        }),
                        websocket
                    )

            elif message.get("type") == "pong":
                # 處理心跳響應
                if websocket in manager.active_connections:
                    manager.active_connections[websocket]["last_pong"] = datetime.now()

            else:
                # 未知消息類型
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": f"Unknown message type: {message.get('type')}"
                    }),
                    websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# 數據推送後台任務
async def data_pusher():
    """後台任務，定期推送數據"""
    import random

    while True:
        try:
            # 策略表現數據 - 每5秒
            strategy_data = DataGenerator.generate_strategy_data()
            await manager.broadcast(
                json.dumps({
                    "type": "update",
                    "channel": "strategy_performance",
                    "payload": strategy_data
                }),
                "strategy_performance"
            )

            # 市場數據 - 每2秒
            market_data = DataGenerator.generate_market_data()
            await manager.broadcast(
                json.dumps({
                    "type": "data",
                    "channel": "market_data",
                    "payload": market_data
                }),
                "market_data"
            )

            # HIBOR 數據 - 每30秒
            hibor_data = DataGenerator.generate_hibor_data()
            await manager.broadcast(
                json.dumps({
                    "type": "update",
                    "channel": "hibor_rates",
                    "payload": hibor_data
                }),
                "hibor_rates"
            )

            # CBSC 數據 - 每10秒
            cbsc_data = DataGenerator.generate_cbsc_data()
            await manager.broadcast(
                json.dumps({
                    "type": "data",
                    "channel": "cbsc_contracts",
                    "payload": cbsc_data
                }),
                "cbsc_contracts"
            )

            # 心跳檢測 - 每15秒
            await asyncio.sleep(15)
            await manager.ping_all()

            # 等待到下一個週期
            await asyncio.sleep(10)  # 總週期約25秒

        except Exception as e:
            logger.error(f"Error in data pusher: {e}")
            await asyncio.sleep(5)


# 健康檢查端點
@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "channel_subscriptions": {
            channel: len(connections)
            for channel, connections in manager.channel_subscriptions.items()
        },
        "timestamp": datetime.now().isoformat()
    }


# 系統狀態端點
@app.get("/api/status")
async def system_status():
    """系統狀態端點"""
    return {
        "status": "running",
        "service": "CBSC WebSocket API",
        "version": "1.0.0",
        "active_connections": len(manager.active_connections),
        "supported_channels": [
            "strategy_performance",
            "market_data",
            "hibor_rates",
            "cbsc_contracts",
            "government_data",
            "system_status"
        ]
    }


# 啟動時事件
@app.on_event("startup")
async def startup_event():
    """應用啟動時執行"""
    logger.info("Starting CBSC WebSocket Server...")

    # 啟動數據推送後台任務
    asyncio.create_task(data_pusher())

    logger.info("WebSocket Server started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉時執行"""
    logger.info("Shutting down WebSocket Server...")


if __name__ == "__main__":
    # 運行服務器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3004,
        reload=True,
        log_level="info"
    )