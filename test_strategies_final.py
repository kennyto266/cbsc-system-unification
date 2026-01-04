"""
Final Strategy Factory Test
最終策略工廠測試
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_import():
    """Test basic import functionality"""
    try:
        from strategies.factory import StrategyFactory
        print("Successfully imported StrategyFactory")

        # Initialize strategies
        StrategyFactory.initialize_default_strategies()
        print("Successfully initialized default strategies")

        # Get available strategies
        strategies = StrategyFactory.get_available_strategies()
        print(f"Available strategies: {len(strategies)} strategies registered")

        return True

    except Exception as e:
        print(f"Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy_creation():
    """Test strategy creation"""
    try:
        import pandas as pd
        import numpy as np
        from datetime import datetime
        from strategies.factory import StrategyFactory

        # Create test data
        dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
        np.random.seed(42)
        price = 100 + np.cumsum(np.random.randn(50) * 0.5)

        test_data = pd.DataFrame({
            'open': price,
            'high': price * (1 + np.abs(np.random.randn(50) * 0.01)),
            'low': price * (1 - np.abs(np.random.randn(50) * 0.01)),
            'close': price,
            'volume': np.random.randint(1000, 10000, 50)
        }, index=dates)

        # Test MA Crossover
        ma_config = {
            "strategy_type": "ma_crossover",
            "parameters": {
                "fast_period": 10,
                "slow_period": 20,
                "symbol": "TEST",
                "quantity": 1.0
            }
        }

        ma_strategy = StrategyFactory.create_strategy(ma_config)
        signals = ma_strategy.generate_signals(test_data)
        print(f"MA Crossover: Created strategy, generated {len(signals)} signals")

        # Test RSI
        rsi_config = {
            "strategy_type": "rsi",
            "parameters": {
                "period": 14,
                "symbol": "TEST"
            }
        }

        rsi_strategy = StrategyFactory.create_strategy(rsi_config)
        signals = rsi_strategy.generate_signals(test_data)
        print(f"RSI: Created strategy, generated {len(signals)} signals")

        # Test ADX
        adx_config = {
            "strategy_type": "adx",
            "parameters": {
                "period": 14,
                "symbol": "TEST"
            }
        }

        adx_strategy = StrategyFactory.create_strategy(adx_config)
        signals = adx_strategy.generate_signals(test_data)
        print(f"ADX: Created strategy, generated {len(signals)} signals")

        return True

    except Exception as e:
        print(f"Strategy creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Strategy Factory Final Test")
    print("=" * 40)

    success1 = test_basic_import()
    print()
    success2 = test_strategy_creation()

    print("\n" + "=" * 40)
    if success1 and success2:
        print("All tests completed successfully!")
        sys.exit(0)
    else:
        print("Some tests failed!")
        sys.exit(1)