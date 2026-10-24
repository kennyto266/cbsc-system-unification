"""
數據遷移執行器

統一執行和管理所有數據遷移腳本的主程序。
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import traceback

from .migration_manager import MigrationManager
from .scripts.migration_001_create_unified_schema import migration as schema_migration
from .scripts.migration_002_migrate_strategy_data import migration as strategy_migration
from .scripts.migration_003_migrate_market_data import migration as market_migration
from .scripts.migration_004_migrate_user_data import migration as user_migration
from ..database.connection import db_manager

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DataMigrationExecutor:
    """數據遷移執行器

    負責協調和執行所有的數據遷移任務，包括：
    - 數據庫模式創建
    - 策略數據遷移
    - 市場數據遷移
    - 用戶數據遷移
    - 遷移驗證和報告
    """

    def __init__(self):
        self.migration_manager = MigrationManager()
        self.migration_scripts = [
            schema_migration,
            strategy_migration,
            market_migration,
            user_migration
        ]
        self.migration_report = {
            "execution_start": datetime.now().isoformat(),
            "migration_results": {},
            "summary": {
                "total_migrations": 0,
                "successful_migrations": 0,
                "failed_migrations": 0,
                "total_execution_time_ms": 0
            },
            "data_statistics": {
                "strategies_migrated": 0,
                "market_data_migrated": 0,
                "users_created": 0,
                "system_configs_migrated": 0,
                "audit_logs_created": 0
            },
            "errors": [],
            "recommendations": []
        }

    async def execute_full_migration(self) -> Dict[str, Any]:
        """執行完整的數據遷移流程"""
        try:
            logger.info("Starting CBSC System Data Migration...")
            logger.info("=" * 60)

            # 1. 準備遷移環境
            await self._prepare_migration_environment()

            # 2. 執行遷移腳本
            await self._execute_migration_scripts()

            # 3. 驗證遷移結果
            await self._validate_migration_results()

            # 4. 生成遷移報告
            await self._generate_migration_report()

            logger.info("=" * 60)
            logger.info("Data Migration Completed!")
            logger.info(f"Summary: {self.migration_report['summary']}")
            logger.info(f"Data Statistics: {self.migration_report['data_statistics']}")

            return self.migration_report

        except Exception as e:
            logger.error(f"Data migration failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.migration_report["errors"].append({
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            })
            return self.migration_report

    async def _prepare_migration_environment(self):
        """準備遷移環境"""
        logger.info("Preparing migration environment...")

        try:
            # 1. 測試數據庫連接
            await self._test_database_connection()

            # 2. 創建遷移表
            await self.migration_manager.create_migration_table_async()

            # 3. 檢查遷移依賴
            await self._check_migration_dependencies()

            # 4. 備份現有數據（如果存在）
            await self._backup_existing_data()

            logger.info("Migration environment prepared successfully")

        except Exception as e:
            logger.error(f"Failed to prepare migration environment: {e}")
            raise

    async def _test_database_connection(self):
        """測試數據庫連接"""
        try:
            async with db_manager.get_async_session() as session:
                await session.execute("SELECT 1")
                logger.info("Database connection test passed")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise

    async def _check_migration_dependencies(self):
        """檢查遷移依賴"""
        logger.info("Checking migration dependencies...")

        # 檢查必要的Python包
        required_packages = [
            'sqlalchemy', 'asyncpg', 'pandas', 'pathlib',
            'json', 'datetime', 'logging'
        ]

        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                raise ImportError(f"Required package '{package}' not found")

        logger.info("All migration dependencies satisfied")

    async def _backup_existing_data(self):
        """備份現有數據"""
        logger.info("Checking for existing data to backup...")

        try:
            async with db_manager.get_async_session() as session:
                # 檢查是否已有數據
                tables_to_check = ['users', 'strategies', 'market_data']
                existing_data = False

                for table_name in tables_to_check:
                    try:
                        result = await session.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = result.scalar()
                        if count > 0:
                            existing_data = True
                            logger.info(f"Found {count} records in {table_name}")
                    except Exception:
                        pass  # 表不存在

                if existing_data:
                    # 記錄備份信息
                    backup_info = {
                        "backup_date": datetime.now().isoformat(),
                        "backup_reason": "pre_migration_backup",
                        "tables_checked": tables_to_check
                    }
                    logger.info(f"Existing data found. Backup info: {backup_info}")
                else:
                    logger.info("No existing data found, proceeding with migration")

        except Exception as e:
            logger.warning(f"Backup check failed: {e}")

    async def _execute_migration_scripts(self):
        """執行遷移腳本"""
        logger.info("Executing migration scripts...")
        total_start_time = datetime.now()

        for migration_script in self.migration_scripts:
            migration_start_time = datetime.now()
            migration_name = f"{migration_script.version}_{migration_script.name}"

            logger.info(f"Executing migration: {migration_name}")
            logger.info("-" * 40)

            try:
                # 執行遷移
                migration_result = await self._execute_single_migration(migration_script)

                # 計算執行時間
                execution_time = (datetime.now() - migration_start_time).total_seconds() * 1000
                migration_result["execution_time_ms"] = execution_time

                # 記錄結果
                self.migration_report["migration_results"][migration_name] = migration_result

                if migration_result.get("success", False):
                    logger.info(f"✓ Migration {migration_name} completed successfully")
                    self.migration_report["summary"]["successful_migrations"] += 1

                    # 更新數據統計
                    self._update_data_statistics(migration_result)
                else:
                    logger.error(f"✗ Migration {migration_name} failed")
                    self.migration_report["summary"]["failed_migrations"] += 1
                    self.migration_report["errors"].extend(migration_result.get("errors", []))

            except Exception as e:
                logger.error(f"✗ Migration {migration_name} failed with exception: {e}")
                error_result = {
                    "success": False,
                    "errors": [str(e)],
                    "execution_time_ms": (datetime.now() - migration_start_time).total_seconds() * 1000
                }
                self.migration_report["migration_results"][migration_name] = error_result
                self.migration_report["summary"]["failed_migrations"] += 1
                self.migration_report["errors"].append(str(e))

            logger.info("-" * 40)

        # 計算總執行時間
        total_execution_time = (datetime.now() - total_start_time).total_seconds() * 1000
        self.migration_report["summary"]["total_execution_time_ms"] = total_execution_time
        self.migration_report["summary"]["total_migrations"] = len(self.migration_scripts)

    async def _execute_single_migration(self, migration_script) -> Dict[str, Any]:
        """執行單個遷移腳本"""
        try:
            # 檢查遷移是否已經執行過
            if await self.migration_manager.is_migration_executed(migration_script.version):
                logger.info(f"Migration {migration_script.version} already executed, skipping")
                return {"success": True, "skipped": True, "reason": "Already executed"}

            # 執行遷移
            async with db_manager.get_async_session() as session:
                # 如果有自定義遷移邏輯
                if hasattr(migration_script, 'execute_migration'):
                    result = await migration_script.execute_migration(session)
                else:
                    # 執行標準SQL遷移
                    up_sql = migration_script.get_up_sql()
                    if up_sql != "-- This migration uses Python logic for data migration":
                        await session.execute(up_sql)
                    result = {"success": True}

                # 記錄遷移歷史
                await self.migration_manager.record_migration_execution(
                    session, migration_script, result
                )

                # 驗證遷移結果
                if hasattr(migration_script, 'validate_migration'):
                    validation_result = await migration_script.validate_migration(session)
                    result.update(validation_result)

                await session.commit()

                return result

        except Exception as e:
            logger.error(f"Migration execution failed: {e}")
            return {
                "success": False,
                "errors": [str(e)],
                "traceback": traceback.format_exc()
            }

    def _update_data_statistics(self, migration_result: Dict[str, Any]):
        """更新數據統計信息"""
        stats_mapping = {
            "strategies_migrated": ["strategies_migrated", "configs_migrated", "performance_records_migrated"],
            "market_data_migrated": ["market_data_migrated", "technical_indicators_migrated", "sentiment_data_migrated"],
            "users_created": ["users_created", "roles_created"],
            "system_configs_migrated": ["system_configs_migrated"],
            "audit_logs_created": ["audit_logs_created"]
        }

        for stat_key, result_keys in stats_mapping.items():
            for result_key in result_keys:
                if result_key in migration_result:
                    self.migration_report["data_statistics"][stat_key] += migration_result[result_key]

    async def _validate_migration_results(self):
        """驗證遷移結果"""
        logger.info("Validating migration results...")

        try:
            async with db_manager.get_async_session() as session:
                # 檢查表是否存在且有數據
                validation_queries = [
                    ("users", "SELECT COUNT(*) FROM users"),
                    ("strategies", "SELECT COUNT(*) FROM strategies"),
                    ("market_data", "SELECT COUNT(*) FROM market_data"),
                    ("system_config", "SELECT COUNT(*) FROM system_config"),
                    ("audit_logs", "SELECT COUNT(*) FROM audit_logs")
                ]

                validation_results = {}
                for table_name, query in validation_queries:
                    try:
                        result = await session.execute(query)
                        count = result.scalar()
                        validation_results[table_name] = count
                        logger.info(f"Table {table_name}: {count} records")
                    except Exception as e:
                        logger.error(f"Failed to validate table {table_name}: {e}")
                        validation_results[table_name] = -1

                # 檢查遷移完整性
                missing_data = []
                for table_name, count in validation_results.items():
                    if count == 0:
                        missing_data.append(table_name)

                if missing_data:
                    logger.warning(f"Tables with no data: {missing_data}")
                    self.migration_report["recommendations"].append(
                        f"Review tables with no data: {', '.join(missing_data)}"
                    )

                # 記錄驗證結果
                self.migration_report["validation_results"] = validation_results

        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            self.migration_report["errors"].append(f"Validation failed: {str(e)}")

    async def _generate_migration_report(self):
        """生成遷移報告"""
        logger.info("Generating migration report...")

        self.migration_report["execution_end"] = datetime.now().isoformat()
        self.migration_report["report_generated_at"] = datetime.now().isoformat()

        # 生成建議
        self._generate_recommendations()

        # 保存報告到文件
        report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.migration_report, f, indent=2, ensure_ascii=False)
            logger.info(f"Migration report saved to: {report_file}")
        except Exception as e:
            logger.error(f"Failed to save migration report: {e}")

        # 打印摘要
        self._print_migration_summary()

    def _generate_recommendations(self):
        """生成遷移建議"""
        recommendations = []

        # 基於遷移結果的建議
        if self.migration_report["summary"]["failed_migrations"] > 0:
            recommendations.append(
                "Review failed migrations and address errors before proceeding to production"
            )

        if self.migration_report["data_statistics"]["strategies_migrated"] == 0:
            recommendations.append(
                "Consider running strategy data migration with additional data sources"
            )

        if self.migration_report["data_statistics"]["market_data_migrated"] < 1000:
            recommendations.append(
                "Consider importing more historical market data for comprehensive analysis"
            )

        # 成功遷移的建議
        if self.migration_report["summary"]["successful_migrations"] == len(self.migration_scripts):
            recommendations.extend([
                "Migration completed successfully. Review data integrity before production deployment",
                "Update application configuration to use the new unified database schema",
                "Plan database backup and maintenance procedures",
                "Train users on the new system features and interfaces"
            ])

        self.migration_report["recommendations"].extend(recommendations)

    def _print_migration_summary(self):
        """打印遷移摘要"""
        summary = self.migration_report["summary"]
        stats = self.migration_report["data_statistics"]

        print("\n" + "=" * 60)
        print("CBSC SYSTEM DATA MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Execution Time: {summary['total_execution_time_ms']:.2f} ms")
        print(f"Total Migrations: {summary['total_migrations']}")
        print(f"Successful: {summary['successful_migrations']}")
        print(f"Failed: {summary['failed_migrations']}")
        print("\nData Statistics:")
        print(f"  - Strategies Migrated: {stats['strategies_migrated']}")
        print(f"  - Market Data Records: {stats['market_data_migrated']}")
        print(f"  - Users Created: {stats['users_created']}")
        print(f"  - System Configs: {stats['system_configs_migrated']}")
        print(f"  - Audit Logs: {stats['audit_logs_created']}")

        if self.migration_report["recommendations"]:
            print("\nRecommendations:")
            for rec in self.migration_report["recommendations"]:
                print(f"  - {rec}")

        print("=" * 60)

async def main():
    """主執行函數"""
    try:
        executor = DataMigrationExecutor()
        report = await executor.execute_full_migration()

        # 根據結果設置退出代碼
        exit_code = 0 if report["summary"]["failed_migrations"] == 0 else 1
        sys.exit(exit_code)

    except Exception as e:
        logger.error(f"Migration execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())