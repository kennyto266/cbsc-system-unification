#!/usr/bin/env python3
"""
Phase 8.1 WebSocket實時推送系統 - 後端API集成
Backend API Integrations for Real-time Push System
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable
from contextlib import asynccontextmanager
import json

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .unified_websocket_manager import (
    UnifiedWebSocketManager,
    StreamType,
    unified_ws_manager
)
from .stream_integrations import (
    StreamIntegrationManager,
    get_integration_manager,
    StreamIntegrationConfig
)
from ..api.database import get_async_session
from ..api.models import (
    Strategy,
    StrategyExecution,
    Portfolio,
    RiskMetrics,
    PerformanceMetrics,
    User,
    MarketData
)
from ..backtest.enhanced_backtest_engine import EnhancedBacktestEngine
from ..backtest.risk_management_api import RiskManagementAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyAPIIntegration:
    """策略管理API集成"""

    def __init__(self, ws_manager: UnifiedWebSocketManager):
        self.ws_manager = ws_manager
        self.running_strategies: Dict[str, asyncio.Task] = {}

    async def start_strategy_monitoring(self, strategy_id: int, db: AsyncSession):
        """開始監控策略執行"""
        if strategy_id in self.running_strategies:
            return

        # Get strategy from database
        result = await db.execute(
            select(Strategy)
            .options(selectinload(Strategy.executions))
            .where(Strategy.id == strategy_id)
        )
        strategy = result.scalar_one_or_none()

        if not strategy:
            logger.error(f"Strategy {strategy_id} not found")
            return

        # Start monitoring task
        task = asyncio.create_task(
            self._monitor_strategy_execution(strategy, db)
        )
        self.running_strategies[str(strategy_id)] = task

        logger.info(f"Started monitoring strategy {strategy_id}")

    async def stop_strategy_monitoring(self, strategy_id: int):
        """停止監控策略執行"""
        strategy_key = str(strategy_id)
        if strategy_key in self.running_strategies:
            self.running_strategies[strategy_key].cancel()
            del self.running_strategies[strategy_key]
            logger.info(f"Stopped monitoring strategy {strategy_id}")

    async def _monitor_strategy_execution(self, strategy: Strategy, db: AsyncSession):
        """監控策略執行"""
        while True:
            try:
                # Get latest execution
                result = await db.execute(
                    select(StrategyExecution)
                    .where(StrategyExecution.strategy_id == strategy.id)
                    .order_by(StrategyExecution.created_at.desc())
                    .limit(1)
                )
                execution = result.scalar_one_or_none()

                if execution:
                    # Prepare execution data
                    execution_data = {
                        "strategy_id": str(strategy.id),
                        "strategy_name": strategy.name,
                        "status": execution.status,
                        "execution_time": execution.execution_time,
                        "performance": {
                            "total_return": execution.total_return or 0,
                            "daily_return": execution.daily_return or 0,
                            "win_rate": execution.win_rate or 0,
                            "sharpe_ratio": execution.sharpe_ratio or 0,
                            "max_drawdown": execution.max_drawdown or 0
                        },
                        "signals": execution.signals or [],
                        "positions": execution.positions or [],
                        "progress": execution.progress or 0,
                        "created_at": execution.created_at.isoformat(),
                        "updated_at": execution.updated_at.isoformat()
                    }

                    if execution.error_message:
                        execution_data["error_message"] = execution.error_message

                    # Broadcast to WebSocket
                    await self.ws_manager.broadcast_to_stream(
                        stream_type=StreamType.STRATEGY_EXECUTION.value,
                        raw_data=execution_data,
                        target_users=[strategy.user_id] if strategy.user_id else None
                    )

                await asyncio.sleep(1)  # Check every second

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring strategy {strategy.id}: {e}")
                await asyncio.sleep(5)

class BacktestEngineIntegration:
    """回測引擎集成"""

    def __init__(self, ws_manager: UnifiedWebSocketManager):
        self.ws_manager = ws_manager
        self.backtest_engine = EnhancedBacktestEngine()
        self.running_backtests: Dict[str, asyncio.Task] = {}

    async def start_backtest_monitoring(self, backtest_id: str, user_id: str):
        """開始監控回測執行"""
        if backtest_id in self.running_backtests:
            return

        task = asyncio.create_task(
            self._monitor_backtest_execution(backtest_id, user_id)
        )
        self.running_backtests[backtest_id] = task

        logger.info(f"Started monitoring backtest {backtest_id}")

    async def stop_backtest_monitoring(self, backtest_id: str):
        """停止監控回測執行"""
        if backtest_id in self.running_backtests:
            self.running_backtests[backtest_id].cancel()
            del self.running_backtests[backtest_id]
            logger.info(f"Stopped monitoring backtest {backtest_id}")

    async def _monitor_backtest_execution(self, backtest_id: str, user_id: str):
        """監控回測執行"""
        while True:
            try:
                # Get backtest status from engine
                status = await self.backtest_engine.get_backtest_status(backtest_id)

                if status:
                    # Prepare backtest data
                    backtest_data = {
                        "backtest_id": backtest_id,
                        "status": status["status"],
                        "progress": status.get("progress", 0),
                        "current_step": status.get("current_step", ""),
                        "total_steps": status.get("total_steps", 0),
                        "performance": status.get("performance", {}),
                        "metrics": status.get("metrics", {}),
                        "error_message": status.get("error_message"),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }

                    # Broadcast to WebSocket
                    await self.ws_manager.broadcast_to_stream(
                        stream_type=StreamType.STRATEGY_EXECUTION.value,
                        raw_data=backtest_data,
                        target_users=[user_id]
                    )

                    # If completed, stop monitoring
                    if status["status"] in ["completed", "failed"]:
                        break

                await asyncio.sleep(2)  # Check every 2 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring backtest {backtest_id}: {e}")
                await asyncio.sleep(5)

class RiskManagementIntegration:
    """風險管理集成"""

    def __init__(self, ws_manager: UnifiedWebSocketManager):
        self.ws_manager = ws_manager
        self.risk_api = RiskManagementAPI()
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}

    async def start_portfolio_monitoring(self, portfolio_id: int, db: AsyncSession):
        """開始監控投資組合風險"""
        portfolio_key = str(portfolio_id)
        if portfolio_key in self.monitoring_tasks:
            return

        # Get portfolio from database
        result = await db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.risk_metrics))
            .where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            logger.error(f"Portfolio {portfolio_id} not found")
            return

        # Start monitoring task
        task = asyncio.create_task(
            self._monitor_portfolio_risk(portfolio, db)
        )
        self.monitoring_tasks[portfolio_key] = task

        logger.info(f"Started monitoring portfolio {portfolio_id}")

    async def stop_portfolio_monitoring(self, portfolio_id: int):
        """停止監控投資組合風險"""
        portfolio_key = str(portfolio_id)
        if portfolio_key in self.monitoring_tasks:
            self.monitoring_tasks[portfolio_key].cancel()
            del self.monitoring_tasks[portfolio_key]
            logger.info(f"Stopped monitoring portfolio {portfolio_id}")

    async def _monitor_portfolio_risk(self, portfolio: Portfolio, db: AsyncSession):
        """監控投資組合風險"""
        while True:
            try:
                # Calculate risk metrics
                risk_data = await self.risk_api.calculate_portfolio_risk(
                    portfolio.id,
                    include_positions=True,
                    include_concentration=True
                )

                if risk_data:
                    # Prepare risk data
                    risk_metrics = {
                        "portfolio_id": str(portfolio.id),
                        "portfolio_name": portfolio.name,
                        "risk_metrics": risk_data.get("risk_metrics", {}),
                        "exposure": risk_data.get("exposure", {}),
                        "concentration": risk_data.get("concentration", {}),
                        "alerts": risk_data.get("alerts", []),
                        "risk_score": risk_data.get("risk_score", 0),
                        "stop_loss_triggered": risk_data.get("stop_loss_triggered", False),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }

                    # Save to database
                    await self._save_risk_metrics(portfolio.id, risk_data, db)

                    # Broadcast to WebSocket
                    await self.ws_manager.broadcast_to_stream(
                        stream_type=StreamType.RISK_MONITORING.value,
                        raw_data=risk_metrics,
                        target_users=[portfolio.user_id] if portfolio.user_id else None
                    )

                await asyncio.sleep(5)  # Update every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring portfolio {portfolio.id}: {e}")
                await asyncio.sleep(10)

    async def _save_risk_metrics(self, portfolio_id: int, risk_data: Dict[str, Any], db: AsyncSession):
        """保存風險指標到數據庫"""
        try:
            # Create risk metrics record
            metrics = RiskMetrics(
                portfolio_id=portfolio_id,
                var_95=risk_data.get("risk_metrics", {}).get("var_95"),
                var_99=risk_data.get("risk_metrics", {}).get("var_99"),
                cvar_95=risk_data.get("risk_metrics", {}).get("cvar_95"),
                cvar_99=risk_data.get("risk_metrics", {}).get("cvar_99"),
                volatility=risk_data.get("risk_metrics", {}).get("volatility"),
                beta=risk_data.get("risk_metrics", {}).get("beta"),
                tracking_error=risk_data.get("risk_metrics", {}).get("tracking_error"),
                risk_score=risk_data.get("risk_score"),
                alerts=risk_data.get("alerts", []),
                created_at=datetime.now(timezone.utc)
            )

            db.add(metrics)
            await db.commit()

        except Exception as e:
            logger.error(f"Error saving risk metrics: {e}")
            await db.rollback()

class MarketDataIntegration:
    """市場數據集成"""

    def __init__(self, ws_manager: UnifiedWebSocketManager):
        self.ws_manager = ws_manager
        self.subscribed_symbols: Set[str] = set()
        self.data_feed_task: Optional[asyncio.Task] = None

    async def subscribe_symbols(self, symbols: List[str], db: AsyncSession):
        """訂閱股票代碼"""
        self.subscribed_symbols.update(symbols)

        if not self.data_feed_task and self.subscribed_symbols:
            self.data_feed_task = asyncio.create_task(
                self._market_data_feed_loop(db)
            )

        logger.info(f"Subscribed to symbols: {symbols}")

    async def unsubscribe_symbols(self, symbols: List[str]):
        """取消訂閱股票代碼"""
        for symbol in symbols:
            self.subscribed_symbols.discard(symbol)

        if not self.subscribed_symbols and self.data_feed_task:
            self.data_feed_task.cancel()
            self.data_feed_task = None

        logger.info(f"Unsubscribed from symbols: {symbols}")

    async def _market_data_feed_loop(self, db: AsyncSession):
        """市場數據推送循環"""
        import random
        import numpy as np

        # Initialize prices from database
        prices = {}
        for symbol in self.subscribed_symbols:
            result = await db.execute(
                select(MarketData)
                .where(MarketData.symbol == symbol)
                .order_by(MarketData.timestamp.desc())
                .limit(1)
            )
            latest_data = result.scalar_one_or_none()
            prices[symbol] = latest_data.price if latest_data else random.uniform(100, 500)

        while self.subscribed_symbols:
            try:
                for symbol in list(self.subscribed_symbols):
                    # Simulate price movement
                    change_pct = np.random.normal(0, 0.001)
                    prices[symbol] *= (1 + change_pct)

                    # Generate market data
                    open_price = prices[symbol]
                    close_price = open_price * (1 + np.random.normal(0, 0.0005))
                    volume = random.randint(100000, 5000000)

                    market_data = {
                        "symbol": symbol,
                        "price": round(close_price, 2),
                        "volume": volume,
                        "bid": round(close_price * 0.999, 2),
                        "ask": round(close_price * 1.001, 2),
                        "high": round(open_price * 1.01, 2),
                        "low": round(open_price * 0.99, 2),
                        "open": round(open_price, 2),
                        "close": round(close_price, 2),
                        "change": round(change_pct * open_price, 2),
                        "change_percent": round(change_pct * 100, 2),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }

                    # Save to database
                    await self._save_market_data(symbol, market_data, db)

                    # Broadcast to WebSocket
                    await self.ws_manager.broadcast_to_stream(
                        stream_type=StreamType.MARKET_DATA.value,
                        raw_data=market_data
                    )

                await asyncio.sleep(0.5)  # Update every 500ms

            except Exception as e:
                logger.error(f"Error in market data feed: {e}")
                await asyncio.sleep(1)

    async def _save_market_data(self, symbol: str, data: Dict[str, Any], db: AsyncSession):
        """保存市場數據到數據庫"""
        try:
            market_data = MarketData(
                symbol=symbol,
                price=data["price"],
                volume=data["volume"],
                bid=data["bid"],
                ask=data["ask"],
                high=data["high"],
                low=data["low"],
                open=data["open"],
                close=data["close"],
                change=data["change"],
                change_percent=data["change_percent"],
                timestamp=datetime.fromisoformat(data["timestamp"])
            )

            db.add(market_data)
            await db.commit()

        except Exception as e:
            logger.error(f"Error saving market data: {e}")
            await db.rollback()

class PerformanceTrackingIntegration:
    """性能追蹤集成"""

    def __init__(self, ws_manager: UnifiedWebSocketManager):
        self.ws_manager = ws_manager
        self.tracking_tasks: Dict[str, asyncio.Task] = {}

    async def start_performance_tracking(self, strategy_id: int, db: AsyncSession):
        """開始追蹤策略性能"""
        strategy_key = str(strategy_id)
        if strategy_key in self.tracking_tasks:
            return

        task = asyncio.create_task(
            self._track_strategy_performance(strategy_id, db)
        )
        self.tracking_tasks[strategy_key] = task

        logger.info(f"Started performance tracking for strategy {strategy_id}")

    async def stop_performance_tracking(self, strategy_id: int):
        """停止追蹤策略性能"""
        strategy_key = str(strategy_id)
        if strategy_key in self.tracking_tasks:
            self.tracking_tasks[strategy_key].cancel()
            del self.tracking_tasks[strategy_key]
            logger.info(f"Stopped performance tracking for strategy {strategy_id}")

    async def _track_strategy_performance(self, strategy_id: int, db: AsyncSession):
        """追蹤策略性能"""
        while True:
            try:
                # Calculate performance metrics
                performance_data = await self._calculate_performance_metrics(strategy_id, db)

                if performance_data:
                    # Broadcast to WebSocket
                    await self.ws_manager.broadcast_to_stream(
                        stream_type=StreamType.PERFORMANCE_METRICS.value,
                        raw_data=performance_data
                    )

                    # Save to database
                    await self._save_performance_metrics(strategy_id, performance_data, db)

                await asyncio.sleep(10)  # Update every 10 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error tracking performance for strategy {strategy_id}: {e}")
                await asyncio.sleep(30)

    async def _calculate_performance_metrics(self, strategy_id: int, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """計算性能指標"""
        # This is a simplified implementation
        # In reality, you would fetch historical returns and calculate metrics
        return {
            "strategy_id": str(strategy_id),
            "returns": {
                "daily": 0.005,
                "weekly": 0.02,
                "monthly": 0.08,
                "ytd": 0.15
            },
            "sharpe_ratio": 1.85,
            "max_drawdown": -0.12,
            "win_rate": 0.65,
            "profit_factor": 1.8,
            "calmar_ratio": 1.2,
            "sortino_ratio": 2.1,
            "beta": 1.05,
            "alpha": 0.02,
            "volatility": 0.15,
            "tracking_error": 0.03,
            "information_ratio": 0.67,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def _save_performance_metrics(self, strategy_id: int, data: Dict[str, Any], db: AsyncSession):
        """保存性能指標到數據庫"""
        try:
            metrics = PerformanceMetrics(
                strategy_id=strategy_id,
                daily_return=data["returns"]["daily"],
                weekly_return=data["returns"]["weekly"],
                monthly_return=data["returns"]["monthly"],
                ytd_return=data["returns"]["ytd"],
                sharpe_ratio=data["sharpe_ratio"],
                max_drawdown=data["max_drawdown"],
                win_rate=data["win_rate"],
                profit_factor=data["profit_factor"],
                calmar_ratio=data.get("calmar_ratio"),
                sortino_ratio=data.get("sortino_ratio"),
                beta=data.get("beta"),
                alpha=data.get("alpha"),
                volatility=data.get("volatility"),
                tracking_error=data.get("tracking_error"),
                information_ratio=data.get("information_ratio"),
                created_at=datetime.now(timezone.utc)
            )

            db.add(metrics)
            await db.commit()

        except Exception as e:
            logger.error(f"Error saving performance metrics: {e}")
            await db.rollback()

class APIIntegrationManager:
    """API集成管理器"""

    def __init__(self, ws_manager: UnifiedWebSocketManager):
        self.ws_manager = ws_manager
        self.strategy_integration = StrategyAPIIntegration(ws_manager)
        self.backtest_integration = BacktestEngineIntegration(ws_manager)
        self.risk_integration = RiskManagementIntegration(ws_manager)
        self.market_integration = MarketDataIntegration(ws_manager)
        self.performance_integration = PerformanceTrackingIntegration(ws_manager)

    async def start_all(self):
        """啟動所有集成"""
        logger.info("Starting all API integrations")

    async def stop_all(self):
        """停止所有集成"""
        logger.info("Stopping all API integrations")

        # Stop all monitoring tasks
        for task_id in list(self.strategy_integration.running_strategies.keys()):
            await self.strategy_integration.stop_strategy_monitoring(task_id)

        for task_id in list(self.backtest_integration.running_backtests.keys()):
            await self.backtest_integration.stop_backtest_monitoring(task_id)

        for task_id in list(self.risk_integration.monitoring_tasks.keys()):
            await self.risk_integration.stop_portfolio_monitoring(int(task_id))

        for task_id in list(self.performance_integration.tracking_tasks.keys()):
            await self.performance_integration.stop_performance_tracking(int(task_id))

# Global integration manager
api_integration_manager: Optional[APIIntegrationManager] = None

def get_api_integration_manager(ws_manager: UnifiedWebSocketManager) -> APIIntegrationManager:
    """獲取API集成管理器實例"""
    global api_integration_manager
    if api_integration_manager is None:
        api_integration_manager = APIIntegrationManager(ws_manager)
    return api_integration_manager