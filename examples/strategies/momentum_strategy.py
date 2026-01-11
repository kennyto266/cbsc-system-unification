"""
Momentum Strategy Template

A momentum-based trading strategy that identifies assets with strong upward
price momentum and enters long positions.

Strategy Rules:
- Entry: Price crosses above 200-day SMA AND RSI > 50
- Exit: Price crosses below 50-day SMA OR RSI < 40
- Position Sizing: Volatility-adjusted based on ATR
- Stop Loss: 2x ATR below entry price
- Take Profit: 3x ATR above entry price
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate technical indicators for momentum strategy.

    Args:
        df: DataFrame with OHLCV data

    Returns:
        DataFrame with added indicators
    """
    # Moving Averages
    df['sma_50'] = df['close'].rolling(window=50).mean()
    df['sma_200'] = df['close'].rolling(window=200).mean()

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # ATR (Average True Range) for volatility-based position sizing
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = true_range.rolling(window=14).mean()

    # Momentum indicator
    df['momentum'] = df['close'] - df['close'].shift(20)

    return df


def generate_signals(df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
    """
    Generate trading signals based on momentum strategy.

    Args:
        df: DataFrame with OHLCV data
        params: Strategy parameters (optional)

    Returns:
        DataFrame with trading signals
    """
    # Default parameters
    if params is None:
        params = {
            'sma_fast': 50,
            'sma_slow': 200,
            'rsi_entry': 50,
            'rsi_exit': 40,
            'atr_multiplier_stop': 2.0,
            'atr_multiplier_profit': 3.0,
            'min_momentum': 0
        }

    # Calculate indicators
    df = calculate_indicators(df)

    # Initialize signals DataFrame
    signals = pd.DataFrame(index=df.index)
    signals['signal'] = 0  # 0 = no position, 1 = long, -1 = short
    signals['stop_loss'] = np.nan
    signals['take_profit'] = np.nan
    signals['position_size'] = 0.0

    # Entry conditions (confluence of factors)
    entry_condition = (
        (df['close'] > df['sma_200']) &  # Price above long-term trend
        (df['close'] > df['sma_50']) &   # Price above short-term MA
        (df['rsi'] > params['rsi_entry']) &  # Strong momentum
        (df['momentum'] > params['min_momentum'])  # Positive momentum
    )

    # Exit conditions
    exit_condition = (
        (df['close'] < df['sma_50']) |  # Price below short-term MA
        (df['rsi'] < params['rsi_exit'])  # Momentum fading
    )

    # Generate signals
    signals.loc[entry_condition, 'signal'] = 1
    signals.loc[exit_condition, 'signal'] = 0

    # Calculate stop loss and take profit
    long_positions = signals['signal'] == 1
    signals.loc[long_positions, 'stop_loss'] = df['close'] - (params['atr_multiplier_stop'] * df['atr'])
    signals.loc[long_positions, 'take_profit'] = df['close'] + (params['atr_multiplier_profit'] * df['atr'])

    # Volatility-adjusted position sizing (risk 2% of capital per trade)
    risk_per_trade = 0.02
    signals.loc[long_positions, 'position_size'] = risk_per_trade / (df['atr'] / df['close'])

    return signals


def backtest(df: pd.DataFrame, initial_capital: float = 100000) -> pd.DataFrame:
    """
    Run simple backtest of momentum strategy.

    Args:
        df: DataFrame with OHLCV data
        initial_capital: Starting capital

    Returns:
        DataFrame with backtest results
    """
    signals = generate_signals(df)

    # Calculate returns
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = signals['signal'].shift(1) * df['returns']

    # Calculate equity curve
    df['equity'] = initial_capital * (1 + df['strategy_returns']).cumsum()

    return df


# Example usage
if __name__ == "__main__":
    # This would be used with the CBSC SDK
    print("Momentum Strategy Template")
    print("==========================")
    print()
    print("Strategy Parameters:")
    print("  - Fast SMA: 50 days")
    print("  - Slow SMA: 200 days")
    print("  - RSI Entry: > 50")
    print("  - RSI Exit: < 40")
    print("  - Stop Loss: 2x ATR")
    print("  - Take Profit: 3x ATR")
    print()
    print("Usage:")
    print("  from cbsc_strategy_sdk import BacktestAdapter")
    print("  from examples.strategies.momentum_strategy import generate_signals")
    print()
    print("  async with BacktestAdapter() as adapter:")
    print("      result = await adapter.run_backtest(")
    print("          strategy_code='momentum',")
    print("          symbols=['AAPL'],")
    print("          start_date=date(2023, 1, 1),")
    print("          end_date=date(2024, 12, 31)")
    print("      )")
