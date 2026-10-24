"""
Performance Benchmark System for Optimization Algorithms
======================================================

Comprehensive benchmarking system for comparing optimization algorithms:
- Standardized benchmark functions (convex, non-convex, multi-modal)
- Statistical analysis with confidence intervals
- Performance metrics (convergence speed, solution quality, efficiency)
- Result visualization and leaderboards
- Save/load functionality for historical comparison

Author: CBSC Quant Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
import json
import time
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import logging
from datetime import datetime
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Import optimizer module
import importlib.util
import sys
import os

logger = logging.getLogger(__name__)


class ProblemType(str, Enum):
    """Benchmark problem types"""
    CONVEX = "convex"           # Smooth, single global optimum
    NON_CONVEX = "non_convex"   # Multiple local optima
    MULTI_MODAL = "multi_modal" # Many local optima
    NOISY = "noisy"             # Stochastic objective
    DISCRETE = "discrete"       # Discrete parameters


@dataclass
class BenchmarkFunction:
    """Benchmark function definition"""
    name: str
    func: Callable
    bounds: List[Tuple[float, float]]
    global_optimum: float
    global_optimum_location: List[float]
    problem_type: ProblemType
    dimensions: int
    description: str = ""


@dataclass
class BenchmarkConfig:
    """Benchmark configuration"""
    n_runs: int = 10  # Number of runs per method for statistical significance
    random_state: int = 42
    timeout_seconds: float = 300  # Maximum time per optimization
    save_results: bool = True
    output_dir: str = "./benchmark_results"
    methods_to_test: List[str] = field(default_factory=lambda: [
        "grid_search",
        "random_search",
        "bayesian_optimization",
        "genetic_algorithm",
        "particle_swarm",
        "differential_evolution",
        "simulated_annealing"
    ])


@dataclass
class BenchmarkResult:
    """Single benchmark run result"""
    method: str
    function_name: str
    run_id: int
    best_score: float
    best_params: Dict[str, Any]
    n_evaluations: int
    runtime: float
    converged: bool
    error_message: Optional[str] = None
    convergence_curve: Optional[List[float]] = None


@dataclass
class AggregateBenchmarkResult:
    """Aggregated benchmark results across multiple runs"""
    method: str
    function_name: str
    problem_type: ProblemType

    # Performance metrics
    mean_score: float
    std_score: float
    min_score: float
    max_score: float
    median_score: float

    # Success rate
    success_rate: float  # Percentage of runs finding near-optimal solution
    convergence_rate: float  # Percentage of runs that converged

    # Efficiency metrics
    mean_runtime: float
    std_runtime: float
    mean_evaluations: float
    std_evaluations: float

    # Confidence intervals (95%)
    score_ci: Tuple[float, float]
    runtime_ci: Tuple[float, float]

    # Individual run results
    individual_results: List[BenchmarkResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class PerformanceBenchmark:
    """
    Performance benchmark system for optimization algorithms
    """

    def __init__(self, config: Optional[BenchmarkConfig] = None):
        """
        Initialize benchmark system

        Args:
            config: Benchmark configuration
        """
        self.config = config or BenchmarkConfig()
        self.benchmark_functions: Dict[str, BenchmarkFunction] = {}
        self.results: List[BenchmarkResult] = []
        self.aggregated_results: Dict[str, AggregateBenchmarkResult] = {}

        # Load optimizer module
        self._load_optimizer()

        # Setup output directory
        if self.config.save_results:
            Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

        logger.info("Performance benchmark system initialized")

    def _load_optimizer(self):
        """Load parameter optimizer module"""
        # Get the path to the optimizer module
        current_dir = Path(__file__).parent
        optimizer_path = current_dir / "parameter_optimizer.py"

        spec = importlib.util.spec_from_file_location(
            "parameter_optimizer",
            str(optimizer_path)
        )
        optimizer_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(optimizer_module)

        self.optimizer_module = optimizer_module

        logger.info("Optimizer module loaded successfully")

    def register_benchmark_function(self, benchmark_func: BenchmarkFunction) -> None:
        """
        Register a benchmark function

        Args:
            benchmark_func: Benchmark function definition
        """
        self.benchmark_functions[benchmark_func.name] = benchmark_func
        logger.info(f"Registered benchmark function: {benchmark_func.name}")

    def run_benchmark(
        self,
        function_names: Optional[List[str]] = None,
        methods: Optional[List[str]] = None
    ) -> Dict[str, AggregateBenchmarkResult]:
        """
        Run comprehensive benchmark

        Args:
            function_names: List of function names to benchmark (None = all)
            methods: List of methods to test (None = all from config)

        Returns:
            Dictionary of aggregated results
        """
        # Use all functions if none specified
        if function_names is None:
            function_names = list(self.benchmark_functions.keys())

        # Use all methods if none specified
        if methods is None:
            methods = self.config.methods_to_test

        logger.info(f"Starting benchmark: {len(function_names)} functions x {len(methods)} methods")
        logger.info(f"Total runs: {len(function_names) * len(methods) * self.config.n_runs}")

        # Clear previous results
        self.results = []
        self.aggregated_results = {}

        # Run benchmarks
        for func_name in function_names:
            benchmark_func = self.benchmark_functions[func_name]
            logger.info(f"\nBenchmarking function: {func_name}")

            for method in methods:
                logger.info(f"  Testing method: {method}")

                # Run multiple times for statistical significance
                for run_id in range(self.config.n_runs):
                    np.random.seed(self.config.random_state + run_id)

                    result = self._run_single_benchmark(
                        benchmark_func,
                        method,
                        run_id
                    )

                    self.results.append(result)

                    if result.error_message:
                        logger.warning(f"    Run {run_id + 1}: ERROR - {result.error_message}")
                    else:
                        logger.info(f"    Run {run_id + 1}: score={result.best_score:.6f}, "
                                  f"time={result.runtime:.2f}s")

        # Aggregate results
        self._aggregate_results(function_names, methods)

        # Save results
        if self.config.save_results:
            self._save_results()

        return self.aggregated_results

    def _run_single_benchmark(
        self,
        benchmark_func: BenchmarkFunction,
        method: str,
        run_id: int
    ) -> BenchmarkResult:
        """Run a single benchmark run"""
        start_time = time.time()
        error_message = None
        converged = False

        try:
            # Create optimizer configuration
            opt_config = self.optimizer_module.create_optimization_config(
                method=self.optimizer_module.OptimizationMethod(method),
                max_iterations=100,
                random_state=self.config.random_state + run_id
            )

            # Create optimizer
            optimizer = self.optimizer_module.ParameterOptimizer(opt_config)

            # Add parameters based on benchmark function dimensions
            for i in range(benchmark_func.dimensions):
                param_name = f"x{i}"
                bounds = benchmark_func.bounds[i]
                if benchmark_func.problem_type == ProblemType.DISCRETE:
                    param_space = self.optimizer_module.create_parameter_space(
                        param_name, 'discrete',
                        (int(bounds[0]), int(bounds[1]))
                    )
                else:
                    param_space = self.optimizer_module.create_parameter_space(
                        param_name, 'continuous', bounds
                    )
                optimizer.add_parameter(param_space)

            # Define objective function wrapper
            def objective(params: Dict[str, Any], data: Any) -> float:
                # Convert params to array
                x = np.array([params[f"x{i}"] for i in range(benchmark_func.dimensions)])
                # Call benchmark function (negative because we maximize)
                return -benchmark_func.func(x)

            # Run optimization
            result = optimizer.optimize(objective, None)

            runtime = time.time() - start_time

            # Check convergence
            converged = self._check_convergence(result, benchmark_func)

            return BenchmarkResult(
                method=method,
                function_name=benchmark_func.name,
                run_id=run_id,
                best_score=-result.best_score,  # Convert back to minimization
                best_params=result.best_params,
                n_evaluations=result.n_evaluations,
                runtime=runtime,
                converged=converged,
                convergence_curve=result.convergence_curve
            )

        except Exception as e:
            runtime = time.time() - start_time
            error_message = str(e)
            logger.error(f"Benchmark run failed: {error_message}")

            return BenchmarkResult(
                method=method,
                function_name=benchmark_func.name,
                run_id=run_id,
                best_score=float('inf'),
                best_params={},
                n_evaluations=0,
                runtime=runtime,
                converged=False,
                error_message=error_message
            )

    def _check_convergence(
        self,
        result: Any,
        benchmark_func: BenchmarkFunction
    ) -> bool:
        """Check if optimization converged to near-optimal solution"""
        # Consider converged if within 1% of global optimum
        tolerance = abs(benchmark_func.global_optimum) * 0.01
        return abs(-result.best_score - benchmark_func.global_optimum) < max(tolerance, 1e-6)

    def _aggregate_results(
        self,
        function_names: List[str],
        methods: List[str]
    ) -> None:
        """Aggregate results across multiple runs"""
        for func_name in function_names:
            benchmark_func = self.benchmark_functions[func_name]

            for method in methods:
                # Filter results for this function and method
                method_results = [
                    r for r in self.results
                    if r.function_name == func_name and r.method == method
                ]

                if not method_results:
                    continue

                # Extract successful runs
                successful_results = [r for r in method_results if r.error_message is None]

                if not successful_results:
                    continue

                # Calculate statistics
                scores = [r.best_score for r in successful_results]
                runtimes = [r.runtime for r in successful_results]
                evaluations = [r.n_evaluations for r in successful_results]

                # Mean and std
                mean_score = np.mean(scores)
                std_score = np.std(scores, ddof=1) if len(scores) > 1 else 0
                min_score = np.min(scores)
                max_score = np.max(scores)
                median_score = np.median(scores)

                mean_runtime = np.mean(runtimes)
                std_runtime = np.std(runtimes, ddof=1) if len(runtimes) > 1 else 0

                mean_evaluations = np.mean(evaluations)
                std_evaluations = np.std(evaluations, ddof=1) if len(evaluations) > 1 else 0

                # Confidence intervals (95%)
                score_ci = stats.t.interval(
                    0.95, len(scores) - 1,
                    loc=mean_score, scale=std_score / np.sqrt(len(scores))
                ) if len(scores) > 1 else (mean_score, mean_score)

                runtime_ci = stats.t.interval(
                    0.95, len(runtimes) - 1,
                    loc=mean_runtime, scale=std_runtime / np.sqrt(len(runtimes))
                ) if len(runtimes) > 1 else (mean_runtime, mean_runtime)

                # Success rate (near-optimal solution)
                successful_runs = sum(1 for r in successful_results if r.converged)
                success_rate = successful_runs / len(successful_results)

                # Convergence rate (no errors)
                convergence_rate = len(successful_results) / len(method_results)

                # Create aggregated result
                key = f"{func_name}_{method}"
                self.aggregated_results[key] = AggregateBenchmarkResult(
                    method=method,
                    function_name=func_name,
                    problem_type=benchmark_func.problem_type,
                    mean_score=mean_score,
                    std_score=std_score,
                    min_score=min_score,
                    max_score=max_score,
                    median_score=median_score,
                    success_rate=success_rate,
                    convergence_rate=convergence_rate,
                    mean_runtime=mean_runtime,
                    std_runtime=std_runtime,
                    mean_evaluations=mean_evaluations,
                    std_evaluations=std_evaluations,
                    score_ci=score_ci,
                    runtime_ci=runtime_ci,
                    individual_results=method_results
                )

    def generate_leaderboard(self, metric: str = "mean_score") -> pd.DataFrame:
        """
        Generate leaderboard ranking methods by performance

        Args:
            metric: Metric to rank by ('mean_score', 'success_rate', 'mean_runtime')

        Returns:
            DataFrame with ranking
        """
        if not self.aggregated_results:
            raise ValueError("No results available. Run benchmark first.")

        # Convert to DataFrame
        data = []
        for result in self.aggregated_results.values():
            data.append({
                'Method': result.method,
                'Function': result.function_name,
                'Problem Type': result.problem_type.value,
                'Mean Score': result.mean_score,
                'Std Score': result.std_score,
                'Success Rate': result.success_rate,
                'Mean Runtime (s)': result.mean_runtime,
                'Mean Evaluations': result.mean_evaluations
            })

        df = pd.DataFrame(data)

        # Sort by metric - map metric names to column names
        metric_mapping = {
            'mean_score': 'Mean Score',
            'success_rate': 'Success Rate',
            'mean_runtime': 'Mean Runtime (s)'
        }

        sort_column = metric_mapping.get(metric, metric)

        if metric == "mean_runtime" or metric == "mean_score":
            # Lower is better for runtime and score (minimization)
            df = df.sort_values(sort_column, ascending=True)
        else:
            # Higher is better for success rate
            df = df.sort_values(sort_column, ascending=False)

        return df

    def plot_comparison(
        self,
        function_name: Optional[str] = None,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot comparison of optimization methods

        Args:
            function_name: Specific function to plot (None = all)
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        if not self.aggregated_results:
            raise ValueError("No results available. Run benchmark first.")

        # Filter results
        if function_name:
            results = {
                k: v for k, v in self.aggregated_results.items()
                if v.function_name == function_name
            }
        else:
            results = self.aggregated_results

        # Group by method
        methods = {}
        for result in results.values():
            if result.method not in methods:
                methods[result.method] = []
            methods[result.method].append(result)

        # Create figure
        fig = plt.figure(figsize=(16, 10))
        gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

        # 1. Score comparison (box plot style)
        ax1 = fig.add_subplot(gs[0, 0])

        method_names = list(methods.keys())
        all_scores = []
        for method in method_names:
            scores = [r.mean_score for r in methods[method]]
            all_scores.append(scores)

        bp = ax1.boxplot(all_scores, labels=method_names, patch_artist=True)
        for patch in bp['boxes']:
            patch.set_facecolor('lightblue')

        ax1.set_ylabel('Objective Value (lower is better)', fontsize=11)
        ax1.set_title('Score Distribution by Method', fontsize=13, fontweight='bold')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)

        # 2. Success rate comparison
        ax2 = fig.add_subplot(gs[0, 1])

        success_rates = []
        for method in method_names:
            rates = [r.success_rate for r in methods[method]]
            success_rates.append(np.mean(rates))

        colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(method_names)))
        bars = ax2.bar(method_names, success_rates, color=colors, edgecolor='black', alpha=0.8)

        ax2.set_ylabel('Success Rate', fontsize=11)
        ax2.set_title('Optimization Success Rate', fontsize=13, fontweight='bold')
        ax2.set_ylim(0, 1.1)
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3, axis='y')

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{height:.2f}', ha='center', va='bottom', fontsize=9)

        # 3. Runtime comparison
        ax3 = fig.add_subplot(gs[1, 0])

        runtimes = []
        runtime_errors = []
        for method in method_names:
            mean_runtime = np.mean([r.mean_runtime for r in methods[method]])
            std_runtime = np.mean([r.std_runtime for r in methods[method]])
            runtimes.append(mean_runtime)
            runtime_errors.append(std_runtime)

        ax3.bar(method_names, runtimes, yerr=runtime_errors,
               color='lightcoral', edgecolor='black', alpha=0.8, capsize=5)

        ax3.set_ylabel('Runtime (seconds)', fontsize=11)
        ax3.set_title('Computational Efficiency', fontsize=13, fontweight='bold')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, alpha=0.3, axis='y')

        # 4. Evaluations comparison
        ax4 = fig.add_subplot(gs[1, 1])

        evaluations = []
        for method in method_names:
            mean_evals = np.mean([r.mean_evaluations for r in methods[method]])
            evaluations.append(mean_evals)

        ax4.bar(method_names, evaluations, color='lightgreen',
               edgecolor='black', alpha=0.8)

        ax4.set_ylabel('Number of Evaluations', fontsize=11)
        ax4.set_title('Function Evaluations Required', fontsize=13, fontweight='bold')
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3, axis='y')

        plt.suptitle(f'Optimization Methods Comparison{" - " + function_name if function_name else ""}',
                    fontsize=15, fontweight='bold', y=0.995)

        if save_path:
            fig.savefig(save_path, dpi=100, bbox_inches='tight')
            logger.info(f"Comparison plot saved to {save_path}")

        return fig

    def _save_results(self) -> None:
        """Save benchmark results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save raw results
        raw_results = [asdict(r) for r in self.results]
        raw_path = Path(self.config.output_dir) / f"benchmark_raw_{timestamp}.json"
        with open(raw_path, 'w') as f:
            json.dump(raw_results, f, indent=2, default=str)

        # Save aggregated results
        agg_results = {k: v.to_dict() for k, v in self.aggregated_results.items()}
        agg_path = Path(self.config.output_dir) / f"benchmark_aggregated_{timestamp}.json"
        with open(agg_path, 'w') as f:
            json.dump(agg_results, f, indent=2, default=str)

        # Save leaderboard
        leaderboard = self.generate_leaderboard()
        leaderboard_path = Path(self.config.output_dir) / f"leaderboard_{timestamp}.csv"
        leaderboard.to_csv(leaderboard_path, index=False)

        logger.info(f"Results saved to {self.config.output_dir}")

    def load_results(self, filepath: str) -> None:
        """
        Load benchmark results from file

        Args:
            filepath: Path to results JSON file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Reconstruct results
        self.results = [
            BenchmarkResult(**r) if isinstance(r, dict) else r
            for r in data
        ]

        logger.info(f"Loaded {len(self.results)} results from {filepath}")


# Standard benchmark functions
def sphere(x: np.ndarray) -> float:
    """Sphere function - smooth, convex, single global minimum at 0"""
    return np.sum(x ** 2)


def rosenbrock(x: np.ndarray) -> float:
    """Rosenbrock function - non-convex, valley-shaped"""
    return np.sum(100 * (x[1:] - x[:-1] ** 2) ** 2 + (1 - x[:-1]) ** 2)


def rastrigin(x: np.ndarray) -> float:
    """Rastrigin function - highly multi-modal, many local optima"""
    n = len(x)
    return 10 * n + np.sum(x ** 2 - 10 * np.cos(2 * np.pi * x))


def ackley(x: np.ndarray) -> float:
    """Ackley function - multi-modal with many local optima"""
    n = len(x)
    sum1 = np.sum(x ** 2)
    sum2 = np.sum(np.cos(2 * np.pi * x))
    term1 = -20 * np.exp(-0.2 * np.sqrt(sum1 / n))
    term2 = -np.exp(sum2 / n)
    return term1 + term2 + 20 + np.e


def griewank(x: np.ndarray) -> float:
    """Griewank function - multi-modal"""
    sum_part = np.sum(x ** 2) / 4000
    prod_part = np.prod(np.cos(x / np.sqrt(np.arange(1, len(x) + 1))))
    return sum_part - prod_part + 1


def schwefel(x: np.ndarray) -> float:
    """Schwefel function - highly multi-modal, deceptive"""
    n = len(x)
    return 418.9829 * n - np.sum(x * np.sin(np.sqrt(np.abs(x))))


def create_standard_benchmarks() -> List[BenchmarkFunction]:
    """
    Create standard benchmark function suite

    Returns:
        List of benchmark functions
    """
    benchmarks = [
        # 2D problems
        BenchmarkFunction(
            name="sphere_2d",
            func=sphere,
            bounds=[(-5.12, 5.12), (-5.12, 5.12)],
            global_optimum=0.0,
            global_optimum_location=[0.0, 0.0],
            problem_type=ProblemType.CONVEX,
            dimensions=2,
            description="Simple convex function with single global minimum"
        ),
        BenchmarkFunction(
            name="rosenbrock_2d",
            func=rosenbrock,
            bounds=[(-2.048, 2.048), (-2.048, 2.048)],
            global_optimum=0.0,
            global_optimum_location=[1.0, 1.0],
            problem_type=ProblemType.NON_CONVEX,
            dimensions=2,
            description="Classic non-convex optimization test function"
        ),
        BenchmarkFunction(
            name="rastrigin_2d",
            func=rastrigin,
            bounds=[(-5.12, 5.12), (-5.12, 5.12)],
            global_optimum=0.0,
            global_optimum_location=[0.0, 0.0],
            problem_type=ProblemType.MULTI_MODAL,
            dimensions=2,
            description="Highly multi-modal function with many local optima"
        ),
        BenchmarkFunction(
            name="ackley_2d",
            func=ackley,
            bounds=[(-32.768, 32.768), (-32.768, 32.768)],
            global_optimum=0.0,
            global_optimum_location=[0.0, 0.0],
            problem_type=ProblemType.MULTI_MODAL,
            dimensions=2,
            description="Multi-modal function with exponential terms"
        ),
        BenchmarkFunction(
            name="griewank_2d",
            func=griewank,
            bounds=[(-600, 600), (-600, 600)],
            global_optimum=0.0,
            global_optimum_location=[0.0, 0.0],
            problem_type=ProblemType.MULTI_MODAL,
            dimensions=2,
            description="Multi-modal function with product term"
        ),
        BenchmarkFunction(
            name="schwefel_2d",
            func=schwefel,
            bounds=[(-500, 500), (-500, 500)],
            global_optimum=0.0,
            global_optimum_location=[420.97, 420.97],
            problem_type=ProblemType.MULTI_MODAL,
            dimensions=2,
            description="Deceptive multi-modal function"
        ),
    ]

    return benchmarks


__all__ = [
    'PerformanceBenchmark',
    'BenchmarkFunction',
    'BenchmarkConfig',
    'BenchmarkResult',
    'AggregateBenchmarkResult',
    'ProblemType',
    'create_standard_benchmarks'
]
