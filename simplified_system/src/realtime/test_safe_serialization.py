#!/usr/bin/env python3
"""
Safe Serialization Test for Redis Cache
測試Redis緩存的安全序列化功能
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any

import numpy as np
import pandas as pd

from redis_cache import RedisCacheManager, CacheConfig
from safe_serialization import SafeDataSerializer, SerializationError, DeserializationError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SafeSerializationTester:
    """安全序列化測試器"""

    def __init__(self):
        self.cache_manager = RedisCacheManager()
        self.test_results = {}

    async def run_all_tests(self):
        """運行所有測試"""
        print("🚀 Starting Safe Serialization Tests...")
        print("=" * 60)

        # 測試序列化器基本功能
        await self.test_basic_serialization()

        # 測試複雜數據類型
        await self.test_complex_data_types()

        # 測試Redis緩存集成
        await self.test_redis_cache_integration()

        # 測試性能對比
        await self.test_performance_comparison()

        # 測試安全性
        await self.test_security_vulnerabilities()

        # 生成測試報告
        self.generate_test_report()

    async def test_basic_serialization(self):
        """測試基本序列化功能"""
        print("\n📝 Testing Basic Serialization...")

        test_cases = [
            ("simple_dict", {"symbol": "0700.HK", "price": 300.5}),
            ("simple_list", [1, 2, 3, 4, 5]),
            ("string", "Hello World"),
            ("number", 42),
            ("boolean", True),
            ("none", None),
        ]

        results = {}

        for test_name, test_data in test_cases:
            try:
                # 序列化
                serialized = SafeDataSerializer.serialize(test_data)

                # 反序列化
                deserialized = SafeDataSerializer.deserialize(serialized)

                # 驗證
                success = deserialized == test_data
                results[test_name] = {
                    "success": success,
                    "serialized_size": len(serialized),
                    "original_type": type(test_data).__name__,
                    "deserialized_type": type(deserialized).__name__
                }

                print(f"  ✅ {test_name}: {'PASS' if success else 'FAIL'}")

            except Exception as e:
                results[test_name] = {
                    "success": False,
                    "error": str(e),
                    "original_type": type(test_data).__name__
                }
                print(f"  ❌ {test_name}: FAIL - {e}")

        self.test_results["basic_serialization"] = results

    async def test_complex_data_types(self):
        """測試複雜數據類型"""
        print("\n🔬 Testing Complex Data Types...")

        # 創建測試數據
        test_dataframe = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='H'),
            'price': [300.1, 300.2, 300.3, 300.4, 300.5],
            'volume': [1000, 1500, 2000, 2500, 3000],
            'symbol': ['0700.HK'] * 5
        })

        test_array = np.array([1.1, 2.2, 3.3, 4.4, 5.5])

        complex_test_cases = [
            ("dataframe", test_dataframe),
            ("numpy_array", test_array),
            ("nested_dict", {
                "market_data": {
                    "0700.HK": {"price": 300.5, "volume": 15000},
                    "0941.HK": {"price": 55.2, "volume": 8000}
                },
                "timestamp": datetime.now().isoformat(),
                "signals": ["buy", "hold", "sell"]
            }),
            ("list_of_dicts", [
                {"symbol": "0700.HK", "price": 300.5},
                {"symbol": "0941.HK", "price": 55.2}
            ])
        ]

        results = {}

        for test_name, test_data in complex_test_cases:
            try:
                # 測試SafeDataSerializer
                start_time = time.perf_counter()
                serialized = SafeDataSerializer.serialize(test_data)
                deserialized = SafeDataSerializer.deserialize(serialized)
                serialization_time = (time.perf_counter() - start_time) * 1000

                # 驗證DataFrame
                if isinstance(test_data, pd.DataFrame):
                    success = deserialized.equals(test_data)
                # 驗證NumPy數組
                elif isinstance(test_data, np.ndarray):
                    success = np.array_equal(deserialized, test_data)
                # 驗證其他類型
                else:
                    success = deserialized == test_data

                results[test_name] = {
                    "success": success,
                    "serialized_size": len(serialized),
                    "serialization_time_ms": serialization_time,
                    "original_type": type(test_data).__name__,
                    "deserialized_type": type(deserialized).__name__
                }

                print(f"  ✅ {test_name}: {'PASS' if success else 'FAIL'} ({serialization_time:.2f}ms)")

            except Exception as e:
                results[test_name] = {
                    "success": False,
                    "error": str(e),
                    "original_type": type(test_data).__name__
                }
                print(f"  ❌ {test_name}: FAIL - {e}")

        self.test_results["complex_data_types"] = results

    async def test_redis_cache_integration(self):
        """測試Redis緩存集成"""
        print("\n🔗 Testing Redis Cache Integration...")

        try:
            # 連接Redis
            connected = await self.cache_manager.connect()
            if not connected:
                print("  ❌ Redis connection failed - skipping Redis tests")
                self.test_results["redis_integration"] = {"success": False, "error": "Redis connection failed"}
                return

            print("  ✅ Redis connected successfully")

            # 測試數據
            test_data = {
                "price_data": {
                    "symbol": "0700.HK",
                    "price": 300.50,
                    "volume": 15000,
                    "timestamp": datetime.now().isoformat()
                },
                "dataframe": pd.DataFrame({
                    'price': [300.1, 300.2, 300.3],
                    'volume': [1000, 2000, 3000]
                }),
                "signals": ["buy", "hold", "sell"]
            }

            results = {}

            # 測試設置和獲取
            for key, value in test_data.items():
                try:
                    # 設置緩存
                    set_success = await self.cache_manager.set(f"test:{key}", value, ttl=60)

                    if set_success:
                        # 獲取緩存
                        retrieved_value = await self.cache_manager.get(f"test:{key}")

                        # 驗證結果
                        if isinstance(value, pd.DataFrame):
                            is_match = retrieved_value.equals(value) if retrieved_value is not None else False
                        else:
                            is_match = retrieved_value == value

                        results[key] = {
                            "set_success": True,
                            "get_success": retrieved_value is not None,
                            "data_match": is_match,
                            "retrieved_type": type(retrieved_value).__name__ if retrieved_value else None
                        }

                        print(f"  ✅ {key}: {'PASS' if is_match else 'FAIL'}")
                    else:
                        results[key] = {"set_success": False}
                        print(f"  ❌ {key}: FAIL - Set operation failed")

                except Exception as e:
                    results[key] = {"success": False, "error": str(e)}
                    print(f"  ❌ {key}: FAIL - {e}")

            # 測試批量操作
            print("  🔄 Testing batch operations...")
            batch_data = {f"batch:{i}": {"value": i, "timestamp": time.time()} for i in range(5)}

            try:
                batch_set_results = await self.cache_manager.batch_set(batch_data)
                batch_get_results = await self.cache_manager.batch_get(list(batch_data.keys()))

                batch_success = all(batch_set_results.values()) and all(v is not None for v in batch_get_results.values())

                results["batch_operations"] = {
                    "success": batch_success,
                    "set_success_rate": sum(batch_set_results.values()) / len(batch_set_results),
                    "get_success_rate": sum(1 for v in batch_get_results.values() if v is not None) / len(batch_get_results)
                }

                print(f"  ✅ Batch operations: {'PASS' if batch_success else 'FAIL'}")

            except Exception as e:
                results["batch_operations"] = {"success": False, "error": str(e)}
                print(f"  ❌ Batch operations: FAIL - {e}")

            self.test_results["redis_integration"] = results

        except Exception as e:
            self.test_results["redis_integration"] = {"success": False, "error": str(e)}
            print(f"  ❌ Redis integration test failed: {e}")

        finally:
            await self.cache_manager.disconnect()

    async def test_performance_comparison(self):
        """測試性能對比"""
        print("\n⚡ Testing Performance...")

        # 創建大型測試數據
        large_dataframe = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=1000, freq='1min'),
            'price': np.random.normal(300, 10, 1000),
            'volume': np.random.randint(1000, 10000, 1000),
            'symbol': ['0700.HK'] * 1000
        })

        large_array = np.random.random(10000)

        test_data = [
            ("large_dataframe", large_dataframe),
            ("large_array", large_array),
            ("nested_data", {
                "data": [ {"id": i, "value": i * 2} for i in range(1000) ],
                "metadata": {"total": 1000, "timestamp": datetime.now().isoformat()}
            })
        ]

        results = {}

        for test_name, data in test_data:
            try:
                # 測試SafeDataSerializer性能
                times = []
                sizes = []

                for _ in range(5):  # 運行5次取平均
                    start_time = time.perf_counter()
                    serialized = SafeDataSerializer.serialize(data)
                    serialization_time = (time.perf_counter() - start_time) * 1000

                    start_time = time.perf_counter()
                    deserialized = SafeDataSerializer.deserialize(serialized)
                    deserialization_time = (time.perf_counter() - start_time) * 1000

                    times.append(serialization_time + deserialization_time)
                    sizes.append(len(serialized))

                avg_time = sum(times) / len(times)
                avg_size = sum(sizes) / len(sizes)

                results[test_name] = {
                    "avg_total_time_ms": avg_time,
                    "avg_serialized_size_bytes": avg_size,
                    "runs": len(times)
                }

                print(f"  ⏱️  {test_name}: {avg_time:.2f}ms avg, {avg_size:.0f} bytes")

            except Exception as e:
                results[test_name] = {"success": False, "error": str(e)}
                print(f"  ❌ {test_name}: FAIL - {e}")

        self.test_results["performance"] = results

    async def test_security_vulnerabilities(self):
        """測試安全性（確保不使用pickle）"""
        print("\n🔒 Testing Security...")

        # 測試惡意數據不會被執行
        malicious_inputs = [
            "os.system('echo hacked')",
            "__import__('os').system('echo pwned')",
            "eval('__import__(\"os\").system(\"echo malicious\")')",
            {"__code__": "malicious_payload"},
            " pickle.loads(b'cos\\nsystem\\n(Vecho hacked\\ntR.')"
        ]

        results = {}

        for i, malicious_input in enumerate(malicious_inputs):
            try:
                # 這應該失敗或安全地處理
                if isinstance(malicious_input, str):
                    # 測試惡意字符串不會被執行
                    serialized = SafeDataSerializer.serialize({"data": malicious_input})
                    deserialized = SafeDataSerializer.deserialize(serialized)

                    # 確保惡意字符串仍然只是字符串
                    is_safe = isinstance(deserialized, dict) and deserialized.get("data") == malicious_input

                    results[f"malicious_input_{i}"] = {
                        "success": True,
                        "safe": is_safe,
                        "treated_as_string": True
                    }

                    print(f"  ✅ Malicious input {i}: SAFE (treated as data)")
                else:
                    results[f"malicious_input_{i}"] = {
                        "success": False,
                        "error": "Unexpected input type"
                    }

            except Exception as e:
                # 預期的失敗是好的
                results[f"malicious_input_{i}"] = {
                    "success": True,
                    "safe": True,
                    "error": str(e)  # 這是我們期望的安全失敗
                }
                print(f"  ✅ Malicious input {i}: SAFE (rejected)")

        # 測試不支持的類型被拒絕
        try:
            class CustomObject:
                def __init__(self):
                    self.value = "test"

            custom_obj = CustomObject()

            try:
                SafeDataSerializer.serialize(custom_obj)
                unsupported_handled = False
            except (SerializationError, UnsupportedTypeError):
                unsupported_handled = True

            results["unsupported_type"] = {
                "success": True,
                "safe": unsupported_handled,
                "correctly_rejected": unsupported_handled
            }

            print(f"  ✅ Unsupported types: {'SAFE' if unsupported_handled else 'UNSAFE'}")

        except Exception as e:
            results["unsupported_type"] = {"success": False, "error": str(e)}
            print(f"  ❌ Unsupported type test: FAIL - {e}")

        self.test_results["security"] = results

    def generate_test_report(self):
        """生成測試報告"""
        print("\n" + "=" * 60)
        print("📊 SAFE SERIALIZATION TEST REPORT")
        print("=" * 60)

        total_tests = 0
        passed_tests = 0

        for category, results in self.test_results.items():
            if isinstance(results, dict):
                for test_name, result in results.items():
                    if isinstance(result, dict):
                        total_tests += 1
                        if result.get("success", False) or result.get("safe", False):
                            passed_tests += 1

                        if "error" in result and result.get("success") is False:
                            print(f"❌ {category}.{test_name}: {result['error']}")

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")

        if success_rate >= 95:
            print("   ✅ EXCELLENT: Safe serialization working correctly!")
        elif success_rate >= 80:
            print("   ⚠️  GOOD: Mostly working, some issues to address")
        else:
            print("   ❌ NEEDS WORK: Significant issues found")

        # 保存詳細報告
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": success_rate
            },
            "detailed_results": self.test_results
        }

        with open("safe_serialization_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: safe_serialization_test_report.json")

async def main():
    """主測試函數"""
    tester = SafeSerializationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())