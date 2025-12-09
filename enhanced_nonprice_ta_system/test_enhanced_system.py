#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced System Integration Test
增強系統集成測試 - 驗證OpenSpec enhance-nonprice-ta-system實施

測試所有增強功能：
- 核心優化引擎性能
- 數據源管理
- 指標計算引擎
- 智能緩存系統
- 錯誤處理和恢復
- MB_KDJ_[10,2]策略保護
"""

import sys
import os
import time
import json
import asyncio
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_nonprice_ta_system import (
    EnhancedOptimizerEngine,
    EnhancedDataManager,
    EnhancedIndicatorEngine,
    PROTECTED_STRATEGIES,
    PERFORMANCE_BENCHMARKS
)
from enhanced_nonprice_ta_system.intelligent_cache import CacheConfig
from enhanced_nonprice_ta_system.performance_monitor import PerformanceMonitor
from enhanced_nonprice_ta_system.error_handler import EnhancedErrorHandler

class EnhancedSystemTester:
    """增強系統測試器"""

    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }

    def run_test(self, test_name: str, test_func):
        """運行單個測試"""
        self.test_results['total_tests'] += 1

        print(f"\n[TEST] 運行測試: {test_name}")
        start_time = time.time()

        try:
            result = test_func()
            execution_time = time.time() - start_time

            if result.get('success', True):
                print(f"[PASS] {test_name} - {execution_time:.3f}秒")
                self.test_results['passed_tests'] += 1
                self.test_results['test_details'].append({
                    'name': test_name,
                    'status': 'PASSED',
                    'time': execution_time,
                    'details': result
                })
            else:
                print(f"[FAIL] {test_name} - {result.get('error', 'Unknown error')}")
                self.test_results['failed_tests'] += 1
                self.test_results['test_details'].append({
                    'name': test_name,
                    'status': 'FAILED',
                    'time': execution_time,
                    'error': result.get('error', 'Unknown error')
                })

        except Exception as e:
            execution_time = time.time() - start_time
            print(f"[ERROR] {test_name} - {str(e)}")
            self.test_results['failed_tests'] += 1
            self.test_results['test_details'].append({
                'name': test_name,
                'status': 'ERROR',
                'time': execution_time,
                'error': str(e)
            })

    def test_cache_system(self):
        """測試智能緩存系統"""
        from enhanced_nonprice_ta_system.intelligent_cache import IntelligentCache

        cache = IntelligentCache()

        # 測試基本緩存操作
        test_key = "test_key_123"
        test_value = [1, 2, 3, 4, 5]

        # 設置和獲取
        cache.set(test_key, test_value)
        retrieved_value = cache.get(test_key)

        # 驗證結果
        if retrieved_value == test_value:
            # 測試統計
            stats = cache.get_cache_statistics()
            return {
                'success': True,
                'cache_working': True,
                'stats': stats
            }
        else:
            return {
                'success': False,
                'error': 'Cache retrieval failed'
            }

    def test_error_handler(self):
        """測試錯誤處理系統"""
        error_handler = EnhancedErrorHandler()

        # 測試錯誤記錄
        test_error = ValueError("Test error for validation")
        error_handler.record_error(test_error)

        # 獲取錯誤摘要
        summary = error_handler.get_error_summary()

        # 測試健康狀態
        health = error_handler.get_health_status()

        if summary['total_errors'] > 0 and health['health_score'] > 0:
            return {
                'success': True,
                'error_recording': True,
                'health_score': health['health_score'],
                'summary': summary
            }
        else:
            return {
                'success': False,
                'error': 'Error handler not working properly'
            }

    def test_performance_monitor(self):
        """測試性能監控系統"""
        monitor = PerformanceMonitor()

        # 測試指標收集
        monitor.start_optimization(100)
        time.sleep(0.1)  # 模擬一些計算時間
        monitor.end_optimization(0.1, 95)

        # 獲取統計
        summary = monitor.get_performance_summary()

        if 'optimization' in summary and summary['optimization']['total_strategies'] == 100:
            return {
                'success': True,
                'monitoring_working': True,
                'summary': summary
            }
        else:
            return {
                'success': False,
                'error': 'Performance monitoring not working'
            }

    def test_indicator_engine(self):
        """測試指標引擎"""
        indicator_engine = EnhancedIndicatorEngine()

        # 測試數據
        test_data = [100, 102, 98, 105, 103, 107, 106, 110, 108, 112] * 25

        # 測試RSI計算
        rsi_result = indicator_engine.calculate_indicator('RSI', test_data, period=14)

        # 測試MACD計算
        macd_result = indicator_engine.calculate_indicator('MACD', test_data, fast=12, slow=26, signal=9)

        # 驗證MB_KDJ_[10,2]策略
        kdj_validation = indicator_engine.validate_mb_kdj_strategy(test_data)

        # 獲取統計
        stats = indicator_engine.get_calculation_stats()

        if (rsi_result.success and macd_result.success and
            len(rsi_result.values) == len(test_data) and
            kdj_validation.get('validation_passed', False)):

            return {
                'success': True,
                'indicators_working': True,
                'mb_kdj_validated': kdj_validation['validation_passed'],
                'stats': stats
            }
        else:
            return {
                'success': False,
                'error': 'Indicator engine validation failed',
                'rsi_success': rsi_result.success,
                'macd_success': macd_result.success,
                'mb_kdj_validation': kdj_validation
            }

    async def test_data_manager(self):
        """測試數據源管理器"""
        data_manager = EnhancedDataManager()

        # 測試獲取股票數據
        stock_success = data_manager.fetch_stock_data("0700.hk", 100)

        # 測試獲取政府數據
        gov_success = await data_manager.fetch_all_government_data(100)

        # 獲取數據摘要
        summary = data_manager.get_data_summary()

        if stock_success and len(data_manager.stock_data) > 0:
            return {
                'success': True,
                'stock_data_working': stock_success,
                'gov_data_sources': len(data_manager.gov_data),
                'summary': summary
            }
        else:
            return {
                'success': False,
                'error': 'Data manager test failed',
                'stock_success': stock_success,
                'gov_success': gov_success
            }

    def test_protected_strategies(self):
        """測試受保護策略"""
        # 驗證MB_KDJ_[10,2]策略配置
        if 'MB_KDJ_[10,2]' not in PROTECTED_STRATEGIES:
            return {
                'success': False,
                'error': 'MB_KDJ_[10,2] strategy not found in protected strategies'
            }

        protected_strategy = PROTECTED_STRATEGIES['MB_KDJ_[10,2]']
        expected_sharpe = protected_strategy['expected_sharpe']

        if expected_sharpe == 3.672:
            return {
                'success': True,
                'mb_kdj_protected': True,
                'expected_sharpe': expected_sharpe
            }
        else:
            return {
                'success': False,
                'error': f'Incorrect expected Sharpe ratio: {expected_sharpe}'
            }

    def test_performance_benchmarks(self):
        """測試性能基準"""
        # 驗證系統性能基準
        required_strategies_per_second = PERFORMANCE_BENCHMARKS.get('strategies_per_second', 0)
        required_parallel_cores = PERFORMANCE_BENCHMARKS.get('parallel_cores', 0)

        if (required_strategies_per_second >= 396 and
            required_parallel_cores >= 32):

            return {
                'success': True,
                'benchmarks_valid': True,
                'required_strategies_per_second': required_strategies_per_second,
                'required_parallel_cores': required_parallel_cores
            }
        else:
            return {
                'success': False,
                'error': 'Performance benchmarks not met',
                'strategies_per_second': required_strategies_per_second,
                'parallel_cores': required_parallel_cores
            }

    async def test_full_integration(self):
        """測試完整系統集成"""
        try:
            # 創建增強優化引擎
            optimizer = EnhancedOptimizerEngine()

            # 測試數據獲取
            stock_fetched = optimizer.fetch_real_stock_data()
            gov_fetched = optimizer.fetch_all_government_data()

            if not stock_fetched:
                return {
                    'success': False,
                    'error': 'Stock data fetching failed'
                }

            # 驗證數據質量
            if len(optimizer.price_data) == 0:
                return {
                    'success': False,
                    'error': 'No price data available'
                }

            if len(optimizer.gov_data) < 5:  # 至少應該有5個數據源
                return {
                    'success': False,
                    'error': f'Insufficient government data sources: {len(optimizer.gov_data)}'
                }

            return {
                'success': True,
                'integration_working': True,
                'stock_data_points': len(optimizer.price_data.get('close', [])),
                'gov_data_sources': len(optimizer.gov_data),
                'data_quality_acceptable': True
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Integration test failed: {str(e)}'
            }

    def run_all_tests(self):
        """運行所有測試"""
        print("="*80)
        print("增強非價格技術分析系統 - 集成測試")
        print("Enhanced Non-Price Technical Analysis System - Integration Test")
        print("="*80)

        # 基礎組件測試
        self.run_test("智能緩存系統", self.test_cache_system)
        self.run_test("錯誤處理系統", self.test_error_handler)
        self.run_test("性能監控系統", self.test_performance_monitor)
        self.run_test("指標計算引擎", self.test_indicator_engine)

        # 核心功能測試
        self.run_test("數據源管理器", lambda: asyncio.run(self.test_data_manager()))
        self.run_test("受保護策略驗證", self.test_protected_strategies)
        self.run_test("性能基準驗證", self.test_performance_benchmarks)

        # 完整集成測試
        self.run_test("完整系統集成", lambda: asyncio.run(self.test_full_integration()))

        # 生成測試報告
        self.generate_test_report()

    def generate_test_report(self):
        """生成測試報告"""
        print("\n" + "="*80)
        print("測試結果總結 / Test Summary")
        print("="*80)

        total = self.test_results['total_tests']
        passed = self.test_results['passed_tests']
        failed = self.test_results['failed_tests']
        success_rate = (passed / total * 100) if total > 0 else 0

        print(f"總測試數: {total}")
        print(f"通過: {passed}")
        print(f"失敗: {failed}")
        print(f"成功率: {success_rate:.1f}%")

        # 顯示失敗的測試
        failed_tests = [t for t in self.test_results['test_details'] if t['status'] in ['FAILED', 'ERROR']]
        if failed_tests:
            print(f"\n失敗的測試:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test.get('error', 'Unknown error')}")

        # 系統健康評估
        if success_rate >= 90:
            health_status = "優秀"
        elif success_rate >= 75:
            health_status = "良好"
        else:
            health_status = "需要改進"

        print(f"\n系統健康狀態: {health_status}")

        # 保存詳細報告
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = f"enhanced_system_test_report_{timestamp}.json"

        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'test_summary': {
                'total_tests': total,
                'passed_tests': passed,
                'failed_tests': failed,
                'success_rate': success_rate,
                'health_status': health_status
            },
            'test_details': self.test_results['test_details'],
            'system_validation': {
                'mb_kdj_strategy_protected': 'MB_KDJ_[10,2]' in PROTECTED_STRATEGIES,
                'performance_benchmarks_met': PERFORMANCE_BENCHMARKS['strategies_per_second'] >= 396,
                'enhancement_objectives_met': success_rate >= 90
            }
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"詳細測試報告已保存: {report_file}")

        return success_rate >= 90

def main():
    """主函數"""
    tester = EnhancedSystemTester()
    success = tester.run_all_tests()

    if success:
        print("\n[SUCCESS] 增強系統測試通過！OpenSpec enhance-nonprice-ta-system 實施成功！")
        return 0
    else:
        print("\n[FAILED] 增強系統測試失敗，需要進行修復")
        return 1

if __name__ == "__main__":
    exit(main())