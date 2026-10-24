# Tutorial: Advanced Backtesting Techniques

Learn advanced backtesting techniques including walk-forward analysis, parameter optimization, and performance evaluation.

## Overview

This tutorial covers advanced backtesting methodologies used by professional quant traders to develop robust trading strategies.

## Prerequisites

- Completed [Quick Start Guide](../QUICKSTART.md)
- Understanding of basic backtesting concepts
- Experience with pandas and numpy

## Walk-Forward Analysis

Walk-forward analysis tests strategy stability over time by optimizing on historical data and validating on out-of-sample data.

### Basic Walk-Forward Implementation

```python
from datetime import date, timedelta
from typing import List, Tuple
import pandas as pd

from cbsc_strategy_sdk import BacktestAdapter, ParameterOptimizer

async def walk_forward_analysis(
    strategy_code: str,
    symbol: str,
    start_date: date,
    end_date: date,
    train_period: int = 252,  # ~1 year of trading days
    test_period: int = 63,     # ~3 months
    parameter_grid: dict = None
) -> pd.DataFrame:
    """
    Perform walk-forward analysis.

    Args:
        strategy_code: Strategy to test
        symbol: Trading symbol
        start_date: Analysis start date
        end_date: Analysis end date
        train_period: Training period in days
        test_period: Testing period in days
        parameter_grid: Parameters to optimize

    Returns:
        DataFrame with walk-forward results
    """
    results = []

    # Walk through time
    current_start = start_date
    iteration = 0

    while current_start < end_date:
        # Define train and test periods
        train_start = current_start
        train_end = train_start + timedelta(days=train_period)
        test_start = train_end
        test_end = test_start + timedelta(days=test_period)

        if test_end > end_date:
            break

        print(f"\nIteration {iteration + 1}:")
        print(f"  Train: {train_start} to {train_end}")
        print(f"  Test:  {test_start} to {test_end}")

        # Optimize on training data
        async with ParameterOptimizer() as optimizer:
            opt_result = await optimizer.grid_search(
                strategy_code=strategy_code,
                symbols=[symbol],
                start_date=train_start,
                end_date=train_end,
                parameter_grid=parameter_grid,
                metric="sharpe_ratio"
            )

        # Test on validation data
        async with BacktestAdapter() as adapter:
            test_result = await adapter.run_backtest(
                strategy_code=strategy_code,
                symbols=[symbol],
                start_date=test_start,
                end_date=test_end,
                parameters=opt_result.best_params
            )

        # Store results
        results.append({
            "iteration": iteration,
            "train_start": train_start,
            "train_end": train_end,
            "test_start": test_start,
            "test_end": test_end,
            "best_params": opt_result.best_params,
            "train_sharpe": opt_result.best_score,
            "test_return": test_result.metrics.total_return,
            "test_sharpe": test_result.metrics.sharpe_ratio,
            "test_max_dd": test_result.metrics.max_drawdown
        })

        # Move forward
        current_start = test_start
        iteration += 1

    return pd.DataFrame(results)

# Usage
result = await walk_forward_analysis(
    strategy_code="rsi_strategy",
    symbol="AAPL",
    start_date=date(2022, 1, 1),
    end_date=date(2024, 12, 31),
    parameter_grid={
        "rsi_period": [10, 14, 20],
        "entry_threshold": [25, 30, 35],
        "exit_threshold": [65, 70, 75]
    }
)

print(result)
```

## Parameter Optimization

### Grid Search

Exhaustive search over parameter space:

```python
from cbsc_strategy_sdk import ParameterOptimizer

async def grid_search_optimization():
    """Perform grid search optimization."""

    # Define parameter grid
    parameter_grid = {
        "rsi_period": [10, 14, 20, 25],
        "entry_threshold": [20, 25, 30, 35],
        "exit_threshold": [65, 70, 75, 80],
        "stop_loss": [0.02, 0.05, 0.10],
        "take_profit": [0.05, 0.10, 0.15]
    }

    # Calculate total combinations
    from itertools import product
    total_combos = 1
    for values in parameter_grid.values():
        total_combos *= len(values)

    print(f"Total combinations: {total_combos}")

    async with ParameterOptimizer() as optimizer:
        result = await optimizer.grid_search(
            strategy_code="rsi_strategy",
            symbols=["AAPL"],
            start_date=date(2023, 1, 1),
            end_date=date(2024, 12, 31),
            parameter_grid=parameter_grid,
            metric="sharpe_ratio"
        )

    print(f"Best parameters: {result.best_params}")
    print(f"Best Sharpe ratio: {result.best_score:.2f}")

    # Plot results
    result.plot_results()

    return result
```

### Bayesian Optimization

More efficient optimization using Bayesian methods:

```python
from skopt import gp_minimize
from skopt.space import Real, Integer
import numpy as np

async def bayesian_optimization():
    """Perform Bayesian optimization."""

    # Define search space
    search_space = [
        Integer(10, 30, name='rsi_period'),
        Integer(20, 35, name='entry_threshold'),
        Integer(65, 80, name='exit_threshold'),
        Real(0.01, 0.15, name='stop_loss'),
        Real(0.05, 0.20, name='take_profit')
    ]

    # Objective function
    async def objective(params):
        param_dict = {
            'rsi_period': params[0],
            'entry_threshold': params[1],
            'exit_threshold': params[2],
            'stop_loss': params[3],
            'take_profit': params[4]
        }

        async with BacktestAdapter() as adapter:
            result = await adapter.run_backtest(
                strategy_code="rsi_strategy",
                symbols=["AAPL"],
                start_date=date(2023, 1, 1),
                end_date=date(2024, 12, 31),
                parameters=param_dict
            )

        # Minimize negative Sharpe ratio
        return -result.metrics.sharpe_ratio

    # Run optimization
    n_calls = 50
    res = gp_minimize(objective, search_space, n_calls=n_calls, random_state=42)

    # Best parameters
    best_params = {
        'rsi_period': res.x[0],
        'entry_threshold': res.x[1],
        'exit_threshold': res.x[2],
        'stop_loss': res.x[3],
        'take_profit': res.x[4]
    }

    print(f"Best parameters: {best_params}")
    print(f"Best Sharpe ratio: {-res.fun:.2f}")

    return best_params
```

## Performance Metrics Analysis

### Custom Metrics

Calculate custom performance metrics:

```python
def calculate_custom_metrics(result) -> dict:
    """Calculate custom performance metrics."""

    metrics = {}

    # Calmar Ratio (Annual Return / Max Drawdown)
    metrics['calmar_ratio'] = (
        result.metrics.total_return / abs(result.metrics.max_drawdown)
    )

    # Sortino Ratio (using downside deviation)
    returns = pd.Series([trade.return_pct for trade in result.trades])
    downside_returns = returns[returns < 0]
    downside_deviation = downside_returns.std()
    if downside_deviation > 0:
        metrics['sortino_ratio'] = (
            returns.mean() / downside_deviation * np.sqrt(252)
        )
    else:
        metrics['sortino_ratio'] = np.nan

    # Win/Loss Ratio
    winning_trades = [t for t in result.trades if t.return_pct > 0]
    losing_trades = [t for t in result.trades if t.return_pct < 0]

    if winning_trades and losing_trades:
        avg_win = np.mean([t.return_pct for t in winning_trades])
        avg_loss = np.mean([t.return_pct for t in losing_trades])
        metrics['win_loss_ratio'] = abs(avg_win / avg_loss)
    else:
        metrics['win_loss_ratio'] = np.nan

    # Expectancy (Average return per trade)
    metrics['expectancy'] = returns.mean()

    # Profit Factor
    total_profit = winning_trades.sum() if winning_trades else 0
    total_loss = abs(losing_trades.sum()) if losing_trades else 0
    metrics['profit_factor'] = total_profit / total_loss if total_loss > 0 else np.nan

    return metrics

# Usage
custom_metrics = calculate_custom_metrics(result)
for metric, value in custom_metrics.items():
    print(f"{metric}: {value:.4f}")
```

### Rolling Metrics

Analyze metrics over rolling windows:

```python
def calculate_rolling_metrics(equity_curve: pd.Series, window: int = 63) -> pd.DataFrame:
    """Calculate rolling performance metrics."""

    rolling_metrics = pd.DataFrame(index=equity_curve.index)

    # Rolling returns
    rolling_metrics['rolling_return'] = equity_curve.pct_change(window)

    # Rolling Sharpe ratio
    rolling_returns = equity_curve.pct_change()
    rolling_metrics['rolling_sharpe'] = (
        rolling_returns.rolling(window).mean() /
        rolling_returns.rolling(window).std() * np.sqrt(252)
    )

    # Rolling volatility
    rolling_metrics['rolling_volatility'] = (
        rolling_returns.rolling(window).std() * np.sqrt(252)
    )

    # Rolling max drawdown
    rolling_max = equity_curve.rolling(window).max()
    rolling_drawdown = (equity_curve - rolling_max) / rolling_max
    rolling_metrics['rolling_max_dd'] = rolling_drawdown.rolling(window).min()

    return rolling_metrics

# Usage
equity_curve = result.equity_curve
rolling_metrics = calculate_rolling_metrics(equity_curve, window=63)

# Plot
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

rolling_metrics['rolling_sharpe'].plot(ax=axes[0], title='Rolling Sharpe Ratio (63-day)')
rolling_metrics['rolling_max_dd'].plot(ax=axes[1], title='Rolling Max Drawdown (63-day)')

plt.tight_layout()
plt.show()
```

## Monte Carlo Simulation

Test strategy robustness with Monte Carlo simulation:

```python
import numpy as np

def monte_carlo_simulation(
    returns: pd.Series,
    num_simulations: int = 1000,
    num_days: int = 252
) -> pd.DataFrame:
    """
    Run Monte Carlo simulation on strategy returns.

    Args:
        returns: Strategy returns series
        num_simulations: Number of simulations
        num_days: Number of days to simulate

    Returns:
        DataFrame with simulation results
    """
    simulations = []

    for _ in range(num_simulations):
        # Randomly sample returns
        sampled_returns = np.random.choice(returns, size=num_days, replace=True)

        # Calculate cumulative returns
        cum_returns = (1 + sampled_returns).cumprod()

        simulations.append(cum_returns)

    # Convert to DataFrame
    sim_df = pd.DataFrame(simulations).T

    # Calculate statistics
    stats = pd.DataFrame({
        'mean': sim_df.mean(axis=1),
        'std': sim_df.std(axis=1),
        'percentile_5': sim_df.quantile(0.05, axis=1),
        'percentile_95': sim_df.quantile(0.95, axis=1),
        'min': sim_df.min(axis=1),
        'max': sim_df.max(axis=1)
    })

    return stats

# Usage
returns = result.equity_curve.pct_change().dropna()
mc_results = monte_carlo_simulation(returns, num_simulations=1000)

# Plot
plt.figure(figsize=(12, 6))
plt.plot(mc_results.index, mc_results['percentile_5'], 'r--', label='5th percentile')
plt.plot(mc_results.index, mc_results['mean'], 'b-', label='Mean')
plt.plot(mc_results.index, mc_results['percentile_95'], 'r--', label='95th percentile')
plt.fill_between(
    mc_results.index,
    mc_results['percentile_5'],
    mc_results['percentile_95'],
    alpha=0.2
)
plt.title('Monte Carlo Simulation - Equity Curve Projections')
plt.legend()
plt.show()
```

## Multi-Asset Backtesting

Test strategy across multiple assets:

```python
async def multi_asset_backtest(
    strategy_code: str,
    symbols: List[str],
    start_date: date,
    end_date: date,
    parameters: dict = None
) -> dict:
    """
    Run backtest across multiple assets.

    Returns dictionary of results by symbol.
    """
    results = {}

    for symbol in symbols:
        print(f"\nBacktesting {symbol}...")

        async with BacktestAdapter() as adapter:
            result = await adapter.run_backtest(
                strategy_code=strategy_code,
                symbols=[symbol],
                start_date=start_date,
                end_date=end_date,
                parameters=parameters
            )

        results[symbol] = result

    # Analyze results
    summary = pd.DataFrame({
        symbol: {
            'total_return': result.metrics.total_return,
            'sharpe_ratio': result.metrics.sharpe_ratio,
            'max_drawdown': result.metrics.max_drawdown,
            'win_rate': result.metrics.win_rate
        }
        for symbol, result in results.items()
    }).T

    print("\nMulti-Asset Summary:")
    print(summary)

    return results

# Usage
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
results = await multi_asset_backtest(
    strategy_code="rsi_strategy",
    symbols=symbols,
    start_date=date(2023, 1, 1),
    end_date=date(2024, 12, 31),
    parameters={"rsi_period": 14}
)
```

## Benchmark Comparison

Compare strategy against benchmark:

```python
async def benchmark_comparison(
    strategy_code: str,
    symbol: str,
    benchmark: str,
    start_date: date,
    end_date: date,
    parameters: dict = None
):
    """Compare strategy performance against benchmark."""

    # Strategy backtest
    async with BacktestAdapter() as adapter:
        strategy_result = await adapter.run_backtest(
            strategy_code=strategy_code,
            symbols=[symbol],
            start_date=start_date,
            end_date=end_date,
            parameters=parameters
        )

        # Buy-and-hold benchmark
        benchmark_result = await adapter.run_backtest(
            strategy_code="buy_and_hold",
            symbols=[benchmark],
            start_date=start_date,
            end_date=end_date
        )

    # Compare metrics
    comparison = pd.DataFrame({
        'Strategy': [
            strategy_result.metrics.total_return,
            strategy_result.metrics.sharpe_ratio,
            strategy_result.metrics.max_drawdown
        ],
        'Benchmark': [
            benchmark_result.metrics.total_return,
            benchmark_result.metrics.sharpe_ratio,
            benchmark_result.metrics.max_drawdown
        ]
    }, index=['Return', 'Sharpe', 'Max DD'])

    print(comparison)

    # Plot equity curves
    plt.figure(figsize=(12, 6))
    plt.plot(strategy_result.equity_curve.index, strategy_result.equity_curve, label='Strategy')
    plt.plot(benchmark_result.equity_curve.index, benchmark_result.equity_curve, label='Benchmark')
    plt.title('Strategy vs Benchmark')
    plt.legend()
    plt.show()

    return comparison
```

## Best Practices

1. **Use out-of-sample testing** - Always validate on unseen data
2. **Account for transaction costs** - Include realistic trading costs
3. **Avoid overfitting** - Keep strategies simple
4. **Test robustness** - Use Monte Carlo and sensitivity analysis
5. **Monitor regime changes** - Test across different market conditions
6. **Keep detailed records** - Document all tests and results

## Next Steps

- Explore [example notebooks](../examples/) for complete implementations
- Learn about [custom indicators](TUTORIAL_CUSTOM_INDICATORS.md)
- Check out [strategy templates](../examples/strategies/)

---

**Version:** 0.1.0
**Last Updated:** 2026-01-11
