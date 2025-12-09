"""
中間件配置
港股量化交易系統 - 中間件管理

集中管理所有中間件的配置、順序和參數。

支持的中間件:
- CORS (跨域)
- GZip (壓縮)
- Session (會話)
- 認證
- 限流
- 日誌
- 監控
"""

import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中間件"""

    def __init__(self, app: FastAPI, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.call_history = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = int(time.time())

        # 清理過舊記錄
        if client_ip in self.call_history:
            self.call_history[client_ip] = [
                t for t in self.call_history[client_ip] if current_time - t < 60
            ]
        else:
            self.call_history[client_ip] = []

        # 檢查速率限制
        if len(self.call_history[client_ip]) >= self.calls_per_minute:
            logger.warning(f"速率限制觸發: {client_ip}")
            return Response(
                content=json.dumps({"error": "Rate limit exceeded"}),
                status_code=429,
                media_type="application / json",
            )

        # 記錄調用
        self.call_history[client_ip].append(current_time)

        # 處理請求
        response = await call_next(request)

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全標頭中間件"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 添加安全標頭
        response.headers["X - Content - Type - Options"] = "nosniff"
        response.headers["X - Frame - Options"] = "DENY"
        response.headers["X - XSS - Protection"] = "1; mode=block"
        response.headers["Strict - Transport - Security"] = (
            "max - age=31536000; includeSubDomains"
        )
        response.headers["Referrer - Policy"] = "strict - origin - when - cross - origin"
        response.headers["Content - Security - Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:;"
        )

        return response


# 中間件配置模板
MIDDLEWARE_TEMPLATES = {
    "cors": {
        "class": CORSMiddleware,
        "args": {
            "allow_origins": ["*"],  # 生產環境應該限制
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        },
        "required": False,
        "description": "跨域资源共享",
    },
    "gzip": {
        "class": GZipMiddleware,
        "args": {
            "minimum_size": 1000,
        },
        "required": True,
        "description": "GZIP壓縮",
    },
    "session": {
        "class": SessionMiddleware,
        "args": {
            "secret_key": "your - secret - key - change - in - production",
        },
        "required": False,
        "description": "會話管理",
    },
    "rate_limit": {
        "class": RateLimitMiddleware,
        "args": {
            "calls_per_minute": 100,
        },
        "required": False,
        "description": "速率限制",
    },
    "security_headers": {
        "class": SecurityHeadersMiddleware,
        "args": {},
        "required": True,
        "description": "安全標頭",
    },
    # 可以添加更多中間件...
    # "auth": {
    #     "class": AuthMiddleware,
    #     "args": {},
    #     "required": False,
    #     "description": "身份認證"
    # },
    # "logging": {
    #     "class": LoggingMiddleware,
    #     "args": {},
    #     "required": True,
    #     "description": "請求日誌"
    # },
    # "metrics": {
    #     "class": MetricsMiddleware,
    #     "args": {},
    #     "required": False,
    #     "description": "性能指標"
    # },
}


class MiddlewareConfig:
    """
    中間件配置管理

    統一管理所有中間件的添加、配置和順序。
    """

    def __init__(self, app: FastAPI):
        self.app = app
        self.middleware_order = [
            "cors",
            "gzip",
            "security_headers",
            "session",
            "rate_limit",
            # 其他自定義中間件應該在這裡添加
        ]

    def configure_from_template(self, template_name: str):
        """
        從模板配置中間件

        Args:
            template_name: 模板名稱 (dev / test / prod)
        """
        if template_name not in MIDDLEWARE_TEMPLATES:
            raise ValueError(f"不支持的模板: {template_name}")

        # 根據環境調整配置
        if template_name == "dev":
            self._apply_dev_config()
        elif template_name == "prod":
            self._apply_prod_config()
        else:
            self._apply_default_config()

    def _apply_dev_config(self):
        """應用開發環境配置"""
        # 開發環境更寬鬆的CORS
        self.configure_middleware("cors", allow_origins=["*"])
        self.configure_middleware("session", secret_key="dev - secret")
        self.configure_middleware("rate_limit", calls_per_minute=1000)  # 更高限制

    def _apply_prod_config(self):
        """應用生產環境配置"""
        # 生產環境更嚴格的安全配置
        self.configure_middleware("cors", allow_origins=["https://yourdomain.com"])
        self.configure_middleware("session", secret_key="prod - secret")
        self.configure_middleware("rate_limit", calls_per_minute=60)  # 更低限制

    def _apply_default_config(self):
        """應用默認配置"""
        # 使用模板中的默認配置
        pass

    def configure_middleware(self, middleware_type: str, **kwargs):
        """
        配置特定中間件

        Args:
            middleware_type: 中間件類型
            **kwargs: 配置參數
        """
        if middleware_type not in MIDDLEWARE_TEMPLATES:
            raise ValueError(f"不支持的中間件: {middleware_type}")

        template = MIDDLEWARE_TEMPLATES[middleware_type]

        # 合併參數
        config = {**template["args"], **kwargs}

        # 添加中間件到應用
        if middleware_type == "cors":
            self.app.add_middleware(CORSMiddleware, **config)
        elif middleware_type == "gzip":
            self.app.add_middleware(GZipMiddleware, **config)
        elif middleware_type == "session":
            self.app.add_middleware(SessionMiddleware, **config)
        elif middleware_type == "rate_limit":
            self.app.add_middleware(RateLimitMiddleware, **config)
        elif middleware_type == "security_headers":
            self.app.add_middleware(SecurityHeadersMiddleware, **config)
        else:
            logger.warning(f"未實現的中間件類型: {middleware_type}")

        logger.info(f"✅ 已配置中間件: {middleware_type}")

    def apply_all_middleware(self, profile: str = "default"):
        """
        應用所有中間件

        Args:
            profile: 配置模板 (default / dev / prod)
        """
        # 應用配置模板
        self.configure_from_template(profile)

        # 按順序添加所有中間件
        for middleware_type in self.middleware_order:
            if middleware_type in MIDDLEWARE_TEMPLATES:
                template = MIDDLEWARE_TEMPLATES[middleware_type]
                if template["required"] or profile != "default":
                    self.configure_middleware(middleware_type)

        print("\n📊 中間件配置完成:")
        print(f"   模板: {profile}")
        print(f"   中間件數量: {len(self.middleware_order)}")

    def get_middleware_info(self) -> Dict[str, Any]:
        """
        獲取中間件信息

        Returns:
            中間件信息字典
        """
        return {
            "total_middleware": len(MIDDLEWARE_TEMPLATES),
            "required_middleware": len(
                [m for m in MIDDLEWARE_TEMPLATES.values() if m["required"]]
            ),
            "optional_middleware": len(
                [m for m in MIDDLEWARE_TEMPLATES.values() if not m["required"]]
            ),
            "middleware_list": list(MIDDLEWARE_TEMPLATES.keys()),
            "middleware_order": self.middleware_order,
        }


def setup_middleware(app: FastAPI, profile: str = "default"):
    """
    便利函數：設置中間件

    Args:
        app: FastAPI應用實例
        profile: 配置模板
    """
    config = MiddlewareConfig(app)
    config.apply_all_middleware(profile)
    return config


if __name__ == "__main__":
    # 測試配置
    print("=" * 60)
    print("中間件配置驗證")
    print("=" * 60)

    from fastapi import FastAPI

    app = FastAPI()
    config = MiddlewareConfig(app)

    info = config.get_middleware_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
