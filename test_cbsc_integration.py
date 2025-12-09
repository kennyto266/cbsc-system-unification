"""
CBSC Integration Test
CBSC組件集成測試

Test script for CBSC models and data integration functionality.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_cbsc_models():
    """測試CBSC模型"""
    print("=== 測試CBSC模型 ===")

    try:
        from models.cbsc_models import create_sample_cbsc_contract, parse_warrant_sentiment_csv

        # 測試合約模型
        contract = create_sample_cbsc_contract()
        print(f"✓ CBSC合約模型: {contract.ticker} ({contract.cbsc_type})")

        # 測試情緒數據解析
        sentiment_path = Path("CODEX--/warrant_sentiment_daily.csv")
        if sentiment_path.exists():
            sentiment_data = parse_warrant_sentiment_csv(str(sentiment_path))
            print(f"✓ 成功解析 {len(sentiment_data)} 條情緒記錄")

            if sentiment_data:
                latest = sentiment_data[-1]
                print(f"  最新情緒: {latest.sentiment_level} ({latest.sentiment_strength:.3f})")
                print(f"  數據日期: {latest.date}")
        else:
            print(f"⚠ 情緒數據文件不存在: {sentiment_path}")

        return True

    except Exception as e:
        print(f"✗ CBSC模型測試失敗: {e}")
        return False

async def test_cbsc_adapter():
    """測試CBSC數據適配器"""
    print("\n=== 測試CBSC數據適配器 ===")

    try:
        from models.cbsc_models import WarrantSentiment, SentimentLevel, SignalType

        # 模擬情緒數據處理
        sentiment_path = Path("CODEX--/warrant_sentiment_daily.csv")
        if sentiment_path.exists():
            # 簡單的數據質量檢查
            import pandas as pd
            df = pd.read_csv(sentiment_path)

            print(f"✓ 情緒數據文件: {len(df)} 條記錄")
            print(f"  數據日期範圍: {df['Date'].min()} 到 {df['Date'].max()}")

            # 檢查情緒等級分佈
            sentiment_counts = df['Sentiment_Level'].value_counts()
            print(f"  情緒等級分佈:")
            for level, count in sentiment_counts.items():
                print(f"    {level}: {count}")

            # 檢查信號分佈
            signal_counts = df['Signal'].value_counts()
            print(f"  信號分佈:")
            for signal, count in signal_counts.items():
                signal_name = "買入牛證" if signal == 1 else "持有" if signal == 0 else "買入熊證"
                print(f"    {signal_name}: {count}")

            return True
        else:
            print(f"⚠ 情緒數據文件不存在: {sentiment_path}")
            return False

    except Exception as e:
        print(f"✗ CBSC適配器測試失敗: {e}")
        return False

def test_data_processing_performance():
    """測試數據處理性能"""
    print("\n=== 測試數據處理性能 ===")

    try:
        import time
        import pandas as pd
        from models.cbsc_models import parse_warrant_sentiment_csv

        sentiment_path = Path("CODEX--/warrant_sentiment_daily.csv")
        if not sentiment_path.exists():
            print(f"⚠ 情緒數據文件不存在: {sentiment_path}")
            return False

        # 測試解析性能
        start_time = time.time()
        sentiment_data = parse_warrant_sentiment_csv(str(sentiment_path))
        parse_time = time.time() - start_time

        print(f"✓ 解析 {len(sentiment_data)} 條記錄耗時: {parse_time:.3f} 秒")

        # 測試數據處理性能
        start_time = time.time()
        processed_data = []
        for record in sentiment_data:
            processed_record = {
                'date': record.date,
                'sentiment_strength': record.sentiment_strength,
                'total_turnover': record.total_turnover,
                'is_extreme': record.get_extreme_signal()
            }
            processed_data.append(processed_record)
        process_time = time.time() - start_time

        print(f"✓ 處理 {len(processed_data)} 條記錄耗時: {process_time:.3f} 秒")

        # 性能目標：1年數據（~250條記錄）在30秒內完成
        records_per_year = 250
        estimated_year_time = (parse_time + process_time) * (records_per_year / len(sentiment_data))

        print(f"✓ 處理1年數據預計耗時: {estimated_year_time:.3f} 秒")

        if estimated_year_time < 30:
            print(f"✓ 性能目標達成！目標: <30秒, 實際: {estimated_year_time:.3f}秒")
            return True
        else:
            print(f"⚠ 性能目標未達成。目標: <30秒, 實際: {estimated_year_time:.3f}秒")
            return False

    except Exception as e:
        print(f"✗ 性能測試失敗: {e}")
        return False

async def main():
    """主測試函數"""
    print("CBSC集成測試開始...\n")

    # 運行所有測試
    test_results = []

    # 測試CBSC模型
    result1 = test_cbsc_models()
    test_results.append(("CBSC模型", result1))

    # 測試CBSC適配器
    result2 = await test_cbsc_adapter()
    test_results.append(("CBSC適配器", result2))

    # 測試性能
    result3 = test_data_processing_performance()
    test_results.append(("數據處理性能", result3))

    # 總結
    print("\n=== 測試結果總結 ===")
    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✓ 通過" if result else "✗ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n總體結果: {passed}/{total} 測試通過")

    if passed == total:
        print("🎉 所有測試通過！CBSC集成準備就緒。")
    else:
        print("⚠ 部分測試失敗，請檢查相關組件。")

if __name__ == "__main__":
    asyncio.run(main())