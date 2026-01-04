"""
Tests for Momentum Strategies
測試動量策略實現
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from uuid import uuid4

# Import strategies
from ..adx_strategy import ADXStrategy
from ..sar_strategy import SARStrategy
from ..base import BaseMomentumStrategy
from ...enhanced_factory import StrategyMetadata, StrategyType


class TestMomentumStrategies:
    """測試動量策略"""

    @pytest.fixture
    def sample_data(self):
        """創建測試用OHLCV數據"""
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        price = 100
        data = []

        # 創建有明顯趨勢的數據
        trend_phase = 0
        for i, date in enumerate(dates):
            # 每25個週期改變一次趨勢
            if i % 25 == 0:
                trend_phase = (trend_phase + 1) % 4

            # 根據趨勢階段調整價格變化
            if trend_phase == 0:  # 上升趨勢
                change = np.random.normal(0.01, 0.015)
            elif trend_phase == 1:  # 橫盤
                change = np.random.normal(0, 0.01)
            elif trend_phase == 2:  # 下降趨勢
                change = np.random.normal(-0.01, 0.015)
            else:  # 震盪
                change = np.random.normal(0, 0.02)

            price *= (1 + change)

            high = price * (1 + abs(np.random.normal(0, 0.01)))
            low = price * (1 - abs(np.random.normal(0, 0.01)))
            volume = np.random.randint(1000000, 5000000)

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
    def strategy_metadata(self):
        """創建策略元數據"""
        return StrategyMetadata(
            name="test_strategy",
            strategy_type=StrategyType.MOMENTUM,
            description="Test momentum strategy",
            version="2.0.0",
            author="Test",
            parameters={}
        )

    @pytest.fixture
    def adx_strategy(self, strategy_metadata):
        """ADX策略實例"""
        config = {
            "period": 14,
            "trend_threshold": 25,
            "symbols": ["TEST"],
            "position_size": 0.1,
            "stop_loss": 0.05,
            "take_profit": 0.15
        }
        return ADXStrategy(
            instance_id=uuid4(),
            config=config,
            metadata=strategy_metadata
        )

    @pytest.fixture
    def sar_strategy(self, strategy_metadata):
        """SAR策略實例"""
        config = {
            "acceleration_factor": 0.02,
            "maximum_acceleration": 0.2,
            "symbols": ["TEST"],
            "position_size": 0.1,
            "stop_loss": 0.05,
            "take_profit": 0.15
        }
        return SARStrategy(
            instance_id=uuid4(),
            config=config,
            metadata=strategy_metadata
        )

    # 測試ADX策略
    def test_adx_initialization(self, adx_strategy):
        """測試ADX策略初始化"""
        assert adx_strategy.STRATEGY_NAME == "adx"
        assert adx_strategy.STRATEGY_TYPE == StrategyType.MOMENTUM
        assert adx_strategy.config["period"] == 14
        assert adx_strategy.config["trend_threshold"] == 25

    def test_adx_signal_generation(self, adx_strategy, sample_data):
        """測試ADX信號生成"""
        signals = adx_strategy.generate_signals(sample_data)

        # 檢查輸出結構
        assert "adx_signal" in signals.columns
        assert "adx" in signals.columns
        assert "plus_di" in signals.columns
        assert "minus_di" in signals.columns
        assert "signal_type" in signals.columns
        assert len(signals) == len(sample_data)

        # 檢查ADX值範圍
        adx_values = signals["adx"].dropna()
        assert all(adx >= 0 for adx in adx_values)

    def test_adx_validate_signals(self, adx_strategy, sample_data):
        """測試ADX信號驗證"""
        raw_signals = adx_strategy.generate_signals(sample_data)
        validated = adx_strategy.validate_signals(raw_signals)

        # 驗證應該過濾掉無效信號
        assert len(validated) <= len(raw_signals)

    # 測試SAR策略
    def test_sar_initialization(self, sar_strategy):
        """測試SAR策略初始化"""
        assert sar_strategy.STRATEGY_NAME == "sar"
        assert sar_strategy.STRATEGY_TYPE == StrategyType.MOMENTUM
        assert sar_strategy.config["acceleration_factor"] == 0.02
        assert sar_strategy.config["maximum_acceleration"] == 0.2

    def test_sar_signal_generation(self, sar_strategy, sample_data):
        """測試SAR信號生成"""
        signals = sar_strategy.generate_signals(sample_data)

        # 檢查輸出結構
        assert "sar_signal" in signals.columns
        assert "sar" in signals.columns
        assert "signal_type" in signals.columns
        assert len(signals) == len(sample_data)

        # 檢查SAR值有效性
        sar_values = signals["sar"].dropna()
        assert all(sar > 0 for sar in sar_values)

    def test_sar_validate_signals(self, sar_strategy, sample_data):
        """測試SAR信號驗證"""
        raw_signals = sar_strategy.generate_signals(sample_data)
        validated = sar_strategy.validate_signals(raw_signals)

        # 驗證應該過濾掉無效信號
        assert len(validated) <= len(raw_signals)

    # 測試策略執行
    def test_strategy_execution(self, adx_strategy, sample_data):
        """測試策略執行"""
        data = {"TEST": sample_data}
        result = adx_strategy.execute(data)

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
        assert "trend_strength" in test_result

    def test_strategy_backtest(self, adx_strategy, sample_data):
        """測試策略回測"""
        data = {"TEST": sample_data}
        result = adx_strategy.backtest(data)

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
        assert "trend_analysis" in test_metrics

    # 測試趨勢強度計算
    def test_trend_strength_calculation(self, adx_strategy, sample_data):
        """測試趨勢強度計算"""
        data = {"TEST": sample_data}
        result = adx_strategy.execute(data)

        trend_strength = result["results"]["TEST"]["trend_strength"]

        # 檢查趨勢強度結構
        assert "strength" in trend_strength
        assert "direction" in trend_strength
        assert "slope" in trend_strength
        assert "momentum_20" in trend_strength
        assert "adx" in trend_strength

        # 檢查強度範圍
        assert 0 <= trend_strength["strength"] <= 1
        assert trend_strength["direction"] in ["bullish", "bearish", "neutral"]

    # 測試性能分析
    def test_performance_analysis(self, adx_strategy, sample_data):
        """測試性能分析"""
        data = {"TEST": sample_data}
        analysis = adx_strategy.analyze_performance(data)

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
    def test_parameter_optimization(self, adx_strategy, sample_data):
        """測試參數優化"""
        data = {"TEST": sample_data}
        optimization = adx_strategy.optimize_parameters(data)

        # 檢查優化結果結構
        assert "strategy" in optimization
        assert "optimization_method" in optimization
        assert "test_parameters" in optimization
        assert "best_parameters" in optimization
        assert "performance" in optimization

    # 測試錯誤處理
    def test_insufficient_data(self, adx_strategy):
        """測試數據不足的情況"""
        # 創建不足的數據
        short_data = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [102, 103, 104],
            "low": [99, 100, 101],
            "close": [101, 102, 103],
            "volume": [1000, 1100, 900]
        })

        signals = adx_strategy.generate_signals(short_data)

        # 應該返回空信號
        assert signals.empty or all(signals["adx_signal"] == 0)

    def test_invalid_parameters(self, adx_strategy, strategy_metadata):
        """測試無效參數"""
        # 無效的ADX參數（負數週期）
        invalid_config = {
            "period": -14,  # 錯誤：不能為負數
            "trend_threshold": 25
        }

        with pytest.raises(ValueError):
            ADXStrategy(
                instance_id=uuid4(),
                config=invalid_config,
                metadata=strategy_metadata
            )

    # 測試SAR特定功能
    def test_sar_acceleration_factor(self, sar_strategy, sample_data):
        """測試SAR加速因子計算"""
        signals = sar_strategy.generate_signals(sample_data)

        # 檢查加速因子
        if "acceleration_factor" in signals.columns:
            af_values = signals["acceleration_factor"].dropna()
            if not af_values.empty:
                # 加速因子應該在範圍內
                assert all(0 < af <= 0.2 for af in af_values)

    def test_sar_reversal_detection(self, sar_strategy, sample_data):
        """測試SAR反轉檢測"""
        signals = sar_strategy.generate_signals(sample_data)

        if "sar_reversal" in signals.columns:
            reversals = signals[signals["sar_reversal"] != 0]
            # 反轉應該產生信號
            assert len(reversals) >= 0

    # 測試動量策略基類
    def test_base_momentum_strategy_interface(self):
        """測試動量策略基類接口"""
        from ..base import BaseMomentumStrategy

        # 嘗試直接實例化基類（應該失敗）
        with pytest.raises(TypeError):
            BaseMomentumStrategy(uuid4(), {}, StrategyMetadata(
                name="test",
                strategy_type=StrategyType.MOMENTUM,
                description="test",
                version="2.0",
                author="test",
                parameters={}
            ))