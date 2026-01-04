#!/usr/bin/env python3
"""
VectorBT Multiprocess Demo
========================

演示VectorBT多進程回測引擎的使用方法

功能展示：
- 投資組合級別並行回測
- 參數優化
- 實時監控
- 結果聚合和分析
"""

import asyncio
import logging
import time
from datetime import date, datetime
from typing import Dict, List, Any

# 導入VectorBT多進程引擎
from src.backtest.vectorbt_multiprocess_engine import (
    VectorBTMultiprocessEngine,
    VectorBTMultiprocessConfig,
    MultiprocessMode,
    run_vectorbt_multiprocess_backtest
)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 示例策略函數
def simple_rsi_strategy(data: Dict, rsi_period: int = 14, oversold: float = 30, overbought: float = 70):
    """
    簡單RSI策略示例

    Args:
        data: OHLCV數據
        rsi_period: RSI周期
        oversold: 超賣線
        overbought: 超買線

    Returns:
        (entries, exits) 信號數組
    """
    import numpy as np

    # 提取收盤價
    if hasattr(data, 'close'):
        close_prices = data['close'].values
    else:
        close_prices = np.array(data)

    # 計算RSI
    delta = np.diff(close_prices)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    # 計算平均收益和損失
    avg_gain = np.zeros_like(close_prices, dtype=float)
    avg_loss = np.zeros_like(close_prices, dtype=float)

    for i in range(rsi_period, len(close_prices)):
        avg_gain[i] = np.mean(gain[max(0, i - rsi_period):i])
        avg_loss[i] = np.mean(loss[max(0, i - rsi_period):i])

    # 計算RSI
    rs = np.divide(avg_gain, avg_loss, where=(avg_loss != 0))
    rsi = 100 - (100 / (1 + rs))

    # 生成信號
    entries = np.zeros(len(close_prices), dtype=bool)
    exits = np.zeros(len(close_prices), dtype=bool)

    # RSI策略邏輯
    entries[rsi < oversold] = True
    exits[rsi > overbought] = True

    return entries, exits


def ma_crossover_strategy(data: Dict, short_period: int = 10, long_period: int = 30):
    """
    移動平均線交叉策略示例

    Args:
        data: OHLCV數據
        short_period: 短期MA周期
        long_period: 長期MA周期

    Returns:
        (entries, exits) 信號數組
    """
    import numpy as np

    # 提取收盤價
    if hasattr(data, 'close'):
        close_prices = data['close'].values
    else:
        close_prices = np.array(data)

    # 計算移動平均線
    short_ma = np.convolve(close_prices, np.ones(short_period)/short_period, mode='valid')
    long_ma = np.convolve(close_prices, np.ones(long_period)/long_period, mode='valid')

    # 對齊長度
    ma_diff = len(short_ma) - len(long_ma)
    if ma_diff > 0:
        short_ma = short_ma[ma_diff:]
    elif ma_diff < 0:
        long_ma = long_ma[-ma_diff:]

    # 生成信號
    entries = np.zeros(len(close_prices), dtype=bool)
    exits = np.zeros(len(close_prices), dtype=bool)

    # MA交叉信號
    for i in range(1, len(short_ma)):
        idx = i + max(len(close_prices) - len(short_ma), 0)
        if idx < len(close_prices):
            if short_ma[i-1] <= long_ma[i-1] and short_ma[i] > long_ma[i]:
                entries[idx] = True  # 金叉
            elif short_ma[i-1] >= long_ma[i-1] and short_ma[i] < long_ma[i]:
                exits[idx] = True   # 死叉

    return entries, exits


async def demo_portfolio_backtest():
    """演示投資組合級別並行回測"""
    print("\n🚀 演示投資組合級別並行回測")
    print("=" * 50)

    # 配置回測參數
    symbols = ["0700.HK", "0388.HK", "1398.HK", "0939.HK", "3988.HK"]
    start_date = date(2023, 1, 1)
    end_date = date(2024, 12, 31)

    # 創建多進程配置
    config = VectorBTMultiprocessConfig(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000,
        commission=0.001,
        execution_mode=MultiprocessMode.PORTFOLIO_LEVEL,
        max_workers=4,
        cache_data=True,
        save_results=True,
        generate_report=True
    )

    print(f"📊 配置: {len(symbols)} 股票, {config.max_workers} 進程並行")
    print(f"📅 時間範圍: {start_date} 到 {end_date}")

    # 運行回測
    start_time = time.time()

    async with VectorBTMultiprocessEngine(config) as engine:
        print("\n⚡ 開始並行回測...")

        # 運行RSI策略回測
        results = await engine.run_portfolio_backtest(
            strategy_func=simple_rsi_strategy,
            parameters={
                'rsi_period': 14,
                'oversold': 30,
                'overbought': 70,
                'strategy_name': 'RSI策略'
            }
        )

        execution_time = time.time() - start_time

        # 聚合結果
        print(f"\n✅ 回測完成，耗時: {execution_time:.2f} 秒")
        print(f"📈 成功回測: {len(results)} 個股票")

        # 獲取聚合統計
        aggregated = await engine.aggregate_results(results)

        # 顯示結果摘要
        print("\n📊 回測結果摘要:")
        print(f"   平均回報率: {aggregated['average_return']:.2%}")
        print(f"   最佳回報率: {aggregated['best_return']:.2%}")
        print(f"   平均夏普比率: {aggregated['average_sharpe']:.2f}")
        print(f"   最佳夏普比率: {aggregated['best_sharpe']:.2f}")
        print(f"   勝率: {aggregated['win_rate']:.1f}%")

        # 顯示個別股票結果
        print("\n🎯 個別股票結果:")
        for task_id, result in results.items():
            symbol = result.metrics.get('symbol', 'Unknown')
            total_return = result.total_return
            sharpe_ratio = result.sharpe_ratio
            max_dd = result.max_drawdown

            print(f"   {symbol}: 回報={total_return:.2%}, 夏普={sharpe_ratio:.2f}, 回撤={max_dd:.2%}")

        # 獲取引擎狀態
        engine_status = await engine.get_engine_status()
        print(f"\n⚙️ 引擎性能:")
        print(f"   總任務數: {engine_status['tasks']['total']}")
        print(f"   完成任務: {engine_status['tasks']['completed']}")
        print(f"   失敗任務: {engine_status['tasks']['failed']}")
        print(f"   平均任務時間: {engine_status['performance']['average_task_time']:.3f}秒")

        # 保存結果
        await engine.save_results(aggregated, f"portfolio_backtest_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")


async def demo_parameter_optimization():
    """演示參數優化"""
    print("\n🔧 演示參數優化")
    print("=" * 50)

    # 配置優化參數
    symbols = ["0700.HK"]  # 使用單個股票進行優化演示
    start_date = date(2023, 1, 1)
    end_date = date(2024, 6, 30)

    # 定義參數網格
    param_grid = {
        'rsi_period': [10, 14, 20],
        'oversold': [20, 30, 40],
        'overbought': [60, 70, 80]
    }

    print(f"📊 優化股票: {symbols[0]}")
    print(f"🔧 參數網格:")
    for param, values in param_grid.items():
        print(f"   {param}: {values}")

    # 創建優化配置
    config = VectorBTMultiprocessConfig(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        execution_mode=MultiprocessMode.PARAMETER_LEVEL,
        max_workers=4,
        cache_data=True
    )

    start_time = time.time()

    async with VectorBTMultiprocessEngine(config) as engine:
        print("\n⚡ 開始參數優化...")

        # 運行參數優化
        optimization_result = await engine.run_parameter_optimization(
            strategy_func=simple_rsi_strategy,
            param_grid=param_grid,
            symbols=symbols,
            objective='sharpe_ratio'
        )

        execution_time = time.time() - start_time

        print(f"\n✅ 優化完成，耗時: {execution_time:.2f} 秒")
        print(f"🧪 測試組合數: {optimization_result['total_combinations']}")

        # 顯示最佳參數
        best_params = optimization_result['best_parameters']
        best_score = optimization_result['best_score']

        print(f"\n🏆 最佳參數:")
        print(f"   參數組合: {best_params}")
        print(f"   夏普比率: {best_score:.3f}")

        # 顯示前5個最佳結果
        all_results = optimization_result['all_results']
        sorted_results = sorted(all_results, key=lambda x: x.get('sharpe_ratio', 0), reverse=True)

        print(f"\n📈 前5個最佳結果:")
        for i, result in enumerate(sorted_results[:5]):
            params = result.get('parameters', {})
            sharpe = result.get('sharpe_ratio', 0)
            total_return = result.get('total_return', 0)
            print(f"   {i+1}. RSI={params.get('rsi_period', 0)}, "
                  f"超賣={params.get('oversold', 0)}, 超買={params.get('overbought', 0)} "
                  f"-> 夏普={sharpe:.3f}, 回報={total_return:.2%}")


async def demo_different_execution_modes():
    """演示不同執行模式的性能比較"""
    print("\n⚡ 演示不同執行模式性能比較")
    print("=" * 50)

    symbols = ["0700.HK", "0388.HK", "1398.HK", "0939.HK"]
    start_date = date(2023, 1, 1)
    end_date = date(2024, 3, 31)

    execution_modes = [
        MultiprocessMode.PORTFOLIO_LEVEL,
        MultiprocessMode.SYMBOL_LEVEL,
        MultiprocessMode.HYBRID
    ]

    results_comparison = {}

    for mode in execution_modes:
        print(f"\n🔄 測試執行模式: {mode.value}")

        config = VectorBTMultiprocessConfig(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            execution_mode=mode,
            max_workers=4,
            cache_data=False  # 不使用緩存以確保公平比較
        )

        start_time = time.time()

        try:
            async with VectorBTMultiprocessEngine(config) as engine:
                results = await engine.run_portfolio_backtest(
                    strategy_func=ma_crossover_strategy,
                    parameters={
                        'short_period': 10,
                        'long_period': 30,
                        'strategy_name': 'MA交叉策略'
                    }
                )

                execution_time = time.time() - start_time
                results_comparison[mode.value] = {
                    'execution_time': execution_time,
                    'success_count': len(results),
                    'avg_return': sum(r.total_return for r in results.values()) / len(results) if results else 0
                }

                print(f"   ⏱️ 執行時間: {execution_time:.2f} 秒")
                print(f"   📈 成功回測: {len(results)} 個")
                print(f"   💹 平均回報: {results_comparison[mode.value]['avg_return']:.2%}")

        except Exception as e:
            print(f"   ❌ 執行失敗: {e}")

    # 性能比較摘要
    print(f"\n📊 性能比較摘要:")
    print(f"{'模式':<20} {'時間(秒)':<10} {'成功數':<8} {'平均回報':<12}")
    print("-" * 55)

    for mode, metrics in results_comparison.items():
        print(f"{mode:<20} {metrics['execution_time']:<10.2f} {metrics['success_count']:<8} "
              f"{metrics['avg_return']:<12.2%}")


async def demo_convenience_function():
    """演示便利函數使用"""
    print("\n🎯 演示便利函數使用")
    print("=" * 50)

    symbols = ["0700.HK", "0388.HK", "1398.HK"]
    start_date = date(2023, 6, 1)
    end_date = date(2024, 6, 30)

    print(f"📊 使用便利函數運行回測: {len(symbols)} 個股票")

    # 使用便利函數
    result = await run_vectorbt_multiprocess_backtest(
        symbols=symbols,
        strategy_func=simple_rsi_strategy,
        start_date=start_date,
        end_date=end_date,
        execution_mode=MultiprocessMode.PORTFOLIO_LEVEL,
        max_workers=3,
        save_results=True,
        strategy_parameters={
            'rsi_period': 14,
            'oversold': 25,
            'overbought': 75
        }
    )

    print(f"\n✅ 便利函數回測完成")

    # 顯示聚合結果
    aggregated = result['aggregated_results']
    print(f"📈 聚合結果:")
    print(f"   總策略數: {aggregated['total_strategies']}")
    print(f"   成功策略: {aggregated['successful_strategies']}")
    print(f"   平均回報: {aggregated['average_return']:.2%}")
    print(f"   最佳回報: {aggregated['best_return']:.2%}")
    print(f"   勝率: {aggregated['win_rate']:.1f}%")

    # 顯示引擎狀態
    engine_status = result['engine_status']
    print(f"\n⚙️ 引擎狀態:")
    print(f"   引擎ID: {engine_status['engine_id']}")
    print(f"   執行模式: {engine_status['config']['execution_mode']}")
    print(f"   工作進程: {engine_status['config']['max_workers']}")
    print(f"   緩存狀態: {engine_status['cache_status']['cached_symbols']} 個股票")


async def main():
    """主演示函數"""
    print("🚀 VectorBT多進程回測引擎演示")
    print("=" * 60)
    print("本演示將展示VectorBT多進程回測引擎的各項功能")
    print("包括投資組合並行、參數優化、不同執行模式等")

    try:
        # 演示1: 投資組合級別並行回測
        await demo_portfolio_backtest()

        # 等待一下
        await asyncio.sleep(2)

        # 演示2: 參數優化
        await demo_parameter_optimization()

        # 等待一下
        await asyncio.sleep(2)

        # 演示3: 不同執行模式比較
        await demo_different_execution_modes()

        # 等待一下
        await asyncio.sleep(2)

        # 演示4: 便利函數使用
        await demo_convenience_function()

        print("\n🎉 所有演示完成！")
        print("=" * 60)
        print("VectorBT多進程回測引擎演示結束")

    except KeyboardInterrupt:
        print("\n⚠️ 用戶中斷演示")
    except Exception as e:
        print(f"\n❌ 演示過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 運行演示
    asyncio.run(main())