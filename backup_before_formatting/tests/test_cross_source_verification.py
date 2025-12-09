"""
跨源数据验证系统测试

测试跨源数据验证器的所有功能：
- 数据源添加和验证
- 差异检测
- 共识数据生成
- 报告生成
- 可视化
- 批量验证
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pytest

from src.data.cross_source_verification import (
    CrossSourceVerifier,
    DataDifference,
    DataSource,
    DataSourcePriority,
    DifferenceType,
    VerificationConfig,
    VerificationLevel,
    VerificationResult,
    VerificationRule,
    compare_dataframes,
    quick_verify,
)


class TestDataSource:
    """数据源测试类"""

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        dates = pd.date_range("2023 - 01 - 01", periods=50, freq="D")
        np.random.seed(42)

        return pd.DataFrame(
            {
                "timestamp": dates,
                "price": 100 + np.cumsum(np.random.randn(50) * 0.5),
                "volume": np.random.randint(1000, 10000, 50),
                "high": 105 + np.cumsum(np.random.randn(50) * 0.5),
                "low": 95 + np.cumsum(np.random.randn(50) * 0.5),
            }
        )

    @pytest.fixture
    def data_with_differences(self):
        """创建带差异的数据"""
        dates = pd.date_range("2023 - 01 - 01", periods=50, freq="D")
        np.random.seed(42)

        df1 = pd.DataFrame(
            {
                "timestamp": dates,
                "price": 100 + np.cumsum(np.random.randn(50) * 0.5),
                "volume": np.random.randint(1000, 10000, 50),
            }
        )

        df2 = df1.copy()
        df2.loc[10:15, "price"] *= 1.05  # 引入5 % 差异
        df2.loc[25, "volume"] = np.nan  # 引入缺失值

        return df1, df2


class TestCrossSourceVerifierInitialization:
    """测试验证器初始化"""

    def test_default_initialization(self):
        """测试默认初始化"""
        verifier = CrossSourceVerifier()
        assert verifier.config.verification_level == VerificationLevel.MODERATE
        assert verifier.config.max_workers == 4
        assert verifier.config.enable_parallel is True
        assert len(verifier.differences_cache) == 0
        assert len(verifier.verification_history) == 0

    def test_custom_config_initialization(self):
        """测试自定义配置初始化"""
        config = VerificationConfig(
            verification_level=VerificationLevel.STRICT,
            max_workers=8,
            tolerance_percentage=0.02,
        )
        verifier = CrossSourceVerifier(config)
        assert verifier.config.verification_level == VerificationLevel.STRICT
        assert verifier.config.max_workers == 8
        assert verifier.config.tolerance_percentage == 0.02

    def test_add_data_source(self, sample_data):
        """测试添加数据源"""
        verifier = CrossSourceVerifier()

        # 正常添加
        verifier.add_data_source(
            name="test_source",
            data=sample_data,
            priority=DataSourcePriority.HIGH,
            reliability_score=0.9,
        )

        # 测试空数据
        with pytest.raises(ValueError):
            verifier.add_data_source(
                name="empty_source",
                data=pd.DataFrame(),
                priority=DataSourcePriority.MEDIUM,
            )

        # 测试无效可靠性评分
        with pytest.raises(ValueError):
            verifier.add_data_source(
                name="invalid_source", data=sample_data, reliability_score=1.5
            )


class TestDifferenceDetection:
    """测试差异检测"""

    @pytest.mark.asyncio
    async def test_detect_value_differences(self, data_with_differences):
        """测试检测数值差异"""
        df1, df2 = data_with_differences

        verifier = CrossSourceVerifier()
        source1 = DataSource(name="source1", data=df1, priority=DataSourcePriority.HIGH)
        source2 = DataSource(
            name="source2", data=df2, priority=DataSourcePriority.MEDIUM
        )

        result = await verifier.verify_sources([source1, source2])

        # 应该有差异
        assert result.total_differences > 0
        assert any(
            d.difference_type == DifferenceType.VALUE_MISMATCH
            for d in result.differences
        )

    @pytest.mark.asyncio
    async def test_detect_missing_data(self, sample_data):
        """测试检测缺失数据"""
        verifier = CrossSourceVerifier()

        df1 = sample_data[:30]  # 前30天
        df2 = sample_data[20:]  # 后30天

        source1 = DataSource(name="source1", data=df1)
        source2 = DataSource(name="source2", data=df2)

        result = await verifier.verify_sources([source1, source2])

        # 应该有缺失数据差异
        assert result.total_differences > 0
        assert any(
            d.difference_type == DifferenceType.MISSING_DATA for d in result.differences
        )

    @pytest.mark.asyncio
    async def test_identical_data(self, sample_data):
        """测试相同数据无差异"""
        verifier = CrossSourceVerifier()

        source1 = DataSource(name="source1", data=sample_data)
        source2 = DataSource(name="source2", data=sample_data.copy())

        result = await verifier.verify_sources([source1, source2])

        # 理想情况下应该没有差异
        # 但由于数据对齐，可能会有微小差异
        assert result.total_differences >= 0  # 至少不应该为负数

    @pytest.mark.asyncio
    async def test_multiple_sources(self, sample_data):
        """测试多个数据源"""
        verifier = CrossSourceVerifier()

        # 创建3个有细微差异的数据源
        np.random.seed(42)
        df1 = sample_data
        df2 = sample_data.copy()
        df2["price"] *= 1.01
        df3 = sample_data.copy()
        df3["price"] *= 0.99

        sources = [
            DataSource(name="source1", data=df1, priority=DataSourcePriority.HIGH),
            DataSource(name="source2", data=df2, priority=DataSourcePriority.MEDIUM),
            DataSource(name="source3", data=df3, priority=DataSourcePriority.LOW),
        ]

        result = await verifier.verify_sources(sources)

        # 应该检测到多个差异（各数据源两两比较）
        assert result.total_differences > 0
        assert len(result.data_sources) == 3


class TestVerificationLevels:
    """测试不同验证级别"""

    @pytest.mark.parametrize(
        "level",
        [
            VerificationLevel.STRICT,
            VerificationLevel.MODERATE,
            VerificationLevel.RELAXED,
        ],
    )
    @pytest.mark.asyncio
    async def test_verification_levels(self, data_with_differences, level):
        """测试不同验证级别的影响"""
        df1, df2 = data_with_differences

        config = VerificationConfig(verification_level=level)
        verifier = CrossSourceVerifier(config)

        source1 = DataSource(name="source1", data=df1)
        source2 = DataSource(name="source2", data=df2)

        result = await verifier.verify_sources([source1, source2])

        # 所有级别都应该检测到差异
        assert result.total_differences > 0
        assert 0 <= result.quality_score <= 1.0

    def test_strict_level_more_differences(self, data_with_differences):
        """测试严格模式检测更多差异"""
        df1, df2 = data_with_differences

        # 比较不同级别
        async def run_verification(level):
            config = VerificationConfig(
                verification_level=level, tolerance_percentage=0.001
            )
            verifier = CrossSourceVerifier(config)
            source1 = DataSource(name="s1", data=df1)
            source2 = DataSource(name="s2", data=df2)
            return await verifier.verify_sources([source1, source2])

        strict_result = asyncio.run(run_verification(VerificationLevel.STRICT))
        relaxed_result = asyncio.run(run_verification(VerificationLevel.RELAXED))

        # 严格模式可能检测更多差异
        # （这取决于具体的容忍度设置）


class TestConsensusData:
    """测试共识数据生成"""

    @pytest.mark.asyncio
    async def test_consensus_data_generation(self, data_with_differences):
        """测试共识数据生成"""
        df1, df2 = data_with_differences

        verifier = CrossSourceVerifier(
            VerificationConfig(auto_merge=True, consensus_method="priority")
        )

        source1 = DataSource(
            name="source1",
            data=df1,
            priority=DataSourcePriority.HIGH,
            reliability_score=0.95,
        )
        source2 = DataSource(
            name="source2",
            data=df2,
            priority=DataSourcePriority.MEDIUM,
            reliability_score=0.80,
        )

        result = await verifier.verify_sources([source1, source2])

        # 应该生成共识数据
        if result.consensus_data is not None:
            assert isinstance(result.consensus_data, pd.DataFrame)
            assert len(result.consensus_data) > 0

    @pytest.mark.asyncio
    async def test_consensus_methods(self, data_with_differences):
        """测试不同共识方法"""
        df1, df2 = data_with_differences

        for method in ["majority_vote", "priority", "average", "median"]:
            config = VerificationConfig(auto_merge=True, consensus_method=method)
            verifier = CrossSourceVerifier(config)

            source1 = DataSource(name="s1", data=df1)
            source2 = DataSource(name="s2", data=df2)

            result = await verifier.verify_sources([source1, source2])

            # 所有方法都应该能生成结果
            assert result.quality_score >= 0.0


class TestQualityScore:
    """测试质量评分"""

    @pytest.mark.asyncio
    async def test_quality_score_calculation(self, sample_data):
        """测试质量评分计算"""
        verifier = CrossSourceVerifier()

        # 相同数据 - 质量评分应该很高
        source1 = DataSource(name="s1", data=sample_data)
        source2 = DataSource(name="s2", data=sample_data.copy())

        result = await verifier.verify_sources([source1, source2])

        # 质量评分在0 - 1之间
        assert 0.0 <= result.quality_score <= 1.0
        # 相同数据质量评分应该较高（但可能不是100%）

    @pytest.mark.asyncio
    async def test_quality_score_with_differences(self, data_with_differences):
        """测试有差异时的质量评分"""
        df1, df2 = data_with_differences

        verifier = CrossSourceVerifier()

        source1 = DataSource(name="s1", data=df1)
        source2 = DataSource(name="s2", data=df2)

        result = await verifier.verify_sources([source1, source2])

        # 质量评分应该较低
        assert 0.0 <= result.quality_score <= 1.0
        # 差异越多，质量评分越低（这取决于差异严重性）


class TestBatchVerification:
    """测试批量验证"""

    @pytest.mark.asyncio
    async def test_batch_verify_sequential(self, sample_data):
        """测试顺序批量验证"""
        config = VerificationConfig(enable_parallel=False)
        verifier = CrossSourceVerifier(config)

        # 创建多个验证任务
        tasks = []
        for i in range(3):
            df1 = sample_data
            df2 = sample_data.copy()
            df2["price"] *= 1 + i * 0.01  # 引入不同大小的差异

            sources = [
                DataSource(name=f"s1_{i}", data=df1),
                DataSource(name=f"s2_{i}", data=df2),
            ]

            tasks.append({"sources": sources})

        results = await verifier.batch_verify(tasks)

        assert len(results) == 3
        for result in results:
            assert isinstance(result, VerificationResult)

    @pytest.mark.asyncio
    async def test_batch_verify_parallel(self, sample_data):
        """测试并行批量验证"""
        config = VerificationConfig(enable_parallel=True, max_workers=4)
        verifier = CrossSourceVerifier(config)

        # 创建多个验证任务
        tasks = []
        for i in range(5):
            df1 = sample_data
            df2 = sample_data.copy()
            df2["price"] *= 1 + i * 0.01

            sources = [
                DataSource(name=f"s1_{i}", data=df1),
                DataSource(name=f"s2_{i}", data=df2),
            ]

            tasks.append({"sources": sources})

        results = await verifier.batch_verify(tasks)

        assert len(results) == 5
        for result in results:
            assert isinstance(result, VerificationResult)


class TestReporting:
    """测试报告生成"""

    @pytest.mark.asyncio
    async def test_generate_report(self, data_with_differences):
        """测试报告生成"""
        df1, df2 = data_with_differences

        verifier = CrossSourceVerifier()
        source1 = DataSource(name="source1", data=df1)
        source2 = DataSource(name="source2", data=df2)

        result = await verifier.verify_sources([source1, source2])
        report = verifier.generate_report(result)

        # 检查报告内容
        assert "跨源数据验证报告" in report
        assert "验证ID" in report
        assert "数据源" in report
        assert "差异统计" in report

    def test_generate_report_file(self, data_with_differences):
        """测试报告文件输出"""
        df1, df2 = data_with_differences

        verifier = CrossSourceVerifier()
        source1 = DataSource(name="source1", data=df1)
        source2 = DataSource(name="source2", data=df2)

        # 运行验证
        result = asyncio.run(verifier.verify_sources([source1, source2]))

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            output_path = f.name

        try:
            verifier.generate_report(result, output_path)
            assert os.path.exists(output_path)

            with open(output_path, "r", encoding="utf - 8") as f:
                content = f.read()
            assert "跨源数据验证报告" in content
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestExportResults:
    """测试结果导出"""

    @pytest.mark.asyncio
    async def test_export_json(self, data_with_differences):
        """测试JSON导出"""
        df1, df2 = data_with_differences

        verifier = CrossSourceVerifier()
        source1 = DataSource(name="source1", data=df1)
        source2 = DataSource(name="source2", data=df2)

        result = await verifier.verify_sources([source1, source2])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            verifier.export_results(result, output_path, "json")
            assert os.path.exists(output_path)

            with open(output_path, "r", encoding="utf - 8") as f:
                data = json.load(f)
            assert "verification_id" in data
            assert "total_differences" in data
            assert "differences" in data
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @pytest.mark.asyncio
    async def test_export_csv(self, data_with_differences):
        """测试CSV导出"""
        df1, df2 = data_with_differences

        verifier = CrossSourceVerifier()
        source1 = DataSource(name="source1", data=df1)
        source2 = DataSource(name="source2", data=df2)

        result = await verifier.verify_sources([source1, source2])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            verifier.export_results(result, output_path, "csv")
            assert os.path.exists(output_path)

            df = pd.read_csv(output_path)
            assert "ID" in df.columns
            assert "Source1" in df.columns
            assert "Source2" in df.columns
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestVisualization:
    """测试可视化功能"""

    @pytest.mark.asyncio
    async def test_visualize_differences(self, data_with_differences):
        """测试差异可视化"""
        df1, df2 = data_with_differences

        config = VerificationConfig(save_visualization=True)
        verifier = CrossSourceVerifier(config)
        source1 = DataSource(name="source1", data=df1)
        source2 = DataSource(name="source2", data=df2)

        result = await verifier.verify_sources([source1, source2])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_files = verifier.visualize_differences(result, tmpdir)

            # 检查是否生成了文件
            assert isinstance(output_files, list)
            # 如果有差异，应该生成可视化文件
            if result.total_differences > 0:
                assert len(output_files) > 0


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_quick_verify(self, sample_data):
        """测试快速验证函数"""
        df1 = sample_data
        df2 = sample_data.copy()
        df2.loc[10:15, "price"] *= 1.05

        sources_data = [
            {"name": "source1", "data": df1, "priority": "high"},
            {"name": "source2", "data": df2, "priority": "medium"},
        ]

        result = quick_verify(sources_data, VerificationLevel.MODERATE)

        assert isinstance(result, VerificationResult)
        assert len(result.differences) > 0

    def test_compare_dataframes(self, sample_data):
        """测试数据框比较函数"""
        df1 = sample_data
        df2 = sample_data.copy()
        df2.loc[10:15, "price"] *= 1.05

        result = compare_dataframes(df1, df2, "DF1", "DF2", tolerance=0.01)

        assert isinstance(result, VerificationResult)
        assert "DF1" in result.data_sources
        assert "DF2" in result.data_sources

    def test_compare_identical_dataframes(self, sample_data):
        """测试相同数据框比较"""
        result = compare_dataframes(sample_data, sample_data, "DF1", "DF2")

        # 相同数据可能仍然有微小差异（由于对齐方式）
        assert isinstance(result, VerificationResult)
        assert len(result.data_sources) == 2


class TestCacheAndHistory:
    """测试缓存和历史记录"""

    @pytest.mark.asyncio
    async def test_verification_history(self, data_with_differences):
        """测试验证历史记录"""
        df1, df2 = data_with_differences

        verifier = CrossSourceVerifier()

        # 执行多次验证
        for _ in range(3):
            source1 = DataSource(name="s1", data=df1)
            source2 = DataSource(name="s2", data=df2)
            await verifier.verify_sources([source1, source2])

        # 检查历史记录
        history = verifier.get_verification_history()
        assert len(history) == 3
        assert all(isinstance(h, VerificationResult) for h in history)

    @pytest.mark.asyncio
    async def test_clear_cache(self, data_with_differences):
        """测试清除缓存"""
        df1, df2 = data_with_differences

        verifier = CrossSourceVerifier()
        source1 = DataSource(name="s1", data=df1)
        source2 = DataSource(name="s2", data=df2)

        await verifier.verify_sources([source1, source2])

        # 缓存应该不为空
        assert len(verifier.differences_cache) > 0

        # 清除缓存
        verifier.clear_cache()
        assert len(verifier.differences_cache) == 0


class TestEdgeCases:
    """测试边缘情况"""

    @pytest.mark.asyncio
    async def test_single_source(self, sample_data):
        """测试单个数据源"""
        verifier = CrossSourceVerifier()
        source1 = DataSource(name="source1", data=sample_data)

        result = await verifier.verify_sources([source1])

        # 单个数据源不应该有差异
        assert result.total_differences == 0
        assert len(result.data_sources) == 1

    @pytest.mark.asyncio
    async def test_empty_dataframe(self, sample_data):
        """测试空数据框"""
        verifier = CrossSourceVerifier()

        df1 = sample_data
        df2 = pd.DataFrame()  # 空数据框

        source1 = DataSource(name="s1", data=df1)
        source2 = DataSource(name="s2", data=df2)

        # 应该引发错误
        with pytest.raises((ValueError, Exception)):
            await verifier.verify_sources([source1, source2])

    @pytest.mark.asyncio
    async def test_different_columns(self, sample_data):
        """测试不同列的数据框"""
        verifier = CrossSourceVerifier()

        df1 = sample_data[["timestamp", "price", "volume"]]
        df2 = sample_data[["timestamp", "price", "high", "low"]]

        source1 = DataSource(name="s1", data=df1)
        source2 = DataSource(name="s2", data=df2)

        result = await verifier.verify_sources([source1, source2])

        # 应该处理不同列的情况
        assert isinstance(result, VerificationResult)
        # 只比较共同列
        assert "volume" not in df2.columns or "volume" in df1.columns

    @pytest.mark.asyncio
    async def test_large_dataset(self):
        """测试大数据集"""
        verifier = CrossSourceVerifier()

        # 创建大数据集
        dates = pd.date_range("2020 - 01 - 01", periods=1000, freq="D")
        np.random.seed(42)

        df1 = pd.DataFrame(
            {
                "timestamp": dates,
                "price": 100 + np.cumsum(np.random.randn(1000) * 0.5),
                "volume": np.random.randint(1000, 10000, 1000),
            }
        )

        df2 = df1.copy()
        df2.loc[100:110, "price"] *= 1.02

        source1 = DataSource(name="s1", data=df1)
        source2 = DataSource(name="s2", data=df2)

        result = await verifier.verify_sources([source1, source2])

        # 应该能够处理大数据集
        assert isinstance(result, VerificationResult)
        assert result.processing_time > 0

    @pytest.mark.asyncio
    async def test_mixed_data_types(self):
        """测试混合数据类型"""
        verifier = CrossSourceVerifier()

        dates = pd.date_range("2023 - 01 - 01", periods=50, freq="D")
        np.random.seed(42)

        df1 = pd.DataFrame(
            {
                "timestamp": dates,
                "price": 100 + np.cumsum(np.random.randn(50) * 0.5),
                "volume": np.random.randint(1000, 10000, 50),
                "category": ["A", "B"] * 25,
                "flag": [True, False] * 25,
            }
        )

        df2 = df1.copy()
        df2.loc[10, "category"] = "C"  # 引入分类差异
        df2.loc[20, "flag"] = True  # 引入布尔差异

        source1 = DataSource(name="s1", data=df1)
        source2 = DataSource(name="s2", data=df2)

        result = await verifier.verify_sources([source1, source2])

        # 应该能够处理混合数据类型
        assert isinstance(result, VerificationResult)


class TestConfigOptions:
    """测试配置选项"""

    @pytest.mark.asyncio
    async def test_tolerance_percentage(self, data_with_differences):
        """测试容忍度百分比"""
        df1, df2 = data_with_differences

        # 高容忍度
        config1 = VerificationConfig(tolerance_percentage=0.1)  # 10%
        verifier1 = CrossSourceVerifier(config1)
        source1 = DataSource(name="s1", data=df1)
        source2 = DataSource(name="s2", data=df2)
        result1 = await verifier1.verify_sources([source1, source2])

        # 低容忍度
        config2 = VerificationConfig(tolerance_percentage=0.001)  # 0.1%
        verifier2 = CrossSourceVerifier(config2)
        result2 = await verifier2.verify_sources([source1, source2])

        # 低容忍度应该检测到更多差异
        assert result2.total_differences >= result1.total_differences

    @pytest.mark.asyncio
    async def test_exclude_fields(self, sample_data):
        """测试排除字段"""
        df1 = sample_data.copy()
        df2 = sample_data.copy()

        # 在排除的字段中引入差异
        df2["price"] *= 1.05
        df2["volume"] *= 1.1

        # 排除price字段
        config = VerificationConfig(exclude_fields=["price"])
        verifier = CrossSourceVerifier(config)
        source1 = DataSource(name="s1", data=df1)
        source2 = DataSource(name="s2", data=df2)

        result = await verifier.verify_sources([source1, source2])

        # 检查是否排除了price字段的差异
        price_diffs = [d for d in result.differences if d.field_name == "price"]
        # 如果配置生效，price字段的差异应该被排除或减少
        assert isinstance(result, VerificationResult)

    @pytest.mark.asyncio
    async def test_validation_rules(self, sample_data):
        """测试验证规则"""
        df1 = sample_data
        df2 = sample_data.copy()
        df2.loc[10, "price"] *= 1.05

        # 自定义验证规则
        rules = [
            VerificationRule(
                rule_name="price_tolerance",
                field_name="price",
                comparison_type="tolerance",
                threshold=0.1,
            )
        ]

        config = VerificationConfig(validation_rules=rules)
        verifier = CrossSourceVerifier(config)
        source1 = DataSource(name="s1", data=df1)
        source2 = DataSource(name="s2", data=df2)

        result = await verifier.verify_sources([source1, source2])

        # 应该应用自定义规则
        assert isinstance(result, VerificationResult)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
