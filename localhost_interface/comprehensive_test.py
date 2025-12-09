#!/usr/bin/env python3
"""
localhost介面全面測試腳本
"""
import requests
import json
import time
import sys

API_BASE = "http://127.0.0.1:8000"

def test_endpoint(name, url, expected_status=200):
    """測試API端點"""
    try:
        response = requests.get(url)
        success = response.status_code == expected_status
        print(f"[{'PASS' if success else 'FAIL'}] {name}: {response.status_code}")
        return success
    except Exception as e:
        print(f"[FAIL] {name}: 連接錯誤 - {e}")
        return False

def run_comprehensive_tests():
    """運行全面測試"""
    print("=" * 50)
    print("localhost介面全面測試報告")
    print("=" * 50)

    tests_passed = 0
    total_tests = 0

    # 基礎端點測試
    print("\n1. 基礎端點測試:")
    total_tests += 1
    if test_endpoint("根路徑", f"{API_BASE}/"):
        tests_passed += 1

    total_tests += 1
    if test_endpoint("健康檢查", f"{API_BASE}/api/health"):
        tests_passed += 1

    total_tests += 1
    if test_endpoint("交易信號列表", f"{API_BASE}/api/signals"):
        tests_passed += 1

    # 功能測試
    print("\n2. 功能測試:")

    # 認證測試
    total_tests += 1
    auth_response = requests.post(f"{API_BASE}/api/auth/token",
                                 params={"username": "admin", "password": "admin123"})
    if auth_response.status_code == 200:
        print("[PASS] 管理員認證")
        tests_passed += 1
    else:
        print("[FAIL] 管理員認證")

    total_tests += 1
    trader_auth_response = requests.post(f"{API_BASE}/api/auth/token",
                                        params={"username": "trader", "password": "trader123"})
    if trader_auth_response.status_code == 200:
        print("[PASS] 交易員認證")
        tests_passed += 1
    else:
        print("[FAIL] 交易員認證")

    # 錯誤處理測試
    print("\n3. 錯誤處理測試:")

    total_tests += 1
    error_response = requests.post(f"{API_BASE}/api/auth/token",
                                  params={"username": "admin", "password": "wrong"})
    if error_response.status_code == 401:
        print("[PASS] 錯誤密碼處理")
        tests_passed += 1
    else:
        print("[FAIL] 錯誤密碼處理")

    total_tests += 1
    if test_endpoint("不存在的信號", f"{API_BASE}/api/signals/nonexistent", 404):
        tests_passed += 1

    # 性能測試
    print("\n4. 性能測試:")
    start_time = time.time()
    for i in range(10):
        requests.get(f"{API_BASE}/api/health")
    end_time = time.time()
    avg_time = (end_time - start_time) / 10 * 1000  # 轉換為毫秒

    if avg_time < 100:  # 小於100ms
        print(f"[PASS] 平均響應時間: {avg_time:.2f}ms")
        tests_passed += 1
        total_tests += 1
    else:
        print(f"[FAIL] 平均響應時間: {avg_time:.2f}ms (過慢)")
        total_tests += 1

    # 數據完整性測試
    print("\n5. 數據完整性測試:")

    total_tests += 1
    signals_response = requests.get(f"{API_BASE}/api/signals")
    if signals_response.status_code == 200:
        signals_data = signals_response.json()
        if len(signals_data) >= 2:
            print("[PASS] 交易信號數量正確")
            tests_passed += 1
        else:
            print("[FAIL] 交易信號數量不足")
    else:
        print("[FAIL] 無法獲取交易信號")

    total_tests += 1
    if signals_response.status_code == 200:
        # 檢查信號結構
        signal = signals_data[0]
        required_fields = ["id", "symbol", "signal_type", "strength", "confidence", "timestamp"]
        if all(field in signal for field in required_fields):
            print("[PASS] 信號數據結構完整")
            tests_passed += 1
        else:
            print("[FAIL] 信號數據結構不完整")

    # 測試結果摘要
    print("\n" + "=" * 50)
    print(f"測試完成: {tests_passed}/{total_tests} 通過")
    print(f"成功率: {(tests_passed/total_tests)*100:.1f}%")

    if tests_passed == total_tests:
        print("🎉 所有測試通過！系統運行完美。")
        return True
    elif tests_passed >= total_tests * 0.8:
        print("✅ 大部分測試通過，系統基本正常。")
        return True
    else:
        print("❌ 多個測試失敗，系統需要檢查。")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)