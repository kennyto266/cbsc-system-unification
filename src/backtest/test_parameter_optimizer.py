"""
Test Parameter Optimizer
=========================

Comprehensive tests for the parameter optimization module.
Tests all optimization methods: grid search, random search, Bayesian optimization, etc.
"""
import sys
import os

# Add parent directory to path for proper imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta

# Import directly from the module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "parameter_optimizer",
    os.path.join(os.path.dirname(__file__), "parameter_optimizer.py")
)
param_opt_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(param_opt_module)

ParameterOptimizer = param_opt_module.ParameterOptimizer
OptimizationConfig = param_opt_module.OptimizationConfig
ParameterSpace = param_opt_module.ParameterSpace
OptimizationResult = param_opt_module.OptimizationResult
OptimizationMethod = param_opt_module.OptimizationMethod
ObjectiveType = param_opt_module.ObjectiveType
create_optimization_config = param_opt_module.create_optimization_config
create_parameter_space = param_opt_module.create_parameter_space

print("=" * 70)
print("Testing Parameter Optimizer Module")
print("=" * 70)

# Create synthetic price data for testing
print("\n[1] Creating synthetic test data...")
np.random.seed(42)
dates = pd.date_range(start='2023-01-01', periods=300, freq='D')
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

price_data = {}
for symbol in symbols:
    # Simulate price movement with trend and noise
    market_returns = np.random.normal(0.0003, 0.015, 300)
    beta = 0.8 + list(symbols).index(symbol) * 0.1
    specific_returns = np.random.normal(0, 0.02, 300)
    returns = market_returns * beta + specific_returns
    price = 100 * np.cumprod(1 + returns)

    price_data[symbol] = pd.DataFrame({
        'close': price,
        'open': price * (1 + np.random.normal(0, 0.005, 300)),
        'high': price * (1 + np.abs(np.random.normal(0, 0.01, 300))),
        'low': price * (1 - np.abs(np.random.normal(0, 0.01, 300))),
        'volume': np.random.randint(1000000, 20000000, 300)
    }, index=dates)

print(f"[OK] Created price data for {len(price_data)} symbols")

# Define objective function for optimization
print("\n[2] Defining objective function...")


def simple_objective(params, data):
    """
    Simple objective function for testing.
    Simulates strategy performance based on parameters.
    """
    # Extract parameters
    window = params.get('window', 20)
    threshold = params.get('threshold', 0.02)
    weight = params.get('weight', 1.0)

    # Simulate performance (mock calculation)
    # In real scenario, this would run actual backtest
    base_score = 0.5

    # Reward moderate window sizes (5-30)
    if 5 <= window <= 30:
        window_score = 1.0 - abs(window - 15) / 15
    else:
        window_score = 0.3

    # Reward moderate thresholds (0.01-0.05)
    if 0.01 <= threshold <= 0.05:
        threshold_score = 1.0 - abs(threshold - 0.03) / 0.03
    else:
        threshold_score = 0.3

    # Reward balanced weights
    weight_score = 1.0 - abs(weight - 0.5)

    # Combined score with some randomness for realism
    score = (base_score + 0.3 * window_score + 0.3 * threshold_score + 0.2 * weight_score)
    score += np.random.normal(0, 0.02)  # Add noise

    return max(0, min(1, score))  # Clamp to [0, 1]


print("[OK] Objective function defined")

# Test 1: Grid Search Optimization
print("\n[3] Testing Grid Search Optimization...")
config = create_optimization_config(
    method=OptimizationMethod.GRID_SEARCH,
    max_iterations=50,
    verbose=True
)

optimizer = ParameterOptimizer(config)
optimizer.add_parameter(ParameterSpace('window', 'discrete', (5, 30)))
optimizer.add_parameter(ParameterSpace('threshold', 'continuous', (0.01, 0.05)))
optimizer.add_parameter(ParameterSpace('weight', 'continuous', (0.1, 1.0)))

start_time = time.time()
grid_result = optimizer.optimize(simple_objective, price_data)
grid_time = time.time() - start_time

print(f"\nGrid Search Results:")
print(f"  Best parameters: {grid_result.best_params}")
print(f"  Best score: {grid_result.best_score:.4f}")
print(f"  Evaluations: {grid_result.n_evaluations}")
print(f"  Time: {grid_time:.2f} seconds")

# Test 2: Random Search Optimization
print("\n[4] Testing Random Search Optimization...")
config = create_optimization_config(
    method=OptimizationMethod.RANDOM_SEARCH,
    max_iterations=100,
    random_state=42
)

optimizer = ParameterOptimizer(config)
optimizer.add_parameter(ParameterSpace('window', 'discrete', (5, 30)))
optimizer.add_parameter(ParameterSpace('threshold', 'continuous', (0.01, 0.05)))
optimizer.add_parameter(ParameterSpace('weight', 'continuous', (0.1, 1.0)))

start_time = time.time()
random_result = optimizer.optimize(simple_objective, price_data)
random_time = time.time() - start_time

print(f"\nRandom Search Results:")
print(f"  Best parameters: {random_result.best_params}")
print(f"  Best score: {random_result.best_score:.4f}")
print(f"  Evaluations: {random_result.n_evaluations}")
print(f"  Time: {random_time:.2f} seconds")

# Test 3: Bayesian Optimization
print("\n[5] Testing Bayesian Optimization...")
config = create_optimization_config(
    method=OptimizationMethod.BAYESIAN_OPTIMIZATION,
    n_calls=50,
    random_state=42
)

optimizer = ParameterOptimizer(config)
optimizer.add_parameter(ParameterSpace('window', 'discrete', (5, 30)))
optimizer.add_parameter(ParameterSpace('threshold', 'continuous', (0.01, 0.05)))
optimizer.add_parameter(ParameterSpace('weight', 'continuous', (0.1, 1.0)))

start_time = time.time()
bayes_result = optimizer.optimize(simple_objective, price_data)
bayes_time = time.time() - start_time

print(f"\nBayesian Optimization Results:")
print(f"  Best parameters: {bayes_result.best_params}")
print(f"  Best score: {bayes_result.best_score:.4f}")
print(f"  Evaluations: {bayes_result.n_evaluations}")
print(f"  Time: {bayes_time:.2f} seconds")

# Test 4: Genetic Algorithm
print("\n[6] Testing Genetic Algorithm...")
config = create_optimization_config(
    method=OptimizationMethod.GENETIC_ALGORITHM,
    max_iterations=50,
    random_state=42
)

optimizer = ParameterOptimizer(config)
optimizer.add_parameter(ParameterSpace('window', 'discrete', (5, 30)))
optimizer.add_parameter(ParameterSpace('threshold', 'continuous', (0.01, 0.05)))
optimizer.add_parameter(ParameterSpace('weight', 'continuous', (0.1, 1.0)))

start_time = time.time()
ga_result = optimizer.optimize(simple_objective, price_data)
ga_time = time.time() - start_time

print(f"\nGenetic Algorithm Results:")
print(f"  Best parameters: {ga_result.best_params}")
print(f"  Best score: {ga_result.best_score:.4f}")
print(f"  Evaluations: {ga_result.n_evaluations}")
print(f"  Time: {ga_time:.2f} seconds")

# Test 5: Particle Swarm Optimization
print("\n[7] Testing Particle Swarm Optimization...")
config = create_optimization_config(
    method=OptimizationMethod.PARTICLE_SWARM,
    max_iterations=30,
    random_state=42
)

optimizer = ParameterOptimizer(config)
optimizer.add_parameter(ParameterSpace('window', 'discrete', (5, 30)))
optimizer.add_parameter(ParameterSpace('threshold', 'continuous', (0.01, 0.05)))
optimizer.add_parameter(ParameterSpace('weight', 'continuous', (0.1, 1.0)))

start_time = time.time()
pso_result = optimizer.optimize(simple_objective, price_data)
pso_time = time.time() - start_time

print(f"\nParticle Swarm Results:")
print(f"  Best parameters: {pso_result.best_params}")
print(f"  Best score: {pso_result.best_score:.4f}")
print(f"  Evaluations: {pso_result.n_evaluations}")
print(f"  Time: {pso_time:.2f} seconds")

# Test 6: Differential Evolution
print("\n[8] Testing Differential Evolution...")
config = create_optimization_config(
    method=OptimizationMethod.DIFFERENTIAL_EVOLUTION,
    max_iterations=30,
    random_state=42
)

optimizer = ParameterOptimizer(config)
optimizer.add_parameter(ParameterSpace('window', 'discrete', (5, 30)))
optimizer.add_parameter(ParameterSpace('threshold', 'continuous', (0.01, 0.05)))
optimizer.add_parameter(ParameterSpace('weight', 'continuous', (0.1, 1.0)))

start_time = time.time()
de_result = optimizer.optimize(simple_objective, price_data)
de_time = time.time() - start_time

print(f"\nDifferential Evolution Results:")
print(f"  Best parameters: {de_result.best_params}")
print(f"  Best score: {de_result.best_score:.4f}")
print(f"  Evaluations: {de_result.n_evaluations}")
print(f"  Time: {de_time:.2f} seconds")

# Test 7: Simulated Annealing
print("\n[9] Testing Simulated Annealing...")
config = create_optimization_config(
    method=OptimizationMethod.SIMULATED_ANNEALING,
    max_iterations=50,
    random_state=42
)

optimizer = ParameterOptimizer(config)
optimizer.add_parameter(ParameterSpace('window', 'discrete', (5, 30)))
optimizer.add_parameter(ParameterSpace('threshold', 'continuous', (0.01, 0.05)))
optimizer.add_parameter(ParameterSpace('weight', 'continuous', (0.1, 1.0)))

start_time = time.time()
sa_result = optimizer.optimize(simple_objective, price_data)
sa_time = time.time() - start_time

print(f"\nSimulated Annealing Results:")
print(f"  Best parameters: {sa_result.best_params}")
print(f"  Best score: {sa_result.best_score:.4f}")
print(f"  Evaluations: {sa_result.n_evaluations}")
print(f"  Time: {sa_time:.2f} seconds")

# Comparison Summary
print("\n" + "=" * 70)
print("OPTIMIZATION METHODS COMPARISON")
print("=" * 70)

results = [
    ("Grid Search", grid_result.best_score, grid_result.n_evaluations, grid_time),
    ("Random Search", random_result.best_score, random_result.n_evaluations, random_time),
    ("Bayesian Opt", bayes_result.best_score, bayes_result.n_evaluations, bayes_time),
    ("Genetic Algorithm", ga_result.best_score, ga_result.n_evaluations, ga_time),
    ("Particle Swarm", pso_result.best_score, pso_result.n_evaluations, pso_time),
    ("Differential Evolution", de_result.best_score, de_result.n_evaluations, de_time),
    ("Simulated Annealing", sa_result.best_score, sa_result.n_evaluations, sa_time),
]

print(f"\n{'Method':<25} {'Best Score':<12} {'Evaluations':<15} {'Time (s)':<10}")
print("-" * 70)
for name, score, evals, t in results:
    print(f"{name:<25} {score:<12.4f} {evals:<15} {t:<10.2f}")

# Find best method
best_method = max(results, key=lambda x: x[1])
print(f"\nBest method: {best_method[0]} with score {best_method[1]:.4f}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"[OK] All optimization tests completed!")
print(f"  - Grid Search: {grid_result.n_evaluations} evaluations, {grid_time:.2f}s")
print(f"  - Random Search: {random_result.n_evaluations} evaluations, {random_time:.2f}s")
print(f"  - Bayesian Opt: {bayes_result.n_evaluations} evaluations, {bayes_time:.2f}s")
print(f"  - Genetic Algorithm: {ga_result.n_evaluations} evaluations, {ga_time:.2f}s")
print(f"  - Particle Swarm: {pso_result.n_evaluations} evaluations, {pso_time:.2f}s")
print(f"  - Differential Evolution: {de_result.n_evaluations} evaluations, {de_time:.2f}s")
print(f"  - Simulated Annealing: {sa_result.n_evaluations} evaluations, {sa_time:.2f}s")
print(f"\nBest overall score: {best_method[1]:.4f} ({best_method[0]})")
print("\n" + "=" * 70)
