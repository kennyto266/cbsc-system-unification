"""
Sprint API測試用例
測試Sprint管理系統的API端點

覆蓋範圍:
- Sprint CRUD操作
- Sprint規劃
- 指標計算
- 燃盡圖數據
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient


class TestSprintsAPI:
    """Sprint API測試類"""

    @pytest.fixture
    def client(self):
        """創建測試客戶端"""
        from fastapi import FastAPI

        from src.dashboard.api_sprints import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_create_sprint(self, client):
        """測試創建Sprint"""
        start_date = date.today()
        end_date = start_date + timedelta(days=14)

        sprint_data = {
            "name": "Sprint 測試",
            "goal": "測試Sprint創建功能",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        response = client.post("/api / v1 / sprints", json=sprint_data)
        assert response.status_code == 201

        result = response.json()
        assert result["data"]["name"] == sprint_data["name"]
        assert result["data"]["status"] == "PLANNING"

    def test_get_sprints(self, client):
        """測試獲取Sprint列表"""
        response = client.get("/api / v1 / sprints")
        assert response.status_code == 200

        result = response.json()
        assert "data" in result
        assert isinstance(result["data"], list)

    def test_get_sprint_by_id(self, client):
        """測試根據ID獲取Sprint"""
        # 創建Sprint
        start_date = date.today()
        end_date = start_date + timedelta(days=14)

        sprint_data = {
            "name": "測試Sprint 2",
            "goal": "測試獲取功能",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        create_response = client.post("/api / v1 / sprints", json=sprint_data)
        sprint_id = create_response.json()["data"]["id"]

        # 獲取Sprint
        response = client.get(f"/api / v1 / sprints/{sprint_id}")
        assert response.status_code == 200

        result = response.json()
        assert result["data"]["id"] == sprint_id

    def test_update_sprint(self, client):
        """測試更新Sprint"""
        # 創建Sprint
        start_date = date.today()
        end_date = start_date + timedelta(days=14)

        sprint_data = {
            "name": "更新測試",
            "goal": "原始目標",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        create_response = client.post("/api / v1 / sprints", json=sprint_data)
        sprint_id = create_response.json()["data"]["id"]

        # 更新Sprint
        update_data = {
            "name": "更新後的Sprint",
            "goal": "更新後的目標",
            "status": "ACTIVE",
        }
        response = client.put(f"/api / v1 / sprints/{sprint_id}", json=update_data)
        assert response.status_code == 200

        result = response.json()
        assert result["data"]["name"] == update_data["name"]
        assert result["data"]["goal"] == update_data["goal"]

    def test_sprint_planning(self, client):
        """測試Sprint規劃"""
        # 創建Sprint
        start_date = date.today()
        end_date = start_date + timedelta(days=14)

        sprint_data = {
            "name": "規劃測試",
            "goal": "測試Sprint規劃",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        create_response = client.post("/api / v1 / sprints", json=sprint_data)
        sprint_id = create_response.json()["data"]["id"]

        # 規劃Sprint
        planning_data = {
            "task_ids": ["TASK - 001", "TASK - 002", "TASK - 003"],
            "planned_hours": 30,
        }
        response = client.post(f"/api / v1 / sprints/{sprint_id}/plan", json=planning_data)
        assert response.status_code == 200

        result = response.json()
        assert "task_ids" in result["data"]
        assert "planned_hours" in result["data"]

    def test_get_sprint_metrics(self, client):
        """測試獲取Sprint指標"""
        # 創建Sprint
        start_date = date.today()
        end_date = start_date + timedelta(days=14)

        sprint_data = {
            "name": "指標測試",
            "goal": "測試指標計算",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        create_response = client.post("/api / v1 / sprints", json=sprint_data)
        sprint_id = create_response.json()["data"]["id"]

        # 獲取指標
        response = client.get(f"/api / v1 / sprints/{sprint_id}/metrics")
        assert response.status_code == 200

        result = response.json()
        metrics = result["data"]

        # 驗證指標字段
        assert "completion_rate" in metrics
        assert "velocity" in metrics
        assert "burndown_data" in metrics

    def test_sprint_status_transition(self, client):
        """測試Sprint狀態流轉"""
        # 創建Sprint
        start_date = date.today()
        end_date = start_date + timedelta(days=14)

        sprint_data = {
            "name": "狀態流轉測試",
            "goal": "測試狀態流轉",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        create_response = client.post("/api / v1 / sprints", json=sprint_data)
        sprint_id = create_response.json()["data"]["id"]

        # 狀態: PLANNING -> ACTIVE
        update_data = {"status": "ACTIVE"}
        response = client.put(f"/api / v1 / sprints/{sprint_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "ACTIVE"

        # 狀態: ACTIVE -> COMPLETED
        update_data = {"status": "COMPLETED"}
        response = client.put(f"/api / v1 / sprints/{sprint_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "COMPLETED"

    def test_delete_sprint(self, client):
        """測試刪除Sprint"""
        # 創建Sprint
        start_date = date.today()
        end_date = start_date + timedelta(days=14)

        sprint_data = {
            "name": "刪除測試",
            "goal": "測試Sprint刪除",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        create_response = client.post("/api / v1 / sprints", json=sprint_data)
        sprint_id = create_response.json()["data"]["id"]

        # 刪除Sprint
        response = client.delete(f"/api / v1 / sprints/{sprint_id}")
        assert response.status_code == 200

    def test_get_active_sprints(self, client):
        """測試獲取進行中的Sprint"""
        # 創建ACTIVE狀態的Sprint
        start_date = date.today()
        end_date = start_date + timedelta(days=14)

        sprint_data = {
            "name": "進行中測試",
            "goal": "測試獲取進行中Sprint",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "status": "ACTIVE",
        }
        client.post("/api / v1 / sprints", json=sprint_data)

        # 獲取進行中的Sprint
        response = client.get("/api / v1 / sprints?status=ACTIVE")
        assert response.status_code == 200

        result = response.json()
        assert all(sprint["status"] == "ACTIVE" for sprint in result["data"])

    def test_sprint_capacity_calculation(self, client):
        """測試Sprint容量計算"""
        # 創建Sprint
        start_date = date.today()
        end_date = start_date + timedelta(days=14)

        sprint_data = {
            "name": "容量測試",
            "goal": "測試容量計算",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "team_capacity": 80,  # 8人 * 10小時
        }
        create_response = client.post("/api / v1 / sprints", json=sprint_data)
        sprint_id = create_response.json()["data"]["id"]

        # 獲取指標
        response = client.get(f"/api / v1 / sprints/{sprint_id}/metrics")
        assert response.status_code == 200

        result = response.json()
        # 驗證容量相關指標
        assert "team_capacity" in result["data"]

    def test_invalid_sprint_creation(self, client):
        """測試無效Sprint創建"""
        # 結束日期早於開始日期
        start_date = date.today()
        end_date = start_date - timedelta(days=1)  # 無效

        sprint_data = {
            "name": "無效Sprint",
            "goal": "測試無效創建",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        response = client.post("/api / v1 / sprints", json=sprint_data)
        assert response.status_code == 422  # 驗證錯誤

    def test_sprint_not_found(self, client):
        """測試Sprint不存在"""
        response = client.get("/api / v1 / sprints / SPRINT - 999")
        assert response.status_code == 404

    def test_burndown_chart_data(self, client):
        """測試燃盡圖數據"""
        # 創建Sprint
        start_date = date.today()
        end_date = start_date + timedelta(days=14)

        sprint_data = {
            "name": "燃盡圖測試",
            "goal": "測試燃盡圖數據",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "planned_hours": 40,
        }
        create_response = client.post("/api / v1 / sprints", json=sprint_data)
        sprint_id = create_response.json()["data"]["id"]

        # 獲取燃盡圖數據
        response = client.get(f"/api / v1 / sprints/{sprint_id}/metrics")
        assert response.status_code == 200

        result = response.json()
        burndown_data = result["data"]["burndown_data"]

        # 驗證燃盡圖數據結構
        assert isinstance(burndown_data, list)
        if burndown_data:
            assert "date" in burndown_data[0]
            assert "remaining_hours" in burndown_data[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
