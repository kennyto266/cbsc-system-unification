#!/usr/bin/env python3
"""
Simple test for Cookbook enhanced features
"""

import sys
import os
import pandas as pd
import numpy as np

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'simplified_system', 'src'))

def test_imports():
    """Test importing Cookbook enhanced features"""
    print("Testing Cookbook enhanced features import...")

    try:
        from backtest.enhanced import (
            WalkForwardOptimizer,
            CookbookStrategyBuilder,
            AdvancedPortfolioAnalyzer,
            GPUVectorBTAccelerator
        )
        print("SUCCESS: All enhanced features imported successfully")

        # Test basic initialization
        print("\nTesting basic initialization...")
        strategy_builder = CookbookStrategyBuilder()
        portfolio_analyzer = AdvancedPortfolioAnalyzer()
        gpu_accelerator = GPUVectorBTAccelerator()

        print("SUCCESS: Basic components initialized")

        # Test available strategies
        strategies = strategy_builder.get_available_strategies()
        print(f"Available strategies: {strategies}")

        return True

    except ImportError as e:
        print(f"FAILED: Import error - {e}")
        return False
    except Exception as e:
        print(f"FAILED: Unexpected error - {e}")
        return False

def test_basic_strategy():
    """Test basic strategy execution"""
    print("\nTesting basic strategy execution...")

    try:
        from backtest.enhanced.cookbook_strategies.ma_crossover_strategy import ma_crossover_strategy
        import vectorbt as vbt

        # Generate sample data
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        price = 100 + np.cumsum(np.random.randn(len(dates)) * 0.01)
        price_data = pd.Series(price, index=dates)

        print(f"Generated {len(price_data)} days of test data")

        # Test MA crossover strategy
        portfolio = ma_crossover_strategy(price_data, fast_window=10, slow_window=30)

        print(f"MA Strategy Results:")
        print(f"  Total Return: {portfolio.total_return():.2%}")
        print(f"  Sharpe Ratio: {portfolio.sharpe_ratio():.3f}")
        print(f"  Max Drawdown: {portfolio.max_drawdown():.2%}")

        print("SUCCESS: Basic strategy test completed")
        return True

    except Exception as e:
        print(f"FAILED: Strategy test error - {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("Cookbook Enhanced Features - Simple Test")
    print("=" * 60)

    # Test imports
    import_success = test_imports()

    if import_success:
        # Test basic strategy
        strategy_success = test_basic_strategy()

        if strategy_success:
            print("\n" + "=" * 60)
            print("ALL TESTS PASSED! Cookbook integration is working correctly.")
            print("=" * 60)
        else:
            print("\nStrategy tests failed")
    else:
        print("\nImport tests failed")

if __name__ == '__main__':
    main()