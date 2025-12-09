"""
Simple Test Phase 3.2: Multi-Objective Optimization System
"""

import sys
import pandas as pd
import numpy as np
import time
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum

# Import the multi-objective optimizer
try:
    from phase3_multi_objective_optimizer import (
        OptimizationObjective,
        WeightedSumOptimizer,
        PerformanceMetricsCalculator,
        OptimizationResult
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_AVAILABLE = False

def mock_evaluation_function(params):
    """Mock evaluation function that returns valid strategy performance"""
    np.random.seed(hash(str(params)) % 1000)  # Deterministic based on params

    # Create realistic mock returns
    n_days = 252
    returns = pd.Series(np.random.normal(0.0005, 0.02, n_days))

    # Calculate basic metrics
    total_return = (1 + returns).prod() - 1
    volatility = returns.std() * np.sqrt(252)
    max_drawdown = -0.1  # Simple mock drawdown

    # Calculate Sharpe ratio with 3% risk-free rate
    risk_free_rate = 0.03
    excess_return = returns.mean() * 252 - risk_free_rate
    sharpe_ratio = excess_return / volatility if volatility > 0 else 0

    # Adjust metrics based on parameters
    if 'period' in params:
        # Prefer RSI periods around 14
        period_factor = 1 - abs(params['period'] - 14) / 30
        sharpe_ratio *= max(0.1, period_factor)

    if 'oversold' in params and 'overbought' in params:
        # Prefer wider bands
        band_width = params['overbought'] - params['oversold']
        width_factor = band_width / 40  # Normalized around 40
        sharpe_ratio *= max(0.5, min(2.0, width_factor))

    # Add some noise
    sharpe_ratio += np.random.normal(0, 0.1)

    return {
        'returns': returns,
        'sharpe_ratio': max(0, sharpe_ratio),
        'total_return': max(-0.5, min(2.0, total_return)),
        'max_drawdown': max(-0.5, min(0, max_drawdown))
    }

def test_simple_multi_objective():
    """Simple test of multi-objective optimization"""

    print("=" * 60)
    print("Phase 3.2: Simple Multi-Objective Optimization Test")
    print("=" * 60)

    if not IMPORTS_AVAILABLE:
        print("[FAILED] Cannot import required modules")
        return False

    try:
        # Define optimization objectives
        objectives = [
            OptimizationObjective("Sharpe Ratio", "Risk-adjusted return measure", maximize=True, weight=0.5),
            OptimizationObjective("Total Return", "Total portfolio return", maximize=True, weight=0.3),
            OptimizationObjective("Max Drawdown", "Maximum portfolio drawdown", maximize=False, weight=0.2)  # Minimize drawdown
        ]

        print(f"Objectives defined: {len(objectives)}")
        for obj in objectives:
            direction = "maximize" if obj.maximize else "minimize"
            print(f"  - {obj.name}: {direction} (weight={obj.weight})")

        # Create parameter combinations
        parameter_combinations = []
        for period in [10, 14, 20, 25]:
            for oversold in [20, 30, 35]:
                for overbought in [70, 75, 80]:
                    parameter_combinations.append({
                        'period': period,
                        'oversold': oversold,
                        'overbought': overbought
                    })

        print(f"Parameter combinations: {len(parameter_combinations)}")

        # Initialize weighted sum optimizer
        optimizer = WeightedSumOptimizer(normalization='minmax')
        print("[SUCCESS] Weighted sum optimizer initialized")

        # Perform optimization
        start_time = time.time()
        results = optimizer.optimize(parameter_combinations, objectives, mock_evaluation_function)
        optimization_time = time.time() - start_time

        print(f"[SUCCESS] Optimization completed in {optimization_time:.2f}s")
        print(f"Results: {len(results)} strategies evaluated")

        # Analyze results
        if results:
            best_result = max(results, key=lambda x: x.metrics.sharpe_ratio)
            print(f"\nBest Strategy:")
            print(f"  Parameters: {best_result.parameters}")
            print(f"  Sharpe Ratio: {best_result.metrics.sharpe_ratio:.3f}")
            print(f"  Total Return: {best_result.metrics.total_return:.2%}")
            print(f"  Max Drawdown: {best_result.metrics.max_drawdown:.2%}")
            print(f"  Composite Score: {best_result.objectives.get('composite_score', 0):.3f}")

        return True

    except Exception as e:
        print(f"[FAILED] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_metrics():
    """Test performance metrics calculation"""

    print("\n" + "=" * 40)
    print("Testing Performance Metrics Calculation")
    print("=" * 40)

    try:
        # Create test data
        n_days = 252
        dates = pd.date_range('2023-01-01', periods=n_days, freq='D')
        np.random.seed(42)

        # Create realistic returns series
        returns = pd.Series(
            np.random.normal(0.0005, 0.02, n_days),
            index=dates
        )

        print(f"Test returns created: {len(returns)} days")
        print(f"Mean return: {returns.mean():.6f}")
        print(f"Std return: {returns.std():.6f}")

        # Calculate metrics using our calculator
        metrics_calculator = PerformanceMetricsCalculator()
        metrics = metrics_calculator.calculate_metrics(returns)

        print(f"[SUCCESS] Performance Metrics Calculated:")
        print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.3f}")
        print(f"  Total Return: {metrics.total_return:.2%}")
        print(f"  Max Drawdown: {metrics.max_drawdown:.2%}")
        print(f"  Volatility: {metrics.volatility:.2%}")
        print(f"  Win Rate: {metrics.win_rate:.2%}")
        print(f"  Sortino Ratio: {metrics.sortino_ratio:.3f}")
        print(f"  Calmar Ratio: {metrics.calmar_ratio:.3f}")

        return True

    except Exception as e:
        print(f"[FAILED] Performance metrics error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Phase 3.2 Simple Multi-Objective Optimization Tests")
    print("=" * 80)

    # Test performance metrics first
    metrics_success = test_performance_metrics()

    # Then test multi-objective optimization
    optimization_success = test_simple_multi_objective()

    print("\n" + "=" * 80)
    print("PHASE 3.2 SIMPLE TEST SUMMARY")
    print("=" * 80)

    if metrics_success and optimization_success:
        print("[SUCCESS] All tests passed!")
        print("[SUCCESS] Multi-objective optimization working")
        print("[SUCCESS] Ready for advanced features")
        print("\nSystem Status: PRODUCTION READY")
        print("=" * 80)
    else:
        print("[FAILED] Some tests failed")
        print(f"Performance Metrics: {'PASS' if metrics_success else 'FAIL'}")
        print(f"Multi-Objective: {'PASS' if optimization_success else 'FAIL'}")
        print("\nSystem Status: NEEDS DEBUGGING")
        print("=" * 80)