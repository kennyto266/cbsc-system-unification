#!/usr/bin/env python3
"""
Test Personal Trading System
测试个人交易系统
"""

import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试导入"""
    print("Testing imports...")

    try:
        from vectorbt_engine import PersonalVectorBTEngine
        print("✓ VectorBT Engine imported successfully")
    except Exception as e:
        print(f"✗ VectorBT Engine import failed: {e}")
        return False

    try:
        from hkma_data_adapter import HKMADataAdapter
        print("✓ HKMA Adapter imported successfully")
    except Exception as e:
        print(f"✗ HKMA Adapter import failed: {e}")
        return False

    try:
        from strategy_templates import StrategyFactory
        print("✓ Strategy Templates imported successfully")
    except Exception as e:
        print(f"✗ Strategy Templates import failed: {e}")
        return False

    try:
        from config import get_config
        print("✓ Config imported successfully")
    except Exception as e:
        print(f"✗ Config import failed: {e}")
        return False

    return True

def test_strategies():
    """测试策略"""
    print("\nTesting strategies...")

    try:
        from strategy_templates import StrategyFactory

        # List available strategies
        strategies = StrategyFactory.get_available_strategies()
        print(f"✓ Available strategies: {strategies}")

        # Test RSI strategy creation
        rsi_strategy = StrategyFactory.create_strategy('RSI')
        default_params = rsi_strategy.get_default_params()
        param_grid = rsi_strategy.get_param_grid()

        print(f"✓ RSI Strategy created successfully")
        print(f"  Default params: {default_params}")
        print(f"  Param grid: {param_grid}")

        return True

    except Exception as e:
        print(f"✗ Strategy test failed: {e}")
        return False

def test_engine():
    """测试引擎"""
    print("\nTesting VectorBT Engine...")

    try:
        from vectorbt_engine import PersonalVectorBTEngine
        from datetime import date, timedelta

        engine = PersonalVectorBTEngine()
        print("✓ PersonalVectorBTEngine created successfully")

        # Test data loading with mock data
        symbol = "0700.HK"
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        data = engine.load_data(symbol, start_date, end_date)
        print(f"✓ Data loaded successfully: {len(data)} records")
        print(f"  Columns: {list(data.columns)}")

        return True

    except Exception as e:
        print(f"✗ Engine test failed: {e}")
        return False

def test_hkma_adapter():
    """测试HKMA适配器"""
    print("\nTesting HKMA Data Adapter...")

    try:
        from hkma_data_adapter import HKMADataAdapter
        from datetime import datetime, timedelta

        adapter = HKMADataAdapter()
        print("✓ HKMADataAdapter created successfully")

        # Test mock data generation
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        hibor_data = adapter.get_hibor_data(start_date, end_date)
        print(f"✓ HIBOR data generated: {len(hibor_data)} records")

        return True

    except Exception as e:
        print(f"✗ HKMA Adapter test failed: {e}")
        return False

def test_config():
    """测试配置"""
    print("\nTesting Configuration...")

    try:
        from config import get_config

        config = get_config()
        print("✓ Configuration loaded successfully")

        config_summary = config.get_config_summary()
        print(f"✓ Config summary: {config_summary}")

        default_symbols = config.get_default_symbols()
        print(f"✓ Default symbols: {len(default_symbols)} symbols")

        return True

    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("Personal Trading System Test Suite")
    print("=" * 50)

    tests = [
        ("Import Test", test_imports),
        ("Strategy Test", test_strategies),
        ("Engine Test", test_engine),
        ("HKMA Adapter Test", test_hkma_adapter),
        ("Config Test", test_config)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")

        try:
            if test_func():
                print(f"✓ {test_name} PASSED")
                passed += 1
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}")

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        print("\nQuick start commands:")
        print("python main.py backtest --strategy RSI --symbol 0700.HK --start-date 6m")
        print("python main.py optimize --strategy RSI --symbol 0700.HK --start-date 6m")
        print("python main.py list-strategies")
    else:
        print("❌ Some tests failed. Please check the errors above.")

    print("=" * 50)

if __name__ == "__main__":
    main()