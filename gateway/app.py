"""
CBSC System API Gateway - Production Ready Version
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
from typing import Dict, Any, List, Optional, Union
import json
import redis
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass, asdict
import uvicorn
from contextlib import asynccontextmanager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置数据结构
@dataclass
class ServiceConfig:
    """服务配置数据类"""
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
    """路由指标数据类"""
    path: str
    method: str
    status_code: int
    response_time: float
    timestamp: datetime
    user_id: Optional[str] = None

# 全局配置
class GatewayConfig:
    """网关全局配置"""
    SECRET_KEY = os.getenv("GATEWAY_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    RATE_LIMIT_WINDOW = 60  # seconds
    MAX_REQUESTS_PER_IP = 1000
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

config = GatewayConfig()

# 服务配置 - 从环境变量加载
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

# 安全配置
security = HTTPBearer(auto_error=False)

# 全局状态
class GatewayState:
    """网关全局状态"""
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.memory_cache: Dict[str, Any] = {}
        self.metrics_storage: List[RouteMetrics] = []

# 全局状态实例
gateway_state = GatewayState()

# 认证服务类
class AuthenticationService:
    """认证服务"""

    def __init__(self):
        self.secret_key = config.SECRET_KEY
        self.algorithm = config.JWT_ALGORITHM
        # Mock user database - in production, use actual database
        self.users_db = {
            "admin": {
                "username": "admin",
                "password_hash": hmac.new(
                    self.secret_key.encode(),
                    "admin123".encode(),
                    hashlib.sha256
                ).hexdigest(),
                "roles": ["admin"],
                "permissions": ["read", "write", "delete"],
                "email": "admin@cbsc.com",
                "created_at": datetime.now().isoformat()
            }
        }

    def create_token(self, payload: Dict[str, Any], token_type: str = "access") -> str:
        """创建JWT令牌"""
        import jwt

        now = datetime.utcnow()
        if token_type == "access":
            expire = now + timedelta(minutes=config.TOKEN_EXPIRE_MINUTES)
        else:  # refresh token
            expire = now + timedelta(days=30)

        payload.update({
            "exp": expire,
            "iat": now,
            "type": token_type,
            "jti": hashlib.md5(f"{now}{token_type}".encode()).hexdigest()
        })

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            import jwt
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            if payload.get("type") != token_type:
                return None

            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """验证用户身份"""
        user = self.users_db.get(username)
        if not user:
            return None

        password_hash = hmac.new(
            self.secret_key.encode(),
            password.encode(),
            hashlib.sha256
        ).hexdigest()

        if user["password_hash"] == password_hash:
            return user

        return None

# 限流器类
class RateLimiter:
    """请求限流器"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client

    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """检查是否允许请求"""
        if not self.redis:
            # 使用内存限流
            current_time = int(time.time())
            window_start = current_time - window

            # 清理过期记录
            if key in gateway_state.memory_cache:
                gateway_state.memory_cache[key] = [
                    timestamp for timestamp in gateway_state.memory_cache[key]
                    if timestamp > window_start
                ]
            else:
                gateway_state.memory_cache[key] = []

            # 检查限流
            if len(gateway_state.memory_cache[key]) >= limit:
                return False

            gateway_state.memory_cache[key].append(current_time)
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

# 指标收集器类
class MetricsCollector:
    """指标收集器"""

    def record_request(self, metrics: RouteMetrics):
        """记录请求指标"""
        gateway_state.metrics_storage.append(metrics)

        # 限制内存使用
        if len(gateway_state.metrics_storage) > 10000:
            gateway_state.metrics_storage = gateway_state.metrics_storage[-5000:]

    def get_service_metrics(self, service_name: str, minutes: int = 5) -> Dict[str, Any]:
        """获取服务指标"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [
            m for m in gateway_state.metrics_storage
            if m.timestamp > cutoff_time and service_name in m.path
        ]

        if not recent_metrics:
            return {"status": "no_data"}

        return {
            "total_requests": len(recent_metrics),
            "avg_response_time": sum(m.response_time for m in recent_metrics) / len(recent_metrics),
            "success_rate": len([m for m in recent_metrics if 200 <= m.status_code < 400]) / len(recent_metrics),
            "error_rate": len([m for m in recent_metrics if m.status_code >= 400]) / len(recent_metrics),
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        total_requests = len(gateway_state.metrics_storage)
        recent_metrics = [
            m for m in gateway_state.metrics_storage
            if (datetime.now() - m.timestamp).total_seconds() < 300  # 5分钟内
        ]

        return {
            "total_requests": total_requests,
            "recent_requests_5min": len(recent_metrics),
            "services": {
                name: self.get_service_metrics(name, 5)
                for name in SERVICES.keys()
            },
            "cache_status": {
                "redis_connected": gateway_state.redis_client is not None,
                "memory_cache_size": len(gateway_state.memory_cache)
            },
            "timestamp": datetime.now().isoformat()
        }

# 代理请求处理器
class ProxyHandler:
    """代理请求处理器"""

    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client

    async def proxy_request(
        self,
        request: Request,
        service_name: str,
        path: str,
        current_user: Optional[Dict[str, Any]] = None
    ):
        """代理请求到后端服务"""
        if service_name not in SERVICES:
            raise HTTPException(
                status_code=404,
                detail=f"服务 {service_name} 不存在"
            )

        service_config = SERVICES[service_name]
        target_url = service_config.url + path

        # 检查认证要求
        if service_config.auth_required and not current_user:
            raise HTTPException(
                status_code=401,
                detail="此服务需要认证"
            )

        # 构建请求头
        headers = dict(request.headers)
        headers.pop("host", None)  # 移除host头避免冲突

        # 添加用户信息到请求头
        if current_user:
            headers["X-User-ID"] = current_user.get("sub", "")
            headers["X-User-Name"] = current_user.get("username", "")

        # 获取请求体
        body = await request.body()

        # 记录开始时间
        start_time = time.time()

        # 重试机制
        last_exception = None
        for attempt in range(service_config.retries):
            try:
                # 发送请求到后端服务
                response = await self.http_client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body,
                    params=request.query_params,
                    timeout=service_config.timeout
                )

                # 记录成功指标
                process_time = time.time() - start_time
                metrics = RouteMetrics(
                    path=f"/{service_name}/{path}",
                    method=request.method,
                    status_code=response.status_code,
                    response_time=process_time,
                    timestamp=datetime.now(),
                    user_id=current_user.get("sub") if current_user else None
                )

                if hasattr(gateway_state, 'metrics_collector'):
                    gateway_state.metrics_collector.record_request(metrics)

                logger.info(f"代理请求成功: {request.method} {service_config.url}{path} - {response.status_code} ({process_time:.3f}s)")

                # 返回响应
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers={
                        **dict(response.headers),
                        "X-Gateway-Service": service_name,
                        "X-Gateway-Proxy-Time": str(process_time)
                    },
                    media_type=response.headers.get("content-type")
                )

            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"服务 {service_name} 请求超时 (尝试 {attempt + 1}/{service_config.retries}): {e}")
                if attempt < service_config.retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))  # 指数退避
                    continue

            except httpx.RequestError as e:
                last_exception = e
                logger.error(f"服务 {service_name} 请求失败 (尝试 {attempt + 1}/{service_config.retries}): {e}")
                if attempt < service_config.retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue

        # 所有重试都失败了
        process_time = time.time() - start_time
        metrics = RouteMetrics(
            path=f"/{service_name}/{path}",
            method=request.method,
            status_code=503,
            response_time=process_time,
            timestamp=datetime.now(),
            user_id=current_user.get("sub") if current_user else None
        )

        if hasattr(gateway_state, 'metrics_collector'):
            gateway_state.metrics_collector.record_request(metrics)

        raise HTTPException(
            status_code=503,
            detail=f"服务 {service_name} 暂时不可用，请稍后再试"
        )

# 初始化服务
auth_service = AuthenticationService()

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 CBSC API Gateway 正在启动...")

    try:
        # 初始化Redis连接
        try:
            gateway_state.redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)
            await asyncio.get_event_loop().run_in_executor(None, gateway_state.redis_client.ping)
            logger.info("✅ Redis 连接成功")
        except Exception as e:
            logger.warning(f"⚠️ Redis 连接失败，将使用内存缓存: {e}")
            gateway_state.redis_client = None

        # 初始化HTTP客户端
        gateway_state.http_client = httpx.AsyncClient(timeout=30.0)

        # 初始化服务
        gateway_state.rate_limiter = RateLimiter(gateway_state.redis_client)
        gateway_state.metrics_collector = MetricsCollector()
        gateway_state.proxy_handler = ProxyHandler(gateway_state.http_client)

        # 检查后端服务健康状态
        logger.info("🔍 检查后端服务健康状态...")
        for service_name, service_config in SERVICES.items():
            try:
                response = await gateway_state.http_client.get(
                    service_config.url + service_config.health_path,
                    timeout=5.0
                )
                logger.info(f"✅ {service_name}: {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ {service_name}: 不可用 - {e}")

        logger.info("🎉 CBSC API Gateway 启动完成!")
        logger.info("📚 API文档: http://localhost:8000/docs")
        logger.info("🔍 健康检查: http://localhost:8000/health")

    except Exception as e:
        logger.error(f"❌ 启动过程中发生错误: {e}")
        raise

    yield

    # 关闭时执行
    logger.info("🛑 正在关闭 CBSC API Gateway...")

    try:
        if gateway_state.http_client:
            await gateway_state.http_client.aclose()
        if gateway_state.redis_client:
            await asyncio.get_event_loop().run_in_executor(None, gateway_state.redis_client.close)
        logger.info("✅ 所有资源已安全关闭")
    except Exception as e:
        logger.error(f"❌ 关闭过程中发生错误: {e}")

# 创建FastAPI应用
app = FastAPI(
    title="CBSC System API Gateway",
    description="""
    ## 🚀 CBSC系统统一API网关

    ### 核心功能
    - **统一入口**: 单一接入点管理所有后端服务
    - **智能路由**: 基于路径的请求分发
    - **统一认证**: JWT标准认证机制
    - **服务监控**: 实时监控和健康检查
    - **限流控制**: IP级别的请求限流
    - **缓存加速**: Redis分布式缓存
    - **指标收集**: 请求链路追踪和指标收集

    ### 支持的服务
    - 🔬 **量化分析系统**: CBSC策略分析、回测引擎
    - 👥 **用户管理系统**: 认证授权、用户资料管理
    - 📊 **策略管理Dashboard**: 策略监控、参数优化
    - ⚙️ **配置管理服务**: 系统配置、参数管理
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS中间件配置
if config.ENVIRONMENT == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # 生产环境CORS配置
    allowed_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

# 请求日志中间件
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()
    request_id = hashlib.md5(f"{time.time()}{request.client.host}".encode()).hexdigest()[:8]

    # 记录请求
    logger.info(f"[{request_id}] {request.method} {request.url.path} - {request.client.host}")

    try:
        # 执行请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        # 记录响应
        logger.info(f"[{request_id}] Response: {response.status_code} - {process_time:.4f}s")

        return response

    except Exception as e:
        # 记录错误
        process_time = time.time() - start_time
        logger.error(f"[{request_id}] Error: {str(e)} - {process_time:.4f}s")
        raise

# 依赖注入函数
async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """获取当前用户信息"""
    if not credentials:
        return None

    payload = auth_service.verify_token(credentials.credentials, "access")
    return payload

async def require_auth(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    """要求认证的依赖"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

async def check_rate_limit(request: Request, limit: int = 1000):
    """检查请求限流"""
    if not hasattr(gateway_state, 'rate_limiter'):
        return

    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"

    if not await gateway_state.rate_limiter.is_allowed(key, limit, config.RATE_LIMIT_WINDOW):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试"
        )

# 健康检查端点
@app.get("/health")
async def health_check():
    """网关健康检查"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "2.0.0",
        "environment": config.ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
        "services": {
            "redis": "connected" if gateway_state.redis_client else "disconnected",
            "total_services": len(SERVICES)
        }
    }

@app.get("/ready")
async def readiness_check():
    """就绪检查"""
    if not gateway_state.http_client:
        return {"status": "not_ready", "reason": "HTTP client not initialized"}

    services_status = {}

    for service_name, service_config in SERVICES.items():
        try:
            url = service_config.url + service_config.health_path
            response = await gateway_state.http_client.get(url, timeout=5.0)
            services_status[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
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
        "timestamp": datetime.now().isoformat()
    }

# 服务信息端点
@app.get("/api/services")
async def list_services():
    """列出所有可用服务"""
    return {
        "services": {name: asdict(config) for name, config in SERVICES.items()},
        "total_count": len(SERVICES),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/metrics")
async def get_metrics():
    """获取网关指标"""
    if not hasattr(gateway_state, 'metrics_collector'):
        return {"status": "metrics_not_available"}

    return gateway_state.metrics_collector.get_system_metrics()

# 认证端点
@app.post("/api/auth/login")
async def login(username: str, password: str):
    """用户登录接口"""
    try:
        # 验证用户
        user = auth_service.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 创建令牌
        token_data = {
            "sub": user["username"],
            "username": user["username"],
            "roles": user["roles"],
            "permissions": user["permissions"]
        }

        access_token = auth_service.create_token(token_data, "access")
        refresh_token = auth_service.create_token({"sub": user["username"]}, "refresh")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": config.TOKEN_EXPIRE_MINUTES * 60,
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
            detail=f"登录失败: {str(e)}"
        )

@app.get("/api/auth/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(require_auth)):
    """获取当前用户信息"""
    return {
        "username": current_user.get("username"),
        "sub": current_user.get("sub"),
        "roles": current_user.get("roles"),
        "permissions": current_user.get("permissions"),
        "exp": current_user.get("exp")
    }

# API路由代理
@app.api_route("/api/quant/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_quant_system(
    request: Request,
    path: str,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """代理量化系统请求（需要认证）"""
    return await gateway_state.proxy_handler.proxy_request(
        request, "quant-system", f"/api/{path}", current_user
    )

@app.api_route("/api/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_user_management(
    request: Request,
    path: str,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """代理用户管理请求（需要认证）"""
    return await gateway_state.proxy_handler.proxy_request(
        request, "user-management", f"/{path}", current_user
    )

@app.api_route("/api/strategies/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_strategy_dashboard(
    request: Request,
    path: str,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """代理策略管理Dashboard请求（需要认证）"""
    return await gateway_state.proxy_handler.proxy_request(
        request, "strategy-dashboard", f"/{path}", current_user
    )

@app.api_route("/api/config/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_config_service(request: Request, path: str):
    """代理配置管理请求（无需认证）"""
    return await gateway_state.proxy_handler.proxy_request(
        request, "config-service", f"/{path}"
    )

# 根路径
@app.get("/")
async def root():
    """网关根路径"""
    return {
        "message": "CBSC System API Gateway",
        "version": "2.0.0",
        "description": "统一API网关 - 服务路由、监控、认证和治理",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "services": "/api/services",
            "metrics": "/api/metrics",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "features": [
            "统一认证 (JWT)",
            "请求限流",
            "服务监控",
            "负载均衡",
            "Redis缓存",
            "错误重试",
            "指标收集"
        ]
    }

# 异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
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
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "服务器内部错误",
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.now().isoformat()
            }
        }
    )

# 启动入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="CBSC System API Gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--port", "-p",
        type=int,
        default=int(os.getenv("GATEWAY_PORT", 8000)),
        help="指定端口号"
    )

    parser.add_argument(
        "--host", "-H",
        type=str,
        default=os.getenv("GATEWAY_HOST", "0.0.0.0"),
        help="指定主机地址"
    )

    parser.add_argument(
        "--production", "-P",
        action="store_true",
        default=os.getenv("ENVIRONMENT") == "production",
        help="生产模式"
    )

    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=int(os.getenv("GATEWAY_WORKERS", 1)),
        help="工作进程数量"
    )

    args = parser.parse_args()

    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        🚀 CBSC System API Gateway v2.0                    ║
    ║                                                           ║
    ║  统一API网关 - 服务路由、监控、认证和治理                    ║
    ║                                                           ║
    ║  📊 服务监控 | 🔐 统一认证 | ⚡ 负载均衡                     ║
    ║  🛡️ 请求限流 | 📈 指标收集 | 🔄 错误重试                     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════════
    """)

    logger.info(f"🎯 启动参数: 端口={args.port}, 主机={args.host}, 生产模式={args.production}")

    # 配置uvicorn
    uvicorn.run(
        "app:app",
        host=args.host,
        port=args.port,
        log_level="info" if args.production else "debug",
        reload=not args.production,
        workers=args.workers if args.production else 1,
        access_log=True,
    )