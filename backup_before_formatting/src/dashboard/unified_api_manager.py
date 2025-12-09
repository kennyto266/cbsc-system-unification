"""
統一API管理器
港股量化交易系統 - 核心模組

提供統一的API路由註冊、中間件配置、錯誤處理和監控功能。

主要功能:
- 統一路由註冊和管理
- 全局中間件配置
- 統一錯誤處理
- API版本管理
- 請求 / 響應日誌
- 性能監控
"""

import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """請求日誌中間件"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 記錄請求開始
        request_id = request.headers.get("X - Request - ID", "unknown")
        logger.info(
            f"請求開始: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
            },
        )

        # 處理請求
        response = await call_next(request)

        # 計算處理時間
        process_time = time.time() - start_time

        # 記錄請求結束
        logger.info(
            f"請求結束: {response.status_code} ({process_time:.3f}s)",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": process_time,
            },
        )

        # 添加響應頭
        response.headers["X - Process - Time"] = str(process_time)
        response.headers["X - Request - ID"] = request_id

        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """性能指標中間件"""

    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.metrics = {
            "request_count": 0,
            "error_count": 0,
            "total_response_time": 0.0,
            "endpoint_stats": {},
        }

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 更新指標
        self.metrics["request_count"] += 1
        endpoint = request.url.path
        method = request.method

        response = await call_next(request)
        process_time = time.time() - start_time

        # 更新總時間
        self.metrics["total_response_time"] += process_time

        # 更新端點統計
        if endpoint not in self.metrics["endpoint_stats"]:
            self.metrics["endpoint_stats"][endpoint] = {
                "count": 0,
                "total_time": 0.0,
                "errors": 0,
                "methods": {},
            }

        stats = self.metrics["endpoint_stats"][endpoint]
        stats["count"] += 1
        stats["total_time"] += process_time

        if method not in stats["methods"]:
            stats["methods"][method] = {"count": 0, "errors": 0}

        stats["methods"][method]["count"] += 1

        # 計算平均時間
        stats["avg_time"] = stats["total_time"] / stats["count"]

        # 統計錯誤
        if response.status_code >= 400:
            self.metrics["error_count"] += 1
            stats["errors"] += 1
            stats["methods"][method]["errors"] += 1

        return response

    def get_metrics(self) -> Dict[str, Any]:
        """獲取指標數據"""
        avg_response_time = (
            self.metrics["total_response_time"] / self.metrics["request_count"]
            if self.metrics["request_count"] > 0
            else 0.0
        )

        error_rate = (
            self.metrics["error_count"] / self.metrics["request_count"] * 100
            if self.metrics["request_count"] > 0
            else 0.0
        )

        return {
            "total_requests": self.metrics["request_count"],
            "total_errors": self.metrics["error_count"],
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "endpoint_stats": self.metrics["endpoint_stats"],
        }


class UnifiedAPIManager:
    """
    統一API管理器

    負責管理整個API系統的配置、路由、中間件和監控。
    """

    def __init__(self, app_name: str = "HK Quant API"):
        """
        初始化API管理器

        Args:
            app_name: 應用名稱
        """
        self.app_name = app_name
        self.app: Optional[FastAPI] = None
        self.routes: List[Dict[str, Any]] = []
        self.middleware_configs: Dict[str, Any] = {}
        self.metrics_middleware: Optional[MetricsMiddleware] = None

    def create_app(self, debug: bool = False) -> FastAPI:
        """
        創建FastAPI應用實例

        Args:
            debug: 是否啟用調試模式

        Returns:
            FastAPI應用實例
        """
        self.app = FastAPI(
            title=self.app_name,
            description="港股量化交易系統API",
            version="1.0.0",
            debug=debug,
            docs_url="/docs" if debug else None,
            redoc_url="/redoc" if debug else None,
        )

        # 添加默認中間件
        self._add_default_middleware()

        # 添加全局異常處理
        self._add_exception_handlers()

        # 添加健康檢查端點
        self._add_health_check()

        return self.app

    def _add_default_middleware(self):
        """添加默認中間件"""
        if not self.app:
            return

        # CORS中間件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 生產環境應該限制具體域名
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # GZip壓縮中間件
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)

        # 會話中間件 (如果需要)
        # self.app.add_middleware(
        #     SessionMiddleware,
        #     secret_key="your - secret - key"
        # )

        # 日誌中間件
        self.app.add_middleware(LoggingMiddleware)

        # 指標中間件
        self.metrics_middleware = MetricsMiddleware(self.app)
        self.app.add_middleware(self.metrics_middleware.__class__)

    def _add_exception_handlers(self):
        """添加全局異常處理器"""
        if not self.app:
            return

        from fastapi.responses import JSONResponse

        @self.app.exception_handler(404)
        async def not_found_handler(request: Request, exc):
            return JSONResponse(
                status_code=404,
                content={
                    "error": "Not Found",
                    "message": "請求的資源不存在",
                    "path": request.url.path,
                },
            )

        @self.app.exception_handler(500)
        async def internal_error_handler(request: Request, exc):
            logger.error(f"內部服務器錯誤: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"error": "Internal Server Error", "message": "服務器內部錯誤"},
            )

        @self.app.exception_handler(ValueError)
        async def value_error_handler(request: Request, exc):
            return JSONResponse(
                status_code=400, content={"error": "Bad Request", "message": str(exc)}
            )

    def _add_health_check(self):
        """添加健康檢查端點"""

        @self.app.get("/health")
        async def health_check():
            """健康檢查端點"""
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "service": self.app_name,
            }

        @self.app.get("/metrics")
        async def get_metrics():
            """獲取性能指標"""
            if self.metrics_middleware:
                return self.metrics_middleware.get_metrics()
            return {"error": "Metrics not available"}

    def register_route(
        self,
        path: str,
        handler: Callable,
        methods: List[str] = None,
        response_model: Any = None,
        tags: List[str] = None,
        summary: str = None,
        description: str = None,
    ):
        """
        註冊API路由

        Args:
            path: 路由路徑
            handler: 處理函數
            methods: HTTP方法列表
            response_model: 響應模型
            tags: 標籤列表
            summary: 摘要
            description: 描述
        """
        if not self.app:
            raise RuntimeError("應用尚未創建，請先調用create_app()")

        route_info = {
            "path": path,
            "handler": handler,
            "methods": methods or ["GET"],
            "response_model": response_model,
            "tags": tags or [],
            "summary": summary or "",
            "description": description or "",
        }

        self.routes.append(route_info)

        # 動態添加路由到應用
        for method in route_info["methods"]:
            getattr(self.app, method.lower())(
                path,
                response_model=response_model,
                tags=tags,
                summary=summary,
                description=description,
            )(handler)

    def register_router(self, router, prefix: str = ""):
        """
        註冊API路由器

        Args:
            router: FastAPI路由器實例
            prefix: 路徑前綴
        """
        if not self.app:
            raise RuntimeError("應用尚未創建，請先調用create_app()")

        # 如果路由器有前綴，使用它；否則使用提供的前綴
        final_prefix = (
            router.prefix if hasattr(router, "prefix") and router.prefix else prefix
        )

        self.app.include_router(router, prefix=final_prefix)

    def configure_middleware(self, middleware_type: str, **kwargs):
        """
        配置中間件

        Args:
            middleware_type: 中間件類型
            **kwargs: 中間件參數
        """
        self.middleware_configs[middleware_type] = kwargs

        if middleware_type == "cors" and self.app:
            self.app.add_middleware(CORSMiddleware, **kwargs)

    def get_route_stats(self) -> Dict[str, Any]:
        """
        獲取路由統計信息

        Returns:
            路由統計信息
        """
        if not self.app:
            return {}

        stats = {
            "total_routes": len(self.app.routes),
            "registered_routes": len(self.routes),
            "route_list": [],
        }

        for route in self.app.routes:
            if isinstance(route, APIRoute):
                stats["route_list"].append(
                    {
                        "path": route.path,
                        "methods": route.methods,
                        "summary": route.summary or "",
                        "tags": route.tags or [],
                    }
                )

        return stats

    def configure_api_versioning(self, version: str = "v1"):
        """
        配置API版本管理

        Args:
            version: API版本號
        """
        self.app.version = version

        # 添加版本信息到文檔
        if hasattr(self.app, "openapi_tags"):
            self.app.openapi_tags = [
                {"name": version, "description": f"API版本 {version}"}
            ]


# 便利函數
def create_unified_api(
    app_name: str = "HK Quant API", debug: bool = False, cors_origins: List[str] = None
) -> UnifiedAPIManager:
    """
    創建統一API管理器的便利函數

    Args:
        app_name: 應用名稱
        debug: 是否啟用調試模式
        cors_origins: CORS允許的源列表

    Returns:
        UnifiedAPIManager實例
    """
    manager = UnifiedAPIManager(app_name)
    app = manager.create_app(debug=debug)

    # 配置CORS
    if cors_origins:
        manager.configure_middleware(
            "cors",
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return manager


if __name__ == "__main__":
    # 示例用法
    from fastapi import FastAPI
    from pydantic import BaseModel

    class Item(BaseModel):
        name: str
        price: float

    # 創建API管理器
    manager = create_unified_api(app_name="測試API", debug=True)

    # 定義處理函數
    async def get_items():
        return {"items": [{"id": 1, "name": "測試"}]}

    async def create_item(item: Item):
        return {"id": 1, **item.dict()}

    # 註冊路由
    manager.register_route(
        "/items",
        get_items,
        methods=["GET"],
        summary="獲取所有項目",
        description="返回項目列表",
    )

    manager.register_route(
        "/items",
        create_item,
        methods=["POST"],
        response_model=dict,
        summary="創建新項目",
        description="創建一個新項目",
    )

    # 獲取應用實例
    app = manager.app

    # 啟動服務
    import uvicorn

    print("啟動API服務器...")
    print("文檔地址: http://localhost:8000 / docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
