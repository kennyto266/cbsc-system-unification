"""
速率限制中间件 - API请求频率限制
"""

from fastapi import Request, HTTPException, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Dict, Optional, Tuple
import time
import logging
import asyncio
from collections import defaultdict, deque

# 导入配置
try:
    from config.api_config import get_rate_limit_config
except ImportError:
    # 为开发环境设置基本导入
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config.api_config import get_rate_limit_config

# 配置日志
logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""

    def __init__(self, app, calls: int = 100, period: int = 60):
        """
        初始化速率限制中间件

        Args:
            app: FastAPI应用实例
            calls: 时间窗口内允许的最大请求数
            period: 时间窗口（秒）
        """
        super().__init__(app)
        self.calls = calls
        self.period = period

        # 使用字典存储客户端请求记录
        # 结构: {client_key: deque([timestamp1, timestamp2, ...])}
        self.client_requests: Dict[str, deque] = defaultdict(lambda: deque())

        # 清理过期记录的间隔
        self.cleanup_interval = 300  # 5分钟
        self.last_cleanup = time.time()

        logger.info(f"速率限制中间件已初始化: {calls} 请求 / {period} 秒")

    async def dispatch(self, request: Request, call_next):
        """
        处理请求并应用速率限制

        Args:
            request: HTTP请求对象
            call_next: 下一个中间件或路由处理器

        Returns:
            HTTP响应对象
        """
        # 获取客户端标识符
        client_key = self._get_client_key(request)

        # 检查速率限制
        is_allowed, retry_after = self._check_rate_limit(client_key)

        if not is_allowed:
            logger.warning(f"速率限制触发: 客户端 {client_key} 超过限制")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"请求频率过高，请在 {retry_after} 秒后重试",
                    "retry_after": retry_after,
                    "limit": self.calls,
                    "window": self.period,
                    "timestamp": time.time()
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Window": str(self.period),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after)
                }
            )

        # 记录请求
        current_time = time.time()
        self.client_requests[client_key].append(current_time)

        # 定期清理过期记录
        self._cleanup_expired_records(current_time)

        # 获取剩余请求数
        remaining = max(0, self.calls - len(self.client_requests[client_key]))

        # 处理请求
        response = await call_next(request)

        # 添加速率限制响应头
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Window"] = str(self.period)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.period))

        return response

    def _get_client_key(self, request: Request) -> str:
        """
        获取客户端标识符

        Args:
            request: HTTP请求对象

        Returns:
            客户端标识符
        """
        # 优先使用API密钥
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"

        # 其次使用Authorization头
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # 使用JWT token的前几位作为标识
            token = auth_header[7:20]  # 取前13个字符
            return f"token:{token}"

        # 最后使用IP地址
        client_host = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # 使用第一个IP（真实客户端IP）
            client_host = forwarded_for.split(",")[0].strip()

        return f"ip:{client_host}"

    def _check_rate_limit(self, client_key: str) -> Tuple[bool, int]:
        """
        检查客户端是否超过速率限制

        Args:
            client_key: 客户端标识符

        Returns:
            (是否允许, 重试等待时间)
        """
        current_time = time.time()
        requests = self.client_requests[client_key]

        # 清理过期的请求记录
        cutoff_time = current_time - self.period
        while requests and requests[0] <= cutoff_time:
            requests.popleft()

        # 检查是否超过限制
        if len(requests) >= self.calls:
            # 计算最早请求的重试时间
            if requests:
                retry_after = int(requests[0] + self.period - current_time)
                return False, max(1, retry_after)
            else:
                return False, self.period

        return True, 0

    def _cleanup_expired_records(self, current_time: Optional[float] = None):
        """
        清理所有客户端的过期记录

        Args:
            current_time: 当前时间戳
        """
        if current_time is None:
            current_time = time.time()

        # 检查是否需要清理
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        cutoff_time = current_time - self.period * 2  # 清理2倍时间窗口前的记录
        cleaned_count = 0

        # 清理所有客户端的过期记录
        for client_key in list(self.client_requests.keys()):
            requests = self.client_requests[client_key]
            original_length = len(requests)

            while requests and requests[0] <= cutoff_time:
                requests.popleft()
                cleaned_count += 1

            # 如果客户端没有活跃请求，删除记录
            if not requests:
                del self.client_requests[client_key]

        self.last_cleanup = current_time

        if cleaned_count > 0:
            logger.info(f"速率限制中间件清理了 {cleaned_count} 条过期记录")


class DynamicRateLimitMiddleware(RateLimitMiddleware):
    """动态速率限制中间件 - 支持不同客户端不同的限制"""

    def __init__(self, app, default_calls: int = 100, default_period: int = 60):
        """
        初始化动态速率限制中间件

        Args:
            app: FastAPI应用实例
            default_calls: 默认最大请求数
            default_period: 默认时间窗口
        """
        super().__init__(app, default_calls, default_period)

        # 预定义的客户端限制规则
        self.custom_limits = {
            # API密钥前缀 -> (调用次数, 时间窗口)
            "cbs_premium_": (500, 60),  # 高级用户
            "cbs_enterprise_": (1000, 60),  # 企业用户
            "cbs_internal_": (5000, 60),  # 内部服务
        }

        # IP白名单（不受限制）
        self.whitelist_ips = [
            "127.0.0.1",  # 本地开发
            "localhost",
        ]

    def _get_client_limits(self, client_key: str) -> Tuple[int, int]:
        """
        获取客户端的速率限制配置

        Args:
            client_key: 客户端标识符

        Returns:
            (最大请求数, 时间窗口)
        """
        # 检查白名单
        if client_key.startswith("ip:") and client_key[3:] in self.whitelist_ips:
            return 10000, 60  # 白名单用户几乎不受限制

        # 检查自定义API密钥限制
        if client_key.startswith("api_key:"):
            api_key = client_key[8:]
            for prefix, (calls, period) in self.custom_limits.items():
                if api_key.startswith(prefix):
                    return calls, period

        # 返回默认限制
        return self.calls, self.period

    def _check_rate_limit(self, client_key: str) -> Tuple[bool, int]:
        """
        检查客户端是否超过速率限制（支持动态限制）

        Args:
            client_key: 客户端标识符

        Returns:
            (是否允许, 重试等待时间)
        """
        current_time = time.time()
        requests = self.client_requests[client_key]

        # 获取客户端特定的限制
        calls, period = self._get_client_limits(client_key)

        # 清理过期的请求记录
        cutoff_time = current_time - period
        while requests and requests[0] <= cutoff_time:
            requests.popleft()

        # 检查是否超过限制
        if len(requests) >= calls:
            # 计算最早请求的重试时间
            if requests:
                retry_after = int(requests[0] + period - current_time)
                return False, max(1, retry_after)
            else:
                return False, period

        return True, 0


def create_rate_limit_middleware(app, use_dynamic: bool = True, **kwargs):
    """
    创建速率限制中间件的工厂函数

    Args:
        app: FastAPI应用实例
        use_dynamic: 是否使用动态速率限制
        **kwargs: 其他配置参数

    Returns:
        速率限制中间件实例
    """
    # 优先使用传入的参数
    if 'calls' in kwargs and 'period' in kwargs:
        calls = kwargs["calls"]
        period = kwargs["period"]
        logger.info(f"使用传入的速率限制参数: {calls} 请求 / {period} 秒")
    else:
        try:
            # 从配置文件读取默认设置
            config = get_rate_limit_config()
            calls = kwargs.get("calls", config.get("limit", 100))
            period = kwargs.get("period", config.get("window", 60))
        except Exception as e:
            logger.warning(f"无法读取速率限制配置，使用默认值: {e}")
            calls = kwargs.get("calls", 100)
            period = kwargs.get("period", 60)

    if use_dynamic:
        return DynamicRateLimitMiddleware(app, calls, period)
    else:
        return RateLimitMiddleware(app, calls, period)


# 测试端点 - 用于验证速率限制功能
async def test_rate_limit_endpoint(request: Request):
    """
    测试速率限制的端点

    Args:
        request: HTTP请求对象

    Returns:
        测试响应
    """
    return {
        "message": "速率限制测试端点",
        "timestamp": time.time(),
        "client": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("User-Agent", "unknown")
    }


if __name__ == "__main__":
    # 测试速率限制中间件
    import uvicorn
    from fastapi import FastAPI

    # 创建测试应用
    test_app = FastAPI(title="速率限制测试")

    # 添加速率限制中间件
    test_app.add_middleware(create_rate_limit_middleware, calls=5, period=60)

    # 添加测试端点
    @test_app.get("/test-rate-limit")
    async def test_endpoint(request: Request):
        return await test_rate_limit_endpoint(request)

    @test_app.get("/api/v1/test-rate-limit")
    async def test_api_endpoint(request: Request):
        return await test_rate_limit_endpoint(request)

    # 启动测试服务器
    logger.info("启动速率限制测试服务器...")
    logger.info("测试地址: http://localhost:3004/api/v1/test-rate-limit")
    logger.info("速率限制: 5 请求 / 60 秒")

    uvicorn.run(
        test_app,
        host="0.0.0.0",
        port=3004,
        log_level="info"
    )