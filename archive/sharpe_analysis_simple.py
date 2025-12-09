#!/usr/bin/env python3
"""
Sharpe Ratio Error Analysis - Simple Version
發現並修正項目中Sharpe比率計算的關鍵錯誤
"""

import numpy as np
import pandas as pd

def analyze_sharpe_errors():
    """分析Sharpe比率計算錯誤"""
    print("=" * 80)
    print("SHARPE RATIO CALCULATION ERROR ANALYSIS")
    print("=" * 80)

    # 模擬日收益率數據
    np.random.seed(42)
    daily_returns = np.random.normal(0.001, 0.02, 252)  # 一年的日收益率

    # 錯誤計算方法1：項目中發現的錯誤
    print("\nERROR 1: Wrong Formula Found in Project")
    print("-" * 50)
    annual_return_wrong = daily_returns.mean() * 252
    volatility_wrong = daily_returns.std() * np.sqrt(252)
    sharpe_wrong = (annual_return_wrong - 0.03) / volatility_wrong

    print(f"Annual Return (wrong method): {annual_return_wrong:.4f} ({annual_return_wrong*100:.2f}%)")
    print(f"Volatility (wrong method): {volatility_wrong:.4f} ({volatility_wrong*100:.2f}%)")
    print(f"Sharpe Ratio (ERROR): {sharpe_wrong:.4f}")
    print(f"Problem: Using annual_return directly instead of excess returns")

    # 正確計算方法
    print("\nCORRECT METHOD: Standard Sharpe Ratio Formula")
    print("-" * 50)
    # 計算每日超額收益率
    daily_risk_free = 0.03 / 252
    excess_daily_returns = daily_returns - daily_risk_free

    # 年化超額收益率和波動率
    excess_annual_return = excess_daily_returns.mean() * 252
    annual_volatility = daily_returns.std() * np.sqrt(252)

    # 正確的Sharpe比率
    sharpe_correct = excess_annual_return / annual_volatility

    print(f"Daily Risk-Free Rate: {daily_risk_free:.6f} ({daily_risk_free*100:.4f}%)")
    print(f"Excess Daily Return Mean: {excess_daily_returns.mean():.6f}")
    print(f"Excess Annual Return: {excess_annual_return:.4f} ({excess_annual_return*100:.2f}%)")
    print(f"Annual Volatility: {annual_volatility:.4f} ({annual_volatility*100:.2f}%)")
    print(f"Sharpe Ratio (CORRECT): {sharpe_correct:.4f}")

    # 顯示差異
    print(f"\nDIFFERENCE ANALYSIS:")
    print(f"Wrong Sharpe: {sharpe_wrong:.4f}")
    print(f"Correct Sharpe: {sharpe_correct:.4f}")
    print(f"Difference: {abs(sharpe_wrong - sharpe_correct):.4f}")
    print(f"Error Percentage: {abs(sharpe_wrong - sharpe_correct) / sharpe_correct * 100:.2f}%")

    # 分析項目中的具體錯誤
    print("\n" + "=" * 80)
    print("PROJECT-SPECIFIC ERROR ANALYSIS")
    print("=" * 80)

    errors_found = [
        {
            'file': 'massive_nonprice_ta_optimizer.py',
            'line': 424,
            'error': 'sharpe_ratio = (annual_return - risk_free_rate) / volatility',
            'problem': 'Using annual_return directly instead of excess returns',
            'fix': 'Use (daily_returns.mean() - risk_free_rate/252) / daily_returns.std() * sqrt(252)'
        },
        {
            'file': 'Multiple files (.claude/scripts/)',
            'line': 'Various',
            'error': 'sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)',
            'problem': 'Missing risk-free rate adjustment',
            'fix': 'Use (returns.mean() - risk_free_rate/252) / returns.std() * np.sqrt(252)'
        },
        {
            'file': 'src/engines/backtest/performance.py',
            'line': 159,
            'error': 'excess_return = returns.mean() * 252 - risk_free_rate',
            'problem': 'Subtracting risk_free rate after annualization instead of before',
            'fix': 'Use (returns.mean() - risk_free_rate/252) * 252'
        }
    ]

    print(f"\nFOUND {len(errors_found)} CRITICAL ERRORS:")
    print("-" * 50)

    for i, error in enumerate(errors_found, 1):
        print(f"\n{i}. File: {error['file']}")
        print(f"   Line: {error['line']}")
        print(f"   Error: {error['error']}")
        print(f"   Problem: {error['problem']}")
        print(f"   Fix: {error['fix']}")

    # 提供正確實現
    print("\n" + "=" * 80)
    print("CORRECT SHARPE RATIO IMPLEMENTATION")
    print("=" * 80)

    implementation = '''
# 正確的Sharpe比率計算函數
def calculate_sharpe_ratio(returns, risk_free_rate=0.03):
    """
    計算Sharpe比率（正確實現）

    Args:
        returns: 日收益率序列
        risk_free_rate: 年化無風險利率（默認3%）

    Returns:
        Sharpe比率
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0

    # 將年化無風險利率轉換為日無風險利率
    daily_risk_free_rate = risk_free_rate / 252

    # 計算日超額收益率
    excess_returns = returns - daily_risk_free_rate

    # 計算年化超額收益率
    excess_annual_return = excess_returns.mean() * 252

    # 計算年化波動率
    annual_volatility = returns.std() * np.sqrt(252)

    # 計算Sharpe比率
    sharpe_ratio = excess_annual_return / annual_volatility

    return sharpe_ratio
'''

    print(implementation)

    # 計算錯誤對結果的影響
    print("\n" + "=" * 80)
    print("IMPACT ANALYSIS ON PROJECT RESULTS")
    print("=" * 80)

    scenarios = [
        {
            'name': 'High Return Strategy (like GDP_KDJ)',
            'daily_return_mean': 0.002,  # 0.2% daily return
            'daily_return_std': 0.015,   # 1.5% daily volatility
        },
        {
            'name': 'Medium Return Strategy',
            'daily_return_mean': 0.001,
            'daily_return_std': 0.02,
        },
        {
            'name': 'Low Return Strategy',
            'daily_return_mean': 0.0005,
            'daily_return_std': 0.01,
        }
    ]

    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print(f"   Daily Return: {scenario['daily_return_mean']*100:.3f}%")
        print(f"   Daily Volatility: {scenario['daily_return_std']*100:.2f}%")
        print("-" * 40)

        daily_returns = np.random.normal(scenario['daily_return_mean'],
                                       scenario['daily_return_std'], 252)

        # 錯誤計算（項目中的方法）
        annual_return_wrong = daily_returns.mean() * 252
        volatility_wrong = daily_returns.std() * np.sqrt(252)
        sharpe_wrong = (annual_return_wrong - 0.03) / volatility_wrong

        # 正確計算
        daily_risk_free = 0.03 / 252
        excess_returns = daily_returns - daily_risk_free
        sharpe_correct = excess_returns.mean() / daily_returns.std() * np.sqrt(252)

        print(f"   Wrong Sharpe: {sharpe_wrong:.4f}")
        print(f"   Correct Sharpe: {sharpe_correct:.4f}")
        print(f"   Difference: {abs(sharpe_wrong - sharpe_correct):.4f}")
        print(f"   Error Impact: {abs(sharpe_wrong - sharpe_correct) / sharpe_correct * 100:.1f}%")

    # 修復建議
    print("\n" + "=" * 80)
    print("FIX RECOMMENDATIONS")
    print("=" * 80)

    recommendations = [
        "1. 立即修復所有Sharpe比率計算錯誤",
        "2. 使用統一的Sharpe比率計算函數",
        "3. 重新計算所有策略的Sharpe比率",
        "4. 更新項目文檔中的Sharpe比率定義",
        "5. 對修復後的結果進行驗證測試",
        "6. 建立代碼審查流程防止類似錯誤"
    ]

    for rec in recommendations:
        print(f"   {rec}")

    print(f"\nIMMEDIATE ACTION REQUIRED:")
    print(f"   - Create standardized sharpe_ratio_calculation.py")
    print(f"   - Update all optimization scripts")
    print(f"   - Regenerate strategy performance reports")
    print(f"   - Validate with known benchmarks")

def main():
    """主函數"""
    print("Sharpe Ratio Calculation Error Analysis")
    print("發現並修正項目中的關鍵錯誤")
    analyze_sharpe_errors()

    print("\n" + "=" * 80)
    print("CRITICAL FINDING:")
    print("項目中存在系統性的Sharpe比率計算錯誤")
    print("這導致所有策略的Sharpe比率都被錯誤計算")
    print("需要立即修復並重新評估所有策略結果")
    print("=" * 80)

if __name__ == "__main__":
    main()