#!/usr/bin/env python3
"""
Simple Test for Personal Trading System
简单的个人交易系统测试
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
        print("+ VectorBT Engine imported successfully")
    except Exception as e:
        print(f"- VectorBT Engine import failed: {e}")
        return False

    try:
        from hkma_data_adapter import HKMADataAdapter
        print("+ HKMA Adapter imported successfully")
    except Exception as e:
        print(f"- HKMA Adapter import failed: {e}")
        return False

    try:
        from strategy_templates import StrategyFactory
        print("+ Strategy Templates imported successfully")
    except Exception as e:
        print(f"- Strategy Templates import failed: {e}")
        return False

    try:
        from config import get_config
        print("+ Config imported successfully")
    except Exception as e:
        print(f"- Config import failed: {e}")
        return False

    return True

def test_strategies():
    """测试策略"""
    print("\nTesting strategies...")

    try:
        from strategy_templates import StrategyFactory

        # List available strategies
        strategies = StrategyFactory.get_available_strategies()
        print(f"+ Available strategies: {strategies}")

        # Test RSI strategy creation
        rsi_strategy = StrategyFactory.create_strategy('RSI')
        default_params = rsi_strategy.get_default_params()
        param_grid = rsi_strategy.get_param_grid()

        print(f"+ RSI Strategy created successfully")
        print(f"  Default params: {default_params}")
        print(f"  Param grid: {param_grid}")

        return True

    except Exception as e:
        print(f"- Strategy test failed: {e}")
        return False

def test_engine():
    """测试引擎"""
    print("\nTesting VectorBT Engine...")

    try:
        from vectorbt_engine import PersonalVectorBTEngine
        from datetime import date, timedelta

        engine = PersonalVectorBTEngine()
        print("+ PersonalVectorBTEngine created successfully")

        # Test data loading with mock data
        symbol = "0700.HK"
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        data = engine.load_data(symbol, start_date, end_date)
        print(f"+ Data loaded successfully: {len(data)} records")
        print(f"  Columns: {list(data.columns)}")

        return True

    except Exception as e:
        print(f"- Engine test failed: {e}")
        return False

def test_backtest():
    """测试回测"""
    print("\nTesting backtest...")

    try:
        from vectorbt_engine import PersonalVectorBTEngine
        from strategy_templates import get_strategy_function
        from datetime import date, timedelta

        engine = PersonalVectorBTEngine()
        strategy_func = get_strategy_function('RSI')

        symbol = "0700.HK"
        start_date = date.today() - timedelta(days=60)  # 2 months
        end_date = date.today()

        result = engine.backtest_strategy(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            strategy_func=strategy_func,
            strategy_name='RSI',
            parameters={'period': 14, 'oversold': 30, 'overbought': 70}
        )

        print(f"+ Backtest completed successfully")
        print(f"  Symbol: {result.symbol}")
        print(f"  Strategy: {result.strategy_name}")
        print(f"  Total Return: {result.total_return:.2%}")
        print(f"  Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"  Total Trades: {result.total_trades}")

        return True

    except Exception as e:
        print(f"- Backtest test failed: {e}")
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
        ("Backtest Test", test_backtest)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")

        try:
            if test_func():
                print(f"+ {test_name} PASSED")
                passed += 1
            else:
                print(f"- {test_name} FAILED")
        except Exception as e:
            print(f"- {test_name} ERROR: {e}")

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS! All tests passed. System is ready to use.")
        print("\nExample commands:")
        print("python main.py backtest --strategy RSI --symbol 0700.HK --start-date 6m")
        print("python main.py optimize --strategy RSI --symbol 0700.HK --start-date 6m")
        print("python main.py list-strategies")
        print("python main.py compare --symbols \"0700.HK,0941.HK\" --strategies \"RSI,MACD\"")
    else:
        print("WARNING: Some tests failed. Please check the errors above.")

    print("=" * 50)

if __name__ == "__main__":
    main()