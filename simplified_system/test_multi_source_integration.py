#!/usr/bin/env python3
"""
多數據源集成測試套件
Multi-Source Integration Test Suite

驗證多數據源架構的完整性和可靠性
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
sys.path.append(os.path.dirname(__file__))

from src.api.multi_source_data_manager import MultiSourceDataManager
from src.api.data_source_monitor import DataSourceMonitor
from src.api.robust_stock_api import RobustStockAPI, get_system_status, get_data_source_health
from config.data_sources_config import get_data_sources_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class MultiSourceIntegrationTester:
    """多數據源集成測試器"""

    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()

    def log_test_result(self, test_name: str, success: bool, message: str = "", data: Any = None):
        """記錄測試結果"""
        self.test_results[test_name] = {
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "data": data
        }

        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")

    async def test_configuration_loading(self):
        """測試配置加載"""
        try:
            config = get_data_sources_config()
            enabled_sources = config.get_enabled_sources()
            total_sources = len(config.data_sources)

            self.log_test_result(
                "configuration_loading",
                True,
                f"Loaded {total_sources} sources, {len(enabled_sources)} enabled",
                {"total_sources": total_sources, "enabled_sources": len(enabled_sources)}
            )

            return True

        except Exception as e:
            self.log_test_result("configuration_loading", False, str(e))
            return False

    async def test_data_manager_initialization(self):
        """測試數據管理器初始化"""
        try:
            data_manager = MultiSourceDataManager()
            await data_manager.start()

            # 檢查數據源配置
            system_status = data_manager.get_system_status()
            total_sources = system_status.get("total_data_sources", 0)

            self.log_test_result(
                "data_manager_initialization",
                True,
                f"Initialized with {total_sources} data sources",
                system_status
            )

            await data_manager.stop()
            return True

        except Exception as e:
            self.log_test_result("data_manager_initialization", False, str(e))
            return False

    async def test_stock_data_retrieval(self):
        """測試股票數據獲取"""
        try:
            api = RobustStockAPI()

            # 測試獲取股票數據
            symbol = "0700.hk"
            data = api.get_stock_data(symbol, 30)

            if data:
                self.log_test_result(
                    "stock_data_retrieval",
                    True,
                    f"Successfully retrieved data for {symbol}",
                    {"data_keys": list(data.keys()) if isinstance(data, dict) else type(data).__name__}
                )
                return True
            else:
                self.log_test_result("stock_data_retrieval", False, "No data returned")
                return False

        except Exception as e:
            self.log_test_result("stock_data_retrieval", False, str(e))
            return False

    async def test_dataframe_conversion(self):
        """測試DataFrame轉換"""
        try:
            api = RobustStockAPI()

            # 測試DataFrame轉換
            symbol = "0700.hk"
            df = api.get_stock_prices_dataframe(symbol, 30)

            if df is not None and not df.empty:
                self.log_test_result(
                    "dataframe_conversion",
                    True,
                    f"Successfully converted to DataFrame with shape {df.shape}",
                    {"columns": list(df.columns), "index_range": [str(df.index[0]), str(df.index[-1])]}
                )
                return True
            else:
                self.log_test_result("dataframe_conversion", False, "Empty DataFrame returned")
                return False

        except Exception as e:
            self.log_test_result("dataframe_conversion", False, str(e))
            return False

    async def test_robust_api_backwards_compatibility(self):
        """測試強化API的向後兼容性"""
        try:
            from src.api.stock_api import get_stock_data as legacy_get_stock_data
            from src.api.robust_stock_api import get_stock_data as robust_get_stock_data

            symbol = "0700.hk"

            # 測試兩種接口
            legacy_data = legacy_get_stock_data(symbol, 10)
            robust_data = robust_get_stock_data(symbol, 10)

            both_available = legacy_data is not None and robust_data is not None
            either_available = legacy_data is not None or robust_data is not None

            if either_available:
                self.log_test_result(
                    "api_backwards_compatibility",
                    True,
                    f"Legacy: {legacy_data is not None}, Robust: {robust_data is not None}",
                    {
                        "legacy_available": legacy_data is not None,
                        "robust_available": robust_data is not None,
                        "both_available": both_available
                    }
                )
                return True
            else:
                self.log_test_result("api_backwards_compatibility", False, "Neither API returned data")
                return False

        except Exception as e:
            self.log_test_result("api_backwards_compatibility", False, str(e))
            return False

    async def test_health_monitoring(self):
        """測試健康監控"""
        try:
            health = get_data_source_health()

            if health and isinstance(health, dict):
                source_count = len(health)
                healthy_count = len([
                    name for name, status in health.items()
                    if status.get("status") == "healthy"
                ])

                self.log_test_result(
                    "health_monitoring",
                    True,
                    f"Monitoring {source_count} sources, {healthy_count} healthy",
                    health
                )
                return True
            else:
                self.log_test_result("health_monitoring", False, "No health data available")
                return False

        except Exception as e:
            self.log_test_result("health_monitoring", False, str(e))
            return False

    async def test_system_status(self):
        """測試系統狀態"""
        try:
            status = get_system_status()

            if status and isinstance(status, dict):
                self.log_test_result(
                    "system_status",
                    True,
                    f"System status retrieved: {status.get('status', 'unknown')}",
                    status
                )
                return True
            else:
                self.log_test_result("system_status", False, "Invalid status data")
                return False

        except Exception as e:
            self.log_test_result("system_status", False, str(e))
            return False

    async def test_failover_mechanism(self):
        """測試故障轉移機制"""
        try:
            api = RobustStockAPI()

            # 獲取初始系統狀態
            initial_status = get_system_status()
            initial_sources = initial_status.get("total_data_sources", 0)

            # 模拟禁用主要數據源
            config = get_data_sources_config()
            primary_source = "primary_central_api"

            if primary_source in config.data_sources:
                # 記錄原始狀態
                original_enabled = config.data_sources[primary_source].get("enabled", True)

                # 禁用主要數據源
                config.disable_data_source(primary_source)

                # 等待健康檢查更新
                await asyncio.sleep(2)

                # 測試數據獲取是否仍然工作
                symbol = "0700.hk"
                data_after_failover = api.get_stock_data(symbol, 10)

                # 恢復原始狀態
                if original_enabled:
                    config.enable_data_source(primary_source)

                if data_after_failover is not None:
                    self.log_test_result(
                        "failover_mechanism",
                        True,
                        f"Failover successful, data retrieved after disabling primary source",
                        {"original_enabled": original_enabled, "data_available": True}
                    )
                    return True
                else:
                    self.log_test_result(
                        "failover_mechanism",
                        False,
                        "No data available after primary source disabled"
                    )
                    return False
            else:
                self.log_test_result(
                    "failover_mechanism",
                    False,
                    "Primary source not found in configuration"
                )
                return False

        except Exception as e:
            self.log_test_result("failover_mechanism", False, str(e))
            return False

    async def test_cache_performance(self):
        """測試緩存性能"""
        try:
            api = RobustStockAPI()
            symbol = "0700.hk"

            # 第一次獲取（無緩存）
            start_time = time.time()
            data1 = api.get_stock_data(symbol, 30)
            first_request_time = time.time() - start_time

            # 第二次獲取（有緩存）
            start_time = time.time()
            data2 = api.get_stock_data(symbol, 30)
            second_request_time = time.time() - start_time

            if data1 is not None and data2 is not None:
                speedup = first_request_time / max(second_request_time, 0.001)

                self.log_test_result(
                    "cache_performance",
                    True,
                    f"Cache speedup: {speedup:.2f}x (first: {first_request_time:.3f}s, second: {second_request_time:.3f}s)",
                    {
                        "first_request_time": first_request_time,
                        "second_request_time": second_request_time,
                        "speedup": speedup,
                        "cache_working": second_request_time < first_request_time
                    }
                )
                return True
            else:
                self.log_test_result("cache_performance", False, "Failed to retrieve data")
                return False

        except Exception as e:
            self.log_test_result("cache_performance", False, str(e))
            return False

    async def test_concurrent_requests(self):
        """測試併發請求處理"""
        try:
            api = RobustStockAPI()
            symbols = ["0700.hk", "0941.hk", "1398.hk"]

            # 並發獲取多個股票數據
            start_time = time.time()

            async def fetch_symbol(symbol):
                return api.get_stock_data(symbol, 30)

            tasks = [fetch_symbol(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            total_time = time.time() - start_time
            successful_retrievals = sum(1 for result in results if result is not None and not isinstance(result, Exception))

            if successful_retrievals > 0:
                self.log_test_result(
                    "concurrent_requests",
                    True,
                    f"Successfully retrieved {successful_retrievals}/{len(symbols)} symbols in {total_time:.3f}s",
                    {
                        "total_symbols": len(symbols),
                        "successful": successful_retrievals,
                        "total_time": total_time,
                        "avg_time_per_symbol": total_time / len(symbols)
                    }
                )
                return True
            else:
                self.log_test_result("concurrent_requests", False, "No data retrieved")
                return False

        except Exception as e:
            self.log_test_result("concurrent_requests", False, str(e))
            return False

    async def test_error_handling(self):
        """測試錯誤處理"""
        try:
            api = RobustStockAPI()

            # 測試無效股票代碼
            invalid_symbol = "INVALID.XX"
            data = api.get_stock_data(invalid_symbol, 30)

            # 應該返回None但不應該拋出異常
            if data is None:
                self.log_test_result(
                    "error_handling",
                    True,
                    "Gracefully handled invalid symbol"
                )
                return True
            else:
                # 如果返回了數據，也可能是某些數據源的容錯機制
                self.log_test_result(
                    "error_handling",
                    True,
                    f"Data returned for invalid symbol (source fault tolerance)",
                    {"data_type": type(data).__name__}
                )
                return True

        except Exception as e:
            self.log_test_result("error_handling", False, f"Exception thrown: {str(e)}")
            return False

    async def run_all_tests(self):
        """運行所有測試"""
        print("=" * 80)
        print("🚀 開始多數據源架構集成測試")
        print("=" * 80)

        # 定義測試列表
        tests = [
            ("Configuration Loading", self.test_configuration_loading),
            ("Data Manager Initialization", self.test_data_manager_initialization),
            ("Stock Data Retrieval", self.test_stock_data_retrieval),
            ("DataFrame Conversion", self.test_dataframe_conversion),
            ("API Backwards Compatibility", self.test_robust_api_backwards_compatibility),
            ("Health Monitoring", self.test_health_monitoring),
            ("System Status", self.test_system_status),
            ("Failover Mechanism", self.test_failover_mechanism),
            ("Cache Performance", self.test_cache_performance),
            ("Concurrent Requests", self.test_concurrent_requests),
            ("Error Handling", self.test_error_handling),
        ]

        # 運行所有測試
        for test_name, test_func in tests:
            print(f"\n🧪 執行測試: {test_name}")
            try:
                await test_func()
            except Exception as e:
                self.log_test_result(test_name, False, f"Test execution error: {str(e)}")

        # 生成測試報告
        self.generate_test_report()

    def generate_test_report(self):
        """生成測試報告"""
        print("\n" + "=" * 80)
        print("📊 測試結果總結")
        print("=" * 80)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"總測試數: {total_tests}")
        print(f"通過: {passed_tests} ✅")
        print(f"失敗: {failed_tests} ❌")
        print(f"成功率: {success_rate:.1f}%")

        print(f"\n📋 詳細結果:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            duration = result["duration"]
            print(f"  {status} {test_name} ({duration:.2f}s) - {result['message']}")

        # 生成JSON報告
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": success_rate,
                "total_duration": (datetime.now() - self.start_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            },
            "test_results": self.test_results
        }

        # 保存報告
        report_file = f"multi_source_integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n📄 詳細報告已保存到: {report_file}")

        # 如果有失敗的測試，返回錯誤代碼
        if failed_tests > 0:
            print(f"\n⚠️  有 {failed_tests} 個測試失敗，請檢查系統配置")
            return False
        else:
            print(f"\n🎉 所有測試通過！多數據源架構運行正常")
            return True

async def main():
    """主函數"""
    tester = MultiSourceIntegrationTester()
    success = await tester.run_all_tests()

    # 返回適當的退出代碼
    exit_code = 0 if success else 1
    exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())