#!/usr/bin/env python3
"""
Phase 8.1 WebSocket實時推送系統 - 數據流集成
Stream Integrations for Real-time Push System
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable
from abc import ABC, abstractmethod
import json
from dataclasses import dataclass
from enum import Enum

from .unified_websocket_manager import (
    UnifiedWebSocketManager,
    StreamType,
    unified_ws_manager
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationStatus(str, Enum):
    """集成狀態"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"

@dataclass
class StreamIntegrationConfig:
    """數據流集成配置"""
    enabled: bool = True
    auto_reconnect: bool = True
    reconnect_interval: float = 5.0  # seconds
    max_reconnect_attempts: int = 10
    buffer_size: int = 1000
    batch_size: int = 10
    flush_interval: float = 0.1  # seconds

class BaseStreamIntegration(ABC):
    """數據流集成基類"""

    def __init__(self,
                 stream_type: StreamType,
                 ws_manager: UnifiedWebSocketManager,
                 config: StreamIntegrationConfig):
        self.stream_type = stream_type
        self.ws_manager = ws_manager
        self.config = config
        self.status = IntegrationStatus.DISCONNECTED
        self.running = False
        self.buffer: List[Dict[str, Any]] = []
        self.last_error: Optional[str] = None
        self.reconnect_attempts = 0

    async def start(self):
        """啟動集成"""
        if not self.config.enabled:
            logger.info(f"{self.__class__.__name__} is disabled")
            return

        logger.info(f"Starting {self.__class__.__name__}")
        self.running = True
        self.status = IntegrationStatus.CONNECTING

        try:
            await self._connect()
            self.status = IntegrationStatus.CONNECTED
            self.reconnect_attempts = 0

            # Start background tasks
            asyncio.create_task(self._buffer_flusher())
            asyncio.create_task(self._health_monitor())

        except Exception as e:
            logger.error(f"Failed to start {self.__class__.__name__}: {e}")
            self.status = IntegrationStatus.ERROR
            self.last_error = str(e)

            if self.config.auto_reconnect:
                asyncio.create_task(self._reconnect())

    async def stop(self):
        """停止集成"""
        logger.info(f"Stopping {self.__class__.__name__}")
        self.running = False
        self.status = IntegrationStatus.DISCONNECTED

        try:
            await self._disconnect()
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    async def push_data(self, data: Dict[str, Any], target_users: Optional[List[str]] = None):
        """推送數據到流"""
        if not self.running or self.status != IntegrationStatus.CONNECTED:
            # Buffer data if not connected
            if len(self.buffer) < self.config.buffer_size:
                self.buffer.append({
                    "data": data,
                    "target_users": target_users,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            return

        try:
            # Send to WebSocket manager
            await self.ws_manager.broadcast_to_stream(
                stream_type=self.stream_type.value,
                raw_data=data,
                target_users=target_users
            )

        except Exception as e:
            logger.error(f"Error pushing data: {e}")
            self.last_error = str(e)

    async def _buffer_flusher(self):
        """緩衝區刷新器"""
        while self.running:
            try:
                if self.buffer and self.status == IntegrationStatus.CONNECTED:
                    # Process buffer in batches
                    batch = self.buffer[:self.config.batch_size]
                    self.buffer = self.buffer[self.config.batch_size:]

                    for item in batch:
                        await self.push_data(
                            item["data"],
                            item.get("target_users")
                        )

                await asyncio.sleep(self.config.flush_interval)

            except Exception as e:
                logger.error(f"Error in buffer flusher: {e}")

    async def _health_monitor(self):
        """健康監控"""
        while self.running:
            try:
                # Check connection health
                if await self._check_health():
                    if self.status != IntegrationStatus.CONNECTED:
                        logger.info(f"{self.__class__.__name__} reconnected")
                        self.status = IntegrationStatus.CONNECTED
                        self.reconnect_attempts = 0
                else:
                    if self.status == IntegrationStatus.CONNECTED:
                        logger.warning(f"{self.__class__.__name__} health check failed")
                        self.status = IntegrationStatus.ERROR
                        if self.config.auto_reconnect:
                            asyncio.create_task(self._reconnect())

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Error in health monitor: {e}")

    async def _reconnect(self):
        """重連邏輯"""
        if not self.config.auto_reconnect:
            return

        self.status = IntegrationStatus.RECONNECTING

        while (self.running and
               self.reconnect_attempts < self.config.max_reconnect_attempts):
            self.reconnect_attempts += 1
            logger.info(f"Reconnecting {self.__class__.__name__} (attempt {self.reconnect_attempts})")

            try:
                await asyncio.sleep(self.config.reconnect_interval)
                await self._connect()

                self.status = IntegrationStatus.CONNECTED
                self.reconnect_attempts = 0
                logger.info(f"{self.__class__.__name__} reconnected successfully")
                return

            except Exception as e:
                logger.error(f"Reconnect attempt {self.reconnect_attempts} failed: {e}")
                self.last_error = str(e)

        logger.error(f"Failed to reconnect after {self.reconnect_attempts} attempts")
        self.status = IntegrationStatus.ERROR

    @abstractmethod
    async def _connect(self):
        """連接到數據源"""
        pass

    @abstractmethod
    async def _disconnect(self):
        """斷開連接"""
        pass

    @abstractmethod
    async def _check_health(self) -> bool:
        """檢查連接健康狀態"""
        pass

class StrategyExecutionIntegration(BaseStreamIntegration):
    """策略執行集成"""

    def __init__(self, ws_manager: UnifiedWebSocketManager, config: StreamIntegrationConfig):
        super().__init__(StreamType.STRATEGY_EXECUTION, ws_manager, config)
        self.strategy_monitoring_tasks: Dict[str, asyncio.Task] = {}

    async def _connect(self):
        """連接到策略執行系統"""
        # This would typically connect to a message queue or database
        # For demonstration, we'll simulate strategy executions
        logger.info("Connected to strategy execution system")

    async def _disconnect(self):
        """斷開連接"""
        # Cancel all monitoring tasks
        for task in self.strategy_monitoring_tasks.values():
            task.cancel()
        self.strategy_monitoring_tasks.clear()

    async def _check_health(self) -> bool:
        """檢查健康狀態"""
        # Simulate health check
        return True

    async def start_strategy_monitoring(self, strategy_id: str, strategy_config: Dict[str, Any]):
        """開始監控策略執行"""
        if strategy_id in self.strategy_monitoring_tasks:
            return

        task = asyncio.create_task(
            self._monitor_strategy_execution(strategy_id, strategy_config)
        )
        self.strategy_monitoring_tasks[strategy_id] = task

    async def stop_strategy_monitoring(self, strategy_id: str):
        """停止監控策略執行"""
        if strategy_id in self.strategy_monitoring_tasks:
            self.strategy_monitoring_tasks[strategy_id].cancel()
            del self.strategy_monitoring_tasks[strategy_id]

    async def _monitor_strategy_execution(self, strategy_id: str, config: Dict[str, Any]):
        """監控策略執行（模擬）"""
        import random

        while self.running:
            try:
                # Simulate strategy execution data
                execution_data = {
                    "strategy_id": strategy_id,
                    "status": random.choice(["running", "paused", "executing"]),
                    "execution_time": round(random.uniform(0.01, 0.5), 3),
                    "performance": {
                        "total_return": round(random.uniform(-0.1, 0.2), 4),
                        "daily_return": round(random.uniform(-0.02, 0.03), 4),
                        "win_rate": round(random.uniform(0.4, 0.8), 3)
                    },
                    "signals": [
                        {
                            "symbol": random.choice(["0700.HK", "0941.HK", "1299.HK"]),
                            "action": random.choice(["BUY", "SELL", "HOLD"]),
                            "price": round(random.uniform(100, 500), 2),
                            "confidence": round(random.uniform(0.6, 0.95), 2)
                        }
                    ] if random.random() > 0.7 else [],
                    "progress": random.uniform(0, 1),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                await self.push_data(execution_data)

                # Random pause
                await asyncio.sleep(random.uniform(1, 5))

            except Exception as e:
                logger.error(f"Error monitoring strategy {strategy_id}: {e}")
                await asyncio.sleep(5)

class RiskMonitoringIntegration(BaseStreamIntegration):
    """風險監控集成"""

    def __init__(self, ws_manager: UnifiedWebSocketManager, config: StreamIntegrationConfig):
        super().__init__(StreamType.RISK_MONITORING, ws_manager, config)
        self.portfolio_watchers: Dict[str, asyncio.Task] = {}

    async def _connect(self):
        """連接到風險監控系統"""
        logger.info("Connected to risk monitoring system")

    async def _disconnect(self):
        """斷開連接"""
        for task in self.portfolio_watchers.values():
            task.cancel()
        self.portfolio_watchers.clear()

    async def _check_health(self) -> bool:
        """檢查健康狀態"""
        return True

    async def start_portfolio_monitoring(self, portfolio_id: str, portfolio_config: Dict[str, Any]):
        """開始監控投資組合風險"""
        if portfolio_id in self.portfolio_watchers:
            return

        task = asyncio.create_task(
            self._monitor_portfolio_risk(portfolio_id, portfolio_config)
        )
        self.portfolio_watchers[portfolio_id] = task

    async def _monitor_portfolio_risk(self, portfolio_id: str, config: Dict[str, Any]):
        """監控投資組合風險（模擬）"""
        import random

        while self.running:
            try:
                # Calculate risk metrics
                var_95 = round(random.uniform(0.01, 0.05), 4)
                cvar_95 = round(var_95 * random.uniform(1.2, 1.5), 4)
                volatility = round(random.uniform(0.1, 0.3), 3)

                # Generate alerts if risk is high
                alerts = []
                risk_score = int(random.uniform(20, 80))

                if risk_score > 70:
                    alerts.append({
                        "type": "HIGH_RISK",
                        "message": "Portfolio risk score exceeds threshold",
                        "severity": "HIGH"
                    })

                if var_95 > 0.04:
                    alerts.append({
                        "type": "VAR_WARNING",
                        "message": f"VaR at 95% is {var_95:.2%}",
                        "severity": "MEDIUM"
                    })

                risk_data = {
                    "portfolio_id": portfolio_id,
                    "risk_metrics": {
                        "var_95": var_95,
                        "var_99": round(var_95 * 1.4, 4),
                        "cvar_95": cvar_95,
                        "cvar_99": round(cvar_95 * 1.4, 4),
                        "volatility": volatility,
                        "beta": round(random.uniform(0.8, 1.2), 3),
                        "tracking_error": round(random.uniform(0.02, 0.08), 3)
                    },
                    "exposure": {
                        "equity": round(random.uniform(0.4, 0.8), 3),
                        "fixed_income": round(random.uniform(0.1, 0.4), 3),
                        "alternatives": round(random.uniform(0, 0.2), 3),
                        "cash": round(random.uniform(0.02, 0.1), 3)
                    },
                    "concentration": {
                        "top_10_holdings": round(random.uniform(0.3, 0.7), 3),
                        "sector_concentration": round(random.uniform(0.4, 0.8), 3),
                        "geographic_concentration": round(random.uniform(0.2, 0.6), 3)
                    },
                    "alerts": alerts,
                    "risk_score": risk_score,
                    "stop_loss_triggered": risk_score > 85,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                await self.push_data(risk_data)

                # Update every 5 seconds
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error monitoring portfolio risk {portfolio_id}: {e}")
                await asyncio.sleep(10)

class MarketDataIntegration(BaseStreamIntegration):
    """市場數據集成"""

    def __init__(self, ws_manager: UnifiedWebSocketManager, config: StreamIntegrationConfig):
        super().__init__(StreamType.MARKET_DATA, ws_manager, config)
        self.symbols: List[str] = []
        self.data_feed_task: Optional[asyncio.Task] = None

    async def _connect(self):
        """連接到市場數據源"""
        logger.info("Connected to market data feed")

    async def _disconnect(self):
        """斷開連接"""
        if self.data_feed_task:
            self.data_feed_task.cancel()
            self.data_feed_task = None

    async def _check_health(self) -> bool:
        """檢查健康狀態"""
        return True

    async def subscribe_symbols(self, symbols: List[str]):
        """訂閱股票代碼"""
        self.symbols = list(set(symbols))  # Remove duplicates

        if not self.data_feed_task and self.symbols:
            self.data_feed_task = asyncio.create_task(self._data_feed_loop())

    async def _data_feed_loop(self):
        """市場數據推送循環（模擬）"""
        import random
        import numpy as np

        # Initialize prices
        prices = {symbol: random.uniform(100, 500) for symbol in self.symbols}

        while self.running and self.symbols:
            try:
                for symbol in self.symbols:
                    # Simulate price movement
                    change_pct = np.random.normal(0, 0.002)
                    prices[symbol] *= (1 + change_pct)

                    # Generate OHLCV data
                    open_price = prices[symbol]
                    close_price = open_price * (1 + np.random.normal(0, 0.001))
                    high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.001)))
                    low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.001)))

                    market_data = {
                        "symbol": symbol,
                        "price": round(close_price, 2),
                        "volume": random.randint(100000, 5000000),
                        "bid": round(close_price * 0.999, 2),
                        "ask": round(close_price * 1.001, 2),
                        "high": round(high_price, 2),
                        "low": round(low_price, 2),
                        "open": round(open_price, 2),
                        "close": round(close_price, 2),
                        "change": round(close_price - open_price, 2),
                        "change_percent": round(change_pct * 100, 2),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "market_cap": round(close_price * random.randint(1000000, 10000000)),
                        "pe_ratio": round(random.uniform(10, 30), 2),
                        "dividend_yield": round(random.uniform(0, 0.05), 4)
                    }

                    await self.push_data(market_data)

                # Update every 100ms for real-time feel
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in market data feed: {e}")
                await asyncio.sleep(1)

class SystemNotificationIntegration(BaseStreamIntegration):
    """系統通知集成"""

    def __init__(self, ws_manager: UnifiedWebSocketManager, config: StreamIntegrationConfig):
        super().__init__(StreamType.SYSTEM_NOTIFICATIONS, ws_manager, config)

    async def _connect(self):
        """連接到系統通知服務"""
        logger.info("Connected to system notification service")

    async def _disconnect(self):
        """斷開連接"""
        pass

    async def _check_health(self) -> bool:
        """檢查健康狀態"""
        return True

    async def send_notification(self,
                              notification_type: str,
                              title: str,
                              message: str,
                              target_users: Optional[List[str]] = None,
                              priority: str = "normal",
                              action_required: bool = False,
                              action_url: Optional[str] = None):
        """發送系統通知"""
        notification = {
            "notification_id": f"notif_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": notification_type,  # info, warning, error, success
            "title": title,
            "message": message,
            "action_required": action_required,
            "action_url": action_url,
            "priority": priority,
            "target_users": target_users or [],
            "expires_at": (datetime.now(timezone.utc).timestamp() + 3600),  # 1 hour
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await self.push_data(notification, target_users)

class StreamIntegrationManager:
    """數據流集成管理器"""

    def __init__(self, ws_manager: UnifiedWebSocketManager):
        self.ws_manager = ws_manager
        self.integrations: Dict[StreamType, BaseStreamIntegration] = {}
        self.configs: Dict[StreamType, StreamIntegrationConfig] = {}

    def configure_integration(self, stream_type: StreamType, config: StreamIntegrationConfig):
        """配置數據流集成"""
        self.configs[stream_type] = config

    def get_integration(self, stream_type: StreamType) -> Optional[BaseStreamIntegration]:
        """獲取數據流集成實例"""
        return self.integrations.get(stream_type)

    async def start_integration(self, stream_type: StreamType):
        """啟動數據流集成"""
        if stream_type in self.integrations:
            return self.integrations[stream_type]

        config = self.configs.get(stream_type, StreamIntegrationConfig())

        # Create integration based on stream type
        if stream_type == StreamType.STRATEGY_EXECUTION:
            integration = StrategyExecutionIntegration(self.ws_manager, config)
        elif stream_type == StreamType.RISK_MONITORING:
            integration = RiskMonitoringIntegration(self.ws_manager, config)
        elif stream_type == StreamType.MARKET_DATA:
            integration = MarketDataIntegration(self.ws_manager, config)
        elif stream_type == StreamType.SYSTEM_NOTIFICATIONS:
            integration = SystemNotificationIntegration(self.ws_manager, config)
        else:
            logger.warning(f"No integration available for stream type: {stream_type}")
            return None

        self.integrations[stream_type] = integration
        await integration.start()

        return integration

    async def stop_integration(self, stream_type: StreamType):
        """停止數據流集成"""
        if stream_type in self.integrations:
            await self.integrations[stream_type].stop()
            del self.integrations[stream_type]

    async def start_all(self):
        """啟動所有配置的集成"""
        for stream_type, config in self.configs.items():
            if config.enabled:
                await self.start_integration(stream_type)

    async def stop_all(self):
        """停止所有集成"""
        for stream_type in list(self.integrations.keys()):
            await self.stop_integration(stream_type)

    def get_status(self) -> Dict[str, Any]:
        """獲取所有集成的狀態"""
        return {
            stream_type.value: {
                "status": integration.status.value,
                "last_error": integration.last_error,
                "reconnect_attempts": integration.reconnect_attempts
            }
            for stream_type, integration in self.integrations.items()
        }

# Global integration manager
integration_manager: Optional[StreamIntegrationManager] = None

def get_integration_manager(ws_manager: UnifiedWebSocketManager) -> StreamIntegrationManager:
    """獲取集成管理器實例"""
    global integration_manager
    if integration_manager is None:
        integration_manager = StreamIntegrationManager(ws_manager)
    return integration_manager