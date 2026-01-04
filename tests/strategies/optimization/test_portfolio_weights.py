"""
Tests for portfolio weight allocation algorithms.

Tests for equal weight, risk parity, and Kelly criterion allocators.
"""

import numpy as np
import pandas as pd

from src.strategies.optimization.portfolio.weights import (
    EqualWeightAllocator,
    RiskParityAllocator,
    KellyAllocator,
)


class TestEqualWeightAllocator:
    """Test cases for EqualWeightAllocator."""

    def test_allocate_equal_weights_three_strategies(self):
        """Test equal weight allocation with three strategies."""
        allocator = EqualWeightAllocator()
        strategies = ['MA', 'RSI', 'ZScore']
        weights = allocator.allocate(strategies)

        assert len(weights) == 3
        assert all(np.isclose(weights[s], 1 / 3) for s in strategies)
        assert np.isclose(sum(weights.values()), 1.0)

    def test_allocate_equal_weights_single_strategy(self):
        """Test equal weight allocation with single strategy."""
        allocator = EqualWeightAllocator()
        strategies = ['MA']
        weights = allocator.allocate(strategies)

        assert len(weights) == 1
        assert weights['MA'] == 1.0

    def test_allocate_equal_weights_many_strategies(self):
        """Test equal weight allocation with many strategies."""
        allocator = EqualWeightAllocator()
        strategies = [f'Strategy{i}' for i in range(10)]
        weights = allocator.allocate(strategies)

        assert len(weights) == 10
        assert all(np.isclose(weights[s], 0.1) for s in strategies)
        assert np.isclose(sum(weights.values()), 1.0)

    def test_allocate_empty_list(self):
        """Test equal weight allocation with empty strategy list."""
        allocator = EqualWeightAllocator()
        weights = allocator.allocate([])

        assert weights == {}


class TestRiskParityAllocator:
    """Test cases for RiskParityAllocator."""

    def test_allocate_risk_parity_basic(self):
        """Test risk parity allocation with basic returns."""
        allocator = RiskParityAllocator(target_volatility=0.15)

        # Create returns with different volatilities
        np.random.seed(42)
        returns = pd.DataFrame({
            'LowVol': np.random.normal(0.001, 0.01, 100),  # 1% vol
            'HighVol': np.random.normal(0.001, 0.03, 100),  # 3% vol
        })

        strategies = ['LowVol', 'HighVol']
        weights = allocator.allocate(strategies, returns)

        # Low volatility should get higher weight (inverse vol weighting)
        assert weights['LowVol'] > weights['HighVol']
        assert np.isclose(sum(weights.values()), 1.0)

    def test_allocate_risk_parity_equal_volatility(self):
        """Test risk parity when all strategies have equal volatility."""
        allocator = RiskParityAllocator()

        np.random.seed(42)
        returns = pd.DataFrame({
            'Strategy1': np.random.normal(0.001, 0.02, 100),
            'Strategy2': np.random.normal(0.001, 0.02, 100),
            'Strategy3': np.random.normal(0.001, 0.02, 100),
        })

        strategies = ['Strategy1', 'Strategy2', 'Strategy3']
        weights = allocator.allocate(strategies, returns)

        # Equal volatility should result in approximately equal weights
        assert all(np.isclose(weights[s], 1 / 3, atol=0.05) for s in strategies)
        assert np.isclose(sum(weights.values()), 1.0)

    def test_allocate_risk_parity_empty_dataframe(self):
        """Test risk parity allocation with empty DataFrame."""
        allocator = RiskParityAllocator()
        strategies = ['MA', 'RSI']
        returns = pd.DataFrame()

        weights = allocator.allocate(strategies, returns)

        assert weights == {}

    def test_allocate_risk_parity_zero_volatility(self):
        """Test risk parity allocation handles zero volatility."""
        allocator = RiskParityAllocator()

        # Create returns where one strategy has zero volatility
        returns = pd.DataFrame({
            'ZeroVol': np.zeros(100),
            'NormalVol': np.random.normal(0.001, 0.02, 100),
        })

        strategies = ['ZeroVol', 'NormalVol']
        weights = allocator.allocate(strategies, returns)

        # Zero volatility strategy should be handled (replaced with nan)
        assert 'ZeroVol' in weights or weights['ZeroVol'] == 0
        assert np.isclose(sum(weights.values()), 1.0, atol=0.01)

    def test_risk_parity_initialization(self):
        """Test RiskParityAllocator initialization."""
        allocator = RiskParityAllocator(target_volatility=0.20)
        assert allocator.target_volatility == 0.20

        default_allocator = RiskParityAllocator()
        assert default_allocator.target_volatility == 0.15


class TestKellyAllocator:
    """Test cases for KellyAllocator."""

    def test_allocate_kelly_basic(self):
        """Test Kelly allocation with basic returns."""
        allocator = KellyAllocator(kelly_fraction=0.25)

        # Create returns with positive expected return
        # Use deterministic data to ensure positive returns
        returns = pd.DataFrame({
            'GoodStrategy': [0.002] * 50 + [0.001] * 50,  # Higher return
            'PoorStrategy': [0.0005] * 100,  # Lower return
        })

        strategies = ['GoodStrategy', 'PoorStrategy']
        weights = allocator.allocate(strategies, returns)

        # Good strategy should get higher weight
        assert weights['GoodStrategy'] > weights['PoorStrategy']
        assert np.isclose(sum(weights.values()), 1.0)

    def test_allocate_kelly_cap_at_one(self):
        """Test Kelly allocation caps individual weights at 1.0."""
        allocator = KellyAllocator(kelly_fraction=1.0)

        # High return, low variance should give Kelly > 1
        np.random.seed(42)
        returns = pd.DataFrame({
            'HighReturn': np.random.normal(0.05, 0.01, 100),  # Very high Sharpe
        })

        strategies = ['HighReturn']
        weights = allocator.allocate(strategies, returns)

        # Should be capped at 1.0
        assert weights['HighReturn'] <= 1.0

    def test_allocate_kelly_normalize_when_sum_exceeds_one(self):
        """Test Kelly allocation normalizes when total exceeds 1.0."""
        allocator = KellyAllocator(kelly_fraction=1.0)

        # Multiple strategies with good returns
        np.random.seed(42)
        returns = pd.DataFrame({
            'Strategy1': np.random.normal(0.03, 0.01, 100),
            'Strategy2': np.random.normal(0.03, 0.01, 100),
        })

        strategies = ['Strategy1', 'Strategy2']
        weights = allocator.allocate(strategies, returns)

        # Sum should be normalized to 1.0
        assert np.isclose(sum(weights.values()), 1.0)
        assert all(w <= 1.0 for w in weights.values())

    def test_allocate_kelly_zero_variance(self):
        """Test Kelly allocation handles zero variance."""
        allocator = KellyAllocator()

        # Strategy with zero variance
        returns = pd.DataFrame({
            'ZeroVar': np.ones(100) * 0.01,
            'Normal': np.random.normal(0.001, 0.02, 100),
        })

        strategies = ['ZeroVar', 'Normal']
        weights = allocator.allocate(strategies, returns)

        # Zero variance strategy should get 0 weight
        assert weights['ZeroVar'] == 0.0

    def test_allocate_kelly_empty_dataframe(self):
        """Test Kelly allocation with empty DataFrame."""
        allocator = KellyAllocator()
        strategies = ['MA', 'RSI']
        returns = pd.DataFrame()

        weights = allocator.allocate(strategies, returns)

        assert weights == {}

    def test_allocate_kelly_missing_strategy(self):
        """Test Kelly allocation when strategy is missing from returns."""
        allocator = KellyAllocator()

        returns = pd.DataFrame({
            'Strategy1': np.random.normal(0.001, 0.02, 100),
        })

        strategies = ['Strategy1', 'MissingStrategy']
        weights = allocator.allocate(strategies, returns)

        # Missing strategy should get 0 weight
        assert weights['MissingStrategy'] == 0.0
        assert 'Strategy1' in weights

    def test_kelly_initialization(self):
        """Test KellyAllocator initialization."""
        allocator = KellyAllocator(kelly_fraction=0.5)
        assert allocator.kelly_fraction == 0.5

        default_allocator = KellyAllocator()
        assert default_allocator.kelly_fraction == 0.25

    def test_allocate_kelly_negative_return(self):
        """Test Kelly allocation with negative expected return."""
        allocator = KellyAllocator(kelly_fraction=0.25)

        np.random.seed(42)
        returns = pd.DataFrame({
            'LosingStrategy': np.random.normal(-0.001, 0.02, 100),  # Negative return
        })

        strategies = ['LosingStrategy']
        weights = allocator.allocate(strategies, returns)

        # Negative return should result in zero or minimal weight
        assert weights['LosingStrategy'] >= 0.0
