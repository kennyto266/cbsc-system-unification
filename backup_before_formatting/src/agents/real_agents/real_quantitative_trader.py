"""Real Quantitative Trader Agent for Hong Kong quantitative trading system.

This agent identifies trading opportunities, generates trading signals, and executes
trades based on real market data with comprehensive risk management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from ...data_adapters.base_adapter import RealMarketData
from .base_real_agent import BaseRealAgent, RealAgentConfig, RealAgentStatus
from .ml_integration import MLModelManager, ModelType
from .real_data_analyzer import AnalysisResult, SignalStrength


class OrderType(str, Enum):
    """Order types for trading."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(str, Enum):
    """Order sides."""

    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Order status."""

    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class TradingSignal(BaseModel):
    """Trading signal model."""

    signal_id: str = Field(..., description="Unique signal identifier")
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="Buy or sell signal")
    order_type: OrderType = Field(..., description="Order type")
    quantity: float = Field(..., description="Order quantity")
    price: Optional[float] = Field(None, description="Limit price for limit orders")
    stop_price: Optional[float] = Field(None, description="Stop price for stop orders")

    # Signal metadata
    strength: float = Field(..., ge=0.0, le=1.0, description="Signal strength")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Signal confidence")
    reasoning: str = Field(..., description="Signal reasoning")

    # Risk management
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    max_position_size: float = Field(..., description="Maximum position size")

    # Timing
    created_at: datetime = Field(
        default_factory=datetime.now, description="Signal creation time"
    )
    expires_at: Optional[datetime] = Field(None, description="Signal expiration time")

    class Config:
        use_enum_values = True


class Order(BaseModel):
    """Order model."""

    order_id: str = Field(..., description="Unique order identifier")
    signal_id: str = Field(..., description="Associated signal ID")
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="Order side")
    order_type: OrderType = Field(..., description="Order type")
    quantity: float = Field(..., description="Order quantity")
    price: Optional[float] = Field(None, description="Order price")
    stop_price: Optional[float] = Field(None, description="Stop price")

    # Order status
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Order status")
    filled_quantity: float = Field(default=0.0, description="Filled quantity")
    average_price: Optional[float] = Field(None, description="Average fill price")

    # Risk management
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")

    # Timing
    created_at: datetime = Field(
        default_factory=datetime.now, description="Order creation time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update time"
    )
    filled_at: Optional[datetime] = Field(None, description="Fill time")

    class Config:
        use_enum_values = True


class Position(BaseModel):
    """Position model."""

    symbol: str = Field(..., description="Trading symbol")
    quantity: float = Field(
        ..., description="Position quantity (positive for long, negative for short)"
    )
    average_price: float = Field(..., description="Average entry price")
    current_price: float = Field(..., description="Current market price")

    # P&L
    unrealized_pnl: float = Field(..., description="Unrealized P&L")
    realized_pnl: float = Field(default=0.0, description="Realized P&L")

    # Risk management
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Position creation time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update time"
    )

    def calculate_unrealized_pnl(self) -> float:
        """Calculate unrealized P&L."""
        if self.quantity > 0:  # Long position
            return (self.current_price - self.average_price) * self.quantity
        else:  # Short position
            return (self.average_price - self.current_price) * abs(self.quantity)


class TradingStrategy(BaseModel):
    """Trading strategy configuration."""

    strategy_id: str = Field(..., description="Strategy identifier")
    name: str = Field(..., description="Strategy name")
    description: str = Field(..., description="Strategy description")

    # Signal parameters
    signal_threshold: float = Field(
        0.6, ge=0.0, le=1.0, description="Minimum signal strength"
    )
    confidence_threshold: float = Field(
        0.7, ge=0.0, le=1.0, description="Minimum confidence"
    )

    # Risk parameters
    max_position_size: float = Field(
        0.1, ge=0.0, le=1.0, description="Maximum position size"
    )
    stop_loss_pct: float = Field(
        0.05, ge=0.0, le=1.0, description="Stop loss percentage"
    )
    take_profit_pct: float = Field(
        0.1, ge=0.0, le=1.0, description="Take profit percentage"
    )

    # Timing parameters
    signal_timeout: int = Field(300, ge=1, description="Signal timeout in seconds")
    order_timeout: int = Field(600, ge=1, description="Order timeout in seconds")

    # Strategy specific parameters
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Strategy specific parameters"
    )

    class Config:
        use_enum_values = True


class TradingPerformance(BaseModel):
    """Trading performance metrics."""

    total_trades: int = Field(default=0, description="Total number of trades")
    winning_trades: int = Field(default=0, description="Number of winning trades")
    losing_trades: int = Field(default=0, description="Number of losing trades")

    # P&L metrics
    total_pnl: float = Field(default=0.0, description="Total P&L")
    realized_pnl: float = Field(default=0.0, description="Realized P&L")
    unrealized_pnl: float = Field(default=0.0, description="Unrealized P&L")

    # Performance ratios
    win_rate: float = Field(default=0.0, description="Win rate")
    profit_factor: float = Field(default=0.0, description="Profit factor")
    sharpe_ratio: float = Field(default=0.0, description="Sharpe ratio")
    max_drawdown: float = Field(default=0.0, description="Maximum drawdown")

    # Risk metrics
    var_95: float = Field(default=0.0, description="95% Value at Risk")
    var_99: float = Field(default=0.0, description="99% Value at Risk")

    # Timing metrics
    avg_trade_duration: float = Field(
        default=0.0, description="Average trade duration in hours"
    )
    max_trade_duration: float = Field(
        default=0.0, description="Maximum trade duration in hours"
    )

    # Update timestamp
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update time"
    )


class RealQuantitativeTrader(BaseRealAgent):
    """Real Quantitative Trader Agent with advanced trading capabilities."""

    def __init__(self, config: RealAgentConfig):
        super().__init__(config)
        self.ml_manager = MLModelManager(config)

        # Trading components
        self.trading_strategies: Dict[str, TradingStrategy] = {}
        self.active_signals: Dict[str, TradingSignal] = {}
        self.active_orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        self.trading_performance = TradingPerformance()

        # Risk management
        self.daily_pnl_limit = (
            config.max_position_size * 0.1
        )  # 10% of max position as daily P&L limit
        self.max_drawdown_limit = 0.15  # 15% maximum drawdown
        self.position_size_limit = config.max_position_size

        # Performance tracking
        self.trade_history: List[Dict[str, Any]] = []
        self.daily_pnl: float = 0.0
        self.peak_equity: float = 0.0
        self.current_drawdown: float = 0.0

    async def _initialize_specific(self) -> bool:
        """Initialize quantitative trader specific components."""
        try:
            self.logger.info("Initializing quantitative trader specific components...")

            # Initialize ML model manager
            if not await self.ml_manager.initialize():
                self.logger.error("Failed to initialize ML model manager")
                return False

            # Load trading strategies
            await self._load_trading_strategies()

            # Initialize risk management
            await self._initialize_risk_management()

            # Load historical performance data
            await self._load_historical_performance()

            self.logger.info("Quantitative trader initialization completed")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to initialize quantitative trader: {e}")
            return False

    async def _load_trading_strategies(self) -> None:
        """Load trading strategies configuration."""
        try:
            # Default momentum strategy
            momentum_strategy = TradingStrategy(
                strategy_id="momentum_strategy",
                name="Momentum Trading Strategy",
                description="Trades based on price momentum and technical indicators",
                signal_threshold=0.6,
                confidence_threshold=0.7,
                max_position_size=0.1,
                stop_loss_pct=0.05,
                take_profit_pct=0.1,
                parameters={
                    "rsi_oversold": 30,
                    "rsi_overbought": 70,
                    "momentum_period": 20,
                    "volume_threshold": 1.5,
                },
            )
            self.trading_strategies["momentum_strategy"] = momentum_strategy

            # Mean reversion strategy
            mean_reversion_strategy = TradingStrategy(
                strategy_id="mean_reversion_strategy",
                name="Mean Reversion Strategy",
                description="Trades based on mean reversion patterns",
                signal_threshold=0.5,
                confidence_threshold=0.6,
                max_position_size=0.08,
                stop_loss_pct=0.03,
                take_profit_pct=0.06,
                parameters={
                    "bollinger_period": 20,
                    "bollinger_std": 2.0,
                    "rsi_period": 14,
                    "reversion_threshold": 0.02,
                },
            )
            self.trading_strategies["mean_reversion_strategy"] = mean_reversion_strategy

            # Breakout strategy
            breakout_strategy = TradingStrategy(
                strategy_id="breakout_strategy",
                name="Breakout Strategy",
                description="Trades based on price breakouts",
                signal_threshold=0.7,
                confidence_threshold=0.8,
                max_position_size=0.12,
                stop_loss_pct=0.04,
                take_profit_pct=0.15,
                parameters={
                    "resistance_period": 20,
                    "support_period": 20,
                    "breakout_threshold": 0.01,
                    "volume_confirmation": True,
                },
            )
            self.trading_strategies["breakout_strategy"] = breakout_strategy

            self.logger.info(
                f"Loaded {len(self.trading_strategies)} trading strategies"
            )

        except Exception as e:
            self.logger.error(f"Error loading trading strategies: {e}")

    async def _initialize_risk_management(self) -> None:
        """Initialize risk management components."""
        try:
            # Initialize risk limits
            self.daily_pnl_limit = self.config.max_position_size * 0.1
            self.max_drawdown_limit = 0.15
            self.position_size_limit = self.config.max_position_size

            # Initialize performance tracking
            self.peak_equity = 1.0  # Starting with 100% equity
            self.current_drawdown = 0.0
            self.daily_pnl = 0.0

            self.logger.info("Risk management initialized")

        except Exception as e:
            self.logger.error(f"Error initializing risk management: {e}")

    async def _load_historical_performance(self) -> None:
        """Load historical performance data."""
        try:
            # In a real implementation, this would load from a database
            # For now, initialize with default values
            self.trading_performance = TradingPerformance()
            self.trade_history = []

            self.logger.info("Historical performance data loaded")

        except Exception as e:
            self.logger.error(f"Error loading historical performance: {e}")

    async def _enhance_analysis(
        self, base_result: AnalysisResult, market_data: List[RealMarketData]
    ) -> AnalysisResult:
        """Enhance analysis with trading - specific logic."""
        try:
            # Add trading - specific indicators
            trading_indicators = await self._calculate_trading_indicators(market_data)

            # Update base result
            enhanced_result = base_result.copy()
            for symbol, indicators in trading_indicators.items():
                if symbol in enhanced_result.technical_indicators:
                    enhanced_result.technical_indicators[symbol].update(indicators)
                else:
                    enhanced_result.technical_indicators[symbol] = indicators

            # Add trading insights
            trading_insights = await self._generate_trading_insights(
                enhanced_result, market_data
            )
            enhanced_result.insights.extend(trading_insights)

            return enhanced_result

        except Exception as e:
            self.logger.error(f"Error enhancing analysis for trading: {e}")
            return base_result

    async def _calculate_trading_indicators(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate trading - specific indicators."""
        try:
            # Group data by symbol
            symbol_data = {}
            for data in market_data:
                if data.symbol not in symbol_data:
                    symbol_data[data.symbol] = []
                symbol_data[data.symbol].append(data)

            trading_indicators = {}

            for symbol, data_list in symbol_data.items():
                if len(data_list) < 20:
                    continue

                # Convert to DataFrame
                df = pd.DataFrame(
                    [
                        {
                            "timestamp": d.timestamp,
                            "open": float(d.open_price),
                            "high": float(d.high_price),
                            "low": float(d.low_price),
                            "close": float(d.close_price),
                            "volume": d.volume,
                        }
                        for d in data_list
                    ]
                )

                df.set_index("timestamp", inplace=True)
                df.sort_index(inplace=True)

                indicators = {}

                # Price action indicators
                indicators["price_change"] = (
                    (df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2]
                    if len(df) > 1
                    else 0
                )
                indicators["price_range"] = (df["high"].max() - df["low"].min()) / df[
                    "close"
                ].mean()

                # Volume indicators
                indicators["volume_ratio"] = (
                    df["volume"].iloc[-1] / df["volume"].rolling(20).mean().iloc[-1]
                    if len(df) >= 20
                    else 1.0
                )
                indicators["volume_trend"] = (
                    df["volume"].rolling(5).mean().iloc[-1]
                    / df["volume"].rolling(20).mean().iloc[-1]
                    if len(df) >= 20
                    else 1.0
                )

                # Volatility indicators
                returns = df["close"].pct_change().dropna()
                indicators["volatility"] = (
                    returns.std() * np.sqrt(252) if len(returns) > 1 else 0
                )
                indicators["volatility_ratio"] = (
                    returns.rolling(5).std().iloc[-1]
                    / returns.rolling(20).std().iloc[-1]
                    if len(returns) >= 20
                    else 1.0
                )

                # Support and resistance
                indicators["resistance"] = (
                    df["high"].rolling(20).max().iloc[-1]
                    if len(df) >= 20
                    else df["high"].max()
                )
                indicators["support"] = (
                    df["low"].rolling(20).min().iloc[-1]
                    if len(df) >= 20
                    else df["low"].min()
                )
                indicators["price_vs_resistance"] = (
                    df["close"].iloc[-1] - indicators["resistance"]
                ) / indicators["resistance"]
                indicators["price_vs_support"] = (
                    df["close"].iloc[-1] - indicators["support"]
                ) / indicators["support"]

                # Momentum indicators
                indicators["momentum_5"] = (
                    (df["close"].iloc[-1] - df["close"].iloc[-6]) / df["close"].iloc[-6]
                    if len(df) >= 6
                    else 0
                )
                indicators["momentum_20"] = (
                    (df["close"].iloc[-1] - df["close"].iloc[-21])
                    / df["close"].iloc[-21]
                    if len(df) >= 21
                    else 0
                )

                # Trend indicators
                sma_20 = (
                    df["close"].rolling(20).mean().iloc[-1]
                    if len(df) >= 20
                    else df["close"].mean()
                )
                sma_50 = (
                    df["close"].rolling(50).mean().iloc[-1]
                    if len(df) >= 50
                    else df["close"].mean()
                )
                indicators["trend_direction"] = 1 if sma_20 > sma_50 else -1
                indicators["trend_strength"] = (
                    abs(sma_20 - sma_50) / sma_50 if sma_50 > 0 else 0
                )

                trading_indicators[symbol] = indicators

            return trading_indicators

        except Exception as e:
            self.logger.error(f"Error calculating trading indicators: {e}")
            return {}

    async def _generate_trading_insights(
        self, analysis_result: AnalysisResult, market_data: List[RealMarketData]
    ) -> List[str]:
        """Generate trading - specific insights."""
        try:
            insights = []

            # Analyze signal strength
            if analysis_result.signal_strength > 0.8:
                insights.append(
                    f"Strong trading signal detected: {analysis_result.signal_direction}"
                )
            elif analysis_result.signal_strength > 0.6:
                insights.append(
                    f"Moderate trading signal: {analysis_result.signal_direction}"
                )

            # Analyze market regime
            regime = analysis_result.market_regime.regime_type
            if regime == "high_volatility":
                insights.append(
                    "High volatility environment - consider reducing position sizes"
                )
            elif regime == "low_volatility":
                insights.append(
                    "Low volatility environment - potential for breakout strategies"
                )

            # Analyze individual symbols
            for symbol, indicators in analysis_result.technical_indicators.items():
                volume_ratio = indicators.get("volume_ratio", 1.0)
                if volume_ratio > 2.0:
                    insights.append(
                        f"{symbol}: High volume activity detected ({volume_ratio:.1f}x average)"
                    )

                price_vs_resistance = indicators.get("price_vs_resistance", 0)
                if price_vs_resistance > 0.95:
                    insights.append(
                        f"{symbol}: Near resistance level - potential reversal"
                    )
                elif price_vs_resistance < -0.95:
                    insights.append(f"{symbol}: Near support level - potential bounce")

            return insights

        except Exception as e:
            self.logger.error(f"Error generating trading insights: {e}")
            return []

    async def _enhance_signals(
        self, base_signals: List[Dict[str, Any]], analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Enhance signals with trading - specific logic."""
        try:
            enhanced_signals = []

            for signal in base_signals:
                # Apply trading strategy filters
                strategy_signals = await self._apply_trading_strategies(
                    signal, analysis_result
                )
                enhanced_signals.extend(strategy_signals)

            # Remove duplicate signals
            unique_signals = []
            seen_symbols = set()
            for signal in enhanced_signals:
                symbol = signal.get("symbol", "")
                if symbol not in seen_symbols:
                    unique_signals.append(signal)
                    seen_symbols.add(symbol)

            return unique_signals

        except Exception as e:
            self.logger.error(f"Error enhancing signals for trading: {e}")
            return base_signals

    async def _apply_trading_strategies(
        self, signal: Dict[str, Any], analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Apply trading strategies to generate enhanced signals."""
        try:
            enhanced_signals = []
            symbol = signal.get("symbol", "")

            if symbol not in analysis_result.technical_indicators:
                return [signal]

            indicators = analysis_result.technical_indicators[symbol]

            # Apply momentum strategy
            momentum_signal = await self._apply_momentum_strategy(signal, indicators)
            if momentum_signal:
                enhanced_signals.append(momentum_signal)

            # Apply mean reversion strategy
            mean_reversion_signal = await self._apply_mean_reversion_strategy(
                signal, indicators
            )
            if mean_reversion_signal:
                enhanced_signals.append(mean_reversion_signal)

            # Apply breakout strategy
            breakout_signal = await self._apply_breakout_strategy(signal, indicators)
            if breakout_signal:
                enhanced_signals.append(breakout_signal)

            return enhanced_signals if enhanced_signals else [signal]

        except Exception as e:
            self.logger.error(f"Error applying trading strategies: {e}")
            return [signal]

    async def _apply_momentum_strategy(
        self, signal: Dict[str, Any], indicators: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Apply momentum trading strategy."""
        try:
            strategy = self.trading_strategies.get("momentum_strategy")
            if not strategy:
                return None

            # Check momentum conditions
            momentum_5 = indicators.get("momentum_5", 0)
            momentum_20 = indicators.get("momentum_20", 0)
            volume_ratio = indicators.get("volume_ratio", 1.0)

            # Generate momentum signal
            if (
                momentum_5 > 0.02
                and momentum_20 > 0.05
                and volume_ratio > strategy.parameters.get("volume_threshold", 1.5)
            ):

                enhanced_signal = signal.copy()
                enhanced_signal.update(
                    {
                        "strategy": "momentum",
                        "strength": min(signal.get("strength", 0.5) * 1.2, 1.0),
                        "confidence": min(signal.get("confidence", 0.5) * 1.1, 1.0),
                        "reasoning": f"Momentum strategy: 5d momentum {momentum_5:.3f}, 20d momentum {momentum_20:.3f}, volume {volume_ratio:.1f}x",
                        "stop_loss_pct": strategy.stop_loss_pct,
                        "take_profit_pct": strategy.take_profit_pct,
                    }
                )
                return enhanced_signal

            return None

        except Exception as e:
            self.logger.error(f"Error applying momentum strategy: {e}")
            return None

    async def _apply_mean_reversion_strategy(
        self, signal: Dict[str, Any], indicators: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Apply mean reversion trading strategy."""
        try:
            strategy = self.trading_strategies.get("mean_reversion_strategy")
            if not strategy:
                return None

            # Check mean reversion conditions
            price_vs_resistance = indicators.get("price_vs_resistance", 0)
            price_vs_support = indicators.get("price_vs_support", 0)
            volatility_ratio = indicators.get("volatility_ratio", 1.0)

            # Generate mean reversion signal
            if (price_vs_resistance > 0.95 and volatility_ratio > 1.2) or (
                price_vs_support < -0.95 and volatility_ratio > 1.2
            ):

                side = "sell" if price_vs_resistance > 0.95 else "buy"

                enhanced_signal = signal.copy()
                enhanced_signal.update(
                    {
                        "strategy": "mean_reversion",
                        "side": side,
                        "strength": min(signal.get("strength", 0.5) * 1.1, 1.0),
                        "confidence": min(signal.get("confidence", 0.5) * 1.05, 1.0),
                        "reasoning": f"Mean reversion strategy: price vs resistance {price_vs_resistance:.3f}, volatility {volatility_ratio:.1f}x",
                        "stop_loss_pct": strategy.stop_loss_pct,
                        "take_profit_pct": strategy.take_profit_pct,
                    }
                )
                return enhanced_signal

            return None

        except Exception as e:
            self.logger.error(f"Error applying mean reversion strategy: {e}")
            return None

    async def _apply_breakout_strategy(
        self, signal: Dict[str, Any], indicators: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Apply breakout trading strategy."""
        try:
            strategy = self.trading_strategies.get("breakout_strategy")
            if not strategy:
                return None

            # Check breakout conditions
            price_vs_resistance = indicators.get("price_vs_resistance", 0)
            volume_ratio = indicators.get("volume_ratio", 1.0)
            momentum_5 = indicators.get("momentum_5", 0)

            # Generate breakout signal
            if price_vs_resistance > 1.01 and volume_ratio > 2.0 and momentum_5 > 0.03:

                enhanced_signal = signal.copy()
                enhanced_signal.update(
                    {
                        "strategy": "breakout",
                        "side": "buy",
                        "strength": min(signal.get("strength", 0.5) * 1.3, 1.0),
                        "confidence": min(signal.get("confidence", 0.5) * 1.2, 1.0),
                        "reasoning": f"Breakout strategy: price above resistance {price_vs_resistance:.3f}, volume {volume_ratio:.1f}x, momentum {momentum_5:.3f}",
                        "stop_loss_pct": strategy.stop_loss_pct,
                        "take_profit_pct": strategy.take_profit_pct,
                    }
                )
                return enhanced_signal

            return None

        except Exception as e:
            self.logger.error(f"Error applying breakout strategy: {e}")
            return None

    async def _execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trading signal with comprehensive risk management."""
        try:
            # Validate signal
            validation_result = await self._validate_trading_signal(signal)
            if not validation_result["is_valid"]:
                return {
                    "signal_id": signal.get("signal_id", "unknown"),
                    "status": "rejected",
                    "reason": validation_result["reason"],
                }

            # Create trading signal
            trading_signal = TradingSignal(
                signal_id=signal.get(
                    "signal_id", f"signal_{datetime.now().strftime('%Y % m % d_ % H % M % S')}"
                ),
                symbol=signal.get("symbol", ""),
                side=OrderSide(signal.get("side", "buy")),
                order_type=OrderType.MARKET,  # Default to market order
                quantity=signal.get("quantity", 0),
                strength=signal.get("strength", 0.5),
                confidence=signal.get("confidence", 0.5),
                reasoning=signal.get("reasoning", ""),
                max_position_size=signal.get(
                    "max_position_size", self.config.max_position_size
                ),
            )

            # Calculate position size
            position_size = await self._calculate_position_size(trading_signal, signal)
            trading_signal.quantity = position_size

            # Calculate stop loss and take profit
            current_price = signal.get("current_price", 0)
            stop_loss_pct = signal.get("stop_loss_pct", 0.05)
            take_profit_pct = signal.get("take_profit_pct", 0.1)

            if trading_signal.side == OrderSide.BUY:
                trading_signal.stop_loss = current_price * (1 - stop_loss_pct)
                trading_signal.take_profit = current_price * (1 + take_profit_pct)
            else:
                trading_signal.stop_loss = current_price * (1 + stop_loss_pct)
                trading_signal.take_profit = current_price * (1 - take_profit_pct)

            # Create order
            order = await self._create_order(trading_signal, current_price)

            # Execute order (simulated)
            execution_result = await self._execute_order(order)

            # Update positions and performance
            if execution_result["status"] == "filled":
                await self._update_position(trading_signal, execution_result)
                await self._update_performance(execution_result)

            return execution_result

        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")
            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }

    async def _validate_trading_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Validate trading signal with risk management checks."""
        try:
            validation_result = {"is_valid": True, "reason": ""}

            # Check signal strength
            strength = signal.get("strength", 0)
            if strength < self.config.signal_threshold:
                validation_result["is_valid"] = False
                validation_result["reason"] = "Signal strength below threshold"
                return validation_result

            # Check confidence
            confidence = signal.get("confidence", 0)
            if confidence < self.config.confidence_threshold:
                validation_result["is_valid"] = False
                validation_result["reason"] = "Confidence below threshold"
                return validation_result

            # Check daily P&L limit
            if abs(self.daily_pnl) > self.daily_pnl_limit:
                validation_result["is_valid"] = False
                validation_result["reason"] = "Daily P&L limit exceeded"
                return validation_result

            # Check maximum drawdown
            if self.current_drawdown > self.max_drawdown_limit:
                validation_result["is_valid"] = False
                validation_result["reason"] = "Maximum drawdown limit exceeded"
                return validation_result

            # Check position size limits
            symbol = signal.get("symbol", "")
            current_position = self.positions.get(symbol, None)
            if current_position:
                total_exposure = abs(current_position.quantity) + signal.get(
                    "quantity", 0
                )
                if total_exposure > self.position_size_limit:
                    validation_result["is_valid"] = False
                    validation_result["reason"] = "Position size limit exceeded"
                    return validation_result

            return validation_result

        except Exception as e:
            self.logger.error(f"Error validating trading signal: {e}")
            return {"is_valid": False, "reason": f"Validation error: {str(e)}"}

    async def _calculate_position_size(
        self, trading_signal: TradingSignal, signal: Dict[str, Any]
    ) -> float:
        """Calculate optimal position size based on risk management."""
        try:
            # Base position size from signal
            base_size = signal.get("quantity", 0.1)

            # Adjust based on signal strength
            strength_multiplier = 0.5 + trading_signal.strength  # 0.5 to 1.5

            # Adjust based on confidence
            confidence_multiplier = 0.5 + trading_signal.confidence  # 0.5 to 1.5

            # Adjust based on current drawdown
            drawdown_multiplier = max(0.1, 1.0 - self.current_drawdown)

            # Adjust based on daily P&L
            pnl_multiplier = max(0.1, 1.0 - abs(self.daily_pnl) / self.daily_pnl_limit)

            # Calculate final position size
            position_size = (
                base_size
                * strength_multiplier
                * confidence_multiplier
                * drawdown_multiplier
                * pnl_multiplier
            )

            # Ensure within limits
            position_size = min(position_size, trading_signal.max_position_size)
            position_size = max(position_size, 0.01)  # Minimum position size

            return position_size

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return signal.get("quantity", 0.1)

    async def _create_order(
        self, trading_signal: TradingSignal, current_price: float
    ) -> Order:
        """Create order from trading signal."""
        try:
            order = Order(
                order_id=f"order_{datetime.now().strftime('%Y % m % d_ % H % M % S_ % f')}",
                signal_id=trading_signal.signal_id,
                symbol=trading_signal.symbol,
                side=trading_signal.side,
                order_type=trading_signal.order_type,
                quantity=trading_signal.quantity,
                price=(
                    current_price
                    if trading_signal.order_type == OrderType.LIMIT
                    else None
                ),
                stop_price=(
                    trading_signal.stop_price
                    if trading_signal.order_type
                    in [OrderType.STOP, OrderType.STOP_LIMIT]
                    else None
                ),
                stop_loss=trading_signal.stop_loss,
                take_profit=trading_signal.take_profit,
            )

            # Store active order
            self.active_orders[order.order_id] = order

            return order

        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            raise

    async def _execute_order(self, order: Order) -> Dict[str, Any]:
        """Execute order (simulated implementation)."""
        try:
            # Simulate order execution
            # In real implementation, this would interface with a trading system

            execution_result = {
                "order_id": order.order_id,
                "signal_id": order.signal_id,
                "status": "filled",
                "filled_quantity": order.quantity,
                "average_price": order.price or 0,
                "execution_time": datetime.now(),
                "commission": order.quantity * 0.001,  # 0.1% commission
            }

            # Update order status
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.average_price = execution_result["average_price"]
            order.filled_at = execution_result["execution_time"]
            order.updated_at = datetime.now()

            self.logger.info(f"Order executed: {order.order_id} for {order.symbol}")
            return execution_result

        except Exception as e:
            self.logger.error(f"Error executing order: {e}")
            return {"order_id": order.order_id, "status": "failed", "error": str(e)}

    async def _update_position(
        self, trading_signal: TradingSignal, execution_result: Dict[str, Any]
    ) -> None:
        """Update position after order execution."""
        try:
            symbol = trading_signal.symbol
            filled_quantity = execution_result["filled_quantity"]
            average_price = execution_result["average_price"]

            if symbol in self.positions:
                # Update existing position
                position = self.positions[symbol]

                if trading_signal.side == OrderSide.BUY:
                    # Add to long position
                    new_quantity = position.quantity + filled_quantity
                    new_average_price = (
                        position.quantity * position.average_price
                        + filled_quantity * average_price
                    ) / new_quantity
                else:
                    # Add to short position (reduce long or increase short)
                    new_quantity = position.quantity - filled_quantity
                    new_average_price = (
                        position.average_price
                    )  # Keep original average for short

                position.quantity = new_quantity
                position.average_price = new_average_price
                position.current_price = average_price
                position.updated_at = datetime.now()

            else:
                # Create new position
                quantity = (
                    filled_quantity
                    if trading_signal.side == OrderSide.BUY
                    else -filled_quantity
                )

                position = Position(
                    symbol=symbol,
                    quantity=quantity,
                    average_price=average_price,
                    current_price=average_price,
                    stop_loss=trading_signal.stop_loss,
                    take_profit=trading_signal.take_profit,
                )

                self.positions[symbol] = position

            # Update unrealized P&L
            position.unrealized_pnl = position.calculate_unrealized_pnl()

            self.logger.info(f"Position updated: {symbol} quantity={position.quantity}")

        except Exception as e:
            self.logger.error(f"Error updating position: {e}")

    async def _update_performance(self, execution_result: Dict[str, Any]) -> None:
        """Update trading performance metrics."""
        try:
            # Update daily P&L
            commission = execution_result.get("commission", 0)
            self.daily_pnl -= commission  # Subtract commission from P&L

            # Update trade history
            trade_record = {
                "timestamp": execution_result["execution_time"],
                "order_id": execution_result["order_id"],
                "signal_id": execution_result["signal_id"],
                "filled_quantity": execution_result["filled_quantity"],
                "average_price": execution_result["average_price"],
                "commission": commission,
            }
            self.trade_history.append(trade_record)

            # Update performance metrics
            self.trading_performance.total_trades += 1
            self.trading_performance.realized_pnl -= commission

            # Calculate win rate
            if self.trading_performance.total_trades > 0:
                self.trading_performance.winning_trades = sum(
                    1 for trade in self.trade_history if trade.get("pnl", 0) > 0
                )
                self.trading_performance.losing_trades = (
                    self.trading_performance.total_trades
                    - self.trading_performance.winning_trades
                )
                self.trading_performance.win_rate = (
                    self.trading_performance.winning_trades
                    / self.trading_performance.total_trades
                )

            # Update peak equity and drawdown
            current_equity = (
                1.0
                + self.trading_performance.realized_pnl
                + sum(p.unrealized_pnl for p in self.positions.values())
            )
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity
                self.current_drawdown = 0.0
            else:
                self.current_drawdown = (
                    self.peak_equity - current_equity
                ) / self.peak_equity

            self.trading_performance.max_drawdown = max(
                self.trading_performance.max_drawdown, self.current_drawdown
            )

            self.logger.debug(
                f"Performance updated: total trades={self.trading_performance.total_trades}, daily P&L={self.daily_pnl:.4f}"
            )

        except Exception as e:
            self.logger.error(f"Error updating performance: {e}")

    async def get_trading_summary(self) -> Dict[str, Any]:
        """Get comprehensive trading summary."""
        try:
            # Calculate current unrealized P&L
            total_unrealized_pnl = sum(
                position.unrealized_pnl for position in self.positions.values()
            )

            # Calculate total P&L
            total_pnl = self.trading_performance.realized_pnl + total_unrealized_pnl

            summary = {
                "agent_id": self.config.agent_id,
                "agent_name": self.config.name,
                "status": self.real_status,
                # Trading metrics
                "total_trades": self.trading_performance.total_trades,
                "win_rate": self.trading_performance.win_rate,
                "total_pnl": total_pnl,
                "realized_pnl": self.trading_performance.realized_pnl,
                "unrealized_pnl": total_unrealized_pnl,
                "max_drawdown": self.trading_performance.max_drawdown,
                "current_drawdown": self.current_drawdown,
                # Position information
                "active_positions": len(self.positions),
                "position_details": {
                    symbol: {
                        "quantity": pos.quantity,
                        "average_price": pos.average_price,
                        "current_price": pos.current_price,
                        "unrealized_pnl": pos.unrealized_pnl,
                    }
                    for symbol, pos in self.positions.items()
                },
                # Risk metrics
                "daily_pnl": self.daily_pnl,
                "daily_pnl_limit": self.daily_pnl_limit,
                "position_size_limit": self.position_size_limit,
                # Strategy information
                "active_strategies": list(self.trading_strategies.keys()),
                "active_signals": len(self.active_signals),
                "active_orders": len(self.active_orders),
                # Performance history
                "trade_history_count": len(self.trade_history),
                "last_trade_time": (
                    self.trade_history[-1]["timestamp"] if self.trade_history else None
                ),
            }

            return summary

        except Exception as e:
            self.logger.error(f"Error getting trading summary: {e}")
            return {"error": str(e)}

    async def cleanup(self) -> None:
        """Cleanup trading agent resources."""
        try:
            self.logger.info(f"Cleaning up trading agent: {self.config.name}")

            # Cancel all active orders
            for order in self.active_orders.values():
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.now()

            # Clear all collections
            self.active_signals.clear()
            self.active_orders.clear()
            self.positions.clear()
            self.trade_history.clear()

            # Reset performance metrics
            self.trading_performance = TradingPerformance()
            self.daily_pnl = 0.0
            self.peak_equity = 1.0
            self.current_drawdown = 0.0

            # Call parent cleanup
            await super().cleanup()

            self.logger.info("Trading agent cleanup completed")

        except Exception as e:
            self.logger.exception(f"Error during cleanup: {e}")
