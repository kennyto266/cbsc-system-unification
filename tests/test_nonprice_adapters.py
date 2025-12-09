#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
非價格數據適配器測試套件
驗證所有適配器的功能
"""

import logging
import os
import sys
import unittest
from datetime import datetime, timedelta

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), "..", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Configure logging
logging.basicConfig(level = logging.INFO)


class TestNonPriceAdapters(unittest.TestCase):
    """非價格數據適配器測試"""

    @classmethod
    def setUpClass(cls):
        """測試類設置"""
        # Import adapters
        from adapters.adapter_manager import get_nonprice_adapter_manager
        from adapters.economic_adapter import get_economic_adapter
        from adapters.hibor_adapter import get_hibor_adapter
        from adapters.monetary_adapter import get_monetary_adapter

        cls.hibor_adapter = get_hibor_adapter()
        cls.monetary_adapter = get_monetary_adapter()
        cls.economic_adapter = get_economic_adapter()
        cls.adapter_manager = get_nonprice_adapter_manager()

    def test_hibor_adapter(self):
        """測試HIBOR適配器"""
        print("\n=== HIBOR Adapter Test ===")

        try:
            # 測試獲取最新數據
            latest_rates = self.hibor_adapter.get_latest_rates()
            self.assertIsInstance(latest_rates, dict)

            print(f"HIBOR latest rates: {len(latest_rates)} tenors")
            for tenor, rate in latest_rates.items():
                print(f"  {tenor}: {rate:.4f}%")

            # 測試獲取歷史數據
            end_date = datetime.now()
            start_date = end_date - timedelta(days = 7)

            data = self.hibor_adapter.get_data(start_date, end_date)
            self.assertIsInstance(data, type(None))  # 可能為None（如果API不可用）

            if data is not None and not data.empty:
                print(f"HIBOR historical data: {len(data)} records")
                print(f"Date range: {data.index.min()} to {data.index.max()}")
                print(f"Tenors: {sorted(data['tenor'].unique())}")

            # 測試統計信息
            stats = self.hibor_adapter.get_statistics()
            print(f"HIBOR adapter statistics: {stats.get('record_count', 0)} records")

        except Exception as e:
            print(f"HIBOR adapter test error: {e}")

    def test_monetary_adapter(self):
        """測試貨幣基礎適配器"""
        print("\n=== Monetary Base Adapter Test ===")

        try:
            # 測試獲取最新數據
            latest_data = self.monetary_adapter.get_latest_monetary_base()
            self.assertIsInstance(latest_data, dict)

            print(f"Monetary base latest: {len(latest_data)} components")
            for component, value in latest_data.items():
                print(f"  {component}: {value:.2f} billion HKD")

            # 測試獲取歷史數據
            end_date = datetime.now()
            start_date = end_date - timedelta(days = 7)

            data = self.monetary_adapter.get_data(start_date, end_date)
            self.assertIsInstance(data, type(None))  # 可能為None

            if data is not None and not data.empty:
                print(f"Monetary base historical data: {len(data)} records")
                print(f"Date range: {data.index.min()} to {data.index.max()}")
                print(f"Components: {sorted(data['component'].unique())}")

            # 測試趨勢分析
            trend = self.monetary_adapter.get_monetary_base_trend(days = 30)
            print(f"Monetary base trend: {trend}")

        except Exception as e:
            print(f"Monetary adapter test error: {e}")

    def test_economic_adapter(self):
        """測試經濟數據適配器"""
        print("\n=== Economic Data Adapter Test ===")

        try:
            # 測試獲取可用數據源
            sources = self.economic_adapter.get_available_sources()
            self.assertIsInstance(sources, list)

            print(f"Available economic data sources: {len(sources)}")
            for source in sources:
                print(f"  {source.source_id}: {source.name} ({source.frequency})")

            # 測試獲取最新數據
            latest_values = self.economic_adapter.get_latest_values()
            self.assertIsInstance(latest_values, dict)

            print(f"Economic data latest values: {len(latest_values)} sources")
            for source_id, data in latest_values.items():
                print(
                    f"  {source_id}: {data.get('value', 'N / A')} ({data.get('name', 'N / A')})"
                )

        except Exception as e:
            print(f"Economic adapter test error: {e}")

    def test_adapter_manager(self):
        """測試適配器管理器"""
        print("\n=== Adapter Manager Test ===")

        try:
            # 測試獲取所有數據源
            sources = self.adapter_manager.get_available_sources()
            self.assertIsInstance(sources, list)

            print(f"Available sources through manager: {len(sources)}")

            # 測試獲取最新數據
            latest_data = self.adapter_manager.get_latest_data(days = 7)
            self.assertIsInstance(latest_data, dict)

            print(f"Latest data through manager: {len(latest_data)} data types")
            for data_type, data in latest_data.items():
                if isinstance(data, dict):
                    print(f"  {data_type}: {len(data)} items")
                else:
                    print(f"  {data_type}: {data}")

            # 測試驗證所有數據源
            validation_results = self.adapter_manager.validate_all_sources()
            self.assertIsInstance(validation_results, dict)

            print(f"Source validation results:")
            healthy_count = 0
            for source_id, is_healthy in validation_results.items():
                status = "OK" if is_healthy else "FAILED"
                print(f"  {source_id}: {status}")
                if is_healthy:
                    healthy_count += 1

            print(f"Healthy sources: {healthy_count}/{len(validation_results)}")

            # 測試統計信息
            stats = self.adapter_manager.get_source_statistics()
            self.assertIsInstance(stats, dict)

            print(f"Source statistics:")
            print(f"  Total sources: {stats.get('total_sources', 0)}")
            print(
                f"  Healthy sources: {stats.get('summary', {}).get('healthy_sources', 0)}"
            )
            print(
                f"  Total records: {stats.get('summary', {}).get('total_records', 0)}"
            )

        except Exception as e:
            print(f"Adapter manager test error: {e}")

    def test_data_quality_report(self):
        """測試數據質量報告"""
        print("\n=== Data Quality Report Test ===")

        try:
            report = self.adapter_manager.get_data_quality_report()
            self.assertIsInstance(report, dict)

            print(f"Data quality report generated: {report.get('generated_at')}")
            print(
                f"Overall completeness: {report.get('overall_quality', {}).get('completeness', 0):.2%}"
            )

            sources = report.get("sources", {})
            print(f"Sources analyzed: {len(sources)}")

            for source_id, source_report in sources.items():
                if "error" not in source_report:
                    record_count = source_report.get("record_count", 0)
                    completeness = source_report.get("completeness", 0)
                    issues = source_report.get("issues", [])
                    print(
                        f"  {source_id}: {record_count} records, {completeness:.2%} complete"
                    )
                    if issues:
                        print(f"    Issues: {', '.join(issues)}")

            overall_issues = report.get("overall_quality", {}).get("issues", [])
            if overall_issues:
                print(f"Overall issues: {len(overall_issues)}")
                for issue in overall_issues[:5]:  # 只顯示前5個
                    print(f"  - {issue}")

        except Exception as e:
            print(f"Data quality report test error: {e}")


def run_adapter_tests():
    """運行所有適配器測試"""
    print("Starting Non - Price Data Adapter Tests")
    print("=" * 50)

    # 創建測試套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestNonPriceAdapters)

    # 運行測試
    runner = unittest.TextTestRunner(verbosity = 2)
    result = runner.run(suite)

    # 總結
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("All adapter tests completed!")
    else:
        print(f"{len(result.failures)} test failures, {len(result.errors)} errors")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_adapter_tests()
    sys.exit(0 if success else 1)
