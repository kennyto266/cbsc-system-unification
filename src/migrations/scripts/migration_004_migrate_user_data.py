"""
用戶數據遷移腳本

遷移系統配置、審計日誌和用戶相關數據到統一模型。
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.connection import db_manager
from ...models import User, Role, UserRole, SystemConfig, AuditLog, DataSchema
from ..migration_script import MigrationScript

logger = logging.getLogger(__name__)

class MigrateUserDataMigration(MigrationScript):
    """用戶數據遷移腳本"""

    def __init__(self):
        super().__init__(
            version="004",
            name="migrate_user_data",
            description="遷移CBSC系統配置、審計日誌和用戶數據到統一模型",
            author="Data Migration System"
        )
        self.data_sources = {
            "env_files": self._find_env_files(),
            "config_files": self._find_config_files(),
            "log_files": self._find_log_files(),
            "system_files": self._find_system_files()
        }

    def _find_env_files(self) -> List[str]:
        """查找環境配置文件"""
        env_files = []
        if os.path.exists('.env'):
            env_files.append('.env')
        if os.path.exists('.env.backup'):
            env_files.append('.env.backup')
        return env_files

    def _find_config_files(self) -> List[str]:
        """查找配置文件"""
        patterns = [
            "*.json",
            "config/**/*.json",
            "src/config/**/*.py"
        ]
        files = []

        for pattern in patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.is_file() and file_path.stat().st_size > 100:
                    files.append(str(file_path))

        return files

    def _find_log_files(self) -> List[str]:
        """查找日誌文件"""
        patterns = [
            "*.log",
            "logs/**/*.log"
        ]
        files = []

        for pattern in patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.is_file() and file_path.stat().st_size > 100:
                    files.append(str(file_path))

        return files

    def _find_system_files(self) -> List[str]:
        """查找系統文件"""
        files = []
        system_files = [
            "init_db.py",
            "database.py",
            "requirements.txt"
        ]

        for file_path in system_files:
            if os.path.exists(file_path):
                files.append(file_path)

        return files

    def get_up_sql(self) -> str:
        """獲取升級SQL語句"""
        return "-- This migration uses Python logic for data migration"

    def get_down_sql(self) -> str:
        """獲取回滾SQL語句"""
        return """
        DELETE FROM audit_logs WHERE user_id IN (
            SELECT id FROM users WHERE metadata->>'migration_source' IS NOT NULL
        );
        DELETE FROM user_roles WHERE user_id IN (
            SELECT id FROM users WHERE metadata->>'migration_source' IS NOT NULL
        );
        DELETE FROM users WHERE metadata->>'migration_source' IS NOT NULL;
        DELETE FROM system_config WHERE config_key LIKE 'migration_%';
        """

    async def execute_migration(self, session: AsyncSession) -> Dict[str, Any]:
        """執行數據遷移"""
        result = {
            "success": True,
            "users_created": 0,
            "roles_created": 0,
            "system_configs_migrated": 0,
            "audit_logs_created": 0,
            "data_schemas_created": 0,
            "errors": [],
            "migration_details": {}
        }

        try:
            # 1. 創建默認用戶和角色
            user_role_result = await self._create_default_users_and_roles(session)
            result.update(user_role_result)

            # 2. 遷移系統配置
            config_result = await self._migrate_system_configs(session)
            result.update(config_result)

            # 3. 遷移審計日誌
            audit_result = await self._migrate_audit_logs(session)
            result.update(audit_result)

            # 4. 創建數據模式記錄
            schema_result = await self._create_data_schemas(session)
            result.update(schema_result)

            await session.commit()
            logger.info(f"User data migration completed: {result}")

        except Exception as e:
            await session.rollback()
            result["success"] = False
            result["errors"].append(f"Migration failed: {str(e)}")
            logger.error(f"User data migration failed: {e}")

        return result

    async def _create_default_users_and_roles(self, session: AsyncSession) -> Dict[str, Any]:
        """創建默認用戶和角色"""
        result = {
            "users_created": 0,
            "roles_created": 0,
            "errors": []
        }

        try:
            # 1. 創建默認角色
            default_roles = [
                {
                    "name": "super_admin",
                    "display_name": "超級管理員",
                    "description": "系統超級管理員，擁有所有權限",
                    "is_system_role": True,
                    "permissions": [
                        "user.create", "user.read", "user.update", "user.delete",
                        "strategy.create", "strategy.read", "strategy.update", "strategy.delete",
                        "portfolio.create", "portfolio.read", "portfolio.update", "portfolio.delete",
                        "system.config", "system.audit", "system.monitor",
                        "data.import", "data.export", "data.analyze"
                    ]
                },
                {
                    "name": "trader",
                    "display_name": "交易員",
                    "description": "專業交易員，可以管理策略和投資組合",
                    "is_system_role": True,
                    "permissions": [
                        "strategy.create", "strategy.read", "strategy.update",
                        "portfolio.create", "portfolio.read", "portfolio.update",
                        "data.read", "data.analyze"
                    ]
                },
                {
                    "name": "analyst",
                    "display_name": "分析師",
                    "description": "數據分析師，可以查看和分析數據",
                    "is_system_role": True,
                    "permissions": [
                        "data.read", "data.analyze", "strategy.read", "portfolio.read"
                    ]
                },
                {
                    "name": "viewer",
                    "display_name": "查看者",
                    "description": "只讀用戶，只能查看公開信息",
                    "is_system_role": True,
                    "permissions": [
                        "data.read", "strategy.read"
                    ]
                }
            ]

            for role_data in default_roles:
                try:
                    # 檢查角色是否已存在
                    existing_role = await session.execute(
                        select(Role).where(Role.name == role_data["name"])
                    )
                    if not existing_role.scalar_one_or_none():
                        role = Role(
                            name=role_data["name"],
                            display_name=role_data["display_name"],
                            description=role_data["description"],
                            is_system_role=role_data["is_system_role"],
                            permissions=role_data["permissions"],
                            metadata={"auto_created": True, "migration_date": datetime.now().isoformat()}
                        )
                        session.add(role)
                        result["roles_created"] += 1
                        logger.info(f"Created role: {role_data['name']}")
                except Exception as e:
                    result["errors"].append(f"Failed to create role {role_data['name']}: {str(e)}")

            # 2. 創建默認用戶
            default_users = [
                {
                    "username": "admin",
                    "email": "admin@cbsc.system",
                    "first_name": "System",
                    "last_name": "Administrator",
                    "role": "super_admin",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "username": "trader",
                    "email": "trader@cbsc.system",
                    "first_name": "Professional",
                    "last_name": "Trader",
                    "role": "trader",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "username": "analyst",
                    "email": "analyst@cbsc.system",
                    "first_name": "Data",
                    "last_name": "Analyst",
                    "role": "analyst",
                    "is_active": True,
                    "is_verified": True
                }
            ]

            for user_data in default_users:
                try:
                    # 檢查用戶是否已存在
                    existing_user = await session.execute(
                        select(User).where(User.email == user_data["email"])
                    )
                    if not existing_user.scalar_one_or_none():
                        user = User(
                            username=user_data["username"],
                            email=user_data["email"],
                            password_hash="migration_placeholder_needs_reset",
                            first_name=user_data["first_name"],
                            last_name=user_data["last_name"],
                            is_active=user_data["is_active"],
                            is_verified=user_data["is_verified"],
                            metadata={
                                "migration_source": "default_users",
                                "migration_date": datetime.now().isoformat(),
                                "password_reset_required": True
                            }
                        )
                        session.add(user)
                        await session.flush()  # 獲取用戶ID

                        # 分配角色
                        role = await session.execute(
                            select(Role).where(Role.name == user_data["role"])
                        )
                        role_obj = role.scalar_one_or_none()
                        if role_obj:
                            user_role = UserRole(
                                user_id=user.id,
                                role_id=role_obj.id,
                                metadata={"auto_assigned": True}
                            )
                            session.add(user_role)

                        result["users_created"] += 1
                        logger.info(f"Created user: {user_data['username']}")

                except Exception as e:
                    result["errors"].append(f"Failed to create user {user_data['username']}: {str(e)}")

        except Exception as e:
            result["errors"].append(f"Default users/roles creation failed: {str(e)}")
            logger.error(f"Default users/roles creation failed: {e}")

        return result

    async def _migrate_system_configs(self, session: AsyncSession) -> Dict[str, Any]:
        """遷移系統配置"""
        result = {
            "system_configs_migrated": 0,
            "errors": []
        }

        try:
            # 從環境文件遷移配置
            for env_file in self.data_sources["env_files"]:
                try:
                    config_count = await self._process_env_file(session, env_file)
                    result["system_configs_migrated"] += config_count
                    logger.info(f"Processed env file: {env_file} ({config_count} configs)")
                except Exception as e:
                    result["errors"].append(f"Failed to process env file {env_file}: {str(e)}")

            # 從配置文件遷移
            for config_file in self.data_sources["config_files"]:
                try:
                    config_count = await self._process_config_file(session, config_file)
                    result["system_configs_migrated"] += config_count
                    logger.info(f"Processed config file: {config_file} ({config_count} configs)")
                except Exception as e:
                    result["errors"].append(f"Failed to process config file {config_file}: {str(e)}")

        except Exception as e:
            result["errors"].append(f"System config migration failed: {str(e)}")
            logger.error(f"System config migration failed: {e}")

        return result

    async def _process_env_file(self, session: AsyncSession, env_file: str) -> int:
        """處理環境配置文件"""
        config_count = 0

        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')  # 移除引號

                    # 檢查配置是否已存在
                    existing_config = await session.execute(
                        select(SystemConfig).where(SystemConfig.config_key == f"migration_{key}")
                    )
                    if not existing_config.scalar_one_or_none():
                        # 確定配置類型
                        config_type = "string"
                        if value.lower() in ('true', 'false'):
                            config_type = "boolean"
                        elif value.replace('.', '', 1).isdigit():
                            config_type = "number"

                        # 確定是否為敏感信息
                        is_sensitive = any(keyword in key.lower() for keyword in
                                         ['password', 'secret', 'key', 'token', 'auth'])

                        system_config = SystemConfig(
                            config_key=f"migration_{key}",
                            config_value=value,
                            config_type=config_type,
                            description=f"Migrated from {env_file}",
                            category="environment",
                            is_sensitive=is_sensitive,
                            is_public=not is_sensitive,
                            metadata={
                                "source_file": env_file,
                                "migration_date": datetime.now().isoformat(),
                                "original_key": key
                            }
                        )
                        session.add(system_config)
                        config_count += 1

        except Exception as e:
            logger.error(f"Error processing env file {env_file}: {e}")
            raise

        return config_count

    async def _process_config_file(self, session: AsyncSession, config_file: str) -> int:
        """處理配置文件"""
        config_count = 0

        try:
            if config_file.endswith('.json'):
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                config_count = await self._process_json_config(session, data, config_file)

            elif config_file.endswith('.py'):
                # 這裡可以添加解析Python配置文件的邏輯
                logger.info(f"Skipping Python config file: {config_file}")

        except Exception as e:
            logger.error(f"Error processing config file {config_file}: {e}")

        return config_count

    async def _process_json_config(self, session: AsyncSession, data: Dict[str, Any], source_file: str) -> int:
        """處理JSON配置數據"""
        config_count = 0

        def process_dict(data_dict, prefix=""):
            nonlocal config_count
            for key, value in data_dict.items():
                full_key = f"{prefix}.{key}" if prefix else key

                if isinstance(value, dict):
                    process_dict(value, full_key)
                elif not callable(value):  # 跳過函數對象
                    # 檢查配置是否已存在
                    existing_config = await session.execute(
                        select(SystemConfig).where(SystemConfig.config_key == f"migration_{full_key}")
                    )
                    if not existing_config.scalar_one_or_none():
                        config_type = "object" if isinstance(value, (dict, list)) else "string"
                        config_value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)

                        system_config = SystemConfig(
                            config_key=f"migration_{full_key}",
                            config_value=config_value,
                            config_type=config_type,
                            description=f"Migrated from {source_file}",
                            category="application",
                            is_sensitive=False,
                            is_public=True,
                            metadata={
                                "source_file": source_file,
                                "migration_date": datetime.now().isoformat()
                            }
                        )
                        session.add(system_config)
                        config_count += 1

        process_dict(data)
        return config_count

    async def _migrate_audit_logs(self, session: AsyncSession) -> Dict[str, Any]:
        """遷移審計日誌"""
        result = {
            "audit_logs_created": 0,
            "errors": []
        }

        try:
            # 創建遷移開始的審計日誌
            admin_user = await session.execute(
                select(User).where(User.username == "admin")
            )
            admin = admin_user.scalar_one_or_none()

            if admin:
                audit_logs = [
                    {
                        "action": "SYSTEM_MIGRATION_STARTED",
                        "resource_type": "system",
                        "description": "CBSC System unification migration started"
                    },
                    {
                        "action": "DATA_SCHEMA_CREATED",
                        "resource_type": "schema",
                        "description": "Unified database schema created"
                    },
                    {
                        "action": "STRATEGY_DATA_MIGRATED",
                        "resource_type": "strategy",
                        "description": "Strategy data migrated to unified model"
                    },
                    {
                        "action": "MARKET_DATA_MIGRATED",
                        "resource_type": "market_data",
                        "description": "Market data migrated to unified model"
                    },
                    {
                        "action": "USER_DATA_MIGRATED",
                        "resource_type": "user",
                        "description": "User and system data migrated to unified model"
                    },
                    {
                        "action": "SYSTEM_MIGRATION_COMPLETED",
                        "resource_type": "system",
                        "description": "CBSC System unification migration completed"
                    }
                ]

                for log_data in audit_logs:
                    audit_log = AuditLog(
                        user_id=admin.id,
                        action=log_data["action"],
                        resource_type=log_data["resource_type"],
                        ip_address="127.0.0.1",
                        user_agent="CBSC Migration System",
                        request_data={"migration_type": "system_unification"},
                        response_status=200,
                        timestamp=datetime.now(),
                        metadata={
                            "migration_audit": True,
                            "description": log_data["description"],
                            "migration_date": datetime.now().isoformat()
                        }
                    )
                    session.add(audit_log)
                    result["audit_logs_created"] += 1

        except Exception as e:
            result["errors"].append(f"Audit log migration failed: {str(e)}")
            logger.error(f"Audit log migration failed: {e}")

        return result

    async def _create_data_schemas(self, session: AsyncSession) -> Dict[str, Any]:
        """創建數據模式記錄"""
        result = {
            "data_schemas_created": 0,
            "errors": []
        }

        try:
            # 創建統一數據模式定義
            schemas = [
                {
                    "schema_name": "cbsc_unified_v1",
                    "schema_version": "1.0.0",
                    "description": "CBSC Unified Data Model Version 1.0",
                    "definition": {
                        "modules": [
                            "user_management",
                            "strategy_management",
                            "market_data",
                            "trading_portfolio",
                            "analytics_reporting",
                            "system_management"
                        ],
                        "tables": [
                            "users", "roles", "user_roles",
                            "strategies", "strategy_configs", "strategy_performance", "strategy_categories",
                            "market_data", "technical_indicators", "sentiment_data",
                            "portfolios", "positions", "orders", "trades",
                            "analysis_reports", "backtest_results", "performance_metrics",
                            "system_config", "audit_logs", "data_schemas"
                        ],
                        "features": [
                            "multi_factor_authentication",
                            "role_based_access_control",
                            "real_time_data_processing",
                            "comprehensive_audit_logging",
                            "data_backup_recovery"
                        ]
                    }
                },
                {
                    "schema_name": "market_data_v1",
                    "schema_version": "1.0.0",
                    "description": "Market Data Schema for CBSC System",
                    "definition": {
                        "tables": ["market_data", "technical_indicators", "sentiment_data"],
                        "indices": ["symbol", "timestamp", "indicator_type"],
                        "data_sources": ["yahoo_finance", "government_data", "real_time_feeds"]
                    }
                },
                {
                    "schema_name": "strategy_framework_v1",
                    "schema_version": "1.0.0",
                    "description": "Strategy Management Framework Schema",
                    "definition": {
                        "tables": ["strategies", "strategy_configs", "strategy_performance", "backtest_results"],
                        "strategy_types": ["technical_analysis", "fundamental_analysis", "quantitative"],
                        "performance_metrics": ["sharpe_ratio", "max_drawdown", "win_rate", "total_return"]
                    }
                }
            ]

            for schema_data in schemas:
                # 檢查模式是否已存在
                existing_schema = await session.execute(
                    select(DataSchema).where(DataSchema.schema_name == schema_data["schema_name"])
                )
                if not existing_schema.scalar_one_or_none():
                    data_schema = DataSchema(
                        schema_name=schema_data["schema_name"],
                        schema_version=schema_data["schema_version"],
                        schema_definition=schema_data["definition"],
                        description=schema_data["description"],
                        is_active=True,
                        metadata={
                            "auto_created": True,
                            "migration_date": datetime.now().isoformat(),
                            "schema_type": "migration"
                        }
                    )
                    session.add(data_schema)
                    result["data_schemas_created"] += 1
                    logger.info(f"Created data schema: {schema_data['schema_name']}")

        except Exception as e:
            result["errors"].append(f"Data schema creation failed: {str(e)}")
            logger.error(f"Data schema creation failed: {e}")

        return result

    async def validate_migration(self, session: AsyncSession) -> Dict[str, Any]:
        """驗證遷移結果"""
        result = {
            "success": True,
            "users_count": 0,
            "roles_count": 0,
            "system_configs_count": 0,
            "audit_logs_count": 0,
            "data_schemas_count": 0,
            "errors": []
        }

        try:
            # 統計遷移的數據
            result["users_count"] = len((await session.execute(
                select(User).where(User.metadata['migration_source'].isnot(None))
            )).scalars().all())

            result["roles_count"] = len((await session.execute(
                select(Role).where(Role.metadata['auto_created'] == True)
            )).scalars().all())

            result["system_configs_count"] = len((await session.execute(
                select(SystemConfig).where(SystemConfig.config_key.like('migration_%'))
            )).scalars().all())

            result["audit_logs_count"] = len((await session.execute(
                select(AuditLog).where(AuditLog.metadata['migration_audit'] == True)
            )).scalars().all())

            result["data_schemas_count"] = len((await session.execute(
                select(DataSchema).where(DataSchema.metadata['auto_created'] == True)
            )).scalars().all())

            # 驗證基本完整性
            if result["users_count"] < 3:
                result["success"] = False
                result["errors"].append("Default users not created properly")

            if result["roles_count"] < 4:
                result["success"] = False
                result["errors"].append("Default roles not created properly")

            logger.info(f"User data migration validation: {result}")

        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Validation failed: {str(e)}")
            logger.error(f"User data migration validation failed: {e}")

        return result

# 註冊遷移腳本
migration = MigrateUserDataMigration()