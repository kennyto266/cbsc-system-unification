"""
測試 API 基礎管理器
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from shared.api.base_manager import (
    APIResponse,
    BaseAPIManager,
    DateRangeParams,
    ErrorResponse,
    PaginationParams,
    add_health_check,
    add_root_route,
    create_error_response,
    create_success_response,
)


class TestBaseAPIManager:
    """基礎 API 管理器測試"""

    def test_manager_initialization(self):
        """測試管理器初始化"""
        manager = BaseAPIManager(
            title="測試 API",
            description="測試描述",
            version="1.0.0",
        )
        assert manager.app.title == "測試 API"
        assert manager.app.description == "測試描述"
        assert manager.app.version == "1.0.0"
        assert len(manager.routes) == 0

    def test_add_route(self):
        """測試添加路由"""
        manager = BaseAPIManager()

        def test_handler():
            return {"message": "success"}

        manager.add_route("/test", test_handler, methods=["GET"])
        assert len(manager.routes) == 1
        assert manager.routes[0]["path"] == "/test"
        assert manager.routes[0]["methods"] == ["GET"]

    def test_get_route_decorator(self):
        """測試 GET 路由裝飾器"""
        manager = BaseAPIManager()

        @manager.get("/api / data")
        def get_data():
            return {"data": "test"}

        assert len(manager.routes) == 1
        assert manager.routes[0]["path"] == "/api / data"
        assert manager.routes[0]["methods"] == ["GET"]

    def test_post_route_decorator(self):
        """測試 POST 路由裝飾器"""
        manager = BaseAPIManager()

        @manager.post("/api / submit")
        def submit_data():
            return {"status": "submitted"}

        assert len(manager.routes) == 1
        assert manager.routes[0]["path"] == "/api / submit"
        assert manager.routes[0]["methods"] == ["POST"]

    def test_put_route_decorator(self):
        """測試 PUT 路由裝飾器"""
        manager = BaseAPIManager()

        @manager.put("/api / update")
        def update_data():
            return {"status": "updated"}

        assert len(manager.routes) == 1
        assert manager.routes[0]["path"] == "/api / update"
        assert manager.routes[0]["methods"] == ["PUT"]

    def test_delete_route_decorator(self):
        """測試 DELETE 路由裝飾器"""
        manager = BaseAPIManager()

        @manager.delete("/api / delete")
        def delete_data():
            return {"status": "deleted"}

        assert len(manager.routes) == 1
        assert manager.routes[0]["path"] == "/api / delete"
        assert manager.routes[0]["methods"] == ["DELETE"]

    def test_get_app(self):
        """測試獲取 FastAPI 應用"""
        manager = BaseAPIManager()
        app = manager.get_app()
        assert isinstance(app, FastAPI)
        assert app is manager.app

    def test_get_routes(self):
        """測試獲取路由列表"""
        manager = BaseAPIManager()

        @manager.get("/test1")
        def test1():
            pass

        @manager.post("/test2")
        def test2():
            pass

        routes = manager.get_routes()
        assert len(routes) == 2
        assert routes[0]["path"] == "/test1"
        assert routes[1]["path"] == "/test2"

    def test_multiple_methods(self):
        """測試多方法路由"""
        manager = BaseAPIManager()

        def handler():
            return {"status": "ok"}

        manager.add_route("/api / item", handler, methods=["GET", "POST", "PUT"])
        assert len(manager.routes) == 1
        assert set(manager.routes[0]["methods"]) == {"GET", "POST", "PUT"}


class TestAPIResponse:
    """API 響應模型測試"""

    def test_success_response_creation(self):
        """測試創建成功響應"""
        response = APIResponse(
            success=True,
            message="操作成功",
            data={"key": "value"},
        )
        assert response.success
        assert response.message == "操作成功"
        assert response.data == {"key": "value"}
        assert response.request_id is not None

    def test_error_response_creation(self):
        """測試創建錯誤響應"""
        response = ErrorResponse(
            message="操作失敗",
            error_code="OPERATION_FAILED",
            details={"field": "error details"},
        )
        assert not response.success
        assert response.message == "操作失敗"
        assert response.error_code == "OPERATION_FAILED"
        assert response.details == {"field": "error details"}


class TestConvenienceFunctions:
    """便捷函數測試"""

    def test_create_success_response(self):
        """測試創建成功響應"""
        response = create_success_response(
            data={"result": "success"},
            message="操作完成",
        )
        assert response.success
        assert response.message == "操作完成"
        assert response.data == {"result": "success"}

    def test_create_error_response(self):
        """測試創建錯誤響應"""
        from fastapi import Response as FastAPIResponse

        response = create_error_response(
            message="數據無效",
            error_code="INVALID_DATA",
            status_code=400,
        )
        assert isinstance(response, FastAPIResponse)
        assert response.status_code == 400


class TestHealthCheck:
    """健康檢查測試"""

    def test_add_health_check(self):
        """測試添加健康檢查端點"""
        manager = BaseAPIManager()
        add_health_check(manager)
        add_root_route(manager)

        assert len(manager.routes) == 2

        # 測試端點存在
        client = TestClient(manager.app)
        response = client.get("/api / health")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["data"]["status"] == "healthy"

    def test_root_route(self):
        """測試根路徑"""
        manager = BaseAPIManager()
        add_root_route(manager)

        client = TestClient(manager.app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data


class TestParameterModels:
    """參數模型測試"""

    def test_pagination_params_default(self):
        """測試分頁參數默認值"""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_pagination_params_custom(self):
        """測試自定義分頁參數"""
        params = PaginationParams(page=2, page_size=50)
        assert params.page == 2
        assert params.page_size == 50

    def test_pagination_params_validation(self):
        """測試分頁參數驗證"""
        # 頁碼必須 >= 1
        with pytest.raises(Exception):
            PaginationParams(page=0)

        # 每頁大小必須在 1 - 100 之間
        with pytest.raises(Exception):
            PaginationParams(page_size=101)

    def test_date_range_params(self):
        """測試日期範圍參數"""
        params = DateRangeParams(
            start_date="2023 - 01 - 01",
            end_date="2023 - 12 - 31",
        )
        assert params.start_date == "2023 - 01 - 01"
        assert params.end_date == "2023 - 12 - 31"

    def test_date_range_params_optional(self):
        """測試日期範圍參數可選"""
        params = DateRangeParams()
        assert params.start_date is None
        assert params.end_date is None


class TestErrorHandling:
    """錯誤處理測試"""

    def test_http_exception(self):
        """測試 HTTP 異常處理"""
        manager = BaseAPIManager()

        @manager.get("/error")
        def error_endpoint():
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="資源未找到")

        client = TestClient(manager.app)
        response = client.get("/error")
        assert response.status_code == 404
        assert response.json()["success"] is False
        assert "資源未找到" in response.json()["message"]

    def test_general_exception(self):
        """測試一般異常處理"""
        manager = BaseAPIManager()

        @manager.get("/exception")
        def exception_endpoint():
            raise ValueError("測試異常")

        client = TestClient(manager.app)
        response = client.get("/exception")
        assert response.status_code == 500
        assert response.json()["success"] is False
        assert response.json()["error_code"] == "INTERNAL_ERROR"


class TestRouteRegistration:
    """路由註冊測試"""

    def test_route_count_increase(self):
        """測試路由數量增加"""
        manager = BaseAPIManager()
        initial_count = len(manager.routes)

        @manager.get("/test1")
        def test1():
            pass

        assert len(manager.routes) == initial_count + 1

        @manager.post("/test2")
        def test2():
            pass

        assert len(manager.routes) == initial_count + 2

    def test_route_preservation(self):
        """測試路由保存"""
        manager = BaseAPIManager()

        @manager.get("/preserved")
        def preserved():
            return {"preserved": True}

        routes = manager.get_routes()
        assert any(r["path"] == "/preserved" for r in routes)


class TestMiddleware:
    """中間件測試"""

    def test_middleware_configuration(self):
        """測試中間件配置"""
        manager = BaseAPIManager()
        # 中間件在初始化時已經配置
        # 這裡主要驗證管理器能正常創建
        assert manager.app is not None

    def test_cors_middleware(self):
        """測試 CORS 中間件"""
        manager = BaseAPIManager()
        client = TestClient(manager.app)
        response = client.options("/", headers={"Origin": "http://localhost:3000"})
        # CORS 頭應該存在
        assert "access - control - allow - origin" in str(response.headers)
