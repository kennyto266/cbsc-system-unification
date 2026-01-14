# CBSC Strategy SDK - Quick Start Guide

Get started with the CBSC Strategy SDK in 5 minutes. This guide will walk you through installation, setup, and running your first trading strategy backtest.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.9+** installed
- **Jupyter Notebook** or **JupyterLab** installed
- Access to a running CBSC backend API (default: `http://localhost:3003`)
- Basic knowledge of Python programming

## Installation

### Step 1: Install the SDK

```bash
# Install via pip
pip install cbsc-strategy-sdk

# Or install from source
git clone https://github.com/your-org/cbsc-strategy-sdk.git
cd cbsc-strategy-sdk
pip install -e .
```

### Step 2: Install Jupyter (if not already installed)

```bash
pip install jupyter notebook
# or
pip install jupyterlab
```

### Step 3: Verify Installation

```python
# Test in Python
import cbsc_strategy_sdk as sdk
print(sdk.__version__)  # Should print: 0.1.0
```

## Your First Strategy in 5 Minutes

### Step 1: Start Jupyter Notebook

```bash
jupyter notebook
```

### Step 2: Create a New Notebook

Create a new Python 3 notebook and name it `my_first_strategy.ipynb`.

### Step 3: Import the SDK

```python
from cbsc_strategy_sdk import StrategyWorkspace, BacktestAdapter
from datetime import date
import pandas as pd
```

### Step 4: Fetch Historical Data

```python
# Create workspace context
async with StrategyWorkspace() as ws:
    # Fetch data for Apple stock
    data = ws.get_historical_data(
        symbol="AAPL",
        start=date(2024, 1, 1),
        end=date(2024, 12, 31)
    )

    # Display first few rows
    print(data.head())
```

**Expected Output:**
```
        open    high     low   close     volume
date
2024-01-01  185.50  187.20  184.90  186.80  50000000
2024-01-02  187.00  188.50  186.50  188.20  55000000
...
```

### Step 5: Run Your First Backtest

```python
# Define a simple RSI strategy
strategy_code = """
def generate_signals(df):
    # Calculate RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # Generate signals
    signals = pd.DataFrame(index=df.index)
    signals['signal'] = 0
    signals.loc[rsi < 30, 'signal'] = 1   # Buy when oversold
    signals.loc[rsi > 70, 'signal'] = -1  # Sell when overbought

    return signals
"""

# Run backtest
async with BacktestAdapter() as adapter:
    result = await adapter.run_backtest(
        strategy_code=strategy_code,
        symbols=["AAPL"],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        parameters={"rsi_period": 14}
    )

    # Print results
    print(f"Total Return: {result.metrics.total_return:.2%}")
    print(f"Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
    print(f"Max Drawdown: {result.metrics.max_drawdown:.2%}")
```

**Expected Output:**
```
Total Return: 15.32%
Sharpe Ratio: 1.45
Max Drawdown: -8.23%
```

### Step 6: Visualize Results

```python
# Plot equity curve
result.plot_equity_curve()

# Plot drawdowns
result.plot_drawdown()

# Display trade analysis
result.print_trade_summary()
```

## What's Next?

Congratulations! You've just run your first backtest. Here are some recommended next steps:

### Learn More

- **[API Reference](API_REFERENCE.md)** - Complete API documentation
- **[Tutorials](tutorials/)** - In-depth tutorials on specific topics
- **[Examples](../examples/)** - Jupyter notebook examples

### Advanced Features

1. **Multi-Factor Strategies**
   ```python
   # Combine multiple indicators
   result = await adapter.run_backtest(
       strategy_code="multi_factor_strategy",
       symbols=["AAPL", "MSFT", "GOOGL"],
       parameters={
           "rsi_period": 14,
           "macd_fast": 12,
           "macd_slow": 26,
           "volume_threshold": 1000000
       }
   )
   ```

2. **Parameter Optimization**
   ```python
   from cbsc_strategy_sdk import ParameterOptimizer

   async with ParameterOptimizer() as optimizer:
       best_params = await optimizer.grid_search(
           strategy_code="my_strategy",
           parameter_grid={
               "rsi_period": [10, 14, 20],
               "entry_threshold": [25, 30, 35],
               "exit_threshold": [65, 70, 75]
           }
       )
   ```

3. **Custom Data Sources**
   ```python
   # Integrate your own data
   async with StrategyWorkspace() as ws:
       # Use custom data connector
       custom_data = ws.get_custom_data(
           source="my_database",
           symbol="BTC-USD",
           start=date(2024, 1, 1),
           end=date(2024, 12, 31)
       )
   ```

## Common Issues

### Issue: Connection Refused

**Problem:** Cannot connect to CBSC backend API

**Solution:**
```bash
# Check if backend is running
curl http://localhost:3003/health

# Start backend if needed
cd /path/to/cbsc-backend
python -m uvicorn main:app --reload --port 3003
```

### Issue: No Data Returned

**Problem:** `get_historical_data()` returns empty DataFrame

**Solution:**
- Verify the symbol is correct
- Check date range (ensure there's data for that period)
- Confirm backend has data for the symbol

### Issue: Authentication Error

**Problem:** 401 Unauthorized error

**Solution:**
```python
# Provide auth token
async with BacktestAdapter(auth_token="your_jwt_token") as adapter:
    result = await adapter.run_backtest(...)
```

## Tips for Success

1. **Start Simple** - Begin with basic strategies before adding complexity
2. **Use Caching** - The SDK caches data automatically to speed up repeated queries
3. **Check Data Quality** - Always inspect data before running backtests
4. **Validate Strategies** - Use the built-in validation framework
5. **Monitor Performance** - Keep an eye on memory usage with large datasets

## Getting Help

- **Documentation:** [docs/](.)
- **Examples:** [examples/](../examples/)
- **GitHub Issues:** [Report a bug](https://github.com/your-org/cbsc-strategy-sdk/issues)
- **Community:** [Join our Discord](https://discord.gg/cbsc-sdk)

## Next Steps

- Explore [API Reference](API_REFERENCE.md) for detailed API documentation
- Check out [tutorials/](tutorials/) for advanced workflows
- Browse [examples/](../examples/) for complete notebook examples

---

**Version:** 0.1.0
**Last Updated:** 2026-01-11
