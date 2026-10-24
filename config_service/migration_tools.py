#!/usr/bin/env python3
"""
Configuration Migration Tools
配置遷移工具

DevOps Configuration Management Expert Implementation
"""

import os
import json
import yaml
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass

from client import ConfigClient, ConfigClientError

logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """遷移結果"""
    success: bool
    migrated_configs: int
    failed_configs: int
    errors: List[str]
    warnings: List[str]
    duration: float


class ConfigMigrator:
    """配置遷移器"""

    def __init__(self, client: ConfigClient):
        self.client = client

    async def migrate_from_json_file(self, file_path: str, environment: str = "development",
                                   service: str = "global", overwrite: bool = False) -> MigrationResult:
        """從JSON文件遷移配置"""
        start_time = datetime.now()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                configs_data = json.load(f)

            return await self._migrate_configs(configs_data, environment, service, overwrite, start_time)

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return MigrationResult(
                success=False,
                migrated_configs=0,
                failed_configs=0,
                errors=[f"Failed to load JSON file: {e}"],
                warnings=[],
                duration=duration
            )

    async def migrate_from_yaml_file(self, file_path: str, environment: str = "development",
                                   service: str = "global", overwrite: bool = False) -> MigrationResult:
        """從YAML文件遷移配置"""
        start_time = datetime.now()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                configs_data = yaml.safe_load(f)

            return await self._migrate_configs(configs_data, environment, service, overwrite, start_time)

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return MigrationResult(
                success=False,
                migrated_configs=0,
                failed_configs=0,
                errors=[f"Failed to load YAML file: {e}"],
                warnings=[],
                duration=duration
            )

    async def migrate_from_env_file(self, file_path: str, environment: str = "development",
                                  service: str = "global", overwrite: bool = False) -> MigrationResult:
        """從環境變量文件遷移配置"""
        start_time = datetime.now()

        try:
            configs_data = {}
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        configs_data[key] = value

            return await self._migrate_configs(configs_data, environment, service, overwrite, start_time)

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return MigrationResult(
                success=False,
                migrated_configs=0,
                failed_configs=0,
                errors=[f"Failed to load environment file: {e}"],
                warnings=[],
                duration=duration
            )

    async def migrate_from_dict(self, configs_data: Dict[str, Any], environment: str = "development",
                              service: str = "global", overwrite: bool = False) -> MigrationResult:
        """從字典遷移配置"""
        start_time = datetime.now()
        return await self._migrate_configs(configs_data, environment, service, overwrite, start_time)

    async def _migrate_configs(self, configs_data: Dict[str, Any], environment: str,
                             service: str, overwrite: bool, start_time: datetime) -> MigrationResult:
        """執行配置遷移"""
        migrated_count = 0
        failed_count = 0
        errors = []
        warnings = []

        # 將嵌套字典展平
        flattened_configs = self._flatten_dict(configs_data)

        for key, value in flattened_configs.items():
            try:
                # 檢查配置是否已存在
                if not overwrite:
                    try:
                        existing = await self.client.get_config(key, environment, service)
                        if existing:
                            warnings.append(f"Configuration {key} already exists, skipping")
                            continue
                    except ConfigClientError:
                        # 配置不存在，繼續創建
                        pass

                # 設置配置
                await self.client.set_config(
                    key=key,
                    value=value,
                    environment=environment,
                    service=service,
                    description=f"Migrated from configuration file on {datetime.now().isoformat()}"
                )

                migrated_count += 1
                logger.info(f"Migrated config: {key}")

            except Exception as e:
                failed_count += 1
                errors.append(f"Failed to migrate config {key}: {e}")
                logger.error(f"Failed to migrate config {key}: {e}")

        duration = (datetime.now() - start_time).total_seconds()
        success = failed_count == 0

        return MigrationResult(
            success=success,
            migrated_configs=migrated_count,
            failed_configs=failed_count,
            errors=errors,
            warnings=warnings,
            duration=duration
        )

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """展平嵌套字典"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


class ConfigExporter:
    """配置導出器"""

    def __init__(self, client: ConfigClient):
        self.client = client

    async def export_to_json_file(self, file_path: str, environment: str = None,
                                service: str = None, include_encrypted: bool = False) -> bool:
        """導出配置到JSON文件"""
        try:
            configs = await self.client.list_configs(environment, service)

            # 過濾加密配置（如果需要）
            if not include_encrypted:
                configs = [c for c in configs if not c["encrypted"]]

            # 將配置轉換為嵌套字典
            configs_dict = self._configs_to_nested_dict(configs)

            # 寫入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(configs_dict, f, indent=2, default=str, ensure_ascii=False)

            logger.info(f"Exported {len(configs)} configs to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export configs to JSON: {e}")
            return False

    async def export_to_yaml_file(self, file_path: str, environment: str = None,
                                service: str = None, include_encrypted: bool = False) -> bool:
        """導出配置到YAML文件"""
        try:
            configs = await self.client.list_configs(environment, service)

            # 過濾加密配置（如果需要）
            if not include_encrypted:
                configs = [c for c in configs if not c["encrypted"]]

            # 將配置轉換為嵌套字典
            configs_dict = self._configs_to_nested_dict(configs)

            # 寫入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(configs_dict, f, default_flow_style=False, allow_unicode=True)

            logger.info(f"Exported {len(configs)} configs to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export configs to YAML: {e}")
            return False

    async def export_to_env_file(self, file_path: str, environment: str = None,
                               service: str = None, include_encrypted: bool = False) -> bool:
        """導出配置到環境變量文件"""
        try:
            configs = await self.client.list_configs(environment, service)

            # 過濾加密配置（如果需要）
            if not include_encrypted:
                configs = [c for c in configs if not c["encrypted"]]

            # 寫入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Configuration Export - {datetime.now().isoformat()}\n")
                f.write(f"# Environment: {environment or 'all'}\n")
                f.write(f"# Service: {service or 'all'}\n\n")

                for config in configs:
                    key = config["key"]
                    value = str(config["value"])
                    f.write(f"{key}={value}\n")

            logger.info(f"Exported {len(configs)} configs to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export configs to ENV: {e}")
            return False

    def _configs_to_nested_dict(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """將配置列表轉換為嵌套字典"""
        result = {}

        for config in configs:
            key = config["key"]
            value = config["value"]

            # 將點分隔的鍵轉換為嵌套字典
            keys = key.split('.')
            current = result

            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]

            current[keys[-1]] = value

        return result


class ConfigValidator:
    """配置驗證器"""

    def __init__(self):
        self.validation_rules = self._load_validation_rules()

    def _load_validation_rules(self) -> Dict[str, Any]:
        """加載驗證規則"""
        # 這裡可以從配置文件加載驗證規則
        return {
            "key_patterns": [
                r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$",  # section.key format
                r"^[a-z][a-z0-9_]*$"                     # simple key format
            ],
            "value_types": ["string", "int", "float", "bool", "json", "yaml"],
            "constraints": {
                "timeout": {"min": 1, "max": 3600},
                "retry_attempts": {"min": 0, "max": 10},
                "memory_fraction": {"min": 0.1, "max": 1.0},
                "port": {"min": 1, "max": 65535}
            }
        }

    async def validate_config(self, key: str, value: Any, value_type: str = "auto") -> List[str]:
        """驗證單個配置"""
        errors = []

        # 檢查鍵格式
        import re
        key_valid = any(re.match(pattern, key) for pattern in self.validation_rules["key_patterns"])
        if not key_valid:
            errors.append(f"Invalid key format: {key}")

        # 自動檢測值類型
        if value_type == "auto":
            value_type = self._detect_value_type(value)

        # 檢查值類型
        if value_type not in self.validation_rules["value_types"]:
            errors.append(f"Invalid value type: {value_type}")

        # 檢查值約束
        constraint_errors = self._check_constraints(key, value)
        errors.extend(constraint_errors)

        return errors

    def _detect_value_type(self, value: Any) -> str:
        """自動檢測值類型"""
        if isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, dict) or isinstance(value, list):
            return "json"
        elif isinstance(value, str):
            try:
                json.loads(value)
                return "json"
            except:
                pass
        return "string"

    def _check_constraints(self, key: str, value: Any) -> List[str]:
        """檢查值約束"""
        errors = []

        # 檢查特定鍵的約束
        for constraint_key, constraint in self.validation_rules["constraints"].items():
            if constraint_key in key:
                if isinstance(value, (int, float)):
                    if "min" in constraint and value < constraint["min"]:
                        errors.append(f"Value {value} is below minimum {constraint['min']} for {key}")
                    if "max" in constraint and value > constraint["max"]:
                        errors.append(f"Value {value} is above maximum {constraint['max']} for {key}")

        return errors


class ConfigBackupManager:
    """配置備份管理器"""

    def __init__(self, client: ConfigClient, backup_dir: str = "backups"):
        self.client = client
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    async def create_backup(self, name: str = None, environment: str = None,
                          service: str = None) -> str:
        """創建配置備份"""
        if not name:
            name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_file = self.backup_dir / f"{name}.json"

        # 導出配置
        exporter = ConfigExporter(self.client)
        success = await exporter.export_to_json_file(str(backup_file), environment, service)

        if success:
            logger.info(f"Created backup: {backup_file}")
            return str(backup_file)
        else:
            raise Exception(f"Failed to create backup: {name}")

    async def restore_backup(self, backup_file: str, environment: str = "development",
                           service: str = "global", overwrite: bool = False) -> MigrationResult:
        """從備份恢復配置"""
        migrator = ConfigMigrator(self.client)
        return await migrator.migrate_from_json_file(backup_file, environment, service, overwrite)

    async def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有備份"""
        backups = []

        for backup_file in self.backup_dir.glob("*.json"):
            try:
                stat = backup_file.stat()
                backups.append({
                    "name": backup_file.stem,
                    "file_path": str(backup_file),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime, timezone.utc),
                    "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc)
                })
            except Exception as e:
                logger.error(f"Error reading backup file {backup_file}: {e}")

        # 按創建時間排序
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups

    async def delete_backup(self, name: str) -> bool:
        """刪除備份"""
        backup_file = self.backup_dir / f"{name}.json"
        try:
            backup_file.unlink()
            logger.info(f"Deleted backup: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete backup {name}: {e}")
            return False


# 便捷函數
async def migrate_configs_from_file(file_path: str, config_service_url: str = "http://localhost:8005",
                                  environment: str = "development", service: str = "global",
                                  overwrite: bool = False) -> MigrationResult:
    """從文件遷移配置的便捷函數"""
    async with ConfigClient(config_service_url) as client:
        migrator = ConfigMigrator(client)

        file_ext = Path(file_path).suffix.lower()
        if file_ext == '.json':
            return await migrator.migrate_from_json_file(file_path, environment, service, overwrite)
        elif file_ext in ['.yaml', '.yml']:
            return await migrator.migrate_from_yaml_file(file_path, environment, service, overwrite)
        elif file_ext == '.env':
            return await migrator.migrate_from_env_file(file_path, environment, service, overwrite)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")


# 使用示例
async def example_migration():
    """遷移使用示例"""

    async with ConfigClient() as client:
        # 從JSON文件遷移
        result = await migrate_configs_from_file(
            "configs.json",
            environment="production",
            service="analytics"
        )

        print(f"Migration completed: {result.success}")
        print(f"Migrated: {result.migrated_configs}")
        print(f"Failed: {result.failed_configs}")
        if result.errors:
            print(f"Errors: {result.errors}")


if __name__ == "__main__":
    asyncio.run(example_migration())