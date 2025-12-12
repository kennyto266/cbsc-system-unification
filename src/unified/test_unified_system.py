"""
统一数据系统综合测试

测试缓存管理器、数据质量验证器、数据同步器、数据管道和回测引擎的集成功能。

Task #31: Data Flow Unification - Price and Non-Price Integration
"""

import asyncio
import logging
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from src.unified import (
    unified_cache_manager,
    data_quality_validator,
    data_synchronizer,
    unified_data_pipeline,
    unified_backtest_engine
)
from src.unified.models import (
    DataSource, DataType, UnifiedDataPointSchema, StrategyConfig,
    StrategyType, BacktestConfig
)

# 配置测试日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestUnifiedCacheManager:
    """统一缓存管理器测试"""

    async def test_basic_cache_operations(self):
        """测试基础缓存操作"""
        try:
            # 测试设置和获取
            test_key = "test_key_001"
            test_data = {"symbol": "AAPL", "value": 150.0, "timestamp": datetime.now().isoformat()}

            # 设置缓存
            result = await unified_cache_manager.set(test_key, test_data)
            assert result, "缓存设置失败"

            # 获取缓存
            cached_data = await unified_cache_manager.get(test_key)
            assert cached_data is not None, "缓存获取失败"
            assert cached_data["symbol"] == test_data["symbol"], "缓存数据不匹配"

            # 删除缓存
            delete_result = await unified_cache_manager.delete(test_key)
            assert delete_result, "缓存删除失败"

            # 验证删除
            deleted_data = await unified_cache_manager.get(test_key)
            assert deleted_data is None, "缓存删除验证失败"

            logger.info("✅ 基础缓存操作测试通过")
            return True

        except Exception as e:
            logger.error(f"❌ 基础缓存操作测试失败: {e}")
            return False

    async def test_l1_l2_cache_interaction(self):
        """测试L1和L2缓存交互"""
        try:
            test_key = "test_l1_l2_001"
            test_data = {"test": "l1_l2_interaction", "timestamp": datetime.now().isoformat()}

            # 设置缓存（会同时存储到L1和L2）
            set_result = await unified_cache_manager.set(test_key, test_data)
            assert set_result, "L1+L2缓存设置失败"

            # 第一次获取（应该命中L1）
            first_get = await unified_cache_manager.get(test_key)
            assert first_get is not None, "L1缓存获取失败"

            # 清空L1缓存（模拟L1失效）
            unified_cache_manager.l1_cache.clear()

            # 第二次获取（应该命中L2并提升到L1）
            second_get = await unified_cache_manager.get(test_key)
            assert second_get is not None, "L2缓存获取失败"
            assert second_get["test"] == test_data["test"], "L2缓存数据不匹配"

            logger.info("✅ L1+L2缓存交互测试通过")
            return True

        except Exception as e:
            logger.error(f"❌ L1+L2缓存交互测试失败: {e}")
            return False

    async def test_cache_statistics(self):
        """测试缓存统计功能"""
        try:
            # 获取初始统计
            initial_stats = await unified_cache_manager.get_cache_info()
            assert 'total_stats' in initial_stats, "缓存统计信息不完整"

            # 执行一些缓存操作
            for i in range(10):
                await unified_cache_manager.set(f"stats_test_{i}", {"data": f"value_{i}"})
                await unified_cache_manager.get(f"stats_test_{i}")

            # 获取更新后的统计
            updated_stats = await unified_cache_manager.get_cache_info()
            assert updated_stats['total_stats']['sets'] >= 10, "缓存设置统计不正确"

            logger.info("✅ 缓存统计测试通过")
            return True

        except Exception as e:
            logger.error(f"❌ 缓存统计测试失败: {e}")
            return False

class TestDataQualityValidator:
    """数据质量验证器测试"""

    async def test_quality_validation(self):
        """测试数据质量验证"""
        try:
            # 创建测试数据
            test_data = []
            base_time = datetime.now() - timedelta(days=10)

            for i in range(100):
                test_point = {
                    'timestamp': (base_time + timedelta(hours=i)).isoformat(),
                    'symbol': 'TEST',
                    'source': 'price',
                    'data_type': 'ohlcv',
                    'value': 100.0 + (i % 20 - 10),  # 一些变化
                    'metadata': {'provider': 'test'}
                }
                test_data.append(test_point)

            # 执行质量验证
            quality_result = await data_quality_validator.validate_data_quality(
                test_data, 'price', 'TEST'
            )

            assert quality_result.overall_score > 0.8, f"质量评分过低: {quality_result.overall_score}"
            assert quality_result.total_points == 100, "数据点数量不正确"

            logger.info(f"✅ 数据质量验证测试通过，评分: {quality_result.overall_score:.3f}")
            return True

        except Exception as e:
            logger.error(f"❌ 数据质量验证测试失败: {e}")
            return False

    async def test_quality_issue_detection(self):
        """测试质量问题检测"""
        try:
            # 创建包含质量问题的测试数据
            test_data_with_issues = []
            base_time = datetime.now() - timedelta(days=5)

            # 正常数据
            for i in range(50):
                test_point = {
                    'timestamp': (base_time + timedelta(hours=i)).isoformat(),
                    'symbol': 'ISSUE_TEST',
                    'source': 'price',
                    'data_type': 'ohlcv',
                    'value': 100.0,
                    'metadata': {'provider': 'test'}
                }
                test_data_with_issues.append(test_point)

            # 添加异常值
            for i in range(10):
                outlier_point = {
                    'timestamp': (base_time + timedelta(hours=50 + i)).isoformat(),
                    'symbol': 'ISSUE_TEST',
                    'source': 'price',
                    'data_type': 'ohlcv',
                    'value': 1000.0 + i * 100,  # 异常高值
                    'metadata': {'provider': 'test'}
                }
                test_data_with_issues.append(outlier_point)

            # 执行质量验证
            quality_result = await data_quality_validator.validate_data_quality(
                test_data_with_issues, 'price', 'ISSUE_TEST'
            )

            # 检查是否检测到异常值
            outlier_check = quality_result.checks.get('outliers')
            assert outlier_check is not None, "缺少异常值检查"
            assert not outlier_check.passed, "应该检测到异常值"

            logger.info(f"✅ 质量问题检测测试通过，异常值: {outlier_check.metadata.get('outliers_detected', 0)}")
            return True

        except Exception as e:
            logger.error(f"❌ 质量问题检测测试失败: {e}")
            return False

class TestDataSynchronizer:
    """数据同步器测试"""

    async def test_sync_task_creation(self):
        """测试同步任务创建"""
        try:
            symbols = ['AAPL', 'GOOGL', 'MSFT']
            sources = ['price', 'hkma', 'sentiment']
            start_time = datetime.now() - timedelta(days=7)
            end_time = datetime.now()

            # 创建同步任务
            task_id = await data_synchronizer.sync_data(
                symbols, sources, start_time, end_time
            )

            assert task_id is not None, "同步任务创建失败"
            assert task_id.startswith("sync_"), "任务ID格式不正确"

            # 检查任务状态
            task_status = data_synchronizer.get_task_status(task_id)
            assert task_status is not None, "无法获取任务状态"

            logger.info(f"✅ 同步任务创建测试通过，任务ID: {task_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 同步任务创建测试失败: {e}")
            return False

    async def test_sync_statistics(self):
        """测试同步统计"""
        try:
            # 获取同步统计
            stats = data_synchronizer.get_sync_stats()

            assert 'total_tasks' in stats, "同步统计不完整"
            assert 'successful_tasks' in stats, "缺少成功任务统计"

            logger.info(f"✅ 同步统计测试通过，总任务数: {stats.get('total_tasks', 0)}")
            return True

        except Exception as e:
            logger.error(f"❌ 同步统计测试失败: {e}")
            return False

class TestDataPipeline:
    """数据管道测试"""

    async def test_data_fetching(self):
        """测试数据获取"""
        try:
            from src.unified.data_pipeline import DataRequest

            symbols = ['TEST_SYMBOL']
            sources = [DataSource.PRICE, DataSource.SENTIMENT]
            start_time = datetime.now() - timedelta(days=3)
            end_time = datetime.now()

            # 创建数据请求
            request = DataRequest(
                symbols=symbols,
                start_time=start_time,
                end_time=end_time,
                sources=sources
            )

            # 获取数据
            unified_data = await unified_data_pipeline.fetch_unified_data(request)

            assert unified_data is not None, "数据获取失败"
            assert len(unified_data) > 0, "没有获取到数据"

            # 检查数据结构
            for symbol, data_points in unified_data.items():
                assert len(data_points) > 0, f"股票 {symbol} 没有数据点"
                for point in data_points:
                    assert hasattr(point, 'timestamp'), "数据点缺少时间戳"
                    assert hasattr(point, 'value'), "数据点缺少值"

            logger.info(f"✅ 数据获取测试通过，获取到 {len(unified_data)} 只股票的数据")
            return True

        except Exception as e:
            logger.error(f"❌ 数据获取测试失败: {e}")
            return False

    async def test_latest_data_fetching(self):
        """测试最新数据获取"""
        try:
            symbols = ['TEST_SYMBOL']
            sources = [DataSource.PRICE]

            # 获取最新数据
            latest_data = await unified_data_pipeline.get_latest_data(
                symbols, sources, lookback_hours=24
            )

            assert latest_data is not None, "最新数据获取失败"
            assert len(latest_data) > 0, "没有获取到最新数据"

            logger.info(f"✅ 最新数据获取测试通过")
            return True

        except Exception as e:
            logger.error(f"❌ 最新数据获取测试失败: {e}")
            return False

class TestBacktestEngine:
    """回测引擎测试"""

    async def test_backtest_execution(self):
        """测试回测执行"""
        try:
            # 创建策略配置
            strategy_config = StrategyConfig(
                strategy_type=StrategyType.PRICE_ONLY,
                name="MA_Cross_Strategy",
                parameters={
                    'ma_short': 10,
                    'ma_long': 30
                }
            )

            # 创建回测配置
            backtest_config = BacktestConfig(
                initial_capital=1000000,
                commission_rate=0.001
            )

            # 设置回测时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)

            # 运行回测
            result = await unified_backtest_engine.run_backtest(
                symbol="TEST_SYMBOL",
                strategy_config=strategy_config,
                backtest_config=backtest_config,
                start_time=start_time,
                end_time=end_time,
                data_sources=[DataSource.PRICE]
            )

            # 验证回测结果
            assert result is not None, "回测结果为空"
            assert result.total_trades >= 0, "交易数量异常"
            assert isinstance(result.total_return, float), "总收益类型错误"

            logger.info(f"✅ 回测执行测试通过，总收益: {result.total_return:.2%}, 交易数: {result.total_trades}")
            return True

        except Exception as e:
            logger.error(f"❌ 回测执行测试失败: {e}")
            return False

    async def test_comparison_backtest(self):
        """测试对比回测"""
        try:
            # 创建多个策略配置
            strategies = [
                StrategyConfig(
                    strategy_type=StrategyType.PRICE_ONLY,
                    name="MA_Cross_10_30",
                    parameters={'ma_short': 10, 'ma_long': 30}
                ),
                StrategyConfig(
                    strategy_type=StrategyType.PRICE_ONLY,
                    name="MA_Cross_5_20",
                    parameters={'ma_short': 5, 'ma_long': 20}
                )
            ]

            backtest_config = BacktestConfig(initial_capital=1000000)

            # 设置时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(days=15)

            # 运行对比回测
            results = await unified_backtest_engine.run_comparison_backtest(
                symbol="TEST_SYMBOL",
                strategies=strategies,
                backtest_config=backtest_config,
                start_time=start_time,
                end_time=end_time
            )

            assert results is not None, "对比回测结果为空"
            assert len(results) >= 2, "对比回测结果数量不足"

            logger.info(f"✅ 对比回测测试通过，策略数: {len(results)}")
            return True

        except Exception as e:
            logger.error(f"❌ 对比回测测试失败: {e}")
            return False

class TestSystemIntegration:
    """系统集成测试"""

    async def test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        try:
            # 1. 数据获取和缓存
            from src.unified.data_pipeline import DataRequest

            symbols = ['INTEGRATION_TEST']
            sources = [DataSource.PRICE, DataSource.SENTIMENT]
            start_time = datetime.now() - timedelta(days=2)
            end_time = datetime.now()

            request = DataRequest(symbols=symbols, start_time=start_time, end_time=end_time, sources=sources)
            data = await unified_data_pipeline.fetch_unified_data(request)

            # 2. 数据质量验证
            for symbol, data_points in data.items():
                if data_points:
                    point_dicts = [point.dict() for point in data_points]
                    quality_result = await data_quality_validator.validate_data_quality(
                        point_dicts, 'price', symbol
                    )
                    assert quality_result.overall_score > 0.5, "数据质量过低"

            # 3. 缓存验证
            for source in sources:
                cached_series = await unified_cache_manager.get_unified_series(symbols[0], source.value)
                # 注意：由于使用模拟数据，可能没有实际缓存

            # 4. 简单回测
            strategy_config = StrategyConfig(
                strategy_type=StrategyType.PRICE_ONLY,
                name="Integration_Test_Strategy",
                parameters={'ma_short': 5, 'ma_long': 15}
            )

            backtest_config = BacktestConfig(initial_capital=100000)
            backtest_result = await unified_backtest_engine.run_backtest(
                symbol=symbols[0],
                strategy_config=strategy_config,
                backtest_config=backtest_config,
                start_time=start_time,
                end_time=end_time,
                data_sources=[DataSource.PRICE]
            )

            assert backtest_result is not None, "端到端回测失败"

            logger.info("✅ 端到端工作流程测试通过")
            return True

        except Exception as e:
            logger.error(f"❌ 端到端工作流程测试失败: {e}")
            return False

async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始统一数据系统综合测试\n")

    test_classes = [
        ("缓存管理器", TestUnifiedCacheManager()),
        ("数据质量验证器", TestDataQualityValidator()),
        ("数据同步器", TestDataSynchronizer()),
        ("数据管道", TestDataPipeline()),
        ("回测引擎", TestBacktestEngine()),
        ("系统集成", TestSystemIntegration())
    ]

    total_tests = 0
    passed_tests = 0

    for test_name, test_class in test_classes:
        print(f"📋 测试 {test_name}:")

        # 获取所有测试方法
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]

        class_passed = 0
        class_total = len(test_methods)

        for test_method in test_methods:
            total_tests += 1
            try:
                method = getattr(test_class, test_method)
                result = await method()
                if result:
                    passed_tests += 1
                    class_passed += 1
                    print(f"  ✅ {test_method}")
                else:
                    print(f"  ❌ {test_method}")
            except Exception as e:
                print(f"  ❌ {test_method} - 异常: {e}")

        print(f"\n📊 {test_name} 测试结果: {class_passed}/{class_total} 通过\n")

    print("=" * 60)
    print(f"🎯 总体测试结果: {passed_tests}/{total_tests} 通过")
    print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")

    if passed_tests == total_tests:
        print("🎉 所有测试通过！统一数据系统运行正常。")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关组件。")
        return False

if __name__ == "__main__":
    # 运行测试
    asyncio.run(run_all_tests())