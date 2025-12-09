"""
Test Volatility Indicators - Phase 2.3 Implementation
测试波动率指标 - Phase 2.3实现
"""

import sys
import os
import pandas as pd
import numpy as np

def test_volatility_indicators():
    """测试波动率扩展指标"""

    # Add path to import the extended indicators
    sys.path.append(os.path.join(os.path.dirname(__file__), 'enhanced_nonprice_ta_system', 'extended'))

    try:
        from extended_technical_indicators import ExtendedTechnicalIndicators
    except ImportError as e:
        print(f"Import error: {e}")
        return False

    # Create test data with OHLC format
    dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
    np.random.seed(42)

    # Simulate realistic price data
    base_price = 100
    close_data = []
    high_data = []
    low_data = []

    for i in range(len(dates)):
        # Add trend and cyclical components
        trend = base_price + i * 0.01
        cycle = 5 * np.sin(2 * np.pi * i / 50)
        noise = np.random.normal(0, 1.5)

        close = trend + cycle + noise
        high = close + abs(np.random.normal(0, 0.8))
        low = close - abs(np.random.normal(0, 0.8))

        close_data.append(close)
        high_data.append(high)
        low_data.append(low)

    # Create series
    close_series = pd.Series(close_data, index=dates)
    high_series = pd.Series(high_data, index=dates)
    low_series = pd.Series(low_data, index=dates)

    # Create indicator calculator
    calculator = ExtendedTechnicalIndicators()

    print("Testing Volatility Indicators - Phase 2.3")
    print("=" * 60)

    # Test Bollinger Bands
    print("\n1. Bollinger Bands:")
    try:
        bb_result = calculator.calculate_bollinger_bands(close_series, period=20, std_dev=2.0)
        print(f"   Bollinger Bands: SUCCESS")
        print(f"   Upper Mean: {bb_result.values['upper'].mean():.2f}")
        print(f"   Middle Mean: {bb_result.values['middle'].mean():.2f}")
        print(f"   Lower Mean: {bb_result.values['lower'].mean():.2f}")
        print(f"   %B Mean: {bb_result.values['percent_b'].mean():.3f}")
        print(f"   Bandwidth Mean: {bb_result.values['bandwidth'].mean():.3f}")
        print(f"   Valid points: {bb_result.values['upper'].count()}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    # Test ATR
    print("\n2. Average True Range (ATR):")
    try:
        atr_result = calculator.calculate_atr(high_series, low_series, close_series, period=14)
        print(f"   ATR: SUCCESS")
        print(f"   ATR Mean: {atr_result.values.mean():.4f}")
        print(f"   ATR Std: {atr_result.values.std():.4f}")
        print(f"   ATR Percent Mean: {atr_result.metadata['atr_percent'].mean():.2f}%")
        print(f"   Valid points: {atr_result.values.count()}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    # Test Keltner Channels
    print("\n3. Keltner Channels:")
    try:
        kc_result = calculator.calculate_keltner_channels(
            high_series, low_series, close_series,
            ema_period=20, atr_period=10, multiplier=2.0
        )
        print(f"   Keltner Channels: SUCCESS")
        print(f"   Upper Mean: {kc_result.values['upper'].mean():.2f}")
        print(f"   Middle Mean: {kc_result.values['middle'].mean():.2f}")
        print(f"   Lower Mean: {kc_result.values['lower'].mean():.2f}")
        print(f"   Channel Position Mean: {kc_result.values['channel_position'].mean():.3f}")
        print(f"   Channel Width Mean: {kc_result.values['channel_width'].mean():.3f}")
        print(f"   Valid points: {kc_result.values['upper'].count()}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    # Test Donchian Channels
    print("\n4. Donchian Channels:")
    try:
        dc_result = calculator.calculate_donchian_channels(high_series, low_series, period=20)
        print(f"   Donchian Channels: SUCCESS")
        print(f"   Upper Mean: {dc_result.values['upper'].mean():.2f}")
        print(f"   Middle Mean: {dc_result.values['middle'].mean():.2f}")
        print(f"   Lower Mean: {dc_result.values['lower'].mean():.2f}")
        print(f"   Channel Width Mean: {dc_result.values['channel_width'].mean():.3f}")
        print(f"   Channel Position Mean: {dc_result.values['channel_position'].mean():.3f}")
        print(f"   Valid points: {dc_result.values['upper'].count()}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    # Test Batch Calculation
    print("\n5. Batch Volatility Indicators Test:")
    try:
        # Create DataFrame for batch calculation
        test_data = pd.DataFrame({
            'high': high_series,
            'low': low_series,
            'close': close_series
        })

        all_results = calculator.calculate_all_volatility_indicators(test_data)
        print(f"   Calculated indicators: {len(all_results)}")

        for name, result in list(all_results.items())[:8]:  # Show first 8
            if hasattr(result, 'values'):
                if isinstance(result.values, dict):
                    valid_count = result.values.get('upper', pd.Series()).count() if 'upper' in result.values else 0
                else:
                    valid_count = result.values.count()
                print(f"   {name}: Valid points {valid_count}")

        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    # Test different parameter combinations
    print("\n6. Parameter Sensitivity Test:")
    try:
        # Bollinger Bands with different parameters
        bb_short = calculator.calculate_bollinger_bands(close_series, period=10, std_dev=1.5)
        bb_long = calculator.calculate_bollinger_bands(close_series, period=50, std_dev=2.5)

        print(f"   BB Short (10, 1.5): Bandwidth {bb_short.values['bandwidth'].mean():.3f}")
        print(f"   BB Long (50, 2.5): Bandwidth {bb_long.values['bandwidth'].mean():.3f}")

        # ATR with different periods
        atr_short = calculator.calculate_atr(high_series, low_series, close_series, period=7)
        atr_long = calculator.calculate_atr(high_series, low_series, close_series, period=21)

        print(f"   ATR Short (7): {atr_short.values.mean():.4f}")
        print(f"   ATR Long (21): {atr_long.values.mean():.4f}")

        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    print("\n" + "=" * 60)
    print("Phase 2.3 Volatility Indicators Test Complete!")
    print("All 4 volatility indicator types implemented successfully!")
    print("Status: ALL TESTS PASSED")
    return True

if __name__ == "__main__":
    success = test_volatility_indicators()
    if success:
        print("\n🎉 Phase 2.3 completed successfully!")
    else:
        print("\n❌ Phase 2.3 failed!")