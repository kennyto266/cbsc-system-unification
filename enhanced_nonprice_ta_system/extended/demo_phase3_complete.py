#!/usr/bin/env python3
"""
Phase 3 Complete Demonstration
完整Phase 3系統演示

Demonstrates the complete Phase 3 parameter optimization system
"""

import json
import logging
import time
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import Phase 3 components
from extended.parameter_space import ExtendedParameterSpace, ParameterRange, IndicatorConfig
from extended.parallel_optimizer import ParallelParameterOptimizer, ResultCache, WorkloadBalancer
from extended.performance_evaluator import PerformanceEvaluator, PerformanceMetrics

logger = logging.getLogger(__name__)

def demo_parameter_space():
    """演示參數空間配置"""
    print("\n=== Parameter Space Demo ===")

    # 創建參數空間管理器
    param_space = ExtendedParameterSpace()

    # 顯示統計信息
    stats = param_space.get_statistics()
    print(f"Total indicators: {stats['total_indicators']}")
    print(f"Enabled indicators: {stats['enabled_indicators']}")
    print(f"Total combinations: {stats['total_combinations']}")

    # 顯示分類統計
    for category, info in stats['categories'].items():
        print(f"  {category}: {info['count']} indicators, {info['combinations']} combinations")

    # 測試參數生成
    print(f"\n--- RSI Parameter Generation ---")
    rsi_combinations = param_space.generate_parameter_combinations("RSI")
    print(f"Generated {len(rsi_combinations)} RSI parameter combinations")

    if rsi_combinations:
        print("Sample combinations:")
        for i, combo in enumerate(rsi_combinations[:3]):
            print(f"  {i+1}: {combo}")

    # 測試參數驗證
    print(f"\n--- Parameter Validation ---")
    valid_params = {"period": 14, "oversold": 30.0, "overbought": 70.0}
    invalid_params = {"period": 150, "oversold": 30.0, "overbought": 70.0}

    print(f"Valid parameters: {param_space.validate_parameters('RSI', valid_params)}")
    print(f"Invalid parameters: {param_space.validate_parameters('RSI', invalid_params)}")

    return param_space

def demo_parallel_optimizer():
    """演示並行優化引擎"""
    print("\n=== Parallel Optimizer Demo ===")

    # 定義目標函數
    def dummy_objective_function(indicator_name: str, parameters: dict) -> dict:
        # 模擬計算延遲
        time.sleep(0.01)

        # 生成基於參數的確定性性能指標
        param_hash = hash(json.dumps(parameters, sort_keys=True))

        # 確保不同參數組合有不同的性能
        sharpe_base = 1.0 + (param_hash % 100) / 50.0  # 1.0 to 3.0
        return_base = 0.05 + (param_hash % 80) / 100.0  # 0.05 to 0.85
        drawdown_base = -0.05 - (param_hash % 60) / 200.0  # -0.05 to -0.35

        return {
            "sharpe_ratio": sharpe_base,
            "total_return": return_base,
            "max_drawdown": drawdown_base,
            "annualized_return": return_base * 252 / len(parameters),  # 假設252天
            "volatility": abs(drawdown_base) * 2,
            "calmar_ratio": return_base / abs(drawdown_base) if drawdown_base != 0 else 0,
            "win_rate": 0.4 + (param_hash % 40) / 100.0,  # 0.4 to 0.8
            "profit_factor": 1.0 + (param_hash % 30) / 10.0,  # 1.0 to 4.0
            "stability_score": 0.3 + (param_hash % 70) / 100.0,  # 0.3 to 1.0
            "consistency_score": 0.2 + (param_hash % 80) / 100.0,  # 0.2 to 1.0
            "composite_score": sharpe_base + return_base
        }

    # 創建並行優化器
    optimizer = ParallelParameterOptimizer(
        objective_function=dummy_objective_function,
        num_workers=2,  # 使用較少工作線程進行演示
        use_multiprocessing=False,  # 使用多線程避免進程問題
        enable_progress_bar=True
    )

    # 準備測試任務
    test_tasks = [
        ("RSI", [
            {"period": 14, "oversold": 30, "overbought": 70},
            {"period": 21, "oversold": 25, "overbought": 75},
            {"period": 10, "oversold": 20, "overbought": 80}
        ]),
        ("MACD", [
            {"fast_period": 12, "slow_period": 26, "signal_period": 9},
            {"fast_period": 5, "slow_period": 35, "signal_period": 5},
            {"fast_period": 8, "slow_period": 21, "signal_period": 7}
        ])
    ]

    print(f"Starting parallel optimization with {len(test_tasks)} indicator types...")

    # 執行優化
    start_time = time.time()
    results = optimizer.optimize_indicators(test_tasks)
    execution_time = time.time() - start_time

    print(f"Optimization completed in {execution_time:.2f}s")
    print(f"Total results: {len(results)}")

    # 獲取最佳結果
    best_results = optimizer.get_best_results(results, "sharpe_ratio", top_n=5)

    print(f"\n--- Top 5 Results by Sharpe Ratio ---")
    for i, result in enumerate(best_results, 1):
        print(f"{i}. {result.indicator_name}:")
        print(f"   Parameters: {result.parameters}")
        print(f"   Sharpe Ratio: {result.performance_metrics['sharpe_ratio']:.3f}")
        print(f"   Total Return: {result.performance_metrics['total_return']:.3f}")
        print(f"   Max Drawdown: {result.performance_metrics['max_drawdown']:.3f}")

    return optimizer

def demo_performance_evaluator():
    """演示性能評估框架"""
    print("\n=== Performance Evaluator Demo ===")

    # 創建評估器
    evaluator = PerformanceEvaluator(
        risk_free_rate=0.03,
        benchmark_return=0.08,
        enable_overfitting_detection=True,
        min_trades_for_evaluation=20
    )

    # 模擬不同的策略性能數據
    strategies = [
        {
            "name": "Conservative RSI",
            "parameters": {"period": 21, "oversold": 25, "overbought": 75},
            "returns": [0.001, -0.0005, 0.002, 0.0008, -0.0012, 0.0015, 0.0003] * 30,  # 210天數據
            "trades": [{"return": 0.05}, {"return": -0.02}, {"return": 0.03}] * 10  # 30筆交易
        },
        {
            "name": "Aggressive MACD",
            "parameters": {"fast_period": 5, "slow_period": 20, "signal_period": 3},
            "returns": [0.003, -0.002, 0.004, 0.001, -0.003, 0.006, 0.002] * 30,
            "trades": [{"return": 0.08}, {"return": -0.05}, {"return": 0.06}] * 10
        },
        {
            "name": "Balanced Strategy",
            "parameters": {"period": 14, "oversold": 30, "overbought": 70},
            "returns": [0.002, -0.001, 0.003, 0.0015, -0.0015, 0.0025, 0.001] * 30,
            "trades": [{"return": 0.06}, {"return": -0.03}, {"return": 0.04}] * 10
        }
    ]

    evaluation_results = []

    for strategy in strategies:
        print(f"\n--- Evaluating {strategy['name']} ---")

        result = evaluator.evaluate_strategy(
            indicator_name=strategy['name'].split()[0],  # 取指標名稱
            parameters=strategy['parameters'],
            returns_data=strategy['returns'],
            trades_data=strategy['trades']
        )

        print(f"Sharpe Ratio: {result.performance_metrics.sharpe_ratio:.3f}")
        print(f"Total Return: {result.performance_metrics.total_return:.3f}")
        print(f"Max Drawdown: {result.performance_metrics.max_drawdown:.3f}")
        print(f"Win Rate: {result.performance_metrics.win_rate:.3f}")
        print(f"Stability Score: {result.performance_metrics.stability_score:.3f}")
        print(f"Composite Score: {result.composite_score:.3f}")
        print(f"Overfitted: {result.overfitting_detection.is_overfitted}")

        if result.overfitting_detection.warnings:
            print("Warnings:")
            for warning in result.overfitting_detection.warnings:
                print(f"  - {warning}")

        evaluation_results.append(result)

    # 排名結果
    ranked_results = evaluator.rank_results(evaluation_results)

    print(f"\n--- Strategy Rankings ---")
    for i, result in enumerate(ranked_results, 1):
        print(f"{i}. {result.indicator_name}: Score {result.composite_score:.3f}, Sharpe {result.performance_metrics.sharpe_ratio:.3f}")

    # 獲取帕累托前沿
    pareto_frontier = evaluator.get_pareto_frontier(evaluation_results)

    print(f"\n--- Pareto Frontier ---")
    for i, result in enumerate(pareto_frontier, 1):
        print(f"{i}. {result.indicator_name}: Score {result.composite_score:.3f}")

    # 生成評估報告
    report_file = evaluator.generate_evaluation_report(
        evaluation_results,
        f"demo_evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    print(f"\nEvaluation report generated: {report_file}")

    return evaluator

def demo_phase3_integration():
    """演示完整的Phase 3集成"""
    print("\n=== Phase 3 Integration Demo ===")

    # 1. 參數空間配置
    print("1. Initializing Parameter Space...")
    param_space = demo_parameter_space()

    # 2. 並行優化引擎
    print("2. Running Parallel Optimization...")
    parallel_optimizer = demo_parallel_optimizer()

    # 3. 性能評估框架
    print("3. Evaluating Performance...")
    performance_evaluator = demo_performance_evaluator()

    # 4. 生成集成報告
    print("\n4. Generating Integration Report...")

    integration_report = {
        "phase3_components": {
            "parameter_space": {
                "total_indicators": len(param_space.indicator_configs),
                "total_combinations": param_space.get_total_combinations()
            },
            "parallel_optimizer": {
                "total_tasks": parallel_optimizer.total_tasks,
                "completed_tasks": parallel_optimizer.completed_tasks,
                "cached_tasks": parallel_optimizer.cached_tasks,
                "execution_time": parallel_optimizer.start_time and (time.time() - parallel_optimizer.start_time) or 0
            },
            "performance_evaluator": {
                "risk_free_rate": performance_evaluator.risk_free_rate,
                "benchmark_return": performance_evaluator.benchmark_return,
                "overfitting_detection_enabled": performance_evaluator.enable_overfitting_detection
            }
        },
        "system_capabilities": {
            "supported_indicators": list(param_space.indicator_configs.keys()),
            "parallel_processing": {
                "max_workers": parallel_optimizer.num_workers,
                "multiprocessing": parallel_optimizer.use_multiprocessing
            },
            "performance_metrics": [
                "sharpe_ratio", "total_return", "max_drawdown", "win_rate",
                "profit_factor", "stability_score", "consistency_score"
            ]
        },
        "demo_timestamp": datetime.now().isoformat(),
        "demo_status": "SUCCESS"
    }

    # 保存集成報告
    report_file = f"phase3_integration_demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(integration_report, f, indent=2, ensure_ascii=False)

    print(f"Phase 3 Integration Report saved to: {report_file}")

    return integration_report

def main():
    """主演示函數"""
    print("=== Phase 3 Complete System Demonstration ===")
    print(f"Started at: {datetime.now()}")

    # 設置日誌級別
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    start_time = time.time()

    try:
        # 執行完整演示
        integration_report = demo_phase3_integration()

        # 成功總結
        execution_time = time.time() - start_time
        print(f"\n=== Demo Summary ===")
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Status: {integration_report['demo_status']}")
        print(f"Total indicators supported: {integration_report['phase3_components']['parameter_space']['total_indicators']}")
        print(f"Total parameter combinations: {integration_report['phase3_components']['parameter_space']['total_combinations']}")

        print("\n=== Phase 3 System Successfully Demonstrated ===")
        print("[OK] Parameter Space Configuration")
        print("[OK] Parallel Optimization Engine")
        print("[OK] Performance Evaluation Framework")
        print("[OK] Complete System Integration")

        return True

    except Exception as e:
        print(f"\n[X] Demo failed with error: {e}")
        logger.exception("Demo execution failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)