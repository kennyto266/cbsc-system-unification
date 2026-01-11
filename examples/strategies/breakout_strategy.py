"""
Breakout Strategy Template

A breakout trading strategy that identifies strong price movements beyond
key support/resistance levels and enters positions in the direction of the breakout.

Strategy Rules:
- Entry: Price closes above Donchian Channel upper band + volume confirmation
- Exit: Price closes below Donchian Channel middle band
- Position Sizing: ATR-based with volatility adjustment
- Stop Loss: Below the Donchian Channel lower band
- Time-based exit: 20 days if target not reached
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


def calculate_donchian_channels(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """
    Calculate Donchian Channels for breakout detection.

    Donchian Channels:
    - Upper Channel: Highest high in period
    - Lower Channel: Lowest low in period
    - Middle Channel: Average of upper and lower

    Args:
        df: DataFrame with OHLCV data
        period: Lookback period for channels

    Returns:
        DataFrame with Donchian Channels
    """
    df['dc_upper'] = df['high'].rolling(window=period).max()
    df['dc_lower'] = df['low'].rolling(window=period).min()
    df['dc_middle'] = (df['dc_upper'] + df['dc_lower']) / 2

    return df


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).

    Args:
        df: DataFrame with OHLCV data
        period: ATR period

    Returns:
        Series with ATR values
    """
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()

    return atr


def generate_signals(df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
    """
    Generate breakout trading signals.

    Args:
        df: DataFrame with OHLCV data
        params: Strategy parameters

    Returns:
        DataFrame with trading signals
    """
    # Default parameters
    if params is None:
        params = {
            'dc_period': 20,
            'atr_period': 14,
            'volume_ma_period': 20,
            'atr_multiplier': 2.0,
            'min_breakout_strength': 0.01,  # 1% above channel
            'volume_multiplier': 1.5  # Volume must be 1.5x average
        }

    # Calculate Donchian Channels
    df = calculate_donchian_channels(df, params['dc_period'])

    # Calculate ATR
    df['atr'] = calculate_atr(df, params['atr_period'])

    # Calculate volume moving average
    df['volume_ma'] = df['volume'].rolling(window=params['volume_ma_period']).mean()

    # Initialize signals
    signals = pd.DataFrame(index=df.index)
    signals['signal'] = 0  # 0 = no position, 1 = long, -1 = short
    signals['entry_price'] = np.nan
    signals['stop_loss'] = np.nan
    signals['target'] = np.nan
    signals['position_size'] = 0.0

    # Breakout conditions
    # Long breakout: Close above upper channel with volume confirmation
    long_breakout = (
        (df['close'] > df['dc_upper'].shift(1)) &  # Close above previous upper channel
        (df['close'] > (df['dc_upper'].shift(1) * (1 + params['min_breakout_strength']))) &  # Minimum strength
        (df['volume'] > (df['volume_ma'] * params['volume_multiplier']))  # Volume confirmation
    )

    # Short breakout: Close below lower channel with volume confirmation
    short_breakout = (
        (df['close'] < df['dc_lower'].shift(1)) &  # Close below previous lower channel
        (df['close'] < (df['dc_lower'].shift(1) * (1 - params['min_breakout_strength']))) &  # Minimum strength
        (df['volume'] > (df['volume_ma'] * params['volume_multiplier']))  # Volume confirmation
    )

    # Exit conditions
    exit_long = df['close'] < df['dc_middle']
    exit_short = df['close'] > df['dc_middle']

    # Generate signals (using previous day's conditions for current day entry)
    signals['signal'] = 0
    signals.loc[long_breakout.shift(1).fillna(False), 'signal'] = 1
    signals.loc[short_breakout.shift(1).fillna(False), 'signal'] = -1

    # Apply exits
    signals.loc[exit_long, 'signal'] = 0
    signals.loc[exit_short, 'signal'] = 0

    # Set entry prices and stops
    long_entry = signals['signal'] == 1
    short_entry = signals['signal'] == -1

    signals.loc[long_entry, 'entry_price'] = df['close']
    signals.loc[long_entry, 'stop_loss'] = df['dc_lower']
    signals.loc[long_entry, 'target'] = df['close'] + (2 * df['atr'])

    signals.loc[short_entry, 'entry_price'] = df['close']
    signals.loc[short_entry, 'stop_loss'] = df['dc_upper']
    signals.loc[short_entry, 'target'] = df['close'] - (2 * df['atr'])

    # Position sizing based on ATR (risk 2% per trade)
    risk_per_trade = 0.02
    signals.loc[long_entry, 'position_size'] = risk_per_trade / (df['atr'] / df['close'])
    signals.loc[short_entry, 'position_size'] = risk_per_trade / (df['atr'] / df['close'])

    return signals


def detect_consolidation(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    Detect consolidation periods (low volatility).

    Consolidation is identified when:
    - Price range is narrow relative to ATR
    - Market is chopping sideways

    Args:
        df: DataFrame with OHLCV data
        period: Lookback period

    Returns:
        Boolean Series indicating consolidation
    """
    # Calculate price range
    high_low_range = (df['high'].rolling(window=period).max() -
                      df['low'].rolling(window=period).min())
    avg_price = df['close'].rolling(window=period).mean()

    # Normalize range by price
    normalized_range = high_low_range / avg_price

    # Calculate ATR
    atr = calculate_atr(df, period)
    normalized_atr = atr / df['close']

    # Consolidation: Low range and low ATR
    consolidation = (normalized_range < 0.05) & (normalized_atr < 0.02)

    return consolidation


def calculate_breakout_strength(df: pd.DataFrame, signals: pd.DataFrame) -> pd.Series:
    """
    Calculate how strong the breakout is.

    Stronger breakouts get larger position sizes.

    Args:
        df: DataFrame with OHLCV data
        signals: DataFrame with trading signals

    Returns:
        Series with breakout strength (0-1)
    """
    # Distance from channel when breakout occurs
    upper_distance = (df['close'] - df['dc_upper']) / df['dc_upper']
    lower_distance = (df['dc_lower'] - df['close']) / df['dc_lower']

    # Volume strength
    volume_strength = df['volume'] / df['volume_ma']

    # Combine metrics
    strength = pd.Series(0.5, index=df.index)
    strength.loc[signals['signal'] == 1] = (
        upper_distance.loc[signals['signal'] == 1] *
        volume_strength.loc[signals['signal'] == 1]
    ).clip(0, 1)
    strength.loc[signals['signal'] == -1] = (
        lower_distance.loc[signals['signal'] == -1] *
        volume_strength.loc[signals['signal'] == -1]
    ).clip(0, 1)

    return strength


# Example usage
if __name__ == "__main__":
    print("Breakout Strategy Template")
    print("=========================")
    print()
    print("Strategy Parameters:")
    print("  - Donchian Channel Period: 20 days")
    print("  - ATR Period: 14 days")
    print("  - Volume MA Period: 20 days")
    print("  - ATR Multiplier: 2.0")
    print("  - Min Breakout Strength: 1%")
    print("  - Volume Confirmation: 1.5x average")
    print()
    print("Entry Conditions:")
    print("  LONG: Close > Upper DC + Volume Confirmation")
    print("  SHORT: Close < Lower DC + Volume Confirmation")
    print()
    print("Exit Conditions:")
    print("  Price crosses middle Donchian Channel")
    print()
    print("Risk Management:")
    print("  Stop Loss: Below opposite channel")
    print("  Position Size: ATR-based (2% risk)")
