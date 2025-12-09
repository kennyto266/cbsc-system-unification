"""Strategy optimization system for Hong Kong quantitative trading.

This module provides comprehensive strategy optimization capabilities using
various optimization algorithms and parameter tuning methods.
"""

import asyncio
import logging
import random
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field

from .strategy_manager import OptimizationMethod, StrategyInstance


class OptimizationAlgorithm(str, Enum):
    """Optimization algorithms."""

    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    GENETIC_ALGORITHM = "genetic_algorithm"
    PARTICLE_SWARM = "particle_swarm"
    SIMULATED_ANNEALING = "simulated_annealing"
    MACHINE_LEARNING = "machine_learning"


class ParameterSpace(BaseModel):
    """Parameter space definition for optimization."""

    parameter_name: str = Field(..., description="Parameter name")
    parameter_type: str = Field(
        "float", description="Parameter type (float, int, bool, categorical)"
    )
    min_value: Optional[float] = Field(None, description="Minimum value")
    max_value: Optional[float] = Field(None, description="Maximum value")
    step_size: Optional[float] = Field(None, description="Step size for grid search")
    categorical_values: Optional[List[str]] = Field(
        None, description="Categorical values"
    )
    default_value: Any = Field(None, description="Default parameter value")


class OptimizationResult(BaseModel):
    """Optimization result model."""

    optimization_id: str = Field(..., description="Optimization identifier")
    strategy_instance_id: str = Field(..., description="Strategy instance identifier")
    algorithm: OptimizationAlgorithm = Field(
        ..., description="Optimization algorithm used"
    )

    # Optimization results
    best_parameters: Dict[str, Any] = Field(..., description="Best parameters found")
    best_fitness: float = Field(..., description="Best fitness score")
    optimization_time: float = Field(..., description="Optimization time in seconds")
    iterations: int = Field(..., description="Number of iterations")

    # Performance metrics
    sharpe_ratio: float = Field(0.0, description="Sharpe ratio of best parameters")
    max_drawdown: float = Field(0.0, description="Maximum drawdown of best parameters")
    total_return: float = Field(0.0, description="Total return of best parameters")
    win_rate: float = Field(0.0, description="Win rate of best parameters")

    # Optimization details
    convergence_history: List[float] = Field(
        default_factory=list, description="Convergence history"
    )
    parameter_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="Parameter history"
    )

    # Metadata
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Optimization timestamp"
    )
    success: bool = Field(True, description="Optimization success status")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        use_enum_values = True


class FitnessFunction:
    """Fitness function for strategy optimization."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {
            "sharpe_ratio": 0.4,
            "max_drawdown": -0.3,
            "total_return": 0.2,
            "win_rate": 0.1,
        }

    def calculate_fitness(self, metrics: Dict[str, float]) -> float:
        """Calculate fitness score from performance metrics."""
        try:
            fitness = 0.0

            # Sharpe ratio (higher is better)
            if "sharpe_ratio" in metrics:
                fitness += self.weights["sharpe_ratio"] * metrics["sharpe_ratio"]

            # Max drawdown (lower is better, so negative weight)
            if "max_drawdown" in metrics:
                fitness += self.weights["max_drawdown"] * metrics["max_drawdown"]

            # Total return (higher is better)
            if "total_return" in metrics:
                fitness += self.weights["total_return"] * metrics["total_return"]

            # Win rate (higher is better)
            if "win_rate" in metrics:
                fitness += self.weights["win_rate"] * metrics["win_rate"]

            return fitness

        except Exception as e:
            logging.getLogger(__name__).error(f"Error calculating fitness: {e}")
            return 0.0


class StrategyOptimizer:
    """Strategy optimization system."""

    def __init__(self, backtest_engine=None):
        self.backtest_engine = backtest_engine
        self.logger = logging.getLogger(__name__)

        # Optimization state
        self.active_optimizations: Dict[str, OptimizationResult] = {}
        self.optimization_history: List[OptimizationResult] = []

        # Optimization algorithms
        self.algorithms: Dict[OptimizationAlgorithm, Callable] = {}

        # Fitness function
        self.fitness_function = FitnessFunction()

        # Statistics
        self.stats = {
            "optimizations_performed": 0,
            "successful_optimizations": 0,
            "failed_optimizations": 0,
            "total_optimization_time": 0.0,
            "start_time": None,
        }

        # Initialize algorithms
        self._initialize_algorithms()

    def _initialize_algorithms(self) -> None:
        """Initialize optimization algorithms."""
        try:
            self.algorithms[OptimizationAlgorithm.GRID_SEARCH] = self._grid_search
            self.algorithms[OptimizationAlgorithm.RANDOM_SEARCH] = self._random_search
            self.algorithms[OptimizationAlgorithm.BAYESIAN_OPTIMIZATION] = (
                self._bayesian_optimization
            )
            self.algorithms[OptimizationAlgorithm.GENETIC_ALGORITHM] = (
                self._genetic_algorithm
            )
            self.algorithms[OptimizationAlgorithm.PARTICLE_SWARM] = self._particle_swarm
            self.algorithms[OptimizationAlgorithm.SIMULATED_ANNEALING] = (
                self._simulated_annealing
            )
            self.algorithms[OptimizationAlgorithm.MACHINE_LEARNING] = (
                self._machine_learning_optimization
            )

            self.logger.info(
                f"Initialized {len(self.algorithms)} optimization algorithms"
            )

        except Exception as e:
            self.logger.error(f"Error initializing algorithms: {e}")

    async def optimize_strategy(
        self,
        instance: StrategyInstance,
        parameter_space: List[ParameterSpace],
        algorithm: OptimizationAlgorithm = OptimizationAlgorithm.BAYESIAN_OPTIMIZATION,
        max_iterations: int = 100,
        timeout: int = 3600,
    ) -> OptimizationResult:
        """Optimize a strategy using specified algorithm."""
        try:
            self.logger.info(
                f"Starting optimization for strategy {instance.instance_id} using {algorithm.value}"
            )

            start_time = datetime.now()
            optimization_id = (
                f"opt_{int(start_time.timestamp())}_{instance.instance_id[:8]}"
            )

            # Get optimization algorithm
            if algorithm not in self.algorithms:
                raise ValueError(f"Unknown optimization algorithm: {algorithm}")

            optimizer = self.algorithms[algorithm]

            # Run optimization
            result = await optimizer(
                instance=instance,
                parameter_space=parameter_space,
                max_iterations=max_iterations,
                timeout=timeout,
            )

            # Calculate optimization time
            optimization_time = (datetime.now() - start_time).total_seconds()

            # Create optimization result
            optimization_result = OptimizationResult(
                optimization_id=optimization_id,
                strategy_instance_id=instance.instance_id,
                algorithm=algorithm,
                best_parameters=result["best_parameters"],
                best_fitness=result["best_fitness"],
                optimization_time=optimization_time,
                iterations=result["iterations"],
                sharpe_ratio=result.get("sharpe_ratio", 0.0),
                max_drawdown=result.get("max_drawdown", 0.0),
                total_return=result.get("total_return", 0.0),
                win_rate=result.get("win_rate", 0.0),
                convergence_history=result.get("convergence_history", []),
                parameter_history=result.get("parameter_history", []),
                success=result["success"],
                error_message=result.get("error_message"),
            )

            # Store result
            self.active_optimizations[optimization_id] = optimization_result
            self.optimization_history.append(optimization_result)

            # Update statistics
            self.stats["optimizations_performed"] += 1
            self.stats["total_optimization_time"] += optimization_time

            if result["success"]:
                self.stats["successful_optimizations"] += 1
            else:
                self.stats["failed_optimizations"] += 1

            self.logger.info(
                f"Optimization completed: {optimization_id} - Success: {result['success']}"
            )
            return optimization_result

        except Exception as e:
            self.logger.error(f"Error optimizing strategy: {e}")
            return OptimizationResult(
                optimization_id=f"failed_{int(datetime.now().timestamp())}",
                strategy_instance_id=instance.instance_id,
                algorithm=algorithm,
                best_parameters={},
                best_fitness=0.0,
                optimization_time=0.0,
                iterations=0,
                success=False,
                error_message=str(e),
            )

    async def _grid_search(
        self,
        instance: StrategyInstance,
        parameter_space: List[ParameterSpace],
        max_iterations: int,
        timeout: int,
    ) -> Dict[str, Any]:
        """Grid search optimization."""
        try:
            # Generate parameter combinations
            parameter_combinations = self._generate_grid_combinations(parameter_space)

            best_fitness = float("-inf")
            best_parameters = {}
            convergence_history = []
            parameter_history = []

            iterations = 0
            for params in parameter_combinations[:max_iterations]:
                # Evaluate parameters
                fitness, metrics = await self._evaluate_parameters(instance, params)

                if fitness > best_fitness:
                    best_fitness = fitness
                    best_parameters = params.copy()

                convergence_history.append(fitness)
                parameter_history.append(params.copy())
                iterations += 1

            return {
                "success": True,
                "best_parameters": best_parameters,
                "best_fitness": best_fitness,
                "iterations": iterations,
                "convergence_history": convergence_history,
                "parameter_history": parameter_history,
                "sharpe_ratio": best_parameters.get("sharpe_ratio", 0.0),
                "max_drawdown": best_parameters.get("max_drawdown", 0.0),
                "total_return": best_parameters.get("total_return", 0.0),
                "win_rate": best_parameters.get("win_rate", 0.0),
            }

        except Exception as e:
            return {"success": False, "error_message": str(e)}

    async def _random_search(
        self,
        instance: StrategyInstance,
        parameter_space: List[ParameterSpace],
        max_iterations: int,
        timeout: int,
    ) -> Dict[str, Any]:
        """Random search optimization."""
        try:
            best_fitness = float("-inf")
            best_parameters = {}
            convergence_history = []
            parameter_history = []

            for i in range(max_iterations):
                # Generate random parameters
                params = self._generate_random_parameters(parameter_space)

                # Evaluate parameters
                fitness, metrics = await self._evaluate_parameters(instance, params)

                if fitness > best_fitness:
                    best_fitness = fitness
                    best_parameters = params.copy()

                convergence_history.append(fitness)
                parameter_history.append(params.copy())

            return {
                "success": True,
                "best_parameters": best_parameters,
                "best_fitness": best_fitness,
                "iterations": max_iterations,
                "convergence_history": convergence_history,
                "parameter_history": parameter_history,
                "sharpe_ratio": best_parameters.get("sharpe_ratio", 0.0),
                "max_drawdown": best_parameters.get("max_drawdown", 0.0),
                "total_return": best_parameters.get("total_return", 0.0),
                "win_rate": best_parameters.get("win_rate", 0.0),
            }

        except Exception as e:
            return {"success": False, "error_message": str(e)}

    async def _bayesian_optimization(
        self,
        instance: StrategyInstance,
        parameter_space: List[ParameterSpace],
        max_iterations: int,
        timeout: int,
    ) -> Dict[str, Any]:
        """Bayesian optimization."""
        try:
            # Simplified Bayesian optimization implementation
            # In real implementation, would use libraries like scikit - optimize

            best_fitness = float("-inf")
            best_parameters = {}
            convergence_history = []
            parameter_history = []

            # Start with random exploration
            exploration_ratio = 0.3
            exploration_iterations = int(max_iterations * exploration_ratio)

            # Exploration phase
            for i in range(exploration_iterations):
                params = self._generate_random_parameters(parameter_space)
                fitness, metrics = await self._evaluate_parameters(instance, params)

                if fitness > best_fitness:
                    best_fitness = fitness
                    best_parameters = params.copy()

                convergence_history.append(fitness)
                parameter_history.append(params.copy())

            # Exploitation phase (simplified)
            for i in range(exploration_iterations, max_iterations):
                # Generate parameters around best known point
                params = self._generate_perturbed_parameters(
                    best_parameters, parameter_space, 0.1
                )
                fitness, metrics = await self._evaluate_parameters(instance, params)

                if fitness > best_fitness:
                    best_fitness = fitness
                    best_parameters = params.copy()

                convergence_history.append(fitness)
                parameter_history.append(params.copy())

            return {
                "success": True,
                "best_parameters": best_parameters,
                "best_fitness": best_fitness,
                "iterations": max_iterations,
                "convergence_history": convergence_history,
                "parameter_history": parameter_history,
                "sharpe_ratio": best_parameters.get("sharpe_ratio", 0.0),
                "max_drawdown": best_parameters.get("max_drawdown", 0.0),
                "total_return": best_parameters.get("total_return", 0.0),
                "win_rate": best_parameters.get("win_rate", 0.0),
            }

        except Exception as e:
            return {"success": False, "error_message": str(e)}

    async def _genetic_algorithm(
        self,
        instance: StrategyInstance,
        parameter_space: List[ParameterSpace],
        max_iterations: int,
        timeout: int,
    ) -> Dict[str, Any]:
        """Genetic algorithm optimization."""
        try:
            # Simplified genetic algorithm implementation
            population_size = 20
            mutation_rate = 0.1
            crossover_rate = 0.8

            # Initialize population
            population = []
            for _ in range(population_size):
                individual = self._generate_random_parameters(parameter_space)
                population.append(individual)

            best_fitness = float("-inf")
            best_parameters = {}
            convergence_history = []
            parameter_history = []

            for generation in range(max_iterations):
                # Evaluate population
                fitness_scores = []
                for individual in population:
                    fitness, metrics = await self._evaluate_parameters(
                        instance, individual
                    )
                    fitness_scores.append(fitness)

                    if fitness > best_fitness:
                        best_fitness = fitness
                        best_parameters = individual.copy()

                convergence_history.append(max(fitness_scores))
                parameter_history.append(best_parameters.copy())

                # Selection, crossover, and mutation
                new_population = []

                # Elitism - keep best individual
                best_idx = fitness_scores.index(max(fitness_scores))
                new_population.append(population[best_idx].copy())

                # Generate new individuals
                while len(new_population) < population_size:
                    # Selection (tournament selection)
                    parent1 = self._tournament_selection(population, fitness_scores)
                    parent2 = self._tournament_selection(population, fitness_scores)

                    # Crossover
                    if random.random() < crossover_rate:
                        child1, child2 = self._crossover(
                            parent1, parent2, parameter_space
                        )
                    else:
                        child1, child2 = parent1.copy(), parent2.copy()

                    # Mutation
                    if random.random() < mutation_rate:
                        child1 = self._mutate(child1, parameter_space)
                    if random.random() < mutation_rate:
                        child2 = self._mutate(child2, parameter_space)

                    new_population.extend([child1, child2])

                population = new_population[:population_size]

            return {
                "success": True,
                "best_parameters": best_parameters,
                "best_fitness": best_fitness,
                "iterations": max_iterations,
                "convergence_history": convergence_history,
                "parameter_history": parameter_history,
                "sharpe_ratio": best_parameters.get("sharpe_ratio", 0.0),
                "max_drawdown": best_parameters.get("max_drawdown", 0.0),
                "total_return": best_parameters.get("total_return", 0.0),
                "win_rate": best_parameters.get("win_rate", 0.0),
            }

        except Exception as e:
            return {"success": False, "error_message": str(e)}

    async def _particle_swarm(
        self,
        instance: StrategyInstance,
        parameter_space: List[ParameterSpace],
        max_iterations: int,
        timeout: int,
    ) -> Dict[str, Any]:
        """Particle swarm optimization."""
        try:
            # Simplified PSO implementation
            swarm_size = 20
            w = 0.9  # inertia weight
            c1 = 2.0  # cognitive parameter
            c2 = 2.0  # social parameter

            # Initialize swarm
            particles = []
            for _ in range(swarm_size):
                position = self._generate_random_parameters(parameter_space)
                velocity = self._generate_zero_velocity(parameter_space)
                particles.append(
                    {
                        "position": position,
                        "velocity": velocity,
                        "best_position": position.copy(),
                        "best_fitness": float("-inf"),
                    }
                )

            global_best_position = {}
            global_best_fitness = float("-inf")
            convergence_history = []
            parameter_history = []

            for iteration in range(max_iterations):
                for particle in particles:
                    # Evaluate current position
                    fitness, metrics = await self._evaluate_parameters(
                        instance, particle["position"]
                    )

                    # Update personal best
                    if fitness > particle["best_fitness"]:
                        particle["best_fitness"] = fitness
                        particle["best_position"] = particle["position"].copy()

                    # Update global best
                    if fitness > global_best_fitness:
                        global_best_fitness = fitness
                        global_best_position = particle["position"].copy()

                # Update velocities and positions
                for particle in particles:
                    for param_name in particle["position"]:
                        if param_name in particle["velocity"]:
                            # Update velocity
                            r1, r2 = random.random(), random.random()
                            cognitive = (
                                c1
                                * r1
                                * (
                                    particle["best_position"][param_name]
                                    - particle["position"][param_name]
                                )
                            )
                            social = (
                                c2
                                * r2
                                * (
                                    global_best_position[param_name]
                                    - particle["position"][param_name]
                                )
                            )
                            particle["velocity"][param_name] = (
                                w * particle["velocity"][param_name]
                                + cognitive
                                + social
                            )

                            # Update position
                            particle["position"][param_name] += particle["velocity"][
                                param_name
                            ]

                convergence_history.append(global_best_fitness)
                parameter_history.append(global_best_position.copy())

            return {
                "success": True,
                "best_parameters": global_best_position,
                "best_fitness": global_best_fitness,
                "iterations": max_iterations,
                "convergence_history": convergence_history,
                "parameter_history": parameter_history,
                "sharpe_ratio": global_best_position.get("sharpe_ratio", 0.0),
                "max_drawdown": global_best_position.get("max_drawdown", 0.0),
                "total_return": global_best_position.get("total_return", 0.0),
                "win_rate": global_best_position.get("win_rate", 0.0),
            }

        except Exception as e:
            return {"success": False, "error_message": str(e)}

    async def _simulated_annealing(
        self,
        instance: StrategyInstance,
        parameter_space: List[ParameterSpace],
        max_iterations: int,
        timeout: int,
    ) -> Dict[str, Any]:
        """Simulated annealing optimization."""
        try:
            # Initial temperature and cooling rate
            initial_temp = 100.0
            cooling_rate = 0.95

            # Start with random parameters
            current_params = self._generate_random_parameters(parameter_space)
            current_fitness, _ = await self._evaluate_parameters(
                instance, current_params
            )

            best_params = current_params.copy()
            best_fitness = current_fitness

            convergence_history = [current_fitness]
            parameter_history = [current_params.copy()]

            temperature = initial_temp

            for iteration in range(max_iterations):
                # Generate neighbor
                neighbor_params = self._generate_neighbor_parameters(
                    current_params, parameter_space, temperature
                )
                neighbor_fitness, _ = await self._evaluate_parameters(
                    instance, neighbor_params
                )

                # Accept or reject neighbor
                if neighbor_fitness > current_fitness:
                    # Accept better solution
                    current_params = neighbor_params
                    current_fitness = neighbor_fitness

                    if neighbor_fitness > best_fitness:
                        best_params = neighbor_params.copy()
                        best_fitness = neighbor_fitness
                else:
                    # Accept worse solution with probability
                    probability = np.exp(
                        (neighbor_fitness - current_fitness) / temperature
                    )
                    if random.random() < probability:
                        current_params = neighbor_params
                        current_fitness = neighbor_fitness

                convergence_history.append(current_fitness)
                parameter_history.append(best_params.copy())

                # Cool down
                temperature *= cooling_rate

            return {
                "success": True,
                "best_parameters": best_params,
                "best_fitness": best_fitness,
                "iterations": max_iterations,
                "convergence_history": convergence_history,
                "parameter_history": parameter_history,
                "sharpe_ratio": best_params.get("sharpe_ratio", 0.0),
                "max_drawdown": best_params.get("max_drawdown", 0.0),
                "total_return": best_params.get("total_return", 0.0),
                "win_rate": best_params.get("win_rate", 0.0),
            }

        except Exception as e:
            return {"success": False, "error_message": str(e)}

    async def _machine_learning_optimization(
        self,
        instance: StrategyInstance,
        parameter_space: List[ParameterSpace],
        max_iterations: int,
        timeout: int,
    ) -> Dict[str, Any]:
        """Machine learning - based optimization."""
        try:
            # Simplified ML optimization
            # In real implementation, would use actual ML models

            best_fitness = float("-inf")
            best_parameters = {}
            convergence_history = []
            parameter_history = []

            # Collect training data
            training_data = []
            for i in range(min(50, max_iterations)):
                params = self._generate_random_parameters(parameter_space)
                fitness, metrics = await self._evaluate_parameters(instance, params)
                training_data.append((params, fitness))

            # Simple linear regression model (placeholder)
            # In real implementation, would train actual ML model

            # Use model to guide search
            for i in range(max_iterations):
                # Generate parameters based on model prediction
                params = self._generate_ml_guided_parameters(
                    parameter_space, training_data
                )
                fitness, metrics = await self._evaluate_parameters(instance, params)

                if fitness > best_fitness:
                    best_fitness = fitness
                    best_parameters = params.copy()

                convergence_history.append(fitness)
                parameter_history.append(params.copy())

                # Update training data
                training_data.append((params, fitness))
                if len(training_data) > 100:
                    training_data = training_data[-100:]  # Keep recent data

            return {
                "success": True,
                "best_parameters": best_parameters,
                "best_fitness": best_fitness,
                "iterations": max_iterations,
                "convergence_history": convergence_history,
                "parameter_history": parameter_history,
                "sharpe_ratio": best_parameters.get("sharpe_ratio", 0.0),
                "max_drawdown": best_parameters.get("max_drawdown", 0.0),
                "total_return": best_parameters.get("total_return", 0.0),
                "win_rate": best_parameters.get("win_rate", 0.0),
            }

        except Exception as e:
            return {"success": False, "error_message": str(e)}

    # Helper methods
    def _generate_grid_combinations(
        self, parameter_space: List[ParameterSpace]
    ) -> List[Dict[str, Any]]:
        """Generate parameter combinations for grid search."""
        try:
            combinations = []

            # Generate all combinations
            param_ranges = []
            for param in parameter_space:
                if param.parameter_type == "float":
                    if param.step_size:
                        values = np.arange(
                            param.min_value,
                            param.max_value + param.step_size,
                            param.step_size,
                        )
                    else:
                        values = [param.min_value, param.max_value]
                elif param.parameter_type == "int":
                    if param.step_size:
                        values = list(
                            range(
                                int(param.min_value),
                                int(param.max_value) + 1,
                                int(param.step_size),
                            )
                        )
                    else:
                        values = [int(param.min_value), int(param.max_value)]
                elif param.parameter_type == "categorical":
                    values = param.categorical_values or []
                else:
                    values = [param.default_value]

                param_ranges.append(values)

            # Generate combinations
            import itertools

            for combination in itertools.product(*param_ranges):
                params = {}
                for i, param in enumerate(parameter_space):
                    params[param.parameter_name] = combination[i]
                combinations.append(params)

            return combinations

        except Exception as e:
            self.logger.error(f"Error generating grid combinations: {e}")
            return []

    def _generate_random_parameters(
        self, parameter_space: List[ParameterSpace]
    ) -> Dict[str, Any]:
        """Generate random parameters within bounds."""
        try:
            params = {}
            for param in parameter_space:
                if param.parameter_type == "float":
                    value = random.uniform(param.min_value, param.max_value)
                elif param.parameter_type == "int":
                    value = random.randint(int(param.min_value), int(param.max_value))
                elif param.parameter_type == "bool":
                    value = random.choice([True, False])
                elif param.parameter_type == "categorical":
                    value = random.choice(param.categorical_values or [])
                else:
                    value = param.default_value

                params[param.parameter_name] = value

            return params

        except Exception as e:
            self.logger.error(f"Error generating random parameters: {e}")
            return {}

    def _generate_perturbed_parameters(
        self,
        base_params: Dict[str, Any],
        parameter_space: List[ParameterSpace],
        perturbation_factor: float,
    ) -> Dict[str, Any]:
        """Generate perturbed parameters around base parameters."""
        try:
            params = base_params.copy()

            for param in parameter_space:
                if param.parameter_type == "float":
                    current_value = params.get(
                        param.parameter_name, param.default_value
                    )
                    perturbation = random.gauss(
                        0, perturbation_factor * (param.max_value - param.min_value)
                    )
                    new_value = current_value + perturbation
                    new_value = max(param.min_value, min(param.max_value, new_value))
                    params[param.parameter_name] = new_value
                elif param.parameter_type == "int":
                    current_value = params.get(
                        param.parameter_name, param.default_value
                    )
                    perturbation = random.randint(-1, 1)
                    new_value = current_value + perturbation
                    new_value = max(
                        int(param.min_value), min(int(param.max_value), new_value)
                    )
                    params[param.parameter_name] = new_value

            return params

        except Exception as e:
            self.logger.error(f"Error generating perturbed parameters: {e}")
            return base_params.copy()

    def _generate_neighbor_parameters(
        self,
        current_params: Dict[str, Any],
        parameter_space: List[ParameterSpace],
        temperature: float,
    ) -> Dict[str, Any]:
        """Generate neighbor parameters for simulated annealing."""
        try:
            params = current_params.copy()

            # Perturb one random parameter
            param = random.choice(parameter_space)
            if param.parameter_type == "float":
                current_value = params.get(param.parameter_name, param.default_value)
                perturbation = random.gauss(
                    0, temperature * (param.max_value - param.min_value) / 100
                )
                new_value = current_value + perturbation
                new_value = max(param.min_value, min(param.max_value, new_value))
                params[param.parameter_name] = new_value
            elif param.parameter_type == "int":
                current_value = params.get(param.parameter_name, param.default_value)
                perturbation = random.randint(-1, 1)
                new_value = current_value + perturbation
                new_value = max(
                    int(param.min_value), min(int(param.max_value), new_value)
                )
                params[param.parameter_name] = new_value

            return params

        except Exception as e:
            self.logger.error(f"Error generating neighbor parameters: {e}")
            return current_params.copy()

    def _generate_ml_guided_parameters(
        self,
        parameter_space: List[ParameterSpace],
        training_data: List[Tuple[Dict[str, Any], float]],
    ) -> Dict[str, Any]:
        """Generate parameters guided by ML model."""
        try:
            # Simple heuristic: prefer parameters similar to high - performing ones
            if not training_data:
                return self._generate_random_parameters(parameter_space)

            # Find best performing parameters
            best_params, best_fitness = max(training_data, key=lambda x: x[1])

            # Generate parameters around best performing ones
            return self._generate_perturbed_parameters(
                best_params, parameter_space, 0.1
            )

        except Exception as e:
            self.logger.error(f"Error generating ML guided parameters: {e}")
            return self._generate_random_parameters(parameter_space)

    def _generate_zero_velocity(
        self, parameter_space: List[ParameterSpace]
    ) -> Dict[str, Any]:
        """Generate zero velocity for PSO."""
        try:
            velocity = {}
            for param in parameter_space:
                velocity[param.parameter_name] = 0.0
            return velocity

        except Exception as e:
            self.logger.error(f"Error generating zero velocity: {e}")
            return {}

    def _tournament_selection(
        self,
        population: List[Dict[str, Any]],
        fitness_scores: List[float],
        tournament_size: int = 3,
    ) -> Dict[str, Any]:
        """Tournament selection for genetic algorithm."""
        try:
            tournament_indices = random.sample(
                range(len(population)), min(tournament_size, len(population))
            )
            tournament_fitness = [fitness_scores[i] for i in tournament_indices]
            winner_idx = tournament_indices[
                tournament_fitness.index(max(tournament_fitness))
            ]
            return population[winner_idx].copy()

        except Exception as e:
            self.logger.error(f"Error in tournament selection: {e}")
            return population[0].copy()

    def _crossover(
        self,
        parent1: Dict[str, Any],
        parent2: Dict[str, Any],
        parameter_space: List[ParameterSpace],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Crossover operation for genetic algorithm."""
        try:
            child1 = parent1.copy()
            child2 = parent2.copy()

            # Single point crossover
            crossover_point = random.randint(1, len(parameter_space) - 1)

            for i, param in enumerate(parameter_space):
                if i >= crossover_point:
                    child1[param.parameter_name] = parent2[param.parameter_name]
                    child2[param.parameter_name] = parent1[param.parameter_name]

            return child1, child2

        except Exception as e:
            self.logger.error(f"Error in crossover: {e}")
            return parent1.copy(), parent2.copy()

    def _mutate(
        self, individual: Dict[str, Any], parameter_space: List[ParameterSpace]
    ) -> Dict[str, Any]:
        """Mutation operation for genetic algorithm."""
        try:
            mutated = individual.copy()

            # Mutate one random parameter
            param = random.choice(parameter_space)
            if param.parameter_type == "float":
                current_value = mutated.get(param.parameter_name, param.default_value)
                mutation = random.gauss(0, (param.max_value - param.min_value) * 0.1)
                new_value = current_value + mutation
                new_value = max(param.min_value, min(param.max_value, new_value))
                mutated[param.parameter_name] = new_value
            elif param.parameter_type == "int":
                current_value = mutated.get(param.parameter_name, param.default_value)
                mutation = random.randint(-1, 1)
                new_value = current_value + mutation
                new_value = max(
                    int(param.min_value), min(int(param.max_value), new_value)
                )
                mutated[param.parameter_name] = new_value
            elif param.parameter_type == "bool":
                mutated[param.parameter_name] = not mutated.get(
                    param.parameter_name, False
                )
            elif param.parameter_type == "categorical":
                mutated[param.parameter_name] = random.choice(
                    param.categorical_values or []
                )

            return mutated

        except Exception as e:
            self.logger.error(f"Error in mutation: {e}")
            return individual.copy()

    async def _evaluate_parameters(
        self, instance: StrategyInstance, parameters: Dict[str, Any]
    ) -> Tuple[float, Dict[str, float]]:
        """Evaluate strategy parameters using backtesting."""
        try:
            # In real implementation, this would run actual backtesting
            # For now, simulate performance metrics

            # Simulate backtesting results
            sharpe_ratio = random.uniform(-1.0, 3.0)
            max_drawdown = random.uniform(0.0, 0.3)
            total_return = random.uniform(-0.2, 0.5)
            win_rate = random.uniform(0.3, 0.8)

            metrics = {
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "total_return": total_return,
                "win_rate": win_rate,
            }

            # Calculate fitness
            fitness = self.fitness_function.calculate_fitness(metrics)

            return fitness, metrics

        except Exception as e:
            self.logger.error(f"Error evaluating parameters: {e}")
            return 0.0, {}

    # Public methods
    def get_optimization_result(
        self, optimization_id: str
    ) -> Optional[OptimizationResult]:
        """Get optimization result by ID."""
        return self.active_optimizations.get(optimization_id)

    def get_optimization_history(self, limit: int = 100) -> List[OptimizationResult]:
        """Get optimization history."""
        return self.optimization_history[-limit:] if self.optimization_history else []

    def get_statistics(self) -> Dict[str, Any]:
        """Get optimizer statistics."""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "uptime_seconds": uptime,
            "active_optimizations": len(self.active_optimizations),
            "optimization_history_count": len(self.optimization_history),
            "stats": self.stats.copy(),
        }
