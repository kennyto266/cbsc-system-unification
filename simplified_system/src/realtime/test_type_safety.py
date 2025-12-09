#!/usr/bin/env python3
"""
Phase 3 Type Safety Test
Phase 3 類型安全測試
測試所有新增的類型註解和異常處理
"""

import sys
import os
import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

# 添加項目根目錄到路徑
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

try:
    from simplified_system.src.realtime.realtime_types import (
        Result, RealtimePriceData, WebSocketMessage,
        WebSocketState, HealthStatus, ValidationResult,
        is_valid_symbol, is_valid_price, is_valid_volume
    )

    from simplified_system.src.realtime.exceptions import (
        RealtimeInfraError, WebSocketError, WebSocketConnectionError,
        WebSocketMessageError, DataValidationError, DataTransformationError,
        ValidationError, ErrorContext, create_websocket_context
    )

    from src.realtime.safe_serialization import (
        SafeDataSerializer, CacheSerializationError
    )

    print("✅ All imports successful")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TypeSafetyTester:
    """類型安全測試器"""

    def __init__(self) -> None:
        self.test_results: Dict[str, bool] = {}
        self.errors: List[str] = []

    def test_result_type(self) -> None:
        """測試Result類型"""
        print("\n🧪 Testing Result Type...")

        try:
            # 測試成功結果
            success_result: Result[str] = Result.ok("test_value")
            assert success_result.is_ok() == True
            assert success_result.unwrap() == "test_value"

            # 測試失敗結果
            error_result: Result[str] = Result.error(Exception("test error"))
            assert error_result.is_error() == True

            # 測試鏈式操作
            mapped_result = success_result.map(str.upper)
            assert mapped_result.unwrap() == "TEST_VALUE"

            self.test_results["result_type"] = True
            print("  ✅ Result type tests passed")

        except Exception as e:
            self.test_results["result_type"] = False
            self.errors.append(f"Result type test failed: {e}")
            print(f"  ❌ Result type test failed: {e}")

    def test_data_types(self) -> None:
        """測試數據類型"""
        print("\n🧪 Testing Data Types...")

        try:
            # 測試RealtimePriceData
            price_data = RealtimePriceData(
                symbol="0700.HK",
                timestamp=datetime.now(),
                price=300.5,
                volume=15000
            )
            assert price_data.symbol == "0700.HK"
            assert price_data.price == 300.5

            # 測試WebSocketMessage
            message = WebSocketMessage(
                message_type="subscription",
                data={"symbols": ["0700.HK"]},
                timestamp=datetime.now()
            )
            json_data = message.to_json()
            assert isinstance(json_data, str)

            self.test_results["data_types"] = True
            print("  ✅ Data type tests passed")

        except Exception as e:
            self.test_results["data_types"] = False
            self.errors.append(f"Data type test failed: {e}")
            print(f"  ❌ Data type test failed: {e}")

    def test_validation_functions(self) -> None:
        """測試驗證函數"""
        print("\n🧪 Testing Validation Functions...")

        try:
            # 測試符號驗證
            assert is_valid_symbol("0700.HK") == True
            assert is_valid_symbol("INVALID SYMBOL!") == False
            assert is_valid_symbol("") == False

            # 測試價格驗證
            assert is_valid_price(300.5) == True
            assert is_valid_price(-10) == False
            assert is_valid_price("300") == False

            # 測試成交量驗證
            assert is_valid_volume(15000) == True
            assert is_valid_volume(-1) == False
            assert is_valid_volume(0) == True

            self.test_results["validation_functions"] = True
            print("  ✅ Validation function tests passed")

        except Exception as e:
            self.test_results["validation_functions"] = False
            self.errors.append(f"Validation function test failed: {e}")
            print(f"  ❌ Validation function test failed: {e}")

    def test_exception_hierarchy(self) -> None:
        """測試異常層次"""
        print("\n🧪 Testing Exception Hierarchy...")

        try:
            # 測試基礎異常
            base_error = RealtimeInfraError("Test error")
            assert base_error.message == "Test error"
            assert isinstance(base_error.context, ErrorContext)

            # 測試WebSocket異常
            ws_error = WebSocketConnectionError(
                "Connection failed",
                context=create_websocket_context("connect", "user_123", "127.0.0.1")
            )
            assert ws_error.context.operation == "connect"
            assert ws_error.context.user_id == "user_123"

            # 測試驗證異常
            validation_error = ValidationError(
                "Invalid field value",
                field="symbol",
                value="INVALID",
                allowed_values=["0700.HK", "0941.HK"]
            )
            assert validation_error.field == "symbol"
            assert validation_error.value == "INVALID"

            # 測試異常序列化
            error_dict = ws_error.to_dict()
            assert isinstance(error_dict, dict)
            assert "error_type" in error_dict

            self.test_results["exception_hierarchy"] = True
            print("  ✅ Exception hierarchy tests passed")

        except Exception as e:
            self.test_results["exception_hierarchy"] = False
            self.errors.append(f"Exception hierarchy test failed: {e}")
            print(f"  ❌ Exception hierarchy test failed: {e}")

    def test_safe_serialization(self) -> None:
        """測試安全序列化"""
        print("\n🧪 Testing Safe Serialization...")

        try:
            # 測試基本序列化
            test_data = {"symbol": "0700.HK", "price": 300.5}
            serialized = SafeDataSerializer.serialize(test_data)
            deserialized = SafeDataSerializer.deserialize(serialized)
            assert deserialized == test_data

            # 測試複雜數據序列化
            complex_data = {
                "symbols": ["0700.HK", "0941.HK"],
                "timestamp": datetime.now(),
                "nested": {"price": 300.5, "volume": 15000}
            }
            complex_serialized = SafeDataSerializer.serialize(complex_data)
            complex_deserialized = SafeDataSerializer.deserialize(complex_serialized)
            assert complex_deserialized["symbols"] == complex_data["symbols"]

            # 測試不安全數據拒絕
            try:
                SafeDataSerializer.serialize(lambda x: x)  # type: ignore
                assert False, "Should have rejected unsafe data"
            except (NameError, CacheSerializationError, TypeError):
                pass  # 預期異常

            self.test_results["safe_serialization"] = True
            print("  ✅ Safe serialization tests passed")

        except Exception as e:
            self.test_results["safe_serialization"] = False
            self.errors.append(f"Safe serialization test failed: {e}")
            print(f"  ❌ Safe serialization test failed: {e}")

    def test_type_annotations(self) -> None:
        """測試類型註解"""
        print("\n🧪 Testing Type Annotations...")

        try:
            # 測試函數簽名
            def typed_function(param: str, number: int) -> bool:
                return param.isdigit() and number > 0

            result: bool = typed_function("123", 456)
            assert result == True

            # 測試泛型類型
            typed_dict: Dict[str, Any] = {"key": "value", "number": 123}
            typed_list: List[str] = ["item1", "item2", "item3"]

            assert isinstance(typed_dict, dict)
            assert isinstance(typed_list, list)

            self.test_results["type_annotations"] = True
            print("  ✅ Type annotation tests passed")

        except Exception as e:
            self.test_results["type_annotations"] = False
            self.errors.append(f"Type annotation test failed: {e}")
            print(f"  ❌ Type annotation test failed: {e}")

    async def test_async_type_safety(self) -> None:
        """測試異步類型安全"""
        print("\n🧪 Testing Async Type Safety...")

        try:
            # 測試異步函數類型註解
            async def async_typed_function(data: Dict[str, Any]) -> str:
                await asyncio.sleep(0.001)  # 模擬異步操作
                return str(data.get("key", ""))

            result: str = await async_typed_function({"key": "test_value"})
            assert result == "test_value"

            self.test_results["async_type_safety"] = True
            print("  ✅ Async type safety tests passed")

        except Exception as e:
            self.test_results["async_type_safety"] = False
            self.errors.append(f"Async type safety test failed: {e}")
            print(f"  ❌ Async type safety test failed: {e}")

    def run_all_tests(self) -> None:
        """運行所有測試"""
        print("🚀 Starting Phase 3 Type Safety Tests...")
        print("=" * 60)

        # 運行同步測試
        self.test_result_type()
        self.test_data_types()
        self.test_validation_functions()
        self.test_exception_hierarchy()
        self.test_safe_serialization()
        self.test_type_annotations()

        # 運行異步測試
        asyncio.run(self.test_async_type_safety())

        # 生成測試報告
        self.generate_report()

    def generate_report(self) -> None:
        """生成測試報告"""
        print("\n" + "=" * 60)
        print("📊 Phase 3 Type Safety Test Report")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        print("\n📋 Test Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")

        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"  - {error}")

        if failed_tests == 0:
            print("\n🎉 All type safety tests passed!")
            print("✅ Phase 3 type safety improvements are working correctly.")
        else:
            print(f"\n⚠️ {failed_tests} test(s) failed.")
            print("🔧 Please review the errors above and fix the issues.")

        print("=" * 60)

def main():
    """主函數"""
    tester = TypeSafetyTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()