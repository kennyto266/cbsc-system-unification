#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
VectorBT增強功能教程示例
Enhanced VectorBT Features Tutorial Examples

本教程展示如何使用Simplified System中的VectorBT增強功能，
包括向量化策略、高級優化、風險管理和信號融合。
"""

import os
import sys
import time

import numpy as np
import pandas as pd

# 添加Simplified System路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backtest.advanced_optimizer import BayesianOptimizer, GeneticOptimizer
from src.backtest.signal_fusion_engine import SignalFusionConfig, SignalFusionEngine

# 導入核心模塊
from src.backtest.vectorbt_engine import VectorBTConfig, VectorBTEngine
from src.backtest.vectorbt_optimizer import OptimizationConfig, VectorBTOptimizer
from src.indicators.core_indicators import CoreIndicators
from src.risk.professional_risk_metrics import ProfessionalRiskMetrics

print("🚀 VectorBT增強功能教程示例")
print("=" * 60)

# ============================================================================
# 示例1: 基礎VectorBT引擎使用
# ============================================================================


def example_1_basic_vectorbt_engine():
    """示例1: 基礎VectorBT引擎使用"""
    print("\n📊 示例1: 基礎VectorBT引擎使用")
    print("-" * 40)

    # 創建測試數據
    np.random.seed(42)
    dates = pd.date_range("2022 - 01 - 01", "2024 - 01 - 01", freq="D")
    n_days = len(dates)

    # 模擬股價數據 (0700.HK 騰訊)
    initial_price = 400.0
    returns = np.random.normal(0.0008, 0.02, n_days)  # 日回報
    prices = initial_price * (1 + returns).cumprod()

    # 創建OHLCV數據
    data = pd.DataFrame(
        {
            "open": prices * np.random.uniform(0.995, 1.005, n_days),
            "high": prices * np.random.uniform(1.005, 1.020, n_days),
            "low": prices * np.random.uniform(0.980, 0.995, n_days),
            "close": prices,
            "volume": np.random.randint(1000000, 5000000, n_days),
        },
        index = dates,
    )

    print(f"📈 測試數據: {len(data)} 條記錄")
    print(f"💰 價格範圍: {data['close'].min():.2f} - {data['close'].max():.2f}")

    # 初始化VectorBT引擎
    config = VectorBTConfig(
        initial_capital = 100000,
        commission = 0.001,
        use_gpu = True,  # 啟用GPU加速
        enable_caching = True,
        parallel_jobs = 4,
    )

    engine = VectorBTEngine(config)
    print("⚡ VectorBT引擎已初始化 (GPU加速已啟用)")

    # 執行RSI策略回測
    start_time = time.time()
    rsi_result = engine.backtest_strategy(
        data, "RSI_MEAN_REVERSION", {"period": 14, "oversold": 30, "overbought": 70}
    )

    execution_time = time.time() - start_time

    print(f"\n🎯 RSI策略回測結果:")
    print(f"   ⏱️  執行時間: {execution_time:.3f}秒")
    print(f"   💹 總回報: {rsi_result.total_return:.2%}")
    print(f"   📊 Sharpe比率: {rsi_result.sharpe_ratio:.3f}")
    print(f"   📉 最大回撤: {rsi_result.max_drawdown:.2%}")

    return data, engine


# ============================================================================
# 示例2: 批量策略回測
# ============================================================================


def example_2_batch_backtesting(data, engine):
    """示例2: 批量策略回測"""
    print("\n🔄 示例2: 批量策略回測")
    print("-" * 40)

    # 定義多個策略
    strategies = [
        ("RSI_MEAN_REVERSION", {"period": 14, "oversold": 30, "overbought": 70}),
        ("MACD_CROSSOVER", {"fast": 12, "slow": 26, "signal": 9}),
        ("BOLLINGER_BANDS", {"period": 20, "std_dev": 2.0}),
        ("DUAL_MOVING_AVERAGE", {"short_period": 20, "long_period": 50}),
        ("MOMENTUM_BREAKOUT", {"momentum_period": 20, "momentum_threshold": 0.02}),
        (
            "VOLATILITY_BREAKOUT",
            {"volatility_period": 20, "volatility_multiplier": 2.0},
        ),
    ]

    print(f"📋 測試策略數量: {len(strategies)}")

    # 執行批量回測
    start_time = time.time()
    batch_results = engine.batch_backtest(data, strategies)
    execution_time = time.time() - start_time

    print(f"⚡ 批量回測完成，耗時: {execution_time:.3f}秒")
    print(f"🚀 平均每策略: {execution_time / len(strategies):.3f}秒")

    # 顯示結果排行
    print(f"\n📊 策略性能排行:")
    print("-" * 50)
    print(f"{'排名':<4} {'策略名稱':<20} {'總回報':<10} {'Sharpe':<8} {'最大回撤':<10}")
    print("-" * 50)

    sorted_results = sorted(batch_results, key = lambda x: x.sharpe_ratio, reverse = True)

    for i, result in enumerate(sorted_results, 1):
        strategy_name = strategies[result.strategy_index][0]
        print(
            f"{i:<4} {strategy_name:<20} {result.total_return:<10.2%} "
            f"{result.sharpe_ratio:<8.3f} {result.max_drawdown:<10.2%}"
        )

    return batch_results


# ============================================================================
# 示例3: 高級參數優化
# ============================================================================


def example_3_parameter_optimization(data, engine):
    """示例3: 高級參數優化"""
    print("\n🎛️ 示例3: 高級參數優化")
    print("-" * 40)

    # 初始化優化器
    optimizer = VectorBTOptimizer(engine)

    # 基礎參數優化
    print("🔍 執行基礎參數優化...")
    start_time = time.time()

    basic_results = optimizer.optimize_parameters(
        data = data,
        strategy_name="RSI_MEAN_REVERSION",
        param_ranges={
            "period": (10, 30, 5),  # (min, max, step)
            "oversold": (20, 40, 5),
            "overbought": (60, 80, 5),
        },
        config = OptimizationConfig(
            objectives=["sharpe_ratio"], constraints={"min_sharpe": 0.5}
        ),
    )

    basic_time = time.time() - start_time
    print(f"⚡ 基礎優化完成: {basic_time:.3f}秒")
    print(f"🏆 最佳參數: {basic_results.best_parameters}")
    print(f"📈 最佳Sharpe: {basic_results.best_score:.3f}")

    # 高級多目標優化
    print("\n🎯 執行多目標優化...")
    start_time = time.time()

    multi_objective_config = OptimizationConfig(
        objectives=["sharpe_ratio", "max_drawdown", "total_return"],
        weights=[0.4, 0.3, 0.3],  # Sharpe權重最高
        constraints={"min_sharpe": 0.5, "max_drawdown": 0.3, "min_trades": 10},
    )

    multi_results = optimizer.optimize_parameters(
        data = data,
        strategy_name="RSI_MEAN_REVERSION",
        param_ranges={
            "period": (10, 25, 3),
            "oversold": (25, 35, 3),
            "overbought": (65, 75, 3),
        },
        config = multi_objective_config,
    )

    multi_time = time.time() - start_time
    print(f"⚡ 多目標優化完成: {multi_time:.3f}秒")
    print(f"🏆 最佳綜合參數: {multi_results.best_parameters}")
    print(f"📊 綜合評分: {multi_results.best_score:.3f}")

    return basic_results, multi_results


# ============================================================================
# 示例4: 貝葉斯優化
# ============================================================================


def example_4_bayesian_optimization(data):
    """示例4: 貝葉斯優化"""
    print("\n🧠 示例4: 貝葉斯優化")
    print("-" * 40)

    # 評估函數
    def evaluate_rsi_strategy(params):
        try:
            engine = VectorBTEngine()
            result = engine.backtest_strategy(
                data,
                "RSI_MEAN_REVERSION",
                {
                    "period": int(params["period"]),
                    "oversold": int(params["oversold"]),
                    "overbought": int(params["overbought"]),
                },
            )
            return result.sharpe_ratio
        except Exception:
            return 0.0

    # 貝葉斯優化器
    bayesian_optimizer = BayesianOptimizer(
        param_bounds={"period": (10, 30), "oversold": (20, 40), "overbought": (60, 80)},
        acquisition_function="expected_improvement",
        n_initial_points = 10,
        max_iter = 50,
    )

    print("🔬 執行貝葉斯優化...")
    start_time = time.time()

    bayesian_results = bayesian_optimizer.optimize(
        evaluation_func = evaluate_rsi_strategy, maximize = True
    )

    bayesian_time = time.time() - start_time

    print(f"⚡ 貝葉斯優化完成: {bayesian_time:.3f}秒")
    print(f"🏆 最佳參數: {bayesian_results.best_params}")
    print(f"📈 最佳Sharpe: {bayesian_results.best_score:.3f}")
    print(f"🎯 收斂迭代: {bayesian_results.n_iterations}")

    return bayesian_results


# ============================================================================
# 示例5: 專業風險管理
# ============================================================================


def example_5_professional_risk_management(data, engine):
    """示例5: 專業風險管理"""
    print("\n🛡️ 示例5: 專業風險管理")
    print("-" * 40)

    # 執行策略獲取回報數據
    result = engine.backtest_strategy(
        data, "RSI_MEAN_REVERSION", {"period": 14, "oversold": 30, "overbought": 70}
    )

    returns = result.returns

    # 初始化風險管理器
    risk_metrics = ProfessionalRiskMetrics()

    # 基礎風險指標
    print("📊 計算基礎風險指標...")
    basic_metrics = risk_metrics.calculate_basic_metrics(returns)

    # 高級風險指標
    print("🎯 計算高級風險指標...")

    # VaR計算 (多種方法)
    var_historical = risk_metrics.calculate_var(returns, 0.95, "historical")
    var_parametric = risk_metrics.calculate_var(returns, 0.95, "parametric")
    var_cornish_fisher = risk_metrics.calculate_var(returns, 0.95, "cornish_fisher")

    # CVaR計算
    cvar_95 = risk_metrics.calculate_cvar(returns, 0.95)
    cvar_99 = risk_metrics.calculate_cvar(returns, 0.99)

    # 高級比率
    sortino_ratio = risk_metrics.calculate_sortino_ratio(returns, mar = 0.02)
    calmar_ratio = risk_metrics.calculate_calmar_ratio(returns)
    information_ratio = risk_metrics.calculate_information_ratio(
        returns, returns.mean()
    )

    # 顯示結果
    print(f"\n📈 風險指標報告:")
    print("-" * 40)
    print(f"📊 基礎Sharpe比率: {basic_metrics['sharpe_ratio']:.3f}")
    print(f"📉 最大回撤: {basic_metrics['max_drawdown']:.2%}")
    print(f"📊 年化波動率: {basic_metrics['annual_volatility']:.2%}")

    print(f"\n🎯 VaR (95%):")
    print(f"   歷史模擬法: {var_historical:.2%}")
    print(f"   參數法: {var_parametric:.2%}")
    print(f"   Cornish - Fisher: {var_cornish_fisher:.2%}")

    print(f"\n⚠️ CVaR (條件風險值):")
    print(f"   95% CVaR: {cvar_95:.2%}")
    print(f"   99% CVaR: {cvar_99:.2%}")

    print(f"\n🏆 高級比率:")
    print(f"   Sortino比率: {sortino_ratio:.3f}")
    print(f"   Calmar比率: {calmar_ratio:.3f}")
    print(f"   Information比率: {information_ratio:.3f}")

    return {
        "basic_metrics": basic_metrics,
        "var_metrics": {
            "historical": var_historical,
            "parametric": var_parametric,
            "cornish_fisher": var_cornish_fisher,
        },
        "cvar_metrics": {"cvar_95": cvar_95, "cvar_99": cvar_99},
        "advanced_ratios": {
            "sortino": sortino_ratio,
            "calmar": calmar_ratio,
            "information": information_ratio,
        },
    }


# ============================================================================
# 示例6: 信號融合引擎
# ============================================================================


def example_6_signal_fusion_engine(data):
    """示例6: 信號融合引擎"""
    print("\n🔄 示例6: 信號融合引擎")
    print("-" * 40)

    # 初始化核心指標計算器
    indicators = CoreIndicators()

    # 生成多個信號源
    print("📡 生成多個信號源...")

    # RSI信號
    rsi = indicators.calculate_rsi(data["close"], 14)
    rsi_signals = (rsi < 30).astype(int) - (rsi > 70).astype(int)

    # MACD信號
    macd_line, macd_signal, macd_histogram = indicators.calculate_macd(
        data["close"], 12, 26, 9
    )
    macd_signals = ((macd_line > macd_signal) & (macd_histogram > 0)).astype(int) - (
        (macd_line < macd_signal)
    ).astype(int)

    # 布林帶信號
    bb_upper, bb_middle, bb_lower = indicators.calculate_bollinger_bands(
        data["close"], 20, 2.0
    )
    bb_signals = ((data["close"] < bb_lower)).astype(int) - (
        (data["close"] > bb_upper)
    ).astype(int)

    # 動量信號
    momentum = data["close"].pct_change(10)
    momentum_signals = (momentum > 0.02).astype(int) - (momentum < -0.02).astype(int)

    print(f"✅ RSI信號: {rsi_signals.sum():.0f} 個交易信號")
    print(f"✅ MACD信號: {macd_signals.sum():.0f} 個交易信號")
    print(f"✅ 布林帶信號: {bb_signals.sum():.0f} 個交易信號")
    print(f"✅ 動量信號: {momentum_signals.sum():.0f} 個交易信號")

    # 初始化信號融合引擎
    fusion_engine = SignalFusionEngine()

    # 配置信號融合
    fusion_config = SignalFusionConfig(
        method="weighted_average",
        weights={"RSI": 0.3, "MACD": 0.3, "Bollinger": 0.2, "Momentum": 0.2},
        confidence_threshold = 0.3,
        disagreement_penalty = 0.1,
    )

    # 執行信號融合
    print("🔀 執行信號融合...")
    signal_sources = {
        "RSI": rsi_signals,
        "MACD": macd_signals,
        "Bollinger": bb_signals,
        "Momentum": momentum_signals,
    }

    fused_signals = fusion_engine.fuse_signals(
        signal_sources = signal_sources, config = fusion_config
    )

    # 市況識別
    market_regime = fusion_engine.identify_market_regime(data["close"], 60)
    print(f"📊 當前市況: {market_regime}")

    # 計算信號統計
    signal_stats = fusion_engine.calculate_signal_statistics(
        signal_sources, fused_signals
    )

    print(f"\n📊 信號融合統計:")
    print(f"   總信號數: {signal_stats['total_signals']}")
    print(f"   買入信號: {signal_stats['buy_signals']}")
    print(f"   賣出信號: {signal_stats['sell_signals']}")
    print(f"   信號一致率: {signal_stats['agreement_rate']:.2%}")
    print(f"   平均置信度: {signal_stats['avg_confidence']:.2%}")

    return {
        "individual_signals": signal_sources,
        "fused_signals": fused_signals,
        "market_regime": market_regime,
        "signal_stats": signal_stats,
    }


# ============================================================================
# 示例7: 性能基準測試
# ============================================================================


def example_7_performance_benchmark():
    """示例7: 性能基準測試"""
    print("\n⚡ 示例7: 性能基準測試")
    print("-" * 40)

    # 創建測試數據集
    np.random.seed(42)
    sizes = [1000, 5000, 10000, 20000]  # 不同的數據集大小

    results = []

    for size in sizes:
        print(f"🧪 測試數據集大小: {size:,}")

        # 生成測試數據
        dates = pd.date_range("2020 - 01 - 01", periods = size, freq="D")
        prices = 100 * np.cumprod(1 + np.random.normal(0.0005, 0.02, size))

        test_data = pd.DataFrame(
            {
                "open": prices * np.random.uniform(0.995, 1.005, size),
                "high": prices * np.random.uniform(1.005, 1.020, size),
                "low": prices * np.random.uniform(0.980, 0.995, size),
                "close": prices,
                "volume": np.random.randint(100000, 1000000, size),
            },
            index = dates,
        )

        # 測試單策略性能
        engine = VectorBTEngine()

        start_time = time.time()
        result = engine.backtest_strategy(
            test_data,
            "RSI_MEAN_REVERSION",
            {"period": 14, "oversold": 30, "overbought": 70},
        )
        single_time = time.time() - start_time

        # 測試批量策略性能
        strategies = [
            ("RSI_MEAN_REVERSION", {"period": 14}),
            ("MACD_CROSSOVER", {"fast": 12, "slow": 26}),
            ("DUAL_MOVING_AVERAGE", {"short_period": 20, "long_period": 50}),
        ]

        start_time = time.time()
        engine.batch_backtest(test_data, strategies)
        batch_time = time.time() - start_time

        # 計算性能指標
        strategies_per_second = len(strategies) / batch_time
        throughput = size / single_time

        results.append(
            {
                "data_size": size,
                "single_strategy_time": single_time,
                "batch_time": batch_time,
                "strategies_per_second": strategies_per_second,
                "throughput": throughput,
            }
        )

        print(f"   ⏱️  單策略: {single_time:.3f}秒")
        print(f"   ⚡ 批量 ({len(strategies)}策略): {batch_time:.3f}秒")
        print(f"   🚀 策略 / 秒: {strategies_per_second:.1f}")
        print(f"   📊 數據點 / 秒: {throughput:.0f}")

    # 性能總結
    print(f"\n📊 性能基準總結:")
    print("-" * 50)
    print(
        f"{'數據大小':<10} {'單策略(s)':<12} {'批量(s)':<10} {'策略 / 秒':<12} {'數據點 / 秒':<12}"
    )
    print("-" * 50)

    for result in results:
        print(
            f"{result['data_size']:<10} {result['single_strategy_time']:<12.3f} "
            f"{result['batch_time']:<10.3f} {result['strategies_per_second']:<12.1f} "
            f"{result['throughput']:<12.0f}"
        )

    # 檢查性能目標
    best_performance = max(results, key = lambda x: x["strategies_per_second"])
    print(f"\n🏆 最佳性能:")
    print(f"   數據大小: {best_performance['data_size']:,}")
    print(f"   策略 / 秒: {best_performance['strategies_per_second']:.1f}")

    if best_performance["strategies_per_second"] > 600:
        print(f"   ✅ 達到性能目標 (>600策略 / 秒)")
    else:
        print(f"   ⚠️  未達到性能目標 (目標: >600策略 / 秒)")

    return results


# ============================================================================
# 主函數
# ============================================================================


def main():
    """主函數 - 運行所有教程示例"""
    print("🎯 開始VectorBT增強功能教程")
    print("本教程將展示所有主要功能的使用方法")
    print("=" * 60)

    try:
        # 示例1: 基礎引擎使用
        data, engine = example_1_basic_vectorbt_engine()

        # 示例2: 批量回測
        example_2_batch_backtesting(data, engine)

        # 示例3: 參數優化
        basic_opt, multi_opt = example_3_parameter_optimization(data, engine)

        # 示例4: 貝葉斯優化
        example_4_bayesian_optimization(data)

        # 示例5: 專業風險管理
        example_5_professional_risk_management(data, engine)

        # 示例6: 信號融合
        example_6_signal_fusion_engine(data)

        # 示例7: 性能基準
        example_7_performance_benchmark()

        print("\n" + "=" * 60)
        print("🎉 教程示例全部完成！")
        print("=" * 60)

        print("\n📚 學習總結:")
        print("✅ 基礎VectorBT引擎使用")
        print("✅ 批量策略回測")
        print("✅ 高級參數優化")
        print("✅ 貝葉斯優化算法")
        print("✅ 專業風險管理")
        print("✅ 信號融合引擎")
        print("✅ 性能基準測試")

        print("\n🚀 下一步建議:")
        print("1. 嘗試您自己的數據和策略")
        print("2. 探索更多的優化算法")
        print("3. 集成實時數據源")
        print("4. 構建完整的量化交易系統")

        return True

    except Exception as e:
        print(f"\n❌ 教程執行出錯: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    sys.exit(exit_code)
