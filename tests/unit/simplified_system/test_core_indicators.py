#!/usr / bin / env python3
"""
核心技術指標單元測試
Unit tests for Core Technical Indicators
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add simplified_system to path
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent.parent / "simplified_system")
)

from src.indicators.core_indicators import CoreIndicators


class TestCoreIndicators:
    """核心技術指標測試類"""

    @pytest.fixture
    def indicators(self):
        """創建技術指標實例fixture"""
        return CoreIndicators()

    @pytest.fixture
    def sample_prices(self):
        """創建測試價格數據fixture"""
        np.random.seed(42)
        # 生成100個價格點
        initial_price = 100
        returns = np.random.normal(0.001, 0.02, 100)
        prices = [initial_price]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        return pd.Series(
            prices, index = pd.date_range("2024 - 01 - 01", periods = 100, freq="D")
        )

    @pytest.fixture
    def short_prices(self):
        """創建短價格序列fixture（用於邊界測試）"""
        return pd.Series(
            [100, 101, 102, 103, 104],
            index = pd.date_range("2024 - 01 - 01", periods = 5, freq="D"),
        )

    def test_init(self, indicators):
        """測試CoreIndicators初始化"""
        assert indicators.cache is not None
        assert indicators.cache_timeout == 300
        assert isinstance(indicators.cache, dict)

    def test_calculate_sma_success(self, indicators, sample_prices):
        """測試SMA計算成功"""
        sma = indicators.calculate_sma(sample_prices, 20)

        assert isinstance(sma, pd.Series)
        assert len(sma) == len(sample_prices)
        assert sma.index.equals(sample_prices.index)

        # 檢查SMA特性
        assert not sma.isna().all()  # 不應該全為NaN
        assert sma.iloc[-1] > 0  # 最後值應該是正數

    def test_calculate_sma_insufficient_data(self, indicators, short_prices):
        """測試SMA計算數據不足"""
        sma = indicators.calculate_sma(short_prices, 20)

        assert isinstance(sma, pd.Series)
        assert len(sma) == len(short_prices)
        assert sma.isna().all()  # 應該全為NaN

    def test_calculate_ema_success(self, indicators, sample_prices):
        """測試EMA計算成功"""
        ema = indicators.calculate_ema(sample_prices, 26)

        assert isinstance(ema, pd.Series)
        assert len(ema) == len(sample_prices)
        assert ema.index.equals(sample_prices.index)

        # 檢查EMA特性
        assert not ema.isna().all()
        assert ema.iloc[-1] > 0

    def test_calculate_ema_insufficient_data(self, indicators, short_prices):
        """測試EMA計算數據不足"""
        ema = indicators.calculate_ema(short_prices, 26)

        assert isinstance(ema, pd.Series)
        assert len(ema) == len(short_prices)
        assert ema.isna().all()

    def test_calculate_macd_success(self, indicators, sample_prices):
        """測試MACD計算成功"""
        macd_result = indicators.calculate_macd(sample_prices, 12, 26, 9)

        assert isinstance(macd_result, dict)
        assert "macd" in macd_result
        assert "signal" in macd_result
        assert "histogram" in macd_result

        for key, series in macd_result.items():
            assert isinstance(series, pd.Series)
            assert len(series) == len(sample_prices)

        # 檢查MACD特性
        macd = macd_result["macd"]
        signal = macd_result["signal"]
        histogram = macd_result["histogram"]

        # histogram = macd - signal
        expected_histogram = macd - signal
        np.testing.assert_array_almost_equal(histogram, expected_histogram, decimal = 10)

    def test_calculate_macd_insufficient_data(self, indicators, short_prices):
        """測試MACD計算數據不足"""
        macd_result = indicators.calculate_macd(short_prices, 12, 26, 9)

        assert isinstance(macd_result, dict)
        assert "macd" in macd_result
        assert "signal" in macd_result
        assert "histogram" in macd_result

        # 數據不足時應該全為NaN
        for series in macd_result.values():
            assert series.isna().all()

    def test_calculate_rsi_success(self, indicators, sample_prices):
        """測試RSI計算成功"""
        rsi = indicators.calculate_rsi(sample_prices, 14)

        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(sample_prices)
        assert rsi.index.equals(sample_prices.index)

        # 檢查RSI特性 (應該在0 - 100之間)
        valid_rsi = rsi.dropna()
        assert len(valid_rsi) > 0
        assert valid_rsi.min() >= 0
        assert valid_rsi.max() <= 100

    def test_calculate_rsi_insufficient_data(self, indicators, short_prices):
        """測試RSI計算數據不足"""
        rsi = indicators.calculate_rsi(short_prices, 14)

        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(short_prices)
        assert rsi.isna().all()

    def test_calculate_bollinger_bands_success(self, indicators, sample_prices):
        """測試布林帶計算成功"""
        bb_result = indicators.calculate_bollinger_bands(sample_prices, 20, 2)

        assert isinstance(bb_result, dict)
        assert "upper_band" in bb_result
        assert "middle_band" in bb_result
        assert "lower_band" in bb_result

        for key, series in bb_result.items():
            assert isinstance(series, pd.Series)
            assert len(series) == len(sample_prices)

        # 檢查布林帶特性
        upper = bb_result["upper_band"].dropna()
        middle = bb_result["middle_band"].dropna()
        lower = bb_result["lower_band"].dropna()

        valid_count = min(len(upper), len(middle), len(lower))
        if valid_count > 0:
            # 上軌 > 中軌 > 下軌
            assert (upper.iloc[:valid_count] > middle.iloc[:valid_count]).all()
            assert (middle.iloc[:valid_count] > lower.iloc[:valid_count]).all()

    def test_calculate_bollinger_bands_insufficient_data(
        self, indicators, short_prices
    ):
        """測試布林帶計算數據不足"""
        bb_result = indicators.calculate_bollinger_bands(short_prices, 20, 2)

        assert isinstance(bb_result, dict)
        for series in bb_result.values():
            assert isinstance(series, pd.Series)
            assert series.isna().all()

    def test_calculate_atr_success(self, indicators):
        """測試ATR計算成功"""
        # 創建OHLC數據
        np.random.seed(42)
        dates = pd.date_range("2024 - 01 - 01", periods = 100, freq="D")
        close = np.random.uniform(90, 110, 100)
        high = close + np.random.uniform(0, 2, 100)
        low = close - np.random.uniform(0, 2, 100)
        open_price = np.random.uniform(90, 110, 100)

        atr = indicators.calculate_atr(
            pd.Series(high, index = dates),
            pd.Series(low, index = dates),
            pd.Series(close, index = dates),
            pd.Series(open_price, index = dates),
            14,
        )

        assert isinstance(atr, pd.Series)
        assert len(atr) == len(dates)

        # ATR應該是正數
        valid_atr = atr.dropna()
        assert len(valid_atr) > 0
        assert (valid_atr > 0).all()

    def test_calculate_stochastic_success(self, indicators):
        """測試隨機指標計算成功"""
        # 創建OHLC數據
        np.random.seed(42)
        dates = pd.date_range("2024 - 01 - 01", periods = 100, freq="D")
        close = np.random.uniform(90, 110, 100)
        high = close + np.random.uniform(0, 2, 100)
        low = close - np.random.uniform(0, 2, 100)

        stoch_result = indicators.calculate_stochastic(
            pd.Series(high, index = dates),
            pd.Series(low, index = dates),
            pd.Series(close, index = dates),
            14,
            3,
        )

        assert isinstance(stoch_result, dict)
        assert "k_percent" in stoch_result
        assert "d_percent" in stoch_result

        for series in stoch_result.values():
            assert isinstance(series, pd.Series)
            assert len(series) == len(dates)

        # 檢查隨機指標特性 (應該在0 - 100之間)
        k_percent = stoch_result["k_percent"].dropna()
        d_percent = stoch_result["d_percent"].dropna()

        if len(k_percent) > 0:
            assert k_percent.min() >= 0
            assert k_percent.max() <= 100

        if len(d_percent) > 0:
            assert d_percent.min() >= 0
            assert d_percent.max() <= 100


class TestCoreIndicatorsEdgeCases:
    """核心技術指標邊界情況測試"""

    @pytest.fixture
    def indicators(self):
        return CoreIndicators()

    def test_empty_series(self, indicators):
        """測試空序列"""
        empty_series = pd.Series([], dtype = float)

        sma = indicators.calculate_sma(empty_series, 20)
        assert sma.empty

        ema = indicators.calculate_ema(empty_series, 26)
        assert ema.empty

        rsi = indicators.calculate_rsi(empty_series, 14)
        assert rsi.empty

    def test_single_value_series(self, indicators):
        """測試單值序列"""
        single_series = pd.Series([100.0], index=[pd.Timestamp("2024 - 01 - 01")])

        sma = indicators.calculate_sma(single_series, 1)
        assert len(sma) == 1
        assert sma.iloc[0] == 100.0

        # 對於單值，較長週期的指標應該返回NaN
        long_sma = indicators.calculate_sma(single_series, 20)
        assert long_sma.isna().iloc[0]

    def test_constant_prices(self, indicators):
        """測試常數價格序列"""
        constant_prices = pd.Series(
            [100.0] * 100, index = pd.date_range("2024 - 01 - 01", periods = 100, freq="D")
        )

        sma = indicators.calculate_sma(constant_prices, 20)
        # 對於常數序列，SMA應該等於常數
        valid_sma = sma.dropna()
        if len(valid_sma) > 0:
            np.testing.assert_array_almost_equal(valid_sma, 100.0, decimal = 10)

        # RSI對於常數序列可能有特殊行為
        rsi = indicators.calculate_rsi(constant_prices, 14)
        rsi.dropna()
        # 常數序列的RSI可能接近50或其他特定值

    def test_nan_values(self, indicators):
        """測試包含NaN的序列"""
        nan_prices = pd.Series(
            [100.0, np.nan, 102.0, 101.0, 103.0],
            index = pd.date_range("2024 - 01 - 01", periods = 5, freq="D"),
        )

        # 測試SMA對NaN的處理
        sma = indicators.calculate_sma(nan_prices, 3)
        assert isinstance(sma, pd.Series)
        assert len(sma) == len(nan_prices)

        # 測試RSI對NaN的處理
        rsi = indicators.calculate_rsi(nan_prices, 3)
        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(nan_prices)

    def test_extreme_values(self, indicators):
        """測試極端值"""
        extreme_prices = pd.Series(
            [0.0001, 1e6, 0.0001, 1e6, 100.0],
            index = pd.date_range("2024 - 01 - 01", periods = 5, freq="D"),
        )

        # 指標應該能處理極端值而不崩潰
        sma = indicators.calculate_sma(extreme_prices, 3)
        assert isinstance(sma, pd.Series)
        assert len(sma) == len(extreme_prices)

        ema = indicators.calculate_ema(extreme_prices, 3)
        assert isinstance(ema, pd.Series)
        assert len(ema) == len(extreme_prices)


@pytest.mark.sharpe
class TestSharpeCalculation:
    """Sharpe比率計算專用測試"""

    @pytest.fixture
    def indicators(self):
        return CoreIndicators()

    def test_calculate_sharpe_basic(self, indicators, sharpe_test_data):
        """測試基本Sharpe比率計算"""
        returns, risk_free_rate = sharpe_test_data

        sharpe = indicators.calculate_sharpe_ratio(returns, risk_free_rate)

        assert isinstance(sharpe, float)
        assert not np.isnan(sharpe)
        assert not np.isinf(sharpe)

    def test_calculate_sharpe_zero_risk_free_rate(self, indicators):
        """測試零無風險利率Sharpe計算"""
        returns = np.array([0.01, 0.02, -0.01, 0.03])

        sharpe = indicators.calculate_sharpe_ratio(returns, 0.0)

        assert isinstance(sharpe, float)
        assert not np.isnan(sharpe)

    def test_calculate_sharpe_constant_returns(self, indicators):
        """測試常數回報率Sharpe計算"""
        returns = np.array([0.01] * 10)  # 常數回報率
        risk_free_rate = 0.03 / 252

        sharpe = indicators.calculate_sharpe_ratio(returns, risk_free_rate)

        # 常數回報率應該產生特定的Sharpe比率
        assert isinstance(sharpe, float)

    def test_calculate_sharpe_empty_returns(self, indicators):
        """測試空回報率序列"""
        returns = np.array([])
        risk_free_rate = 0.03 / 252

        with pytest.raises((ValueError, IndexError)):
            indicators.calculate_sharpe_ratio(returns, risk_free_rate)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
