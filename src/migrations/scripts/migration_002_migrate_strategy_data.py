"""
策略數據遷移腳本

將現有的策略配置、性能數據和回測結果遷移到統一模型。
"""

import os
import json
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ...database.connection import db_manager
from ...models import Strategy, StrategyConfig, StrategyPerformance, BacktestResult, StrategyCategory, User
from ..migration_script import MigrationScript

logger = logging.getLogger(__name__)

class MigrateStrategyDataMigration(MigrationScript):
    """策略數據遷移腳本"""

    def __init__(self):
        super().__init__(
            version="002",
            name="migrate_strategy_data",
            description="遷移CBSC策略配置、性能數據和回測結果到統一模型",
            author="Data Migration System"
        )
        self.data_sources = {
            "backtest_results": self._find_backtest_files(),
            "strategy_configs": self._find_config_files(),
            "strategy_templates": self._find_template_files()
        }

    def _find_backtest_files(self) -> List[str]:
        """查找回測結果文件"""
        patterns = [
            "*_backtest_results_*.json",
            "*optimization_results_*.json",
            "*analysis_report_*.json"
        ]
        files = []

        for pattern in patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.is_file() and file_path.stat().st_size > 100:
                    files.append(str(file_path))

        return files

    def _find_config_files(self) -> List[str]:
        """查找策略配置文件"""
        files = []
        config_paths = [
            "data/strategy_templates.db",
            "data/strategy_registry.db"
        ]

        for path in config_paths:
            if os.path.exists(path):
                files.append(path)

        return files

    def _find_template_files(self) -> List[str]:
        """查找策略模板文件"""
        files = []
        template_dirs = [
            "src/strategy/",
            "src/cbsc/"
        ]

        for dir_path in template_dirs:
            if os.path.exists(dir_path):
                for file_path in Path(dir_path).glob("*strategy*.py"):
                    files.append(str(file_path))

        return files

    def get_up_sql(self) -> str:
        """獲取升級SQL語句"""
        return "-- This migration uses Python logic for data migration"

    def get_down_sql(self) -> str:
        """獲取回滾SQL語句"""
        return """
        DELETE FROM strategy_performance WHERE strategy_id IN (
            SELECT id FROM strategies WHERE migrated_from_file IS NOT NULL
        );
        DELETE FROM strategy_configs WHERE strategy_id IN (
            SELECT id FROM strategies WHERE migrated_from_file IS NOT NULL
        );
        DELETE FROM strategies WHERE migrated_from_file IS NOT NULL;
        """

    async def execute_migration(self, session: AsyncSession) -> Dict[str, Any]:
        """執行數據遷移"""
        result = {
            "success": True,
            "strategies_migrated": 0,
            "configs_migrated": 0,
            "performance_records_migrated": 0,
            "backtest_results_migrated": 0,
            "errors": [],
            "migration_details": {}
        }

        try:
            # 1. 遷移回測結果數據
            backtest_migration = await self._migrate_backtest_results(session)
            result.update(backtest_migration)

            # 2. 遷移策略配置數據
            config_migration = await self._migrate_strategy_configs(session)
            result.update(config_migration)

            # 3. 從代碼文件創建策略模板
            template_migration = await self._create_strategy_templates(session)
            result.update(template_migration)

            await session.commit()
            logger.info(f"Strategy data migration completed: {result}")

        except Exception as e:
            await session.rollback()
            result["success"] = False
            result["errors"].append(f"Migration failed: {str(e)}")
            logger.error(f"Strategy data migration failed: {e}")

        return result

    async def _migrate_backtest_results(self, session: AsyncSession) -> Dict[str, Any]:
        """遷移回測結果數據"""
        result = {
            "backtest_results_migrated": 0,
            "performance_records_migrated": 0,
            "errors": []
        }

        try:
            # 創建默認用戶和分類（如果不存在）
            await self._ensure_default_user_and_category(session)

            for file_path in self.data_sources["backtest_results"]:
                try:
                    migration_result = await self._migrate_backtest_file(session, file_path)
                    result["backtest_results_migrated"] += migration_result.get("results", 0)
                    result["performance_records_migrated"] += migration_result.get("performances", 0)

                    logger.info(f"Migrated backtest file: {file_path}")

                except Exception as e:
                    result["errors"].append(f"Failed to migrate {file_path}: {str(e)}")
                    logger.error(f"Failed to migrate backtest file {file_path}: {e}")

        except Exception as e:
            result["errors"].append(f"Backtest migration failed: {str(e)}")
            logger.error(f"Backtest migration failed: {e}")

        return result

    async def _migrate_backtest_file(self, session: AsyncSession, file_path: str) -> Dict[str, Any]:
        """遷移單個回測文件"""
        result = {"results": 0, "performances": 0}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 解析文件數據
            symbol = data.get("symbol", "UNKNOWN")
            timestamp = data.get("timestamp", datetime.now().isoformat())
            summary = data.get("summary", {})
            top_strategies = data.get("top_strategies", [])

            if not top_strategies and summary:
                # 處理單策略格式
                top_strategies = [{
                    "strategy_name": data.get("strategy_name", "Default"),
                    "total_return": summary.get("total_return", 0),
                    "sharpe_ratio": summary.get("best_sharpe", summary.get("sharpe_ratio", 0)),
                    "max_drawdown": summary.get("max_drawdown", 0),
                    "win_rate": summary.get("win_rate", 0),
                    "total_trades": summary.get("total_trades", 0)
                }]

            # 遷移每個策略的結果
            for strategy_data in top_strategies:
                await self._create_strategy_and_backtest(session, strategy_data, symbol, timestamp, file_path)
                result["results"] += 1

            # 創建性能記錄
            if summary:
                await self._create_performance_metrics(session, symbol, summary, timestamp, file_path)
                result["performances"] += 1

        except Exception as e:
            logger.error(f"Failed to process backtest file {file_path}: {e}")
            raise

        return result

    async def _create_strategy_and_backtest(self, session: AsyncSession, strategy_data: Dict[str, Any],
                                           symbol: str, timestamp: str, source_file: str):
        """創建策略和回測結果記錄"""
        strategy_name = strategy_data.get("strategy_name", "Unknown Strategy")

        # 解析策略名稱和參數
        strategy_code, parameters = self._parse_strategy_name(strategy_name)

        # 查找或創建策略
        strategy = await self._find_or_create_strategy(session, strategy_name, strategy_code, parameters, source_file)

        # 創建回測結果
        backtest_data = {
            "strategy_id": strategy.id,
            "symbol": symbol,
            "total_return": strategy_data.get("total_return", 0),
            "sharpe_ratio": strategy_data.get("sharpe_ratio", 0),
            "max_drawdown": strategy_data.get("max_drawdown", 0),
            "win_rate": strategy_data.get("win_rate", 0),
            "total_trades": strategy_data.get("total_trades", 0),
            "profit_factor": strategy_data.get("profit_factor", 0),
            "volatility": strategy_data.get("volatility", 0),
            "backtest_date": datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date(),
            "metadata": {
                "source_file": source_file,
                "migration_date": datetime.now().isoformat(),
                "original_data": strategy_data
            }
        }

        backtest_result = BacktestResult(**backtest_data)
        session.add(backtest_result)

    async def _create_performance_metrics(self, session: AsyncSession, symbol: str,
                                        summary: Dict[str, Any], timestamp: str, source_file: str):
        """創建性能指標記錄"""
        metrics = [
            ("total_return", summary.get("total_return", 0), "decimal"),
            ("sharpe_ratio", summary.get("best_sharpe", 0), "decimal"),
            ("max_drawdown", summary.get("max_drawdown", 0), "decimal"),
            ("win_rate", summary.get("win_rate", 0), "decimal"),
            ("total_trades", summary.get("total_trades", 0), "integer")
        ]

        for metric_name, metric_value, metric_type in metrics:
            if metric_value is not None:
                performance_data = {
                    "metric_type": "backtest_summary",
                    "metric_name": metric_name,
                    "metric_value": float(metric_value) if isinstance(metric_value, (int, float)) else metric_value,
                    "metric_unit": "ratio" if "rate" in metric_name or metric_name == "sharpe_ratio" else "count" if metric_name == "total_trades" else "decimal",
                    "symbol": symbol,
                    "timestamp": datetime.fromisoformat(timestamp.replace('Z', '+00:00')),
                    "metadata": {
                        "source_file": source_file,
                        "migration_date": datetime.now().isoformat()
                    }
                }

                performance = PerformanceMetrics(**performance_data)
                session.add(performance)

    def _parse_strategy_name(self, strategy_name: str) -> tuple[str, Dict[str, Any]]:
        """解析策略名稱和參數"""
        # 示例: "RSI_MR_14_25_70" -> code="RSI_MR", parameters={"period":14, "oversold":25, "overbought":70}
        parts = strategy_name.split('_')

        if len(parts) >= 3 and parts[0] == "RSI" and parts[1] == "MR":
            code = "RSI_MR"
            parameters = {
                "period": int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 14,
                "oversold": int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 25,
                "overbought": int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 70
            }
        elif "RSI" in strategy_name:
            code = "RSI"
            parameters = {"period": 14}
        elif "MA" in strategy_name or "Moving" in strategy_name:
            code = "MA"
            parameters = {"short_period": 10, "long_period": 30}
        else:
            code = strategy_name.replace(' ', '_').upper()
            parameters = {}

        return code, parameters

    async def _find_or_create_strategy(self, session: AsyncSession, name: str, code: str,
                                     parameters: Dict[str, Any], source_file: str) -> Strategy:
        """查找或創建策略"""
        # 查找現有策略
        result = await session.execute(
            select(Strategy).where(Strategy.code == code, Strategy.name == name)
        )
        strategy = result.scalar_one_or_none()

        if not strategy:
            # 創建新策略
            strategy_data = {
                "name": name,
                "code": code,
                "description": f"Migrated from {source_file}",
                "status": "migrated",
                "risk_level": "medium",
                "parameters": parameters,
                "tags": ["migrated", "backtest"],
                "metadata": {
                    "source_file": source_file,
                    "migration_date": datetime.now().isoformat(),
                    "auto_migrated": True
                }
            }

            strategy = Strategy(**strategy_data)
            session.add(strategy)
            await session.flush()  # 獲取ID

            logger.info(f"Created new strategy: {name} (code: {code})")

        return strategy

    async def _ensure_default_user_and_category(self, session: AsyncSession):
        """確保默認用戶和分類存在"""
        # 檢查是否有管理員用戶
        result = await session.execute(select(User).where(User.email == "admin@cbsc.local"))
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@cbsc.local",
                password_hash="migration_placeholder",
                first_name="System",
                last_name="Administrator",
                is_active=True,
                is_verified=True,
                metadata={"auto_created": True, "migration_date": datetime.now().isoformat()}
            )
            session.add(admin_user)

        # 檢查是否有技術指標分類
        result = await session.execute(
            select(StrategyCategory).where(StrategyCategory.code == "technical_indicators")
        )
        tech_category = result.scalar_one_or_none()

        if not tech_category:
            tech_category = StrategyCategory(
                name="technical_indicators",
                display_name="技術指標策略",
                description="基於技術指標的交易策略",
                icon="trending-up",
                color="#3B82F6",
                is_active=True,
                metadata={"auto_created": True}
            )
            session.add(tech_category)

        await session.flush()

    async def _migrate_strategy_configs(self, session: AsyncSession) -> Dict[str, Any]:
        """遷移策略配置數據"""
        result = {
            "configs_migrated": 0,
            "errors": []
        }

        try:
            for config_file in self.data_sources["strategy_configs"]:
                try:
                    # 這裡可以添加從SQLite或其他數據庫讀取配置的邏輯
                    # 目前先跳過，因為主要數據在JSON文件中
                    logger.info(f"Skipping config file migration for: {config_file}")

                except Exception as e:
                    result["errors"].append(f"Failed to migrate config {config_file}: {str(e)}")
                    logger.error(f"Failed to migrate config file {config_file}: {e}")

        except Exception as e:
            result["errors"].append(f"Config migration failed: {str(e)}")
            logger.error(f"Config migration failed: {e}")

        return result

    async def _create_strategy_templates(self, session: AsyncSession) -> Dict[str, Any]:
        """從代碼文件創建策略模板"""
        result = {
            "templates_created": 0,
            "errors": []
        }

        try:
            # 這裡可以添加從Python代碼文件解析策略模板的邏輯
            # 目前先跳過，專注於現有JSON數據的遷移
            logger.info("Strategy template creation skipped for now")

        except Exception as e:
            result["errors"].append(f"Template creation failed: {str(e)}")
            logger.error(f"Template creation failed: {e}")

        return result

    async def validate_migration(self, session: AsyncSession) -> Dict[str, Any]:
        """驗證遷移結果"""
        result = {
            "success": True,
            "strategies_count": 0,
            "backtest_results_count": 0,
            "performance_metrics_count": 0,
            "errors": []
        }

        try:
            # 統計遷移的數據
            strategies_result = await session.execute(select(Strategy).where(Strategy.metadata['source_file'].isnot(None)))
            result["strategies_count"] = len(strategies_result.scalars().all())

            backtest_result = await session.execute(
                select(BacktestResult).where(BacktestResult.metadata['source_file'].isnot(None))
            )
            result["backtest_results_count"] = len(backtest_result.scalars().all())

            performance_result = await session.execute(
                select(PerformanceMetrics).where(PerformanceMetrics.metadata['source_file'].isnot(None))
            )
            result["performance_metrics_count"] = len(performance_result.scalars().all())

            # 驗證數據完整性
            if result["strategies_count"] == 0 and result["backtest_results_count"] == 0:
                result["success"] = False
                result["errors"].append("No strategy data was migrated")

            logger.info(f"Strategy migration validation: {result}")

        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Validation failed: {str(e)}")
            logger.error(f"Strategy migration validation failed: {e}")

        return result

# 註冊遷移腳本
migration = MigrateStrategyDataMigration()