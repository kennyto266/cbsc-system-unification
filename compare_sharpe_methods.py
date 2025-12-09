#!/usr/bin/env python3
"""
比較修正前後的夏普比率計算方法
"""

import sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')

def calculate_sharpe_original_wrong(returns, risk_free_rate=0.03):
    """原始的錯誤方法"""
    if len(returns) < 2:
        return 0.0

    # 錯誤的無風險利率轉換
    daily_risk_free = risk_free_rate / 365
    excess_returns = np.array(returns) - daily_risk_free

    # 錯誤的年化和統計方法
    sharpe_ratio = excess_returns.mean() / np.array(returns).std() * np.sqrt(365)
    return sharpe_ratio

def calculate_sharpe_correct_new(returns, risk_free_rate=0.03):
    """修正後的正確方法"""
    if len(returns) < 2:
        return 0.0

    # 正確的複利計算
    daily_rf = (1 + risk_free_rate) ** (1/252) - 1

    # 計算超額回報
    excess_returns = np.array(returns) - daily_rf

    # 使用樣本標準差
    mean_excess = np.mean(excess_returns)
    std_excess = np.std(excess_returns, ddof=1)

    if std_excess == 0:
        return 0.0

    # 正確的年化
    sharpe = (mean_excess * 252) / (std_excess * np.sqrt(252))
    return sharpe

def main():
    print("Sharpe Ratio Method Comparison")
    print("=" * 50)

    # 創建不同的測試場景
    test_scenarios = [
        {
            'name': 'High Volatility Strategy',
            'returns': np.random.normal(0.001, 0.03, 252),  # 高波動率
            'expected_sharpe': '1.0-2.0'
        },
        {
            'name': 'Low Volatility Strategy',
            'returns': np.random.normal(0.0008, 0.01, 252),  # 低波動率
            'expected_sharpe': '1.5-3.0'
        },
        {
            'name': 'Conservative Strategy',
            'returns': np.random.normal(0.0005, 0.008, 252),  # 保守策略
            'expected_sharpe': '1.0-2.0'
        }
    ]

    for scenario in test_scenarios:
        print(f"\n{scenario['name']}:")
        print("-" * 30)

        returns = scenario['returns']

        # 計算兩種方法
        sharpe_wrong = calculate_sharpe_original_wrong(returns)
        sharpe_correct = calculate_sharpe_correct_new(returns)

        # 計算差異
        difference = sharpe_wrong - sharpe_correct
        difference_pct = (difference / sharpe_correct * 100) if sharpe_correct != 0 else 0

        print(f"Original (Wrong):   {sharpe_wrong:.4f}")
        print(f"Corrected:          {sharpe_correct:.4f}")
        print(f"Difference:         {difference:+.4f}")
        print(f"Error Percentage:   {difference_pct:+.2f}%")
        print(f"Expected Range:     {scenario['expected_sharpe']}")

    # 特別測試：模擬"世界級"策略數據
    print(f"\nWorld-Class Strategy Simulation:")
    print("-" * 40)

    # 創建一個看似"世界級"的策略
    np.random.seed(42)
    world_class_returns = np.random.normal(0.002, 0.015, 252)  # 高回報，低波動

    sharpe_wrong = calculate_sharpe_original_wrong(world_class_returns)
    sharpe_correct = calculate_sharpe_correct_new(world_class_returns)

    print(f"Simulated Strategy Sharpe (Wrong):   {sharpe_wrong:.4f}")
    print(f"Simulated Strategy Sharpe (Correct): {sharpe_correct:.4f}")
    print(f"Adjustment Factor:                    {sharpe_correct/sharpe_wrong:.3f}")

    # 計算從3.672下降到多少
    if sharpe_wrong > 0:
        original_claimed_sharpe = 3.672
        adjusted_sharpe = original_claimed_sharpe * (sharpe_correct/sharpe_wrong)
        print(f"MB_KDJ_[10,2] Adjusted Sharpe:         {adjusted_sharpe:.3f}")
        print(f"Ranking Impact:                         {'High' if adjusted_sharpe < 2.5 else 'Medium' if adjusted_sharpe < 3.0 else 'Low'}")

if __name__ == "__main__":
    main()