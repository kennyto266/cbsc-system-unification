"""
Debug Phase 3.2 Multi-Objective Optimization
"""

import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

def debug_multi_objective():
    print("Debugging Multi-Objective Optimization System")
    print("=" * 60)

    # Create simple mock data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)

    returns = np.random.normal(0.001, 0.02, 100)
    cumulative = np.cumprod(1 + returns)
    equity_curve = pd.Series(cumulative, index=dates)

    print(f"Mock equity curve created: {len(equity_curve)} points")
    print(f"Return series length: {len(returns)}")
    print(f"Equity curve length: {len(equity_curve)}")

    try:
        # Try to calculate basic metrics
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0] - 1) * 100
        print(f"Total Return: {total_return:.2f}%")

        volatility = np.std(returns) * np.sqrt(252) * 100
        print(f"Annual Volatility: {volatility:.2f}%")

        # Simple Sharpe ratio (risk-free rate = 3%)
        excess_return = np.mean(returns) * 252 - 0.03
        sharpe_ratio = excess_return / (np.std(returns) * np.sqrt(252))
        print(f"Sharpe Ratio: {sharpe_ratio:.3f}")

        # Calculate drawdown
        peak = equity_curve.expanding().max()
        drawdown = (equity_curve - peak) / peak * 100
        max_drawdown = drawdown.min()
        print(f"Max Drawdown: {max_drawdown:.2f}%")

        print("[SUCCESS] Basic metrics calculation works")

        # Test array operations
        test_array1 = np.array([1, 2, 3, 4, 5])
        test_array2 = np.array([1, 2, 3])  # Different length
        print(f"Array 1 length: {len(test_array1)}")
        print(f"Array 2 length: {len(test_array2)}")

        # This should fail
        try:
            result = test_array1 + test_array2
            print("Arrays with different lengths were added - this shouldn't happen")
        except ValueError as e:
            print(f"Expected error with different length arrays: {e}")

        return True

    except Exception as e:
        print(f"[FAILED] Error in basic metrics: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_multi_objective()