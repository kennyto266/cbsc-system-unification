"""
單元測試 - 基礎功能測試
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthCheck:
    """健康檢查測試"""

    def test_health_endpoint(self):
        """測試健康檢查端點"""
        from complete_project_system import app

        client = TestClient(app)
        response = client.get("/api / health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestBasicAPI:
    """基礎API測試"""

    def test_get_stock_data(self):
        """測試獲取股票數據"""
        from complete_project_system import app

        client = TestClient(app)
        response = client.post(
            "/api / data / stock", json={"symbol": "0700.HK", "period": "1y"}
        )
        assert response.status_code == 200
        assert "data" in response.json()
