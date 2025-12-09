#!/usr/bin/env python3
"""
實時WebSocket服務器 - Real-time WebSocket Server
香港市場實時價格數據流傳輸
Hong Kong Market Real-time Price Data Streaming
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import (
    Dict, List, Optional, Any, Union, Tuple, Callable,
    Set, AsyncIterator, Awaitable
)
from dataclasses import dataclass, asdict
import websockets
from websockets.server import WebSocketServerProtocol
import redis.asyncio as redis
import aioredis
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi import HTTPException, status
import numpy as np
import pandas as pd

# 導入自定義異常和類型
try:
    from exceptions import (
        RealtimeInfraError,
        WebSocketError,
        WebSocketConnectionError,
        WebSocketMessageError,
        WebSocketAuthenticationError,
        WebSocketAuthorizationError,
        create_websocket_context
    )
except ImportError:
    # Fallback if exceptions module not available
    class RealtimeInfraError(Exception):
        pass
    class WebSocketError(RealtimeInfraError):
        pass
    def create_websocket_context(*args, **kwargs):
        return None

# 導入身份驗證模組
from auth import (
    WebSocketAuthenticator,
    WebSocketMiddleware,
    ConnectionContext,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    create_authenticator,
    create_middleware
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RealtimePrice:
    """實時價格數據"""
    symbol: str
    timestamp: datetime
    price: float
    change: float
    change_percent: float
    volume: int
    bid: Optional[float] = None
    ask: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None

@dataclass
class MarketUpdate:
    """市場更新數據"""
    timestamp: datetime
    hsi_index: float
    hsi_change: float
    market_sentiment: str
    total_trades: int
    total_volume: float
    top_gainers: List[str]
    top_losers: List[str]

class ConnectionManager:
    """WebSocket連接管理器 - 支援身份驗證"""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        self.connection_contexts: Dict[WebSocket, Any] = {}
        self.subscriptions: Dict[WebSocket, List[str]] = {}
        self.connection_stats: Dict[str, Union[int, datetime]] = {
            "total_connections": 0,
            "current_connections": 0,
            "authenticated_connections": 0,
            "messages_sent": 0,
            "last_update": datetime.now()
        }

    async def connect(
        self,
        websocket: WebSocket,
        context: Any,  # ConnectionContext
        symbols: Optional[List[str]] = None
    ) -> None:
        """接受經過身份驗證的新連接"""
        try:
            await websocket.accept()
        except Exception as e:
            raise WebSocketConnectionError(
                f"Failed to accept WebSocket connection: {e}",
                context=create_websocket_context("connect", getattr(context, 'user_id', None))
            ) from e

        try:
            self.active_connections.append(websocket)
            self.connection_contexts[websocket] = context
            self.subscriptions[websocket] = symbols or []

            self.connection_stats["current_connections"] = int(
                self.connection_stats["current_connections"]
            ) + 1
            self.connection_stats["total_connections"] = int(
                self.connection_stats["total_connections"]
            ) + 1
            self.connection_stats["authenticated_connections"] = int(
                self.connection_stats["authenticated_connections"]
            ) + 1
            self.connection_stats["last_update"] = datetime.now()

            logger.info(
                f"Authenticated WebSocket connection: user_id={context.user_id}, "
                f"permissions={context.permissions}, Total: {self.connection_stats['current_connections']}"
            )

        except Exception as e:
            # 清理部分成功的操作
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            raise WebSocketConnectionError(
                f"Failed to complete connection setup: {e}",
                context=create_websocket_context("connect", getattr(context, 'user_id', None))
            ) from e

    def disconnect(self, websocket: WebSocket) -> None:
        """斷開連接"""
        context: Any = self.connection_contexts.get(websocket)

        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            if websocket in self.connection_contexts:
                del self.connection_contexts[websocket]
            if websocket in self.subscriptions:
                del self.subscriptions[websocket]

            current_connections = int(
                self.connection_stats.get("current_connections", 0)
            )
            self.connection_stats["current_connections"] = max(0, current_connections - 1)

        except Exception as e:
            logger.error(f"Error during disconnect cleanup: {e}")

        # 記錄斷開連接
        try:
            if context and hasattr(context, 'user_id') and hasattr(context, 'connected_at'):
                session_duration = (datetime.now() - context.connected_at).total_seconds()
                logger.info(
                    f"WebSocket disconnected: user_id={context.user_id}, "
                    f"session_duration={session_duration:.1f}s"
                )
            else:
                logger.info(f"WebSocket disconnected. Total: {self.connection_stats.get('current_connections', 0)}")
        except Exception as e:
            logger.error(f"Error logging disconnect: {e}")

    def get_connection_context(self, websocket: WebSocket) -> Optional[Any]:
        """獲取連接上下文"""
        return self.connection_contexts.get(websocket)

    def update_activity(self, websocket: WebSocket) -> bool:
        """更新連接活動時間"""
        context = self.connection_contexts.get(websocket)
        if context and hasattr(context, 'last_activity'):
            try:
                context.last_activity = datetime.now()
                return True
            except Exception as e:
                logger.error(f"Error updating activity: {e}")
                return False
        return False

    async def send_personal_message(
        self,
        message: str,
        websocket: WebSocket
    ) -> bool:
        """發送個人消息"""
        if not isinstance(message, str):
            raise WebSocketMessageError(
                "Message must be a string",
                context=create_websocket_context(
                    "send_personal_message",
                    getattr(self.connection_contexts.get(websocket), 'user_id', None)
                )
            )

        if websocket not in self.active_connections:
            raise WebSocketConnectionError(
                "WebSocket connection not active",
                context=create_websocket_context(
                    "send_personal_message",
                    getattr(self.connection_contexts.get(websocket), 'user_id', None)
                )
            )

        try:
            await websocket.send_text(message)
            self.connection_stats["messages_sent"] = int(
                self.connection_stats.get("messages_sent", 0)
            ) + 1
            return True
        except WebSocketDisconnect as e:
            logger.warning(f"WebSocket disconnected during send: {e}")
            self.disconnect(websocket)
            return False
        except WebSocketConnectionError as e:
            logger.error(f"WebSocket connection error sending message: {e}")
            self.disconnect(websocket)
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            raise WebSocketMessageError(
                f"Failed to send message: {e}",
                context=create_websocket_context(
                    "send_personal_message",
                    getattr(self.connection_contexts.get(websocket), 'user_id', None)
                ),
                cause=e
            )

    async def broadcast(self, message: Dict[str, Any]) -> int:
        """廣播消息給所有連接，返回成功發送數量"""
        if not isinstance(message, dict):
            raise ValidationError(
                "Message must be a dictionary",
                context=create_websocket_context("broadcast")
            )

        if not self.active_connections:
            return 0

        try:
            message_json: str = json.dumps(message, default=str)
        except (TypeError, ValueError) as e:
            raise WebSocketMessageError(
                f"Failed to serialize broadcast message: {e}",
                context=create_websocket_context("broadcast"),
                cause=e
            )

        disconnected: List[WebSocket] = []
        successful_sends: int = 0

        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
                self.connection_stats["messages_sent"] = int(
                    self.connection_stats.get("messages_sent", 0)
                ) + 1
                successful_sends += 1
            except WebSocketDisconnect as e:
                logger.warning(f"WebSocket disconnected during broadcast: {e}")
                disconnected.append(connection)
            except WebSocketConnectionError as e:
                logger.error(f"WebSocket connection error during broadcast: {e}")
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Unexpected error broadcasting to connection: {e}")
                disconnected.append(connection)

        # 清理斷開的連接
        for connection in disconnected:
            try:
                self.disconnect(connection)
            except Exception as e:
                logger.error(f"Error disconnecting failed connection: {e}")

        return successful_sends

    async def broadcast_to_subscribers(
        self,
        symbol: str,
        data: Dict[str, Any]
    ) -> int:
        """廣播給訂閱特定符號的連接，返回成功發送數量"""
        # 輸入驗證
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValidationError(
                "Symbol must be a non-empty string",
                field="symbol",
                value=symbol,
                context=create_websocket_context("broadcast_to_subscribers")
            )

        if not isinstance(data, dict):
            raise ValidationError(
                "Data must be a dictionary",
                field="data",
                value=data,
                context=create_websocket_context("broadcast_to_subscribers")
            )

        try:
            message_json: str = json.dumps(data, default=str)
        except (TypeError, ValueError) as e:
            raise WebSocketMessageError(
                f"Failed to serialize subscriber message: {e}",
                context=create_websocket_context("broadcast_to_subscribers"),
                cause=e
            )

        disconnected: List[WebSocket] = []
        successful_sends: int = 0

        for websocket, subscribed_symbols in self.subscriptions.items():
            if symbol in subscribed_symbols:
                try:
                    await websocket.send_text(message_json)
                    self.connection_stats["messages_sent"] = int(
                        self.connection_stats.get("messages_sent", 0)
                    ) + 1
                    successful_sends += 1
                except WebSocketDisconnect as e:
                    logger.warning(f"WebSocket subscriber disconnected: {e}")
                    disconnected.append(websocket)
                except WebSocketConnectionError as e:
                    logger.error(f"WebSocket connection error sending to subscriber: {e}")
                    disconnected.append(websocket)
                except Exception as e:
                    logger.error(f"Unexpected error sending to subscriber: {e}")
                    disconnected.append(websocket)

        for connection in disconnected:
            try:
                self.disconnect(connection)
            except Exception as e:
                logger.error(f"Error disconnecting failed subscriber connection: {e}")

        return successful_sends

class RealTimeDataGenerator:
    """實時數據生成器"""

    def __init__(self, redis_client: redis.Redis) -> None:
        if not isinstance(redis_client, redis.Redis):
            raise ValidationError(
                "redis_client must be a valid Redis client",
                field="redis_client",
                value=type(redis_client),
                context=create_cache_context("initialize")
            )

        self.redis = redis_client
        self.symbols: List[str] = [
            "0700.HK", "0941.HK", "1299.HK", "2318.HK", "0388.HK",
            "0005.HK", "1398.HK", "09988.HK", "2628.HK", "3988.HK"
        ]
        self.base_prices: Dict[str, float] = {symbol: 300.0 for symbol in self.symbols}
        self.running: bool = False

    async def generate_realtime_prices(self) -> None:
        """生成實時價格數據"""
        self.running = True

        while self.running:
            try:
                timestamp: datetime = datetime.now()
                price_updates: List[RealtimePrice] = []

                for symbol in self.symbols:
                    try:
                        # 模擬價格變化
                        price_change = np.random.normal(0, 0.5)
                        if not isinstance(price_change, (int, float)):
                            raise DataTransformationError("Invalid price change value generated")

                        self.base_prices[symbol] *= (1 + price_change / 100)

                        # 確保價格不為負數
                        if self.base_prices[symbol] <= 0:
                            self.base_prices[symbol] = 1.0

                        price_data = RealtimePrice(
                            symbol=symbol,
                            timestamp=timestamp,
                            price=round(self.base_prices[symbol], 2),
                            change=round(price_change, 2),
                            change_percent=round(price_change / self.base_prices[symbol] * 100, 2),
                            volume=np.random.randint(1000, 50000),
                            bid=round(self.base_prices[symbol] * 0.999, 2),
                            ask=round(self.base_prices[symbol] * 1.001, 2),
                            high=round(self.base_prices[symbol] * 1.02, 2),
                            low=round(self.base_prices[symbol] * 0.98, 2),
                            open=self.base_prices[symbol]
                        )

                        price_updates.append(price_data)

                        # 存儲到Redis
                        await self._store_price_data(symbol, price_data)

                    except DataTransformationError as e:
                        logger.error(f"Data transformation error for {symbol}: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing symbol {symbol}: {e}")
                        continue

                # 生成市場綜合數據
                if price_updates:
                    try:
                        market_update = self._generate_market_update(price_updates)
                        await self._store_market_data(market_update)

                        # 更新Redis市場指標
                        total_updates = int(await self.redis.hget("realtime:metrics", "total_updates") or 0) + 1
                        await self.redis.hset(
                            "realtime:metrics",
                            {
                                "last_update": timestamp.isoformat(),
                                "total_symbols": len(self.symbols),
                                "total_updates": str(total_updates)
                            }
                        )
                    except CacheError as e:
                        logger.error(f"Cache error updating market metrics: {e}")
                    except Exception as e:
                        logger.error(f"Error updating market metrics: {e}")

                await asyncio.sleep(0.1)  # 100ms更新頻率

            except Exception as e:
                logger.error(f"Critical error in price generation loop: {e}")
                await asyncio.sleep(1)

    async def _store_price_data(self, symbol: str, price_data: RealtimePrice) -> None:
        """存儲價格數據到Redis"""
        # 輸入驗證
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValidationError(
                "Symbol must be a non-empty string",
                field="symbol",
                value=symbol,
                context=create_cache_context("store_price_data", symbol)
            )

        if not isinstance(price_data, RealtimePrice):
            raise ValidationError(
                "price_data must be a RealtimePrice object",
                field="price_data",
                value=type(price_data),
                context=create_cache_context("store_price_data", symbol)
            )

        try:
            # 存儲實時價格
            await self.redis.hset(
                f"realtime:price:{symbol}",
                mapping={
                    "price": str(price_data.price),
                    "change": str(price_data.change),
                    "change_percent": str(price_data.change_percent),
                    "volume": str(price_data.volume),
                    "bid": str(price_data.bid),
                    "ask": str(price_data.ask),
                    "high": str(price_data.high),
                    "low": str(price_data.low),
                    "timestamp": price_data.timestamp.isoformat()
                }
            )

            # 存儲歷史數據（最近1000個點）
            history_key = f"history:price:{symbol}"
            history_data = {
                "timestamp": price_data.timestamp.isoformat(),
                "price": price_data.price,
                "volume": price_data.volume
            }

            try:
                history_json = json.dumps(history_data, default=str)
            except (TypeError, ValueError) as e:
                raise CacheSerializationError(
                    f"Failed to serialize history data for {symbol}: {e}",
                    context=create_cache_context("store_price_data", symbol),
                    cause=e
                )

            await self.redis.lpush(history_key, history_json)
            await self.redis.ltrim(history_key, 0, 999)  # 保持最近1000條記錄

            # 設置過期時間
            await self.redis.expire(history_key, 86400)  # 24小時

        except CacheError:
            # Re-raise cache errors
            raise
        except redis.RedisError as e:
            raise CacheConnectionError(
                f"Redis connection error storing price data for {symbol}: {e}",
                context=create_cache_context("store_price_data", symbol),
                cause=e
            )
        except (TypeError, ValueError) as e:
            raise CacheSerializationError(
                f"Data serialization error for {symbol}: {e}",
                context=create_cache_context("store_price_data", symbol),
                cause=e
            )
        except Exception as e:
            logger.error(f"Unexpected error storing price data for {symbol}: {e}")
            raise CacheError(
                f"Failed to store price data for {symbol}: {e}",
                context=create_cache_context("store_price_data", symbol),
                cause=e
            )

    async def _store_market_data(self, market_update: MarketUpdate) -> None:
        """存儲市場數據到Redis"""
        # 輸入驗證
        if not isinstance(market_update, MarketUpdate):
            raise ValidationError(
                "market_update must be a MarketUpdate object",
                field="market_update",
                value=type(market_update),
                context=create_cache_context("store_market_data")
            )

        try:
            await self.redis.hset(
                "realtime:market",
                mapping={
                    "hsi_index": str(market_update.hsi_index),
                    "hsi_change": str(market_update.hsi_change),
                    "sentiment": market_update.market_sentiment,
                    "total_trades": str(market_update.total_trades),
                    "total_volume": str(market_update.total_volume),
                    "timestamp": market_update.timestamp.isoformat()
                }
            )
        except redis.RedisError as e:
            raise CacheConnectionError(
                f"Redis connection error storing market data: {e}",
                context=create_cache_context("store_market_data"),
                cause=e
            )
        except Exception as e:
            logger.error(f"Unexpected error storing market data: {e}")
            raise CacheError(
                f"Failed to store market data: {e}",
                context=create_cache_context("store_market_data"),
                cause=e
            )

    def _generate_market_update(self, price_updates: List[RealtimePrice]) -> MarketUpdate:
        """生成市場綜合更新"""
        # 輸入驗證
        if not isinstance(price_updates, list):
            raise ValidationError(
                "price_updates must be a list",
                field="price_updates",
                value=type(price_updates),
                context=create_pipeline_context("generate_market_update")
            )

        if not price_updates:
            raise ValidationError(
                "price_updates cannot be empty",
                field="price_updates",
                value=len(price_updates),
                context=create_pipeline_context("generate_market_update")
            )

        for i, update in enumerate(price_updates):
            if not isinstance(update, RealtimePrice):
                raise ValidationError(
                    f"price_updates[{i}] must be a RealtimePrice object",
                    field=f"price_updates[{i}]",
                    value=type(update),
                    context=create_pipeline_context("generate_market_update")
                )

        try:
            # 計算HSI指數（基於樣本股票）
            changes = [p.change_percent for p in price_updates]
            hsi_change = float(np.mean(changes))
            hsi_index = 28000.0 * (1 + hsi_change / 100.0)

            # 確定市場情緒
            if hsi_change > 0.5:
                sentiment: str = "STRONGLY_BULLISH"
            elif hsi_change > 0.1:
                sentiment = "BULLISH"
            elif hsi_change > -0.1:
                sentiment = "NEUTRAL"
            elif hsi_change > -0.5:
                sentiment = "BEARISH"
            else:
                sentiment = "STRONGLY_BEARISH"

            # 找出漲跌最多的股票
            sorted_changes = sorted(price_updates, key=lambda x: x.change_percent, reverse=True)
            top_gainers: List[str] = [p.symbol for p in sorted_changes[:3]]
            top_losers: List[str] = [p.symbol for p in sorted_changes[-3:]]

            total_volume: int = sum(p.volume for p in price_updates)
            total_trades: int = np.random.randint(10000, 50000)

            return MarketUpdate(
                timestamp=datetime.now(),
                hsi_index=round(hsi_index, 2),
                hsi_change=round(hsi_change, 2),
                market_sentiment=sentiment,
                total_trades=total_trades,
                total_volume=total_volume,
                top_gainers=top_gainers,
                top_losers=top_losers
            )

        except (ValueError, TypeError) as e:
            raise DataTransformationError(
                f"Error processing market update calculations: {e}",
                context=create_pipeline_context("generate_market_update"),
                cause=e
            )
        except Exception as e:
            raise DataAggregationError(
                f"Error generating market update: {e}",
                context=create_pipeline_context("generate_market_update"),
                cause=e
            )

    def stop(self) -> None:
        """停止數據生成"""
        self.running = False

class RealtimeWebSocketServer:
    """實時WebSocket服務器 - 支援身份驗證"""

    def __init__(self, secret_key: str = "hong-kong-market-secret-key") -> None:
        # 輸入驗證
        if not isinstance(secret_key, str) or len(secret_key) < 16:
            raise ConfigurationError(
                "Secret key must be a string of at least 16 characters",
                field="secret_key",
                value="***" if secret_key else None,
                context=ErrorContext(operation="initialize", component="websocket_server")
            )

        self.app: FastAPI = FastAPI(title="Hong Kong Real-time Market Data API")
        self.manager: ConnectionManager = ConnectionManager()

        # 設置身份驗證
        self.authenticator: WebSocketAuthenticator = create_authenticator(secret_key)
        self.auth_middleware: WebSocketMiddleware = create_middleware(self.authenticator)

        self.redis_client: Optional[redis.Redis] = None
        self.data_generator: Optional[RealTimeDataGenerator] = None
        self._setup_routes()
        self._setup_auth_routes()

    def _setup_routes(self) -> None:
        """設置API路由"""

        @self.app.get("/")
        async def get() -> HTMLResponse:
            return HTMLResponse("""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>香港實時市場數據</title>
                    <meta charset="utf-8">
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .container { max-width: 1200px; margin: 0 auto; }
                        .market-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
                        .price-card { background: #f5f5f5; padding: 15px; border-radius: 8px; }
                        .price { font-size: 24px; font-weight: bold; color: #333; }
                        .change.positive { color: green; }
                        .change.negative { color: red; }
                        .status { background: #e3f2fd; padding: 10px; border-radius: 5px; margin: 10px 0; }
                        .connection-count { font-weight: bold; color: #1976d2; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>香港實時市場數據</h1>
                        <div class="status">
                            <span class="connection-count">連接數量: <span id="connections">0</span></span>
                            <span style="margin-left: 20px;">最後更新: <span id="lastUpdate">--</span></span>
                        </div>
                        <div class="market-grid" id="priceGrid">
                            <!-- 實時價格數據將在這裡顯示 -->
                        </div>
                        <div id="marketOverview">
                            <h3>市場概況</h3>
                            <p>恆生指數: <span id="hsiIndex">--</span> (<span id="hsiChange">--</span>)</p>
                            <p>市場情緒: <span id="sentiment">--</span></p>
                        </div>
                    </div>

                    <script>
                        const ws = new WebSocket('ws://localhost:8000/ws');
                        const connectionsElement = document.getElementById('connections');
                        const lastUpdateElement = document.getElementById('lastUpdate');
                        const priceGrid = document.getElementById('priceGrid');
                        const hsiIndexElement = document.getElementById('hsiIndex');
                        const hsiChangeElement = document.getElementById('hsiChange');
                        const sentimentElement = document.getElementById('sentiment');

                        let priceCards = {};

                        ws.onmessage = function(event) {
                            const data = JSON.parse(event.data);

                            if (data.type === 'connection_update') {
                                connectionsElement.textContent = data.connections;
                                lastUpdateElement.textContent = new Date().toLocaleTimeString();
                            } else if (data.type === 'market_update') {
                                hsiIndexElement.textContent = data.hsi_index;
                                hsiChangeElement.textContent = data.hsi_change + '%';
                                sentimentElement.textContent = data.sentiment;
                            } else if (data.type === 'price_update') {
                                updatePriceCard(data);
                            }
                        };

                        function updatePriceCard(data) {
                            let card = priceCards[data.symbol];

                            if (!card) {
                                card = document.createElement('div');
                                card.className = 'price-card';
                                card.innerHTML = `
                                    <h4>${data.symbol}</h4>
                                    <div class="price">${data.price}</div>
                                    <div class="change">(${data.change > 0 ? '+' : ''}${data.change_percent.toFixed(2)}%)</div>
                                    <div style="font-size: 12px; color: #666;">
                                        Volume: ${data.volume.toLocaleString()}<br>
                                        Bid: ${data.bid} | Ask: ${data.ask}
                                    </div>
                                `;
                                priceGrid.appendChild(card);
                                priceCards[data.symbol] = card;
                            } else {
                                card.querySelector('.price').textContent = data.price;
                                const changeElement = card.querySelector('.change');
                                changeElement.textContent = `(${data.change > 0 ? '+' : ''}${data.change_percent.toFixed(2)}%)`;
                                changeElement.className = `change ${data.change > 0 ? 'positive' : 'negative'}`;
                                card.querySelector('div[style*="Volume"]').innerHTML =
                                    `Volume: ${data.volume.toLocaleString()}<br>Bid: ${data.bid} | Ask: ${data.ask}`;
                            }
                        }
                    </script>
                </body>
                </html>
            """)

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket) -> None:
            """安全WebSocket端點 - 需要身份驗證"""
            try:
                # 關鍵安全修復：身份驗證
                context = await self.auth_middleware.authenticate_connection(websocket)

                # 接受經過身份驗證的連接
                await self.manager.connect(websocket, context)

                # 發送歡迎消息
                await self.manager.send_personal_message(
                    json.dumps({
                        "type": "authentication_success",
                        "user_id": context.user.user_id,
                        "username": context.user.username,
                        "permissions": context.permissions,
                        "timestamp": datetime.now().isoformat()
                    }),
                    websocket
                )

                try:
                    while True:
                        # 更新活動時間
                        self.manager.update_activity(websocket)

                        # 發送連接狀態更新
                        await self.manager.send_personal_message(
                            json.dumps({
                                "type": "connection_update",
                                "user_id": context.user.user_id,
                                "connections": self.manager.connection_stats["current_connections"],
                                "authenticated_connections": self.manager.connection_stats["authenticated_connections"],
                                "timestamp": datetime.now().isoformat()
                            }),
                            websocket
                        )

                        # 接收客戶端消息（需要輸入驗證）
                        try:
                            data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)

                            # 關鍵安全修復：輸入驗證
                            message = self._validate_websocket_message(data, context)

                            # 處理訂閱請求（需要授權）
                            if message.get("type") == "subscribe":
                                symbols = message.get("symbols", [])

                                # 授權檢查
                                authorized_symbols = self.authenticator.authorize_subscription(context, symbols)
                                self.manager.subscriptions[websocket] = authorized_symbols

                                # 確認訂閱
                                await self.manager.send_personal_message(
                                    json.dumps({
                                        "type": "subscription_confirmed",
                                        "symbols": authorized_symbols,
                                        "message": f"Subscribed to {len(authorized_symbols)} symbols"
                                    }),
                                    websocket
                                )

                        except asyncio.TimeoutError:
                            pass  # 正常超時，繼續循環
                        except ValueError as e:
                            # 輸入驗證錯誤
                            logger.warning(f"Invalid message from {context.user.user_id}: {e}")
                            await self.manager.send_personal_message(
                                json.dumps({
                                    "type": "error",
                                    "error": "Invalid message format",
                                    "details": str(e)
                                }),
                                websocket
                            )
                        except AuthorizationError as e:
                            # 授權錯誤
                            logger.warning(f"Authorization failed for {context.user.user_id}: {e}")
                            await self.manager.send_personal_message(
                                json.dumps({
                                    "type": "authorization_error",
                                    "error": "Authorization failed",
                                    "details": str(e)
                                }),
                                websocket
                            )

                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected by client: user_id={context.user.user_id}")
                except Exception as e:
                    logger.error(f"WebSocket error for user {context.user.user_id}: {e}")

            except AuthenticationError as e:
                # 身份驗證失敗 - 連接已經被中間件關閉
                logger.warning(f"WebSocket authentication failed: {e}")
            except RateLimitError as e:
                # 速率限制 - 連接已經被中間件關閉
                logger.warning(f"WebSocket rate limited: {e}")
            except Exception as e:
                # 未知錯誤
                logger.error(f"WebSocket endpoint error: {e}")
            finally:
                # 確保清理
                try:
                    self.manager.disconnect(websocket)
                except:
                    pass

        @self.app.get("/api/status")
        async def get_status() -> Dict[str, Any]:
            """獲取服務器狀態"""
            return {
                "status": "running",
                "connections": self.manager.connection_stats,
                "timestamp": datetime.now().isoformat(),
                "uptime": "N/A",  # 可以添加運行時間計算
                "redis_connected": self.redis_client is not None
            }

        @self.app.get("/api/symbols")
        async def get_symbols() -> Dict[str, List[str]]:
            """獲取支持的股票代碼"""
            if self.data_generator:
                return {"symbols": self.data_generator.symbols}
            return {"symbols": []}

        @self.app.get("/api/price/{symbol}")
        async def get_current_price(symbol: str) -> Dict[str, Any]:
            """獲取特定股票的當前價格"""
            if not self.redis_client:
                return {"error": "Redis not connected"}

            try:
                price_data = await self.redis_client.hgetall(f"realtime:price:{symbol}")
                if price_data:
                    return {
                        "symbol": symbol,
                        "data": price_data,
                        "timestamp": price_data.get("timestamp")
                    }
                else:
                    return {"error": "Symbol not found"}
            except Exception as e:
                return {"error": str(e)}

        @self.app.get("/api/market")
        async def get_market_data():
            """獲取市場數據"""
            if not self.redis_client:
                return {"error": "Redis not connected"}

            try:
                market_data = await self.redis_client.hgetall("realtime:market")
                return {
                    "market_data": market_data,
                    "timestamp": market_data.get("timestamp") if market_data else None
                }
            except Exception as e:
                return {"error": str(e)}

    async def initialize_redis(self):
        """初始化Redis連接"""
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True
            )

            # 測試連接
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.info("Continuing without Redis...")
            return False

    async def start_data_generation(self):
        """啟動數據生成"""
        if self.redis_client:
            self.data_generator = RealTimeDataGenerator(self.redis_client)

            # 啟動後台任務
            asyncio.create_task(self.data_generator.generate_realtime_prices())

            # 啟動廣播任務
            asyncio.create_task(self._broadcast_loop())

            logger.info("Real-time data generation started")
        else:
            logger.warning("Redis not available, using mock data only")

    async def _broadcast_loop(self):
        """廣播循環"""
        while True:
            try:
                if self.redis_client:
                    # 廣播市場更新
                    market_data = await self.redis_client.hgetall("realtime:market")
                    if market_data:
                        await self.manager.broadcast({
                            "type": "market_update",
                            "hsi_index": float(market_data.get("hsi_index", 0)),
                            "hsi_change": float(market_data.get("hsi_change", 0)),
                            "sentiment": market_data.get("sentiment", "NEUTRAL"),
                            "timestamp": market_data.get("timestamp")
                        })

                    # 廣播價格更新
                    for symbol in self.data_generator.symbols[:3]:  # 只廣播前3個避免過多流量
                        price_data = await self.redis_client.hgetall(f"realtime:price:{symbol}")
                        if price_data:
                            await self.manager.broadcast({
                                "type": "price_update",
                                "symbol": symbol,
                                "price": float(price_data.get("price", 0)),
                                "change": float(price_data.get("change", 0)),
                                "change_percent": float(price_data.get("change_percent", 0)),
                                "volume": int(price_data.get("volume", 0)),
                                "bid": float(price_data.get("bid", 0)),
                                "ask": float(price_data.get("ask", 0))
                            })

                await asyncio.sleep(0.5)  # 500ms廣播間隔

            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(2)

    def _validate_websocket_message(
        self,
        data: str,
        context: Any  # ConnectionContext
    ) -> Dict[str, Any]:
        """驗證WebSocket消息輸入"""
        # 基本類型檢查
        if not isinstance(data, str):
            raise WebSocketMessageError(
                "Message must be a string",
                context=create_websocket_context(
                    "validate_message",
                    getattr(context, 'user_id', None)
                )
            )

        # 大小限制檢查
        if len(data) > 10240:  # 10KB限制
            raise WebSocketMessageError(
                "Message too large (max 10KB)",
                context=create_websocket_context(
                    "validate_message",
                    getattr(context, 'user_id', None)
                )
            )

        # JSON解析
        try:
            message: Dict[str, Any] = json.loads(data)
        except json.JSONDecodeError as e:
            raise WebSocketMessageError(
                f"Invalid JSON format: {str(e)}",
                context=create_websocket_context(
                    "validate_message",
                    getattr(context, 'user_id', None)
                )
            ) from e

        # 結構檢查
        if not isinstance(message, dict):
            raise WebSocketMessageError(
                "Message must be a JSON object",
                context=create_websocket_context(
                    "validate_message",
                    getattr(context, 'user_id', None)
                )
            )

        # 消息類型檢查
        message_type = message.get("type")
        if not isinstance(message_type, str):
            raise WebSocketMessageError(
                "Message type must be a string",
                context=create_websocket_context(
                    "validate_message",
                    getattr(context, 'user_id', None)
                )
            )

        # 特定消息類型驗證
        if message_type == "subscribe":
            symbols = message.get("symbols", [])
            if not isinstance(symbols, list):
                raise WebSocketMessageError(
                    "Symbols must be a list",
                    context=create_websocket_context(
                        "validate_message",
                        getattr(context, 'user_id', None)
                    )
                )

            # 符號列表驗證
            for symbol in symbols:
                if not isinstance(symbol, str):
                    raise WebSocketMessageError(
                        "Each symbol must be a string",
                        context=create_websocket_context(
                            "validate_message",
                            getattr(context, 'user_id', None)
                        )
                    )

                # 符號格式驗證
                if not (3 <= len(symbol) <= 10):
                    raise WebSocketMessageError(
                        f"Invalid symbol format: {symbol} (must be 3-10 characters)",
                        context=create_websocket_context(
                            "validate_message",
                            getattr(context, 'user_id', None)
                        )
                    )

                # 安全性檢查 - 防止注入攻擊
                if any(char in symbol for char in ['<', '>', '"', "'", '\\', '/', '&', ';']):
                    raise WebSocketMessageError(
                        f"Invalid characters in symbol: {symbol} (security violation)",
                        context=create_websocket_context(
                            "validate_message",
                            getattr(context, 'user_id', None)
                        )
                    )

        # 記錄用於審計
        try:
            user_id = getattr(context, 'user_id', 'unknown')
            logger.info(f"Validated message from {user_id}: type={message_type}, size={len(data)}")
        except Exception as e:
            logger.error(f"Error logging validated message: {e}")

        return message

    def _setup_auth_routes(self):
        """設置身份驗證相關路由"""

        @self.app.post("/api/auth/token")
        async def generate_token(request: dict):
            """生成JWT token"""
            try:
                user_id = request.get("user_id")
                password = request.get("password")  # 在實際應用中應該驗證

                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="user_id required"
                    )

                # 檢查用戶存在
                if user_id not in self.authenticator.users:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )

                user = self.authenticator.users[user_id]
                if not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User account is inactive"
                    )

                # 生成token
                token = self.authenticator.generate_jwt_token(user_id)

                return {
                    "token": token,
                    "user_id": user_id,
                    "username": user.username,
                    "permissions": user.permissions,
                    "expires_in": 86400  # 24 hours
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Token generation error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error"
                )

        @self.app.post("/api/auth/api-key")
        async def generate_api_key(request: dict):
            """生成API密鑰"""
            try:
                user_id = request.get("user_id")

                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="user_id required"
                    )

                # 檢查用戶存在
                if user_id not in self.authenticator.users:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )

                # 生成API密鑰
                api_key = self.authenticator.generate_api_key(user_id)

                return {
                    "api_key": api_key,
                    "user_id": user_id
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"API key generation error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error"
                )

        @self.app.get("/api/auth/users")
        async def get_users():
            """獲取用戶列表（僅限管理員）"""
            return {
                "users": [
                    {
                        "user_id": user.user_id,
                        "username": user.username,
                        "permissions": user.permissions,
                        "is_active": user.is_active,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "last_login": user.last_login.isoformat() if user.last_login else None
                    }
                    for user in self.authenticator.users.values()
                ]
            }

        @self.app.get("/api/auth/stats")
        async def get_auth_stats():
            """獲取身份驗證統計信息"""
            return self.authenticator.get_user_stats()

        @self.app.post("/api/auth/demo/setup")
        async def setup_demo():
            """設置演示環境"""
            # 生成演示用戶的token和API密鑰
            demo_credentials = {}

            for user_id in ["user_001", "user_002", "user_003"]:
                try:
                    # 生成JWT token
                    token = self.authenticator.generate_jwt_token(user_id)

                    # 生成API密鑰
                    api_key = self.authenticator.generate_api_key(user_id)

                    user = self.authenticator.users[user_id]
                    demo_credentials[user_id] = {
                        "username": user.username,
                        "permissions": user.permissions,
                        "jwt_token": token,
                        "api_key": api_key,
                        "websocket_url": f"ws://localhost:8000/ws?token={token}",
                        "websocket_url_api_key": f"ws://localhost:8000/ws?api_key={api_key}"
                    }

                except Exception as e:
                    logger.error(f"Error setting up demo for {user_id}: {e}")

            return {
                "demo_credentials": demo_credentials,
                "usage_examples": {
                    "jwt_auth": "ws://localhost:8000/ws?token=YOUR_JWT_TOKEN",
                    "api_key_auth": "ws://localhost:8000/ws?api_key=YOUR_API_KEY"
                },
                "note": "Use either JWT token or API key for WebSocket authentication"
            }

    async def run(self, host: str = "localhost", port: int = 8000):
        """運行服務器"""
        # 初始化Redis
        redis_connected = await self.initialize_redis()

        # 啟動數據生成
        await self.start_data_generation()

        logger.info(f"Starting WebSocket server on {host}:{port}")
        logger.info(f"Redis status: {'Connected' if redis_connected else 'Disconnected (Mock Mode)'}")

        # 運行FastAPI服務器
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )

        server = uvicorn.Server(config)
        await server.serve()

async def main():
    """主函數"""
    server = RealtimeWebSocketServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())