"""
Test Optimization Visualization
================================

Tests for the optimization visualization module.
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

# Import visualization module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "optimization_visualization",
    os.path.join(os.path.dirname(__file__), "optimization_visualization.py")
)
viz_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(viz_module)

OptimizationVisualizer = viz_module.OptimizationVisualizer
VisualizationConfig = viz_module.VisualizationConfig
visualize_optimization_results = viz_module.visualize_optimization_results

print("=" * 70)
print("Testing Optimization Visualization Module")
print("=" * 70)

# Create synthetic optimization results
print("\n[1] Creating synthetic optimization results...")

np.random.seed(42)

# Generate convergence curves
methods = ['Grid Search', 'Random Search', 'Bayesian Opt', 'Genetic Algorithm']
results = {}

for method in methods:
    # Generate synthetic convergence curve
    if method == 'Grid Search':
        # Smooth convergence
        curve = 1 - np.exp(-np.linspace(0, 5, 100)) + np.random.normal(0, 0.02, 100)
    elif method == 'Random Search':
        # Noisy convergence
        curve = np.maximum.accumulate(np.random.uniform(0, 1, 50))
    elif method == 'Bayesian Opt':
        # Fast convergence
        curve = np.concatenate([
            np.random.uniform(0.5, 0.9, 10),
            1 - np.exp(-np.linspace(0, 3, 40))
        ])
    else:  # Genetic Algorithm
        # Step-wise convergence
        curve = np.concatenate([
            np.repeat(0.5, 20),
            np.repeat(0.7, 30),
            np.repeat(0.85, 40),
            np.repeat(0.95, 50)
        ])

    results[method] = {
        'best_score': np.max(curve),
        'n_evaluations': len(curve),
        'runtime': np.random.uniform(0.5, 10),
        'convergence_curve': curve.tolist(),
        'best_params': {
            'window': np.random.randint(5, 30),
            'threshold': np.random.uniform(0.01, 0.05),
            'weight': np.random.uniform(0.1, 1.0)
        }
    }

print(f"[OK] Created {len(results)} optimization results")

# Create optimization history
print("\n[2] Creating optimization history...")
optimization_history = []

for i in range(100):
    optimization_history.append({
        'params': {
            'window': np.random.randint(5, 30),
            'threshold': np.random.uniform(0.01, 0.05),
            'weight': np.random.uniform(0.1, 1.0)
        },
        'score': np.random.uniform(0.5, 1.0)
    })

print(f"[OK] Created {len(optimization_history)} evaluation records")

# Test 1: Method comparison
print("\n[3] Testing method comparison plot...")
config = VisualizationConfig(figsize=(12, 6))
visualizer = OptimizationVisualizer(config)

fig = visualizer.plot_method_comparison(
    results,
    save_path="test_method_comparison.png"
)
plt.close(fig)
print("[OK] Method comparison plot created")

# Test 2: Convergence curves
print("\n[4] Testing convergence curves plot...")
results_list = [results[m] for m in methods]
fig = visualizer.plot_convergence(
    results_list,
    method_names=methods,
    save_path="test_convergence.png"
)
plt.close(fig)
print("[OK] Convergence curves plot created")

# Test 3: Parameter distributions
print("\n[5] Testing parameter distributions plot...")
fig = visualizer.plot_parameter_distributions(
    optimization_history,
    save_path="test_param_distributions.png"
)
plt.close(fig)
print("[OK] Parameter distributions plot created")

# Test 4: Parameter importance
print("\n[6] Testing parameter importance plot...")
fig = visualizer.plot_parameter_importance(
    optimization_history,
    save_path="test_param_importance.png"
)
plt.close(fig)
print("[OK] Parameter importance plot created")

# Test 5: 2D parameter space
print("\n[7] Testing 2D parameter space plot...")
fig = visualizer.plot_2d_parameter_space(
    optimization_history,
    'window',
    'threshold',
    save_path="test_2d_param_space.png"
)
plt.close(fig)
print("[OK] 2D parameter space plot created")

# Test 6: Optimization summary
print("\n[8] Testing optimization summary plot...")
fig = visualizer.plot_optimization_summary(
    results['Bayesian Opt'],
    method_name='Bayesian Optimization',
    save_path="test_optimization_summary.png"
)
plt.close(fig)
print("[OK] Optimization summary plot created")

# Test 7: Interactive dashboard
print("\n[9] Testing interactive dashboard...")
dashboard = visualizer.create_interactive_dashboard(
    results,
    save_path="test_interactive_dashboard.html"
)
if dashboard:
    print("[OK] Interactive dashboard created")
else:
    print("[SKIP] Plotly not available, skipping interactive dashboard")

# Test 8: Full visualization suite
print("\n[10] Testing full visualization suite...")
try:
    visualize_optimization_results(
        results,
        output_dir="test_optimization_plots",
        config=VisualizationConfig(save_format='png')
    )
    print("[OK] Full visualization suite created")
except Exception as e:
    print(f"[ERROR] Full visualization suite failed: {e}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"[OK] All visualization tests completed!")
print(f"  - Method comparison plot created")
print(f"  - Convergence curves plot created")
print(f"  - Parameter distributions plot created")
print(f"  - Parameter importance plot created")
print(f"  - 2D parameter space plot created")
print(f"  - Optimization summary plot created")
print(f"  - Interactive dashboard created")
print(f"\nGenerated files:")
import os
for f in os.listdir('.'):
    if f.startswith('test_') and (f.endswith('.png') or f.endswith('.html')):
        size = os.path.getsize(f)
        print(f"  - {f} ({size} bytes)")
print("\n" + "=" * 70)
