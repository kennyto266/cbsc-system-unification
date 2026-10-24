"""
API配置模块 - 管理API生态系统的配置设置
"""

import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings
    from pydantic import validator
except ImportError:
    from pydantic import BaseSettings, validator


class APISettings(BaseSettings):
    """API生态系统配置设置"""

    # API基本信息
    API_TITLE: str = "CBSC Trading Platform API"
    API_VERSION: str = "v1"
    API_DESCRIPTION: str = "Comprehensive RESTful API for CBSC Trading Platform"
    API_HOST: str = "localhost:3005"
    API_SCHEME: str = "https"

    # Svix Webhook配置
    SVIX_AUTH_TOKEN: Optional[str] = None
    SVIX_SERVER_URL: str = "http://localhost:8071"
    WEBHOOK_SECRET: Optional[str] = None

    # OAuth2配置
    OAUTH2_CLIENT_ID: Optional[str] = None
    OAUTH2_CLIENT_SECRET: Optional[str] = None

    # JWT配置
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # API密钥配置
    API_KEY_LENGTH: int = 32
    API_KEY_PREFIX: str = "cbs_"

    # 速率限制配置
    API_RATE_LIMIT: int = 100
    API_RATE_LIMIT_WINDOW: int = 60  # 秒

    # 开发者门户配置
    DEVELOPER_PORTAL_ENABLED: bool = True
    API_DOCS_URL: str = "/docs"
    DEVELOPER_PORTAL_URL: str = "/developers"

    # CORS配置
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]

    # API监控配置
    API_MONITORING_ENABLED: bool = True
    API_AUDIT_LOGGING: bool = True
    API_METRICS_ENABLED: bool = True

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        """解析CORS origins配置"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @validator("CORS_ALLOW_METHODS", pre=True)
    def assemble_cors_methods(cls, v):
        """解析CORS methods配置"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @validator("CORS_ALLOW_HEADERS", pre=True)
    def assemble_cors_headers(cls, v):
        """解析CORS headers配置"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @property
    def api_base_url(self) -> str:
        """获取API基础URL"""
        return f"{self.API_SCHEME}://{self.API_HOST}"

    @property
    def openapi_url(self) -> str:
        """获取OpenAPI文档URL"""
        return f"{self.api_base_url}/openapi.json"

    @property
    def svix_config(self) -> dict:
        """获取Svix配置"""
        return {
            "auth_token": self.SVIX_AUTH_TOKEN,
            "server_url": self.SVIX_SERVER_URL,
        }

    @property
    def jwt_config(self) -> dict:
        """获取JWT配置"""
        return {
            "secret_key": self.JWT_SECRET_KEY,
            "algorithm": self.JWT_ALGORITHM,
            "access_token_expire_minutes": self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": self.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
        }

    @property
    def rate_limit_config(self) -> dict:
        """获取速率限制配置"""
        return {
            "limit": self.API_RATE_LIMIT,
            "window": self.API_RATE_LIMIT_WINDOW,
        }

    @property
    def oauth2_config(self) -> dict:
        """获取OAuth2配置"""
        return {
            "client_id": self.OAUTH2_CLIENT_ID,
            "client_secret": self.OAUTH2_CLIENT_SECRET,
        }

    def get_cors_config(self) -> dict:
        """获取CORS配置"""
        return {
            "allow_origins": self.CORS_ORIGINS,
            "allow_credentials": self.CORS_ALLOW_CREDENTIALS,
            "allow_methods": self.CORS_ALLOW_METHODS,
            "allow_headers": self.CORS_ALLOW_HEADERS,
        }

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的环境变量


# 创建全局配置实例
settings = APISettings()


def get_api_settings() -> APISettings:
    """获取API配置设置"""
    return settings


def get_svix_config() -> dict:
    """获取Svix webhook配置"""
    return settings.svix_config


def get_jwt_config() -> dict:
    """获取JWT配置"""
    return settings.jwt_config


def get_rate_limit_config() -> dict:
    """获取速率限制配置"""
    return settings.rate_limit_config


def get_oauth2_config() -> dict:
    """获取OAuth2配置"""
    return settings.oauth2_config


def get_cors_config() -> dict:
    """获取CORS配置"""
    return settings.get_cors_config()


# 验证必要配置
def validate_config():
    """验证必要的配置项"""
    missing_configs = []

    if not settings.JWT_SECRET_KEY:
        missing_configs.append("JWT_SECRET_KEY")

    if not settings.SVIX_AUTH_TOKEN:
        missing_configs.append("SVIX_AUTH_TOKEN")

    if not settings.WEBHOOK_SECRET:
        missing_configs.append("WEBHOOK_SECRET")

    if missing_configs:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_configs)}")

    return True


if __name__ == "__main__":
    # 测试配置加载
    try:
        print(f"API配置加载成功:")
        print(f"  API标题: {settings.API_TITLE}")
        print(f"  API版本: {settings.API_VERSION}")
        print(f"  API基础URL: {settings.api_base_url}")
        print(f"  Svix服务器URL: {settings.SVIX_SERVER_URL}")
        print(f"  速率限制: {settings.API_RATE_LIMIT}/{settings.API_RATE_LIMIT_WINDOW}秒")
        print(f"  开发者门户: {'启用' if settings.DEVELOPER_PORTAL_ENABLED else '禁用'}")
        print(f"  CORS origins: {len(settings.CORS_ORIGINS)} 个")
        validate_config()
        print("  配置验证: 通过")
    except Exception as e:
        print(f"  配置验证失败: {e}")