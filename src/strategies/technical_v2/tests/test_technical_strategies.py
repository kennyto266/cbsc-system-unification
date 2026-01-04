"""
Tests for Technical Indicator Strategies
測試技術指標策略實現
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from uuid import uuid4

# Import strategies
from ..ma_crossover import MACrossoverStrategy
from ..rsi_strategy import RSIStrategy
from ..macd_strategy import MACDStrategy
from ..bollinger_bands import BollingerBandsStrategy
from ..base import BaseTechnicalIndicatorStrategy
from ...enhanced_factory import StrategyMetadata, StrategyType


class TestTechnicalIndicatorStrategies:
    """測試技術指標策略"""

    @pytest.fixture
    def sample_data(self):
        """創建測試用OHLCV數據"""
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        price = 100
        data = []

        for i, date in enumerate(dates):
            # 模擬價格波動
            change = np.random.normal(0, 0.02)  # 2%日波動率
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
            strategy_type=StrategyType.TECHNICAL_ANALYSIS,
            description="Test strategy",
            version="2.0.0",
            author="Test",
            parameters={}
        )

    @pytest.fixture
    def ma_crossover_strategy(self, strategy_metadata):
        """MA交叉策略實例"""
        config = {
            "fast_period": 10,
            "slow_period": 20,
            "symbols": ["TEST"],
            "position_size": 0.1,
            "stop_loss": 0.05,
            "take_profit": 0.10
        }
        return MACrossoverStrategy(
            instance_id=uuid4(),
            config=config,
            metadata=strategy_metadata
        )

    @pytest.fixture
    def rsi_strategy(self, strategy_metadata):
        """RSI策略實例"""
        config = {
            "period": 14,
            "oversold_threshold": 30,
            "overbought_threshold": 70,
            "symbols": ["TEST"],
            "position_size": 0.1
        }
        return RSIStrategy(
            instance_id=uuid4(),
            config=config,
            metadata=strategy_metadata
        )

    @pytest.fixture
    def macd_strategy(self, strategy_metadata):
        """MACD策略實例"""
        config = {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
            "symbols": ["TEST"],
            "position_size": 0.1
        }
        return MACDStrategy(
            instance_id=uuid4(),
            config=config,
            metadata=strategy_metadata
        )

    @pytest.fixture
    def bollinger_bands_strategy(self, strategy_metadata):
        """布林帶策略實例"""
        config = {
            "period": 20,
            "std_dev": 2.0,
            "symbols": ["TEST"],
            "position_size": 0.1
        }
        return BollingerBandsStrategy(
            instance_id=uuid4(),
            config=config,
            metadata=strategy_metadata
        )

    # 測試MA交叉策略
    def test_ma_crossover_initialization(self, ma_crossover_strategy):
        """測試MA交叉策略初始化"""
        assert ma_crossover_strategy.STRATEGY_NAME == "ma_crossover"
        assert ma_crossover_strategy.STRATEGY_TYPE == StrategyType.MOMENTUM
        assert ma_crossover_strategy.config["fast_period"] == 10
        assert ma_crossover_strategy.config["slow_period"] == 20

    def test_ma_crossover_signal_generation(self, ma_crossover_strategy, sample_data):
        """測試MA交叉信號生成"""
        signals = ma_crossover_strategy.generate_signals(sample_data)

        # 檢查輸出結構
        assert "ma_cross_signal" in signals.columns
        assert "fast_ma" in signals.columns
        assert "slow_ma" in signals.columns
        assert "signal_type" in signals.columns
        assert len(signals) == len(sample_data)

    def test_ma_crossover_validate_signals(self, ma_crossover_strategy, sample_data):
        """測試MA交叉信號驗證"""
        raw_signals = ma_crossover_strategy.generate_signals(sample_data)
        validated = ma_crossover_strategy.validate_signals(raw_signals)

        # 驗證應該過濾掉無效信號
        assert len(validated) <= len(raw_signals)

    # 測試RSI策略
    def test_rsi_initialization(self, rsi_strategy):
        """測試RSI策略初始化"""
        assert rsi_strategy.STRATEGY_NAME == "rsi"
        assert rsi_strategy.STRATEGY_TYPE == StrategyType.TECHNICAL_ANALYSIS
        assert rsi_strategy.config["period"] == 14
        assert rsi_strategy.config["oversold_threshold"] == 30

    def test_rsi_signal_generation(self, rsi_strategy, sample_data):
        """測試RSI信號生成"""
        signals = rsi_strategy.generate_signals(sample_data)

        # 檢查輸出結構
        assert "rsi_signal" in signals.columns
        assert "rsi_value" in signals.columns
        assert "signal_type" in signals.columns
        assert len(signals) == len(sample_data)

        # 檢查RSI值範圍
        rsi_values = signals["rsi_value"].dropna()
        assert all(0 <= rsi <= 100 for rsi in rsi_values)

    def test_rsi_validate_signals(self, rsi_strategy, sample_data):
        """測試RSI信號驗證"""
        raw_signals = rsi_strategy.generate_signals(sample_data)
        validated = rsi_strategy.validate_signals(raw_signals)

        # 驗證應該過濾掉無效信號
        assert len(validated) <= len(raw_signals)

    # 測試MACD策略
    def test_macd_initialization(self, macd_strategy):
        """測試MACD策略初始化"""
        assert macd_strategy.STRATEGY_NAME == "macd"
        assert macd_strategy.STRATEGY_TYPE == StrategyType.MOMENTUM
        assert macd_strategy.config["fast_period"] == 12
        assert macd_strategy.config["slow_period"] == 26
        assert macd_strategy.config["signal_period"] == 9

    def test_macd_signal_generation(self, macd_strategy, sample_data):
        """測試MACD信號生成"""
        signals = macd_strategy.generate_signals(sample_data)

        # 檢查輸出結構
        assert "macd_line" in signals.columns
        assert "macd_signal" in signals.columns
        assert "macd_histogram" in signals.columns
        assert "signal_type" in signals.columns
        assert len(signals) == len(sample_data)

    def test_macd_validate_signals(self, macd_strategy, sample_data):
        """測試MACD信號驗證"""
        raw_signals = macd_strategy.generate_signals(sample_data)
        validated = macd_strategy.validate_signals(raw_signals)

        # 驗證應該過濾掉無效信號
        assert len(validated) <= len(raw_signals)

    # 測試布林帶策略
    def test_bollinger_bands_initialization(self, bollinger_bands_strategy):
        """測試布林帶策略初始化"""
        assert bollinger_bands_strategy.STRATEGY_NAME == "bollinger_bands"
        assert bollinger_bands_strategy.STRATEGY_TYPE == StrategyType.VOLATILITY
        assert bollinger_bands_strategy.config["period"] == 20
        assert bollinger_bands_strategy.config["std_dev"] == 2.0

    def test_bollinger_bands_signal_generation(self, bollinger_bands_strategy, sample_data):
        """測試布林帶信號生成"""
        signals = bollinger_bands_strategy.generate_signals(sample_data)

        # 檢查輸出結構
        assert "bb_upper" in signals.columns
        assert "bb_middle" in signals.columns
        assert "bb_lower" in signals.columns
        assert "bb_final_signal" in signals.columns
        assert "signal_type" in signals.columns
        assert len(signals) == len(sample_data)

        # 檢查布林帶關係
        valid_bands = signals.dropna(subset=["bb_upper", "bb_lower"])
        assert all(valid_bands["bb_upper"] > valid_bands["bb_lower"])

    def test_bollinger_bands_validate_signals(self, bollinger_bands_strategy, sample_data):
        """測試布林帶信號驗證"""
        raw_signals = bollinger_bands_strategy.generate_signals(sample_data)
        validated = bollinger_bands_strategy.validate_signals(raw_signals)

        # 驗證應該過濾掉無效信號
        assert len(validated) <= len(raw_signals)

    # 測試策略執行
    def test_strategy_execution(self, ma_crossover_strategy, sample_data):
        """測試策略執行"""
        data = {"TEST": sample_data}
        result = ma_crossover_strategy.execute(data)

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

    def test_strategy_backtest(self, ma_crossover_strategy, sample_data):
        """測試策略回測"""
        data = {"TEST": sample_data}
        result = ma_crossover_strategy.backtest(data)

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

    # 測試性能分析
    def test_performance_analysis(self, ma_crossover_strategy, sample_data):
        """測試性能分析"""
        data = {"TEST": sample_data}
        analysis = ma_crossover_strategy.analyze_performance(data)

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

    # 測試參數優化
    def test_parameter_optimization(self, rsi_strategy, sample_data):
        """測試參數優化"""
        data = {"TEST": sample_data}
        optimization = rsi_strategy.optimize_parameters(data)

        # 檢查優化結果結構
        assert "strategy" in optimization
        assert "optimization_method" in optimization
        assert "test_parameters" in optimization
        assert "best_parameters" in optimization
        assert "performance" in optimization

    # 測試錯誤處理
    def test_insufficient_data(self, ma_crossover_strategy):
        """測試數據不足的情況"""
        # 創建不足的數據
        short_data = pd.DataFrame({
            "close": [100, 101, 102],
            "volume": [1000, 1100, 900]
        })

        signals = ma_crossover_strategy.generate_signals(short_data)

        # 應該返回空信號
        assert signals.empty or all(signals["ma_cross_signal"] == 0)

    def test_invalid_parameters(self, rsi_strategy, strategy_metadata):
        """測試無效參數"""
        # 無效的RSI參數（超買閾值小於超賣閾值）
        invalid_config = {
            "period": 14,
            "oversold_threshold": 70,
            "overbought_threshold": 30  # 錯誤：應該大於oversold
        }

        with pytest.raises(ValueError):
            RSIStrategy(
                instance_id=uuid4(),
                config=invalid_config,
                metadata=strategy_metadata
            )