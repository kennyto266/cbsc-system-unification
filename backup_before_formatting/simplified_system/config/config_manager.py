#!/usr/bin/env python3
"""
Simplified System - Configuration Manager
简化系统 - 配置管理器

统一的配置管理系统，支持环境变量、类型验证和热重载。
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

try:
    from pydantic import BaseSettings, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    # Fallback to basic configuration if Pydantic not available
    PYDANTIC_AVAILABLE = False
    BaseSettings = object

logger = logging.getLogger(__name__)


class DataSourceSettings:
    """数据源配置"""

    def __init__(self):
        self.stock_api = {
            "base_url": "http://18.180.162.113:9191",
            "timeout": 30,
            "endpoint": "/inst/getInst"
        }

        self.government_data = {
            "hibor_rates": {
                "base_url": "https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily",
                "timeout": 30,
                "priority": 1
            },
            "exchange_rates": {
                "base_url": "https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily",
                "timeout": 30,
                "priority": 1
            },
            "monetary_base": {
                "base_url": "https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base",
                "timeout": 30,
                "priority": 1
            }
        }

        # 数据缓存配置
        self.cache = {
            "timeout": 300,  # 5分钟
            "max_size": 1000,
            "data_storage_path": "data/government"
        }


class PerformanceSettings:
    """性能配置"""

    def __init__(self):
        self.vectorbt = {
            "chunk_size": 10000,
            "parallel_cores": "auto",  # 自动检测核心数
            "memory_limit": "8GB"
        }

        self.gpu = {
            "enabled": True,
            "auto_detect": True,
            "fallback_to_cpu": True,
            "memory_fraction": 0.8
        }

        self.caching = {
            "enabled": True,
            "indicator_cache_ttl": 1800,  # 30分钟
            "api_cache_ttl": 300,         # 5分钟
            "max_cache_size": "1GB"
        }

        self.optimization = {
            "strategy_parallel": True,
            "max_workers": 32,
            "chunk_size": 100
        }


class APISettings:
    """API配置"""

    def __init__(self):
        self.server = {
            "host": "0.0.0.0",
            "port": 8000,
            "debug": False,
            "reload": False
        }

        self.rate_limiting = {
            "enabled": True,
            "requests_per_minute": 100,
            "burst_size": 20
        }

        self.security = {
            "cors_enabled": True,
            "allowed_origins": ["*"],
            "api_key_required": False
        }


class SystemSettings:
    """系统配置"""

    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # 路径配置
        self.paths = {
            "data_root": "data",
            "cache_dir": "cache",
            "logs_dir": "logs",
            "temp_dir": "temp"
        }

        # 数据库配置
        self.database = {
            "url": "sqlite:///./simplified_system.db",
            "echo": False,
            "pool_size": 5
        }

        # 监控配置
        self.monitoring = {
            "enabled": True,
            "metrics_port": 9090,
            "health_check_interval": 60
        }


class ConfigManager:
    """配置管理器"""

    def __init__(self):
        self._config_dir = Path(__file__).parent
        self._environment = os.getenv("ENVIRONMENT", "development")

        # 初始化配置对象
        self._system = SystemSettings()
        self._data_source = DataSourceSettings()
        self._performance = PerformanceSettings()
        self._api = APISettings()

        # 加载环境特定配置
        self._load_environment_config()

        logger.info(f"Configuration initialized for environment: {self._environment}")

    def _load_environment_config(self):
        """加载环境特定配置"""
        config_file = self._config_dir / f"{self._environment}.json"

        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    env_config = json.load(f)

                self._apply_config_overrides(env_config)
                logger.info(f"Loaded environment configuration from {config_file}")

            except Exception as e:
                logger.warning(f"Failed to load environment config: {e}")

    def _apply_config_overrides(self, config: Dict[str, Any]):
        """应用配置覆盖"""
        if 'data_source' in config:
            self._update_nested_dict(self._data_source.__dict__, config['data_source'])

        if 'performance' in config:
            self._update_nested_dict(self._performance.__dict__, config['performance'])

        if 'api' in config:
            self._update_nested_dict(self._api.__dict__, config['api'])

        if 'system' in config:
            self._update_nested_dict(self._system.__dict__, config['system'])

    def _update_nested_dict(self, target: dict, source: dict):
        """递归更新嵌套字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_nested_dict(target[key], value)
            else:
                target[key] = value

    @property
    def system(self) -> SystemSettings:
        """获取系统配置"""
        return self._system

    @property
    def data_source(self) -> DataSourceSettings:
        """获取数据源配置"""
        return self._data_source

    @property
    def performance(self) -> PerformanceSettings:
        """获取性能配置"""
        return self._performance

    @property
    def api(self) -> APISettings:
        """获取API配置"""
        return self._api

    def reload(self):
        """重新加载配置"""
        logger.info("Reloading configuration...")
        self._load_environment_config()
        logger.info("Configuration reloaded successfully")

    def get_cache_path(self, name: str) -> Path:
        """获取缓存路径"""
        cache_dir = Path(self._system.paths["cache_dir"])
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / name

    def get_data_path(self, *parts: str) -> Path:
        """获取数据路径"""
        data_root = Path(self._system.paths["data_root"])
        data_root.mkdir(exist_ok=True)
        return data_root.joinpath(*parts)

    def get_log_path(self, name: str) -> Path:
        """获取日志路径"""
        logs_dir = Path(self._system.paths["logs_dir"])
        logs_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d")
        return logs_dir / f"{name}_{timestamp}.log"


# 全局配置实例
_config_manager = None

def get_config_manager() -> ConfigManager:
    """获取配置管理器单例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

# 便捷函数
def get_config() -> SystemSettings:
    """获取系统配置"""
    return get_config_manager().system

def get_data_source_config() -> DataSourceSettings:
    """获取数据源配置"""
    return get_config_manager().data_source

def get_performance_config() -> PerformanceSettings:
    """获取性能配置"""
    return get_config_manager().performance

def get_api_config() -> APISettings:
    """获取API配置"""
    return get_config_manager().api

def reload_config():
    """重新加载配置"""
    return get_config_manager().reload()


if __name__ == "__main__":
    # 测试配置系统
    print("Testing Simplified System Configuration Manager...")

    config = get_config_manager()

    print(f"Environment: {config.system.environment}")
    print(f"Debug: {config.system.debug}")
    print(f"Stock API Base URL: {config.data_source.stock_api['base_url']}")
    print(f"GPU Enabled: {config.performance.gpu['enabled']}")
    print(f"API Server Port: {config.api.server['port']}")

    # 测试路径生成
    cache_path = config.get_cache_path("test_cache")
    data_path = config.get_data_path("government", "hibor")
    log_path = config.get_log_path("system")

    print(f"Cache Path: {cache_path}")
    print(f"Data Path: {data_path}")
    print(f"Log Path: {log_path}")

    print("\n✅ Configuration manager test completed successfully!")