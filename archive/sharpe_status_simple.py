#!/usr/bin/env python3
"""
Simple Sharpe Ratio Status Check
簡化的Sharpe比率狀態檢查
"""

import numpy as np

def check_sharpe_status():
    """檢查Sharpe比率狀態"""
    print("=" * 80)
    print("SHARPE RATIO STATUS CHECK")
    print("=" * 80)

    # 1. 3%無風險利率配置情況
    print("\n1. 3% RISK-FREE RATE CONFIGURATION:")
    print("-" * 50)

    configs = [
        ("CLAUDE.md", "計算正確的Sharpe Ratio，將無風險利率設為3%"),
        ("advanced_strategy_optimizer.py", "risk_free_rate: float = 0.03"),
        ("authentic_real_data_optimizer.py", "excess_returns = returns - 0.03/252"),
        ("massive_nonprice_ta_optimizer.py", "risk_free_rate = 0.03 (line 423)"),
        ("src/engines/backtest/performance.py", "risk_free_rate = 0.03 (line 158)")
    ]

    for file, config in configs:
        print(f"   {file}: {config}")

    # 2. 最新結果分析
    print("\n2. LATEST STRATEGY RESULTS:")
    print("-" * 50)

    # 從分析中獲取的數據
    latest_strategies = [
        {"name": "GD_KDJ_[10, 2]", "sharpe": 6.8199, "annual_return": 2.1706},
        {"name": "GD_KDJ_[9, 3]", "sharpe": 6.5600, "annual_return": None},
        {"name": "HB_RSI_[45]", "sharpe": 5.8900, "annual_return": None}
    ]

    for i, strategy in enumerate(latest_strategies, 1):
        sharpe = strategy['sharpe']
        print(f"{i}. {strategy['name']}")
        print(f"   Sharpe Ratio: {sharpe:.4f}")

        if sharpe > 3:
            print(f"   ⚠️  WARNING: Sharpe > 3 is extremely rare!")
        if sharpe > 5:
            print(f"   ⚠️  CRITICAL: Sharpe > 5 suggests calculation error!")

    # 3. 正確的Sharpe比率計算
    print("\n3. CORRECT SHARPE RATIO CALCULATION:")
    print("-" * 50)

    # 模擬數據
    np.random.seed(42)
    daily_returns = np.random.normal(0.001, 0.02, 245)  # 245天

    # 正確計算（3%無風險利率）
    risk_free_rate = 0.03
    daily_risk_free = risk_free_rate / 365
    excess_returns = daily_returns - daily_risk_free
    correct_sharpe = excess_returns.mean() / daily_returns.std() * np.sqrt(365)

    print(f"Risk-free rate: {risk_free_rate:.3f} (3%)")
    print(f"Daily risk-free: {daily_risk_free:.6f}")
    print(f"Correct Sharpe: {correct_sharpe:.4f}")
    print(f"✅ 3% risk-free rate properly applied")

    # 4. 項目中的錯誤
    print("\n4. PROJECT IMPLEMENTATION ERRORS:")
    print("-" * 50)

    print("MAJOR ERRORS FOUND:")
    print("❌ massive_nonprice_ta_optimizer.py line 406-407:")
    print("   Uses CAGR instead of arithmetic mean")
    print("   annual_return = (1 + total_return) ** (1/years) - 1")
    print("   Should be: annual_return = daily_returns.mean() * 365")

    print("\n❌ massive_nonprice_ta_optimizer.py line 424:")
    print("   Uses wrong annual return in Sharpe formula")
    print("   sharpe_ratio = (annual_return - risk_free_rate) / volatility")
    print("   Should be based on daily excess returns")

    print("\n❌ Multiple files missing risk-free rate:")
    print("   sharpe_ratio = returns.mean() / returns.std() * sqrt(252)")
    print("   Should be: (returns.mean() - 0.03/252) / returns.std() * sqrt(252)")

    # 5. 修復狀態
    print("\n5. FIX STATUS:")
    print("-" * 50)

    fix_status = [
        "🔧 3% risk-free rate: ✅ CONFIGURED in multiple files",
        "🔧 Sharpe formula: ❌ INCORRECT in key files",
        "🔧 Results validation: ❌ FAILED (Sharpe > 6 unrealistic)",
        "🔧 Immediate action: ❌ NEEDED"
    ]

    for status in fix_status:
        print(f"   {status}")

def main():
    """主函數"""
    print("Sharpe Ratio Status Check")
    print("檢查當前Sharpe比率和3%無風險利率使用情況")

    check_sharpe_status()

    print("\n" + "=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    print("📊 CURRENT STATUS:")
    print("   ✅ 3%無風險利率已在配置中正確設定")
    print("   ❌ 但Sharpe比率計算公式存在系統性錯誤")
    print("   ❌ 最新結果Sharpe > 6，表明計算有問題")
    print("   🚨 需要立即修復才能使用任何策略結果")
    print("\n💡 RECOMMENDATION:")
    print("   先修復計算錯誤，再重新運行所有優化")
    print("=" * 80)

if __name__ == "__main__":
    main()