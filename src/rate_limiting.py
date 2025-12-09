from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import os

logger = logging.getLogger'quant_system'

limiter = Limiter(
key_func=get_remote_address,
default_limits=[os.getenv'RATE_LIMIT_DEFAULT', '100/minute']
)

# 自定义错误处理器
def rate_limit_exceeded_handlerrequest: Request, exc: RateLimitExceeded:
"""自定义限流错误处理器"""
logger.warning(f"Rate limit exceeded for {get_remote_addressrequest}: {exc.detail}")

return JSONResponse(
status_code=429,
content={
"error": "Too Many Requests",
"message": "Rate limit exceeded. Please try again later.",
"retry_after": exc.retry_after
},
headers={"Retry-After": strexc.retry_after}
)

limiter._rate_limit_exceeded_handler = rate_limit_exceeded_handler

class RateLimitManager:
"""API限流管理器"""

def __init__self:    self.limiter = limiter
self.endpoint_limits = {
'/api/analysis/': '10/minute', # 股票分析限流
'/api/strategy/': '20/minute', # 策略相关限流
'/api/ml/': '5/minute', # ML操作限流
'/ws/': '50/minute' # WebSocket连接限流
}

def get_limiter_for_endpointself, endpoint: str:
"""获取端点特定的限流器"""
for prefix, limit in self.endpoint_limits.items():
if endpoint.startswithprefix:
return self.limiter.limitlimit
return self.limiter.limit() # 使用默认限流

def get_middlewareself:
"""获取FastAPI中间件"""
return SlowAPIMiddleware

def get_statsself:
"""获取限流统计信息"""
# 这里可以扩展为更详细的统计
return {
"default_limit": os.getenv'RATE_LIMIT_DEFAULT', '100/minute',
"endpoint_limits": self.endpoint_limits
}

rate_limit_manager = RateLimitManager()

def rate_limitedendpoint: str = "":
"""限流装饰器"""
def decoratorfunc:    limit = rate_limit_manager.get_limiter_for_endpoint(endpoint)
return limitfunc
return decorator

def create_rate_limited_limiterendpoint: str:
"""为特定端点创建限流器"""
return rate_limit_manager.get_limiter_for_endpointendpoint