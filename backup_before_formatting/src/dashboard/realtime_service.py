"""
實時服務模組 - WebSocket連接管理
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket


class RealtimeService:
    """實時服務管理器"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.realtime_service")
        self.active_connections: Set[WebSocket] = set()
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    def connect(self, websocket: WebSocket, metadata: Optional[Dict[str, Any]] = None):
        """建立WebSocket連接"""
        try:
            self.active_connections.add(websocket)

            if metadata is None:
                metadata = {}

            metadata.update(
                {
                    "connected_at": datetime.now(),
                    "subscriptions": set(),
                    "last_activity": datetime.now(),
                }
            )

            self.connection_metadata[websocket] = metadata

            self.logger.info(
                f"WebSocket連接已建立，當前連接數: {len(self.active_connections)}"
            )

        except Exception as e:
            self.logger.error(f"建立WebSocket連接失敗: {e}")

    def disconnect(self, websocket: WebSocket):
        """斷開WebSocket連接"""
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]

            self.logger.info(
                f"WebSocket連接已斷開，當前連接數: {len(self.active_connections)}"
            )

        except Exception as e:
            self.logger.error(f"斷開WebSocket連接失敗: {e}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """向特定WebSocket發送個人消息"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            self.logger.error(f"發送消息失敗: {e}")

    async def broadcast(self, message: str, exclude: Optional[WebSocket] = None):
        """廣播消息 - 優化版本"""
        try:
            if not self.active_connections:
                return

            # 使用並發發送消息
            tasks = []
            disconnected = set()

            for connection in self.active_connections:
                if connection != exclude:
                    task = asyncio.create_task(
                        self._send_to_connection(connection, message)
                    )
                    tasks.append((connection, task))

            # 等待所有發送任務完成
            if tasks:
                results = await asyncio.gather(
                    *[task for _, task in tasks], return_exceptions=True
                )

                # 處理結果，標記斷開的連接
                for (connection, _), result in zip(tasks, results):
                    if isinstance(result, Exception):
                        disconnected.add(connection)

            # 批量清理斷開的連接
            for connection in disconnected:
                self.disconnect(connection)

        except Exception as e:
            self.logger.error(f"廣播消息失敗: {e}")

    async def _send_to_connection(self, connection: WebSocket, message: str):
        """向單個連接發送消息"""
        try:
            await connection.send_text(message)
        except Exception as e:
            self.logger.error(f"發送消息到連接失敗: {e}")
            raise

    async def broadcast_to_subscribers(self, message: str, subscription_type: str):
        """向特定訂閱者廣播消息"""
        try:
            disconnected = []

            for connection in self.active_connections:
                if connection in self.connection_metadata:
                    subscriptions = self.connection_metadata[connection].get(
                        "subscriptions", set()
                    )
                    if subscription_type in subscriptions:
                        try:
                            await connection.send_text(message)
                        except Exception as e:
                            self.logger.error(f"發送訂閱消息失敗: {e}")
                            disconnected.append(connection)

            # 清理斷開的連接
            for connection in disconnected:
                self.disconnect(connection)

        except Exception as e:
            self.logger.error(f"向訂閱者廣播消息失敗: {e}")

    def subscribe(self, websocket: WebSocket, subscription_type: str):
        """訂閱特定類型的消息"""
        try:
            if websocket in self.connection_metadata:
                subscriptions = self.connection_metadata[websocket].get(
                    "subscriptions", set()
                )
                subscriptions.add(subscription_type)
                self.connection_metadata[websocket]["subscriptions"] = subscriptions

                self.logger.info(f"WebSocket已訂閱: {subscription_type}")

        except Exception as e:
            self.logger.error(f"訂閱失敗: {e}")

    def unsubscribe(self, websocket: WebSocket, subscription_type: str):
        """取消訂閱特定類型的消息"""
        try:
            if websocket in self.connection_metadata:
                subscriptions = self.connection_metadata[websocket].get(
                    "subscriptions", set()
                )
                subscriptions.discard(subscription_type)
                self.connection_metadata[websocket]["subscriptions"] = subscriptions

                self.logger.info(f"WebSocket已取消訂閱: {subscription_type}")

        except Exception as e:
            self.logger.error(f"取消訂閱失敗: {e}")

    def get_connection_count(self) -> int:
        """獲取當前連接數"""
        return len(self.active_connections)

    def get_connection_info(self) -> Dict[str, Any]:
        """獲取連接信息"""
        try:
            info = {
                "total_connections": len(self.active_connections),
                "connections": [],
            }

            for websocket, metadata in self.connection_metadata.items():
                connection_info = {
                    "connected_at": metadata.get("connected_at"),
                    "last_activity": metadata.get("last_activity"),
                    "subscriptions": list(metadata.get("subscriptions", set())),
                }
                info["connections"].append(connection_info)

            return info

        except Exception as e:
            self.logger.error(f"獲取連接信息失敗: {e}")
            return {"total_connections": 0, "connections": []}

    async def send_market_data(self, symbol: str, data: Dict[str, Any]):
        """發送市場數據"""
        try:
            message = json.dumps(
                {
                    "type": "market_data",
                    "symbol": symbol,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            await self.broadcast_to_subscribers(message, "market_data")

        except Exception as e:
            self.logger.error(f"發送市場數據失敗: {e}")

    async def send_system_alert(
        self, alert_type: str, message: str, severity: str = "info"
    ):
        """發送系統警報"""
        try:
            alert_message = json.dumps(
                {
                    "type": "system_alert",
                    "alert_type": alert_type,
                    "message": message,
                    "severity": severity,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            await self.broadcast_to_subscribers(alert_message, "system_alerts")

        except Exception as e:
            self.logger.error(f"發送系統警報失敗: {e}")

    async def send_trading_signal(self, signal: Dict[str, Any]):
        """發送交易信號"""
        try:
            message = json.dumps(
                {
                    "type": "trading_signal",
                    "signal": signal,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            await self.broadcast_to_subscribers(message, "trading_signals")

        except Exception as e:
            self.logger.error(f"發送交易信號失敗: {e}")

    async def cleanup_inactive_connections(self, timeout_minutes: int = 30):
        """清理非活躍連接"""
        try:
            current_time = datetime.now()
            inactive_connections = []

            for websocket, metadata in self.connection_metadata.items():
                last_activity = metadata.get("last_activity")
                if last_activity:
                    time_diff = current_time - last_activity
                    if time_diff.total_seconds() > timeout_minutes * 60:
                        inactive_connections.append(websocket)

            for connection in inactive_connections:
                self.disconnect(connection)
                self.logger.info(f"清理非活躍連接: {len(inactive_connections)}")

        except Exception as e:
            self.logger.error(f"清理非活躍連接失敗: {e}")


# 全局實時服務實例
realtime_service = RealtimeService()
