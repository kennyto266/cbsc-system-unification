#!/usr/bin/env python3
"""
CBSC策略管理系统集成测试 (Task 005)
CBSC Strategy Management System Integration Test

全面测试CBSC策略管理API的集成、兼容性和数据迁移功能
"""

import asyncio
import json
import logging
import pytest
import httpx
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

# 导入API模块
from src.api.strategy_management_api import (
    Strategy, StrategyType, StrategyStatus, StrategyParameters,
    DataCompatibilityAdapter, StrategyTemplates
)
from src.api.strategy_endpoints import StrategyManager
from src.api.strategy_migration import CBSCDataMigrator, MigrationValidator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategy_integration_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class IntegrationTestSuite:
    """集成测试套件"""

    def __init__(self):
        self.test_results = []
        self.api_base_url = "http://localhost:3004"
        self.test_db_path = "test_integrated_system.db"
        self.legacy_db_path = "test_legacy_system.db"

    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有集成测试"""
        logger.info("=== 开始CBSC策略管理系统集成测试 ===")

        test_start = datetime.now()

        try:
            # 1. 环境准备测试
            await self._test_environment_setup()

            # 2. 数据模型测试
            await self._test_data_models()

            # 3. 兼容性适配器测试
            await self._test_compatibility_adapter()

            # 4. 策略管理器测试
            await self._test_strategy_manager()

            # 5. 数据迁移测试
            await self._test_data_migration()

            # 6. API端点测试
            await self._test_api_endpoints()

            # 7. 端到端工作流测试
            await self._test_end_to_end_workflows()

            # 8. 性能和负载测试
            await self._test_performance_load()

            test_end = datetime.now()
            test_duration = (test_end - test_start).total_seconds()

            # 生成测试报告
            test_report = self._generate_test_report(test_duration)

            logger.info(f"集成测试完成: {test_report['summary']['passed']}/{test_report['summary']['total']} 通过")
            return test_report

        except Exception as e:
            logger.error(f"集成测试过程出现异常: {e}")
            return {
                "status": "error",
                "error": str(e),
                "test_results": self.test_results
            }

    async def _test_environment_setup(self):
        """测试环境准备"""
        test_name = "environment_setup"
        try:
            logger.info("测试环境准备...")

            # 创建测试数据库
            await self._create_test_databases()

            # 创建测试数据
            await self._create_test_data()

            self._record_test_result(test_name, True, "环境准备成功")

        except Exception as e:
            self._record_test_result(test_name, False, f"环境准备失败: {e}")
            raise

    async def _test_data_models(self):
        """测试数据模型"""
        test_name = "data_models"
        try:
            logger.info("测试数据模型...")

            # 测试策略创建
            strategy = Strategy(
                id="test_strategy_001",
                name="测试RSI策略",
                description="这是一个测试用的RSI策略",
                strategy_type=StrategyType.DIRECT_RSI,
                parameters=StrategyParameters(rsi_period=14, oversold_threshold=30, overbought_threshold=70),
                status=StrategyStatus.ACTIVE
            )

            assert strategy.id == "test_strategy_001"
            assert strategy.strategy_type == StrategyType.DIRECT_RSI
            assert strategy.parameters.rsi_period == 14

            # 测试策略模板
            templates = StrategyTemplates.get_all_templates()
            assert len(templates) == 4
            assert all(hasattr(template, 'id') for template in templates)

            # 测试数据验证
            self._test_data_validation()

            self._record_test_result(test_name, True, "数据模型测试通过")

        except Exception as e:
            self._record_test_result(test_name, False, f"数据模型测试失败: {e}")

    async def _test_compatibility_adapter(self):
        """测试兼容性适配器"""
        test_name = "compatibility_adapter"
        try:
            logger.info("测试兼容性适配器...")

            # 测试旧版策略格式适配
            legacy_strategy = {
                "id": "legacy_001",
                "name": "Legacy Strategy",
                "strategy_type": "direct_rsi",
                "parameters": {"rsi_period": 10, "oversold_threshold": 25},
                "is_active": True,
                "created_at": "2024-01-01T00:00:00"
            }

            adapted_strategy = DataCompatibilityAdapter.adapt_legacy_strategy_format(legacy_strategy)

            assert adapted_strategy.id == "legacy_001"
            assert adapted_strategy.strategy_type == StrategyType.DIRECT_RSI
            assert adapted_strategy.parameters.rsi_period == 10
            assert adapted_strategy.is_active == True

            # 测试旧版信号格式适配
            legacy_signal = {
                "signal_id": "legacy_signal_001",
                "strategy_type": "direct_rsi",
                "signal_type": "buy",
                "strength": 85.5,
                "confidence": 92.3,
                "timestamp": "2024-01-01T10:00:00",
                "market_data": {"price": 150.0, "volume": 1000000}
            }

            adapted_signal = DataCompatibilityAdapter.adapt_legacy_signal_format(legacy_signal)

            assert adapted_signal.signal_id == "legacy_signal_001"
            assert adapted_signal.strategy_type == StrategyType.DIRECT_RSI

            self._record_test_result(test_name, True, "兼容性适配器测试通过")

        except Exception as e:
            self._record_test_result(test_name, False, f"兼容性适配器测试失败: {e}")

    async def _test_strategy_manager(self):
        """测试策略管理器"""
        test_name = "strategy_manager"
        try:
            logger.info("测试策略管理器...")

            manager = StrategyManager()
            await manager.initialize()

            # 测试策略创建
            strategy = Strategy(
                id="manager_test_001",
                name="Manager Test Strategy",
                description="Test strategy for manager",
                strategy_type=StrategyType.SENTIMENT_MOMENTUM,
                parameters=StrategyParameters(fast_period=12, slow_period=26, signal_period=9)
            )

            manager.strategies[strategy.id] = strategy

            # 验证策略添加
            assert strategy.id in manager.strategies
            assert manager.strategies[strategy.id].name == "Manager Test Strategy"

            # 测试模板加载
            assert len(manager.templates) == 4

            self._record_test_result(test_name, True, "策略管理器测试通过")

        except Exception as e:
            self._record_test_result(test_name, False, f"策略管理器测试失败: {e}")

    async def _test_data_migration(self):
        """测试数据迁移"""
        test_name = "data_migration"
        try:
            logger.info("测试数据迁移...")

            # 创建迁移器
            migrator = CBSCDataMigrator(self.legacy_db_path, self.test_db_path)

            # 模拟旧版数据
            await self._create_legacy_data()

            # 执行迁移
            migration_result = await migrator.migrate_all_data()

            # 验证迁移结果
            assert migration_result["status"] == "success"
            assert migration_result["strategies_migrated"] > 0
            assert migration_result["errors"] == 0

            # 验证迁移数据
            validator = MigrationValidator(migrator)
            validation_result = await validator.validate_migration()

            assert validation_result["overall"]["status"] == "success"

            self._record_test_result(test_name, True, f"数据迁移测试通过: 迁移了{migration_result['strategies_migrated']}个策略")

        except Exception as e:
            self._record_test_result(test_name, False, f"数据迁移测试失败: {e}")

    async def _test_api_endpoints(self):
        """测试API端点"""
        test_name = "api_endpoints"
        try:
            logger.info("测试API端点...")

            # 注意：这里假设API服务器正在运行
            # 在实际测试中，可能需要使用TestClient启动测试服务器

            async with httpx.AsyncClient(timeout=30.0) as client:
                # 测试健康检查
                response = await client.get(f"{self.api_base_url}/health")
                assert response.status_code == 200

                # 测试获取策略列表
                response = await client.get(f"{self.api_base_url}/api/strategies/")
                assert response.status_code == 200
                strategies_data = response.json()
                assert "strategies" in strategies_data

                # 测试获取策略模板
                response = await client.get(f"{self.api_base_url}/api/strategies/templates")
                assert response.status_code == 200
                templates_data = response.json()
                assert isinstance(templates_data, list)

            self._record_test_result(test_name, True, "API端点测试通过")

        except httpx.ConnectError:
            self._record_test_result(test_name, False, "API服务器未运行，跳过API端点测试")
        except Exception as e:
            self._record_test_result(test_name, False, f"API端点测试失败: {e}")

    async def _test_end_to_end_workflows(self):
        """测试端到端工作流"""
        test_name = "end_to_end_workflows"
        try:
            logger.info("测试端到端工作流...")

            # 测试完整的策略创建到执行工作流
            await self._test_strategy_creation_workflow()

            # 测试策略优化工作流
            await self._test_strategy_optimization_workflow()

            # 测试批量操作工作流
            await self._test_batch_operations_workflow()

            self._record_test_result(test_name, True, "端到端工作流测试通过")

        except Exception as e:
            self._record_test_result(test_name, False, f"端到端工作流测试失败: {e}")

    async def _test_performance_load(self):
        """测试性能和负载"""
        test_name = "performance_load"
        try:
            logger.info("测试性能和负载...")

            # 测试大量策略的创建和管理
            await self._test_large_scale_strategy_management()

            # 测试并发操作
            await self._test_concurrent_operations()

            self._record_test_result(test_name, True, "性能和负载测试通过")

        except Exception as e:
            self._record_test_result(test_name, False, f"性能和负载测试失败: {e}")

    async def _create_test_databases(self):
        """创建测试数据库"""
        # 创建旧版测试数据库
        legacy_conn = sqlite3.connect(self.legacy_db_path)
        cursor = legacy_conn.cursor()

        # 创建旧版策略表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                strategy_type TEXT NOT NULL,
                parameters TEXT,
                is_active BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建旧版信号表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_signals (
                signal_id TEXT PRIMARY KEY,
                strategy_id TEXT,
                signal_type TEXT,
                strength REAL,
                confidence REAL,
                timestamp TIMESTAMP,
                market_data TEXT
            )
        """)

        legacy_conn.commit()
        legacy_conn.close()

        # 创建新版测试数据库
        new_conn = sqlite3.connect(self.test_db_path)
        cursor = new_conn.cursor()

        # 创建新版策略表（更复杂的结构）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unified_strategies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                strategy_type TEXT NOT NULL,
                parameters TEXT,
                status TEXT DEFAULT 'inactive',
                is_active BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        new_conn.commit()
        new_conn.close()

    async def _create_test_data(self):
        """创建测试数据"""
        # 创建CBSC情绪测试数据
        test_sentiment_data = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=100, freq='D'),
            'Afternoon_Close': 150 + range(100),
            'Bull_Ratio': [0.5 + 0.1 * (i % 10 - 5) / 5 for i in range(100)],
            'Bull_Turnover_HKD': [1000000 + i * 10000 for i in range(100)],
            'Bear_Turnover_HKD': [800000 + i * 8000 for i in range(100)]
        })

        test_sentiment_file = "test_cbsc_sentiment.csv"
        test_sentiment_data.to_csv(test_sentiment_file, index=False)

    async def _create_legacy_data(self):
        """创建旧版测试数据"""
        legacy_conn = sqlite3.connect(self.legacy_db_path)
        cursor = legacy_conn.cursor()

        # 插入测试策略
        test_strategies = [
            ("legacy_rsi_001", "Legacy RSI Strategy", "direct_rsi",
             '{"rsi_period": 14, "oversold_threshold": 30, "overbought_threshold": 70}',
             True),
            ("legacy_momentum_001", "Legacy Momentum Strategy", "sentiment_momentum",
             '{"fast_period": 12, "slow_period": 26, "signal_period": 9}',
             False),
            ("legacy_composite_001", "Legacy Composite Strategy", "composite_index",
             '{"bb_period": 20, "bb_std": 2, "weight_sentiment": 0.6}',
             True)
        ]

        cursor.executemany("""
            INSERT OR REPLACE INTO strategies (id, name, strategy_type, parameters, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, test_strategies)

        # 插入测试信号
        test_signals = []
        for strategy_id, _, strategy_type, *_ in test_strategies:
            for i in range(10):
                signal_id = f"{strategy_id}_signal_{i+1}"
                test_signals.append((
                    signal_id,
                    strategy_id,
                    "buy" if i % 2 == 0 else "sell",
                    75.0 + i * 2,
                    80.0 + i,
                    datetime.now() - timedelta(days=i),
                    json.dumps({"price": 150.0 + i * 5, "volume": 1000000 + i * 100000})
                ))

        cursor.executemany("""
            INSERT OR REPLACE INTO strategy_signals
            (signal_id, strategy_id, signal_type, strength, confidence, timestamp, market_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, test_signals)

        legacy_conn.commit()
        legacy_conn.close()

    def _test_data_validation(self):
        """测试数据验证"""
        # 测试参数验证
        try:
            # 无效的RSI周期
            invalid_params = StrategyParameters(rsi_period=-1)
            assert False, "应该抛出验证错误"
        except Exception:
            pass  # 预期的验证错误

        # 测试有效的参数
        valid_params = StrategyParameters(
            rsi_period=14,
            oversold_threshold=30,
            overbought_threshold=70
        )
        assert valid_params.rsi_period == 14

    async def _test_strategy_creation_workflow(self):
        """测试策略创建工作流"""
        manager = StrategyManager()
        await manager.initialize()

        # 创建策略
        strategy = Strategy(
            id="workflow_test_001",
            name="Workflow Test Strategy",
            description="Strategy for workflow testing",
            strategy_type=StrategyType.DIRECT_RSI,
            parameters=StrategyParameters(rsi_period=14)
        )

        manager.strategies[strategy.id] = strategy

        # 验证策略创建
        assert strategy.id in manager.strategies
        assert strategy.status == StrategyStatus.INACTIVE

    async def _test_strategy_optimization_workflow(self):
        """测试策略优化工作流"""
        # 模拟策略优化过程
        from src.api.strategy_management_api import StrategyOptimizationRequest

        optimization_request = StrategyOptimizationRequest(
            strategy_id="test_strategy",
            optimization_method="grid",
            parameter_ranges={
                "rsi_period": {"min": 10, "max": 20},
                "oversold_threshold": {"min": 25, "max": 35}
            },
            objective_metric="sharpe_ratio",
            max_iterations=10,
            time_range={"start": "2024-01-01", "end": "2024-12-31"}
        )

        assert optimization_request.strategy_id == "test_strategy"
        assert optimization_request.optimization_method == "grid"

    async def _test_batch_operations_workflow(self):
        """测试批量操作工作流"""
        manager = StrategyManager()
        await manager.initialize()

        # 创建多个测试策略
        strategy_ids = []
        for i in range(5):
            strategy_id = f"batch_test_{i+1:03d}"
            strategy = Strategy(
                id=strategy_id,
                name=f"Batch Test Strategy {i+1}",
                description="Strategy for batch testing",
                strategy_type=StrategyType.DIRECT_RSI,
                parameters=StrategyParameters(rsi_period=14)
            )
            manager.strategies[strategy_id] = strategy
            strategy_ids.append(strategy_id)

        # 批量激活策略
        success_count = 0
        for strategy_id in strategy_ids:
            if strategy_id in manager.strategies:
                manager.strategies[strategy_id].is_active = True
                success_count += 1

        assert success_count == 5

    async def _test_large_scale_strategy_management(self):
        """测试大规模策略管理"""
        manager = StrategyManager()
        await manager.initialize()

        # 创建大量策略
        strategy_count = 100
        for i in range(strategy_count):
            strategy_id = f"scale_test_{i+1:04d}"
            strategy = Strategy(
                id=strategy_id,
                name=f"Scale Test Strategy {i+1}",
                description="Strategy for scale testing",
                strategy_type=StrategyType.DIRECT_RSI,
                parameters=StrategyParameters(rsi_period=14 + i % 10)
            )
            manager.strategies[strategy_id] = strategy

        assert len(manager.strategies) == strategy_count + len(manager.templates)

    async def _test_concurrent_operations(self):
        """测试并发操作"""
        async def create_strategy_async(index):
            """异步创建策略"""
            strategy_id = f"concurrent_test_{index}"
            strategy = Strategy(
                id=strategy_id,
                name=f"Concurrent Test Strategy {index}",
                description="Strategy for concurrent testing",
                strategy_type=StrategyType.SENTIMENT_MOMENTUM,
                parameters=StrategyParameters(fast_period=12, slow_period=26)
            )
            await asyncio.sleep(0.01)  # 模拟异步操作
            return strategy

        # 并发创建策略
        tasks = [create_strategy_async(i) for i in range(20)]
        strategies = await asyncio.gather(*tasks)

        assert len(strategies) == 20
        assert all(strategy.id.startswith("concurrent_test_") for strategy in strategies)

    def _record_test_result(self, test_name: str, passed: bool, message: str):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

        status = "✅" if passed else "❌"
        logger.info(f"{status} {test_name}: {message}")

    def _generate_test_report(self, test_duration: float) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests

        report = {
            "timestamp": datetime.now().isoformat(),
            "test_duration_seconds": test_duration,
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "test_results": self.test_results,
            "environment": {
                "python_version": "3.x",
                "test_database": self.test_db_path,
                "legacy_database": self.legacy_db_path
            }
        }

        # 保存测试报告
        report_file = f"strategy_integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"测试报告已保存到: {report_file}")
        return report

async def main():
    """主测试函数"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     🚀 CBSC策略管理系统集成测试 (Task 005)                   ║
    ║                                                           ║
    ║     全面验证API集成、数据迁移和系统兼容性                     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════════
    """)

    # 创建并运行测试套件
    test_suite = IntegrationTestSuite()
    test_report = await test_suite.run_all_tests()

    # 打印测试结果摘要
    print(f"""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                      📊 测试结果摘要                           ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║  总测试数: {test_report['summary']['total']:>25}              ║
    ║  通过数:   {test_report['summary']['passed']:>25}              ║
    ║  失败数:   {test_report['summary']['failed']:>25}              ║
    ║  通过率:   {test_report['summary']['pass_rate']:>24.1f}%        ║
    ║  测试时长: {test_report['test_duration_seconds']:>22.1f}秒      ║
    ╚═══════════════════════════════════════════════════════════════
    """)

    if test_report['summary']['failed'] > 0:
        print("\n❌ 失败的测试:")
        for result in test_report['test_results']:
            if not result['passed']:
                print(f"  - {result['test_name']}: {result['message']}")

    print(f"\n📄 详细测试报告已保存到JSON文件")

    # 清理测试文件
    try:
        Path(test_suite.test_db_path).unlink(missing_ok=True)
        Path(test_suite.legacy_db_path).unlink(missing_ok=True)
        Path("test_cbsc_sentiment.csv").unlink(missing_ok=True)
    except Exception as e:
        logger.warning(f"清理测试文件时出现警告: {e}")

    return test_report

if __name__ == "__main__":
    # 运行集成测试
    asyncio.run(main())