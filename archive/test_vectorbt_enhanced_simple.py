#!/usr/bin/env python3
"""
Simple test for Enhanced VectorBT Engine
"""

import pandas as pd
import numpy as np
import sys
import os

# Add the path to our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'simplified_system', 'src'))

try:
    from backtest.enhanced_vectorbt_engine import EnhancedVectorBTEngine, EnhancedBacktestConfig
    print("Successfully imported enhanced engine")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def create_sample_data():
    """Create sample price data"""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    n_days = len(dates)

    # Simulate price data
    initial_price = 450.0
    returns = np.random.normal(0.0008, 0.02, n_days)
    trend = np.linspace(0, 0.3, n_days)  # 30% trend
    returns = returns + trend / n_days

    prices = initial_price * np.exp(np.cumsum(returns))

    # Generate OHLC
    high = prices * (1 + np.abs(np.random.normal(0, 0.01, n_days)))
    low = prices * (1 - np.abs(np.random.normal(0, 0.01, n_days)))
    open_price = prices + np.random.normal(0, prices * 0.005, n_days)
    volume = np.random.randint(1000000, 5000000, n_days)

    high = np.maximum(high, np.maximum(open_price, prices))
    low = np.minimum(low, np.minimum(open_price, prices))

    return pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': prices,
        'volume': volume
    }, index=dates)

def test_basic_functionality():
    """Test basic enhanced engine functionality"""
    print("=" * 60)
    print("Testing Enhanced VectorBT Engine")
    print("=" * 60)

    # Create sample data
    data = create_sample_data()
    print(f"Sample data: {len(data)} days, price range: {data['close'].min():.2f} - {data['close'].max():.2f}")

    # Create enhanced engine
    config = EnhancedBacktestConfig(
        initial_cash=100000,
        fees=0.001
    )

    try:
        engine = EnhancedVectorBTEngine(config)
        print("Enhanced VectorBT Engine created successfully")

        # Test strategy registry
        strategies = engine.get_performance_summary()['available_strategies']
        print(f"Available strategies: {len(strategies)}")
        print(f"Strategies: {strategies[:10]}...")  # Show first 10

        # Test a basic strategy
        result = engine.backtest_strategy(
            data=data,
            strategy='RSI_MEAN_REVERSION',
            parameters={'period': 14, 'oversold': 30, 'overbought': 70},
            symbol='TEST'
        )

        print(f"\nRSI Strategy Results:")
        print(f"  Total Return: {result.total_return:.2%}")
        print(f"  Annual Return: {result.annual_return:.2%}")
        print(f"  Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"  Max Drawdown: {result.max_drawdown:.2%}")
        print(f"  Total Trades: {result.total_trades}")
        print(f"  Execution Time: {result.execution_time:.3f}s")

        # Test performance summary
        summary = engine.get_performance_summary()
        print(f"\nEngine Summary:")
        print(f"  Total Backtests: {summary['engine_statistics']['total_backtests']}")
        print(f"  Average Execution Time: {summary['engine_statistics']['average_execution_time']:.3f}s")

        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    success = test_basic_functionality()

    if success:
        print("\n" + "=" * 60)
        print("SUCCESS: Enhanced VectorBT Engine test completed!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("FAILED: Enhanced VectorBT Engine test failed!")
        print("=" * 60)

if __name__ == "__main__":
    main()