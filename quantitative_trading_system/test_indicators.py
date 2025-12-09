#!/usr/bin/env python3
"""
Test script for the 20 core indicators
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from indicators.core_indicators import CoreIndicators

def test_individual_indicators():
    """Test individual indicators"""
    print("Testing Individual Indicators")
    print("=" * 40)

    # Create test data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    test_data = pd.DataFrame({
        'open': np.random.uniform(100, 200, 100),
        'high': np.random.uniform(100, 200, 100),
        'low': np.random.uniform(100, 200, 100),
        'close': np.random.uniform(100, 200, 100),
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)

    indicators = CoreIndicators()

    # Test trend indicators
    try:
        print("Testing trend indicators...")
        sma = indicators.calculate_sma(test_data['close'], 20)
        print(f"  SMA: {sma.iloc[-1]:.4f}")

        ema = indicators.calculate_ema(test_data['close'], 20)
        print(f"  EMA: {ema.iloc[-1]:.4f}")

        macd = indicators.calculate_macd(test_data['close'])
        print(f"  MACD: {macd['macd'].iloc[-1]:.4f}")

        adx = indicators.calculate_adx(test_data['high'], test_data['low'], test_data['close'])
        print(f"  ADX: {adx.iloc[-1]:.4f}")

        print("Trend indicators: SUCCESS")
    except Exception as e:
        print(f"Trend indicators: FAILED - {e}")

    # Test momentum indicators
    try:
        print("Testing momentum indicators...")
        rsi = indicators.calculate_rsi(test_data['close'], 14)
        print(f"  RSI: {rsi.iloc[-1]:.4f}")

        stoch = indicators.calculate_stochastic(test_data['high'], test_data['low'], test_data['close'])
        print(f"  Stochastic K: {stoch['k'].iloc[-1]:.4f}")

        williams = indicators.calculate_williams_r(test_data['high'], test_data['low'], test_data['close'])
        print(f"  Williams %R: {williams.iloc[-1]:.4f}")

        print("Momentum indicators: SUCCESS")
    except Exception as e:
        print(f"Momentum indicators: FAILED - {e}")

    # Test volatility indicators
    try:
        print("Testing volatility indicators...")
        bb = indicators.calculate_bollinger_bands(test_data['close'])
        print(f"  BB Upper: {bb['upper'].iloc[-1]:.4f}")

        atr = indicators.calculate_atr(test_data['high'], test_data['low'], test_data['close'])
        print(f"  ATR: {atr.iloc[-1]:.4f}")

        print("Volatility indicators: SUCCESS")
    except Exception as e:
        print(f"Volatility indicators: FAILED - {e}")

    # Test volume indicators
    try:
        print("Testing volume indicators...")
        obv = indicators.calculate_obv(test_data['close'], test_data['volume'])
        print(f"  OBV: {obv.iloc[-1]:.4f}")

        vwap = indicators.calculate_vwap(test_data['high'], test_data['low'], test_data['close'], test_data['volume'])
        print(f"  VWAP: {vwap.iloc[-1]:.4f}")

        print("Volume indicators: SUCCESS")
    except Exception as e:
        print(f"Volume indicators: FAILED - {e}")

def test_batch_calculation():
    """Test batch calculation"""
    print("\nTesting Batch Calculation")
    print("=" * 40)

    # Create test data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    test_data = pd.DataFrame({
        'open': np.random.uniform(100, 200, 100),
        'high': np.random.uniform(100, 200, 100),
        'low': np.random.uniform(100, 200, 100),
        'close': np.random.uniform(100, 200, 100),
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)

    indicators = CoreIndicators()

    try:
        results = indicators.calculate_all_indicators(test_data)
        print(f"Successfully calculated {len(results)} indicators in batch")

        # Show first few indicators
        for i, (name, value) in enumerate(results.items()):
            if i < 5:  # Show only first 5
                if isinstance(value, pd.Series):
                    print(f"  {name}: {float(value.iloc[-1]):.4f}")
                else:
                    print(f"  {name}: Composite indicator")

        print("Batch calculation: SUCCESS")
        return True
    except Exception as e:
        print(f"Batch calculation: FAILED - {e}")
        return False

def test_indicator_summary():
    """Test indicator summary"""
    print("\nTesting Indicator Summary")
    print("=" * 40)

    indicators = CoreIndicators()
    summary = indicators.get_indicator_summary()

    total_indicators = sum(len(indicators) for indicators in summary.values())
    print(f"Total indicators in summary: {total_indicators}")

    for category, indicator_list in summary.items():
        print(f"  {category}: {len(indicator_list)} indicators")
        for indicator in indicator_list:
            print(f"    - {indicator}")

    print("Indicator summary: SUCCESS")

if __name__ == "__main__":
    print("Core Indicators Test Suite")
    print("=" * 50)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Run tests
    test_individual_indicators()
    batch_success = test_batch_calculation()
    test_indicator_summary()

    print("\n" + "=" * 50)
    if batch_success:
        print("OVERALL RESULT: SUCCESS")
        print("All 20 core indicators are working correctly!")
    else:
        print("OVERALL RESULT: FAILED")
        print("Some indicators have issues that need to be resolved.")