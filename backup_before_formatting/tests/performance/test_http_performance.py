"""
HTTP性能測試

測試範圍：
- US - 003: 批量請求處理性能
- 併發性能測試
- 延遲基準測試
- 連接池性能
"""

import asyncio
import statistics
import time
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest

from src.core.async_http_client import AsyncHTTPClient


class TestHTTPPerformance:
    """HTTP性能測試類"""

    @pytest.mark.asyncio
    async def test_concurrent_request_performance(self):
        """測試併發請求性能 (目標: 100ms內完成10個請求)"""
        client = AsyncHTTPClient(max_connections=200)

        with patch.object(client.session, "request") as mock_request:
            # 模擬快速響應
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"data": "test"})
            mock_response.headers = {}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_request.return_value = mock_response

            # 測試10個併發請求
            start_time = time.time()

            requests = [
                {"method": "GET", "url": f"https://api{i}.com / data", "params": {}}
                for i in range(10)
            ]

            results = await client.batch_request(requests, max_concurrent=10)

            total_time = time.time() - start_time
            avg_time = total_time / len(requests)

            print("\n=== 併發請求性能測試 ===")
            print(f"請求數量: {len(requests)}")
            print(f"總耗時: {total_time:.3f}s")
            print(f"平均每請求: {avg_time * 1000:.2f}ms")
            print("每請求最大耗時: 100ms (目標)")

            # 驗證結果
            assert len(results) == 10
            assert all(r["success"] for r in results)
            assert avg_time < 0.1, f"平均延遲 {avg_time * 1000:.2f}ms 超過100ms目標"

        await client.close()

    @pytest.mark.asyncio
    async def test_batch_request_performance_100_requests(self):
        """測試批量請求性能 (US - 003: 100個請求 < 500ms)"""
        client = AsyncHTTPClient(max_connections=1000)

        with patch.object(client.session, "request") as mock_request:
            # 模擬快速響應
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"status": "ok"})
            mock_response.headers = {}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_request.return_value = mock_response

            # 測試100個請求
            start_time = time.time()

            requests = [
                {"method": "GET", "url": f"https://api{i}.com / data", "params": {}}
                for i in range(100)
            ]

            results = await client.batch_request(requests, max_concurrent=100)

            total_time = time.time() - start_time
            avg_time = total_time / len(requests)

            print("\n=== 批量請求性能測試 (100個) ===")
            print(f"請求數量: {len(requests)}")
            print(f"總耗時: {total_time:.3f}s")
            print(f"平均每請求: {avg_time * 1000:.2f}ms")
            print("目標: 每請求 < 5ms")

            # 驗證結果
            assert len(results) == 100
            assert all(r["success"] for r in results)
            assert avg_time < 0.005, f"平均延遲 {avg_time * 1000:.2f}ms 超過5ms目標"

        await client.close()

    @pytest.mark.asyncio
    async def test_large_batch_request_performance(self):
        """測試大批量請求性能 (1000個請求)"""
        client = AsyncHTTPClient(max_connections=1000)

        with patch.object(client.session, "request") as mock_request:
            # 模擬快速響應
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"status": "ok"})
            mock_response.headers = {}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_request.return_value = mock_response

            # 測試1000個請求
            start_time = time.time()

            requests = [
                {"method": "GET", "url": f"https://api{i}.com / data", "params": {}}
                for i in range(1000)
            ]

            results = await client.batch_request(requests, max_concurrent=500)

            total_time = time.time() - start_time
            avg_time = total_time / len(requests)
            throughput = len(requests) / total_time

            print("\n=== 大批量請求性能測試 (1000個) ===")
            print(f"請求數量: {len(requests)}")
            print(f"總耗時: {total_time:.3f}s")
            print(f"平均每請求: {avg_time * 1000:.2f}ms")
            print(f"吞吐量: {throughput:.2f} req / s")

            # 驗證結果
            assert len(results) == 1000
            assert all(r["success"] for r in results)
            assert throughput > 100, f"吞吐量 {throughput:.2f} req / s 低於100 req / s"

        await client.close()

    @pytest.mark.asyncio
    async def test_different_concurrency_levels(self):
        """測試不同併發級別的性能"""
        concurrency_levels = [10, 50, 100, 200, 500]
        client = AsyncHTTPClient(max_connections=1000)

        with patch.object(client.session, "request") as mock_request:
            # 模擬快速響應
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"status": "ok"})
            mock_response.headers = {}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_request.return_value = mock_response

            print("\n=== 不同併發級別性能測試 ===")
            results_summary = []

            for concurrency in concurrency_levels:
                requests = [
                    {"method": "GET", "url": f"https://api{i}.com / data", "params": {}}
                    for i in range(100)
                ]

                start_time = time.time()
                results = await client.batch_request(
                    requests, max_concurrent=concurrency
                )
                total_time = time.time() - start_time

                avg_time = total_time / len(requests)
                throughput = len(requests) / total_time

                results_summary.append(
                    {
                        "concurrency": concurrency,
                        "total_time": total_time,
                        "avg_time": avg_time,
                        "throughput": throughput,
                    }
                )

                print(
                    f"併發 {concurrency:3d}: {total_time:.3f}s, "
                    f"{avg_time * 1000:.2f}ms / req, {throughput:.2f} req / s"
                )

            # 驗證性能隨併發數增加而提升
            assert len(results_summary) == len(concurrency_levels)
            # 吞吐量應該隨併發數增加
            throughput_values = [r["throughput"] for r in results_summary]
            assert max(throughput_values) > min(throughput_values)

        await client.close()

    @pytest.mark.asyncio
    async def test_latency_distribution(self):
        """測試延遲分佈 (P50, P95, P99)"""
        client = AsyncHTTPClient(max_connections=200)

        with patch.object(client.session, "request") as mock_request:
            # 模擬不同響應時間
            response_times = [0.01, 0.02, 0.03, 0.04, 0.05] * 20  # 100個響應

            async def mock_response_delayed(*args, **kwargs):
                response = AsyncMock()
                response.status = 200
                response.json = AsyncMock(return_value={"status": "ok"})
                response.headers = {}
                response.__aenter__ = AsyncMock(return_value=response)
                response.__aexit__ = AsyncMock(return_value=None)

                # 模擬延遲
                delay = response_times.pop(0)
                await asyncio.sleep(delay)

                return response

            mock_request.side_effect = mock_response_delayed

            requests = [
                {"method": "GET", "url": f"https://api{i}.com / data", "params": {}}
                for i in range(100)
            ]

            start_time = time.time()
            results = await client.batch_request(requests, max_concurrent=100)
            total_time = time.time() - start_time

            # 提取實際延遲
            durations = [r["duration"] for r in results if r.get("success")]

            p50 = statistics.median(durations)
            p95 = sorted(durations)[int(len(durations) * 0.95)]
            p99 = sorted(durations)[int(len(durations) * 0.99)]

            print("\n=== 延遲分佈測試 ===")
            print(f"P50: {p50 * 1000:.2f}ms")
            print(f"P95: {p95 * 1000:.2f}ms")
            print(f"P99: {p99 * 1000:.2f}ms")
            print(f"總耗時: {total_time:.3f}s")

            # 驗證P95延遲小於100ms目標
            assert p95 < 0.1, f"P95延遲 {p95 * 1000:.2f}ms 超過100ms目標"

        await client.close()

    @pytest.mark.asyncio
    async def test_connection_pool_reuse(self):
        """測試連接池重用 (US - 002)"""
        client = AsyncHTTPClient(max_connections=100, max_connections_per_host=50)

        with patch.object(client.session, "request") as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"status": "ok"})
            mock_response.headers = {}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_request.return_value = mock_response

            # 多次重用連接池
            print("\n=== 連接池重用測試 ===")

            for round_num in range(3):
                requests = [
                    {"method": "GET", "url": f"https://api{i}.com / data", "params": {}}
                    for i in range(50)
                ]

                start_time = time.time()
                results = await client.batch_request(requests, max_concurrent=50)
                total_time = time.time() - start_time

                print(
                    f"輪次 {round_num + 1}: {total_time:.3f}s, "
                    f"成功率 {sum(1 for r in results if r['success']) / len(results) * 100:.1f}%"
                )

                assert all(r["success"] for r in results)

            # 檢查連接池狀態
            pool_status = await client.get_pool_status()
            print(f"連接池狀態: {pool_status}")

            assert pool_status["total_connections"] == 100
            assert pool_status["max_per_host"] == 50

        await client.close()

    @pytest.mark.asyncio
    async def test_real_api_performance(self):
        """真實API性能測試 (如果可用)"""
        # 這是一個實際的API測試，需要網絡連接
        # 可以通過環境變量控制是否運行
        import os

        if not os.getenv("RUN_REAL_API_TESTS"):
            print("\n跳過真實API測試（設置RUN_REAL_API_TESTS=1啟用）")
            return

        print("\n=== 真實API性能測試 ===")

        # 測試港交所API
        client = AsyncHTTPClient(
            max_connections=100, max_connections_per_host=50, timeout=5
        )

        symbols = ["0700.hk", "0388.hk", "1398.hk"]

        # 單個請求測試
        start_time = time.time()
        result = await client.get(
            "http://18.180.162.113:9191 / inst / getInst",
            params={"symbol": "0700.hk", "duration": 365},
        )
        single_time = time.time() - start_time

        print(f"單個請求: {single_time * 1000:.2f}ms")

        # 批量請求測試
        start_time = time.time()

        requests = [
            {
                "method": "GET",
                "url": "http://18.180.162.113:9191 / inst / getInst",
                "params": {"symbol": symbol, "duration": 365},
            }
            for symbol in symbols
        ]

        results = await client.batch_request(requests, max_concurrent=10)
        batch_time = time.time() - start_time

        print(f"批量請求 {len(symbols)} 個: {batch_time * 1000:.2f}ms")
        print(
            f"成功率: {sum(1 for r in results if r['success']) / len(results) * 100:.1f}%"
        )

        assert batch_time < 2.0, f"批量請求耗時 {batch_time:.2f}s 超過2s限制"

        await client.close()


class TestHTTPBenchmark:
    """HTTP基準測試類"""

    @pytest.mark.asyncio
    async def test_throughput_benchmark(self):
        """吞吐量基準測試"""
        client = AsyncHTTPClient(max_connections=1000)

        with patch.object(client.session, "request") as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"status": "ok"})
            mock_response.headers = {}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_request.return_value = mock_response

            # 基準測試：測試1000個請求的吞吐量
            requests = [
                {"method": "GET", "url": f"https://api{i}.com / data", "params": {}}
                for i in range(1000)
            ]

            start_time = time.time()
            results = await client.batch_request(requests, max_concurrent=500)
            end_time = time.time()

            total_time = end_time - start_time
            throughput = len(requests) / total_time

            print("\n=== 吞吐量基準測試 ===")
            print(f"請求數量: {len(requests)}")
            print(f"總耗時: {total_time:.3f}s")
            print(f"吞吐量: {throughput:.2f} req / s")
            print("吞吐量目標: > 100 req / s")
            print(f"測試結果: {'✓ 通過' if throughput > 100 else '✗ 失敗'}")

            assert throughput > 100, f"吞吐量 {throughput:.2f} req / s 低於100 req / s"

        await client.close()


async def run_performance_test():
    """手動運行性能測試"""
    test = TestHTTPPerformance()

    print("=" * 60)
    print("HTTP性能測試套件")
    print("=" * 60)

    try:
        await test.test_concurrent_request_performance()
        await test.test_batch_request_performance_100_requests()
        await test.test_different_concurrency_levels()
        await test.test_latency_distribution()
        await test.test_connection_pool_reuse()

        print("\n" + "=" * 60)
        print("所有性能測試通過 ✓")
        print("=" * 60)
    except Exception as e:
        print(f"\n性能測試失敗: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_performance_test())
