#!/usr/bin/env python3
"""
Phase 4 回測功能測試
測試新實現的回測功能
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

def test_vectorbt_integration():
    """測試VectorBT集成"""
    print("=== VectorBT集成測試 ===")

    try:
        from simplified_system.src.backtest.vectorbt_engine import VectorBTEngine
        print("✅ VectorBTEngine導入成功")

        # 創建測試數據
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 102,
            'low': np.random.randn(100).cumsum() + 98,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)

        print("✅ 測試數據創建成功")

        # 初始化引擎
        engine = VectorBTEngine()
        print("✅ VectorBTEngine初始化成功")

        # 測試單策略回測
        result = engine.backtest_strategy(
            data=data,
            strategy="RSI_MEAN_REVERSION",
            parameters={"period": 14, "oversold": 30, "overbought": 70},
            symbol="TEST"
        )

        print("✅ 單策略回測成功")
        print(f"   - 總回報: {result.total_return:.2%}")
        print(f"   - 夏普比率: {result.sharpe_ratio:.3f}")
        print(f"   - 最大回撤: {result.max_drawdown:.2%}")

        # 測試參數優化
        param_ranges = {
            'period': range(10, 21, 5),
            'oversold': [25, 30, 35],
            'overbought': [65, 70, 75]
        }

        optimization_result = engine.optimize_parameters(
            data=data,
            strategy="RSI_MEAN_REVERSION",
            param_ranges=param_ranges,
            symbol="TEST",
            max_combinations=50
        )

        print("✅ 參數優化成功")
        print(f"   - 最佳參數: {optimization_result['best_parameters']}")
        print(f"   - 最佳性能: {optimization_result['best_performance']}")

        return True

    except Exception as e:
        print(f"❌ VectorBT集成測試失敗: {e}")
        return False

def test_interactive_trader_menu():
    """測試互動式交易菜單"""
    print("\n=== 互動式菜單測試 ===")

    try:
        # 測試導入
        sys.path.insert(0, str(Path(__file__).parent))
        from interactive_quantitative_trader import InteractiveQuantitativeTrader

        print("✅ InteractiveQuantitativeTrader導入成功")

        # 創建實例（不運行主循環）
        trader = InteractiveQuantitativeTrader()
        print("✅ InteractiveQuantitativeTrader初始化成功")

        # 檢查backtest_menu方法存在
        if hasattr(trader, 'backtest_menu'):
            print("✅ backtest_menu方法存在")
        else:
            print("❌ backtest_menu方法不存在")
            return False

        # 檢查輔助方法
        methods = [
            '_single_strategy_backtest',
            '_parameter_optimization',
            '_multi_strategy_comparison',
            '_execute_backtest',
            '_display_backtest_result',
            '_select_strategy',
            '_set_strategy_parameters'
        ]

        for method in methods:
            if hasattr(trader, method):
                print(f"✅ {method}方法存在")
            else:
                print(f"❌ {method}方法不存在")

        return True

    except Exception as e:
        print(f"❌ 互動式菜單測試失敗: {e}")
        return False

def test_data_integration():
    """測試數據集成"""
    print("\n=== 數據集成測試 ===")

    try:
        # 測試Phase 2數據獲取
        from simplified_system.src.api.stock_api import get_hk_stock_data

        # 嘗試獲取少量數據
        data = get_hk_stock_data("0700.HK", 30)

        if data is not None and len(data) > 0:
            print("✅ Phase 2數據獲取成功")
            print(f"   - 數據點數: {len(data)}")
            print(f"   - 數據列: {list(data.columns)}")
            print(f"   - 價格範圍: {data['close'].min():.2f} - {data['close'].max():.2f}")
            return True
        else:
            print("⚠️ Phase 2數據獲取返回空數據")
            return False

    except Exception as e:
        print(f"❌ 數據集成測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🧪 Phase 4 回測功能測試")
    print("=" * 50)

    test_results = []

    # 運行所有測試
    test_results.append(test_vectorbt_integration())
    test_results.append(test_interactive_trader_menu())
    test_results.append(test_data_integration())

    # 總結測試結果
    print("\n" + "=" * 50)
    print("📊 測試結果總結")

    passed = sum(test_results)
    total = len(test_results)

    print(f"通過: {passed}/{total}")

    if passed == total:
        print("🎉 所有測試通過！Phase 4 回測功能實現成功！")
    else:
        print("⚠️ 部分測試失敗，請檢查相關功能")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)