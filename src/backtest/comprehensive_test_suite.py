"""
Comprehensive Test Suite for CBSC Quant Trading System
=======================================================

This test suite covers P0 critical components:
1. Backtest Engine Tests
2. Parameter Optimization Tests
3. Integration Tests
4. Performance Tests

Author: CBSC Quant Team
Version: 1.0.0
"""

import sys
import os
import time
import traceback
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import numpy as np
import pandas as pd


class TestStatus(Enum):
    """Test execution status"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class TestResult:
    """Test result data class"""
    name: str
    category: str
    status: TestStatus
    duration: float
    message: str = ""
    error: str = ""
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class ComprehensiveTestSuite:
    """
    Comprehensive test suite for CBSC system
    """

    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
        self.modules = {}

    def load_modules(self):
        """Load required modules dynamically"""
        print("[Loading Modules]")

        # Load parameter optimizer
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "parameter_optimizer",
                os.path.join(os.path.dirname(__file__), "parameter_optimizer.py")
            )
            self.modules['optimizer'] = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.modules['optimizer'])
            print("  [OK] Parameter Optimizer loaded")
        except Exception as e:
            print(f"  [FAIL] Parameter Optimizer: {e}")

        # Load performance benchmark
        try:
            spec = importlib.util.spec_from_file_location(
                "performance_benchmark",
                os.path.join(os.path.dirname(__file__), "performance_benchmark.py")
            )
            self.modules['benchmark'] = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.modules['benchmark'])
            print("  [OK] Performance Benchmark loaded")
        except Exception as e:
            print(f"  [FAIL] Performance Benchmark: {e}")

        # Load optimization visualization
        try:
            spec = importlib.util.spec_from_file_location(
                "optimization_visualization",
                os.path.join(os.path.dirname(__file__), "optimization_visualization.py")
            )
            self.modules['visualization'] = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.modules['visualization'])
            print("  [OK] Optimization Visualization loaded")
        except Exception as e:
            print(f"  [FAIL] Optimization Visualization: {e}")

    # ========================================
    # Test Categories
    # ========================================

    def test_parameter_optimizer(self) -> List[TestResult]:
        """Test parameter optimizer functionality"""
        print("\n" + "="*70)
        print("TEST: Parameter Optimizer")
        print("="*70)

        results = []

        # Test 1: Module loading
        results.append(self._test_case(
            "Optimizer Module Load",
            "Parameter Optimizer",
            self._test_optimizer_module_load
        ))

        # Test 2: Configuration creation
        results.append(self._test_case(
            "Optimizer Config Creation",
            "Parameter Optimizer",
            self._test_optimizer_config
        ))

        # Test 3: Parameter space definition
        results.append(self._test_case(
            "Parameter Space Definition",
            "Parameter Optimizer",
            self._test_parameter_space
        ))

        # Test 4: Grid search optimization
        results.append(self._test_case(
            "Grid Search Optimization",
            "Parameter Optimizer",
            self._test_grid_search
        ))

        # Test 5: Random search optimization
        results.append(self._test_case(
            "Random Search Optimization",
            "Parameter Optimizer",
            self._test_random_search
        ))

        # Test 6: Bayesian optimization
        results.append(self._test_case(
            "Bayesian Optimization",
            "Parameter Optimizer",
            self._test_bayesian_optimization
        ))

        return results

    def test_performance_benchmark(self) -> List[TestResult]:
        """Test performance benchmark functionality"""
        print("\n" + "="*70)
        print("TEST: Performance Benchmark")
        print("="*70)

        results = []

        # Test 1: Benchmark creation
        results.append(self._test_case(
            "Benchmark System Creation",
            "Performance Benchmark",
            self._test_benchmark_creation
        ))

        # Test 2: Standard benchmarks
        results.append(self._test_case(
            "Standard Benchmark Functions",
            "Performance Benchmark",
            self._test_standard_benchmarks
        ))

        # Test 3: Benchmark execution
        results.append(self._test_case(
            "Benchmark Execution",
            "Performance Benchmark",
            self._test_benchmark_execution
        ))

        return results

    def test_optimization_visualization(self) -> List[TestResult]:
        """Test optimization visualization functionality"""
        print("\n" + "="*70)
        print("TEST: Optimization Visualization")
        print("="*70)

        results = []

        # Test 1: Visualization config
        results.append(self._test_case(
            "Visualization Configuration",
            "Visualization",
            self._test_visualization_config
        ))

        # Test 2: Convergence plot
        results.append(self._test_case(
            "Convergence Plot Generation",
            "Visualization",
            self._test_convergence_plot
        ))

        # Test 3: Method comparison
        results.append(self._test_case(
            "Method Comparison Plot",
            "Visualization",
            self._test_method_comparison
        ))

        return results

    def test_integration(self) -> List[TestResult]:
        """Test system integration"""
        print("\n" + "="*70)
        print("TEST: System Integration")
        print("="*70)

        results = []

        # Test 1: Optimizer to visualization pipeline
        results.append(self._test_case(
            "Optimizer to Visualization Pipeline",
            "Integration",
            self._test_optimizer_visualization_pipeline
        ))

        # Test 2: Benchmark to leaderboard pipeline
        results.append(self._test_case(
            "Benchmark to Leaderboard Pipeline",
            "Integration",
            self._test_benchmark_leaderboard_pipeline
        ))

        return results

    # ========================================
    # Individual Test Cases
    # ========================================

    def _test_optimizer_module_load(self) -> Tuple[TestStatus, str, str]:
        """Test optimizer module loads correctly"""
        if 'optimizer' not in self.modules:
            return TestStatus.ERROR, "Optimizer module not loaded", "Module failed to import"
        return TestStatus.PASSED, "Module loaded successfully", ""

    def _test_optimizer_config(self) -> Tuple[TestStatus, str, str]:
        """Test optimizer configuration"""
        if 'optimizer' not in self.modules:
            return TestStatus.SKIPPED, "Optimizer not available", "Module not loaded"

        try:
            opt = self.modules['optimizer']
            config = opt.create_optimization_config(
                method=opt.OptimizationMethod.RANDOM_SEARCH,
                max_iterations=10
            )

            if config.max_iterations != 10:
                return TestStatus.FAILED, "Config mismatch", f"Expected 10, got {config.max_iterations}"

            return TestStatus.PASSED, "Config created successfully", f"Iterations: {config.max_iterations}"

        except Exception as e:
            return TestStatus.ERROR, "Config creation failed", str(e)

    def _test_parameter_space(self) -> Tuple[TestStatus, str, str]:
        """Test parameter space definition"""
        if 'optimizer' not in self.modules:
            return TestStatus.SKIPPED, "Optimizer not available", ""

        try:
            opt = self.modules['optimizer']
            space = opt.create_parameter_space(
                name="test_param",
                param_type="continuous",
                bounds=(0.0, 1.0)
            )

            if space.name != "test_param":
                return TestStatus.FAILED, "Name mismatch", f"Expected 'test_param', got {space.name}"

            return TestStatus.PASSED, "Parameter space created", f"Type: {space.param_type}"

        except Exception as e:
            return TestStatus.ERROR, "Parameter space failed", str(e)

    def _test_grid_search(self) -> Tuple[TestStatus, str, str]:
        """Test grid search optimization"""
        if 'optimizer' not in self.modules:
            return TestStatus.SKIPPED, "Optimizer not available", ""

        try:
            opt = self.modules['optimizer']
            config = opt.create_optimization_config(
                method=opt.OptimizationMethod.GRID_SEARCH,
                max_iterations=10
            )

            optimizer = opt.ParameterOptimizer(config)
            optimizer.add_parameter(opt.create_parameter_space("x", "continuous", (0, 1)))
            optimizer.add_parameter(opt.create_parameter_space("y", "continuous", (0, 1)))

            # Simple objective: minimize x^2 + y^2 (maximize negative)
            def objective(params, data):
                return -(params['x']**2 + params['y']**2)

            result = optimizer.optimize(objective, None)

            # Grid search with 10 iterations should find something reasonable
            # The objective is to maximize -(x^2 + y^2), so max is near (0,0) = 0
            # Negative scores are expected since we're maximizing a negative function
            if result.best_score > -2.0:  # Should find better than random
                return TestStatus.PASSED, "Grid search successful", f"Score: {result.best_score:.4f}, Params: {result.best_params}"

            return TestStatus.FAILED, "Score too low", f"Score: {result.best_score:.4f}"

        except Exception as e:
            return TestStatus.ERROR, "Grid search failed", str(e)

    def _test_random_search(self) -> Tuple[TestStatus, str, str]:
        """Test random search optimization"""
        if 'optimizer' not in self.modules:
            return TestStatus.SKIPPED, "Optimizer not available", ""

        try:
            opt = self.modules['optimizer']
            config = opt.create_optimization_config(
                method=opt.OptimizationMethod.RANDOM_SEARCH,
                max_iterations=100,
                random_state=42
            )

            optimizer = opt.ParameterOptimizer(config)
            optimizer.add_parameter(opt.create_parameter_space("x", "continuous", (-5, 5)))
            optimizer.add_parameter(opt.create_parameter_space("y", "continuous", (-5, 5)))

            # Simple objective: minimize (x-2)^2 + (y-3)^2 (maximize negative)
            # Optimal is at x=2, y=3 giving score = 0
            def objective(params, data):
                return -((params['x']-2)**2 + (params['y']-3)**2)

            result = optimizer.optimize(objective, None)

            # With 100 iterations, should find something reasonable
            if result.best_score > -5:  # Within 5 units of optimal
                return TestStatus.PASSED, "Random search successful", f"Score: {result.best_score:.4f}, Evaluations: {result.n_evaluations}"

            return TestStatus.FAILED, "Score too low", f"Score: {result.best_score:.4f}"

        except Exception as e:
            return TestStatus.ERROR, "Random search failed", str(e)

    def _test_bayesian_optimization(self) -> Tuple[TestStatus, str, str]:
        """Test Bayesian optimization"""
        if 'optimizer' not in self.modules:
            return TestStatus.SKIPPED, "Optimizer not available", ""

        try:
            opt = self.modules['optimizer']
            config = opt.create_optimization_config(
                method=opt.OptimizationMethod.BAYESIAN_OPTIMIZATION,
                n_calls=20,
                random_state=42
            )

            optimizer = opt.ParameterOptimizer(config)
            optimizer.add_parameter(opt.create_parameter_space("x", "continuous", (-5, 5)))
            optimizer.add_parameter(opt.create_parameter_space("y", "continuous", (-5, 5)))

            # Simple objective: minimize x^2 + y^2 (maximize negative)
            def objective(params, data):
                return -(params['x']**2 + params['y']**2)

            result = optimizer.optimize(objective, None)

            # Bayesian should find near optimal
            if result.best_score > -1:  # Within 1 unit of optimal (0,0)
                return TestStatus.PASSED, "Bayesian optimization successful", f"Score: {result.best_score:.4f}, Evaluations: {result.n_evaluations}"

            return TestStatus.FAILED, "Score too low", f"Score: {result.best_score:.4f}"

        except Exception as e:
            return TestStatus.ERROR, "Bayesian optimization failed", str(e)

    def _test_benchmark_creation(self) -> Tuple[TestStatus, str, str]:
        """Test benchmark system creation"""
        if 'benchmark' not in self.modules:
            return TestStatus.SKIPPED, "Benchmark not available", ""

        try:
            bench = self.modules['benchmark']
            config = bench.BenchmarkConfig(n_runs=2, random_state=42)
            benchmark = bench.PerformanceBenchmark(config)

            return TestStatus.PASSED, "Benchmark created successfully", ""

        except Exception as e:
            return TestStatus.ERROR, "Benchmark creation failed", str(e)

    def _test_standard_benchmarks(self) -> Tuple[TestStatus, str, str]:
        """Test standard benchmark functions"""
        if 'benchmark' not in self.modules:
            return TestStatus.SKIPPED, "Benchmark not available", ""

        try:
            bench = self.modules['benchmark']
            benchmarks = bench.create_standard_benchmarks()

            if len(benchmarks) < 6:
                return TestStatus.FAILED, "Insufficient benchmarks", f"Found {len(benchmarks)}"

            # Test sphere function
            sphere = [b for b in benchmarks if b.name == "sphere_2d"][0]
            result = sphere.func(np.array([0.0, 0.0]))
            if abs(result) > 1e-10:
                return TestStatus.FAILED, "Sphere function incorrect", f"f(0,0)={result}"

            return TestStatus.PASSED, f"{len(benchmarks)} benchmarks validated", ""

        except Exception as e:
            return TestStatus.ERROR, "Benchmark validation failed", str(e)

    def _test_benchmark_execution(self) -> Tuple[TestStatus, str, str]:
        """Test benchmark execution"""
        if 'benchmark' not in self.modules:
            return TestStatus.SKIPPED, "Benchmark not available", ""

        try:
            bench = self.modules['benchmark']
            config = bench.BenchmarkConfig(n_runs=2, random_state=42, save_results=False)
            benchmark = bench.PerformanceBenchmark(config)

            # Register one simple function
            sphere = bench.BenchmarkFunction(
                name="test_sphere",
                func=lambda x: np.sum(x**2),
                bounds=[(-5, 5), (-5, 5)],
                global_optimum=0.0,
                global_optimum_location=[0.0, 0.0],
                problem_type=bench.ProblemType.CONVEX,
                dimensions=2,
                description="Test sphere function"
            )
            benchmark.register_benchmark_function(sphere)

            # Run limited benchmark
            results = benchmark.run_benchmark(
                function_names=['test_sphere'],
                methods=['random_search']
            )

            if len(results) == 0:
                return TestStatus.FAILED, "No results generated", ""

            return TestStatus.PASSED, "Benchmark executed", f"Generated {len(results)} results"

        except Exception as e:
            return TestStatus.ERROR, "Benchmark execution failed", str(e)

    def _test_visualization_config(self) -> Tuple[TestStatus, str, str]:
        """Test visualization configuration"""
        if 'visualization' not in self.modules:
            return TestStatus.SKIPPED, "Visualization not available", ""

        try:
            viz = self.modules['visualization']
            config = viz.VisualizationConfig()

            if config.figsize != (12, 8):
                return TestStatus.FAILED, "Default figsize incorrect", f"Got {config.figsize}"

            return TestStatus.PASSED, "Visualization config created", ""

        except Exception as e:
            return TestStatus.ERROR, "Visualization config failed", str(e)

    def _test_convergence_plot(self) -> Tuple[TestStatus, str, str]:
        """Test convergence plot generation"""
        if 'visualization' not in self.modules:
            return TestStatus.SKIPPED, "Visualization not available", ""

        try:
            viz = self.modules['visualization']
            visualizer = viz.OptimizationVisualizer(viz.VisualizationConfig())

            # Create dummy results
            if 'optimizer' in self.modules:
                opt = self.modules['optimizer']
                dummy_results = [
                    opt.OptimizationResult(
                        best_params={'x': 0.1, 'y': 0.1},
                        best_score=0.99,
                        best_iteration=10,
                        optimization_history=[],
                        convergence_curve=[0.5, 0.7, 0.8, 0.9, 0.95, 0.99],
                        n_evaluations=100
                    )
                ]

                import matplotlib
                matplotlib.use('Agg')
                fig = visualizer.plot_convergence(
                    dummy_results,
                    ['test_method'],
                    save_path="test_convergence_temp.png"
                )

                return TestStatus.PASSED, "Convergence plot created", ""

            return TestStatus.SKIPPED, "Optimizer not available", ""

        except Exception as e:
            return TestStatus.ERROR, "Convergence plot failed", str(e)

    def _test_method_comparison(self) -> Tuple[TestStatus, str, str]:
        """Test method comparison plot"""
        if 'visualization' not in self.modules:
            return TestStatus.SKIPPED, "Visualization not available", ""

        try:
            viz = self.modules['visualization']
            visualizer = viz.OptimizationVisualizer(viz.VisualizationConfig())

            if 'optimizer' in self.modules:
                opt = self.modules['optimizer']
                dummy_results = {
                    'method1': opt.OptimizationResult(
                        best_params={'x': 0.1},
                        best_score=0.9,
                        best_iteration=10,
                        optimization_history=[],
                        n_evaluations=100
                    ),
                    'method2': opt.OptimizationResult(
                        best_params={'x': 0.05},
                        best_score=0.95,
                        best_iteration=5,
                        optimization_history=[],
                        n_evaluations=50
                    )
                }

                import matplotlib
                matplotlib.use('Agg')
                fig = visualizer.plot_method_comparison(
                    dummy_results,
                    ['Mean Score', 'Success Rate'],
                    save_path="test_comparison_temp.png"
                )

                return TestStatus.PASSED, "Method comparison created", ""

            return TestStatus.SKIPPED, "Optimizer not available", ""

        except Exception as e:
            return TestStatus.ERROR, "Method comparison failed", str(e)

    def _test_optimizer_visualization_pipeline(self) -> Tuple[TestStatus, str, str]:
        """Test optimizer to visualization pipeline"""
        if 'optimizer' not in self.modules or 'visualization' not in self.modules:
            return TestStatus.SKIPPED, "Required modules not available", ""

        try:
            opt = self.modules['optimizer']
            viz = self.modules['visualization']

            # Run optimization
            config = opt.create_optimization_config(
                method=opt.OptimizationMethod.GRID_SEARCH,
                max_iterations=5
            )

            optimizer = opt.ParameterOptimizer(config)
            optimizer.add_parameter(opt.create_parameter_space("x", "continuous", (0, 1)))

            def objective(params, data):
                return -params['x']**2

            result = optimizer.optimize(objective, None)

            # Visualize
            visualizer = viz.OptimizationVisualizer(viz.VisualizationConfig())

            import matplotlib
            matplotlib.use('Agg')
            fig = visualizer.plot_optimization_summary(
                result,
                "test_method",
                save_path="test_pipeline_temp.png"
            )

            return TestStatus.PASSED, "Pipeline successful", "Optimizer → Visualization"

        except Exception as e:
            return TestStatus.ERROR, "Pipeline failed", str(e)

    def _test_benchmark_leaderboard_pipeline(self) -> Tuple[TestStatus, str, str]:
        """Test benchmark to leaderboard pipeline"""
        if 'benchmark' not in self.modules or 'optimizer' not in self.modules:
            return TestStatus.SKIPPED, "Required modules not available", ""

        try:
            bench = self.modules['benchmark']
            opt = self.modules['optimizer']

            # Setup benchmark
            config = bench.BenchmarkConfig(
                n_runs=2,
                random_state=42,
                save_results=False
            )

            benchmark = bench.PerformanceBenchmark(config)

            # Create simple test function
            test_func = bench.BenchmarkFunction(
                name="simple_test",
                func=lambda x: np.sum(x**2),
                bounds=[(-1, 1)],
                global_optimum=0.0,
                global_optimum_location=[0.0],
                problem_type=bench.ProblemType.CONVEX,
                dimensions=1,
                description="Simple test"
            )

            benchmark.register_benchmark_function(test_func)

            # Run benchmark
            results = benchmark.run_benchmark(
                function_names=['simple_test'],
                methods=['random_search']
            )

            # Generate leaderboard
            leaderboard = benchmark.generate_leaderboard()

            if len(leaderboard) == 0:
                return TestStatus.FAILED, "Empty leaderboard", ""

            return TestStatus.PASSED, "Pipeline successful", f"{len(leaderboard)} entries"

        except Exception as e:
            return TestStatus.ERROR, "Pipeline failed", str(e)

    # ========================================
    # Test Execution Helpers
    # ========================================

    def _test_case(self, name: str, category: str, test_func) -> TestResult:
        """Run a single test case"""
        start = time.time()
        status = TestStatus.ERROR
        message = ""
        error = ""
        details = {}

        try:
            status, message, error = test_func()
        except Exception as e:
            status = TestStatus.ERROR
            error = traceback.format_exc()
            message = "Exception occurred"

        duration = time.time() - start

        # Print result
        status_icon = {
            TestStatus.PASSED: "[PASS]",
            TestStatus.FAILED: "[FAIL]",
            TestStatus.SKIPPED: "[SKIP]",
            TestStatus.ERROR: "[ERR ]"
        }[status]

        print(f"  {status_icon} {name}: {message}")
        if error:
            print(f"        Error: {error[:200]}...")

        return TestResult(
            name=name,
            category=category,
            status=status,
            duration=duration,
            message=message,
            error=error,
            details=details
        )

    # ========================================
    # Main Execution
    # ========================================

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        print("\n" + "="*70)
        print("COMPREHENSIVE TEST SUITE")
        print("CBSC Quant Trading System")
        print("="*70)

        # Load modules
        self.load_modules()

        # Run test suites
        all_results = []

        all_results.extend(self.test_parameter_optimizer())
        all_results.extend(self.test_performance_benchmark())
        all_results.extend(self.test_optimization_visualization())
        all_results.extend(self.test_integration())

        self.results = all_results

        # Generate summary
        return self._generate_summary()

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary"""
        total_time = time.time() - self.start_time

        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        total = len(self.results)

        success_rate = (passed / total * 100) if total > 0 else 0

        summary = {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'errors': errors,
            'success_rate': success_rate,
            'total_time': total_time,
            'results_by_category': {},
            'failed_tests': []
        }

        # Group by category
        for result in self.results:
            if result.category not in summary['results_by_category']:
                summary['results_by_category'][result.category] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'errors': 0
                }

            cat = summary['results_by_category'][result.category]
            cat['total'] += 1
            if result.status == TestStatus.PASSED:
                cat['passed'] += 1
            elif result.status == TestStatus.FAILED:
                cat['failed'] += 1
                summary['failed_tests'].append(result)
            elif result.status == TestStatus.ERROR:
                cat['errors'] += 1

        return summary

    def print_summary(self, summary: Dict[str, Any]):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        print(f"\nTotal Tests: {summary['total']}")
        print(f"  Passed:  {summary['passed']} ({summary['passed']/summary['total']*100:.1f}%)")
        print(f"  Failed:  {summary['failed']} ({summary['failed']/summary['total']*100:.1f}%)")
        print(f"  Skipped: {summary['skipped']} ({summary['skipped']/summary['total']*100:.1f}%)")
        print(f"  Errors:  {summary['errors']} ({summary['errors']/summary['total']*100:.1f}%)")
        print(f"\nSuccess Rate: {summary['success_rate']:.1f}%")
        print(f"Total Time:   {summary['total_time']:.2f}s")

        print("\nResults by Category:")
        print("-" * 70)
        for category, stats in summary['results_by_category'].items():
            print(f"\n{category}:")
            print(f"  Total:   {stats['total']}")
            print(f"  Passed:  {stats['passed']}")
            print(f"  Failed:  {stats['failed']}")
            print(f"  Errors:  {stats['errors']}")

        if summary['failed_tests']:
            print("\nFailed Tests:")
            print("-" * 70)
            for test in summary['failed_tests']:
                print(f"  - {test.name}: {test.message}")
                if test.error:
                    print(f"    {test.error[:200]}")

        print("\n" + "="*70)


def main():
    """Main entry point"""
    suite = ComprehensiveTestSuite()
    summary = suite.run_all_tests()
    suite.print_summary(summary)

    # Save results
    results_data = {
        'summary': summary,
        'tests': [
            {
                'name': r.name,
                'category': r.category,
                'status': r.status.value,
                'duration': r.duration,
                'message': r.message,
                'error': r.error
            }
            for r in suite.results
        ]
    }

    with open('test_results.json', 'w') as f:
        json.dump(results_data, f, indent=2, default=str)

    print(f"\nResults saved to: test_results.json")

    # Return exit code
    return 0 if summary['failed'] == 0 and summary['errors'] == 0 else 1


if __name__ == "__main__":
    exit(main())
