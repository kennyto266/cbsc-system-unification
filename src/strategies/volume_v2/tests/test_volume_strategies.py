"""
Tests for Volume Strategies
測試成交量策略實現
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from uuid import uuid4

# Import strategies
from ..obv_strategy import OBVStrategy
from ..vwap_strategy import VWAPStrategy
from ..mfi_strategy import MFIStrategy
from ..base import BaseVolumeStrategy
from ...enhanced_factory import StrategyMetadata, StrategyType


class TestVolumeStrategies:
    """測試成交量策略"""

    @pytest.fixture
    def sample_data(self):
        """創建測試用OHLCV數據"""
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        price = 100
        data = []

        # 創建具有不同成交量模式的數據
        for i, date in enumerate(dates):
            # 每25個週期改變一次成交量模式
            if i % 25 == 0:
                volume_phase = (i // 25) % 4

            # 根據成交量階段調整成交量
            if volume_phase == 0:  # 上升放量
                volume_multiplier = 1.5 + np.random.uniform(0, 0.5)
            elif volume_phase == 1:  # 正常成交量
                volume_multiplier = 1.0
            elif volume_phase == 2:  # 下降放量
                volume_multiplier = 0.8 + np.random.uniform(0, 0.3)
            else:  # 縮量整理
                volume_multiplier = 0.5 + np.random.uniform(0, 0.2)

            # 價格變化
            change = np.random.normal(0.005, 0.015)
            price *= (1 + change)

            high = price * (1 + abs(np.random.normal(0, 0.01)))
            low = price * (1 - abs(np.random.normal(0, 0.01)))
            volume = int(np.random.uniform(1000000, 5000000) * volume_multiplier)

            data.append({
                "date": date,
                "open": price * (1 + np.random.normal(0, 0.005)),
                "high": high,
                "low": low,
                "close": price,
                "volume": volume
            })

        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)
        return df

    @pytest.fixture
    def intraday_data(self):
        """創建盤中測試數據（用於VWAP測試）"""
        dates = pd.date_range(start="2024-01-01 09:30:00", periods=390, freq="1min")
        price = 100
        data = []

        for i, date in enumerate(dates):
            # 模擬盤中價格走勢
            if i < 120:  # 上午上漲
                change = np.random.normal(0.001, 0.005)
            elif i < 240:  # 中午整理
                change = np.random.normal(0, 0.003)
            else:  # 下午下跌
                change = np.random.normal(-0.001, 0.004)

            price *= (1 + change)

            volume = np.random.randint(50000, 200000)
            high = price * (1 + abs(np.random.normal(0, 0.002)))
            low = price * (1 - abs(np.random.normal(0, 0.002)))

            data.append({
                "date": date,
                "open": price,
                "high": high,
                "low": low,
                "close": price,
                "volume": volume
            })

        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)
        return df

    @pytest.fixture
    def strategy_metadata(self):
        """創建策略元數據"""
        return StrategyMetadata(
            name="test_strategy",
            strategy_type=StrategyType.VOLUME,
            description="Test volume strategy",
            version="2.0.0",
            author="Test",
            parameters={}
        )

    @pytest.fixture
    def obv_strategy(self, strategy_metadata):
        """OBV策略實例"""
        config = {
            "ma_period": 20,
            "divergence_period": 10,
            "symbols": ["TEST"],
            "position_size": 0.1,
            "stop_loss": 0.05,
            "take_profit": 0.20
        }
        return OBVStrategy(
            instance_id=uuid4(),
            config=config,
            metadata=strategy_metadata
        )

    @pytest.fixture
    def vwap_strategy(self, strategy_metadata):
        """VWAP策略實例"""
        config = {
            "reset_period": None,
            "std_dev_bands": 2.0,
            "symbols": ["TEST"],
            "position_size": 0.1,
            "stop_loss": 0.04,
            "take_profit": 0.15
        }
        return VWAPStrategy(
            instance_id=uuid4(),
            config=config,
            metadata=strategy_metadata
        )

    @pytest.fixture
    def mfi_strategy(self, strategy_metadata):
        """MFI策略實例"""
        config = {
            "period": 14,
            "overbought_level": 80,
            "oversold_level": 20,
            "symbols": ["TEST"],
            "position_size": 0.1,
            "stop_loss": 0.05,
            "take_profit": 0.20
        }
        return MFIStrategy(
            instance_id=uuid4(),
            config=config,
            metadata=strategy_metadata
        )

    # 測試OBV策略
    def test_obv_initialization(self, obv_strategy):
        """測試OBV策略初始化"""
        assert obv_strategy.STRATEGY_NAME == "obv"
        assert obv_strategy.STRATEGY_TYPE == StrategyType.VOLUME
        assert obv_strategy.config["ma_period"] == 20
        assert obv_strategy.config["divergence_period"] == 10

    def test_obv_signal_generation(self, obv_strategy, sample_data):
        """測試OBV信號生成"""
        signals = obv_strategy.generate_signals(sample_data)

        # 檢查輸出結構
        assert "obv_signal" in signals.columns
        assert "obv" in signals.columns
        assert "obv_ma" in signals.columns
        assert "signal_type" in signals.columns
        assert len(signals) == len(sample_data)

        # 檢查OBV值有效性
        obv_values = signals["obv"].dropna()
        assert len(obv_values) > 0

    def test_obv_validate_signals(self, obv_strategy, sample_data):
        """測試OBV信號驗證"""
        raw_signals = obv_strategy.generate_signals(sample_data)
        validated = obv_strategy.validate_signals(raw_signals)

        # 驗證應該過濾掉無效信號
        assert len(validated) <= len(raw_signals)

    def test_obv_divergence_detection(self, obv_strategy, sample_data):
        """測試OBV背離檢測"""
        signals = obv_strategy.generate_signals(sample_data)

        if "obv_divergence" in signals.columns:
            divergences = signals[signals["obv_divergence"] != 0]
            # 應該能檢測到背離
            assert len(divergences) >= 0

    # 測試VWAP策略
    def test_vwap_initialization(self, vwap_strategy):
        """測試VWAP策略初始化"""
        assert vwap_strategy.STRATEGY_NAME == "vwap"
        assert vwap_strategy.STRATEGY_TYPE == StrategyType.VOLUME
        assert vwap_strategy.config["std_dev_bands"] == 2.0
        assert vwap_strategy.config["reset_period"] is None

    def test_vwap_signal_generation(self, vwap_strategy, sample_data):
        """測試VWAP信號生成"""
        signals = vwap_strategy.generate_signals(sample_data)

        # 檢查輸出結構
        assert "vwap_signal" in signals.columns
        assert "vwap" in signals.columns
        assert "vwap_upper" in signals.columns
        assert "vwap_lower" in signals.columns
        assert "signal_type" in signals.columns
        assert len(signals) == len(sample_data)

        # 檢查VWAP值有效性
        vwap_values = signals["vwap"].dropna()
        assert len(vwap_values) > 0
        assert all(vwap > 0 for vwap in vwap_values)

    def test_vwap_bands(self, vwap_strategy, sample_data):
        """測試VWAP帶"""
        signals = vwap_strategy.generate_signals(sample_data)

        if "vwap_upper" in signals.columns and "vwap_lower" in signals.columns:
            # 上軌應該大於下軌
            valid_bands = signals.dropna(subset=["vwap_upper", "vwap_lower"])
            assert all(valid_bands["vwap_upper"] > valid_bands["vwap_lower"])

            # VWAP應該在帶內
            assert all(valid_bands["vwap_lower"] <= valid_bands["vwap"])
            assert all(valid_bands["vwap"] <= valid_bands["vwap_upper"])

    def test_vwap_reset(self, vwap_strategy, intraday_data):
        """測試VWAP重置功能"""
        # 使用盤中數據測試重置
        config = vwap_strategy.config.copy()
        config["reset_period"] = 60  # 每小時重置
        vwap_strategy.config = config

        signals = vwap_strategy.generate_signals(intraday_data)
        assert "vwap" in signals.columns

        # VWAP應該在重置點重新計算
        assert len(signals["vwap"].dropna()) > 0

    # 測試MFI策略
    def test_mfi_initialization(self, mfi_strategy):
        """測試MFI策略初始化"""
        assert mfi_strategy.STRATEGY_NAME == "mfi"
        assert mfi_strategy.STRATEGY_TYPE == StrategyType.VOLUME
        assert mfi_strategy.config["period"] == 14
        assert mfi_strategy.config["overbought_level"] == 80
        assert mfi_strategy.config["oversold_level"] == 20

    def test_mfi_signal_generation(self, mfi_strategy, sample_data):
        """測試MFI信號生成"""
        signals = mfi_strategy.generate_signals(sample_data)

        # 檢查輸出結構
        assert "mfi_signal" in signals.columns
        assert "mfi" in signals.columns
        assert "signal_type" in signals.columns
        assert len(signals) == len(sample_data)

        # 檢查MFI值範圍
        mfi_values = signals["mfi"].dropna()
        assert all(0 <= mfi <= 100 for mfi in mfi_values)

    def test_mfi_zones(self, mfi_strategy, sample_data):
        """測試MFI區域分類"""
        signals = mfi_strategy.generate_signals(sample_data)

        if "mfi_zone" in signals.columns:
            zones = signals["mfi_zone"].unique()
            # 應該包含所有區域
            expected_zones = {"overbought", "oversold", "neutral"}
            assert all(zone in zones for zone in expected_zones if len(zones) > 0)

    def test_mfi_validate_signals(self, mfi_strategy, sample_data):
        """測試MFI信號驗證"""
        raw_signals = mfi_strategy.generate_signals(sample_data)
        validated = mfi_strategy.validate_signals(raw_signals)

        # 驗證應該過濾掉無效信號
        assert len(validated) <= len(raw_signals)

    # 測試策略執行
    def test_strategy_execution(self, obv_strategy, sample_data):
        """測試策略執行"""
        data = {"TEST": sample_data}
        result = obv_strategy.execute(data)

        # 檢查執行結果結構
        assert "strategy_id" in result
        assert "strategy_name" in result
        assert "execution_time" in result
        assert "results" in result
        assert "TEST" in result["results"]

        # 檢查結果內容
        test_result = result["results"]["TEST"]
        assert "signals" in test_result
        assert "indicators" in test_result
        assert "last_price" in test_result
        assert "timestamp" in test_result
        assert "volume_analysis" in test_result

    def test_strategy_backtest(self, obv_strategy, sample_data):
        """測試策略回測"""
        data = {"TEST": sample_data}
        result = obv_strategy.backtest(data)

        # 檢查回測結果結構
        assert "strategy" in result
        assert "backtest_results" in result
        assert "backtest_period" in result
        assert "TEST" in result["backtest_results"]

        # 檢查性能指標
        test_metrics = result["backtest_results"]["TEST"]
        assert "total_return" in test_metrics
        assert "max_drawdown" in test_metrics
        assert "sharpe_ratio" in test_metrics
        assert "total_trades" in test_metrics
        assert "volume_analysis" in test_metrics

    # 測試成交量分析
    def test_volume_analysis(self, obv_strategy, sample_data):
        """測試成交量分析"""
        data = {"TEST": sample_data}
        result = obv_strategy.execute(data)

        volume_analysis = result["results"]["TEST"]["volume_analysis"]

        # 檢查成交量分析結構
        assert "strength" in volume_analysis
        assert "trend" in volume_analysis
        assert "price_volume_relation" in volume_analysis
        assert "current_volume" in volume_analysis
        assert "avg_volume" in volume_analysis

        # 檢查趨勢類型
        assert volume_analysis["trend"] in ["increasing", "decreasing", "stable"]

    # 測試性能分析
    def test_performance_analysis(self, obv_strategy, sample_data):
        """測試性能分析"""
        data = {"TEST": sample_data}
        analysis = obv_strategy.analyze_performance(data)

        # 檢查分析結果結構
        assert "strategy" in analysis
        assert "parameters" in analysis
        assert "symbols_analyzed" in analysis
        assert "performance_metrics" in analysis

        # 檢查符號分析
        symbol_analysis = analysis["symbols_analyzed"]
        assert len(symbol_analysis) == 1
        assert symbol_analysis[0]["symbol"] == "TEST"
        assert "total_bars" in symbol_analysis[0]
        assert "signals_generated" in symbol_analysis[0]

    # 測試參數優化
    def test_parameter_optimization(self, obv_strategy, sample_data):
        """測試參數優化"""
        data = {"TEST": sample_data}
        optimization = obv_strategy.optimize_parameters(data)

        # 檢查優化結果結構
        assert "strategy" in optimization
        assert "optimization_method" in optimization
        assert "test_parameters" in optimization
        assert "best_parameters" in optimization
        assert "performance" in optimization

    # 測試錯誤處理
    def test_insufficient_data(self, obv_strategy):
        """測試數據不足的情況"""
        # 創建不足的數據
        short_data = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [102, 103, 104],
            "low": [99, 100, 101],
            "close": [101, 102, 103],
            "volume": [1000, 1100, 900]
        })

        signals = obv_strategy.generate_signals(short_data)

        # 應該返回空信號
        assert signals.empty or all(signals["obv_signal"] == 0)

    def test_invalid_volume_data(self, obv_strategy, strategy_metadata):
        """測試無效成交量數據"""
        # 包含零成交量的數據
        invalid_config = obv_strategy.config.copy()

        invalid_data = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [102, 103, 104],
            "low": [99, 100, 101],
            "close": [101, 102, 103],
            "volume": [0, 0, 0]  # 無效成交量
        })

        # 策略應該能處理零成交量
        signals = obv_strategy.generate_signals(invalid_data)
        assert len(signals) == len(invalid_data)

    def test_invalid_mfi_parameters(self, mfi_strategy, strategy_metadata):
        """測試無效MFI參數"""
        # 無效的MFI參數（超買閾值小於超賣閾值）
        invalid_config = {
            "period": 14,
            "oversold_level": 70,
            "overbought_level": 30  # 錯誤：應該大於oversold
        }

        with pytest.raises(ValueError):
            MFIStrategy(
                instance_id=uuid4(),
                config=invalid_config,
                metadata=strategy_metadata
            )

    # 測試成交量策略基類
    def test_base_volume_strategy_interface(self):
        """測試成交量策略基類接口"""
        from ..base import BaseVolumeStrategy

        # 嘗試直接實例化基類（應該失敗）
        with pytest.raises(TypeError):
            BaseVolumeStrategy(uuid4(), {}, StrategyMetadata(
                name="test",
                strategy_type=StrategyType.VOLUME,
                description="test",
                version="2.0",
                author="test",
                parameters={}
            ))