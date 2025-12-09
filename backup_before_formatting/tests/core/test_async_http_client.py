"""
AsyncHTTPClient 單元測試

測試範圍：
- US - 001: AsyncHTTPClient類實現
- US - 002: TCPConnector連接池實現
- US - 004: 重試機制實現
- US - 005: Prometheus監控實現
"""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

# 導入被測試的模塊
from src.core.async_http_client import (
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS_TOTAL,
    AsyncHTTPClient,
)


class TestAsyncHTTPClient:
    """AsyncHTTPClient測試類"""

    @pytest.fixture
    async def http_client(self):
        """HTTP客戶端fixture"""
        client = AsyncHTTPClient(
            max_connections=100,
            max_connections_per_host=50,
            timeout=10,
            max_retries=2,
            retry_backoff_factor=2.0,
        )
        await client.create_session()
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_http_client_initialization(self):
        """測試HTTP客戶端初始化"""
        client = AsyncHTTPClient(
            max_connections=200, max_connections_per_host=100, timeout=15, max_retries=3
        )

        assert client.max_connections == 200
        assert client.max_connections_per_host == 100
        assert client.timeout.total == 15
        assert client.max_retries == 3
        assert client.retry_backoff_factor == 2.0
        assert client.connector._limit == 200
        assert client.connector._limit_per_host == 100
        assert client.session is None

        await client.close()

    @pytest.mark.asyncio
    async def test_create_and_close_session(self):
        """測試創建和關閉會話"""
        client = AsyncHTTPClient(max_connections=10)

        assert client.session is None

        await client.create_session()
        assert client.session is not None
        assert not client.session.closed

        await client.close()
        assert client.session.closed

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """測試上下文管理器"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            async with AsyncHTTPClient() as client:
                assert client.session is not None
                assert not client.session.closed

            assert mock_session.close.called

    @pytest.mark.asyncio
    async def test_successful_get_request(self, http_client):
        """測試成功的GET請求 (US - 001)"""
        with patch.object(http_client.session, "request") as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"data": "test"})
            mock_response.headers = {"Content - Type": "application / json"}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_request.return_value = mock_response

            result = await http_client.get(
                "https://api.example.com / data", params={"key": "value"}
            )

            assert result["status"] == 200
            assert result["data"] == {"data": "test"}
            assert result["success"] is True
            assert "headers" in result
            assert "duration" in result
            assert result["attempts"] == 1

            # 驗證請求參數
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "GET"
            assert call_args[1]["params"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_successful_post_request(self, http_client):
        """測試成功的POST請求 (US - 001)"""
        with patch.object(http_client.session, "request") as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.json = AsyncMock(return_value={"id": 123})
            mock_response.headers = {"Content - Type": "application / json"}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_request.return_value = mock_response

            result = await http_client.post(
                "https://api.example.com / data", json={"name": "test"}
            )

            assert result["status"] == 201
            assert result["data"] == {"id": 123}
            assert result["success"] is True
            assert result["attempts"] == 1

    @pytest.mark.asyncio
    async def test_request_timeout_and_retry(self, http_client):
        """測試請求超時和重試機制 (US - 004)"""
        with patch.object(http_client.session, "request") as mock_request:
            # 模擬前兩次超時，第三次成功
            mock_request.side_effect = [
                asyncio.TimeoutError("Timeout 1"),
                asyncio.TimeoutError("Timeout 2"),
                AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": "success"}),
                    headers={},
                    __aenter__=AsyncMock(return_value=None),
                    __aexit__=AsyncMock(return_value=None),
                ),
            ]

            # 使用patch sleep避免實際等待
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                result = await http_client.get("https://api.example.com / data")

                assert result["success"] is True
                assert result["data"] == {"data": "success"}
                assert result["attempts"] == 3

                # 驗證重試次數
                assert mock_request.call_count == 3
                # 驗證退避等待
                assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, http_client):
        """測試超過最大重試次數 (US - 004)"""
        with patch.object(http_client.session, "request") as mock_request:
            # 模擬所有嘗試都失敗
            mock_request.side_effect = aiohttp.ClientError("Network error")

            result = await http_client.get("https://api.example.com / data")

            assert result["success"] is False
            assert "error" in result
            assert "error_type" in result
            assert result["attempts"] == http_client.max_retries + 1

            # 驗證重試次數
            assert mock_request.call_count == http_client.max_retries + 1

    @pytest.mark.asyncio
    async def test_http_error_no_retry(self, http_client):
        """測試HTTP錯誤不重試 (US - 004)"""
        with patch.object(http_client.session, "request") as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.raise_for_status = Mock(
                side_effect=aiohttp.ClientResponseError(
                    None, None, status=500, message="Server Error"
                )
            )
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_request.return_value = mock_response

            result = await http_client.get("https://api.example.com / data")

            assert result["success"] is False
            assert "error" in result
            # HTTP錯誤不應該重試，只嘗試一次
            assert mock_request.call_count == 1

    @pytest.mark.asyncio
    async def test_batch_request_success(self, http_client):
        """測試批量請求成功 (US - 003)"""
        with patch.object(http_client.session, "request") as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"status": "ok"})
            mock_response.headers = {}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_request.return_value = mock_response

            requests = [
                {"method": "GET", "url": "https://api1.com", "params": {}},
                {"method": "GET", "url": "https://api2.com", "params": {}},
                {"method": "POST", "url": "https://api3.com", "json": {}},
            ]

            results = await http_client.batch_request(requests, max_concurrent=2)

            assert len(results) == 3
            assert all(r["success"] for r in results)
            assert all("data" in r for r in results)

    @pytest.mark.asyncio
    async def test_batch_request_partial_failure(self, http_client):
        """測試批量請求部分失敗 (US - 003)"""
        with patch.object(http_client.session, "request") as mock_request:
            # 模擬部分請求失敗
            mock_request.side_effect = [
                AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": "success1"}),
                    headers={},
                    __aenter__=AsyncMock(return_value=None),
                    __aexit__=AsyncMock(return_value=None),
                ),
                aiohttp.ClientError("Network error"),
                AsyncMock(
                    status=200,
                    json=AsyncMock(return_value={"data": "success2"}),
                    headers={},
                    __aenter__=AsyncMock(return_value=None),
                    __aexit__=AsyncMock(return_value=None),
                ),
            ]

            requests = [
                {"method": "GET", "url": "https://api1.com", "params": {}},
                {"method": "GET", "url": "https://api2.com", "params": {}},
                {"method": "GET", "url": "https://api3.com", "params": {}},
            ]

            results = await http_client.batch_request(requests)

            assert len(results) == 3
            assert results[0]["success"] is True
            assert results[1]["success"] is False
            assert results[2]["success"] is True

    @pytest.mark.asyncio
    async def test_connection_pool_configuration(self, http_client):
        """測試連接池配置 (US - 002)"""
        # 驗證連接池配置
        assert http_client.connector._limit == 100
        assert http_client.connector._limit_per_host == 50
        assert http_client.connector._keepalive_timeout == 30

    @pytest.mark.asyncio
    async def test_get_pool_status(self, http_client):
        """測試獲取連接池狀態 (US - 002)"""
        status = await http_client.get_pool_status()

        assert "total_connections" in status
        assert "available_connections" in status
        assert "closed_connections" in status
        assert "in_flight_connections" in status
        assert "max_per_host" in status

        assert status["total_connections"] == 100
        assert status["max_per_host"] == 50

    def test_extract_host(self, http_client):
        """測試提取主機名"""
        assert (
            http_client._extract_host("https://api.example.com / data")
            == "api.example.com"
        )
        assert (
            http_client._extract_host("http://localhost:8080 / path") == "localhost:8080"
        )
        assert http_client._extract_host("invalid - url") == "unknown"

    @pytest.mark.asyncio
    async def test_metrics_collection(self, http_client):
        """測試Prometheus指標收集 (US - 005)"""
        with patch.object(http_client.session, "request") as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"data": "test"})
            mock_response.headers = {}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_request.return_value = mock_response

            await http_client.get("https://api.example.com / data")

            # 獲取指標
            metrics = http_client.get_metrics()

            assert "requests_total" in metrics
            assert "request_duration_seconds_sum" in metrics
            assert "concurrent_requests" in metrics
            assert "retries_total" in metrics

    @pytest.mark.asyncio
    async def test_load_config(self):
        """測試加載配置文件"""
        # 創建測試配置文件
        import tempfile

        import yaml

        config_data = {
            "http_client": {"max_connections": 500, "timeout": 20, "max_retries": 5}
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            client = AsyncHTTPClient(config_path=config_path)
            await client.create_session()

            assert client.max_connections == 500
            assert client.timeout.total == 20
            assert client.max_retries == 5

            await client.close()
        finally:
            import os

            os.unlink(config_path)


class TestHTTPClientRetryMechanism:
    """重試機制專項測試"""

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """測試指數退避算法"""
        client = AsyncHTTPClient(max_retries=3, retry_backoff_factor=2.0)

        with patch.object(client.session, "request") as mock_request:
            mock_request.side_effect = aiohttp.ClientError("Error")

            with patch("asyncio.sleep") as mock_sleep:
                await client.get("https://api.example.com")

                # 驗證退避等待時間
                assert mock_sleep.call_count == client.max_retries
                # 2^0, 2^1, 2^2
                assert mock_sleep.call_args_list[0][0][0] == 1.0
                assert mock_sleep.call_args_list[1][0][0] == 2.0
                assert mock_sleep.call_args_list[2][0][0] == 4.0

        await client.close()

    @pytest.mark.asyncio
    async def test_retry_with_different_error_types(self):
        """測試不同錯誤類型的重試"""
        client = AsyncHTTPClient(max_retries=2)

        test_cases = [
            asyncio.TimeoutError("Timeout"),
            aiohttp.ClientError("Connection error"),
            aiohttp.ClientConnectorError(None, None, "DNS error"),
        ]

        for error in test_cases:
            with patch.object(client.session, "request") as mock_request:
                mock_request.side_effect = error

                result = await client.get("https://api.example.com")

                assert result["success"] is False
                assert result["error_type"] in [
                    "TimeoutError",
                    "ClientError",
                    "ClientConnectorError",
                ]

        await client.close()


class TestHTTPClientBatchProcessing:
    """批量處理專項測試"""

    @pytest.mark.asyncio
    async def test_batch_request_semaphore(self):
        """測試批量請求信號量控制"""
        client = AsyncHTTPClient()

        with patch.object(client.session, "request") as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"status": "ok"})
            mock_response.headers = {}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_request.return_value = mock_response

            # 創建10個請求，限制併發為3
            requests = [
                {"method": "GET", "url": f"https://api{i}.com", "params": {}}
                for i in range(10)
            ]

            start_time = asyncio.get_event_loop().time()
            results = await client.batch_request(requests, max_concurrent=3)
            end_time = asyncio.get_event_loop().time()

            # 驗證所有請求完成
            assert len(results) == 10
            assert all(r["success"] for r in results)

        await client.close()


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v"])
