"""
Enhanced HIBOR System Simple Test Script
简化的增强HIBOR系统测试脚本 - 移除emoji字符避免编码问题
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'enhanced_nonprice_ta_system'))

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def test_data_alignment_manager():
    """测试数据对齐管理器"""
    print("Testing Data Alignment Manager...")

    try:
        from enhanced_nonprice_ta_system.core.data_alignment_manager import DataAlignmentManager
        manager = DataAlignmentManager()
        print("  [OK] Data Alignment Manager initialized successfully")

        # 创建测试数据
        np.random.seed(42)
        dates1 = pd.date_range('2020-01-01', '2024-12-31', freq='D')
        data1 = pd.DataFrame({'hibor_rate': np.random.uniform(1.5, 5.0, len(dates1))}, index=dates1)

        dates2 = pd.date_range('2020-06-01', '2024-06-30', freq='D')
        data2 = pd.DataFrame({'fx_rate': np.random.uniform(7.7, 7.9, len(dates2))}, index=dates2)

        test_datasets = {'HIBOR': data1, 'FX': data2}

        # 测试对齐功能
        aligned_result = manager.align_datasets(test_datasets)
        print(f"  [OK] Data alignment successful: {aligned_result.data.shape}")

        return True

    except Exception as e:
        print(f"  [FAIL] Data Alignment Manager test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_intelligent_indicator_selector():
    """测试智能指标选择器"""
    print("Testing Intelligent Indicator Selector...")

    try:
        from enhanced_nonprice_ta_system.core.intelligent_indicator_selector import IntelligentIndicatorSelector
        selector = IntelligentIndicatorSelector()
        print("  [OK] Intelligent Indicator Selector initialized successfully")

        # 创建测试数据
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
        test_data = pd.DataFrame({
            'interest_rate': np.random.uniform(1.5, 5.0, len(dates))
        }, index=dates)

        # 测试指标选择
        recommendations = selector.select_indicators(test_data, top_n=3)
        print(f"  [OK] Indicator recommendation successful: {len(recommendations)} recommendations")

        return True

    except Exception as e:
        print(f"  [FAIL] Intelligent Indicator Selector test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_data_collector():
    """测试增强数据收集器"""
    print("Testing Enhanced Data Collector...")

    try:
        from enhanced_nonprice_ta_system.core.enhanced_data_collector import EnhancedDataCollector
        collector = EnhancedDataCollector()
        print("  [OK] Enhanced Data Collector initialized successfully")

        # 测试数据源配置
        sources_count = len(collector.data_sources)
        print(f"  [OK] Found {sources_count} configured data sources")

        # 显示数据源列表
        for key, config in collector.data_sources.items():
            print(f"    [SOURCE] {config['name']}: {config['endpoint'][:50]}...")

        return True

    except Exception as e:
        print(f"  [FAIL] Enhanced Data Collector test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_system_integration():
    """测试系统集成"""
    print("Testing System Integration...")

    try:
        from enhanced_nonprice_ta_system.enhanced_hibor_analyzer import EnhancedHIBORAnalyzer
        analyzer = EnhancedHIBORAnalyzer()
        print("  [OK] Main analyzer initialized successfully")

        # 获取摘要统计
        summary = analyzer.get_summary_statistics()
        print(f"  [OK] System status: {summary}")

        return True

    except Exception as e:
        print(f"  [FAIL] System integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_mock_data_processing():
    """测试模拟数据处理"""
    print("Testing Mock Data Processing...")

    try:
        # 创建模拟的HIBOR数据
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')

        # 模拟HIBOR利率数据（加入一些真实的特征）
        base_rate = 3.0
        hibor_rates = []
        for i in range(len(dates)):
            # 加入均值回归和季节性特征
            rate = base_rate + np.sin(i/365.25 * 2 * np.pi) * 0.5  # 季节性
            rate += np.random.normal(0, 0.2)  # 随机波动
            rate = max(0.5, min(8.0, rate))  # 限制在合理范围
            hibor_rates.append(rate)

        hibor_data = pd.DataFrame({
            'overnight_rate': hibor_rates,
            '1w_rate': [r + np.random.uniform(0.1, 0.3) for r in hibor_rates],
            '1m_rate': [r + np.random.uniform(0.2, 0.5) for r in hibor_rates]
        }, index=dates)

        # 模拟汇率数据
        fx_base = 7.8
        fx_rates = [fx_base + np.random.uniform(-0.1, 0.1) + np.sin(i/100) * 0.02
                   for i in range(len(dates))]
        fx_data = pd.DataFrame({'usd_hkd': fx_rates}, index=dates)

        # 模拟货币基础数据（长期增长趋势）
        mb_trend = np.linspace(2000, 2500, len(dates))
        mb_data = pd.DataFrame({
            'monetary_base': mb_trend + np.random.normal(0, 20, len(dates))
        }, index=dates)

        mock_datasets = {
            'HIBOR_Rates': hibor_data,
            'FX_Rates': fx_data,
            'Monetary_Base': mb_data
        }

        print(f"  [OK] Mock data created successfully:")
        for name, data in mock_datasets.items():
            print(f"    [DATA] {name}: {data.shape} - Date range {data.index.min()} to {data.index.max()}")

        # 测试数据对齐
        from enhanced_nonprice_ta_system.core.data_alignment_manager import DataAlignmentManager
        manager = DataAlignmentManager()
        aligned_result = manager.align_datasets(mock_datasets)

        print(f"  [OK] Mock data alignment successful: {aligned_result.data.shape}")

        # 测试指标推荐
        from enhanced_nonprice_ta_system.core.intelligent_indicator_selector import IntelligentIndicatorSelector
        selector = IntelligentIndicatorSelector()

        recommendations = {}
        for name, data in mock_datasets.items():
            recs = selector.select_indicators(data, top_n=2)
            recommendations[name] = recs
            print(f"  [OK] {name} indicator recommendations: {len(recs)}")

        return True

    except Exception as e:
        print(f"  [FAIL] Mock data processing test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("Enhanced HIBOR System - Core Function Tests")
    print("=" * 80)

    test_results = {}

    # 执行各项测试
    tests = [
        ("Data Alignment Manager", test_data_alignment_manager),
        ("Intelligent Indicator Selector", test_intelligent_indicator_selector),
        ("Enhanced Data Collector", test_enhanced_data_collector),
        ("System Integration", test_system_integration),
        ("Mock Data Processing", test_mock_data_processing)
    ]

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        success = test_func()
        test_results[test_name] = success

        if success:
            print(f"[PASS] {test_name} test passed")
        else:
            print(f"[FAIL] {test_name} test failed")

    # 生成测试报告
    print(f"\n{'='*80}")
    print("Test Results Summary")
    print("=" * 80)

    passed_tests = sum(test_results.values())
    total_tests = len(test_results)

    print(f"Total tests: {total_tests}")
    print(f"Passed tests: {passed_tests}")
    print(f"Failed tests: {total_tests - passed_tests}")
    print(f"Success rate: {passed_tests/total_tests:.1%}")

    print("\nDetailed results:")
    for test_name, success in test_results.items():
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {test_name}: {status}")

    if passed_tests == total_tests:
        print("\n[SUCCESS] All core function tests passed! System is ready.")
        print("\nNext steps:")
        print("1. Run 'python enhanced_nonprice_ta_system/enhanced_hibor_analyzer.py' for full analysis")
        print("2. Check output files in 'enhanced_hibor_data/' directory")
    else:
        print(f"\n[WARNING] {total_tests - passed_tests} tests failed, need to check related modules.")

    return test_results

if __name__ == "__main__":
    results = main()