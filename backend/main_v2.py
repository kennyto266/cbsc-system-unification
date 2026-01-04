"""
CBSC Trading System - Unified Backend API
整合 API v1/v2 與 WebSocket 服務
"""

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Set
import uvicorn
import sys

# Add backend directory to FRONT of Python path to ensure our modules are imported first
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Remove src directories from sys.path to avoid import conflicts
# This prevents importing from src/ instead of backend/
import pathlib
project_root = os.path.dirname(backend_dir)
src_paths_to_remove = []
for path in sys.path[:]:  # Iterate over a copy
    try:
        path_normalized = os.path.normpath(path).lower()
        # Check if path contains src directory from our project
        if 'src' in path_normalized and project_root.lower() in path_normalized:
            src_paths_to_remove.append(path)
            print(f"Removing from sys.path to avoid conflicts: {path}")
    except:
        pass

for path in src_paths_to_remove:
    sys.path.remove(path)

# Also add parent directory for sibling imports
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# ============================================
# 新的 API v1/v2 導入
# ============================================
from api.v1 import router as v1_router
from api.v2 import router as v2_router

# ============================================
# 舊的 API 導入 (保留向後兼容)
# ============================================
from api.portfolio import router as portfolio_router
from api.data import router as data_router
from api.analysis import router as analysis_router
from api.backtest import router as backtest_router
from api.persistent_context import router as persistent_context_router
from api.strategies import router as strategies_router

# ============================================
# 創建必要的目錄
# ============================================
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# ============================================
# 設置日誌
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'backend.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# 創建 FastAPI 應用
# ============================================
app = FastAPI(
    title="CBSC Trading System API",
    description="CBSC 量化交易系統統一後端 API - Integrated v1/v2 APIs with WebSocket",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================
# CORS 配置
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:3001", "http://127.0.0.1:3001",
        "http://localhost:8888", "http://127.0.0.1:8888"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# 請求日誌中間件
# ============================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import sys
    logger.info(f"[REQUEST] {request.method} {request.url.path}")
    # Only log path and method, don't consume body to allow downstream handlers to read it
    response = await call_next(request)
    logger.info(f"[RESPONSE] {response.status_code}")
    print(f"[RESPONSE] {response.status_code}", file=sys.stderr)
    return response


# ============================================
# WebSocket Connection Manager (保留現有功能)
# ============================================
class ConnectionManager:
    """管理 WebSocket 連接的類"""

    def __init__(self):
        self.active_connections: Dict[WebSocket, Dict] = {}
        self.channel_subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket] = {
            "subscriptions": set(),
            "last_pong": datetime.now()
        }
        logger.info(f"New connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            subscriptions = self.active_connections[websocket]["subscriptions"]
            for channel in subscriptions:
                if channel in self.channel_subscriptions:
                    self.channel_subscriptions[channel].discard(websocket)
                    if not self.channel_subscriptions[channel]:
                        del self.channel_subscriptions[channel]
            del self.active_connections[websocket]
            logger.info(f"Connection closed. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str, channel: str):
        if channel not in self.channel_subscriptions:
            return

        message_dict = json.loads(message)
        message_dict["timestamp"] = datetime.now().isoformat()
        message_json = json.dumps(message_dict)

        disconnected = set()
        for connection in self.channel_subscriptions[channel]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error broadcasting to channel {channel}: {e}")
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn)

    async def ping_all(self):
        now = datetime.now()
        disconnected = set()

        for websocket, info in self.active_connections.items():
            if (now - info["last_pong"]).seconds > 60:
                disconnected.add(websocket)
                continue

            try:
                await websocket.send_text(json.dumps({"type": "ping"}))
            except Exception:
                disconnected.add(websocket)

        for conn in disconnected:
            self.disconnect(conn)

    def subscribe(self, websocket: WebSocket, channel: str):
        if websocket in self.active_connections:
            self.active_connections[websocket]["subscriptions"].add(channel)
            if channel not in self.channel_subscriptions:
                self.channel_subscriptions[channel] = set()
            self.channel_subscriptions[channel].add(websocket)
            logger.info(f"Subscribed to {channel}. Total subscribers: {len(self.channel_subscriptions.get(channel, []))}")

    def unsubscribe(self, websocket: WebSocket, channel: str):
        if websocket in self.active_connections:
            self.active_connections[websocket]["subscriptions"].discard(channel)
            if channel in self.channel_subscriptions:
                self.channel_subscriptions[channel].discard(websocket)
                if not self.channel_subscriptions[channel]:
                    del self.channel_subscriptions[channel]
            logger.info(f"Unsubscribed from {channel}")


manager = ConnectionManager()


# ============================================
# 數據生成器 (保留現有功能)
# ============================================
class DataGenerator:
    """生成實時策略和市場數據"""

    @staticmethod
    def generate_strategy_data():
        import random
        return {
            "strategies": [
                {
                    "name": "DirectRSIStrategy",
                    "sharpe_ratio": 1.23 + random.uniform(-0.1, 0.1),
                    "max_drawdown": 0.15 + random.uniform(-0.02, 0.02),
                    "total_return": 0.25 + random.uniform(-0.05, 0.05),
                    "win_rate": 0.68 + random.uniform(-0.05, 0.05),
                    "status": "enabled"
                },
                {
                    "name": "MACDCrossStrategy",
                    "sharpe_ratio": 0.95 + random.uniform(-0.1, 0.1),
                    "max_drawdown": 0.12 + random.uniform(-0.02, 0.02),
                    "total_return": 0.18 + random.uniform(-0.05, 0.05),
                    "status": "enabled"
                }
            ]
        }

    @staticmethod
    def generate_market_data():
        import random
        data = [
            {"symbol": "0700.HK", "price": 385.20 + random.uniform(-2, 2), "change": random.uniform(-3, 3)},
            {"symbol": "0941.HK", "price": 52.15 + random.uniform(-1, 1), "change": random.uniform(-2, 2)},
        ]
        for item in data:
            item["change_percent"] = (item["change"] / item["price"]) * 100
        return {"data": data}


# ============================================
# 註冊路由
# ============================================

# 新的 API v1/v2 路由
app.include_router(
    v1_router,
    prefix="/api/v1",
    tags=["API v1 (Legacy)"]
)

app.include_router(
    v2_router,
    prefix="/api/v2",
    tags=["API v2 (New Architecture)"]
)

# 舊的路由 (保留向後兼容)
app.include_router(portfolio_router, prefix="/api/portfolio", tags=["投資組合"])
app.include_router(data_router, prefix="/api/data", tags=["數據服務"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["分析服務"])
app.include_router(backtest_router, prefix="/api/backtest", tags=["回測服務"])
app.include_router(persistent_context_router, prefix="/api/persistent-context", tags=["持久化上下文"])
app.include_router(strategies_router, prefix="/api/strategies-legacy", tags=["策略管理 (舊版)"])


# ============================================
# 異常處理器
# ============================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import sys
    import traceback
    print(f"GLOBAL EXCEPTION: {exc}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    logger.error(f"全局異常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {"code": "INTERNAL_SERVER_ERROR", "message": "服務器內部錯誤"},
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================
# 根路徑和健康檢查
# ============================================
@app.get("/")
async def root():
    return {
        "message": "CBSC Trading System API - Unified Backend",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "api_versions": {
            "v1": "/api/v1 - Legacy endpoints (backward compatibility)",
            "v2": "/api/v2 - New architecture endpoints"
        },
        "websocket": {
            "endpoint": "/ws",
            "channels": ["strategy_performance", "market_data", "hibor_rates"]
        },
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "active_connections": len(manager.active_connections),
        "api": {"v1": "enabled", "v2": "enabled"}
    }


# ============================================
# WebSocket 端點 (保留現有功能)
# ============================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Manual CORS check for WebSocket (CORS middleware doesn't apply to WS)
    origin = websocket.headers.get("origin")
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        None  # Allow connections without Origin header (e.g., from same origin)
    ]

    if origin not in allowed_origins:
        logger.warning(f"WebSocket connection rejected from origin: {origin}")
        await websocket.close(code=1008, reason="Origin not allowed")
        return

    await manager.connect(websocket)
    logger.info(f"WebSocket connection accepted from origin: {origin}")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "subscribe":
                channel = message.get("channel")
                if channel:
                    manager.subscribe(websocket, channel)
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "channel": channel,
                            "message": f"Successfully subscribed to {channel}"
                        }),
                        websocket
                    )

            elif message.get("type") == "unsubscribe":
                channel = message.get("channel")
                if channel:
                    manager.unsubscribe(websocket, channel)

            elif message.get("type") == "pong":
                if websocket in manager.active_connections:
                    manager.active_connections[websocket]["last_pong"] = datetime.now()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ============================================
# 數據推送後台任務
# ============================================
async def data_pusher():
    while True:
        try:
            strategy_data = DataGenerator.generate_strategy_data()
            await manager.broadcast(
                json.dumps({"type": "update", "channel": "strategy_performance", "payload": strategy_data}),
                "strategy_performance"
            )

            market_data = DataGenerator.generate_market_data()
            await manager.broadcast(
                json.dumps({"type": "data", "channel": "market_data", "payload": market_data}),
                "market_data"
            )

            await asyncio.sleep(15)
            await manager.ping_all()

        except Exception as e:
            logger.error(f"Error in data pusher: {e}")
            await asyncio.sleep(5)


# ============================================
# 啟動/關閉事件
# ============================================
@app.on_event("startup")
async def startup_event():
    logger.info("Starting CBSC Trading System API v2.0...")

    # Initialize database
    from core.database import init_db
    try:
        await init_db()
        logger.info("[DB] Database initialized successfully")
    except Exception as e:
        logger.error(f"[DB] Database initialization failed: {e}")

    asyncio.create_task(data_pusher())
    logger.info("[OK] CBSC Trading System API started successfully")
    logger.info("[API] API Docs: http://localhost:3004/docs")
    logger.info("[WS] WebSocket: ws://localhost:3004/ws")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down CBSC Trading System API...")


# ============================================
# 開發服務器啟動
# ============================================
if __name__ == "__main__":
    try:
        logger.info("Starting development server...")
        uvicorn.run(
            "main_v2:app",
            host="0.0.0.0",
            port=3004,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down server...")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)
