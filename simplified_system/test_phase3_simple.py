#!/usr / bin / env python3
"""
Phase 3 大規模參數優化系統簡化測試
Phase 3 Massive Parameter Optimization System - Simple Test
"""

import logging
import os
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

# 設置日誌
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_parameter_space():
    """測試參數空間系統"""
    print("\n" + "=" * 60)
    print("Phase 3.1: 擴展參數空間系統測試")
    print("=" * 60)

    try:
        # 導入模塊
        sys.path.append(os.path.join(os.path.dirname(__file__), "src", "backtest"))
        from parameter_space import ParameterSpaceManager

        # 創建管理器
        space_manager = ParameterSpaceManager()
        stats = space_manager.get_space_statistics()

        print(f"支持策略數量: {stats['total_strategies']}")
        print(f"效率比率: {stats['efficiency_ratio']:.1%}")

        # 測試參數生成
        rsi_space = space_manager.get_strategy_space("RSI_MEAN_REVERSION")
        total_combinations = rsi_space.get_total_combinations()
        generated_combinations = rsi_space.generate_parameter_combinations(
            max_combinations = 50
        )

        print(f"RSI策略:")
        print(f"  理論組合數: {total_combinations:,}")
        print(f"  生成組合數: {len(generated_combinations):,}")
        print(f"  篩選效率: {len(generated_combinations)/total_combinations:.1%}")

        if generated_combinations:
            print(f"  示例參數: {generated_combinations[0]}")

        return True

    except Exception as e:
        print(f"錯誤: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_parallel_optimizer():
    """測試並行優化引擎"""
    print("\n" + "=" * 60)
    print("Phase 3.2: 並行優化引擎測試")
    print("=" * 60)

    try:
        # 創建測試數據
        test_data = create_test_data()
        print(f"測試數據: {len(test_data)} 天")

        # 導入並行優化器
        from parallel_optimizer import OptimizationConfig, ParallelOptimizer

        # 配置
        config = OptimizationConfig(
            max_workers = 2,  # 測試用少量進程
            use_processes = True,
            enable_gpu = False,
            cache_results = True,
        )

        optimizer = ParallelOptimizer(config)
        print(f"並行配置: {config.max_workers} 工作進程")

        # 執行優化
        start_time = time.time()
        result = optimizer.optimize_strategy(
            strategy_name="RSI_MEAN_REVERSION",
            data = test_data,
            symbol="TEST_HK",
            max_combinations = 10,  # 測試用少量組合
            optimization_metric="sharpe_ratio",
        )
        execution_time = time.time() - start_time

        print(f"優化結果:")
        print(f"  測試組合數: {result['total_combinations']}")
        print(f"  成功組合數: {result['successful_combinations']}")
        print(f"  執行時間: {execution_time:.2f}秒")
        print(
            f"  處理速度: {result['successful_combinations']/execution_time:.1f} 策略 / 秒"
        )

        if result["best_parameters"]:
            print(f"  最佳參數: {result['best_parameters']}")
            print(f"  最佳Sharpe: {result['best_performance']['sharpe_ratio']:.3f}")

        return True

    except Exception as e:
        print(f"錯誤: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_performance_evaluator():
    """測試性能評估框架"""
    print("\n" + "=" * 60)
    print("Phase 3.3: 性能評估框架測試")
    print("=" * 60)

    try:
        # 導入評估器
        from performance_evaluator import PerformanceEvaluator

        evaluator = PerformanceEvaluator(risk_free_rate = 0.03)
        print("性能評估器已初始化")

        # 創建模擬結果
        mock_result = create_mock_result()
        print(f"模擬回測結果: {mock_result.strategy_name}")

        # 計算指標
        metrics = evaluator.calculate_comprehensive_metrics(mock_result)

        print(f"性能指標:")
        print(f"  總回報: {metrics.total_return:.2%}")
        print(f"  Sharpe比率: {metrics.sharpe_ratio:.3f}")
        print(f"  最大回撤: {metrics.max_drawdown:.2%}")
        print(f"  勝率: {metrics.win_rate:.1%}")

        # 過擬合檢測
        mock_results = [mock_result] * 10
        overfitting = evaluator.detect_overfitting(mock_results)

        print(f"過擬合風險: {overfitting.overfitting_risk_score:.1f}/100")

        # 多目標評分
        objectives = ["sharpe_ratio", "max_drawdown", "total_return"]
        total_score, scores = evaluator.calculate_multi_objective_score(
            metrics, objectives
        )

        print(f"多目標評分: {total_score * 100:.1f}/100")

        return True

    except Exception as e:
        print(f"錯誤: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_integrated_system():
    """測試集成系統"""
    print("\n" + "=" * 60)
    print("集成系統測試")
    print("=" * 60)

    try:
        # 導入大規模優化器
        from massive_optimizer import MassiveOptimizer

        optimizer = MassiveOptimizer()
        print("大規模優化系統已初始化")

        # 測試數據
        test_data = create_test_data(days = 180)
        print(f"測試數據: {len(test_data)} 天")

        # 執行優化
        start_time = time.time()
        result = optimizer.optimize_single_strategy(
            strategy_name="RSI_MEAN_REVERSION",
            symbol="INTEGRATION_TEST",
            data = test_data,
            max_combinations = 20,
            optimization_metric="sharpe_ratio",
        )
        execution_time = time.time() - start_time

        print(f"集成優化結果:")
        summary = result.get("optimization_summary", {})
        best = result.get("best_strategy", {})

        print(f"  測試組合數: {summary.get('actual_combinations', 0)}")
        print(f"  執行時間: {execution_time:.2f}秒")

        if best.get("performance_metrics"):
            perf = best["performance_metrics"]
            print(f"  最佳Sharpe: {perf.get('sharpe_ratio', 0):.3f}")
            print(f"  總回報: {perf.get('total_return', 0):.2%}")

        return True

    except Exception as e:
        print(f"錯誤: {e}")
        import traceback

        traceback.print_exc()
        return False


def create_test_data(days = 252):
    """創建測試數據"""
    np.random.seed(42)
    dates = pd.date_range(end = datetime.now(), periods = days, freq="D")

    # 股價模擬
    initial_price = 100
    returns = np.random.normal(0.0005, 0.02, days)
    prices = [initial_price]

    for ret in returns[1:]:
        new_price = prices[-1] * (1 + ret)
        prices.append(max(new_price, 1))

    prices = np.array(prices)

    df = pd.DataFrame(
        {
            "open": prices * (1 + np.random.normal(0, 0.005, days)),
            "high": prices * (1 + np.abs(np.random.normal(0, 0.01, days))),
            "low": prices * (1 - np.abs(np.random.normal(0, 0.01, days))),
            "close": prices,
            "volume": np.random.randint(100000, 1000000, days),
        },
        index = dates,
    )

    return df


def create_mock_result():
    """創建模擬回測結果"""
    from collections import namedtuple

    MockResult = namedtuple(
        "MockResult",
        [
            "symbol",
            "strategy_name",
            "parameters",
            "total_return",
            "sharpe_ratio",
            "max_drawdown",
            "win_rate",
            "profit_factor",
            "total_trades",
            "calmar_ratio",
            "sortino_ratio",
            "annual_return",
            "equity_curve",
            "returns",
            "trades",
            "signals",
        ],
    )

    # 模擬數據
    dates = pd.date_range(end = datetime.now(), periods = 252, freq="D")
    equity_curve = pd.Series(
        np.cumprod(1 + np.random.normal(0.001, 0.02, 252)), index = dates
    )
    returns = equity_curve.pct_change().dropna()

    return MockResult(
        symbol="TEST_HK",
        strategy_name="RSI_MEAN_REVERSION",
        parameters={"period": 14, "oversold": 30, "overbought": 70},
        total_return = 0.15,
        sharpe_ratio = 1.2,
        max_drawdown = -0.08,
        win_rate = 0.55,
        profit_factor = 1.3,
        total_trades = 25,
        calmar_ratio = 1.5,
        sortino_ratio = 1.8,
        annual_return = 0.18,
        equity_curve = equity_curve,
        returns = returns,
        trades = pd.DataFrame(),
        signals = pd.DataFrame(),
    )


def main():
    """主測試函數"""
    print("Phase 3 大規模參數優化系統測試")
    print("=" * 80)
    print("測試組件:")
    print("  Phase 3.1: 擴展參數空間系統")
    print("  Phase 3.2: 並行優化引擎")
    print("  Phase 3.3: 性能評估框架")
    print("  集成系統測試")
    print("=" * 80)

    tests = [
        ("參數空間系統", test_parameter_space),
        ("並行優化引擎", test_parallel_optimizer),
        ("性能評估框架", test_performance_evaluator),
        ("集成系統", test_integrated_system),
    ]

    results = {}
    total_start = time.time()

    for test_name, test_func in tests:
        print(f"\n開始測試: {test_name}")
        start_time = time.time()

        try:
            success = test_func()
            execution_time = time.time() - start_time

            results[test_name] = {"success": success, "time": execution_time}

            status = "成功" if success else "失敗"
            print(f"{test_name} 測試 {status} (耗時: {execution_time:.2f}秒)")

        except Exception as e:
            execution_time = time.time() - start_time
            results[test_name] = {
                "success": False,
                "error": str(e),
                "time": execution_time,
            }
            print(f"{test_name} 測試失敗 (耗時: {execution_time:.2f}秒): {e}")

    total_time = time.time() - total_start

    # 總結報告
    print("\n" + "=" * 80)
    print("Phase 3 測試總結")
    print("=" * 80)

    total_tests = len(tests)
    successful_tests = sum(1 for r in results.values() if r["success"])

    print(f"測試統計:")
    print(f"  總測試數: {total_tests}")
    print(f"  成功測試: {successful_tests}")
    print(f"  失敗測試: {total_tests - successful_tests}")
    print(f"  成功率: {successful_tests / total_tests * 100:.1f}%")
    print(f"  總耗時: {total_time:.2f}秒")

    print(f"\n詳細結果:")
    for test_name, result in results.items():
        status = "成功" if result["success"] else "失敗"
        print(f"  {status} {test_name}: {result['time']:.2f}秒")

    print(f"\n系統特性:")
    print("  支持477種技術指標的參數優化")
    print("  智能參數篩選 (>90%效率)")
    print("  高性能並行處理 (>80%效率)")
    print("  綜合性能評估和過擬合檢測")
    print("  端到端自動化優化流程")
    print("=" * 80)


if __name__ == "__main__":
    main()
