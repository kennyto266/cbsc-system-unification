#!/usr/bin/env python3
"""
配置管理器 - 简化版
Configuration Manager - Simplified Edition

统一的配置管理，支持环境变量和配置文件

Author: Claude Code Assistant
Created: 2025-11-29
Version: 1.0.0
"""

import os
import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

@dataclass
class DataConfig:
    """数据配置"""
    stock_api_base: str = "http://18.180.162.113:9191"
    stock_timeout: int = 30
    hibor_api_base: str = "https://api.hkma.gov.hk/public/market-data-and-statistics"
    gov_timeout: int = 30
    cache_timeout: int = 300

@dataclass
class BacktestConfig:
    """回测配置"""
    initial_cash: float = 10000.0
    commission: float = 0.001
    slippage: float = 0.0005
    risk_free_rate: float = 0.03

@dataclass
class OptimizationConfig:
    """优化配置"""
    max_workers: int = 4
    max_iterations: int = 1000
    timeout: float = 300.0
    objective: str = "sharpe_ratio"

@dataclass
class SystemConfig:
    """系统配置"""
    log_level: str = "INFO"
    log_file: str = "quantitative_trading_system.log"
    debug_mode: bool = False

class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file or "config.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        # 默认配置
        default_config = {
            "data": asdict(DataConfig()),
            "backtest": asdict(BacktestConfig()),
            "optimization": asdict(OptimizationConfig()),
            "system": asdict(SystemConfig())
        }

        # 从文件加载配置
        file_config = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                logger.info(f"已加载配置文件: {self.config_file}")
            except Exception as e:
                logger.warning(f"配置文件加载失败: {e}")

        # 从环境变量加载配置
        env_config = self._load_from_env()

        # 合并配置 (优先级: 环境变量 > 配置文件 > 默认配置)
        merged_config = self._merge_configs(default_config, file_config, env_config)

        return merged_config

    def _load_from_env(self) -> Dict[str, Any]:
        """从环境变量加载配置"""
        env_config = {}

        # 数据配置
        if os.getenv("STOCK_API_BASE"):
            env_config["data"] = env_config.get("data", {})
            env_config["data"]["stock_api_base"] = os.getenv("STOCK_API_BASE")

        if os.getenv("LOG_LEVEL"):
            env_config["system"] = env_config.get("system", {})
            env_config["system"]["log_level"] = os.getenv("LOG_LEVEL")

        return env_config

    def _merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """合并多个配置字典"""
        merged = {}

        for config in configs:
            for key, value in config.items():
                if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key].update(value)
                else:
                    merged[key] = value.copy() if isinstance(value, dict) else value

        return merged

    def get_data_config(self) -> DataConfig:
        """获取数据配置"""
        return DataConfig(**self.config.get("data", {}))

    def get_backtest_config(self) -> BacktestConfig:
        """获取回测配置"""
        return BacktestConfig(**self.config.get("backtest", {}))

    def get_optimization_config(self) -> OptimizationConfig:
        """获取优化配置"""
        return OptimizationConfig(**self.config.get("optimization", {}))

    def get_system_config(self) -> SystemConfig:
        """获取系统配置"""
        return SystemConfig(**self.config.get("system", {}))

    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已保存到: {self.config_file}")
        except Exception as e:
            logger.error(f"配置保存失败: {e}")

    def update_config(self, section: str, key: str, value: Any):
        """更新配置"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def get_config_value(self, section: str, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(section, {}).get(key, default)


# 全局配置实例
_config_manager = None

def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """获取配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    return _config_manager

def get_data_config() -> DataConfig:
    """获取数据配置"""
    return get_config_manager().get_data_config()

def get_backtest_config() -> BacktestConfig:
    """获取回测配置"""
    return get_config_manager().get_backtest_config()