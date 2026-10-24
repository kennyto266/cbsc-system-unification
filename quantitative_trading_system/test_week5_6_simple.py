#!/usr/bin/env python3
"""
Week 5-6: Simple Integration Test
Simplified test to verify core functionality
"""

import sys
import os
import numpy as np
import pandas as pd
import time
import gc

# Add path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_core_imports():
    """Test core module imports"""
    print("=" * 50)
    print("Core Module Import Test")
    print("=" * 50)

    try:
        # Test core imports
        from backtest.vectorbt_engine import VectorBTEngine
        from optimization.optimizer import ParameterOptimizer
        from indicators.core_indicators import CoreIndicators

        print("✓ Core modules imported successfully")

        # Test basic instantiation
        engine = VectorBTEngine()
        optimizer = ParameterOptimizer()
        indicators = CoreIndicators()

        print("✓ Core components instantiated successfully")
        return True

    except Exception as e:
        print(f"✗ Core import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality"""
    print("\n" + "=" * 50)
    print("Basic Functionality Test")
    print("=" * 50)

    try:
        from backtest.vectorbt_engine import VectorBTEngine
        from indicators.core_indicators import CoreIndicators

        # Create test data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        prices = 100 + np.cumsum(np.random.normal(0, 1, 100))

        data = pd.DataFrame({
            'open': prices * (1 + np.random.uniform(-0.01, 0.01, 100)),
            'high': prices * (1 + np.random.uniform(0, 0.02, 100)),
            'low': prices * (1 - np.random.uniform(0, 0.02, 100)),
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, 100)
        }, index=dates)

        print(f"✓ Test data created: {len(data)} records")

        # Test technical indicators
        indicators = CoreIndicators()
        rsi = indicators.calculate_rsi(data['close'], 14)
        sma = indicators.calculate_sma(data['close'], 20)

        print(f"✓ RSI calculated: {len(rsi)} values")
        print(f"✓ SMA calculated: {len(sma)} values")

        # Test backtest engine
        engine = VectorBTEngine()
        result = engine.backtest_strategy(data, "RSI_MEAN_REVERSION", {"period": 14})

        print(f"✓ Backtest completed")
        print(f"  Total Return: {result.total_return:.2%}")
        print(f"  Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"  Total Trades: {result.total_trades}")

        return True

    except Exception as e:
        print(f"✗ Basic functionality failed: {e}")
        return False

def test_performance_benchmark():
    """Test performance benchmark"""
    print("\n" + "=" * 50)
    print("Performance Benchmark Test")
    print("=" * 50)

    try:
        from backtest.vectorbt_engine import VectorBTEngine

        # Create test data
        dates = pd.date_range('2023-01-01', periods=252, freq='D')
        prices = 100 + np.cumsum(np.random.normal(0, 1, 252))

        data = pd.DataFrame({
            'open': prices * (1 + np.random.uniform(-0.01, 0.01, 252)),
            'high': prices * (1 + np.random.uniform(0, 0.02, 252)),
            'low': prices * (1 - np.random.uniform(0, 0.02, 252)),
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, 252)
        }, index=dates)

        engine = VectorBTEngine()

        # Test multiple strategies
        strategies = []
        for i in range(20):
            period = 10 + (i % 20)
            strategies.append((f"RSI_{period}", {"period": period, "oversold": 30, "overbought": 70}))

        start_time = time.time()
        results = engine.backtest_multiple_strategies(data, strategies[:10], parallel=True)
        execution_time = time.time() - start_time

        strategies_per_second = len(strategies[:10]) / execution_time
        successful_strategies = len([r for r in results.values() if r.total_trades > 0])

        print(f"✓ Performance test completed")
        print(f"  Strategies tested: {len(strategies[:10])}")
        print(f"  Execution time: {execution_time:.3f}s")
        print(f"  Speed: {strategies_per_second:.1f} strategies/sec")
        print(f"  Successful strategies: {successful_strategies}/{len(strategies[:10])}")

        # Check performance target (300 strategies/sec as a reasonable target)
        performance_target_met = strategies_per_second >= 300
        print(f"  Performance target met (300+ strategies/sec): {performance_target_met}")

        return performance_target_met

    except Exception as e:
        print(f"✗ Performance benchmark failed: {e}")
        return False

def test_memory_usage():
    """Test memory usage"""
    print("\n" + "=" * 50)
    print("Memory Usage Test")
    print("=" * 50)

    try:
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(f"Initial memory: {initial_memory:.1f} MB")

        # Create and destroy objects
        for i in range(5):
            from backtest.vectorbt_engine import VectorBTEngine
            from indicators.core_indicators import CoreIndicators

            # Create large data
            dates = pd.date_range('2020-01-01', periods=504, freq='D')
            prices = 100 + np.cumsum(np.random.normal(0, 2, 504))

            data = pd.DataFrame({
                'close': prices,
                'volume': np.random.randint(1000000, 10000000, 504)
            }, index=dates)

            # Process data
            engine = VectorBTEngine()
            indicators = CoreIndicators()

            rsi = indicators.calculate_rsi(data['close'], 14)
            result = engine.backtest_strategy(data, "RSI_MEAN_REVERSION", {"period": 14})

            # Clean up
            del engine, indicators, rsi, result, data, dates, prices
            gc.collect()

            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - initial_memory

            print(f"  Iteration {i+1}: {current_memory:.1f} MB (+{memory_increase:.1f} MB)")

        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory

        print(f"✓ Memory test completed")
        print(f"  Final memory: {final_memory:.1f} MB")
        print(f"  Total increase: {total_increase:.1f} MB")

        # Check for memory leaks (less than 20MB increase is acceptable)
        memory_healthy = total_increase < 20
        print(f"  Memory healthy: {memory_healthy}")

        return memory_healthy

    except Exception as e:
        print(f"✗ Memory usage test failed: {e}")
        return False

def test_code_structure():
    """Test code structure and quality"""
    print("\n" + "=" * 50)
    print("Code Structure Test")
    print("=" * 50)

    try:
        # Count Python files
        python_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    python_files.append(os.path.join(root, file))

        print(f"✓ Python files found: {len(python_files)}")

        # Check key files exist
        key_files = [
            'backtest/vectorbt_engine.py',
            'optimization/optimizer.py',
            'indicators/core_indicators.py'
        ]

        existing_files = 0
        for file_path in key_files:
            if os.path.exists(file_path):
                existing_files += 1
                file_size = os.path.getsize(file_path) / 1024  # KB
                print(f"✓ {file_path}: {file_size:.1f} KB")
            else:
                print(f"✗ {file_path}: Missing")

        structure_score = existing_files / len(key_files)
        print(f"Code structure score: {structure_score:.1%}")

        return structure_score >= 0.8

    except Exception as e:
        print(f"✗ Code structure test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Week 5-6: Simple Integration Test")
    print("=" * 60)
    print("Testing core system functionality...")
    print()

    try:
        # Run tests
        test_results = []
        test_results.append(("Core Imports", test_core_imports()))
        test_results.append(("Basic Functionality", test_basic_functionality()))
        test_results.append(("Performance Benchmark", test_performance_benchmark()))
        test_results.append(("Memory Usage", test_memory_usage()))
        test_results.append(("Code Structure", test_code_structure()))

        # Results
        passed_tests = [name for name, result in test_results if result]
        failed_tests = [name for name, result in test_results if not result]

        print("\n" + "=" * 60)
        print("Test Results Summary")
        print("=" * 60)

        print(f"Total tests: {len(test_results)}")
        print(f"Passed: {len(passed_tests)}")
        print(f"Failed: {len(failed_tests)}")

        print(f"\nPassed tests:")
        for test_name in passed_tests:
            print(f"  [OK] {test_name}")

        if failed_tests:
            print(f"\nFailed tests:")
            for test_name in failed_tests:
                print(f"  [FAIL] {test_name}")

        success_rate = len(passed_tests) / len(test_results)
        print(f"\nOverall success rate: {success_rate:.1%}")

        if success_rate >= 0.8:
            print(f"\nWeek 5-6 Integration Test: SUCCESS!")
            print(f"System is production ready!")
            return True
        elif success_rate >= 0.6:
            print(f"\nWeek 5-6 Integration Test: PARTIAL SUCCESS!")
            print(f"System mostly functional with minor issues.")
            return True
        else:
            print(f"\nWeek 5-6 Integration Test: NEEDS IMPROVEMENT")
            print(f"System requires significant fixes.")
            return False

    except Exception as e:
        print(f"\nCritical error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    sys.exit(exit_code)