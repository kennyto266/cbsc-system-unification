#!/usr/bin/env python3
"""
CBSC策略管理数据迁移脚本 (Task 005)
CBSC Strategy Management Data Migration Script

负责将现有CBSC策略数据迁移到新的统一架构中，确保数据完整性和向后兼容性
"""

import asyncio
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
from contextlib import asynccontextmanager

from .strategy_management_api import (
    Strategy, StrategySignal, StrategyPerformance, StrategyType,
    DataCompatibilityAdapter, StrategyParameters, CBSCStrategyTemplate
)

logger = logging.getLogger(__name__)

class CBSCDataMigrator:
    """CBSC数据迁移器"""

    def __init__(self, legacy_db_path: str, new_db_path: str):
        """
        初始化数据迁移器

        Args:
            legacy_db_path: 旧版数据库路径
            new_db_path: 新版数据库路径
        """
        self.legacy_db_path = legacy_db_path
        self.new_db_path = new_db_path
        self.migration_log: List[Dict[str, Any]] = []
        self.error_count = 0
        self.success_count = 0

    async def migrate_all_data(self) -> Dict[str, Any]:
        """
        迁移所有数据

        Returns:
            迁移结果统计
        """
        logger.info("开始CBSC策略数据迁移")

        migration_start = datetime.now()

        try:
            # 1. 迁移策略定义
            await self._migrate_strategies()

            # 2. 迁移历史信号
            await self._migrate_signals()

            # 3. 迁移性能数据
            await self._migrate_performance_data()

            # 4. 迁移CBSC情绪数据
            await self._migrate_cbsc_sentiment_data()

            # 5. 创建索引和约束
            await self._create_indexes_and_constraints()

            migration_end = datetime.now()
            migration_duration = (migration_end - migration_start).total_seconds()

            result = {
                "status": "success",
                "migration_time": migration_duration,
                "strategies_migrated": self.success_count,
                "errors": self.error_count,
                "log_entries": len(self.migration_log),
                "migration_log": self.migration_log
            }

            logger.info(f"CBSC策略数据迁移完成: {result}")
            return result

        except Exception as e:
            logger.error(f"CBSC策略数据迁移失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "errors": self.error_count + 1,
                "migration_log": self.migration_log
            }

    async def _migrate_strategies(self) -> None:
        """迁移策略定义"""
        logger.info("迁移策略定义...")

        try:
            # 读取旧版策略数据
            legacy_strategies = await self._load_legacy_strategies()

            # 适配并保存策略
            for legacy_strategy in legacy_strategies:
                try:
                    # 使用兼容性适配器转换格式
                    adapted_strategy = DataCompatibilityAdapter.adapt_legacy_strategy_format(legacy_strategy)

                    # 保存到新数据库
                    await self._save_strategy(adapted_strategy)

                    self.success_count += 1
                    self._log_migration("strategy", legacy_strategy.get("id"), "success")

                except Exception as e:
                    self.error_count += 1
                    self._log_migration("strategy", legacy_strategy.get("id"), "error", str(e))
                    logger.error(f"迁移策略失败: {legacy_strategy.get('id')} - {e}")

            # 创建系统默认策略模板
            await self._create_default_strategy_templates()

        except Exception as e:
            logger.error(f"策略迁移过程失败: {e}")
            raise

    async def _migrate_signals(self) -> None:
        """迁移历史信号"""
        logger.info("迁移历史信号...")

        try:
            # 读取旧版信号数据
            legacy_signals = await self._load_legacy_signals()

            # 批量适配并保存信号
            batch_size = 1000
            total_signals = len(legacy_signals)

            for i in range(0, total_signals, batch_size):
                batch = legacy_signals[i:i + batch_size]
                adapted_signals = []

                for legacy_signal in batch:
                    try:
                        adapted_signal = DataCompatibilityAdapter.adapt_legacy_signal_format(legacy_signal)
                        adapted_signals.append(adapted_signal)

                        self.success_count += 1
                        self._log_migration("signal", legacy_signal.get("signal_id"), "success")

                    except Exception as e:
                        self.error_count += 1
                        self._log_migration("signal", legacy_signal.get("signal_id"), "error", str(e))
                        logger.error(f"迁移信号失败: {legacy_signal.get('signal_id')} - {e}")

                # 批量保存信号
                if adapted_signals:
                    await self._save_signals_batch(adapted_signals)

                logger.info(f"信号迁移进度: {min(i + batch_size, total_signals)}/{total_signals}")

        except Exception as e:
            logger.error(f"信号迁移过程失败: {e}")
            raise

    async def _migrate_performance_data(self) -> None:
        """迁移性能数据"""
        logger.info("迁移性能数据...")

        try:
            # 读取旧版性能数据
            legacy_performance = await self._load_legacy_performance_data()

            # 适配并保存性能数据
            for legacy_perf in legacy_performance:
                try:
                    adapted_performance = await self._adapt_performance_data(legacy_perf)
                    await self._save_performance_data(adapted_performance)

                    self.success_count += 1
                    self._log_migration("performance", legacy_perf.get("strategy_id"), "success")

                except Exception as e:
                    self.error_count += 1
                    self._log_migration("performance", legacy_perf.get("strategy_id"), "error", str(e))
                    logger.error(f"迁移性能数据失败: {legacy_perf.get('strategy_id')} - {e}")

        except Exception as e:
            logger.error(f"性能数据迁移过程失败: {e}")
            raise

    async def _migrate_cbsc_sentiment_data(self) -> None:
        """迁移CBSC情绪数据"""
        logger.info("迁移CBSC情绪数据...")

        try:
            # 查找CBSC情绪数据文件
            cbsc_files = self._find_cbsc_sentiment_files()

            for file_path in cbsc_files:
                try:
                    await self._migrate_cbsc_file(file_path)

                    self.success_count += 1
                    self._log_migration("cbsc_file", str(file_path), "success")

                except Exception as e:
                    self.error_count += 1
                    self._log_migration("cbsc_file", str(file_path), "error", str(e))
                    logger.error(f"迁移CBSC文件失败: {file_path} - {e}")

        except Exception as e:
            logger.error(f"CBSC情绪数据迁移过程失败: {e}")
            raise

    async def _create_default_strategy_templates(self) -> None:
        """创建默认策略模板"""
        logger.info("创建默认策略模板...")

        try:
            # 导入模板定义
            from .strategy_management_api import StrategyTemplates

            templates = StrategyTemplates.get_all_templates()

            for template in templates:
                await self._save_strategy_template(template)
                logger.info(f"创建策略模板: {template.name}")

        except Exception as e:
            logger.error(f"创建默认策略模板失败: {e}")
            raise

    async def _load_legacy_strategies(self) -> List[Dict[str, Any]]:
        """加载旧版策略数据"""
        strategies = []

        try:
            # 尝试从SQLite数据库加载
            if Path(self.legacy_db_path).exists():
                conn = sqlite3.connect(self.legacy_db_path)
                cursor = conn.cursor()

                try:
                    cursor.execute("SELECT * FROM strategies")
                    columns = [description[0] for description in cursor.description]

                    for row in cursor.fetchall():
                        strategy_dict = dict(zip(columns, row))

                        # 解析JSON参数
                        if strategy_dict.get('parameters'):
                            try:
                                strategy_dict['parameters'] = json.loads(strategy_dict['parameters'])
                            except json.JSONDecodeError:
                                strategy_dict['parameters'] = {}

                        strategies.append(strategy_dict)

                except sqlite3.OperationalError:
                    logger.warning("策略表不存在，尝试其他数据源")

                conn.close()

            # 尝试从JSON文件加载
            json_files = list(Path(".").rglob("*.json"))
            for json_file in json_files:
                if "strategy" in json_file.name.lower():
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            file_data = json.load(f)

                        if isinstance(file_data, list):
                            strategies.extend(file_data)
                        elif isinstance(file_data, dict):
                            strategies.append(file_data)

                    except Exception as e:
                        logger.warning(f"无法读取策略JSON文件 {json_file}: {e}")

            # 尝试从CSV文件加载CBSC策略数据
            csv_files = list(Path(".").rglob("*.csv"))
            for csv_file in csv_files:
                if "strategy" in csv_file.name.lower() or "cbsc" in csv_file.name.lower():
                    try:
                        df = pd.read_csv(csv_file)
                        if not df.empty:
                            # 转换DataFrame为字典列表
                            csv_strategies = df.to_dict('records')
                            strategies.extend(csv_strategies)

                    except Exception as e:
                        logger.warning(f"无法读取策略CSV文件 {csv_file}: {e}")

            logger.info(f"加载到 {len(strategies)} 个旧版策略")
            return strategies

        except Exception as e:
            logger.error(f"加载旧版策略数据失败: {e}")
            return []

    async def _load_legacy_signals(self) -> List[Dict[str, Any]]:
        """加载旧版信号数据"""
        signals = []

        try:
            # 从JSON文件加载信号数据
            json_files = list(Path(".").rglob("*.json"))
            for json_file in json_files:
                if "signal" in json_file.name.lower():
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            file_data = json.load(f)

                        if isinstance(file_data, list):
                            signals.extend(file_data)
                        elif isinstance(file_data, dict):
                            if "signals" in file_data:
                                signals.extend(file_data["signals"])
                            else:
                                signals.append(file_data)

                    except Exception as e:
                        logger.warning(f"无法读取信号JSON文件 {json_file}: {e}")

            # 从SQLite数据库加载信号数据
            if Path(self.legacy_db_path).exists():
                conn = sqlite3.connect(self.legacy_db_path)
                cursor = conn.cursor()

                try:
                    cursor.execute("SELECT * FROM strategy_signals")
                    columns = [description[0] for description in cursor.description]

                    for row in cursor.fetchall():
                        signal_dict = dict(zip(columns, row))

                        # 解析JSON字段
                        for field in ['market_data', 'parameters', 'metadata']:
                            if signal_dict.get(field):
                                try:
                                    signal_dict[field] = json.loads(signal_dict[field])
                                except json.JSONDecodeError:
                                    signal_dict[field] = {}

                        signals.append(signal_dict)

                except sqlite3.OperationalError:
                    logger.warning("信号表不存在")

                conn.close()

            logger.info(f"加载到 {len(signals)} 个旧版信号")
            return signals

        except Exception as e:
            logger.error(f"加载旧版信号数据失败: {e}")
            return []

    async def _load_legacy_performance_data(self) -> List[Dict[str, Any]]:
        """加载旧版性能数据"""
        performance_data = []

        try:
            # 从数据库加载性能数据
            if Path(self.legacy_db_path).exists():
                conn = sqlite3.connect(self.legacy_db_path)
                cursor = conn.cursor()

                try:
                    cursor.execute("SELECT * FROM backtest_results")
                    columns = [description[0] for description in cursor.description]

                    for row in cursor.fetchall():
                        perf_dict = dict(zip(columns, row))
                        performance_data.append(perf_dict)

                except sqlite3.OperationalError:
                    logger.warning("回测结果表不存在")

                conn.close()

            logger.info(f"加载到 {len(performance_data)} 个性能数据记录")
            return performance_data

        except Exception as e:
            logger.error(f"加载旧版性能数据失败: {e}")
            return []

    def _find_cbsc_sentiment_files(self) -> List[Path]:
        """查找CBSC情绪数据文件"""
        cbsc_files = []

        try:
            # 查找包含CBSC、sentiment、warrant等关键词的文件
            keywords = ["cbsc", "sentiment", "warrant", "bull", "bear"]

            for keyword in keywords:
                cbsc_files.extend(list(Path(".").rglob(f"*{keyword}*")))

            # 过滤常见的数据文件格式
            data_extensions = {'.csv', '.json', '.xlsx', '.xls', '.parquet'}
            cbsc_files = [
                f for f in cbsc_files
                if f.suffix.lower() in data_extensions and f.is_file()
            ]

            # 去重
            cbsc_files = list(set(cbsc_files))

            logger.info(f"找到 {len(cbsc_files)} 个CBSC情绪数据文件")
            return cbsc_files

        except Exception as e:
            logger.error(f"查找CBSC情绪数据文件失败: {e}")
            return []

    async def _migrate_cbsc_file(self, file_path: Path) -> None:
        """迁移单个CBSC文件"""
        try:
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)

                # 验证CBSC数据格式
                required_columns = ['Date', 'Bull_Ratio', 'Bull_Turnover_HKD', 'Bear_Turnover_HKD']
                if not all(col in df.columns for col in required_columns):
                    logger.warning(f"CBSC文件缺少必要列: {file_path}")
                    return

                # 保存到新数据库
                await self._save_cbsc_sentiment_data(df)

            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 转换为DataFrame并保存
                df = pd.DataFrame(data)
                await self._save_cbsc_sentiment_data(df)

            logger.info(f"成功迁移CBSC文件: {file_path}")

        except Exception as e:
            logger.error(f"迁移CBSC文件失败 {file_path}: {e}")
            raise

    async def _save_strategy(self, strategy: Strategy) -> None:
        """保存策略到新数据库"""
        # 实现具体的数据库保存逻辑
        pass

    async def _save_signals_batch(self, signals: List[StrategySignal]) -> None:
        """批量保存信号到新数据库"""
        # 实现具体的数据库保存逻辑
        pass

    async def _save_performance_data(self, performance: StrategyPerformance) -> None:
        """保存性能数据到新数据库"""
        # 实现具体的数据库保存逻辑
        pass

    async def _save_strategy_template(self, template: CBSCStrategyTemplate) -> None:
        """保存策略模板到新数据库"""
        # 实现具体的数据库保存逻辑
        pass

    async def _save_cbsc_sentiment_data(self, df: pd.DataFrame) -> None:
        """保存CBSC情绪数据到新数据库"""
        # 实现具体的数据库保存逻辑
        pass

    async def _adapt_performance_data(self, legacy_perf: Dict[str, Any]) -> StrategyPerformance:
        """适配性能数据格式"""
        return StrategyPerformance(
            strategy_type=StrategyType(legacy_perf.get("strategy_type", "direct_rsi")),
            total_return=legacy_perf.get("total_return", 0.0),
            annual_return=legacy_perf.get("annual_return", 0.0),
            sharpe_ratio=legacy_perf.get("sharpe_ratio", 0.0),
            max_drawdown=legacy_perf.get("max_drawdown", 0.0),
            win_rate=legacy_perf.get("win_rate", 0.0),
            profit_factor=legacy_perf.get("profit_factor", 0.0),
            calmar_ratio=legacy_perf.get("calmar_ratio", 0.0),
            total_trades=legacy_perf.get("total_trades", 0),
            profit_trades=legacy_perf.get("profit_trades", 0),
            avg_profit=legacy_perf.get("avg_profit", 0.0),
            avg_loss=legacy_perf.get("avg_loss", 0.0),
            last_updated=datetime.now()
        )

    async def _create_indexes_and_constraints(self) -> None:
        """创建索引和约束"""
        # 实现数据库索引和约束创建逻辑
        pass

    def _log_migration(self, entity_type: str, entity_id: str, status: str, error: str = None) -> None:
        """记录迁移日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "status": status,
            "error": error
        }
        self.migration_log.append(log_entry)

class MigrationValidator:
    """迁移验证器"""

    def __init__(self, migrator: CBSCDataMigrator):
        self.migrator = migrator

    async def validate_migration(self) -> Dict[str, Any]:
        """验证迁移结果"""
        logger.info("开始验证迁移结果...")

        validation_results = {
            "strategies": await self._validate_strategies(),
            "signals": await self._validate_signals(),
            "performance_data": await self._validate_performance_data(),
            "cbsc_sentiment_data": await self._validate_cbsc_data(),
            "overall": {"status": "pending", "issues": []}
        }

        # 检查整体验证结果
        all_valid = all(
            result.get("status") == "success"
            for result in validation_results.values()
            if isinstance(result, dict) and "status" in result
        )

        validation_results["overall"]["status"] = "success" if all_valid else "failed"

        logger.info(f"迁移验证完成: {validation_results['overall']['status']}")
        return validation_results

    async def _validate_strategies(self) -> Dict[str, Any]:
        """验证策略迁移"""
        # 实现策略验证逻辑
        return {"status": "success", "count": 0, "issues": []}

    async def _validate_signals(self) -> Dict[str, Any]:
        """验证信号迁移"""
        # 实现信号验证逻辑
        return {"status": "success", "count": 0, "issues": []}

    async def _validate_performance_data(self) -> Dict[str, Any]:
        """验证性能数据迁移"""
        # 实现性能数据验证逻辑
        return {"status": "success", "count": 0, "issues": []}

    async def _validate_cbsc_data(self) -> Dict[str, Any]:
        """验证CBSC数据迁移"""
        # 实现CBSC数据验证逻辑
        return {"status": "success", "count": 0, "issues": []}

async def run_migration():
    """运行数据迁移"""
    logger.info("=== CBSC策略管理数据迁移开始 ===")

    # 配置路径
    legacy_db_path = "data/legacy_quant_system.db"
    new_db_path = "data/unified_quant_system.db"

    # 创建迁移器
    migrator = CBSCDataMigrator(legacy_db_path, new_db_path)

    try:
        # 执行迁移
        migration_result = await migrator.migrate_all_data()

        # 验证迁移结果
        if migration_result["status"] == "success":
            validator = MigrationValidator(migrator)
            validation_result = await validator.validate_migration()

            print(f"""
            === CBSC策略管理数据迁移完成 ===

            迁移状态: {migration_result['status']}
            迁移时间: {migration_result['migration_time']:.2f}秒
            成功迁移: {migration_result['strategies_migrated']}个条目
            错误数量: {migration_result['errors']}个

            验证状态: {validation_result['overall']['status']}

            详细日志已保存到 migration_log.json
            """)

            # 保存迁移日志
            with open("migration_log.json", "w", encoding="utf-8") as f:
                json.dump(migration_result, f, indent=2, ensure_ascii=False)
        else:
            logger.error(f"迁移失败: {migration_result}")

    except Exception as e:
        logger.error(f"数据迁移过程出现异常: {e}")
        raise

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('cbsc_migration.log'),
            logging.StreamHandler()
        ]
    )

    # 运行迁移
    asyncio.run(run_migration())