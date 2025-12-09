"""
港股量化交易 AI Agent 系统核心模块

这个模块包含了系统的核心功能，包括：
- 配置管理
- 日志系统
- 基础工具类
- 系统常量
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict

from pydantic import Field

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class SystemConfig(BaseSettings):
    """系统配置类"""

    # 系统基础配置
    app_name: str = "港股量化交易AI Agent系统"
    app_version: str = "1.0.0"
    debug: bool = False

    # 数据库配置
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432 / hk_quant_db",
        env="DATABASE_URL",
    )

    # Redis配置
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")

    # 港股数据源配置
    hk_data_source: str = Field(default="yfinance", env="HK_DATA_SOURCE")
    data_update_interval: int = Field(default=60, env="DATA_UPDATE_INTERVAL")

    # Agent配置
    max_concurrent_agents: int = Field(default=10, env="MAX_CONCURRENT_AGENTS")
    agent_heartbeat_interval: int = Field(default=30, env="AGENT_HEARTBEAT_INTERVAL")
    update_interval: int = Field(default=5, env="UPDATE_INTERVAL")

    # 交易配置
    trading_enabled: bool = Field(default=False, env="TRADING_ENABLED")
    max_position_size: float = Field(default=1000000.0, env="MAX_POSITION_SIZE")
    risk_limit: float = Field(default=0.02, env="RISK_LIMIT")

    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs / hk_quant_system.log", env="LOG_FILE")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略額外的環境變量


class SystemConstants:
    """系统常量"""

    # Agent类型
    AGENT_TYPES = [
        "quant_analyst",  # 量化分析师
        "quant_trader",  # 量化交易员
        "portfolio_manager",  # 投资组合经理
        "risk_analyst",  # 风险分析师
        "data_scientist",  # 数据科学家
        "quant_engineer",  # 量化工程师
        "research_analyst",  # 研究分析师
    ]

    # Agent状态
    AGENT_STATUS = {
        "IDLE": "idle",
        "RUNNING": "running",
        "STOPPED": "stopped",
        "ERROR": "error",
        "MAINTENANCE": "maintenance",
    }

    # 消息类型
    MESSAGE_TYPES = {
        "HEARTBEAT": "heartbeat",
        "CONTROL": "control",
        "DATA": "data",
        "ALERT": "alert",
        "STATUS": "status",
    }

    # 默认配置
    DEFAULT_CONFIG = {
        "max_agents": 10,
        "heartbeat_interval": 30,
        "data_update_interval": 60,
        "log_level": "INFO",
    }


def setup_logging(config: SystemConfig = None):
    """设置日志配置"""
    if config is None:
        config = SystemConfig()

    # 创建日志目录
    log_dir = Path(config.log_file).parent
    log_dir.mkdir(exist_ok=True)

    # 配置日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 设置日志级别
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)

    # 配置日志处理器
    handlers = [
        logging.StreamHandler(),  # 控制台输出
        logging.FileHandler(config.log_file, encoding="utf - 8"),  # 文件输出
    ]

    # 应用配置
    logging.basicConfig(level=log_level, format=log_format, handlers=handlers)

    return logging.getLogger("hk_quant_system")


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def get_config_path() -> Path:
    """获取配置文件路径"""
    return get_project_root() / "config"


def get_logs_path() -> Path:
    """获取日志目录路径"""
    return get_project_root() / "logs"


# 导出主要类和函数
__all__ = [
    "SystemConfig",
    "SystemConstants",
    "setup_logging",
    "get_project_root",
    "get_config_path",
    "get_logs_path",
]
