# Tutorial: Creating Custom Technical Indicators

Learn how to create custom technical indicators for use with the CBSC Strategy SDK. This tutorial covers indicator design, implementation, testing, and integration with strategies.

## Overview

Technical indicators are mathematical calculations based on historical price and volume data. The CBSC SDK provides a flexible framework for creating custom indicators that can be used in your trading strategies.

## Prerequisites

- Completed [Quick Start Guide](../QUICKSTART.md)
- Basic understanding of pandas DataFrame operations
- Familiarity with technical analysis concepts

## Indicator Structure

### Basic Indicator Template

All custom indicators should follow this structure:

```python
import pandas as pd
import numpy as np
from typing import Optional

def custom_indicator(
    df: pd.DataFrame,
    period: int = 14,
    column: str = "close"
) -> pd.Series:
    """
    Calculate custom technical indicator.

    Args:
        df: DataFrame with OHLCV data
        period: Calculation period
        column: Column to use for calculation

    Returns:
        Series with indicator values
    """
    # Validate inputs
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")

    if len(df) < period:
        raise ValueError(f"Insufficient data: need at least {period} rows")

    # Calculate indicator
    indicator_values = df[column].rolling(window=period).mean()

    return indicator_values
```

## Example 1: Simple Moving Average (SMA)

Let's create a simple moving average indicator:

```python
def sma(df: pd.DataFrame, period: int = 20, column: str = "close") -> pd.Series:
    """
    Calculate Simple Moving Average (SMA).

    SMA = Sum of prices / Number of periods

    Args:
        df: DataFrame with OHLCV data
        period: Number of periods for average
        column: Column to average (default: 'close')

    Returns:
        Series with SMA values
    """
    return df[column].rolling(window=period).mean()

# Usage
from cbsc_strategy_sdk import StrategyWorkspace
from datetime import date

async with StrategyWorkspace() as ws:
    data = await ws.get_historical_data(
        symbol="AAPL",
        start=date(2024, 1, 1),
        end=date(2024, 12, 31)
    )

    # Calculate SMA
    data["sma_20"] = sma(data, period=20)
    data["sma_50"] = sma(data, period=50)

    print(data[["close", "sma_20", "sma_50"]].tail())
```

## Example 2: Relative Strength Index (RSI)

A more complex indicator with multiple steps:

```python
def rsi(
    df: pd.DataFrame,
    period: int = 14,
    column: str = "close"
) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).

    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss

    Args:
        df: DataFrame with OHLCV data
        period: Calculation period (default: 14)
        column: Column to use (default: 'close')

    Returns:
        Series with RSI values (0-100)
    """
    # Calculate price changes
    delta = df[column].diff()

    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)

    # Calculate average gains and losses
    avg_gains = gains.rolling(window=period).mean()
    avg_losses = losses.rolling(window=period).mean()

    # Calculate RS (Relative Strength)
    rs = avg_gains / avg_losses

    # Calculate RSI
    rsi_values = 100 - (100 / (1 + rs))

    return rsi_values

# Usage
async with StrategyWorkspace() as ws:
    data = await ws.get_historical_data(
        symbol="AAPL",
        start=date(2024, 1, 1),
        end=date(2024, 12, 31)
    )

    # Calculate RSI
    data["rsi"] = rsi(data, period=14)

    # Identify overbought/oversold conditions
    data["overbought"] = data["rsi"] > 70
    data["oversold"] = data["rsi"] < 30

    print(data[["close", "rsi", "overbought", "oversold"]].tail())
```

## Example 3: Bollinger Bands

Multi-value indicator returning multiple series:

```python
def bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0,
    column: str = "close"
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.

    Bollinger Bands consist of:
    - Middle Band: SMA
    - Upper Band: SMA + (std_dev * standard deviation)
    - Lower Band: SMA - (std_dev * standard deviation)

    Args:
        df: DataFrame with OHLCV data
        period: Period for SMA and std calculation
        std_dev: Number of standard deviations
        column: Column to use (default: 'close')

    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    # Middle band (SMA)
    middle_band = df[column].rolling(window=period).mean()

    # Standard deviation
    std = df[column].rolling(window=period).std()

    # Upper and lower bands
    upper_band = middle_band + (std_dev * std)
    lower_band = middle_band - (std_dev * std)

    return upper_band, middle_band, lower_band

# Usage
async with StrategyWorkspace() as ws:
    data = await ws.get_historical_data(
        symbol="AAPL",
        start=date(2024, 1, 1),
        end=date(2024, 12, 31)
    )

    # Calculate Bollinger Bands
    data["bb_upper"], data["bb_middle"], data["bb_lower"] = bollinger_bands(data)

    # Calculate bandwidth and %B
    data["bb_width"] = (data["bb_upper"] - data["bb_lower"]) / data["bb_middle"]
    data["bb_pct_b"] = (data["close"] - data["bb_lower"]) / (data["bb_upper"] - data["bb_lower"])

    print(data[["close", "bb_upper", "bb_middle", "bb_lower", "bb_pct_b"]].tail())
```

## Example 4: MACD (Moving Average Convergence Divergence)

Complex indicator with multiple components:

```python
def macd(
    df: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    column: str = "close"
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    MACD Line = EMA(fast) - EMA(slow)
    Signal Line = EMA(MACD Line)
    Histogram = MACD Line - Signal Line

    Args:
        df: DataFrame with OHLCV data
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line EMA period (default: 9)
        column: Column to use (default: 'close')

    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    # Calculate EMAs
    ema_fast = df[column].ewm(span=fast_period, adjust=False).mean()
    ema_slow = df[column].ewm(span=slow_period, adjust=False).mean()

    # MACD line
    macd_line = ema_fast - ema_slow

    # Signal line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

    # Histogram
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram

# Usage
async with StrategyWorkspace() as ws:
    data = await ws.get_historical_data(
        symbol="AAPL",
        start=date(2024, 1, 1),
        end=date(2024, 12, 31)
    )

    # Calculate MACD
    data["macd"], data["macd_signal"], data["macd_hist"] = macd(data)

    # Identify crossovers
    data["macd_bullish"] = (data["macd"] > data["macd_signal"]) & (data["macd"].shift(1) <= data["macd_signal"].shift(1))
    data["macd_bearish"] = (data["macd"] < data["macd_signal"]) & (data["macd"].shift(1) >= data["macd_signal"].shift(1))

    print(data[["close", "macd", "macd_signal", "macd_hist"]].tail())
```

## Custom Indicator Class

For more complex indicators, create a class:

```python
from typing import Dict, Any

class CustomIndicator:
    """
    Base class for custom indicators.

    Provides common functionality for indicator calculation.
    """

    def __init__(self, params: Dict[str, Any] = None):
        """Initialize indicator with parameters."""
        self.params = params or {}
        self.name = self.__class__.__name__

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate indicator values.

        Must be implemented by subclasses.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Series with indicator values
        """
        raise NotImplementedError("Subclasses must implement calculate()")

    def validate(self, df: pd.DataFrame) -> bool:
        """
        Validate input data.

        Args:
            df: DataFrame to validate

        Returns:
            True if valid, raises exception otherwise
        """
        required_columns = ["open", "high", "low", "close", "volume"]
        missing = [col for col in required_columns if col not in df.columns]

        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        return True

    def __call__(self, df: pd.DataFrame) -> pd.Series:
        """Allow indicator to be called as a function."""
        self.validate(df)
        return self.calculate(df)


# Example custom indicator class
class ATRIndicator(CustomIndicator):
    """
    Average True Range (ATR) indicator.

    Measures market volatility.
    """

    def __init__(self, period: int = 14):
        super().__init__({"period": period})
        self.period = period

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate ATR.

        ATR = max(high-low, abs(high-close_prev), abs(low-close_prev))

        Returns:
            Series with ATR values
        """
        high = df["high"]
        low = df["low"]
        close = df["close"]

        # Previous close
        close_prev = close.shift(1)

        # True Range components
        tr1 = high - low
        tr2 = abs(high - close_prev)
        tr3 = abs(low - close_prev)

        # True Range
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR (average of TR)
        atr = tr.rolling(window=self.period).mean()

        return atr

# Usage
async with StrategyWorkspace() as ws:
    data = await ws.get_historical_data(
        symbol="AAPL",
        start=date(2024, 1, 1),
        end=date(2024, 12, 31)
    )

    # Create and use ATR indicator
    atr_indicator = ATRIndicator(period=14)
    data["atr"] = atr_indicator(data)

    print(data[["close", "atr"]].tail())
```

## Testing Custom Indicators

Always test your indicators before using them in strategies:

```python
import unittest

class TestCustomIndicator(unittest.TestCase):
    """Test suite for custom indicators."""

    def setUp(self):
        """Create test data."""
        import numpy as np
        np.random.seed(42)

        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        self.test_data = pd.DataFrame({
            "open": np.random.randn(100).cumsum() + 100,
            "high": np.random.randn(100).cumsum() + 102,
            "low": np.random.randn(100).cumsum() + 98,
            "close": np.random.randn(100).cumsum() + 100,
            "volume": np.random.randint(1000000, 10000000, 100)
        }, index=dates)

    def test_sma_calculation(self):
        """Test SMA calculation."""
        result = sma(self.test_data, period=20)

        # Check that result is a Series
        self.assertIsInstance(result, pd.Series)

        # Check that first 19 values are NaN
        self.assertTrue(result[:19].isna().all())

        # Check that 20th value is not NaN
        self.assertFalse(pd.isna(result.iloc[19]))

    def test_rsi_range(self):
        """Test RSI values are in valid range."""
        result = rsi(self.test_data, period=14)

        # RSI should be between 0 and 100
        self.assertTrue((result >= 0).all())
        self.assertTrue((result <= 100).all())

    def test_atr_positive(self):
        """Test ATR values are positive."""
        atr_indicator = ATRIndicator(period=14)
        result = atr_indicator(self.test_data)

        # ATR should always be positive
        self.assertTrue((result > 0).all())

# Run tests
if __name__ == "__main__":
    unittest.main()
```

## Best Practices

### 1. Input Validation

Always validate input data:

```python
def robust_indicator(df: pd.DataFrame, period: int) -> pd.Series:
    """Indicator with robust input validation."""

    # Check DataFrame
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

    # Check period
    if period <= 0:
        raise ValueError("Period must be positive")

    # Check sufficient data
    if len(df) < period:
        raise ValueError(f"Insufficient data: need at least {period} rows")

    # Check required columns
    required_cols = ["close"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Calculate indicator
    return df["close"].rolling(window=period).mean()
```

### 2. Documentation

Document your indicators thoroughly:

```python
def well_documented_indicator(
    df: pd.DataFrame,
    period: int = 14,
    column: str = "close"
) -> pd.Series:
    """
    Calculate a well-documented custom indicator.

    This indicator measures [brief description of what it measures].
    It's useful for [use case].

    Calculation:
        1. [Step 1]
        2. [Step 2]
        3. [Step 3]

    Interpretation:
        - Values > X indicate [interpretation]
        - Values < Y indicate [interpretation]

    Args:
        df: DataFrame with OHLCV data. Must contain at least `period` rows.
        period: Calculation period. Must be positive integer.
        column: Column to use for calculation. Must exist in DataFrame.

    Returns:
        Series with indicator values. Length equals input DataFrame.
        First `period-1` values will be NaN.

    Raises:
        ValueError: If period <= 0 or insufficient data
        TypeError: If df is not a DataFrame

    Examples:
        >>> data = pd.DataFrame({"close": [1, 2, 3, 4, 5]})
        >>> result = well_documented_indicator(data, period=3)
        >>> print(result)
        0    NaN
        1    NaN
        2    2.0
        3    3.0
        4    4.0

    References:
        - [Link to methodology or research paper]
        - [Author, Year]
    """
    # Implementation
    pass
```

### 3. Performance Optimization

Use vectorized operations for better performance:

```python
# Bad: Slow loop-based approach
def slow_indicator(df: pd.DataFrame, period: int) -> pd.Series:
    """Slow indicator using loops."""
    values = []
    for i in range(len(df)):
        if i < period - 1:
            values.append(np.nan)
        else:
            values.append(df["close"].iloc[i-period+1:i+1].mean())
    return pd.Series(values, index=df.index)

# Good: Fast vectorized approach
def fast_indicator(df: pd.DataFrame, period: int) -> pd.Series:
    """Fast indicator using vectorized operations."""
    return df["close"].rolling(window=period).mean()
```

## Integrating with Strategies

Use your custom indicators in strategies:

```python
async def rsi_mean_reversion_strategy(
    symbol: str,
    start_date: date,
    end_date: date,
    rsi_period: int = 14,
    entry_threshold: float = 30,
    exit_threshold: float = 70
):
    """
    Strategy using custom RSI indicator.

    Entry: RSI < entry_threshold (oversold)
    Exit: RSI > exit_threshold (overbought)
    """
    from cbsc_strategy_sdk import StrategyWorkspace, BacktestAdapter

    # Fetch data
    async with StrategyWorkspace() as ws:
        data = await ws.get_historical_data(symbol, start_date, end_date)

        # Calculate custom RSI indicator
        data["rsi"] = rsi(data, period=rsi_period)

        # Generate signals
        data["signal"] = 0
        data.loc[data["rsi"] < entry_threshold, "signal"] = 1   # Buy
        data.loc[data["rsi"] > exit_threshold, "signal"] = -1  # Sell

    # Run backtest
    async with BacktestAdapter() as adapter:
        result = await adapter.run_backtest(
            strategy_code="rsi_mean_reversion",
            symbols=[symbol],
            start_date=start_date,
            end_date=end_date,
            parameters={
                "rsi_period": rsi_period,
                "entry_threshold": entry_threshold,
                "exit_threshold": exit_threshold
            }
        )

        return result
```

## Next Steps

- Learn about [custom data sources](TUTORIAL_DATA_SOURCES.md)
- Explore [advanced backtesting techniques](TUTORIAL_ADVANCED_BACKTEST.md)
- Check out [example notebooks](../examples/) for complete strategies

---

**Version:** 0.1.0
**Last Updated:** 2026-01-11
