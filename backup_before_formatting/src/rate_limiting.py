import logging
import os

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

logger = logging.getLogger("quant_system")

# 创建限流器实例
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[os.getenv("RATE_LIMIT_DEFAULT", "100 / minute")],
)


# 自定义错误处理器
def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """自定义限流错误处理器"""
    logger.warning(
        f"Rate limit exceeded for {get_remote_address(request)}: {exc.detail}"
    )

    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": "Rate limit exceeded. Please try again later.",
            "retry_after": exc.retry_after,
        },
        headers={"Retry - After": str(exc.retry_after)},
    )


# 注册错误处理器
limiter._rate_limit_exceeded_handler = rate_limit_exceeded_handler


class RateLimitManager:
    """API限流管理器"""

    def __init__(self):
        self.limiter = limiter
        self.endpoint_limits = {
            "/api / analysis/": "10 / minute",  # 股票分析限流
            "/api / strategy/": "20 / minute",  # 策略相关限流
            "/api / ml/": "5 / minute",  # ML操作限流
            "/ws/": "50 / minute",  # WebSocket连接限流
        }

    def get_limiter_for_endpoint(self, endpoint: str):
        """获取端点特定的限流器"""
        for prefix, limit in self.endpoint_limits.items():
            if endpoint.startswith(prefix):
                return self.limiter.limit(limit)
        return self.limiter.limit()  # 使用默认限流

    def get_middleware(self):
        """获取FastAPI中间件"""
        return SlowAPIMiddleware

    def get_stats(self):
        """获取限流统计信息"""
        # 这里可以扩展为更详细的统计
        return {
            "default_limit": os.getenv("RATE_LIMIT_DEFAULT", "100 / minute"),
            "endpoint_limits": self.endpoint_limits,
        }


# 全局实例
rate_limit_manager = RateLimitManager()


# 便捷装饰器
def rate_limited(endpoint: str = ""):
    """限流装饰器"""

    def decorator(func):
        limit = rate_limit_manager.get_limiter_for_endpoint(endpoint)
        return limit(func)

    return decorator


def create_rate_limited_limiter(endpoint: str):
    """为特定端点创建限流器"""
    return rate_limit_manager.get_limiter_for_endpoint(endpoint)
