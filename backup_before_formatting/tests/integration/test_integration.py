"""
集成測試
"""

import os

import pytest
from fastapi.testclient import TestClient


class TestAPIIntegration:
    """API集成測試"""

    @pytest.fixture
    def client(self):
        """創建測試客戶端"""
        from complete_project_system import app

        return TestClient(app)

    def test_complete_workflow(self, client):
        """測試完整工作流程"""
        # 1. 健康檢查
        response = client.get("/api / health")
        assert response.status_code == 200

        # 2. 獲取股票數據
        response = client.post(
            "/api / data / stock", json={"symbol": "0700.HK", "period": "1y"}
        )
        assert response.status_code == 200

        # 3. 運行回測
        response = client.post(
            "/api / backtest",
            json={
                "symbol": "0700.HK",
                "start_date": "2023 - 01 - 01",
                "end_date": "2023 - 12 - 31",
                "strategy": "ma",
            },
        )
        assert response.status_code == 200


class TestPerformance:
    """性能測試"""

    def test_response_time(self):
        """測試響應時間"""
        from complete_project_system import app

        client = TestClient(app)
        response = client.get("/api / health")
        assert response.elapsed.total_seconds() < 1.0
