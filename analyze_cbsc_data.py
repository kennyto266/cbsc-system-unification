#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBSC Backtest Data Authenticity Analysis Tool
Analyze data quality and reliability of acheng_sharpe_results.csv
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import sys

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import locale
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

def analyze_cbsc_data():
    """Comprehensive analysis of CBSC backtest data authenticity and reliability"""

    # Read data
    print("Reading data...")
    df = pd.read_csv('acheng_sharpe_results.csv')

    # Basic data structure analysis
    print('=== CBSC Backtest Data Authenticity Analysis Report ===')
    print(f'Data range: {df["Date"].iloc[0]} to {df["Date"].iloc[-1]}')
    print(f'Total trading days: {len(df)}')
    print(f'Number of columns: {len(df.columns)}')
    print(f'Column names: {list(df.columns)}')
    print()

    # Data integrity check
    print('=== Data Integrity Check ===')
    print('Missing values:')
    missing_data = {}
    for col in df.columns:
        missing = df[col].isnull().sum()
        missing_data[col] = missing
        if missing > 0:
            print(f'  {col}: {missing} ({missing/len(df)*100:.2f}%)')
        else:
            print(f'  {col}: Complete')
    print()

    # HSIF price analysis
    print('=== HSIF (Hang Seng Index Futures) Price Analysis ===')
    hsif_stats = df['HSIF_close'].describe()
    print(hsif_stats)
    print(f'Price range: {df["HSIF_close"].min():.0f} - {df["HSIF_close"].max():.0f}')
    print(f'Price change multiple: {df["HSIF_close"].max()/df["HSIF_close"].min():.2f}')

    # Check HSIF price reasonableness
    hsif_min_2010 = 14000  # Reasonable minimum for 2010
    hsif_max_2024 = 25000  # Reasonable maximum for 2024
    if df['HSIF_close'].min() < hsif_min_2010:
        print(f'WARNING: Minimum price {df["HSIF_close"].min():.0f} below reasonable 2010 level')
    if df['HSIF_close'].max() > hsif_max_2024:
        print(f'WARNING: Maximum price {df["HSIF_close"].max():.0f} above reasonable 2024 level')
    print()

    # USDCNH exchange rate analysis
    print('=== USDCNH Exchange Rate Analysis ===')
    usdcnh_stats = df['USDCNH_close'].describe()
    print(usdcnh_stats)
    print(f'Exchange rate range: {df["USDCNH_close"].min():.4f} - {df["USDCNH_close"].max():.4f}')

    # Check exchange rate reasonableness
    if df['USDCNH_close'].min() < 6.0 or df['USDCNH_close'].max() > 7.5:
        print('WARNING: USDCNH exchange rate range outside normal interval (6.0-7.5)')
    else:
        print('OK: USDCNH exchange rate range is normal')
    print()

    # Signal statistics
    print('=== Trading Signal Statistics ===')
    signal_counts = df['signal'].value_counts()
    print(signal_counts)
    print(f'Signal coverage: {signal_counts.sum()/len(df)*100:.2f}%')
    print(f'Buy signals: {signal_counts.get(1, 0)}')
    print(f'Sell signals: {signal_counts.get(-1, 0)}')
    print()

    # Strategy performance analysis
    print('=== Strategy Performance Analysis ===')
    valid_signals = df[df['signal'] != 0]
    strategy_returns = valid_signals['strategy_return']
    print(f'Number of trades: {len(strategy_returns)}')
    print(f'Average return per trade: {strategy_returns.mean():.6f}')
    print(f'Return standard deviation: {strategy_returns.std():.6f}')
    print(f'Maximum single trade profit: {strategy_returns.max():.6f}')
    print(f'Maximum single trade loss: {strategy_returns.min():.6f}')
    print(f'Win rate: {(strategy_returns > 0).sum() / len(strategy_returns) * 100:.2f}%')

    # Calculate cumulative returns
    df['cumulative_return'] = (1 + df['strategy_return']).cumprod()
    total_return = df['cumulative_return'].iloc[-1] - 1
    print(f'Total cumulative return: {total_return:.6f} ({total_return*100:.2f}%)')
    print()

    # Outlier detection
    print('=== Outlier Detection ===')
    # Check extreme daily returns
    extreme_market_returns = df[abs(df['HSIF_return']) > 0.05]
    extreme_strategy_returns = df[abs(df['strategy_return']) > 0.05]

    print(f'Extreme market return days (>5%): {len(extreme_market_returns)}')
    print(f'Extreme strategy return instances (>5%): {len(extreme_strategy_returns)}')

    if len(extreme_strategy_returns) > 0:
        print('Extreme strategy return examples:')
        print(extreme_strategy_returns[['Date', 'HSIF_return', 'strategy_return', 'signal']].head())
    print()

    # Price continuity check
    print('=== Price Continuity Check ===')
    gaps = df[df['HSIF_close'].isnull() | df['USDCNH_close'].isnull()]
    print(f'Missing price data days: {len(gaps)}')

    # Check duplicate dates
    duplicates = df[df.duplicated(subset=['Date'], keep=False)]
    print(f'Duplicate dates: {len(duplicates)}')

    # Check date continuity
    df['Date'] = pd.to_datetime(df['Date'])
    date_gaps = pd.date_range(start=df['Date'].min(), end=df['Date'].max(), freq='D').difference(df['Date'])
    print(f'Missing trading days: {len(date_gaps)}')
    print()

    # Correlation analysis
    print('=== Correlation Analysis ===')
    correlation = df[['HSIF_return', 'USDCNH_return', 'strategy_return']].corr()
    print(correlation)

    # Check strategy vs market return correlation
    strategy_market_corr = correlation.loc['HSIF_return', 'strategy_return']
    print(f'Strategy vs market return correlation: {strategy_market_corr:.4f}')

    if abs(strategy_market_corr) > 0.8:
        print('WARNING: Strategy-market correlation too high, possible overfitting')
    elif abs(strategy_market_corr) < 0.1:
        print('WARNING: Strategy-market correlation too low, possible data issues')
    else:
        print('OK: Strategy-market correlation is reasonable')
    print()

    # CBSC vs HSIF relationship analysis
    print('=== CBSC vs HSIF Relationship Analysis ===')
    print('CBSC (Callable Bull/Bear Contracts) are derivatives based on Hang Seng Index Futures:')
    print('- CBSC prices are highly correlated with HSIF futures prices')
    print('- CBSC has leverage effects, typically 5-10x leverage')
    print('- CBSC has mandatory knock-out mechanisms')
    print('- CBSC includes bull contracts (long) and bear contracts (short)')
    print()

    # Data reliability assessment
    print('=== Data Reliability Assessment ===')
    reliability_score = 0
    max_score = 10

    # Scoring criteria
    if missing_data['HSIF_close'] == 0:
        reliability_score += 2
        print('OK: HSIF price data complete (+2 points)')

    if missing_data['USDCNH_close'] == 0:
        reliability_score += 1
        print('OK: USDCNH exchange rate data complete (+1 point)')

    if 6.0 <= df['USDCNH_close'].min() and df['USDCNH_close'].max() <= 7.5:
        reliability_score += 1
        print('OK: Exchange rate data reasonable (+1 point)')

    if df['HSIF_close'].min() > 10000 and df['HSIF_close'].max() < 35000:
        reliability_score += 2
        print('OK: HSIF price range reasonable (+2 points)')

    if len(duplicates) == 0:
        reliability_score += 1
        print('OK: No duplicate dates (+1 point)')

    if len(extreme_strategy_returns) < len(strategy_returns) * 0.05:  # Extreme returns < 5%
        reliability_score += 1
        print('OK: Extreme return proportion reasonable (+1 point)')

    if 0.1 <= abs(strategy_market_corr) <= 0.8:
        reliability_score += 2
        print('OK: Strategy-market correlation reasonable (+2 points)')

    print(f'\nData reliability score: {reliability_score}/{max_score}')

    if reliability_score >= 8:
        print('GREEN: Data reliability - HIGH')
    elif reliability_score >= 6:
        print('YELLOW: Data reliability - MEDIUM')
    else:
        print('RED: Data reliability - LOW')

    # Potential issues identification
    print('\n=== Potential Issues Identification ===')
    issues = []

    if total_return > 5:  # Return > 500%
        issues.append("Total return too high, possible overfitting or data issues")

    if len(strategy_returns) < 100:  # Too few trades
        issues.append("Too few trades for statistical significance")

    if strategy_returns.std() > 0.1:  # Return volatility too high
        issues.append("Strategy return volatility too high, risk control issues")

    if len(extreme_strategy_returns) > len(strategy_returns) * 0.1:
        issues.append("High proportion of extreme returns, data quality questionable")

    if issues:
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
    else:
        print("OK: No obvious issues found")

    return {
        'total_records': len(df),
        'total_return': total_return,
        'trading_signals': len(strategy_returns),
        'reliability_score': reliability_score,
        'issues': issues
    }

if __name__ == "__main__":
    results = analyze_cbsc_data()