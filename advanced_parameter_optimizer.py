#!/usr/bin/env python3
"""
Advanced Parameter Optimizer
Supports multiple optimization algorithms for 500+ strategy combinations
"""

import asyncio
import json
import logging
import time
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from enum import Enum
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing as mp
import pickle
import random
from scipy import optimize
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')

# Import our framework components
from comprehensive_strategy_framework import (
    BaseStrategy, BacktestResult, StrategyType, MarketState
)
from strategy_registry import StrategyRegistry

logger = logging.getLogger(__name__)


class OptimizationAlgorithm(Enum):
    """Optimization algorithm types"""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    GENETIC_ALGORITHM = "genetic_algorithm"
    PARTICLE_SWARM = "particle_swarm"
    SIMULATED_ANNEALING = "simulated_annealing"
    DIFFERENTIAL_EVOLUTION = "differential_evolution"


class OptimizationObjective(Enum):
    """Optimization objectives"""
    MAXIMIZE_SHARPE = "maximize_sharpe"
    MAXIMIZE_RETURN = "maximize_return"
    MINIMIZE_DRAWDOWN = "minimize_drawdown"
    MAXIMIZE_CALMAR = "maximize_calmar"
    MULTI_OBJECTIVE = "multi_objective"


@dataclass
class ParameterSpace:
    """Parameter space definition"""
    name: str
    param_type: str  # 'continuous', 'discrete', 'categorical'
    bounds: Tuple[float, float]  # For continuous/discrete
    values: List[Any] = None  # For categorical
    step: Optional[float] = None  # For discrete
    log_scale: bool = False  # Use logarithmic scale


@dataclass
class OptimizationConfig:
    """Optimization configuration"""
    algorithm: OptimizationAlgorithm
    objective: OptimizationObjective
    max_iterations: int = 1000
    population_size: int = 50
    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    elite_size: int = 5
    convergence_threshold: float = 1e-6
    time_limit: Optional[float] = None  # seconds
    memory_limit: Optional[int] = None  # MB
    parallel_workers: int = None
    random_seed: Optional[int] = None
    early_stopping: bool = True
    patience: int = 50  # iterations without improvement


@dataclass
class OptimizationResult:
    """Optimization result"""
    best_parameters: Dict[str, Any]
    best_score: float
    optimization_history: List[Dict[str, Any]]
    convergence_info: Dict[str, Any]
    total_evaluations: int
    execution_time: float
    algorithm_used: str
    objective_function: str
    success: bool
    error_message: Optional[str] = None


class BaseOptimizer(ABC):
    """Abstract base class for optimizers"""

    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.optimization_history = []
        self.best_score = -np.inf if 'maximize' in config.objective.value else np.inf
        self.best_parameters = None
        self.evaluations = 0
        self.iterations_without_improvement = 0

    @abstractmethod
    def optimize(self, objective_function: Callable, parameter_spaces: List[ParameterSpace]) -> OptimizationResult:
        """Run optimization"""
        pass

    def _evaluate_parameters(self, params: Dict[str, Any], objective_function: Callable) -> float:
        """Evaluate a parameter set"""
        try:
            score = objective_function(params)
            self.evaluations += 1

            # Update best solution
            is_better = self._is_better_score(score)
            if is_better:
                self.best_score = score
                self.best_parameters = params.copy()
                self.iterations_without_improvement = 0
            else:
                self.iterations_without_improvement += 1

            # Record history
            self.optimization_history.append({
                'iteration': len(self.optimization_history),
                'parameters': params.copy(),
                'score': score,
                'best_score': self.best_score,
                'evaluations': self.evaluations
            })

            return score

        except Exception as e:
            self.logger.error(f"Error evaluating parameters: {e}")
            return -np.inf if 'maximize' in self.config.objective.value else np.inf

    def _is_better_score(self, new_score: float) -> bool:
        """Check if new score is better than current best"""
        if 'maximize' in self.config.objective.value:
            return new_score > self.best_score
        else:
            return new_score < self.best_score

    def _check_convergence(self) -> bool:
        """Check if optimization has converged"""
        if self.config.early_stopping and self.iterations_without_improvement >= self.config.patience:
            return True

        if len(self.optimization_history) > 10:
            recent_scores = [h['score'] for h in self.optimization_history[-10:]]
            score_std = np.std(recent_scores)
            if score_std < self.config.convergence_threshold:
                return True

        return False


class GridSearchOptimizer(BaseOptimizer):
    """Grid search optimizer"""

    def optimize(self, objective_function: Callable, parameter_spaces: List[ParameterSpace]) -> OptimizationResult:
        self.logger.info("Starting grid search optimization")
        start_time = time.time()

        # Generate grid points
        grid_points = self._generate_grid(parameter_spaces)
        total_combinations = len(grid_points)
        self.logger.info(f"Generated {total_combinations} parameter combinations")

        if total_combinations > self.config.max_iterations:
            self.logger.warning(f"Grid size ({total_combinations}) exceeds max_iterations ({self.config.max_iterations}), sampling randomly")
            np.random.seed(self.config.random_seed or 42)
            indices = np.random.choice(total_combinations, self.config.max_iterations, replace=False)
            grid_points = [grid_points[i] for i in indices]

        # Evaluate grid points
        for i, params in enumerate(grid_points):
            if i >= self.config.max_iterations:
                break

            if time.time() - start_time > (self.config.time_limit or float('inf')):
                self.logger.info("Time limit reached, stopping optimization")
                break

            self._evaluate_parameters(params, objective_function)

            if i % 100 == 0:
                self.logger.info(f"Evaluated {i+1}/{min(len(grid_points), self.config.max_iterations)} combinations")

        execution_time = time.time() - start_time

        return OptimizationResult(
            best_parameters=self.best_parameters,
            best_score=self.best_score,
            optimization_history=self.optimization_history,
            convergence_info={'method': 'exhaustive_search', 'total_combinations': total_combinations},
            total_evaluations=self.evaluations,
            execution_time=execution_time,
            algorithm_used=self.config.algorithm.value,
            objective_function=self.config.objective.value,
            success=self.best_parameters is not None
        )

    def _generate_grid(self, parameter_spaces: List[ParameterSpace]) -> List[Dict[str, Any]]:
        """Generate grid points from parameter spaces"""
        grid_points = [{}]

        for param_space in parameter_spaces:
            new_grid = []

            if param_space.param_type == 'continuous':
                # Generate 10 points for continuous parameters
                if param_space.log_scale:
                    points = np.logspace(np.log10(param_space.bounds[0]), np.log10(param_space.bounds[1]), 10)
                else:
                    points = np.linspace(param_space.bounds[0], param_space.bounds[1], 10)
            elif param_space.param_type == 'discrete':
                if param_space.step:
                    points = np.arange(param_space.bounds[0], param_space.bounds[1] + param_space.step, param_space.step)
                else:
                    points = np.linspace(param_space.bounds[0], param_space.bounds[1], 10)
            elif param_space.param_type == 'categorical':
                points = param_space.values
            else:
                points = [param_space.bounds[0]]  # Default

            for base_point in grid_points:
                for point in points:
                    new_point = base_point.copy()
                    new_point[param_space.name] = point
                    new_grid.append(new_point)

            grid_points = new_grid

        return grid_points


class RandomSearchOptimizer(BaseOptimizer):
    """Random search optimizer"""

    def optimize(self, objective_function: Callable, parameter_spaces: List[ParameterSpace]) -> OptimizationResult:
        self.logger.info("Starting random search optimization")
        start_time = time.time()

        if self.config.random_seed is not None:
            np.random.seed(self.config.random_seed)
            random.seed(self.config.random_seed)

        for iteration in range(self.config.max_iterations):
            if time.time() - start_time > (self.config.time_limit or float('inf')):
                self.logger.info("Time limit reached, stopping optimization")
                break

            if self._check_convergence():
                self.logger.info(f"Converged after {iteration} iterations")
                break

            # Generate random parameters
            params = self._generate_random_parameters(parameter_spaces)
            self._evaluate_parameters(params, objective_function)

            if iteration % 100 == 0:
                self.logger.info(f"Iteration {iteration}: Best score = {self.best_score:.4f}")

        execution_time = time.time() - start_time

        return OptimizationResult(
            best_parameters=self.best_parameters,
            best_score=self.best_score,
            optimization_history=self.optimization_history,
            convergence_info={'method': 'random_sampling', 'iterations': iteration + 1},
            total_evaluations=self.evaluations,
            execution_time=execution_time,
            algorithm_used=self.config.algorithm.value,
            objective_function=self.config.objective.value,
            success=self.best_parameters is not None
        )

    def _generate_random_parameters(self, parameter_spaces: List[ParameterSpace]) -> Dict[str, Any]:
        """Generate random parameters"""
        params = {}

        for param_space in parameter_spaces:
            if param_space.param_type == 'continuous':
                if param_space.log_scale:
                    log_min, log_max = np.log10(param_space.bounds[0]), np.log10(param_space.bounds[1])
                    value = 10 ** np.random.uniform(log_min, log_max)
                else:
                    value = np.random.uniform(param_space.bounds[0], param_space.bounds[1])
            elif param_space.param_type == 'discrete':
                if param_space.step:
                    values = np.arange(param_space.bounds[0], param_space.bounds[1] + param_space.step, param_space.step)
                else:
                    values = np.linspace(param_space.bounds[0], param_space.bounds[1], 50)
                value = np.random.choice(values)
            elif param_space.param_type == 'categorical':
                value = np.random.choice(param_space.values)
            else:
                value = param_space.bounds[0]

            params[param_space.name] = value

        return params


class BayesianOptimizer(BaseOptimizer):
    """Bayesian optimization using Gaussian Process surrogate model"""

    def __init__(self, config: OptimizationConfig):
        super().__init__(config)
        self.X = []  # Parameter points
        self.y = []  # Scores
        self.acquisition_function = 'expected_improvement'

    def optimize(self, objective_function: Callable, parameter_spaces: List[ParameterSpace]) -> OptimizationResult:
        self.logger.info("Starting Bayesian optimization")
        start_time = time.time()

        # Initial random sampling
        n_initial = min(20, self.config.max_iterations // 4)

        for iteration in range(self.config.max_iterations):
            if time.time() - start_time > (self.config.time_limit or float('inf')):
                break

            if self._check_convergence():
                self.logger.info(f"Converged after {iteration} iterations")
                break

            if iteration < n_initial:
                # Random initial points
                params = self._generate_random_parameters(parameter_spaces)
            else:
                # Bayesian optimization
                params = self._acquire_next_parameters(parameter_spaces)

            score = self._evaluate_parameters(params, objective_function)

            # Update surrogate model data
            self.X.append(list(params.values()))
            self.y.append(score)

            if iteration % 50 == 0:
                self.logger.info(f"Iteration {iteration}: Best score = {self.best_score:.4f}")

        execution_time = time.time() - start_time

        return OptimizationResult(
            best_parameters=self.best_parameters,
            best_score=self.best_score,
            optimization_history=self.optimization_history,
            convergence_info={'method': 'bayesian_optimization', 'surrogate_samples': len(self.X)},
            total_evaluations=self.evaluations,
            execution_time=execution_time,
            algorithm_used=self.config.algorithm.value,
            objective_function=self.config.objective.value,
            success=self.best_parameters is not None
        )

    def _generate_random_parameters(self, parameter_spaces: List[ParameterSpace]) -> Dict[str, Any]:
        """Generate random parameters (same as RandomSearchOptimizer)"""
        params = {}

        for param_space in parameter_spaces:
            if param_space.param_type == 'continuous':
                if param_space.log_scale:
                    log_min, log_max = np.log10(param_space.bounds[0]), np.log10(param_space.bounds[1])
                    value = 10 ** np.random.uniform(log_min, log_max)
                else:
                    value = np.random.uniform(param_space.bounds[0], param_space.bounds[1])
            elif param_space.param_type == 'discrete':
                if param_space.step:
                    values = np.arange(param_space.bounds[0], param_space.bounds[1] + param_space.step, param_space.step)
                else:
                    values = np.linspace(param_space.bounds[0], param_space.bounds[1], 50)
                value = np.random.choice(values)
            elif param_space.param_type == 'categorical':
                value = np.random.choice(param_space.values)
            else:
                value = param_space.bounds[0]

            params[param_space.name] = value

        return params

    def _acquire_next_parameters(self, parameter_spaces: List[ParameterSpace]) -> Dict[str, Any]:
        """Acquire next parameters using expected improvement"""
        if len(self.X) < 2:
            return self._generate_random_parameters(parameter_spaces)

        # Simple acquisition using random perturbation around best point
        best_params = self.best_parameters
        new_params = best_params.copy()

        for param_space in parameter_spaces:
            if np.random.random() < 0.3:  # 30% chance to modify each parameter
                if param_space.param_type == 'continuous':
                    # Add Gaussian noise
                    current_value = new_params[param_space.name]
                    noise_scale = (param_space.bounds[1] - param_space.bounds[0]) * 0.1
                    new_value = current_value + np.random.normal(0, noise_scale)
                    new_value = np.clip(new_value, param_space.bounds[0], param_space.bounds[1])
                    new_params[param_space.name] = new_value

        return new_params


class GeneticAlgorithmOptimizer(BaseOptimizer):
    """Genetic Algorithm optimizer"""

    def optimize(self, objective_function: Callable, parameter_spaces: List[ParameterSpace]) -> OptimizationResult:
        self.logger.info("Starting genetic algorithm optimization")
        start_time = time.time()

        if self.config.random_seed is not None:
            np.random.seed(self.config.random_seed)
            random.seed(self.config.random_seed)

        # Initialize population
        population = self._initialize_population(parameter_spaces)
        self.logger.info(f"Initialized population with {len(population)} individuals")

        for generation in range(self.config.max_iterations):
            if time.time() - start_time > (self.config.time_limit or float('inf')):
                break

            if self._check_convergence():
                self.logger.info(f"Converged after {generation} generations")
                break

            # Evaluate fitness
            fitness_scores = []
            for individual in population:
                score = self._evaluate_parameters(individual, objective_function)
                fitness_scores.append(score)

            # Select elite individuals
            elite_indices = np.argsort(fitness_scores)[-self.config.elite_size:]
            elite_population = [population[i] for i in elite_indices]

            # Create new generation
            new_population = elite_population.copy()

            while len(new_population) < self.config.population_size:
                # Selection
                parent1, parent2 = self._tournament_selection(population, fitness_scores)

                # Crossover
                child1, child2 = self._crossover(parent1, parent2, parameter_spaces)

                # Mutation
                if np.random.random() < self.config.mutation_rate:
                    child1 = self._mutate(child1, parameter_spaces)
                if np.random.random() < self.config.mutation_rate:
                    child2 = self._mutate(child2, parameter_spaces)

                new_population.extend([child1, child2])

            population = new_population[:self.config.population_size]

            if generation % 50 == 0:
                self.logger.info(f"Generation {generation}: Best score = {self.best_score:.4f}")

        execution_time = time.time() - start_time

        return OptimizationResult(
            best_parameters=self.best_parameters,
            best_score=self.best_score,
            optimization_history=self.optimization_history,
            convergence_info={'method': 'genetic_algorithm', 'generations': generation + 1},
            total_evaluations=self.evaluations,
            execution_time=execution_time,
            algorithm_used=self.config.algorithm.value,
            objective_function=self.config.objective.value,
            success=self.best_parameters is not None
        )

    def _initialize_population(self, parameter_spaces: List[ParameterSpace]) -> List[Dict[str, Any]]:
        """Initialize random population"""
        population = []
        for _ in range(self.config.population_size):
            individual = {}
            for param_space in parameter_spaces:
                if param_space.param_type == 'continuous':
                    value = np.random.uniform(param_space.bounds[0], param_space.bounds[1])
                elif param_space.param_type == 'discrete':
                    if param_space.step:
                        values = np.arange(param_space.bounds[0], param_space.bounds[1] + param_space.step, param_space.step)
                    else:
                        values = np.linspace(param_space.bounds[0], param_space.bounds[1], 20)
                    value = np.random.choice(values)
                elif param_space.param_type == 'categorical':
                    value = np.random.choice(param_space.values)
                else:
                    value = param_space.bounds[0]

                individual[param_space.name] = value

            population.append(individual)

        return population

    def _tournament_selection(self, population: List[Dict[str, Any]], fitness_scores: List[float]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Tournament selection"""
        tournament_size = 3

        def select_one():
            indices = np.random.choice(len(population), tournament_size, replace=False)
            tournament_fitness = [fitness_scores[i] for i in indices]
            winner_idx = indices[np.argmax(tournament_fitness)]
            return population[winner_idx]

        return select_one(), select_one()

    def _crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any], parameter_spaces: List[ParameterSpace]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Crossover operation"""
        child1 = {}
        child2 = {}

        for param_space in parameter_spaces:
            if np.random.random() < self.config.crossover_rate:
                # Swap parameters
                child1[param_space.name] = parent2[param_space.name]
                child2[param_space.name] = parent1[param_space.name]
            else:
                # Keep original parameters
                child1[param_space.name] = parent1[param_space.name]
                child2[param_space.name] = parent2[param_space.name]

        return child1, child2

    def _mutate(self, individual: Dict[str, Any], parameter_spaces: List[ParameterSpace]) -> Dict[str, Any]:
        """Mutation operation"""
        mutated = individual.copy()

        for param_space in parameter_spaces:
            if np.random.random() < 1.0 / len(parameter_spaces):  # Mutate one parameter on average
                if param_space.param_type == 'continuous':
                    # Gaussian mutation
                    current_value = individual[param_space.name]
                    mutation_scale = (param_space.bounds[1] - param_space.bounds[0]) * 0.1
                    new_value = current_value + np.random.normal(0, mutation_scale)
                    new_value = np.clip(new_value, param_space.bounds[0], param_space.bounds[1])
                    mutated[param_space.name] = new_value

                elif param_space.param_type == 'discrete':
                    # Random reassignment
                    if param_space.step:
                        values = np.arange(param_space.bounds[0], param_space.bounds[1] + param_space.step, param_space.step)
                    else:
                        values = np.linspace(param_space.bounds[0], param_space.bounds[1], 20)
                    mutated[param_space.name] = np.random.choice(values)

                elif param_space.param_type == 'categorical':
                    mutated[param_space.name] = np.random.choice(param_space.values)

        return mutated


class AdvancedParameterOptimizer:
    """Main optimizer class that orchestrates different optimization algorithms"""

    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or mp.cpu_count()
        self.logger = logging.getLogger(__name__)

        # Optimizer factory
        self.optimizer_factory = {
            OptimizationAlgorithm.GRID_SEARCH: GridSearchOptimizer,
            OptimizationAlgorithm.RANDOM_SEARCH: RandomSearchOptimizer,
            OptimizationAlgorithm.BAYESIAN_OPTIMIZATION: BayesianOptimizer,
            OptimizationAlgorithm.GENETIC_ALGORITHM: GeneticAlgorithmOptimizer,
        }

    def create_parameter_spaces(self, strategy_definition: Dict[str, Any]) -> List[ParameterSpace]:
        """Create parameter spaces from strategy definition"""
        parameter_spaces = []

        # RSI parameters
        if 'rsi_period' in strategy_definition:
            parameter_spaces.append(ParameterSpace(
                name='rsi_period',
                param_type='discrete',
                bounds=(5, 30),
                step=1
            ))

        if 'oversold' in strategy_definition:
            parameter_spaces.append(ParameterSpace(
                name='oversold',
                param_type='discrete',
                bounds=(10, 40),
                step=5
            ))

        if 'overbought' in strategy_definition:
            parameter_spaces.append(ParameterSpace(
                name='overbought',
                param_type='discrete',
                bounds=(60, 90),
                step=5
            ))

        # MACD parameters
        if 'fast_period' in strategy_definition:
            parameter_spaces.append(ParameterSpace(
                name='fast_period',
                param_type='discrete',
                bounds=(8, 20),
                step=2
            ))

        if 'slow_period' in strategy_definition:
            parameter_spaces.append(ParameterSpace(
                name='slow_period',
                param_type='discrete',
                bounds=(20, 40),
                step=2
            ))

        if 'signal_period' in strategy_definition:
            parameter_spaces.append(ParameterSpace(
                name='signal_period',
                param_type='discrete',
                bounds=(6, 18),
                step=2
            ))

        # Bollinger Bands parameters
        if 'period' in strategy_definition and 'bb_period' not in strategy_definition:
            parameter_spaces.append(ParameterSpace(
                name='period',
                param_type='discrete',
                bounds=(10, 30),
                step=2
            ))

        if 'bb_period' in strategy_definition:
            parameter_spaces.append(ParameterSpace(
                name='bb_period',
                param_type='discrete',
                bounds=(10, 30),
                step=2
            ))

        if 'std_dev' in strategy_definition:
            parameter_spaces.append(ParameterSpace(
                name='std_dev',
                param_type='continuous',
                bounds=(1.0, 3.0)
            ))

        return parameter_spaces

    def optimize_strategy(self,
                         strategy_class,
                         base_parameters: Dict[str, Any],
                         data: pd.DataFrame,
                         optimization_config: OptimizationConfig,
                         max_workers: int = None) -> OptimizationResult:
        """Optimize a single strategy"""
        self.logger.info(f"Optimizing strategy with {optimization_config.algorithm.value}")

        # Create parameter spaces
        parameter_spaces = self.create_parameter_spaces(base_parameters)

        # Create optimizer
        optimizer_class = self.optimizer_factory.get(optimization_config.algorithm)
        if not optimizer_class:
            raise ValueError(f"Unknown optimization algorithm: {optimization_config.algorithm}")

        optimizer = optimizer_class(optimization_config)

        # Define objective function
        def objective_function(params: Dict[str, Any]) -> float:
            try:
                # Create strategy instance with new parameters
                merged_params = {**base_parameters, **params}
                strategy = strategy_class(merged_params)

                # Run backtest (simplified version)
                signals = strategy.generate_signals(data)

                if not signals:
                    return -1.0  # Penalize strategies with no signals

                # Calculate performance metrics
                returns = []
                position = 0
                entry_price = None

                for signal in signals:
                    if signal.signal_type == "BUY" and position == 0:
                        position = 1
                        entry_price = signal.price
                    elif signal.signal_type == "SELL" and position == 1:
                        trade_return = (signal.price - entry_price) / entry_price
                        returns.append(trade_return)
                        position = 0
                        entry_price = None

                if not returns:
                    return -1.0

                # Calculate objective based on configuration
                returns_series = pd.Series(returns)

                if optimization_config.objective == OptimizationObjective.MAXIMIZE_SHARPE:
                    if returns_series.std() > 0:
                        sharpe = returns_series.mean() / returns_series.std() * np.sqrt(252)
                        return sharpe
                    else:
                        return 0.0

                elif optimization_config.objective == OptimizationObjective.MAXIMIZE_RETURN:
                    return returns_series.sum()

                elif optimization_config.objective == OptimizationObjective.MINIMIZE_DRAWDOWN:
                    cumulative = (1 + returns_series).cumprod()
                    running_max = cumulative.expanding().max()
                    drawdown = (cumulative - running_max) / running_max
                    max_dd = drawdown.min()
                    return -abs(max_dd)  # Negative because we want to minimize

                else:
                    # Default to Sharpe ratio
                    if returns_series.std() > 0:
                        return returns_series.mean() / returns_series.std() * np.sqrt(252)
                    else:
                        return 0.0

            except Exception as e:
                self.logger.error(f"Error in objective function: {e}")
                return -1.0

        # Run optimization
        result = optimizer.optimize(objective_function, parameter_spaces)

        self.logger.info(f"Optimization completed. Best score: {result.best_score:.4f}")
        return result

    async def optimize_multiple_strategies(self,
                                          strategy_configs: List[Tuple[type, Dict[str, Any]]],
                                          data: pd.DataFrame,
                                          optimization_config: OptimizationConfig) -> List[OptimizationResult]:
        """Optimize multiple strategies in parallel"""
        self.logger.info(f"Optimizing {len(strategy_configs)} strategies in parallel")

        results = []
        max_workers = max_workers or min(self.max_workers, len(strategy_configs))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all optimization tasks
            futures = []
            for strategy_class, base_params in strategy_configs:
                future = executor.submit(
                    self.optimize_strategy,
                    strategy_class,
                    base_params,
                    data,
                    optimization_config
                )
                futures.append(future)

            # Collect results
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=300)  # 5 minute timeout per strategy
                    results.append(result)
                    self.logger.info(f"Completed optimization {i+1}/{len(futures)}: {result.algorithm_used}")

                except Exception as e:
                    self.logger.error(f"Error in parallel optimization {i+1}: {e}")
                    # Create a failed result
                    failed_result = OptimizationResult(
                        best_parameters={},
                        best_score=-np.inf,
                        optimization_history=[],
                        convergence_info={},
                        total_evaluations=0,
                        execution_time=0,
                        algorithm_used=optimization_config.algorithm.value,
                        objective_function=optimization_config.objective.value,
                        success=False,
                        error_message=str(e)
                    )
                    results.append(failed_result)

        # Sort results by score
        results.sort(key=lambda r: r.best_score, reverse=True)

        self.logger.info(f"Completed all optimizations. Best score: {results[0].best_score:.4f}")
        return results


# Factory function
def create_optimizer(max_workers: int = None) -> AdvancedParameterOptimizer:
    """Factory function to create optimizer"""
    return AdvancedParameterOptimizer(max_workers)


# Main execution for testing
if __name__ == "__main__":
    async def main():
        print("Advanced Parameter Optimizer Test")
        print("=" * 50)

        # Import strategy classes for testing
        from comprehensive_strategy_framework import RSIMeanReversionStrategy

        # Generate test data
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', '2024-12-31', freq='D')
        dates = dates[dates.weekday < 5]  # Weekdays only

        base_price = 100.0
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = [base_price]

        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        data = pd.DataFrame({
            'open': prices,
            'high': [p * 1.02 for p in prices],
            'low': [p * 0.98 for p in prices],
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, len(dates))
        }, index=dates)

        print(f"Generated test data: {len(data)} records")

        # Test different optimization algorithms
        base_params = {
            'rsi_period': 14,
            'oversold': 25,
            'overbought': 75
        }

        algorithms = [
            OptimizationAlgorithm.RANDOM_SEARCH,
            OptimizationAlgorithm.BAYESIAN_OPTIMIZATION,
            OptimizationAlgorithm.GENETIC_ALGORITHM,
        ]

        for algorithm in algorithms:
            print(f"\nTesting {algorithm.value}:")

            config = OptimizationConfig(
                algorithm=algorithm,
                objective=OptimizationObjective.MAXIMIZE_SHARPE,
                max_iterations=100,
                population_size=30,
                random_seed=42
            )

            optimizer = create_optimizer()

            try:
                result = optimizer.optimize_strategy(
                    RSIMeanReversionStrategy,
                    base_params,
                    data,
                    config
                )

                print(f"  Best Score: {result.best_score:.4f}")
                print(f"  Best Parameters: {result.best_parameters}")
                print(f"  Evaluations: {result.total_evaluations}")
                print(f"  Execution Time: {result.execution_time:.2f}s")
                print(f"  Success: {result.success}")

            except Exception as e:
                print(f"  Error: {e}")

        print("\nParameter optimizer test completed!")

    asyncio.run(main())