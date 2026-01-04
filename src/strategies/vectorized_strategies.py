"""
Vectorized Strategy Library for VectorBT Multiprocess Engine
==========================================================

Provides comprehensive pre-built vectorized trading strategies
with automatic parameter validation and performance estimation.
"""

import numpy as np
import pandas as pd
import vectorbt as vbt
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from abc import ABC, abstractmethod
import warnings

logger = logging.getLogger(__name__)


class StrategyType(str, Enum):
    """Strategy classification"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    TREND = "trend"
    VOLATILITY = "volatility"
    ARBITRAGE = "arbitrage"
    STATISTICAL = "statistical"
    CUSTOM = "custom"


class Timeframe(str, Enum):
    """Supported timeframes"""
    TICK = "tick"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


@dataclass
class StrategyConfig:
    """Strategy configuration parameters"""
    name: str
    type: StrategyType
    timeframe: Timeframe
    symbols: List[str]
    start_date: str
    end_date: str
    initial_cash: float = 10000.0
    fees: float = 0.001
    slippage: float = 0.001
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Execution settings
    warmup_period: int = 0
    rebalance_on: str = "all"  # 'all', 'entry', 'exit', 'none'
    rebalance_freq: str = "D"  # pandas frequency

    # Risk management
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_position_size: float = 1.0
    min_position_size: float = 0.01

    # Advanced settings
    enable_short: bool = False
    enable_leverage: bool = False
    leverage: float = 1.0
    random_state: Optional[int] = None


@dataclass
class StrategyResult:
    """Strategy backtest results"""
    config: StrategyConfig
    portfolio: Any  # vectorbt Portfolio
    stats: Dict[str, float]
    trades: pd.DataFrame
    orders: pd.DataFrame
    positions: pd.DataFrame
    equity_curve: pd.Series
    drawdowns: pd.Series
    performance_metrics: Dict[str, Any]

    # Risk metrics
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    avg_win_loss_ratio: float

    # Execution metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_trade_duration: pd.Timedelta
    execution_time: float  # seconds


class BaseVectorizedStrategy(ABC):
    """Base class for vectorized strategies"""

    def __init__(self, config: StrategyConfig):
        self.config = config
        self.name = config.name
        self.type = config.type
        self.validate_config()

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals"""
        pass

    @abstractmethod
    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default strategy parameters"""
        pass

    def validate_config(self):
        """Validate strategy configuration"""
        if not self.config.symbols:
            raise ValueError("At least one symbol is required")

        if self.config.initial_cash <= 0:
            raise ValueError("Initial cash must be positive")

        if self.config.fees < 0 or self.config.fees > 1:
            raise ValueError("Fees must be between 0 and 1")

        if self.config.slippage < 0:
            raise ValueError("Slippage cannot be negative")

    def prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate data"""
        # Check required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Filter by date range
        if self.config.start_date and self.config.end_date:
            mask = (data.index >= self.config.start_date) & (data.index <= self.config.end_date)
            data = data.loc[mask]

        # Handle missing data
        data = data.fillna(method='ffill').fillna(method='bfill')

        return data

    def backtest(self, data: pd.DataFrame) -> StrategyResult:
        """Run strategy backtest"""
        import time
        start_time = time.time()

        # Prepare data
        data = self.prepare_data(data)

        # Generate signals
        signals = self.generate_signals(data)

        # Create portfolio
        portfolio = self._create_portfolio(signals, data)

        # Calculate results
        result = self._calculate_results(portfolio, data, time.time() - start_time)

        return result

    def _create_portfolio(self, signals: pd.DataFrame, data: pd.DataFrame) -> Any:
        """Create VectorBT portfolio"""
        # Extract entry and exit signals
        entries = signals['entry'] if 'entry' in signals.columns else signals.iloc[:, 0]
        exits = signals['exit'] if 'exit' in signals.columns else signals.iloc[:, 1] if len(signals.columns) > 1 else signals.iloc[:, 0]

        # Create portfolio
        portfolio = vbt.Portfolio.from_signals(
            data['close'],
            entries,
            exits,
            init_cash=self.config.initial_cash,
            fees=self.config.fees,
            slippage=self.config.slippage,
            freq=self.config.rebalance_freq,
            warmup=self.config.warmup_period,
            cash_sharing=True,
            group_by=None
        )

        return portfolio

    def _calculate_results(self, portfolio: Any, data: pd.DataFrame, execution_time: float) -> StrategyResult:
        """Calculate comprehensive results"""
        # Basic stats
        stats = portfolio.stats()

        # Get trades and positions
        trades = portfolio.trades.records_readable
        orders = portfolio.orders.records_readable
        positions = portfolio.positions.records_readable

        # Equity curve and drawdowns
        equity_curve = portfolio.value()
        drawdowns = portfolio.drawdowns()

        # Calculate advanced metrics
        performance_metrics = self._calculate_performance_metrics(portfolio, data)
        risk_metrics = self._calculate_risk_metrics(portfolio)

        return StrategyResult(
            config=self.config,
            portfolio=portfolio,
            stats=stats.to_dict(),
            trades=trades,
            orders=orders,
            positions=positions,
            equity_curve=equity_curve,
            drawdowns=drawdowns,
            performance_metrics=performance_metrics,
            execution_time=execution_time,
            **risk_metrics
        )

    def _calculate_performance_metrics(self, portfolio: Any, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate detailed performance metrics"""
        returns = portfolio.returns()

        metrics = {
            'total_return': portfolio.total_return(),
            'annual_return': portfolio.annual_return(),
            'volatility': portfolio.annual_volatility(),
            'beta': None,  # Would need benchmark
            'alpha': None,  # Would need benchmark
            'information_ratio': None,  # Would need benchmark
            'tracking_error': None,  # Would need benchmark
            'up_capture': None,  # Would need benchmark
            'down_capture': None,  # Would need benchmark
        }

        # Calculate additional metrics if possible
        try:
            metrics['var_95'] = returns.quantile(0.05)
            metrics['cvar_95'] = returns[returns <= metrics['var_95']].mean()
            metrics['skewness'] = returns.skew()
            metrics['kurtosis'] = returns.kurtosis()
        except Exception as e:
            logger.warning(f"Could not calculate advanced metrics: {e}")

        return metrics

    def _calculate_risk_metrics(self, portfolio: Any) -> Dict[str, float]:
        """Calculate risk metrics"""
        stats = portfolio.stats()

        return {
            'max_drawdown': stats['Max Drawdown'],
            'sharpe_ratio': stats['Sharpe Ratio'],
            'sortino_ratio': stats['Sortino Ratio'],
            'calmar_ratio': stats['Calmar Ratio'],
            'win_rate': stats['Win Rate'],
            'profit_factor': stats['Profit Factor'],
            'avg_win_loss_ratio': stats['Avg Win / Loss'],
            'total_trades': stats['# Trades'],
            'winning_trades': stats['# Winning Trades'],
            'losing_trades': stats['# Losing Trades'],
            'avg_trade_duration': stats['Avg Trade Duration']
        }

    def optimize_parameters(self, data: pd.DataFrame, param_grid: Dict[str, List]) -> Dict[str, Any]:
        """Optimize strategy parameters"""
        # This is a placeholder for parameter optimization
        # In practice, you would use VectorBT's optimization capabilities
        logger.info(f"Parameter optimization not implemented for {self.name}")
        return {'best_params': self.config.parameters, 'best_score': 0.0}


class MovingAverageCrossoverStrategy(BaseVectorizedStrategy):
    """Moving Average Crossover Strategy"""

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'fast_window': 10,
            'slow_window': 50,
            'signal_type': 'crossover'  # 'crossover', 'golden_cross'
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        fast_window = self.config.parameters.get('fast_window', 10)
        slow_window = self.config.parameters.get('slow_window', 50)

        # Calculate moving averages
        fast_ma = vbt.MA.run(data['close'], window=fast_window)
        slow_ma = vbt.MA.run(data['close'], window=slow_window)

        # Generate signals
        entries = fast_ma.ma_crossed_above(slow_ma.ma)
        exits = fast_ma.ma_crossed_below(slow_ma.ma)

        signals = pd.DataFrame({
            'entry': entries,
            'exit': exits
        }, index=data.index)

        return signals


class RSIMeanReversionStrategy(BaseVectorizedStrategy):
    """RSI Mean Reversion Strategy"""

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'rsi_window': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70,
            'exit_threshold': 50
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        rsi_window = self.config.parameters.get('rsi_window', 14)
        oversold = self.config.parameters.get('oversold_threshold', 30)
        overbought = self.config.parameters.get('overbought_threshold', 70)
        exit_thresh = self.config.parameters.get('exit_threshold', 50)

        # Calculate RSI
        rsi = vbt.RSI.run(data['close'], window=rsi_window).rsi

        # Generate signals
        entries = rsi.vbt.crossed_below(oversold)  # Buy when RSI crosses below oversold
        exits = rsi.vbt.crossed_above(exit_thresh)  # Sell when RSI crosses above exit threshold

        signals = pd.DataFrame({
            'entry': entries,
            'exit': exits
        }, index=data.index)

        return signals


class BollingerBandsStrategy(BaseVectorizedStrategy):
    """Bollinger Bands Strategy"""

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'bb_window': 20,
            'bb_std': 2.0,
            'position_type': 'reversal'  # 'reversal', 'breakout'
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        bb_window = self.config.parameters.get('bb_window', 20)
        bb_std = self.config.parameters.get('bb_std', 2.0)
        position_type = self.config.parameters.get('position_type', 'reversal')

        # Calculate Bollinger Bands
        bb = vbt.BBANDS.run(data['close'], window=bb_window, std=bb_std)

        if position_type == 'reversal':
            # Mean reversion: Buy at lower band, sell at upper band
            entries = data['close'].vbt.crossed_below(bb.lower)
            exits = data['close'].vbt.crossed_above(bb.upper)
        else:
            # Breakout: Buy when price crosses upper band, sell when crosses below
            entries = data['close'].vbt.crossed_above(bb.upper)
            exits = data['close'].vbt.crossed_below(bb.lower)

        signals = pd.DataFrame({
            'entry': entries,
            'exit': exits
        }, index=data.index)

        return signals


class MACDStrategy(BaseVectorizedStrategy):
    """MACD Strategy"""

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'fast_ema': 12,
            'slow_ema': 26,
            'signal_ema': 9,
            'signal_type': 'crossover'  # 'crossover', 'divergence'
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        fast_ema = self.config.parameters.get('fast_ema', 12)
        slow_ema = self.config.parameters.get('slow_ema', 26)
        signal_ema = self.config.parameters.get('signal_ema', 9)

        # Calculate MACD
        macd = vbt.MACD.run(
            data['close'],
            fast_window=fast_ema,
            slow_window=slow_ema,
            signal_window=signal_ema
        )

        # Generate signals
        entries = macd.macd.vbt.crossed_above(macd.signal)
        exits = macd.macd.vbt.crossed_below(macd.signal)

        signals = pd.DataFrame({
            'entry': entries,
            'exit': exits
        }, index=data.index)

        return signals


class DualMomentumStrategy(BaseVectorizedStrategy):
    """Dual Momentum Strategy (Trend Following)"""

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'lookback_period': 12,
            'risk_free_rate': 0.02,
            'momentum_threshold': 0.0
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        lookback = self.config.parameters.get('lookback_period', 12)
        threshold = self.config.parameters.get('momentum_threshold', 0.0)

        # Calculate momentum (returns over lookback period)
        returns = data['close'].pct_change(lookback)
        momentum = returns.shift(1)  # Use previous momentum for signal

        # Generate signals based on momentum
        entries = momentum > threshold
        exits = momentum <= -threshold

        signals = pd.DataFrame({
            'entry': entries,
            'exit': exits
        }, index=data.index)

        return signals


class PairsTradingStrategy(BaseVectorizedStrategy):
    """Pairs Trading Strategy"""

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'lookback_period': 60,
            'zscore_threshold': 2.0,
            'exit_threshold': 0.0,
            'hedge_ratio_calculation': 'ols'  # 'ols', 'static'
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        if len(self.config.symbols) != 2:
            raise ValueError("Pairs trading requires exactly 2 symbols")

        lookback = self.config.parameters.get('lookback_period', 60)
        z_threshold = self.config.parameters.get('zscore_threshold', 2.0)
        exit_thresh = self.config.parameters.get('exit_threshold', 0.0)

        # Extract price series for the two assets
        price1 = data.xs(self.config.symbols[0], level='symbol', axis=1)['close']
        price2 = data.xs(self.config.symbols[1], level='symbol', axis=1)['close']

        # Calculate hedge ratio (simplified - use rolling ratio)
        hedge_ratio = (price1 / price2).rolling(lookback).mean()

        # Calculate spread
        spread = price1 - hedge_ratio * price2

        # Calculate z-score of spread
        zscore = (spread - spread.rolling(lookback).mean()) / spread.rolling(lookback).std()

        # Generate signals
        entries = zscore < -z_threshold  # Buy spread
        exits = abs(zscore) < exit_thresh  # Exit when spread reverts

        signals = pd.DataFrame({
            'entry': entries,
            'exit': exits
        }, index=data.index)

        return signals


class VolatilityBreakoutStrategy(BaseVectorizedStrategy):
    """Volatility Breakout Strategy"""

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'atr_window': 14,
            'breakout_multiplier': 2.0,
            'lookback_period': 20
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        atr_window = self.config.parameters.get('atr_window', 14)
        multiplier = self.config.parameters.get('breakout_multiplier', 2.0)
        lookback = self.config.parameters.get('lookback_period', 20)

        # Calculate ATR
        atr = vbt.ATR.run(
            data['high'],
            data['low'],
            data['close'],
            window=atr_window
        ).atr

        # Calculate breakout levels
        high_lookback = data['high'].rolling(lookback).max()
        low_lookback = data['low'].rolling(lookback).min()

        # Generate breakout signals
        breakout_up = data['close'] > (high_lookback.shift(1) + multiplier * atr.shift(1))
        breakout_down = data['close'] < (low_lookback.shift(1) - multiplier * atr.shift(1))

        # Entry signals
        entries = breakout_up
        exits = breakout_down

        signals = pd.DataFrame({
            'entry': entries,
            'exit': exits
        }, index=data.index)

        return signals


class MeanReversionStrategy(BaseVectorizedStrategy):
    """General Mean Reversion Strategy"""

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'lookback_period': 20,
            'std_multiplier': 2.0,
            'exit_offset': 0.0
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        lookback = self.config.parameters.get('lookback_period', 20)
        std_mult = self.config.parameters.get('std_multiplier', 2.0)
        exit_offset = self.config.parameters.get('exit_offset', 0.0)

        # Calculate mean and standard deviation
        mean_price = data['close'].rolling(lookback).mean()
        std_price = data['close'].rolling(lookback).std()

        # Calculate bands
        upper_band = mean_price + std_mult * std_price
        lower_band = mean_price - std_mult * std_price

        # Generate signals
        entries = data['close'] < lower_band  # Buy when below lower band
        exits = data['close'] > (mean_price + exit_offset)  # Exit at mean

        signals = pd.DataFrame({
            'entry': entries,
            'exit': exits
        }, index=data.index)

        return signals


class VectorizedStrategyFactory:
    """Factory for creating vectorized strategies"""

    _strategies = {
        StrategyType.MOMENTUM: [
            MovingAverageCrossoverStrategy,
            MACDStrategy,
            DualMomentumStrategy
        ],
        StrategyType.MEAN_REVERSION: [
            RSIMeanReversionStrategy,
            BollingerBandsStrategy,
            MeanReversionStrategy
        ],
        StrategyType.VOLATILITY: [
            VolatilityBreakoutStrategy
        ],
        StrategyType.ARBITRAGE: [
            PairsTradingStrategy
        ]
    }

    @classmethod
    def create_strategy(cls, config: StrategyConfig) -> BaseVectorizedStrategy:
        """Create strategy instance"""
        strategies = cls._strategies.get(config.type, [])

        # Find matching strategy by name or use first available
        for strategy_class in strategies:
            if config.name.lower() in strategy_class.__name__.lower():
                return strategy_class(config)

        # Use first available strategy of the type
        if strategies:
            return strategies[0](config)

        raise ValueError(f"No strategy found for type: {config.type}")

    @classmethod
    def list_strategies(cls) -> Dict[str, List[str]]:
        """List all available strategies"""
        return {
            strategy_type.value: [strategy.__name__ for strategy in strategies]
            for strategy_type, strategies in cls._strategies.items()
        }

    @classmethod
    def get_strategy_info(cls, strategy_name: str) -> Dict[str, Any]:
        """Get strategy information"""
        for strategies in cls._strategies.values():
            for strategy_class in strategies:
                if strategy_name.lower() in strategy_class.__name__.lower():
                    # Create temporary config to get default parameters
                    temp_config = StrategyConfig(
                        name=strategy_name,
                        type=StrategyType.CUSTOM,
                        timeframe=Timeframe.DAY_1,
                        symbols=['AAPL'],
                        start_date='2020-01-01',
                        end_date='2021-01-01'
                    )
                    strategy = strategy_class(temp_config)

                    return {
                        'name': strategy.__name__,
                        'type': strategy.type.value,
                        'default_parameters': strategy.get_default_parameters(),
                        'class': strategy_class
                    }

        return {}


def create_strategy_config(
    name: str,
    strategy_type: StrategyType,
    symbols: List[str],
    start_date: str,
    end_date: str,
    **kwargs
) -> StrategyConfig:
    """Create strategy configuration"""
    return StrategyConfig(
        name=name,
        type=strategy_type,
        timeframe=kwargs.get('timeframe', Timeframe.DAY_1),
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        **kwargs
    )


def backtest_strategy(
    name: str,
    strategy_type: StrategyType,
    symbols: List[str],
    data: pd.DataFrame,
    start_date: str,
    end_date: str,
    **kwargs
) -> StrategyResult:
    """Convenient function to backtest a strategy"""
    config = create_strategy_config(
        name=name,
        strategy_type=strategy_type,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        **kwargs
    )

    strategy = VectorizedStrategyFactory.create_strategy(config)
    return strategy.backtest(data)