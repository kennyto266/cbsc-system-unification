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
