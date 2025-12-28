"""
Performance Comparison Test - Optimized vs Original
====================================================

Tests the performance improvements from:
1. Parallel objective function evaluation
2. Reduced copy operations
3. Vectorized PSO operations
4. Optimized result aggregation

Author: CBSC Quant Team
Version: 1.0.0
"""

import sys
import os
import time
from typing import Dict, List, Any
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import modules
try:
    from parameter_optimizer import (
        ParameterOptimizer,
        ParameterSpace,
        OptimizationConfig,
        OptimizationMethod
    )
    OPTIMIZER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import parameter_optimizer: {e}")
    OPTIMIZER_AVAILABLE = False

try:
    from performance_optimizer import (
        OptimizedParameterOptimizer,
        ParallelConfig
    )
    PERFORMANCE_OPTIMIZER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import performance_optimizer: {e}")
    PERFORMANCE_OPTIMIZER_AVAILABLE = False


class PerformanceComparisonTest:
    """Compare original vs optimized optimizer performance"""

    def __init__(self):
        self.results = {}

    # ========================================
    # Test Objective Functions
    # ========================================

    @staticmethod
    def sphere_objective(params: Dict[str, Any], data: Any) -> float:
        """Simple 2D sphere function: -(x^2 + y^2)"""
        return -(params['x']**2 + params['y']**2)

    @staticmethod
    def rosenbrock_objective(params: Dict[str, Any], data: Any) -> float:
        """Rosenbrock function"""
        x = params['x']
        y = params['y']
        return -((1 - x)**2 + 100 * (y - x**2)**2)

    # ========================================
    # Test 1: Grid Search Performance
    # ========================================

    def test_grid_search_performance(self):
        """Compare grid search performance"""
        print("\n" + "="*70)
        print("TEST 1: Grid Search Performance Comparison")
        print("="*70)

        if not OPTIMIZER_AVAILABLE or not PERFORMANCE_OPTIMIZER_AVAILABLE:
            print("Skipped: Required modules not available")
            return

        # Setup parameter spaces
        param_spaces = [
            ParameterSpace(name='x', param_type='continuous', bounds=(-5, 5)),
            ParameterSpace(name='y', param_type='continuous', bounds=(-5, 5))
        ]

        # Original optimizer (serial)
        config_original = OptimizationConfig(
            method=OptimizationMethod.GRID_SEARCH,
            max_iterations=100,
            random_state=42
        )
        original_optimizer = ParameterOptimizer(config_original)
        for ps in param_spaces:
            original_optimizer.add_parameter(ps)

        start_time = time.time()
        original_result = original_optimizer.optimize(self.sphere_objective, None)
        original_time = time.time() - start_time

        # Optimized optimizer (parallel)
        config_optimized = OptimizationConfig(
            method=OptimizationMethod.GRID_SEARCH,
            max_iterations=100,
            random_state=42
        )
        parallel_config = ParallelConfig(n_jobs=-1)  # Use all cores
        optimized_optimizer = OptimizedParameterOptimizer(
            param_spaces,
            config_optimized,
            parallel_config
        )

        start_time = time.time()
        optimized_result = optimized_optimizer.parallel_grid_search(self.sphere_objective, None)
        optimized_time = time.time() - start_time

        # Calculate speedup
        speedup = original_time / optimized_time if optimized_time > 0 else 0

        print(f"\nOriginal Optimizer:")
        print(f"  Time: {original_time:.4f}s")
        print(f"  Best Score: {original_result.best_score:.6f}")
        print(f"  Evaluations: {original_result.n_evaluations}")

        print(f"\nOptimized Optimizer (Parallel):")
        print(f"  Time: {optimized_time:.4f}s")
        print(f"  Best Score: {optimized_result.best_score:.6f}")
        print(f"  Evaluations: {optimized_result.n_evaluations}")

        print(f"\nSpeedup: {speedup:.2f}x")

        self.results['grid_search'] = {
            'original_time': original_time,
            'optimized_time': optimized_time,
            'speedup': speedup,
            'original_score': original_result.best_score,
            'optimized_score': optimized_result.best_score
        }

    # ========================================
    # Test 2: PSO Vectorization Performance
    # ========================================

    def test_pso_performance(self):
        """Compare PSO performance (vectorized vs original)"""
        print("\n" + "="*70)
        print("TEST 2: PSO Vectorization Performance Comparison")
        print("="*70)

        if not OPTIMIZER_AVAILABLE or not PERFORMANCE_OPTIMIZER_AVAILABLE:
            print("Skipped: Required modules not available")
            return

        # Setup parameter spaces
        param_spaces = [
            ParameterSpace(name='x', param_type='continuous', bounds=(-5, 5)),
            ParameterSpace(name='y', param_type='continuous', bounds=(-5, 5))
        ]

        # Original PSO
        config_original = OptimizationConfig(
            method=OptimizationMethod.PARTICLE_SWARM,
            max_iterations=300,
            random_state=42
        )
        original_optimizer = ParameterOptimizer(config_original)
        for ps in param_spaces:
            original_optimizer.add_parameter(ps)

        start_time = time.time()
        original_result = original_optimizer.optimize(self.sphere_objective, None)
        original_time = time.time() - start_time

        # Optimized PSO (vectorized)
        config_optimized = OptimizationConfig(
            method=OptimizationMethod.PARTICLE_SWARM,
            max_iterations=300,
            random_state=42
        )
        parallel_config = ParallelConfig(n_jobs=1)  # Single-core for fair comparison
        optimized_optimizer = OptimizedParameterOptimizer(
            param_spaces,
            config_optimized,
            parallel_config
        )

        start_time = time.time()
        optimized_result = optimized_optimizer.vectorized_pso_optimize(self.sphere_objective, None)
        optimized_time = time.time() - start_time

        # Calculate speedup
        speedup = original_time / optimized_time if optimized_time > 0 else 0

        print(f"\nOriginal PSO:")
        print(f"  Time: {original_time:.4f}s")
        print(f"  Best Score: {original_result.best_score:.6f}")

        print(f"\nOptimized PSO (Vectorized):")
        print(f"  Time: {optimized_time:.4f}s")
        print(f"  Best Score: {optimized_result.best_score:.6f}")

        print(f"\nSpeedup: {speedup:.2f}x")

        self.results['pso'] = {
            'original_time': original_time,
            'optimized_time': optimized_time,
            'speedup': speedup,
            'original_score': original_result.best_score,
            'optimized_score': optimized_result.best_score
        }

    # ========================================
    # Test 3: Memory Usage Comparison
    # ========================================

    def test_memory_usage(self):
        """Compare memory usage between original and optimized"""
        print("\n" + "="*70)
        print("TEST 3: Memory Usage Comparison")
        print("="*70)

        if not OPTIMIZER_AVAILABLE or not PERFORMANCE_OPTIMIZER_AVAILABLE:
            print("Skipped: Required modules not available")
            return

        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            print("Skipped: psutil not available")
            return

        # Setup parameter spaces
        param_spaces = [
            ParameterSpace(name='x', param_type='continuous', bounds=(-5, 5)),
            ParameterSpace(name='y', param_type='continuous', bounds=(-5, 5)),
            ParameterSpace(name='z', param_type='continuous', bounds=(-5, 5))
        ]

        # Original optimizer memory
        config = OptimizationConfig(
            method=OptimizationMethod.GRID_SEARCH,
            max_iterations=50,
            random_state=42
        )

        # Measure original memory
        original_optimizer = ParameterOptimizer(config)
        for ps in param_spaces:
            original_optimizer.add_parameter(ps)

        mem_before = process.memory_info().rss / 1024 / 1024
        original_optimizer.optimize(self.sphere_objective, None)
        mem_after_original = process.memory_info().rss / 1024 / 1024
        original_memory = mem_after_original - mem_before

        # Measure optimized memory
        parallel_config = ParallelConfig(n_jobs=1)
        optimized_optimizer = OptimizedParameterOptimizer(
            param_spaces,
            config,
            parallel_config
        )

        mem_before = process.memory_info().rss / 1024 / 1024
        optimized_optimizer.parallel_grid_search(self.sphere_objective, None)
        mem_after_optimized = process.memory_info().rss / 1024 / 1024
        optimized_memory = mem_after_optimized - mem_before

        # Calculate improvement
        memory_reduction = (original_memory - optimized_memory) / original_memory * 100

        print(f"\nOriginal Optimizer Memory:")
        print(f"  Used: {original_memory:.2f} MB")

        print(f"\nOptimized Optimizer Memory:")
        print(f"  Used: {optimized_memory:.2f} MB")

        print(f"\nMemory Reduction: {memory_reduction:.1f}%")

        self.results['memory'] = {
            'original_mb': original_memory,
            'optimized_mb': optimized_memory,
            'reduction_percent': memory_reduction
        }

    # ========================================
    # Summary
    # ========================================

    def print_summary(self):
        """Print performance comparison summary"""
        print("\n" + "="*70)
        print("PERFORMANCE COMPARISON SUMMARY")
        print("="*70)

        if 'grid_search' in self.results:
            print(f"\nGrid Search:")
            print(f"  Speedup: {self.results['grid_search']['speedup']:.2f}x")
            print(f"  Original: {self.results['grid_search']['original_time']:.4f}s")
            print(f"  Optimized: {self.results['grid_search']['optimized_time']:.4f}s")

        if 'pso' in self.results:
            print(f"\nParticle Swarm Optimization:")
            print(f"  Speedup: {self.results['pso']['speedup']:.2f}x")
            print(f"  Original: {self.results['pso']['original_time']:.4f}s")
            print(f"  Optimized: {self.results['pso']['optimized_time']:.4f}s")

        if 'memory' in self.results:
            print(f"\nMemory Usage:")
            print(f"  Reduction: {self.results['memory']['reduction_percent']:.1f}%")
            print(f"  Original: {self.results['memory']['original_mb']:.2f} MB")
            print(f"  Optimized: {self.results['memory']['optimized_mb']:.2f} MB")

        # Overall summary
        avg_speedup = 0
        speedup_count = 0
        if 'grid_search' in self.results:
            avg_speedup += self.results['grid_search']['speedup']
            speedup_count += 1
        if 'pso' in self.results:
            avg_speedup += self.results['pso']['speedup']
            speedup_count += 1

        if speedup_count > 0:
            avg_speedup /= speedup_count
            print(f"\n{'='*70}")
            print(f"Average Speedup: {avg_speedup:.2f}x")
            print(f"{'='*70}")


if __name__ == "__main__":
    tester = PerformanceComparisonTest()

    print("CBSC Parameter Optimizer - Performance Comparison Test")
    print("="*70)

    # Run tests
    tester.test_grid_search_performance()
    tester.test_pso_performance()
    tester.test_memory_usage()

    # Print summary
    tester.print_summary()
