"""
Test Momentum Indicators - Phase 2.2 Implementation
测试动量类扩展指标 - Phase 2.2实现
"""

import sys
import os
import pandas as pd
import numpy as np

def test_momentum_indicators():
    """测试动量类扩展指标"""

    # Add path to import the extended indicators
    sys.path.append(os.path.join(os.path.dirname(__file__), 'enhanced_nonprice_ta_system', 'extended'))

    try:
        from extended_technical_indicators import ExtendedTechnicalIndicators
    except ImportError as e:
        print(f"Import error: {e}")
        return False

    # Create test data
    dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
    np.random.seed(42)

    # Simulate comprehensive economic data
    base_value = 100
    price_data = []
    high_data = []
    low_data = []

    for i in range(len(dates)):
        # Add trend and cyclical components
        trend = base_value + i * 0.01
        cycle = 10 * np.sin(2 * np.pi * i / 50)
        noise = np.random.normal(0, 2)

        close = trend + cycle + noise
        high = close + abs(np.random.normal(0, 1))
        low = close - abs(np.random.normal(0, 1))

        price_data.append(close)
        high_data.append(high)
        low_data.append(low)

    # Simulate volume data
    volume_data = np.random.lognormal(10, 0.5, len(dates))

    close_series = pd.Series(price_data, index=dates)
    high_series = pd.Series(high_data, index=dates)
    low_series = pd.Series(low_data, index=dates)
    volume_series = pd.Series(volume_data, index=dates)

    # Create indicator calculator
    calculator = ExtendedTechnicalIndicators()

    print("Testing Momentum Indicators - Phase 2.2")
    print("=" * 60)

    # Test Extended RSI
    print("\n1. Extended RSI:")
    try:
        # Standard RSI
        rsi_std = calculator.calculate_rsi_extended(close_series, period=14, method='standard')
        std_metrics = calculator.get_indicator_performance_metrics(rsi_std)
        print(f"   RSI Standard: SUCCESS")
        print(f"   Mean: {std_metrics['mean']:.2f}, Valid: {std_metrics['valid_count']}")

        # Wilder RSI
        rsi_wild = calculator.calculate_rsi_extended(close_series, period=14, method='wilder')
        wild_metrics = calculator.get_indicator_performance_metrics(rsi_wild)
        print(f"   RSI Wilder: SUCCESS")
        print(f"   Mean: {wild_metrics['mean']:.2f}, Valid: {wild_metrics['valid_count']}")

        # Adaptive RSI
        rsi_adapt = calculator.calculate_rsi_extended(close_series, period=14, method='adaptive')
        adapt_metrics = calculator.get_indicator_performance_metrics(rsi_adapt)
        print(f"   RSI Adaptive: SUCCESS")
        print(f"   Mean: {adapt_metrics['mean']:.2f}, Valid: {adapt_metrics['valid_count']}")

        # Normalized RSI
        rsi_norm = calculator.calculate_rsi_extended(close_series, period=14, normalization='minmax')
        norm_metrics = calculator.get_indicator_performance_metrics(rsi_norm)
        print(f"   RSI Normalized: SUCCESS")
        print(f"   Mean: {norm_metrics['mean']:.2f}, Valid: {norm_metrics['valid_count']}")

        print("   Overall Status: SUCCESS")
    except Exception as e:
        print(f"   Overall Status: FAILED - {e}")
        return False

    # Test Stochastic Oscillator
    print("\n2. Stochastic Oscillator:")
    try:
        stochastic = calculator.calculate_stochastic(high_series, low_series, close_series)
        print(f"   Stochastic: SUCCESS")
        print(f"   %K Mean: {stochastic.values['%K'].mean():.2f}")
        print(f"   %D Mean: {stochastic.values['%D'].mean():.2f}")
        print(f"   Valid points: {stochastic.values['%K'].count()}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    # Test Williams %R
    print("\n3. Williams %R:")
    try:
        williams = calculator.calculate_williams_r(high_series, low_series, close_series)
        print(f"   Williams %R: SUCCESS")
        print(f"   Mean: {williams.values.mean():.2f}")
        print(f"   Range: {williams.values.min():.2f} to {williams.values.max():.2f}")
        print(f"   Valid points: {williams.values.count()}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    # Test CCI
    print("\n4. Commodity Channel Index:")
    try:
        cci = calculator.calculate_cci(high_series, low_series, close_series)
        cci_metrics = calculator.get_indicator_performance_metrics(cci)
        print(f"   CCI: SUCCESS")
        print(f"   Mean: {cci_metrics['mean']:.2f}")
        print(f"   Std Dev: {cci_metrics['std']:.2f}")
        print(f"   Valid points: {cci_metrics['valid_count']}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    # Test MFI
    print("\n5. Money Flow Index:")
    try:
        mfi = calculator.calculate_mfi(high_series, low_series, close_series, volume_series)
        mfi_metrics = calculator.get_indicator_performance_metrics(mfi)
        print(f"   MFI: SUCCESS")
        print(f"   Mean: {mfi_metrics['mean']:.2f}")
        print(f"   Range: {mfi_metrics['min']:.2f} to {mfi_metrics['max']:.2f}")
        print(f"   Valid points: {mfi_metrics['valid_count']}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    print("\n" + "=" * 60)
    print("Phase 2.2 Momentum Indicators Test Complete!")
    print("All 5 momentum indicator types implemented successfully!")
    print("Status: ALL TESTS PASSED")
    return True

if __name__ == "__main__":
    success = test_momentum_indicators()
    if success:
        print("\n🎉 Phase 2.2 completed successfully!")
    else:
        print("\n❌ Phase 2.2 failed!")