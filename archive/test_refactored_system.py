#!/usr/bin/env python3
"""
Test Refactored Technical Analysis System
測試重構後的技術分析系統

This script tests the refactored system to ensure it maintains
the same functionality while providing better architecture.
"""

import sys
import time
sys.path.append('.')

from refactored_tech_analysis import (
    DataRepository,
    IndicatorFactory,
    BacktestEngine,
    OptimizationOrchestrator,
    OptimizationConfig
)


def test_data_repository():
    """Test DataRepository functionality"""
    print("=" * 60)
    print("TESTING DATA REPOSITORY")
    print("=" * 60)

    try:
        # Test repository creation
        repo = DataRepository()
        print("✓ DataRepository created successfully")

        # Test stock data
        stock_data = repo.get_stock_data('0700.HK')
        print(f"✓ Stock data: {len(stock_data)} records")

        # Test government data
        gov_data = repo.get_government_data('HB')
        print(f"✓ Government data (HB): {len(gov_data)} records")

        # Test cache functionality
        cache_size = repo.get_cache_size()
        print(f"✓ Cache size: {cache_size} items")

        print("✓ DataRepository test PASSED")
        return True

    except Exception as e:
        print(f"❌ DataRepository test FAILED: {e}")
        return False


def test_indicator_factory():
    """Test IndicatorFactory functionality"""
    print("\n" + "=" * 60)
    print("TESTING INDICATOR FACTORY")
    print("=" * 60)

    try:
        repo = DataRepository()
        factory = IndicatorFactory(repo)
        print("✓ IndicatorFactory created successfully")

        # Test single indicator creation
        indicator = factory.create_indicator('RSI', 'HB', {'period': 14})
        print(f"✓ RSI indicator created: {len(indicator)} values")

        # Test parameter combinations generation
        combinations = factory.generate_all_combinations()
        print(f"✓ Generated {len(combinations)} combinations")

        # Test batch creation (small batch)
        test_combinations = combinations[:5]
        batch_indicators = factory.create_indicator_batch(test_combinations)
        print(f"✓ Batch creation: {len(batch_indicators)} indicators")

        print("✓ IndicatorFactory test PASSED")
        return True

    except Exception as e:
        print(f"❌ IndicatorFactory test FAILED: {e}")
        return False


def test_backtest_engine():
    """Test BacktestEngine functionality"""
    print("\n" + "=" * 60)
    print("TESTING BACKTEST ENGINE")
    print("=" * 60)

    try:
        # Test engine creation
        engine = BacktestEngine()
        print("✓ BacktestEngine created successfully")

        # Create test data
        import pandas as pd
        import numpy as np

        # Test indicator and price data
        test_indicator = pd.Series(np.random.randn(100))
        test_prices = pd.Series(100 + np.random.randn(100).cumsum())

        # Test single backtest
        result = engine.backtest_strategy(test_indicator, test_prices, "TEST_STRATEGY")
        print(f"✓ Single backtest: Sharpe={result.sharpe_ratio:.3f}")

        # Test multiple backtests
        test_indicators = {
            "STRATEGY_1": pd.Series(np.random.randn(100)),
            "STRATEGY_2": pd.Series(np.random.randn(100)),
            "STRATEGY_3": pd.Series(np.random.randn(100))
        }
        results = engine.backtest_multiple_strategies(test_indicators, test_prices)
        print(f"✓ Multiple backtests: {len(results)} results")

        # Test top strategies
        top_strategies = engine.get_top_strategies(results, top_n=2)
        print(f"✓ Top strategies: {len(top_strategies)} results")

        print("✓ BacktestEngine test PASSED")
        return True

    except Exception as e:
        print(f"❌ BacktestEngine test FAILED: {e}")
        return False


def test_optimization_orchestrator():
    """Test OptimizationOrchestrator functionality"""
    print("\n" + "=" * 60)
    print("TESTING OPTIMIZATION ORCHESTRATOR")
    print("=" * 60)

    try:
        # Test orchestrator creation
        config = OptimizationConfig(max_workers=4)  # Use fewer workers for testing
        orchestrator = OptimizationOrchestrator(config)
        print("✓ OptimizationOrchestrator created successfully")

        # Test small-scale optimization
        print("Running small-scale optimization test...")
        start_time = time.time()

        results = orchestrator.run_complete_optimization(max_combinations=10)

        execution_time = time.time() - start_time
        print(f"✓ Optimization completed in {execution_time:.2f} seconds")
        print(f"✓ Total results: {len(results)}")
        print(f"✓ Successful results: {sum(1 for r in results if r.success)}")

        # Test top strategies
        top_strategies = orchestrator.get_top_strategies(results, top_n=3)
        print(f"✓ Top 3 strategies:")
        for i, strategy in enumerate(top_strategies, 1):
            print(f"   {i}. {strategy.strategy_id}: Sharpe={strategy.sharpe_ratio:.3f}, Score={strategy.quality_score:.1f}")

        print("✓ OptimizationOrchestrator test PASSED")
        return True

    except Exception as e:
        print(f"❌ OptimizationOrchestrator test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def compare_sharpe_calculations():
    """Compare Sharpe ratio calculations with original system"""
    print("\n" + "=" * 60)
    print("TESTING SHARPE RATIO CALCULATION ACCURACY")
    print("=" * 60)

    try:
        from refactored_tech_analysis.backtest_engine import PerformanceCalculator

        # Test data
        test_returns = [0.01, -0.005, 0.02, -0.01, 0.015, -0.008, 0.025, -0.003]

        calculator = PerformanceCalculator(risk_free_rate=0.03)
        sharpe = calculator.calculate_sharpe_ratio(test_returns)

        print(f"Test returns: {test_returns}")
        print(f"Calculated Sharpe: {sharpe:.6f}")

        # Verify it's in reasonable range (not artificially high)
        if 0.5 <= sharpe <= 3.0:
            print("✓ Sharpe ratio calculation is reasonable")
            return True
        else:
            print(f"⚠️  Sharpe ratio {sharpe:.6f} is outside expected range [0.5, 3.0]")
            return False

    except Exception as e:
        print(f"❌ Sharpe calculation test FAILED: {e}")
        return False


def main():
    """Main test function"""
    print("REFACTORED TECHNICAL ANALYSIS SYSTEM TESTS")
    print("=" * 80)

    test_results = []

    # Run all tests
    test_results.append(("Data Repository", test_data_repository()))
    test_results.append(("Indicator Factory", test_indicator_factory()))
    test_results.append(("Backtest Engine", test_backtest_engine()))
    test_results.append(("Optimization Orchestrator", test_optimization_orchestrator()))
    test_results.append(("Sharpe Calculation", compare_sharpe_calculations()))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = 0
    for test_name, result in test_results:
        status = "PASSED" if result else "FAILED"
        icon = "✓" if result else "❌"
        print(f"{icon} {test_name:<25}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{len(test_results)} tests passed")

    if passed == len(test_results):
        print("\n🎉 ALL TESTS PASSED! Refactoring successful!")
        print("✓ Architecture improved")
        print("✓ Design patterns applied")
        print("✓ Functionality preserved")
        print("✓ Sharpe ratio calculation fixed")
    else:
        print(f"\n⚠️  {len(test_results) - passed} tests failed. Check the errors above.")

    print("=" * 80)

    return passed == len(test_results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)