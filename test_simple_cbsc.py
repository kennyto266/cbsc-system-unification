"""
Simple CBSC Test
CBSC組件簡單測試
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_cbsc_models():
    """測試CBSC模型"""
    print("=== Testing CBSC Models ===")

    try:
        from models.cbsc_models import create_sample_cbsc_contract, parse_warrant_sentiment_csv

        # 測試合約模型
        contract = create_sample_cbsc_contract()
        print(f"OK: CBSC Contract created: {contract.ticker} ({contract.cbsc_type})")

        # 測試情緒數據解析
        sentiment_path = Path("CODEX--/warrant_sentiment_daily.csv")
        if sentiment_path.exists():
            sentiment_data = parse_warrant_sentiment_csv(str(sentiment_path))
            print(f"OK: Parsed {len(sentiment_data)} sentiment records")

            if sentiment_data:
                latest = sentiment_data[-1]
                print(f"  Latest sentiment: {latest.sentiment_level} ({latest.sentiment_strength:.3f})")
                print(f"  Date: {latest.date}")
        else:
            print(f"WARN: Sentiment file not found: {sentiment_path}")

        return True

    except Exception as e:
        print(f"FAIL: CBSC Models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_processing():
    """測試數據處理"""
    print("\n=== Testing Data Processing ===")

    try:
        import time
        import pandas as pd
        from models.cbsc_models import parse_warrant_sentiment_csv

        sentiment_path = Path("CODEX--/warrant_sentiment_daily.csv")
        if not sentiment_path.exists():
            print(f"WARN: Sentiment file not found: {sentiment_path}")
            return False

        # 測試解析性能
        start_time = time.time()
        sentiment_data = parse_warrant_sentiment_csv(str(sentiment_path))
        parse_time = time.time() - start_time

        print(f"OK: Parsed {len(sentiment_data)} records in {parse_time:.3f} seconds")

        # 測試數據統計
        if sentiment_data:
            bull_count = sum(1 for record in sentiment_data if record.sentiment_level.value in ['EXTREME BULL', 'MOD BULL'])
            bear_count = sum(1 for record in sentiment_data if record.sentiment_level.value in ['EXTREME BEAR', 'MOD BEAR'])
            neutral_count = sum(1 for record in sentiment_data if record.sentiment_level.value == 'NEUTRAL')

            print(f"  Bull sentiment: {bull_count} records")
            print(f"  Bear sentiment: {bear_count} records")
            print(f"  Neutral sentiment: {neutral_count} records")

            # Performance test
            records_per_year = 250
            estimated_year_time = parse_time * (records_per_year / len(sentiment_data))
            print(f"  Estimated time for 1 year data: {estimated_year_time:.3f} seconds")

            if estimated_year_time < 30:
                print(f"OK: Performance target met! (< 30 seconds)")
                return True
            else:
                print(f"WARN: Performance target not met ({estimated_year_time:.3f} > 30 seconds)")
                return False

        return True

    except Exception as e:
        print(f"FAIL: Data processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("CBSC Simple Test Starting...\n")

    # 運行測試
    test_results = []

    result1 = test_cbsc_models()
    test_results.append(("CBSC Models", result1))

    result2 = test_data_processing()
    test_results.append(("Data Processing", result2))

    # 總結
    print("\n=== Test Results ===")
    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: All tests passed! CBSC integration ready.")
        return True
    else:
        print("WARNING: Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)