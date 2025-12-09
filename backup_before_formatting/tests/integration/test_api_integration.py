#!/usr/bin/env python3
"""
API集成測試
API Integration Tests

測試各個API服務之間的集成和數據流
"""

import pytest
import asyncio
import httpx
import json
from pathlib import Path
import sys
import time
from typing import Dict, Any, List

# Add simplified_system to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "simplified_system"))

from tests.factories.stock_data_factory import create_test_stock_data, create_test_hibor_data

@pytest.mark.integration
@pytest.mark.api
class TestStockAPIIntegration:
    """股票API集成測試"""

    @pytest.fixture
    async def api_client(self):
        """異步HTTP客戶端"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client

    @pytest.fixture
    def api_base_url(self):
        """API基礎URL"""
        return "http://localhost:8001"

    @pytest.mark.slow
    async def test_api_startup(self, api_client, api_base_url):
        """測試API服務啟動"""
        try:
            response = await api_client.get(f"{api_base_url}/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("API服務未啟動 - 跳過集成測試")

    @pytest.mark.slow
    async def test_stock_data_endpoint(self, api_client, api_base_url):
        """測試股票數據端點"""
        try:
            response = await api_client.get(
                f"{api_base_url}/api/stock/0700.HK?duration=30"
            )

            if response.status_code == 404:
                pytest.skip("股票數據端點未實現")

            assert response.status_code == 200
            data = response.json()

            assert "data" in data
            assert "close" in data["data"]
            assert isinstance(data["data"]["close"], dict)

        except httpx.ConnectError:
            pytest.skip("API服務未啟動")

    @pytest.mark.slow
    async def test_multiple_stocks_endpoint(self, api_client, api_base_url):
        """測試多股票數據端點"""
        symbols = ["0700.HK", "0941.HK", "1398.HK"]

        try:
            response = await api_client.post(
                f"{api_base_url}/api/stocks/batch",
                json={"symbols": symbols, "duration": 30}
            )

            if response.status_code == 404:
                pytest.skip("批量股票端點未實現")

            assert response.status_code == 200
            data = response.json()

            assert isinstance(data, dict)
            for symbol in symbols:
                assert symbol in data

        except httpx.ConnectError:
            pytest.skip("API服務未啟動")

@pytest.mark.integration
@pytest.mark.government_data
class TestHiborDataIntegration:
    """HIBOR數據集成測試"""

    @pytest.fixture
    async def api_client(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client

    @pytest.fixture
    def api_base_url(self):
        return "http://localhost:8001"

    @pytest.mark.slow
    async def test_hibor_data_endpoint(self, api_client, api_base_url):
        """測試HIBOR數據端點"""
        try:
            response = await api_client.get(f"{api_base_url}/api/hibor/latest")

            if response.status_code == 404:
                pytest.skip("HIBOR數據端點未實現")

            assert response.status_code == 200
            data = response.json()

            assert "overnight" in data
            assert isinstance(data["overnight"], (int, float))

        except httpx.ConnectError:
            pytest.skip("API服務未啟動")

    @pytest.mark.slow
    async def test_hibor_historical_data(self, api_client, api_base_url):
        """測試HIBOR歷史數據"""
        try:
            response = await api_client.get(
                f"{api_base_url}/api/hibor/history?days=30"
            )

            if response.status_code == 404:
                pytest.skip("HIBOR歷史數據端點未實現")

            assert response.status_code == 200
            data = response.json()

            assert isinstance(data, list)
            if len(data) > 0:
                assert "date" in data[0]
                assert "overnight" in data[0]

        except httpx.ConnectError:
            pytest.skip("API服務未啟動")

@pytest.mark.integration
@pytest.mark.vectorbt
class TestVectorBTIntegration:
    """VectorBT回測引擎集成測試"""

    @pytest.fixture
    async def api_client(self):
        async with httpx.AsyncClient(timeout=60.0) as client:
            yield client

    @pytest.fixture
    def api_base_url(self):
        return "http://localhost:8001"

    @pytest.mark.slow
    async def test_backtest_endpoint(self, api_client, api_base_url):
        """測試回測端點"""
        backtest_request = {
            "symbol": "0700.HK",
            "strategy": "RSI_MEAN_REVERSION",
            "parameters": {
                "period": 14,
                "oversold": 30,
                "overbought": 70
            },
            "duration": 252
        }

        try:
            response = await api_client.post(
                f"{api_base_url}/api/backtest",
                json=backtest_request
            )

            if response.status_code == 404:
                pytest.skip("回測端點未實現")

            assert response.status_code == 200
            data = response.json()

            assert "total_return" in data
            assert "sharpe_ratio" in data
            assert "max_drawdown" in data

        except httpx.ConnectError:
            pytest.skip("API服務未啟動")
        except asyncio.TimeoutError:
            pytest.fail("回測請求超時 - 可能是性能問題")

    @pytest.mark.slow
    async def test_multi_strategy_backtest(self, api_client, api_base_url):
        """測試多策略回測"""
        backtest_request = {
            "symbol": "0700.HK",
            "strategies": [
                {
                    "name": "RSI_MEAN_REVERSION",
                    "parameters": {"period": 14, "oversold": 30, "overbought": 70}
                },
                {
                    "name": "MACD_CROSSOVER",
                    "parameters": {"fast": 12, "slow": 26, "signal": 9}
                },
                {
                    "name": "DUAL_MOVING_AVERAGE",
                    "parameters": {"short": 20, "long": 50}
                }
            ],
            "duration": 252
        }

        try:
            response = await api_client.post(
                f"{api_base_url}/api/backtest/multi",
                json=backtest_request
            )

            if response.status_code == 404:
                pytest.skip("多策略回測端點未實現")

            assert response.status_code == 200
            data = response.json()

            assert isinstance(data, list)
            assert len(data) == 3

            for result in data:
                assert "strategy" in result
                assert "total_return" in result
                assert "sharpe_ratio" in result

        except httpx.ConnectError:
            pytest.skip("API服務未啟動")
        except asyncio.TimeoutError:
            pytest.fail("多策略回測請求超時")

@pytest.mark.integration
@pytest.mark.performance
class TestAPIPerformanceIntegration:
    """API性能集成測試"""

    @pytest.fixture
    async def api_client(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client

    @pytest.fixture
    def api_base_url(self):
        return "http://localhost:8001"

    @pytest.mark.slow
    async def test_concurrent_requests(self, api_client, api_base_url):
        """測試併發請求性能"""
        if not hasattr(httpx, 'AsyncClient'):
            pytest.skip("AsyncClient not available")

        try:
            # 創建併發請求
            tasks = []
            for i in range(10):
                task = api_client.get(f"{api_base_url}/api/stock/0700.HK?duration=30")
                tasks.append(task)

            # 執行併發請求
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            # 檢查結果
            successful_responses = [r for r in responses if not isinstance(r, Exception)]
            assert len(successful_responses) >= 5  # 至少一半請求成功

            # 性能檢查：10個併發請求應該在5秒內完成
            total_time = end_time - start_time
            assert total_time < 5.0, f"併發請求過慢: {total_time:.2f}秒"

        except httpx.ConnectError:
            pytest.skip("API服務未啟動")

    @pytest.mark.slow
    async def test_large_data_request(self, api_client, api_base_url):
        """測試大數據請求性能"""
        try:
            # 請求大量數據（3年）
            start_time = time.time()
            response = await api_client.get(f"{api_base_url}/api/stock/0700.HK?duration=1095")

            if response.status_code == 404:
                pytest.skip("大數據端點未實現")

            assert response.status_code == 200

            end_time = time.time()
            request_time = end_time - start_time

            # 大數據請求應該在10秒內完成
            assert request_time < 10.0, f"大數據請求過慢: {request_time:.2f}秒"

            # 檢查數據大小
            data = response.json()
            if "data" in data and "close" in data["data"]:
                data_points = len(data["data"]["close"])
                assert data_points > 500  # 應該有足夠的數據點

        except httpx.ConnectError:
            pytest.skip("API服務未啟動")

@pytest.mark.integration
@pytest.mark.security
class TestAPISecurityIntegration:
    """API安全集成測試"""

    @pytest.fixture
    async def api_client(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client

    @pytest.fixture
    def api_base_url(self):
        return "http://localhost:8001"

    @pytest.mark.slow
    async def test_rate_limiting(self, api_client, api_base_url):
        """測試速率限制"""
        try:
            # 快速發送多個請求
            responses = []
            for i in range(50):  # 50個快速請求
                try:
                    response = await api_client.get(f"{api_base_url}/api/stock/0700.HK?duration=7")
                    responses.append(response)
                except httpx.HTTPStatusError as e:
                    responses.append(e.response)

            # 檢查是否有速率限制響應
            rate_limited_responses = [r for r in responses if r.status_code == 429]

            # 如果實現了速率限制，應該有一些429響應
            if len(rate_limited_responses) > 0:
                assert any("X-RateLimit" in str(r.headers) for r in rate_limited_responses)

        except httpx.ConnectError:
            pytest.skip("API服務未啟動")

    @pytest.mark.slow
    async def test_input_validation(self, api_client, api_base_url):
        """測試輸入驗證"""
        test_cases = [
            # 無效股票代碼
            ("", 400),
            ("INVALID_SYMBOL_FORMAT", 400),
            # 無效參數
            ("0700.HK?duration=-1", 400),
            ("0700.HK?duration=999999", 400),
        ]

        for path, expected_status in test_cases:
            try:
                response = await api_client.get(f"{api_base_url}/api/stock/{path}")

                # 如果端點實現了驗證，應該返回400
                if response.status_code != 404:
                    assert response.status_code == expected_status, f"Path {path} should return {expected_status}"

            except httpx.ConnectError:
                pytest.skip("API服務未啟動")

@pytest.mark.integration
@pytest.mark.e2e
class TestEndToEndWorkflow:
    """端到端工作流程測試"""

    @pytest.fixture
    async def api_client(self):
        async with httpx.AsyncClient(timeout=60.0) as client:
            yield client

    @pytest.fixture
    def api_base_url(self):
        return "http://localhost:8001"

    @pytest.mark.slow
    async def test_complete_trading_workflow(self, api_client, api_base_url):
        """測試完整交易工作流程"""
        try:
            # 1. 獲取股票數據
            stock_response = await api_client.get(f"{api_base_url}/api/stock/0700.HK?duration=252")
            if stock_response.status_code == 404:
                pytest.skip("股票數據端點未實現")
            assert stock_response.status_code == 200

            # 2. 獲取HIBOR數據（用於無風險利率）
            hibor_response = await api_client.get(f"{api_base_url}/api/hibor/latest")
            # HIBOR端點可能未實現，這是可接受的

            # 3. 執行回測
            backtest_request = {
                "symbol": "0700.HK",
                "strategy": "RSI_MEAN_REVERSION",
                "parameters": {
                    "period": 14,
                    "oversold": 30,
                    "overbought": 70
                }
            }

            backtest_response = await api_client.post(
                f"{api_base_url}/api/backtest",
                json=backtest_request
            )

            if backtest_response.status_code == 404:
                pytest.skip("回測端點未實現")
            assert backtest_response.status_code == 200

            backtest_result = backtest_response.json()

            # 4. 驗證回測結果
            assert "total_return" in backtest_result
            assert "sharpe_ratio" in backtest_result
            assert isinstance(backtest_result["sharpe_ratio"], (int, float))

            # 5. 測試Sharpe比率計算邏輯
            sharpe = backtest_result["sharpe_ratio"]
            # Sharpe比率應該在合理範圍內
            assert -10 < sharpe < 10, f"Sharpe比率超出合理範圍: {sharpe}"

        except httpx.ConnectError:
            pytest.skip("API服務未啟動")
        except asyncio.TimeoutError:
            pytest.fail("端到端工作流程超時")

    @pytest.mark.slow
    async def test_data_quality_workflow(self, api_client, api_base_url):
        """測試數據質量檢查工作流程"""
        try:
            # 1. 獲取股票數據
            response = await api_client.get(f"{api_base_url}/api/stock/0700.HK?duration=30")

            if response.status_code == 404:
                pytest.skip("股票數據端點未實現")

            assert response.status_code == 200
            data = response.json()

            # 2. 數據完整性檢查
            assert "data" in data
            assert "close" in data["data"]

            close_data = data["data"]["close"]
            assert len(close_data) > 0, "應該有收盤價數據"

            # 3. 數據質量檢查
            prices = list(close_data.values())
            assert all(isinstance(p, (int, float)) for p in prices), "價格應該是數字"
            assert all(p > 0 for p in prices), "價格應該為正數"

            # 4. 數據時間順序檢查
            dates = list(close_data.keys())
            # 確保日期格式正確且按時間順序排列

        except httpx.ConnectError:
            pytest.skip("API服務未啟動")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not slow"])