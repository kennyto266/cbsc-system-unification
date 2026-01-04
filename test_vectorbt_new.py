"""Test VectorBT with new Numba version"""
import vectorbt as vbt
import pandas as pd
import numpy as np

print('Testing VectorBT with Numba 0.63.1...')

# Create small test data
dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
prices = pd.Series(np.random.randn(50).cumsum() + 100, index=dates)

# Create signals
entries = pd.Series([False] * 50, index=dates)
exits = pd.Series([False] * 50, index=dates)
entries.iloc[10:20] = True
exits.iloc[20] = True

print('Creating portfolio...')
pf = vbt.Portfolio.from_signals(
    prices,
    entries=entries,
    exits=exits,
    init_cash=10000,
    fees=0.001,
    freq='1D'
)

stats = pf.stats()
print('SUCCESS!')
print(f'Total Return: {stats.get("Total Return [%]", 0):.2f}%')
print(f'Sharpe Ratio: {stats.get("Sharpe Ratio", 0):.2f}')
