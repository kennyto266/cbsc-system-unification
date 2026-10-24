"""
配置设置
Configuration Settings

职责：
- 应用配置管理
- 环境变量处理
- 配置验证
"""

from typing import Optional, List
import os
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    app_name: str = "CBSC Strategy API"
    app_version: str = "2.0.0"
    debug: bool = False

    # API配置
    api_prefix: str = "/api/strategies"
    api_title: str = "CBSC策略管理API"
    api_description: str = "CBSC量化交易策略管理系统API"
    api_docs_url: str = "/docs"

    # 数据库配置
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/cbsc",
        env="DATABASE_URL"
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis配置
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    redis_max_connections: int = 100

    # 认证配置
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS配置
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080"
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]

    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 缓存配置
    cache_ttl_default: int = 300  # 5分钟
    cache_ttl_short: int = 60  # 1分钟
    cache_ttl_long: int = 3600  # 1小时

    # WebSocket配置
    websocket_heartbeat_interval: int = 30
    websocket_max_connections: int = 1000
    websocket_message_queue_size: int = 10000

    # 执行配置
    max_concurrent_executions: int = 10
    default_execution_timeout: int = 3600  # 1小时
    execution_cleanup_interval: int = 300  # 5分钟

    # 限流配置
    rate_limit_default: int = 100  # 每小时请求数
    rate_limit_window: int = 3600  # 1小时

    # 监控配置
    metrics_enabled: bool = True
    health_check_enabled: bool = True
    prometheus_metrics_path: str = "/metrics"

    # 特性开关
    feature_v2_api: bool = True
    feature_real_time_execution: bool = True
    feature_advanced_analytics: bool = True
    feature_websocket_notifications: bool = True

    # 环境配置
    environment: str = Field(default="development", env="ENVIRONMENT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    获取配置实例（单例模式）
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings():
    """
    重新加载配置
    """
    global _settings
    _settings = None