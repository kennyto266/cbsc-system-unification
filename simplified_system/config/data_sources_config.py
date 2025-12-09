#!/usr/bin/env python3
"""
多數據源配置管理
Multi-Data Source Configuration Management

統一管理所有數據源的配置、監控和故障轉移策略
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class DataSourceType(Enum):
    """數據源類型"""
    STOCK_API = "stock_api"
    GOVERNMENT_API = "government_api"
    CACHE = "cache"
    FALLBACK = "fallback"

class FailoverStrategy(Enum):
    """故障轉移策略"""
    PRIORITY_BASED = "priority_based"
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    RANDOM = "random"

@dataclass
class RetryConfig:
    """重試配置"""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    backoff_multiplier: float = 2.0
    jitter: bool = True

@dataclass
class CacheConfig:
    """緩存配置"""
    memory_ttl: int = 300  # 5 minutes
    disk_ttl: int = 3600   # 1 hour
    redis_ttl: int = 7200  # 2 hours
    max_memory_size: int = 1000  # items
    max_disk_size: str = "1GB"
    compression: bool = True
    encryption: bool = False

@dataclass
class MonitoringConfig:
    """監控配置"""
    health_check_interval: int = 60  # seconds
    alert_thresholds: Dict[str, float] = None
    performance_metrics_retention: int = 168  # hours (1 week)
    auto_failover: bool = True
    failback_delay: int = 300  # seconds
    notification_channels: List[str] = None

    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "response_time_ms": 5000,
                "success_rate": 0.95,
                "data_quality_score": 0.7,
                "error_rate": 0.1
            }
        if self.notification_channels is None:
            self.notification_channels = ["log", "file"]

@dataclass
class RateLimitConfig:
    """速率限制配置"""
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 20
    concurrent_requests: int = 5

class DataSourcesConfiguration:
    """多數據源配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config/multi_data_sources.json"
        self.config_dir = Path(self.config_file).parent
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 默認配置
        self.retry_config = RetryConfig()
        self.cache_config = CacheConfig()
        self.monitoring_config = MonitoringConfig()
        self.failover_strategy = FailoverStrategy.PRIORITY_BASED

        # 數據源配置
        self.data_sources = self._initialize_default_sources()

        # 加載配置文件
        self.load_configuration()

        logger.info(f"Data sources configuration initialized from {self.config_file}")

    def _initialize_default_sources(self) -> Dict[str, Dict[str, Any]]:
        """初始化默認數據源配置"""
        return {
            "primary_central_api": {
                "name": "Primary Central API",
                "type": DataSourceType.STOCK_API.value,
                "url": "http://18.180.162.113:9191",
                "priority": 1,
                "enabled": True,
                "timeout": 30,
                "rate_limit": asdict(RateLimitConfig(
                    requests_per_minute=60,
                    requests_per_hour=1000,
                    burst_size=10
                )),
                "retry_config": asdict(RetryConfig(max_retries=3)),
                "required_headers": {
                    "User-Agent": "QuantSystem/2.0",
                    "Accept": "application/json"
                },
                "health_check": {
                    "endpoint": "/health",
                    "interval": 60,
                    "timeout": 10
                },
                "data_format": "json",
                "auth": {
                    "type": "none"
                }
            },

            "backup_central_api": {
                "name": "Backup Central API",
                "type": DataSourceType.STOCK_API.value,
                "url": "http://backup.central-api.com:9191",
                "priority": 2,
                "enabled": False,  # Disabled by default
                "timeout": 45,
                "rate_limit": asdict(RateLimitConfig(
                    requests_per_minute=30,
                    requests_per_hour=500,
                    burst_size=5
                )),
                "retry_config": asdict(RetryConfig(max_retries=2)),
                "required_headers": {
                    "User-Agent": "QuantSystem/2.0",
                    "Accept": "application/json"
                },
                "health_check": {
                    "endpoint": "/health",
                    "interval": 120,
                    "timeout": 15
                },
                "data_format": "json",
                "auth": {
                    "type": "none"
                }
            },

            "binance_api": {
                "name": "Binance API",
                "type": DataSourceType.STOCK_API.value,
                "url": "https://api.binance.com/api/v3",
                "priority": 3,
                "enabled": True,
                "timeout": 20,
                "rate_limit": asdict(RateLimitConfig(
                    requests_per_minute=1200,
                    requests_per_hour=100000,
                    burst_size=100
                )),
                "retry_config": asdict(RetryConfig(max_retries=2)),
                "required_headers": {
                    "User-Agent": "QuantSystem/2.0"
                },
                "health_check": {
                    "endpoint": "/ping",
                    "interval": 60,
                    "timeout": 5
                },
                "data_format": "json",
                "auth": {
                    "type": "none"
                }
            },

            "alpha_vantage": {
                "name": "Alpha Vantage",
                "type": DataSourceType.STOCK_API.value,
                "url": "https://www.alphavantage.co/query",
                "priority": 4,
                "enabled": True,
                "timeout": 60,
                "rate_limit": asdict(RateLimitConfig(
                    requests_per_minute=5,
                    requests_per_hour=500,
                    requests_per_day=5000,
                    burst_size=1
                )),
                "retry_config": asdict(RetryConfig(max_retries=1)),
                "required_headers": {
                    "User-Agent": "QuantSystem/2.0"
                },
                "health_check": {
                    "endpoint": None,  # No specific health endpoint
                    "interval": 300,
                    "timeout": 30
                },
                "data_format": "json",
                "auth": {
                    "type": "api_key",
                    "key_env_var": "ALPHA_VANTAGE_API_KEY"
                }
            },

            "hkma_hibor": {
                "name": "HKMA HIBOR Rates",
                "type": DataSourceType.GOVERNMENT_API.value,
                "url": "https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily",
                "priority": 1,
                "enabled": True,
                "timeout": 30,
                "rate_limit": asdict(RateLimitConfig(
                    requests_per_minute=60,
                    requests_per_hour=1000,
                    burst_size=10
                )),
                "retry_config": asdict(RetryConfig(max_retries=3)),
                "required_headers": {
                    "Accept": "application/json",
                    "User-Agent": "QuantSystem/2.0"
                },
                "health_check": {
                    "endpoint": None,
                    "interval": 300,
                    "timeout": 15
                },
                "data_format": "json",
                "auth": {
                    "type": "none"
                },
                "data_type": "hibor_rates",
                "priority": 1
            },

            "hkma_monetary_base": {
                "name": "HKMA Monetary Base",
                "type": DataSourceType.GOVERNMENT_API.value,
                "url": "https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base",
                "priority": 1,
                "enabled": True,
                "timeout": 30,
                "rate_limit": asdict(RateLimitConfig(
                    requests_per_minute=60,
                    requests_per_hour=1000,
                    burst_size=10
                )),
                "retry_config": asdict(RetryConfig(max_retries=3)),
                "required_headers": {
                    "Accept": "application/json",
                    "User-Agent": "QuantSystem/2.0"
                },
                "health_check": {
                    "endpoint": None,
                    "interval": 300,
                    "timeout": 15
                },
                "data_format": "json",
                "auth": {
                    "type": "none"
                },
                "data_type": "monetary_base",
                "priority": 1
            },

            "hkma_exchange_rate": {
                "name": "HKMA Exchange Rates",
                "type": DataSourceType.GOVERNMENT_API.value,
                "url": "https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily",
                "priority": 1,
                "enabled": True,
                "timeout": 30,
                "rate_limit": asdict(RateLimitConfig(
                    requests_per_minute=60,
                    requests_per_hour=1000,
                    burst_size=10
                )),
                "retry_config": asdict(RetryConfig(max_retries=3)),
                "required_headers": {
                    "Accept": "application/json",
                    "User-Agent": "QuantSystem/2.0"
                },
                "health_check": {
                    "endpoint": None,
                    "interval": 300,
                    "timeout": 15
                },
                "data_format": "json",
                "auth": {
                    "type": "none"
                },
                "data_type": "exchange_rates",
                "priority": 1
            },

            "redis_cache": {
                "name": "Redis Cache",
                "type": DataSourceType.CACHE.value,
                "url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                "priority": 1,
                "enabled": bool(os.getenv("REDIS_URL")),
                "timeout": 5,
                "rate_limit": asdict(RateLimitConfig(
                    requests_per_minute=1000,
                    requests_per_hour=100000,
                    burst_size=50
                )),
                "retry_config": asdict(RetryConfig(max_retries=2)),
                "auth": {
                    "type": "password",
                    "password_env_var": "REDIS_PASSWORD"
                }
            }
        }

    def load_configuration(self):
        """從文件加載配置"""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                # 更新數據源配置
                if "data_sources" in config_data:
                    self.data_sources.update(config_data["data_sources"])

                # 更新其他配置
                if "retry_config" in config_data:
                    self.retry_config = RetryConfig(**config_data["retry_config"])

                if "cache_config" in config_data:
                    self.cache_config = CacheConfig(**config_data["cache_config"])

                if "monitoring_config" in config_data:
                    self.monitoring_config = MonitoringConfig(**config_data["monitoring_config"])

                if "failover_strategy" in config_data:
                    self.failover_strategy = FailoverStrategy(config_data["failover_strategy"])

                logger.info(f"Configuration loaded from {self.config_file}")
            else:
                logger.info("Configuration file not found, using defaults")
                self.save_configuration()  # Save default configuration

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.warning("Using default configuration")

    def save_configuration(self):
        """保存配置到文件"""
        try:
            config_data = {
                "data_sources": self.data_sources,
                "retry_config": asdict(self.retry_config),
                "cache_config": asdict(self.cache_config),
                "monitoring_config": asdict(self.monitoring_config),
                "failover_strategy": self.failover_strategy.value
            }

            # 確保目錄存在
            Path(self.config_file).parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration saved to {self.config_file}")

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def get_data_source_config(self, name: str) -> Optional[Dict[str, Any]]:
        """獲取指定數據源的配置"""
        return self.data_sources.get(name)

    def get_enabled_sources(self) -> List[Dict[str, Any]]:
        """獲取所有啟用的數據源"""
        return [
            config for config in self.data_sources.values()
            if config.get("enabled", False)
        ]

    def get_sources_by_type(self, source_type: DataSourceType) -> List[Dict[str, Any]]:
        """根據類型獲取數據源"""
        return [
            config for config in self.data_sources.values()
            if config.get("type") == source_type.value and config.get("enabled", False)
        ]

    def get_sources_by_priority(self) -> List[Dict[str, Any]]:
        """按優先級排序獲取數據源"""
        enabled_sources = self.get_enabled_sources()
        return sorted(enabled_sources, key=lambda x: x.get("priority", 999))

    def update_data_source(self, name: str, updates: Dict[str, Any]):
        """更新數據源配置"""
        if name in self.data_sources:
            self.data_sources[name].update(updates)
            logger.info(f"Updated configuration for data source: {name}")
            self.save_configuration()
        else:
            logger.error(f"Data source not found: {name}")

    def enable_data_source(self, name: str):
        """啟用數據源"""
        self.update_data_source(name, {"enabled": True})

    def disable_data_source(self, name: str):
        """禁用數據源"""
        self.update_data_source(name, {"enabled": False})

    def add_data_source(self, name: str, config: Dict[str, Any]):
        """添加新的數據源"""
        self.data_sources[name] = config
        logger.info(f"Added new data source: {name}")
        self.save_configuration()

    def remove_data_source(self, name: str):
        """刪除數據源"""
        if name in self.data_sources:
            del self.data_sources[name]
            logger.info(f"Removed data source: {name}")
            self.save_configuration()
        else:
            logger.error(f"Data source not found: {name}")

    def validate_configuration(self) -> List[str]:
        """驗證配置的完整性"""
        errors = []

        for name, config in self.data_sources.items():
            # 檢查必填字段
            required_fields = ["name", "type", "url", "priority"]
            for field in required_fields:
                if field not in config:
                    errors.append(f"Data source {name}: Missing required field '{field}'")

            # 檢查URL格式
            if "url" in config:
                url = config["url"]
                if not (url.startswith("http://") or url.startswith("https://") or url.startswith("redis://")):
                    errors.append(f"Data source {name}: Invalid URL format")

            # 檢查API密鑰配置
            auth = config.get("auth", {})
            if auth.get("type") == "api_key":
                key_env_var = auth.get("key_env_var")
                if key_env_var and not os.getenv(key_env_var):
                    errors.append(f"Data source {name}: API key environment variable {key_env_var} not set")

        return errors

    def get_environment_overrides(self) -> Dict[str, Any]:
        """獲取環境變量覆蓋"""
        overrides = {}

        # Redis配置
        if os.getenv("REDIS_URL"):
            overrides["redis_cache"] = {
                "url": os.getenv("REDIS_URL"),
                "enabled": True
            }

        # API密鑰
        if os.getenv("ALPHA_VANTAGE_API_KEY"):
            overrides["alpha_vantage"] = {
                "auth": {
                    "type": "api_key",
                    "api_key": os.getenv("ALPHA_VANTAGE_API_KEY")
                },
                "enabled": True
            }

        # 禁用特定數據源
        disabled_sources = os.getenv("DISABLE_DATA_SOURCES", "").split(",")
        for source in disabled_sources:
            source = source.strip()
            if source in self.data_sources:
                overrides[source] = {"enabled": False}

        return overrides

    def apply_environment_overrides(self):
        """應用環境變量覆蓋"""
        overrides = self.get_environment_overrides()

        for source_name, updates in overrides.items():
            if source_name in self.data_sources:
                self.data_sources[source_name].update(updates)
                logger.info(f"Applied environment override for {source_name}")

    def get_cache_configuration(self) -> CacheConfig:
        """獲取緩存配置"""
        return self.cache_config

    def get_monitoring_configuration(self) -> MonitoringConfig:
        """獲取監控配置"""
        return self.monitoring_config

    def export_configuration(self) -> Dict[str, Any]:
        """導出完整配置"""
        return {
            "data_sources": self.data_sources,
            "retry_config": asdict(self.retry_config),
            "cache_config": asdict(self.cache_config),
            "monitoring_config": asdict(self.monitoring_config),
            "failover_strategy": self.failover_strategy.value,
            "environment_overrides": self.get_environment_overrides()
        }

# Global configuration instance
_config: Optional[DataSourcesConfiguration] = None

def get_data_sources_config(config_file: Optional[str] = None) -> DataSourcesConfiguration:
    """獲取全局數據源配置實例"""
    global _config
    if _config is None:
        _config = DataSourcesConfiguration(config_file)
        _config.apply_environment_overrides()
    return _config

def reload_configuration():
    """重新加載配置"""
    global _config
    _config = None
    return get_data_sources_config()