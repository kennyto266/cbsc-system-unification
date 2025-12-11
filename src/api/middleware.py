"""
API中间件
API Middleware

Task #002: API接口集成和數據獲取
提供缓存、日志记录、性能监控等中间件功能
"""

import time
import logging
from typing import Callable
from datetime import datetime
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint

from .cache_service import cache_service

logger = logging.getLogger(__name__)

class CacheMiddleware(BaseHTTPMiddleware):
    """缓存中间件"""

    def __init__(self, app, cache_ttl: int = 300):
        super().__init__(app)
        self.cache_ttl = cache_ttl

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 只缓存GET请求
        if request.method != "GET":
            return await call_next(request)

        # 生成缓存键
        cache_key = f"api_cache:{request.url.path}:{hash(str(request.query_params))}"

        # 尝试从缓存获取
        cached_response = await cache_service.get(cache_key, use_pickle=False)
        if cached_response:
            logger.debug(f"缓存命中: {cache_key}")
            return Response(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response["headers"],
                media_type=cached_response["media_type"]
            )

        # 缓存未命中，执行请求
        response = await call_next(request)

        # 只缓存成功的响应
        if response.status_code == 200:
            # 获取响应内容
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # 准备缓存数据
            cache_data = {
                "content": response_body.decode('utf-8'),
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type
            }

            # 存储到缓存
            await cache_service.set(cache_key, cache_data, expire=self.cache_ttl, use_pickle=False)
            logger.debug(f"缓存存储: {cache_key}")

            # 重新创建响应
            response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()

        # 记录请求信息
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        path = request.url.path
        query_params = str(request.query_params)

        logger.info(
            f"请求开始 - {client_ip} - {method} {path} - Query: {query_params} - UA: {user_agent}"
        )

        try:
            # 执行请求
            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time

            # 记录响应信息
            logger.info(
                f"请求完成 - {client_ip} - {method} {path} - "
                f"状态码: {response.status_code} - 处理时间: {process_time:.3f}s"
            )

            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"请求错误 - {client_ip} - {method} {path} - "
                f"错误: {str(e)} - 处理时间: {process_time:.3f}s"
            )
            raise


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()

        # 执行请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 获取用户ID（如果已认证）
        user_id = None
        if hasattr(request.state, 'user') and request.state.user:
            user_id = request.state.user.id

        # 记录API调用统计
        try:
            await cache_service.record_api_call(
                endpoint=request.url.path,
                user_id=user_id or 0,
                response_time=process_time
            )
        except Exception as e:
            logger.error(f"记录API调用统计失败: {e}")

        # 添加性能信息到响应头
        response.headers["X-Performance-Time"] = f"{process_time:.3f}"
        response.headers["X-Timestamp"] = datetime.utcnow().isoformat()

        # 如果处理时间过长，记录警告
        if process_time > 2.0:
            logger.warning(
                f"慢请求检测 - {request.method} {request.url.path} - "
                f"处理时间: {process_time:.3f}s"
            )

        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """限流中间件"""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"

        # 生成限流键
        rate_limit_key = f"rate_limit:{client_ip}"

        try:
            # 检查当前请求次数
            current_requests = await cache_service.get(rate_limit_key, default=0)

            if current_requests >= self.requests_per_minute:
                return Response(
                    content='{"error": "Rate limit exceeded"}',
                    status_code=429,
                    headers={"Content-Type": "application/json"}
                )

            # 增加请求计数
            await cache_service.increment(rate_limit_key)
            await cache_service.expire(rate_limit_key, 60)  # 1分钟过期

        except Exception as e:
            logger.error(f"限流检查失败: {e}")

        # 执行请求
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:; "
        )

        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """指标收集中间件"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()

        # 获取请求信息
        method = request.method
        path = request.url.path
        status_code = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response

        except Exception as e:
            status_code = 500
            raise

        finally:
            # 计算处理时间
            process_time = time.time() - start_time

            # 记录指标
            await self._record_metrics(method, path, status_code, process_time)

    async def _record_metrics(self, method: str, path: str, status_code: int, process_time: float):
        """记录指标数据"""
        try:
            # 记录请求计数
            await cache_service.hash_set(
                "metrics:request_count",
                f"{method}:{path}",
                await cache_service.hash_get("metrics:request_count", f"{method}:{path}", default=0) + 1
            )

            # 记录状态码计数
            await cache_service.hash_set(
                "metrics:status_count",
                str(status_code),
                await cache_service.hash_get("metrics:status_count", str(status_code), default=0) + 1
            )

            # 更新平均响应时间
            current_avg = await cache_service.hash_get("metrics:avg_response_time", f"{method}:{path}", default=0.0)
            count = await cache_service.hash_get("metrics:request_count", f"{method}:{path}", default=1)
            new_avg = ((current_avg * (count - 1)) + process_time) / count
            await cache_service.hash_set("metrics:avg_response_time", f"{method}:{path}", new_avg)

        except Exception as e:
            logger.error(f"记录指标失败: {e}")


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)

        except Exception as e:
            logger.error(f"未处理的异常: {e}", exc_info=True)

            # 返回友好的错误响应
            return Response(
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "服务器内部错误"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                },
                status_code=500,
                headers={"Content-Type": "application/json"}
            )


def setup_middleware(app):
    """设置所有中间件"""
    # 注意：中间件的添加顺序很重要

    # 1. 错误处理中间件（最外层）
    app.add_middleware(ErrorHandlingMiddleware)

    # 2. 安全头中间件
    app.add_middleware(SecurityHeadersMiddleware)

    # 3. 限流中间件
    app.add_middleware(RateLimitingMiddleware, requests_per_minute=120)

    # 4. 性能监控中间件
    app.add_middleware(PerformanceMonitoringMiddleware)

    # 5. 指标收集中间件
    app.add_middleware(MetricsMiddleware)

    # 6. 缓存中间件
    app.add_middleware(CacheMiddleware, cache_ttl=300)

    # 7. 日志中间件（最内层）
    app.add_middleware(LoggingMiddleware)

    logger.info("所有中间件已设置完成")


__all__ = [
    "CacheMiddleware",
    "LoggingMiddleware",
    "PerformanceMonitoringMiddleware",
    "RateLimitingMiddleware",
    "SecurityHeadersMiddleware",
    "MetricsMiddleware",
    "ErrorHandlingMiddleware",
    "setup_middleware"
]