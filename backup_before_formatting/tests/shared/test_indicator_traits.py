"""
測試技術指標基礎框架
"""

import numpy as np
import pandas as pd
import pytest
from shared.strategy.traits import (
    BaseIndicator,
    IndicatorCategory,
    IndicatorConfig,
    IndicatorRegistry,
    IndicatorSignal,
    SignalType,
    calculate_returns,
    ensure_ohlcv_columns,
    normalize_series,
    register_indicator,
    smooth_series,
)


class TestIndicatorConfig:
    """技術指標配置測試"""

    def test_config_creation(self):
        """測試配置創建"""
        config = IndicatorConfig(
            name="移動平均",
            category=IndicatorCategory.TREND,
            parameters={"period": 20},
            required_columns=["close"],
            description="簡單移動平均線",
        )
        assert config.name == "移動平均"
        assert config.category == IndicatorCategory.TREND
        assert config.parameters["period"] == 20
        assert "close" in config.required_columns


class TestIndicatorSignal:
    """指標信號測試"""

    def test_signal_creation(self):
        """測試信號創建"""
        signal = IndicatorSignal(
            indicator_name="MA",
            signal=SignalType.BUY,
            strength=0.8,
            value=50.0,
            threshold=45.0,
        )
        assert signal.indicator_name == "MA"
        assert signal.signal == SignalType.BUY
        assert signal.strength == 0.8
        assert signal.value == 50.0
        assert signal.threshold == 45.0
        assert signal.metadata == {}

    def test_signal_with_metadata(self):
        """測試帶元數據的信號"""
        signal = IndicatorSignal(
            indicator_name="RSI",
            signal=SignalType.SELL,
            strength=0.9,
            value=75.0,
            metadata={"overbought": True, "divergence": False},
        )
        assert signal.metadata["overbought"] is True
        assert signal.metadata["divergence"] is False

    def test_signal_to_dict(self):
        """測試信號轉字典"""
        signal = IndicatorSignal(
            indicator_name="MACD",
            signal=SignalType.NEUTRAL,
            strength=0.5,
            value=0.0,
        )
        signal_dict = signal.to_dict()
        assert signal_dict["indicator_name"] == "MACD"
        assert signal_dict["signal"] == "neutral"
        assert signal_dict["strength"] == 0.5
        assert signal_dict["value"] == 0.0


# 創建測試用的技術指標
class TestMAIndicator(BaseIndicator):
    """測試用移動平均指標"""

    def __init__(self, config: IndicatorConfig):
        super().__init__(config)
        self.period = config.parameters.get("period", 20)

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """計算移動平均"""
        close_series = data["close"]
        return close_series.rolling(window=self.period).mean()

    def generate_signals(self, values: pd.Series) -> list[IndicatorSignal]:
        """生成交易信號"""
        signals = []
        data = self.data["close"]

        for i in range(1, len(values)):
            if pd.isna(values.iloc[i]) or pd.isna(data.iloc[i]):
                continue

            price = data.iloc[i]
            ma_value = values.iloc[i]

            if price > ma_value:
                signal = SignalType.BUY
                strength = min(1.0, (price - ma_value) / ma_value * 10)
            elif price < ma_value:
                signal = SignalType.SELL
                strength = min(1.0, (ma_value - price) / ma_value * 10)
            else:
                signal = SignalType.NEUTRAL
                strength = 0.0

            signals.append(
                IndicatorSignal(
                    indicator_name="MA",
                    signal=signal,
                    strength=strength,
                    value=ma_value,
                )
            )

        return signals


class TestRSIIndicator(BaseIndicator):
    """測試用 RSI 指標"""

    def __init__(self, config: IndicatorConfig):
        super().__init__(config)
        self.period = config.parameters.get("period", 14)
        self.overbought = config.parameters.get("overbought", 70)
        self.oversold = config.parameters.get("oversold", 30)

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """計算 RSI"""
        close = data["close"]
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signals(self, values: pd.Series) -> list[IndicatorSignal]:
        """生成交易信號"""
        signals = []
        for i in range(len(values)):
            if pd.isna(values.iloc[i]):
                continue

            rsi_value = values.iloc[i]

            if rsi_value < self.oversold:
                signal = SignalType.BUY
                strength = min(1.0, (self.oversold - rsi_value) / 20)
            elif rsi_value > self.overbought:
                signal = SignalType.SELL
                strength = min(1.0, (rsi_value - self.overbought) / 20)
            else:
                signal = SignalType.NEUTRAL
                strength = 0.0

            signals.append(
                IndicatorSignal(
                    indicator_name="RSI",
                    signal=signal,
                    strength=strength,
                    value=rsi_value,
                    threshold=(
                        self.oversold if signal == SignalType.BUY else self.overbought
                    ),
                )
            )

        return signals


class TestBaseIndicator:
    """基礎指標類測試"""

    @pytest.fixture
    def sample_data(self):
        """創建示例數據"""
        dates = pd.date_range("2023 - 01 - 01", periods=100, freq="D")
        np.random.seed(42)
        base_price = 100

        data = {
            "open": [base_price * (1 + np.random.normal(0, 0.01)) for _ in range(100)],
            "high": [0, 0] * 50,
            "low": [0, 0] * 50,
            "close": [0, 0] * 50,
            "volume": [1000000] * 100,
        }

        # 生成合理的 OHLC 數據
        for i in range(100):
            change = np.random.normal(0, 0.02)
            if i == 0:
                data["open"][i] = base_price
            else:
                data["open"][i] = data["close"][i - 1]

            data["close"][i] = data["open"][i] * (1 + change)
            data["high"][i] = max(data["open"][i], data["close"][i]) * (
                1 + abs(np.random.normal(0, 0.01))
            )
            data["low"][i] = min(data["open"][i], data["close"][i]) * (
                1 - abs(np.random.normal(0, 0.01))
            )

        return pd.DataFrame(data, index=dates)

    def test_indicator_initialization(self, sample_data):
        """測試指標初始化"""
        config = IndicatorConfig(
            name="MA",
            category=IndicatorCategory.TREND,
            parameters={"period": 20},
            required_columns=["close"],
        )
        indicator = TestMAIndicator(config)
        assert indicator.config.name == "MA"
        assert indicator.period == 20
        assert indicator.data is None
        assert not indicator.is_calculated

    def test_data_validation_success(self, sample_data):
        """測試數據驗證成功"""
        config = IndicatorConfig(
            name="MA",
            category=IndicatorCategory.TREND,
            parameters={"period": 20},
            required_columns=["open", "high", "low", "close", "volume"],
        )
        indicator = TestMAIndicator(config)
        assert indicator.validate_data(sample_data) is True

    def test_data_validation_missing_columns(self):
        """測試缺少列的數據驗證"""
        incomplete_data = pd.DataFrame({"close": [100, 101, 102]})
        config = IndicatorConfig(
            name="MA",
            category=IndicatorCategory.TREND,
            parameters={"period": 20},
            required_columns=["open", "high", "low", "close", "volume"],
        )
        indicator = TestMAIndicator(config)
        assert indicator.validate_data(incomplete_data) is False

    def test_indicator_run(self, sample_data):
        """測試指標運行"""
        config = IndicatorConfig(
            name="MA",
            category=IndicatorCategory.TREND,
            parameters={"period": 20},
            required_columns=["close"],
        )
        indicator = TestMAIndicator(config)
        values, signals = indicator.run(sample_data)

        assert indicator.is_calculated
        assert isinstance(values, pd.Series)
        assert isinstance(signals, list)
        assert len(signals) > 0
        assert all(isinstance(s, IndicatorSignal) for s in signals)

    def test_get_latest_signal(self, sample_data):
        """測試獲取最新信號"""
        config = IndicatorConfig(
            name="RSI",
            category=IndicatorCategory.MOMENTUM,
            parameters={"period": 14},
            required_columns=["close"],
        )
        indicator = TestRSIIndicator(config)
        _, signals = indicator.run(sample_data)

        latest = indicator.get_latest_signal()
        if signals:
            assert latest is not None
            assert latest == signals[-1]

    def test_get_signals_by_type(self, sample_data):
        """測試按類型篩選信號"""
        config = IndicatorConfig(
            name="MA",
            category=IndicatorCategory.TREND,
            parameters={"period": 20},
            required_columns=["close"],
        )
        indicator = TestMAIndicator(config)
        _, signals = indicator.run(sample_data)

        buy_signals = indicator.get_signals_by_type(SignalType.BUY)
        sell_signals = indicator.get_signals_by_type(SignalType.SELL)

        assert all(s.signal == SignalType.BUY for s in buy_signals)
        assert all(s.signal == SignalType.SELL for s in sell_signals)

    def test_indicator_to_dict(self, sample_data):
        """測試指標轉字典"""
        config = IndicatorConfig(
            name="MA",
            category=IndicatorCategory.TREND,
            parameters={"period": 20},
            required_columns=["close"],
        )
        indicator = TestMAIndicator(config)
        indicator.run(sample_data)

        result = indicator.to_dict()
        assert "config" in result
        assert "signals" in result
        assert "is_calculated" in result
        assert result["config"]["name"] == "MA"
        assert result["is_calculated"] is True


class TestIndicatorRegistry:
    """指標註冊表測試"""

    def test_registry_creation(self):
        """測試創建註冊表"""
        registry = IndicatorRegistry()
        assert len(registry._indicators) == 0
        assert len(registry._configs) == 0

    def test_register_indicator(self):
        """測試註冊指標"""
        registry = IndicatorRegistry()
        config = IndicatorConfig(
            name="TestIndicator",
            category=IndicatorCategory.CUSTOM,
            parameters={},
            required_columns=["close"],
        )

        registry.register(TestMAIndicator, config)

        assert "TestIndicator" in registry._indicators
        assert "TestIndicator" in registry._configs
        assert registry._indicators["TestIndicator"] == TestMAIndicator
        assert registry._configs["TestIndicator"] == config

    def test_get_indicator(self):
        """測試獲取指標類"""
        registry = IndicatorRegistry()
        config = IndicatorConfig(
            name="TestIndicator",
            category=IndicatorCategory.CUSTOM,
            parameters={},
            required_columns=["close"],
        )
        registry.register(TestMAIndicator, config)

        indicator_class = registry.get_indicator("TestIndicator")
        assert indicator_class == TestMAIndicator

        # 獲取不存在的指標
        assert registry.get_indicator("NonExistent") is None

    def test_get_config(self):
        """測試獲取配置"""
        registry = IndicatorRegistry()
        config = IndicatorConfig(
            name="TestIndicator",
            category=IndicatorCategory.CUSTOM,
            parameters={},
            required_columns=["close"],
        )
        registry.register(TestMAIndicator, config)

        retrieved_config = registry.get_config("TestIndicator")
        assert retrieved_config == config

    def test_create_indicator(self):
        """測試創建指標實例"""
        registry = IndicatorRegistry()
        config = IndicatorConfig(
            name="TestIndicator",
            category=IndicatorCategory.CUSTOM,
            parameters={"period": 20},
            required_columns=["close"],
        )
        registry.register(TestMAIndicator, config)

        indicator = registry.create_indicator("TestIndicator", period=30)
        assert isinstance(indicator, TestMAIndicator)
        assert indicator.period == 30
        assert indicator.config.parameters["period"] == 30

    def test_list_indicators(self):
        """測試列出所有指標"""
        registry = IndicatorRegistry()
        config1 = IndicatorConfig(
            name="Indicator1",
            category=IndicatorCategory.TREND,
            parameters={},
            required_columns=["close"],
        )
        config2 = IndicatorConfig(
            name="Indicator2",
            category=IndicatorCategory.MOMENTUM,
            parameters={},
            required_columns=["close"],
        )

        registry.register(TestMAIndicator, config1)
        registry.register(TestRSIIndicator, config2)

        indicators = registry.list_indicators()
        assert "Indicator1" in indicators
        assert "Indicator2" in indicators

    def test_list_indicators_by_category(self):
        """測試按分類列出指標"""
        registry = IndicatorRegistry()
        config1 = IndicatorConfig(
            name="TrendIndicator",
            category=IndicatorCategory.TREND,
            parameters={},
            required_columns=["close"],
        )
        config2 = IndicatorConfig(
            name="MomentumIndicator",
            category=IndicatorCategory.MOMENTUM,
            parameters={},
            required_columns=["close"],
        )
        config3 = IndicatorConfig(
            name="VolatilityIndicator",
            category=IndicatorCategory.VOLATILITY,
            parameters={},
            required_columns=["close"],
        )

        registry.register(TestMAIndicator, config1)
        registry.register(TestRSIIndicator, config2)
        registry.register(TestMAIndicator, config3)  # 重複使用同一類

        trend_indicators = registry.list_indicators_by_category(IndicatorCategory.TREND)
        assert "TrendIndicator" in trend_indicators

        momentum_indicators = registry.list_indicators_by_category(
            IndicatorCategory.MOMENTUM
        )
        assert "MomentumIndicator" in momentum_indicators

        volatility_indicators = registry.list_indicators_by_category(
            IndicatorCategory.VOLATILITY
        )
        assert "VolatilityIndicator" in volatility_indicators


class TestRegisterDecorator:
    """註冊裝飾器測試"""

    def test_register_indicator_decorator(self):
        """測試指標註冊裝飾器"""
        from shared.strategy.traits import indicator_registry

        config = IndicatorConfig(
            name="DecoratedIndicator",
            category=IndicatorCategory.CUSTOM,
            parameters={},
            required_columns=["close"],
        )

        @register_indicator(config)
        class DecoratedTestIndicator(BaseIndicator):
            def calculate(self, data):
                return data["close"]

            def generate_signals(self, values):
                return []

        assert "DecoratedIndicator" in indicator_registry._indicators
        assert (
            indicator_registry._indicators["DecoratedIndicator"]
            == DecoratedTestIndicator
        )


class TestUtilityFunctions:
    """工具函數測試"""

    def test_ensure_ohlcv_columns(self):
        """測試確保 OHLCV 列"""
        data = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [101, 102, 103],
                "low": [99, 100, 101],
                "close": [100, 101, 102],
                "volume": [1000, 1100, 1200],
            }
        )

        result = ensure_ohlcv_columns(data)
        assert result.equals(data)

    def test_ensure_ohlcv_columns_missing(self):
        """測試缺少列時的錯誤"""
        incomplete_data = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "close": [100, 101, 102],
            }
        )

        with pytest.raises(ValueError):
            ensure_ohlcv_columns(incomplete_data)

    def test_calculate_returns(self):
        """測試計算收益率"""
        prices = pd.Series([100, 101, 102, 100, 103])
        returns = calculate_returns(prices)

        assert len(returns) == len(prices)
        assert pd.isna(returns.iloc[0])
        assert abs(returns.iloc[1] - 0.01) < 0.0001  # (101 - 100)/100

    def test_normalize_series(self):
        """測試標準化序列"""
        series = pd.Series([1, 2, 3, 4, 5])
        normalized = normalize_series(series)

        assert abs(normalized.mean()) < 0.0001  # 均值接近 0
        assert abs(normalized.std() - 1.0) < 0.0001  # 標準差接近 1

    def test_smooth_series(self):
        """測試平滑序列"""
        series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        smoothed = smooth_series(series, window=3)

        assert len(smoothed) == len(series)
        assert pd.isna(smoothed.iloc[0])
        assert pd.isna(smoothed.iloc[1])
        assert not pd.isna(smoothed.iloc[2])


class TestEnums:
    """枚舉類測試"""

    def test_signal_type_enum(self):
        """測試信號類型枚舉"""
        assert SignalType.BUY.value == "buy"
        assert SignalType.SELL.value == "sell"
        assert SignalType.HOLD.value == "hold"
        assert SignalType.NEUTRAL.value == "neutral"

    def test_indicator_category_enum(self):
        """測試指標分類枚舉"""
        assert IndicatorCategory.TREND.value == "trend"
        assert IndicatorCategory.MOMENTUM.value == "momentum"
        assert IndicatorCategory.VOLATILITY.value == "volatility"
        assert IndicatorCategory.VOLUME.value == "volume"
        assert IndicatorCategory.CUSTOM.value == "custom"
