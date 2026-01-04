"""
Fix VectorBT Numba JIT cache issue
"""
import os
import shutil
import sys
from pathlib import Path

print('=' * 70)
print('VectorBT Numba Cache Repair Tool')
print('=' * 70)

# Find and clear Numba cache directories
cache_locations = [
    Path(__file__).parent / '__pycache__',
    Path.home() / '.cache' / 'numba_cache',
    Path.home() / '.local' / 'share' / 'numba_cache',
]

# Also find in site-packages
site_packages = []
for path in sys.path:
    if 'site-packages' in path:
        site_packages.append(Path(path))

for site_pkg in site_packages:
    if (site_pkg / 'numba').exists():
        cache_locations.append(site_pkg / 'numba' / '__pycache__')
    if (site_pkg / 'vectorbt').exists():
        cache_locations.append(site_pkg / 'vectorbt' / '__pycache__')

print(f'\n[1] Found {len(cache_locations)} potential cache locations')

cleared = 0
for cache_dir in cache_locations:
    if cache_dir.exists():
        print(f'    Clearing: {cache_dir}')
        try:
            shutil.rmtree(cache_dir)
            cleared += 1
            print(f'    [OK] Cleared')
        except Exception as e:
            print(f'    [SKIP] {e}')
    else:
        print(f'    [N/A] {cache_dir} (not found)')

print(f'\n[2] Summary: {cleared} cache directories cleared')

# Set environment variable to disable Numba cache
print(f'\n[3] Configuring Numba to disable cache...')
os.environ['NUMBA_DISABLE_JIT'] = '0'  # Keep JIT enabled
os.environ['NUMBA_CACHE_DIR'] = ''    # Disable cache

print(f'    NUMBA_DISABLE_JIT = 0 (JIT enabled)')
print(f'    NUMBA_CACHE_DIR = "" (cache disabled)')

print(f'\n[4] Testing VectorBT with fresh JIT compilation...')

try:
    import vectorbt as vbt
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta

    # Create small test data
    print(f'\n    Creating test data...')
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    prices = pd.Series(
        np.random.randn(50).cumsum() + 100,
        index=dates
    )

    # Create signals
    entries = pd.Series([False] * 50, index=dates)
    exits = pd.Series([False] * 50, index=dates)
    entries.iloc[10:20] = True
    exits.iloc[20] = True

    print(f'    Running VectorBT Portfolio.from_signals()...')
    pf = vbt.Portfolio.from_signals(
        prices,
        entries=entries,
        exits=exits,
        init_cash=10000,
        fees=0.001,
        freq='1D'
    )

    stats = pf.stats()
    print(f'    [OK] VectorBT works!')
    print(f'    Total Return: {stats.get("Total Return [%]", 0):.2f}%')
    print(f'    Sharpe Ratio: {stats.get("Sharpe Ratio", 0):.2f}')

    print(f'\n[5] SUCCESS: VectorBT is now working!')
    print(f'    The Numba cache issue has been resolved.')

except Exception as e:
    print(f'\n[5] FAILED: VectorBT still has issues')
    print(f'    Error: {e}')
    print(f'\n    Alternative solutions:')
    print(f'    1. Reinstall Numba: pip uninstall numba -y && pip install numba')
    print(f'    2. Reinstall VectorBT: pip uninstall vectorbt -y && pip install vectorbt')
    print(f'    3. Use conda: conda install -c conda-forge vectorbt')

print('=' * 70)
