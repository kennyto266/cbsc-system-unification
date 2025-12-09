#!/usr/bin/env python3
"""
測試政府經濟數據技術分析信號系統
Test Government Economic Data Technical Analysis Signal System
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from indicators.government_ta_signals import (
    generate_signals_from_real_data,
    generate_all_signals_from_real_data
)

def test_monetary_base_signals():
    """測試貨幣基礎信號生成"""
    print("=" * 80)
    print("測試政府經濟數據技術分析信號系統")
    print("Testing Government Economic Data Technical Analysis Signal System")
    print("=" * 80)
    print("基於香港政府真實API的技術分析信號生成系統")
    print("Real-time Hong Kong Government API-based Technical Analysis Signal System")
    print()

    try:
        # 測試單個數據源
        print("Testing real data signal generation...")
        print("Fetching real HKMA government data...")
        print()

        print("=== Testing Monetary Base Signals (1000+ records) ===")
        monetary_signals = generate_signals_from_real_data('monetary_base', 1000)

        print(f"Monetary base signals: {monetary_signals.get('success', False)}")

        if monetary_signals.get('success'):
            print(f"Records analyzed: {monetary_signals['records_analyzed']}")
            print(f"Signal types: {list(monetary_signals.get('signal_types', {}).keys())}")

            # 顯示信號詳情
            signal_types = monetary_signals.get('signal_types', {})
            for signal_type, signal_data in signal_types.items():
                print(f"\n{signal_data.get('name', signal_type)}:")
                if 'buy_signals' in signal_data:
                    print(f"  Buy signals: {len(signal_data['buy_signals'])}")
                if 'sell_signals' in signal_data:
                    print(f"  Sell signals: {len(signal_data['sell_signals'])}")
                if 'trend' in signal_data:
                    print(f"  Trend: {signal_data['trend']} (strength: {signal_data.get('strength', 0):.3f})")
        else:
            print(f"Error: {monetary_signals.get('error', 'Unknown error')}")

        return monetary_signals.get('success', False)

    except Exception as e:
        print(f"Exception during testing: {e}")
        print("This may be due to network issues or API unavailability")
        return False

def test_all_signals():
    """測試所有數據源信號生成"""
    print("\n=== Testing All Data Sources (1000+ records each) ===")

    try:
        # 測試所有數據源
        all_signals_result = generate_all_signals_from_real_data(1000)

        if all_signals_result.get('success'):
            print(f"Overall success: True")
            print(f"Data sources processed: {all_signals_result['data_sources_processed']}")
            print(f"Total signals generated: {all_signals_result['total_signals_generated']}")
            print(f"Generation time: {all_signals_result['generation_time']}")

            # 顯示各數據源記錄數
            metadata = all_signals_result.get('metadata', {})
            records_per_source = metadata.get('records_per_source', {})
            print(f"\nRecords per source:")
            for source, count in records_per_source.items():
                print(f"  {source}: {count} records")

            # 顯示綜合信號
            composite_signals = all_signals_result.get('composite_signals', {})
            if composite_signals.get('success'):
                print(f"\nComposite Technical Score: {composite_signals.get('composite_score', 0):.3f}")

                individual_scores = composite_signals.get('individual_scores', {})
                if individual_scores:
                    print(f"\nIndividual Source Scores:")
                    for source, score_data in individual_scores.items():
                        print(f"  {source}: {score_data.get('score', 0):.3f} (weight: {score_data.get('weight', 0):.2f})")

                recommendations = composite_signals.get('recommendations', [])
                if recommendations:
                    print(f"\nTrading Recommendations:")
                    for rec in recommendations:
                        print(f"  {rec}")
            else:
                print(f"Composite signals failed: {composite_signals.get('error', 'Unknown error')}")

            return True
        else:
            print(f"Failed to generate all signals: {all_signals_result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"Exception during all signals testing: {e}")
        return False

def main():
    """主測試函數"""
    success_count = 0
    total_tests = 2

    # 測試1: 貨幣基礎信號
    if test_monetary_base_signals():
        success_count += 1

    # 測試2: 所有數據源信號
    if test_all_signals():
        success_count += 1

    # 總結
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Passed: {success_count}/{total_tests}")
    print(f"Failed: {total_tests - success_count}/{total_tests}")

    if success_count == total_tests:
        print("\nALL TESTS PASSED!")
        print("Government TA Signal System is ready for production use!")
        print("Successfully integrated with 1000+ real HKMA records")
    else:
        print("\nSOME TESTS FAILED")
        print("Please check network connectivity and API availability")

    print("\n=== Usage Examples ===")
    print("# Import the enhanced signal system")
    print("from test_government_ta_signals import test_monetary_base_signals")
    print("from indicators.government_ta_signals import generate_all_signals_from_real_data")
    print()
    print("# Generate signals from real monetary base data (1000+ records)")
    print("monetary_signals = generate_signals_from_real_data('monetary_base', 1000)")
    print()
    print("# Generate all signals from real government data")
    print("all_signals = generate_all_signals_from_real_data(1000)")
    print("print(f'Success: {all_signals[\"success\"]}')")
    print("print(f'Data sources: {all_signals[\"data_sources_processed\"]}')")
    print()
    print("System ready for real government data technical analysis!")

    return success_count == total_tests

if __name__ == "__main__":
    main()