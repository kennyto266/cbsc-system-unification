"""
端到端測試
"""

import time

import pytest
from fastapi.testclient import TestClient


class TestFullSystem:
    """完整系統端到端測試"""

    @pytest.fixture
    def client(self):
        from complete_project_system import app

        return TestClient(app)

    def test_complete_trading_workflow(self, client):
        """完整交易工作流程"""
        # 1. 系統健康檢查
        response = client.get("/api / health")
        assert response.status_code == 200

        # 2. 獲取股票數據
        response = client.post(
            "/api / data / stock", json={"symbol": "0700.HK", "period": "1y"}
        )
        assert response.status_code == 200
        data = response.json()

        # 3. 分析策略
        response = client.post(
            "/api / strategy",
            json={
                "symbol": "0700.HK",
                "strategy": "rsi",
                "params": {"period": 14, "overbought": 70, "oversold": 30},
            },
        )
        assert response.status_code == 200
        strategy_data = response.json()
        assert "signals" in strategy_data

        # 4. 運行回測
        response = client.post(
            "/api / backtest",
            json={
                "symbol": "0700.HK",
                "start_date": "2023 - 01 - 01",
                "end_date": "2023 - 12 - 31",
                "strategy": "ma",
                "params": {"short_window": 20, "long_window": 50},
            },
        )
        assert response.status_code == 200
        backtest_data = response.json()
        assert "result" in backtest_data

        # 5. 驗證結果
        assert "total_return" in backtest_data["result"]
        assert "sharpe_ratio" in backtest_data["result"]
        assert "max_drawdown" in backtest_data["result"]


class TestLoad:
    """負載測試"""

    def test_multiple_requests(self):
        """測試多個並發請求"""
        import threading
        import time

        from complete_project_system import app

        client = TestClient(app)
        errors = []

        def make_request():
            try:
                response = client.get("/api / health")
                if response.status_code != 200:
                    errors.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # 發送10個並發請求
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0, f"Errors: {errors}"
