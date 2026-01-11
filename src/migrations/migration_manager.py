"""
數據遷移管理器

提供數據庫遷移、版本控制、回滾和數據驗證功能。
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import asyncio
import logging

from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import db_manager
from .migration_script import MigrationScript
from .data_validator import DataValidator

logger = logging.getLogger(__name__)

class MigrationManager:
    """數據遷移管理器

    負責管理數據庫遷移的整個生命週期，包括：
    - 遷移腳本管理
    - 版本控制
    - 執行遷移
    - 回滾操作
    - 數據驗證
    """

    def __init__(self):
        self.migrations_dir = Path(__file__).parent / "scripts"
        self.migrations_dir.mkdir(exist_ok=True)
        self.validator = DataValidator()

    def create_migration_table(self):
        """創建遷移記錄表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS migration_history (
            id SERIAL PRIMARY KEY,
            version VARCHAR(20) NOT NULL UNIQUE,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            execution_time_ms INTEGER,
            success BOOLEAN NOT NULL DEFAULT TRUE,
            error_message TEXT,
            checksum VARCHAR(64),
            rollback_script TEXT,
            metadata JSONB
        );

        CREATE INDEX IF NOT EXISTS idx_migration_version ON migration_history(version);
        CREATE INDEX IF NOT EXISTS idx_migration_executed_at ON migration_history(executed_at);
        CREATE INDEX IF NOT EXISTS idx_migration_success ON migration_history(success);
        """

        try:
            with db_manager.get_session() as session:
                session.execute(text(create_table_sql))
                session.commit()
            logger.info("Migration table created successfully")
        except Exception as e:
            logger.error(f"Failed to create migration table: {e}")
            raise

    async def create_migration_table_async(self):
        """異步創建遷移記錄表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS migration_history (
            id SERIAL PRIMARY KEY,
            version VARCHAR(20) NOT NULL UNIQUE,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            execution_time_ms INTEGER,
            success BOOLEAN NOT NULL DEFAULT TRUE,
            error_message TEXT,
            checksum VARCHAR(64),
            rollback_script TEXT,
            metadata JSONB
        );

        CREATE INDEX IF NOT EXISTS idx_migration_version ON migration_history(version);
        CREATE INDEX IF NOT EXISTS idx_migration_executed_at ON migration_history(executed_at);
        CREATE INDEX IF NOT EXISTS idx_migration_success ON migration_history(success);
        """

        try:
            async with db_manager.get_async_session() as session:
                await session.execute(text(create_table_sql))
                await session.commit()
            logger.info("Migration table created successfully (async)")
        except Exception as e:
            logger.error(f"Failed to create migration table (async): {e}")
            raise

    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """獲取已應用的遷移"""
        try:
            with db_manager.get_session() as session:
                result = session.execute(
                    text("SELECT * FROM migration_history ORDER BY version")
                )
                return [dict(row) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []

    async def get_applied_migrations_async(self) -> List[Dict[str, Any]]:
        """異步獲取已應用的遷移"""
        try:
            async with db_manager.get_async_session() as session:
                result = await session.execute(
                    text("SELECT * FROM migration_history ORDER BY version")
                )
                return [dict(row) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get applied migrations (async): {e}")
            return []

    def get_pending_migrations(self) -> List[MigrationScript]:
        """獲取待執行的遷移"""
        applied_versions = {m["version"] for m in self.get_applied_migrations()}
        pending = []

        for script_file in sorted(self.migrations_dir.glob("*.sql")):
            script = MigrationScript.from_file(script_file)
            if script.version not in applied_versions:
                pending.append(script)

        return pending

    async def get_pending_migrations_async(self) -> List[MigrationScript]:
        """異步獲取待執行的遷移"""
        applied_versions = {m["version"] for m in await self.get_applied_migrations_async()}
        pending = []

        for script_file in sorted(self.migrations_dir.glob("*.sql")):
            script = MigrationScript.from_file(script_file)
            if script.version not in applied_versions:
                pending.append(script)

        return pending

    def execute_migration(self, migration: MigrationScript) -> Dict[str, Any]:
        """執行單個遷移"""
        start_time = datetime.now()
        result = {
            "version": migration.version,
            "name": migration.name,
            "success": False,
            "error": None,
            "execution_time_ms": 0
        }

        try:
            logger.info(f"Executing migration: {migration.version} - {migration.name}")

            # 驗證遷移腳本
            validation_result = self.validator.validate_migration_script(migration)
            if not validation_result["valid"]:
                result["error"] = validation_result["error"]
                return result

            # 執行遷移
            with db_manager.get_session() as session:
                # 開始事務
                session.begin()

                try:
                    # 執行遷移SQL
                    for sql_statement in migration.sql_statements:
                        session.execute(text(sql_statement))

                    # 記錄遷移歷史
                    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    insert_sql = """
                    INSERT INTO migration_history (
                        version, name, description, executed_at, execution_time_ms,
                        success, checksum, rollback_script, metadata
                    ) VALUES (:version, :name, :description, :executed_at, :execution_time_ms,
                            :success, :checksum, :rollback_script, :metadata)
                    """

                    session.execute(text(insert_sql), {
                        "version": migration.version,
                        "name": migration.name,
                        "description": migration.description,
                        "executed_at": start_time,
                        "execution_time_ms": execution_time,
                        "success": True,
                        "checksum": migration.checksum,
                        "rollback_script": migration.rollback_sql,
                        "metadata": json.dumps(migration.metadata)
                    })

                    # 提交事務
                    session.commit()

                    result["success"] = True
                    result["execution_time_ms"] = execution_time

                    logger.info(f"Migration {migration.version} executed successfully in {execution_time}ms")

                except Exception as e:
                    # 回滾事務
                    session.rollback()
                    raise

        except Exception as e:
            error_msg = f"Migration {migration.version} failed: {str(e)}"
            logger.error(error_msg)

            # 記錄失敗的遷移
            try:
                with db_manager.get_session() as session:
                    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    insert_sql = """
                    INSERT INTO migration_history (
                        version, name, description, executed_at, execution_time_ms,
                        success, error_message, metadata
                    ) VALUES (:version, :name, :description, :executed_at, :execution_time_ms,
                            :success, :error_message, :metadata)
                    """

                    session.execute(text(insert_sql), {
                        "version": migration.version,
                        "name": migration.name,
                        "description": migration.description,
                        "executed_at": start_time,
                        "execution_time_ms": execution_time,
                        "success": False,
                        "error_message": str(e),
                        "metadata": json.dumps(migration.metadata)
                    })
                    session.commit()
            except Exception as record_error:
                logger.error(f"Failed to record migration failure: {record_error}")

            result["error"] = str(e)
            result["execution_time_ms"] = int((datetime.now() - start_time).total_seconds() * 1000)

        return result

    async def execute_migration_async(self, migration: MigrationScript) -> Dict[str, Any]:
        """異步執行單個遷移"""
        start_time = datetime.now()
        result = {
            "version": migration.version,
            "name": migration.name,
            "success": False,
            "error": None,
            "execution_time_ms": 0
        }

        try:
            logger.info(f"Executing migration (async): {migration.version} - {migration.name}")

            # 驗證遷移腳本
            validation_result = self.validator.validate_migration_script(migration)
            if not validation_result["valid"]:
                result["error"] = validation_result["error"]
                return result

            # 執行遷移
            async with db_manager.get_async_session() as session:
                # 開始事務
                await session.begin()

                try:
                    # 執行遷移SQL
                    for sql_statement in migration.sql_statements:
                        await session.execute(text(sql_statement))

                    # 記錄遷移歷史
                    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    insert_sql = """
                    INSERT INTO migration_history (
                        version, name, description, executed_at, execution_time_ms,
                        success, checksum, rollback_script, metadata
                    ) VALUES (:version, :name, :description, :executed_at, :execution_time_ms,
                            :success, :checksum, :rollback_script, :metadata)
                    """

                    await session.execute(text(insert_sql), {
                        "version": migration.version,
                        "name": migration.name,
                        "description": migration.description,
                        "executed_at": start_time,
                        "execution_time_ms": execution_time,
                        "success": True,
                        "checksum": migration.checksum,
                        "rollback_script": migration.rollback_sql,
                        "metadata": json.dumps(migration.metadata)
                    })

                    # 提交事務
                    await session.commit()

                    result["success"] = True
                    result["execution_time_ms"] = execution_time

                    logger.info(f"Migration {migration.version} executed successfully in {execution_time}ms (async)")

                except Exception as e:
                    # 回滾事務
                    await session.rollback()
                    raise

        except Exception as e:
            error_msg = f"Migration {migration.version} failed (async): {str(e)}"
            logger.error(error_msg)

            # 記錄失敗的遷移
            try:
                async with db_manager.get_async_session() as session:
                    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    insert_sql = """
                    INSERT INTO migration_history (
                        version, name, description, executed_at, execution_time_ms,
                        success, error_message, metadata
                    ) VALUES (:version, :name, :description, :executed_at, :execution_time_ms,
                            :success, :error_message, :metadata)
                    """

                    await session.execute(text(insert_sql), {
                        "version": migration.version,
                        "name": migration.name,
                        "description": migration.description,
                        "executed_at": start_time,
                        "execution_time_ms": execution_time,
                        "success": False,
                        "error_message": str(e),
                        "metadata": json.dumps(migration.metadata)
                    })
                    await session.commit()
            except Exception as record_error:
                logger.error(f"Failed to record migration failure (async): {record_error}")

            result["error"] = str(e)
            result["execution_time_ms"] = int((datetime.now() - start_time).total_seconds() * 1000)

        return result

    def migrate(self) -> Dict[str, Any]:
        """執行所有待遷移"""
        start_time = datetime.now()
        pending_migrations = self.get_pending_migrations()

        if not pending_migrations:
            return {
                "success": True,
                "message": "No pending migrations",
                "executed_migrations": [],
                "total_execution_time_ms": 0
            }

        results = []
        total_success = True

        logger.info(f"Starting migration of {len(pending_migrations)} pending migrations")

        for migration in pending_migrations:
            result = self.execute_migration(migration)
            results.append(result)
            if not result["success"]:
                total_success = False
                break  # 停止執行後續遷移

        total_time = int((datetime.now() - start_time).total_seconds() * 1000)

        return {
            "success": total_success,
            "message": f"Executed {len(results)} migrations" if total_success else "Migration failed",
            "executed_migrations": results,
            "total_execution_time_ms": total_time
        }

    async def migrate_async(self) -> Dict[str, Any]:
        """異步執行所有待遷移"""
        start_time = datetime.now()
        pending_migrations = await self.get_pending_migrations_async()

        if not pending_migrations:
            return {
                "success": True,
                "message": "No pending migrations",
                "executed_migrations": [],
                "total_execution_time_ms": 0
            }

        results = []
        total_success = True

        logger.info(f"Starting async migration of {len(pending_migrations)} pending migrations")

        for migration in pending_migrations:
            result = await self.execute_migration_async(migration)
            results.append(result)
            if not result["success"]:
                total_success = False
                break  # 停止執行後續遷移

        total_time = int((datetime.now() - start_time).total_seconds() * 1000)

        return {
            "success": total_success,
            "message": f"Executed {len(results)} migrations" if total_success else "Migration failed",
            "executed_migrations": results,
            "total_execution_time_ms": total_time
        }

    def rollback_migration(self, version: str) -> Dict[str, Any]:
        """回滾指定版本的遷移"""
        try:
            # 獲取遷移記錄
            with db_manager.get_session() as session:
                result = session.execute(
                    text("SELECT * FROM migration_history WHERE version = :version AND success = true"),
                    {"version": version}
                )
                migration_record = result.fetchone()

                if not migration_record:
                    return {
                        "success": False,
                        "error": f"Migration {version} not found or not successful"
                    }

                rollback_sql = migration_record.rollback_script
                if not rollback_sql:
                    return {
                        "success": False,
                        "error": f"No rollback script available for migration {version}"
                    }

                # 執行回滾
                start_time = datetime.now()
                with db_manager.get_session() as session:
                    session.begin()

                    try:
                        # 執行回滾SQL
                        session.execute(text(rollback_sql))

                        # 更新遷移記錄
                        update_sql = """
                        UPDATE migration_history
                        SET success = false,
                            error_message = 'Rolled back manually',
                            rolled_back_at = :rolled_back_at
                        WHERE version = :version
                        """
                        session.execute(text(update_sql), {
                            "version": version,
                            "rolled_back_at": datetime.now()
                        })

                        session.commit()

                        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

                        logger.info(f"Migration {version} rolled back successfully in {execution_time}ms")

                        return {
                            "success": True,
                            "message": f"Migration {version} rolled back successfully",
                            "execution_time_ms": execution_time
                        }

                    except Exception as e:
                        session.rollback()
                        raise

        except Exception as e:
            error_msg = f"Failed to rollback migration {version}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

    def get_migration_status(self) -> Dict[str, Any]:
        """獲取遷移狀態"""
        try:
            applied_migrations = self.get_applied_migrations()
            pending_migrations = self.get_pending_migrations()

            latest_version = None
            if applied_migrations:
                latest_version = max(m["version"] for m in applied_migrations)

            return {
                "current_version": latest_version,
                "applied_count": len(applied_migrations),
                "pending_count": len(pending_migrations),
                "latest_migration": applied_migrations[-1] if applied_migrations else None,
                "pending_migrations": [
                    {"version": m.version, "name": m.name} for m in pending_migrations
                ],
                "migration_history": applied_migrations
            }

        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {
                "error": str(e),
                "current_version": None,
                "applied_count": 0,
                "pending_count": 0
            }

    async def get_migration_status_async(self) -> Dict[str, Any]:
        """異步獲取遷移狀態"""
        try:
            applied_migrations = await self.get_applied_migrations_async()
            pending_migrations = await self.get_pending_migrations_async()

            latest_version = None
            if applied_migrations:
                latest_version = max(m["version"] for m in applied_migrations)

            return {
                "current_version": latest_version,
                "applied_count": len(applied_migrations),
                "pending_count": len(pending_migrations),
                "latest_migration": applied_migrations[-1] if applied_migrations else None,
                "pending_migrations": [
                    {"version": m.version, "name": m.name} for m in pending_migrations
                ],
                "migration_history": applied_migrations
            }

        except Exception as e:
            logger.error(f"Failed to get migration status (async): {e}")
            return {
                "error": str(e),
                "current_version": None,
                "applied_count": 0,
                "pending_count": 0
            }

# 全局遷移管理器實例
migration_manager = MigrationManager()

# 便捷函數
def run_migrations() -> Dict[str, Any]:
    """運行所有待遷移（便捷函數）"""
    return migration_manager.migrate()

async def run_migrations_async() -> Dict[str, Any]:
    """異步運行所有待遷移（便捷函數）"""
    return await migration_manager.migrate_async()

def get_migration_status() -> Dict[str, Any]:
    """獲取遷移狀態（便捷函數）"""
    return migration_manager.get_migration_status()

async def get_migration_status_async() -> Dict[str, Any]:
    """異步獲取遷移狀態（便捷函數）"""
    return await migration_manager.get_migration_status_async()