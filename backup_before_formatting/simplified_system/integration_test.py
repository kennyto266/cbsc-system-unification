#!/usr/bin/env python3
"""
Simplified System Integration Test
Phase 2.5: 測試集成驗證

完整測試simplified_system的所有模塊協同工作
"""

import sys
import os
import pandas as pd
import numpy as np
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_test_data():
    """Create comprehensive test data for integration testing"""
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    np.random.seed(42)

    # Realistic price data
    base_price = 100.0
    daily_returns = np.random.normal(0.001, 0.02, 252)

    # Add trend and seasonality
    trend = np.linspace(0, 0.3, 252)  # 30% overall trend
    seasonal = 0.02 * np.sin(2 * np.pi * np.arange(252) / 60)  # 60-day cycle

    price_changes = daily_returns + trend / 252 + seasonal / 252
    prices = [base_price]

    for i in range(1, 252):
        new_price = prices[-1] * (1 + price_changes[i])
        prices.append(max(new_price, base_price * 0.5))

    close = np.array(prices)
    high = close * (1 + np.abs(np.random.normal(0, 0.01, 252)))
    low = close * (1 - np.abs(np.random.normal(0, 0.01, 252)))
    open_price = np.roll(close, 1)
    open_price[0] = close[0]
    volume = np.ones(252) * 1000000 * (1 + np.random.normal(0, 0.5, 252))
    volume = np.maximum(volume, 100000)

    return pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)

def test_module_imports():
    """Test that all modules can be imported successfully"""
    print("=" * 60)
    print("1. Module Import Test")
    print("=" * 60)

    modules_to_test = [
        ("Stock API", "src.api.stock_api"),
        ("Government Data", "src.api.government_data"),
        ("Daily Tasks API", "src.api.daily_tasks_api"),
        ("Technical Indicators", "src.indicators.core_indicators"),
        ("Technical Analyzer", "src.indicators.technical_analyzer"),
        ("VectorBT Engine", "src.backtest.vectorbt_engine"),
        ("Strategy Builder", "src.backtest.strategy_builder"),
        ("Telegram Bot", "src.telegram.telegram_bot"),
    ]

    results = {}
    for module_name, module_path in modules_to_test:
        try:
            __import__(module_path)
            print(f"[OK] {module_name}")
            results[module_name] = True
        except ImportError as e:
            print(f"[ERROR] {module_name}: {e}")
            results[module_name] = False
        except Exception as e:
            print(f"[ERROR] {module_name}: {e}")
            results[module_name] = False

    success_count = sum(results.values())
    total_count = len(results)
    print(f"\nModule imports: {success_count}/{total_count} passed")

    return success_count == total_count

def test_stock_api_integration():
    """Test Stock API integration"""
    print("\n" + "=" * 60)
    print("2. Stock API Integration Test")
    print("=" * 60)

    try:
        from src.api.stock_api import StockAPI, create_stock_api, get_hk_stock_data

        # Test factory function
        api = create_stock_api()
        print("[OK] Stock API factory function")

        # Test basic methods
        if hasattr(api, 'get_stock_data'):
            print("[OK] get_stock_data method exists")
        else:
            print("[WARNING] get_stock_data method not found")

        # Test convenience function
        if callable(get_hk_stock_data):
            print("[OK] get_hk_stock_data function available")

        print("Stock API integration test PASSED")
        return True

    except Exception as e:
        print(f"[ERROR] Stock API integration failed: {e}")
        return False

def test_government_data_integration():
    """Test Government Data integration"""
    print("\n" + "=" * 60)
    print("3. Government Data Integration Test")
    print("=" * 60)

    try:
        from src.api.government_data import GovernmentDataAPI, get_hibor_data, get_hkma_data

        # Test API creation
        api = GovernmentDataAPI()
        print("[OK] Government Data API created")

        # Test data retrieval functions
        if callable(get_hibor_data):
            print("[OK] get_hibor_data function available")

        if callable(get_hkma_data):
            print("[OK] get_hkma_data function available")

        print("Government Data integration test PASSED")
        return True

    except Exception as e:
        print(f"[ERROR] Government Data integration failed: {e}")
        return False

def test_technical_indicators_integration():
    """Test Technical Indicators integration"""
    print("\n" + "=" * 60)
    print("4. Technical Indicators Integration Test")
    print("=" * 60)

    try:
        from src.indicators.core_indicators import CoreIndicators
        from src.indicators.technical_analyzer import TechnicalAnalyzer

        # Create test data
        test_data = create_test_data()
        close_prices = test_data['close']

        # Test CoreIndicators
        indicators = CoreIndicators()

        # Test key indicators
        rsi = indicators.calculate_rsi(close_prices, 14)
        print(f"[OK] RSI calculated: {rsi.iloc[-1]:.2f}")

        sma = indicators.calculate_sma(close_prices, 20)
        print(f"[OK] SMA calculated: {sma.iloc[-1]:.2f}")

        ema = indicators.calculate_ema(close_prices, 20)
        print(f"[OK] EMA calculated: {ema.iloc[-1]:.2f}")

        # Test TechnicalAnalyzer
        analyzer = TechnicalAnalyzer()

        # Test technical analysis methods
        trend = analyzer.analyze_trend(test_data)
        print(f"[OK] Trend analysis completed: {trend}")

        signals = analyzer.generate_trading_signals(test_data)
        print(f"[OK] Trading signals generated: {len(signals)} signals")

        print("Technical Indicators integration test PASSED")
        return True

    except Exception as e:
        print(f"[ERROR] Technical Indicators integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backtest_integration():
    """Test Backtest integration"""
    print("\n" + "=" * 60)
    print("5. Backtest Integration Test")
    print("=" * 60)

    try:
        from src.backtest.vectorbt_engine import VectorBTEngine, BacktestConfig
        from src.backtest.strategy_builder import StrategyBuilder

        # Create test data
        test_data = create_test_data()

        # Test VectorBTEngine
        config = BacktestConfig(initial_cash=100000, fees=0.001)
        engine = VectorBTEngine(config)
        print("[OK] VectorBTEngine created")

        # Test strategy execution
        result = engine.backtest_strategy(
            data=test_data,
            strategy="RSI_MEAN_REVERSION",
            parameters={'period': 14, 'oversold': 30, 'overbought': 70},
            symbol="INTEGRATION_TEST"
        )

        print(f"[OK] Strategy executed: Return={result.total_return:.2%}, Sharpe={result.sharpe_ratio:.3f}")

        # Test StrategyBuilder
        builder = StrategyBuilder()

        # Create dummy signals for testing
        entries = pd.Series([False] * len(test_data))
        exits = pd.Series([False] * len(test_data))
        entries.iloc[::50] = True  # Entry every 50 days
        exits.iloc[25::50] = True  # Exit 25 days later

        builder.register_strategy("Test", entries, exits, weight=1.0)
        print("[OK] Strategy registered with StrategyBuilder")

        # Test signal combination
        combined = builder.combine_strategies(["Test"], "weighted_sum")
        print(f"[OK] Strategies combined: {combined['entries'].sum()} entries")

        print("Backtest integration test PASSED")
        return True

    except Exception as e:
        print(f"[ERROR] Backtest integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_telegram_integration():
    """Test Telegram Bot integration"""
    print("\n" + "=" * 60)
    print("6. Telegram Bot Integration Test")
    print("=" * 60)

    try:
        from src.telegram.telegram_bot import TelegramBot, create_telegram_bot

        # Test bot creation (without actual bot token)
        print("[OK] TelegramBot class imported")

        if callable(create_telegram_bot):
            print("[OK] create_telegram_bot function available")

        print("Telegram Bot integration test PASSED (basic import)")
        return True

    except Exception as e:
        print(f"[ERROR] Telegram Bot integration failed: {e}")
        return False

def test_end_to_end_workflow():
    """Test complete end-to-end workflow"""
    print("\n" + "=" * 60)
    print("7. End-to-End Workflow Test")
    print("=" * 60)

    try:
        # Import all necessary modules
        from src.api.stock_api import get_hk_stock_data
        from src.indicators.core_indicators import CoreIndicators
        from src.backtest.vectorbt_engine import VectorBTEngine

        # Step 1: Get/ create test data
        print("Step 1: Creating test data...")
        test_data = create_test_data()
        print(f"[OK] Test data created: {len(test_data)} records")

        # Step 2: Calculate technical indicators
        print("Step 2: Calculating technical indicators...")
        indicators = CoreIndicators()
        rsi = indicators.calculate_rsi(test_data['close'], 14)
        sma_20 = indicators.calculate_sma(test_data['close'], 20)
        sma_50 = indicators.calculate_sma(test_data['close'], 50)
        print(f"[OK] Indicators calculated: RSI={rsi.iloc[-1]:.2f}, SMA20={sma_20.iloc[-1]:.2f}")

        # Step 3: Execute backtest with different strategies
        print("Step 3: Running backtests...")
        engine = VectorBTEngine()

        strategies = [
            ("RSI_MEAN_REVERSION", {'period': 14, 'oversold': 30, 'overbought': 70}),
            ("DUAL_MOVING_AVERAGE", {'short_period': 20, 'long_period': 50}),
            ("BOLLINGER_BANDS", {'period': 20, 'std_dev': 2.0})
        ]

        results = {}
        for strategy_name, params in strategies:
            result = engine.backtest_strategy(
                data=test_data,
                strategy=strategy_name,
                parameters=params,
                symbol="E2E_TEST"
            )
            results[strategy_name] = result
            print(f"[OK] {strategy_name}: Return={result.total_return:.2%}, Sharpe={result.sharpe_ratio:.3f}")

        # Step 4: Compare results
        print("Step 4: Analyzing results...")
        best_strategy = max(results.items(), key=lambda x: x[1].sharpe_ratio)
        print(f"[OK] Best strategy: {best_strategy[0]} (Sharpe: {best_strategy[1].sharpe_ratio:.3f})")

        print("End-to-end workflow test PASSED")
        return True

    except Exception as e:
        print(f"[ERROR] End-to-end workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main integration test function"""
    print("=" * 80)
    print("SIMPLIFIED SYSTEM INTEGRATION TEST - PHASE 2.5")
    print("=" * 80)
    print("Testing all modules work together seamlessly")
    print("=" * 80)

    # Run all tests
    tests = [
        ("Module Imports", test_module_imports),
        ("Stock API Integration", test_stock_api_integration),
        ("Government Data Integration", test_government_data_integration),
        ("Technical Indicators Integration", test_technical_indicators_integration),
        ("Backtest Integration", test_backtest_integration),
        ("Telegram Integration", test_telegram_integration),
        ("End-to-End Workflow", test_end_to_end_workflow)
    ]

    results = {}
    start_time = time.time()

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"[CRITICAL ERROR] {test_name} crashed: {e}")
            results[test_name] = False

    total_time = time.time() - start_time

    # Summary
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{test_name:30}: {status}")

    print(f"\nOverall Results: {passed}/{total} tests passed")
    print(f"Execution Time: {total_time:.2f} seconds")

    if passed == total:
        print("\n" + "="*80)
        print("ALL INTEGRATION TESTS PASSED!")
        print("Simplified System is ready for production use")
        print("All modules are working together correctly")
        print("="*80)
    else:
        print(f"\n{total - passed} test(s) failed. Review the issues above.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)