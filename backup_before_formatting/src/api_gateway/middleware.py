#!/usr / bin / env python3
"""
API網關中間件
港股量化交易系統 - 請求處理中間件

提供請求認證、授權、限流、日誌記錄、
性能監控、緩存等中間件功能。

中間件鏈:
1. 請求日誌中間件
2. 請求ID生成中間件
3. 限流中間件
4. 認證中間件
5. 授權中間件
6. 緩存中間件
7. 性能監控中間件
8. 壓縮中間件
9. 響應格式化中間件
"""

import asyncio
import hashlib
import ipaddress
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import quote, unquote

import aiofiles
import jwt
import redis
from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .api_standards import (
    APIErrorCodes,
    APIRateLimits,
    APISecurity,
    APIValidationRules,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """請求ID生成中間件"""

    def __init__(self, app):
        super().__init__(app)
        self.counter = 0

    async def dispatch(self, request: Request, call_next: Callable):
        # 生成請求ID
        self.counter += 1
        timestamp = int(time.time() * 1000)
        request_id = f"req_{timestamp}_{self.counter:06d}"

        # 添加到請求狀態
        request.state.request_id = request_id

        # 處理請求
        response = await call_next(request)

        # 添加響應頭
        response.headers["X - Request - ID"] = request_id

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """請求日誌中間件"""

    def __init__(self, app, log_level: str = "INFO"):
        super().__init__(app)
        self.logger = logging.getLogger(f"{__name__}.request_logger")
        self.logger.setLevel(getattr(logging, log_level.upper()))

    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")

        # 收集請求信息
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("User - Agent", ""),
            "content_length": request.headers.get("Content - Length", "0"),
            "content_type": request.headers.get("Content - Type", ""),
        }

        # 記錄敏感信息
        if hasattr(request.state, "user"):
            request_info["user_id"] = request.state.user.user_id

        # 記錄請求開始
        self.logger.info(
            f"API請求開始: {request.method} {request.url.path}", extra=request_info
        )

        # 處理請求
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # 收集響應信息
            response_info = request_info.copy()
            response_info.update(
                {
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "response_size": response.headers.get("Content - Length", "0"),
                }
            )

            # 根據狀態碼決定日誌級別
            log_level = "INFO"
            if response.status_code >= 400:
                log_level = "WARNING"
            if response.status_code >= 500:
                log_level = "ERROR"

            # 記錄請求完成
            log_method = getattr(self.logger, log_level.lower())
            log_method(
                f"API請求完成: {response.status_code} ({process_time:.3f}s)",
                extra=response_info,
            )

            return response

        except Exception as e:
            process_time = time.time() - start_time

            # 記錄錯誤
            error_info = request_info.copy()
            error_info.update(
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "process_time": process_time,
                }
            )

            self.logger.error(
                f"API請求錯誤: {str(e)} ({process_time:.3f}s)", extra=error_info
            )

            raise

    def _get_client_ip(self, request: Request) -> str:
        """獲取客戶端真實IP"""
        # 檢查代理頭
        forwarded_for = request.headers.get("X - Forwarded - For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X - Real - IP")
        if real_ip:
            return real_ip

        # 直接連接
        return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """API限流中間件"""

    def __init__(
        self,
        app,
        redis_client: Optional[redis.Redis] = None,
        limits: Dict[str, int] = None,
    ):
        super().__init__(app)
        self.redis_client = redis_client
        self.limits = limits or {
            "default": APIRateLimits.BASIC_LIMIT,
            "auth": APIRateLimits.AUTH_LIMIT,
            "trade": APIRateLimits.TRADE_LIMIT,
            "backtest": APIRateLimits.BACKTEST_LIMIT,
        }

    async def dispatch(self, request: Request, call_next: Callable):
        # 獲取限流配置
        limit_type = self._get_limit_type(request)
        limit = self.limits.get(limit_type, self.limits["default"])
        window = 60  # 1分鐘窗口

        # 獲取限流鍵
        rate_limit_key = self._get_rate_limit_key(request)

        # 檢查限流
        if self.redis_client:
            allowed, remaining, reset_time = await self._check_rate_limit(
                rate_limit_key, limit, window
            )

            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "success": False,
                        "error": {
                            "code": APIErrorCodes.RATE_LIMIT_EXCEEDED,
                            "message": "請求過於頻繁，請稍後再試",
                            "details": {
                                "limit": limit,
                                "window": window,
                                "reset_time": reset_time,
                            },
                        },
                    },
                    headers={
                        "X - RateLimit - Limit": str(limit),
                        "X - RateLimit - Remaining": str(remaining),
                        "X - RateLimit - Reset": str(reset_time),
                        "Retry - After": str(reset_time - int(time.time())),
                    },
                )

        response = await call_next(request)

        # 添加限流響應頭
        if self.redis_client:
            response.headers["X - RateLimit - Limit"] = str(limit)
            response.headers["X - RateLimit - Remaining"] = str(remaining)

        return response

    def _get_limit_type(self, request: Request) -> str:
        """根據路徑確定限流類型"""
        path = request.url.path.lower()

        if "/auth" in path:
            return "auth"
        elif "/trade" in path or "/order" in path:
            return "trade"
        elif "/backtest" in path:
            return "backtest"
        else:
            return "default"

    def _get_rate_limit_key(self, request: Request) -> str:
        """生成限流鍵"""
        # 優先使用用戶ID
        if hasattr(request.state, "user"):
            user_id = request.state.user.user_id
            return f"rate_limit:user:{user_id}"

        # 使用IP地址
        client_ip = request.headers.get("X - Real - IP") or request.client.host
        return f"rate_limit:ip:{client_ip}"

    async def _check_rate_limit(
        self, key: str, limit: int, window: int
    ) -> Tuple[bool, int, int]:
        """檢查限流狀態"""
        try:
            current_time = int(time.time())
            window_start = current_time - window

            # 清理過期記錄
            await self.redis_client.zremrangebyscore(key, 0, window_start)

            # 獲取當前計數
            current_count = await self.redis_client.zcard(key)

            if current_count >= limit:
                # 計算重置時間
                oldest_request = await self.redis_client.zrange(
                    key, 0, 0, withscores=True
                )
                reset_time = (
                    int(oldest_request[0][1]) + window
                    if oldest_request
                    else current_time + window
                )
                return False, 0, reset_time

            # 記錄新請求
            await self.redis_client.zadd(key, {str(current_time): current_time})
            await self.redis_client.expire(key, window)

            remaining = limit - current_count - 1
            reset_time = current_time + window

            return True, remaining, reset_time

        except Exception as e:
            logger.error(f"限流檢查失敗: {e}")
            # 限流失敗時默認允許
            return True, limit, int(time.time()) + 60


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """JWT認證中間件"""

    def __init__(
        self,
        app,
        jwt_secret: str,
        excluded_paths: List[str] = None,
        algorithm: str = "HS256",
    ):
        super().__init__(app)
        self.jwt_secret = jwt_secret
        self.algorithm = algorithm
        self.excluded_paths = excluded_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics",
            "/auth / login",
            "/auth / register",
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
            payload = jwt.decode(
                credentials, self.jwt_secret, algorithms=[self.algorithm]
            )

            # 檢查token過期
            if "exp" in payload:
                exp = datetime.fromtimestamp(payload["exp"])
                if datetime.utcnow() > exp:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token已過期",
                        headers={"WWW - Authenticate": "Bearer"},
                    )

            # 添加用戶信息到請求狀態
            request.state.user = payload
            request.state.auth_type = "jwt"

        except (ValueError, InvalidTokenError) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW - Authenticate": "Bearer"},
            )

        return await call_next(request)


class AuthorizationMiddleware(BaseHTTPMiddleware):
    """權限授權中間件"""

    def __init__(self, app, permissions_map: Dict[str, List[str]]):
        super().__init__(app)
        self.permissions_map = permissions_map

    async def dispatch(self, request: Request, call_next: Callable):
        # 檢查是否需要權限驗證
        required_permissions = self._get_required_permissions(request)
        if not required_permissions:
            return await call_next(request)

        # 檢查用戶是否已認證
        if not hasattr(request.state, "user"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="需要認證"
            )

        user = request.state.user

        # 檢查用戶權限
        user_permissions = user.get("permissions", [])
        user_roles = user.get("roles", [])

        has_permission = self._check_permissions(
            user_roles, user_permissions, required_permissions
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="權限不足"
            )

        return await call_next(request)

    def _get_required_permissions(self, request: Request) -> List[str]:
        """獲取請求所需的權限"""
        path = request.url.path
        method = request.method

        # 根據路徑和方法確定所需權限
        for pattern, permissions in self.permissions_map.items():
            if self._path_matches(path, pattern):
                method_permissions = permissions.get(method, [])
                return method_permissions

        return []

    def _path_matches(self, path: str, pattern: str) -> bool:
        """檢查路徑是否匹配模式"""
        # 簡單的匹配邏輯，可以擴展支持更複雜的模式
        if pattern.endswith("*"):
            return path.startswith(pattern[:-1])
        return path == pattern

    def _check_permissions(
        self,
        user_roles: List[str],
        user_permissions: List[str],
        required_permissions: List[str],
    ) -> bool:
        """檢查用戶是否具有所需權限"""
        # 管理員具有所有權限
        if "admin" in user_roles:
            return True

        # 檢查具體權限
        for permission in required_permissions:
            if permission not in user_permissions and "*" not in user_permissions:
                return False

        return True


class CacheMiddleware(BaseHTTPMiddleware):
    """緩存中間件"""

    def __init__(
        self,
        app,
        redis_client: Optional[redis.Redis] = None,
        cache_duration: int = 300,
        cache_key_prefix: str = "api_cache",
    ):
        super().__init__(app)
        self.redis_client = redis_client
        self.cache_duration = cache_duration
        self.cache_key_prefix = cache_key_prefix

    async def dispatch(self, request: Request, call_next: Callable):
        # 只緩存GET請求
        if request.method != "GET":
            return await call_next(request)

        # 生成緩存鍵
        cache_key = self._generate_cache_key(request)

        # 嘗試從緩存獲取
        if self.redis_client:
            cached_response = await self.redis_client.get(cache_key)
            if cached_response:
                response_data = json.loads(cached_response)
                response = JSONResponse(content=response_data["content"])

                # 添加緩存響應頭
                response.headers["X - Cache"] = "HIT"
                response.headers["X - Cache - Key"] = cache_key

                return response

        # 執行請求
        response = await call_next(request)

        # 緩存響應 (僅成功響應)
        if (
            self.redis_client
            and response.status_code == 200
            and isinstance(response, JSONResponse)
        ):
            try:
                response_content = response.body.decode()
                cache_data = {
                    "content": json.loads(response_content),
                    "timestamp": time.time(),
                    "status_code": response.status_code,
                }

                await self.redis_client.setex(
                    cache_key, self.cache_duration, json.dumps(cache_data)
                )

                response.headers["X - Cache"] = "MISS"
                response.headers["X - Cache - Key"] = cache_key

            except Exception as e:
                logger.error(f"緩存響應失敗: {e}")

        return response

    def _generate_cache_key(self, request: Request) -> str:
        """生成緩存鍵"""
        # 包含路徑和查詢參數
        path = quote(request.url.path, safe="")
        query = quote(str(request.url.query), safe="")

        # 如果有用戶信息，包含用戶ID
        user_id = ""
        if hasattr(request.state, "user"):
            user_id = request.state.user.get("user_id", "")

        # 生成哈希
        cache_string = f"{path}:{query}:{user_id}"
        cache_hash = hashlib.sha256(cache_string.encode()).hexdigest()

        return f"{self.cache_key_prefix}:{cache_hash}"


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """性能監控中間件"""

    def __init__(self, app, metrics_collector=None):
        super().__init__(app)
        self.metrics_collector = metrics_collector
        self.metrics = {
            "request_count": 0,
            "error_count": 0,
            "total_response_time": 0.0,
            "endpoint_stats": {},
            "status_code_stats": {},
        }

    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()

        # 更新請求計數
        self.metrics["request_count"] += 1

        endpoint = request.url.path
        method = request.method

        # 初始化端點統計
        if endpoint not in self.metrics["endpoint_stats"]:
            self.metrics["endpoint_stats"][endpoint] = {
                "count": 0,
                "total_time": 0.0,
                "errors": 0,
                "methods": {},
            }

        endpoint_stats = self.metrics["endpoint_stats"][endpoint]
        endpoint_stats["count"] += 1

        if method not in endpoint_stats["methods"]:
            endpoint_stats["methods"][method] = {"count": 0, "errors": 0}

        endpoint_stats["methods"][method]["count"] += 1

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # 更新統計
            self.metrics["total_response_time"] += process_time
            endpoint_stats["total_time"] += process_time

            # 更新狀態碼統計
            status_code = response.status_code
            if status_code not in self.metrics["status_code_stats"]:
                self.metrics["status_code_stats"][status_code] = 0
            self.metrics["status_code_stats"][status_code] += 1

            # 統計錯誤
            if status_code >= 400:
                self.metrics["error_count"] += 1
                endpoint_stats["errors"] += 1
                endpoint_stats["methods"][method]["errors"] += 1

            # 添加性能響應頭
            response.headers["X - Process - Time"] = f"{process_time:.3f}"

            # 檢查性能警告
            if process_time > 2.0:  # 超過2秒
                logger.warning(
                    f"慢請求警告: {method} {endpoint} ({process_time:.3f}s)",
                    extra={
                        "endpoint": endpoint,
                        "method": method,
                        "process_time": process_time,
                        "request_id": getattr(request.state, "request_id", "unknown"),
                    },
                )

            return response

        except Exception as e:
            process_time = time.time() - start_time
            self.metrics["error_count"] += 1
            endpoint_stats["errors"] += 1
            endpoint_stats["methods"][method]["errors"] += 1

            logger.error(
                f"請求處理異常: {method} {endpoint} ({process_time:.3f}s) - {str(e)}",
                extra={
                    "endpoint": endpoint,
                    "method": method,
                    "process_time": process_time,
                    "error": str(e),
                    "request_id": getattr(request.state, "request_id", "unknown"),
                },
            )
            raise

    def get_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
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

        # 計算端點平均響應時間
        for endpoint_stats in self.metrics["endpoint_stats"].values():
            if endpoint_stats["count"] > 0:
                endpoint_stats["avg_time"] = (
                    endpoint_stats["total_time"] / endpoint_stats["count"]
                )

        return {
            "total_requests": self.metrics["request_count"],
            "total_errors": self.metrics["error_count"],
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "endpoint_stats": self.metrics["endpoint_stats"],
            "status_code_stats": self.metrics["status_code_stats"],
        }


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中間件"""

    def __init__(self, app):
        super().__init__(app)
        self.blocked_ips = set()

    async def dispatch(self, request: Request, call_next: Callable):
        client_ip = self._get_client_ip(request)

        # IP黑名單檢查
        if client_ip in self.blocked_ips:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="IP地址已被封鎖"
            )

        # 檢查請求頭
        self._validate_headers(request)

        # 檢查請求大小
        content_length = request.headers.get("Content - Length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="請求體過大",
            )

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """獲取客戶端IP"""
        forwarded_for = request.headers.get("X - Forwarded - For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X - Real - IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _validate_headers(self, request: Request):
        """驗證請求頭"""
        # 檢查User - Agent
        user_agent = request.headers.get("User - Agent", "")
        if not user_agent:
            logger.warning(
                "缺少User - Agent頭",
                extra={
                    "client_ip": self._get_client_ip(request),
                    "request_id": getattr(request.state, "request_id", "unknown"),
                },
            )

        # 檢查可疑的請求頭
        suspicious_headers = [
            "X - Forwarded - Host",
            "X - Forwarded - Proto",
            "X - Forwarded - For",
            "X - Real - IP",
            "X - Originating - IP",
        ]

        for header in suspicious_headers:
            if header in request.headers:
                value = request.headers[header]
                if self._is_suspicious_header_value(value):
                    logger.warning(
                        f"可疑的請求頭: {header}={value}",
                        extra={
                            "client_ip": self._get_client_ip(request),
                            "request_id": getattr(
                                request.state, "request_id", "unknown"
                            ),
                        },
                    )

    def _is_suspicious_header_value(self, value: str) -> bool:
        """檢查是否為可疑的請求頭值"""
        suspicious_patterns = [
            "<script",
            "javascript:",
            "vbscript:",
            "onload=",
            "onerror=",
            "eval(",
            "alert(",
        ]

        value_lower = value.lower()
        return any(pattern in value_lower for pattern in suspicious_patterns)

    def block_ip(self, ip: str):
        """封鎖IP地址"""
        self.blocked_ips.add(ip)
        logger.info(f"IP地址已封鎖: {ip}")

    def unblock_ip(self, ip: str):
        """解鎖IP地址"""
        self.blocked_ips.discard(ip)
        logger.info(f"IP地址已解鎖: {ip}")


class ResponseFormatterMiddleware(BaseHTTPMiddleware):
    """響應格式化中間件"""

    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # 如果是標準響應格式，直接返回
            if isinstance(response, JSONResponse) and self._is_standard_response(
                response.body.decode()
            ):
                response.headers["X - Process - Time"] = f"{process_time:.3f}"
                return response

            # 格式化非標準響應
            if response.status_code < 400:
                # 成功響應
                formatted_response = StandardResponse(
                    success=True,
                    data=response.body.decode() if response.body else None,
                    meta=ResponseMetadata(
                        version="v1",
                        request_id=request_id,
                        processing_time=process_time,
                        endpoint=request.url.path,
                        method=request.method,
                    ),
                )
            else:
                # 錯誤響應
                error_code = f"HTTP_{response.status_code}"
                error_message = getattr(response, "detail", "Internal Server Error")

                formatted_response = StandardResponse(
                    success=False,
                    error=StandardError(
                        code=error_code, message=error_message, request_id=request_id
                    ),
                    meta=ResponseMetadata(
                        version="v1",
                        request_id=request_id,
                        processing_time=process_time,
                        endpoint=request.url.path,
                        method=request.method,
                    ),
                )

            return JSONResponse(
                content=formatted_response.dict(),
                status_code=response.status_code,
                headers={"X - Process - Time": f"{process_time:.3f}"},
            )

        except Exception as e:
            process_time = time.time() - start_time

            # 異常情況返回標準錯誤響應
            error_response = StandardResponse(
                success=False,
                error=StandardError(
                    code=APIErrorCodes.INTERNAL_ERROR,
                    message="服務器內部錯誤",
                    request_id=request_id,
                ),
                meta=ResponseMetadata(
                    version="v1",
                    request_id=request_id,
                    processing_time=process_time,
                    endpoint=request.url.path,
                    method=request.method,
                ),
            )

            return JSONResponse(
                content=error_response.dict(),
                status_code=500,
                headers={"X - Process - Time": f"{process_time:.3f}"},
            )

    def _is_standard_response(self, content: str) -> bool:
        """檢查是否為標準響應格式"""
        try:
            data = json.loads(content)
            return (
                "success" in data
                and isinstance(data["success"], bool)
                and "timestamp" in data
            )
        except (json.JSONDecodeError, KeyError):
            return False


# 中間件工廠函數
def create_middleware_chain(
    app, config: Dict[str, Any] = None
) -> List[BaseHTTPMiddleware]:
    """創建中間件鏈"""
    if not config:
        config = {}

    middlewares = []

    # 1. 安全中間件 (最先執行)
    if config.get("security_enabled", True):
        middlewares.append(SecurityMiddleware(app))

    # 2. 請求ID中間件
    middlewares.append(RequestIDMiddleware(app))

    # 3. 請求日誌中間件
    middlewares.append(
        RequestLoggingMiddleware(app, log_level=config.get("log_level", "INFO"))
    )

    # 4. 限流中間件
    if config.get("rate_limit_enabled", True) and config.get("redis_client"):
        middlewares.append(
            RateLimitMiddleware(
                app,
                redis_client=config["redis_client"],
                limits=config.get("rate_limits"),
            )
        )

    # 5. 認證中間件
    if config.get("auth_enabled", True) and config.get("jwt_secret"):
        middlewares.append(
            AuthenticationMiddleware(
                app,
                jwt_secret=config["jwt_secret"],
                excluded_paths=config.get("auth_excluded_paths"),
                algorithm=config.get("jwt_algorithm", "HS256"),
            )
        )

    # 6. 授權中間件
    if config.get("authorization_enabled", True) and config.get("permissions_map"):
        middlewares.append(
            AuthorizationMiddleware(app, permissions_map=config["permissions_map"])
        )

    # 7. 緩存中間件
    if config.get("cache_enabled", True) and config.get("redis_client"):
        middlewares.append(
            CacheMiddleware(
                app,
                redis_client=config["redis_client"],
                cache_duration=config.get("cache_duration", 300),
                cache_key_prefix=config.get("cache_key_prefix", "api_cache"),
            )
        )

    # 8. 性能監控中間件
    if config.get("performance_monitoring_enabled", True):
        middlewares.append(
            PerformanceMonitoringMiddleware(
                app, metrics_collector=config.get("metrics_collector")
            )
        )

    # 9. 響應格式化中間件 (最後執行)
    if config.get("response_formatting_enabled", True):
        middlewares.append(ResponseFormatterMiddleware(app))

    return middlewares
