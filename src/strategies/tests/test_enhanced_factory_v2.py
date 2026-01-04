"""
Tests for Enhanced Strategy Factory v2.0
測試增強的策略工廠實現
"""

import pytest
import pandas as pd
import numpy as np
from uuid import uuid4

from ..enhanced_factory_v2 import (
    StrategyFactoryV2,
    strategy_factory,
    create_strategy,
    get_available_strategies,
    get_strategies_by_type
)
from ..enhanced_factory import StrategyMetadata, StrategyType


class TestStrategyFactoryV2:
    """測試策略工廠"""

    @pytest.fixture
    def factory(self):
        """創建策略工廠實例"""
        return StrategyFactoryV2()

    def test_initialization(self, factory):
        """測試工廠初始化"""
        assert len(factory._strategies) > 0
        assert len(factory._strategy_metadata) > 0

        # 應該註冊了所有策略類型
        available = factory.get_available_strategies()
        assert len(available) > 0

    def test_get_available_strategies(self, factory):
        """測試獲取可用策略"""
        strategies = factory.get_available_strategies()

        # 應該包含所有策略類型
        assert isinstance(strategies, dict)

        # 檢查元數據結構
        for name, metadata in strategies.items():
            assert isinstance(metadata, StrategyMetadata)
            assert metadata.name == name
            assert metadata.strategy_type in StrategyType
            assert metadata.description
            assert metadata.version
            assert isinstance(metadata.parameters, dict)

    def test_get_strategies_by_type(self, factory):
        """測試根據類型獲取策略"""
        # 測試技術指標策略
        technical_strategies = factory.get_strategies_by_type(StrategyType.TECHNICAL_ANALYSIS)
        assert isinstance(technical_strategies, dict)
        for metadata in technical_strategies.values():
            assert metadata.strategy_type == StrategyType.TECHNICAL_ANALYSIS

        # 測試動量策略
        momentum_strategies = factory.get_strategies_by_type(StrategyType.MOMENTUM)
        assert isinstance(momentum_strategies, dict)
        for metadata in momentum_strategies.values():
            assert metadata.strategy_type == StrategyType.MOMENTUM

        # 測試成交量策略
        volume_strategies = factory.get_strategies_by_type(StrategyType.VOLUME)
        assert isinstance(volume_strategies, dict)
        for metadata in volume_strategies.values():
            assert metadata.strategy_type == StrategyType.VOLUME

    def test_create_technical_strategy(self, factory):
        """測試創建技術指標策略"""
        config = {
            "fast_period": 10,
            "slow_period": 20,
            "symbols": ["TEST"]
        }

        strategy = factory.create_strategy("ma_crossover", config)
        assert strategy is not None
        # 驗證策略創建成功

    def test_create_momentum_strategy(self, factory):
        """測試創建動量策略"""
        config = {
            "period": 14,
            "trend_threshold": 25,
            "symbols": ["TEST"]
        }

        strategy = factory.create_strategy("adx", config)
        assert strategy is not None

    def test_create_volume_strategy(self, factory):
        """測試創建成交量策略"""
        config = {
            "ma_period": 20,
            "divergence_period": 10,
            "symbols": ["TEST"]
        }

        strategy = factory.create_strategy("obv", config)
        assert strategy is not None

    def test_create_strategy_invalid_name(self, factory):
        """測試創建不存在的策略"""
        with pytest.raises(ValueError, match="Strategy 'invalid' not found"):
            factory.create_strategy("invalid")

    def test_create_strategy_with_config_validation(self, factory):
        """測試創建策略時的配置驗證"""
        # 測試缺少必需參數
        with pytest.raises(ValueError):
            factory.create_strategy("adx", {"trend_threshold": 25})  # 缺少period

        # 測試參數範圍錯誤
        with pytest.raises(ValueError):
            factory.create_strategy("rsi", {"period": -5})  # 負數週期

    def test_validate_strategy_config(self, factory):
        """測試策略配置驗證"""
        # 測試有效配置
        valid_config = {"period": 14, "trend_threshold": 25}
        result = factory.validate_strategy_config("adx", valid_config)
        assert result['valid'] is True
        assert len(result['errors']) == 0

        # 測試無效配置
        invalid_config = {"period": -5}
        result = factory.validate_strategy_config("adx", invalid_config)
        assert result['valid'] is False
        assert len(result['errors']) > 0

    def test_create_strategy_batch(self, factory):
        """測試批量創建策略"""
        configs = [
            {
                "name": "ma_crossover",
                "fast_period": 10,
                "slow_period": 20
            },
            {
                "name": "adx",
                "period": 14,
                "trend_threshold": 25
            },
            {
                "name": "obv",
                "ma_period": 20,
                "divergence_period": 10
            }
        ]

        strategies = factory.create_strategy_batch(configs)
        assert len(strategies) == 3

        # 檢查每個策略都成功創建
        for strategy in strategies:
            assert strategy is not None

    def test_search_strategies(self, factory):
        """測試策略搜索"""
        # 搜索移動平均相關策略
        results = factory.search_strategies("ma")
        assert len(results) >= 1
        assert any("ma" in metadata.name.lower() or
                   "ma" in metadata.description.lower()
                   for metadata in results)

        # 搜索成交量相關策略
        results = factory.search_strategies("volume")
        assert len(results) >= 1

    def test_get_strategy_info(self, factory):
        """測試獲取策略信息"""
        # 獲取存在的策略信息
        info = factory.get_strategy_info("ma_crossover")
        assert info is not None
        assert isinstance(info, StrategyMetadata)
        assert info.name == "ma_crossover"

        # 獲取不存在的策略信息
        info = factory.get_strategy_info("nonexistent")
        assert info is None

    def test_get_strategy_stats(self, factory):
        """測試策略統計"""
        stats = factory.get_strategy_stats()

        assert 'total_strategies' in stats
        assert 'by_type' in stats
        assert 'latest_version' in stats

        assert stats['total_strategies'] > 0
        assert len(stats['by_type']) > 0

    def test_export_strategy_config(self, factory):
        """測試導出策略配置"""
        # 導出存在的策略配置
        config = factory.export_strategy_config("ma_crossover")
        assert config is not None
        assert 'name' in config
        assert 'type' in config
        assert 'parameters' in config
        assert 'required_parameters' in config
        assert 'optional_parameters' in config

        # 導出不存在的策略配置
        config = factory.export_strategy_config("nonexistent")
        assert config is None

    def test_cleanup_strategy_instances(self, factory):
        """測試清理策略實例"""
        # 創建一些實例
        factory.create_strategy("ma_crossover", {"fast_period": 10, "slow_period": 20})
        factory.create_strategy("adx", {"period": 14})

        # 清理實例
        factory.cleanup_strategy_instances()
        assert len(factory._strategy_instances) == 0

    def test_legacy_strategy_compatibility(self, factory):
        """測試遺留策略的向後兼容性"""
        # 應該包含遺留策略
        available = factory.get_available_strategies()
        legacy_strategies = [name for name in available.keys() if name.endswith('_legacy')]
        assert len(legacy_strategies) > 0

        # 應該能創建遺留策略
        if "adx_legacy" in available:
            legacy_strategy = factory.create_strategy("adx_legacy", {"period": 14})
            assert legacy_strategy is not None


class TestGlobalFunctions:
    """測試全局便捷函數"""

    def test_create_strategy_global(self):
        """測試全局創建策略函數"""
        config = {"fast_period": 10, "slow_period": 20}
        strategy = create_strategy("ma_crossover", config)
        assert strategy is not None

    def test_get_available_strategies_global(self):
        """測試全局獲取策略函數"""
        strategies = get_available_strategies()
        assert isinstance(strategies, dict)
        assert len(strategies) > 0

    def test_get_strategies_by_type_global(self):
        """測試全局按類型獲取策略函數"""
        technical = get_strategies_by_type(StrategyType.TECHNICAL_ANALYSIS)
        assert isinstance(technical, dict)

    def test_global_factory_access(self):
        """測試全局工廠實例"""
        # 全局工廠應該可用
        assert strategy_factory is not None
        assert len(strategy_factory._strategies) > 0


class TestStrategyFactoryIntegration:
    """策略工廠集成測試"""

    @pytest.fixture
    def sample_data(self):
        """創建測試數據"""
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        data = []

        for date in dates:
            price = 100 + np.random.normal(0, 2)
            data.append({
                "date": date,
                "open": price,
                "high": price * 1.02,
                "low": price * 0.98,
                "close": price,
                "volume": np.random.randint(1000000, 5000000)
            })

        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)
        return df

    def test_strategy_execution(self, factory, sample_data):
        """測試通過工廠創建和執行策略"""
        # 創建策略
        config = {"fast_period": 10, "slow_period": 20, "symbols": ["TEST"]}
        strategy = factory.create_strategy("ma_crossover", config)

        # 執行策略
        result = strategy.execute({"TEST": sample_data})

        # 驗證執行結果
        assert "strategy_id" in result
        assert "strategy_name" in result
        assert "results" in result
        assert "TEST" in result["results"]

    def test_strategy_batch_execution(self, factory, sample_data):
        """測試批量策略執行"""
        configs = [
            {
                "name": "ma_crossover",
                "fast_period": 10,
                "slow_period": 20
            },
            {
                "name": "adx",
                "period": 14,
                "trend_threshold": 25
            }
        ]

        # 批量創建策略
        strategies = factory.create_strategy_batch(configs)

        # 執行所有策略
        results = []
        for strategy in strategies:
            result = strategy.execute({"TEST": sample_data})
            results.append(result)

        # 驗證所有策略都成功執行
        assert len(results) == len(strategies)
        for result in results:
            assert "strategy_name" in result
            assert "results" in result

    def test_strategy_config_templates(self, factory):
        """測試策略配置模板"""
        # 獲取配置模板
        template = factory.export_strategy_config("ma_crossover")
        assert template is not None

        # 使用模板創建策略
        strategy = factory.create_strategy(
            "ma_crossover",
            template["parameters"]
        )
        assert strategy is not None

        # 驗證配置參數
        metadata = factory.get_strategy_info("ma_crossover")
        if hasattr(strategy, 'config'):
            assert "fast_period" in strategy.config
            assert "slow_period" in strategy.config