"""
Simple Strategy Factory Test
簡單策略工廠測試
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_test_data(days=100):
    """Create test market data"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

    # Generate synthetic price data
    np.random.seed(42)
    price = 100 + np.cumsum(np.random.randn(days) * 0.5)

    # Create OHLCV data
    data = pd.DataFrame({
        'open': price,
        'high': price * (1 + np.abs(np.random.randn(days) * 0.01)),
        'low': price * (1 - np.abs(np.random.randn(days) * 0.01)),
        'close': price,
        'volume': np.random.randint(1000, 10000, days)
    }, index=dates)

    return data

def test_strategy_factory():
    """Test strategy factory functionality"""
    print("Strategy Factory Simple Test")
    print("=" * 40)

    try:
        # Import modules
        from strategies.factory import StrategyFactory
        from strategies.base import BaseSignal

        print("[OK] Successfully imported strategy modules")

        # Initialize strategies
        StrategyFactory.initialize_default_strategies()
        print("[OK] Successfully initialized default strategies")

        # Get available strategies
        strategies = StrategyFactory.get_available_strategies()
        print(f"✓ Available strategies: {len(strategies)} strategies registered")

        # Show registered strategies
        for code, name in list(strategies.items())[:10]:  # Show first 10
            print(f"  - {code}: {name}")

        # Test creating a strategy
        test_data = create_test_data(50)

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
        print(f"✓ MA Crossover: Created strategy, generated {len(signals)} signals")

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
        print(f"✓ RSI: Created strategy, generated {len(signals)} signals")

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
        print(f"✓ ADX: Created strategy, generated {len(signals)} signals")

        # Test OBV
        obv_config = {
            "strategy_type": "obv",
            "parameters": {
                "ma_period": 10,
                "symbol": "TEST"
            }
        }

        obv_strategy = StrategyFactory.create_strategy(obv_config)
        signals = obv_strategy.generate_signals(test_data)
        print(f"✓ OBV: Created strategy, generated {len(signals)} signals")

        print("\n" + "=" * 40)
        print("All tests completed successfully!")
        print(f"Total strategies registered: {len(strategies)}")

        return True

    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_strategy_factory()
    sys.exit(0 if success else 1)