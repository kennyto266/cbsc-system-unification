"""
Bayesian optimization engine for strategy parameter optimization.

Uses scikit-optimize (skopt) for efficient global optimization using
Gaussian Process regression.
"""

from typing import Dict, Callable, Tuple, Any, List, Optional
import logging

try:
    from skopt import gp_minimize
    from skopt.space import Real, Integer
    from skopt.utils import use_named_args
    SKOPT_AVAILABLE = True
except ImportError:
    SKOPT_AVAILABLE = False
    gp_minimize = None
    Real = None
    Integer = None
    use_named_args = None


class BayesianOptimizer:
    """
    Bayesian optimization using Gaussian Process regression.

    Uses scikit-optimize's gp_minimize for efficient global optimization
    of black-box functions.
    """

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        n_calls: int = 50,
        n_random_starts: int = 10,
        random_state: Optional[int] = None
    ):
        """
        Initialize Bayesian optimizer.

        Args:
            n_calls: Number of optimization iterations
            n_random_starts: Number of random initial points before Bayesian optimization
            random_state: Random seed for reproducibility
        """
        if not SKOPT_AVAILABLE:
            raise ImportError(
                "scikit-optimize (skopt) is required for Bayesian optimization. "
                "Install it with: pip install scikit-optimize"
            )

        self.n_calls = n_calls
        self.n_random_starts = n_random_starts
        self.random_state = random_state
        self.optimization_result = None

    def optimize(
        self,
        param_space: Dict[str, Tuple[Any, Any]],
        objective_func: Callable[[Dict[str, Any]], float]
    ) -> Tuple[Dict[str, Any], float]:
        """
        Optimize parameters using Bayesian optimization.

        Args:
            param_space: Dictionary mapping parameter names to (min, max) tuples
            objective_func: Function to maximize (takes dict, returns score)

        Returns:
            Tuple of (best_parameters_dict, best_score_float)

        Raises:
            ValueError: If parameter space is empty or parameters are invalid
        """
        # Input validation
        if not param_space:
            raise ValueError("Parameter space cannot be empty")

        if self.n_calls <= 0:
            raise ValueError(f"n_calls must be positive, got {self.n_calls}")

        if self.n_random_starts <= 0:
            raise ValueError(f"n_random_starts must be positive, got {self.n_random_starts}")

        if self.n_random_starts >= self.n_calls:
            raise ValueError(
                f"n_random_starts ({self.n_random_starts}) must be less than n_calls ({self.n_calls})"
            )

        # Validate parameter ranges
        for param_name, (min_val, max_val) in param_space.items():
            if min_val >= max_val:
                raise ValueError(
                    f"Parameter '{param_name}' has invalid range: min ({min_val}) >= max ({max_val})"
                )

        # Build skopt dimension list
        dimensions = []
        param_names = []

        for param_name, (min_val, max_val) in param_space.items():
            param_names.append(param_name)

            # Detect integer vs float parameters
            if isinstance(min_val, int) and isinstance(max_val, int):
                dimensions.append(Integer(min_val, max_val, name=param_name))
            else:
                dimensions.append(Real(min_val, max_val, name=param_name))

        # Wrap objective function to use named arguments
        @use_named_args(dimensions=dimensions)
        def neg_objective(**kwargs):
            """Negate objective because skopt minimizes."""
            score = objective_func(kwargs)
            return -score  # Minimize negative = maximize original

        # Run Bayesian optimization
        self.logger.info(f"Starting Bayesian optimization with {self.n_calls} calls...")
        result = gp_minimize(
            func=neg_objective,
            dimensions=dimensions,
            n_calls=self.n_calls,
            n_initial_points=self.n_random_starts,
            random_state=self.random_state,
            verbose=False
        )

        self.optimization_result = result

        # Convert result to dict
        best_params = dict(zip(param_names, result.x))
        best_score = -result.fun  # Convert back from minimization

        self.logger.info(f"Optimization complete. Best score: {best_score:.4f}")

        return best_params, best_score

    def get_optimization_history(self) -> Dict[str, List]:
        """
        Get optimization history.

        Returns:
            Dict with 'scores' list and 'params' list
        """
        if self.optimization_result is None:
            return {'scores': [], 'params': []}

        # Convert scores back to maximization (negated from minimization)
        scores = [-s for s in self.optimization_result.func_vals]

        return {
            'scores': scores,
            'params': self.optimization_result.x_iters
        }
