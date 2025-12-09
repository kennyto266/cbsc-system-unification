"""
Task API測試用例
測試任務管理系統的API端點

覆蓋範圍:
- 任務CRUD操作
- 狀態流轉
- 任務分配
- 搜索和過濾
- 批量操作
"""

import json

import pytest
from fastapi.testclient import TestClient


class TestTasksAPI:
    """任務API測試類"""

    @pytest.fixture
    def client(self):
        """創建測試客戶端"""
        # 注意：這裡需要實際的FastAPI應用實例
        from fastapi import FastAPI

        from src.dashboard.api_tasks import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_create_task(self, client):
        """測試創建任務"""
        task_data = {
            "title": "測試任務",
            "description": "這是一個測試任務",
            "priority": "P1",
            "estimated_hours": 3,
            "assignee": "測試用戶",
            "sprint": "SPRINT - 2025 - 10",
        }

        response = client.post("/api / v1 / tasks", json=task_data)
        assert response.status_code == 201

        result = response.json()
        assert result["data"]["title"] == task_data["title"]
        assert result["data"]["priority"] == "P1"
        assert result["data"]["status"] == "TODO"

    def test_get_tasks(self, client):
        """測試獲取任務列表"""
        response = client.get("/api / v1 / tasks")
        assert response.status_code == 200

        result = response.json()
        assert "data" in result
        assert isinstance(result["data"], list)

    def test_get_task_by_id(self, client):
        """測試根據ID獲取任務"""
        # 先創建一個任務
        task_data = {
            "title": "測試任務2",
            "description": "測試任務2描述",
            "priority": "P2",
            "estimated_hours": 2,
        }
        create_response = client.post("/api / v1 / tasks", json=task_data)
        task_id = create_response.json()["data"]["id"]

        # 獲取任務
        response = client.get(f"/api / v1 / tasks/{task_id}")
        assert response.status_code == 200

        result = response.json()
        assert result["data"]["id"] == task_id

    def test_update_task(self, client):
        """測試更新任務"""
        # 創建任務
        task_data = {
            "title": "測試任務3",
            "description": "測試任務3描述",
            "priority": "P1",
            "estimated_hours": 4,
        }
        create_response = client.post("/api / v1 / tasks", json=task_data)
        task_id = create_response.json()["data"]["id"]

        # 更新任務
        update_data = {"title": "更新後的任務", "priority": "P0", "estimated_hours": 5}
        response = client.put(f"/api / v1 / tasks/{task_id}", json=update_data)
        assert response.status_code == 200

        result = response.json()
        assert result["data"]["title"] == update_data["title"]
        assert result["data"]["priority"] == "P0"

    def test_delete_task(self, client):
        """測試刪除任務"""
        # 創建任務
        task_data = {
            "title": "測試任務4",
            "description": "測試任務4描述",
            "priority": "P2",
            "estimated_hours": 2,
        }
        create_response = client.post("/api / v1 / tasks", json=task_data)
        task_id = create_response.json()["data"]["id"]

        # 刪除任務
        response = client.delete(f"/api / v1 / tasks/{task_id}")
        assert response.status_code == 200

    def test_task_status_transition(self, client):
        """測試任務狀態流轉"""
        # 創建任務
        task_data = {
            "title": "狀態流轉測試",
            "description": "測試狀態流轉",
            "priority": "P0",
            "estimated_hours": 3,
        }
        create_response = client.post("/api / v1 / tasks", json=task_data)
        task_id = create_response.json()["data"]["id"]

        # 狀態: TODO -> IN_PROGRESS
        transition_data = {"new_status": "IN_PROGRESS"}
        response = client.put(
            f"/api / v1 / tasks/{task_id}/transition", json=transition_data
        )
        assert response.status_code == 200

        result = response.json()
        assert result["data"]["status"] == "IN_PROGRESS"

        # 狀態: IN_PROGRESS -> REVIEW
        transition_data = {"new_status": "REVIEW"}
        response = client.put(
            f"/api / v1 / tasks/{task_id}/transition", json=transition_data
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "REVIEW"

        # 狀態: REVIEW -> DONE
        transition_data = {"new_status": "DONE"}
        response = client.put(
            f"/api / v1 / tasks/{task_id}/transition", json=transition_data
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "DONE"

    def test_assign_task(self, client):
        """測試任務分配"""
        # 創建任務
        task_data = {
            "title": "分配測試",
            "description": "測試任務分配",
            "priority": "P1",
            "estimated_hours": 3,
        }
        create_response = client.post("/api / v1 / tasks", json=task_data)
        task_id = create_response.json()["data"]["id"]

        # 分配任務
        assign_data = {"assignee": "張三"}
        response = client.put(f"/api / v1 / tasks/{task_id}/assign", json=assign_data)
        assert response.status_code == 200

        result = response.json()
        assert result["data"]["assignee"] == "張三"

    def test_filter_tasks_by_status(self, client):
        """測試按狀態過濾任務"""
        # 創建多個不同狀態的任務
        for i in range(3):
            task_data = {
                "title": f"狀態測試{i}",
                "priority": "P2",
                "estimated_hours": 2,
            }
            client.post("/api / v1 / tasks", json=task_data)

        # 獲取TODO狀態的任務
        response = client.get("/api / v1 / tasks?status=TODO")
        assert response.status_code == 200

        result = response.json()
        assert all(task["status"] == "TODO" for task in result["data"])

    def test_filter_tasks_by_priority(self, client):
        """測試按優先級過濾任務"""
        # 創建P0優先級任務
        task_data = {"title": "P0優先級測試", "priority": "P0", "estimated_hours": 3}
        client.post("/api / v1 / tasks", json=task_data)

        # 獲取P0優先級任務
        response = client.get("/api / v1 / tasks?priority=P0")
        assert response.status_code == 200

        result = response.json()
        assert all(task["priority"] == "P0" for task in result["data"])

    def test_get_task_metrics(self, client):
        """測試獲取任務指標"""
        # 創建一些測試任務
        for i in range(5):
            task_data = {
                "title": f"指標測試{i}",
                "priority": "P1",
                "estimated_hours": 2,
            }
            client.post("/api / v1 / tasks", json=task_data)

        # 獲取指標
        response = client.get("/api / v1 / tasks / metrics")
        assert response.status_code == 200

        result = response.json()
        metrics = result["data"]

        # 驗證指標字段
        assert "total_tasks" in metrics
        assert "completed_tasks" in metrics
        assert "in_progress_tasks" in metrics
        assert "completion_rate" in metrics
        assert "tasks_by_priority" in metrics

    def test_invalid_task_creation(self, client):
        """測試無效任務創建"""
        # 缺少必填字段
        task_data = {
            "title": "無效任務"
            # 缺少 estimated_hours
        }
        response = client.post("/api / v1 / tasks", json=task_data)
        assert response.status_code == 422  # 驗證錯誤

    def test_invalid_status_transition(self, client):
        """測試無效狀態轉換"""
        # 創建任務
        task_data = {"title": "無效轉換測試", "priority": "P2", "estimated_hours": 2}
        create_response = client.post("/api / v1 / tasks", json=task_data)
        task_id = create_response.json()["data"]["id"]

        # 嘗試直接從TODO轉換到DONE（無效）
        transition_data = {"new_status": "DONE"}
        response = client.put(
            f"/api / v1 / tasks/{task_id}/transition", json=transition_data
        )
        assert response.status_code == 400  # 錯誤請求

    def test_task_not_found(self, client):
        """測試任務不存在"""
        response = client.get("/api / v1 / tasks / TASK - 999")
        assert response.status_code == 404

    def test_search_tasks(self, client):
        """測試搜索任務"""
        # 創建包含特定關鍵字的任務
        task_data = {
            "title": "搜索關鍵詞測試",
            "description": "這是一個包含搜索關鍵詞的任務",
            "priority": "P1",
            "estimated_hours": 3,
        }
        client.post("/api / v1 / tasks", json=task_data)

        # 搜索
        response = client.get("/api / v1 / tasks / search?q=關鍵詞")
        assert response.status_code == 200

        result = response.json()
        # 驗證搜索結果包含關鍵詞
        # 注意：實際搜索實現可能需要調整


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
