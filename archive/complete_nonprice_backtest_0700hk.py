#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整非價格數據技術分析回測 - 0700.HK 騰訊專用
使用完整的Phase 1-4系統進行綜合回測分析
"""

import pandas as pd
import numpy as np
import json
import time
from datetime import datetime, timedelta
import sys
import os

def load_real_0700_data():
    """加載0700.HK真實數據"""
    print("[DATA] 正在加載0700.HK真實數據...")

    try:
        # 1. 加載股票數據
        from relaxed_data_integration import DataIntegrationManager
        data_manager = DataIntegrationManager()

        # 獲取2年數據以進行完整回測
        stock_data, gov_data = data_manager.prepare_backtest_data("0700.HK", 730)  # 2年數據

        print(f"  [OK] 股票數據: {len(stock_data)} 條記錄")
        print(f"  [OK] 政府數據: {len(gov_data)} 條記錄")
        print(f"  [OK] 價格範圍: {stock_data['close'].min():.2f} - {stock_data['close'].max():.2f} HKD")
        print(f"  [OK] 時間範圍: {stock_data.index[0].date()} 至 {stock_data.index[-1].date()}")

        return stock_data, gov_data

    except Exception as e:
        print(f"  [FAIL] 數據加載失敗: {str(e)}")
        # 生成模擬數據作為備用
        return generate_mock_0700_data()

def generate_mock_0700_data():
    """生成0700.HK模擬數據"""
    print("[DATA] 生成0700.HK模擬數據...")

    # 生成2年的每日數據
    dates = pd.date_range(end=datetime.now(), periods=730, freq='D')

    # 基於騰訊真實價格範圍生成模擬數據
    initial_price = 450.0
    returns = np.random.normal(0.0008, 0.025, len(dates))  # 稍微正向的日回報
    prices = [initial_price]

    for i in range(1, len(dates)):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(new_price)

    # 創建OHLCV數據
    volatility = 0.025
    stock_data = pd.DataFrame({
        'open': [p * (1 + np.random.normal(0, volatility * 0.3)) for p in prices],
        'high': [p * (1 + abs(np.random.normal(0, volatility * 0.5))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, volatility * 0.5))) for p in prices],
        'close': prices,
        'volume': [int(np.random.uniform(10000000, 25000000)) for _ in dates]
    }, index=dates)

    # 確保OHLC邏輯正確
    stock_data['high'] = np.maximum(stock_data['high'], np.maximum(stock_data['open'], stock_data['close']))
    stock_data['low'] = np.minimum(stock_data['low'], np.minimum(stock_data['open'], stock_data['close']))

    # 生成模擬政府數據
    gov_data = pd.DataFrame({
        'hibor_rate': np.random.uniform(2.5, 5.5, len(dates)),
        'monetary_base': np.random.uniform(1800000, 2000000, len(dates)),
        'exchange_rate': np.random.uniform(7.7, 7.9, len(dates))
    }, index=dates)

    print(f"  [OK] 模擬股票數據: {len(stock_data)} 條記錄")
    print(f"  [OK] 模擬政府數據: {len(gov_data)} 條記錄")
    print(f"  [OK] 模擬價格範圍: {stock_data['close'].min():.2f} - {stock_data['close'].max():.2f} HKD")

    return stock_data, gov_data

def run_phase1_parameter_optimization(stock_data, gov_data):
    """Phase 1: 參數空間優化"""
    print("\n" + "="*80)
    print("PHASE 1: 非價格數據參數空間優化")
    print("="*80)

    try:
        from relaxed_parameter_optimizer import CompleteParameterSpace, RelaxedEntryConditionEngine

        # 1. 初始化參數空間
        print("\n[1.1] 初始化完整參數空間...")
        param_space = CompleteParameterSpace()

        # 獲取參數範圍信息
        param_ranges = {
            'rsi': len(param_space.parameter_ranges['rsi_period']),
            'macd_fast': len(param_space.parameter_ranges['macd_fast']),
            'macd_slow': len(param_space.parameter_ranges['macd_slow']),
            'kdj_k': len(param_space.parameter_ranges['kdj_k']),
            'bb_period': len(param_space.parameter_ranges['bb_period'])
        }

        total_rsi_combinations = param_ranges['rsi'] * 2 * 2  # RSI * oversold * overbought
        total_macd_combinations = param_ranges['macd_fast'] * param_ranges['macd_slow'] * 4
        total_kdj_combinations = param_ranges['kdj_k'] * 4  # K period * D period

        print(f"  [OK] RSI參數組合: {total_rsi_combinations:,}")
        print(f"  [OK] MACD參數組合: {total_macd_combinations:,}")
        print(f"  [OK] KDJ參數組合: {total_kdj_combinations:,}")

        # 2. 配置進場條件
        print("\n[1.2] 配置放寬進場條件...")
        entry_engine = RelaxedEntryConditionEngine()

        # 測試三種進場條件
        conditions = ['strict', 'moderate', 'relaxed']
        for condition in conditions:
            entry_engine.set_condition_type(condition)
            thresholds = entry_engine.get_current_thresholds()
            print(f"  [OK] {condition.title()} 條件: RSI({thresholds.get('rsi_oversold', 'N/A')}-{thresholds.get('rsi_overbought', 'N/A')})")

        # 3. 生成測試參數組合 (為了演示，使用較小的子集)
        print("\n[1.3] 生成優化參數組合...")

        # 生成有代表性的參數組合
        test_combinations = []

        # RSI組合 (關鍵區間)
        rsi_periods = [5, 10, 14, 20, 30, 50, 100, 200]
        for period in rsi_periods:
            test_combinations.append({
                'strategy': 'RSI',
                'period': period,
                'oversold': 25,
                'overbought': 75,
                'condition_type': 'moderate'
            })

        # MACD組合
        macd_params = [
            (5, 35, 9), (8, 21, 9), (12, 26, 9),
            (10, 50, 12), (15, 40, 8)
        ]
        for fast, slow, signal in macd_params:
            test_combinations.append({
                'strategy': 'MACD',
                'fast': fast,
                'slow': slow,
                'signal': signal,
                'condition_type': 'standard'
            })

        # KDJ組合
        kdj_periods = [5, 9, 14, 21, 30]
        for k_period in kdj_periods:
            test_combinations.append({
                'strategy': 'KDJ',
                'k_period': k_period,
                'd_period': 3,
                'condition_type': 'standard'
            })

        # 布林帶組合
        bb_periods = [10, 20, 30, 50]
        for period in bb_periods:
            test_combinations.append({
                'strategy': 'BOLLINGER_BANDS',
                'period': period,
                'std_dev': 2.0,
                'condition_type': 'moderate'
            })

        print(f"  [OK] 生成 {len(test_combinations)} 個測試組合")

        return test_combinations, {
            'rsi_combinations': total_rsi_combinations,
            'macd_combinations': total_macd_combinations,
            'kdj_combinations': total_kdj_combinations,
            'test_combinations': len(test_combinations)
        }

    except Exception as e:
        print(f"  [FAIL] Phase 1 錯誤: {str(e)}")
        return [], {}

def run_phase2_strategy_backtest(test_combinations, stock_data, gov_data):
    """Phase 2: 策略回測執行"""
    print("\n" + "="*80)
    print("PHASE 2: 非價格數據策略回測執行")
    print("="*80)

    try:
        from strategy_backtest_implementations import StrategyBacktestImplementations

        strategy_impl = StrategyBacktestImplementations()
        backtest_results = []

        print(f"\n[2.1] 開始執行 {len(test_combinations)} 個策略回測...")

        successful_strategies = 0
        total_sharpe = 0
        max_sharpe = -999
        best_strategy = None

        for i, params in enumerate(test_combinations):
            try:
                strategy_type = params['strategy']
                print(f"  [{i+1}/{len(test_combinations)}] 測試 {strategy_type} 策略...")

                # 動態調用對應的回測方法
                if strategy_type == 'RSI':
                    result = strategy_impl.backtest_rsi_strategy(params, stock_data)
                elif strategy_type == 'MACD':
                    result = strategy_impl.backtest_macd_strategy(params, stock_data)
                elif strategy_type == 'KDJ':
                    result = strategy_impl.backtest_kdj_strategy(params, stock_data)
                elif strategy_type == 'BOLLINGER_BANDS':
                    result = strategy_impl.backtest_bollinger_bands_strategy(params, stock_data)

                if result.success:
                    successful_strategies += 1
                    total_sharpe += result.sharpe_ratio

                    if result.sharpe_ratio > max_sharpe:
                        max_sharpe = result.sharpe_ratio
                        best_strategy = {
                            'strategy': strategy_type,
                            'parameters': params,
                            'sharpe': result.sharpe_ratio,
                            'return': result.total_return,
                            'drawdown': result.max_drawdown,
                            'trades': result.trade_frequency
                        }

                    # 存儲結果
                    backtest_results.append({
                        'strategy_type': strategy_type,
                        'parameters': params,
                        'success': True,
                        'sharpe_ratio': result.sharpe_ratio,
                        'total_return': result.total_return,
                        'max_drawdown': result.max_drawdown,
                        'volatility': result.volatility,
                        'trade_frequency': result.trade_frequency,
                        'trade_count': result.trade_count
                    })

                    print(f"    [OK] Sharpe: {result.sharpe_ratio:.3f}, Return: {result.total_return:.2%}")
                else:
                    print(f"    [SKIP] 策略失敗: {result.error_message}")
                    backtest_results.append({
                        'strategy_type': strategy_type,
                        'parameters': params,
                        'success': False,
                        'error': result.error_message
                    })

            except Exception as e:
                print(f"    [ERROR] 回測錯誤: {str(e)}")
                backtest_results.append({
                    'strategy_type': params.get('strategy', 'Unknown'),
                    'parameters': params,
                    'success': False,
                    'error': str(e)
                })

        # 計算統計
        success_rate = successful_strategies / len(test_combinations) if test_combinations else 0
        avg_sharpe = total_sharpe / successful_strategies if successful_strategies > 0 else 0

        print(f"\n[2.2] 回測結果統計:")
        print(f"  [OK] 成功策略: {successful_strategies}/{len(test_combinations)} ({success_rate:.1%})")
        print(f"  [OK] 平均Sharpe: {avg_sharpe:.3f}")
        print(f"  [OK] 最高Sharpe: {max_sharpe:.3f}")

        if best_strategy:
            print(f"  [OK] 最佳策略: {best_strategy['strategy']}")
            print(f"      參數: {best_strategy['parameters']}")
            print(f"      Sharpe: {best_strategy['sharpe']:.3f}")
            print(f"      Return: {best_strategy['return']:.2%}")
            print(f"      Max DD: {best_strategy['drawdown']:.2%}")

        return backtest_results, {
            'total_strategies': len(test_combinations),
            'successful_strategies': successful_strategies,
            'success_rate': success_rate,
            'avg_sharpe': avg_sharpe,
            'max_sharpe': max_sharpe,
            'best_strategy': best_strategy
        }

    except Exception as e:
        print(f"  [FAIL] Phase 2 錯誤: {str(e)}")
        return [], {}

def run_phase3_parallel_optimization(stock_data):
    """Phase 3: 並行優化處理"""
    print("\n" + "="*80)
    print("PHASE 3: 高性能並行優化處理")
    print("="*80)

    try:
        from phase3_performance_optimization import AdvancedMultiProcessOptimizer

        print("\n[3.1] 初始化高性能並行優化器...")
        optimizer = AdvancedMultiProcessOptimizer()

        # 生成大規模測試任務
        print("[3.2] 生成大規模並行任務...")

        parallel_tasks = []
        # 生成更多RSI任務進行並行測試
        for i in range(100):
            task = {
                'task_id': f'parallel_rsi_task_{i}',
                'strategy_type': 'RSI',
                'parameters': {
                    'period': 5 + (i % 30),  # 5-34週期
                    'oversold': 20 + (i % 20),  # 20-39
                    'overbought': 60 + (i % 25),  # 60-84
                    'condition_type': 'moderate'
                },
                'data': stock_data
            }
            parallel_tasks.append(task)

        print(f"  [OK] 生成 {len(parallel_tasks)} 個並行任務")

        # 執行並行優化
        print("\n[3.3] 執行並行優化處理...")
        start_time = time.time()

        # 使用較少的worker避免資源問題
        results = optimizer.optimize_strategies(
            parallel_tasks[:50],  # 限制到50個任務
            max_workers=8,  # 使用8個worker
            timeout=30
        )

        execution_time = time.time() - start_time

        # 分析並行結果
        successful_tasks = sum(1 for r in results if r.get('success', False))
        failed_tasks = len(results) - successful_tasks
        throughput = len(results) / execution_time if execution_time > 0 else 0

        print(f"\n[3.4] 並行優化結果:")
        print(f"  [OK] 成功任務: {successful_tasks}/{len(results)}")
        print(f"  [OK] 失敗任務: {failed_tasks}")
        print(f"  [OK] 執行時間: {execution_time:.2f}秒")
        print(f"  [OK] 處理速度: {throughput:.1f} 任務/秒")

        # 計算並行Sharpe統計
        parallel_sharpes = [r.get('sharpe_ratio', 0) for r in results if r.get('success', False) and r.get('sharpe_ratio') is not None]
        if parallel_sharpes:
            avg_parallel_sharpe = np.mean(parallel_sharpes)
            max_parallel_sharpe = np.max(parallel_sharpes)
            print(f"  [OK] 並行平均Sharpe: {avg_parallel_sharpe:.3f}")
            print(f"  [OK] 並行最高Sharpe: {max_parallel_sharpe:.3f}")

        return results, {
            'total_parallel_tasks': len(results),
            'successful_parallel_tasks': successful_tasks,
            'parallel_throughput': throughput,
            'execution_time': execution_time,
            'avg_parallel_sharpe': avg_parallel_sharpe if parallel_sharpes else 0,
            'max_parallel_sharpe': max_parallel_sharpe if parallel_sharpes else 0
        }

    except Exception as e:
        print(f"  [FAIL] Phase 3 錯誤: {str(e)}")
        return [], {}

def run_phase4_analysis_visualization(backtest_results, parallel_results):
    """Phase 4: 結果分析和可視化"""
    print("\n" + "="*80)
    print("PHASE 4: 結果分析和可視化")
    print("="*80)

    try:
        # 1. 基本統計分析
        print("\n[4.1] 基本統計分析...")

        successful_results = [r for r in backtest_results if r.get('success', False)]

        if successful_results:
            sharpe_values = [r['sharpe_ratio'] for r in successful_results]
            return_values = [r['total_return'] for r in successful_results]
            drawdown_values = [r['max_drawdown'] for r in successful_results]

            analysis_stats = {
                'total_analyzed': len(successful_results),
                'sharpe_stats': {
                    'mean': np.mean(sharpe_values),
                    'std': np.std(sharpe_values),
                    'min': np.min(sharpe_values),
                    'max': np.max(sharpe_values),
                    'median': np.median(sharpe_values)
                },
                'return_stats': {
                    'mean': np.mean(return_values),
                    'std': np.std(return_values),
                    'min': np.min(return_values),
                    'max': np.max(return_values)
                },
                'drawdown_stats': {
                    'mean': np.mean(drawdown_values),
                    'worst': np.min(drawdown_values),
                    'best': np.max(drawdown_values)
                }
            }

            print(f"  [OK] 分析策略數: {analysis_stats['total_analyzed']}")
            print(f"  [OK] Sharpe統計: 均值={analysis_stats['sharpe_stats']['mean']:.3f}, 標準差={analysis_stats['sharpe_stats']['std']:.3f}")
            print(f"  [OK] 回報統計: 均值={analysis_stats['return_stats']['mean']:.2%}, 標準差={analysis_stats['return_stats']['std']:.2%}")
            print(f"  [OK] 回撤統計: 平均={analysis_stats['drawdown_stats']['mean']:.2%}, 最差={analysis_stats['drawdown_stats']['worst']:.2%}")
        else:
            analysis_stats = {}
            print("  [WARN] 沒有成功的策略結果可供分析")

        # 2. 策略類型分析
        print("\n[4.2] 策略類型性能分析...")

        strategy_performance = {}
        for result in successful_results:
            strategy_type = result['strategy_type']
            if strategy_type not in strategy_performance:
                strategy_performance[strategy_type] = []
            strategy_performance[strategy_type].append(result['sharpe_ratio'])

        for strategy_type, sharpes in strategy_performance.items():
            avg_sharpe = np.mean(sharpes)
            max_sharpe = np.max(sharpes)
            count = len(sharpes)
            print(f"  [OK] {strategy_type}: 平均={avg_sharpe:.3f}, 最高={max_sharpe:.3f}, 數量={count}")

        # 3. 參數效率分析 (簡化版)
        print("\n[4.3] 關鍵參數效率分析...")

        # RSI週期效率
        rsi_results = [r for r in successful_results if r['strategy_type'] == 'RSI']
        if rsi_results:
            rsi_periods = [r['parameters']['period'] for r in rsi_results]
            rsi_sharpes = [r['sharpe_ratio'] for r in rsi_results]

            # 找到最佳RSI週期範圍
            best_rsi_idx = np.argmax(rsi_sharpes)
            best_rsi_period = rsi_periods[best_rsi_idx]
            best_rsi_sharpe = rsi_sharpes[best_rsi_idx]

            print(f"  [OK] 最佳RSI週期: {best_rsi_period} (Sharpe: {best_rsi_sharpe:.3f})")

        # 4. 風險回報分析
        print("\n[4.4] 風險回報分析...")

        if successful_results:
            # 計算風險調整回報
            risk_adjusted_returns = []
            for result in successful_results:
                if result['max_drawdown'] < 0:  # 避免除零
                    risk_adj_return = result['total_return'] / abs(result['max_drawdown'])
                    risk_adjusted_returns.append(risk_adj_return)

            if risk_adjusted_returns:
                avg_risk_adj = np.mean(risk_adjusted_returns)
                print(f"  [OK] 平均風險調整回報: {avg_risk_adj:.2f}")

        return {
            'analysis_stats': analysis_stats,
            'strategy_performance': strategy_performance,
            'total_successful': len(successful_results),
            'analysis_timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        print(f"  [FAIL] Phase 4 錯誤: {str(e)}")
        return {}

def generate_comprehensive_report(phase1_data, phase2_data, phase2_results, phase3_data, phase4_data):
    """生成綜合分析報告"""
    print("\n" + "="*80)
    print("生成0700.HK非價格數據技術分析綜合報告")
    print("="*80)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 綜合報告數據
    comprehensive_report = {
        'report_info': {
            'stock': '0700.HK',
            'company': 'Tencent Holdings Limited',
            'report_type': 'Non-Price Data Technical Analysis',
            'generated_at': datetime.now().isoformat(),
            'data_period': '2 Years',
            'analysis_phases': 4
        },
        'phase1_parameter_optimization': phase1_data,
        'phase2_strategy_backtest': phase2_data,
        'phase3_parallel_optimization': phase3_data,
        'phase4_analysis_visualization': phase4_data,
        'key_findings': {},
        'recommendations': []
    }

    # 關鍵發現
    print("\n[REPORT] 提取關鍵發現...")

    key_findings = []

    if phase2_data.get('best_strategy'):
        best = phase2_data['best_strategy']
        key_findings.append(f"最佳策略: {best['strategy']} (Sharpe: {best['sharpe']:.3f})")
        key_findings.append(f"最高回報: {best['return']:.2%}")
        key_findings.append(f"風險控制: 最大回撤 {best['drawdown']:.2%}")

    if phase2_data.get('success_rate', 0) > 0.5:
        key_findings.append(f"策略成功率: {phase2_data['success_rate']:.1%}")

    if phase3_data.get('max_parallel_sharpe', 0) > 1.0:
        key_findings.append(f"並行優化發現高Sharpe策略: {phase3_data['max_parallel_sharpe']:.3f}")

    comprehensive_report['key_findings'] = key_findings

    # 建議
    recommendations = []

    if phase2_data.get('max_sharpe', 0) > 1.5:
        recommendations.append("發現高Sharpe策略，建議進行實際驗證")

    if phase2_data.get('success_rate', 0) > 0.7:
        recommendations.append("策略整體表現良好，可考慮實際部署")
    else:
        recommendations.append("建議優化策略參數以提高成功率")

    if phase3_data.get('parallel_throughput', 0) > 10:
        recommendations.append("並行處理效率優異，可擴展更大規模優化")

    comprehensive_report['recommendations'] = recommendations

    # 保存報告
    report_file = f"0700_hk_nonprice_ta_analysis_report_{timestamp}.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_report, f, ensure_ascii=False, indent=2)

    print(f"  [OK] 綜合報告已保存: {report_file}")

    # 打印關鍵發現
    print(f"\n[REPORT] 關鍵發現:")
    for i, finding in enumerate(key_findings, 1):
        print(f"  {i}. {finding}")

    print(f"\n[REPORT] 主要建議:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")

    return report_file, comprehensive_report

def main():
    """主函數 - 完整0700.HK非價格數據回測"""
    print("=" * 100)
    print("0700.HK 騰訊 - 非價格數據技術分析完整回測系統")
    print("=" * 100)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    start_time = time.time()

    try:
        # 加載數據
        stock_data, gov_data = load_real_0700_data()

        if stock_data.empty:
            print("[ERROR] 無法加載股票數據，退出")
            return False

        # Phase 1: 參數優化
        test_combinations, phase1_data = run_phase1_parameter_optimization(stock_data, gov_data)

        if not test_combinations:
            print("[ERROR] 無法生成測試組合，退出")
            return False

        # Phase 2: 策略回測
        backtest_results, phase2_data = run_phase2_strategy_backtest(test_combinations, stock_data, gov_data)

        # Phase 3: 並行優化
        parallel_results, phase3_data = run_phase3_parallel_optimization(stock_data)

        # Phase 4: 分析可視化
        phase4_data = run_phase4_analysis_visualization(backtest_results, parallel_results)

        # 生成綜合報告
        report_file, comprehensive_report = generate_comprehensive_report(
            phase1_data, phase2_data, backtest_results, phase3_data, phase4_data
        )

        # 總結
        total_time = time.time() - start_time

        print("\n" + "="*100)
        print("0700.HK 非價格數據技術分析回測完成")
        print("="*100)

        print(f"\n[SUMMARY] 執行總結:")
        print(f"  執行時間: {total_time:.2f}秒")
        print(f"  股票數據: {len(stock_data)} 天")
        print(f"  測試策略: {len(test_combinations)} 個")
        print(f"  成功策略: {phase2_data.get('successful_strategies', 0)} 個")
        print(f"  成功率: {phase2_data.get('success_rate', 0):.1%}")
        print(f"  最高Sharpe: {phase2_data.get('max_sharpe', 0):.3f}")
        print(f"  並行處理: {phase3_data.get('parallel_throughput', 0):.1f} 任務/秒")

        print(f"\n[SUMMARY] 綜合報告: {report_file}")

        # 判斷整體成功
        overall_success = (
            phase2_data.get('success_rate', 0) > 0.3 and  # 至少30%成功率
            phase2_data.get('max_sharpe', 0) > 0.5 and     # 最高Sharpe > 0.5
            len(backtest_results) > 0                      # 有回測結果
        )

        if overall_success:
            print(f"\n[SUCCESS] 0700.HK非價格數據技術分析回測成功完成！")
            print("系統發現了有價值的交易策略和參數組合。")
        else:
            print(f"\n[WARNING] 回測結果不理想，建議調整策略參數。")

        return overall_success

    except Exception as e:
        print(f"\n[FATAL] 系統錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)