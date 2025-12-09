#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整參數優化腳本 - 可視化結果
運行方式: python run_full_optimization.py
"""

import time
import json
from datetime import datetime

print("=== 0700.HK 完整參數優化 ===")
print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

try:
    # 導入優化器
    from enhanced_comprehensive_parameter_optimizer import EnhancedComprehensiveParameterOptimizer, EnhancedOptimizationConfig
    print("[1/6] 導入優化器成功")

    # 配置參數 - 新手友好設置
    config = EnhancedOptimizationConfig(
        max_workers=4,                     # 使用4個線程
        batch_size=50,                     # 每批50個組合
        use_gpu=False,                     # 暫時不用GPU避免問題
        min_sharpe_ratio=0.0,              # 降低篩選條件
        max_max_drawdown=1.0,               # 放寬回撤限制
        min_win_rate=0.0,                  # 降低勝率要求

        # 增強功能配置
        use_intelligent_search=False,       # 暫時關閉以保穩定
        enable_real_time_monitoring=False,   # 暫時關閉監控
        enable_statistical_validation=False, # 暫時關閉統計驗證
        enable_gpu_memory_management=False,  # 暫時關閉GPU內存管理
    )
    print("[2/6] 配置創建成功")

    # 創建優化器
    optimizer = EnhancedComprehensiveParameterOptimizer(config)
    print("[3/6] 優化器創建成功")

    # 分析參數空間
    spaces = optimizer.define_parameter_spaces()
    total_combinations = sum(space.total_combinations for space in spaces.values())

    print("\n📊 參數空間分析:")
    print("-" * 50)
    for strategy, space in spaces.items():
        print(f"{strategy:15} : {space.total_combinations:,} 組合")
    print("-" * 50)
    print(f"{'總計':15} : {total_combinations:,} 組合")

    # 設置優化規模
    max_combinations_per_strategy = min(5000, total_combinations // 2)  # 最多5000個
    print(f"\n🎯 優化規模: 每個策略最多 {max_combinations_per_strategy:,} 個組合")
    print(f"📐 總共最多測試: {max_combinations_per_strategy * 2:,} 個組合")

    # 執行優化
    print("\n🚀 開始完整參數優化...")
    print("=" * 60)

    optimization_start = time.time()

    # 執行兩個策略的優化
    results = optimizer.run_enhanced_comprehensive_optimization(
        symbol="0700.HK",
        data_period=365,  # 使用一年數據
        max_combinations_per_strategy=max_combinations_per_strategy
    )

    optimization_time = time.time() - optimization_start

    print("=" * 60)
    print(f"✅ 優化完成! 耗時: {optimization_time:.2f}秒")
    print()

    # 顯示結果
    if results:
        print("📈 優化結果詳情:")
        print("=" * 80)

        for i, (strategy, result) in enumerate(results.items(), 1):
            print(f"\n🏆 {i}. {strategy} 策略")
            print("-" * 40)

            if hasattr(result, 'performance_metrics') and result.performance_metrics:
                # 顯示前3個最佳結果
                for j, metrics in enumerate(result.performance_metrics[:3], 1):
                    sharpe = metrics.get('sharpe_ratio', 0)
                    drawdown = metrics.get('max_drawdown', 0) * 100
                    win_rate = metrics.get('win_rate', 0) * 100
                    total_return = metrics.get('total_return', 0) * 100

                    print(f"  {j}. Sharpe: {sharpe:6.3f} | 回撤: {drawdown:6.2f}% | 勝率: {win_rate:5.1f}% | 回報: {total_return:6.2f}%")

                # 顯示最佳參數
                if hasattr(result, 'top_parameters') and result.top_parameters:
                    best_params = result.top_parameters[0]
                    print(f"  🔧 最佳參數: {best_params}")
            else:
                print("  ❌ 無有效結果")

        # 統計信息
        print("\n📊 優化統計:")
        print("-" * 40)

        total_tested = sum(result.successful_combinations if hasattr(result, 'successful_combinations') else 0 for result in results.values())
        success_rate = (total_tested / (max_combinations_per_strategy * 2)) * 100 if max_combinations_per_strategy > 0 else 0
        avg_speed = total_tested / optimization_time if optimization_time > 0 else 0

        print(f"總測試組合: {total_tested:,}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"處理速度: {avg_speed:.1f} 組合/秒")

        # 找出最佳策略
        best_sharpe = -999
        best_strategy = None
        best_params = None

        for strategy, result in results.items():
            if hasattr(result, 'performance_metrics') and result.performance_metrics:
                current_sharpe = result.performance_metrics[0].get('sharpe_ratio', 0)
                if current_sharpe > best_sharpe:
                    best_sharpe = current_sharpe
                    best_strategy = strategy
                    if hasattr(result, 'top_parameters') and result.top_parameters:
                        best_params = result.top_parameters[0]

        if best_strategy:
            print(f"\n🏅 最優策略: {best_strategy}")
            print(f"   最佳 Sharpe: {best_sharpe:.3f}")
            if best_params:
                print(f"   最佳參數: {best_params}")

        # 保存結果到文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_filename = f"optimization_results_{timestamp}.json"

        # 準備保存的數據
        save_data = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'max_workers': config.max_workers,
                'batch_size': config.batch_size,
                'use_gpu': config.use_gpu,
                'max_combinations_per_strategy': max_combinations_per_strategy
            },
            'optimization_time': optimization_time,
            'total_tested': total_tested,
            'success_rate': success_rate,
            'best_strategy': best_strategy,
            'best_sharpe': best_sharpe,
            'results': {}
        }

        # 添加結果詳情
        for strategy, result in results.items():
            save_data['results'][strategy] = {
                'successful_combinations': result.successful_combinations if hasattr(result, 'successful_combinations') else 0,
                'total_combinations': result.total_combinations if hasattr(result, 'total_combinations') else 0,
                'optimization_time': result.optimization_time if hasattr(result, 'optimization_time') else 0,
                'top_parameters': result.top_parameters[:5] if hasattr(result, 'top_parameters') else [],
                'performance_metrics': result.performance_metrics[:10] if hasattr(result, 'performance_metrics') else []
            }

        # 保存文件
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 結果已保存: {result_filename}")

        # 生成簡單的可視化報告
        report_filename = f"optimization_report_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("0700.HK 參數優化報告\n")
            f.write("=" * 50 + "\n")
            f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"優化耗時: {optimization_time:.2f}秒\n")
            f.write(f"總測試組合: {total_tested:,}\n")
            f.write(f"成功率: {success_rate:.1f}%\n")
            f.write(f"處理速度: {avg_speed:.1f} 組合/秒\n\n")

            f.write("策略排名:\n")
            f.write("-" * 30 + "\n")
            rank = 1
            for strategy, result in results.items():
                if hasattr(result, 'performance_metrics') and result.performance_metrics:
                    sharpe = result.performance_metrics[0].get('sharpe_ratio', 0)
                    f.write(f"{rank}. {strategy}: Sharpe {sharpe:.3f}\n")
                    rank += 1

            if best_params:
                f.write(f"\n最優參數組合:\n")
                f.write(f"策略: {best_strategy}\n")
                f.write(f"Sharpe: {best_sharpe:.3f}\n")
                f.write(f"參數: {best_params}\n")

        print(f"📄 報告已生成: {report_filename}")

    else:
        print("❌ 優化失敗 - 未獲得結果")

except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    print("請確保在正確的項目目錄中運行此腳本")
except Exception as e:
    print(f"❌ 執行錯誤: {e}")
    import traceback
    traceback.print_exc()

print(f"\n🎯 腳本執行完成於: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")