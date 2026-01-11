#!/usr/bin/env python3
"""
CBSC策略WebSocket實時服務 (Task #005)
CBSC Strategy WebSocket Real-time Service

提供策略實時狀態推送和監控功能
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, asdict
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .strategy_management_api import (
    Strategy, StrategySignal, StrategyPerformance, StrategyStatus
)
from .strategy_execution_engine import StrategySignal as ExecutionSignal
from .cbsc_strategy_api import StrategyRealTimeStatus, CBSCStrategyManager

logger = logging.getLogger(__name__)

# ============================================================================
# WebSocket消息模型 (WebSocket Message Models)
# ============================================================================

class WebSocketMessage(BaseModel):
    """WebSocket消息基類"""
    type: str
    timestamp: datetime
    data: Dict[str, Any]

class StrategyStatusUpdateMessage(WebSocketMessage):
    """策略狀態更新消息"""
    type: str = "strategy_status_update"
    data: Dict[str, Any]

class StrategySignalMessage(WebSocketMessage):
    """策略信號消息"""
    type: str = "strategy_signal"
    data: Dict[str, Any]

class StrategyPerformanceMessage(WebSocketMessage):
    """策略性能消息"""
    type: str = "strategy_performance_update"
    data: Dict[str, Any]

class MarketDataMessage(WebSocketMessage):
    """市場數據消息"""
    type: str = "market_data_update"
    data: Dict[str, Any]

class SystemStatusMessage(WebSocketMessage):
    """系統狀態消息"""
    type: str = "system_status"
    data: Dict[str, Any]

class ErrorMessage(WebSocketMessage):
    """錯誤消息"""
    type: str = "error"
    data: Dict[str, Any]

# ============================================================================
# 連接管理 (Connection Management)
# ============================================================================

@dataclass
class WebSocketConnection:
    """WebSocket連接"""
    websocket: WebSocket
    user_id: int
    connection_id: str
    connected_at: datetime
    subscribed_strategies: Set[str]
    subscribed_channels: Set[str]
    last_ping: datetime
    is_alive: bool = True

class StrategyWebSocketManager:
    """策略WebSocket管理器"""

    def __init__(self, strategy_manager: CBSCStrategyManager):
        self.strategy_manager = strategy_manager
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[int, Set[str]] = {}  # user_id -> connection_ids
        self.strategy_subscribers: Dict[str, Set[str]] = {}  # strategy_id -> connection_ids

        # 實時數據緩存
        self.strategy_status_cache: Dict[str, StrategyRealTimeStatus] = {}
        self.strategy_performance_cache: Dict[str, StrategyPerformance] = {}
        self.market_data_cache: Dict[str, Any] = {}

        # 廣播任務
        self.broadcast_tasks: List[asyncio.Task] = []
        self.is_running = False

        self.logger = logging.getLogger("strategy_websocket_manager")

    async def connect(self, websocket: WebSocket, user_id: int) -> str:
        """建立WebSocket連接"""
        try:
            await websocket.accept()

            connection_id = str(uuid.uuid4())
            connection = WebSocketConnection(
                websocket=websocket,
                user_id=user_id,
                connection_id=connection_id,
                connected_at=datetime.now(),
                subscribed_strategies=set(),
                subscribed_channels=set(),
                last_ping=datetime.now()
            )

            self.connections[connection_id] = connection

            # 維護用戶連接映射
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)

            self.logger.info(f"WebSocket連接建立: {connection_id} (用戶: {user_id})")

            # 發送歡迎消息
            await self.send_message(connection_id, SystemStatusMessage(
                timestamp=datetime.now(),
                data={
                    "status": "connected",
                    "connection_id": connection_id,
                    "user_id": user_id,
                    "message": "WebSocket連接建立成功"
                }
            ))

            # 發送初始策略狀態
            await self._send_initial_strategy_status(connection_id, user_id)

            return connection_id

        except Exception as e:
            self.logger.error(f"建立WebSocket連接失敗: {e}")
            raise

    async def disconnect(self, connection_id: str):
        """斷開WebSocket連接"""
        try:
            if connection_id not in self.connections:
                return

            connection = self.connections[connection_id]

            # 清理訂閱
            for strategy_id in connection.subscribed_strategies:
                if strategy_id in self.strategy_subscribers:
                    self.strategy_subscribers[strategy_id].discard(connection_id)
                    if not self.strategy_subscribers[strategy_id]:
                        del self.strategy_subscribers[strategy_id]

            # 清理用戶連接
            if connection.user_id in self.user_connections:
                self.user_connections[connection.user_id].discard(connection_id)
                if not self.user_connections[connection.user_id]:
                    del self.user_connections[connection.user_id]

            # 移除連接
            del self.connections[connection_id]

            self.logger.info(f"WebSocket連接斷開: {connection_id}")

        except Exception as e:
            self.logger.error(f"斷開WebSocket連接失敗: {e}")

    async def subscribe_strategy(self, connection_id: str, strategy_id: str) -> bool:
        """訂閱策略"""
        try:
            if connection_id not in self.connections:
                return False

            connection = self.connections[connection_id]
            connection.subscribed_strategies.add(strategy_id)

            # 維護策略訂閱者映射
            if strategy_id not in self.strategy_subscribers:
                self.strategy_subscribers[strategy_id] = set()
            self.strategy_subscribers[strategy_id].add(connection_id)

            # 發送當前策略狀態
            if strategy_id in self.strategy_status_cache:
                await self.send_message(connection_id, StrategyStatusUpdateMessage(
                    timestamp=datetime.now(),
                    data={
                        "strategy_id": strategy_id,
                        "status": self.strategy_status_cache[strategy_id].dict()
                    }
                ))

            self.logger.info(f"連接 {connection_id} 訂閱策略: {strategy_id}")
            return True

        except Exception as e:
            self.logger.error(f"訂閱策略失敗: {e}")
            return False

    async def unsubscribe_strategy(self, connection_id: str, strategy_id: str) -> bool:
        """取消訂閱策略"""
        try:
            if connection_id not in self.connections:
                return False

            connection = self.connections[connection_id]
            connection.subscribed_strategies.discard(strategy_id)

            # 清理策略訂閱者映射
            if strategy_id in self.strategy_subscribers:
                self.strategy_subscribers[strategy_id].discard(connection_id)
                if not self.strategy_subscribers[strategy_id]:
                    del self.strategy_subscribers[strategy_id]

            self.logger.info(f"連接 {connection_id} 取消訂閱策略: {strategy_id}")
            return True

        except Exception as e:
            self.logger.error(f"取消訂閱策略失敗: {e}")
            return False

    async def send_message(self, connection_id: str, message: WebSocketMessage) -> bool:
        """發送消息到指定連接"""
        try:
            if connection_id not in self.connections:
                return False

            connection = self.connections[connection_id]
            if not connection.is_alive:
                return False

            message_data = {
                "type": message.type,
                "timestamp": message.timestamp.isoformat(),
                "data": message.data
            }

            await connection.websocket.send_json(message_data)
            connection.last_ping = datetime.now()

            return True

        except Exception as e:
            self.logger.error(f"發送消息失敗: {e}")
            # 標記連接為死亡
            if connection_id in self.connections:
                self.connections[connection_id].is_alive = False
            return False

    async def broadcast_to_strategy_subscribers(self, strategy_id: str, message: WebSocketMessage):
        """廣播消息給策略訂閱者"""
        try:
            if strategy_id not in self.strategy_subscribers:
                return

            failed_connections = []

            for connection_id in self.strategy_subscribers[strategy_id]:
                if not await self.send_message(connection_id, message):
                    failed_connections.append(connection_id)

            # 清理失敗的連接
            for connection_id in failed_connections:
                await self.disconnect(connection_id)

        except Exception as e:
            self.logger.error(f"廣播消息給策略訂閱者失敗: {e}")

    async def broadcast_to_user(self, user_id: int, message: WebSocketMessage):
        """廣播消息給用戶的所有連接"""
        try:
            if user_id not in self.user_connections:
                return

            failed_connections = []

            for connection_id in self.user_connections[user_id]:
                if not await self.send_message(connection_id, message):
                    failed_connections.append(connection_id)

            # 清理失敗的連接
            for connection_id in failed_connections:
                await self.disconnect(connection_id)

        except Exception as e:
            self.logger.error(f"廣播消息給用戶失敗: {e}")

    async def update_strategy_status(self, strategy_id: str, status: StrategyRealTimeStatus):
        """更新策略狀態並推送"""
        try:
            # 更新緩存
            self.strategy_status_cache[strategy_id] = status

            # 廣播更新
            message = StrategyStatusUpdateMessage(
                timestamp=datetime.now(),
                data={
                    "strategy_id": strategy_id,
                    "status": status.dict()
                }
            )

            await self.broadcast_to_strategy_subscribers(strategy_id, message)

        except Exception as e:
            self.logger.error(f"更新策略狀態失敗: {e}")

    async def push_strategy_signal(self, strategy_id: str, signal: StrategySignal):
        """推送策略信號"""
        try:
            message = StrategySignalMessage(
                timestamp=datetime.now(),
                data={
                    "strategy_id": strategy_id,
                    "signal": signal.dict()
                }
            )

            await self.broadcast_to_strategy_subscribers(strategy_id, message)

        except Exception as e:
            self.logger.error(f"推送策略信號失敗: {e}")

    async def update_strategy_performance(self, strategy_id: str, performance: StrategyPerformance):
        """更新策略性能並推送"""
        try:
            # 更新緩存
            self.strategy_performance_cache[strategy_id] = performance

            # 廣播更新
            message = StrategyPerformanceMessage(
                timestamp=datetime.now(),
                data={
                    "strategy_id": strategy_id,
                    "performance": performance.dict()
                }
            )

            await self.broadcast_to_strategy_subscribers(strategy_id, message)

        except Exception as e:
            self.logger.error(f"更新策略性能失敗: {e}")

    async def push_market_data(self, market_data: Dict[str, Any]):
        """推送市場數據"""
        try:
            # 更新緩存
            self.market_data_cache.update(market_data)

            # 廣播給所有連接
            message = MarketDataMessage(
                timestamp=datetime.now(),
                data=market_data
            )

            failed_connections = []
            for connection_id in self.connections:
                if not await self.send_message(connection_id, message):
                    failed_connections.append(connection_id)

            # 清理失敗的連接
            for connection_id in failed_connections:
                await self.disconnect(connection_id)

        except Exception as e:
            self.logger.error(f"推送市場數據失敗: {e}")

    async def start_real_time_updates(self):
        """啟動實時更新服務"""
        try:
            if self.is_running:
                return

            self.is_running = True
            self.logger.info("啟動實時更新服務")

            # 啟動各種更新任務
            self.broadcast_tasks = [
                asyncio.create_task(self._heartbeat_task()),
                asyncio.create_task(self._strategy_status_monitor_task()),
                asyncio.create_task(self._market_data_simulation_task()),
                asyncio.create_task(self._connection_cleanup_task())
            ]

        except Exception as e:
            self.logger.error(f"啟動實時更新服務失敗: {e}")

    async def stop_real_time_updates(self):
        """停止實時更新服務"""
        try:
            self.is_running = False
            self.logger.info("停止實時更新服務")

            # 取消所有任務
            for task in self.broadcast_tasks:
                task.cancel()

            # 等待任務完成
            await asyncio.gather(*self.broadcast_tasks, return_exceptions=True)
            self.broadcast_tasks.clear()

        except Exception as e:
            self.logger.error(f"停止實時更新服務失敗: {e}")

    async def _send_initial_strategy_status(self, connection_id: str, user_id: int):
        """發送初始策略狀態"""
        try:
            # 獲取用戶策略
            strategies = await self.strategy_manager.get_strategies(user_id)

            for strategy in strategies:
                if strategy.id in self.strategy_status_cache:
                    await self.send_message(connection_id, StrategyStatusUpdateMessage(
                        timestamp=datetime.now(),
                        data={
                            "strategy_id": strategy.id,
                            "status": self.strategy_status_cache[strategy.id].dict()
                        }
                    ))

        except Exception as e:
            self.logger.error(f"發送初始策略狀態失敗: {e}")

    async def _heartbeat_task(self):
        """心跳任務"""
        while self.is_running:
            try:
                heartbeat_message = SystemStatusMessage(
                    timestamp=datetime.now(),
                    data={
                        "type": "heartbeat",
                        "server_time": datetime.now().isoformat()
                    }
                )

                failed_connections = []
                for connection_id in self.connections:
                    if not await self.send_message(connection_id, heartbeat_message):
                        failed_connections.append(connection_id)

                # 清理失敗的連接
                for connection_id in failed_connections:
                    await self.disconnect(connection_id)

                await asyncio.sleep(30)  # 每30秒一次心跳

            except Exception as e:
                self.logger.error(f"心跳任務失敗: {e}")
                await asyncio.sleep(5)

    async def _strategy_status_monitor_task(self):
        """策略狀態監控任務"""
        while self.is_running:
            try:
                # 模擬策略狀態更新
                for strategy_id in list(self.strategy_status_cache.keys()):
                    if strategy_id in self.strategy_subscribers:
                        status = self.strategy_status_cache[strategy_id]

                        # 模擬PnL變化
                        import random
                        pnl_change = random.uniform(-100, 100)
                        status.current_pnl += pnl_change
                        status.daily_pnl += pnl_change * 0.1  # 日內PnL變化較小
                        status.last_updated = datetime.now()

                        await self.update_strategy_status(strategy_id, status)

                await asyncio.sleep(10)  # 每10秒更新一次

            except Exception as e:
                self.logger.error(f"策略狀態監控任務失敗: {e}")
                await asyncio.sleep(5)

    async def _market_data_simulation_task(self):
        """市場數據模擬任務"""
        while self.is_running:
            try:
                import random

                market_data = {
                    "hsi": {
                        "price": 18500 + random.uniform(-200, 200),
                        "change": random.uniform(-0.02, 0.02),
                        "volume": random.randint(1000000, 5000000)
                    },
                    "hsi_futures": {
                        "price": 18600 + random.uniform(-200, 200),
                        "change": random.uniform(-0.02, 0.02),
                        "volume": random.randint(500000, 2000000)
                    },
                    "sentiment": {
                        "bull_ratio": random.uniform(0.3, 0.7),
                        "sentiment_strength": random.uniform(-0.5, 0.5)
                    }
                }

                await self.push_market_data(market_data)
                await asyncio.sleep(5)  # 每5秒更新一次市場數據

            except Exception as e:
                self.logger.error(f"市場數據模擬任務失敗: {e}")
                await asyncio.sleep(5)

    async def _connection_cleanup_task(self):
        """連接清理任務"""
        while self.is_running:
            try:
                current_time = datetime.now()
                dead_connections = []

                for connection_id, connection in self.connections.items():
                    # 檢查連接是否超時（2分鐘無響應）
                    if (current_time - connection.last_ping) > timedelta(minutes=2):
                        dead_connections.append(connection_id)
                    elif not connection.is_alive:
                        dead_connections.append(connection_id)

                # 清理死亡連接
                for connection_id in dead_connections:
                    await self.disconnect(connection_id)

                await asyncio.sleep(60)  # 每分鐘檢查一次

            except Exception as e:
                self.logger.error(f"連接清理任務失敗: {e}")
                await asyncio.sleep(30)

    async def get_connection_stats(self) -> Dict[str, Any]:
        """獲取連接統計信息"""
        try:
            return {
                "total_connections": len(self.connections),
                "active_connections": sum(1 for conn in self.connections.values() if conn.is_alive),
                "user_count": len(self.user_connections),
                "strategy_subscriptions": sum(len(subs) for subs in self.strategy_subscribers.values()),
                "cache_sizes": {
                    "strategy_status": len(self.strategy_status_cache),
                    "strategy_performance": len(self.strategy_performance_cache),
                    "market_data": len(self.market_data_cache)
                }
            }
        except Exception as e:
            self.logger.error(f"獲取連接統計失敗: {e}")
            return {}

# ============================================================================
# WebSocket路由 (WebSocket Routes)
# ============================================================================

class StrategyWebSocketRouter:
    """策略WebSocket路由"""

    def __init__(self, websocket_manager: StrategyWebSocketManager):
        self.websocket_manager = websocket_manager

    async def handle_connection(self, websocket: WebSocket, user_id: int):
        """處理WebSocket連接"""
        connection_id = None
        try:
            # 建立連接
            connection_id = await self.websocket_manager.connect(websocket, user_id)

            # 處理消息循環
            while True:
                try:
                    # 接收客戶端消息
                    data = await websocket.receive_json()

                    await self._handle_client_message(connection_id, data)

                except WebSocketDisconnect:
                    break
                except Exception as e:
                    self.websocket_manager.logger.error(f"處理客戶端消息失敗: {e}")

        except WebSocketDisconnect:
            pass
        except Exception as e:
            self.websocket_manager.logger.error(f"WebSocket連接處理失敗: {e}")
        finally:
            if connection_id:
                await self.websocket_manager.disconnect(connection_id)

    async def _handle_client_message(self, connection_id: str, data: Dict[str, Any]):
        """處理客戶端消息"""
        try:
            message_type = data.get("type")

            if message_type == "subscribe_strategy":
                strategy_id = data.get("strategy_id")
                if strategy_id:
                    await self.websocket_manager.subscribe_strategy(connection_id, strategy_id)

            elif message_type == "unsubscribe_strategy":
                strategy_id = data.get("strategy_id")
                if strategy_id:
                    await self.websocket_manager.unsubscribe_strategy(connection_id, strategy_id)

            elif message_type == "ping":
                # 響應ping
                await self.websocket_manager.send_message(connection_id, SystemStatusMessage(
                    timestamp=datetime.now(),
                    data={"type": "pong", "timestamp": datetime.now().isoformat()}
                ))

            elif message_type == "get_strategy_status":
                strategy_id = data.get("strategy_id")
                if strategy_id and strategy_id in self.websocket_manager.strategy_status_cache:
                    await self.websocket_manager.send_message(connection_id, StrategyStatusUpdateMessage(
                        timestamp=datetime.now(),
                        data={
                            "strategy_id": strategy_id,
                            "status": self.websocket_manager.strategy_status_cache[strategy_id].dict()
                        }
                    ))

            else:
                self.websocket_manager.logger.warning(f"未知消息類型: {message_type}")

        except Exception as e:
            self.websocket_manager.logger.error(f"處理客戶端消息失敗: {e}")

            # 發送錯誤消息
            error_message = ErrorMessage(
                timestamp=datetime.now(),
                data={
                    "error": str(e),
                    "message": "處理消息失敗"
                }
            )
            await self.websocket_manager.send_message(connection_id, error_message)

# ============================================================================
# 導出 (Exports)
# ============================================================================

__all__ = [
    "WebSocketMessage",
    "StrategyStatusUpdateMessage",
    "StrategySignalMessage",
    "StrategyPerformanceMessage",
    "MarketDataMessage",
    "SystemStatusMessage",
    "ErrorMessage",
    "WebSocketConnection",
    "StrategyWebSocketManager",
    "StrategyWebSocketRouter"
]