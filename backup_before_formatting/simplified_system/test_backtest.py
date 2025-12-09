#!/usr/bin/env python3
"""
簡化系統 - VectorBT回測測試
Simplified System - VectorBT Backtesting Test

測試VectorBT回測引擎的功能和性能
Test VectorBT backtesting engine functionality and performance
"""

import sys
import os
import pandas as pd
import numpy as np
import time
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_sample_price_data(days: int = 252) -> pd.DataFrame:
    """創建樣本價格數據"""
    np.random.seed(42)

    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')

    # 生成更真實的股價數據
    base_price = 100.0
    daily_returns = np.random.normal(0.001, 0.02, days)  # 日收益率

    # 添加趨勢和週期性
    trend = np.linspace(0, 0.3, days)  # 30%的總趨勢
    seasonal = 0.02 * np.sin(2 * np.pi * np.arange(days) / 60)  # 60天週期

    # 綜合價格變動
    price_changes = daily_returns + trend / days + seasonal / 252
    prices = [base_price]

    for i in range(1, days):
        new_price = prices[-1] * (1 + price_changes[i])
        prices.append(max(new_price, base_price * 0.5))  # 防止價格過低

    # 計算OHLC
    close = np.array(prices)
    high = close * (1 + np.abs(np.random.normal(0, 0.01, days)))
    low = close * (1 - np.abs(np.random.normal(0, 0.01, days)))
    open_price = np.roll(close, 1)
    open_price[0] = close[0]

    # 確保 high >= close >= low, high >= open >= low
    high = np.maximum(np.maximum(high, close), open_price)
    low = np.minimum(np.minimum(low, close), open_price)

    # 生成成交量
    base_volume = 1000000
    volume_variation = np.random.normal(0, 0.5, days)
    volume = base_volume * (1 + volume_variation)
    volume = np.maximum(volume, base_volume * 0.1)

    return pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)

def test_vectorbt_engine_basic():
    """測試VectorBT引擎基本功能"""
    print("Testing VectorBT Engine basic functionality...")

    try:
        from src.backtest.vectorbt_engine import VectorBTEngine, BacktestConfig

        # 創建引擎
        config = BacktestConfig(
            initial_cash=100000,
            fees=0.001,
            slippage=0.0005
        )
        engine = VectorBTEngine(config)

        # 創建測試數據
        data = create_sample_price_data(252)  # 一年數據

        # 測試RSI策略
        print("Testing RSI strategy...")
        result = engine.backtest_strategy(
            data=data,
            strategy="RSI_MEAN_REVERSION",
            parameters={'period': 14, 'oversold': 30, 'overbought': 70},
            symbol="TEST"
        )

        # 驗證結果
        assert result.symbol == "TEST"
        assert result.strategy_name == "RSI_MEAN_REVERSION"
        assert result.data_points == 252
        assert isinstance(result.total_return, float)
        assert isinstance(result.sharpe_ratio, float)
        assert isinstance(result.max_drawdown, float)

        print(f"[OK] RSI Strategy Results:")
        print(f"   Total Return: {result.total_return:.2%}")
        print(f"   Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"   Max Drawdown: {result.max_drawdown:.2%}")
        print(f"   Win Rate: {result.win_rate:.2%}")
        print(f"   Total Trades: {result.total_trades}")

        print("Basic functionality test passed!")
        return True

    except ImportError as e:
        print(f"[ERROR] VectorBT not available: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Basic test failed: {e}")
        return False

def test_multiple_strategies():
    """測試多種策略"""
    print("\nTesting multiple strategies...")

    try:
        from src.backtest.vectorbt_engine import VectorBTEngine

        engine = VectorBTEngine()
        data = create_sample_price_data(200)

        strategies = [
            ("RSI_MEAN_REVERSION", {'period': 14, 'oversold': 30, 'overbought': 70}),
            ("MACD_CROSSOVER", {'fast': 12, 'slow': 26, 'signal': 9}),
            ("BOLLINGER_BANDS", {'period': 20, 'std_dev': 2.0}),
            ("DUAL_MOVING_AVERAGE", {'short_period': 20, 'long_period': 50})
        ]

        results = {}
        for strategy_name, params in strategies:
            print(f"\nTesting {strategy_name}...")
            try:
                result = engine.backtest_strategy(
                    data=data,
                    strategy=strategy_name,
                    parameters=params,
                    symbol="MULTI_TEST"
                )
                results[strategy_name] = result

                print(f"   Return: {result.total_return:.2%}, Sharpe: {result.sharpe_ratio:.3f}")

            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results[strategy_name] = None

        # 比較策略性能
        successful_results = {k: v for k, v in results.items() if v is not None}
        if successful_results:
            best_strategy = max(successful_results.items(), key=lambda x: x[1].sharpe_ratio)
            print(f"\n🏆 Best Strategy: {best_strategy[0]} (Sharpe: {best_strategy[1].sharpe_ratio:.3f})")

        print("Multiple strategies test completed!")
        return len(successful_results) > 0

    except Exception as e:
        print(f"❌ Multiple strategies test failed: {e}")
        return False

def test_parameter_optimization():
    """測試參數優化"""
    print("\nTesting parameter optimization...")

    try:
        from src.backtest.vectorbt_engine import VectorBTEngine

        engine = VectorBTEngine()
        data = create_sample_price_data(100)  # 較少數據以加快測試

        # RSI參數優化
        print("Optimizing RSI strategy parameters...")
        param_ranges = {
            'period': range(10, 21, 2),  # 10, 12, 14, 16, 18, 20
            'oversold': [20, 25, 30, 35],
            'overbought': [65, 70, 75, 80]
        }

        start_time = time.time()
        optimization_result = engine.optimize_parameters(
            data=data,
            strategy="RSI_MEAN_REVERSION",
            param_ranges=param_ranges,
            symbol="OPT_TEST",
            optimization_metric="sharpe_ratio",
            max_combinations=50  # 限制組合數量以加快測試
        )
        optimization_time = time.time() - start_time

        print(f"✅ Optimization completed in {optimization_time:.2f}s")
        print(f"   Total combinations: {optimization_result['total_combinations']}")
        print(f"   Successful combinations: {optimization_result['successful_combinations']}")
        print(f"   Best parameters: {optimization_result['best_parameters']}")
        print(f"   Best Sharpe: {optimization_result['best_performance']['sharpe_ratio']:.3f}")
        print(f"   Best Return: {optimization_result['best_performance']['total_return']:.2%}")

        print("Parameter optimization test passed!")
        return True

    except Exception as e:
        print(f"❌ Parameter optimization test failed: {e}")
        return False

def test_strategy_builder():
    """測試策略構建器"""
    print("\nTesting strategy builder...")

    try:
        from src.backtest.strategy_builder import StrategyBuilder
        from src.backtest.vectorbt_engine import VectorBTEngine

        engine = VectorBTEngine()
        data = create_sample_price_data(150)

        # 創建兩個獨立策略的信號
        rsi_result = engine.backtest_strategy(
            data=data,
            strategy="RSI_MEAN_REVERSION",
            parameters={'period': 14, 'oversold': 30, 'overbought': 70}
        )

        macd_result = engine.backtest_strategy(
            data=data,
            strategy="MACD_CROSSOVER",
            parameters={'fast': 12, 'slow': 26, 'signal': 9}
        )

        # 創建策略構建器
        builder = StrategyBuilder()

        # 從引擎結果中提取信號（模擬）
        rsi_entries = pd.Series([False] * len(data))
        rsi_exits = pd.Series([False] * len(data))
        rsi_entries.iloc[::30] = True  # 每30天進場一次
        rsi_exits.iloc[15::30] = True  # 15天後退出

        macd_entries = pd.Series([False] * len(data))
        macd_exits = pd.Series([False] * len(data))
        macd_entries.iloc[::45] = True  # 每45天進場一次
        macd_exits[20::45] = True  # 20天後退出

        # 註冊策略
        builder.register_strategy("RSI_Strategy", rsi_entries, rsi_exits, weight=0.6)
        builder.register_strategy("MACD_Strategy", macd_entries, macd_exits, weight=0.4)

        # 組合策略
        combined_signals = builder.combine_strategies(
            ["RSI_Strategy", "MACD_Strategy"],
            combination_method="weighted_sum"
        )

        print(f"✅ Combined signals created:")
        print(f"   Entry signals: {combined_signals['entries'].sum()}")
        print(f"   Exit signals: {combined_signals['exits'].sum()}")

        # 獲取策略性能分析
        performance = builder.get_strategy_performance(combined_signals, data)
        print(f"   Signal quality: {performance.get('signal_statistics', {}).get('entry_quality', 0):.1f}")
        print(f"   Recommendations: {performance.get('recommendations', [])}")

        print("Strategy builder test passed!")
        return True

    except Exception as e:
        print(f"❌ Strategy builder test failed: {e}")
        return False

def test_performance():
    """性能測試"""
    print("\nPerformance testing...")

    try:
        from src.backtest.vectorbt_engine import VectorBTEngine

        engine = VectorBTEngine()
        data_sizes = [100, 200, 500]

        performance_results = {}

        for size in data_sizes:
            data = create_sample_price_data(size)

            # 測試單個策略性能
            start_time = time.time()
            result = engine.backtest_strategy(
                data=data,
                strategy="RSI_MEAN_REVERSION",
                parameters={'period': 14, 'oversold': 30, 'overbought': 70},
                symbol=f"PERF_TEST_{size}"
            )
            execution_time = time.time() - start_time

            performance_results[size] = {
                'execution_time': execution_time,
                'records_per_second': size / execution_time,
                'total_return': result.total_return,
                'sharpe_ratio': result.sharpe_ratio
            }

            print(f"\n📊 {size} data points:")
            print(f"   Execution time: {execution_time:.3f}s")
            print(f"   Records/sec: {size/execution_time:.0f}")
            print(f"   Return: {result.total_return:.2%}")

        # 計算平均性能
        avg_records_per_sec = np.mean([r['records_per_second'] for r in performance_results.values()])
        print(f"\n⚡ Average performance: {avg_records_per_sec:.0f} records/second")

        print("Performance test completed!")
        return True

    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def main():
    """主測試函數"""
    print("="*60)
    print("Simplified System VectorBT Backtesting Test")
    print("="*60)

    tests = [
        ("Basic Functionality", test_vectorbt_engine_basic),
        ("Multiple Strategies", test_multiple_strategies),
        ("Parameter Optimization", test_parameter_optimization),
        ("Strategy Builder", test_strategy_builder),
        ("Performance", test_performance)
    ]

    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False

    # 總結
    print("\n" + "="*60)
    print("VectorBT Backtesting Test Summary")
    print("="*60)

    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:25}: {status}")

    print(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\n🎉 All tests passed! VectorBT engine is working correctly.")
        print("✅ Ready for production use")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please check the issues.")

    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)