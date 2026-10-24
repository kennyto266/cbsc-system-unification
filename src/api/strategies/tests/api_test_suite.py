"""
API Test Suite for Strategy Management
策略管理 API 測試套件

提供完整的 API 測試，包括：
- 端到端 API 測試
- 性能測試
- 負載測試
- 集成測試
"""

import pytest
import asyncio
import aiohttp
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json

from .base_test_classes import APIEndpointTestCase, MockDataGenerator, TestAssertions


class StrategyAPITestSuite(APIEndpointTestCase):
    """
    策略 API 測試套件
    """

    @pytest.mark.asyncio
    async def test_strategy_lifecycle(self, client, auth_headers):
        """
        測試策略完整的生命周期：創建 -> 讀取 -> 更新 -> 刪除
        """
        # 1. 創建策略
        strategy_data = MockDataGenerator.generate_strategy_data()
        response = client.post(
            "/api/v2/strategies",
            json=strategy_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        result = response.json()
        strategy_id = result["id"]
        assert strategy_id is not None

        # 2. 獲取策略詳情
        response = client.get(
            f"/api/v2/strategies/{strategy_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        strategy = response.json()
        assert strategy["id"] == strategy_id
        assert strategy["name"] == strategy_data["name"]

        # 3. 更新策略
        update_data = {
            "name": f"Updated_{strategy_data['name']}",
            "description": "Updated description"
        }
        response = client.put(
            f"/api/v2/strategies/{strategy_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == update_data["name"]

        # 4. 刪除策略
        response = client.delete(
            f"/api/v2/strategies/{strategy_id}",
            headers=auth_headers
        )
        assert response.status_code == 204

        # 5. 驗證刪除
        response = client.get(
            f"/api/v2/strategies/{strategy_id}",
            headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_strategy_execution_flow(self, client, auth_headers):
        """
        測試策略執行流程
        """
        # 1. 創建策略
        strategy_data = MockDataGenerator.generate_strategy_data()
        response = client.post(
            "/api/v2/strategies",
            json=strategy_data,
            headers=auth_headers
        )
        strategy_id = response.json()["id"]

        # 2. 執行策略
        execution_request = MockDataGenerator.generate_execution_data(strategy_id)
        response = client.post(
            f"/api/v2/strategies/{strategy_id}/executions",
            json=execution_request,
            headers=auth_headers
        )
        assert response.status_code == 202
        execution_id = response.json()["execution_id"]

        # 3. 檢查執行狀態
        # 注意：在實際測試中，可能需要等待執行完成
        response = client.get(
            f"/api/v2/strategies/{strategy_id}/executions/{execution_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        execution = response.json()
        assert execution["execution_id"] == execution_id
        assert execution["strategy_id"] == strategy_id

    @pytest.mark.asyncio
    async def test_performance_metrics(self, client, auth_headers):
        """
        測試性能指標獲取
        """
        # 1. 創建策略
        strategy_data = MockDataGenerator.generate_strategy_data()
        response = client.post(
            "/api/v2/strategies",
            json=strategy_data,
            headers=auth_headers
        )
        strategy_id = response.json()["id"]

        # 2. 獲取性能指標
        response = client.get(
            f"/api/v2/strategies/{strategy_id}/performance",
            headers=auth_headers
        )
        assert response.status_code == 200

        # 3. 驗證響應結構
        TestAssertions.assert_api_response_structure(response.json())

        # 4. 獲取性能報告
        response = client.get(
            f"/api/v2/strategies/{strategy_id}/performance/report",
            params={"report_type": "summary"},
            headers=auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_batch_operations(self, client, auth_headers):
        """
        測試批量操作
        """
        # 1. 創建多個策略
        strategy_ids = []
        for i in range(3):
            strategy_data = MockDataGenerator.generate_strategy_data()
            response = client.post(
                "/api/v2/strategies",
                json=strategy_data,
                headers=auth_headers
            )
            strategy_ids.append(response.json()["id"])

        # 2. 批量激活
        response = client.post(
            "/api/v2/strategies/batch",
            params={"operation": "activate"},
            json={"strategy_ids": strategy_ids},
            headers=auth_headers
        )
        assert response.status_code == 200
        batch_result = response.json()
        assert batch_result["successful"] == 3

        # 3. 批量刪除
        response = client.post(
            "/api/v2/strategies/batch",
            params={"operation": "delete"},
            json={"strategy_ids": strategy_ids},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["successful"] == 3

    @pytest.mark.asyncio
    async def test_api_pagination(self, client, auth_headers):
        """
        測試 API 分頁功能
        """
        # 1. 創建足夠的策略用於分頁測試
        strategy_ids = []
        for i in range(25):
            strategy_data = MockDataGenerator.generate_strategy_data()
            response = client.post(
                "/api/v2/strategies",
                json=strategy_data,
                headers=auth_headers
            )
            strategy_ids.append(response.json()["id"])

        # 2. 測試第一頁
        response = client.get(
            "/api/v2/strategies?page=1&page_size=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        page1 = response.json()
        assert len(page1["data"]) == 10
        assert page1["pagination"]["page"] == 1
        assert page1["pagination"]["total"] == 25

        # 3. 測試第二頁
        response = client.get(
            "/api/v2/strategies?page=2&page_size=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        page2 = response.json()
        assert len(page2["data"]) == 10
        assert page2["pagination"]["page"] == 2

        # 4. 測試最後一頁
        response = client.get(
            "/api/v2/strategies?page=3&page_size=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        page3 = response.json()
        assert len(page3["data"]) == 5  # 剩餘的策略

        # 5. 清理
        client.post(
            "/api/v2/strategies/batch",
            params={"operation": "delete"},
            json={"strategy_ids": strategy_ids},
            headers=auth_headers
        )

    @pytest.mark.asyncio
    async def test_api_filtering_and_sorting(self, client, auth_headers):
        """
        測試 API 過濾和排序功能
        """
        # 1. 創建不同類型的策略
        strategy_types = ["RSI", "MACD", "BOLLINGER"]
        strategy_ids = []

        for strategy_type in strategy_types:
            for i in range(2):
                strategy_data = MockDataGenerator.generate_strategy_data()
                strategy_data["strategy_type"] = strategy_type
                response = client.post(
                    "/api/v2/strategies",
                    json=strategy_data,
                    headers=auth_headers
                )
                strategy_ids.append(response.json()["id"])

        # 2. 測試按類型過濾
        response = client.get(
            "/api/v2/strategies?filter_type=RSI",
            headers=auth_headers
        )
        assert response.status_code == 200
        filtered = response.json()
        assert all(s["strategy_type"] == "RSI" for s in filtered["data"])

        # 3. 測試排序
        response = client.get(
            "/api/v2/strategies?sort_by=name&sort_order=asc",
            headers=auth_headers
        )
        assert response.status_code == 200
        sorted_data = response.json()["data"]
        assert sorted_data == sorted(sorted_data, key=lambda x: x["name"])

        # 4. 清理
        client.post(
            "/api/v2/strategies/batch",
            params={"operation": "delete"},
            json={"strategy_ids": strategy_ids},
            headers=auth_headers
        )


class APIPerformanceTestSuite:
    """
    API 性能測試套件
    """

    def __init__(self, base_url: str, auth_headers: Dict[str, str]):
        self.base_url = base_url
        self.auth_headers = auth_headers

    async def test_endpoint_response_times(self):
        """
        測試端點響應時間
        """
        results = {}
        endpoints = [
            ("/api/v2/version", "GET"),
            ("/api/v2/strategies?page=1&page_size=20", "GET"),
            ("/api/v2/health", "GET")
        ]

        async with aiohttp.ClientSession() as session:
            for endpoint, method in endpoints:
                times = []
                for _ in range(10):  # 測試10次
                    start = time.time()
                    if method == "GET":
                        async with session.get(
                            f"{self.base_url}{endpoint}",
                            headers=self.auth_headers
                        ) as response:
                            await response.text()
                    end = time.time()
                    times.append(end - start)

                results[endpoint] = {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "p95": sorted(times)[int(len(times) * 0.95)]
                }

        return results

    async def test_concurrent_requests(self, concurrency: int = 50):
        """
        測試並發請求
        """
        async def make_request():
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/v2/strategies",
                    headers=self.auth_headers
                ) as response:
                    return response.status, await response.json()

        # 並發執行請求
        tasks = [make_request() for _ in range(concurrency)]
        results = await asyncio.gather(*tasks)

        # 統計結果
        successful = sum(1 for status, _ in results if status == 200)
        avg_time = sum(_['data'].get('response_time', 0) for _, data in results if 'data' in data) / len(results)

        return {
            "total_requests": concurrency,
            "successful": successful,
            "failed": concurrency - successful,
            "success_rate": successful / concurrency,
            "avg_response_time": avg_time
        }

    async def test_load_over_time(self, duration_seconds: int = 60, rps: int = 10):
        """
        測試持續負載
        """
        start_time = time.time()
        end_time = start_time + duration_seconds
        results = []

        async with aiohttp.ClientSession() as session:
            while time.time() < end_time:
                request_start = time.time()
                async with session.get(
                    f"{self.base_url}/api/v2/strategies",
                    headers=self.auth_headers
                ) as response:
                    await response.text()
                request_time = time.time() - request_start
                results.append(request_time)

                # 控制請求速率
                await asyncio.sleep(1.0 / rps)

        return {
            "duration": duration_seconds,
            "total_requests": len(results),
            "rps_target": rps,
            "rps_actual": len(results) / duration_seconds,
            "avg_response_time": sum(results) / len(results),
            "max_response_time": max(results),
            "min_response_time": min(results)
        }


class APIIntegrationTestSuite:
    """
    API 集成測試套件
    測試 API 與其他系統的集成
    """

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def test_api_version_compatibility(self):
        """
        測試 API 版本兼容性
        """
        versions = ["1.0", "2.0"]
        compatibility_results = {}

        async with aiohttp.ClientSession() as session:
            for version in versions:
                headers = {"API-Version": version}
                async with session.get(
                    f"{self.base_url}/api/v2/version",
                    headers=headers
                ) as response:
                    compatibility_results[version] = {
                        "status": response.status,
                        "supports_version": response.headers.get("API-Version") == version
                    }

        return compatibility_results

    async def test_websocket_integration(self):
        """
        測試 WebSocket 集成
        """
        ws_url = self.base_url.replace("http", "ws") + "/ws/strategies"

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                # 發送訂閱消息
                await ws.send_str(json.dumps({
                    "type": "subscribe_strategy",
                    "strategy_id": "test_strategy_001"
                }))

                # 接收消息
                messages = []
                for _ in range(5):
                    msg = await ws.receive_str()
                    messages.append(json.loads(msg))

                return {
                    "connected": True,
                    "messages_received": len(messages),
                    "subscription_confirmed": any(
                        msg.get("type") == "subscription_confirmed"
                        for msg in messages
                    )
                }

    async def test_error_handling(self):
        """
        測試錯誤處理
        """
        error_test_cases = [
            # 不存在的資源
            ("/api/v2/strategies/nonexistent_id", 404),
            # 無效的參數
            ("/api/v2/strategies?page=-1", 422),
            # 無認證
            ("/api/v2/strategies", 401),
        ]

        async with aiohttp.ClientSession() as session:
            results = {}
            for endpoint, expected_status in error_test_cases:
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    results[endpoint] = {
                        "status": response.status,
                        "expected": expected_status,
                        "correct": response.status == expected_status,
                        "error_body": await response.json() if response.content_type == "application/json" else None
                    }

            return results


# 測試運行器
class APITestRunner:
    """
    API 測試運行器
    """

    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.auth_headers = {"Authorization": f"Bearer {auth_token}"}
        self.results = {}

    async def run_all_tests(self):
        """
        運行所有測試
        """
        print("開始運行 API 測試套件...\n")

        # 1. 功能測試
        print("1. 運行功能測試...")
        # 這裡需要 pytest 或自定義測試運行器

        # 2. 性能測試
        print("2. 運行性能測試...")
        perf_suite = APIPerformanceTestSuite(self.base_url, self.auth_headers)
        self.results["performance"] = {
            "response_times": await perf_suite.test_endpoint_response_times(),
            "concurrent_requests": await perf_suite.test_concurrent_requests(),
            "load_test": await perf_suite.test_load_over_time()
        }

        # 3. 集成測試
        print("3. 運行集成測試...")
        integration_suite = APIIntegrationTestSuite(self.base_url)
        self.results["integration"] = {
            "version_compatibility": await integration_suite.test_api_version_compatibility(),
            "websocket": await integration_suite.test_websocket_integration(),
            "error_handling": await integration_suite.test_error_handling()
        }

        return self.results

    def generate_report(self) -> str:
        """
        生成測試報告
        """
        report = ["# API 測試報告\n"]
        report.append(f"測試時間: {datetime.now().isoformat()}\n")

        # 性能測試報告
        if "performance" in self.results:
            report.append("## 性能測試結果\n")

            # 響應時間
            rt_results = self.results["performance"]["response_times"]
            report.append("### 端點響應時間 (ms)")
            for endpoint, metrics in rt_results.items():
                report.append(f"- {endpoint}:")
                report.append(f"  - 平均: {metrics['avg']*1000:.2f}ms")
                report.append(f"  - 最小: {metrics['min']*1000:.2f}ms")
                report.append(f"  - P95: {metrics['p95']*1000:.2f}ms")

            # 並發測試
            concurrent = self.results["performance"]["concurrent_requests"]
            report.append(f"\n### 並發測試")
            report.append(f"- 總請求: {concurrent['total_requests']}")
            report.append(f"- 成功率: {concurrent['success_rate']:.2%}")
            report.append(f"- 平均響應時間: {concurrent['avg_response_time']*1000:.2f}ms")

        # 集成測試報告
        if "integration" in self.results:
            report.append("\n## 集成測試結果\n")

            # 版本兼容性
            compat = self.results["integration"]["version_compatibility"]
            report.append("### 版本兼容性")
            for version, result in compat.items():
                status = "✅" if result["supports_version"] else "❌"
                report.append(f"- v{version}: {status}")

            # WebSocket
            ws_result = self.results["integration"]["websocket"]
            ws_status = "✅" if ws_result["connected"] else "❌"
            report.append(f"\n### WebSocket {ws_status}")
            if ws_result["connected"]:
                report.append(f"- 連接成功")
                report.append(f"- 接收消息: {ws_result['messages_received']}")
                report.append(f"- 訂閱確認: {'是' if ws_result['subscription_confirmed'] else '否'}")

            # 錯誤處理
            error_results = self.results["integration"]["error_handling"]
            report.append("\n### 錯誤處理")
            for endpoint, result in error_results.items():
                status = "✅" if result["correct"] else "❌"
                report.append(f"- {endpoint}: {status} (期望 {result['expected']}, 實際 {result['status']})")

        return "\n".join(report)


# 使用示例
async def run_api_tests():
    """
    運行 API 測試的示例
    """
    # 配置
    BASE_URL = "http://localhost:8000"
    AUTH_TOKEN = "your_auth_token_here"

    # 運行測試
    runner = APITestRunner(BASE_URL, AUTH_TOKEN)
    results = await runner.run_all_tests()

    # 生成報告
    report = runner.generate_report()

    # 保存報告
    with open("api_test_report.md", "w") as f:
        f.write(report)

    print("測試完成！報告已保存到 api_test_report.md")
    return results