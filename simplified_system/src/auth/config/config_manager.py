#!/usr / bin / env python3
"""
Configuration Manager
配置管理器

Dynamic configuration management with hot - reload capabilities
支持热重载的动态配置管理
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import yaml

# Optional watchdog import for hot - reload functionality
try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None
    logging.warning("Watchdog not available, hot - reload functionality disabled")

# Setup logging
logger = logging.getLogger(__name__)


class ConfigChangeHandler(
    FileSystemEventHandler if FileSystemEventHandler is not None else object
):
    """文件变更处理器"""

    def __init__(self, config_manager: "ConfigManager", file_path: Path):
        self.config_manager = config_manager
        self.file_path = file_path

    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory and Path(event.src_path) == self.file_path:
            logger.info(f"Configuration file {self.file_path} modified, reloading...")
            asyncio.create_task(self.config_manager._reload_config())


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，支持 JSON 和 YAML 格式
        """
        self.config_path = Path(config_path) if config_path else None
        self.config: Dict[str, Any] = {}
        self.observers: List[Observer] = []
        self.change_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.hot_reload_enabled = True
        self.default_config = self._get_default_config()

        # 加载配置
        if self.config_path and self.config_path.exists():
            self._load_config()
            self._setup_file_watcher()
        else:
            self.config = self.default_config.copy()
            logger.warning("No config file found, using default configuration")

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "version": "1.0.0",
            "authenticity_manager": {
                "max_history_size": 1000,
                "default_timeout": 30.0,
                "parallel_execution": True,
                "enable_caching": True,
            },
            "verifiers": {
                "digital_signature": {
                    "enabled": True,
                    "priority": 100,
                    "config": {
                        "require_signature": True,
                        "trusted_sources": ["hkma.gov.hk", "data.gov.hk"],
                        "signature_algorithms": ["RSA - 256", "ECDSA"],
                    },
                },
                "blockchain_verification": {
                    "enabled": False,
                    "priority": 90,
                    "config": {
                        "network": "ethereum",
                        "contract_address": None,
                        "gas_limit": 100000,
                    },
                },
                "statistical_analysis": {
                    "enabled": True,
                    "priority": 80,
                    "config": {
                        "outlier_detection": True,
                        "confidence_threshold": 0.95,
                        "min_sample_size": 30,
                    },
                },
                "domain_validation": {
                    "enabled": True,
                    "priority": 70,
                    "config": {
                        "trusted_domains": ["*.gov.hk", "*.hkma.gov.hk"],
                        "require_https": True,
                        "certificate_validation": True,
                    },
                },
                "data_integrity": {
                    "enabled": True,
                    "priority": 60,
                    "config": {
                        "hash_algorithm": "SHA256",
                        "require_checksum": True,
                        "corruption_detection": True,
                    },
                },
            },
            "rules_engine": {
                "enabled": True,
                "rule_files": ["rules / authenticity_rules.yaml"],
                "execution_timeout": 60.0,
                "max_rules_per_execution": 100,
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": None,
                "max_size_mb": 100,
                "backup_count": 5,
            },
            "cache": {
                "enabled": True,
                "type": "memory",
                "ttl_seconds": 3600,
                "max_size": 1000,
            },
        }

    def _load_config(self):
        """加载配置文件"""
        try:
            if not self.config_path or not self.config_path.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                self.config = self.default_config.copy()
                return

            with open(self.config_path, "r", encoding="utf - 8") as f:
                if self.config_path.suffix.lower() in [".yaml", ".yml"]:
                    loaded_config = yaml.safe_load(f)
                elif self.config_path.suffix.lower() == ".json":
                    loaded_config = json.load(f)
                else:
                    raise ValueError(
                        f"Unsupported config file format: {self.config_path.suffix}"
                    )

            # 合并默认配置和加载的配置
            self.config = self._merge_configs(self.default_config, loaded_config)
            logger.info(f"Configuration loaded from {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            logger.info("Using default configuration")
            self.config = self.default_config.copy()

    def _merge_configs(
        self, default: Dict[str, Any], loaded: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并配置"""
        result = default.copy()

        for key, value in loaded.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _setup_file_watcher(self):
        """设置文件监控"""
        if not self.hot_reload_enabled or not self.config_path:
            return

        if not WATCHDOG_AVAILABLE:
            logger.warning(
                "File watching not available - install watchdog package for hot - reload functionality"
            )
            return

        try:
            observer = Observer()
            event_handler = ConfigChangeHandler(self, self.config_path)
            observer.schedule(
                event_handler, str(self.config_path.parent), recursive = False
            )
            observer.start()
            self.observers.append(observer)
            logger.info(f"File watcher setup for {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to setup file watcher: {e}")

    async def _reload_config(self):
        """重新加载配置"""
        self.config.copy()
        self._load_config()

        # 通知变更回调
        for callback in self.change_callbacks:
            try:
                callback(self.config)
            except Exception as e:
                logger.error(f"Error in config change callback: {e}")

        logger.info("Configuration reloaded")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点分隔的嵌套键
            default: 默认值

        Returns:
            Any: 配置值
        """
        keys = key.split(".")
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any, persist: bool = False) -> bool:
        """
        设置配置值

        Args:
            key: 配置键，支持点分隔的嵌套键
            value: 配置值
            persist: 是否持久化到文件

        Returns:
            bool: 设置是否成功
        """
        try:
            keys = key.split(".")
            config = self.config

            # 导航到目标位置
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]

            # 设置值
            config[keys[-1]] = value

            # 持久化到文件
            if persist and self.config_path:
                self._save_config()

            logger.info(f"Configuration updated: {key} = {value}")
            return True

        except Exception as e:
            logger.error(f"Failed to set configuration {key}: {e}")
            return False

    def _save_config(self):
        """保存配置到文件"""
        try:
            if not self.config_path:
                return

            # 确保目录存在
            self.config_path.parent.mkdir(parents = True, exist_ok = True)

            with open(self.config_path, "w", encoding="utf - 8") as f:
                if self.config_path.suffix.lower() in [".yaml", ".yml"]:
                    yaml.dump(
                        self.config, f, default_flow_style = False, allow_unicode = True
                    )
                elif self.config_path.suffix.lower() == ".json":
                    json.dump(self.config, f, indent = 2, ensure_ascii = False)

            logger.info(f"Configuration saved to {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to save config to {self.config_path}: {e}")

    def get_verifier_config(self, verifier_type: str) -> Dict[str, Any]:
        """
        获取验证器配置

        Args:
            verifier_type: 验证器类型

        Returns:
            Dict[str, Any]: 验证器配置
        """
        return self.get(f"verifiers.{verifier_type}", {})

    def is_verifier_enabled(self, verifier_type: str) -> bool:
        """
        检查验证器是否启用

        Args:
            verifier_type: 验证器类型

        Returns:
            bool: 是否启用
        """
        return self.get(f"verifiers.{verifier_type}.enabled", False)

    def get_enabled_verifiers(self) -> List[str]:
        """获取启用的验证器列表"""
        enabled = []
        verifiers = self.get("verifiers", {})

        for verifier_type, config in verifiers.items():
            if config.get("enabled", False):
                enabled.append(verifier_type)

        return enabled

    def update_verifier_config(
        self, verifier_type: str, config: Dict[str, Any], persist: bool = False
    ) -> bool:
        """
        更新验证器配置

        Args:
            verifier_type: 验证器类型
            config: 新配置
            persist: 是否持久化

        Returns:
            bool: 更新是否成功
        """
        return self.set(f"verifiers.{verifier_type}", config, persist)

    def add_change_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        添加配置变更回调

        Args:
            callback: 回调函数，接收新配置作为参数
        """
        self.change_callbacks.append(callback)

    def remove_change_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        移除配置变更回调

        Args:
            callback: 要移除的回调函数
        """
        if callback in self.change_callbacks:
            self.change_callbacks.remove(callback)

    def enable_hot_reload(self, enabled: bool = True):
        """
        启用 / 禁用热重载

        Args:
            enabled: 是否启用
        """
        self.hot_reload_enabled = enabled

        if enabled and self.config_path:
            self._setup_file_watcher()
        else:
            self._stop_file_watchers()

    def _stop_file_watchers(self):
        """停止文件监控"""
        for observer in self.observers:
            observer.stop()
            observer.join()
        self.observers.clear()

    def reload(self):
        """手动重新加载配置"""
        if self.config_path and self.config_path.exists():
            asyncio.create_task(self._reload_config())

    def export_config(
        self, export_path: Union[str, Path], format: str = "yaml"
    ) -> bool:
        """
        导出配置

        Args:
            export_path: 导出路径
            format: 导出格式 ('yaml' 或 'json')

        Returns:
            bool: 导出是否成功
        """
        try:
            export_path = Path(export_path)
            export_path.parent.mkdir(parents = True, exist_ok = True)

            with open(export_path, "w", encoding="utf - 8") as f:
                if format.lower() == "yaml":
                    yaml.dump(
                        self.config, f, default_flow_style = False, allow_unicode = True
                    )
                elif format.lower() == "json":
                    json.dump(self.config, f, indent = 2, ensure_ascii = False)
                else:
                    raise ValueError(f"Unsupported export format: {format}")

            logger.info(f"Configuration exported to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export config: {e}")
            return False

    def get_all_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config.copy()

    def validate_config(self) -> Dict[str, Any]:
        """
        验证配置完整性

        Returns:
            Dict[str, Any]: 验证结果
        """
        issues = []
        warnings = []

        # 检查必需的配置项
        required_keys = ["authenticity_manager", "verifiers", "rules_engine"]

        for key in required_keys:
            if key not in self.config:
                issues.append(f"Missing required configuration section: {key}")

        # 检查验证器配置
        verifiers = self.get("verifiers", {})
        if not verifiers:
            warnings.append("No verifiers configured")

        for vtype, config in verifiers.items():
            if not isinstance(config, dict):
                issues.append(f"Invalid verifier configuration for {vtype}")
                continue

            if "enabled" not in config:
                warnings.append(f"Verifier {vtype} missing 'enabled' flag")

            if config.get("enabled") and "priority" not in config:
                warnings.append(f"Enabled verifier {vtype} missing priority")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "total_verifiers": len(verifiers),
            "enabled_verifiers": len(self.get_enabled_verifiers()),
        }

    async def cleanup(self):
        """清理资源"""
        logger.info("Cleaning up ConfigManager")
        self._stop_file_watchers()
        self.change_callbacks.clear()
