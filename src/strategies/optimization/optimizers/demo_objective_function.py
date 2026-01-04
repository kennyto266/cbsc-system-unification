# src/strategies/optimization/optimizers/demo_objective_function.py
"""
Demo script for ObjectiveFunction
Shows how to use the objective function for strategy optimization
"""

import pandas as pd
import numpy as np
from src.strategies.optimization.optimizers.objective import ObjectiveFunction

def main():
    """Demonstrate objective function usage"""
    print("=" * 60)
    print("Objective Function Demo for Strategy Optimization")
    print("=" * 60)
    print()

    # Create sample return series (simulated strategy returns)
    np.random.seed(42)
    n_days = 252  # One trading year

    # Simulate a decent strategy with some volatility
    returns = pd.Series(
        np.random.normal(loc=0.0005, scale=0.015, size=n_days)  # ~12% annual return, ~24% vol
    )

    print("Sample Strategy Statistics:")
    print(f"  Total days: {n_days}")
    print(f"  Mean daily return: {returns.mean():.6f}")
    print(f"  Std daily return: {returns.std():.6f}")
    print()

    # Initialize objective function with default weights
    print("1. Default Weights (α=0.5, β=0.3, γ=0.2)")
    print("-" * 60)
    obj = ObjectiveFunction()
    metrics = obj.calculate_metrics(returns)

    print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.4f}")
    print(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")
    print(f"  Calmar Ratio: {metrics['calmar_ratio']:.4f}")
    print(f"  Composite Score: {metrics['composite_score']:.4f}")
    print(f"  Total Return: {metrics['total_return']:.2%}")
    print(f"  Win Rate: {metrics['win_rate']:.2%}")
    print()

    # Try different weight configurations
    print("2. Sharpe-Focused (α=0.7, β=0.2, γ=0.1)")
    print("-" * 60)
    obj_sharpe = ObjectiveFunction(alpha=0.7, beta=0.2, gamma=0.1)
    score_sharpe = obj_sharpe.calculate_score(returns)
    print(f"  Composite Score: {score_sharpe:.4f}")
    print()

    print("3. Risk-Averse (α=0.3, β=0.6, γ=0.1)")
    print("-" * 60)
    obj_risk = ObjectiveFunction(alpha=0.3, beta=0.6, gamma=0.1)
    score_risk = obj_risk.calculate_score(returns)
    print(f"  Composite Score: {score_risk:.4f}")
    print()

    print("4. Balanced (α=0.4, β=0.3, γ=0.3)")
    print("-" * 60)
    obj_balanced = ObjectiveFunction(alpha=0.4, beta=0.3, gamma=0.3)
    score_balanced = obj_balanced.calculate_score(returns)
    print(f"  Composite Score: {score_balanced:.4f}")
    print()

    # Compare scores
    print("5. Score Comparison")
    print("-" * 60)
    print(f"  Default:  {metrics['composite_score']:.4f}")
    print(f"  Sharpe:   {score_sharpe:.4f}")
    print(f"  Risk:     {score_risk:.4f}")
    print(f"  Balanced: {score_balanced:.4f}")
    print()

    # Edge case handling
    print("6. Edge Case Handling")
    print("-" * 60)

    # Empty returns
    empty_returns = pd.Series([])
    score_empty = obj.calculate_score(empty_returns)
    print(f"  Empty returns score: {score_empty:.4f}")

    # Zero volatility
    constant_returns = pd.Series([0.01] * 100)
    score_constant = obj.calculate_score(constant_returns)
    print(f"  Constant returns score: {score_constant:.4f}")
    print()

    print("=" * 60)
    print("Demo Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
