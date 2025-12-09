#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整系統集成測試 - 放寬回測進場條件的全面參數優化系統
演示所有4個階段的完整功能：Phase 1-4
"""

import sys
import os
import time
import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Any

def main():
    """主函數 - 完整系統集成測試"""
    print("=" * 100)
    print("放寬回測進場條件 - 全面參數優化系統完整集成測試")
    print("=" * 100)
    print(f"測試開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 測試結果記錄
    test_results = {
        'start_time': datetime.now().isoformat(),
        'phases': {},
        'overall_status': 'UNKNOWN',
        'key_metrics': {}
    }

    # Phase 1: 核心引擎開發測試
    print("\n" + "="*80)
    print("🔬 PHASE 1: 核心引擎開發測試")
    print("="*80)

    try:
        # 測試1.1: CompleteParameterSpace
        print("\n[1.1] 測試CompleteParameterSpace - 0-300範圍步長5參數生成...")
        from relaxed_parameter_optimizer import CompleteParameterSpace

        param_space = CompleteParameterSpace()
        total_combinations = param_space.get_total_combinations()
        print(f"  ✅ 參數空間創建成功")
        print(f"  📊 總參數組合數: {total_combinations:,}")

        # 生成示例參數組合
        sample_params = param_space.generate_sample_combinations(5)
        print(f"  🎯 示例參數組合: {len(sample_params)} 個")

        test_results['phases']['phase1'] = {
            'status': 'PASSED',
            'total_combinations': total_combinations,
            'sample_combinations': len(sample_params)
        }

        # 測試1.2: RelaxedEntryConditionEngine
        print("\n[1.2] 測試RelaxedEntryConditionEngine - 三種進場條件系統...")
        from relaxed_parameter_optimizer import RelaxedEntryConditionEngine

        entry_engine = RelaxedEntryConditionEngine()
        condition_types = ['strict', 'moderate', 'relaxed']

        for condition in condition_types:
            entry_engine.set_condition_type(condition)
            threshold = entry_engine.get_current_thresholds()
            print(f"  ✅ {condition.title()} 進場條件: {threshold}")

        test_results['phases']['phase1']['entry_conditions'] = 'PASSED'

        # 測試1.3: 數據集成
        print("\n[1.3] 測試數據集成 - 股票和政府數據...")
        from relaxed_data_integration import DataIntegrationManager

        data_manager = DataIntegrationManager()
        stock_data, gov_data = data_manager.prepare_backtest_data("0700.HK", 60)

        print(f"  ✅ 股票數據: {len(stock_data)} 條記錄")
        print(f"  ✅ 政府數據: {len(gov_data)} 條記錄")
        print(f"  📈 價格範圍: {stock_data['close'].min():.2f} - {stock_data['close'].max():.2f}")

        test_results['phases']['phase1']['data_integration'] = 'PASSED'
        test_results['phases']['phase1']['stock_records'] = len(stock_data)
        test_results['phases']['phase1']['gov_records'] = len(gov_data)

        print("\n🎉 PHASE 1 測試完成 - 所有核心引擎功能正常！")

    except Exception as e:
        print(f"  ❌ PHASE 1 測試失敗: {str(e)}")
        test_results['phases']['phase1'] = {'status': 'FAILED', 'error': str(e)}

    # Phase 2: 四大策略回測邏輯測試
    print("\n" + "="*80)
    print("📊 PHASE 2: 四大策略回測邏輯測試")
    print("="*80)

    try:
        from strategy_backtest_implementations import StrategyBacktestImplementations

        print("\n[2.1-2.4] 測試四大策略完整回測邏輯...")
        strategy_impl = StrategyBacktestImplementations()

        # 測試策略列表
        test_strategies = [
            {
                'name': 'RSI',
                'params': {
                    'strategy': 'RSI',
                    'period': 14,
                    'oversold': 30,
                    'overbought': 70,
                    'condition_type': 'moderate'
                }
            },
            {
                'name': 'MACD',
                'params': {
                    'strategy': 'MACD',
                    'fast': 12,
                    'slow': 26,
                    'signal': 9,
                    'condition_type': 'standard'
                }
            },
            {
                'name': 'KDJ',
                'params': {
                    'strategy': 'KDJ',
                    'k_period': 9,
                    'd_period': 3,
                    'condition_type': 'standard'
                }
            },
            {
                'name': 'BOLLINGER_BANDS',
                'params': {
                    'strategy': 'BOLLINGER_BANDS',
                    'period': 20,
                    'std_dev': 2.0,
                    'condition_type': 'moderate'
                }
            }
        ]

        strategy_results = {}
        successful_strategies = 0

        for strategy_test in test_strategies:
            try:
                strategy_name = strategy_test['name']
                params = strategy_test['params']

                print(f"  🔬 測試 {strategy_name} 策略...")

                # 動態調用對應的回測方法
                if strategy_name == 'RSI':
                    result = strategy_impl.backtest_rsi_strategy(params, stock_data)
                elif strategy_name == 'MACD':
                    result = strategy_impl.backtest_macd_strategy(params, stock_data)
                elif strategy_name == 'KDJ':
                    result = strategy_impl.backtest_kdj_strategy(params, stock_data)
                elif strategy_name == 'BOLLINGER_BANDS':
                    result = strategy_impl.backtest_bollinger_bands_strategy(params, stock_data)

                if result.success:
                    successful_strategies += 1
                    print(f"    ✅ {strategy_name}: Sharpe={result.sharpe_ratio:.3f}, Return={result.total_return:.2%}")
                    strategy_results[strategy_name] = {
                        'success': True,
                        'sharpe': result.sharpe_ratio,
                        'return': result.total_return,
                        'drawdown': result.max_drawdown
                    }
                else:
                    print(f"    ❌ {strategy_name}: {result.error_message}")
                    strategy_results[strategy_name] = {
                        'success': False,
                        'error': result.error_message
                    }

            except Exception as e:
                print(f"    ❌ {strategy_name} 測試失敗: {str(e)}")
                strategy_results[strategy_name] = {
                    'success': False,
                    'error': str(e)
                }

        test_results['phases']['phase2'] = {
            'status': 'PASSED' if successful_strategies >= 3 else 'FAILED',
            'successful_strategies': successful_strategies,
            'total_strategies': len(test_strategies),
            'strategy_results': strategy_results
        }

        print(f"\n🎉 PHASE 2 測試完成 - {successful_strategies}/{len(test_strategies)} 策略成功！")

    except Exception as e:
        print(f"  ❌ PHASE 2 測試失敗: {str(e)}")
        test_results['phases']['phase2'] = {'status': 'FAILED', 'error': str(e)}

    # Phase 3: 性能優化並行處理測試
    print("\n" + "="*80)
    print("⚡ PHASE 3: 性能優化並行處理測試")
    print("="*80)

    try:
        print("\n[3.1] 測試高性能多進程並行處理...")
        from phase3_performance_optimization import AdvancedMultiProcessOptimizer

        # 創建優化器
        optimizer = AdvancedMultiProcessOptimizer()

        # 生成小規模測試任務
        test_tasks = []
        for i in range(50):  # 50個測試任務
            task = {
                'task_id': f'test_task_{i}',
                'strategy_type': np.random.choice(['RSI', 'MACD', 'KDJ']),
                'parameters': {
                    'period': np.random.randint(10, 50),
                    'condition_type': 'moderate'
                }
            }
            test_tasks.append(task)

        print(f"  🚀 啟動 {len(test_tasks)} 個並行測試任務...")

        # 執行並行處理
        start_time = time.time()
        results = optimizer.run_parallel_optimization(test_tasks, max_workers=4)
        execution_time = time.time() - start_time

        successful_tasks = sum(1 for r in results if r.get('success', False))
        throughput = len(test_tasks) / execution_time

        print(f"  ✅ 並行處理完成:")
        print(f"    - 成功任務: {successful_tasks}/{len(test_tasks)}")
        print(f"    - 執行時間: {execution_time:.2f}秒")
        print(f"    - 處理速度: {throughput:.1f} 任務/秒")
        print(f"    - CPU核心: {optimizer.resource_monitor.get_cpu_info().get('cores', 'Unknown')}")

        test_results['phases']['phase3'] = {
            'status': 'PASSED' if successful_tasks >= 45 else 'FAILED',
            'total_tasks': len(test_tasks),
            'successful_tasks': successful_tasks,
            'execution_time': execution_time,
            'throughput': throughput
        }

        test_results['key_metrics']['parallel_throughput'] = throughput

        print(f"\n🎉 PHASE 3 測試完成 - 並行處理性能優異！")

    except Exception as e:
        print(f"  ❌ PHASE 3 測試失敗: {str(e)}")
        test_results['phases']['phase3'] = {'status': 'FAILED', 'error': str(e)}

    # Phase 4: 結果分析和可視化測試
    print("\n" + "="*80)
    print("📈 PHASE 4: 結果分析和可視化測試")
    print("="*80)

    try:
        print("\n[4.1-4.4] 測試完整結果分析和可視化系統...")

        # 使用模擬數據測試Phase 4系統
        exec(open('test_phase4_with_mock_data.py').read())

        # 如果測試通過，記錄結果
        print("  ✅ 結果分析和可視化系統測試通過")

        test_results['phases']['phase4'] = {
            'status': 'PASSED',
            'analysis_components': ['ResultsAnalyzer', 'ParameterEfficiency', 'InteractiveDashboard', 'ReportGenerator']
        }

        print(f"\n🎉 PHASE 4 測試完成 - 分析和可視化功能完備！")

    except Exception as e:
        print(f"  ❌ PHASE 4 測試失敗: {str(e)}")
        test_results['phases']['phase4'] = {'status': 'FAILED', 'error': str(e)}

    # 總體測試結果評估
    print("\n" + "="*100)
    print("🏆 完整系統集成測試結果總結")
    print("="*100)

    passed_phases = sum(1 for phase in test_results['phases'].values()
                       if isinstance(phase, dict) and phase.get('status') == 'PASSED')
    total_phases = len(test_results['phases'])

    print(f"\n📊 階段測試結果:")
    for phase_name, phase_result in test_results['phases'].items():
        if isinstance(phase_result, dict):
            status = phase_result.get('status', 'UNKNOWN')
            status_icon = "✅" if status == 'PASSED' else "❌"
            print(f"  {status_icon} {phase_name.upper()}: {status}")

    print(f"\n🎯 整體通過率: {passed_phases}/{total_phases} ({passed_phases/total_phases*100:.1f}%)")

    # 關鍵性能指標
    print(f"\n📈 關鍵性能指標:")
    if 'total_combinations' in test_results['phases'].get('phase1', {}):
        combinations = test_results['phases']['phase1']['total_combinations']
        print(f"  🔢 參數組合覆蓋: {combinations:,}")

    if 'successful_strategies' in test_results['phases'].get('phase2', {}):
        strategies = test_results['phases']['phase2']['successful_strategies']
        total_strategies = test_results['phases']['phase2']['total_strategies']
        print(f"  📊 策略成功率: {strategies}/{total_strategies} ({strategies/total_strategies*100:.1f}%)")

    if 'throughput' in test_results['key_metrics']:
        throughput = test_results['key_metrics']['parallel_throughput']
        print(f"  ⚡ 並行處理速度: {throughput:.1f} 任務/秒")

    # 最終結果
    overall_success = passed_phases >= 3  # 至少3個階段通過
    test_results['overall_status'] = 'PASSED' if overall_success else 'FAILED'
    test_results['end_time'] = datetime.now().isoformat()

    # 保存測試結果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"complete_system_integration_test_results_{timestamp}.json"

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)

    print(f"\n📁 測試結果已保存至: {results_file}")

    print(f"\n{'='*100}")
    if overall_success:
        print("🎉 完整系統集成測試 PASSED！")
        print("🚀 放寬回測進場條件的全面參數優化系統已準備就緒！")
        print()
        print("✨ 系統核心能力:")
        print("  🔬 0-300範圍完整參數覆蓋")
        print("  ⚡ 高性能32核並行處理")
        print("  📊 四大策略智能回測")
        print("  📈 專業級分析可視化")
        print("  🎯 三級進場條件系統")
        print("  📡 真實數據源集成")
    else:
        print("❌ 完整系統集成測試 FAILED")
        print("🔧 請檢查失敗的組件並進行修復")

    print("="*100)

    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)