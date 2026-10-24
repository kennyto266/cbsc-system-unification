#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Direct Component Test
直接組件測試 - 測試增強系統的核心功能
"""

import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_intelligent_cache():
    """直接測試智能緩存系統"""
    print("[TEST] 智能緩存系統測試")
    try:
        from intelligent_cache import IntelligentCache, CacheConfig

        config = CacheConfig(l1_max_size=100, l2_enabled=False)  # 禁用L2緩存避免權限問題
        cache = IntelligentCache(config)

        # 測試基本操作
        test_key = "test_key_123"
        test_value = [1, 2, 3, 4, 5]

        cache.set(test_key, test_value)
        retrieved = cache.get(test_key)

        stats = cache.get_cache_statistics()

        if retrieved == test_value:
            print(f"  [OK] 緩存系統工作正常")
            print(f"  [INFO] L1緩存: {stats['l1_stats']['size']}/{stats['l1_stats']['max_size']}")
            print(f"  [INFO] 總命中率: {stats['overall']['overall_hit_rate']:.1f}%")
            return True
        else:
            print(f"  [FAIL] 緩存檢索失敗")
            return False

    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def test_performance_monitor():
    """直接測試性能監控系統"""
    print("[TEST] 性能監控系統測試")
    try:
        from performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor()

        # 模擬優化過程
        monitor.start_optimization(100)
        time.sleep(0.5)  # 模擬計算時間
        monitor.end_optimization(0.5, 95)

        summary = monitor.get_performance_summary()
        bottlenecks = monitor.detect_bottlenecks()

        if 'optimization' in summary:
            print(f"  [OK] 性能監控工作正常")
            print(f"  [INFO] 總策略數: {summary['optimization']['total_strategies']}")
            print(f"  [INFO] 成功率: {summary['optimization']['success_rate']:.1f}%")
            print(f"  [INFO] 檢測到瓶頸: {len(bottlenecks)} 個")
            return True
        else:
            print(f"  [FAIL] 性能監控數據不完整")
            return False

    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def test_error_handler():
    """直接測試錯誤處理系統"""
    print("[TEST] 錯誤處理系統測試")
    try:
        from error_handler import EnhancedErrorHandler

        handler = EnhancedErrorHandler()

        # 測試錯誤記錄
        test_error = ValueError("測試錯誤")
        handler.record_error(test_error)

        summary = handler.get_error_summary()
        health = handler.get_health_status()

        if summary['total_errors'] > 0 and health['health_score'] > 0:
            print(f"  [OK] 錯誤處理工作正常")
            print(f"  [INFO] 記錄錯誤數: {summary['total_errors']}")
            print(f"  [INFO] 健康分數: {health['health_score']:.1f}")
            print(f"  [INFO] 系統狀態: {health['status']}")
            return True
        else:
            print(f"  [FAIL] 錯誤處理功能異常")
            return False

    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def test_indicator_engine():
    """直接測試指標計算引擎"""
    print("[TEST] 指標計算引擎測試")
    try:
        from indicator_engine import EnhancedIndicatorEngine

        engine = EnhancedIndicatorEngine()

        # 測試數據
        test_data = [100, 102, 98, 105, 103, 107, 106, 110, 108, 112] * 25

        # 測試RSI計算
        rsi_result = engine.calculate_indicator('RSI', test_data, period=14)

        # 測試MACD計算
        macd_result = engine.calculate_indicator('MACD', test_data, fast=12, slow=26, signal=9)

        # 驗證MB_KDJ策略
        kdj_validation = engine.validate_mb_kdj_strategy(test_data)

        if (rsi_result.success and macd_result.success and
            len(rsi_result.values) == len(test_data)):
            print(f"  [OK] 指標引擎工作正常")
            print(f"  [INFO] RSI計算時間: {rsi_result.calculation_time:.4f}秒")
            print(f"  [INFO] MACD計算時間: {macd_result.calculation_time:.4f}秒")
            print(f"  [INFO] MB_KDJ驗證: {'通過' if kdj_validation['validation_passed'] else '失敗'}")

            stats = engine.get_calculation_stats()
            print(f"  [INFO] 計算統計: {stats['total_calculations']} 次計算, 成功率 {stats['success_rate']:.1f}%")
            return True
        else:
            print(f"  [FAIL] 指標計算失敗")
            print(f"  [INFO] RSI成功: {rsi_result.success}")
            print(f"  [INFO] MACD成功: {macd_result.success}")
            return False

    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def test_data_manager():
    """直接測試數據管理器"""
    print("[TEST] 數據管理器測試")
    try:
        from data_manager import EnhancedDataManager

        manager = EnhancedDataManager()

        # 測試股票數據獲取
        stock_success = manager.fetch_stock_data("0700.hk", 365)

        if stock_success and len(manager.stock_data) > 0:
            stock_info = manager.stock_data["0700.hk"]
            print(f"  [OK] 股票數據獲取成功")
            print(f"  [INFO] 價格記錄數: {len(stock_info['close'])}")
            print(f"  [INFO] 價格範圍: {min(stock_info['close']):.2f} - {max(stock_info['close']):.2f}")
            print(f"  [INFO] 數據來源: {stock_info.get('source', 'unknown')}")

            # 測試數據質量統計
            summary = manager.get_data_summary()
            print(f"  [INFO] 數據質量統計: {summary['stock_data_count']} 個股票數據源")
            return True
        else:
            print(f"  [FAIL] 股票數據獲取失敗")
            return False

    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def test_core_functionality():
    """測試核心功能"""
    print("[TEST] 核心功能驗證")
    try:
        # 測試保護策略配置
        with open('__init__.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'MB_KDJ_[10,2]' in content and '3.672' in content:
                print(f"  [OK] MB_KDJ_[10,2]策略保護配置存在")
            else:
                print(f"  [FAIL] MB_KDJ策略保護配置缺失")
                return False

        # 測試性能基準
        if 'strategies_per_second' in content and 'parallel_cores' in content:
            print(f"  [OK] 性能基準配置存在")
        else:
            print(f"  [FAIL] 性能基準配置缺失")
            return False

        # 測試組件導入
        components = ['intelligent_cache', 'performance_monitor', 'error_handler',
                     'indicator_engine', 'data_manager', 'core_optimizer']

        import_count = 0
        for component in components:
            try:
                __import__(component)
                import_count += 1
            except ImportError:
                print(f"  [WARN] 無法導入 {component}")

        if import_count >= 4:  # 至少有一半組件可以導入
            print(f"  [OK] 核心組件導入成功: {import_count}/{len(components)}")
            return True
        else:
            print(f"  [FAIL] 核心組件導入失敗: {import_count}/{len(components)}")
            return False

    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def run_direct_tests():
    """運行直接測試"""
    print("="*60)
    print("增強非價格技術分析系統 - 直接組件測試")
    print("Enhanced Non-Price TA System - Direct Component Test")
    print("="*60)

    tests = [
        ("智能緩存系統", test_intelligent_cache),
        ("性能監控系統", test_performance_monitor),
        ("錯誤處理系統", test_error_handler),
        ("指標計算引擎", test_indicator_engine),
        ("數據管理器", test_data_manager),
        ("核心功能驗證", test_core_functionality)
    ]

    results = []
    for test_name, test_func in tests:
        start_time = time.time()
        try:
            success = test_func()
        except Exception as e:
            print(f"  [ERROR] 測試異常: {str(e)}")
            success = False

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
    print("測試結果總結")
    print("="*60)
    print(f"總測試數: {total_tests}")
    print(f"通過: {passed_tests}")
    print(f"失敗: {total_tests - passed_tests}")
    print(f"成功率: {success_rate:.1f}%")

    # 評估系統狀態
    if success_rate >= 90:
        system_status = "優秀 - 系統完全可用"
    elif success_rate >= 75:
        system_status = "良好 - 系統基本可用"
    elif success_rate >= 50:
        system_status = "一般 - 系統部分可用"
    else:
        system_status = "需要修復 - 系統存在問題"

    print(f"系統狀態: {system_status}")

    # 關鍵組件檢查
    key_components = ['智能緩存系統', '指標計算引擎', '核心功能驗證']
    key_components_ok = sum(1 for r in results if r['name'] in key_components and r['success'])

    print(f"關鍵組件: {key_components_ok}/{len(key_components)} 正常")

    if success_rate >= 80 and key_components_ok >= 2:
        print("\n[RESULT] 增強系統核心功能驗證成功！")
        print("OpenSpec enhance-nonprice-ta-system 實施有效！")
        return True
    else:
        print("\n[RESULT] 增強系統需要進一步完善")
        return False

if __name__ == "__main__":
    success = run_direct_tests()
    exit(0 if success else 1)