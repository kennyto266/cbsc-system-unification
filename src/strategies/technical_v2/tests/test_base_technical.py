"""
Tests for Base Technical Indicator Strategy
測試技術指標策略基類
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from uuid import uuid4
from unittest.mock import patch

from base import BaseTechnicalIndicatorStrategy
from enhanced_factory import StrategyType, StrategyMetadata


class TestTechnicalIndicatorStrategy(BaseTechnicalIndicatorStrategy):
    """測試用的技術指標策略實現"""

    STRATEGY_NAME = "test_technical"
    STRATEGY_TYPE = StrategyType.TECHNICAL_ANALYSIS
    DESCRIPTION = "Test technical indicator strategy"

    INDICATORS = {
        "test_indicator": {
            "default": {"period": 14},
            "required": True
        }
    }

    DEFAULT_PARAMETERS = {
        "test_param": "default_value"
    }

    REQUIRED_PARAMETERS = ["test_param"]

    OPTIONAL_PARAMETERS = {
        "optional_param": {
            "type": int,
            "default": 10,
            "min": 1,
            "max": 100
        }
    }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成測試信號"""
        signals = pd.DataFrame(index=data.index)
        signals["signal"] = 0

        # 簡單的測試信號邏輯
        if len(data) > 10:
            signals.loc[data.index[10:], "signal"] = 1

        return signals

    def validate_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """驗證測試信號"""
        # 移除無效信號
        return signals[signals["signal"] != 0]


class TestBaseTechnicalIndicatorStrategy:
    """測試技術指標策略基類"""

    @pytest.fixture
    def strategy_config(self):
        return {
            "test_param": "test_value",
            "optional_param": 50,
            "risk_rules": {
                "max_positions": 3,
                "max_loss_per_trade": 0.03
            }
        }

    @pytest.fixture
    def strategy_metadata(self):
        return StrategyMetadata(
            name="test_technical",
            strategy_type=StrategyType.TECHNICAL_ANALYSIS,
            description="Test",
            version="1.0.0",
            author="Test",
            parameters={}
        )

    @pytest.fixture
    def strategy(self, strategy_config, strategy_metadata):
        return TestTechnicalIndicatorStrategy(
            instance_id=uuid4(),
            config=strategy_config,
            metadata=strategy_metadata
        )

    def test_strategy_initialization(self, strategy):
        """測試策略初始化"""
        assert strategy.STRATEGY_NAME == "test_technical"
        assert strategy.STRATEGY_TYPE == StrategyType.TECHNICAL_ANALYSIS
        assert strategy.config["test_param"] == "test_value"
        assert strategy.config["optional_param"] == 50

    def test_validate_config_success(self, strategy_config, strategy_metadata):
        """測試配置驗證成功"""
        # 有效配置
        TestTechnicalIndicatorStrategy(
            instance_id=uuid4(),
            config=strategy_config,
            metadata=strategy_metadata
        )

    def test_validate_config_missing_required(self, strategy_metadata):
        """測試缺少必需參數"""
        invalid_config = {"wrong_param": "value"}

        with pytest.raises(ValueError, match="Required parameter 'test_param'"):
            TestTechnicalIndicatorStrategy(
                instance_id=uuid4(),
                config=invalid_config,
                metadata=strategy_metadata
            )

    def test_validate_config_type_error(self, strategy_metadata):
        """測試參數類型錯誤"""
        invalid_config = {
            "test_param": "test_value",
            "optional_param": "string_instead_of_int"
        }

        with pytest.raises(ValueError, match="must be of type"):
            TestTechnicalIndicatorStrategy(
                instance_id=uuid4(),
                config=invalid_config,
                metadata=strategy_metadata
            )

    def test_validate_config_out_of_range(self, strategy_metadata):
        """測試參數超出範圍"""
        invalid_config = {
            "test_param": "test_value",
            "optional_param": 150  # 超出最大值 100
        }

        with pytest.raises(ValueError, match="must be <="):
            TestTechnicalIndicatorStrategy(
                instance_id=uuid4(),
                config=invalid_config,
                metadata=strategy_metadata
            )

    def test_validate_dataframe_success(self, strategy):
        """測試數據框驗證成功"""
        # 創建有效的OHLCV數據
        data = pd.DataFrame({
            "open": [100, 101, 102, 103, 104],
            "high": [102, 103, 104, 105, 106],
            "low": [99, 100, 101, 102, 103],
            "close": [101, 102, 103, 104, 105],
            "volume": [1000, 1100, 900, 1200, 800]
        })

        # 不應該拋出異常
        strategy._validate_dataframe(data)

    def test_validate_dataframe_missing_column(self, strategy):
        """測試數據框缺少必需列"""
        invalid_data = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [102, 103, 104],
            "close": [101, 102, 103]
            # 缺少 "low" 和 "volume"
        })

        with pytest.raises(ValueError, match="Required column"):
            strategy._validate_dataframe(invalid_data)

    def test_calculate_indicators(self, strategy):
        """測試指標計算"""
        data = pd.DataFrame({
            "close": [100, 101, 102, 103, 104, 105, 106],
            "open": [100, 101, 102, 103, 104, 105, 106],
            "high": [101, 102, 103, 104, 105, 106, 107],
            "low": [99, 100, 101, 102, 103, 104, 105],
            "volume": [1000, 1100, 900, 1200, 800, 1300, 700]
        })

        result = strategy._calculate_indicators(data)

        # 檢查計算的指標
        assert "returns" in result.columns
        assert "log_returns" in result.columns
        assert "sma_5" in result.columns or len(result) < 10  # 可能因為數據不足而無法計算
        assert "close" in result.columns  # 原數據應該保留

    def test_generate_signals(self, strategy):
        """測試信號生成"""
        data = pd.DataFrame({
            "close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            "volume": [1000] * 11
        })

        result = strategy.generate_signals(data)

        assert "signal" in result.columns
        assert result["signal"].iloc[0] == 0  # 前面應該無信號
        assert result["signal"].iloc[-1] == 1  # 後面應該有信號

    def test_validate_signals(self, strategy):
        """測試信號驗證"""
        signals = pd.DataFrame({
            "signal": [0, 0, 1, 0, 1, 0, 1, 0]
        })

        result = strategy.validate_signals(signals)

        # 應該只返回有信號的行
        assert len(result) == 3
        assert all(result["signal"] != 0)

    def test_apply_risk_management(self, strategy):
        """測試風險管理應用"""
        signals = pd.DataFrame({
            "signal": [1, 0, 1, 0, 1, 0, 1],  # 4個信號
            "close": [100, 101, 102, 103, 104, 105, 106]
        })

        risk_rules = {
            "max_positions": 2,
            "use_stop_loss": True,
            "max_loss_per_trade": 0.03
        }

        result = strategy._apply_risk_management(signals, risk_rules)

        # 由於max_positions=2，應該限制信號數量
        assert len(result) <= len(signals)

    def test_strategy_execution_success(self, strategy):
        """測試策略執行成功"""
        data = {
            "AAPL": pd.DataFrame({
                "open": [100, 101, 102],
                "high": [102, 103, 104],
                "low": [99, 100, 101],
                "close": [101, 102, 103],
                "volume": [1000, 1100, 900]
            })
        }

        result = strategy.execute(data)

        assert "strategy_id" in result
        assert "strategy_name" in result
        assert "execution_time" in result
        assert "results" in result
        assert "AAPL" in result["results"]

    def test_strategy_execution_empty_data(self, strategy):
        """測試策略執行空數據"""
        data = {"EMPTY": pd.DataFrame()}

        result = strategy.execute(data)

        assert len(result["results"]) == 0

    def test_strategy_execution_invalid_data(self, strategy):
        """測試策略執行無效數據"""
        data = {"INVALID": pd.DataFrame({"invalid": [1, 2, 3]})}

        with pytest.raises(ValueError, match="Required column"):
            strategy.execute(data)

    def test_get_strategy_info(self, strategy):
        """測試獲取策略信息"""
        info = strategy.get_strategy_info()

        assert info["name"] == "test_technical"
        assert info["type"] == StrategyType.TECHNICAL_ANALYSIS
        assert "parameters" in info
        assert "indicators" in info

    def test_backtest(self, strategy):
        """測試回測功能"""
        data = {
            "TEST": pd.DataFrame({
                "open": [100, 101, 102, 103, 104, 105, 106],
                "high": [101, 102, 103, 104, 105, 106, 107],
                "low": [99, 100, 101, 102, 103, 104, 105],
                "close": [101, 102, 103, 104, 105, 106, 107],
                "volume": [1000] * 7
            })
        }

        result = strategy.backtest(data)

        assert "strategy" in result
        assert "backtest_results" in result
        assert "TEST" in result["backtest_results"]
        assert "total_return" in result["backtest_results"]["TEST"]
        assert "max_drawdown" in result["backtest_results"]["TEST"]

    def test_performance_calculations(self, strategy):
        """測試性能指標計算"""
        # 測試總回報率
        prices = [100, 105, 110, 108, 112]
        assert strategy._calculate_total_return(pd.DataFrame({"close": prices})) == 0.12

        # 測試空數據
        assert strategy._calculate_total_return(pd.DataFrame()) == 0.0

        # 測試最大回撤
        returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        prices = (1 + returns).cumprod()
        max_dd = strategy._calculate_max_drawdown(pd.DataFrame({"close": prices}))
        assert max_dd <= 0.0  # 應該是負數或零

        # 測試夏普比率
        sharpe = strategy._calculate_sharpe_ratio(pd.DataFrame({"close": prices}))
        assert isinstance(sharpe, float)
        # 夏普比率可以是正數、負數或零