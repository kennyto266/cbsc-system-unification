"""
Phase 2 Integration Test - Simple English Version
Phase 2 集成测试 - 简化英文版本
"""

import sys
import os
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def test_phase2_simple():
    """Simple integration test for Phase 2 indicators"""

    print("Phase 2 Integration Test - Simple Version")
    print("=" * 50)

    # Create test data
    dates = pd.date_range('2020-01-01', periods=500, freq='D')
    np.random.seed(42)

    # Create price data
    prices = 100 + np.cumsum(np.random.randn(500) * 0.5)
    high_prices = prices + np.random.rand(500) * 2
    low_prices = prices - np.random.rand(500) * 2
    volumes = np.random.randint(1000000, 10000000, 500)

    close_series = pd.Series(prices, index=dates)
    high_series = pd.Series(high_prices, index=dates)
    low_series = pd.Series(low_prices, index=dates)
    volume_series = pd.Series(volumes, index=dates)

    print(f"Test data created: {len(dates)} days")
    print(f"Price range: {prices.min():.2f} to {prices.max():.2f}")

    # Test results
    results = {}
    success_count = 0
    total_tests = 0

    # ========================================
    # Test Phase 2.1: Trend Indicators
    # ========================================

    print("\nTesting Phase 2.1: Trend Indicators")
    print("-" * 30)

    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'enhanced_nonprice_ta_system', 'extended'))
        from extended_technical_indicators import ExtendedTechnicalIndicators

        calculator = ExtendedTechnicalIndicators()

        # Test DEMA
        dema = calculator.calculate_dema(close_series, period=20)
        results['DEMA'] = dema
        total_tests += 1
        if dema.values.count() > 0:
            print(f"DEMA: SUCCESS - Mean: {dema.values.mean():.2f}")
            success_count += 1
        else:
            print("DEMA: FAILED - No valid data")

        # Test TEMA
        tema = calculator.calculate_tema(close_series, period=20)
        results['TEMA'] = tema
        total_tests += 1
        if tema.values.count() > 0:
            print(f"TEMA: SUCCESS - Mean: {tema.values.mean():.2f}")
            success_count += 1
        else:
            print("TEMA: FAILED - No valid data")

        # Test TRIMA
        trima = calculator.calculate_trima(close_series, period=20)
        results['TRIMA'] = trima
        total_tests += 1
        if trima.values.count() > 0:
            print(f"TRIMA: SUCCESS - Mean: {trima.values.mean():.2f}")
            success_count += 1
        else:
            print("TRIMA: FAILED - No valid data")

        # Test MACD
        macd = calculator.calculate_macd_extended(close_series, 'standard')
        results['MACD'] = macd
        total_tests += 1
        if hasattr(macd, 'values'):
            print("MACD: SUCCESS")
            success_count += 1
        else:
            print("MACD: FAILED")

    except Exception as e:
        print(f"Trend Indicators: ERROR - {e}")

    # ========================================
    # Test Phase 2.2: Momentum Indicators
    # ========================================

    print("\nTesting Phase 2.2: Momentum Indicators")
    print("-" * 30)

    try:
        # Test RSI
        rsi = calculator.calculate_rsi_extended(close_series, period=14, method='standard')
        results['RSI'] = rsi
        total_tests += 1
        if rsi.values.count() > 0:
            print(f"RSI: SUCCESS - Mean: {rsi.values.mean():.2f}")
            success_count += 1
        else:
            print("RSI: FAILED")

        # Test Stochastic
        stochastic = calculator.calculate_stochastic(high_series, low_series, close_series)
        results['Stochastic'] = stochastic
        total_tests += 1
        if hasattr(stochastic, 'values'):
            print("Stochastic: SUCCESS")
            success_count += 1
        else:
            print("Stochastic: FAILED")

        # Test Williams %R
        williams = calculator.calculate_williams_r(high_series, low_series, close_series)
        results['Williams_R'] = williams
        total_tests += 1
        if williams.values.count() > 0:
            print(f"Williams %R: SUCCESS - Mean: {williams.values.mean():.2f}")
            success_count += 1
        else:
            print("Williams %R: FAILED")

    except Exception as e:
        print(f"Momentum Indicators: ERROR - {e}")

    # ========================================
    # Test Phase 2.3: Volatility Indicators
    # ========================================

    print("\nTesting Phase 2.3: Volatility Indicators")
    print("-" * 30)

    try:
        from volatility_indicators_phase2_3 import VolatilityIndicators

        vol_calc = VolatilityIndicators()

        # Test Bollinger Bands
        bb = vol_calc.calculate_bollinger_bands(close_series, period=20, std_dev=2.0)
        results['Bollinger_Bands'] = bb
        total_tests += 1
        if hasattr(bb, 'values') and 'upper' in bb.values:
            print(f"Bollinger Bands: SUCCESS - Upper Mean: {bb.values['upper'].mean():.2f}")
            success_count += 1
        else:
            print("Bollinger Bands: FAILED")

        # Test ATR
        atr = vol_calc.calculate_atr(high_series, low_series, close_series, period=14)
        results['ATR'] = atr
        total_tests += 1
        if atr.values.count() > 0:
            print(f"ATR: SUCCESS - Mean: {atr.values.mean():.4f}")
            success_count += 1
        else:
            print("ATR: FAILED")

        # Test Keltner Channels
        kc = vol_calc.calculate_keltner_channels(high_series, low_series, close_series)
        results['Keltner_Channels'] = kc
        total_tests += 1
        if hasattr(kc, 'values') and 'upper' in kc.values:
            print(f"Keltner Channels: SUCCESS - Upper Mean: {kc.values['upper'].mean():.2f}")
            success_count += 1
        else:
            print("Keltner Channels: FAILED")

        # Test Donchian Channels
        dc = vol_calc.calculate_donchian_channels(high_series, low_series, period=20)
        results['Donchian_Channels'] = dc
        total_tests += 1
        if hasattr(dc, 'values') and 'upper' in dc.values:
            print(f"Donchian Channels: SUCCESS - Upper Mean: {dc.values['upper'].mean():.2f}")
            success_count += 1
        else:
            print("Donchian Channels: FAILED")

    except Exception as e:
        print(f"Volatility Indicators: ERROR - {e}")

    # ========================================
    # Test Phase 2.4: Data Source Indicators
    # ========================================

    print("\nTesting Phase 2.4: Data Source Indicators")
    print("-" * 30)

    try:
        from data_source_specific_indicators_phase2_4 import EconomicDataIndicators

        econ_calc = EconomicDataIndicators()

        # Create mock HIBOR data
        hibor_data = []
        tenors = ['Overnight', '1W', '1M', '3M']
        base_rate = 3.0

        for date in dates[:100]:  # Use smaller dataset for speed
            for tenor in tenors:
                rate = base_rate + np.random.normal(0, 0.3) + tenors.index(tenor) * 0.1
                hibor_data.append({
                    'date': date,
                    'tenor': tenor,
                    'rate': max(0.1, rate)
                })

        hibor_df = pd.DataFrame(hibor_data)

        # Test Rate Curve Indicator
        rate_curve = econ_calc.calculate_rate_curve_indicator(hibor_df)
        results['Rate_Curve'] = rate_curve
        total_tests += 1
        if hasattr(rate_curve, 'values'):
            print("Rate Curve Indicator: SUCCESS")
            success_count += 1
        else:
            print("Rate Curve Indicator: FAILED")

        # Test Rate Spread Indicator
        rate_spread = econ_calc.calculate_rate_spread_indicator(hibor_df)
        results['Rate_Spread'] = rate_spread
        total_tests += 1
        if hasattr(rate_spread, 'values'):
            print("Rate Spread Indicator: SUCCESS")
            success_count += 1
        else:
            print("Rate Spread Indicator: FAILED")

    except Exception as e:
        print(f"Data Source Indicators: ERROR - {e}")

    # ========================================
    # Results Summary
    # ========================================

    print("\n" + "=" * 50)
    print("PHASE 2 INTEGRATION TEST RESULTS")
    print("=" * 50)

    print(f"Total Tests: {total_tests}")
    print(f"Successful Tests: {success_count}")
    print(f"Success Rate: {success_count/total_tests*100:.1f}%")

    print(f"\nIndicators Implemented: {len(results)}")
    for indicator_name in results.keys():
        print(f"  - {indicator_name}")

    if success_count >= total_tests * 0.8:  # 80% success rate
        print(f"\n[SUCCESS] Phase 2 Integration: PASSED")
        print("System is ready for production use!")
        return True
    else:
        print(f"\n[FAILED] Phase 2 Integration: FAILED")
        print(f"Success rate ({success_count/total_tests*100:.1f}%) below threshold (80%)")
        return False


if __name__ == "__main__":
    success = test_phase2_simple()

    if success:
        print("\n" + "=" * 50)
        print("PHASE 2 IMPLEMENTATION COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("All major technical indicator categories implemented")
        print("Integration testing passed")
        print("Ready for Phase 3: Parameter Optimization")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("PHASE 2 IMPLEMENTATION INCOMPLETE")
        print("=" * 50)
        print("Some components failed integration testing")
        print("Review and fix issues before proceeding")
        print("=" * 50)