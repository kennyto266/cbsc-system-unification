"""
Backtest Engine Implementation
回測引擎實現

Enhanced backtesting engine with comprehensive strategy support,
performance analysis, and risk management capabilities.
增強的回測引擎，支持全面的策略分析、性能分析和風險管理功能。
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable
from enum import Enum

import numpy as np
import pandas as pd

from ..base.base_engine import BaseEngine, EngineConfig, EngineResult
from ...core.logging import log_performance
from .strategy import Strategy, StrategyType, StrategySignal
from .performance import PerformanceAnalyzer


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


@dataclass
class BacktestConfig:
    """Backtest configuration."""

    initial_capital: float = 100000.0
    commission_rate: float = 0.001
    slippage_rate: float = 0.0001
    margin_requirement: float = 1.0
    short_selling_enabled: bool = False
    position_sizing_method: str = "fixed"  # fixed, percentage, volatility
    risk_per_trade: float = 0.02
    max_position_size: float = 0.3
    stop_loss_enabled: bool = True
    take_profit_enabled: bool = True
    benchmark_symbol: Optional[str] = None


@dataclass
class Trade:
    """Trade record."""

    symbol: str
    side: OrderSide
    quantity: int
    price: float
    commission: float
    timestamp: datetime
    order_type: OrderType = OrderType.MARKET
    strategy_name: str = "UNKNOWN"


@dataclass
class Position:
    """Position information."""

    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    last_trade_timestamp: Optional[datetime] = None


@dataclass
class Portfolio:
    """Portfolio state."""

    cash: float
    positions: Dict[str, Position] = field(default_factory=dict)
    total_value: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)

    def get_position_value(self, symbol: str, current_price: float) -> float:
        """Get total value of a position."""
        if symbol not in self.positions:
            return 0.0

        position = self.positions[symbol]
        return abs(position.quantity) * current_price

    def get_total_equity(self, prices: Dict[str, float]) -> float:
        """Calculate total portfolio equity."""
        equity = self.cash

        for symbol, position in self.positions.items():
            if symbol in prices:
                current_price = prices[symbol]
                position.current_price = current_price
                position.unrealized_pnl = (
                    (current_price - position.avg_price) * position.quantity
                )
                equity += position.get_position_value(symbol, current_price)

        self.total_value = equity
        return equity


class BacktestEngine(BaseEngine):
    """
    Enhanced Backtest Engine

    Provides comprehensive backtesting capabilities including:
    - Multiple strategy support
    - Portfolio management
    - Risk management
    - Performance analysis
    - Benchmark comparison
    """

    def __init__(
        self,
        config: Optional[EngineConfig] = None,
        backtest_config: Optional[BacktestConfig] = None
    ):
        """
        Initialize backtest engine.

        Args:
            config: Engine configuration
            backtest_config: Backtest-specific configuration
        """
        if config is None:
            config = EngineConfig(
                name="backtest_engine",
                version="2.0.0",
                timeout_seconds=120,
                cache_enabled=False,  # Disable caching for backtests
                parallel_processing=True,
                max_workers=4
            )

        super().__init__(config)

        self.backtest_config = backtest_config or BacktestConfig()
        self.performance_analyzer = PerformanceAnalyzer()

        # Backtest state
        self.reset_state()

        self.logger.info(
            "Backtest Engine initialized",
            initial_capital=self.backtest_config.initial_capital,
            commission_rate=self.backtest_config.commission_rate
        )

    def reset_state(self):
        """Reset backtest state."""
        self.portfolio = Portfolio(cash=self.backtest_config.initial_capital)
        self.trades: List[Trade] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.daily_returns: List[float] = []
        self.current_date: Optional[datetime] = None
        self.signals_processed = 0

    async def _analyze(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Run backtest simulation.

        Args:
            data: Market data and strategies
            **kwargs: Additional backtest parameters

        Returns:
            Backtest results and performance metrics
        """
        self.reset_state()

        # Validate input
        if not await self.validate_input(data):
            raise ValueError("Invalid input data for backtesting")

        # Extract market data and strategies
        market_data = data.get("market_data", {})
        strategies = data.get("strategies", [])

        if not market_data:
            raise ValueError("No market data provided")

        self.logger.info(
            "Starting backtest",
            strategies_count=len(strategies),
            symbols=list(market_data.keys())
        )

        # Run backtest simulation
        results = await self._run_simulation(market_data, strategies, **kwargs)

        # Calculate performance metrics
        performance_metrics = await self._calculate_performance_metrics(results)

        # Generate detailed results
        final_results = {
            "backtest_config": {
                "initial_capital": self.backtest_config.initial_capital,
                "commission_rate": self.backtest_config.commission_rate,
                "strategies_tested": [s.name for s in strategies]
            },
            "summary": {
                "final_equity": results["final_equity"],
                "total_return": results["total_return"],
                "total_trades": results["total_trades"],
                "win_rate": results["win_rate"],
                "max_drawdown": results["max_drawdown"],
                "sharpe_ratio": results["sharpe_ratio"]
            },
            "performance": performance_metrics,
            "trades": [self._serialize_trade(trade) for trade in self.trades[-100:]],  # Last 100 trades
            "equity_curve": self.equity_curve,
            "daily_returns": self.daily_returns,
            "positions": {
                symbol: {
                    "quantity": pos.quantity,
                    "avg_price": pos.avg_price,
                    "current_price": pos.current_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "realized_pnl": pos.realized_pnl
                }
                for symbol, pos in self.portfolio.positions.items()
            },
            "execution_time": results.get("execution_time", 0.0),
            "signals_processed": self.signals_processed
        }

        self.logger.info(
            "Backtest completed",
            final_equity=results["final_equity"],
            total_return=results["total_return"],
            total_trades=results["total_trades"]
        )

        return final_results

    async def _run_simulation(
        self,
        market_data: Dict[str, Any],
        strategies: List[Strategy],
        **kwargs
    ) -> Dict[str, Any]:
        """Run the backtest simulation."""
        start_time = datetime.now()

        # Get all timestamps for simulation
        all_timestamps = set()
        symbol_data = {}

        for symbol, data in market_data.items():
            df = pd.DataFrame(data)
            symbol_data[symbol] = df
            if "timestamp" in df.columns:
                all_timestamps.update(df["timestamp"].tolist())
            else:
                # Use index as timestamps if not provided
                all_timestamps.update([f"day_{i}" for i in range(len(df))])

        sorted_timestamps = sorted(all_timestamps)

        # Simulate day by day
        for timestamp in sorted_timestamps:
            self.current_date = timestamp
            current_prices = {}

            # Get current prices for all symbols
            for symbol, df in symbol_data.items():
                current_row = self._get_data_for_timestamp(df, timestamp)
                if current_row is not None:
                    current_prices[symbol] = current_row["close"]

            if not current_prices:
                continue

            # Update portfolio value
            current_equity = self.portfolio.get_total_equity(current_prices)
            self.equity_curve.append((timestamp, current_equity))

            # Generate signals from strategies
            for strategy in strategies:
                try:
                    signals = await strategy.generate_signals(symbol_data, timestamp)
                    self.signals_processed += len(signals)

                    # Process signals
                    for signal in signals:
                        await self._process_signal(signal, current_prices)

                except Exception as e:
                    self.logger.error(
                        "Strategy error",
                        strategy=strategy.name,
                        timestamp=timestamp,
                        error=str(e)
                    )

        # Final portfolio value
        final_prices = {}
        for symbol, df in symbol_data.items():
            final_prices[symbol] = df["close"].iloc[-1]

        final_equity = self.portfolio.get_total_equity(final_prices)
        execution_time = (datetime.now() - start_time).total_seconds()

        # Calculate basic metrics
        total_return = ((final_equity - self.backtest_config.initial_capital) /
                       self.backtest_config.initial_capital * 100)

        win_trades = len([t for t in self.trades if t.side == OrderSide.SELL])
        win_rate = (win_trades / max(1, len(self.trades))) * 100

        # Calculate daily returns
        self._calculate_daily_returns()

        return {
            "final_equity": final_equity,
            "total_return": total_return,
            "total_trades": len(self.trades),
            "win_rate": win_rate,
            "max_drawdown": self._calculate_max_drawdown(),
            "sharpe_ratio": self._calculate_sharpe_ratio(),
            "execution_time": execution_time
        }

    async def _process_signal(self, signal: StrategySignal, current_prices: Dict[str, float]):
        """Process a trading signal."""
        if signal.symbol not in current_prices:
            return

        current_price = current_prices[signal.symbol]

        if signal.signal_type == "BUY":
            await self._execute_buy(signal.symbol, current_price, signal.confidence)
        elif signal.signal_type == "SELL":
            await self._execute_sell(signal.symbol, current_price, signal.confidence)

    async def _execute_buy(self, symbol: str, price: float, confidence: float = 1.0):
        """Execute a buy order."""
        # Calculate position size
        position_size = self._calculate_position_size(symbol, price, confidence)
        cost = position_size * price * (1 + self.backtest_config.commission_rate)

        if cost <= self.portfolio.cash:
            # Execute trade
            self.portfolio.cash -= cost

            # Update or create position
            if symbol in self.portfolio.positions:
                position = self.portfolio.positions[symbol]
                old_quantity = position.quantity
                old_cost = position.avg_price * old_quantity

                new_quantity = position_size + old_quantity
                new_avg_price = (old_cost + cost) / new_quantity if new_quantity > 0 else price

                position.quantity = new_quantity
                position.avg_price = new_avg_price
            else:
                self.portfolio.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=position_size,
                    avg_price=price + price * self.backtest_config.commission_rate
                )

            # Record trade
            trade = Trade(
                symbol=symbol,
                side=OrderSide.BUY,
                quantity=position_size,
                price=price,
                commission=cost - position_size * price,
                timestamp=self.current_date,
                strategy_name="Backtest"
            )
            self.trades.append(trade)

    async def _execute_sell(self, symbol: str, price: float, confidence: float = 1.0):
        """Execute a sell order."""
        if symbol not in self.portfolio.positions:
            return

        position = self.portfolio.positions[symbol]

        if position.quantity <= 0:
            return

        # Calculate commission
        proceeds = position.quantity * price * (1 - self.backtest_config.commission_rate)

        # Update portfolio
        self.portfolio.cash += proceeds

        # Calculate realized P&L
        realized_pnl = (price - position.avg_price) * position.quantity
        position.realized_pnl += realized_pnl

        # Record trade
        trade = Trade(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=abs(position.quantity),
            price=price,
            commission=position.quantity * price * self.backtest_config.commission_rate,
            timestamp=self.current_date,
            strategy_name="Backtest"
        )
        self.trades.append(trade)

        # Remove position
        del self.portfolio.positions[symbol]

    def _calculate_position_size(self, symbol: str, price: float, confidence: float) -> int:
        """Calculate position size based on risk management."""
        if self.backtest_config.position_sizing_method == "fixed":
            # Fixed dollar amount
            risk_amount = self.portfolio.cash * self.backtest_config.risk_per_trade
            return int(risk_amount / price)

        elif self.backtest_config.position_sizing_method == "percentage":
            # Percentage of portfolio
            position_value = self.portfolio.total_value * self.backtest_config.risk_per_trade
            max_position = position_value / price

            # Apply maximum position size limit
            max_allowed = self.portfolio.total_value * self.backtest_config.max_position_size / price

            return int(min(max_position, max_allowed) * confidence)

        else:  # default to fixed
            return int(100)  # Default to 100 shares

    def _get_data_for_timestamp(self, df: pd.DataFrame, timestamp: Any) -> Optional[Dict[str, float]]:
        """Get data row for specific timestamp."""
        if "timestamp" in df.columns:
            mask = df["timestamp"] == timestamp
            rows = df[mask]
            if not rows.empty:
                return rows.iloc[0].to_dict()
        else:
            # Use index
            try:
                if isinstance(timestamp, str) and timestamp.startswith("day_"):
                    day_index = int(timestamp.split("_")[1])
                    if day_index < len(df):
                        return df.iloc[day_index].to_dict()
            except (ValueError, IndexError):
                pass

        return None

    def _calculate_daily_returns(self):
        """Calculate daily portfolio returns."""
        if len(self.equity_curve) < 2:
            return

        self.daily_returns = []
        for i in range(1, len(self.equity_curve)):
            prev_value = self.equity_curve[i-1][1]
            curr_value = self.equity_curve[i][1]
            daily_return = (curr_value - prev_value) / prev_value
            self.daily_returns.append(daily_return)

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        if len(self.equity_curve) < 2:
            return 0.0

        values = [point[1] for point in self.equity_curve]
        peak = values[0]
        max_dd = 0.0

        for value in values[1:]:
            if value > peak:
                peak = value
            else:
                drawdown = (peak - value) / peak * 100
                max_dd = max(max_dd, drawdown)

        return max_dd

    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.03) -> float:
        """Calculate Sharpe ratio."""
        if not self.daily_returns:
            return 0.0

        returns_array = np.array(self.daily_returns)

        # Annualized return and volatility
        annual_return = returns_array.mean() * 252
        annual_volatility = returns_array.std() * np.sqrt(252)

        if annual_volatility == 0:
            return 0.0

        excess_return = annual_return - risk_free_rate
        sharpe_ratio = excess_return / annual_volatility

        return round(sharpe_ratio, 4)

    async def _calculate_performance_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed performance metrics."""
        return await self.performance_analyzer.analyze(
            self.equity_curve,
            self.daily_returns,
            self.trades,
            self.backtest_config.initial_capital
        )

    def _serialize_trade(self, trade: Trade) -> Dict[str, Any]:
        """Serialize trade to dictionary."""
        return {
            "symbol": trade.symbol,
            "side": trade.side.value,
            "quantity": trade.quantity,
            "price": trade.price,
            "commission": trade.commission,
            "timestamp": trade.timestamp.isoformat() if trade.timestamp else None,
            "order_type": trade.order_type.value,
            "strategy_name": trade.strategy_name
        }

    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data for backtesting."""
        if not await super().validate_input(data):
            return False

        # Check for market data
        if "market_data" not in data:
            self.logger.warning("No market data provided for backtesting")
            return False

        market_data = data["market_data"]
        if not isinstance(market_data, dict) or not market_data:
            self.logger.warning("Invalid market data format")
            return False

        # Validate market data structure
        for symbol, symbol_data in market_data.items():
            if not symbol_data:
                self.logger.warning(f"No data for symbol: {symbol}")
                return False

            df = pd.DataFrame(symbol_data)
            required_columns = ["open", "high", "low", "close"]

            if not all(col in df.columns for col in required_columns):
                self.logger.warning(f"Missing required columns for symbol: {symbol}")
                return False

            if len(df) < 2:
                self.logger.warning(f"Insufficient data for symbol: {symbol}")
                return False

        return True

    def get_equity_curve_data(self) -> List[Dict[str, Any]]:
        """Get equity curve data for visualization."""
        return [
            {
                "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else timestamp,
                "equity": equity
            }
            for timestamp, equity in self.equity_curve
        ]

    def export_trades(self, format: str = "dict") -> Any:
        """Export trades in specified format."""
        if format == "dict":
            return [self._serialize_trade(trade) for trade in self.trades]
        elif format == "dataframe":
            return pd.DataFrame([self._serialize_trade(trade) for trade in self.trades])
        else:
            raise ValueError(f"Unsupported export format: {format}")