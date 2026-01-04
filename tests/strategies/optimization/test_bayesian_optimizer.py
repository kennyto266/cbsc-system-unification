"""
Tests for Bayesian optimization engine.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from src.strategies.optimization.optimizers.bayesian import BayesianOptimizer
from src.strategies.optimization.optimizers.objective import ObjectiveFunction


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

    def test_empty_parameter_space_raises_error(self):
        """Test that empty parameter space raises ValueError."""
        optimizer = BayesianOptimizer(n_calls=20, n_random_starts=5, random_state=42)

        param_space = {}
        mock_objective = Mock()
        mock_objective.return_value = 0.85

        with pytest.raises(ValueError, match="Parameter space cannot be empty"):
            optimizer.optimize(param_space, mock_objective)

    def test_invalid_parameter_range_raises_error(self):
        """Test that invalid parameter range (min >= max) raises ValueError."""
        optimizer = BayesianOptimizer(n_calls=20, n_random_starts=5, random_state=42)

        param_space = {
            'param1': (10.0, 5.0),  # min > max, invalid
        }
        mock_objective = Mock()
        mock_objective.return_value = 0.85

        with pytest.raises(ValueError, match="has invalid range"):
            optimizer.optimize(param_space, mock_objective)

    def test_n_random_starts_greater_than_n_calls_raises_error(self):
        """Test that n_random_starts >= n_calls raises ValueError."""
        optimizer = BayesianOptimizer(n_calls=10, n_random_starts=15, random_state=42)

        param_space = {
            'param1': (0.0, 10.0),
        }
        mock_objective = Mock()
        mock_objective.return_value = 0.85

        with pytest.raises(ValueError, match="must be less than n_calls"):
            optimizer.optimize(param_space, mock_objective)

    def test_integration_with_objective_function(self):
        """Test integration with real ObjectiveFunction from Task 6."""
        # Create optimizer with small number of calls for fast test
        optimizer = BayesianOptimizer(n_calls=15, n_random_starts=5, random_state=42)

        # Create objective function
        objective_fn = ObjectiveFunction(alpha=0.5, beta=0.3, gamma=0.2)

        # Define parameter space (simple moving average crossover parameters)
        param_space = {
            'short_window': (5, 20),   # int range
            'long_window': (20, 50),   # int range
        }

        # Create wrapper that simulates backtest with given parameters
        def objective_wrapper(params: dict) -> float:
            """Simulate strategy backtest with given parameters."""
            short_window = params['short_window']
            long_window = params['long_window']

            # Generate synthetic returns based on parameter quality
            # Simulate that medium short_window and larger long_window work better
            np.random.seed(42)
            n_days = 252

            # Create synthetic returns with some signal
            signal_quality = 1.0 - abs(short_window - 10) / 20.0  # Prefer ~10
            trend_quality = long_window / 50.0  # Prefer longer windows

            # Generate returns with signal + noise
            returns = np.random.normal(
                loc=0.0005 * signal_quality * trend_quality,
                scale=0.02,
                size=n_days
            )

            returns_series = pd.Series(returns)

            # Calculate objective score
            score = objective_fn.calculate_score(returns_series)
            return score

        # Run optimization
        best_params, best_score = optimizer.optimize(param_space, objective_wrapper)

        # Verify return types
        assert isinstance(best_params, dict)
        assert isinstance(best_score, float)

        # Verify parameters are in valid ranges
        assert 5 <= best_params['short_window'] <= 20
        assert 20 <= best_params['long_window'] <= 50

        # Verify score is reasonable (not NaN or infinite)
        assert not np.isnan(best_score)
        assert not np.isinf(best_score)

        # Verify optimization history is available
        history = optimizer.get_optimization_history()
        assert 'scores' in history
        assert 'params' in history
        assert len(history['scores']) == optimizer.n_calls
