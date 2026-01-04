# tests/strategies/optimization/test_backtest_engine.py
import pytest
import pandas as pd
import numpy as np
from src.strategies.optimization.backtest.engine import BacktestEngine

def test_backtest_engine_initialization():
    """Test backtest engine can be initialized"""
    engine = BacktestEngine()
    assert engine is not None
    assert hasattr(engine, 'commission')

def test_backtest_simple_ma_strategy():
    """Test backtesting simple moving average strategy"""
    # Create sample price data
    np.random.seed(42)
    prices = pd.Series(100 + np.random.randn(100).cumsum())

    engine = BacktestEngine(initial_capital=10000, commission=0.001)

    # Define strategy: simple MA crossover
    def strategy(data):
        if len(data) < 20:
            return 0  # Hold

        short_ma = data['close'].iloc[-5:].mean()
        long_ma = data['close'].iloc[-20:].mean()

        if short_ma > long_ma:
            return 1  # Buy
        elif short_ma < long_ma:
            return -1  # Sell
        else:
            return 0  # Hold

    # Run backtest
    results = engine.run(prices.to_frame('close'), strategy)

    assert results is not None
    assert 'returns' in results
    assert 'total_return' in results
    assert 'sharpe_ratio' in results

# Critical Bug #1: Test small dataset with configurable window size
def test_backtest_small_dataset_with_window():
    """Test backtesting with small dataset and custom window size"""
    np.random.seed(42)
    # Create small dataset (<50 rows)
    prices = pd.Series(100 + np.random.randn(30).cumsum())

    engine = BacktestEngine(initial_capital=10000)

    def simple_strategy(data):
        if len(data) < 10:
            return 0
        return 1 if data['close'].iloc[-1] > data['close'].mean() else -1

    # Should work with window_size=10 for 30-row dataset
    results = engine.run(prices.to_frame('close'), simple_strategy, window_size=10)

    assert results is not None
    assert 'returns' in results
    assert results['n_trades'] > 0  # Should generate signals

# Critical Bug #2: Test empty data validation
def test_backtest_empty_data():
    """Test backtesting with empty data raises error"""
    engine = BacktestEngine()
    empty_data = pd.DataFrame()

    with pytest.raises(ValueError, match="Input data cannot be empty"):
        engine.run(empty_data, lambda x: 0)

# Critical Bug #2: Test missing close column validation
def test_backtest_missing_close_column():
    """Test backtesting without 'close' column raises error"""
    engine = BacktestEngine()
    data = pd.DataFrame({'open': [100, 101, 102]})

    with pytest.raises(ValueError, match="must contain 'close' column"):
        engine.run(data, lambda x: 0)

# Critical Bug #1: Test insufficient data validation
def test_backtest_insufficient_data():
    """Test backtesting with insufficient data for window size"""
    np.random.seed(42)
    prices = pd.Series(100 + np.random.randn(10).cumsum())

    engine = BacktestEngine()

    def simple_strategy(data):
        return 1

    # Should raise error when data < window_size
    with pytest.raises(ValueError, match="must have at least"):
        engine.run(prices.to_frame('close'), simple_strategy, window_size=20)

# Critical Bug #4: Test division by zero protection
def test_backtest_zero_returns():
    """Test win_rate calculation doesn't crash with zero returns"""
    engine = BacktestEngine()

    # Create data where no trades will occur
    prices = pd.Series([100] * 100)  # Flat prices, no signals

    def no_trade_strategy(data):
        return 0  # Always hold, no trades

    results = engine.run(prices.to_frame('close'), no_trade_strategy, window_size=10)

    assert results is not None
    assert results['win_rate'] == 0.0  # Should handle empty returns gracefully

# Additional edge case: Test initial capital is used correctly
def test_backtest_initial_capital_usage():
    """Test that initial_capital is properly used in calculations"""
    initial_capital = 50000
    engine = BacktestEngine(initial_capital=initial_capital)

    np.random.seed(42)
    prices = pd.Series(100 + np.random.randn(60).cumsum())

    def simple_strategy(data):
        return 1 if data['close'].iloc[-1] > data['close'].mean() else -1

    results = engine.run(prices.to_frame('close'), simple_strategy, window_size=10)

    assert 'initial_capital' in results
    assert results['initial_capital'] == initial_capital
    assert 'final_equity' in results
    # Verify final equity calculation
    expected_equity = initial_capital * (1 + results['total_return'])
    assert abs(results['final_equity'] - expected_equity) < 0.01

# Additional edge case: Test zero volatility data
def test_backtest_zero_volatility():
    """Test backtesting with constant prices (zero volatility)"""
    engine = BacktestEngine(commission=0, slippage=0)  # No costs to isolate price volatility

    # Create constant price data
    prices = pd.Series([100.0] * 60)

    def hold_strategy(data):
        return 0  # Hold, no trading

    results = engine.run(prices.to_frame('close'), hold_strategy, window_size=10)

    # Should handle gracefully
    assert results is not None
    assert results['total_return'] == 0.0  # No price change, no costs = no return
    # Note: volatility calculation uses returns, which are all zeros
    assert results['volatility'] >= 0.0

# Additional edge case: Test single window size
def test_backtest_exact_window_size():
    """Test backtesting with data exactly equal to window_size"""
    engine = BacktestEngine()

    np.random.seed(42)
    window_size = 20
    prices = pd.Series(100 + np.random.randn(window_size).cumsum())

    def simple_strategy(data):
        return 1

    results = engine.run(prices.to_frame('close'), simple_strategy, window_size=window_size)

    # Should work with exactly window_size rows
    assert results is not None
    assert 'returns' in results
