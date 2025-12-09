#!/usr/bin/env python3
"""
0700.HK 0-300 參數回測系統演示
HK700 0-300 Parameter Backtesting System Demo

展示完整的0-300參數空間回測功能
演示系統性能和結果分析
"""

import time
import json
import logging
from datetime import datetime

# 設置路徑
import sys
sys.path.append('src')
sys.path.append('src/parameter_space')
sys.path.append('src/adapters')
sys.path.append('src/optimization')

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def demonstrate_parameter_space():
    """演示參數空間管理"""
    print("=" * 80)
    print("0700.HK 參數空間管理器演示")
    print("=" * 80)

    try:
        from hk700_parameter_manager import HK700ParameterManager
        manager = HK700ParameterManager()

        # 顯示所有參數空間
        print("\n可用參數空間:")
        for space_name in manager.parameter_spaces.keys():
            stats = manager.get_space_statistics(space_name)
            print(f"  {space_name}:")
            print(f"    - 總組合數: {stats['total_combinations']:,}")
            print(f"    - 參數數量: {stats['total_parameters']}")
            print(f"    - 約束條件: {stats['constraints_count']}")
            print(f"    - 描述: {stats['description']}")

        # 展示參數範圍
        print(f"\nRSI 0-300 參數範圍詳情:")
        rsi_space = manager.parameter_spaces['RSI_0_300']
        for param in rsi_space.parameters:
            param_range = param.generate_range()
            print(f"  {param.name}:")
            print(f"    - 範圍: {param.min_value} - {param.max_value} (步長: {param.step})")
            print(f"    - 類型: {param.param_type}")
            print(f"    - 選項數: {len(param_range)}")
            if len(param_range) <= 10:
                print(f"    - 示例值: {param_range[:5]}...")

        # 演示智能採樣
        print(f"\n智能採樣演示:")
        sample_size = 1000
        smart_sample = manager.generate_smart_sample('RSI_0_300', sample_size)
        print(f"  生成 {len(smart_sample)} 個智能採樣組合")

        # 分析採樣策略
        rsi_oversold_values = [p['rsi_oversold'] for p in smart_sample]
        rsi_overbought_values = [p['rsi_overbought'] for p in smart_sample]

        print(f"  RSI超賣值分佈: min={min(rsi_oversold_values)}, max={max(rsi_oversold_values)}, avg={sum(rsi_oversold_values)/len(rsi_oversold_values):.1f}")
        print(f"  RSI超買值分佈: min={min(rsi_overbought_values)}, max={max(rsi_overbought_values)}, avg={sum(rsi_overbought_values)/len(rsi_overbought_values):.1f}")

    except Exception as e:
        logger.error(f"Parameter space demo failed: {e}")
        return False

    return True


def demonstrate_data_adapter():
    """演示數據適配器"""
    print("\n" + "=" * 80)
    print("0700.HK 數據適配器演示")
    print("=" * 80)

    try:
        from hk700_data_adapter import HK700DataAdapter
        adapter = HK700DataAdapter()

        # 獲取數據統計
        print("\n📈 數據統計信息:")
        stats = adapter.get_data_statistics()
        if 'error' in stats:
            print("  ❌ 無法獲取數據")
            return False

        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    - {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")

        # 載入處理後的數據
        print(f"\n🔧 載入技術指標數據...")
        data_with_indicators = adapter.get_data_with_indicators()

        if not data_with_indicators.empty:
            print(f"  ✅ 成功加載 {len(data_with_indicators)} 個數據點")
            print(f"  📅 技術指標: {list(data_with_indicators.columns)}")

            # 顯示最新指標值
            print(f"\n📊 最新技術指標值:")
            latest_row = data_with_indicators.iloc[-1]
            for col in ['rsi_14', 'macd', 'atr', 'volume_ratio']:
                if col in data_with_indicators.columns:
                    print(f"  - {col}: {latest_row[col]:.3f}")
        else:
            print("  ❌ 無法加載指標數據")

    except Exception as e:
        logger.error(f"Data adapter demo failed: {e}")
        return False

    return True


def demonstrate_optimizer():
    """演示優化器功能"""
    print("\n" + "=" * 80)
    print("⚡ 0700.HK 參數優化器演示")
    print("=" * 80)

    try:
        from hk700_optimizer import HK700Optimizer

        # 初始化優化器
        print("🔧 初始化優化器...")
        optimizer = HK700Optimizer(max_workers=4)

        # 設置優化參數
        test_combinations = 1000
        optimization_metric = "sharpe_ratio"

        print(f"⚙️ 開始小規模優化測試...")
        print(f"  - 測試組合數: {test_combinations:,}")
        print(f"  - 優化指標: {optimization_metric}")
        print(f"  - 使用線程數: {optimizer.max_workers}")

        # 執行優化（使用小規模測試）
        start_time = time.time()
        result = optimizer.run_parameter_optimization(
            parameter_space="RSI_0_300",
            optimization_metric=optimization_metric,
            max_combinations=test_combinations,
            use_smart_sampling=True
        )
        optimization_time = time.time() - start_time

        # 顯示結果
        print(f"\n🎯 優化結果 (耗時: {optimization_time:.2f}秒):")
        print(f"  📊 策略名稱: {result.strategy_name}")
        print(f"  🔢 測試組合: {result.total_combinations:,}")
        print(f"  ✅ 成功組合: {result.successful_combinations:,}")
        print(f"  ⚡ 處理速度: {result.successful_combinations/optimization_time:.1f} 組合/秒")
        print(f"  💾 緩存命中率: {result.cache_hit_rate:.1%}")
        print(f"  👥 使用線程: {result.workers_used}")

        # 顯示最佳參數
        print(f"\n🏆 最佳參數組合:")
        for param, value in result.best_parameters.items():
            print(f"  • {param}: {value}")

        # 顯示最佳性能
        print(f"\n📈 最佳性能指標:")
        key_metrics = ['sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate']
        for metric in key_metrics:
            if metric in result.best_performance:
                value = result.best_performance[metric]
                if metric in ['sharpe_ratio']:
                    print(f"  - {metric}: {value:.3f}")
                elif metric in ['total_return', 'max_drawdown']:
                    print(f"  - {metric}: {value:.2%}")
                else:
                    print(f"  - {metric}: {value}")

        # 顯示性能統計
        if result.performance_statistics:
            print(f"\n📊 優化統計:")
            stats = result.performance_statistics
            print(f"  - 平均分數: {stats['mean_score']:.4f}")
            print(f"  - 分數標準差: {stats['std_score']:.4f}")
            print(f"  - 分數範圍: {stats['min_score']:.4f} - {stats['max_score']:.4f}")
            print(f"  - 成功率: {stats['successful_rate']:.1%}")

        # 生成並顯示報告
        report = optimizer.generate_optimization_report(result)
        print(report)

    except Exception as e:
        logger.error(f"Optimizer demo failed: {e}")
        return False

    return True


def run_comparison_demo():
    """運行參數空間比較演示"""
    print("\n" + "=" * 80)
    print("🔄 參數空間比較演示")
    print("=" * 80)

    try:
        from hk700_optimizer import HK700Optimizer

        # 初始化優化器
        optimizer = HK700Optimizer(max_workers=2)  # 使用較少線程以加快演示

        # 測試多個參數空間
        test_spaces = ["RSI_0_300", "MACD_0_300", "MA_0_300"]
        test_combinations = 500

        print(f"🧪 比較參數空間: {', '.join(test_spaces)}")
        print(f"🎯 每個空間測試: {test_combinations:,} 組合")

        # 運行比較
        results = optimizer.compare_parameter_spaces(
            parameter_spaces=test_spaces,
            max_combinations_per_space=test_combinations,
            optimization_metric="sharpe_ratio"
        )

        # 顯示比較結果
        print(f"\n📊 比較結果總覽:")
        for space_name, result in results.items():
            sharpe = result.best_performance.get('sharpe_ratio', 0)
            print(f"  {space_name}:")
            print(f"    - 最佳Sharpe: {sharpe:.3f}")
            print(f"    - 總回報: {result.best_performance.get('total_return', 0):.2%}")
            print(f"    - 最大回撤: {result.best_performance.get('max_drawdown', 0):.2%}")
            print(f"    - 優化時間: {result.optimization_time:.2f}秒")

        # 找出最佳策略
        best_space = max(results.items(), key=lambda x: x[1].best_performance.get('sharpe_ratio', 0))
        print(f"\n🏆 最佳策略: {best_space[0]} (Sharpe: {best_space[1].best_performance.get('sharpe_ratio', 0):.3f})")

    except Exception as e:
        logger.error(f"Comparison demo failed: {e}")
        return False

    return True


def main():
    """主演示函數"""
    print("🚀 0700.HK 0-300 參數回測系統演示")
    print("專為騰訊控股設計的大規模參數優化平台")
    print("支持0-300全範圍參數組合測試和智能採樣優化")
    print()

    start_time = time.time()

    # 運行各個演示模組
    demos = [
        demonstrate_parameter_space,
        demonstrate_data_adapter,
        demonstrate_optimizer,
        run_comparison_demo
    ]

    results = []
    for demo in demos:
        try:
            result = demo()
            results.append(result)
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            results.append(False)

    # 總結
    total_time = time.time() - start_time
    success_count = sum(results)

    print("\n" + "=" * 80)
    print("📋 演示完成總結")
    print("=" * 80)
    print(f"✅ 成功演示: {success_count}/{len(demos)}")
    print(f"⏱️ 總耗時: {total_time:.2f}秒")
    print()
    print("🎯 核心特性展示:")
    print("  • ✅ 參數空間管理器 - 支持0-300全範圍")
    print("  • ✅ 智能採樣算法 - 減少計算複雜度")
    print("  • ✅ 高性能並行處理 - 多線程優化")
    print("  • ✅ 數據緩存機制 - 提升處理效率")
    print("  • ✅ 綜合性能分析 - Sharpe、Sortino等指標")
    print("  • ✅ 實時結果可視化 - 完整報告生成")
    print()
    print("🚀 系統已準備好進行大規模0-300參數回測！")
    print("💡 可以運行: python hk700_parameter_backtest.py --mode=full")

    if success_count == len(demos):
        print("\n🎉 所有演示成功完成！0700.HK參數回測系統已就緒。")
        return True
    else:
        print(f"\n⚠️  部分演示失敗，請檢查日誌了解詳情。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)