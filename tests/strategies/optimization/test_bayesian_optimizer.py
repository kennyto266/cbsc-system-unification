"""
Tests for Bayesian optimization engine.
"""

import pytest
from unittest.mock import Mock, patch

from src.strategies.optimization.optimizers.bayesian import BayesianOptimizer


class TestBayesianOptimizer:
    """Test Bayesian optimizer implementation."""

    def test_bayesian_optimizer_initialization(self):
        """Verify optimizer has n_calls attribute and proper initialization."""
        optimizer = BayesianOptimizer(n_calls=50, n_random_starts=10, random_state=42)

        assert hasattr(optimizer, 'n_calls')
        assert optimizer.n_calls == 50
        assert optimizer.n_random_starts == 10
        assert optimizer.random_state == 42

    def test_bayesian_optimize_simple_parameters(self):
        """Test optimization with mock objective function."""
        # Create optimizer
        optimizer = BayesianOptimizer(n_calls=20, n_random_starts=5, random_state=42)

        # Define parameter space
        param_space = {
            'param1': (0.0, 10.0),  # float range
            'param2': (1, 100),     # int range
        }

        # Create mock objective function
        mock_objective = Mock()
        mock_objective.return_value = 0.85

        # Run optimization
        best_params, best_score = optimizer.optimize(param_space, mock_objective)

        # Verify objective was called
        assert mock_objective.called

        # Verify return types
        assert isinstance(best_params, dict)
        assert isinstance(best_score, float)

        # Verify parameters are in valid ranges
        assert 0.0 <= best_params['param1'] <= 10.0
        assert 1 <= best_params['param2'] <= 100

        # Verify score matches objective return value
        assert best_score == 0.85
