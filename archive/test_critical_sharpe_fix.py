#!/usr/bin/env python3
"""
測試夏普比率的關鍵修正：使用原始回報標準差
"""

import sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')

from professional_sharpe_calculator import ProfessionalSharpeCalculator

def calculate_sharpe_before_this_fix(returns, risk_free_rate=0.03):
    """我之前錯誤的方法 - 使用超額回報標準差"""
    if len(returns) < 2:
        return 0.0

    daily_rf = (1 + risk_free_rate) ** (1/252) - 1
    excess_returns = np.array(returns) - daily_rf

    # 錯誤：使用超額回報的標準差
    mean_excess = np.mean(excess_returns)
    std_excess = np.std(excess_returns, ddof=1)

    sharpe = (mean_excess * 252) / (std_excess * np.sqrt(252))
    return sharpe

def calculate_sharpe_correct_now(returns, risk_free_rate=0.03):
    """現在正確的方法 - 使用原始回報標準差"""
    if len(returns) < 2:
        return 0.0

    # 計算年化回報率
    annual_return = (1 + np.mean(returns))**252 - 1

    # 計算年化無風險利率
    annual_rf = risk_free_rate

    # 正確：使用原始回報的標準差
    annual_volatility = np.std(returns, ddof=1) * np.sqrt(252)

    if annual_volatility == 0:
        return 0.0

    sharpe = (annual_return - annual_rf) / annual_volatility
    return sharpe

def main():
    print("Testing Critical Sharpe Ratio Fix")
    print("=" * 50)
    print("Focus: Use original returns std instead of excess returns std")
    print()

    calculator = ProfessionalSharpeCalculator()

    # 創建不同的測試場景
    test_scenarios = [
        {
            'name': 'High Return Strategy',
            'returns': np.random.normal(0.002, 0.025, 252),
            'description': '高回報中等波動率'
        },
        {
            'name': 'Low Volatility Strategy',
            'returns': np.random.normal(0.001, 0.015, 252),
            'description': '低波動率策略'
        },
        {
            'name': 'Volatile Strategy',
            'returns': np.random.normal(0.0005, 0.04, 252),
            'description': '高波動率策略'
        }
    ]

    print("Strategy Analysis:")
    print("-" * 80)

    for scenario in test_scenarios:
        returns = scenario['returns']

        # 計算三種方法
        sharpe_wrong = calculate_sharpe_before_this_fix(returns)
        sharpe_correct = calculate_sharpe_correct_now(returns)

        # 使用專業計算器
        prof_results = calculator.calculate_sharpe_ratio(returns)
        prof_recommended = calculator.get_recommended_sharpe(returns)

        difference = sharpe_wrong - sharpe_correct
        diff_pct = (difference / sharpe_correct * 100) if sharpe_correct != 0 else 0

        print(f"\n{scenario['name']}:")
        print(f"Description: {scenario['description']}")
        print(f"Before fix (wrong std):   {sharpe_wrong:8.4f}")
        print(f"After fix (correct std): {sharpe_correct:8.4f}")
        print(f"Professional calculator:   {prof_recommended:8.4f}")
        print(f"Difference:               {difference:+8.4f}")
        print(f"Error percentage:         {diff_pct:+8.2f}%")

    # 特別分析：模擬MB_KDJ_[10,2]類型策略
    print(f"\n" + "=" * 80)
    print("MB_KDJ_[10,2] Strategy Simulation:")
    print("=" * 80)

    np.random.seed(42)
    # 創建一個看似高性能的策略（高回報，中等波動）
    mb_kdj_returns = np.random.normal(0.0018, 0.018, 252)  # 年化約 64%，波動率約 28%

    sharpe_wrong = calculate_sharpe_before_this_fix(mb_kdj_returns)
    sharpe_correct = calculate_sharpe_correct_now(mb_kdj_returns)
    prof_results = calculator.calculate_sharpe_ratio(mb_kdj_returns)
    prof_recommended = calculator.get_recommended_sharpe(mb_kdj_returns)

    print(f"Simulated MB_KDJ strategy:")
    print(f"Before this fix:           {sharpe_wrong:8.4f}")
    print(f"After this fix:            {sharpe_correct:8.4f}")
    print(f"Professional calculator:   {prof_recommended:8.4f}")

    # 計算對原始聲稱的影響
    if sharpe_wrong > 0:
        original_claimed = 3.672  # 原始聲稱
        adjustment_factor = sharpe_correct / sharpe_wrong
        adjusted_claimed = original_claimed * adjustment_factor

        print(f"\nImpact on Original Claims:")
        print(f"Original claimed Sharpe:   {original_claimed:.3f}")
        print(f"Adjustment factor:         {adjustment_factor:.3f}")
        print(f"Adjusted claimed Sharpe:   {adjusted_claimed:.3f}")
        print(f"Total reduction:           {(original_claimed - adjusted_claimed)/original_claimed*100:.1f}%")

        ranking = "Still World-Class" if adjusted_claimed > 3.0 else "Excellent" if adjusted_claimed > 2.0 else "Good"
        print(f"New ranking category:      {ranking}")

if __name__ == "__main__":
    main()