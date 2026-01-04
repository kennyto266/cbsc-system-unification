# tests/strategies/optimization/test_objective.py
import pytest
import pandas as pd
import numpy as np
from src.strategies.optimization.optimizers.objective import ObjectiveFunction

def test_objective_function_initialization():
    """Test objective function can be initialized"""
    obj = ObjectiveFunction()
    assert obj is not None
    assert obj.alpha == 0.5  # Default SR weight
    assert obj.beta == 0.3   # Default MDD weight
    assert obj.gamma == 0.2  # Default Calmar weight

def test_objective_function_calculate_score():
    """Test calculating optimization score"""
    # Create sample returns
    np.random.seed(42)
    returns = pd.Series(np.random.randn(252) * 0.02)  # Daily returns

    obj = ObjectiveFunction()
    score = obj.calculate_score(returns)

    assert score is not None
    assert isinstance(score, (int, float))

def test_objective_function_custom_weights():
    """Test objective function with custom weights"""
    obj = ObjectiveFunction(alpha=0.7, beta=0.2, gamma=0.1)

    assert obj.alpha == 0.7
    assert obj.beta == 0.2
    assert obj.gamma == 0.1

def test_objective_function_calculate_metrics():
    """Test calculating all metrics"""
    np.random.seed(42)
    returns = pd.Series(np.random.randn(252) * 0.02)

    obj = ObjectiveFunction()
    metrics = obj.calculate_metrics(returns)

    assert metrics is not None
    assert 'sharpe_ratio' in metrics
    assert 'max_drawdown' in metrics
    assert 'calmar_ratio' in metrics
    assert 'composite_score' in metrics
    assert 'total_return' in metrics
    assert 'win_rate' in metrics

def test_objective_function_handles_edge_cases():
    """Test handling of NaN, Inf, and division by zero"""
    # Test with empty returns
    returns = pd.Series([])
    obj = ObjectiveFunction()
    score = obj.calculate_score(returns)

    # Should not crash
    assert isinstance(score, (int, float))

    # Test with constant returns (zero volatility)
    returns = pd.Series([0.01] * 100)
    score = obj.calculate_score(returns)

    # Should not crash
    assert isinstance(score, (int, float))
