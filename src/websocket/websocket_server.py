#!/usr/bin/env python3
"""
Phase 8.1 WebSocket實時推送系統 - 主服務器
Main WebSocket Server for Real-time Push System
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import uvicorn
import redis.asyncio as redis
from pydantic import BaseModel, Field

from .unified_websocket_manager import (
    UnifiedWebSocketManager,
    StreamType,
    MessageType,
    unified_ws_manager
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

class WebSocketServerConfig(BaseModel):
    """WebSocket服務器配置"""
    host: str = "0.0.0.0"
    port: int = 8001
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "websocket-server-secret-key"
    enable_compression: bool = True
    max_connections_per_user: int = 10
    cors_origins: List[str] = ["*"]
    enable_docs: bool = True

class SubscriptionRequest(BaseModel):
    """訂閱請求模型"""
    stream_type: str = Field(..., description="數據流類型")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="過濾條件")
    frequency_limit: Optional[float] = Field(default=None, description="頻率限制（每秒消息數）")

class BroadcastRequest(BaseModel):
    """廣播請求模型"""
    stream_type: str = Field(..., description="數據流類型")
    data: Dict[str, Any] = Field(..., description="數據內容")
    target_users: Optional[List[str]] = Field(default=None, description="目標用戶列表")

class RealtimeWebSocketServer:
    """實時WebSocket服務器"""

    def __init__(self, config: WebSocketServerConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self.app = FastAPI(
            title="Quantitative Strategy Real-time WebSocket API",
            description="實時策略管理系統WebSocket推送服務",
            version="8.1.0",
            docs_url="/docs" if config.enable_docs else None
        )

        # 初始化WebSocket管理器
        self.ws_manager = UnifiedWebSocketManager(
            redis_client=None,  # Will be set after Redis connection
            secret_key=config.secret_key,
            enable_compression=config.enable_compression,
            max_connections_per_user=config.max_connections_per_user
        )

        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        """設置中間件"""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """設置路由"""

        @self.app.get("/")
        async def root():
            """根路由"""
            return {
                "service": "Real-time WebSocket API",
                "version": "8.1.0",
                "status": "running",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        @self.app.get("/health")
        async def health_check():
            """健康檢查"""
            stats = await self.ws_manager.get_connection_stats()
            return {
                "status": "healthy",
                "websocket_stats": stats,
                "redis_connected": self.redis_client is not None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket端點"""
            await websocket.accept()

            # 獲取認證token
            token = websocket.query_params.get("token")
            if not token:
                await websocket.close(code=4001, reason="Missing authentication token")
                return

            # 驗證連接
            context = await self.ws_manager.authenticate_connection(websocket, token)
            if not context:
                await websocket.close(code=4003, reason="Authentication failed")
                return

            # 發送歡迎消息
            await self.ws_manager.send_personal_message(websocket, {
                "stream_type": "system",
                "message_type": "connection_established",
                "data": {
                    "user_id": context.user_id,
                    "permissions": context.permissions,
                    "available_streams": [stream.value for stream in StreamType],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            })

            try:
                while True:
                    # 接收客戶端消息
                    try:
                        data = await websocket.receive_json()
                        await self._handle_client_message(websocket, data)
                    except Exception as e:
                        logger.error(f"Error handling client message: {e}")
                        await self.ws_manager.send_personal_message(websocket, {
                            "stream_type": "system",
                            "message_type": MessageType.ERROR.value,
                            "data": {
                                "error": str(e),
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        })

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: user_id={context.user_id}")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                await self.ws_manager.disconnect(websocket)

        @self.app.post("/api/broadcast")
        async def broadcast_message(request: BroadcastRequest):
            """廣播消息到數據流"""
            try:
                sent_count = await self.ws_manager.broadcast_to_stream(
                    stream_type=request.stream_type,
                    raw_data=request.data,
                    target_users=request.target_users
                )

                return {
                    "success": True,
                    "sent_count": sent_count,
                    "stream_type": request.stream_type,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/subscribe")
        async def subscribe_to_stream(
            request: SubscriptionRequest,
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            """訂閱數據流（REST API方式）"""
            # Note: This is for testing purposes
            return {
                "message": "Please use WebSocket connection to subscribe to streams",
                "websocket_url": f"ws://{self.config.host}:{self.config.port}/ws?token={credentials.credentials}",
                "available_streams": [stream.value for stream in StreamType]
            }

        @self.app.get("/api/stats")
        async def get_stats():
            """獲取服務器統計信息"""
            return await self.ws_manager.get_connection_stats()

        @self.app.get("/api/streams")
        async def get_available_streams():
            """獲取可用的數據流"""
            return {
                "streams": [
                    {
                        "type": stream.value,
                        "description": self._get_stream_description(stream)
                    }
                    for stream in StreamType
                ]
            }

        @self.app.post("/api/test/data/{stream_type}")
        async def send_test_data(stream_type: str, data: Optional[Dict[str, Any]] = None):
            """發送測試數據（僅用於開發測試）"""
            if stream_type not in [s.value for s in StreamType]:
                raise HTTPException(status_code=400, detail="Invalid stream type")

            # 生成測試數據
            test_data = data or self._generate_test_data(stream_type)

            sent_count = await self.ws_manager.broadcast_to_stream(stream_type, test_data)

            return {
                "success": True,
                "sent_count": sent_count,
                "test_data": test_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def _handle_client_message(self, websocket: WebSocket, data: Dict[str, Any]):
        """處理客戶端消息"""
        message_type = data.get("type")

        if message_type == "subscribe":
            # 處理訂閱請求
            stream_type = data.get("stream_type")
            filters = data.get("filters", {})
            frequency_limit = data.get("frequency_limit")

            if not stream_type:
                await self.ws_manager.send_personal_message(websocket, {
                    "stream_type": "system",
                    "message_type": MessageType.ERROR.value,
                    "data": {"error": "Missing stream_type"}
                })
                return

            success = await self.ws_manager.subscribe_to_stream(
                websocket=websocket,
                stream_type=stream_type,
                filters=filters,
                frequency_limit=frequency_limit
            )

            if not success:
                await self.ws_manager.send_personal_message(websocket, {
                    "stream_type": "system",
                    "message_type": MessageType.ERROR.value,
                    "data": {"error": f"Failed to subscribe to {stream_type}"}
                })

        elif message_type == "unsubscribe":
            # 處理取消訂閱請求
            stream_type = data.get("stream_type")

            if not stream_type:
                await self.ws_manager.send_personal_message(websocket, {
                    "stream_type": "system",
                    "message_type": MessageType.ERROR.value,
                    "data": {"error": "Missing stream_type"}
                })
                return

            success = await self.ws_manager.unsubscribe_from_stream(websocket, stream_type)

            if not success:
                await self.ws_manager.send_personal_message(websocket, {
                    "stream_type": "system",
                    "message_type": MessageType.ERROR.value,
                    "data": {"error": f"Failed to unsubscribe from {stream_type}"}
                })

        elif message_type == "ping":
            # 處理心跳
            await self.ws_manager.send_personal_message(websocket, {
                "stream_type": "system",
                "message_type": "pong",
                "data": {
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            })

        else:
            # 未知消息類型
            await self.ws_manager.send_personal_message(websocket, {
                "stream_type": "system",
                "message_type": MessageType.ERROR.value,
                "data": {"error": f"Unknown message type: {message_type}"}
            })

    def _get_stream_description(self, stream_type: StreamType) -> str:
        """獲取數據流描述"""
        descriptions = {
            StreamType.STRATEGY_EXECUTION: "策略執行狀態和實時指標",
            StreamType.RISK_MONITORING: "風險監控指標和警報",
            StreamType.PERFORMANCE_METRICS: "策略性能指標更新",
            StreamType.MARKET_DATA: "實時市場數據更新",
            StreamType.SYSTEM_NOTIFICATIONS: "系統通知和警報",
            StreamType.USER_ALERTS: "用戶個人化警報",
            StreamType.PORTFOLIO_UPDATES: "投資組合變更通知"
        }
        return descriptions.get(stream_type, "未知數據流")

    def _generate_test_data(self, stream_type: str) -> Dict[str, Any]:
        """生成測試數據"""
        if stream_type == StreamType.STRATEGY_EXECUTION.value:
            return {
                "strategy_id": "test_strategy_001",
                "status": "running",
                "execution_time": 0.05,
                "performance": {
                    "total_return": 0.15,
                    "annualized_return": 0.18,
                    "win_rate": 0.65
                },
                "signals": [
                    {"symbol": "0700.HK", "action": "BUY", "price": 320.5}
                ],
                "progress": 0.75
            }

        elif stream_type == StreamType.RISK_MONITORING.value:
            return {
                "portfolio_id": "test_portfolio_001",
                "risk_metrics": {
                    "var_95": 0.02,
                    "cvar_95": 0.025,
                    "volatility": 0.15
                },
                "exposure": {
                    "equity": 0.6,
                    "fixed_income": 0.3,
                    "cash": 0.1
                },
                "risk_score": 45,
                "alerts": []
            }

        elif stream_type == StreamType.PERFORMANCE_METRICS.value:
            return {
                "strategy_id": "test_strategy_001",
                "returns": {
                    "daily": 0.005,
                    "weekly": 0.02,
                    "monthly": 0.08
                },
                "sharpe_ratio": 1.85,
                "max_drawdown": -0.12,
                "win_rate": 0.65,
                "profit_factor": 1.8
            }

        elif stream_type == StreamType.MARKET_DATA.value:
            return {
                "symbol": "0700.HK",
                "price": 320.5,
                "volume": 1500000,
                "bid": 320.4,
                "ask": 320.6,
                "change": 2.5,
                "change_percent": 0.79
            }

        elif stream_type == StreamType.SYSTEM_NOTIFICATIONS.value:
            return {
                "notification_id": "notif_001",
                "type": "info",
                "title": "系統維護通知",
                "message": "系統將於今晚11點進行例行維護",
                "priority": "normal"
            }

        else:
            return {"test": True, "timestamp": datetime.now(timezone.utc).isoformat()}

    async def initialize_redis(self) -> bool:
        """初始化Redis連接"""
        try:
            self.redis_client = redis.from_url(self.config.redis_url)
            await self.redis_client.ping()

            # Update WebSocket manager with Redis client
            self.ws_manager.redis_client = self.redis_client

            logger.info(f"Connected to Redis at {self.config.redis_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False

    async def start(self):
        """啟動服務器"""
        # Initialize Redis
        redis_connected = await self.initialize_redis()

        logger.info(f"Starting WebSocket server on {self.config.host}:{self.config.port}")
        logger.info(f"Redis connected: {redis_connected}")

        # Run server
        config = uvicorn.Config(
            app=self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info"
        )

        server = uvicorn.Server(config)
        await server.serve()

# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程序生命週期管理"""
    # Startup
    logger.info("WebSocket server starting up...")
    yield
    # Shutdown
    logger.info("WebSocket server shutting down...")

# Global server instance
server_instance: Optional[RealtimeWebSocketServer] = None

async def create_server(config: Optional[WebSocketServerConfig] = None) -> RealtimeWebSocketServer:
    """創建WebSocket服務器實例"""
    global server_instance

    if config is None:
        config = WebSocketServerConfig()

    server_instance = RealtimeWebSocketServer(config)
    return server_instance

async def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="Real-time WebSocket Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--redis-url", default="redis://localhost:6379", help="Redis URL")
    parser.add_argument("--secret-key", default="websocket-server-secret-key", help="Secret key for JWT")

    args = parser.parse_args()

    # Create config
    config = WebSocketServerConfig(
        host=args.host,
        port=args.port,
        redis_url=args.redis_url,
        secret_key=args.secret_key
    )

    # Create and start server
    server = await create_server(config)
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())