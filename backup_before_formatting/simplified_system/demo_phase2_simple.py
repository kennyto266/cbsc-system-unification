#!/usr/bin/env python3
"""
Phase 2 Extended Indicators Simple Demo
Phase 2擴展指標系統簡化演示
"""

import sys
import numpy as np
import pandas as pd
import time

# Add src to path
sys.path.append('src')

from indicators.phase2_extended_indicators import Phase2ExtendedIndicators

def generate_test_data():
    """生成測試數據"""
    np.random.seed(42)
    n_points = 252

    # 股價數據
    initial_price = 100
    returns = np.random.normal(0.001, 0.02, n_points)
    price_data = initial_price * np.exp(np.cumsum(returns))

    # HIBOR數據
    hibor_data = {
        'ON': np.clip(np.random.normal(3.5, 0.3, n_points), 2.0, 5.0),
        '1M': np.clip(np.random.normal(4.5, 0.5, n_points), 3.0, 7.0)
    }

    dates = pd.date_range('2024-01-01', periods=n_points, freq='D')

    price_series = pd.Series(price_data, index=dates, name='price')
    hibor_df = pd.DataFrame(hibor_data, index=dates)

    return price_series, hibor_df

def main():
    """主演示函數"""
    print("Phase 2 Extended Technical Indicators System Demo")
    print("=" * 60)

    # 創建指標系統
    indicators = Phase2ExtendedIndicators()
    print(f"System initialized with {len(indicators.indicator_metadata)} indicators")

    # 生成測試數據
    print("\nGenerating test data...")
    price_data, hibor_data = generate_test_data()
    print(f"Price data: {len(price_data)} points")
    print(f"HIBOR data: {len(hibor_data)} points, {len(hibor_data.columns)} tenors")

    # 演示趨勢指標
    print("\n" + "="*50)
    print("Trend Extension Indicators Demo")
    print("="*50)

    # DEMA
    print("\n1. DEMA (Double Exponential Moving Average)")
    dema, dema_info = indicators.calculate_dema(price_data)
    print(f"   Calculation time: {dema_info['calculation_time_ms']:.3f}ms")
    print(f"   Data type: {dema_info['data_type']}")
    print(f"   Latest DEMA: {dema.iloc[-1]:.2f}")
    print(f"   Latest Price: {price_data.iloc[-1]:.2f}")
    print(f"   Signal: {'Bullish' if price_data.iloc[-1] > dema.iloc[-1] else 'Bearish'}")

    # TEMA
    print("\n2. TEMA (Triple Exponential Moving Average)")
    tema, tema_info = indicators.calculate_tema(price_data)
    print(f"   Calculation time: {tema_info['calculation_time_ms']:.3f}ms")
    print(f"   Latest TEMA: {tema.iloc[-1]:.2f}")
    print(f"   Trend strength: {'Strong' if abs(price_data.iloc[-1] - tema.iloc[-1]) > 5 else 'Weak'}")

    # 演示動量指標
    print("\n" + "="*50)
    print("Momentum Extension Indicators Demo")
    print("="*50)

    # RSI Extended
    print("\n1. RSI Extended (with smart period selection)")
    rsi, rsi_info = indicators.calculate_rsi_extended(price_data)
    print(f"   Calculation time: {rsi_info['calculation_time_ms']:.3f}ms")
    print(f"   Optimized period: {rsi_info['optimal_period']}")
    print(f"   Latest RSI: {rsi.iloc[-1]:.2f}")

    latest_rsi = rsi.iloc[-1]
    if latest_rsi > 70:
        print("   Signal: Overbought WARNING")
    elif latest_rsi < 30:
        print("   Signal: Oversold OPPORTUNITY")
    else:
        print("   Signal: Neutral zone")

    # Williams %R
    print("\n2. Williams %R")
    williams_r, williams_info = indicators.calculate_williams_r(price_data)
    print(f"   Calculation time: {williams_info['calculation_time_ms']:.3f}ms")
    print(f"   Latest Williams %R: {williams_r.iloc[-1]:.2f}")

    latest_wr = williams_r.iloc[-1]
    if latest_wr < -80:
        print("   Signal: Oversold (Williams %R < -80)")
    elif latest_wr > -20:
        print("   Signal: Overbought (Williams %R > -20)")

    # 演示波動率指標
    print("\n" + "="*50)
    print("Volatility Indicators Demo")
    print("="*50)

    # Bollinger Bands
    print("\n1. Bollinger Bands")
    bb_result = indicators.calculate_bollinger_bands(price_data)
    print(f"   Calculation time: {bb_result['adaptation_info']['calculation_time_ms']:.3f}ms")

    latest_price = price_data.iloc[-1]
    latest_upper = bb_result['upper'].iloc[-1]
    latest_lower = bb_result['lower'].iloc[-1]
    latest_percent_b = bb_result['percent_b'].iloc[-1]

    print(f"   Latest Price: {latest_price:.2f}")
    print(f"   Upper Band: {latest_upper:.2f}")
    print(f"   Lower Band: {latest_lower:.2f}")
    print(f"   %B Position: {latest_percent_b:.2f}")

    if latest_percent_b > 1.0:
        print("   Signal: Price above upper band (potential overbought)")
    elif latest_percent_b < 0.0:
        print("   Signal: Price below lower band (potential oversold)")
    else:
        print("   Signal: Price within bands")

    # 演示數據源特定指標
    print("\n" + "="*50)
    print("Data Source Specific Indicators Demo")
    print("="*50)

    # HIBOR Term Structure
    print("\n1. HIBOR Term Structure Analysis")
    hibor_result = indicators.calculate_hibor_term_structure(
        hibor_data, short_term='ON', long_term='1M'
    )

    if 'term_spread' in hibor_result:
        spread = hibor_result['term_spread']
        zscore = hibor_result['spread_zscore']
        signal = hibor_result['structure_signal']

        print(f"   Calculation time: {hibor_result['adaptation_info']['calculation_time_ms']:.3f}ms")
        print(f"   Latest Spread: {spread.iloc[-1]:.3f}%")
        print(f"   Z-Score: {zscore.iloc[-1]:.2f}")
        print(f"   Signal: {signal.iloc[-1]:.0f} ({'Bullish' if signal.iloc[-1] > 0 else 'Bearish' if signal.iloc[-1] < 0 else 'Neutral'})")

    # Rate Spread Analysis
    print("\n2. Rate Spread Analysis")
    spread_result = indicators.calculate_rate_spread_analysis(
        hibor_data['ON'], hibor_data['1M']
    )

    print(f"   Calculation time: {spread_result['adaptation_info']['calculation_time_ms']:.3f}ms")
    print(f"   Latest Spread: {spread_result['spread'].iloc[-1]:.3f}%")
    print(f"   Signal Strength: {spread_result['signal_strength'].iloc[-1]:.2f}")

    latest_percentile = spread_result['spread_percentile'].iloc[-1]
    if latest_percentile > 80:
        print(f"   Assessment: High spread (percentile: {latest_percentile:.1f}%)")
    elif latest_percentile < 20:
        print(f"   Assessment: Low spread (percentile: {latest_percentile:.1f}%)")
    else:
        print(f"   Assessment: Normal spread (percentile: {latest_percentile:.1f}%)")

    # 綜合信號分析
    print("\n" + "="*50)
    print("Comprehensive Signal Analysis")
    print("="*50)

    signals = []

    # 趨勢信號
    if price_data.iloc[-1] > dema.iloc[-1]:
        signals.append("Trend: Bullish (above DEMA)")
    else:
        signals.append("Trend: Bearish (below DEMA)")

    # 動量信號
    if latest_rsi < 30:
        signals.append("Momentum: Oversold (RSI < 30)")
    elif latest_rsi > 70:
        signals.append("Momentum: Overbought (RSI > 70)")
    else:
        signals.append("Momentum: Neutral (RSI in normal range)")

    # 波動率信號
    if latest_percent_b < 0.2:
        signals.append("Volatility: Oversold (near lower BB)")
    elif latest_percent_b > 0.8:
        signals.append("Volatility: Overbought (near upper BB)")
    else:
        signals.append("Volatility: Neutral (within BB)")

    # 宏觀信號
    if 'structure_signal' in hibor_result:
        latest_hibor_signal = hibor_result['structure_signal'].iloc[-1]
        if latest_hibor_signal > 0:
            signals.append("Macro: Bullish HIBOR term structure")
        elif latest_hibor_signal < 0:
            signals.append("Macro: Bearish HIBOR term structure")
        else:
            signals.append("Macro: Neutral HIBOR term structure")

    print("\nSignal Summary:")
    for signal in signals:
        print(f"   - {signal}")

    # 統計信號
    bullish_signals = sum(1 for s in signals if "Bullish" in s or "Oversold" in s)
    bearish_signals = sum(1 for s in signals if "Bearish" in s or "Overbought" in s)
    neutral_signals = sum(1 for s in signals if "Neutral" in s)

    print(f"\nSignal Count:")
    print(f"   Bullish/Oversold: {bullish_signals}")
    print(f"   Bearish/Overbought: {bearish_signals}")
    print(f"   Neutral: {neutral_signals}")

    # 最終建議
    if bullish_signals > bearish_signals and bullish_signals > neutral_signals:
        final_recommendation = "STRONG BUY"
    elif bearish_signals > bullish_signals and bearish_signals > neutral_signals:
        final_recommendation = "STRONG SELL"
    else:
        final_recommendation = "HOLD/WATCH"

    print(f"\nFinal Recommendation: {final_recommendation}")

    # 性能總結
    print("\n" + "="*50)
    print("Performance Summary")
    print("="*50)

    # 測試所有指標性能
    test_start = time.time()

    all_indicators = [
        ('DEMA', lambda: indicators.calculate_dema(price_data)),
        ('TEMA', lambda: indicators.calculate_tema(price_data)),
        ('RSI_EXTENDED', lambda: indicators.calculate_rsi_extended(price_data)),
        ('BOLLINGER_BANDS', lambda: indicators.calculate_bollinger_bands(price_data)),
        ('WILLIAMS_R', lambda: indicators.calculate_williams_r(price_data)),
    ]

    total_times = []
    for name, func in all_indicators:
        start = time.time()
        result = func()
        calc_time = (time.time() - start) * 1000

        if isinstance(result, tuple):
            calc_time = result[1].get('calculation_time_ms', calc_time)
        elif isinstance(result, dict) and 'adaptation_info' in result:
            calc_time = result['adaptation_info'].get('calculation_time_ms', calc_time)

        total_times.append(calc_time)
        print(f"{name:20s}: {calc_time:7.3f}ms")

    test_time = time.time() - test_start
    avg_time = np.mean(total_times)
    max_time = np.max(total_times)

    print("-" * 30)
    print(f"Total test time: {test_time:.3f}s")
    print(f"Average time: {avg_time:.3f}ms")
    print(f"Max time: {max_time:.3f}ms")
    print(f"Performance target (<1ms): {'PASS' if avg_time < 1.0 else 'NEEDS OPTIMIZATION'}")

    print(f"\nPhase 2 Extended Indicators System Demo Complete!")
    print(f"System Status: OPERATIONAL")

if __name__ == "__main__":
    main()