"""
Mean Reversion Strategy Template

A mean reversion strategy that identifies overbought/oversold conditions
and trades against the current trend expecting price to revert to the mean.

Strategy Rules:
- Entry Short: RSI > 70 AND Price > Upper Bollinger Band
- Entry Long: RSI < 30 AND Price < Lower Bollinger Band
- Exit: When price returns to middle Bollinger Band
- Position Sizing: Fixed size with scaling based on signal strength
- Stop Loss: 1.5x ATR
- Maximum Hold Time: 10 trading days
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


def calculate_indicators(df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
    """
    Calculate indicators for mean reversion strategy.

    Args:
        df: DataFrame with OHLCV data
        params: Strategy parameters

    Returns:
        DataFrame with added indicators
    """
    if params is None:
        params = {'bb_period': 20, 'bb_std': 2.0, 'rsi_period': 14}

    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(window=params['bb_period']).mean()
    bb_std = df['close'].rolling(window=params['bb_period']).std()
    df['bb_upper'] = df['bb_middle'] + (params['bb_std'] * bb_std)
    df['bb_lower'] = df['bb_middle'] - (params['bb_std'] * bb_std)

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=params['rsi_period']).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=params['rsi_period']).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # %B (position within Bollinger Bands)
    df['bb_pct_b'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

    # Bandwidth (volatility measure)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

    # ATR for stop loss
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = true_range.rolling(window=14).mean()

    return df


def generate_signals(df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
    """
    Generate mean reversion trading signals.

    Args:
        df: DataFrame with OHLCV data
        params: Strategy parameters

    Returns:
        DataFrame with trading signals
    """
    # Default parameters
    if params is None:
        params = {
            'bb_period': 20,
            'bb_std': 2.0,
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'atr_stop_multiplier': 1.5,
            'max_hold_days': 10
        }

    # Calculate indicators
    df = calculate_indicators(df, params)

    # Initialize signals
    signals = pd.DataFrame(index=df.index)
    signals['signal'] = 0
    signals['entry_price'] = np.nan
    signals['stop_loss'] = np.nan
    signals['target'] = np.nan
    signals['entry_date'] = pd.NaT

    # Entry conditions
    # Short entry: Overbought + above upper band
    short_entry = (
        (df['rsi'] > params['rsi_overbought']) &
        (df['close'] > df['bb_upper']) &
        (df['bb_pct_b'] > 1.0)
    )

    # Long entry: Oversold + below lower band
    long_entry = (
        (df['rsi'] < params['rsi_oversold']) &
        (df['close'] < df['bb_lower']) &
        (df['bb_pct_b'] < 0.0)
    )

    # Exit condition: Return to mean (middle band)
    exit_long = df['close'] >= df['bb_middle']
    exit_short = df['close'] <= df['bb_middle']

    # Generate signals (previous day's signal for current day execution)
    signals['signal'] = 0
    signals.loc[short_entry.shift(1).fillna(False), 'signal'] = -1
    signals.loc[long_entry.shift(1).fillna(False), 'signal'] = 1

    # Set exit signals
    signals.loc[exit_long, 'signal'] = 0
    signals.loc[exit_short, 'signal'] = 0

    # Set entry prices and stops
    signals.loc[signals['signal'] == 1, 'entry_price'] = df['close']
    signals.loc[signals['signal'] == 1, 'stop_loss'] = df['close'] - (params['atr_stop_multiplier'] * df['atr'])
    signals.loc[signals['signal'] == 1, 'target'] = df['bb_middle']

    signals.loc[signals['signal'] == -1, 'entry_price'] = df['close']
    signals.loc[signals['signal'] == -1, 'stop_loss'] = df['close'] + (params['atr_stop_multiplier'] * df['atr'])
    signals.loc[signals['signal'] == -1, 'target'] = df['bb_middle']

    return signals


def calculate_position_size(
    signal_strength: float,
    account_value: float,
    risk_per_trade: float = 0.02
) -> float:
    """
    Calculate position size based on signal strength.

    Args:
        signal_strength: How strong the signal is (0-1)
        account_value: Current account value
        risk_per_trade: Percentage of account to risk

    Returns:
        Position size in dollars
    """
    base_size = account_value * risk_per_trade

    # Scale by signal strength
    # Stronger signals (further from mean) get larger positions
    scaled_size = base_size * (0.5 + signal_strength)

    return scaled_size


# Example usage
if __name__ == "__main__":
    print("Mean Reversion Strategy Template")
    print("===============================")
    print()
    print("Strategy Parameters:")
    print("  - Bollinger Band Period: 20 days")
    print("  - Bollinger Band Std Dev: 2.0")
    print("  - RSI Overbought: > 70")
    print("  - RSI Oversold: < 30")
    print("  - Stop Loss: 1.5x ATR")
    print("  - Max Hold Time: 10 days")
    print()
    print("Entry Conditions:")
    print("  LONG: RSI < 30 AND Price < Lower BB")
    print("  SHORT: RSI > 70 AND Price > Upper BB")
    print()
    print("Exit Condition:")
    print("  Price returns to middle Bollinger Band")
