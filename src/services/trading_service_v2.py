"""
Trading Service v2.0
Integrates real-time trading engine with broker APIs
Phase 5.1 - 實施回測引擎集成
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, UUID
from uuid import uuid4
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database import get_db
from ..models.strategy_models import Strategy, StrategyInstance
from ..models.trading_models_v2 import (
    Trade, Order, Position, Portfolio, BrokerAccount
)
from ..trading.realtime_trading_engine import (
    RealtimeTradingEngine, LiveSignal, Order as TradingOrder,
    OrderSide, OrderStatus, PositionStatus
)
from .cache_service import CacheService

logger = logging.getLogger(__name__)


class TradingServiceV2:
    """Enhanced trading service integrated with real-time engine and broker APIs"""

    def __init__(self, db: Session):
        """Initialize trading service"""
        self.db = db
        self.cache_service = CacheService()
        self.trading_engines: Dict[str, RealtimeTradingEngine] = {}
        self.active_orders: Dict[str, TradingOrder] = {}
        self.market_data_subscriptions: Dict[str, List[str]] = {}

    async def initialize_trading_session(
        self,
        strategy_instance_id: UUID,
        broker_config: Dict[str, Any],
        initial_capital: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Initialize trading session for a strategy instance

        Args:
            strategy_instance_id: Strategy instance to trade
            broker_config: Broker configuration (API keys, credentials)
            initial_capital: Starting capital (if not provided, use from instance)

        Returns:
            Initialization status and trading session details
        """
        try:
            # Get strategy instance
            instance = self.db.query(StrategyInstance).filter(
                StrategyInstance.id == strategy_instance_id
            ).first()

            if not instance:
                raise ValueError(f"Strategy instance {strategy_instance_id} not found")

            # Get or create broker account
            broker_account = await self._get_or_create_broker_account(
                instance.user_id,
                broker_config
            )

            # Set initial capital
            if initial_capital is None:
                initial_capital = instance.parameters.get("initial_capital", 100000.0)

            # Initialize trading engine
            trading_engine = RealtimeTradingEngine(initial_capital=initial_capital)

            # Store engine
            self.trading_engines[str(strategy_instance_id)] = trading_engine

            # Create portfolio record
            portfolio = Portfolio(
                strategy_instance_id=strategy_instance_id,
                broker_account_id=broker_account.id,
                initial_capital=initial_capital,
                current_capital=initial_capital,
                status="active",
                created_at=datetime.utcnow()
            )
            self.db.add(portfolio)
            self.db.commit()

            # Cache session info
            await self.cache_service.set(
                f"trading_session:{strategy_instance_id}",
                {
                    "status": "active",
                    "portfolio_id": str(portfolio.id),
                    "broker_account_id": str(broker_account.id),
                    "initial_capital": initial_capital,
                    "session_started": datetime.utcnow().isoformat()
                },
                ttl=3600
            )

            logger.info(f"Trading session initialized for instance {strategy_instance_id}")

            return {
                "status": "success",
                "session_id": str(portfolio.id),
                "strategy_instance_id": str(strategy_instance_id),
                "initial_capital": initial_capital,
                "broker_account_id": str(broker_account.id),
                "trading_active": False  # Need to start trading separately
            }

        except Exception as e:
            logger.error(f"Failed to initialize trading session: {e}")
            return {
                "status": "error",
                "error": str(e),
                "strategy_instance_id": str(strategy_instance_id)
            }

    async def start_trading(
        self,
        strategy_instance_id: UUID,
        market_data_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start live trading for a strategy instance

        Args:
            strategy_instance_id: Strategy instance to start trading
            market_data_config: Market data subscription configuration

        Returns:
            Trading start status
        """
        try:
            instance_key = str(strategy_instance_id)

            if instance_key not in self.trading_engines:
                return {
                    "status": "error",
                    "message": "Trading session not initialized",
                    "instance_id": instance_key
                }

            trading_engine = self.trading_engines[instance_key]

            # Start trading engine
            await trading_engine.start_trading()

            # Set up market data subscriptions
            if market_data_config:
                symbols = market_data_config.get("symbols", [])
                await self._setup_market_data_subscriptions(instance_key, symbols)

            # Update portfolio status
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.strategy_instance_id == strategy_instance_id,
                Portfolio.status == "active"
            ).first()

            if portfolio:
                portfolio.trading_started_at = datetime.utcnow()
                portfolio.status = "trading"
                self.db.commit()

            # Cache trading status
            await self.cache_service.set(
                f"trading_status:{strategy_instance_id}",
                {
                    "trading_active": True,
                    "started_at": datetime.utcnow().isoformat(),
                    "market_data_symbols": symbols if market_data_config else []
                },
                ttl=3600
            )

            logger.info(f"Trading started for instance {strategy_instance_id}")

            return {
                "status": "success",
                "instance_id": instance_key,
                "trading_active": True,
                "started_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to start trading: {e}")
            return {
                "status": "error",
                "error": str(e),
                "instance_id": str(strategy_instance_id)
            }

    async def stop_trading(
        self,
        strategy_instance_id: UUID,
        close_positions: bool = True
    ) -> Dict[str, Any]:
        """
        Stop live trading for a strategy instance

        Args:
            strategy_instance_id: Strategy instance to stop trading
            close_positions: Whether to close all open positions

        Returns:
            Trading stop status
        """
        try:
            instance_key = str(strategy_instance_id)

            if instance_key not in self.trading_engines:
                return {
                    "status": "warning",
                    "message": "No active trading session",
                    "instance_id": instance_key
                }

            trading_engine = self.trading_engines[instance_key]

            # Stop trading
            await trading_engine.stop_trading()

            # Get portfolio summary before closing
            portfolio_summary = trading_engine.get_portfolio_summary()

            # Close positions if requested
            closed_positions = []
            if close_positions:
                await trading_engine.close_all_positions()
                closed_positions = list(trading_engine.position_manager.positions.keys())

            # Update portfolio status
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.strategy_instance_id == strategy_instance_id
            ).first()

            if portfolio:
                portfolio.status = "stopped"
                portfolio.stopped_at = datetime.utcnow()
                portfolio.final_capital = portfolio_summary["portfolio_value"]
                portfolio.total_pnl = portfolio_summary["total_pnl"]
                self.db.commit()

            # Clean up cache
            await self.cache_service.delete(f"trading_status:{strategy_instance_id}")

            logger.info(f"Trading stopped for instance {strategy_instance_id}")

            return {
                "status": "success",
                "instance_id": instance_key,
                "trading_active": False,
                "stopped_at": datetime.utcnow().isoformat(),
                "final_portfolio_value": portfolio_summary["portfolio_value"],
                "total_pnl": portfolio_summary["total_pnl"],
                "closed_positions": closed_positions
            }

        except Exception as e:
            logger.error(f"Failed to stop trading: {e}")
            return {
                "status": "error",
                "error": str(e),
                "instance_id": str(strategy_instance_id)
            }

    async def execute_signal(
        self,
        strategy_instance_id: UUID,
        signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute trading signal from strategy

        Args:
            strategy_instance_id: Strategy instance
            signal: Trading signal data

        Returns:
            Execution result
        """
        try:
            instance_key = str(strategy_instance_id)

            if instance_key not in self.trading_engines:
                return {
                    "status": "error",
                    "message": "No active trading session",
                    "instance_id": instance_key
                }

            trading_engine = self.trading_engines[instance_key]

            # Convert signal to LiveSignal
            live_signal = LiveSignal(
                symbol=signal["symbol"],
                timestamp=datetime.fromisoformat(signal["timestamp"]) if isinstance(signal["timestamp"], str) else signal["timestamp"],
                direction=signal["direction"],
                confidence=signal.get("confidence", 1.0),
                entry_price=signal["entry_price"],
                target_price=signal.get("target_price"),
                stop_loss=signal.get("stop_loss"),
                position_size=signal["position_size"],
                reason=signal.get("reason", ""),
                source=signal.get("source", "STRATEGY"),
                alt_data_inputs=signal.get("alt_data_inputs", {})
            )

            # Process signal
            order_id = await trading_engine.process_signal(live_signal)

            # Record execution in database
            if order_id:
                await self._record_execution(strategy_instance_id, signal, order_id)

            return {
                "status": "success",
                "instance_id": instance_key,
                "signal_id": signal.get("id"),
                "order_id": order_id,
                "executed": order_id is not None
            }

        except Exception as e:
            logger.error(f"Failed to execute signal: {e}")
            return {
                "status": "error",
                "error": str(e),
                "instance_id": str(strategy_instance_id)
            }

    async def update_market_prices(
        self,
        strategy_instance_id: UUID,
        prices: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Update market prices for open positions

        Args:
            strategy_instance_id: Strategy instance
            prices: Symbol -> price mapping

        Returns:
            Update status
        """
        try:
            instance_key = str(strategy_instance_id)

            if instance_key not in self.trading_engines:
                return {
                    "status": "error",
                    "message": "No active trading session",
                    "instance_id": instance_key
                }

            trading_engine = self.trading_engines[instance_key]

            # Update prices
            await trading_engine.update_market_prices(prices)

            # Get updated portfolio summary
            portfolio_summary = trading_engine.get_portfolio_summary()

            # Update portfolio in database
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.strategy_instance_id == strategy_instance_id
            ).first()

            if portfolio:
                portfolio.current_capital = portfolio_summary["portfolio_value"]
                portfolio.unrealized_pnl = portfolio_summary["unrealized_pnl"]
                portfolio.last_updated = datetime.utcnow()
                self.db.commit()

            return {
                "status": "success",
                "instance_id": instance_key,
                "updated_prices": len(prices),
                "portfolio_value": portfolio_summary["portfolio_value"],
                "unrealized_pnl": portfolio_summary["unrealized_pnl"]
            }

        except Exception as e:
            logger.error(f"Failed to update market prices: {e}")
            return {
                "status": "error",
                "error": str(e),
                "instance_id": str(strategy_instance_id)
            }

    async def get_trading_status(
        self,
        strategy_instance_id: UUID
    ) -> Dict[str, Any]:
        """
        Get current trading status for a strategy instance

        Args:
            strategy_instance_id: Strategy instance

        Returns:
            Trading status and portfolio information
        """
        try:
            instance_key = str(strategy_instance_id)

            if instance_key not in self.trading_engines:
                # Check if session exists but is stopped
                portfolio = self.db.query(Portfolio).filter(
                    Portfolio.strategy_instance_id == strategy_instance_id
                ).first()

                if portfolio:
                    return {
                        "status": "stopped",
                        "instance_id": instance_key,
                        "portfolio_id": str(portfolio.id),
                        "final_capital": float(portfolio.final_capital or portfolio.current_capital),
                        "total_pnl": float(portfolio.total_pnl or 0),
                        "stopped_at": portfolio.stopped_at.isoformat() if portfolio.stopped_at else None
                    }
                else:
                    return {
                        "status": "not_found",
                        "instance_id": instance_key,
                        "message": "No trading session found"
                    }

            trading_engine = self.trading_engines[instance_key]

            # Get portfolio summary
            portfolio_summary = trading_engine.get_portfolio_summary()
            performance_metrics = trading_engine.get_performance_metrics()

            # Get recent executions
            recent_executions = trading_engine.order_gateway.get_executions()[-10:]

            return {
                "status": "active",
                "instance_id": instance_key,
                "portfolio_summary": portfolio_summary,
                "performance_metrics": performance_metrics,
                "recent_executions": [
                    {
                        "order_id": exec.order_id,
                        "symbol": exec.symbol,
                        "side": exec.side.value,
                        "quantity": exec.filled_quantity,
                        "price": exec.average_fill_price,
                        "timestamp": exec.timestamp.isoformat()
                    }
                    for exec in recent_executions
                ]
            }

        except Exception as e:
            logger.error(f"Failed to get trading status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "instance_id": str(strategy_instance_id)
            }

    async def _get_or_create_broker_account(
        self,
        user_id: UUID,
        broker_config: Dict[str, Any]
    ) -> BrokerAccount:
        """Get or create broker account for user"""
        broker_name = broker_config.get("broker", "simulated")

        # Check if account exists
        account = self.db.query(BrokerAccount).filter(
            BrokerAccount.user_id == user_id,
            BrokerAccount.broker_name == broker_name,
            BrokerAccount.account_identifier == broker_config.get("account_id", "default")
        ).first()

        if not account:
            # Create new account
            account = BrokerAccount(
                user_id=user_id,
                broker_name=broker_name,
                account_identifier=broker_config.get("account_id", "default"),
                account_type=broker_config.get("account_type", "simulation"),
                credentials=broker_config.get("credentials", {}),
                is_active=True,
                created_at=datetime.utcnow()
            )
            self.db.add(account)
            self.db.commit()

        return account

    async def _setup_market_data_subscriptions(
        self,
        instance_key: str,
        symbols: List[str]
    ):
        """Set up market data subscriptions"""
        self.market_data_subscriptions[instance_key] = symbols
        logger.info(f"Set up market data subscriptions for {instance_key}: {symbols}")

    async def _record_execution(
        self,
        strategy_instance_id: UUID,
        signal: Dict[str, Any],
        order_id: str
    ):
        """Record signal execution in database"""
        try:
            # Create trade record
            trade = Trade(
                strategy_instance_id=strategy_instance_id,
                signal_id=signal.get("id"),
                order_id=order_id,
                symbol=signal["symbol"],
                direction=signal["direction"],
                quantity=signal["position_size"],
                entry_price=signal["entry_price"],
                executed_at=datetime.utcnow(),
                status="executed"
            )
            self.db.add(trade)
            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to record execution: {e}")

    async def cleanup_session(self, strategy_instance_id: UUID):
        """Clean up trading session data"""
        try:
            instance_key = str(strategy_instance_id)

            # Stop trading if active
            if instance_key in self.trading_engines:
                await self.stop_trading(strategy_instance_id, close_positions=True)
                del self.trading_engines[instance_key]

            # Clean up market data subscriptions
            if instance_key in self.market_data_subscriptions:
                del self.market_data_subscriptions[instance_key]

            # Clear cache
            await self.cache_service.delete(f"trading_session:{strategy_instance_id}")
            await self.cache_service.delete(f"trading_status:{strategy_instance_id}")

            logger.info(f"Cleaned up trading session for instance {strategy_instance_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup session: {e}")