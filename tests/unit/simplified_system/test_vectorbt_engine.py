#!/usr / bin / env python3
"""
VectorBT回測引擎單元測試
Unit tests for VectorBT Backtesting Engine
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

# Add simplified_system to path
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent.parent / "simplified_system")
)

try:
    from src.backtest.vectorbt_engine import (
        BacktestConfig,
        BacktestResult,
        VectorBTEngine,
    )

    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    VectorBTEngine = None
    BacktestConfig = None
    BacktestResult = None

pytestmark = pytest.mark.skipif(
    not VECTORBT_AVAILABLE,
    reason="VectorBT not available - install with: pip install vectorbt",
)


class TestBacktestConfig:
    """回測配置測試類"""

    def test_default_config(self):
        """測試默認配置"""
        config = BacktestConfig()

        assert config.initial_cash == 100000.0
        assert config.fees == 0.001
        assert config.slippage == 0.0005
        assert config.risk_free_rate == 0.03
        assert config.stop_loss is None
        assert config.take_profit is None
        assert config.max_position_size == 1.0

    def test_custom_config(self):
        """測試自定義配置"""
        config = BacktestConfig(
            initial_cash = 500000.0,
            fees = 0.002,
            slippage = 0.001,
            risk_free_rate = 0.02,
            stop_loss = 0.05,
            take_profit = 0.10,
            max_position_size = 0.8,
        )

        assert config.initial_cash == 500000.0
        assert config.fees == 0.002
        assert config.slippage == 0.001
        assert config.risk_free_rate == 0.02
        assert config.stop_loss == 0.05
        assert config.take_profit == 0.10
        assert config.max_position_size == 0.8


class TestBacktestResult:
    """回測結果測試類"""

    @pytest.fixture
    def sample_result_data(self):
        """創建測試用回測結果數據"""
        dates = pd.date_range("2024 - 01 - 01", periods = 10, freq="D")
        equity_curve = pd.Series(
            [
                100000,
                102000,
                101000,
                103000,
                105000,
                104000,
                106000,
                108000,
                107000,
                109000,
            ],
            index = dates,
        )
        returns = equity_curve.pct_change().dropna()

        return {
            "symbol": "0700.HK",
            "strategy_name": "RSI_MEAN_REVERSION",
            "parameters": {"period": 14, "oversold": 30, "overbought": 70},
            "total_return": 0.09,
            "sharpe_ratio": 1.25,
            "max_drawdown": -0.05,
            "win_rate": 0.6,
            "profit_factor": 1.5,
            "total_trades": 20,
            "calmar_ratio": 1.8,
            "sortino_ratio": 1.4,
            "annual_return": 0.12,
            "equity_curve": equity_curve,
            "returns": returns,
            "trades": pd.DataFrame(),  # 空的交易DataFrame
            "signals": pd.DataFrame(),  # 空的信號DataFrame
            "start_date": "2024 - 01 - 01",
            "end_date": "2024 - 01 - 10",
            "data_points": 10,
            "execution_time": 1.5,
        }

    def test_result_creation(self, sample_result_data):
        """測試回測結果創建"""
        result = BacktestResult(**sample_result_data)

        assert result.symbol == "0700.HK"
        assert result.strategy_name == "RSI_MEAN_REVERSION"
        assert result.total_return == 0.09
        assert result.sharpe_ratio == 1.25
        assert isinstance(result.equity_curve, pd.Series)
        assert isinstance(result.returns, pd.Series)

    def test_result_to_dict(self, sample_result_data):
        """測試回測結果轉字典"""
        result = BacktestResult(**sample_result_data)
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "symbol" in result_dict
        assert "strategy" in result_dict
        assert "parameters" in result_dict
        assert "performance" in result_dict

        # 檢查性能指標
        performance = result_dict["performance"]
        assert "total_return" in performance
        assert "sharpe_ratio" in performance
        assert isinstance(performance["total_return"], (int, float))
        assert isinstance(performance["sharpe_ratio"], (int, float))


@pytest.mark.vectorbt
class TestVectorBTEngine:
    """VectorBT引擎測試類"""

    @pytest.fixture
    def engine(self):
        """創建VectorBT引擎實例"""
        return VectorBTEngine()

    @pytest.fixture
    def sample_data(self):
        """創建測試用OHLCV數據"""
        dates = pd.date_range("2024 - 01 - 01", periods = 100, freq="D")
        np.random.seed(42)

        # 生成模擬股價數據
        initial_price = 100
        returns = np.random.normal(0.001, 0.02, 100)
        prices = [initial_price]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        data = pd.DataFrame(
            {
                "close": prices,
                "volume": np.random.randint(1000, 10000, 100),
                "open": np.array(prices) * np.random.uniform(0.99, 1.01, 100),
                "high": np.array(prices) * np.random.uniform(1.01, 1.05, 100),
                "low": np.array(prices) * np.random.uniform(0.95, 0.99, 100),
            },
            index = dates,
        )

        return data

    def test_engine_initialization(self, engine):
        """測試引擎初始化"""
        assert engine is not None

    def test_calculate_rsi_signals(self, engine, sample_data):
        """測試RSI信號計算"""
        signals = engine._calculate_rsi_signals(sample_data["close"], 14, 30, 70)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)
        assert signals.index.equals(sample_data.index)

        # 檢查信號值
        unique_signals = signals.unique()
        # 信號應該包含 - 1 (賣出), 0 (持有), 1 (買入)
        valid_signals = set([-1, 0, 1])
        assert all(
            signal in valid_signals for signal in unique_signals if not np.isnan(signal)
        )

    def test_calculate_macd_signals(self, engine, sample_data):
        """測試MACD信號計算"""
        signals = engine._calculate_macd_signals(sample_data["close"], 12, 26, 9)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)
        assert signals.index.equals(sample_data.index)

    def test_calculate_ma_signals(self, engine, sample_data):
        """測試移動平均信號計算"""
        signals = engine._calculate_ma_signals(sample_data["close"], 20, 50)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)
        assert signals.index.equals(sample_data.index)

    @patch("vectorbt.Portfolio.from_signals")
    def test_backtest_strategy_success(self, mock_portfolio, engine, sample_data):
        """測試策略回測成功"""
        # 模擬vectorbt Portfolio返回值
        mock_result = Mock()
        mock_result.total_return = 0.15
        mock_result.sharpe_ratio = 1.35
        mock_result.max_drawdown = -0.08
        mock_result.trades = pd.DataFrame()
        mock_result.positions = pd.DataFrame()
        mock_result.orders = pd.DataFrame()

        mock_portfolio.return_value = mock_result

        result = engine.backtest_strategy(
            sample_data,
            "RSI_MEAN_REVERSION",
            {"period": 14, "oversold": 30, "overbought": 70},
        )

        assert isinstance(result, BacktestResult)
        assert result.strategy_name == "RSI_MEAN_REVERSION"
        assert result.symbol == "UNKNOWN"  # 默認值

    def test_backtest_strategy_invalid_strategy(self, engine, sample_data):
        """測試無效策略回測"""
        with pytest.raises(ValueError):
            engine.backtest_strategy(sample_data, "INVALID_STRATEGY", {})

    def test_calculate_performance_metrics(self, engine, sample_data):
        """測試性能指標計算"""
        # 創建模擬回報和權益曲線
        returns = pd.Series(np.random.normal(0.001, 0.02, 100), index = sample_data.index)
        equity_curve = (1 + returns).cumprod() * 100000

        metrics = engine._calculate_performance_metrics(returns, equity_curve)

        assert isinstance(metrics, dict)
        assert "total_return" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
        assert "win_rate" in metrics

        # 檢查指標值類型
        assert isinstance(metrics["total_return"], (int, float))
        assert isinstance(metrics["sharpe_ratio"], (int, float))
        assert isinstance(metrics["max_drawdown"], (int, float))

    def test_calculate_performance_metrics_empty_data(self, engine):
        """測試空數據性能指標計算"""
        empty_returns = pd.Series([], dtype = float)
        empty_equity = pd.Series([], dtype = float)

        metrics = engine._calculate_performance_metrics(empty_returns, empty_equity)

        # 空數據應該返回默認值或拋出異常
        assert isinstance(metrics, dict)


@pytest.mark.sharpe
@pytest.mark.vectorbt
class TestVectorBTSharpeCalculation:
    """VectorBT Sharpe比率計算專用測試"""

    @pytest.fixture
    def engine(self):
        return VectorBTEngine()

    def test_sharpe_calculation_accuracy(self, engine, sharpe_test_data):
        """測試Sharpe計算精度"""
        returns, risk_free_rate = sharpe_test_data

        # 轉換為pandas Series
        returns_series = pd.Series(returns)

        # 使用VectorBT引擎計算
        sharpe_result = engine._calculate_sharpe_ratio(returns_series, risk_free_rate)

        # 手動計算Sharpe進行驗證
        excess_returns = returns - risk_free_rate
        if len(returns) > 1:
            expected_sharpe = np.mean(excess_returns) / np.std(excess_returns, ddof = 1)
            if np.std(excess_returns, ddof = 1) > 0:
                # 年化Sharpe (假設252個交易日)
                expected_sharpe *= np.sqrt(252)
            else:
                expected_sharpe = 0.0
        else:
            expected_sharpe = 0.0

        # 比較結果（允許小的誤差）
        if not np.isnan(sharpe_result) and not np.isnan(expected_sharpe):
            assert abs(sharpe_result - expected_sharpe) < 0.1

    def test_sharpe_calculation_edge_cases(self, engine):
        """測試Sharpe計算邊界情況"""
        # 零波動率回報序列
        constant_returns = pd.Series([0.01] * 10)
        sharpe_const = engine._calculate_sharpe_ratio(constant_returns, 0.03 / 252)

        # 零回報序列
        zero_returns = pd.Series([0.0] * 10)
        sharpe_zero = engine._calculate_sharpe_ratio(zero_returns, 0.03 / 252)

        # 極端回報序列
        extreme_returns = pd.Series([1.0, -1.0, 1.0, -1.0])
        sharpe_extreme = engine._calculate_sharpe_ratio(extreme_returns, 0.03 / 252)

        # 所有結果應該是有限數值
        for sharpe in [sharpe_const, sharpe_zero, sharpe_extreme]:
            if sharpe is not None:
                assert not np.isnan(sharpe)
                assert not np.isinf(sharpe)


@pytest.mark.performance
@pytest.mark.vectorbt
class TestVectorBTPerformance:
    """VectorBT性能測試"""

    @pytest.fixture
    def engine(self):
        return VectorBTEngine()

    @pytest.fixture
    def large_dataset(self):
        """創建大型測試數據集"""
        dates = pd.date_range("2020 - 01 - 01", periods = 1000, freq="D")
        np.random.seed(42)

        # 生成長期價格數據
        returns = np.random.normal(0.0005, 0.02, 1000)
        prices = [100]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        data = pd.DataFrame(
            {
                "close": prices,
                "volume": np.random.randint(1000, 50000, 1000),
                "open": np.array(prices) * np.random.uniform(0.99, 1.01, 1000),
                "high": np.array(prices) * np.random.uniform(1.01, 1.05, 1000),
                "low": np.array(prices) * np.random.uniform(0.95, 0.99, 1000),
            },
            index = dates,
        )

        return data

    @pytest.mark.benchmark
    def test_rsi_calculation_performance(self, engine, large_dataset, benchmark):
        """基準測試RSI計算性能"""

        def calculate_rsi_signals():
            return engine._calculate_rsi_signals(large_dataset["close"], 14, 30, 70)

        result = benchmark(calculate_rsi_signals)
        assert len(result) == len(large_dataset)

    @pytest.mark.benchmark
    def test_macd_calculation_performance(self, engine, large_dataset, benchmark):
        """基準測試MACD計算性能"""

        def calculate_macd_signals():
            return engine._calculate_macd_signals(large_dataset["close"], 12, 26, 9)

        result = benchmark(calculate_macd_signals)
        assert len(result) == len(large_dataset)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
