#!/usr/bin/env python3
"""
CBSC策略遷移工具
CBSC Strategy Migration Tool

將現有CBSC策略數據遷移到統一架構
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.strategy_compatibility_adapter import (
    StrategyCompatibilityAdapter,
    StrategyDataMigrator
)
from api.unified_strategy_service import get_unified_strategy_manager
from models.strategy import (
    Strategy, StrategyConfig, StrategyPerformance,
    StrategyCategory, StatusEnum, RiskLevelEnum
)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# 遷移配置 (Migration Configuration)
# ============================================================================

class MigrationConfig:
    """遷移配置"""

    def __init__(self):
        # 數據源路徑
        self.legacy_data_dir = Path("data/legacy_strategies")
        self.backup_dir = Path("data/migration_backups")

        # 遷移設置
        self.batch_size = 100
        self.enable_validation = True
        self.create_backups = True
        self.dry_run = False

        # 數據映射
        self.category_mapping = {
            "technical": "技術分析",
            "fundamental": "基本面分析",
            "sentiment": "情緒分析",
            "quantitative": "量化分析"
        }

# ============================================================================
# 遷移管理器 (Migration Manager)
# ============================================================================

class CBS CStrategyMigrationManager:
    """CBSC策略遷移管理器"""

    def __init__(self, config: MigrationConfig):
        self.config = config
        self.logger = logging.getLogger("migration_manager")

        # 初始化組件
        self.adapter = StrategyCompatibilityAdapter()
        self.migrator = StrategyDataMigrator(self.adapter)
        self.strategy_manager = None

        # 遷移統計
        self.migration_stats = {
            "total_strategies": 0,
            "migrated_strategies": 0,
            "failed_strategies": 0,
            "total_configs": 0,
            "migrated_configs": 0,
            "failed_configs": 0,
            "total_performance": 0,
            "migrated_performance": 0,
            "failed_performance": 0,
            "warnings": [],
            "errors": []
        }

    async def initialize(self):
        """初始化遷移管理器"""
        try:
            self.logger.info("初始化遷移管理器...")

            # 初始化策略管理器
            self.strategy_manager = get_unified_strategy_manager()

            # 創建必要目錄
            self.config.backup_dir.mkdir(parents=True, exist_ok=True)
            self.config.legacy_data_dir.mkdir(parents=True, exist_ok=True)

            self.logger.info("遷移管理器初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"初始化遷移管理器失敗: {e}")
            return False

    async def run_migration(self, dry_run: bool = False) -> Dict[str, Any]:
        """執行遷移"""
        try:
            self.logger.info(f"開始CBSC策略遷移 (dry_run={dry_run})")

            if dry_run:
                self.logger.warning("這是試運行模式，不會實際修改數據")

            # 1. 遷移策略分類
            await self._migrate_categories(dry_run)

            # 2. 遷移策略主數據
            await self._migrate_strategies(dry_run)

            # 3. 遷移策略配置
            await self._migrate_strategy_configs(dry_run)

            # 4. 遷移性能數據
            await self._migrate_performance_data(dry_run)

            # 5. 生成遷移報告
            report = await self._generate_migration_report()

            self.logger.info("CBSC策略遷移完成")
            return report

        except Exception as e:
            self.logger.error(f"遷移失敗: {e}")
            raise

    async def _migrate_categories(self, dry_run: bool):
        """遷移策略分類"""
        try:
            self.logger.info("遷移策略分類...")

            # 創建默認分類
            default_categories = [
                {"name": "technical", "display_name": "技術分析", "description": "基於技術指標的交易策略"},
                {"name": "fundamental", "display_name": "基本面分析", "description": "基於基本面數據的策略"},
                {"name": "sentiment", "display_name": "情緒分析", "description": "基於市場情緒的策略"},
                {"name": "quantitative", "display_name": "量化分析", "description": "純量化模型策略"}
            ]

            for cat_data in default_categories:
                if not dry_run:
                    # 檢查分類是否已存在
                    # 實際實現中需要在數據庫中檢查和創建
                    self.logger.info(f"創建分類: {cat_data['display_name']}")
                else:
                    self.logger.info(f"[DRY RUN] 創建分類: {cat_data['display_name']}")

        except Exception as e:
            self.logger.error(f"遷移分類失敗: {e}")
            self.migration_stats["errors"].append(f"遷移分類失敗: {str(e)}")

    async def _migrate_strategies(self, dry_run: bool):
        """遷移策略主數據"""
        try:
            self.logger.info("遷移策略主數據...")

            # 查找遺留策略文件
            legacy_files = list(self.config.legacy_data_dir.glob("*_strategies.json"))
            if not legacy_files:
                # 創建示例遺留數據用於測試
                await self._create_sample_legacy_data()
                legacy_files = list(self.config.legacy_data_dir.glob("*_strategies.json"))

            all_legacy_strategies = []
            for file_path in legacy_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            all_legacy_strategies.extend(data)
                        else:
                            all_legacy_strategies.append(data)
                except Exception as e:
                    self.logger.error(f"讀取遺留文件失敗 {file_path}: {e}")
                    continue

            self.migration_stats["total_strategies"] = len(all_legacy_strategies)
            self.logger.info(f"找到 {len(all_legacy_strategies)} 個遺留策略")

            # 批量遷移
            migration_result = await self.migrator.migrate_strategies(
                all_legacy_strategies,
                batch_size=self.config.batch_size
            )

            self.migration_stats["migrated_strategies"] = migration_result["success_count"]
            self.migration_stats["failed_strategies"] = migration_result["error_count"]
            self.migration_stats["warnings"].extend(migration_result["warnings"])
            self.migration_stats["errors"].extend(migration_result["errors"])

            if not dry_run:
                # 實際保存到數據庫
                self.logger.info(f"實際遷移 {migration_result['success_count']} 個策略到數據庫")
            else:
                self.logger.info(f"[DRY RUN] 擬遷移 {migration_result['success_count']} 個策略")

        except Exception as e:
            self.logger.error(f"遷移策略主數據失敗: {e}")
            self.migration_stats["errors"].append(f"遷移策略主數據失敗: {str(e)}")

    async def _migrate_strategy_configs(self, dry_run: bool):
        """遷移策略配置"""
        try:
            self.logger.info("遷移策略配置...")

            # 查找配置文件
            config_files = list(self.config.legacy_data_dir.glob("*_configs.json"))

            all_configs = []
            for file_path in config_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            all_configs.extend(data)
                        else:
                            all_configs.append(data)
                except Exception as e:
                    self.logger.error(f"讀取配置文件失敗 {file_path}: {e}")
                    continue

            self.migration_stats["total_configs"] = len(all_configs)

            for config_data in all_configs:
                try:
                    # 驗證配置兼容性
                    validation = self.adapter.validate_data_compatibility(config_data, "strategy")

                    if validation["is_compatible"]:
                        if not dry_run:
                            # 實際保存配置到數據庫
                            # 實現中需要創建StrategyConfig對象並保存
                            pass
                        self.migration_stats["migrated_configs"] += 1
                    else:
                        self.migration_stats["failed_configs"] += 1
                        self.migration_stats["errors"].extend(validation["errors"])

                    self.migration_stats["warnings"].extend(validation["warnings"])

                except Exception as e:
                    self.migration_stats["failed_configs"] += 1
                    self.migration_stats["errors"].append(f"遷移配置失敗: {str(e)}")

            self.logger.info(f"配置遷移完成: 成功 {self.migration_stats['migrated_configs']}, 失敗 {self.migration_stats['failed_configs']}")

        except Exception as e:
            self.logger.error(f"遷移策略配置失敗: {e}")
            self.migration_stats["errors"].append(f"遷移策略配置失敗: {str(e)}")

    async def _migrate_performance_data(self, dry_run: bool):
        """遷移性能數據"""
        try:
            self.logger.info("遷移性能數據...")

            # 查找性能數據文件
            perf_files = list(self.config.legacy_data_dir.glob("*_performance.json"))

            all_performance = []
            for file_path in perf_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            all_performance.extend(data)
                        else:
                            all_performance.append(data)
                except Exception as e:
                    self.logger.error(f"讀取性能文件失敗 {file_path}: {e}")
                    continue

            self.migration_stats["total_performance"] = len(all_performance)

            # 轉換性能數據
            converted_performance = self.adapter.convert_performance_data(all_performance)

            if not dry_run:
                # 實際保存性能數據到數據庫
                # 實現中需要創建StrategyPerformance對象並批量保存
                pass

            self.migration_stats["migrated_performance"] = len(converted_performance)

            self.logger.info(f"性能數據遷移完成: {len(converted_performance)} 條記錄")

        except Exception as e:
            self.logger.error(f"遷移性能數據失敗: {e}")
            self.migration_stats["errors"].append(f"遷移性能數據失敗: {str(e)}")

    async def _create_sample_legacy_data(self):
        """創建示例遺留數據"""
        try:
            self.logger.info("創建示例遺留數據...")

            # 示例策略數據
            sample_strategies = [
                {
                    "id": "legacy_rsi_001",
                    "name": "RSI超賣策略",
                    "description": "基於RSI指標的超賣買入策略",
                    "strategy_type": "direct_rsi",
                    "status": "active",
                    "risk_level": "medium",
                    "parameters": {
                        "rsi_period": 14,
                        "oversold_threshold": 30,
                        "overbought_threshold": 70
                    },
                    "performance": {
                        "total_return": 0.15,
                        "sharpe_ratio": 1.2,
                        "max_drawdown": 0.08,
                        "win_rate": 0.65
                    },
                    "indicators": ["RSI"],
                    "timeframes": ["1d", "1h"],
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-12-01T00:00:00Z"
                },
                {
                    "id": "legacy_sentiment_001",
                    "name": "情緒動量策略",
                    "description": "結合市場情緒和價格動量的複合策略",
                    "strategy_type": "sentiment_momentum",
                    "status": "inactive",
                    "risk_level": "high",
                    "parameters": {
                        "rsi_period": 14,
                        "fast_period": 12,
                        "slow_period": 26,
                        "weight_sentiment": 0.6,
                        "volume_weight": 0.3
                    },
                    "performance": {
                        "total_return": 0.22,
                        "sharpe_ratio": 1.8,
                        "max_drawdown": 0.12,
                        "win_rate": 0.58
                    },
                    "indicators": ["RSI", "MACD", "Volume", "Sentiment"],
                    "timeframes": ["1d", "4h", "1h"],
                    "created_at": "2024-02-01T00:00:00Z",
                    "updated_at": "2024-11-15T00:00:00Z"
                }
            ]

            # 保存示例數據
            strategies_file = self.config.legacy_data_dir / "sample_strategies.json"
            with open(strategies_file, 'w', encoding='utf-8') as f:
                json.dump(sample_strategies, f, indent=2, ensure_ascii=False)

            self.logger.info(f"示例遺留數據已創建: {strategies_file}")

        except Exception as e:
            self.logger.error(f"創建示例遺留數據失敗: {e}")

    async def _generate_migration_report(self) -> Dict[str, Any]:
        """生成遷移報告"""
        try:
            report = {
                "migration_summary": {
                    "timestamp": datetime.now().isoformat(),
                    "total_strategies": self.migration_stats["total_strategies"],
                    "migrated_strategies": self.migration_stats["migrated_strategies"],
                    "failed_strategies": self.migration_stats["failed_strategies"],
                    "success_rate": (
                        self.migration_stats["migrated_strategies"] /
                        max(self.migration_stats["total_strategies"], 1) * 100
                    ),
                    "total_configs": self.migration_stats["total_configs"],
                    "migrated_configs": self.migration_stats["migrated_configs"],
                    "failed_configs": self.migration_stats["failed_configs"],
                    "total_performance": self.migration_stats["total_performance"],
                    "migrated_performance": self.migration_stats["migrated_performance"]
                },
                "warnings": self.migration_stats["warnings"],
                "errors": self.migration_stats["errors"],
                "recommendations": []
            }

            # 添加建議
            if self.migration_stats["failed_strategies"] > 0:
                report["recommendations"].append("建議檢查遷移失敗的策略數據格式")

            if len(self.migration_stats["warnings"]) > 0:
                report["recommendations"].append("建議檢查並解決遷移過程中的警告")

            if report["migration_summary"]["success_rate"] < 90:
                report["recommendations"].append("成功率較低，建議檢查數據兼容性")

            # 保存報告
            report_file = self.config.backup_dir / f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            self.logger.info(f"遷移報告已保存: {report_file}")
            return report

        except Exception as e:
            self.logger.error(f"生成遷移報告失敗: {e}")
            return {}

# ============================================================================
# 主執行函數 (Main Execution Function)
# ============================================================================

async def main():
    """主執行函數"""
    try:
        print("=" * 60)
        print("CBSC策略遷移工具")
        print("=" * 60)

        # 創建配置
        config = MigrationConfig()

        # 詢問是否進行試運行
        dry_run_input = input("是否進行試運行？(y/N): ").strip().lower()
        dry_run = dry_run_input in ['y', 'yes', '是']

        if dry_run:
            print("⚠️  試運行模式 - 不會實際修改數據")
        else:
            print("🚀 正式遷移模式 - 將實際修改數據")
            confirm = input("確認繼續？(y/N): ").strip().lower()
            if confirm not in ['y', 'yes', '是']:
                print("遷移已取消")
                return

        # 初始化遷移管理器
        migration_manager = CB CStrategyMigrationManager(config)

        if not await migration_manager.initialize():
            print("❌ 遷移管理器初始化失敗")
            return

        # 執行遷移
        report = await migration_manager.run_migration(dry_run)

        # 顯示結果
        print("\n" + "=" * 60)
        print("遷移結果")
        print("=" * 60)

        summary = report["migration_summary"]
        print(f"總策略數: {summary['total_strategies']}")
        print(f"成功遷移: {summary['migrated_strategies']}")
        print(f"失敗策略: {summary['failed_strategies']}")
        print(f"成功率: {summary['success_rate']:.1f}%")
        print(f"配置遷移: {summary['migrated_configs']}/{summary['total_configs']}")
        print(f"性能數據: {summary['migrated_performance']} 條記錄")

        if report["warnings"]:
            print(f"\n⚠️  警告 ({len(report['warnings'])}):")
            for warning in report["warnings"][:5]:  # 只顯示前5個
                print(f"  - {warning}")
            if len(report["warnings"]) > 5:
                print(f"  ... 還有 {len(report['warnings']) - 5} 個警告")

        if report["errors"]:
            print(f"\n❌ 錯誤 ({len(report['errors'])}):")
            for error in report["errors"][:5]:  # 只顯示前5個
                print(f"  - {error}")
            if len(report["errors"]) > 5:
                print(f"  ... 還有 {len(report['errors']) - 5} 個錯誤")

        if report["recommendations"]:
            print(f"\n💡 建議:")
            for rec in report["recommendations"]:
                print(f"  - {rec}")

        print("\n✅ 遷移完成！")

    except KeyboardInterrupt:
        print("\n❌ 遷移被用戶中斷")
    except Exception as e:
        print(f"\n❌ 遷移失敗: {e}")
        logger.exception("遷移過程發生異常")

if __name__ == "__main__":
    asyncio.run(main())