"""
Advanced Parameter Optimizer for Backtesting
============================================

Sophisticated parameter optimization with multiple algorithms:
- Grid search optimization
- Random search optimization
- Bayesian optimization
- Genetic algorithms
- Particle swarm optimization
- Multi-objective optimization
- Cross-validation integration
- Hyperparameter tuning

Author: CBSC Quant Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import time
from scipy.optimize import minimize, differential_evolution, basinhopping
from scipy.stats import uniform, randint
import warnings

# Optimization libraries (optional dependencies)
try:
    from skopt import gp_minimize, forest_minimize, gbrt_minimize
    from skopt.space import Real, Integer, Categorical
    SKOPT_AVAILABLE = True
except ImportError:
    SKOPT_AVAILABLE = False

try:
    from hyperopt import fmin, tpe, hp, STATUS_OK, Trials
    HYPEROPT_AVAILABLE = True
except ImportError:
    HYPEROPT_AVAILABLE = False

try:
    from optuna import create_study, study, samplers, pruners
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

logger = logging.getLogger(__name__)


class OptimizationMethod(str, Enum):
    """Parameter optimization methods"""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    GENETIC_ALGORITHM = "genetic_algorithm"
    PARTICLE_SWARM = "particle_swarm"
    DIFFERENTIAL_EVOLUTION = "differential_evolution"
    SIMULATED_ANNEALING = "simulated_annealing"


class ObjectiveType(str, Enum):
    """Objective function types"""
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"
    MAXIMIZE_SHARPE = "maximize_sharpe"
    MINIMIZE_DRAWDOWN = "minimize_drawdown"
    MULTI_OBJECTIVE = "multi_objective"


@dataclass
class ParameterSpace:
    """Parameter space definition"""
    name: str
    param_type: str  # 'continuous', 'discrete', 'categorical'
    bounds: Tuple[Any, Any]  # (min, max) for continuous/discrete, list of values for categorical
    scale: str = "linear"  # 'linear', 'log', 'logit'

    def __post_init__(self):
        """Validate parameter space"""
        if self.param_type not in ['continuous', 'discrete', 'categorical']:
            raise ValueError(f"Invalid param_type: {self.param_type}")


@dataclass
class OptimizationConfig:
    """Parameter optimization configuration"""
    method: OptimizationMethod = OptimizationMethod.RANDOM_SEARCH
    objective_type: ObjectiveType = ObjectiveType.MAXIMIZE_SHARPE
    max_iterations: int = 100
    n_calls: int = 100  # For Bayesian optimization
    random_state: int = 42

    # Convergence criteria
    tolerance: float = 1e-6
    patience: int = 10  # Early stopping patience
    min_improvement: float = 1e-4

    # Cross-validation
    cv_folds: int = 5
    cv_scoring: str = "sharpe"
    shuffle_cv: bool = True

    # Parallel processing
    n_jobs: int = -1  # -1 for all CPUs
    verbose: bool = True
    progress_callback: Optional[Callable] = None

    # Constraints
    constraints: List[Callable] = field(default_factory=list)
    bounds: Dict[str, Tuple[float, float]] = field(default_factory=dict)


@dataclass
class OptimizationResult:
    """Parameter optimization result"""
    best_params: Dict[str, Any]
    best_score: float
    best_iteration: int
    optimization_history: List[Dict[str, Any]]
    cv_scores: Optional[List[float]] = None
    convergence_curve: Optional[List[float]] = None
    runtime: float = 0.0
    n_evaluations: int = 0


class ParameterOptimizer:
    """
    Advanced parameter optimizer with multiple algorithms
    """

    def __init__(self, config: OptimizationConfig):
        """
        Initialize parameter optimizer

        Args:
            config: Optimization configuration
        """
        self.config = config
        self.parameter_spaces: List[ParameterSpace] = []
        self.optimization_history: List[Dict[str, Any]] = []
        self.best_score: float = float('-inf')
        self.best_params: Optional[Dict[str, Any]] = None

        logger.info(f"Parameter optimizer initialized with {config.method} method")

    def add_parameter(self, param_space: ParameterSpace) -> None:
        """
        Add parameter to optimization space

        Args:
            param_space: Parameter space definition
        """
        self.parameter_spaces.append(param_space)

    def optimize(
        self,
        objective_func: Callable,
        data: Optional[Any] = None,
        bounds: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> OptimizationResult:
        """
        Run parameter optimization

        Args:
            objective_func: Objective function to optimize
            data: Data to pass to objective function
            bounds: Parameter bounds (overrides ParameterSpace bounds)

        Returns:
            OptimizationResult with best parameters and score
        """
        try:
            start_time = time.time()

            # Update bounds if provided
            if bounds:
                self._update_bounds(bounds)

            # Run optimization based on method
            if self.config.method == OptimizationMethod.GRID_SEARCH:
                result = self._grid_search(objective_func, data)
            elif self.config.method == OptimizationMethod.RANDOM_SEARCH:
                result = self._random_search(objective_func, data)
            elif self.config.method == OptimizationMethod.BAYESIAN_OPTIMIZATION:
                result = self._bayesian_optimization(objective_func, data)
            elif self.config.method == OptimizationMethod.GENETIC_ALGORITHM:
                result = self._genetic_algorithm(objective_func, data)
            elif self.config.method == OptimizationMethod.PARTICLE_SWARM:
                result = self._particle_swarm(objective_func, data)
            elif self.config.method == OptimizationMethod.DIFFERENTIAL_EVOLUTION:
                result = self._differential_evolution(objective_func, data)
            elif self.config.method == OptimizationMethod.SIMULATED_ANNEALING:
                result = self._simulated_annealing(objective_func, data)
            else:
                raise ValueError(f"Unknown optimization method: {self.config.method}")

            # Add runtime
            result.runtime = time.time() - start_time

            logger.info(f"Optimization completed. Best score: {result.best_score:.6f}")
            return result

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise

    def _update_bounds(self, bounds: Dict[str, Tuple[float, float]]) -> None:
        """Update parameter bounds"""
        for param_space in self.parameter_spaces:
            if param_space.name in bounds:
                param_space.bounds = bounds[param_space.name]

    def _grid_search(self, objective_func: Callable, data: Any) -> OptimizationResult:
        """Grid search optimization"""

        # Generate grid
        grid_points = self._generate_grid()

        best_score = float('-inf')
        best_params = None
        all_scores = []

        for i, params in enumerate(grid_points):
            # Evaluate objective
            score = objective_func(params, data)

            # Update best
            if score > best_score:
                best_score = score
                best_params = params.copy()

            all_scores.append(score)
            self.optimization_history.append({
                'iteration': i,
                'params': params.copy(),
                'score': score
            })

            # Progress callback
            if self.config.progress_callback:
                self.config.progress_callback(i, score)

            # Check convergence
            if i > self.config.patience and self._check_convergence(all_scores[-self.config.patience:]):
                break

        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            best_iteration=len(grid_points),
            optimization_history=self.optimization_history,
            convergence_curve=all_scores,
            n_evaluations=len(grid_points)
        )

    def _random_search(self, objective_func: Callable, data: Any) -> OptimizationResult:
        """Random search optimization"""

        best_score = float('-inf')
        best_params = None
        all_scores = []

        for i in range(self.config.max_iterations):
            # Random parameter sample
            params = self._sample_parameters()

            # Evaluate objective
            score = objective_func(params, data)

            # Update best
            if score > best_score:
                best_score = score
                best_params = params.copy()

            all_scores.append(score)
            self.optimization_history.append({
                'iteration': i,
                'params': params.copy(),
                'score': score
            })

            # Progress callback
            if self.config.progress_callback:
                self.config.progress_callback(i, score)

            # Check convergence
            if i > self.config.patience and self._check_convergence(all_scores[-self.config.patience:]):
                break

        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            best_iteration=i,
            optimization_history=self.optimization_history,
            convergence_curve=all_scores,
            n_evaluations=i + 1
        )

    def _bayesian_optimization(self, objective_func: Callable, data: Any) -> OptimizationResult:
        """Bayesian optimization using scikit-optimize"""

        if not SKOPT_AVAILABLE:
            logger.warning("scikit-optimize not available, falling back to random search")
            return self._random_search(objective_func, data)

        # Define search space
        dimensions = []
        for param_space in self.parameter_spaces:
            if param_space.param_type == 'continuous':
                dimensions.append(Real(param_space.bounds[0], param_space.bounds[1], name=param_space.name))
            elif param_space.param_type == 'discrete':
                dimensions.append(Integer(int(param_space.bounds[0]), int(param_space.bounds[1]), name=param_space.name))
            elif param_space.param_type == 'categorical':
                dimensions.append(Categorical(param_space.bounds, name=param_space.name))

        # Define objective for scikit-optimize
        def skopt_objective(params):
            param_dict = {dim.name: val for dim, val in zip(dimensions, params)}
            score = objective_func(param_dict, data)
            return -score  # skopt minimizes

        # Run optimization
        result = gp_minimize(
            func=skopt_objective,
            dimensions=dimensions,
            n_calls=self.config.n_calls,
            random_state=self.config.random_state,
            verbose=self.config.verbose
        )

        # Convert result
        best_params = {dim.name: val for dim, val in zip(dimensions, result.x)}
        optimization_history = []

        for i in range(len(result.func_vals)):
            params = {dim.name: val for dim, val in zip(dimensions, result.x_iters[i])}
            optimization_history.append({
                'iteration': i,
                'params': params,
                'score': -result.func_vals[i]
            })

        return OptimizationResult(
            best_params=best_params,
            best_score=-result.fun,
            best_iteration=len(result.x),
            optimization_history=optimization_history,
            convergence_curve=[-val for val in result.func_vals],
            n_evaluations=len(result.x)
        )

    def _genetic_algorithm(self, objective_func: Callable, data: Any) -> OptimizationResult:
        """Genetic algorithm optimization"""

        # Simplified genetic algorithm implementation
        population_size = 50
        mutation_rate = 0.1
        crossover_rate = 0.7
        n_generations = self.config.max_iterations // 10

        # Initialize population
        population = [self._sample_parameters() for _ in range(population_size)]

        best_score = float('-inf')
        best_params = None
        all_scores = []

        for generation in range(n_generations):
            # Evaluate fitness
            scores = []
            for params in population:
                score = objective_func(params, data)
                scores.append(score)

                if score > best_score:
                    best_score = score
                    best_params = params.copy()

            all_scores.extend(scores)

            # Selection (tournament)
            selected = self._tournament_selection(population, scores)

            # Crossover and mutation
            new_population = []
            for i in range(0, len(selected), 2):
                if i + 1 < len(selected):
                    parent1, parent2 = selected[i], selected[i + 1]

                    # Crossover
                    if np.random.random() < crossover_rate:
                        child1, child2 = self._crossover(parent1, parent2)
                    else:
                        child1, child2 = parent1.copy(), parent2.copy()

                    # Mutation
                    if np.random.random() < mutation_rate:
                        child1 = self._mutate(child1)
                    if np.random.random() < mutation_rate:
                        child2 = self._mutate(child2)

                    new_population.extend([child1, child2])

            population = new_population

        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            best_iteration=n_generations,
            optimization_history=self.optimization_history,
            convergence_curve=all_scores,
            n_evaluations=n_generations * population_size
        )

    def _particle_swarm(self, objective_func: Callable, data: Any) -> OptimizationResult:
        """Particle swarm optimization"""

        n_particles = 30
        n_dimensions = len(self.parameter_spaces)
        max_iterations = self.config.max_iterations

        # Initialize particles
        particles = np.array([self._sample_parameters_array() for _ in range(n_particles)])
        velocities = np.random.randn(n_particles, n_dimensions) * 0.1

        # Initialize best positions
        personal_best = particles.copy()
        personal_best_scores = np.array([objective_func(self._array_to_dict(p), data) for p in particles])

        global_best_idx = np.argmax(personal_best_scores)
        global_best = personal_best[global_best_idx].copy()
        global_best_score = personal_best_scores[global_best_idx]

        all_scores = []

        for iteration in range(max_iterations):
            for i, particle in enumerate(particles):
                # Update velocity
                w = 0.7  # Inertia weight
                c1 = 1.5  # Cognitive parameter
                c2 = 1.5  # Social parameter

                r1, r2 = np.random.random(2)
                velocities[i] = (w * velocities[i] +
                               c1 * r1 * (personal_best[i] - particle) +
                               c2 * r2 * (global_best - particle))

                # Update position
                particles[i] += velocities[i]

                # Apply bounds
                particles[i] = self._apply_bounds_array(particles[i])

                # Evaluate fitness
                score = objective_func(self._array_to_dict(particles[i]), data)

                # Update personal best
                if score > personal_best_scores[i]:
                    personal_best[i] = particles[i].copy()
                    personal_best_scores[i] = score

                    # Update global best
                    if score > global_best_score:
                        global_best = particles[i].copy()
                        global_best_score = score

                all_scores.append(score)

        return OptimizationResult(
            best_params=self._array_to_dict(global_best),
            best_score=global_best_score,
            best_iteration=max_iterations,
            optimization_history=self.optimization_history,
            convergence_curve=all_scores,
            n_evaluations=max_iterations * n_particles
        )

    def _differential_evolution(self, objective_func: Callable, data: Any) -> OptimizationResult:
        """Differential evolution optimization using scipy"""

        # Define bounds
        bounds = []
        for param_space in self.parameter_spaces:
            bounds.append(param_space.bounds)

        # Define objective for scipy
        def de_objective(x):
            param_dict = self._array_to_dict(x)
            score = objective_func(param_dict, data)
            return -score  # scipy minimizes

        # Run differential evolution
        result = differential_evolution(
            func=de_objective,
            bounds=bounds,
            maxiter=self.config.max_iterations,
            popsize=15,
            tol=self.config.tolerance,
            updating='deferred',
            workers=1,  # Disable multiprocessing to avoid pickle issues
            seed=self.config.random_state
        )

        return OptimizationResult(
            best_params=self._array_to_dict(result.x),
            best_score=-result.fun,
            best_iteration=result.nit,
            optimization_history=self.optimization_history,
            convergence_curve=[],  # fun_vals not available in all scipy versions
            n_evaluations=result.nfev
        )

    def _simulated_annealing(self, objective_func: Callable, data: Any) -> OptimizationResult:
        """Simulated annealing optimization"""

        def sa_objective(params_array):
            param_dict = self._array_to_dict(params_array)
            return -objective_func(param_dict, data)  # Minimize negative score

        # Initial point
        x0 = self._sample_parameters_array()
        bounds = [param_space.bounds for param_space in self.parameter_spaces]

        # Run simulated annealing
        result = basinhopping(
            func=sa_objective,
            x0=x0,
            niter=self.config.max_iterations,
            T=1.0,
            stepsize=0.5,
            minimizer_kwargs={'method': 'L-BFGS-B', 'bounds': bounds},
            disp=self.config.verbose,
            seed=self.config.random_state
        )

        return OptimizationResult(
            best_params=self._array_to_dict(result.x),
            best_score=-result.fun,
            best_iteration=result.nit,
            optimization_history=self.optimization_history,
            convergence_curve=[],  # fun_vals not available in all scipy versions
            n_evaluations=result.nfev
        )

    def _generate_grid(self) -> List[Dict[str, Any]]:
        """Generate grid of parameter combinations"""
        grids = []

        for param_space in self.parameter_spaces:
            if param_space.param_type == 'continuous':
                # Use 10 points for continuous
                points = np.linspace(param_space.bounds[0], param_space.bounds[1], 10)
            elif param_space.param_type == 'discrete':
                points = list(range(int(param_space.bounds[0]), int(param_space.bounds[1]) + 1))
            else:  # categorical
                points = param_space.bounds

            grids.append(points)

        # Create all combinations
        from itertools import product
        combinations = list(product(*grids))

        # Convert to parameter dictionaries
        param_combinations = []
        for combo in combinations:
            param_dict = {}
            for i, param_space in enumerate(self.parameter_spaces):
                param_dict[param_space.name] = combo[i]
            param_combinations.append(param_dict)

        return param_combinations

    def _sample_parameters(self) -> Dict[str, Any]:
        """Sample random parameters"""
        params = {}

        for param_space in self.parameter_spaces:
            if param_space.param_type == 'continuous':
                params[param_space.name] = np.random.uniform(param_space.bounds[0], param_space.bounds[1])
            elif param_space.param_type == 'discrete':
                params[param_space.name] = np.random.randint(param_space.bounds[0], param_space.bounds[1] + 1)
            else:  # categorical
                params[param_space.name] = np.random.choice(param_space.bounds)

        return params

    def _sample_parameters_array(self) -> np.ndarray:
        """Sample parameters as array"""
        params = []
        for param_space in self.parameter_spaces:
            if param_space.param_type == 'continuous':
                params.append(np.random.uniform(param_space.bounds[0], param_space.bounds[1]))
            elif param_space.param_type == 'discrete':
                params.append(np.random.randint(param_space.bounds[0], param_space.bounds[1] + 1))
            else:  # categorical
                params.append(np.random.choice(range(len(param_space.bounds))))
        return np.array(params)

    def _array_to_dict(self, params_array: np.ndarray) -> Dict[str, Any]:
        """Convert parameter array to dictionary"""
        params = {}
        for i, param_space in enumerate(self.parameter_spaces):
            if param_space.param_type == 'continuous' or param_space.param_type == 'discrete':
                params[param_space.name] = params_array[i]
            else:  # categorical
                params[param_space.name] = param_space.bounds[int(params_array[i])]
        return params

    def _apply_bounds_array(self, params_array: np.ndarray) -> np.ndarray:
        """Apply bounds to parameter array"""
        bounded_params = params_array.copy()

        for i, param_space in enumerate(self.parameter_spaces):
            if param_space.param_type != 'categorical':
                bounded_params[i] = np.clip(
                    bounded_params[i],
                    param_space.bounds[0],
                    param_space.bounds[1]
                )

        return bounded_params

    def _tournament_selection(self, population: List[Dict[str, Any]], scores: List[float]) -> List[Dict[str, Any]]:
        """Tournament selection for genetic algorithm"""
        tournament_size = 3
        selected = []

        for _ in range(len(population)):
            # Random tournament
            candidates = np.random.choice(len(population), tournament_size, replace=False)
            winner_idx = candidates[np.argmax([scores[i] for i in candidates])]
            selected.append(population[winner_idx].copy())

        return selected

    def _crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Crossover two parents"""
        child1, child2 = parent1.copy(), parent2.copy()

        # Single-point crossover
        crossover_point = np.random.randint(1, len(self.parameter_spaces))
        param_names = [ps.name for ps in self.parameter_spaces]

        for i in range(crossover_point, len(param_names)):
            param_name = param_names[i]
            child1[param_name], child2[param_name] = child2[param_name], child1[param_name]

        return child1, child2

    def _mutate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mutate parameters"""
        mutated = params.copy()

        for param_space in self.parameter_spaces:
            if np.random.random() < 0.1:  # 10% mutation rate per parameter
                if param_space.param_type == 'continuous':
                    mutated[param_space.name] = np.random.uniform(param_space.bounds[0], param_space.bounds[1])
                elif param_space.param_type == 'discrete':
                    mutated[param_space.name] = np.random.randint(param_space.bounds[0], param_space.bounds[1] + 1)
                else:  # categorical
                    mutated[param_space.name] = np.random.choice(param_space.bounds)

        return mutated

    def _check_convergence(self, recent_scores: List[float]) -> bool:
        """Check if optimization has converged"""
        if len(recent_scores) < self.config.patience:
            return False

        # Check if improvement is less than threshold
        improvement = max(recent_scores) - min(recent_scores)
        return improvement < self.config.min_improvement


# Utility functions
def create_optimization_config(
    method: OptimizationMethod = OptimizationMethod.RANDOM_SEARCH,
    objective_type: ObjectiveType = ObjectiveType.MAXIMIZE_SHARPE,
    **kwargs
) -> OptimizationConfig:
    """Create optimization configuration"""
    config = {
        'method': method,
        'objective_type': objective_type,
        'max_iterations': 100,
        'n_calls': 100,
        'random_state': 42,
        'n_jobs': -1
    }

    config.update(kwargs)
    return OptimizationConfig(**config)


def create_parameter_space(
    name: str,
    param_type: str,
    bounds: Tuple[Any, Any],
    scale: str = "linear"
) -> ParameterSpace:
    """Create parameter space"""
    return ParameterSpace(
        name=name,
        param_type=param_type,
        bounds=bounds,
        scale=scale
)


__all__ = [
    'ParameterOptimizer',
    'OptimizationConfig',
    'ParameterSpace',
    'OptimizationResult',
    'OptimizationMethod',
    'ObjectiveType',
    'create_optimization_config',
    'create_parameter_space'
]