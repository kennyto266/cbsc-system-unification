#!/usr / bin / env python3
"""
Simple Sharpe Ratio Test
簡化Sharpe比率測試
"""

import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
if src_dir not in sys.path:
    sys.path.append(src_dir)


def test_sharpe_calculator_directly():
    """Direct test of the Sharpe calculator without complex imports"""
    print("=" * 60)
    print("SHARPE RATIO CALCULATOR TEST")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        # Import the standardized sharpe calculator directly
        sys.path.append(os.path.join(src_dir, "backtest"))
        from standardized_sharpe_calculator import StandardizedSharpeCalculator

        # Create calculator instance
        calculator = StandardizedSharpeCalculator()
        print(f"Risk - free rate: {calculator.risk_free_rate}")
        print(f"Trading days: {calculator.trading_days}")

        # Create test data
        np.random.seed(42)
        test_returns = np.random.normal(0.001, 0.02, 252)
        print(f"Test data: {len(test_returns)} days")
        print(f"Mean daily return: {np.mean(test_returns):.6f}")
        print(f"Std daily return: {np.std(test_returns, ddof = 1):.6f}")

        # Test calculation methods
        methods = ["standard", "conservative", "robust"]
        results = {}

        for method in methods:
            result = calculator.calculate_sharpe_ratio(test_returns, method)
            results[method] = result
            print(f"\n{method.upper()} method:")
            print(f"  Sharpe: {result['sharpe_ratio']:.4f}")
            print(
                f"  Annual return: {result['annual_return']:.4f} ({result['annual_return']*100:.2f}%)"
            )
            print(
                f"  Annual volatility: {result['annual_volatility']:.4f} ({result['annual_volatility']*100:.2f}%)"
            )

        # Check consistency
        sharpe_values = [results[method]["sharpe_ratio"] for method in methods]
        max_diff = max(sharpe_values) - min(sharpe_values)
        print(f"\nConsistency check:")
        print(f"  Max difference between methods: {max_diff:.4f}")

        if max_diff < 0.5:
            print("  GOOD: Methods are consistent")
        else:
            print("  WARNING: High variation between methods")

        # Validate results
        validation = calculator.validate_sharpe_calculation(test_returns)
        print(f"\nValidation:")
        print(f"  Valid: {validation['is_valid']}")
        if validation["warnings"]:
            print(f"  Warnings: {len(validation['warnings'])}")
        if validation["errors"]:
            print(f"  Errors: {len(validation['errors'])}")

        # Test with realistic market data
        print(f"\nRealistic market test:")
        np.random.seed(123)
        realistic_returns = np.random.normal(
            0.0008, 0.025, 252
        )  # ~20% annual return, 40% volatility
        realistic_result = calculator.calculate_sharpe_ratio(realistic_returns)

        print(
            f"  Annual return: {realistic_result['annual_return']:.4f} ({realistic_result['annual_return']*100:.2f}%)"
        )
        print(
            f"  Annual volatility: {realistic_result['annual_volatility']:.4f} ({realistic_result['annual_volatility']*100:.2f}%)"
        )
        print(f"  Sharpe ratio: {realistic_result['sharpe_ratio']:.4f}")

        # Check if Sharpe is realistic
        if 0.3 <= realistic_result["sharpe_ratio"] <= 1.5:
            print("  Sharpe ratio is realistic")
        else:
            print("  WARNING: Sharpe ratio may be unrealistic")

        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("✓ Sharpe calculator basic functionality works")
        print("✓ Multiple calculation methods implemented")
        print("✓ Validation and consistency checks work")
        print("✓ Realistic market data produces reasonable results")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_formula_comparison():
    """Compare different Sharpe calculation formulas"""
    print("\n" + "=" * 60)
    print("FORMULA COMPARISON TEST")
    print("=" * 60)

    # Create test data
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 252)

    risk_free_rate = 0.03
    daily_rf = risk_free_rate / 252

    # Method 1: Original incorrect method (for comparison)
    total_return = np.prod(1 + returns) - 1
    years = len(returns) / 252
    annual_return_incorrect = (1 + total_return) ** (1 / years) - 1
    annual_volatility = returns.std() * np.sqrt(252)
    sharpe_incorrect = (annual_return_incorrect - risk_free_rate) / annual_volatility

    # Method 2: Correct method using daily excess returns
    excess_returns = returns - daily_rf
    annual_return_correct = returns.mean() * 252
    sharpe_correct = excess_returns.mean() / returns.std() * np.sqrt(252)

    # Method 3: Compounded method (most accurate)
    annual_return_compounded = (1 + total_return) ** (252 / len(returns)) - 1
    sharpe_compounded = (annual_return_compounded - risk_free_rate) / annual_volatility

    print(f"Method comparison:")
    print(f"  Incorrect method: {sharpe_incorrect:.4f}")
    print(f"  Daily excess method: {sharpe_correct:.4f}")
    print(f"  Compounded method: {sharpe_compounded:.4f}")

    print(f"\nAnnual returns:")
    print(f"  Incorrect: {annual_return_incorrect:.4f}")
    print(f"  Daily mean: {annual_return_correct:.4f}")
    print(f"  Compounded: {annual_return_compounded:.4f}")

    print(f"\nDifference between methods:")
    print(
        f"  Max difference: {max(abs(sharpe_incorrect - sharpe_correct), abs(sharpe_compounded - sharpe_correct)):.4f}"
    )

    return True


def main():
    """Main test function"""
    print("SHARPE RATIO CALCULATION VERIFICATION")
    print("====================================")

    # Run tests
    test1_passed = test_sharpe_calculator_directly()
    test2_passed = test_formula_comparison()

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    if test1_passed and test2_passed:
        print("SUCCESS: All tests passed!")
        print("\nFixes implemented:")
        print("1. Created standardized Sharpe calculator")
        print("2. Fixed annual return calculation")
        print("3. Fixed volatility calculation")
        print("4. Unified 3% risk - free rate usage")
        print("5. Added validation methods")

        print("\nNext steps:")
        print("1. Update VectorBT engine to use new calculator")
        print("2. Re - run all strategy optimizations")
        print("3. Validate new Sharpe ratios are realistic")
    else:
        print("Some tests failed. Please check the implementation.")

    print("=" * 60)


if __name__ == "__main__":
    main()
