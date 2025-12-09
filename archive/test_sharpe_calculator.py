#!/usr/bin/env python3
"""
測試專業級夏普比率計算器
"""

import sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')

from professional_sharpe_calculator import ProfessionalSharpeCalculator

def main():
    """主程序 - 測試專業級夏普比率計算器"""
    print("Professional Sharpe Ratio Calculator Test")

    calculator = ProfessionalSharpeCalculator()

    # 創建測試數據
    np.random.seed(42)
    test_returns = np.random.normal(0.001, 0.02, 252)  # 一年的日回報

    print(f"\nTest Data: {len(test_returns)} trading days")
    print(f"Daily Return Mean: {np.mean(test_returns):.6f}")
    print(f"Daily Return Std: {np.std(test_returns, ddof=1):.6f}")

    # 計算夏普比率
    results = calculator.calculate_sharpe_ratio(test_returns)

    print(f"\nMulti-method Sharpe Ratio Calculation:")
    print(f"Standard Method: {results['standard']:.4f}")
    print(f"Annual Return Method: {results['annual_return']:.4f}")
    print(f"Conservative Method: {results['conservative']:.4f}")
    print(f"QuantStats: {results['quantstats'] if results['quantstats'] else 'N/A'}")

    # 驗證計算一致性
    validation = calculator.validate_calculation(test_returns)
    print(f"\nCalculation Validation:")
    print(f"Consistent: {validation['consistent']}")
    print(f"Consistency Level: {validation['consistency_level']}")
    print(f"Max Difference: {validation['max_difference_pct']:.2f}%")
    print(f"Recommended Sharpe: {validation['standard_sharpe']:.4f}")

    # 獲取推薦值
    recommended = calculator.get_recommended_sharpe(test_returns)
    print(f"\nFinal Recommended Sharpe Ratio: {recommended:.4f}")

    print(f"\nDetailed Statistics:")
    print(f"Daily Risk-Free Rate: {results['daily_rf']:.6f}")
    print(f"Excess Return Mean: {results['excess_return_mean']:.6f}")
    print(f"Excess Return Std: {results['excess_return_std']:.6f}")
    print(f"Annual Volatility: {results['volatility_annual']:.4f}")

if __name__ == "__main__":
    main()