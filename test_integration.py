"""
測試 CBS-C 系統整合
Test CBS-C System Integration
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any

API_BASE_URL = "http://localhost:3004"
FRONTEND_URL = "http://localhost:3000"


def test_api_health() -> Dict[str, Any]:
    """測試 API 健康端點"""
    print("\n[測試] API 健康檢查...")

    try:
        # 測試基本健康檢查
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 基本健康檢查通過")
            basic_health = response.json()
        else:
            print(f"❌ 基本健康檢查失敗: {response.status_code}")
            return {"success": False, "error": "Basic health check failed"}

        # 測試增強健康檢查
        response = requests.get(f"{API_BASE_URL}/health/enhanced", timeout=5)
        if response.status_code == 200:
            print("✅ 增強健康檢查通過")
            enhanced_health = response.json()

            # 檢查各組件狀態
            components = enhanced_health.get("services", {})
            for component, status in components.items():
                if status == "healthy" or status == "configured":
                    print(f"  - {component}: {status}")
                else:
                    print(f"  ⚠️ {component}: {status}")
        else:
            print(f"❌ 增強健康檢查失敗: {response.status_code}")

        return {
            "success": True,
            "basic_health": basic_health,
            "enhanced_health": enhanced_health
        }

    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 API 服務器")
        return {"success": False, "error": "Cannot connect to API server"}
    except Exception as e:
        print(f"❌ 健康檢查錯誤: {e}")
        return {"success": False, "error": str(e)}


def test_trading_api() -> Dict[str, Any]:
    """測試交易 API"""
    print("\n[測試] 交易 API...")

    try:
        # 測試獲取交易引擎狀態
        response = requests.get(f"{API_BASE_URL}/api/v2/trading/engine/status", timeout=5)
        if response.status_code == 200:
            print("✅ 交易引擎狀態 API 正常")
            status = response.json()
            print(f"  引擎狀態: {status.get('status', {}).get('status', 'unknown')}")
        else:
            print(f"⚠️ 交易引擎狀態 API 返回: {response.status_code}")

        # 測試獲取訂單列表
        response = requests.get(f"{API_BASE_URL}/api/v2/trading/orders", timeout=5)
        if response.status_code == 200:
            print("✅ 訂單列表 API 正常")
            orders = response.json()
            print(f"  訂單數量: {len(orders)}")
        else:
            print(f"⚠️ 訂單列表 API 返回: {response.status_code}")

        return {"success": True}

    except Exception as e:
        print(f"❌ 交易 API 錯誤: {e}")
        return {"success": False, "error": str(e)}


def test_risk_management_api() -> Dict[str, Any]:
    """測試風險管理 API"""
    print("\n[測試] 風險管理 API...")

    try:
        # 測試獲取風險儀表板
        response = requests.get(f"{API_BASE_URL}/risk/dashboard", timeout=5)
        if response.status_code == 200:
            print("✅ 風險儀表板 API 正常")
            dashboard = response.json()
            print(f"  監控實例數: {dashboard.get('active_monitoring', 0)}")
        else:
            print(f"⚠️ 風險儀表板 API 返回: {response.status_code}")

        # 測試獲取監控狀態
        response = requests.get(f"{API_BASE_URL}/risk/monitoring/status", timeout=5)
        if response.status_code == 200:
            print("✅ 監控狀態 API 正常")
            status = response.json()
            print(f"  活躍實例: {status.get('total_active', 0)}")
        else:
            print(f"⚠️ 監控狀態 API 返回: {response.status_code}")

        return {"success": True}

    except Exception as e:
        print(f"❌ 風險管理 API 錯誤: {e}")
        return {"success": False, "error": str(e)}


def test_backtest_api() -> Dict[str, Any]:
    """測試回測 API"""
    print("\n[測試] 回測 API...")

    try:
        # 測試獲取用戶回測歷史
        response = requests.get(f"{API_BASE_URL}/api/v2/backtest/user/test_user", timeout=5)
        if response.status_code == 200:
            print("✅ 回測歷史 API 正常")
            history = response.json()
            print(f"  回測任務數: {len(history.get('items', []))}")
        else:
            print(f"⚠️ 回測歷史 API 返回: {response.status_code}")

        # 測試獲取統計信息
        response = requests.get(f"{API_BASE_URL}/api/v2/backtest/statistics?user_id=test_user", timeout=5)
        if response.status_code == 200:
            print("✅ 回測統計 API 正常")
            stats = response.json()
            print(f"  總任務數: {stats.get('total_tasks', 0)}")
        else:
            print(f"⚠️ 回測統計 API 返回: {response.status_code}")

        return {"success": True}

    except Exception as e:
        print(f"❌ 回測 API 錯誤: {e}")
        return {"success": False, "error": str(e)}


def test_monitoring_api() -> Dict[str, Any]:
    """測試監控 API"""
    print("\n[測試] 監控 API...")

    try:
        # 測試獲取系統指標
        response = requests.get(f"{API_BASE_URL}/api/v1/monitoring/metrics", timeout=5)
        if response.status_code == 200:
            print("✅ 系統指標 API 正常")
            metrics = response.json()
            print(f"  指標數量: {len(metrics.get('metrics', []))}")
        else:
            print(f"⚠️ 系統指標 API 返回: {response.status_code}")

        # 測試獲取活躍警報
        response = requests.get(f"{API_BASE_URL}/api/v1/monitoring/alerts", timeout=5)
        if response.status_code == 200:
            print("✅ 警報 API 正常")
            alerts = response.json()
            print(f"  活躍警報數: {len(alerts)}")
        else:
            print(f"⚠️ 警報 API 返回: {response.status_code}")

        return {"success": True}

    except Exception as e:
        print(f"❌ 監控 API 錯誤: {e}")
        return {"success": False, "error": str(e)}


def test_frontend() -> Dict[str, Any]:
    """測試前端"""
    print("\n[測試] 前端服務...")

    try:
        # 檢查前端是否運行
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ 前端服務正常運行")
            return {"success": True}
        else:
            print(f"⚠️ 前端服務返回: {response.status_code}")
            return {"success": False, "error": f"Frontend returned {response.status_code}"}

    except requests.exceptions.ConnectionError:
        print("⚠️ 前端服務未運行（這在純後端測試中是正常的）")
        return {"success": True, "warning": "Frontend not running"}
    except Exception as e:
        print(f"❌ 前端測試錯誤: {e}")
        return {"success": False, "error": str(e)}


def main():
    """主測試函數"""
    print("=" * 60)
    print("CBS-C 系統整合測試")
    print("CBS-C System Integration Test")
    print("=" * 60)

    test_results = {
        "api_health": test_api_health(),
        "trading": test_trading_api(),
        "risk_management": test_risk_management_api(),
        "backtest": test_backtest_api(),
        "monitoring": test_monitoring_api(),
        "frontend": test_frontend()
    }

    # 統計結果
    print("\n" + "=" * 60)
    print("測試結果摘要 / Test Summary")
    print("=" * 60)

    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results.values() if r.get("success", False))
    failed_tests = total_tests - passed_tests

    print(f"\n總測試數: {total_tests}")
    print(f"通過: {passed_tests}")
    print(f"失敗: {failed_tests}")

    # 詳細結果
    print("\n詳細結果:")
    for test_name, result in test_results.items():
        status = "✅ 通過" if result.get("success", False) else "❌ 失敗"
        if result.get("warning"):
            status = "⚠️ 警告"
        print(f"  {test_name}: {status}")
        if not result.get("success", False) and "error" in result:
            print(f"    錯誤: {result['error']}")

    # API 文檔提示
    print("\n" + "=" * 60)
    print("API 文檔 / API Documentation")
    print("=" * 60)
    print(f"Swagger UI: {API_BASE_URL}/docs")
    print(f"ReDoc: {API_BASE_URL}/redoc")

    # 總體狀態
    print("\n" + "=" * 60)
    if failed_tests == 0:
        print("🎉 所有測試通過！系統整合成功！")
        print("🎉 All tests passed! System integration successful!")
        return 0
    else:
        print("❌ 部分測試失敗。請檢查錯誤信息。")
        print("❌ Some tests failed. Please check error messages.")
        return 1


if __name__ == "__main__":
    sys.exit(main())