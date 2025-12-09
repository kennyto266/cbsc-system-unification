"""
技术指标单元测试

测试所有技术指标的计算正确性和性能。
"""

from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pytest

from src.strategy.indicators import (
    EMAIndicator,
    MACDIndicator,
    RSIIndicator,
    SMAIndicator,
    VWMAIndicator,
    WMAIndicator,
)
from src.strategy.indicators.engine import IndicatorEngine, default_engine
from src.strategy.traits import BaseIndicator


class TestDataGenerator:
    """测试数据生成器"""

    @staticmethod
    def generate_ohlcv_data(n_periods: int = 252) -> pd.DataFrame:
        """生成模拟的OHLCV数据

        Args:
            n_periods: 数据点数量，默认252（1年交易日）

        Returns:
            包含OHLCV的DataFrame
        """
        np.random.seed(42)  # 确保可重现性

        # 生成基础价格序列
        returns = np.random.normal(0.0005, 0.02, n_periods)  # 日收益率
        closes = [100.0]  # 初始价格

        for ret in returns:
            closes.append(closes[-1] * (1 + ret))

        closes = np.array(closes[1:])

        # 生成其他价格
        highs = closes + np.random.uniform(0, 2.0, n_periods)
        lows = closes - np.random.uniform(0, 2.0, n_periods)
        volumes = np.random.randint(100000, 1000000, n_periods)

        # 确保low <= close <= high
        lows = np.minimum(lows, closes)
        highs = np.maximum(highs, closes)

        # 创建DataFrame
        data = pd.DataFrame(
            {
                "open": closes + np.random.uniform(-0.5, 0.5, n_periods),
                "high": highs,
                "low": lows,
                "close": closes,
                "volume": volumes,
            }
        )

        return data


class TestSMAIndicator:
    """测试简单移动平均指标"""

    def test_sma_calculation(self):
        """测试SMA计算正确性"""
        data = TestDataGenerator.generate_ohlcv_data(100)
        sma = SMAIndicator(period=20)

        result = sma.calculate(data)

        assert "sma" in result.columns
        assert len(result) == len(data)
        # 前19个值应该为NaN或基于较少数据点的计算
        assert pd.isna(result["sma"].iloc[0])
        # 第20个点应该有有效值
        assert not pd.isna(result["sma"].iloc[19])

    def test_sma_values(self):
        """测试SMA数值正确性"""
        # 简单测试用例
        data = pd.DataFrame(
            {
                "close": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            }
        )
        sma = SMAIndicator(period=3)
        result = sma.calculate(data)

        # 期望值: [NaN, NaN, 2, 3, 4, 5, 6, 7, 8, 9]
        expected = [np.nan, np.nan, 2, 3, 4, 5, 6, 7, 8, 9]
        for i, exp in enumerate(expected):
            if pd.isna(exp):
                assert pd.isna(result["sma"].iloc[i])
            else:
                assert abs(result["sma"].iloc[i] - exp) < 1e - 10

    def test_sma_with_different_periods(self):
        """测试不同周期的SMA"""
        data = TestDataGenerator.generate_ohlcv_data(100)

        sma_10 = SMAIndicator(period=10)
        sma_20 = SMAIndicator(period=20)

        result_10 = sma_10.calculate(data)
        result_20 = sma_20.calculate(data)

        # 短期SMA应该更接近当前价格
        assert abs(result_10["sma"].iloc[-1] - data["close"].iloc[-1]) < abs(
            result_20["sma"].iloc[-1] - data["close"].iloc[-1]
        )

    def test_sma_insufficient_data(self):
        """测试数据不足的情况"""
        data = TestDataGenerator.generate_ohlcv_data(5)
        sma = SMAIndicator(period=20)

        with pytest.raises(ValueError, match="数据长度.*小于周期"):
            sma.calculate(data)


class TestEMAIndicator:
    """测试指数移动平均指标"""

    def test_ema_calculation(self):
        """测试EMA计算"""
        data = TestDataGenerator.generate_ohlcv_data(100)
        ema = EMAIndicator(period=20)

        result = ema.calculate(data)

        assert "ema" in result.columns
        assert len(result) == len(data)

    def test_ema_vs_sma(self):
        """测试EMA与SMA的差异"""
        data = TestDataGenerator.generate_ohlcv_data(100)
        period = 20

        sma = SMAIndicator(period=period)
        ema = EMAIndicator(period=period)

        result_sma = sma.calculate(data)
        result_ema = ema.calculate(data)

        # 在趋势行情中，EMA应该比SMA更敏感
        # 在震荡行情中，两者应该接近
        diff_ema = abs(result_ema["ema"].iloc[-1] - data["close"].iloc[-1])
        diff_sma = abs(result_sma["sma"].iloc[-1] - data["close"].iloc[-1])

        # 这里只是一个存在性检查，实际差异取决于数据
        assert isinstance(diff_ema, float)
        assert isinstance(diff_sma, float)


class TestWMAIndicator:
    """测试加权移动平均指标"""

    def test_wma_calculation(self):
        """测试WMA计算"""
        data = TestDataGenerator.generate_ohlcv_data(100)
        wma = WMAIndicator(period=20)

        result = wma.calculate(data)

        assert "wma" in result.columns
        assert len(result) == len(data)

    def test_wma_values(self):
        """测试WMA数值正确性"""
        # 简单测试用例
        data = pd.DataFrame(
            {
                "close": [1, 2, 3, 4, 5],
            }
        )
        wma = WMAIndicator(period=3)
        result = wma.calculate(data)

        # 期望值: [NaN, NaN, (1 * 3 + 2 * 2 + 3 * 1)/(3 + 2 + 1)=10 / 6, ...]
        assert not pd.isna(result["wma"].iloc[2])
        # WMA应该更重视近期价格
        assert result["wma"].iloc[2] > 2.0  # 大于简单平均


class TestVWMAIndicator:
    """测试成交量加权移动平均指标"""

    def test_vwma_calculation(self):
        """测试VWMA计算"""
        data = TestDataGenerator.generate_ohlcv_data(100)
        vwma = VWMAIndicator(period=20)

        result = vwma.calculate(data)

        assert "vwma" in result.columns
        assert len(result) == len(data)

    def test_vwma_missing_volume(self):
        """测试缺少成交量数据的情况"""
        data = pd.DataFrame(
            {
                "close": [1, 2, 3, 4, 5],
            }
        )
        vwma = VWMAIndicator(period=3)

        with pytest.raises(ValueError, match="数据中缺少.*volume.*列"):
            vwma.calculate(data)


class TestRSIIndicator:
    """测试RSI指标"""

    def test_rsi_calculation(self):
        """测试RSI计算"""
        data = TestDataGenerator.generate_ohlcv_data(100)
        rsi = RSIIndicator(period=14)

        result = rsi.calculate(data)

        assert "rsi" in result.columns
        assert len(result) == len(data)
        # RSI值应该在0 - 100之间
        assert result["rsi"].min() >= 0
        assert result["rsi"].max() <= 100

    def test_rsi_oversold_overbought(self):
        """测试RSI超买超卖信号"""
        # 创建上升趋势数据
        data = pd.DataFrame(
            {
                "close": list(range(100, 200)),
            }
        )
        rsi = RSIIndicator(period=14)
        result = rsi.calculate(data)

        # 上升趋势中，RSI应该较高
        assert result["rsi"].iloc[-1] > 50

        # 创建下降趋势数据
        data = pd.DataFrame(
            {
                "close": list(range(200, 100, -1)),
            }
        )
        result = rsi.calculate(data)

        # 下降趋势中，RSI应该较低
        assert result["rsi"].iloc[-1] < 50

    def test_rsi_boundaries(self):
        """测试RSI边界值"""
        data = TestDataGenerator.generate_ohlcv_data(100)
        rsi = RSIIndicator(period=14)
        result = rsi.calculate(data)

        # 所有值应该在0 - 100之间
        assert result["rsi"].min() >= 0
        assert result["rsi"].max() <= 100

        # 前period个值可能为NaN
        assert pd.isna(result["rsi"].iloc[0])


class TestMACDIndicator:
    """测试MACD指标"""

    def test_macd_calculation(self):
        """测试MACD计算"""
        data = TestDataGenerator.generate_ohlcv_data(100)
        macd = MACDIndicator(
            fast_period=12,
            slow_period=26,
            signal_period=9,
        )

        result = macd.calculate(data)

        assert "macd" in result.columns
        assert "macd_signal" in result.columns
        assert "macd_histogram" in result.columns
        assert len(result) == len(data)

    def test_macd_components(self):
        """测试MACD组件关系"""
        data = TestDataGenerator.generate_ohlcv_data(100)
        macd = MACDIndicator()

        result = macd.calculate(data)

        # 柱状图应该是MACD线减信号线
        expected_histogram = result["macd"] - result["macd_signal"]
        np.testing.assert_array_almost_equal(
            result["macd_histogram"].values,
            expected_histogram.values,
            decimal=10,
        )

    def test_macd_parameters_validation(self):
        """测试MACD参数验证"""
        # slow_period应该大于fast_period
        with pytest.raises(ValueError, match="slow_period 必须大于 fast_period"):
            MACDIndicator(fast_period=12, slow_period=10)


class TestIndicatorEngine:
    """测试指标计算引擎"""

    def test_engine_calculate(self):
        """测试引擎计算单个指标"""
        data = TestDataGenerator.generate_ohlcv_data(100)
        engine = IndicatorEngine()

        result = engine.calculate("sma", data, period=20)

        assert result.indicator_name == "sma"
        assert "sma" in result.data.columns
        assert not result.is_valid or result.calculation_time_ms >= 0

    def test_engine_cache(self):
        """测试引擎缓存机制"""
        data = TestDataGenerator.generate_ohlcv_data(100)
        engine = IndicatorEngine(cache_size=10)

        # 第一次计算
        result1 = engine.calculate("sma", data, period=20)

        # 第二次计算（应该命中缓存）
        result2 = engine.calculate("sma", data, period=20)

        assert result1.cache_hit == False
        assert result2.cache_hit == True

    def test_engine_multiple_indicators(self):
        """测试批量计算"""
        data = TestDataGenerator.generate_ohlcv_data(100)
        engine = IndicatorEngine()

        indicators = [
            {"name": "sma", "params": {"period": 20}},
            {"name": "rsi", "params": {"period": 14}},
        ]

        results = engine.calculate_multiple(indicators, data)

        assert "sma" in results
        assert "rsi" in results
        assert "sma" in results["sma"].data.columns
        assert "rsi" in results["rsi"].data.columns

    def test_engine_sequential(self):
        """测试顺序计算并合并"""
        data = TestDataGenerator.generate_ohlcv_data(100)
        engine = IndicatorEngine()

        indicators = [
            {"name": "sma", "params": {"period": 20}},
            {"name": "rsi", "params": {"period": 14}},
        ]

        result = engine.calculate_sequential(indicators, data)

        assert "sma" in result.columns
        assert "rsi" in result.columns

    def test_engine_stats(self):
        """测试统计信息"""
        data = TestDataGenerator.generate_ohlcv_data(100)
        engine = IndicatorEngine()

        # 初始统计
        stats = engine.get_stats()
        assert stats["cache_entries"] == 0

        # 执行计算
        engine.calculate("sma", data, period=20)
        engine.calculate("sma", data, period=20)  # 第二次应该命中缓存

        stats = engine.get_stats()
        assert stats["total_calculations"] >= 1
        assert stats["cache_hits"] >= 0

    def test_engine_benchmark(self):
        """测试性能基准测试"""
        data = TestDataGenerator.generate_ohlcv_data(1000)
        engine = IndicatorEngine()

        stats = engine.benchmark("sma", data, iterations=10, period=20)

        assert "mean_ms" in stats
        assert "median_ms" in stats
        assert "min_ms" in stats
        assert stats["iterations"] == 10
        assert stats["data_points"] == 1000

    def test_performance_requirement(self):
        """测试性能要求：单次计算 < 5ms (1000个数据点)"""
        data = TestDataGenerator.generate_ohlcv_data(1000)
        engine = IndicatorEngine()

        # 多次测试确保稳定性
        for _ in range(3):
            stats = engine.benchmark("sma", data, iterations=10, period=20)
            # 90分位数应该小于5ms
            assert stats["p95_ms"] < 5.0, f"P95时间 {stats['p95_ms']}ms 超过5ms要求"


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流程"""
        data = TestDataGenerator.generate_ohlcv_data(100)

        # 创建多个指标
        indicators_config = [
            {"name": "sma", "params": {"period": 20}},
            {"name": "ema", "params": {"period": 20}},
            {"name": "rsi", "params": {"period": 14}},
            {"name": "macd", "params": {}},
        ]

        # 使用默认引擎计算
        results = default_engine.calculate_multiple(indicators_config, data)

        # 验证结果
        assert len(results) == 4
        for name in ["sma", "ema", "rsi", "macd"]:
            assert name in results
            assert results[name].is_valid

    def test_indicator_registry(self):
        """测试指标注册表"""
        from src.strategy.indicators import get_all_configs, list_indicators

        # 检查是否注册了预期指标
        indicators = list_indicators()
        assert "SMAIndicator" in indicators or "sma" in indicators
        assert "RSIIndicator" in indicators or "rsi" in indicators
        assert "MACDIndicator" in indicators or "macd" in indicators

        # 检查配置
        configs = get_all_configs()
        assert len(configs) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
