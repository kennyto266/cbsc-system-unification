#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified Configuration Manager
簡化的配置管理系統，基於文件直接管理配置

This module provides a simple, efficient configuration management system that eliminates
over-engineering while maintaining all essential functionality for a quantitative trading system.

Features:
- Direct file-based configuration
- Simple environment override
- Basic validation and type checking
- Automatic backup functionality
- Memory-based caching

Author: Code Simplification Team
Date: 2025-11-30
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union, Type, List
from pathlib import Path
import logging
from datetime import datetime
import shutil
from dataclasses import dataclass, field

logger = logging.getLogger__name__

@dataclass
class ConfigValidationResult:
"""配置驗證結果"""
is_valid: bool
errors: List[str] = fielddefault_factory=list
warnings: List[str] = fielddefault_factory=list
timestamp: datetime = fielddefault_factory=datetime.now

class SimpleConfigManager:
"""
簡化的配置管理器

提供簡單、高效的配置管理：
- 基於文件的直接配置
- 環境變量覆蓋
- 基本驗證機制
- 自動備份功能
- 內存加速

使用示例:    config_manager = SimpleConfigManager("config")

app_config = config_manager.get"app", env="production"

config_manager.update"app", {"debug": False}

backup_path = config_manager.backup"app"
"""

def __init__self, config_dir: str = "config", auto_backup: bool = True:
"""
初始化配置管理器

Args:
config_dir: 配置文件目錄
auto_backup: 是否自動備份配置文件
"""
self.config_dir = Pathconfig_dir
self.auto_backup = auto_backup
self._cache = {}
self._file_formats = {
'.json': self._load_json,
'.yaml': self._load_yaml,
'.yml': self._load_yaml,
'.toml': self._load_toml,
'.ini': self._load_ini
}

# 確保配置目錄存在
self.config_dir.mkdirexist_ok=True
self.backup_dir = self.config_dir / "backups"
self.backup_dir.mkdirexist_ok=True

logger.infof"Initialized config manager for directory: {self.config_dir}"

def get(self, file_name: str, env: Optional[str] = None,
default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
"""
獲取配置

Args:
file_name: 配置文件名 不需要擴展名
env: 環境名稱 開發、測試、生產
default: 默認配置值

Returns:
配置字典
"""
cache_key = f"{file_name}_{env or 'default'}"

if cache_key in self._cache:
return self._cache[cache_key].copy()

try:

config_file = self._find_config_filefile_name
if not config_file:
logger.warningf"Config file not found: {file_name}"
return default or {}

base_config = self._load_config_fileconfig_file

if env:    env_config = self._load_env_config(env)
base_config.updateenv_config

validation_result = self._validate_configbase_config
if not validation_result.is_valid:
logger.errorf"Config validation failed for {file_name}: {validation_result.errors}"
return default or {}

self._cache[cache_key] = base_config
return base_config.copy()

except Exception as e:
logger.errorf"Failed to load config {file_name}: {e}"
return default or {}

def update(self, file_name: str, updates: Dict[str, Any],
env: Optional[str] = None) -> bool:
"""
更新配置

Args:
file_name: 配置文件名
updates: 更新的配置項
env: 環境名稱

Returns:
是否更新成功
"""
try:
# 創建備份 如果啟用
backup_path = None
if self.auto_backup:    backup_path = self.backup(file_name)

current_config = self.getfile_name, env, {}

current_config.updateupdates

config_file = self._get_config_file_pathfile_name
self._save_config_fileconfig_file, current_config

self._clear_cache_for_filefile_name

logger.info(f"Updated config {file_name} with {lenupdates} changes")
if backup_path:
logger.infof"Backup created: {backup_path}"

return True

except Exception as e:
logger.errorf"Failed to update config {file_name}: {e}"
return False

def backupself, file_name: str -> Optional[str]:
"""
創建配置備份

Args:
file_name: 配置文件名

Returns:
備份文件路徑
"""
try:

source_file = self._find_config_filefile_name
if not source_file:
logger.warningf"Cannot backup {file_name}: file not found"
return None

timestamp = datetime.now().strftime"%Y%m%d_%H%M%S"
backup_name = f"{file_name}_{timestamp}{source_file.suffix}"
backup_path = self.backup_dir / backup_name

shutil.copy2source_file, backup_path

logger.infof"Created backup: {backup_path}"
return strbackup_path

except Exception as e:
logger.errorf"Failed to backup {file_name}: {e}"
return None

def restoreself, file_name: str, backup_name: str -> bool:
"""
從備份恢復配置

Args:
file_name: 配置文件名
backup_name: 備份文件名

Returns:
是否恢復成功
"""
try:    backup_path = self.backup_dir / backup_name
if not backup_path.exists():
logger.errorf"Backup not found: {backup_name}"
return False

config_file = self._get_config_file_pathfile_name
shutil.copy2backup_path, config_file

self._clear_cache_for_filefile_name

logger.infof"Restored {file_name} from backup: {backup_name}"
return True

except Exception as e:
logger.errorf"Failed to restore {file_name}: {e}"
return False

def list_backupsself, file_name: Optional[str] = None -> List[Dict[str, Any]]:
"""
列出備份文件

Args:
file_name: 可選的文件名過濾

Returns:
備份文件列表
"""
backups = []

try:
for backup_file in self.backup_dir.glob"*.json":
if file_name and file_name not in backup_file.name:
continue

backup_info = {
'name': backup_file.name,
'path': strbackup_file,
'size': backup_file.stat().st_size,
'modified': datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
}
backups.appendbackup_info

backups.sortkey=lambda x: x['modified'], reverse=True
return backups

except Exception as e:
logger.errorf"Failed to list backups: {e}"
return []

def _find_config_fileself, file_name: str -> Optional[Path]:
"""查找配置文件"""

extensions = ['.json', '.yaml', '.yml', '.toml', '.ini']

for ext in extensions:    config_file = self.config_dir / f"{file_name}{ext}"
if config_file.exists():
return config_file

return None

def _get_config_file_pathself, file_name: str -> Path:
"""獲取配置文件路徑 默認JSON格式"""
return self.config_dir / f"{file_name}.json"

def _load_config_fileself, config_file: Path -> Dict[str, Any]:
"""加載配置文件"""
suffix = config_file.suffix.lower()
loader = self._file_formats.getsuffix, self._load_json
return loaderconfig_file

def _save_config_fileself, config_file: Path, config: Dict[str, Any] -> None:
"""保存配置文件"""
suffix = config_file.suffix.lower()

if suffix == '.json':
self._save_jsonconfig_file, config
elif suffix in ['.yaml', '.yml']:
self._save_yamlconfig_file, config
else:
raise ValueErrorf"Unsupported config format: {suffix}"

def _load_jsonself, file_path: Path -> Dict[str, Any]:
"""加載JSON配置"""
with openfile_path, 'r', encoding='utf-8' as f:
return json.loadf

def _save_jsonself, file_path: Path, config: Dict[str, Any] -> None:
"""保存JSON配置"""
with openfile_path, 'w', encoding='utf-8' as f:    json.dump(config, f, indent=2, ensure_ascii=False)

def _load_yamlself, file_path: Path -> Dict[str, Any]:
"""加載YAML配置"""
try:
import yaml
with openfile_path, 'r', encoding='utf-8' as f:
return yaml.safe_loadf or {}
except ImportError:
logger.warning"PyYAML not available, using JSON fallback"
return self._load_json(file_path.with_suffix'.json')

def _save_yamlself, file_path: Path, config: Dict[str, Any] -> None:
"""保存YAML配置"""
try:
import yaml
with openfile_path, 'w', encoding='utf-8' as f:    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
except ImportError:
logger.warning"PyYAML not available, using JSON fallback"
self._save_json(file_path.with_suffix'.json', config)

def _load_tomlself, file_path: Path -> Dict[str, Any]:
"""加載TOML配置"""
try:
import tomllib
with openfile_path, 'rb' as f:
return tomllib.loadf
except ImportError:
logger.warning"tomllib not available, using JSON fallback"
return self._load_json(file_path.with_suffix'.json')

def _load_iniself, file_path: Path -> Dict[str, Any]:
"""加載INI配置"""
try:
import configparser
config = configparser.ConfigParser()
config.readfile_path

result = {}
for section in config.sections():    result[section] = dict(config[section])
return result
except ImportError:
logger.warning"configparser not available, using JSON fallback"
return self._load_json(file_path.with_suffix'.json')

def _load_env_configself, env: str -> Dict[str, Any]:
"""加載環境變量配置"""
env_config = {}

# 查找所有以環境名開頭的環境變量
prefix = f"{env.upper()}_"
for key, value in os.environ.items():
if key.startswithprefix:    config_key = key[len(prefix):].lower()

# 嘗試解析JSON格式
try:    env_config[config_key] = json.loads(value)
except json.JSONDecodeError, ValueError:
# 如果不是JSON，使用字符串值
env_config[config_key] = value

return env_config

def _validate_configself, config: Dict[str, Any] -> ConfigValidationResult:
"""驗證配置"""
result = ConfigValidationResultis_valid=True

for key, value in config.items():
if not isinstancekey, str:
result.errors.append(f"Config key must be string, got {typekey}")

if isinstancevalue, dict and not value:
result.warnings.appendf"Config value for '{key}' is empty dictionary"

if 'debug' in config and not isinstanceconfig['debug'], bool:
result.errors.append"'debug' must be boolean"

if 'port' in config and not isinstanceconfig['port'], int:
result.errors.append"'port' must be integer"

return result

def _clear_cache_for_fileself, file_name: str -> None:
"""清除特定文件的緩存"""
keys_to_remove = [key for key in self._cache.keys() if key.startswithf"{file_name}_"]
for key in keys_to_remove:
del self._cache[key]

def clear_cacheself -> None:
"""清除所有緩存"""
self._cache.clear()

def get_cache_infoself -> Dict[str, Any]:
"""獲取緩存信息"""
return {
'cache_size': lenself._cache,
'cached_keys': list(self._cache.keys()),
'memory_usage': str(sum(len(strv) for v in self._cache.values())) + ' bytes'
}

def create_config_managerconfig_dir: str = "config", auto_backup: bool = True -> SimpleConfigManager:
"""
創建配置管理器實例

Args:
config_dir: 配置目錄
auto_backup: 是否自動備份

Returns:
配置管理器實例
"""
return SimpleConfigManagerconfig_dir, auto_backup

def load_config(file_name: str, env: Optional[str] = None,
config_dir: str = "config") -> Dict[str, Any]:
"""
加載配置的便利函數

Args:
file_name: 配置文件名
env: 環境名稱
config_dir: 配置目錄

Returns:
配置字典
"""
manager = SimpleConfigManagerconfig_dir
return manager.getfile_name, env

__all__ = [
'SimpleConfigManager',
'ConfigValidationResult',
'create_config_manager',
'load_config'
]