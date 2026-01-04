#!/usr/bin/env python3
"""
Task 9.2: Real-time Data Push - Enhanced WebSocket Server
實時數據推送 - 增強版 WebSocket 服務器
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

# Import existing modules
from .unified_websocket_manager import (
    UnifiedWebSocketManager,
    StreamType,
    MessageType
)

# Import new modules
from .market_data_stream import (
    MarketDataStreamer,
    MarketDataType,
    DataFrequency,
    get_market_data_streamer
)
from .notification_manager import (
    NotificationManager,
    NotificationType,
    NotificationPriority,
    NotificationChannel,
    get_notification_manager
)
from .subscription_manager import (
    SubscriptionManager,
    SubscriptionType,
    SubscriptionFilter,
    get_subscription_manager
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

class EnhancedWebSocketServerConfig(BaseModel):
    """增強版WebSocket服務器配置"""
    host: str = "0.0.0.0"
    port: int = 8001
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "enhanced-websocket-secret-key"
    enable_compression: bool = True
    max_connections_per_user: int = 10
    max_subscriptions_per_user: int = 50
    cors_origins: List[str] = ["*"]
    enable_docs: bool = True

    # Market data config
    market_data_enabled: bool = True
    market_data_sources: List[str] = ["simulated"]

    # Notification config
    notification_email: Optional[Dict[str, Any]] = None
    notification_webhook: Optional[Dict[str, Any]] = None

class MarketDataSubscriptionRequest(BaseModel):
    """市場數據訂閱請求"""
    symbols: List[str] = Field(..., description="股票代碼列表")
    data_types: List[MarketDataType] = Field(..., description="數據類型列表")
    frequency: DataFrequency = Field(DataFrequency.REALTIME, description="數據頻率")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="過濾條件")
    max_frequency: Optional[float] = Field(default=None, description="最大頻率限制")

class AdvancedSubscriptionRequest(BaseModel):
    """高級訂閱請求"""
    subscription_type: SubscriptionType = Field(..., description="訂閱類型")
    filters: List[Dict[str, Any]] = Field(default_factory=list, description="過濾器列表")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="訂閱參數")
    expires_at: Optional[datetime] = Field(default=None, description="過期時間")
    rate_limit: Optional[float] = Field(default=None, description="速率限制")

class NotificationRequest(BaseModel):
    """通知請求"""
    title: str = Field(..., description="通知標題")
    message: str = Field(..., description="通知內容")
    type: NotificationType = Field(NotificationType.INFO, description="通知類型")
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="優先級")
    target_users: Optional[List[str]] = Field(default=None, description="目標用戶")
    channels: Optional[List[NotificationChannel]] = Field(default=None, description="通知渠道")
    data: Optional[Dict[str, Any]] = Field(default=None, description="附加數據")

class RealtimeWebSocketServer:
    """實時WebSocket服務器（增強版）"""

    def __init__(self, config: EnhancedWebSocketServerConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self.app = FastAPI(
            title="Enhanced Quantitative Strategy Real-time WebSocket API",
            description="增強版實時策略管理系統WebSocket推送服務",
            version="9.2.0",
            docs_url="/docs" if config.enable_docs else None
        )

        # Initialize managers
        self.ws_manager = UnifiedWebSocketManager(
            redis_client=None,  # Will be set after Redis connection
            secret_key=config.secret_key,
            enable_compression=config.enable_compression,
            max_connections_per_user=config.max_connections_per_user
        )

        self.subscription_manager: Optional[SubscriptionManager] = None
        self.market_data_streamer: Optional[MarketDataStreamer] = None
        self.notification_manager: Optional[NotificationManager] = None

        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        """設置中間件"""
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
                "service": "Enhanced Real-time WebSocket API",
                "version": "9.2.0",
                "status": "running",
                "features": {
                    "market_data": self.config.market_data_enabled,
                    "notifications": True,
                    "advanced_subscriptions": True
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        @self.app.get("/health")
        async def health_check():
            """健康檢查"""
            ws_stats = await self.ws_manager.get_connection_stats()

            health_data = {
                "status": "healthy",
                "websocket_stats": ws_stats,
                "redis_connected": self.redis_client is not None,
                "managers": {
                    "subscription_manager": self.subscription_manager is not None,
                    "market_data_streamer": self.market_data_streamer is not None,
                    "notification_manager": self.notification_manager is not None
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Add manager stats if available
            if self.subscription_manager:
                health_data["subscription_stats"] = await self.subscription_manager.get_subscription_stats()

            if self.market_data_streamer:
                health_data["market_data_stats"] = await self.market_data_streamer.get_stats()

            if self.notification_manager:
                health_data["notification_stats"] = await self.notification_manager.get_stats()

            return health_data

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket端點（增強版）"""
            await websocket.accept()
            connection_id = f"conn_{datetime.now().timestamp()}"

            # Get authentication token
            token = websocket.query_params.get("token")
            if not token:
                await websocket.close(code=4001, reason="Missing authentication token")
                return

            # Authenticate connection
            context = await self.ws_manager.authenticate_connection(websocket, token)
            if not context:
                await websocket.close(code=4003, reason="Authentication failed")
                return

            # Register connection with subscription manager
            if self.subscription_manager:
                success = await self.subscription_manager.register_connection(
                    connection_id=connection_id,
                    user_id=context.user_id,
                    websocket=websocket,
                    ip_address=websocket.client.host if websocket.client else None
                )
                if not success:
                    await websocket.close(code=4004, reason="Connection limit exceeded")
                    return

            # Send welcome message
            await self.ws_manager.send_personal_message(websocket, {
                "stream_type": "system",
                "message_type": "connection_established",
                "data": {
                    "user_id": context.user_id,
                    "permissions": context.permissions,
                    "connection_id": connection_id,
                    "available_streams": [stream.value for stream in StreamType],
                    "features": {
                        "market_data": self.config.market_data_enabled,
                        "advanced_subscriptions": True
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            })

            try:
                while True:
                    try:
                        data = await websocket.receive_json()
                        await self._handle_client_message(websocket, connection_id, data)
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
                logger.info(f"WebSocket disconnected: user_id={context.user_id}, connection_id={connection_id}")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                # Unregister connection
                if self.subscription_manager:
                    await self.subscription_manager.unregister_connection(connection_id)
                await self.ws_manager.disconnect(websocket)

        # Market data endpoints
        @self.app.post("/api/market-data/subscribe")
        async def subscribe_market_data(
            request: MarketDataSubscriptionRequest,
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            """訂閱市場數據"""
            if not self.market_data_streamer:
                raise HTTPException(status_code=503, detail="Market data service not available")

            # Extract user_id from token (simplified)
            user_id = "user_from_token"  # In production, decode JWT token

            success = await self.market_data_streamer.subscribe_market_data(
                user_id=user_id,
                symbols=request.symbols,
                data_types=request.data_types,
                frequency=request.frequency,
                filters=request.filters,
                max_frequency=request.max_frequency
            )

            if success:
                return {
                    "success": True,
                    "message": f"Subscribed to {len(request.symbols)} symbols",
                    "symbols": request.symbols,
                    "data_types": [dt.value for dt in request.data_types],
                    "frequency": request.frequency.value
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to subscribe")

        @self.app.get("/api/market-data/latest/{symbol}")
        async def get_latest_market_data(symbol: str, data_type: MarketDataType = MarketDataType.QUOTE):
            """獲取最新市場數據"""
            if not self.market_data_streamer:
                raise HTTPException(status_code=503, detail="Market data service not available")

            data_point = await self.market_data_streamer.get_latest_data(symbol, data_type)

            if data_point:
                return {
                    "success": True,
                    "data": data_point.to_dict()
                }
            else:
                return {
                    "success": False,
                    "message": "No data available"
                }

        @self.app.get("/api/market-data/history/{symbol}")
        async def get_market_data_history(
            symbol: str,
            data_type: MarketDataType = MarketDataType.QUOTE,
            limit: int = 100
        ):
            """獲取市場數據歷史"""
            if not self.market_data_streamer:
                raise HTTPException(status_code=503, detail="Market data service not available")

            history = await self.market_data_streamer.get_historical_data(symbol, data_type, limit)

            return {
                "success": True,
                "data": [dp.to_dict() for dp in history],
                "count": len(history)
            }

        # Advanced subscription endpoints
        @self.app.post("/api/subscriptions/advanced")
        async def create_advanced_subscription(
            request: AdvancedSubscriptionRequest,
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            """創建高級訂閱"""
            if not self.subscription_manager:
                raise HTTPException(status_code=503, detail="Subscription service not available")

            # Extract user_id and connection_id from token (simplified)
            user_id = "user_from_token"
            connection_id = "conn_from_token"

            # Convert filters to SubscriptionFilter objects
            filters = []
            for filter_dict in request.filters:
                filters.append(SubscriptionFilter(
                    field=filter_dict["field"],
                    operator=filter_dict["operator"],
                    value=filter_dict["value"]
                ))

            subscription_id = await self.subscription_manager.create_subscription(
                user_id=user_id,
                connection_id=connection_id,
                subscription_type=request.subscription_type,
                filters=filters,
                parameters=request.parameters,
                expires_at=request.expires_at,
                rate_limit=request.rate_limit
            )

            if subscription_id:
                return {
                    "success": True,
                    "subscription_id": subscription_id,
                    "subscription_type": request.subscription_type.value
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to create subscription")

        @self.app.get("/api/subscriptions")
        async def get_user_subscriptions(credentials: HTTPAuthorizationCredentials = Depends(security)):
            """獲取用戶訂閱列表"""
            if not self.subscription_manager:
                raise HTTPException(status_code=503, detail="Subscription service not available")

            user_id = "user_from_token"  # Extract from token
            subscriptions = await self.subscription_manager.get_user_subscriptions(user_id)

            return {
                "success": True,
                "subscriptions": [sub.to_dict() for sub in subscriptions],
                "count": len(subscriptions)
            }

        @self.app.put("/api/subscriptions/{subscription_id}")
        async def update_subscription(
            subscription_id: str,
            request: AdvancedSubscriptionRequest,
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            """更新訂閱"""
            if not self.subscription_manager:
                raise HTTPException(status_code=503, detail="Subscription service not available")

            # Convert filters
            filters = []
            for filter_dict in request.filters:
                filters.append(SubscriptionFilter(
                    field=filter_dict["field"],
                    operator=filter_dict["operator"],
                    value=filter_dict["value"]
                ))

            success = await self.subscription_manager.update_subscription(
                subscription_id=subscription_id,
                filters=filters,
                parameters=request.parameters,
                rate_limit=request.rate_limit
            )

            if success:
                return {
                    "success": True,
                    "message": "Subscription updated successfully"
                }
            else:
                raise HTTPException(status_code=404, detail="Subscription not found")

        @self.app.delete("/api/subscriptions/{subscription_id}")
        async def delete_subscription(
            subscription_id: str,
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            """刪除訂閱"""
            if not self.subscription_manager:
                raise HTTPException(status_code=503, detail="Subscription service not available")

            success = await self.subscription_manager.unsubscribe(subscription_id)

            if success:
                return {
                    "success": True,
                    "message": "Subscription deleted successfully"
                }
            else:
                raise HTTPException(status_code=404, detail="Subscription not found")

        # Notification endpoints
        @self.app.post("/api/notifications/send")
        async def send_notification(
            request: NotificationRequest,
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            """發送通知"""
            if not self.notification_manager:
                raise HTTPException(status_code=503, detail="Notification service not available")

            # Create notification object
            from .notification_manager import Notification
            notification = Notification(
                type=request.type,
                title=request.title,
                message=request.message,
                priority=request.priority,
                data=request.data or {}
            )

            results = await self.notification_manager.send_notification(
                notification=notification,
                target_users=request.target_users,
                channels=request.channels
            )

            success_count = sum(1 for success in results.values() if success)

            return {
                "success": True,
                "sent_to": success_count,
                "total_recipients": len(results),
                "results": results
            }

        @self.app.post("/api/notifications/system")
        async def send_system_notification(request: NotificationRequest):
            """發送系統廣播通知"""
            if not self.notification_manager:
                raise HTTPException(status_code=503, detail="Notification service not available")

            success_count = await self.notification_manager.broadcast_system_notification(
                title=request.title,
                message=request.message,
                type=request.type,
                priority=request.priority,
                data=request.data
            )

            return {
                "success": True,
                "sent_to": success_count,
                "message": "System notification broadcasted"
            }

        @self.app.post("/api/notifications/strategy-alert")
        async def send_strategy_alert(
            strategy_id: str,
            alert_type: str,
            message: str,
            user_id: str,
            data: Optional[Dict[str, Any]] = None
        ):
            """發送策略警報"""
            if not self.notification_manager:
                raise HTTPException(status_code=503, detail="Notification service not available")

            success = await self.notification_manager.send_strategy_alert(
                strategy_id=strategy_id,
                alert_type=alert_type,
                message=message,
                user_id=user_id,
                data=data
            )

            return {
                "success": success,
                "strategy_id": strategy_id,
                "alert_type": alert_type
            }

        @self.app.post("/api/notifications/risk-alert")
        async def send_risk_alert(
            portfolio_id: str,
            risk_level: str,
            message: str,
            user_id: str,
            data: Optional[Dict[str, Any]] = None
        ):
            """發送風險警報"""
            if not self.notification_manager:
                raise HTTPException(status_code=503, detail="Notification service not available")

            success = await self.notification_manager.send_risk_alert(
                portfolio_id=portfolio_id,
                risk_level=risk_level,
                message=message,
                user_id=user_id,
                data=data
            )

            return {
                "success": success,
                "portfolio_id": portfolio_id,
                "risk_level": risk_level
            }

        # Stats endpoints
        @self.app.get("/api/stats/all")
        async def get_all_stats():
            """獲取所有統計信息"""
            stats = {
                "websocket": await self.ws_manager.get_connection_stats(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            if self.subscription_manager:
                stats["subscriptions"] = await self.subscription_manager.get_subscription_stats()

            if self.market_data_streamer:
                stats["market_data"] = await self.market_data_streamer.get_stats()

            if self.notification_manager:
                stats["notifications"] = await self.notification_manager.get_stats()

            return stats

    async def _handle_client_message(self, websocket: WebSocket, connection_id: str, data: Dict[str, Any]):
        """處理客戶端消息（增強版）"""
        message_type = data.get("type")

        if message_type == "subscribe":
            # Handle legacy subscription
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

        elif message_type == "advanced_subscribe":
            # Handle advanced subscription
            subscription_data = data.get("subscription", {})

            if self.subscription_manager:
                # Convert to subscription request
                from .subscription_manager import SubscriptionType, SubscriptionFilter

                subscription_type = SubscriptionType(subscription_data.get("type"))
                filters = []
                for filter_dict in subscription_data.get("filters", []):
                    filters.append(SubscriptionFilter(
                        field=filter_dict["field"],
                        operator=filter_dict["operator"],
                        value=filter_dict["value"]
                    ))

                subscription_id = await self.subscription_manager.create_subscription(
                    user_id="user_from_token",  # Extract from context
                    connection_id=connection_id,
                    subscription_type=subscription_type,
                    filters=filters,
                    parameters=subscription_data.get("parameters", {}),
                    expires_at=subscription_data.get("expires_at"),
                    rate_limit=subscription_data.get("rate_limit")
                )

                if subscription_id:
                    await self.ws_manager.send_personal_message(websocket, {
                        "stream_type": "system",
                        "message_type": "subscription_created",
                        "data": {
                            "subscription_id": subscription_id,
                            "type": subscription_type.value
                        }
                    })
                else:
                    await self.ws_manager.send_personal_message(websocket, {
                        "stream_type": "system",
                        "message_type": MessageType.ERROR.value,
                        "data": {"error": "Failed to create subscription"}
                    })

        elif message_type == "unsubscribe":
            # Handle unsubscribe
            subscription_id = data.get("subscription_id")
            stream_type = data.get("stream_type")

            if subscription_id and self.subscription_manager:
                # Unsubscribe from advanced subscription
                success = await self.subscription_manager.unsubscribe(subscription_id)
            elif stream_type:
                # Unsubscribe from legacy stream
                success = await self.ws_manager.unsubscribe_from_stream(websocket, stream_type)
            else:
                success = False

            if not success:
                await self.ws_manager.send_personal_message(websocket, {
                    "stream_type": "system",
                    "message_type": MessageType.ERROR.value,
                    "data": {"error": "Failed to unsubscribe"}
                })

        elif message_type == "ping":
            # Handle ping
            await self.ws_manager.send_personal_message(websocket, {
                "stream_type": "system",
                "message_type": "pong",
                "data": {
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            })

        else:
            # Unknown message type
            await self.ws_manager.send_personal_message(websocket, {
                "stream_type": "system",
                "message_type": MessageType.ERROR.value,
                "data": {"error": f"Unknown message type: {message_type}"}
            })

    async def initialize_redis(self) -> bool:
        """初始化Redis連接"""
        try:
            self.redis_client = redis.from_url(self.config.redis_url)
            await self.redis_client.ping()

            # Update managers with Redis client
            self.ws_manager.redis_client = self.redis_client

            logger.info(f"Connected to Redis at {self.config.redis_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False

    async def initialize_managers(self):
        """初始化所有管理器"""
        # Initialize subscription manager
        self.subscription_manager = await get_subscription_manager(
            self.ws_manager,
            self.redis_client,
            {"max_subscriptions_per_user": self.config.max_subscriptions_per_user}
        )

        # Initialize market data streamer
        if self.config.market_data_enabled:
            self.market_data_streamer = await get_market_data_streamer(
                self.ws_manager,
                self.redis_client
            )

        # Initialize notification manager
        notification_config = {}
        if self.config.notification_email:
            notification_config["email"] = self.config.notification_email
        if self.config.notification_webhook:
            notification_config["webhook"] = self.config.notification_webhook

        self.notification_manager = await get_notification_manager(
            self.ws_manager,
            self.redis_client,
            notification_config
        )

        logger.info("All managers initialized successfully")

    async def start(self):
        """啟動服務器"""
        # Initialize Redis
        redis_connected = await self.initialize_redis()

        # Initialize managers
        await self.initialize_managers()

        logger.info(f"Starting enhanced WebSocket server on {self.config.host}:{self.config.port}")
        logger.info(f"Redis connected: {redis_connected}")
        logger.info(f"Market data enabled: {self.config.market_data_enabled}")

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
    logger.info("Enhanced WebSocket server starting up...")
    yield
    # Shutdown
    logger.info("Enhanced WebSocket server shutting down...")

# Global server instance
server_instance: Optional[RealtimeWebSocketServer] = None

async def create_server(config: Optional[EnhancedWebSocketServerConfig] = None) -> RealtimeWebSocketServer:
    """創建增強版WebSocket服務器實例"""
    global server_instance

    if config is None:
        config = EnhancedWebSocketServerConfig()

    server_instance = RealtimeWebSocketServer(config)
    return server_instance

async def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Real-time WebSocket Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--redis-url", default="redis://localhost:6379", help="Redis URL")
    parser.add_argument("--secret-key", default="enhanced-websocket-secret-key", help="Secret key for JWT")
    parser.add_argument("--disable-market-data", action="store_true", help="Disable market data streaming")

    args = parser.parse_args()

    # Create config
    config = EnhancedWebSocketServerConfig(
        host=args.host,
        port=args.port,
        redis_url=args.redis_url,
        secret_key=args.secret_key,
        market_data_enabled=not args.disable_market_data
    )

    # Create and start server
    server = await create_server(config)
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())