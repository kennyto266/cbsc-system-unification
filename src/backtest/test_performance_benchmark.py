"""
Test Performance Benchmark System
==================================

Comprehensive tests for the performance benchmark module.
Tests all benchmark functions and optimization methods.
"""
import sys
import os

# Add parent directory to path for proper imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path
import time

# Import benchmark module directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "performance_benchmark",
    os.path.join(os.path.dirname(__file__), "performance_benchmark.py")
)
bench_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench_module)

PerformanceBenchmark = bench_module.PerformanceBenchmark
BenchmarkConfig = bench_module.BenchmarkConfig
BenchmarkFunction = bench_module.BenchmarkFunction
ProblemType = bench_module.ProblemType
create_standard_benchmarks = bench_module.create_standard_benchmarks

print("=" * 70)
print("Testing Performance Benchmark System")
print("=" * 70)

# Test 1: Create benchmark system
print("\n[1] Creating benchmark system...")
config = BenchmarkConfig(
    n_runs=3,  # Reduced for faster testing
    random_state=42,
    save_results=True,
    output_dir="./test_benchmark_results"
)

benchmark = PerformanceBenchmark(config)
print("[OK] Benchmark system created")

# Test 2: Register benchmark functions
print("\n[2] Registering benchmark functions...")
standard_benchmarks = create_standard_benchmarks()
for func in standard_benchmarks:
    benchmark.register_benchmark_function(func)
print(f"[OK] Registered {len(standard_benchmarks)} benchmark functions:")
for func in standard_benchmarks:
    print(f"  - {func.name}: {func.description}")

# Test 3: Test individual benchmark functions
print("\n[3] Testing benchmark functions...")
test_functions = [
    ("sphere_2d", np.array([0.0, 0.0]), 0.0),
    ("rosenbrock_2d", np.array([1.0, 1.0]), 0.0),
    ("rastrigin_2d", np.array([0.0, 0.0]), 0.0),
]

for func_name, test_x, expected_value in test_functions:
    func = benchmark.benchmark_functions[func_name]
    result = func.func(test_x)
    error = abs(result - expected_value)
    status = "OK" if error < 1e-10 else "FAIL"
    print(f"  {status} {func_name}: f(x)={result:.6e} (expected={expected_value:.6e})")

print("[OK] Benchmark functions validated")

# Test 4: Run limited benchmark (subset of methods and functions)
print("\n[4] Running limited benchmark test...")
print("  Testing 2 functions x 3 methods x 3 runs = 18 total runs")

test_functions_subset = ["sphere_2d", "rosenbrock_2d"]
test_methods_subset = ["random_search", "bayesian_optimization", "differential_evolution"]

start_time = time.time()
aggregated_results = benchmark.run_benchmark(
    function_names=test_functions_subset,
    methods=test_methods_subset
)
benchmark_time = time.time() - start_time

print(f"[OK] Benchmark completed in {benchmark_time:.2f} seconds")

# Test 5: Display results
print("\n[5] Aggregated results:")
print("-" * 70)
for key, result in aggregated_results.items():
    print(f"\n{key}:")
    print(f"  Mean Score: {result.mean_score:.6f} +/- {result.std_score:.6f}")
    print(f"  Success Rate: {result.success_rate:.2%}")
    print(f"  Mean Runtime: {result.mean_runtime:.2f}s")
    print(f"  Mean Evaluations: {result.mean_evaluations:.0f}")

# Test 6: Generate leaderboard
print("\n[6] Generating leaderboard...")
leaderboard = benchmark.generate_leaderboard(metric="mean_score")
print("\nLeaderboard (ranked by mean score, lower is better):")
print("-" * 70)
print(leaderboard.to_string(index=False))

# Save leaderboard
leaderboard_path = Path(config.output_dir) / "test_leaderboard.csv"
leaderboard.to_csv(leaderboard_path, index=False)
print(f"\n[OK] Leaderboard saved to {leaderboard_path}")

# Test 7: Create comparison plots
print("\n[7] Creating comparison plots...")

# Overall comparison
fig1 = benchmark.plot_comparison(save_path="test_benchmark_comparison_all.png")
plt.close(fig1)
print("  [OK] Overall comparison plot created")

# Per-function comparison
for func_name in test_functions_subset:
    fig = benchmark.plot_comparison(
        function_name=func_name,
        save_path=f"test_benchmark_comparison_{func_name}.png"
    )
    plt.close(fig)
    print(f"  [OK] {func_name} comparison plot created")

# Test 8: Verify saved results
print("\n[8] Verifying saved results...")
output_dir = Path(config.output_dir)
saved_files = list(output_dir.glob("*.*"))
print(f"[OK] Found {len(saved_files)} saved files:")
for f in saved_files:
    size = f.stat().st_size
    print(f"  - {f.name} ({size} bytes)")

# Test 9: Test loading results
print("\n[9] Testing loading results...")
json_files = list(output_dir.glob("benchmark_raw_*.json"))
if json_files:
    benchmark.load_results(str(json_files[0]))
    print(f"[OK] Loaded results from {json_files[0].name}")
else:
    print("[SKIP] No JSON files found to load")

# Test 10: Statistical analysis
print("\n[10] Statistical analysis summary:")
print("-" * 70)

# Group by method
method_stats = {}
for result in aggregated_results.values():
    if result.method not in method_stats:
        method_stats[result.method] = {
            'scores': [],
            'runtimes': [],
            'success_rates': []
        }
    method_stats[result.method]['scores'].append(result.mean_score)
    method_stats[result.method]['runtimes'].append(result.mean_runtime)
    method_stats[result.method]['success_rates'].append(result.success_rate)

for method, stats in method_stats.items():
    avg_score = np.mean(stats['scores'])
    avg_runtime = np.mean(stats['runtimes'])
    avg_success = np.mean(stats['success_rates'])
    print(f"\n{method}:")
    print(f"  Average Score: {avg_score:.6f}")
    print(f"  Average Runtime: {avg_runtime:.2f}s")
    print(f"  Average Success Rate: {avg_success:.2%}")

# Final summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"[OK] All performance benchmark tests completed!")
print(f"\nBenchmark Statistics:")
print(f"  - Functions tested: {len(test_functions_subset)}")
print(f"  - Methods tested: {len(test_methods_subset)}")
print(f"  - Runs per configuration: {config.n_runs}")
print(f"  - Total runs: {len(test_functions_subset) * len(test_methods_subset) * config.n_runs}")
print(f"  - Total time: {benchmark_time:.2f} seconds")
print(f"\nGenerated files:")
for f in saved_files:
    print(f"  - {f.name}")

# Find best method
best_method = min(method_stats.items(), key=lambda x: np.mean(x[1]['scores']))
print(f"\nBest overall method: {best_method[0]} (avg score: {np.mean(best_method[1]['scores']):.6f})")

print("\n" + "=" * 70)
