#!/usr/bin/env python3
"""
Task 9.2: Real-time Data Push - Market Data Streaming Module
實時數據推送 - 市場數據流模塊
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import redis.asyncio as redis
from collections import defaultdict, deque

from .unified_websocket_manager import (
    UnifiedWebSocketManager,
    StreamType,
    MessageType,
    StreamMessage
)

logger = logging.getLogger(__name__)

class MarketDataType(str, Enum):
    """市場數據類型"""
    QUOTE = "quote"           # 報價數據
    TRADE = "trade"           # 交易數據
    ORDERBOOK = "orderbook"   # 訂單簿數據
    AGGREGATE = "aggregate"   # 聚合數據（K線）
    NEWS = "news"             # 新聞數據
    ECONOMIC = "economic"     # 經濟數據

class DataFrequency(str, Enum):
    """數據頻率"""
    REALTIME = "realtime"    # 實時
    TICK = "tick"            # Tick級別
    SECOND = "1s"            # 1秒
    MINUTE = "1m"            # 1分鐘
    FIVE_MINUTE = "5m"       # 5分鐘
    FIFTEEN_MINUTE = "15m"   # 15分鐘
    HOUR = "1h"              # 1小時
    DAY = "1d"               # 1天

@dataclass
class MarketDataSubscription:
    """市場數據訂閱配置"""
    symbols: Set[str] = field(default_factory=set)
    data_types: Set[MarketDataType] = field(default_factory=set)
    frequency: DataFrequency = DataFrequency.REALTIME
    filters: Dict[str, Any] = field(default_factory=dict)
    max_frequency: Optional[float] = None  # 每秒最大消息數
    last_update: float = field(default_factory=lambda: datetime.now().timestamp())

    def should_update(self, current_time: float) -> bool:
        """檢查是否需要更新（基於頻率限制）"""
        if self.frequency == DataFrequency.REALTIME:
            if self.max_frequency:
                time_diff = current_time - self.last_update
                if time_diff < 1.0 / self.max_frequency:
                    return False
            self.last_update = current_time
            return True
        return True

@dataclass
class MarketDataPoint:
    """市場數據點"""
    symbol: str
    data_type: MarketDataType
    timestamp: datetime
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "symbol": self.symbol,
            "data_type": self.data_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }

class MarketDataSource:
    """市場數據源基類"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.is_connected = False
        self.subscriptions: Dict[str, MarketDataSubscription] = {}

    async def connect(self) -> bool:
        """連接到數據源"""
        raise NotImplementedError

    async def disconnect(self):
        """斷開連接"""
        raise NotImplementedError

    async def subscribe(self, subscription: MarketDataSubscription):
        """訂閱數據"""
        raise NotImplementedError

    async def unsubscribe(self, symbols: List[str]):
        """取消訂閱"""
        raise NotImplementedError

class SimulatedMarketDataSource(MarketDataSource):
    """模擬市場數據源（用於測試）"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("simulated", config or {})
        self.running = False
        self.price_cache: Dict[str, float] = {}

    async def connect(self) -> bool:
        """連接（模擬）"""
        self.is_connected = True
        logger.info("Simulated market data source connected")
        return True

    async def disconnect(self):
        """斷開連接"""
        self.running = False
        self.is_connected = False
        logger.info("Simulated market data source disconnected")

    async def subscribe(self, subscription: MarketDataSubscription):
        """訂閱數據"""
        for symbol in subscription.symbols:
            self.subscriptions[symbol] = subscription
            # 初始化價格
            if symbol not in self.price_cache:
                self.price_cache[symbol] = 100.0 + hash(symbol) % 100

        if not self.running:
            self.running = True
            asyncio.create_task(self._generate_data())

    async def unsubscribe(self, symbols: List[str]):
        """取消訂閱"""
        for symbol in symbols:
            self.subscriptions.pop(symbol, None)

        if not self.subscriptions:
            self.running = False

    async def _generate_data(self):
        """生成模擬數據"""
        while self.running:
            current_time = datetime.now(timezone.utc)

            for symbol, subscription in list(self.subscriptions.items()):
                if not subscription.should_update(current_time.timestamp()):
                    continue

                # 生成價格變化
                base_price = self.price_cache[symbol]
                change = (hash(f"{symbol}{current_time.timestamp()}") % 200 - 100) / 10000
                new_price = base_price * (1 + change)
                self.price_cache[symbol] = new_price

                # 創建數據點
                for data_type in subscription.data_types:
                    if data_type == MarketDataType.QUOTE:
                        data_point = MarketDataPoint(
                            symbol=symbol,
                            data_type=data_type,
                            timestamp=current_time,
                            data={
                                "price": round(new_price, 2),
                                "bid": round(new_price - 0.01, 2),
                                "ask": round(new_price + 0.01, 2),
                                "volume": hash(f"{symbol}{current_time.timestamp()}") % 1000000,
                                "change": round(change * 100, 2)
                            }
                        )
                        await self._on_data_received(data_point)

                    elif data_type == MarketDataType.TRADE:
                        data_point = MarketDataPoint(
                            symbol=symbol,
                            data_type=data_type,
                            timestamp=current_time,
                            data={
                                "price": round(new_price, 2),
                                "volume": hash(f"{symbol}{current_time.timestamp()}") % 10000,
                                "direction": "buy" if change > 0 else "sell",
                                "trade_id": f"trade_{current_time.timestamp()}"
                            }
                        )
                        await self._on_data_received(data_point)

            await asyncio.sleep(0.1)  # 100ms間隔

    async def _on_data_received(self, data_point: MarketDataPoint):
        """數據回調（由子類實現）"""
        pass

class RedisMarketDataSource(MarketDataSource):
    """Redis市場數據源"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("redis", config)
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub = None

    async def connect(self) -> bool:
        """連接到Redis"""
        try:
            self.redis_client = redis.from_url(
                self.config.get("url", "redis://localhost:6379")
            )
            await self.redis_client.ping()
            self.pubsub = self.redis_client.pubsub()
            self.is_connected = True
            logger.info("Redis market data source connected")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False

    async def disconnect(self):
        """斷開Redis連接"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        self.is_connected = False

    async def subscribe(self, subscription: MarketDataSubscription):
        """訂閱Redis頻道"""
        if not self.pubsub:
            return

        for symbol in subscription.symbols:
            for data_type in subscription.data_types:
                channel = f"market:{data_type.value}:{symbol}"
                await self.pubsub.subscribe(channel)
                self.subscriptions[channel] = subscription

        # 啟動監聽任務
        asyncio.create_task(self._listen_messages())

    async def unsubscribe(self, symbols: List[str]):
        """取消訂閱Redis頻道"""
        if not self.pubsub:
            return

        channels_to_unsub = []
        for channel in list(self.subscriptions.keys()):
            if any(symbol in channel for symbol in symbols):
                channels_to_unsub.append(channel)

        if channels_to_unsub:
            await self.pubsub.unsubscribe(*channels_to_unsub)
            for channel in channels_to_unsub:
                self.subscriptions.pop(channel, None)

    async def _listen_messages(self):
        """監聽Redis消息"""
        if not self.pubsub:
            return

        async for message in self.pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    channel = message["channel"]

                    # 解析頻道名稱
                    parts = channel.decode().split(":")
                    if len(parts) >= 3:
                        data_type = MarketDataType(parts[1])
                        symbol = parts[2]

                        data_point = MarketDataPoint(
                            symbol=symbol,
                            data_type=data_type,
                            timestamp=datetime.now(timezone.utc),
                            data=data
                        )

                        await self._on_data_received(data_point)

                except Exception as e:
                    logger.error(f"Error parsing Redis message: {e}")

    async def _on_data_received(self, data_point: MarketDataPoint):
        """數據回調（由子類實現）"""
        pass

class MarketDataStreamer:
    """市場數據流管理器"""

    def __init__(self,
                 ws_manager: UnifiedWebSocketManager,
                 redis_client: Optional[redis.Redis] = None):
        """
        初始化市場數據流管理器

        Args:
            ws_manager: WebSocket管理器
            redis_client: Redis客戶端（可選）
        """
        self.ws_manager = ws_manager
        self.redis_client = redis_client

        # 數據源配置
        self.data_sources: Dict[str, MarketDataSource] = {}
        self.active_subscriptions: Dict[str, MarketDataSubscription] = {}

        # 數據緩存
        self.data_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.latest_data: Dict[str, MarketDataPoint] = {}

        # 統計信息
        self.stats = {
            "messages_processed": 0,
            "messages_sent": 0,
            "subscriptions_active": 0,
            "errors_count": 0,
            "last_reset": datetime.now(timezone.utc)
        }

        # 初始化數據源
        self._initialize_data_sources()

    def _initialize_data_sources(self):
        """初始化數據源"""
        # 添加模擬數據源（用於測試）
        self.data_sources["simulated"] = SimulatedMarketDataSource()

        # 如果有Redis配置，添加Redis數據源
        if self.redis_client:
            redis_config = {"url": "redis://localhost:6379"}
            self.data_sources["redis"] = RedisMarketDataSource(redis_config)

    async def start(self):
        """啟動數據流服務"""
        logger.info("Starting market data streamer...")

        # 連接所有數據源
        for source in self.data_sources.values():
            if await source.connect():
                logger.info(f"Connected to data source: {source.name}")
            else:
                logger.warning(f"Failed to connect to data source: {source.name}")

        # 啟動後台任務
        asyncio.create_task(self._cleanup_task())

    async def stop(self):
        """停止數據流服務"""
        logger.info("Stopping market data streamer...")

        # 斷開所有數據源
        for source in self.data_sources.values():
            await source.disconnect()

    async def subscribe_market_data(self,
                                  user_id: str,
                                  symbols: List[str],
                                  data_types: List[MarketDataType],
                                  frequency: DataFrequency = DataFrequency.REALTIME,
                                  filters: Optional[Dict[str, Any]] = None,
                                  max_frequency: Optional[float] = None) -> bool:
        """
        訂閱市場數據

        Args:
            user_id: 用戶ID
            symbols: 股票代碼列表
            data_types: 數據類型列表
            frequency: 數據頻率
            filters: 過濾條件
            max_frequency: 最大頻率限制

        Returns:
            bool: 訂閱是否成功
        """
        try:
            # 創建訂閱
            subscription = MarketDataSubscription(
                symbols=set(symbols),
                data_types=set(data_types),
                frequency=frequency,
                filters=filters or {},
                max_frequency=max_frequency
            )

            # 存儲訂閱
            subscription_key = f"{user_id}:{hash(str(subscription))}"
            self.active_subscriptions[subscription_key] = subscription

            # 訂閱到數據源
            for source in self.data_sources.values():
                if source.is_connected:
                    await source.subscribe(subscription)

            # 更新統計
            self.stats["subscriptions_active"] = len(self.active_subscriptions)

            logger.info(f"Subscribed user {user_id} to {len(symbols)} symbols")
            return True

        except Exception as e:
            logger.error(f"Error subscribing to market data: {e}")
            self.stats["errors_count"] += 1
            return False

    async def unsubscribe_market_data(self, user_id: str, symbols: Optional[List[str]] = None):
        """
        取消訂閱市場數據

        Args:
            user_id: 用戶ID
            symbols: 要取消的股票代碼（None表示全部）
        """
        try:
            # 找到要取消的訂閱
            to_remove = []
            for key, subscription in self.active_subscriptions.items():
                if key.startswith(f"{user_id}:"):
                    if symbols is None or any(s in subscription.symbols for s in symbols):
                        to_remove.append(key)

            # 移除訂閱
            for key in to_remove:
                subscription = self.active_subscriptions.pop(key)

                # 從數據源取消訂閱
                for source in self.data_sources.values():
                    if source.is_connected:
                        await source.unsubscribe(list(subscription.symbols))

            # 更新統計
            self.stats["subscriptions_active"] = len(self.active_subscriptions)

            logger.info(f"Unsubscribed user {user_id} from {len(to_remove)} subscriptions")

        except Exception as e:
            logger.error(f"Error unsubscribing from market data: {e}")
            self.stats["errors_count"] += 1

    async def broadcast_market_data(self, data_point: MarketDataPoint):
        """
        廣播市場數據到WebSocket客戶端

        Args:
            data_point: 市場數據點
        """
        try:
            # 緩存數據
            cache_key = f"{data_point.symbol}:{data_point.data_type.value}"
            self.data_cache[cache_key].append(data_point)
            self.latest_data[cache_key] = data_point

            # 轉換為StreamMessage
            message = StreamMessage(
                stream_type=StreamType.MARKET_DATA,
                message_type=MessageType.REALTIME_UPDATE,
                data={
                    "market_data": data_point.to_dict(),
                    "source": "market_data_streamer"
                }
            )

            # 廣播到訂閱的客戶端
            sent_count = await self.ws_manager.broadcast_to_stream(
                stream_type=StreamType.MARKET_DATA.value,
                raw_data=message.to_dict()["data"],
                target_users=None  # 廣播給所有訂閱者
            )

            # 更新統計
            self.stats["messages_processed"] += 1
            self.stats["messages_sent"] += sent_count

        except Exception as e:
            logger.error(f"Error broadcasting market data: {e}")
            self.stats["errors_count"] += 1

    async def get_latest_data(self,
                            symbol: str,
                            data_type: MarketDataType) -> Optional[MarketDataPoint]:
        """
        獲取最新數據

        Args:
            symbol: 股票代碼
            data_type: 數據類型

        Returns:
            MarketDataPoint: 最新數據點
        """
        cache_key = f"{symbol}:{data_type.value}"
        return self.latest_data.get(cache_key)

    async def get_historical_data(self,
                                symbol: str,
                                data_type: MarketDataType,
                                limit: int = 100) -> List[MarketDataPoint]:
        """
        獲取歷史數據

        Args:
            symbol: 股票代碼
            data_type: 數據類型
            limit: 返回數量限制

        Returns:
            List[MarketDataPoint]: 歷史數據列表
        """
        cache_key = f"{symbol}:{data_type.value}"
        cache = self.data_cache[cache_key]
        return list(cache)[-limit:] if cache else []

    async def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            **self.stats,
            "active_subscriptions": self.stats["subscriptions_active"],
            "cached_symbols": len(self.latest_data),
            "data_sources": {
                name: {
                    "connected": source.is_connected,
                    "subscriptions": len(source.subscriptions)
                }
                for name, source in self.data_sources.items()
            }
        }

    async def _cleanup_task(self):
        """清理任務"""
        while True:
            try:
                # 清理過期訂閱
                current_time = datetime.now(timezone.utc).timestamp()
                expired = []

                for key, subscription in self.active_subscriptions.items():
                    # 檢查訂閱是否超時（24小時）
                    if current_time - subscription.last_update > 86400:
                        expired.append(key)

                for key in expired:
                    subscription = self.active_subscriptions.pop(key)
                    logger.info(f"Removed expired subscription: {key}")

                # 更新統計
                self.stats["subscriptions_active"] = len(self.active_subscriptions)

                await asyncio.sleep(300)  # 5分鐘清理一次

            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)

# 擴展MarketDataSource以支持數據回調
async def setup_data_source_callbacks(streamer: MarketDataStreamer):
    """設置數據源回調"""
    for source in streamer.data_sources.values():
        if isinstance(source, (SimulatedMarketDataSource, RedisMarketDataSource)):
            # 綁定廣播方法到數據源的回調
            original_on_data_received = source._on_data_received

            async def on_data_received(data_point: MarketDataPoint):
                # 調用原始回調
                await original_on_data_received(data_point)
                # 廣播數據
                await streamer.broadcast_market_data(data_point)

            source._on_data_received = on_data_received

# 創建全局市場數據流管理器實例
market_data_streamer: Optional[MarketDataStreamer] = None

async def get_market_data_streamer(ws_manager: UnifiedWebSocketManager,
                                 redis_client: Optional[redis.Redis] = None) -> MarketDataStreamer:
    """獲取或創建市場數據流管理器實例"""
    global market_data_streamer

    if market_data_streamer is None:
        market_data_streamer = MarketDataStreamer(ws_manager, redis_client)
        await market_data_streamer.start()
        await setup_data_source_callbacks(market_data_streamer)

    return market_data_streamer