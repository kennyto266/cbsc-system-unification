#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 2 完整策略測試 - 四大策略集成驗證
測試所有策略類型的完整實現和集成

核心測試:
1. RSI策略完整回測實現
2. MACD策略完整回測實現
3. KDJ策略完整回測實現
4. 布林帶策略完整回測實現
5. 多策略並行處理性能測試

作者: Claude Code Assistant
日期: 2025-11-24
"""

import pandas as pd
import numpy as np
import time
import json
from datetime import datetime
from typing import Dict, List, Any

# 導入核心組件
from relaxed_parameter_optimizer import (
    CompleteParameterSpace,
    AdvancedMultiProcessBacktestEngine
)
from relaxed_data_integration import DataIntegrationManager
from strategy_backtest_implementations import StrategyBacktestImplementations


class Phase2CompleteStrategyTest:
    """Phase 2 完整策略測試類"""

    def __init__(self):
        print("="*80)
        print("PHASE 2 COMPLETE STRATEGY TEST")
        print("四大策略集成驗證")
        print("="*80)

        # 初始化所有組件
        self.param_space = CompleteParameterSpace()
        self.backtest_engine = AdvancedMultiProcessBacktestEngine()
        self.data_manager = DataIntegrationManager()
        self.strategy_impl = StrategyBacktestImplementations()

        print(f"[INIT] Phase 2 test components initialized successfully")

    def run_complete_strategy_test(self, stock_symbol: str = "0700.HK",
                                  test_duration_days: int = 180,
                                  max_strategies_per_type: int = 50) -> Dict[str, Any]:
        """
        運行完整策略測試

        Args:
            stock_symbol: 測試股票代碼
            test_duration_days: 測試數據天數
            max_strategies_per_type: 每種策略最大測試數量

        Returns:
            Dict: 測試結果
        """

        test_results = {
            'test_timestamp': datetime.now().isoformat(),
            'phase': 'Phase 2',
            'stock_symbol': stock_symbol,
            'test_duration_days': test_duration_days,
            'strategy_types_tested': [],
            'performance_metrics': {},
            'top_strategies_by_type': {},
            'overall_statistics': {},
            'errors': []
        }

        try:
            # 準備數據
            print(f"\n{'='*60}")
            print("STEP 1: DATA PREPARATION")
            print(f"{'='*60}")

            stock_data, gov_data = self.data_manager.prepare_backtest_data(
                stock_symbol, test_duration_days
            )

            if stock_data.empty:
                raise ValueError(f"Failed to load stock data for {stock_symbol}")

            test_results['data_quality'] = {
                'stock_records': len(stock_data),
                'date_range': f"{stock_data.index[0].date()} to {stock_data.index[-1].date()}",
                'price_range': f"{stock_data['close'].min():.2f} - {stock_data['close'].max():.2f}"
            }

            print(f"[DATA] Stock data loaded: {len(stock_data)} records")

            # 生成參數組合
            print(f"\n{'='*60}")
            print("STEP 2: PARAMETER SPACE GENERATION")
            print(f"{'='*60}")

            all_combinations = self.param_space.generate_all_combinations()

            # 限制每種策略的測試數量
            limited_combinations = {}
            for strategy_type, combos in all_combinations.items():
                limited_combinations[strategy_type] = combos[:max_strategies_per_type]
                print(f"[PARAM] {strategy_type}: {len(limited_combinations[strategy_type])} combinations")

            # 逐一測試每種策略類型
            print(f"\n{'='*60}")
            print("STEP 3: STRATEGY-BY-STRATEGY TESTING")
            print(f"{'='*60}")

            strategy_results = {}

            for strategy_type in ['RSI', 'MACD', 'KDJ', 'BOLLINGER_BANDS']:
                print(f"\n[TEST] Testing {strategy_type} strategies...")

                strategy_test_results = self._test_strategy_type(
                    strategy_type,
                    limited_combinations[strategy_type],
                    stock_data,
                    gov_data
                )

                strategy_results[strategy_type] = strategy_test_results
                test_results['strategy_types_tested'].append(strategy_type)

                # 顯示測試摘要
                self._display_strategy_summary(strategy_type, strategy_test_results)

            # 準備並運行多策略並行測試
            print(f"\n{'='*60}")
            print("STEP 4: MULTI-STRATEGY PARALLEL TESTING")
            print(f"{'='*60}")

            parallel_results = self._test_multi_strategy_parallel(
                limited_combinations, stock_data, gov_data
            )

            test_results['parallel_performance'] = parallel_results

            # 生成整體統計
            test_results['overall_statistics'] = self._calculate_overall_statistics(strategy_results)

            # 收集最佳策略
            test_results['top_strategies_by_type'] = self._extract_top_strategies(strategy_results)

            # 生成測試報告
            self._generate_phase2_report(test_results)

            return test_results

        except Exception as e:
            error_msg = f"Phase 2 test failed: {str(e)}"
            print(f"\n[ERROR] {error_msg}")
            test_results['errors'].append(error_msg)
            return test_results

    def _test_strategy_type(self, strategy_type: str, combinations: List[Dict],
                           stock_data: pd.DataFrame, gov_data: Dict) -> Dict[str, Any]:
        """測試單個策略類型"""

        results = {
            'strategy_type': strategy_type,
            'total_combinations': len(combinations),
            'successful_strategies': 0,
            'failed_strategies': 0,
            'execution_time': 0,
            'performance_stats': {},
            'top_strategies': [],
            'errors': []
        }

        start_time = time.time()

        try:
            strategy_performance = []
            successful_results = []
            failed_results = []

            # 測試每個策略組合
            for i, combo in enumerate(combinations):
                try:
                    # 根據策略類型執行相應的回測
                    if strategy_type == 'RSI':
                        result = self.strategy_impl.backtest_rsi_strategy(combo, stock_data)
                    elif strategy_type == 'MACD':
                        result = self.strategy_impl.backtest_macd_strategy(combo, stock_data)
                    elif strategy_type == 'KDJ':
                        result = self.strategy_impl.backtest_kdj_strategy(combo, stock_data)
                    elif strategy_type == 'BOLLINGER_BANDS':
                        result = self.strategy_impl.backtest_bollinger_bands_strategy(combo, stock_data)
                    else:
                        continue

                    if result.success:
                        successful_results.append(result)
                        strategy_performance.append({
                            'strategy_name': result.strategy_name,
                            'sharpe_ratio': result.sharpe_ratio,
                            'total_return': result.total_return,
                            'max_drawdown': result.max_drawdown,
                            'trade_frequency': result.trade_frequency,
                            'quality_score': result.quality_score
                        })
                    else:
                        failed_results.append(result)

                except Exception as e:
                    failed_results.append({
                        'strategy_name': f"{strategy_type}_error_{i}",
                        'error': str(e)
                    })

                # 進度報告
                if (i + 1) % 10 == 0:
                    progress = (i + 1) / len(combinations) * 100
                    print(f"  Progress: {progress:.1f}% ({i+1}/{len(combinations)})")

            # 計算統計數據
            results['successful_strategies'] = len(successful_results)
            results['failed_strategies'] = len(failed_results)
            results['execution_time'] = time.time() - start_time

            # 計算性能統計
            if successful_results:
                sharpe_values = [r.sharpe_ratio for r in successful_results]
                return_values = [r.total_return for r in successful_results]
                drawdown_values = [r.max_drawdown for r in successful_results]

                results['performance_stats'] = {
                    'avg_sharpe': np.mean(sharpe_values),
                    'max_sharpe': np.max(sharpe_values),
                    'min_sharpe': np.min(sharpe_values),
                    'avg_return': np.mean(return_values),
                    'max_return': np.max(return_values),
                    'avg_drawdown': np.mean(drawdown_values),
                    'worst_drawdown': np.min(drawdown_values),
                    'success_rate': len(successful_results) / len(combinations) * 100
                }

                # 獲取前5名策略
                top_5 = sorted(successful_results, key=lambda x: x.sharpe_ratio, reverse=True)[:5]
                results['top_strategies'] = [
                    {
                        'strategy_name': r.strategy_name,
                        'sharpe_ratio': r.sharpe_ratio,
                        'total_return': r.total_return,
                        'max_drawdown': r.max_drawdown,
                        'trade_frequency': r.trade_frequency,
                        'quality_score': r.quality_score,
                        'params': r.params
                    }
                    for r in top_5
                ]

            # 收集錯誤信息
            if failed_results:
                results['errors'] = [r.get('error', 'Unknown error') for r in failed_results[:5]]

        except Exception as e:
            results['errors'].append(f"Strategy type test failed: {str(e)}")

        return results

    def _test_multi_strategy_parallel(self, combinations: Dict[str, List[Dict]],
                                    stock_data: pd.DataFrame, gov_data: Dict) -> Dict[str, Any]:
        """測試多策略並行處理"""

        try:
            start_time = time.time()

            # 使用引擎的並行處理功能
            print(f"[PARALLEL] Starting multi-strategy parallel test...")

            # 運行小規模並行測試
            parallel_results = self.backtest_engine.run_comprehensive_optimization(
                stock_data, gov_data
            )

            execution_time = time.time() - start_time

            # 計算並行性能統計
            total_strategies = sum(len(combos) for combos in combinations.values())
            successful_strategies = len([r for r in parallel_results if r.success])

            parallel_stats = {
                'total_strategies_tested': len(parallel_results),
                'successful_strategies': successful_strategies,
                'failed_strategies': len(parallel_results) - successful_strategies,
                'execution_time': execution_time,
                'strategies_per_second': len(parallel_results) / execution_time if execution_time > 0 else 0,
                'success_rate': successful_strategies / len(parallel_results) * 100 if parallel_results else 0
            }

            # 按策略類型分組統計
            strategy_type_stats = {}
            for result in parallel_results:
                if result.success:
                    strategy_type = result.strategy_type
                    if strategy_type not in strategy_type_stats:
                        strategy_type_stats[strategy_type] = {
                            'count': 0,
                            'avg_sharpe': 0,
                            'max_sharpe': -999
                        }

                    strategy_type_stats[strategy_type]['count'] += 1
                    strategy_type_stats[strategy_type]['avg_sharpe'] += result.sharpe_ratio
                    strategy_type_stats[strategy_type]['max_sharpe'] = max(
                        strategy_type_stats[strategy_type]['max_sharpe'], result.sharpe_ratio
                    )

            # 計算平均值
            for stats in strategy_type_stats.values():
                if stats['count'] > 0:
                    stats['avg_sharpe'] /= stats['count']

            parallel_stats['strategy_type_performance'] = strategy_type_stats

            return parallel_stats

        except Exception as e:
            return {
                'error': f"Parallel test failed: {str(e)}",
                'execution_time': time.time() - start_time
            }

    def _display_strategy_summary(self, strategy_type: str, results: Dict[str, Any]):
        """顯示策略測試摘要"""

        print(f"\n{strategy_type} Strategy Results:")
        print(f"  Total Combinations: {results['total_combinations']}")
        print(f"  Successful: {results['successful_strategies']}")
        print(f"  Failed: {results['failed_strategies']}")
        print(f"  Success Rate: {results['successful_strategies']/results['total_combinations']*100:.1f}%")
        print(f"  Execution Time: {results['execution_time']:.2f}s")

        if results['performance_stats']:
            stats = results['performance_stats']
            print(f"  Performance:")
            print(f"    Avg Sharpe: {stats['avg_sharpe']:.3f}")
            print(f"    Max Sharpe: {stats['max_sharpe']:.3f}")
            print(f"    Avg Return: {stats['avg_return']:.2%}")
            print(f"    Max Return: {stats['max_return']:.2%}")
            print(f"    Avg Drawdown: {stats['avg_drawdown']:.2%}")

        if results['top_strategies']:
            print(f"  Top 3 Strategies:")
            for i, strategy in enumerate(results['top_strategies'][:3], 1):
                print(f"    {i}. {strategy['strategy_name']}")
                print(f"       Sharpe: {strategy['sharpe_ratio']:.3f}, "
                      f"Return: {strategy['total_return']:.2%}, "
                      f"Drawdown: {strategy['max_drawdown']:.2%}")

    def _calculate_overall_statistics(self, strategy_results: Dict[str, Dict]) -> Dict[str, Any]:
        """計算整體統計數據"""

        overall_stats = {
            'total_strategies_tested': 0,
            'total_successful': 0,
            'total_failed': 0,
            'overall_success_rate': 0,
            'strategy_type_summary': {},
            'best_strategy_overall': None
        }

        all_successful_strategies = []

        for strategy_type, results in strategy_results.items():
            overall_stats['strategy_type_summary'][strategy_type] = {
                'total': results['total_combinations'],
                'successful': results['successful_strategies'],
                'failed': results['failed_strategies'],
                'success_rate': results['successful_strategies'] / results['total_combinations'] * 100 if results['total_combinations'] > 0 else 0
            }

            overall_stats['total_strategies_tested'] += results['total_combinations']
            overall_stats['total_successful'] += results['successful_strategies']
            overall_stats['total_failed'] += results['failed_strategies']

            # 收集所有成功的策略
            if results['top_strategies']:
                all_successful_strategies.extend(results['top_strategies'])

        # 計算整體成功率
        if overall_stats['total_strategies_tested'] > 0:
            overall_stats['overall_success_rate'] = (
                overall_stats['total_successful'] / overall_stats['total_strategies_tested'] * 100
            )

        # 找出最佳策略
        if all_successful_strategies:
            best_strategy = max(all_successful_strategies, key=lambda x: x['sharpe_ratio'])
            overall_stats['best_strategy_overall'] = {
                'strategy_name': best_strategy['strategy_name'],
                'sharpe_ratio': best_strategy['sharpe_ratio'],
                'total_return': best_strategy['total_return'],
                'max_drawdown': best_strategy['max_drawdown'],
                'quality_score': best_strategy['quality_score']
            }

        return overall_stats

    def _extract_top_strategies(self, strategy_results: Dict[str, Dict]) -> Dict[str, List[Dict]]:
        """提取各策略類型的頂級策略"""

        top_strategies = {}

        for strategy_type, results in strategy_results.items():
            if results['top_strategies']:
                top_strategies[strategy_type] = results['top_strategies']

        return top_strategies

    def _generate_phase2_report(self, test_results: Dict[str, Any]):
        """生成Phase 2測試報告"""

        print(f"\n{'='*80}")
        print("PHASE 2 COMPLETE STRATEGY TEST REPORT")
        print(f"{'='*80}")

        print(f"\nTest Configuration:")
        print(f"  Stock: {test_results['stock_symbol']}")
        print(f"  Data Duration: {test_results['test_duration_days']} days")
        print(f"  Strategy Types: {', '.join(test_results['strategy_types_tested'])}")

        if 'data_quality' in test_results:
            dq = test_results['data_quality']
            print(f"  Data Quality: {dq['stock_records']} records, {dq['date_range']}")

        # 整體統計
        if 'overall_statistics' in test_results:
            stats = test_results['overall_statistics']
            print(f"\nOverall Statistics:")
            print(f"  Total Strategies Tested: {stats['total_strategies_tested']:,}")
            print(f"  Successful: {stats['total_successful']:,}")
            print(f"  Failed: {stats['total_failed']:,}")
            print(f"  Overall Success Rate: {stats['overall_success_rate']:.1f}%")

            if stats['best_strategy_overall']:
                best = stats['best_strategy_overall']
                print(f"\nBest Strategy Overall:")
                print(f"  Strategy: {best['strategy_name']}")
                print(f"  Sharpe Ratio: {best['sharpe_ratio']:.3f}")
                print(f"  Total Return: {best['total_return']:.2%}")
                print(f"  Max Drawdown: {best['max_drawdown']:.2%}")
                print(f"  Quality Score: {best['quality_score']:.1f}")

        # 按策略類型統計
        print(f"\nStrategy Type Performance:")
        for strategy_type, summary in stats['strategy_type_summary'].items():
            print(f"  {strategy_type}:")
            print(f"    Total: {summary['total']:,}")
            print(f"    Success Rate: {summary['success_rate']:.1f}%")
            print(f"    Successful: {summary['successful']:,}")

        # 並行處理性能
        if 'parallel_performance' in test_results:
            perf = test_results['parallel_performance']
            if 'error' not in perf:
                print(f"\nParallel Processing Performance:")
                print(f"  Strategies Processed: {perf['total_strategies_tested']:,}")
                print(f"  Processing Speed: {perf['strategies_per_second']:.1f} strategies/sec")
                print(f"  Success Rate: {perf['success_rate']:.1f}%")
                print(f"  Execution Time: {perf['execution_time']:.2f}s")

        print(f"\n{'='*80}")
        print("PHASE 2 TESTING COMPLETED SUCCESSFULLY")
        print(f"{'='*80}")

    def save_test_results(self, test_results: Dict[str, Any],
                         filename: str = None):
        """保存測試結果"""

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phase2_complete_strategy_test_results_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(test_results, f, indent=2, ensure_ascii=False, default=str)

            print(f"\n[SAVE] Phase 2 test results saved to: {filename}")

        except Exception as e:
            print(f"[ERROR] Failed to save test results: {str(e)}")


def main():
    """主函數 - 運行Phase 2完整策略測試"""

    # 創建測試實例
    test_suite = Phase2CompleteStrategyTest()

    # 運行完整測試
    print(f"\n[START] Running Phase 2 complete strategy test...")
    test_results = test_suite.run_complete_strategy_test(
        stock_symbol="0700.HK",
        test_duration_days=180,
        max_strategies_per_type=30
    )

    # 保存測試結果
    test_suite.save_test_results(test_results)

    # 返回測試成功狀態
    success = (len(test_results['errors']) == 0 and
               len(test_results['strategy_types_tested']) == 4 and
               test_results.get('overall_statistics', {}).get('overall_success_rate', 0) > 50)

    print(f"\n[RESULT] Phase 2 test {'PASSED' if success else 'FAILED'}")

    return success


if __name__ == "__main__":
    main()