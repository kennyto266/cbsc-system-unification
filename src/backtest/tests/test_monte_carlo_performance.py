"""
Monte Carlo Performance Benchmark Tests
======================================

Performance benchmarking for the enhanced Monte Carlo simulation system.
Tests scaling, parallelization efficiency, and VectorBT acceleration.

Author: Claude Code Assistant
Date: 2025-01-19
"""

import asyncio
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import psutil

# Import the enhanced Monte Carlo system
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_monte_carlo import (
    EnhancedMonteCarloSimulator,
    EnhancedMCConfig,
    SimulationMethod,
    run_enhanced_monte_carlo
)

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')


class MonteCarloPerformanceBenchmark:
    """Performance benchmarking suite for Monte Carlo simulations"""

    def __init__(self):
        """Initialize the benchmark suite"""
        self.results = {
            'scaling': [],
            'parallel_efficiency': [],
            'vectorbt_comparison': [],
            'memory_usage': []
        }

    def generate_test_data(self, n_days: int = 252, seed: int = 42) -> pd.Series:
        """Generate test returns data"""
        np.random.seed(seed)
        returns = pd.Series(
            np.random.normal(0.001, 0.02, n_days),
            index=pd.date_range(start='2023-01-01', periods=n_days, freq='D')
        )
        return returns

    async def benchmark_scaling(self) -> Dict[str, List]:
        """
        Benchmark simulation performance across different simulation counts
        """
        print("Benchmarking simulation scaling...")

        returns = self.generate_test_data()
        simulation_counts = [100, 500, 1000, 5000, 10000, 20000]

        results = {
            'n_simulations': [],
            'execution_time': [],
            'simulations_per_second': [],
            'memory_mb': []
        }

        for n_sim in simulation_counts:
            print(f"  Testing {n_sim} simulations...")

            # Monitor memory before
            process = psutil.Process()
            mem_before = process.memory_info().rss / 1024 / 1024  # MB

            # Run simulation
            config = EnhancedMCConfig(
                n_simulations=n_sim,
                time_horizon=252,
                n_workers=4,
                use_vectorbt=False
            )

            simulator = EnhancedMonteCarloSimulator(config)

            start_time = time.time()
            sim_results = await simulator.simulate_parallel(
                returns=returns,
                method=SimulationMethod.BOOTSTRAP,
                initial_capital=100000
            )
            execution_time = time.time() - start_time

            # Monitor memory after
            mem_after = process.memory_info().rss / 1024 / 1024  # MB

            # Store results
            results['n_simulations'].append(n_sim)
            results['execution_time'].append(execution_time)
            results['simulations_per_second'].append(n_sim / execution_time)
            results['memory_mb'].append(mem_after - mem_before)

            print(f"    Time: {execution_time:.2f}s, Rate: {n_sim/execution_time:.0f} sims/s")

        self.results['scaling'] = results
        return results

    async def benchmark_parallel_efficiency(self) -> Dict[str, List]:
        """
        Benchmark parallelization efficiency across different worker counts
        """
        print("\nBenchmarking parallel efficiency...")

        returns = self.generate_test_data()
        worker_counts = [1, 2, 4, 8, 16, min(32, mp.cpu_count())]
        n_simulations = 5000

        results = {
            'n_workers': [],
            'execution_time': [],
            'speedup': [],
            'efficiency': [],
            'cpu_usage': []
        }

        # Baseline with 1 worker
        baseline_time = None

        for n_workers in worker_counts:
            print(f"  Testing {n_workers} workers...")

            config = EnhancedMCConfig(
                n_simulations=n_simulations,
                time_horizon=252,
                n_workers=n_workers,
                use_vectorbt=False
            )

            simulator = EnhancedMonteCarloSimulator(config)

            # Monitor CPU usage during simulation
            cpu_before = psutil.cpu_percent(interval=0.1)

            start_time = time.time()
            sim_results = await simulator.simulate_parallel(
                returns=returns,
                method=SimulationMethod.BOOTSTRAP,
                initial_capital=100000
            )
            execution_time = time.time() - start_time

            cpu_after = psutil.cpu_percent(interval=0.1)
            cpu_usage = (cpu_before + cpu_after) / 2

            # Store results
            results['n_workers'].append(n_workers)
            results['execution_time'].append(execution_time)

            if baseline_time is None:
                baseline_time = execution_time
                results['speedup'].append(1.0)
                results['efficiency'].append(1.0)
            else:
                speedup = baseline_time / execution_time
                efficiency = speedup / n_workers
                results['speedup'].append(speedup)
                results['efficiency'].append(efficiency)

            results['cpu_usage'].append(cpu_usage)

            print(f"    Time: {execution_time:.2f}s, Speedup: {results['speedup'][-1]:.2f}x, Efficiency: {results['efficiency'][-1]:.2%}")

        self.results['parallel_efficiency'] = results
        return results

    async def benchmark_vectorbt_comparison(self) -> Dict[str, List]:
        """
        Compare performance between standard simulation and VectorBT-accelerated version
        """
        print("\nBenchmarking VectorBT acceleration...")

        returns = self.generate_test_data()
        simulation_counts = [1000, 5000, 10000]
        methods = [
            (SimulationMethod.BOOTSTRAP, 'Standard Bootstrap', False),
            (SimulationMethod.GEOMETRIC_BROWNIAN, 'Standard GBM', False)
        ]

        # Try to add VectorBT methods if available
        try:
            import vectorbt as vbt
            methods.extend([
                (SimulationMethod.VECTORBT_RESAMPLE, 'VectorBT Resample', True),
                (SimulationMethod.GEOMETRIC_BROWNIAN, 'VectorBT GBM', True)
            ])
        except ImportError:
            print("  VectorBT not available, skipping VectorBT benchmarks")

        results = {
            'method': [],
            'n_simulations': [],
            'execution_time': [],
            'simulations_per_second': []
        }

        for n_sim in simulation_counts:
            print(f"  Testing {n_sim} simulations...")

            for method, method_name, use_vectorbt in methods:
                print(f"    Method: {method_name}")

                config = EnhancedMCConfig(
                    n_simulations=n_sim,
                    time_horizon=252,
                    n_workers=4,
                    use_vectorbt=use_vectorbt
                )

                simulator = EnhancedMonteCarloSimulator(config)

                try:
                    start_time = time.time()
                    sim_results = await simulator.simulate_parallel(
                        returns=returns,
                        method=method,
                        initial_capital=100000
                    )
                    execution_time = time.time() - start_time

                    results['method'].append(method_name)
                    results['n_simulations'].append(n_sim)
                    results['execution_time'].append(execution_time)
                    results['simulations_per_second'].append(n_sim / execution_time)

                    print(f"      Time: {execution_time:.2f}s, Rate: {n_sim/execution_time:.0f} sims/s")

                except Exception as e:
                    print(f"      Failed: {e}")
                    continue

        self.results['vectorbt_comparison'] = results
        return results

    async def benchmark_memory_usage(self) -> Dict[str, List]:
        """
        Benchmark memory usage across different simulation configurations
        """
        print("\nBenchmarking memory usage...")

        returns = self.generate_test_data()
        simulation_counts = [1000, 5000, 10000, 20000]

        results = {
            'n_simulations': [],
            'memory_per_simulation_mb': [],
            'peak_memory_mb': [],
            'memory_optimized': []
        }

        for n_sim in simulation_counts:
            print(f"  Testing {n_sim} simulations...")

            # Test without memory optimization
            config_normal = EnhancedMCConfig(
                n_simulations=n_sim,
                time_horizon=252,
                n_workers=4,
                use_vectorbt=False,
                enable_memory_optimization=False
            )

            process = psutil.Process()
            mem_before = process.memory_info().rss / 1024 / 1024

            simulator = EnhancedMonteCarloSimulator(config_normal)

            start_time = time.time()
            sim_results = await simulator.simulate_parallel(
                returns=returns,
                method=SimulationMethod.BOOTSTRAP,
                initial_capital=100000
            )

            mem_after = process.memory_info().rss / 1024 / 1024
            memory_used = mem_after - mem_before
            memory_per_sim = memory_used / n_sim

            print(f"    Without optimization: {memory_per_sim:.4f} MB per sim")

            # Test with memory optimization
            config_optimized = EnhancedMCConfig(
                n_simulations=n_sim,
                time_horizon=252,
                n_workers=4,
                use_vectorbt=False,
                enable_memory_optimization=True,
                chunk_size=100
            )

            mem_before_opt = process.memory_info().rss / 1024 / 1024

            simulator_opt = EnhancedMonteCarloSimulator(config_optimized)

            sim_results_opt = await simulator_opt.simulate_parallel(
                returns=returns,
                method=SimulationMethod.BOOTSTRAP,
                initial_capital=100000
            )

            mem_after_opt = process.memory_info().rss / 1024 / 1024
            memory_used_opt = mem_after_opt - mem_before_opt
            memory_per_sim_opt = memory_used_opt / n_sim

            print(f"    With optimization: {memory_per_sim_opt:.4f} MB per sim")

            # Store results
            results['n_simulations'].append(n_sim)
            results['memory_per_simulation_mb'].append(memory_per_sim)
            results['peak_memory_mb'].append(max(memory_used, memory_used_opt))
            results['memory_optimized'].append(memory_per_sim_opt)

        self.results['memory_usage'] = results
        return results

    def plot_results(self, save_path: str = 'monte_carlo_performance.png'):
        """
        Plot benchmark results

        Args:
            save_path: Path to save the plot
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Monte Carlo Simulation Performance Benchmarks', fontsize=16)

        # Plot 1: Scaling performance
        if 'scaling' in self.results and self.results['scaling']:
            ax = axes[0, 0]
            scaling = self.results['scaling']
            ax.plot(scaling['n_simulations'], scaling['execution_time'], 'bo-', label='Execution Time')
            ax.set_xlabel('Number of Simulations')
            ax.set_ylabel('Execution Time (s)')
            ax.set_title('Simulation Scaling Performance')
            ax.set_xscale('log')
            ax.set_yscale('log')
            ax.grid(True, alpha=0.3)
            ax.legend()

        # Plot 2: Parallel efficiency
        if 'parallel_efficiency' in self.results and self.results['parallel_efficiency']:
            ax = axes[0, 1]
            parallel = self.results['parallel_efficiency']
            ax.plot(parallel['n_workers'], parallel['speedup'], 'go-', label='Speedup')
            ax.axhline(y=parallel['n_workers'][-1], color='r', linestyle='--', label='Ideal')
            ax.set_xlabel('Number of Workers')
            ax.set_ylabel('Speedup')
            ax.set_title('Parallel Efficiency')
            ax.grid(True, alpha=0.3)
            ax.legend()

        # Plot 3: Method comparison
        if 'vectorbt_comparison' in self.results and self.results['vectorbt_comparison']:
            ax = axes[1, 0]
            comparison = self.results['vectorbt_comparison']

            # Group by method
            methods = list(set(comparison['method']))
            n_sims = list(set(comparison['n_simulations']))

            for method in methods:
                method_times = []
                for n_sim in n_sims:
                    idx = comparison['method'].index(method)
                    if comparison['n_simulations'][idx] == n_sim:
                        method_times.append(comparison['execution_time'][idx])

                if method_times:
                    ax.plot(n_sims[:len(method_times)], method_times, marker='o', label=method)

            ax.set_xlabel('Number of Simulations')
            ax.set_ylabel('Execution Time (s)')
            ax.set_title('Method Performance Comparison')
            ax.set_xscale('log')
            ax.set_yscale('log')
            ax.grid(True, alpha=0.3)
            ax.legend()

        # Plot 4: Memory usage
        if 'memory_usage' in self.results and self.results['memory_usage']:
            ax = axes[1, 1]
            memory = self.results['memory_usage']

            x = np.arange(len(memory['n_simulations']))
            width = 0.35

            ax.bar(x - width/2, memory['memory_per_simulation_mb'], width,
                   label='Without Optimization', alpha=0.7)
            ax.bar(x + width/2, memory['memory_optimized'], width,
                   label='With Optimization', alpha=0.7)

            ax.set_xlabel('Number of Simulations')
            ax.set_ylabel('Memory per Simulation (MB)')
            ax.set_title('Memory Usage Comparison')
            ax.set_xticks(x)
            ax.set_xticklabels(memory['n_simulations'])
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\nPerformance plots saved to: {save_path}")

    def save_results(self, save_path: str = 'monte_carlo_benchmark_results.json'):
        """
        Save benchmark results to JSON

        Args:
            save_path: Path to save results
        """
        import json

        # Convert numpy arrays to lists for JSON serialization
        serializable_results = {}
        for key, value in self.results.items():
            serializable_results[key] = {
                k: v.tolist() if hasattr(v, 'tolist') else v
                for k, v in value.items()
            }

        with open(save_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)

        print(f"Benchmark results saved to: {save_path}")

    def print_summary(self):
        """Print a summary of benchmark results"""
        print("\n" + "="*60)
        print("MONTE CARLO PERFORMANCE BENCHMARK SUMMARY")
        print("="*60)

        # Scaling summary
        if 'scaling' in self.results and self.results['scaling']:
            scaling = self.results['scaling']
            print(f"\n1. SCALING PERFORMANCE:")
            print(f"   - 100 sims: {scaling['execution_time'][0]:.2f}s")
            print(f"   - 20,000 sims: {scaling['execution_time'][-1]:.2f}s")
            print(f"   - Scaling factor: {scaling['execution_time'][-1]/scaling['execution_time'][0]:.1f}x")

        # Parallel efficiency summary
        if 'parallel_efficiency' in self.results and self.results['parallel_efficiency']:
            parallel = self.results['parallel_efficiency']
            max_speedup = max(parallel['speedup'])
            max_workers = parallel['n_workers'][parallel['speedup'].index(max_speedup)]
            print(f"\n2. PARALLEL EFFICIENCY:")
            print(f"   - Maximum speedup: {max_speedup:.2f}x with {max_workers} workers")
            print(f"   - Efficiency at {max_workers} workers: {parallel['efficiency'][parallel['n_workers'].index(max_workers)]:.1%}")

        # VectorBT comparison
        if 'vectorbt_comparison' in self.results and self.results['vectorbt_comparison']:
            comparison = self.results['vectorbt_comparison']
            vectorbt_methods = [m for m in comparison['method'] if 'VectorBT' in m]
            if vectorbt_methods:
                print(f"\n3. VECTOREBT ACCELERATION:")
                print(f"   - VectorBT methods tested: {len(vectorbt_methods)}")
                # Compare fastest methods
                fastest_method = comparison['method'][np.argmax(comparison['simulations_per_second'])]
                fastest_rate = max(comparison['simulations_per_second'])
                print(f"   - Fastest method: {fastest_method} ({fastest_rate:.0f} sims/s)")

        # Memory usage
        if 'memory_usage' in self.results and self.results['memory_usage']:
            memory = self.results['memory_usage']
            if len(memory['memory_per_simulation_mb']) > 0:
                print(f"\n4. MEMORY USAGE:")
                print(f"   - Average memory per simulation: {np.mean(memory['memory_per_simulation_mb']):.4f} MB")
                if len(memory['memory_optimized']) > 0:
                    reduction = 1 - np.mean(memory['memory_optimized']) / np.mean(memory['memory_per_simulation_mb'])
                    print(f"   - Memory optimization reduction: {reduction:.1%}")

        print("\n" + "="*60)


async def run_full_benchmark():
    """
    Run the complete performance benchmark suite
    """
    print("Starting Monte Carlo Performance Benchmark Suite...")
    print(f"System: {mp.cpu_count()} CPU cores")

    benchmark = MonteCarloPerformanceBenchmark()

    # Run all benchmarks
    try:
        await benchmark.benchmark_scaling()
        await benchmark.benchmark_parallel_efficiency()
        await benchmark.benchmark_vectorbt_comparison()
        await benchmark.benchmark_memory_usage()

        # Save results
        benchmark.save_results('monte_carlo_benchmark_results.json')
        benchmark.plot_results('monte_carlo_performance.png')

        # Print summary
        benchmark.print_summary()

    except Exception as e:
        print(f"Benchmark failed: {e}")
        import traceback
        traceback.print_exc()


async def run_quick_benchmark():
    """
    Run a quick subset of benchmarks for testing
    """
    print("Running Quick Monte Carlo Benchmark...")

    benchmark = MonteCarloPerformanceBenchmark()

    # Run only scaling benchmark
    await benchmark.benchmark_scaling()

    # Print summary
    benchmark.print_summary()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Monte Carlo Performance Benchmark')
    parser.add_argument('--quick', action='store_true', help='Run quick benchmark only')
    args = parser.parse_args()

    if args.quick:
        asyncio.run(run_quick_benchmark())
    else:
        asyncio.run(run_full_benchmark())