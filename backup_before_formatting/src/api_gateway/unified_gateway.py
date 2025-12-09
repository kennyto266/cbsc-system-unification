#!/usr / bin / env python3
"""
統一API網關
港股量化交易系統 - 企業級API標準化實現

提供統一的API入口、標準化的請求 / 響應格式、
認證授權、限流、監控和API治理功能。

主要功能:
- 統一API入口點 (Port 7777)
- 標準化請求 / 響應格式
- JWT認證和RBAC授權
- API限流和安全防護
- 服務發現和路由
- 統一錯誤處理
- API監控和分析
"""

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import aiofiles
import jwt
import redis
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

logger = logging.getLogger(__name__)

# 配置常量
API_VERSION = "v1"
GATEWAY_VERSION = "1.0.0"
DEFAULT_TIMEOUT = 30
RATE_LIMIT_REQUESTS = 1000
RATE_LIMIT_WINDOW = 60  # seconds


class APIStandardResponse(BaseModel):
    """標準API響應格式"""

    success: bool = Field(..., description="請求是否成功")
    data: Optional[Any] = Field(None, description="響應數據")
    error: Optional[Dict[str, Any]] = Field(None, description="錯誤信息")
    meta: Optional[Dict[str, Any]] = Field(None, description="元數據")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="響應時間戳"
    )


class APIError(BaseModel):
    """標準錯誤格式"""

    code: str = Field(..., description="錯誤代碼")
    message: str = Field(..., description="錯誤消息")
    details: Optional[Dict[str, Any]] = Field(None, description="錯誤詳情")
    request_id: Optional[str] = Field(None, description="請求ID")


class APIMetadata(BaseModel):
    """API元數據"""

    version: str = Field(..., description="API版本")
    request_id: str = Field(..., description="請求ID")
    processing_time: float = Field(..., description="處理時間(秒)")
    endpoint: str = Field(..., description="端點路徑")
    method: str = Field(..., description="HTTP方法")


class User(BaseModel):
    """用戶模型"""

    user_id: str
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    is_active: bool = True


class ServiceRegistry:
    """服務註冊中心"""

    def __init__(self):
        self.services: Dict[str, Dict[str, Any]] = {}
        self.load_services_config()

    def load_services_config(self):
        """加載服務配置"""
        services_config = {
            "dashboard": {
                "host": "localhost",
                "port": 8001,
                "prefix": "/api / v2",
                "health_check": "/health",
                "timeout": 30,
                "retries": 3,
            },
            "analysis": {
                "host": "localhost",
                "port": 8002,
                "prefix": "/api / v1",
                "health_check": "/health",
                "timeout": 60,
                "retries": 2,
            },
            "trading": {
                "host": "localhost",
                "port": 8003,
                "prefix": "/api / v1",
                "health_check": "/health",
                "timeout": 30,
                "retries": 3,
            },
            "ml": {
                "host": "localhost",
                "port": 8004,
                "prefix": "/api / v1",
                "health_check": "/health",
                "timeout": 120,
                "retries": 1,
            },
            "portfolio": {
                "host": "localhost",
                "port": 8005,
                "prefix": "/api / v1",
                "health_check": "/health",
                "timeout": 30,
                "retries": 3,
            },
            "risk": {
                "host": "localhost",
                "port": 8006,
                "prefix": "/api / v1",
                "health_check": "/health",
                "timeout": 30,
                "retries": 3,
            },
        }

        for service_name, config in services_config.items():
            self.register_service(service_name, config)

    def register_service(self, name: str, config: Dict[str, Any]):
        """註冊服務"""
        self.services[name] = config

    def get_service(self, name: str) -> Optional[Dict[str, Any]]:
        """獲取服務配置"""
        return self.services.get(name)

    def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有服務"""
        return self.services.copy()


class RateLimiter:
    """API限流器"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def is_allowed(
        self,
        key: str,
        limit: int = RATE_LIMIT_REQUESTS,
        window: int = RATE_LIMIT_WINDOW,
    ) -> tuple[bool, int]:
        """
        檢查是否允許請求

        Args:
            key: 限流鍵 (用戶ID、IP等)
            limit: 請求限制數
            window: 時間窗口(秒)

        Returns:
            (是否允許, 剩餘請求數)
        """
        try:
            current_time = int(time.time())
            window_start = current_time - window

            # 清理過期記錄
            await self.redis.zremrangebyscore(key, 0, window_start)

            # 獲取當前計數
            current_count = await self.redis.zcard(key)

            if current_count >= limit:
                return False, 0

            # 記錄新請求
            await self.redis.zadd(key, {str(current_time): current_time})
            await self.redis.expire(key, window)

            remaining = limit - current_count - 1
            return True, remaining

        except Exception as e:
            logger.error(f"限流檢查失敗: {e}")
            # 限流失敗時默認允許
            return True, limit


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """JWT認證中間件"""

    def __init__(self, app: FastAPI, secret_key: str, excluded_paths: List[str] = None):
        super().__init__(app)
        self.secret_key = secret_key
        self.excluded_paths = excluded_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/metrics",
        ]

    async def dispatch(self, request: Request, call_next: Callable):
        # 檢查是否為排除路徑
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # 獲取Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少Authorization header",
                headers={"WWW - Authenticate": "Bearer"},
            )

        try:
            scheme, credentials = authorization.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")

            # 驗證JWT token
            payload = jwt.decode(credentials, self.secret_key, algorithms=["HS256"])

            # 添加用戶信息到請求狀態
            request.state.user = User(**payload)

        except (ValueError, InvalidTokenError) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW - Authenticate": "Bearer"},
            )

        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """請求日誌中間件"""

    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()

        # 生成請求ID
        request_id = request.headers.get(
            "X - Request - ID", f"req_{int(time.time() * 1000)}"
        )

        # 記錄請求開始
        logger.info(
            f"API請求開始: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("User - Agent"),
            },
        )

        # 處理請求
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # 記錄請求完成
            logger.info(
                f"API請求完成: {response.status_code} ({process_time:.3f}s)",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time": process_time,
                },
            )

            # 添加響應頭
            response.headers["X - Request - ID"] = request_id
            response.headers["X - Process - Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"API請求錯誤: {str(e)} ({process_time:.3f}s)",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "process_time": process_time,
                },
            )
            raise


class APIGateway:
    """統一API網關"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.service_registry = ServiceRegistry()
        self.app: Optional[FastAPI] = None
        self.redis_client: Optional[redis.Redis] = None
        self.rate_limiter: Optional[RateLimiter] = None

        # 負載統計
        self.stats = {
            "total_requests": 0,
            "error_count": 0,
            "services_status": {},
            "last_health_check": None,
        }

    def initialize_redis(self, redis_url: str = "redis://localhost:6379 / 0"):
        """初始化Redis連接"""
        try:
            self.redis_client = redis.from_url(redis_url)
            self.rate_limiter = RateLimiter(self.redis_client)
            logger.info(f"Redis連接成功: {redis_url}")
        except Exception as e:
            logger.error(f"Redis連接失敗: {e}")
            # 繼續運行，但限流功能不可用

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """應用生命週期管理"""
        # 啟動時初始化
        logger.info("API網關啟動中...")
        await self.health_check_all_services()

        yield

        # 關閉時清理
        logger.info("API網關關閉中...")
        if self.redis_client:
            await self.redis_client.close()

    def create_app(self) -> FastAPI:
        """創建FastAPI應用"""
        self.app = FastAPI(
            title="港股量化交易系統 - 統一API網關",
            description="企業級量化交易平台的統一API入口點",
            version=GATEWAY_VERSION,
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
            lifespan=self.lifespan,
        )

        # 添加中間件
        self._setup_middleware()

        # 添加路由
        self._setup_routes()

        # 添加異常處理
        self._setup_exception_handlers()

        return self.app

    def _setup_middleware(self):
        """設置中間件"""
        # 信任主機中間件
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "*.codex - quant.com"],
        )

        # CORS中間件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.get("cors_origins", ["*"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # GZip壓縮
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)

        # 請求日誌
        self.app.add_middleware(RequestLoggingMiddleware)

        # JWT認證 (如果配置了密鑰)
        jwt_secret = self.config.get("jwt_secret")
        if jwt_secret:
            excluded_paths = [
                "/health",
                "/docs",
                "/redoc",
                "/openapi.json",
                "/auth / login",
            ]
            self.app.add_middleware(
                AuthenticationMiddleware,
                secret_key=jwt_secret,
                excluded_paths=excluded_paths,
            )

    def _setup_routes(self):
        """設置路由"""

        @self.app.get("/health", tags=["系統"])
        async def health_check():
            """健康檢查"""
            return APIStandardResponse(
                success=True,
                data={
                    "status": "healthy",
                    "version": GATEWAY_VERSION,
                    "services": await self.get_services_status(),
                    "uptime": time.time() - getattr(self, "_start_time", time.time()),
                },
                meta=APIMetadata(
                    version=API_VERSION,
                    request_id="health_check",
                    processing_time=0.0,
                    endpoint="/health",
                    method="GET",
                ).dict(),
            )

        @self.app.get("/metrics", tags=["系統"])
        async def get_metrics():
            """獲取系統指標"""
            return APIStandardResponse(
                success=True,
                data={
                    "gateway_stats": self.stats,
                    "services_status": await self.get_services_status(),
                    "redis_connected": self.redis_client is not None,
                },
            )

        @self.app.post("/auth / login", tags=["認證"])
        async def login(username: str, password: str):
            """用戶登錄"""
            # 這裡應該驗證用戶憑證
            # 為了示例，使用簡單的驗證邏輯

            if username == "admin" and password == "admin123":
                # 生成JWT token
                token = jwt.encode(
                    {
                        "user_id": "admin",
                        "username": "admin",
                        "email": "admin@codex - quant.com",
                        "roles": ["admin"],
                        "permissions": ["*"],
                        "exp": datetime.utcnow() + timedelta(hours=24),
                    },
                    self.config.get("jwt_secret", "secret"),
                    algorithm="HS256",
                )

                return APIStandardResponse(
                    success=True, data={"token": token, "expires_in": 86400}
                )
            else:
                raise HTTPException(status_code=401, detail="無效的憑證")

        # 代理路由 - 將請求轉發到對應的微服務
        for (
            service_name,
            service_config,
        ) in self.service_registry.get_all_services().items():
            self._setup_proxy_routes(service_name, service_config)

    def _setup_proxy_routes(self, service_name: str, service_config: Dict[str, Any]):
        """設置代理路由"""
        base_path = f"/{API_VERSION}/{service_name}"
        service_prefix = service_config.get("prefix", "")

        @self.app.api_router(
            f"{base_path}{{path:path}}", methods=["GET", "POST", "PUT", "DELETE"]
        )
        async def proxy_request(request: Request, path: str):
            """代理請求到微服務"""
            return await self._proxy_to_service(
                service_name, service_prefix + path, request
            )

    async def _proxy_to_service(self, service_name: str, path: str, request: Request):
        """代理請求到指定服務"""
        service_config = self.service_registry.get_service(service_name)
        if not service_config:
            raise HTTPException(status_code=404, detail=f"服務 {service_name} 未找到")

        # 檢查服務健康狀態
        if not await self.is_service_healthy(service_name):
            raise HTTPException(status_code=503, detail=f"服務 {service_name} 不可用")

        # 限流檢查
        user = getattr(request.state, "user", None)
        rate_limit_key = f"rate_limit:{user.user_id if user else request.client.host}"

        if self.rate_limiter:
            allowed, remaining = await self.rate_limiter.is_allowed(rate_limit_key)
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail="請求過於頻繁，請稍後再試",
                    headers={"X - RateLimit - Remaining": str(remaining)},
                )

        # TODO: 實現實際的HTTP代理功能
        # 這裡返回示例響應
        return APIStandardResponse(
            success=True,
            data={
                "message": f"請求已代理到 {service_name} 服務",
                "path": path,
                "method": request.method,
                "service_config": service_config,
            },
        )

    def _setup_exception_handlers(self):
        """設置異常處理"""

        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content=APIStandardResponse(
                    success=False,
                    error=APIError(
                        code=f"HTTP_{exc.status_code}",
                        message=exc.detail,
                        request_id=request.headers.get("X - Request - ID"),
                    ).dict(),
                ).dict(),
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            logger.error(f"未處理的異常: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content=APIStandardResponse(
                    success=False,
                    error=APIError(
                        code="INTERNAL_ERROR",
                        message="服務器內部錯誤",
                        request_id=request.headers.get("X - Request - ID"),
                    ).dict(),
                ).dict(),
            )

    async def health_check_all_services(self):
        """檢查所有服務健康狀態"""
        services = self.service_registry.get_all_services()
        status_tasks = []

        for service_name in services:
            status_tasks.append(self.check_service_health(service_name))

        if status_tasks:
            await asyncio.gather(*status_tasks, return_exceptions=True)

        self.stats["last_health_check"] = datetime.utcnow()

    async def check_service_health(self, service_name: str) -> bool:
        """檢查單個服務健康狀態"""
        service_config = self.service_registry.get_service(service_name)
        if not service_config:
            return False

        try:
            # TODO: 實現實際的健康檢查HTTP請求
            # 這裡模擬健康檢查
            is_healthy = True

            self.stats["services_status"][service_name] = {
                "healthy": is_healthy,
                "last_check": datetime.utcnow(),
                "config": service_config,
            }

            return is_healthy

        except Exception as e:
            logger.error(f"檢查服務 {service_name} 健康狀態失敗: {e}")
            self.stats["services_status"][service_name] = {
                "healthy": False,
                "last_check": datetime.utcnow(),
                "error": str(e),
            }
            return False

    async def get_services_status(self) -> Dict[str, Any]:
        """獲取所有服務狀態"""
        return {
            "total_services": len(self.service_registry.get_all_services()),
            "healthy_services": sum(
                1
                for status in self.stats["services_status"].values()
                if status.get("healthy", False)
            ),
            "services": self.stats["services_status"],
            "last_check": self.stats["last_health_check"],
        }

    def run(self, host: str = "0.0.0.0", port: int = 7777, **kwargs):
        """運行API網關"""
        app = self.create_app()
        self._start_time = time.time()

        print(
            """
╔══════════════════════════════════════════════════════════════╗
║         港股量化交易系統 - 統一API網關                          ║
╠══════════════════════════════════════════════════════════════╣
║ 版本: {GATEWAY_VERSION:>53} ║
║ 端口: {port:>53} ║
║ 文檔: http://{host}:{port}/docs{"":44} ║
║ 狀態: http://{host}:{port}/health{"":42} ║
╚══════════════════════════════════════════════════════════════╝
        """
        )

        uvicorn.run(app, host=host, port=port, log_level="info", **kwargs)


def create_gateway(config_path: Optional[str] = None) -> APIGateway:
    """創建API網關實例"""
    config = {}

    if config_path and Path(config_path).exists():
        with open(config_path, "r", encoding="utf - 8") as f:
            config = json.load(f)

    # 從環境變量加載配置
    config.update(
        {
            "cors_origins": config.get("cors_origins", ["*"]),
            "jwt_secret": config.get("jwt_secret")
            or os.getenv("JWT_SECRET", "your - secret - key"),
            "redis_url": config.get("redis_url")
            or os.getenv("REDIS_URL", "redis://localhost:6379 / 0"),
        }
    )

    gateway = APIGateway(config)
    gateway.initialize_redis(config["redis_url"])

    return gateway


if __name__ == "__main__":
    import os

    # 從命令行參數或環境變量獲取配置
    config_file = os.getenv("GATEWAY_CONFIG", "config / gateway.json")
    host = os.getenv("GATEWAY_HOST", "0.0.0.0")
    port = int(os.getenv("GATEWAY_PORT", "7777"))

    # 創建並運行網關
    gateway = create_gateway(config_file)
    gateway.run(host=host, port=port)
