"""
API端點測試
"""

import json

import pytest
from fastapi.testclient import TestClient


class TestDataEndpoints:
    """數據API測試"""

    @pytest.fixture
    def client(self):
        from complete_project_system import app

        return TestClient(app)

    def test_stock_data(self, client):
        """測試股票數據端點"""
        response = client.post(
            "/api / data / stock", json={"symbol": "0700.HK", "period": "1y"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_invalid_symbol(self, client):
        """測試無效股票代碼"""
        response = client.post(
            "/api / data / stock", json={"symbol": "INVALID", "period": "1y"}
        )
        assert response.status_code == 400


class TestBacktestEndpoints:
    """回測API測試"""

    @pytest.fixture
    def client(self):
        from complete_project_system import app

        return TestClient(app)

    def test_run_backtest(self, client):
        """測試運行回測"""
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
        data = response.json()
        assert "result" in data
