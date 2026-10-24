"""
Moving Average Crossover Strategy

Strategy: When short-term MA crosses above long-term MA, buy
         When short-term MA crosses below long-term MA, sell
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from enum import Enum
from abc import ABC, abstractmethod


class Signal(Enum):
    """Trading signals"""
    BUY = 1
    SELL = -1
    HOLD = 0


class BaseStrategy(ABC):
    """Base class for all trading strategies"""

    def __init__(self, name: str, params: Dict = None):
        self.name = name
        self.params = params or {}
        self.positions = 0
        self.signals = []

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals"""
        pass

    def calculate_returns(self, data: pd.DataFrame, signals: pd.Series) -> pd.Series:
        """Calculate strategy returns"""
        returns = data['close'].pct_change()
        strategy_returns = returns * signals.shift(1)
        return strategy_returns.fillna(0)


class MACrossoverStrategy(BaseStrategy):
    """
    Moving Average Crossover Strategy

    Generates buy/sell signals based on the crossover of two moving averages.

    Parameters:
        short_window: Short-term MA window (default: 10)
        long_window: Long-term MA window (default: 30)
        ma_type: Type of MA ('sma', 'ema', 'wma') (default: 'sma')
    """

    def __init__(self, short_window: int = 10, long_window: int = 30, ma_type: str = 'sma'):
        super().__init__(
            name=f"MA_Crossover_{short_window}_{long_window}",
            params={
                'short_window': short_window,
                'long_window': long_window,
                'ma_type': ma_type.lower()
            }
        )
        self.short_window = short_window
        self.long_window = long_window
        self.ma_type = ma_type.lower()

        # Validate parameters
        if short_window >= long_window:
            raise ValueError("Short window must be less than long window")
        if ma_type.lower() not in ['sma', 'ema', 'wma']:
            raise ValueError("MA type must be 'sma', 'ema', or 'wma'")

    def calculate_ma(self, data: pd.Series, window: int, ma_type: str) -> pd.Series:
        """Calculate moving average based on type"""
        if ma_type == 'sma':
            return data.rolling(window=window).mean()
        elif ma_type == 'ema':
            return data.ewm(span=window).mean()
        elif ma_type == 'wma':
            # Weighted Moving Average
            weights = np.arange(1, window + 1)
            weights = weights / weights.sum()
            return data.rolling(window=window).apply(
                lambda x: np.dot(x, weights), raw=True
            )
        else:
            raise ValueError(f"Unknown MA type: {ma_type}")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on MA crossover

        Args:
            data: DataFrame with OHLCV data

        Returns:
            pd.Series: Trading signals (1 for buy, -1 for sell, 0 for hold)
        """
        # Calculate moving averages
        short_ma = self.calculate_ma(data['close'], self.short_window, self.ma_type)
        long_ma = self.calculate_ma(data['close'], self.long_window, self.ma_type)

        # Initialize signals series
        signals = pd.Series(0, index=data.index)

        # Generate crossover signals
        # Buy when short MA crosses above long MA
        # Sell when short MA crosses below long MA

        # Calculate the difference
        ma_diff = short_ma - long_ma

        # Find crossover points
        # When ma_diff changes from negative to positive = buy signal
        # When ma_diff changes from positive to negative = sell signal

        ma_diff_shifted = ma_diff.shift(1)

        # Buy signal: previous diff <= 0, current diff > 0
        buy_signal = (ma_diff_shifted <= 0) & (ma_diff > 0)

        # Sell signal: previous diff >= 0, current diff < 0
        sell_signal = (ma_diff_shifted >= 0) & (ma_diff < 0)

        signals[buy_signal] = Signal.BUY.value
        signals[sell_signal] = Signal.SELL.value

        return signals

    def get_ma_values(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        Get the moving average values for plotting/analysis

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Tuple: (short_ma, long_ma)
        """
        short_ma = self.calculate_ma(data['close'], self.short_window, self.ma_type)
        long_ma = self.calculate_ma(data['close'], self.long_window, self.ma_type)

        return short_ma, long_ma

    def calculate_performance_metrics(self, data: pd.DataFrame) -> Dict:
        """
        Calculate basic performance metrics for the strategy

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Dict: Performance metrics
        """
        signals = self.generate_signals(data)
        returns = self.calculate_returns(data, signals)

        # Basic metrics
        total_return = (1 + returns).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0

        # Signal metrics
        total_signals = (signals != 0).sum()
        buy_signals = (signals == 1).sum()
        sell_signals = (signals == -1).sum()

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'total_signals': total_signals,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'signal_frequency': total_signals / len(data)
        }


class EnhancedMACrossoverStrategy(MACrossoverStrategy):
    """
    Enhanced Moving Average Crossover Strategy with additional features

    Features:
    - Stop loss
    - Take profit
    - Position sizing
    - Trend filter
    - Volume confirmation
    """

    def __init__(
        self,
        short_window: int = 10,
        long_window: int = 30,
        ma_type: str = 'sma',
        stop_loss: float = 0.05,
        take_profit: float = 0.10,
        position_size: float = 1.0,
        use_volume_filter: bool = True,
        volume_threshold: float = 1.0
    ):
        super().__init__(short_window, long_window, ma_type)

        self.name = f"Enhanced_{self.name}"
        self.params.update({
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size': position_size,
            'use_volume_filter': use_volume_filter,
            'volume_threshold': volume_threshold
        })

        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.position_size = position_size
        self.use_volume_filter = use_volume_filter
        self.volume_threshold = volume_threshold

        self.entry_price = None
        self.current_position = 0

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate enhanced trading signals with risk management

        Args:
            data: DataFrame with OHLCV data

        Returns:
            pd.Series: Enhanced trading signals
        """
        # Get basic MA crossover signals
        base_signals = super().generate_signals(data)

        # Initialize enhanced signals
        enhanced_signals = pd.Series(0, index=data.index)

        # Calculate volume moving average for filter
        volume_ma = data['volume'].rolling(window=20).mean()

        for i in range(1, len(data)):
            current_signal = base_signals.iloc[i]
            current_price = data['close'].iloc[i]
            current_volume = data['volume'].iloc[i]

            # Volume filter
            if self.use_volume_filter:
                volume_ratio = current_volume / volume_ma.iloc[i]
                if volume_ratio < self.volume_threshold:
                    continue  # Skip signal if volume is too low

            # Risk management logic
            if current_signal == Signal.BUY.value and self.current_position <= 0:
                # Check if we can enter a long position
                self.entry_price = current_price
                self.current_position = self.position_size
                enhanced_signals.iloc[i] = Signal.BUY.value

            elif current_signal == Signal.SELL.value and self.current_position >= 0:
                # Check if we can enter a short position
                self.entry_price = current_price
                self.current_position = -self.position_size
                enhanced_signals.iloc[i] = Signal.SELL.value

            elif self.current_position != 0:
                # Check for exit conditions
                if self.current_position > 0:  # Long position
                    pnl = (current_price - self.entry_price) / self.entry_price

                    # Exit conditions
                    if pnl <= -self.stop_loss:  # Stop loss
                        self.current_position = 0
                        self.entry_price = None
                        enhanced_signals.iloc[i] = Signal.SELL.value
                    elif pnl >= self.take_profit:  # Take profit
                        self.current_position = 0
                        self.entry_price = None
                        enhanced_signals.iloc[i] = Signal.SELL.value

                elif self.current_position < 0:  # Short position
                    pnl = (self.entry_price - current_price) / self.entry_price

                    # Exit conditions
                    if pnl <= -self.stop_loss:  # Stop loss
                        self.current_position = 0
                        self.entry_price = None
                        enhanced_signals.iloc[i] = Signal.BUY.value
                    elif pnl >= self.take_profit:  # Take profit
                        self.current_position = 0
                        self.entry_price = None
                        enhanced_signals.iloc[i] = Signal.BUY.value

        return enhanced_signals

    def reset(self):
        """Reset strategy state"""
        self.entry_price = None
        self.current_position = 0
        self.signals = []


# Utility functions for strategy optimization
def optimize_ma_parameters(
    data: pd.DataFrame,
    short_range: range = range(5, 21, 5),
    long_range: range = range(20, 61, 10),
    ma_types: List[str] = ['sma', 'ema']
) -> Dict:
    """
    Optimize MA crossover parameters

    Args:
        data: OHLCV data
        short_range: Range of short windows to test
        long_range: Range of long windows to test
        ma_types: List of MA types to test

    Returns:
        Dict: Best parameters and performance
    """
    best_params = None
    best_sharpe = -np.inf

    results = []

    for ma_type in ma_types:
        for short_window in short_range:
            for long_window in long_range:
                if short_window >= long_window:
                    continue

                strategy = MACrossoverStrategy(
                    short_window=short_window,
                    long_window=long_window,
                    ma_type=ma_type
                )

                metrics = strategy.calculate_performance_metrics(data)
                sharpe = metrics['sharpe_ratio']

                results.append({
                    'short_window': short_window,
                    'long_window': long_window,
                    'ma_type': ma_type,
                    'sharpe_ratio': sharpe,
                    'total_return': metrics['total_return'],
                    'volatility': metrics['volatility']
                })

                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = {
                        'short_window': short_window,
                        'long_window': long_window,
                        'ma_type': ma_type,
                        'sharpe_ratio': sharpe,
                        'total_return': metrics['total_return']
                    }

    return {
        'best_params': best_params,
        'all_results': sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True)
    }