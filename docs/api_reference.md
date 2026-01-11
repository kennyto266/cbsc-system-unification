# CBSC Strategy SDK - API Reference

Complete API reference for the CBSC Strategy SDK. This document provides detailed documentation for all public interfaces, classes, methods, and functions.

## Table of Contents

- [Core Classes](#core-classes)
  - [StrategyWorkspace](#strategyworkspace)
  - [BacktestAdapter](#backtestadapter)
  - [BacktestResult](#backtestresult)
- [Configuration](#configuration)
  - [WorkspaceConfig](#workspaceconfig)
  - [create_config](#create_config)
- [Data Models](#data-models)
  - [OHLCVBar](#ohlcvbar)
  - [SymbolInfo](#symbolinfo)
- [Exceptions](#exceptions)
- [Optimization](#optimization)
  - [ParameterOptimizer](#parameteroptimizer)
  - [OptimizationResult](#optimizationresult)

---

## Core Classes

### StrategyWorkspace

Main workspace for strategy development in Jupyter notebooks. Provides unified interface for accessing market data, managing workspace state, and integrating with the CBSC backend API.

#### Constructor

```python
StrategyWorkspace(
    api_base: str = "http://localhost:3003",
    cache_ttl: int = 300,
    timeout: int = 30
) -> None
```

**Parameters:**
- `api_base` (str): Base URL for CBSC backend API. Default: `"http://localhost:3003"`
- `cache_ttl` (int): Cache time-to-live in seconds. Default: `300`
- `timeout` (int): HTTP request timeout in seconds. Default: `30`

**Example:**
```python
from cbsc_strategy_sdk import StrategyWorkspace

# Create workspace with custom settings
ws = StrategyWorkspace(
    api_base="http://localhost:3003",
    cache_ttl=600,
    timeout=60
)
```

#### Methods

##### async get_historical_data

Fetch historical OHLCV data for a symbol.

```python
async get_historical_data(
    symbol: str,
    start: date,
    end: date,
    interval: str = "1d"
) -> pd.DataFrame
```

**Parameters:**
- `symbol` (str): Trading symbol (e.g., "AAPL", "BTC-USD")
- `start` (date): Start date for data retrieval
- `end` (date): End date for data retrieval
- `interval` (str): Data interval - "1d", "1h", "5m", etc. Default: "1d"

**Returns:**
- `pd.DataFrame`: DataFrame with columns `[open, high, low, close, volume]` indexed by timestamp

**Raises:**
- `DataFetchError`: If data cannot be fetched from API
- `StrategyWorkspaceError`: If workspace is not initialized

**Example:**
```python
from datetime import date

async with StrategyWorkspace() as ws:
    data = ws.get_historical_data(
        symbol="AAPL",
        start=date(2024, 1, 1),
        end=date(2024, 12, 31),
        interval="1d"
    )
    print(data.head())
```

##### async get_available_symbols

Get list of available trading symbols.

```python
async get_available_symbols() -> List[SymbolInfo]
```

**Returns:**
- `List[SymbolInfo]`: List of available symbols with metadata

**Example:**
```python
async with StrategyWorkspace() as ws:
    symbols = ws.get_available_symbols()
    for symbol in symbols[:5]:
        print(f"{symbol.symbol}: {symbol.name}")
```

##### async clear_cache

Clear all cached data.

```python
async clear_cache() -> None
```

**Example:**
```python
async with StrategyWorkspace() as ws:
    # Clear cache to force fresh data fetch
    await ws.clear_cache()
```

---

### BacktestAdapter

Adapter for CBSC backtesting API with notebook-friendly interface. Supports async operations, progress tracking, and result visualization.

#### Constructor

```python
BacktestAdapter(
    api_base: str = "http://localhost:3003",
    timeout: int = 30,
    auth_token: Optional[str] = None
) -> None
```

**Parameters:**
- `api_base` (str): Base URL for CBSC backend API. Default: `"http://localhost:3003"`
- `timeout` (int): HTTP request timeout in seconds. Default: `30`
- `auth_token` (Optional[str]): JWT token for authentication. Default: `None`

**Example:**
```python
from cbsc_strategy_sdk import BacktestAdapter

adapter = BacktestAdapter(
    api_base="http://localhost:3003",
    auth_token="your_jwt_token"
)
```

#### Methods

##### async run_backtest

Run a strategy backtest.

```python
async run_backtest(
    strategy_code: str,
    symbols: List[str],
    start_date: date,
    end_date: date,
    parameters: Dict[str, Any] = None,
    initial_capital: float = 100000,
    progress_callback: Optional[Callable[[BacktestProgress], None]] = None
) -> BacktestResult
```

**Parameters:**
- `strategy_code` (str): Strategy code or function name
- `symbols` (List[str]): List of symbols to backtest
- `start_date` (date): Backtest start date
- `end_date` (date): Backtest end date
- `parameters` (Dict[str, Any], optional): Strategy parameters. Default: `None`
- `initial_capital` (float): Starting capital for backtest. Default: `100000`
- `progress_callback` (Optional[Callable]): Callback function for progress updates. Default: `None`

**Returns:**
- `BacktestResult`: Backtest results with metrics and trades

**Raises:**
- `APIConnectionError`: If API request fails
- `DataFetchError`: If backtest data cannot be retrieved

**Example:**
```python
from datetime import date

async with BacktestAdapter() as adapter:
    result = await adapter.run_backtest(
        strategy_code="rsi_strategy",
        symbols=["AAPL", "MSFT"],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        parameters={"rsi_period": 14},
        initial_capital=100000
    )
    print(f"Total Return: {result.metrics.total_return:.2%}")
```

##### async cancel_backtest

Cancel a running backtest.

```python
async cancel_backtest(job_id: str) -> bool
```

**Parameters:**
- `job_id` (str): Backtest job ID to cancel

**Returns:**
- `bool`: True if cancellation was successful

**Example:**
```python
async with BacktestAdapter() as adapter:
    # Start backtest and get job_id
    result = await adapter.run_backtest(...)
    job_id = result.job_id

    # Cancel if needed
    await adapter.cancel_backtest(job_id)
```

---

### BacktestResult

Container for backtest results with methods for analysis and visualization.

#### Properties

##### metrics

Backtest performance metrics.

```python
metrics: BacktestMetrics
```

**Properties:**
- `total_return` (float): Total return as decimal (0.15 = 15%)
- `sharpe_ratio` (float): Sharpe ratio
- `sortino_ratio` (float): Sortino ratio
- `max_drawdown` (float): Maximum drawdown as decimal
- `win_rate` (float): Win rate as decimal
- `profit_factor` (float): Profit factor
- `total_trades` (int): Total number of trades
- `avg_trade` (float): Average trade return
- `volatility` (float): Annualized volatility

**Example:**
```python
result = await adapter.run_backtest(...)
print(f"Total Return: {result.metrics.total_return:.2%}")
print(f"Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.metrics.max_drawdown:.2%}")
```

##### trades

List of trades executed during backtest.

```python
trades: List[BacktestTrade]
```

**Trade Properties:**
- `timestamp` (datetime): Trade timestamp
- `symbol` (str): Trading symbol
- `action` (str): "BUY" or "SELL"
- `price` (float): Execution price
- `quantity` (float): Trade quantity
- `value` (float): Trade value

**Example:**
```python
for trade in result.trades[:10]:
    print(f"{trade.timestamp}: {trade.action} {trade.quantity} {trade.symbol} @ {trade.price}")
```

#### Methods

##### plot_equity_curve

Plot the equity curve.

```python
plot_equity_curve(
    figsize: Tuple[int, int] = (12, 6),
    title: str = "Equity Curve"
) -> None
```

**Parameters:**
- `figsize` (Tuple[int, int]): Figure size (width, height). Default: `(12, 6)`
- `title` (str): Chart title. Default: `"Equity Curve"`

**Example:**
```python
result.plot_equity_curve(figsize=(14, 7), title="My Strategy Performance")
```

##### plot_drawdown

Plot drawdown over time.

```python
plot_drawdown(
    figsize: Tuple[int, int] = (12, 4),
    title: str = "Drawdown"
) -> None
```

**Parameters:**
- `figsize` (Tuple[int, int]): Figure size (width, height). Default: `(12, 4)`
- `title` (str): Chart title. Default: `"Drawdown"`

**Example:**
```python
result.plot_drawdown()
```

##### print_trade_summary

Print summary statistics of trades.

```python
print_trade_summary() -> None
```

**Example:**
```python
result.print_trade_summary()
```

**Output:**
```
Trade Summary
=============
Total Trades: 45
Winning Trades: 28 (62.2%)
Losing Trades: 17 (37.8%)

Average Win: $1,234.56
Average Loss: -$876.43
Profit Factor: 1.41

Best Trade: $5,432.10
Worst Trade: -$2,345.67
```

##### to_dataframe

Convert results to pandas DataFrame.

```python
to_dataframe() -> pd.DataFrame
```

**Returns:**
- `pd.DataFrame`: DataFrame with equity curve and metrics

**Example:**
```python
df = result.to_dataframe()
df.to_csv("backtest_results.csv")
```

---

## Configuration

### WorkspaceConfig

Configuration object for StrategyWorkspace.

#### Properties

```python
api_base: str              # CBSC API base URL
cache_ttl: int             # Cache time-to-live in seconds
timeout: int               # HTTP request timeout
max_retries: int           # Maximum retry attempts
retry_delay: float         # Delay between retries in seconds
```

### create_config

Factory function to create WorkspaceConfig.

```python
create_config(
    api_base: str = "http://localhost:3003",
    cache_ttl: int = 300,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> WorkspaceConfig
```

**Parameters:**
- `api_base` (str): CBSC API base URL
- `cache_ttl` (int): Cache TTL in seconds
- `timeout` (int): HTTP timeout
- `max_retries` (int): Maximum retries
- `retry_delay` (float): Retry delay

**Returns:**
- `WorkspaceConfig`: Configuration object

**Example:**
```python
from cbsc_strategy_sdk import create_config

config = create_config(
    api_base="http://localhost:3003",
    cache_ttl=600,
    timeout=60
)
```

---

## Data Models

### OHLCVBar

Single OHLCV (Open, High, Low, Close, Volume) data bar.

#### Properties

```python
timestamp: datetime    # Bar timestamp
open: float           # Open price
high: float           # High price
low: float            # Low price
close: float          # Close price
volume: float         # Trading volume
```

### SymbolInfo

Information about a trading symbol.

#### Properties

```python
symbol: str           # Trading symbol
name: str             # Symbol name
exchange: str         # Exchange
type: str             # Symbol type (stock, crypto, etc.)
currency: str         # Trading currency
```

---

## Exceptions

### StrategyWorkspaceError

Base exception for workspace errors.

```python
class StrategyWorkspaceError(Exception)
```

**Raised when:**
- Workspace not initialized
- Invalid configuration
- Resource not available

### DataFetchError

Exception for data fetching errors.

```python
class DataFetchError(StrategyWorkspaceError)
```

**Raised when:**
- API request fails
- Data parsing fails
- Invalid response format

### APIConnectionError

Exception for API connection errors.

```python
class APIConnectionError(StrategyWorkspaceError)
```

**Raised when:**
- Cannot connect to API
- Connection timeout
- Network errors

### ConfigurationError

Exception for configuration errors.

```python
class ConfigurationError(StrategyWorkspaceError)
```

**Raised when:**
- Invalid configuration parameters
- Missing required settings

---

## Optimization

### ParameterOptimizer

Optimizer for strategy parameter tuning using grid search and Bayesian optimization.

#### Methods

##### async grid_search

Perform grid search optimization.

```python
async grid_search(
    strategy_code: str,
    symbols: List[str],
    start_date: date,
    end_date: date,
    parameter_grid: Dict[str, List[Any]],
    metric: str = "sharpe_ratio",
    maximize: bool = True
) -> OptimizationResult
```

**Parameters:**
- `strategy_code` (str): Strategy code
- `symbols` (List[str]): Symbols to optimize
- `start_date` (date): Optimization start date
- `end_date` (date): Optimization end date
- `parameter_grid` (Dict[str, List[Any]]): Parameter grid to search
- `metric` (str): Metric to optimize. Default: `"sharpe_ratio"`
- `maximize` (bool): Whether to maximize the metric. Default: `True`

**Returns:**
- `OptimizationResult`: Optimization results

**Example:**
```python
from cbsc_strategy_sdk import ParameterOptimizer

async with ParameterOptimizer() as optimizer:
    result = await optimizer.grid_search(
        strategy_code="rsi_strategy",
        symbols=["AAPL"],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        parameter_grid={
            "rsi_period": [10, 14, 20],
            "entry_threshold": [25, 30, 35],
            "exit_threshold": [65, 70, 75]
        },
        metric="sharpe_ratio"
    )

    print(f"Best parameters: {result.best_params}")
    print(f"Best Sharpe ratio: {result.best_score:.2f}")
```

### OptimizationResult

Results from parameter optimization.

#### Properties

```python
best_params: Dict[str, Any]      # Best parameter combination
best_score: float                 # Best metric score
all_results: List[Dict]           # All optimization results
optimization_time: float          # Time taken in seconds
```

#### Methods

##### plot_results

Plot optimization results heatmap.

```python
plot_results(figsize: Tuple[int, int] = (10, 8)) -> None
```

**Example:**
```python
result.plot_results(figsize=(12, 10))
```

---

## Utility Functions

### get_version

Get the current SDK version.

```python
get_version() -> str
```

**Returns:**
- `str`: Version string (e.g., "0.1.0")

**Example:**
```python
from cbsc_strategy_sdk import get_version

print(f"SDK Version: {get_version()}")
```

### check_version

Check if the current SDK version meets requirements.

```python
check_version(required_version: str) -> bool
```

**Parameters:**
- `required_version` (str): Minimum required version

**Returns:**
- `bool`: True if current version >= required version

**Example:**
```python
from cbsc_strategy_sdk import check_version

if not check_version("0.2.0"):
    print("Please upgrade SDK to version 0.2.0 or higher")
```

---

## Type Hints

The SDK uses Python type hints for better IDE support and type checking.

```python
from typing import List, Dict, Optional, Callable, Tuple
from datetime import date, datetime
import pandas as pd
```

Common types used:
- `List[str]` - List of strings
- `Dict[str, Any]` - Dictionary with string keys
- `Optional[str]` - Optional string (can be None)
- `Callable[[BacktestProgress], None]` - Callback function
- `Tuple[int, int]` - Tuple of two integers
- `pd.DataFrame` - Pandas DataFrame

---

**Version:** 0.1.0
**Last Updated:** 2026-01-11
