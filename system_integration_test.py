#!/usr/bin/env python3
"""
CBSC System Integration Test
CBSC 系統集成測試
"""

import requests
import json
import time
import sys
from datetime import datetime

# API 測試配置
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

# 測試結果
test_results = {
    "總測試數": 0,
    "通過測試": 0,
    "失敗測試": 0,
    "詳細結果": []
}

def print_header(title):
    """打印測試標題"""
    print(f"\n{'='*50}")
    print(f"測試: {title}")
    print(f"{'='*50}")

def run_api_test(test_name, url, expected_status=200):
    """運行 API 測試"""
    global test_results
    test_results["總測試數"] += 1

    try:
        print(f"測試: {test_name}")
        response = requests.get(url, timeout=10)

        if response.status_code == expected_status:
            print(f"✅ 通過 - 狀態碼: {response.status_code}")
            test_results["通過測試"] += 1
            result = "通過"

            # 如果是 JSON 響應，嘗試解析並顯示關鍵信息
            try:
                data = response.json()
                if "success" in data:
                    print(f"   📊 API 響應成功: {data.get('success')}")
                if "data" in data and isinstance(data["data"], dict):
                    print(f"   📋 數據鍵數量: {len(data['data'])}")
                if "timestamp" in data:
                    print(f"   ⏰ 時間戳: {data['timestamp']}")
            except:
                print(f"   📄 響應長度: {len(response.text)} 字符")

        else:
            print(f"❌ 失敗 - 預期狀態碼: {expected_status}, 實際: {response.status_code}")
            print(f"   📄 錯誤響應: {response.text[:200]}...")
            test_results["失敗測試"] += 1
            result = "失敗"

    except requests.exceptions.RequestException as e:
        print(f"❌ 失敗 - 請求異常: {str(e)}")
        test_results["失敗測試"] += 1
        result = "失敗"

    test_results["詳細結果"].append({
        "測試": test_name,
        "URL": url,
        "結果": result,
        "時間": datetime.now().isoformat()
    })

    print()

def test_performance_endpoints():
    """測試性能相關端點"""
    print_header("性能端點測試")

    run_api_test(
        "獲取績效摘要",
        f"{BACKEND_URL}/api/v1/performance/summary"
    )

    run_api_test(
        "獲取儀表板概覽",
        f"{BACKEND_URL}/api/v1/dashboard/overview"
    )

def test_data_endpoints():
    """測試數據相關端點"""
    print_header("數據端點測試")

    run_api_test(
        "獲取所有策略",
        f"{BACKEND_URL}/api/v1/strategies"
    )

    run_api_test(
        "獲取經濟數據",
        f"{BACKEND_URL}/api/v1/economic-data"
    )

    run_api_test(
        "獲取特定策略詳情",
        f"{BACKEND_URL}/api/v1/strategies/ma_crossover_001"
    )

def test_system_health():
    """測試系統健康狀態"""
    print_header("系統健康檢查")

    run_api_test(
        "後端健康檢查",
        f"{BACKEND_URL}/api/health"
    )

    run_api_test(
        "API 根路徑",
        f"{BACKEND_URL}/"
    )

    # 測試 API 文檔
    run_api_test(
        "API 文檔",
        f"{BACKEND_URL}/docs"
    )

    # 測試前端
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        if response.status_code == 200:
            print(f"✅ 前端服務 - 正常運行")
            test_results["通過測試"] += 1
        else:
            print(f"❌ 前端服務 - 狀態碼: {response.status_code}")
            test_results["失敗測試"] += 1
        test_results["總測試數"] += 1
    except Exception as e:
        print(f"❌ 前端服務 - 連接失敗: {str(e)}")
        test_results["總測試數"] += 1
        test_results["失敗測試"] += 1

def test_response_times():
    """測試響應時間"""
    print_header("響應時間測試")

    endpoints = [
        ("健康檢查", f"{BACKEND_URL}/api/health"),
        ("策略列表", f"{BACKEND_URL}/api/v1/strategies"),
        ("經濟數據", f"{BACKEND_URL}/api/v1/economic-data"),
        ("儀表板概覽", f"{BACKEND_URL}/api/v1/dashboard/overview")
    ]

    total_time = 0

    for name, url in endpoints:
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            end_time = time.time()

            response_time = (end_time - start_time) * 1000  # 轉換為毫秒
            total_time += response_time

            print(f"⏱️ {name}: {response_time:.2f}ms")

            if response_time < 500:
                print(f"   ✅ 優秀 (< 500ms)")
            elif response_time < 1000:
                print(f"   ✅ 良好 (< 1000ms)")
            else:
                print(f"   ⚠️ 需要優化 (> 1000ms)")

        except Exception as e:
            print(f"❌ {name}: 測試失敗 - {str(e)}")

    avg_time = total_time / len(endpoints)
    print(f"\n📊 平均響應時間: {avg_time:.2f}ms")

    test_results["總測試數"] += 1
    if avg_time < 500:
        test_results["通過測試"] += 1
        print(f"✅ 響應時間測試通過")
    else:
        test_results["失敗測試"] += 1
        print(f"❌ 響應時間需要優化")

def generate_report():
    """生成測試報告"""
    print_header("系統集成測試報告")

    success_rate = (test_results["通過測試"] / test_results["總測試數"]) * 100 if test_results["總測試數"] > 0 else 0

    print(f"📈 測試統計:")
    print(f"   總測試數: {test_results['總測試數']}")
    print(f"   通過測試: {test_results['通過測試']}")
    print(f"   失敗測試: {test_results['失敗測試']}")
    print(f"   成功率: {success_rate:.1f}%")

    if success_rate >= 80:
        print(f"🎉 系統集成測試結果: 優秀")
    elif success_rate >= 60:
        print(f"✅ 系統集成測試結果: 良好")
    else:
        print(f"⚠️ 系統集成測試結果: 需要改進")

    print(f"\n📋 詳細測試結果:")
    for i, result in enumerate(test_results["詳細結果"], 1):
        status_emoji = "✅" if result["結果"] == "通過" else "❌"
        print(f"   {i}. {status_emoji} {result['測試']}")

    # 保存詳細報告到文件
    report_data = {
        "測試時間": datetime.now().isoformat(),
        "系統信息": {
            "後端URL": BACKEND_URL,
            "前端URL": FRONTEND_URL
        },
        "測試統計": {
            "總測試數": test_results["總測試數"],
            "通過測試": test_results["通過測試"],
            "失敗測試": test_results["失敗測試"],
            "成功率": f"{success_rate:.1f}%"
        },
        "詳細結果": test_results["詳細結果"]
    }

    with open("system_integration_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 詳細報告已保存到: system_integration_test_report.json")

def main():
    """主測試函數"""
    print("CBSC 系統集成測試開始")
    print(f"測試時間: {datetime.now().isoformat()}")
    print(f"後端服務: {BACKEND_URL}")
    print(f"前端服務: {FRONTEND_URL}")

    try:
        # 執行各類測試
        test_system_health()
        test_data_endpoints()
        test_performance_endpoints()
        test_response_times()

        # 生成報告
        generate_report()

    except KeyboardInterrupt:
        print(f"\n測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n測試過程中發生錯誤: {str(e)}")
        sys.exit(1)

    return test_results["通過測試"] == test_results["總測試數"]

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)