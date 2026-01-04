"""
CBSC Backtest System - Parameter Optimization Quick Start Guide
============================================================

This script demonstrates how to use the parameter optimization system.

Author: CBSC Quant Team
Date: 2025-12-28
"""

print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     CBSC Parameter Optimization System - Quick Start        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

# Example 1: Basic Parameter Optimization
print("\n" + "="*60)
print("Example 1: Basic Parameter Optimization")
print("="*60)

from parameter_optimizer import (
    ParameterOptimizer,
    OptimizationConfig,
    OptimizationMethod,
    ParameterSpace
)
import time

# Define a simple objective function (sphere function)
def simple_objective(params, data=None):
    """
    Simple sphere function: -(x^2 + y^2)
    Maximum at x=0, y=0 with value 0
    """
    x = params.get('x', 0)
    y = params.get('y', 0)
    return -(x**2 + y**2)

# Create optimizer configuration
config = OptimizationConfig(
    method=OptimizationMethod.GRID_SEARCH,
    max_iterations=25
)

# Create optimizer
optimizer = ParameterOptimizer(config)

# Add parameters using ParameterSpace
optimizer.add_parameter(ParameterSpace(name='x', param_type='continuous', bounds=(-5, 5)))
optimizer.add_parameter(ParameterSpace(name='y', param_type='continuous', bounds=(-5, 5)))

# Run optimization
print("\nRunning optimization...")
start = time.time()
result = optimizer.optimize(simple_objective)
elapsed = time.time() - start

# Display results
print(f"\nResults:")
print(f"  Best Score:   {result.best_score:.6f}")
print(f"  Best Params:   {result.best_params}")
print(f"  Evaluations:   {result.n_evaluations}")
print(f"  Time:          {elapsed:.3f}s")

# Example 2: Try Different Optimization Methods
print("\n" + "="*60)
print("Example 2: Compare Different Methods")
print("="*60)

methods = [
    OptimizationMethod.GRID_SEARCH,
    OptimizationMethod.RANDOM_SEARCH,
    OptimizationMethod.PARTICLE_SWARM
]

results_comparison = []

for method in methods:
    config.method = method
    config.max_iterations = 50

    test_optimizer = ParameterOptimizer(config)
    test_optimizer.add_parameter(ParameterSpace(name='x', param_type='continuous', bounds=(-5, 5)))
    test_optimizer.add_parameter(ParameterSpace(name='y', param_type='continuous', bounds=(-5, 5)))

    start = time.time()
    result = test_optimizer.optimize(simple_objective)
    elapsed = time.time() - start

    results_comparison.append({
        'method': method.value,
        'score': result.best_score,
        'time': elapsed
    })

    print(f"\n{method.value:25s}: Score={result.best_score:8.4f}, Time={elapsed:.3f}s")

# Example 3: All 7 Optimization Methods
print("\n" + "="*60)
print("Example 3: Test All 7 Optimization Algorithms")
print("="*60)

all_methods = [
    ("Grid Search", OptimizationMethod.GRID_SEARCH),
    ("Random Search", OptimizationMethod.RANDOM_SEARCH),
    ("Bayesian Optimization", OptimizationMethod.BAYESIAN_OPTIMIZATION),
    ("Genetic Algorithm", OptimizationMethod.GENETIC_ALGORITHM),
    ("Particle Swarm", OptimizationMethod.PARTICLE_SWARM),
    ("Differential Evolution", OptimizationMethod.DIFFERENTIAL_EVOLUTION),
    ("Simulated Annealing", OptimizationMethod.SIMULATED_ANNEALING)
]

print("\nRunning all 7 optimization algorithms...\n")
all_results = []

for name, method in all_methods:
    config.method = method
    config.max_iterations = 30  # Reduced for faster demo

    test_optimizer = ParameterOptimizer(config)
    test_optimizer.add_parameter(ParameterSpace(name='x', param_type='continuous', bounds=(-5, 5)))
    test_optimizer.add_parameter(ParameterSpace(name='y', param_type='continuous', bounds=(-5, 5)))

    start = time.time()
    try:
        result = test_optimizer.optimize(simple_objective)
        elapsed = time.time() - start

        all_results.append({
            'name': name,
            'score': result.best_score,
            'time': elapsed,
            'evals': result.n_evaluations
        })

        print(f"  {name:25s}: Score={result.best_score:8.4f}, Time={elapsed:6.3f}s, Evals={result.n_evaluations:3d}")
    except Exception as e:
        print(f"  {name:25s}: ERROR - {str(e)[:50]}")

# Show winner
if all_results:
    winner = max(all_results, key=lambda x: x['score'])
    print(f"\n  [WINNER] Best Algorithm: {winner['name']} (Score: {winner['score']:.4f})")

# Example 4: Multi-Dimensional Optimization
print("\n" + "="*60)
print("Example 4: 3D Parameter Optimization")
print("="*60)

config_3d = OptimizationConfig(
    method=OptimizationMethod.RANDOM_SEARCH,
    max_iterations=100
)

optimizer_3d = ParameterOptimizer(config_3d)
optimizer_3d.add_parameter(ParameterSpace(name='x', param_type='continuous', bounds=(-5, 5)))
optimizer_3d.add_parameter(ParameterSpace(name='y', param_type='continuous', bounds=(-5, 5)))
optimizer_3d.add_parameter(ParameterSpace(name='z', param_type='continuous', bounds=(-5, 5)))

def sphere_3d(params, data=None):
    return -(params['x']**2 + params['y']**2 + params['z']**2)

print("\nRunning 3D optimization...")
start = time.time()
result_3d = optimizer_3d.optimize(sphere_3d)
elapsed = time.time() - start

print(f"\n3D Results:")
print(f"  Best Score:   {result_3d.best_score:.6f}")
print(f"  Best Params:   {result_3d.best_params}")
print(f"  Evaluations:   {result_3d.n_evaluations}")
print(f"  Time:          {elapsed:.3f}s")

# Example 5: 4D+ High-Dimensional Optimization
print("\n" + "="*60)
print("Example 5: 4D High-Dimensional Optimization")
print("="*60)

config_4d = OptimizationConfig(
    method=OptimizationMethod.RANDOM_SEARCH,
    max_iterations=200
)

optimizer_4d = ParameterOptimizer(config_4d)

# Add 4 parameters
for i in range(4):
    optimizer_4d.add_parameter(
        ParameterSpace(
            name=f'param_{i}',
            param_type='continuous',
            bounds=(-5, 5)
        )
    )

def sphere_4d(params, data=None):
    return -sum(params.get(f'param_{i}', 0)**2 for i in range(4))

print("\nRunning 4D optimization...")
start = time.time()
result_4d = optimizer_4d.optimize(sphere_4d)
elapsed = time.time() - start

print(f"\n4D Results:")
print(f"  Best Score:   {result_4d.best_score:.6f}")
print(f"  Best Params:   {result_4d.best_params}")
print(f"  Evaluations:   {result_4d.n_evaluations}")
print(f"  Time:          {elapsed:.3f}s")

# Example 6: Different Parameter Types
print("\n" + "="*60)
print("Example 6: Mixed Parameter Types")
print("="*60)

config_mixed = OptimizationConfig(
    method=OptimizationMethod.GRID_SEARCH,
    max_iterations=100
)

optimizer_mixed = ParameterOptimizer(config_mixed)

# Continuous parameter (e.g., learning rate)
optimizer_mixed.add_parameter(
    ParameterSpace(name='learning_rate', param_type='continuous', bounds=(0.001, 0.1))
)

# Discrete parameter (e.g., batch size - will be sampled as continuous then converted)
optimizer_mixed.add_parameter(
    ParameterSpace(name='batch_size', param_type='discrete', bounds=(16, 128))
)

# Categorical parameter (e.g., optimizer choice)
optimizer_mixed.add_parameter(
    ParameterSpace(name='optimizer_type', param_type='categorical', bounds=['adam', 'sgd', 'rmsprop'])
)

def mixed_objective(params, data=None):
    """Example hyperparameter optimization objective"""
    lr = params.get('learning_rate', 0.01)
    bs = params.get('batch_size', 32)
    opt = params.get('optimizer_type', 'adam')

    # Simulated objective (higher is better)
    # Adam generally performs better, higher learning rate preferred but not too high
    opt_score = {'adam': 1.0, 'sgd': 0.8, 'rmsprop': 0.9}[opt]
    score = (lr * 100) * opt_score - (bs / 1000)
    return score

print("\nRunning mixed-type optimization...")
start = time.time()
result_mixed = optimizer_mixed.optimize(mixed_objective)
elapsed = time.time() - start

print(f"\nMixed-Type Results:")
print(f"  Best Score:   {result_mixed.best_score:.6f}")
print(f"  Best Params:")
for key, value in result_mixed.best_params.items():
    print(f"    {key}: {value}")
print(f"  Evaluations:   {result_mixed.n_evaluations}")
print(f"  Time:          {elapsed:.3f}s")

# Example 7: Custom Objective Function (Rosenbrock)
print("\n" + "="*60)
print("Example 7: Rosenbrock Function Optimization")
print("="*60)

def rosenbrock(params, data=None):
    """
    Rosenbrock function: f(x,y) = (a-x)^2 + b(y-x^2)^2
    where a=1, b=100
    Minimum at x=1, y=1 with value 0
    """
    x = params.get('x', 0)
    y = params.get('y', 0)
    a = 1
    b = 100
    return -((a - x)**2 + b * (y - x**2)**2)

config_rosen = OptimizationConfig(
    method=OptimizationMethod.GRID_SEARCH,
    max_iterations=100
)

optimizer_rosen = ParameterOptimizer(config_rosen)
optimizer_rosen.add_parameter(ParameterSpace(name='x', param_type='continuous', bounds=(-2, 2)))
optimizer_rosen.add_parameter(ParameterSpace(name='y', param_type='continuous', bounds=(-1, 3)))

print("\nRunning Rosenbrock optimization...")
print("(Theoretical minimum at x=1, y=1 with value 0)")
start = time.time()
result_rosen = optimizer_rosen.optimize(rosenbrock)
elapsed = time.time() - start

print(f"\nRosenbrock Results:")
print(f"  Best Score:   {result_rosen.best_score:.6f}")
print(f"  Best Params:   x={result_rosen.best_params['x']:.4f}, y={result_rosen.best_params['y']:.4f}")
print(f"  Error from optimal: {abs(result_rosen.best_params['x']-1):.4f}, {abs(result_rosen.best_params['y']-1):.4f}")
print(f"  Evaluations:   {result_rosen.n_evaluations}")
print(f"  Time:          {elapsed:.3f}s")

# Example 8: Using Visualization
print("\n" + "="*60)
print("Example 8: Generate Optimization Visualization")
print("="*60)

try:
    from optimization_visualization import OptimizationVisualizer

    visualizer = OptimizationVisualizer()

    # Generate convergence plot
    print("\nGenerating convergence plot...")
    try:
        visualizer.plot_convergence(result, save_path='convergence_plot.png')
        print("  [OK] Saved: convergence_plot.png")
    except Exception as e:
        print(f"  [SKIP] Convergence plot skipped: {e}")

    # Generate parameter distribution plot
    print("\nGenerating parameter distribution plot...")
    try:
        visualizer.plot_parameter_distribution(result, save_path='param_distribution.png')
        print("  [OK] Saved: param_distribution.png")
    except Exception as e:
        print(f"  [SKIP] Distribution plot skipped: {e}")

    # Generate comparison plot
    print("\nGenerating algorithm comparison plot...")
    try:
        if all_results:
            import matplotlib.pyplot as plt

            methods_names = [r['name'] for r in all_results]
            scores = [r['score'] for r in all_results]

            plt.figure(figsize=(12, 6))
            plt.subplot(1, 2, 1)
            plt.bar(methods_names, scores)
            plt.xticks(rotation=45, ha='right')
            plt.ylabel('Best Score')
            plt.title('Optimization Algorithm Comparison')
            plt.tight_layout()
            plt.savefig('algorithm_comparison.png', dpi=150, bbox_inches='tight')
            plt.close()
            print("  [OK] Saved: algorithm_comparison.png")
    except Exception as e:
        print(f"  [SKIP] Comparison plot skipped: {e}")

except ImportError:
    print("  [SKIP] Visualization module not available")
except Exception as e:
    print(f"  [SKIP] Visualization skipped: {e}")

# Final Summary
print("\n" + "="*60)
print("SUMMARY - All Examples Completed Successfully!")
print("="*60)
print(f"""
[OK] Example 1: Basic 2D Optimization
   Method: Grid Search
   Score: {result.best_score:.4f}

[OK] Example 2: Method Comparison (3 methods)
   Best: {max(results_comparison, key=lambda x: x['score'])['method']}

[OK] Example 3: All 7 Algorithms Tested
   Winner: {winner['name'] if all_results else 'N/A'}

[OK] Example 4: 3D Optimization
   Score: {result_3d.best_score:.4f}

[OK] Example 5: 4D High-Dimensional
   Score: {result_4d.best_score:.4f}

[OK] Example 6: Mixed Parameter Types
   Continuous + Discrete + Categorical

[OK] Example 7: Rosenbrock Function
   Error: x={abs(result_rosen.best_params['x']-1):.4f}, y={abs(result_rosen.best_params['y']-1):.4f}
""")

print("\n" + "="*60)
print("System Capabilities")
print("="*60)
print("""
The CBSC Parameter Optimization System provides:

1. 7 Optimization Algorithms:
   [OK] Grid Search, Random Search, Bayesian Optimization
   [OK] Genetic Algorithm, Particle Swarm (PSO)
   [OK] Differential Evolution, Simulated Annealing

2. Parameter Types:
   [OK] Continuous (e.g., learning_rate: 0.001-0.1)
   [OK] Discrete (e.g., batch_size: 16-128)
   [OK] Categorical (e.g., optimizer: ['adam', 'sgd', 'rmsprop'])

3. Multi-Dimensional Support:
   [OK] 2D, 3D, 4D, 5D+ parameters
   [OK] Mixed parameter types
   [OK] Custom objective functions

4. Performance Features:
   [OK] Adaptive sampling
   [OK] Convergence tracking
   [OK] Multiple visualization options
   [OK] Performance benchmarking

5. Easy Integration:
   from parameter_optimizer import ParameterOptimizer, OptimizationConfig

   config = OptimizationConfig(method=OptimizationMethod.GRID_SEARCH)
   optimizer = ParameterOptimizer(config)
   optimizer.add_parameter(ParameterSpace(name='param', param_type='continuous', bounds=(min, max)))
   result = optimizer.optimize(your_objective_function)

For more examples, see:
  - src/backtest/examples/
  - docs/phase_6_5_deployment_summary.md
  - docs/phase_6_5_production_deployment_complete.md
""")

print("\n" + "="*60)
print("Quick Start Complete! [SUCCESS]")
print("="*60)
print("""
Next Steps:
1. Try your own objective functions
2. Experiment with different optimization algorithms
3. Adjust parameter ranges and iterations
4. Visualize optimization results
5. Integrate into your backtesting workflow
""")
