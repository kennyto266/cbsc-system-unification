#!/usr/bin/env python3
"""
測試高級技術分析信號系統
Test Advanced Technical Analysis Signal System
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from indicators.advanced_ta_signals import AdvancedTechnicalSignals
    from data.historical_data_extender import extend_data_records

    print("=" * 80)
    print("Advanced Technical Analysis Signal System Test")
    print("高級技術分析信號系統測試")
    print("=" * 80)
    print()

    # 創建測試數據
    test_data = []
    for i in range(20):
        date = f"2025-01-{(i+1):02d}"
        base_value = 100.0 + (i * 0.5) + (i % 5 - 2) * 0.1  # 添加一些波動
        test_data.append({
            'date': date,
            'monetary_base': base_value,
            'm1': base_value * 3.2,
            'm2': base_value * 6.5,
            'interbank_rate': base_value / 100
        })

    print(f"Test data: {len(test_data)} records")
    print("Sample record:", test_data[0])
    print()

    # 測試數據擴展
    print("=== Testing Data Extension ===")
    extension_result = extend_data_records(test_data, 1000, 'hybrid_approach')

    if extension_result.get('success'):
        extended_data = extension_result['data']
        print(f"[OK] Data extension: {len(test_data)} -> {len(extended_data)} records")
        print(f"Extension ratio: {extension_result['extension_ratio']:.2f}x")
    else:
        print(f"[FAIL] Data extension failed: {extension_result.get('error', 'Unknown')}")
        extended_data = test_data

    print()

    # 測試高級信號生成
    print("=== Testing Advanced Signal Generation ===")
    advanced_signals = AdvancedTechnicalSignals()
    result = advanced_signals.generate_enhanced_signals(
        data=extended_data,
        data_type='monetary_base',
        extend_to_1000=False,  # 已經擴展過了
        optimize_signals=True
    )

    if result.get('success'):
        print(f"[OK] Advanced signals generated successfully")
        print(f"Signal Quality Score: {result.get('signal_quality_score', 0):.2f}/10")
        print(f"Processed Records: {result.get('processed_records', 0)}")
        print(f"Numeric Columns: {result.get('numeric_columns', 0)}")

        recommendations = result.get('recommendations', [])
        if recommendations:
            print("\nTrading Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")

        # 顯示指標信息
        indicators = result.get('indicators', {})
        if 'success' in indicators and indicators['success']:
            print(f"\nIndicators Calculated: {indicators.get('total_indicators', 0)}")

            # 顯示第一個指標的樣本
            if indicators['indicators']:
                first_col = list(indicators['indicators'].keys())[0]
                first_indicators = indicators['indicators'][first_col]
                print(f"First indicator ('{first_col}') has {len(first_indicators)} types")
    else:
        print(f"[FAIL] Advanced signals failed: {result.get('error', 'Unknown error')}")

    print("\n=== Performance Test ===")
    import time
    start_time = time.time()

    # 測試多次生成時間
    test_iterations = 3
    for i in range(test_iterations):
        print(f"Running test iteration {i+1}/{test_iterations}...")
        test_result = advanced_signals.generate_enhanced_signals(
            data=extended_data[:100],  # 使用較少數據加快測試
            data_type='monetary_base',
            extend_to_1000=False,
            optimize_signals=False
        )
        if not test_result.get('success'):
            print(f"[FAIL] Iteration {i+1} failed")

    end_time = time.time()
    avg_time = (end_time - start_time) / test_iterations
    print(f"\nPerformance: Average {avg_time:.2f} seconds per analysis")
    print(f"Throughput: {len(extended_data[:100]) / avg_time:.1f} records/second")

except ImportError as e:
    print(f"[IMPORT ERROR] {e}")
    print("Make sure all required modules are available")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)