#!/usr/bin/env python3
"""
CBSC策略數據遷移工具 (Task #005)
CBSC Strategy Data Migration Tool

提供現有CBSC策略數據到新統一架構的遷移功能
"""

import asyncio
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np

from .strategy_management_api import (
    Strategy, StrategyType, StrategyStatus, StrategyParameters,
    StrategySignal, StrategyPerformance, DataCompatibilityAdapter
)

logger = logging.getLogger(__name__)

# ============================================================================
# 遷移配置 (Migration Configuration)
# ============================================================================

class MigrationConfig:
    """遷移配置"""

    def __init__(self,
                 source_data_path: str,
                 target_data_path: str,
                 backup_path: str = None,
                 enable_dry_run: bool = True,
                 batch_size: int = 100,
                 validate_data: bool = True):
        self.source_data_path = Path(source_data_path)
        self.target_data_path = Path(target_data_path)
        self.backup_path = Path(backup_path) if backup_path else None
        self.enable_dry_run = enable_dry_run
        self.batch_size = batch_size
        self.validate_data = validate_data

        # 確保目標目錄存在
        self.target_data_path.mkdir(parents=True, exist_ok=True)

        if self.backup_path:
            self.backup_path.mkdir(parents=True, exist_ok=True)

# ============================================================================
# 數據源適配器 (Data Source Adapters)
# ============================================================================

class DataSourceAdapter:
    """數據源適配器基類"""

    def __init__(self, source_path: Path):
        self.source_path = source_path

    async def load_strategies(self) -> List[Dict[str, Any]]:
        """加載策略數據"""
        raise NotImplementedError

    async def load_signals(self) -> List[Dict[str, Any]]:
        """加載信號數據"""
        raise NotImplementedError

    async def load_performances(self) -> List[Dict[str, Any]]:
        """加載性能數據"""
        raise NotImplementedError

class JSONDataSourceAdapter(DataSourceAdapter):
    """JSON數據源適配器"""

    async def load_strategies(self) -> List[Dict[str, Any]]:
        """從JSON文件加載策略數據"""
        try:
            strategies_file = self.source_path / "strategies.json"
            if not strategies_file.exists():
                logger.warning(f"策略文件不存在: {strategies_file}")
                return []

            with open(strategies_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            strategies = data if isinstance(data, list) else data.get('strategies', [])
            logger.info(f"從JSON加載 {len(strategies)} 個策略")
            return strategies

        except Exception as e:
            logger.error(f"從JSON加載策略失敗: {e}")
            return []

    async def load_signals(self) -> List[Dict[str, Any]]:
        """從JSON文件加載信號數據"""
        try:
            signals_file = self.source_path / "signals.json"
            if not signals_file.exists():
                logger.warning(f"信號文件不存在: {signals_file}")
                return []

            with open(signals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            signals = data if isinstance(data, list) else data.get('signals', [])
            logger.info(f"從JSON加載 {len(signals)} 個信號")
            return signals

        except Exception as e:
            logger.error(f"從JSON加載信號失敗: {e}")
            return []

    async def load_performances(self) -> List[Dict[str, Any]]:
        """從JSON文件加載性能數據"""
        try:
            performances_file = self.source_path / "performances.json"
            if not performances_file.exists():
                logger.warning(f"性能文件不存在: {performances_file}")
                return []

            with open(performances_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            performances = data if isinstance(data, list) else data.get('performances', [])
            logger.info(f"從JSON加載 {len(performances)} 個性能記錄")
            return performances

        except Exception as e:
            logger.error(f"從JSON加載性能失敗: {e}")
            return []

class SQLiteDataSourceAdapter(DataSourceAdapter):
    """SQLite數據源適配器"""

    async def load_strategies(self) -> List[Dict[str, Any]]:
        """從SQLite數據庫加載策略數據"""
        try:
            db_path = self.source_path / "strategies.db"
            if not db_path.exists():
                logger.warning(f"數據庫文件不存在: {db_path}")
                return []

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 查詢策略表
            cursor.execute("""
                SELECT id, name, description, strategy_type, parameters,
                       status, is_active, created_at, updated_at, last_executed
                FROM strategies
            """)

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            strategies = []
            for row in rows:
                strategy_dict = dict(zip(columns, row))
                # 解析JSON參數
                if strategy_dict.get('parameters'):
                    strategy_dict['parameters'] = json.loads(strategy_dict['parameters'])
                strategies.append(strategy_dict)

            conn.close()
            logger.info(f"從SQLite加載 {len(strategies)} 個策略")
            return strategies

        except Exception as e:
            logger.error(f"從SQLite加載策略失敗: {e}")
            return []

    async def load_signals(self) -> List[Dict[str, Any]]:
        """從SQLite數據庫加載信號數據"""
        try:
            db_path = self.source_path / "strategies.db"
            if not db_path.exists():
                return []

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT signal_id, strategy_type, signal_type, strength, confidence,
                       timestamp, market_data, parameters, metadata
                FROM signals
            """)

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            signals = []
            for row in rows:
                signal_dict = dict(zip(columns, row))
                # 解析JSON字段
                for field in ['market_data', 'parameters', 'metadata']:
                    if signal_dict.get(field):
                        signal_dict[field] = json.loads(signal_dict[field])
                signals.append(signal_dict)

            conn.close()
            logger.info(f"從SQLite加載 {len(signals)} 個信號")
            return signals

        except Exception as e:
            logger.error(f"從SQLite加載信號失敗: {e}")
            return []

    async def load_performances(self) -> List[Dict[str, Any]]:
        """從SQLite數據庫加載性能數據"""
        try:
            db_path = self.source_path / "strategies.db"
            if not db_path.exists():
                return []

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT strategy_id, strategy_type, total_return, annual_return,
                       sharpe_ratio, max_drawdown, win_rate, profit_factor,
                       calmar_ratio, total_trades, profit_trades, avg_profit,
                       avg_loss, last_updated
                FROM strategy_performances
            """)

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            performances = []
            for row in rows:
                perf_dict = dict(zip(columns, row))
                performances.append(perf_dict)

            conn.close()
            logger.info(f"從SQLite加載 {len(performances)} 個性能記錄")
            return performances

        except Exception as e:
            logger.error(f"從SQLite加載性能失敗: {e}")
            return []

class CSVDataSourceAdapter(DataSourceAdapter):
    """CSV數據源適配器"""

    async def load_strategies(self) -> List[Dict[str, Any]]:
        """從CSV文件加載策略數據"""
        try:
            strategies_file = self.source_path / "strategies.csv"
            if not strategies_file.exists():
                logger.warning(f"策略文件不存在: {strategies_file}")
                return []

            df = pd.read_csv(strategies_file)
            strategies = df.to_dict('records')

            # 處理日期和參數字段
            for strategy in strategies:
                for field in ['created_at', 'updated_at', 'last_executed']:
                    if strategy.get(field) and pd.notna(strategy[field]):
                        strategy[field] = pd.to_datetime(strategy[field]).isoformat()

                # 解析參數JSON
                if strategy.get('parameters'):
                    try:
                        strategy['parameters'] = json.loads(strategy['parameters'])
                    except:
                        strategy['parameters'] = {}

            logger.info(f"從CSV加載 {len(strategies)} 個策略")
            return strategies

        except Exception as e:
            logger.error(f"從CSV加載策略失敗: {e}")
            return []

    async def load_signals(self) -> List[Dict[str, Any]]:
        """從CSV文件加載信號數據"""
        try:
            signals_file = self.source_path / "signals.csv"
            if not signals_file.exists():
                return []

            df = pd.read_csv(signals_file)
            signals = df.to_dict('records')

            # 處理時間戳和JSON字段
            for signal in signals:
                if signal.get('timestamp') and pd.notna(signal['timestamp']):
                    signal['timestamp'] = pd.to_datetime(signal['timestamp']).isoformat()

                for field in ['market_data', 'parameters', 'metadata']:
                    if signal.get(field):
                        try:
                            signal[field] = json.loads(signal[field])
                        except:
                            signal[field] = {}

            logger.info(f"從CSV加載 {len(signals)} 個信號")
            return signals

        except Exception as e:
            logger.error(f"從CSV加載信號失敗: {e}")
            return []

    async def load_performances(self) -> List[Dict[str, Any]]:
        """從CSV文件加載性能數據"""
        try:
            performances_file = self.source_path / "performances.csv"
            if not performances_file.exists():
                return []

            df = pd.read_csv(performances_file)
            performances = df.to_dict('records')

            logger.info(f"從CSV加載 {len(performances)} 個性能記錄")
            return performances

        except Exception as e:
            logger.error(f"從CSV加載性能失敗: {e}")
            return []

# ============================================================================
# 數據遷移器 (Data Migrator)
# ============================================================================

class StrategyDataMigrator:
    """策略數據遷移器"""

    def __init__(self, config: MigrationConfig):
        self.config = config
        self.logger = logging.getLogger("strategy_data_migrator")

        # 遷移統計
        self.migration_stats = {
            "strategies_migrated": 0,
            "strategies_failed": 0,
            "signals_migrated": 0,
            "signals_failed": 0,
            "performances_migrated": 0,
            "performances_failed": 0,
            "validation_errors": [],
            "migration_warnings": []
        }

    async def migrate_all_data(self) -> Dict[str, Any]:
        """遷移所有數據"""
        try:
            self.logger.info("開始數據遷移")
            start_time = datetime.now()

            # 檢測數據源類型並創建適配器
            data_source_adapter = self._create_data_source_adapter()

            # 創建備份
            if not self.config.enable_dry_run and self.config.backup_path:
                await self._create_backup(data_source_adapter)

            # 遷移策略
            await self._migrate_strategies(data_source_adapter)

            # 遷移信號
            await self._migrate_signals(data_source_adapter)

            # 遷移性能數據
            await self._migrate_performances(data_source_adapter)

            # 生成遷移報告
            migration_time = datetime.now() - start_time
            report = self._generate_migration_report(migration_time)

            self.logger.info(f"數據遷移完成，耗時: {migration_time}")
            return report

        except Exception as e:
            self.logger.error(f"數據遷移失敗: {e}")
            raise

    def _create_data_source_adapter(self) -> DataSourceAdapter:
        """創建數據源適配器"""
        source_path = self.config.source_data_path

        # 檢測數據源類型
        if (source_path / "strategies.db").exists():
            self.logger.info("檢測到SQLite數據源")
            return SQLiteDataSourceAdapter(source_path)
        elif (source_path / "strategies.json").exists():
            self.logger.info("檢測到JSON數據源")
            return JSONDataSourceAdapter(source_path)
        elif (source_path / "strategies.csv").exists():
            self.logger.info("檢測到CSV數據源")
            return CSVDataSourceAdapter(source_path)
        else:
            raise ValueError(f"無法識別的數據源格式: {source_path}")

    async def _create_backup(self, data_source_adapter: DataSourceAdapter):
        """創建數據備份"""
        try:
            self.logger.info("創建數據備份")

            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.config.backup_path / f"backup_{backup_timestamp}"
            backup_dir.mkdir(exist_ok=True)

            # 備份策略數據
            strategies = await data_source_adapter.load_strategies()
            if strategies:
                with open(backup_dir / "strategies_backup.json", 'w', encoding='utf-8') as f:
                    json.dump(strategies, f, indent=2, ensure_ascii=False, default=str)

            # 備份信號數據
            signals = await data_source_adapter.load_signals()
            if signals:
                with open(backup_dir / "signals_backup.json", 'w', encoding='utf-8') as f:
                    json.dump(signals, f, indent=2, ensure_ascii=False, default=str)

            # 備份性能數據
            performances = await data_source_adapter.load_performances()
            if performances:
                with open(backup_dir / "performances_backup.json", 'w', encoding='utf-8') as f:
                    json.dump(performances, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"數據備份完成: {backup_dir}")

        except Exception as e:
            self.logger.error(f"創建備份失敗: {e}")
            raise

    async def _migrate_strategies(self, data_source_adapter: DataSourceAdapter):
        """遷移策略數據"""
        try:
            self.logger.info("開始遷移策略數據")

            # 加載原始策略數據
            legacy_strategies = await data_source_adapter.load_strategies()

            if not legacy_strategies:
                self.logger.warning("沒有找到策略數據")
                return

            # 分批處理
            migrated_strategies = []
            for i in range(0, len(legacy_strategies), self.config.batch_size):
                batch = legacy_strategies[i:i + self.config.batch_size]
                batch_migrated = await self._migrate_strategy_batch(batch)
                migrated_strategies.extend(batch_migrated)

            # 保存遷移後的策略
            if not self.config.enable_dry_run:
                await self._save_migrated_strategies(migrated_strategies)

            self.logger.info(f"策略遷移完成: {len(migrated_strategies)}/{len(legacy_strategies)}")

        except Exception as e:
            self.logger.error(f"策略遷移失敗: {e}")
            raise

    async def _migrate_strategy_batch(self, legacy_strategies: List[Dict[str, Any]]) -> List[Strategy]:
        """遷移策略批次"""
        migrated_strategies = []

        for legacy_strategy in legacy_strategies:
            try:
                # 使用兼容性適配器轉換
                adapted_strategy = DataCompatibilityAdapter.adapt_legacy_strategy_format(legacy_strategy)

                # 驗證策略
                if self.config.validate_data:
                    validation_result = self._validate_migrated_strategy(adapted_strategy)
                    if not validation_result["is_valid"]:
                        self.migration_stats["validation_errors"].append({
                            "strategy_id": adapted_strategy.id,
                            "errors": validation_result["errors"]
                        })
                        continue

                migrated_strategies.append(adapted_strategy)
                self.migration_stats["strategies_migrated"] += 1

            except Exception as e:
                self.logger.error(f"遷移策略失敗 {legacy_strategy.get('id', 'unknown')}: {e}")
                self.migration_stats["strategies_failed"] += 1

        return migrated_strategies

    async def _migrate_signals(self, data_source_adapter: DataSourceAdapter):
        """遷移信號數據"""
        try:
            self.logger.info("開始遷移信號數據")

            # 加載原始信號數據
            legacy_signals = await data_source_adapter.load_signals()

            if not legacy_signals:
                self.logger.warning("沒有找到信號數據")
                return

            # 分批處理
            migrated_signals = []
            for i in range(0, len(legacy_signals), self.config.batch_size):
                batch = legacy_signals[i:i + self.config.batch_size]
                batch_migrated = await self._migrate_signal_batch(batch)
                migrated_signals.extend(batch_migrated)

            # 保存遷移後的信號
            if not self.config.enable_dry_run:
                await self._save_migrated_signals(migrated_signals)

            self.logger.info(f"信號遷移完成: {len(migrated_signals)}/{len(legacy_signals)}")

        except Exception as e:
            self.logger.error(f"信號遷移失敗: {e}")
            raise

    async def _migrate_signal_batch(self, legacy_signals: List[Dict[str, Any]]) -> List[StrategySignal]:
        """遷移信號批次"""
        migrated_signals = []

        for legacy_signal in legacy_signals:
            try:
                # 使用兼容性適配器轉換
                adapted_signal = DataCompatibilityAdapter.adapt_legacy_signal_format(legacy_signal)

                migrated_signals.append(adapted_signal)
                self.migration_stats["signals_migrated"] += 1

            except Exception as e:
                self.logger.error(f"遷移信號失敗 {legacy_signal.get('signal_id', 'unknown')}: {e}")
                self.migration_stats["signals_failed"] += 1

        return migrated_signals

    async def _migrate_performances(self, data_source_adapter: DataSourceAdapter):
        """遷移性能數據"""
        try:
            self.logger.info("開始遷移性能數據")

            # 加載原始性能數據
            legacy_performances = await data_source_adapter.load_performances()

            if not legacy_performances:
                self.logger.warning("沒有找到性能數據")
                return

            # 分批處理
            migrated_performances = []
            for i in range(0, len(legacy_performances), self.config.batch_size):
                batch = legacy_performances[i:i + self.config.batch_size]
                batch_migrated = await self._migrate_performance_batch(batch)
                migrated_performances.extend(batch_migrated)

            # 保存遷移後的性能數據
            if not self.config.enable_dry_run:
                await self._save_migrated_performances(migrated_performances)

            self.logger.info(f"性能數據遷移完成: {len(migrated_performances)}/{len(legacy_performances)}")

        except Exception as e:
            self.logger.error(f"性能數據遷移失敗: {e}")
            raise

    async def _migrate_performance_batch(self, legacy_performances: List[Dict[str, Any]]) -> List[StrategyPerformance]:
        """遷移性能數據批次"""
        migrated_performances = []

        for legacy_performance in legacy_performances:
            try:
                # 轉換性能數據
                performance = StrategyPerformance(
                    strategy_type=StrategyType(legacy_performance.get('strategy_type', 'direct_rsi')),
                    total_return=float(legacy_performance.get('total_return', 0)),
                    annual_return=float(legacy_performance.get('annual_return', 0)),
                    sharpe_ratio=float(legacy_performance.get('sharpe_ratio', 0)),
                    max_drawdown=float(legacy_performance.get('max_drawdown', 0)),
                    win_rate=float(legacy_performance.get('win_rate', 0)),
                    profit_factor=float(legacy_performance.get('profit_factor', 0)),
                    calmar_ratio=float(legacy_performance.get('calmar_ratio', 0)),
                    total_trades=int(legacy_performance.get('total_trades', 0)),
                    profit_trades=int(legacy_performance.get('profit_trades', 0)),
                    avg_profit=float(legacy_performance.get('avg_profit', 0)),
                    avg_loss=float(legacy_performance.get('avg_loss', 0)),
                    last_updated=datetime.fromisoformat(legacy_performance.get('last_updated', datetime.now().isoformat()))
                )

                migrated_performances.append(performance)
                self.migration_stats["performances_migrated"] += 1

            except Exception as e:
                self.logger.error(f"遷移性能數據失敗 {legacy_performance.get('strategy_id', 'unknown')}: {e}")
                self.migration_stats["performances_failed"] += 1

        return migrated_performances

    def _validate_migrated_strategy(self, strategy: Strategy) -> Dict[str, Any]:
        """驗證遷移後的策略"""
        errors = []

        # 檢查必需字段
        if not strategy.id:
            errors.append("策略ID不能為空")

        if not strategy.name:
            errors.append("策略名稱不能為空")

        if not strategy.strategy_type:
            errors.append("策略類型不能為空")

        # 檢查參數
        if not strategy.parameters:
            errors.append("策略參數不能為空")

        # 檢查時間戳
        if strategy.created_at > datetime.now():
            errors.append("創建時間不能未來")

        if strategy.updated_at < strategy.created_at:
            errors.append("更新時間不能早於創建時間")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }

    async def _save_migrated_strategies(self, strategies: List[Strategy]):
        """保存遷移後的策略"""
        try:
            strategies_data = [strategy.dict() for strategy in strategies]

            with open(self.config.target_data_path / "migrated_strategies.json", 'w', encoding='utf-8') as f:
                json.dump(strategies_data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            self.logger.error(f"保存遷移策略失敗: {e}")
            raise

    async def _save_migrated_signals(self, signals: List[StrategySignal]):
        """保存遷移後的信號"""
        try:
            signals_data = [signal.dict() for signal in signals]

            with open(self.config.target_data_path / "migrated_signals.json", 'w', encoding='utf-8') as f:
                json.dump(signals_data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            self.logger.error(f"保存遷移信號失敗: {e}")
            raise

    async def _save_migrated_performances(self, performances: List[StrategyPerformance]):
        """保存遷移後的性能數據"""
        try:
            performances_data = [performance.dict() for performance in performances]

            with open(self.config.target_data_path / "migrated_performances.json", 'w', encoding='utf-8') as f:
                json.dump(performances_data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            self.logger.error(f"保存遷移性能數據失敗: {e}")
            raise

    def _generate_migration_report(self, migration_time: timedelta) -> Dict[str, Any]:
        """生成遷移報告"""
        report = {
            "migration_completed": True,
            "migration_time": str(migration_time),
            "dry_run": self.config.enable_dry_run,
            "statistics": self.migration_stats.copy(),
            "source_path": str(self.config.source_data_path),
            "target_path": str(self.config.target_data_path),
            "backup_path": str(self.config.backup_path) if self.config.backup_path else None
        }

        # 保存報告
        report_path = self.config.target_data_path / f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        self.logger.info(f"遷移報告已保存: {report_path}")
        return report

# ============================================================================
# 工具函數 (Utility Functions)
# ============================================================================

async def run_strategy_migration(
    source_path: str,
    target_path: str,
    backup_path: str = None,
    enable_dry_run: bool = True
) -> Dict[str, Any]:
    """運行策略數據遷移"""
    try:
        # 配置遷移
        config = MigrationConfig(
            source_data_path=source_path,
            target_data_path=target_path,
            backup_path=backup_path,
            enable_dry_run=enable_dry_run,
            batch_size=100,
            validate_data=True
        )

        # 創建遷移器
        migrator = StrategyDataMigrator(config)

        # 執行遷移
        return await migrator.migrate_all_data()

    except Exception as e:
        logger.error(f"運行策略遷移失敗: {e}")
        raise

def detect_data_source_format(source_path: str) -> str:
    """檢測數據源格式"""
    source = Path(source_path)

    if (source / "strategies.db").exists():
        return "sqlite"
    elif (source / "strategies.json").exists():
        return "json"
    elif (source / "strategies.csv").exists():
        return "csv"
    else:
        return "unknown"

# ============================================================================
# 導出 (Exports)
# ============================================================================

__all__ = [
    "MigrationConfig",
    "DataSourceAdapter",
    "JSONDataSourceAdapter",
    "SQLiteDataSourceAdapter",
    "CSVDataSourceAdapter",
    "StrategyDataMigrator",
    "run_strategy_migration",
    "detect_data_source_format"
]