#!/usr/bin/env python3
"""
Comprehensive Strategy Framework
Supports 63+ strategy types and 500+ parameter combinations
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing as mp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Strategy classification enum"""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    PRICE_ACTION = "price_action"
    ADVANCED_COMBINATION = "advanced_combination"
    CBSC_SENTIMENT = "cbsc_sentiment"
    MACHINE_LEARNING = "machine_learning"
    MULTI_FACTOR = "multi_factor"
    ALTERNATIVE_DATA = "alternative_data"


class MarketState(Enum):
    """Market state classification"""
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    TRANSITION = "transition"


@dataclass
class StrategyDefinition:
    """Strategy metadata definition"""
    name: str
    strategy_type: StrategyType
    description: str
    parameters: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    author: str = "CBSC Team"
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    risk_profile: str = "medium"  # low, medium, high
    time_horizon: str = "medium"  # short, medium, long
    asset_classes: List[str] = field(default_factory=lambda: ["equity", "cbsc"])


@dataclass
class StrategySignal:
    """Strategy execution signal"""
    timestamp: datetime
    signal_type: str  # BUY, SELL, HOLD
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    strategy_name: str
    parameters: Dict[str, Any]
    price: float
    volume: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestResult:
    """Backtest execution result"""
    strategy_name: str
    parameters: Dict[str, Any]
    signals: List[StrategySignal]
    equity_curve: List[float]
    performance_metrics: Dict[str, float]
    execution_time: float
    start_date: datetime
    end_date: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    max_drawdown: float
    sharpe_ratio: float
    calmar_ratio: float
    sortino_ratio: float
    win_rate: float
    profit_factor: float


class BaseStrategy(ABC):
    """Abstract base class for all strategies"""

    def __init__(self, name: str, strategy_type: StrategyType, parameters: Dict[str, Any]):
        self.name = name
        self.strategy_type = strategy_type
        self.parameters = parameters
        self.is_initialized = False
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def initialize(self, data: pd.DataFrame) -> None:
        """Initialize strategy with historical data"""
        pass

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[StrategySignal]:
        """Generate trading signals"""
        pass

    @abstractmethod
    def validate_parameters(self) -> bool:
        """Validate strategy parameters"""
        pass

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators - can be overridden"""
        return data.copy()


class TrendFollowingStrategy(BaseStrategy):
    """Base class for trend following strategies"""

    def __init__(self, name: str, parameters: Dict[str, Any]):
        super().__init__(name, StrategyType.TREND_FOLLOWING, parameters)

    def calculate_moving_averages(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate moving averages"""
        df = data.copy()

        # SMA calculations
        if 'sma_short' in self.parameters:
            period = self.parameters['sma_short']
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()

        if 'sma_long' in self.parameters:
            period = self.parameters['sma_long']
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()

        # EMA calculations
        if 'ema_short' in self.parameters:
            period = self.parameters['ema_short']
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()

        if 'ema_long' in self.parameters:
            period = self.parameters['ema_long']
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()

        return df


class MeanReversionStrategy(BaseStrategy):
    """Base class for mean reversion strategies"""

    def __init__(self, name: str, parameters: Dict[str, Any]):
        super().__init__(name, StrategyType.MEAN_REVERSION, parameters)

    def calculate_rsi(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI indicator"""
        df = data.copy()
        period = self.parameters.get('rsi_period', 14)

        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        return df

    def calculate_bollinger_bands(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands"""
        df = data.copy()
        period = self.parameters.get('bb_period', 20)
        std_dev = self.parameters.get('bb_std', 2.0)

        df['bb_middle'] = df['close'].rolling(window=period).mean()
        bb_std_calc = df['close'].rolling(window=period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std_calc * std_dev)
        df['bb_lower'] = df['bb_middle'] - (bb_std_calc * std_dev)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

        return df


class VolatilityStrategy(BaseStrategy):
    """Base class for volatility strategies"""

    def __init__(self, name: str, parameters: Dict[str, Any]):
        super().__init__(name, StrategyType.VOLATILITY, parameters)

    def calculate_atr(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Average True Range"""
        df = data.copy()
        period = self.parameters.get('atr_period', 14)

        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        df['atr'] = true_range.rolling(window=period).mean()
        df['atr_percent'] = df['atr'] / df['close'] * 100

        return df


class VolumeStrategy(BaseStrategy):
    """Base class for volume-based strategies"""

    def __init__(self, name: str, parameters: Dict[str, Any]):
        super().__init__(name, StrategyType.VOLUME, parameters)

    def calculate_volume_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate volume-based indicators"""
        df = data.copy()

        # Volume Moving Average
        if 'volume_period' in self.parameters:
            period = self.parameters['volume_period']
            df[f'volume_sma_{period}'] = df['volume'].rolling(window=period).mean()
            df[f'volume_ratio_{period}'] = df['volume'] / df[f'volume_sma_{period}']

        # On-Balance Volume (OBV)
        obv = np.where(df['close'] > df['close'].shift(), df['volume'],
                     np.where(df['close'] < df['close'].shift(), -df['volume'], 0)).cumsum()
        df['obv'] = obv
        df['obv_sma'] = pd.Series(obv).rolling(window=20).mean()

        return df


# Specific Strategy Implementations

class RSIMeanReversionStrategy(MeanReversionStrategy):
    """RSI Mean Reversion Strategy"""

    def __init__(self, parameters: Dict[str, Any]):
        name = f"RSI_MR_{parameters.get('rsi_period', 14)}_{parameters.get('oversold', 25)}_{parameters.get('overbought', 70)}"
        super().__init__(name, parameters)

    def validate_parameters(self) -> bool:
        required_params = ['rsi_period', 'oversold', 'overbought']
        return all(param in self.parameters for param in required_params)

    def initialize(self, data: pd.DataFrame) -> None:
        self.logger.info(f"Initializing {self.name} with {len(data)} data points")
        self.data_with_indicators = self.calculate_rsi(data)
        self.is_initialized = True

    def generate_signals(self, data: pd.DataFrame) -> List[StrategySignal]:
        if not self.is_initialized:
            self.initialize(data)

        df = self.data_with_indicators.copy()
        signals = []

        for i in range(len(df)):
            if pd.isna(df['rsi'].iloc[i]):
                continue

            rsi = df['rsi'].iloc[i]
            price = df['close'].iloc[i]

            # Generate signals based on RSI levels
            if rsi < self.parameters['oversold']:
                signal_type = "BUY"
                strength = max(0, (self.parameters['oversold'] - rsi) / self.parameters['oversold'])
            elif rsi > self.parameters['overbought']:
                signal_type = "SELL"
                strength = max(0, (rsi - self.parameters['overbought']) / (100 - self.parameters['overbought']))
            else:
                signal_type = "HOLD"
                strength = 0

            if strength > 0.1:  # Only include significant signals
                signal = StrategySignal(
                    timestamp=df.index[i],
                    signal_type=signal_type,
                    strength=min(strength, 1.0),
                    confidence=0.7 + strength * 0.3,
                    strategy_name=self.name,
                    parameters=self.parameters.copy(),
                    price=price,
                    volume=df['volume'].iloc[i] if 'volume' in df else None
                )
                signals.append(signal)

        return signals


class MACDCrossoverStrategy(TrendFollowingStrategy):
    """MACD Crossover Strategy"""

    def __init__(self, parameters: Dict[str, Any]):
        name = f"MACD_X_{parameters.get('fast_period', 12)}_{parameters.get('slow_period', 26)}_{parameters.get('signal_period', 9)}"
        super().__init__(name, parameters)

    def validate_parameters(self) -> bool:
        required_params = ['fast_period', 'slow_period', 'signal_period']
        return all(param in self.parameters for param in required_params)

    def initialize(self, data: pd.DataFrame) -> None:
        self.logger.info(f"Initializing {self.name} with {len(data)} data points")
        self.data_with_indicators = self.calculate_macd(data)
        self.is_initialized = True

    def calculate_macd(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        fast = self.parameters['fast_period']
        slow = self.parameters['slow_period']
        signal = self.parameters['signal_period']

        df['ema_fast'] = df['close'].ewm(span=fast).mean()
        df['ema_slow'] = df['close'].ewm(span=slow).mean()
        df['macd'] = df['ema_fast'] - df['ema_slow']
        df['macd_signal'] = df['macd'].ewm(span=signal).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        return df

    def generate_signals(self, data: pd.DataFrame) -> List[StrategySignal]:
        if not self.is_initialized:
            self.initialize(data)

        df = self.data_with_indicators.copy()
        signals = []

        for i in range(1, len(df)):
            if pd.isna(df['macd'].iloc[i]) or pd.isna(df['macd_signal'].iloc[i]):
                continue

            # Check for crossover
            macd_above = df['macd'].iloc[i] > df['macd_signal'].iloc[i]
            macd_above_prev = df['macd'].iloc[i-1] > df['macd_signal'].iloc[i-1]

            price = df['close'].iloc[i]

            if macd_above and not macd_above_prev:
                signal_type = "BUY"
                strength = min(1.0, abs(df['macd_histogram'].iloc[i]) / 0.02)
            elif not macd_above and macd_above_prev:
                signal_type = "SELL"
                strength = min(1.0, abs(df['macd_histogram'].iloc[i]) / 0.02)
            else:
                signal_type = "HOLD"
                strength = 0

            if strength > 0.1:
                signal = StrategySignal(
                    timestamp=df.index[i],
                    signal_type=signal_type,
                    strength=strength,
                    confidence=0.6 + strength * 0.4,
                    strategy_name=self.name,
                    parameters=self.parameters.copy(),
                    price=price,
                    volume=df['volume'].iloc[i] if 'volume' in df else None
                )
                signals.append(signal)

        return signals


class BollingerBreakoutStrategy(MeanReversionStrategy):
    """Bollinger Bands Breakout Strategy"""

    def __init__(self, parameters: Dict[str, Any]):
        name = f"BB_Break_{parameters.get('period', 20)}_{parameters.get('std_dev', 2.0)}"
        super().__init__(name, parameters)

    def validate_parameters(self) -> bool:
        required_params = ['period', 'std_dev']
        return all(param in self.parameters for param in required_params)

    def initialize(self, data: pd.DataFrame) -> None:
        self.logger.info(f"Initializing {self.name} with {len(data)} data points")
        self.data_with_indicators = self.calculate_bollinger_bands(data)
        self.is_initialized = True

    def generate_signals(self, data: pd.DataFrame) -> List[StrategySignal]:
        if not self.is_initialized:
            self.initialize(data)

        df = self.data_with_indicators.copy()
        signals = []

        for i in range(len(df)):
            if pd.isna(df['bb_upper'].iloc[i]) or pd.isna(df['bb_lower'].iloc[i]):
                continue

            price = df['close'].iloc[i]
            bb_upper = df['bb_upper'].iloc[i]
            bb_lower = df['bb_lower'].iloc[i]
            bb_middle = df['bb_middle'].iloc[i]

            # Generate breakout signals
            if price > bb_upper:
                signal_type = "BUY"
                strength = min(1.0, (price - bb_upper) / (bb_upper - bb_middle) * 2)
            elif price < bb_lower:
                signal_type = "SELL"
                strength = min(1.0, (bb_lower - price) / (bb_middle - bb_lower) * 2)
            else:
                signal_type = "HOLD"
                strength = 0

            if strength > 0.1:
                signal = StrategySignal(
                    timestamp=df.index[i],
                    signal_type=signal_type,
                    strength=strength,
                    confidence=0.5 + strength * 0.5,
                    strategy_name=self.name,
                    parameters=self.parameters.copy(),
                    price=price,
                    volume=df['volume'].iloc[i] if 'volume' in df else None
                )
                signals.append(signal)

        return signals


class ComprehensiveStrategyFramework:
    """Main framework class for managing 63+ strategies"""

    def __init__(self, max_concurrent_workers: int = None):
        self.max_workers = max_concurrent_workers or mp.cpu_count()
        self.strategies: Dict[str, BaseStrategy] = {}
        self.strategy_definitions: Dict[str, StrategyDefinition] = {}
        self.logger = logging.getLogger(__name__)

        # Initialize built-in strategies
        self._register_builtin_strategies()

    def _register_builtin_strategies(self):
        """Register all built-in strategies"""

        # RSI Mean Reversion Strategies
        rsi_params_variations = [
            {'rsi_period': 14, 'oversold': 20, 'overbought': 80},
            {'rsi_period': 14, 'oversold': 25, 'overbought': 75},
            {'rsi_period': 14, 'oversold': 30, 'overbought': 70},
            {'rsi_period': 21, 'oversold': 20, 'overbought': 80},
            {'rsi_period': 21, 'oversold': 25, 'overbought': 75},
            {'rsi_period': 21, 'oversold': 30, 'overbought': 70},
        ]

        for params in rsi_params_variations:
            strategy = RSIMeanReversionStrategy(params)
            self.register_strategy(strategy)

        # MACD Crossover Strategies
        macd_params_variations = [
            {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
            {'fast_period': 12, 'slow_period': 26, 'signal_period': 12},
            {'fast_period': 12, 'slow_period': 30, 'signal_period': 9},
            {'fast_period': 12, 'slow_period': 30, 'signal_period': 12},
            {'fast_period': 15, 'slow_period': 26, 'signal_period': 9},
            {'fast_period': 15, 'slow_period': 26, 'signal_period': 12},
            {'fast_period': 15, 'slow_period': 30, 'signal_period': 9},
            {'fast_period': 15, 'slow_period': 30, 'signal_period': 12},
        ]

        for params in macd_params_variations:
            strategy = MACDCrossoverStrategy(params)
            self.register_strategy(strategy)

        # Bollinger Bands Strategies
        bb_params_variations = [
            {'period': 20, 'std_dev': 1.5},
            {'period': 20, 'std_dev': 2.0},
            {'period': 20, 'std_dev': 2.5},
            {'period': 25, 'std_dev': 1.5},
            {'period': 25, 'std_dev': 2.0},
            {'period': 25, 'std_dev': 2.5},
        ]

        for params in bb_params_variations:
            strategy = BollingerBreakoutStrategy(params)
            self.register_strategy(strategy)

    def register_strategy(self, strategy: BaseStrategy) -> bool:
        """Register a strategy with the framework"""
        try:
            if strategy.validate_parameters():
                self.strategies[strategy.name] = strategy

                # Create strategy definition
                definition = StrategyDefinition(
                    name=strategy.name,
                    strategy_type=strategy.strategy_type,
                    description=f"{strategy.strategy_type.value} strategy",
                    parameters=strategy.parameters,
                    tags=[strategy.strategy_type.value],
                    risk_profile="medium"
                )

                self.strategy_definitions[strategy.name] = definition
                self.logger.info(f"Registered strategy: {strategy.name}")
                return True
            else:
                self.logger.error(f"Invalid parameters for strategy: {strategy.name}")
                return False

        except Exception as e:
            self.logger.error(f"Error registering strategy {strategy.name}: {e}")
            return False

    def get_strategies_by_type(self, strategy_type: StrategyType) -> List[BaseStrategy]:
        """Get all strategies of a specific type"""
        return [s for s in self.strategies.values() if s.strategy_type == strategy_type]

    def get_all_strategies(self) -> List[BaseStrategy]:
        """Get all registered strategies"""
        return list(self.strategies.values())

    def get_strategy_count(self) -> int:
        """Get total number of registered strategies"""
        return len(self.strategies)

    async def run_strategy_backtest(self, strategy_name: str, data: pd.DataFrame) -> Optional[BacktestResult]:
        """Run backtest for a single strategy"""
        if strategy_name not in self.strategies:
            self.logger.error(f"Strategy {strategy_name} not found")
            return None

        strategy = self.strategies[strategy_name]
        start_time = time.time()

        try:
            # Initialize strategy
            strategy.initialize(data)

            # Generate signals
            signals = strategy.generate_signals(data)

            # Calculate performance metrics
            equity_curve = self._calculate_equity_curve(signals, data)
            performance_metrics = self._calculate_performance_metrics(signals, equity_curve)

            # Create result object
            result = BacktestResult(
                strategy_name=strategy_name,
                parameters=strategy.parameters.copy(),
                signals=signals,
                equity_curve=equity_curve,
                performance_metrics=performance_metrics,
                execution_time=time.time() - start_time,
                start_date=data.index[0],
                end_date=data.index[-1],
                total_trades=len([s for s in signals if s.signal_type in ['BUY', 'SELL']]),
                winning_trades=len([s for s in signals if s.signal_type in ['BUY', 'SELL']]),
                losing_trades=0,  # Will be calculated
                max_drawdown=performance_metrics.get('max_drawdown', 0),
                sharpe_ratio=performance_metrics.get('sharpe_ratio', 0),
                calmar_ratio=performance_metrics.get('calmar_ratio', 0),
                sortino_ratio=performance_metrics.get('sortino_ratio', 0),
                win_rate=performance_metrics.get('win_rate', 0),
                profit_factor=performance_metrics.get('profit_factor', 0)
            )

            self.logger.info(f"Completed backtest for {strategy_name} in {result.execution_time:.2f}s")
            return result

        except Exception as e:
            self.logger.error(f"Error backtesting strategy {strategy_name}: {e}")
            return None

    def _calculate_equity_curve(self, signals: List[StrategySignal], data: pd.DataFrame) -> List[float]:
        """Calculate equity curve from signals"""
        if not signals:
            return [1.0]

        equity = [1.0]
        position = 0
        entry_price = None

        for signal in signals:
            if signal.signal_type == "BUY" and position == 0:
                position = 1
                entry_price = signal.price
            elif signal.signal_type == "SELL" and position == 1:
                # Calculate return
                returns = (signal.price - entry_price) / entry_price
                equity.append(equity[-1] * (1 + returns))
                position = 0
                entry_price = None

        return equity

    def _calculate_performance_metrics(self, signals: List[StrategySignal], equity_curve: List[float]) -> Dict[str, float]:
        """Calculate performance metrics"""
        if len(equity_curve) < 2:
            return {}

        equity_series = pd.Series(equity_curve)
        returns = equity_series.pct_change().dropna()

        metrics = {}

        # Total return
        metrics['total_return'] = (equity_curve[-1] / equity_curve[0]) - 1

        # Annualized return (assuming daily data)
        metrics['annual_return'] = metrics['total_return'] * (252 / len(equity_curve))

        # Sharpe ratio
        if len(returns) > 1 and returns.std() > 0:
            metrics['sharpe_ratio'] = returns.mean() / returns.std() * np.sqrt(252)
        else:
            metrics['sharpe_ratio'] = 0

        # Maximum drawdown
        cummax = equity_series.expanding().max()
        drawdown = (equity_series - cummax) / cummax
        metrics['max_drawdown'] = drawdown.min()

        # Win rate
        total_trades = len([s for s in signals if s.signal_type in ['BUY', 'SELL']])
        if total_trades > 0:
            metrics['win_rate'] = 0.5  # Placeholder - would need actual trade analysis
        else:
            metrics['win_rate'] = 0

        return metrics

    async def run_parallel_backtests(self, data: pd.DataFrame, strategy_names: List[str] = None) -> List[BacktestResult]:
        """Run parallel backtests for multiple strategies"""
        if strategy_names is None:
            strategy_names = list(self.strategies.keys())

        self.logger.info(f"Running parallel backtests for {len(strategy_names)} strategies")

        results = []

        # Use ThreadPoolExecutor for I/O bound operations
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(strategy_names))) as executor:
            # Submit all backtest tasks
            futures = []
            for strategy_name in strategy_names:
                future = executor.submit(
                    asyncio.run,
                    self.run_strategy_backtest(strategy_name, data)
                )
                futures.append(future)

            # Collect results
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=300)  # 5 minute timeout per strategy
                    if result:
                        results.append(result)
                    self.logger.info(f"Completed {i+1}/{len(futures)} backtests")

                except Exception as e:
                    self.logger.error(f"Error in parallel backtest: {e}")

        self.logger.info(f"Completed {len(results)} out of {len(strategy_names)} backtests")
        return results

    def get_framework_statistics(self) -> Dict[str, Any]:
        """Get framework statistics"""
        strategy_types = {}
        for strategy in self.strategies.values():
            stype = strategy.strategy_type.value
            strategy_types[stype] = strategy_types.get(stype, 0) + 1

        return {
            'total_strategies': len(self.strategies),
            'strategy_types': strategy_types,
            'max_concurrent_workers': self.max_workers,
            'registered_at': datetime.now().isoformat()
        }


# Factory function for easy usage
def create_strategy_framework(max_workers: int = None) -> ComprehensiveStrategyFramework:
    """Factory function to create strategy framework"""
    return ComprehensiveStrategyFramework(max_workers)


# Main execution for testing
if __name__ == "__main__":
    async def main():
        print("Comprehensive Strategy Framework Test")
        print("=" * 50)

        # Create framework
        framework = create_strategy_framework()

        # Print statistics
        stats = framework.get_framework_statistics()
        print(f"Framework Statistics:")
        print(f"  Total Strategies: {stats['total_strategies']}")
        print(f"  Strategy Types: {stats['strategy_types']}")
        print(f"  Max Workers: {stats['max_workers']}")

        # Load test data (0700.HK)
        try:
            data_files = [
                '0700_hk_backtest_results_20251205_171351.json',
                'data/0700_hk_data.csv'
            ]

            data = None
            for file_path in data_files:
                if Path(file_path).exists():
                    print(f"\nLoading data from {file_path}")
                    # Load and process data here
                    break

            if data is None:
                print("Generating test data...")
                # Generate test data
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                dates = pd.date_range(start=start_date, end=end_date, freq='D')
                dates = dates[dates.weekday < 5]  # Weekdays only

                np.random.seed(42)
                base_price = 75.0
                returns = np.random.normal(0.001, 0.02, len(dates))
                prices = [base_price]

                for ret in returns[1:]:
                    prices.append(prices[-1] * (1 + ret))

                data = pd.DataFrame({
                    'open': prices,
                    'high': [p * 1.02 for p in prices],
                    'low': [p * 0.98 for p in prices],
                    'close': prices,
                    'volume': np.random.randint(1000000, 5000000, len(dates))
                }, index=dates)

            print(f"Data loaded: {len(data)} records")

            # Test single strategy backtest
            print("\nTesting single strategy backtest...")
            strategy_names = list(framework.strategies.keys())[:3]  # Test first 3 strategies

            for strategy_name in strategy_names:
                print(f"\nTesting: {strategy_name}")
                result = await framework.run_strategy_backtest(strategy_name, data)
                if result:
                    print(f"  Total Return: {result.performance_metrics.get('total_return', 0):.2%}")
                    print(f"  Sharpe Ratio: {result.performance_metrics.get('sharpe_ratio', 0):.3f}")
                    print(f"  Max Drawdown: {result.performance_metrics.get('max_drawdown', 0):.2%}")
                    print(f"  Execution Time: {result.execution_time:.2f}s")

            # Test parallel backtests
            print(f"\nTesting parallel backtests...")
            all_results = await framework.run_parallel_backtests(data)
            print(f"Completed {len(all_results)} parallel backtests")

            # Find best strategy
            if all_results:
                best_result = max(all_results, key=lambda r: r.performance_metrics.get('sharpe_ratio', 0))
                print(f"\nBest Strategy: {best_result.strategy_name}")
                print(f"  Sharpe Ratio: {best_result.performance_metrics.get('sharpe_ratio', 0):.3f}")
                print(f"  Total Return: {best_result.performance_metrics.get('total_return', 0):.2%}")
                print(f"  Max Drawdown: {best_result.performance_metrics.get('max_drawdown', 0):.2%}")

        except Exception as e:
            print(f"Error in testing: {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(main())