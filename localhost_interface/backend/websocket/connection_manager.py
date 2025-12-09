"""
WebSocket連接管理器
管理客戶端WebSocket連接和數據廣播
"""

import json
import asyncio
import logging
from typing import Dict, List, Set, Any, Optional
from datetime import datetime
import uuid
from fastapi import WebSocket, WebSocketDisconnect

from shared.models.schemas import WebSocketMessage, TradingSignal, MarketDataPoint

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket連接管理器"""

    def __init__(self):
        # 存儲活躍的WebSocket連接
        self.active_connections: Dict[str, WebSocket] = {}

        # 存儲客戶端訂閱信息
        # {client_id: {symbol: [data_types]}}
        self.client_subscriptions: Dict[str, Dict[str, Set[str]]] = {}

        # 存儲符號訂閱者列表
        # {symbol: {data_type: {client_ids}}}
        self.symbol_subscribers: Dict[str, Dict[str, Set[str]]] = {}

        # 連接元數據
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}

        # 速率限制
        self.rate_limits: Dict[str, List[datetime]] = {}

        logger.info("WebSocket連接管理器初始化完成")

    async def connect(self, websocket: WebSocket, client_id: str, user_info: Optional[Dict[str, Any]] = None):
        """接受新的WebSocket連接"""
        try:
            await websocket.accept()

            # 檢查是否已存在連接，如果存在則斷開舊連接
            if client_id in self.active_connections:
                await self.disconnect(client_id)
                logger.warning(f"客戶端 {client_id} 已有連接，斷開舊連接")

            # 建立新連接
            self.active_connections[client_id] = websocket
            self.client_subscriptions[client_id] = {}

            # 存儲連接元數據
            self.connection_metadata[client_id] = {
                "connected_at": datetime.now(),
                "last_heartbeat": datetime.now(),
                "ip_address": getattr(websocket.client, "host", "unknown"),
                "user_info": user_info or {},
                "message_count": 0,
                "bytes_sent": 0
            }

            # 初始化速率限制
            self.rate_limits[client_id] = []

            # 發送歡迎消息
            welcome_message = {
                "type": "welcome",
                "client_id": client_id,
                "server_time": datetime.now().isoformat(),
                "message": "WebSocket連接已建立"
            }

            await self.send_personal_message(welcome_message, client_id)

            logger.info(f"客戶端 {client_id} 已連接WebSocket，總連接數: {len(self.active_connections)}")

        except Exception as e:
            logger.error(f"建立WebSocket連接失敗: {e}")
            raise

    async def disconnect(self, client_id: str):
        """斷開WebSocket連接並清理資源"""
        try:
            # 移除所有訂閱
            if client_id in self.client_subscriptions:
                for symbol, data_types in self.client_subscriptions[client_id].items():
                    for data_type in data_types:
                        self._remove_symbol_subscriber(symbol, data_type, client_id)

            # 清理連接數據
            self.active_connections.pop(client_id, None)
            self.client_subscriptions.pop(client_id, None)
            self.connection_metadata.pop(client_id, None)
            self.rate_limits.pop(client_id, None)

            logger.info(f"客戶端 {client_id} 已斷開連接，剩餘連接數: {len(self.active_connections)}")

        except Exception as e:
            logger.error(f"斷開WebSocket連接時發生錯誤: {e}")

    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """向特定客戶端發送消息"""
        try:
            if client_id in self.active_connections:
                websocket = self.active_connections[client_id]

                # 檢查速率限制
                if not self._check_rate_limit(client_id):
                    logger.warning(f"客戶端 {client_id} 超過速率限制")
                    return

                # 發送消息
                message_json = json.dumps(message, default=str, ensure_ascii=False)
                await websocket.send_text(message_json)

                # 更新統計
                if client_id in self.connection_metadata:
                    self.connection_metadata[client_id]["message_count"] += 1
                    self.connection_metadata[client_id]["bytes_sent"] += len(message_json.encode('utf-8'))
                    self.connection_metadata[client_id]["last_heartbeat"] = datetime.now()

                logger.debug(f"向客戶端 {client_id} 發送消息: {message.get('type', 'unknown')}")
            else:
                logger.warning(f"客戶端 {client_id} 不存在，無法發送消息")

        except Exception as e:
            logger.error(f"向客戶端 {client_id} 發送消息失敗: {e}")
            # 連接可能已斷開，清理資源
            await self.disconnect(client_id)

    async def broadcast_message(self, message: Dict[str, Any], exclude_clients: Optional[List[str]] = None):
        """向所有連接的客戶端廣播消息"""
        exclude_clients = exclude_clients or []

        # 創建發送任務列表
        tasks = []
        for client_id in self.active_connections:
            if client_id not in exclude_clients:
                tasks.append(self.send_personal_message(message, client_id))

        # 並發執行所有發送任務
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.debug(f"向 {len(tasks)} 個客戶端廣播消息: {message.get('type', 'unknown')}")
            except Exception as e:
                logger.error(f"廣播消息時發生錯誤: {e}")

    async def broadcast_to_symbol_subscribers(self, symbol: str, data_type: str, message: Dict[str, Any]):
        """向特定符號的訂閱者廣播消息"""
        if symbol in self.symbol_subscribers and data_type in self.symbol_subscribers[symbol]:
            subscribers = self.symbol_subscribers[symbol][data_type]

            if subscribers:
                # 添加符號和數據類型到消息中
                enhanced_message = {
                    **message,
                    "symbol": symbol,
                    "data_type": data_type,
                    "broadcast_to": f"{symbol}_{data_type}"
                }

                tasks = []
                for client_id in list(subscribers):  # 使用list避免迭代時修改
                    tasks.append(self.send_personal_message(enhanced_message, client_id))

                if tasks:
                    try:
                        await asyncio.gather(*tasks, return_exceptions=True)
                        logger.debug(f"向 {symbol} 的 {len(subscribers)} 個 {data_type} 訂閱者廣播消息")
                    except Exception as e:
                        logger.error(f"向符號訂閱者廣播消息時發生錯誤: {e}")

    def add_subscription(self, client_id: str, symbol: str, data_type: str):
        """添加客戶端訂閱"""
        try:
            # 初始化客戶端訂閱
            if client_id not in self.client_subscriptions:
                self.client_subscriptions[client_id] = {}

            if symbol not in self.client_subscriptions[client_id]:
                self.client_subscriptions[client_id][symbol] = set()

            self.client_subscriptions[client_id][symbol].add(data_type)

            # 添加到符號訂閱者列表
            self._add_symbol_subscriber(symbol, data_type, client_id)

            logger.info(f"客戶端 {client_id} 訂閱了 {symbol} 的 {data_type}")

        except Exception as e:
            logger.error(f"添加訂閱失敗: {e}")

    def remove_subscription(self, client_id: str, symbol: str, data_type: str):
        """移除客戶端訂閱"""
        try:
            # 從客戶端訂閱中移除
            if (client_id in self.client_subscriptions and
                symbol in self.client_subscriptions[client_id] and
                data_type in self.client_subscriptions[client_id][symbol]):

                self.client_subscriptions[client_id][symbol].remove(data_type)

                # 如果符號沒有其他訂閱，移除符號
                if not self.client_subscriptions[client_id][symbol]:
                    del self.client_subscriptions[client_id][symbol]

            # 從符號訂閱者列表中移除
            self._remove_symbol_subscriber(symbol, data_type, client_id)

            logger.info(f"客戶端 {client_id} 取消訂閱了 {symbol} 的 {data_type}")

        except Exception as e:
            logger.error(f"移除訂閱失敗: {e}")

    async def broadcast_signals(self, signals: List[TradingSignal]):
        """廣播交易信號"""
        try:
            for signal in signals:
                # 將Pydantic模型轉換為字典
                signal_dict = signal.dict()

                # 創建信號消息
                message = {
                    "type": "trading_signal",
                    "timestamp": datetime.now().isoformat(),
                    "data": signal_dict
                }

                # 向信號符號的訂閱者廣播
                await self.broadcast_to_symbol_subscribers(
                    signal.symbol,
                    "signals",
                    message
                )

        except Exception as e:
            logger.error(f"廣播交易信號失敗: {e}")

    async def broadcast_market_data(self, market_data: List[MarketDataPoint]):
        """廣播市場數據"""
        try:
            # 按符號分組市場數據
            data_by_symbol = {}
            for data_point in market_data:
                if data_point.symbol not in data_by_symbol:
                    data_by_symbol[data_point.symbol] = []
                data_by_symbol[data_point.symbol].append(data_point.dict())

            # 分別廣播給各符號的訂閱者
            for symbol, data_points in data_by_symbol.items():
                message = {
                    "type": "market_data",
                    "timestamp": datetime.now().isoformat(),
                    "data": data_points
                }

                await self.broadcast_to_symbol_subscribers(
                    symbol,
                    "market_data",
                    message
                )

        except Exception as e:
            logger.error(f"廣播市場數據失敗: {e}")

    async def send_heartbeat(self):
        """發送心跳檢查"""
        heartbeat_message = {
            "type": "heartbeat",
            "timestamp": datetime.now().isoformat(),
            "server_status": "healthy"
        }

        await self.broadcast_message(heartbeat_message)

    def get_connection_stats(self) -> Dict[str, Any]:
        """獲取連接統計信息"""
        total_subscriptions = sum(
            len(subscriptions.values())
            for subscriptions in self.client_subscriptions.values()
        )

        symbol_stats = {}
        for symbol, data_types in self.symbol_subscribers.items():
            symbol_stats[symbol] = {
                data_type: len(subscribers)
                for data_type, subscribers in data_types.items()
            }

        return {
            "total_connections": len(self.active_connections),
            "total_subscriptions": total_subscriptions,
            "connections_by_user": {
                client_id: metadata.get("user_info", {}).get("username", "unknown")
                for client_id, metadata in self.connection_metadata.items()
            },
            "symbol_subscriptions": symbol_stats,
            "uptime": datetime.now().isoformat() if self.connection_metadata else None
        }

    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """獲取客戶端信息"""
        if client_id in self.connection_metadata:
            metadata = self.connection_metadata[client_id].copy()
            metadata["subscriptions"] = dict(
                (symbol, list(data_types))
                for symbol, data_types in self.client_subscriptions.get(client_id, {}).items()
            )
            return metadata
        return None

    def _add_symbol_subscriber(self, symbol: str, data_type: str, client_id: str):
        """添加符號訂閱者（內部方法）"""
        if symbol not in self.symbol_subscribers:
            self.symbol_subscribers[symbol] = {}

        if data_type not in self.symbol_subscribers[symbol]:
            self.symbol_subscribers[symbol][data_type] = set()

        self.symbol_subscribers[symbol][data_type].add(client_id)

    def _remove_symbol_subscriber(self, symbol: str, data_type: str, client_id: str):
        """移除符號訂閱者（內部方法）"""
        if (symbol in self.symbol_subscribers and
            data_type in self.symbol_subscribers[symbol] and
            client_id in self.symbol_subscribers[symbol][data_type]):

            self.symbol_subscribers[symbol][data_type].remove(client_id)

            # 如果數據類型沒有其他訂閱者，移除數據類型
            if not self.symbol_subscribers[symbol][data_type]:
                del self.symbol_subscribers[symbol][data_type]

            # 如果符號沒有其他訂閱，移除符號
            if not self.symbol_subscribers[symbol]:
                del self.symbol_subscribers[symbol]

    def _check_rate_limit(self, client_id: str) -> bool:
        """檢查客戶端速率限制（內部方法）"""
        try:
            now = datetime.now()

            # 清理舊的速率限制記錄（1分鐘前）
            if client_id in self.rate_limits:
                self.rate_limits[client_id] = [
                    timestamp for timestamp in self.rate_limits[client_id]
                    if (now - timestamp).total_seconds() < 60
                ]
            else:
                self.rate_limits[client_id] = []

            # 檢查1分鐘內是否超過100條消息
            if len(self.rate_limits[client_id]) < 100:
                self.rate_limits[client_id].append(now)
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"檢查速率限制失敗: {e}")
            return True  # 出錯時允許發送