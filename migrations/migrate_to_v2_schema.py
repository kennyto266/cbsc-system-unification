"""
Migration Script for Strategy Schema v2
策略數據庫遷移腳本 - v1到v2模式

This script handles the migration of existing strategy data from the legacy
schema to the new modular architecture schema.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.strategies.database.database import Database
from src.api.strategies.models import Strategy, StrategyType, StrategyStatus, RiskLevel
from src.api.strategies.repositories.strategy_repository import StrategyRepository
from src.api.strategies.repositories.execution_repository import ExecutionRepository

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StrategySchemaMigrator:
    """
    策略模式遷移器
    負責將舊的數據模式遷移到新的模式
    """

    def __init__(self, db_url: str):
        self.db = Database(db_url)
        self.strategy_repo = None
        self.execution_repo = None
        self.migration_log = []

    async def initialize(self):
        """初始化遷移器"""
        await self.db.connect()
        self.strategy_repo = StrategyRepository(self.db)
        self.execution_repo = ExecutionRepository(self.db)

    async def migrate_all(self, backup: bool = True):
        """
        執行完整的遷移流程
        """
        try:
            logger.info("開始策略模式遷移...")

            # 1. 備份現有數據
            if backup:
                await self.backup_existing_data()

            # 2. 遷移策略數據
            await self.migrate_strategies()

            # 3. 遷移執行數據
            await self.migrate_executions()

            # 4. 遷移用戶偏好
            await self.migrate_user_preferences()

            # 5. 更新外鍵關係
            await self.update_foreign_keys()

            # 6. 驗證遷移結果
            await self.validate_migration()

            logger.info("策略模式遷移成功完成！")
            return True

        except Exception as e:
            logger.error(f"遷移失敗: {e}")
            await self.rollback_migration()
            return False

    async def backup_existing_data(self):
        """備份現有數據"""
        logger.info("備份現有數據...")

        backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)

        # 備份策略表
        strategies_backup = await self._backup_table("personal_strategies")
        with open(f"{backup_dir}/personal_strategies_backup.json", 'w') as f:
            json.dump(strategies_backup, f, indent=2, default=str)

        # 備份執行表
        executions_backup = await self._backup_table("strategy_executions")
        with open(f"{backup_dir}/strategy_executions_backup.json", 'w') as f:
            json.dump(executions_backup, f, indent=2, default=str)

        # 備份用戶偏好表
        preferences_backup = await self._backup_table("user_preferences")
        with open(f"{backup_dir}/user_preferences_backup.json", 'w') as f:
            json.dump(preferences_backup, f, indent=2, default=str)

        logger.info(f"數據已備份到: {backup_dir}")
        self.log_migration("backup", f"數據備份到 {backup_dir}")

    async def migrate_strategies(self):
        """遷移策略數據"""
        logger.info("遷移策略數據...")

        # 獲取舊的策略數據
        old_strategies = await self._get_old_strategies()

        migrated_count = 0
        failed_count = 0

        for old_strategy in old_strategies:
            try:
                # 轉換策略數據
                new_strategy = await self._convert_strategy_data(old_strategy)

                # 保存新策略
                await self.strategy_repo.create(new_strategy)

                migrated_count += 1
                self.log_migration(
                    "strategy",
                    f"遷移策略: {old_strategy['id']} -> {new_strategy.id}",
                    {"old_id": old_strategy['id'], "new_id": new_strategy.id}
                )

            except Exception as e:
                failed_count += 1
                logger.error(f"遷移策略失敗 {old_strategy['id']}: {e}")
                self.log_migration(
                    "error",
                    f"策略遷移失敗: {old_strategy['id']}",
                    {"error": str(e), "data": old_strategy}
                )

        logger.info(f"策略遷移完成: 成功 {migrated_count}, 失敗 {failed_count}")

    async def migrate_executions(self):
        """遷移執行數據"""
        logger.info("遷移執行數據...")

        # 獲取舊的執行數據
        old_executions = await self._get_old_executions()

        migrated_count = 0
        failed_count = 0

        for old_execution in old_executions:
            try:
                # 轉換執行數據
                new_execution = await self._convert_execution_data(old_execution)

                # 保存新執行記錄
                await self.execution_repo.create(new_execution)

                migrated_count += 1
                self.log_migration(
                    "execution",
                    f"遷移執行: {old_execution['id']} -> {new_execution.id}",
                    {"old_id": old_execution['id'], "new_id": new_execution.id}
                )

            except Exception as e:
                failed_count += 1
                logger.error(f"遷移執行失敗 {old_execution['id']}: {e}")
                self.log_migration(
                    "error",
                    f"執行遷移失敗: {old_execution['id']}",
                    {"error": str(e), "data": old_execution}
                )

        logger.info(f"執行數據遷移完成: 成功 {migrated_count}, 失敗 {failed_count}")

    async def migrate_user_preferences(self):
        """遷移用戶偏好"""
        logger.info("遷移用戶偏好...")

        # 獲取舊的用戶偏好
        old_preferences = await self._get_old_user_preferences()

        migrated_count = 0
        for old_pref in old_preferences:
            try:
                # 轉換偏好數據
                new_pref = self._convert_user_preferences(old_pref)

                # 保存新偏好
                await self._save_user_preferences(new_pref)

                migrated_count += 1
                self.log_migration(
                    "preferences",
                    f"遷移用戶偏好: {old_pref['user_id']}"
                )

            except Exception as e:
                logger.error(f"遷移用戶偏好失敗 {old_pref['user_id']}: {e}")

        logger.info(f"用戶偏好遷移完成: {migrated_count}")

    async def update_foreign_keys(self):
        """更新外鍵關係"""
        logger.info("更新外鍵關係...")

        # 更新執行記錄的策略ID
        await self._update_execution_strategy_ids()

        # 更新其他關聯表的ID
        await self._update_related_tables()

        logger.info("外鍵關係更新完成")

    async def validate_migration(self):
        """驗證遷移結果"""
        logger.info("驗證遷移結果...")

        # 檢查數據完整性
        validation_results = {
            "strategies_count": await self._validate_strategies(),
            "executions_count": await self._validate_executions(),
            "relationships": await self._validate_relationships(),
            "data_integrity": await self._validate_data_integrity()
        }

        # 生成驗證報告
        report_file = f"migration_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(validation_results, f, indent=2, default=str)

        logger.info(f"驗證報告已生成: {report_file}")

        # 檢查是否有驗證失敗
        if any(result.get("errors") for result in validation_results.values()):
            logger.error("遷移驗證失敗！請檢查驗證報告。")
            return False

        logger.info("遷移驗證成功！")
        return True

    async def rollback_migration(self):
        """回滾遷移"""
        logger.warning("開始回滾遷移...")

        # 刪除新創建的表
        await self._drop_new_tables()

        # 恢復舊的表結構（如果需要）
        # await self._restore_old_tables()

        logger.warning("遷移已回滾")

    # Helper methods
    async def _backup_table(self, table_name: str) -> List[Dict[str, Any]]:
        """備份表數據"""
        query = f"SELECT * FROM {table_name}"
        with self.db.get_session() as session:
            result = session.execute(query)
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    async def _get_old_strategies(self) -> List[Dict[str, Any]]:
        """獲取舊的策略數據"""
        query = """
            SELECT * FROM personal_strategies
            WHERE deleted_at IS NULL
        """
        with self.db.get_session() as session:
            result = session.execute(query)
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    async def _convert_strategy_data(self, old_data: Dict[str, Any]) -> Strategy:
        """轉換策略數據格式"""
        # 映射策略類型
        type_mapping = {
            "RSI": StrategyType.DIRECT_RSI,
            "MACD": StrategyType.MACD_CROSS,
            "BOLLINGER": StrategyType.BOLLINGER_BANDS,
            "CUSTOM": StrategyType.CUSTOM
        }

        # 映射狀態
        status_mapping = {
            "ACTIVE": StrategyStatus.ACTIVE,
            "INACTIVE": StrategyStatus.INACTIVE,
            "DRAFT": StrategyStatus.DRAFT,
            "ARCHIVED": StrategyStatus.ARCHIVED
        }

        # 映射風險級別
        risk_mapping = {
            "LOW": RiskLevel.LOW,
            "MEDIUM": RiskLevel.MEDIUM,
            "HIGH": RiskLevel.HIGH
        }

        return Strategy(
            id=old_data['id'],
            name=old_data['name'],
            description=old_data.get('description', ''),
            strategy_type=type_mapping.get(old_data.get('strategy_type', 'CUSTOM'), StrategyType.CUSTOM),
            status=status_mapping.get(old_data.get('status', 'DRAFT'), StrategyStatus.DRAFT),
            parameters=old_data.get('parameters', {}),
            risk_level=risk_mapping.get(old_data.get('risk_level', 'MEDIUM'), RiskLevel.MEDIUM),
            is_active=old_data.get('is_active', True),
            user_id=old_data['user_id'],
            created_at=old_data.get('created_at', datetime.now(timezone.utc)),
            updated_at=old_data.get('updated_at', datetime.now(timezone.utc))
        )

    async def _get_old_executions(self) -> List[Dict[str, Any]]:
        """獲取舊的執行數據"""
        query = "SELECT * FROM strategy_executions"
        with self.db.get_session() as session:
            result = session.execute(query)
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    async def _convert_execution_data(self, old_data: Dict[str, Any]) -> Any:
        """轉換執行數據格式"""
        # 這裡需要根據新的執行模型來轉換
        # 簡化實現
        return {
            "id": old_data['id'],
            "strategy_id": old_data['strategy_id'],
            "user_id": old_data['user_id'],
            "execution_mode": old_data.get('mode', 'backtest'),
            "status": old_data.get('status', 'pending'),
            "start_time": old_data.get('start_time'),
            "end_time": old_data.get('end_time'),
            "results": old_data.get('results', {}),
            "created_at": old_data.get('created_at', datetime.now(timezone.utc))
        }

    async def _get_old_user_preferences(self) -> List[Dict[str, Any]]:
        """獲取舊的用戶偏好"""
        query = "SELECT * FROM user_preferences"
        with self.db.get_session() as session:
            result = session.execute(query)
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    def _convert_user_preferences(self, old_data: Dict[str, Any]) -> Dict[str, Any]:
        """轉換用戶偏好格式"""
        return {
            "user_id": old_data['user_id'],
            "theme": old_data.get('theme', 'light'),
            "language": old_data.get('language', 'zh-CN'),
            "timezone": old_data.get('timezone', 'Asia/Shanghai'),
            "notifications": old_data.get('notifications', {}),
            "risk_tolerance": old_data.get('risk_tolerance', 'medium'),
            "auto_save": old_data.get('auto_save', True),
            "updated_at": datetime.now(timezone.utc)
        }

    async def _save_user_preferences(self, preferences: Dict[str, Any]):
        """保存用戶偏好"""
        query = """
            INSERT INTO user_preferences_v2 (
                user_id, theme, language, timezone,
                notifications, risk_tolerance, auto_save, updated_at
            ) VALUES (
                :user_id, :theme, :language, :timezone,
                :notifications, :risk_tolerance, :auto_save, :updated_at
            )
            ON CONFLICT (user_id) DO UPDATE SET
                theme = EXCLUDED.theme,
                language = EXCLUDED.language,
                timezone = EXCLUDED.timezone,
                notifications = EXCLUDED.notifications,
                risk_tolerance = EXCLUDED.risk_tolerance,
                auto_save = EXCLUDED.auto_save,
                updated_at = EXCLUDED.updated_at
        """
        with self.db.get_session() as session:
            session.execute(query, preferences)

    async def _update_execution_strategy_ids(self):
        """更新執行記錄的策略ID映射"""
        query = """
            UPDATE strategy_executions_v2
            SET strategy_id = new_mapping.new_id
            FROM strategy_id_mapping new_mapping
            WHERE strategy_executions_v2.strategy_id = new_mapping.old_id
        """
        with self.db.get_session() as session:
            session.execute(query)

    async def _update_related_tables(self):
        """更新相關表的關係"""
        # 更新其他可能有策略ID引用的表
        pass

    async def _validate_strategies(self) -> Dict[str, Any]:
        """驗證策略數據"""
        with self.db.get_session() as session:
            # 檢查新策略表中的記錄數
            new_count = session.execute("SELECT COUNT(*) FROM strategies").scalar()
            # 檢查舊策略表中的記錄數
            old_count = session.execute("SELECT COUNT(*) FROM personal_strategies WHERE deleted_at IS NULL").scalar()

            errors = []
            if new_count != old_count:
                errors.append(f"策略數量不匹配: 新={new_count}, 舊={old_count}")

            return {
                "old_count": old_count,
                "new_count": new_count,
                "errors": errors
            }

    async def _validate_executions(self) -> Dict[str, Any]:
        """驗證執行數據"""
        with self.db.get_session() as session:
            new_count = session.execute("SELECT COUNT(*) FROM strategy_executions_v2").scalar()
            old_count = session.execute("SELECT COUNT(*) FROM strategy_executions").scalar()

            errors = []
            if new_count != old_count:
                errors.append(f"執行記錄數量不匹配: 新={new_count}, 舊={old_count}")

            return {
                "old_count": old_count,
                "new_count": new_count,
                "errors": errors
            }

    async def _validate_relationships(self) -> Dict[str, Any]:
        """驗證關聯關係"""
        with self.db.get_session() as session:
            # 檢查孤立的執行記錄
            orphaned_executions = session.execute("""
                SELECT COUNT(*) FROM strategy_executions_v2 e
                LEFT JOIN strategies s ON e.strategy_id = s.id
                WHERE s.id IS NULL
            """).scalar()

            errors = []
            if orphaned_executions > 0:
                errors.append(f"發現 {orphaned_executions} 條孤立的執行記錄")

            return {
                "orphaned_executions": orphaned_executions,
                "errors": errors
            }

    async def _validate_data_integrity(self) -> Dict[str, Any]:
        """驗證數據完整性"""
        errors = []

        # 檢查必要的字段
        with self.db.get_session() as session:
            null_names = session.execute("""
                SELECT COUNT(*) FROM strategies WHERE name IS NULL OR name = ''
            """).scalar()
            if null_names > 0:
                errors.append(f"發現 {null_names} 條記錄的策略名稱為空")

        return {
            "errors": errors
        }

    async def _drop_new_tables(self):
        """刪除新創建的表"""
        tables_to_drop = [
            'strategies',
            'strategy_executions_v2',
            'user_preferences_v2',
            'strategy_id_mapping'
        ]

        with self.db.get_session() as session:
            for table in tables_to_drop:
                try:
                    session.execute(f"DROP TABLE IF EXISTS {table}")
                    session.commit()
                except Exception as e:
                    logger.error(f"刪除表失敗 {table}: {e}")

    def log_migration(self, action: str, message: str, details: Optional[Dict] = None):
        """記錄遷移日誌"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "message": message,
            "details": details or {}
        }
        self.migration_log.append(log_entry)

    async def save_migration_log(self):
        """保存遷移日誌"""
        log_file = f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(self.migration_log, f, indent=2)
        logger.info(f"遷移日誌已保存: {log_file}")


async def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="策略模式遷移工具")
    parser.add_argument("--db-url", required=True, help="數據庫連接URL")
    parser.add_argument("--no-backup", action="store_true", help="跳過備份")
    parser.add_argument("--validate-only", action="store_true", help="只進行驗證")
    parser.add_argument("--dry-run", action="store_true", help="試運行模式")

    args = parser.parse_args()

    migrator = StrategySchemaMigrator(args.db_url)
    await migrator.initialize()

    if args.validate_only:
        # 只進行驗證
        result = await migrator.validate_migration()
        sys.exit(0 if result else 1)

    if args.dry_run:
        logger.info("試運行模式 - 不會執行實際遷移")
        # TODO: 實現試運行邏輯
        return

    # 執行遷移
    success = await migrator.migrate_all(backup=not args.no_backup)

    # 保存遷移日誌
    await migrator.save_migration_log()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())