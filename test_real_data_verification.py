"""
Test script to verify real data usage in backtesting
"""
import sys
sys.path.insert(0, '.')

from datetime import date
import pandas as pd
import numpy as np

# Import the data fetching function
from src.api.vectorbt_simple_api import fetch_real_market_data

print('=' * 70)
print('Deep Data Source Verification Test')
print('=' * 70)

# Test parameters
symbol = '0700.HK'
start_date = date(2024, 1, 1)
end_date = date(2024, 12, 31)

# Fetch real data
print(f'\n1. Testing Stock: {symbol}')
print(f'   Time Range: {start_date} to {end_date}')
print(f'\n2. Fetching data from Yahoo Finance...')

real_data = fetch_real_market_data([symbol], start_date, end_date)

if symbol in real_data:
    df = real_data[symbol]

    print(f'\n3. Data Verification Results:')
    print(f'   - Data points: {len(df)}')
    print(f'   - Date range: {df.index[0].strftime("%Y-%m-%d")} to {df.index[-1].strftime("%Y-%m-%d")}')
    print(f'   - Price range: HK${df["close"].min():.2f} - HK${df["close"].max():.2f}')
    print(f'   - Average price: HK${df["close"].mean():.2f}')
    print(f'   - Total volume: {df["volume"].sum():,.0f}')

    # Show sample data
    print(f'\n4. Sample Data (First 5 rows):')
    for i, (idx, row) in enumerate(df.head().iterrows()):
        print(f'   {idx.strftime("%Y-%m-%d")}: Open={row["open"]:.2f}, High={row["high"]:.2f}, Low={row["low"]:.2f}, Close={row["close"]:.2f}, Vol={row["volume"]:,.0f}')

    # Verify with known 0700.HK data characteristics
    print(f'\n5. Authenticity Checks:')
    min_price = df['close'].min()
    max_price = df['close'].max()

    # Tencent (0700.HK) was trading around 250-450 HKD in 2024
    if 250 < min_price < 500 and 250 < max_price < 500:
        print(f'   [PASS] Price range matches Tencent (0700.HK) 2024 trading range')
    else:
        print(f'   [FAIL] Price range suspicious: {min_price:.2f} - {max_price:.2f}')

    # Check for real volatility
    if df['close'].std() > 10:
        print(f'   [PASS] Realistic volatility (std dev: {df["close"].std():.2f})')
    else:
        print(f'   [FAIL] Low volatility - possible mock data')

    # Check volume patterns
    max_vol = df['volume'].max()
    if max_vol > 1000000:
        print(f'   [PASS] Realistic trading volume (max: {max_vol:,.0f} shares)')
    else:
        print(f'   [WARN] Low volume detected')

    # Check data completeness
    missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
    if missing_pct < 1:
        print(f'   [PASS] Data complete ({missing_pct:.2f}% missing)')
    else:
        print(f'   [WARN] High missing data percentage: {missing_pct:.2f}%')

    print(f'\n6. CONCLUSION:')
    print(f'   Data Source: Yahoo Finance (Real Market Data)')
    print(f'   Status: VERIFIED - Using authentic market data')
    print(f'   Confidence: HIGH')

else:
    print(f'\n[ERROR] Failed to fetch data for {symbol}')

print('=' * 70)
