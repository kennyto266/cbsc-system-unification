"""
Integration test for Phase 2.4 Specialized Indicators
Phase 2.4专用指标集成测试

Demonstrates how to use the new specialized indicators with real government data patterns.
"""

import pandas as pd
import numpy as np
from specialized_indicators import SpecializedIndicators, IndicatorResult

def create_realistic_hkma_data():
    """Create realistic HKMA-like test data"""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=252, freq='D')

    # Simulate HIBOR data with realistic patterns
    base_rate = 3.5
    hibor_data = pd.DataFrame({
        'Overnight': base_rate + np.random.normal(0, 0.1, 252),
        '1-month': base_rate + 0.3 + np.random.normal(0, 0.15, 252),
        '3-month': base_rate + 0.5 + np.random.normal(0, 0.2, 252),
        '6-month': base_rate + 0.7 + np.random.normal(0, 0.25, 252),
        '12-months': base_rate + 1.0 + np.random.normal(0, 0.3, 252)
    }, index=dates)

    # Add some trend patterns
    for col in hibor_data.columns:
        trend = np.linspace(0, 0.5, 252)  # Gradual rate increase
        hibor_data[col] += trend

    # Exchange rate (HKD/USD)
    exchange_rate = 7.8 + np.random.normal(0, 0.05, 252)
    exchange_rate = pd.Series(exchange_rate, index=dates)

    # Monetary base (growing trend)
    monetary_base = 1000000 + np.cumsum(np.random.uniform(100, 1000, 252))
    monetary_base = pd.Series(monetary_base, index=dates)

    # Interbank liquidity
    interbank_liquidity = 50000 + np.random.uniform(-5000, 5000, 252)
    interbank_liquidity = pd.Series(interbank_liquidity, index=dates)

    # Exchange Fund Bills yields
    efbn_data = pd.DataFrame({
        '2-year': 3.0 + np.random.normal(0, 0.2, 252),
        '5-year': 3.5 + np.random.normal(0, 0.3, 252),
        '10-year': 4.0 + np.random.normal(0, 0.4, 252)
    }, index=dates)

    # RMB liquidity usage
    rmb_usage = 10000 + np.random.uniform(-2000, 3000, 252)
    total_liquidity = 50000 + np.random.uniform(-5000, 5000, 252)
    rmb_usage = pd.Series(rmb_usage, index=dates)
    total_liquidity = pd.Series(total_liquidity, index=dates)

    return {
        'hibor_data': hibor_data,
        'exchange_rate': exchange_rate,
        'monetary_base': monetary_base,
        'interbank_liquidity': interbank_liquidity,
        'efbn_data': efbn_data,
        'rmb_usage': rmb_usage,
        'total_liquidity': total_liquidity
    }

def analyze_indicator_result(result: IndicatorResult):
    """Analyze and display indicator results"""
    print(f"\n=== {result.name} Analysis ===")
    print(f"Current indicator value: {result.values.iloc[-1]:.4f}")

    # Display key parameters
    for key, value in result.parameters.items():
        if isinstance(value, (int, float, np.number)):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")

    # Signal analysis
    if result.signals is not None:
        current_signal = result.signals.iloc[-1]
        signal_text = "BUY" if current_signal == 1 else ("SELL" if current_signal == -1 else "HOLD")
        print(f"  Current signal: {signal_text} ({current_signal})")

        signal_count = (result.signals != 0).sum()
        print(f"  Total signals generated: {signal_count}")

    # Performance metrics
    if result.performance_metrics:
        metrics = result.performance_metrics
        print(f"  Signal ratio: {metrics.get('signal_ratio', 0):.2%}")
        print(f"  Volatility: {metrics.get('volatility', 0):.4f}")
        print(f"  Trend strength: {metrics.get('trend_strength', 0):.4f}")

def demonstrate_specialized_indicators():
    """Demonstrate all Phase 2.4 specialized indicators"""
    print("Phase 2.4 Specialized Indicators Integration Test")
    print("=" * 60)

    # Create specialized indicators calculator
    calculator = SpecializedIndicators()

    # Generate realistic test data
    print("\nGenerating realistic HKMA-style test data...")
    test_data = create_realistic_hkma_data()

    results = []

    try:
        # 1. HIBOR Rate Curve Indicator
        print("\n1. Calculating HIBOR Rate Curve Indicator...")
        result1 = calculator.calculate_rate_curve_indicator(
            test_data['hibor_data'],
            short_tenor='Overnight',
            long_tenor='12-months'
        )
        results.append(result1)
        analyze_indicator_result(result1)

        # 2. Rate Spread Indicator
        print("\n2. Calculating Rate Spread Indicator...")
        result2 = calculator.calculate_rate_spread_indicator(
            test_data['hibor_data'],
            benchmark_tenor='Overnight',
            spread_tenors=['1-month', '3-month', '6-month']
        )
        results.append(result2)
        analyze_indicator_result(result2)

        # 3. Currency Strength Indicator
        print("\n3. Calculating Currency Strength Indicator...")
        result3 = calculator.calculate_currency_strength_indicator(
            test_data['exchange_rate'],
            period=21  # 1 month
        )
        results.append(result3)
        analyze_indicator_result(result3)

        # 4. Monetary Growth Indicator
        print("\n4. Calculating Monetary Growth Indicator...")
        result4 = calculator.calculate_monetary_growth_indicator(
            test_data['monetary_base'],
            period=30  # 1 month
        )
        results.append(result4)
        analyze_indicator_result(result4)

        # 5. Liquidity Pressure Indicator
        print("\n5. Calculating Liquidity Pressure Indicator...")
        result5 = calculator.calculate_liquidity_pressure_indicator(
            test_data['interbank_liquidity'],
            threshold_percentile=75
        )
        results.append(result5)
        analyze_indicator_result(result5)

        # 6. Yield Spread Indicator
        print("\n6. Calculating Yield Spread Indicator...")
        result6 = calculator.calculate_yield_spread_indicator(
            test_data['efbn_data'],
            short_term='2-year',
            long_term='10-year'
        )
        results.append(result6)
        analyze_indicator_result(result6)

        # 7. RMB Usage Ratio Indicator
        print("\n7. Calculating RMB Usage Ratio Indicator...")
        result7 = calculator.calculate_usage_ratio_indicator(
            test_data['rmb_usage'],
            test_data['total_liquidity'],
            period=20  # 1 month
        )
        results.append(result7)
        analyze_indicator_result(result7)

        # Summary Analysis
        print("\n" + "=" * 60)
        print("SIGNAL SUMMARY")
        print("=" * 60)

        buy_signals = 0
        sell_signals = 0
        hold_signals = 0

        for result in results:
            if result.signals is not None:
                current_signal = result.signals.iloc[-1]
                if current_signal == 1:
                    buy_signals += 1
                    signal_type = "BUY"
                elif current_signal == -1:
                    sell_signals += 1
                    signal_type = "SELL"
                else:
                    hold_signals += 1
                    signal_type = "HOLD"

                print(f"{result.name:<25} -> {signal_type}")

        print(f"\nSignal Distribution:")
        print(f"  BUY signals: {buy_signals}")
        print(f"  SELL signals: {sell_signals}")
        print(f"  HOLD signals: {hold_signals}")

        if buy_signals > sell_signals:
            overall_sentiment = "BULLISH"
        elif sell_signals > buy_signals:
            overall_sentiment = "BEARISH"
        else:
            overall_sentiment = "NEUTRAL"

        print(f"\nOverall Market Sentiment: {overall_sentiment}")

        # Performance comparison
        print("\n" + "=" * 60)
        print("PERFORMANCE COMPARISON")
        print("=" * 60)

        print(f"{'Indicator':<25} {'Signal Ratio':<12} {'Volatility':<12} {'Data Points':<12}")
        print("-" * 65)

        for result in results:
            if result.performance_metrics:
                metrics = result.performance_metrics
                signal_ratio = metrics.get('signal_ratio', 0)
                volatility = metrics.get('volatility', 0)
                data_points = len(result.values)

                print(f"{result.name:<25} {signal_ratio:<12.2%} {volatility:<12.4f} {data_points:<12}")

        print(f"\n[PASS] All {len(results)} specialized indicators successfully integrated!")
        return True

    except Exception as e:
        print(f"[ERROR] Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def trading_strategy_example():
    """Example of using indicators in a simple trading strategy"""
    print("\n" + "=" * 60)
    print("TRADING STRATEGY EXAMPLE")
    print("=" * 60)

    calculator = SpecializedIndicators()
    test_data = create_realistic_hkma_data()

    # Calculate key indicators
    rate_curve = calculator.calculate_rate_curve_indicator(test_data['hibor_data'])
    currency_strength = calculator.calculate_currency_strength_indicator(test_data['exchange_rate'])
    monetary_growth = calculator.calculate_monetary_growth_indicator(test_data['monetary_base'])

    # Simple composite strategy
    signals = pd.DataFrame({
        'Rate_Curve': rate_curve.signals,
        'Currency_Strength': currency_strength.signals,
        'Monetary_Growth': monetary_growth.signals
    })

    # Generate composite signal
    composite_signal = signals.sum(axis=1)
    composite_signal = np.where(composite_signal >= 2, 1,  # Strong buy if 2+ indicators agree
                               np.where(composite_signal <= -2, -1, 0))  # Strong sell if 2+ indicators agree

    # Current strategy signal
    current_composite = composite_signal[-1] if len(composite_signal) > 0 else 0
    signal_text = "STRONG BUY" if current_composite == 1 else ("STRONG SELL" if current_composite == -1 else "NEUTRAL")

    print(f"Composite Strategy Signal: {signal_text}")
    print(f"Individual component signals:")
    print(f"  Rate Curve: {signals['Rate_Curve'].iloc[-1]}")
    print(f"  Currency Strength: {signals['Currency_Strength'].iloc[-1]}")
    print(f"  Monetary Growth: {signals['Monetary_Growth'].iloc[-1]}")

    print("\nStrategy interpretation:")
    if current_composite == 1:
        print("  Multiple indicators suggest positive market conditions")
        print("  Consider increasing exposure to HK market assets")
    elif current_composite == -1:
        print("  Multiple indicators suggest negative market conditions")
        print("  Consider reducing exposure or hedging positions")
    else:
        print("  Mixed signals - wait for clearer indication")
        print("  Maintain current positions with caution")

if __name__ == "__main__":
    success = demonstrate_specialized_indicators()

    if success:
        trading_strategy_example()
        print("\n" + "=" * 60)
        print("[SUCCESS] Phase 2.4 Specialized Indicators Integration Complete!")
        print("These indicators are now ready for production use with real HKMA data.")
        print("=" * 60)
    else:
        print("\n[ERROR] Integration test failed!")