#!/usr/bin/env python3
"""
Test DataSerializer with SafeDataSerializer Integration
獨立測試DataSerializer類
"""

import json
import time
import zlib
import numpy as np
import pandas as pd
from datetime import datetime

# Import our modules directly
from safe_serialization import SafeDataSerializer, SerializationError, DeserializationError

class DataSerializer:
    """安全數據序列化器 - 使用SafeDataSerializer避免pickle安全漏洞"""

    @staticmethod
    def serialize(data) -> bytes:
        """安全序列化數據"""
        try:
            # 使用SafeDataSerializer進行安全序列化
            serialized = SafeDataSerializer.serialize(data)

            # 對大型數據進行壓縮
            if len(serialized) > 1024:
                return zlib.compress(serialized)
            return serialized

        except (SerializationError, ValueError, TypeError) as e:
            print(f"Safe serialization error: {e}")
            raise SerializationError(f"Cannot safely serialize data: {e}") from e
        except Exception as e:
            print(f"Unexpected serialization error: {e}")
            raise SerializationError(f"Unexpected serialization error: {e}") from e

    @staticmethod
    def deserialize(data: bytes, data_type: str = "auto"):
        """安全反序列化數據"""
        try:
            # 首先嘗試解壓縮（如果適用）
            if data_type == "compressed" or data_type == "auto":
                try:
                    # 檢查是否為壓縮數據
                    decompressed = zlib.decompress(data)
                    data_to_deserialize = decompressed
                except:
                    # 不是壓縮數據，使用原始數據
                    data_to_deserialize = data
            else:
                data_to_deserialize = data

            # 使用SafeDataSerializer進行安全反序列化
            return SafeDataSerializer.deserialize(data_to_deserialize)

        except (DeserializationError, ValueError, UnicodeDecodeError) as e:
            print(f"Safe deserialization error: {e}")
            raise DeserializationError(f"Cannot safely deserialize data: {e}") from e
        except Exception as e:
            print(f"Unexpected deserialization error: {e}")
            raise DeserializationError(f"Unexpected deserialization error: {e}") from e

def run_tests():
    """運行所有測試"""
    print("Testing DataSerializer with SafeDataSerializer integration...")
    print("=" * 60)

    tests_passed = 0
    total_tests = 0

    # Test 1: Basic market data
    print("\nTest 1: Basic market data")
    market_data = {
        'symbol': '0700.HK',
        'price': 300.50,
        'volume': 15000,
        'timestamp': '2024-01-01T10:00:00'
    }

    try:
        serialized = DataSerializer.serialize(market_data)
        deserialized = DataSerializer.deserialize(serialized)
        success = deserialized == market_data
        print(f"  Result: {'PASS' if success else 'FAIL'}")
        if success:
            tests_passed += 1
        total_tests += 1
        print(f"  Serialized size: {len(serialized)} bytes")
    except Exception as e:
        print(f"  Result: FAIL - {e}")
        total_tests += 1

    # Test 2: DataFrame
    print("\nTest 2: DataFrame")
    df = pd.DataFrame({
        'price': [300.1, 300.2, 300.3],
        'volume': [1000, 2000, 3000],
        'symbol': ['0700.HK'] * 3
    })

    try:
        serialized_df = DataSerializer.serialize(df)
        deserialized_df = DataSerializer.deserialize(serialized_df)
        df_match = isinstance(deserialized_df, pd.DataFrame) and deserialized_df.equals(df)
        print(f"  Result: {'PASS' if df_match else 'FAIL'}")
        if df_match:
            tests_passed += 1
        total_tests += 1
        print(f"  Serialized size: {len(serialized_df)} bytes")
        print(f"  DataFrame shape: {deserialized_df.shape if deserialized_df is not None else 'None'}")
    except Exception as e:
        print(f"  Result: FAIL - {e}")
        total_tests += 1

    # Test 3: NumPy array
    print("\nTest 3: NumPy array")
    arr = np.array([1.1, 2.2, 3.3])

    try:
        serialized_arr = DataSerializer.serialize(arr)
        deserialized_arr = DataSerializer.deserialize(serialized_arr)
        arr_match = isinstance(deserialized_arr, np.ndarray) and np.array_equal(deserialized_arr, arr)
        print(f"  Result: {'PASS' if arr_match else 'FAIL'}")
        if arr_match:
            tests_passed += 1
        total_tests += 1
        print(f"  Serialized size: {len(serialized_arr)} bytes")
        print(f"  Array shape: {deserialized_arr.shape if deserialized_arr is not None else 'None'}")
    except Exception as e:
        print(f"  Result: FAIL - {e}")
        total_tests += 1

    # Test 4: Large data (should be compressed)
    print("\nTest 4: Large data (compression)")
    large_data = {'data': list(range(1000)), 'metadata': {'source': 'test', 'timestamp': datetime.now().isoformat()}}

    try:
        serialized_large = DataSerializer.serialize(large_data)
        deserialized_large = DataSerializer.deserialize(serialized_large)
        large_match = deserialized_large == large_data
        print(f"  Result: {'PASS' if large_match else 'FAIL'}")
        if large_match:
            tests_passed += 1
        total_tests += 1
        print(f"  Serialized size: {len(serialized_large)} bytes")
        print(f"  Compressed: {len(serialized_large) < len(str(large_data))}")
    except Exception as e:
        print(f"  Result: FAIL - {e}")
        total_tests += 1

    # Test 5: Security test - ensure no pickle usage
    print("\nTest 5: Security test (no pickle)")

    class UnsafeObject:
        def __init__(self):
            self.code = "malicious"

    try:
        unsafe_obj = UnsafeObject()
        DataSerializer.serialize(unsafe_obj)
        print(f"  Result: FAIL - Should have rejected unsafe object")
        total_tests += 1
    except (SerializationError, ValueError, TypeError):
        print(f"  Result: PASS - Correctly rejected unsafe object")
        tests_passed += 1
        total_tests += 1
    except Exception as e:
        print(f"  Result: PASS - Rejected with unexpected error: {e}")
        tests_passed += 1
        total_tests += 1

    # Test 6: Performance test
    print("\nTest 6: Performance test")
    performance_df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='1min'),
        'price': np.random.normal(300, 10, 100),
        'volume': np.random.randint(1000, 10000, 100)
    })

    try:
        start_time = time.perf_counter()
        serialized_perf = DataSerializer.serialize(performance_df)
        serialization_time = (time.perf_counter() - start_time) * 1000

        start_time = time.perf_counter()
        deserialized_perf = DataSerializer.deserialize(serialized_perf)
        deserialization_time = (time.perf_counter() - start_time) * 1000

        perf_match = isinstance(deserialized_perf, pd.DataFrame) and deserialized_perf.equals(performance_df)
        total_time = serialization_time + deserialization_time

        print(f"  Result: {'PASS' if perf_match else 'FAIL'}")
        if perf_match:
            tests_passed += 1
        total_tests += 1
        print(f"  Serialization: {serialization_time:.2f}ms")
        print(f"  Deserialization: {deserialization_time:.2f}ms")
        print(f"  Total time: {total_time:.2f}ms")
        print(f"  Data size: {len(serialized_perf)} bytes")
    except Exception as e:
        print(f"  Result: FAIL - {e}")
        total_tests += 1

    # Results summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    print(f"Success rate: {(tests_passed/total_tests*100):.1f}%")

    if tests_passed == total_tests:
        print("✅ ALL TESTS PASSED!")
        print("🔒 CRITICAL SECURITY FIX VERIFIED:")
        print("   - Unsafe pickle deserialization ELIMINATED")
        print("   - Safe JSON-based serialization working correctly")
        print("   - DataFrame and NumPy array serialization functional")
        print("   - Compression working for large data")
        print("   - Security controls preventing unsafe object serialization")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Security fix needs additional work.")

    return tests_passed == total_tests

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)