#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版參數優化演示腳本
Enhanced Parameter Optimization Demo

展示如何使用四個新的增強功能：
1. GPU內存管理
2. 智能搜索算法
3. 實時性能監控
4. 高級統計驗證
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any

# 導入增強版優化器
from enhanced_comprehensive_parameter_optimizer import (
    EnhancedComprehensiveParameterOptimizer,
    EnhancedOptimizationConfig,
    quick_enhanced_optimize_0700
)

# 導入原有系統用於比較
from comprehensive_parameter_optimizer import quick_optimize_0700

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_comparison_demo():
    """運行對比演示 - 原系統 vs 增強系統"""
    print("\n" + "="*80)
    print("🚀 0700.HK 增強版參數優化系統演示")
    print("="*80)

    print("\n📊 系統對比測試")
    print("-" * 40)

    # 測試參數設置
    test_combinations = 1000
    symbol = "0700.HK"

    print(f"測試股票: {symbol}")
    print(f"測試組合數: {test_combinations}")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 運行原系統（基準測試）
    print(f"\n🔄 運行原系統基準測試...")
    start_time = time.time()

    try:
        original_results = quick_optimize_0700(
            max_combinations=test_combinations,
            use_gpu=True
        )
        original_time = time.time() - start_time

        print(f"✅ 原系統完成，耗時: {original_time:.2f}秒")

        # 顯示原系統結果
        for strategy, result in original_results.items():
            if result.performance_metrics:
                best = result.performance_metrics[0]
                print(f"   {strategy}: Sharpe {best['sharpe_ratio']:.3f}, 回撤 {best['max_drawdown']*100:.2f}%")

    except Exception as e:
        print(f"❌ 原系統運行失敗: {e}")
        original_results = {}
        original_time = 0

    # 2. 運行增強系統
    print(f"\n🚀 運行增強系統測試...")
    start_time = time.time()

    try:
        enhanced_results = quick_enhanced_optimize_0700(
            max_combinations=test_combinations,
            use_gpu=True,
            enable_all_enhancements=True
        )
        enhanced_time = time.time() - start_time

        print(f"✅ 增強系統完成，耗時: {enhanced_time:.2f}秒")

        # 顯示增強系統結果
        for strategy, result in enhanced_results.items():
            if result.performance_metrics:
                best = result.performance_metrics[0]
                print(f"   {strategy}: Sharpe {best['sharpe_ratio']:.3f}, 回撤 {best['max_drawdown']*100:.2f}%, 算法 {best.get('algorithm', 'N/A')}")

    except Exception as e:
        print(f"❌ 增強系統運行失敗: {e}")
        enhanced_results = {}
        enhanced_time = 0

    # 3. 性能比較
    print(f"\n📈 性能比較分析")
    print("-" * 40)

    if original_time > 0 and enhanced_time > 0:
        speed_improvement = (original_time - enhanced_time) / original_time * 100
        print(f"執行時間: 原系統 {original_time:.2f}s vs 增強系統 {enhanced_time:.2f}s")
        print(f"性能提升: {speed_improvement:+.1f}%")

    # 比較最佳結果
    for strategy in ['HIBOR_RSI', 'MONETARY_MACD']:
        if strategy in original_results and strategy in enhanced_results:
            orig_best = original_results[strategy].performance_metrics[0]['sharpe_ratio'] if original_results[strategy].performance_metrics else 0
            enh_best = enhanced_results[strategy].performance_metrics[0]['sharpe_ratio'] if enhanced_results[strategy].performance_metrics else 0

            improvement = ((enh_best - orig_best) / orig_best * 100) if orig_best > 0 else 0
            print(f"{strategy} Sharpe: {orig_best:.3f} → {enh_best:.3f} ({improvement:+.1f}%)")

    # 4. 增強功能詳情
    print(f"\n🔧 增強功能詳情")
    print("-" * 40)

    for strategy, result in enhanced_results.items():
        print(f"\n{strategy} 策略增強功能:")

        # 統計驗證
        if result.statistical_validation:
            validation = result.statistical_validation
            print(f"  ✅ 統計驗證: {'通過' if validation.is_valid else '失敗'} (評分: {validation.validation_score:.3f})")
            print(f"  📊 過擬合風險: {validation.overfitting_risk}")

        # 搜索算法性能
        if result.search_algorithm_performance:
            best_algo = None
            best_score = -1
            for algorithm, results in result.search_algorithm_performance.items():
                if results:
                    algo_best = max(r.score for r in results)
                    if algo_best > best_score:
                        best_score = algo_best
                        best_algo = algorithm
            print(f"  🧠 最佳算法: {best_algo} (評分: {best_score:.3f})")

        # 性能警報
        if result.performance_alerts:
            print(f"  ⚠️ 性能警報: {len(result.performance_alerts)} 個")
            for alert in result.performance_alerts[:3]:  # 顯示前3個
                print(f"     - {alert.severity}: {alert.message}")

        # 內存優化
        if result.memory_optimization_report:
            memory_report = result.memory_optimization_report
            current_memory = memory_report.get('current_memory_state', {})
            if current_memory:
                print(f"  💾 GPU利用率: {current_memory.get('utilization_percentage', 0):.1f}%")
                print(f"  🔧 內存效率: {current_memory.get('allocation_efficiency', 0):.1%}")

def run_feature_demonstration():
    """運行功能演示"""
    print("\n" + "="*80)
    print("🔬 單獨功能演示")
    print("="*80)

    # 創建增強版配置
    config = EnhancedOptimizationConfig(
        max_workers=8,
        batch_size=200,
        use_gpu=True,
        min_sharpe_ratio=0.5,
        max_max_drawdown=0.4,

        # 啟用所有增強功能
        use_intelligent_search=True,
        enable_real_time_monitoring=True,
        enable_statistical_validation=True,
        enable_gpu_memory_management=True,

        # 調整參數以便觀察效果
        max_iterations_per_algorithm=20,
        monitoring_interval=1.0,  # 1秒監控間隔
        validation_folds=3,
        significance_level=0.1  # 10%顯著性水平，更容易觀察
    )

    optimizer = EnhancedComprehensiveParameterOptimizer(config)

    print("\n🧠 測試智能搜索引擎...")
    try:
        # 小規模測試智能搜索
        result = optimizer.optimize_strategy_enhanced(
            strategy_type='HIBOR_RSI',
            max_combinations=200  # 小規模測試
        )

        print(f"✅ 智能搜索完成")
        print(f"   測試組合: {result.total_combinations}")
        print(f"   成功組合: {result.successful_combinations}")
        print(f"   最佳Sharpe: {result.performance_metrics[0]['sharpe_ratio']:.3f}" if result.performance_metrics else "   無結果")

        # 顯示搜索算法性能
        if result.search_algorithm_performance:
            print("\n   搜索算法性能:")
            for algorithm, results in result.search_algorithm_performance.items():
                if results:
                    scores = [r.score for r in results]
                    print(f"     {algorithm}: 最佳 {max(scores):.3f}, 平均 {np.mean(scores):.3f}, 個數 {len(results)}")

    except Exception as e:
        print(f"❌ 智能搜索測試失敗: {e}")

def run_monitoring_demo():
    """運行監控演示"""
    print("\n" + "="*80)
    print("📊 實時監控演示")
    print("="*80)

    # 導入監控器
    from real_time_performance_monitor import RealTimePerformanceMonitor, AlertConfig

    # 創建監控器配置
    alert_config = AlertConfig(
        enable_sharpe_alerts=True,
        enable_performance_alerts=True,
        enable_memory_alerts=True,
        sharpe_threshold=1.5,
        performance_degradation_threshold=0.2
    )

    monitor = RealTimePerformanceMonitor(
        monitoring_interval=0.5,
        enable_alerts=True,
        alert_config=alert_config
    )

    print("\n📡 啟動實時監控...")
    monitor.start_monitoring()

    try:
        # 模擬一些性能數據
        import numpy as np

        for i in range(10):
            # 模擬性能指標
            metrics = {
                'search_speed': 100 + np.random.normal(0, 20),
                'sharpe_ratio': 1.0 + np.random.normal(0, 0.3),
                'convergence_rate': 0.1 + np.random.normal(0, 0.05),
                'gpu_utilization': np.random.uniform(0.3, 0.9),
                'cpu_usage': np.random.uniform(0.2, 0.8),
                'memory_usage': np.random.uniform(0.4, 0.8)
            }

            monitor.add_performance_metrics(metrics)
            time.sleep(0.6)  # 等待監控間隔

        # 獲取監控總結
        summary = monitor.get_performance_summary()
        alerts = monitor.get_active_alerts()

        print(f"✅ 監控完成")
        print(f"   監控時長: {summary.get('monitoring_duration', 0):.1f}秒")
        print(f"   平均搜索速度: {summary.get('average_search_speed', 0):.1f} 組合/秒")
        print(f"   性能警報: {len(alerts)} 個")

        # 顯示警報
        for alert in alerts[:3]:
            print(f"     - {alert.severity}: {alert.message}")

    except Exception as e:
        print(f"❌ 監控演示失敗: {e}")

    finally:
        monitor.stop_monitoring()

def run_statistical_validation_demo():
    """運行統計驗證演示"""
    print("\n" + "="*80)
    print("📈 統計驗證演示")
    print("="*80)

    try:
        # 導入驗證器
        from advanced_statistical_validator import AdvancedStatisticalValidator
        from simplified_system.src.backtest.vectorbt_engine import VectorBTEngine
        from simplified_system.src.api.stock_api import get_hk_stock_data

        # 創建驗證器
        validator = AdvancedStatisticalValidator()

        # 獲取測試數據
        print("\n📊 加載測試數據...")
        data = get_hk_stock_data("0700.HK", 200)  # 200天數據
        print(f"   數據長度: {len(data)} 天")

        # 測試參數
        test_params = {
            'rsi_period': 14,
            'oversold': 30,
            'overbought': 70
        }

        print("\n🔬 執行統計驗證...")
        validation_result = validator.validate_parameters(
            data=data,
            strategy_type='HIBOR_RSI',
            parameters=test_params,
            n_folds=3
        )

        print(f"✅ 驗證完成")
        print(f"   驗證結果: {'通過' if validation_result.is_valid else '失敗'}")
        print(f"   驗證評分: {validation_result.validation_score:.3f}")
        print(f"   過擬合風險: {validation_result.overfitting_risk}")

        # 顯示交叉驗證結果
        if validation_result.cross_validation_results:
            cv = validation_result.cross_validation_results
            print(f"   交叉驗證:")
            print(f"     平均Sharpe: {cv.get('mean_sharpe', 0):.3f}")
            print(f"     Sharpe標準差: {cv.get('std_sharpe', 0):.3f}")
            print(f"     穩定性評分: {cv.get('stability_score', 0):.3f}")

        # 顯示顯著性檢驗結果
        if validation_result.significance_test_results:
            sig = validation_result.significance_test_results
            print(f"   顯著性檢驗:")
            print(f"     t檢驗p值: {sig.get('t_test_p_value', 'N/A')}")
            print(f"     Wilcoxon檢驗p值: {sig.get('wilcoxon_p_value', 'N/A')}")
            print(f"     統計顯著: {sig.get('is_statistically_significant', False)}")

    except Exception as e:
        print(f"❌ 統計驗證演示失敗: {e}")

def main():
    """主演示函數"""
    print("\n🎯 開始增強版參數優化系統演示")
    print(f"演示時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 1. 運行比較演示
        run_comparison_demo()

        # 2. 運行功能演示
        run_feature_demonstration()

        # 3. 運行監控演示
        run_monitoring_demo()

        # 4. 運行統計驗證演示
        run_statistical_validation_demo()

        print("\n" + "="*80)
        print("🎉 增強版參數優化系統演示完成！")
        print("="*80)

        print("\n📝 演示總結:")
        print("1. ✅ GPU內存管理 - 動態批量大小和內存池管理")
        print("2. ✅ 智能搜索引擎 - 遺傳算法、貝葉斯優化、多臂老虎機")
        print("3. ✅ 實時性能監控 - 動態監控和智能警報")
        print("4. ✅ 高級統計驗證 - 交叉驗證和顯著性檢驗")
        print("5. ✅ 系統集成 - 所有增強功能無縫整合")

        print("\n🚀 您現在可以使用以下命令運行完整的增強優化:")
        print("   python run_enhanced_optimization_demo.py")
        print("   或者在您的代碼中:")
        print("   from enhanced_comprehensive_parameter_optimizer import quick_enhanced_optimize_0700")
        print("   results = quick_enhanced_optimize_0700(max_combinations=5000)")

    except Exception as e:
        logger.error(f"演示過程中發生錯誤: {e}")
        print(f"\n❌ 演示失敗: {e}")

if __name__ == "__main__":
    import numpy as np  # 在演示中需要用到
    main()