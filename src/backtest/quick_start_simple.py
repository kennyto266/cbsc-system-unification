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

# Example 3: Multi-Dimensional Optimization
print("\n" + "="*60)
print("Example 3: 3D Parameter Optimization")
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

# Example 4: Custom Objective Function
print("\n" + "="*60)
print("Example 4: Custom Objective Function")
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
start = time.time()
result_rosen = optimizer_rosen.optimize(rosenbrock)
elapsed = time.time() - start

print(f"\nRosenbrock Results:")
print(f"  Best Score:   {result_rosen.best_score:.6f}")
print(f"  Best Params:   {result_rosen.best_params}")
print(f"  Evaluations:   {result_rosen.n_evaluations}")
print(f"  Time:          {elapsed:.3f}s")

# Example 5: Using Visualization
print("\n" + "="*60)
print("Example 5: Generate Optimization Visualization")
print("="*60)

try:
    from optimization_visualization import OptimizationVisualizer

    visualizer = OptimizationVisualizer()

    # Generate convergence plot
    print("\nGenerating convergence plot...")
    visualizer.plot_convergence(result, save_path='convergence_plot.png')
    print("  Saved: convergence_plot.png")

    # Generate parameter distribution plot
    print("\nGenerating parameter distribution plot...")
    visualizer.plot_parameter_distribution(result, save_path='param_distribution.png')
    print("  Saved: param_distribution.png")

except Exception as e:
    print(f"  Visualization skipped: {e}")

# Summary
print("\n" + "="*60)
print("Summary")
print("="*60)
print("""
The CBSC Parameter Optimization System provides:

1. 7 Optimization Algorithms:
   - Grid Search, Random Search, Bayesian Optimization
   - Genetic Algorithm, Particle Swarm (PSO)
   - Differential Evolution, Simulated Annealing

2. Performance Features:
   - Multi-dimensional support (2D, 3D, 4D+)
   - Adaptive sampling
   - Performance benchmarking

3. Easy Integration:
   from parameter_optimizer import ParameterOptimizer, OptimizationConfig

   config = OptimizationConfig(method=OptimizationMethod.GRID_SEARCH)
   optimizer = ParameterOptimizer(config)
   optimizer.add_parameter(ParameterSpace(name='param', param_type='continuous', bounds=(min, max)))
   result = optimizer.optimize(your_objective_function)

For more examples, see:
  - src/backtest/examples/
  - docs/phase_6_5_deployment_summary.md
""")

print("\n" + "="*60)
print("Quick Start Complete!")
print("="*60)
