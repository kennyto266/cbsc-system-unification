"""
策略管理Dashboard - 核心模块

提供系统配置、日志和基础功能。
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any
from pydantic import Field

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class SystemConfig(BaseSettings):
    """系统配置类"""

    app_name: str = "策略管理Dashboard"
    app_version: str = "1.0.0"
    debug: bool = False

    # 数据库配置
    database_url: str = Field(
        default="sqlite:///./strategy_dashboard.db",
        env="DATABASE_URL"
    )

    # Redis配置
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")

    # 数据源配置
    hk_data_source: str = Field(default="yfinance", env="HK_DATA_SOURCE")
    data_update_interval: int = Field(default=60, env="DATA_UPDATE_INTERVAL")

    # Dashboard配置
    max_concurrent_strategies: int = Field(default=10, env="MAX_CONCURRENT_STRATEGIES")
    update_interval: int = Field(default=5, env="UPDATE_INTERVAL")
    dashboard_port: int = Field(default=3003, env="DASHBOARD_PORT")

    # 交易配置
    trading_enabled: bool = Field(default=False, env="TRADING_ENABLED")
    max_position_size: float = Field(default=1000000.0, env="MAX_POSITION_SIZE")
    risk_limit: float = Field(default=0.02, env="RISK_LIMIT")

    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/strategy_dashboard.log", env="LOG_FILE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 允许额外字段忽略

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_logging()

    def _setup_logging(self):
        """设置日志配置"""
        # 创建日志目录
        log_dir = Path(self.log_file).parent
        log_dir.mkdir(exist_ok=True)

        # 配置日志
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return {
            "url": self.database_url,
            "echo": self.debug
        }

    def get_redis_config(self) -> Dict[str, Any]:
        """获取Redis配置"""
        return {
            "host": self.redis_host,
            "port": self.redis_port,
            "password": self.redis_password if self.redis_password else None,
            "decode_responses": True
        }

    def get_trading_config(self) -> Dict[str, Any]:
        """获取交易配置"""
        return {
            "enabled": self.trading_enabled,
            "max_position_size": self.max_position_size,
            "risk_limit": self.risk_limit
        }


# 创建全局配置实例
config = SystemConfig()

# 导出常用组件
__all__ = [
    "SystemConfig",
    "config"
]