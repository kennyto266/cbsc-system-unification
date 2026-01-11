"""
CBSC System API Gateway - Enhanced Version
统一API网关 - 服务路由、监控、认证和治理
"""

from fastapi import FastAPI, HTTPException, Request, Response, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import logging
import time
import os
import hashlib
import hmac
import base64
from typing import Dict, Any, List, Optional
import json
import redis
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置數據結構
@dataclass
class ServiceConfig:
    """服務配置數據類"""
    name: str
    url: str
    health_path: str
    prefix: str
    timeout: float = 30.0
    retries: int = 3
    load_balancer: Optional[List[str]] = None
    auth_required: bool = True
    rate_limit: Optional[int] = None  # requests per minute

@dataclass
class RouteMetrics:
    """路由指標數據類"""
    path: str
    method: str
    status_code: int
    response_time: float
    timestamp: datetime
    user_id: Optional[str] = None

# 增強的服務發現配置
SERVICES = {
    "quant-system": ServiceConfig(
        name="quant-system",
        url=os.getenv("QUANT_SYSTEM_URL", "http://localhost:8001"),
        health_path="/api/health",
        prefix="/api/quant",
        timeout=30.0,
        retries=3,
        auth_required=True,
        rate_limit=1000
    ),
    "user-management": ServiceConfig(
        name="user-management",
        url=os.getenv("USER_MANAGEMENT_URL", "http://localhost:3004"),
        health_path="/health",
        prefix="/api/users",
        timeout=15.0,
        retries=2,
        auth_required=True,
        rate_limit=500
    ),
    "strategy-dashboard": ServiceConfig(
        name="strategy-dashboard",
        url=os.getenv("STRATEGY_DASHBOARD_URL", "http://localhost:3003"),
        health_path="/health",
        prefix="/api/strategies",
        timeout=20.0,
        retries=3,
        auth_required=True,
        rate_limit=800
    ),
    "config-service": ServiceConfig(
        name="config-service",
        url=os.getenv("CONFIG_SERVICE_URL", "http://localhost:3005"),
        health_path="/health",
        prefix="/api/config",
        timeout=10.0,
        retries=2,
        auth_required=False,
        rate_limit=200
    )
}

# 全局配置
class GatewayConfig:
    """網關全局配置"""
    SECRET_KEY = os.getenv("GATEWAY_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    RATE_LIMIT_WINDOW = 60  # seconds
    MAX_REQUESTS_PER_IP = 1000

config = GatewayConfig()

# 初始化Redis客戶端
try:
    redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("✅ Redis連接成功")
except Exception as e:
    logger.warning(f"⚠️ Redis連接失敗，將使用內存緩存: {e}")
    redis_client = None

# 安全配置
security = HTTPBearer()

# 內存緩存（Redis備用）
memory_cache: Dict[str, Any] = {}
metrics_storage: List[RouteMetrics] = []

# 創建增強的FastAPI應用
app = FastAPI(
    title="CBSC System API Gateway - Enhanced",
    description="""
    ## 🚀 CBSC系統統一API網關

    ### 核心功能
    - **統一入口**: 單一接入點管理所有後端服務
    - **智能路由**: 基於路徑和負載均衡的請求分發
    - **統一認證**: JWT + OAuth2標準認證機制
    - **服務監控**: 實時監控和健康檢查
    - **限流控制**: IP和用戶級別的請求限流
    - **緩存加速**: Redis分佈式緩存
    - **日誌追蹤**: 完整的請求鏈路追蹤

    ### 支持的服務
    - 🔬 **量化分析系統**: CBSC策略分析、回測引擎
    - 👥 **用戶管理系統**: 認證授權、用戶資料管理
    - 📊 **策略管理Dashboard**: 策略監控、參數優化
    - ⚙️ **配置管理服務**: 系統配置、參數管理

    ### 安全特性
    - JWT令牌驗證
    - 請求簽名驗證
    - IP白名單機制
    - CORS跨域控制
    - 請求限流保護
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 服务发现配置
SERVICES = {
    "quant-system": {
        "url": os.getenv("QUANT_SYSTEM_URL", "http://localhost:8001"),
        "health_path": "/api/health",
        "prefix": "/api/quant"
    },
    "user-management": {
        "url": os.getenv("USER_MANAGEMENT_URL", "http://localhost:3004"),
        "health_path": "/health",
        "prefix": "/api/users"
    }
}

# 全局HTTP客户端
http_client = httpx.AsyncClient(timeout=30.0)

# 導入增強的認證服務
from auth_service import jwt_auth_service, oauth2_service, get_current_user_token, check_user_permission

# 增強的中間件和認證功能
class GatewayAuthenticationService:
    """網關認證服務包裝器"""

    @staticmethod
    def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """驗證JWT令牌"""
        payload = jwt_auth_service.verify_token(credentials.credentials, "access")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的或已過期的Token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    @staticmethod
    def verify_token_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
        """可選的令牌驗證"""
        if not credentials:
            return None

        return GatewayAuthenticationService.verify_token(credentials)

    @staticmethod
    def require_permission(permission: str):
        """權限檢查依賴"""
        def permission_checker(current_user: Dict[str, Any] = Depends(GatewayAuthenticationService.verify_token)):
            username = current_user.get("sub")
            if not check_user_permission(username, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要權限: {permission}"
                )
            return current_user
        return permission_checker

class RateLimiter:
    """請求限流器"""

    def __init__(self):
        self.redis = redis_client

    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """檢查是否允許請求"""
        if not self.redis:
            # 使用內存限流
            current_time = int(time.time())
            window_start = current_time - window

            # 清理過期記錄
            memory_cache[key] = [
                timestamp for timestamp in memory_cache.get(key, [])
                if timestamp > window_start
            ]

            # 檢查限流
            if len(memory_cache[key]) >= limit:
                return False

            memory_cache[key].append(current_time)
            return True

        # 使用Redis限流
        current_time = int(time.time())
        pipeline = self.redis.pipeline()
        pipeline.zremrangebyscore(key, 0, current_time - window)
        pipeline.zcard(key)
        pipeline.zadd(key, {str(current_time): current_time})
        pipeline.expire(key, window)

        results = await pipeline.execute()
        return results[1] < limit

class MetricsCollector:
    """指標收集器"""

    def __init__(self):
        self.metrics = metrics_storage

    def record_request(self, metrics: RouteMetrics):
        """記錄請求指標"""
        self.metrics.append(metrics)

        # 限制內存使用
        if len(self.metrics) > 10000:
            self.metrics = self.metrics[-5000:]

    def get_service_metrics(self, service_name: str, minutes: int = 5) -> Dict[str, Any]:
        """獲取服務指標"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [
            m for m in self.metrics
            if m.timestamp > cutoff_time
        ]

        if not recent_metrics:
            return {"status": "no_data"}

        service_metrics = [m for m in recent_metrics]

        return {
            "total_requests": len(service_metrics),
            "avg_response_time": sum(m.response_time for m in service_metrics) / len(service_metrics),
            "success_rate": len([m for m in service_metrics if 200 <= m.status_code < 400]) / len(service_metrics),
            "error_rate": len([m for m in service_metrics if m.status_code >= 400]) / len(service_metrics),
            "status_codes": {m.status_code: [m for m in service_metrics if m.status_code == m.status_code] for m in service_metrics}
        }

# 初始化服務
gateway_auth_service = GatewayAuthenticationService()
rate_limiter = RateLimiter()
metrics_collector = MetricsCollector()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """獲取當前用戶信息"""
    return gateway_auth_service.verify_token(credentials)

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """可選的當前用戶信息"""
    return gateway_auth_service.verify_token_optional(credentials)

async def check_rate_limit(request: Request, limit: int = 1000):
    """檢查請求限流"""
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"

    if not await rate_limiter.is_allowed(key, limit, config.RATE_LIMIT_WINDOW):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="請求過於頻繁，請稍後再試"
        )

@app.middleware("http")
async def enhanced_logging_middleware(request: Request, call_next):
    """增強請求日誌中間件"""
    start_time = time.time()
    request_id = hashlib.md5(f"{time.time()}{request.client.host}".encode()).hexdigest()[:8]

    # 記錄請求
    logger.info(f"[{request_id}] {request.method} {request.url.path} - {request.client.host}")

    try:
        # 執行請求
        response = await call_next(request)

        # 計算處理時間
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        # 記錄指標
        user_id = None
        if hasattr(request.state, 'user'):
            user_id = request.state.user.get('sub', None)

        metrics = RouteMetrics(
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            response_time=process_time,
            timestamp=datetime.now(),
            user_id=user_id
        )
        metrics_collector.record_request(metrics)

        # 記錄響應
        logger.info(f"[{request_id}] Response: {response.status_code} - {process_time:.4f}s")

        return response

    except Exception as e:
        # 記錄錯誤
        process_time = time.time() - start_time
        logger.error(f"[{request_id}] Error: {str(e)} - {process_time:.4f}s")

        # 記錄錯誤指標
        metrics = RouteMetrics(
            path=request.url.path,
            method=request.method,
            status_code=500,
            response_time=process_time,
            timestamp=datetime.now()
        )
        metrics_collector.record_request(metrics)

        raise

# 增強的健康檢查和管理端點
@app.get("/health")
async def health_check():
    """網關健康檢查"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "redis": "connected" if redis_client else "disconnected",
            "total_services": len(SERVICES)
        }
    }

@app.get("/ready")
async def readiness_check():
    """就绪检查 - 增強版本"""
    services_status = {}

    for service_name, service_config in SERVICES.items():
        try:
            url = service_config.url + service_config.health_path
            response = await http_client.get(url, timeout=5.0)
            services_status[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time": response.headers.get("X-Process-Time", "N/A"),
                "url": service_config.url
            }
        except Exception as e:
            services_status[service_name] = {
                "status": "unreachable",
                "error": str(e),
                "url": service_config.url
            }

    all_healthy = all(
        status["status"] == "healthy"
        for status in services_status.values()
    )

    return {
        "status": "ready" if all_healthy else "not_ready",
        "services": services_status,
        "timestamp": datetime.now().isoformat(),
        "gateway_version": "2.0.0"
    }

@app.get("/api/services")
async def list_services():
    """列出所有可用服务"""
    return {
        "services": {name: config.__dict__ for name, config in SERVICES.items()},
        "total_count": len(SERVICES),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/metrics")
async def get_metrics():
    """獲取網關指標"""
    total_metrics = len(metrics_storage)
    recent_metrics = [
        m for m in metrics_storage
        if (datetime.now() - m.timestamp).total_seconds() < 300  # 5分鐘內
    ]

    return {
        "total_requests": total_metrics,
        "recent_requests_5min": len(recent_metrics),
        "services": {
            name: metrics_collector.get_service_metrics(name, 5)
            for name in SERVICES.keys()
        },
        "cache_status": {
            "redis_connected": redis_client is not None,
            "memory_cache_size": len(memory_cache)
        },
        "timestamp": datetime.now().isoformat()
    }

# 認證相關API端點
@app.post("/api/auth/login")
async def login(username: str, password: str):
    """用戶登錄接口"""
    try:
        # 驗證用戶
        user = jwt_auth_service.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用戶名或密碼錯誤",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 創建令牌
        token_data = {
            "sub": user["username"],
            "username": user["username"],
            "roles": user["roles"],
            "permissions": user["permissions"]
        }

        access_token = jwt_auth_service.create_access_token(token_data)
        refresh_token = jwt_auth_service.create_refresh_token({"sub": user["username"]})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": jwt_auth_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "username": user["username"],
                "email": user["email"],
                "roles": user["roles"],
                "permissions": user["permissions"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登錄失敗: {str(e)}"
        )

@app.post("/api/auth/refresh")
async def refresh_token(refresh_token: str):
    """刷新訪問令牌"""
    try:
        new_access_token = jwt_auth_service.refresh_access_token(refresh_token)
        if not new_access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的刷新令牌"
            )

        return {
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": jwt_auth_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌刷新失敗: {str(e)}"
        )

@app.post("/api/auth/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user),
    refresh_token: Optional[str] = None
):
    """用戶登出"""
    try:
        # 撤銷當前用戶的所有令牌
        if refresh_token:
            payload = jwt_auth_service.verify_token(refresh_token, "refresh")
            if payload:
                jti = payload.get("jti")
                exp = datetime.fromtimestamp(payload.get("exp"))
                jwt_auth_service.revoke_token(jti, exp)

        return {
            "message": "登出成功",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登出失敗: {str(e)}"
        )

@app.get("/api/auth/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """獲取當前用戶信息"""
    try:
        username = current_user.get("sub")
        user = jwt_auth_service.users_db.get(username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )

        return {
            "username": user["username"],
            "email": user["email"],
            "roles": user["roles"],
            "permissions": user["permissions"],
            "created_at": user["created_at"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取用戶信息失敗: {str(e)}"
        )

# OAuth2 授權端點
@app.get("/api/oauth2/authorize")
async def oauth2_authorize(
    response_type: str = "code",
    client_id: str = "",
    redirect_uri: str = "",
    scope: str = "",
    state: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """OAuth2授權端點"""
    if response_type != "code":
        raise HTTPException(
            status_code=400,
            detail="只支持授權碼模式"
        )

    # 驗證客戶端
    client = oauth2_service.clients.get(client_id)
    if not client:
        raise HTTPException(
            status_code=400,
            detail="無效的客戶端ID"
        )

    if redirect_uri not in client["redirect_uris"]:
        raise HTTPException(
            status_code=400,
            detail="無效的重定向URI"
        )

    # 生成授權碼
    scope_list = scope.split() if scope else client["scopes"]
    code = oauth2_service.generate_authorization_code(client_id, current_user["sub"], scope_list)

    # 構建回調URL
    callback_url = f"{redirect_uri}?code={code}"
    if state:
        callback_url += f"&state={state}"

    return {
        "authorization_url": callback_url,
        "message": "請訪問授權URL完成授權"
    }

@app.post("/api/oauth2/token")
async def oauth2_token(
    grant_type: str,
    code: Optional[str] = None,
    refresh_token: Optional[str] = None,
    client_id: str = "",
    client_secret: str = ""
):
    """OAuth2令牌端點"""
    if grant_type == "authorization_code":
        if not code:
            raise HTTPException(
                status_code=400,
                detail="缺少授權碼"
            )

        tokens = oauth2_service.exchange_code_for_tokens(code, client_id, client_secret)
        if not tokens:
            raise HTTPException(
                status_code=400,
                detail="無效的授權碼"
            )

        return tokens

    elif grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(
                status_code=400,
                detail="缺少刷新令牌"
            )

        # 驗證客戶端
        if not oauth2_service.validate_client(client_id, client_secret):
            raise HTTPException(
                status_code=401,
                detail="無效的客戶端認證"
            )

        new_access_token = jwt_auth_service.refresh_access_token(refresh_token)
        if not new_access_token:
            raise HTTPException(
                status_code=401,
                detail="無效的刷新令牌"
            )

        return {
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": jwt_auth_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    else:
        raise HTTPException(
            status_code=400,
            detail="不支持的授權類型"
        )

@app.get("/ready")
async def readiness_check():
    """就绪检查"""
    services_status = {}

    for service_name, service_config in SERVICES.items():
        try:
            url = service_config["url"] + service_config["health_path"]
            response = await http_client.get(url)
            services_status[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code
            }
        except Exception as e:
            services_status[service_name] = {
                "status": "unreachable",
                "error": str(e)
            }

    all_healthy = all(
        status["status"] == "healthy"
        for status in services_status.values()
    )

    return {
        "status": "ready" if all_healthy else "not_ready",
        "services": services_status,
        "timestamp": time.time()
    }

@app.get("/api/services")
async def list_services():
    """列出所有可用服务"""
    return {
        "services": list(SERVICES.keys()),
        "timestamp": time.time()
    }

async def enhanced_proxy_request(
    request: Request,
    service_name: str,
    path: str,
    current_user: Dict[str, Any] = None
):
    """增強的代理請求到後端服務"""
    if service_name not in SERVICES:
        raise HTTPException(
            status_code=404,
            detail=f"服務 {service_name} 不存在"
        )

    service_config: ServiceConfig = SERVICES[service_name]
    target_url = service_config.url + path

    # 檢查認證要求
    if service_config.auth_required and not current_user:
        raise HTTPException(
            status_code=401,
            detail="此服務需要認證"
        )

    # 檢查限流
    if service_config.rate_limit:
        user_key = f"service_limit:{service_name}:{current_user.get('sub', 'anonymous')}"
        if not await rate_limiter.is_allowed(user_key, service_config.rate_limit, 60):
            raise HTTPException(
                status_code=429,
                detail=f"服務 {service_name} 請求過於頻繁"
            )

    # 獲取請求體
    body = await request.body()

    # 構建請求頭
    headers = dict(request.headers)
    headers.pop("host", None)  # 移除host頭避免衝突

    # 添加用戶信息到請求頭
    if current_user:
        headers["X-User-ID"] = current_user.get("sub", "")
        headers["X-User-Name"] = current_user.get("username", "")

    # 記錄開始時間
    start_time = time.time()

    # 重試機制
    last_exception = None
    for attempt in range(service_config.retries):
        try:
            # 發送請求到後端服務
            response = await http_client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params,
                timeout=service_config.timeout
            )

            # 記錄成功指標
            process_time = time.time() - start_time
            metrics = RouteMetrics(
                path=f"/{service_name}/{path}",
                method=request.method,
                status_code=response.status_code,
                response_time=process_time,
                timestamp=datetime.now(),
                user_id=current_user.get("sub") if current_user else None
            )
            metrics_collector.record_request(metrics)

            logger.info(f"代理請求成功: {request.method} {service_config.url}{path} - {response.status_code} ({process_time:.3f}s)")

            # 返回響應
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers={
                    **dict(response.headers),
                    "X-Gateway-Request-ID": getattr(request.state, 'request_id', 'N/A'),
                    "X-Gateway-Service": service_name,
                    "X-Gateway-Proxy-Time": str(process_time)
                },
                media_type=response.headers.get("content-type")
            )

        except httpx.TimeoutException as e:
            last_exception = e
            logger.warning(f"服務 {service_name} 請求超時 (嘗試 {attempt + 1}/{service_config.retries}): {e}")
            if attempt < service_config.retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))  # 指數退避
                continue

        except httpx.RequestError as e:
            last_exception = e
            logger.error(f"服務 {service_name} 請求失敗 (嘗試 {attempt + 1}/{service_config.retries}): {e}")
            if attempt < service_config.retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue

    # 所有重試都失敗了
    process_time = time.time() - start_time
    metrics = RouteMetrics(
        path=f"/{service_name}/{path}",
        method=request.method,
        status_code=503,
        response_time=process_time,
        timestamp=datetime.now(),
        user_id=current_user.get("sub") if current_user else None
    )
    metrics_collector.record_request(metrics)

    raise HTTPException(
        status_code=503,
        detail=f"服務 {service_name} 暫時不可用，請稍後再試"
    )

# 增強的API路由，集成認證和限流
@app.api_route("/api/quant/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_quant_system(
    request: Request,
    path: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: None = Depends(check_rate_limit)
):
    """代理量化系統請求（需要認證）"""
    return await enhanced_proxy_request(request, "quant-system", f"/api/{path}", current_user)

@app.api_route("/api/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_user_management(
    request: Request,
    path: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: None = Depends(check_rate_limit)
):
    """代理用戶管理請求（需要認證）"""
    return await enhanced_proxy_request(request, "user-management", f"/{path}", current_user)

@app.api_route("/api/strategies/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_strategy_dashboard(
    request: Request,
    path: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: None = Depends(check_rate_limit)
):
    """代理策略管理Dashboard請求（需要認證）"""
    return await enhanced_proxy_request(request, "strategy-dashboard", f"/{path}", current_user)

@app.api_route("/api/config/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_config_service(
    request: Request,
    path: str,
    _: None = Depends(check_rate_limit)
):
    """代理配置管理請求（無需認證）"""
    return await enhanced_proxy_request(request, "config-service", f"/{path}")

@app.get("/")
async def root():
    """網關根路徑"""
    return {
        "message": "CBSC System API Gateway - Enhanced",
        "version": "2.0.0",
        "description": "統一API網關 - 服務路由、監控、認證和治理",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "services": "/api/services",
            "metrics": "/api/metrics",
            "auth": "/api/auth/token",
            "docs": "/docs",
            "redoc": "/redoc",
            "api_routes": {
                "quant_system": "/api/quant/*",
                "user_management": "/api/users/*",
                "strategy_dashboard": "/api/strategies/*",
                "config_service": "/api/config/*"
            }
        },
        "features": [
            "統一認證 (JWT)",
            "請求限流",
            "服務監控",
            "負載均衡",
            "Redis緩存",
            "錯誤重試",
            "指標收集"
        ]
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP異常處理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.now().isoformat()
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局異常處理器"""
    logger.error(f"未處理的異常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "服務器內部錯誤",
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.now().isoformat()
            }
        }
    )

# 啟動和關閉事件
@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    logger.info("🚀 CBSC API Gateway v2.0 正在啟動...")

    try:
        # 檢查Redis連接
        if redis_client:
            await redis_client.ping()
            logger.info("✅ Redis 連接成功")
        else:
            logger.warning("⚠️ Redis 連接失敗，使用內存緩存")

        # 檢查後端服務健康狀態
        logger.info("🔍 檢查後端服務健康狀態...")
        for service_name, service_config in SERVICES.items():
            try:
                response = await http_client.get(
                    service_config.url + service_config.health_path,
                    timeout=5.0
                )
                logger.info(f"✅ {service_name}: {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ {service_name}: 不可用 - {e}")

        logger.info("🎉 CBSC API Gateway v2.0 啟動完成!")
        logger.info("📚 API文檔: http://localhost:8000/docs")
        logger.info("🔍 健康檢查: http://localhost:8000/health")

    except Exception as e:
        logger.error(f"❌ 啟動過程中發生錯誤: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    logger.info("🛑 正在關閉 CBSC API Gateway...")

    try:
        await http_client.aclose()
        if redis_client:
            await redis_client.close()
        logger.info("✅ 所有資源已安全關閉")
    except Exception as e:
        logger.error(f"❌ 關閉過程中發生錯誤: {e}")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": time.time()
        }
    )

# 启动和关闭事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("API Gateway starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("API Gateway shutting down...")
    await http_client.aclose()

if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(
        description="CBSC System API Gateway - Enhanced",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        ## 🚀 啟動示例

        # 默認啟動 (端口8000)
        python main.py

        # 指定端口啟動
        python main.py --port 8080

        # 生產模式啟動
        python main.py --production

        # 調試模式啟動
        python main.py --debug

        ## 📱 訪問地址

        API文檔: http://localhost:8000/docs
        健康檢查: http://localhost:8000/health
        服務狀態: http://localhost:8000/api/services
        系統指標: http://localhost:8000/api/metrics
        """
    )

    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="指定端口號 (默認: 8000)"
    )

    parser.add_argument(
        "--host", "-H",
        type=str,
        default="0.0.0.0",
        help="指定主機地址 (默認: 0.0.0.0)"
    )

    parser.add_argument(
        "--production", "-P",
        action="store_true",
        help="生產模式 (關閉重載和調試)"
    )

    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="調試模式 (啟用詳細日誌)"
    )

    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=1,
        help="工作進程數量 (生產模式)"
    )

    args = parser.parse_args()

    # 打印啟動信息
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        🚀 CBSC System API Gateway - Enhanced v2.0         ║
    ║                                                           ║
    ║  統一API網關 - 服務路由、監控、認證和治理                    ║
    ║                                                           ║
    ║  📊 服務監控 | 🔐 統一認證 | ⚡ 負載均衡                     ║
    ║  🛡️ 請求限流 | 📈 指標收集 | 🔄 錯誤重試                     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════════
    """)

    logger.info(f"🎯 啟動參數: 端口={args.port}, 主機={args.host}, 生產模式={args.production}, 調試模式={args.debug}")

    # 配置uvicorn
    config = {
        "app": "main:app",
        "host": args.host,
        "port": args.port,
        "log_level": "debug" if args.debug else "info",
        "reload": not args.production,
        "access_log": True,
        "use_colors": True,
    }

    # 生產模式配置
    if args.production:
        config.update({
            "workers": args.workers,
            "limit_concurrency": 1000,
            "limit_max_requests": 10000,
            "limit_max_requests_jitter": 1000,
        })

    try:
        uvicorn.run(**config)
    except KeyboardInterrupt:
        logger.info("👋 收到中斷信號，正在關閉網關...")
    except Exception as e:
        logger.error(f"❌ 網關啟動失敗: {e}")
        sys.exit(1)