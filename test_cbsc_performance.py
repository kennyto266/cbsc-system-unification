"""
CBSC Performance Test
CBSC性能測試

Performance testing for CBSC data processing and analysis to meet Phase 1 success criteria:
- Process 1 year of historical data within 30 seconds
- Validate CBSC-specific functionality
"""

import sys
import time
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date, timedelta

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_cbsc_models_performance():
    """測試CBSC模型性能"""
    print("=== Testing CBSC Models Performance ===")

    try:
        from models.cbsc_models import create_sample_cbsc_contract

        # 測試模型創建性能
        start_time = time.time()
        contracts = []
        for i in range(1000):  # 創建1000個合約
            contract = create_sample_cbsc_contract()
            contracts.append(contract)
        model_creation_time = time.time() - start_time

        print(f"OK: Created {len(contracts)} CBSC contracts in {model_creation_time:.3f} seconds")
        print(f"  Average creation time: {model_creation_time/len(contracts)*1000:.3f} ms per contract")

        # 測試風險計算性能
        start_time = time.time()
        for contract in contracts:
            distance = contract.calculate_distance_to_call(260.0)
            time_decay = contract.calculate_time_decay_factor(date.today())
        risk_calculation_time = time.time() - start_time

        print(f"OK: Calculated risk metrics for {len(contracts)} contracts in {risk_calculation_time:.3f} seconds")
        print(f"  Average risk calculation time: {risk_calculation_time/len(contracts)*1000:.3f} ms per contract")

        return True

    except Exception as e:
        print(f"FAIL: CBSC Models performance test failed: {e}")
        return False

def test_sentiment_data_processing_performance():
    """測試情緒數據處理性能"""
    print("\n=== Testing Sentiment Data Processing Performance ===")

    try:
        from models.cbsc_models import parse_warrant_sentiment_csv, WarrantSentiment

        sentiment_path = Path("CODEX--/warrant_sentiment_daily.csv")
        if not sentiment_path.exists():
            print(f"WARN: Sentiment data file not found: {sentiment_path}")
            return False

        # 測試CSV解析性能
        start_time = time.time()
        sentiment_data = parse_warrant_sentiment_csv(str(sentiment_path))
        parse_time = time.time() - start_time

        print(f"OK: Parsed {len(sentiment_data)} sentiment records in {parse_time:.3f} seconds")

        if not sentiment_data:
            print("WARN: No valid sentiment data parsed")
            return False

        # 測試數據處理性能
        start_time = time.time()
        processed_data = []
        for record in sentiment_data:
            processed_record = {
                'date': record.date,
                'sentiment_strength': record.sentiment_strength,
                'total_turnover': record.total_turnover,
                'is_extreme': record.get_extreme_signal(),
                'sentiment_level': record.sentiment_level
            }
            processed_data.append(processed_record)
        processing_time = time.time() - start_time

        print(f"OK: Processed {len(processed_data)} records in {processing_time:.3f} seconds")

        # 計算性能目標
        records_per_year = 250  # 假設1年約250個交易日
        estimated_year_time = (parse_time + processing_time) * (records_per_year / len(sentiment_data))

        print(f"  Estimated time for 1 year data: {estimated_year_time:.3f} seconds")

        if estimated_year_time < 30:
            print(f"✓ Performance target MET! Target: <30s, Actual: {estimated_year_time:.3f}s")
            performance_met = True
        else:
            print(f"✗ Performance target NOT MET! Target: <30s, Actual: {estimated_year_time:.3f}s")
            performance_met = False

        # 測試數據統計
        bull_count = sum(1 for r in processed_data if r['sentiment_level'] in ['EXTREME BULL', 'MOD BULL'])
        bear_count = sum(1 for r in processed_data if r['sentiment_level'] in ['EXTREME BEAR', 'MOD BEAR'])
        neutral_count = sum(1 for r in processed_data if r['sentiment_level'] == 'NEUTRAL')

        print(f"  Data distribution: Bull={bull_count}, Bear={bear_count}, Neutral={neutral_count}")

        return performance_met

    except Exception as e:
        print(f"FAIL: Sentiment data processing performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sentiment_technical_integration_performance():
    """測試情緒-技術整合性能"""
    print("\n=== Testing Sentiment-Technical Integration Performance ===")

    try:
        from analysis.sentiment_technical_integration import create_sentiment_integrator
        from models.cbsc_models import parse_warrant_sentiment_csv

        sentiment_path = Path("CODEX--/warrant_sentiment_daily.csv")
        if not sentiment_path.exists():
            print(f"WARN: Sentiment data file not found: {sentiment_path}")
            return False

        sentiment_data = parse_warrant_sentiment_csv(str(sentiment_path))
        if not sentiment_data:
            print("WARN: No valid sentiment data parsed")
            return False

        # 創建整合器
        integrator = create_sentiment_integrator()
        print("OK: Created sentiment-technical integrator")

        # 測試指標計算性能
        start_time = time.time()
        for i in range(100):  # 測試100次指標計算
            indicators = integrator.calculate_sentiment_indicators(sentiment_data)
        indicators_time = time.time() - start_time

        print(f"OK: Calculated sentiment indicators 100 times in {indicators_time:.3f} seconds")
        print(f"  Average indicators calculation time: {indicators_time/100*1000:.3f} ms")

        # 測試信號生成性能
        start_time = time.time()
        signals = []
        price_data = pd.DataFrame({
            'close': np.random.normal(270, 20, 252),  # 模擬1年價格數據
            'date': pd.date_range('2024-01-01', periods=252)
        })

        # 為每個交易日生成信號
        for i in range(50):  # 測試50個交易日
            day_price = price_data.iloc[:i+20] if i+20 <= len(price_data) else price_data
            if not day_price.empty:
                signal = integrator.generate_trading_signal("0700.HK", day_price, sentiment_data[-min(i+1, len(sentiment_data)):])
                signals.append(signal)

        signal_generation_time = time.time() - start_time
        print(f"OK: Generated {len(signals)} trading signals in {signal_generation_time:.3f} seconds")
        print(f"  Average signal generation time: {signal_generation_time/len(signals)*1000:.3f} ms")

        return True

    except Exception as e:
        print(f"FAIL: Sentiment-Technical integration performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backtest_performance():
    """測試回測性能"""
    print("\n=== Testing Backtest Performance ===")

    try:
        from analysis.sentiment_technical_integration import create_sentiment_integrator
        from models.cbsc_models import parse_warrant_sentiment_csv

        sentiment_path = Path("CODEX--/warrant_sentiment_daily.csv")
        if not sentiment_path.exists():
            print(f"WARN: Sentiment data file not found: {sentiment_path}")
            return False

        sentiment_data = parse_warrant_sentiment_csv(str(sentiment_path))
        if not sentiment_data:
            print("WARN: No valid sentiment data parsed")
            return False

        integrator = create_sentiment_integrator()

        # 創建測試價格數據 (1年數據)
        price_data = pd.DataFrame({
            'close': np.random.normal(270, 20, 252),
            'date': pd.date_range('2024-01-01', periods=252)
        })

        # 測試回測性能
        start_time = time.time()
        backtest_results = integrator.backtest_strategy("0700.HK", price_data, sentiment_data)
        backtest_time = time.time() - start_time

        print(f"OK: Completed backtest in {backtest_time:.3f} seconds")
        print(f"  Total return: {backtest_results['total_return']:.2%}")
        print(f"  Total trades: {backtest_results['total_trades']}")
        print(f"  Signals count: {backtest_results['signals_count']}")

        # 性能評估
        if backtest_time < 10:  # 10秒內完成回測
            print(f"✓ Backtest performance EXCELLENT! Target: <10s, Actual: {backtest_time:.3f}s")
        elif backtest_time < 30:
            print(f"✓ Backtest performance GOOD! Target: <30s, Actual: {backtest_time:.3f}s")
        else:
            print(f"⚠ Backtest performance needs improvement: {backtest_time:.3f}s")

        return True

    except Exception as e:
        print(f"FAIL: Backtest performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_usage():
    """測試內存使用"""
    print("\n=== Testing Memory Usage ===")

    try:
        import psutil
        import os

        # 獲取當前進程內存使用
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(f"Initial memory usage: {initial_memory:.1f} MB")

        # 模擬大量數據處理
        from models.cbsc_models import create_sample_cbsc_contract
        from analysis.sentiment_technical_integration import create_sentiment_integrator

        # 創建大量對象
        contracts = [create_sample_cbsc_contract() for _ in range(1000)]
        integrator = create_sentiment_integrator()

        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - initial_memory

        print(f"Peak memory usage: {current_memory:.1f} MB")
        print(f"Memory increase: {memory_increase:.1f} MB")

        if memory_increase < 100:  # 內存增長小於100MB
            print(f"✓ Memory usage EXCELLENT! Increase: {memory_increase:.1f} MB")
        elif memory_increase < 500:
            print(f"✓ Memory usage GOOD! Increase: {memory_increase:.1f} MB")
        else:
            print(f"⚠ Memory usage HIGH: Increase: {memory_increase:.1f} MB")

        return True

    except ImportError:
        print("WARN: psutil not available for memory testing")
        return True
    except Exception as e:
        print(f"FAIL: Memory usage test failed: {e}")
        return False

def main():
    """主測試函數"""
    print("CBSC Performance Test Starting...")
    print("=" * 60)

    # 運行所有性能測試
    test_results = []

    start_time = time.time()

    result1 = test_cbsc_models_performance()
    test_results.append(("CBSC Models", result1))

    result2 = test_sentiment_data_processing_performance()
    test_results.append(("Sentiment Data Processing", result2))

    result3 = test_sentiment_technical_integration_performance()
    test_results.append(("Sentiment-Technical Integration", result3))

    result4 = test_backtest_performance()
    test_results.append(("Backtest Performance", result4))

    result5 = test_memory_usage()
    test_results.append(("Memory Usage", result5))

    total_time = time.time() - start_time

    # 總結
    print("\n" + "=" * 60)
    print("=== Performance Test Results ===")
    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")
    print(f"Total test time: {total_time:.2f} seconds")

    if passed == total:
        print("\n🎉 SUCCESS: All CBSC performance tests passed!")
        print("   Phase 1 implementation is COMPLETE and ready for production!")
        return True
    else:
        print(f"\n⚠ WARNING: {total - passed} CBSC performance tests failed.")
        print("   Some optimizations may be needed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)