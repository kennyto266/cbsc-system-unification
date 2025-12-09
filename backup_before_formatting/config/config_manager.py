#!/usr/bin/env python3
"""
配置管理系統
負責管理用戶配置、系統設置和配置驗證
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: Union[str, Path] = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        # 配置文件路徑
        self.user_config_file = self.config_dir / "user_preferences.json"
        self.system_config_file = self.config_dir / "system_config.json"
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        # 配置模式
        self.config_mode = "production"  # production, development, testing

        # 初始化配置
        self.config = {}
        self.system_config = {}
        self._init_configs()

    def _init_configs(self):
        """初始化配置系統"""
        try:
            # 初始化系統配置
            self._init_system_config()

            # 初始化用戶配置
            self._init_user_config()

            # 合併配置
            self._merge_configs()

        except Exception as e:
            logger.error(f"配置初始化失敗: {e}")
            self._load_default_configs()

    def _init_system_config(self):
        """初始化系統配置"""
        self.default_system_config = {
            "system": {
                "version": "1.0.0",
                "debug_mode": False,
                "log_level": "INFO",
                "max_cache_size": 100,
                "auto_save_interval": 300
            },
            "data_sources": {
                "stock_api": {
                    "base_url": "http://18.180.162.113:9191",
                    "timeout": 30,
                    "max_retries": 3,
                    "endpoint": "/inst/getInst"
                },
                "government_data": {
                    "hibor_source": "simplified_system/src/api/government_data.py",
                    "hkma_base_url": "https://api.hkma.gov.hk",
                    "cache_duration": 300
                }
            },
            "performance": {
                "enable_gpu": True,
                "gpu_memory_limit": "8GB",
                "parallel_cores": "auto",
                "chunk_size": 1000
            },
            "backtesting": {
                "default_duration": 252,
                "commission": 0.001,
                "slippage": 0.0001,
                "risk_free_rate": 0.03
            },
            "ui": {
                "theme": "dark",
                "language": "zh-CN",
                "chart_type": "ascii",
                "table_format": "grid",
                "decimal_places": 2,
                "date_format": "%Y-%m-%d"
            }
        }

        # 加載或創建系統配置
        if self.system_config_file.exists():
            try:
                with open(self.system_config_file, 'r', encoding='utf-8') as f:
                    self.system_config = json.load(f)
                logger.info("系統配置加載成功")
            except Exception as e:
                logger.warning(f"系統配置文件損壞，使用默認配置: {e}")
                self.system_config = self.default_system_config.copy()
                self._save_system_config()
        else:
            self.system_config = self.default_system_config.copy()
            self._save_system_config()

    def _init_user_config(self):
        """初始化用戶配置"""
        self.default_user_config = {
            "trading": {
                "default_symbol": "0700.HK",
                "default_duration": 252,
                "favorite_symbols": ["0700.HK", "0941.HK", "1398.HK"],
                "auto_refresh": True,
                "refresh_interval": 60
            },
            "indicators": {
                "rsi": {"period": 14, "oversold": 30, "overbought": 70},
                "macd": {"fast": 12, "slow": 26, "signal": 9},
                "sma": {"short_period": 20, "long_period": 50},
                "bollinger": {"period": 20, "std_dev": 2},
                "kdj": {"k_period": 9, "d_period": 3, "j_period": 3}
            },
            "strategies": {
                "enabled": ["RSI_MEAN_REVERSION", "DUAL_MOVING_AVERAGE", "MACD_CROSSOVER"],
                "default_strategy": "RSI_MEAN_REVERSION",
                "risk_management": {
                    "max_position_size": 0.1,
                    "stop_loss": 0.05,
                    "take_profit": 0.15
                }
            },
            "export": {
                "default_format": "json",
                "auto_save_results": True,
                "output_directory": "results",
                "include_charts": True
            },
            "notifications": {
                "enable_telegram": False,
                "telegram_bot_token": "",
                "telegram_chat_id": "",
                "alert_threshold": 0.02
            },
            "ui_preferences": {
                "show_advanced_options": False,
                "compact_mode": False,
                "sound_enabled": True,
                "animation_enabled": True
            }
        }

        # 加載或創建用戶配置
        if self.user_config_file.exists():
            try:
                with open(self.user_config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info("用戶配置加載成功")
                # 驗證並更新配置
                self._validate_and_update_config()
            except Exception as e:
                logger.warning(f"用戶配置文件損壞，使用默認配置: {e}")
                self.config = self.default_user_config.copy()
                self._save_user_config()
        else:
            self.config = self.default_user_config.copy()
            self._save_user_config()

    def _merge_configs(self):
        """合併系統配置和用戶配置"""
        # 系統配置有最高優先級
        self.merged_config = self.system_config.copy()

        # 用戶配置覆蓋部分系統配置
        for key, value in self.config.items():
            if key in self.merged_config:
                if isinstance(self.merged_config[key], dict) and isinstance(value, dict):
                    self.merged_config[key].update(value)
                else:
                    self.merged_config[key] = value
            else:
                self.merged_config[key] = value

    def _validate_and_update_config(self):
        """驗證並更新用戶配置"""
        updated = False

        # 檢查缺失的配置項
        for section, settings in self.default_user_config.items():
            if section not in self.config:
                self.config[section] = settings
                updated = True
            elif isinstance(settings, dict):
                for key, value in settings.items():
                    if key not in self.config[section]:
                        self.config[section][key] = value
                        updated = True

        if updated:
            logger.info("用戶配置已更新")
            self._save_user_config()

    def get(self, key_path: str, default=None):
        """獲取配置值，支持點號分隔的路徑"""
        try:
            keys = key_path.split('.')
            value = self.merged_config

            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default

            return value
        except Exception:
            return default

    def set(self, key_path: str, value: Any):
        """設置配置值"""
        try:
            keys = key_path.split('.')
            config = self.config

            # 導航到目標位置
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]

            # 設置值
            config[keys[-1]] = value

            # 重新合併配置
            self._merge_configs()

            logger.info(f"配置已更新: {key_path} = {value}")
            return True

        except Exception as e:
            logger.error(f"設置配置失敗: {e}")
            return False

    def save_config(self):
        """保存用戶配置"""
        return self._save_user_config()

    def _save_user_config(self):
        """保存用戶配置到文件"""
        try:
            # 創建備份
            self._create_backup(self.user_config_file)

            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)

            logger.info("用戶配置保存成功")
            return True

        except Exception as e:
            logger.error(f"保存用戶配置失敗: {e}")
            return False

    def _save_system_config(self):
        """保存系統配置到文件"""
        try:
            with open(self.system_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.system_config, f, ensure_ascii=False, indent=2)

            logger.info("系統配置保存成功")
            return True

        except Exception as e:
            logger.error(f"保存系統配置失敗: {e}")
            return False

    def _create_backup(self, config_file: Path):
        """創建配置文件備份"""
        try:
            if config_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{config_file.stem}_{timestamp}{config_file.suffix}"
                backup_path = self.backup_dir / backup_name

                shutil.copy2(config_file, backup_path)

                # 清理舊備份（保留最近10個）
                self._cleanup_old_backups(config_file.stem)

                logger.debug(f"配置備份已創建: {backup_path}")

        except Exception as e:
            logger.warning(f"創建配置備份失敗: {e}")

    def _cleanup_old_backups(self, config_stem: str):
        """清理舊的配置備份"""
        try:
            backup_pattern = f"{config_stem}_*"
            backup_files = list(self.backup_dir.glob(f"{config_stem}_*.json"))

            # 按修改時間排序，保留最新的10個
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            for old_backup in backup_files[10:]:
                old_backup.unlink()
                logger.debug(f"已刪除舊備份: {old_backup}")

        except Exception as e:
            logger.warning(f"清理備份文件失敗: {e}")

    def reset_to_default(self, section: Optional[str] = None):
        """重置配置為默認值"""
        try:
            if section:
                if section in self.default_user_config:
                    self.config[section] = self.default_user_config[section].copy()
                    logger.info(f"配置節 '{section}' 已重置為默認值")
                    return True
                else:
                    logger.warning(f"配置節 '{section}' 不存在")
                    return False
            else:
                # 重置所有配置
                self.config = self.default_user_config.copy()
                logger.info("所有配置已重置為默認值")
                return True

        except Exception as e:
            logger.error(f"重置配置失敗: {e}")
            return False

    def export_config(self, export_path: Union[str, Path], include_system: bool = False):
        """導出配置到文件"""
        try:
            export_path = Path(export_path)
            export_data = {
                "export_time": datetime.now().isoformat(),
                "version": self.system_config.get("system", {}).get("version", "1.0.0")
            }

            if include_system:
                export_data["system_config"] = self.system_config
                export_data["user_config"] = self.config
            else:
                export_data["user_config"] = self.config

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"配置已導出到: {export_path}")
            return True

        except Exception as e:
            logger.error(f"導出配置失敗: {e}")
            return False

    def import_config(self, import_path: Union[str, Path], merge: bool = True):
        """從文件導入配置"""
        try:
            import_path = Path(import_path)

            if not import_path.exists():
                logger.error(f"配置文件不存在: {import_path}")
                return False

            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            if "user_config" in import_data:
                if merge:
                    # 合併導入的配置
                    self._deep_merge(self.config, import_data["user_config"])
                else:
                    # 完全替換配置
                    self.config = import_data["user_config"]

                self._merge_configs()
                self._save_user_config()
                logger.info(f"配置導入成功: {import_path}")
                return True
            else:
                logger.error("配置文件格式無效")
                return False

        except Exception as e:
            logger.error(f"導入配置失敗: {e}")
            return False

    def _deep_merge(self, base_dict: dict, merge_dict: dict):
        """深度合併字典"""
        for key, value in merge_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value

    def validate_config(self) -> List[str]:
        """驗證配置的有效性"""
        errors = []

        try:
            # 驗證交易配置
            if "trading" in self.config:
                trading = self.config["trading"]

                # 驗證股票代碼格式
                if "default_symbol" in trading:
                    symbol = trading["default_symbol"]
                    if not isinstance(symbol, str) or len(symbol) < 4:
                        errors.append("默認股票代碼格式無效")

                # 驗證時間範圍
                if "default_duration" in trading:
                    duration = trading["default_duration"]
                    if not isinstance(duration, int) or duration <= 0 or duration > 3650:
                        errors.append("默認時間範圍必須是1-3650之間的整數")

            # 驗證指標配置
            if "indicators" in self.config:
                indicators = self.config["indicators"]

                # RSI驗證
                if "rsi" in indicators:
                    rsi = indicators["rsi"]
                    if "period" in rsi:
                        period = rsi["period"]
                        if not isinstance(period, int) or period < 2 or period > 100:
                            errors.append("RSI週期必須是2-100之間的整數")

            # 驗證策略配置
            if "strategies" in self.config:
                strategies = self.config["strategies"]

                if "risk_management" in strategies:
                    risk = strategies["risk_management"]

                    # 驗證風險參數
                    for param in ["max_position_size", "stop_loss", "take_profit"]:
                        if param in risk:
                            value = risk[param]
                            if not isinstance(value, (int, float)) or value <= 0 or value > 1:
                                errors.append(f"風險參數 {param} 必須是0-1之間的數值")

            # 驗證通知配置
            if "notifications" in self.config:
                notifications = self.config["notifications"]

                if notifications.get("enable_telegram", False):
                    if not notifications.get("telegram_bot_token", ""):
                        errors.append("啟用Telegram通知需要設置Bot Token")
                    if not notifications.get("telegram_chat_id", ""):
                        errors.append("啟用Telegram通知需要設置Chat ID")

        except Exception as e:
            errors.append(f"配置驗證過程中發生錯誤: {e}")

        return errors

    def get_config_summary(self) -> Dict[str, Any]:
        """獲取配置摘要信息"""
        return {
            "config_version": self.system_config.get("system", {}).get("version", "1.0.0"),
            "user_config_exists": self.user_config_file.exists(),
            "system_config_exists": self.system_config_file.exists(),
            "last_backup": self._get_latest_backup_time(),
            "validation_errors": len(self.validate_config()),
            "config_sections": list(self.config.keys()),
            "favorite_symbols": self.get("trading.favorite_symbols", []),
            "default_symbol": self.get("trading.default_symbol", "N/A"),
            "theme": self.get("ui.theme", "dark"),
            "language": self.get("ui.language", "zh-CN")
        }

    def _get_latest_backup_time(self) -> Optional[str]:
        """獲取最新備份時間"""
        try:
            backup_files = list(self.backup_dir.glob("*.json"))
            if backup_files:
                latest_file = max(backup_files, key=lambda x: x.stat().st_mtime)
                return datetime.fromtimestamp(latest_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
        return None

    def _load_default_configs(self):
        """加載默認配置（緊急情況下使用）"""
        logger.warning("使用緊急默認配置")
        self.config = self.default_user_config.copy()
        self.system_config = self.default_system_config.copy()
        self._merge_configs()