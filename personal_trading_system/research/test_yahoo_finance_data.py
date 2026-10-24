#!/usr/bin/env python3
"""
Yahoo Finance Historical Data Quality Test
Test Yahoo Finance for 5+ year historical data availability
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def test_yahoo_finance_historical_data():
    """Test Yahoo Finance for extended historical data"""
    print("Testing Yahoo Finance Historical Data Quality")
    print("=" * 50)

    # Test symbols - major HK stocks
    test_symbols = ['0700.HK', '0941.HK', '1398.HK', '0005.HK', '0388.HK']
    test_periods = [5, 7, 10]

    results = {}

    for symbol in test_symbols:
        print(f"\nTesting {symbol}...")
        symbol_results = {}

        try:
            ticker = yf.Ticker(symbol)

            for years in test_periods:
                start_date = datetime.now() - timedelta(days=years*365)

                try:
                    hist = ticker.history(start=start_date)

                    if len(hist) > 0:
                        data_points = len(hist)
                        actual_years = (hist.index.max() - hist.index.min()).days / 365.25
                        completeness = data_points / (years * 252) if years > 0 else 0  # ~252 trading days per year

                        symbol_results[years] = {
                            'success': True,
                            'data_points': data_points,
                            'actual_years': actual_years,
                            'completeness_percentage': min(completeness, 1.0) * 100,
                            'start_date': str(hist.index.min().date()),
                            'end_date': str(hist.index.max().date()),
                            'columns': list(hist.columns)
                        }

                        print(f"  {years} years: {data_points} records, {actual_years:.1f} years, {min(completeness, 1.0):.1%} complete")
                    else:
                        symbol_results[years] = {
                            'success': False,
                            'error': 'No data returned'
                        }
                        print(f"  {years} years: FAILED - No data")

                except Exception as e:
                    symbol_results[years] = {
                        'success': False,
                        'error': str(e)
                    }
                    print(f"  {years} years: ERROR - {e}")

        except Exception as e:
            print(f"  FAILED to create ticker: {e}")
            symbol_results = {'error': f'Ticker creation failed: {e}'}

        results[symbol] = symbol_results

    # Summary Analysis
    print("\n" + "=" * 50)
    print("YAHOO FINANCE DATA AVAILABILITY SUMMARY")
    print("=" * 50)

    total_symbols = len([s for s in results.values() if isinstance(s, dict) and not 'error' in s])
    symbols_with_5yr = len([s for s in results.values()
                           if isinstance(s, dict) and
                              s.get(5, {}).get('success', False)])
    symbols_with_7yr = len([s for s in results.values()
                           if isinstance(s, dict) and
                              s.get(7, {}).get('success', False)])
    symbols_with_10yr = len([s for s in results.values()
                            if isinstance(s, dict) and
                               s.get(10, {}).get('success', False)])

    print(f"Total symbols tested: {total_symbols}")
    print(f"Symbols with 5+ years: {symbols_with_5yr}/{total_symbols}")
    print(f"Symbols with 7+ years: {symbols_with_7yr}/{total_symbols}")
    print(f"Symbols with 10+ years: {symbols_with_10yr}/{total_symbols}")

    # Assessment
    print("\nASSESSMENT:")
    if symbols_with_5yr >= total_symbols * 0.8:
        print("EXCELLENT: Yahoo Finance provides sufficient 5+ year data")
        print("RECOMMENDATION: Proceed with Yahoo Finance as primary data source")
    elif symbols_with_5yr >= total_symbols * 0.5:
        print("GOOD: Yahoo Finance provides adequate 5+ year data")
        print("RECOMMENDATION: Use Yahoo Finance with backup data sources")
    else:
        print("LIMITED: Yahoo Finance data availability is insufficient")
        print("RECOMMENDATION: Implement multi-source data strategy")

    return results

def test_data_quality():
    """Test the quality of Yahoo Finance data"""
    print("\nTesting Data Quality...")
    print("-" * 30)

    try:
        # Test with a well-known stock
        ticker = yf.Ticker('0700.HK')
        hist = ticker.history(start=datetime.now() - timedelta(days=5*365))

        print(f"Sample data for 0700.HK:")
        print(f"  Records: {len(hist)}")
        print(f"  Columns: {list(hist.columns)}")
        print(f"  Date range: {hist.index.min().date()} to {hist.index.max().date()}")

        # Check for data quality issues
        missing_data = hist.isnull().sum()
        print(f"\nMissing data:")
        for col, count in missing_data.items():
            if count > 0:
                print(f"  {col}: {count} missing records")

        # Check price consistency
        price_cols = ['Open', 'High', 'Low', 'Close']
        if all(col in hist.columns for col in price_cols):
            inconsistent = (
                (hist['High'] < hist['Open']).any() |
                (hist['High'] < hist['Close']).any() |
                (hist['Low'] > hist['Open']).any() |
                (hist['Low'] > hist['Close']).any()
            )
            print(f"\nPrice consistency: {'PASS' if not inconsistent else 'FAILED'}")

        # Check for zero or negative prices
        zero_prices = (
            (hist[price_cols] <= 0).any().any()
        )
        print(f"Price validity: {'PASS' if not zero_prices else 'FAILED'}")

        print("\nData quality assessment: GOOD" if not inconsistent and not zero_prices else "NEEDS INVESTIGATION")

    except Exception as e:
        print(f"Data quality test failed: {e}")

if __name__ == "__main__":
    results = test_yahoo_finance_historical_data()
    test_data_quality()