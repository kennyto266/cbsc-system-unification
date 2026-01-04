"""
Tests for Portfolio Strategies
測試組合策略實現
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from uuid import uuid4

# Import strategies
from ..multi_factor_strategy import MultiFactorStrategy
from ..risk_parity_strategy import RiskParityStrategy
from .base import BasePortfolioStrategy
from ...enhanced_factory import StrategyMetadata, StrategyType


class TestPortfolioStrategies:
    """測試組合策略"""

    @pytest.fixture
    def sample_data(self):
        """創建測試用多資產OHLCV數據"""
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN"]

        data = {}
        for symbol in symbols:
            # 創建不同的價格走勢
            if symbol == "AAPL":
                trend = 0.001
            elif symbol == "GOOGL":
                trend = 0.0005
            elif symbol == "MSFT":
                trend = 0.0008
            else:  # AMZN
                trend = 0.0012

            prices = [100]
            np.random.seed(hash(symbol) % 2**32)  # 確保可重複性

            for i in range(1, len(dates)):
                change = np.random.normal(trend, 0.02)
                prices.append(prices[-1] * (1 + change))

            # 創建OHLCV數據
            df_data = []
            for i, (date, close) in enumerate(zip(dates, prices)):
                high = close * (1 + abs(np.random.normal(0, 0.01)))
                low = close * (1 - abs(np.random.normal(0, 0.01)))
                open_price = close * (1 + np.random.normal(0, 0.005))
                volume = np.random.randint(1000000, 10000000)

                df_data.append({
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume
                })

            df = pd.DataFrame(df_data, index=dates)
            data[symbol] = df

        return data

    @pytest.fixture
    def strategy_metadata(self):
        """創建策略元數據"""
        return StrategyMetadata(
            name="test_portfolio",
            strategy_type=StrategyType.PORTFOLIO,
            description="Test portfolio strategy",
            version="2.0.0",
            author="Test",
            parameters={}
        )

    @pytest.fixture
    def multi_factor_strategy(self, strategy_metadata):
        """多因子策略實例"""
        config = {
            "factors": [
                {
                    "name": "ma_crossover",
                    "weight": 0.4,
                    "config": {"fast_period": 10, "slow_period": 20}
                },
                {
                    "name": "rsi",
                    "weight": 0.3,
                    "config": {"period": 14, "oversold_threshold": 30, "overbought_threshold": 70}
                },
                {
                    "name": "adx",
                    "weight": 0.3,
                    "config": {"period": 14, "trend_threshold": 25}
                }
            ],
            "rebalance_frequency": "M",
            "min_positions": 2,
            "max_positions": 4,
            "signal_threshold": 0.5
        }
        return MultiFactorStrategy(
            instance_id=uuid4(),
            config=config,
            metadata=strategy_metadata
        )

    @pytest.fixture
    def risk_parity_strategy(self, strategy_metadata):
        """風險平價策略實例"""
        config = {
            "assets": [
                ("AAPL", {}),
                ("GOOGL", {}),
                ("MSFT", {}),
                ("AMZN", {})
            ],
            "rebalance_frequency": "M",
            "risk_target": 0.15,
            "lookback_period": 60,
            "max_weight": 0.4,
            "min_weight": 0.05,
            "risk_parity_method": "iterative"
        }
        return RiskParityStrategy(
            instance_id=uuid4(),
            config=config,
            metadata=strategy_metadata
        )

    # 測試多因子策略
    def test_multi_factor_initialization(self, multi_factor_strategy):
        """測試多因子策略初始化"""
        assert multi_factor_strategy.STRATEGY_NAME == "multi_factor"
        assert multi_factor_strategy.STRATEGY_TYPE == StrategyType.PORTFOLIO
        assert len(multi_factor_strategy.factor_strategies) == 3

    def test_multi_factor_factor_initialization(self, multi_factor_strategy):
        """測試因子初始化"""
        # 檢查因子是否正確創建
        factor_names = list(multi_factor_strategy.factor_strategies.keys())
        assert "ma_crossover" in factor_names
        assert "rsi" in factor_names
        assert "adx" in factor_names

        # 檢查權重正規化
        total_weight = sum(
            info['weight'] for info in multi_factor_strategy.factor_strategies.values()
        )
        assert np.isclose(total_weight, 1.0, atol=1e-6)

    def test_multi_factor_signal_generation(self, multi_factor_strategy, sample_data):
        """測試多因子信號生成"""
        signals = multi_factor_strategy.generate_signals(sample_data)

        # 檢查輸出結構
        assert isinstance(signals, pd.DataFrame)
        assert len(signals) > 0
        assert any('portfolio_signal' in col for col in signals.columns)

    def test_multi_factor_factor_combination(self, multi_factor_strategy, sample_data):
        """測試因子組合"""
        factor_signals = multi_factor_strategy.generate_factor_signals(sample_data)

        # 檢查每個因子都有信號
        assert len(factor_signals) == 3

        # 測試組合方法
        combined = multi_factor_strategy.combine_factors(factor_signals)
        assert isinstance(combined, pd.Series)
        assert len(combined) > 0

    def test_multi_factor_weight_calculation(self, multi_factor_strategy, sample_data):
        """測試權重計算"""
        weights = multi_factor_strategy.calculate_allocation_weights(sample_data)

        # 檢查權重有效性
        if weights:
            total_weight = sum(weights.values())
            assert np.isclose(total_weight, 1.0, atol=1e-6)
            assert all(0 <= w <= 1 for w in weights.values())

    def test_multi_factor_position_limits(self, multi_factor_strategy):
        """測試持倉限制"""
        # 測試超過最大持倉數
        weights = {
            f"asset_{i}": 0.2 for i in range(10)  # 10個資產，每個20%
        }
        adjusted = multi_factor_strategy._apply_position_limits(weights)

        # 應該只保留前4個資產
        assert len(adjusted) <= 4

        # 測試低於最小持倉數
        weights = {"single_asset": 1.0}
        multi_factor_strategy.min_positions = 3
        adjusted = multi_factor_strategy._apply_position_limits(weights)

        assert len(adjusted) >= 3

    # 測試風險平價策略
    def test_risk_parity_initialization(self, risk_parity_strategy):
        """測試風險平價策略初始化"""
        assert risk_parity_strategy.STRATEGY_NAME == "risk_parity"
        assert risk_parity_strategy.STRATEGY_TYPE == StrategyType.PORTFOLIO
        assert len(risk_parity_strategy.asset_symbols) == 4
        assert risk_parity_strategy.risk_target == 0.15

    def test_risk_parity_returns_calculation(self, risk_parity_strategy, sample_data):
        """測試收益率計算"""
        returns = risk_parity_strategy.calculate_returns(sample_data)

        assert isinstance(returns, pd.DataFrame)
        assert len(returns) > 0
        assert len(returns.columns) == 4  # 4個資產

    def test_risk_parity_volatility_estimates(self, risk_parity_strategy, sample_data):
        """測試波動率估計"""
        returns = risk_parity_strategy.calculate_returns(sample_data)
        volatilities = risk_parity_strategy.calculate_volatility_estimates(returns)

        assert isinstance(volatilities, pd.Series)
        assert len(volatilities) == 4
        assert all(v > 0 for v in volatilities.values)

    def test_risk_parity_inverse_volatility_weights(self, risk_parity_strategy):
        """測試反向波動率權重"""
        volatilities = pd.Series({
            "AAPL": 0.2,
            "GOOGL": 0.15,
            "MSFT": 0.25,
            "AMZN": 0.3
        })
        weights = risk_parity_strategy.calculate_inverse_volatility_weights(volatilities)

        assert isinstance(weights, pd.Series)
        assert np.isclose(weights.sum(), 1.0, atol=1e-6)
        # 高波動率資產應該有較低權重
        assert weights["AMZN"] < weights["GOOGL"]

    def test_risk_parity_weight_calculation(self, risk_parity_strategy, sample_data):
        """測試風險平價權重計算"""
        weights = risk_parity_strategy.calculate_risk_parity_weights(sample_data)

        # 檢查權重有效性
        if weights:
            total_weight = sum(weights.values())
            assert np.isclose(total_weight, 1.0, atol=1e-6)
            assert all(0 <= w <= 1 for w in weights.values())

    def test_risk_parity_iterative_method(self, risk_parity_strategy, sample_data):
        """測試迭代法風險平價"""
        returns = risk_parity_strategy.calculate_returns(sample_data)
        if len(returns) > 1:
            cov_matrix = returns.cov() * 252
            weights = risk_parity_strategy.calculate_risk_parity_weights_iterative(cov_matrix)

            assert len(weights) == len(returns.columns)
            assert np.isclose(weights.sum(), 1.0, atol=1e-6)
            assert all(w >= 0 for w in weights)

    def test_risk_parity_rebalance_condition(self, risk_parity_strategy, sample_data):
        """測試再平衡條件"""
        # 初始狀態應該需要再平衡
        assert risk_parity_strategy.should_rebalance(sample_data)

        # 設置再平衡日期
        risk_parity_strategy.last_rebalance_date = datetime.now() - timedelta(days=5)
        assert risk_parity_strategy.should_rebalance(sample_data)

    def test_risk_parity_position_limits(self, risk_parity_strategy):
        """測試風險平價持倉限制"""
        weights = np.array([0.5, 0.3, 0.15, 0.05])
        symbols = ["A", "B", "C", "D"]

        # 應該限制最大權重
        adjusted = risk_parity_strategy._apply_position_limits(weights, symbols)
        assert max(adjusted) <= risk_parity_strategy.max_weight

    # 測試組合策略執行
    def test_multi_factor_execution(self, multi_factor_strategy, sample_data):
        """測試多因子策略執行"""
        result = multi_factor_strategy.execute(sample_data)

        # 檢查執行結果結構
        assert "strategy_id" in result
        assert "strategy_name" in result
        assert "execution_time" in result
        assert "results" in result

        # 檢查結果內容
        assert "_portfolio" in result["results"]
        portfolio_result = result["results"]["_portfolio"]
        assert "metrics" in portfolio_result
        assert "status" in portfolio_result

    def test_risk_parity_execution(self, risk_parity_strategy, sample_data):
        """測試風險平價策略執行"""
        result = risk_parity_strategy.execute(sample_data)

        # 檢查執行結果結構
        assert "strategy_id" in result
        assert "strategy_name" in result
        assert "execution_time" in result
        assert "results" in result

        # 檢查結果內容
        assert "_portfolio" in result["results"]
        portfolio_result = result["results"]["_portfolio"]
        assert "metrics" in portfolio_result

    def test_portfolio_metrics(self, multi_factor_strategy, sample_data):
        """測試組合指標計算"""
        weights = {"AAPL": 0.4, "GOOGL": 0.3, "MSFT": 0.2, "AMZN": 0.1}
        metrics = multi_factor_strategy.calculate_portfolio_metrics(sample_data, weights)

        # 檢查指標
        assert "portfolio_return" in metrics
        assert "portfolio_volatility" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics

    def test_risk_contributions(self, risk_parity_strategy, sample_data):
        """測試風險貢獻計算"""
        weights = {"AAPL": 0.25, "GOOGL": 0.25, "MSFT": 0.25, "AMZN": 0.25}
        risk_contribs = risk_parity_strategy.calculate_risk_contributions(
            sample_data, weights
        )

        # 檢查風險貢獻
        if risk_contribs:
            assert len(risk_contribs) == 4
            total_contrib = sum(risk_contribs.values())
            assert np.isclose(total_contrib, 1.0, atol=1e-6)

    # 測試錯誤處理
    def test_multi_factor_invalid_factors(self, strategy_metadata):
        """測試無效因子配置"""
        config = {
            "factors": [],  # 空因子列表
            "rebalance_frequency": "M"
        }

        with pytest.raises(ValueError, match="No valid factors could be initialized"):
            MultiFactorStrategy(uuid4(), config, strategy_metadata)

    def test_portfolio_empty_data(self, multi_factor_strategy):
        """測試空數據處理"""
        empty_data = {}
        weights = multi_factor_strategy.calculate_allocation_weights(empty_data)
        assert weights == {}

    def test_portfolio_insufficient_data(self, risk_parity_strategy):
        """測試數據不足的情況"""
        # 創建不足的數據
        insufficient_data = {
            "TEST": pd.DataFrame({
                "close": [100, 101]  # 只有2個數據點
            })
        }
        weights = risk_parity_strategy.calculate_risk_parity_weights(insufficient_data)
        assert weights == {}

    def test_portfolio_constraints_validation(self, multi_factor_strategy):
        """測試組合約束驗證"""
        # 測試權重總和不為1
        invalid_weights = {"A": 0.3, "B": 0.3}  # 總和為0.6
        result = multi_factor_strategy.validate_portfolio_constraints(invalid_weights)
        assert result is False

        # 測試超過最大持倉數
        multi_factor_strategy.max_positions = 2
        too_many_positions = {f"Asset_{i}": 0.2 for i in range(5)}
        result = multi_factor_strategy.validate_portfolio_constraints(too_many_positions)
        assert result is False

    # 測試分析功能
    def test_multi_factor_analysis(self, multi_factor_strategy):
        """測試多因子分析"""
        analysis = multi_factor_strategy.get_factor_analysis()

        assert "factor_count" in analysis
        assert "factors" in analysis
        assert "combination_method" in analysis
        assert analysis["factor_count"] == 3

        factors = analysis["factors"]
        assert len(factors) == 3
        for factor in factors:
            assert "name" in factor
            assert "weight" in factor

    def test_risk_parity_metrics(self, risk_parity_strategy, sample_data):
        """測試風險平價指標"""
        # 先執行策略以設置當前權重
        result = risk_parity_strategy.execute(sample_data)

        if risk_parity_strategy.current_weights:
            metrics = risk_parity_strategy.get_risk_metrics(sample_data)

            if metrics:
                assert "portfolio_volatility" in metrics
                assert "risk_contributions" in metrics
                assert "diversification_ratio" in metrics