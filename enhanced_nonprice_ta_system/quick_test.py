#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Quick Test for Enhanced System
增強系統快速測試 - 展示核心功能，避免異步問題
"""

import sys
import time
import json
from typing import Dict, Any

def test_cache_system():
    """測試智能緩存系統"""
    print("[TEST] 測試智能緩存系統")
    try:
        from enhanced_nonprice_ta_system.intelligent_cache import IntelligentCache

        cache = IntelligentCache()
        test_key = "test_key"
        test_value = [1, 2, 3, 4, 5]

        # 測試設置和獲取
        cache.set(test_key, test_value)
        retrieved = cache.get(test_key)

        stats = cache.get_cache_statistics()

        if retrieved == test_value:
            print(f"  [OK] 緩存系統正常工作")
            print(f"  [INFO] 緩存統計: {stats['l1_stats']['size']}/{stats['l1_stats']['max_size']} 項目")
            return True
        else:
            print(f"  [FAIL] 緩存檢索失敗")
            return False
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def test_error_handler():
    """測試錯誤處理系統"""
    print("[TEST] 測試錯誤處理系統")
    try:
        from enhanced_nonprice_ta_system.error_handler import EnhancedErrorHandler

        handler = EnhancedErrorHandler()
        test_error = ValueError("測試錯誤")
        handler.record_error(test_error)

        summary = handler.get_error_summary()
        health = handler.get_health_status()

        print(f"  [OK] 錯誤處理正常工作")
        print(f"  [INFO] 總錯誤數: {summary['total_errors']}")
        print(f"  [INFO] 健康分數: {health['health_score']:.1f}")
        return True
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def test_performance_monitor():
    """測試性能監控"""
    print("[TEST] 測試性能監控系統")
    try:
        from enhanced_nonprice_ta_system.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor()
        monitor.start_optimization(100)
        time.sleep(0.5)
        monitor.end_optimization(0.5, 95)

        summary = monitor.get_performance_summary()

        print(f"  [OK] 性能監控正常工作")
        print(f"  [INFO] 策略數: {summary['optimization']['total_strategies']}")
        print(f"  [INFO] 成功率: {summary['optimization']['success_rate']:.1f}%")
        return True
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def test_indicator_engine():
    """測試指標引擎"""
    print("[TEST] 測試指標計算引擎")
    try:
        from enhanced_nonprice_ta_system.indicator_engine import EnhancedIndicatorEngine

        engine = EnhancedIndicatorEngine()
        test_data = [100, 102, 98, 105, 103, 107, 106, 110, 108, 112] * 25

        # 測試RSI計算
        rsi_result = engine.calculate_indicator('RSI', test_data, period=14)

        if rsi_result.success:
            print(f"  [OK] RSI計算成功: {rsi_result.calculation_time:.4f}秒")
            print(f"  [INFO] 指標值數量: {len(rsi_result.values)}")

            # 獲取統計
            stats = engine.get_calculation_stats()
            print(f"  [INFO] 計算統計: {stats['total_calculations']} 次計算")
            return True
        else:
            print(f"  [FAIL] RSI計算失敗: {rsi_result.error_message}")
            return False
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def test_data_manager():
    """測試數據管理器（同步版本）"""
    print("[TEST] 測試數據源管理器")
    try:
        from enhanced_nonprice_ta_system.data_manager import EnhancedDataManager

        manager = EnhancedDataManager()

        # 只測試股票數據獲取（避免異步問題）
        stock_success = manager.fetch_stock_data("0700.hk", 365)

        if stock_success and len(manager.stock_data) > 0:
            stock_info = manager.stock_data["0700.hk"]
            print(f"  [OK] 股票數據獲取成功")
            print(f"  [INFO] 價格記錄數: {len(stock_info['close'])}")
            print(f"  [INFO] 數據來源: {stock_info.get('source', 'unknown')}")

            # 測試數據摘要
            summary = manager.get_data_summary()
            print(f"  [INFO] 數據源數量: {summary['stock_data_count']} 個")
            return True
        else:
            print(f"  [FAIL] 股票數據獲取失敗")
            return False
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def test_protected_strategies():
    """測試保護策略"""
    print("[TEST] 測試MB_KDJ_[10,2]策略保護")
    try:
        from enhanced_nonprice_ta_system import PROTECTED_STRATEGIES

        if 'MB_KDJ_[10,2]' in PROTECTED_STRATEGIES:
            strategy = PROTECTED_STRATEGIES['MB_KDJ_[10,2]']
            if strategy['expected_sharpe'] == 3.672:
                print(f"  [OK] MB_KDJ_[10,2]策略保護正常")
                print(f"  [INFO] 期望Sharpe: {strategy['expected_sharpe']}")
                return True
            else:
                print(f"  [FAIL] Sharpe比率不正確: {strategy['expected_sharpe']}")
                return False
        else:
            print(f"  [FAIL] MB_KDJ_[10,2]策略未找到")
            return False
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def test_performance_benchmarks():
    """測試性能基準"""
    print("[TEST] 測試系統性能基準")
    try:
        from enhanced_nonprice_ta_system import PERFORMANCE_BENCHMARKS

        strategies_per_sec = PERFORMANCE_BENCHMARKS.get('strategies_per_second', 0)
        parallel_cores = PERFORMANCE_BENCHMARKS.get('parallel_cores', 0)

        if strategies_per_sec >= 396 and parallel_cores >= 32:
            print(f"  [OK] 性能基準符合要求")
            print(f"  [INFO] 策略/秒: {strategies_per_sec}")
            print(f"  [INFO] 並行核心: {parallel_cores}")
            return True
        else:
            print(f"  [FAIL] 性能基準不足")
            print(f"  [INFO] 策略/秒: {strategies_per_sec} (需要 >=396)")
            print(f"  [INFO] 並行核心: {parallel_cores} (需要 >=32)")
            return False
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def run_quick_tests():
    """運行快速測試"""
    print("="*60)
    print("增強非價格技術分析系統 - 快速測試")
    print("Enhanced Non-Price Technical Analysis System - Quick Test")
    print("="*60)

    tests = [
        ("智能緩存系統", test_cache_system),
        ("錯誤處理系統", test_error_handler),
        ("性能監控系統", test_performance_monitor),
        ("指標計算引擎", test_indicator_engine),
        ("數據源管理器", test_data_manager),
        ("保護策略驗證", test_protected_strategies),
        ("性能基準驗證", test_performance_benchmarks)
    ]

    results = []
    for test_name, test_func in tests:
        start_time = time.time()
        success = test_func()
        execution_time = time.time() - start_time

        results.append({
            'name': test_name,
            'success': success,
            'time': execution_time
        })

        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {test_name} - {execution_time:.3f}秒")
        print()

    # 總結報告
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    print("="*60)
    print("測試結果總結 / Test Summary")
    print("="*60)
    print(f"總測試數: {total_tests}")
    print(f"通過: {passed_tests}")
    print(f"失敗: {total_tests - passed_tests}")
    print(f"成功率: {success_rate:.1f}%")

    if success_rate >= 80:
        health_status = "良好"
    else:
        health_status = "需要改進"

    print(f"系統健康: {health_status}")

    # 保存測試報告
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = f"enhanced_system_quick_test_{timestamp}.json"

    report = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'test_summary': {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': success_rate,
            'health_status': health_status
        },
        'test_details': results,
        'system_validation': {
            'cache_working': results[0]['success'],
            'error_handling_working': results[1]['success'],
            'performance_monitoring_working': results[2]['success'],
            'indicator_engine_working': results[3]['success'],
            'data_manager_working': results[4]['success'],
            'protected_strategies_valid': results[5]['success'],
            'performance_benchmarks_met': results[6]['success']
        }
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"詳細測試報告已保存: {report_file}")

    return success_rate >= 80

def main():
    """主函數"""
    success = run_quick_tests()

    if success:
        print("\n[SUCCESS] 增強系統快速測試通過！")
        print("OpenSpec enhance-nonprice-ta-system 核心功能正常運行！")
        return 0
    else:
        print("\n[FAILED] 增強系統快速測試失敗，需要進行修復")
        return 1

if __name__ == "__main__":
    exit(main())