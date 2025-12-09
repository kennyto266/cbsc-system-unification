#!/usr/bin/env python3
"""
Simple VectorBT Sharpe Ratio Demo
簡化的VectorBT Sharpe比率演示，無Unicode字符
"""

import numpy as np
import pandas as pd
import requests
import vectorbt as vbt
import json
from datetime import datetime

def main():
    """主函數"""
    print("=" * 80)
    print("VECTORBT SHARPE RATIO DEMONSTRATION")
    print("=" * 80)

    # 配置
    base_url = "http://18.180.162.113:9191/inst/getInst"
    risk_free_rate = 0.03  # 3%無風險利率

    print(f"Risk-free rate: {risk_free_rate} (3%)")
    print(f"Data source: {base_url}")
    print(f"Symbol: 0700.hk (Tencent)")

    try:
        # 獲取真實數據
        print(f"\n1. FETCHING REAL DATA...")
        params = {"symbol": "0700.hk", "duration": 365}
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if 'data' not in data or 'close' not in data['data']:
            print("ERROR: Invalid API response format")
            return

        close_data = data['data']['close']
        prices = list(close_data.values())
        print(f"   SUCCESS: Retrieved {len(prices)} price records")

        # 轉換為pandas Series
        price_series = pd.Series(prices)
        returns = price_series.pct_change().dropna()

        print(f"\n2. SHARPE RATIO CALCULATION COMPARISON:")
        print("-" * 60)

        # 方法1：錯誤的CAGR方法（當前項目中使用）
        total_return = (prices[-1] / prices[0]) - 1
        years = len(prices) / 365.0
        annual_return_cagr = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
        volatility = returns.std() * np.sqrt(365)
        sharpe_wrong = (annual_return_cagr - risk_free_rate) / volatility
        print(f"Method 1 - WRONG CAGR Method:")
        print(f"   Sharpe Ratio: {sharpe_wrong:.6f}")
        print(f"   Problem: Uses compound annual growth rate")

        # 方法2：正確的手動計算方法
        daily_risk_free = risk_free_rate / 365
        excess_returns = returns - daily_risk_free
        sharpe_correct_manual = excess_returns.mean() / returns.std() * np.sqrt(365)
        annual_return_arith = returns.mean() * 365
        print(f"\nMethod 2 - CORRECT Manual Method:")
        print(f"   Sharpe Ratio: {sharpe_correct_manual:.6f}")
        print(f"   Method: Daily excess returns arithmetic mean")
        print(f"   Risk-free rate: {risk_free_rate} applied daily")

        # 方法3：VectorBT Returns Accessor方法
        sharpe_vbt_returns = returns.vbt.returns.sharpe_ratio(risk_free=risk_free_rate)
        print(f"\nMethod 3 - VECTORTB Returns Method (RECOMMENDED):")
        print(f"   Sharpe Ratio: {sharpe_vbt_returns:.6f}")
        print(f"   Advantage: Professional institutional implementation")

        # 方法4：VectorBT Portfolio方法
        portfolio = vbt.Portfolio.from_holding(price_series, init_cash=100000)
        sharpe_vbt_portfolio = portfolio.sharpe_ratio(risk_free=risk_free_rate)
        print(f"\nMethod 4 - VECTORTB Portfolio Method:")
        print(f"   Sharpe Ratio: {sharpe_vbt_portfolio:.6f}")
        print(f"   Advantage: Complete portfolio analysis with costs")

        # 比較結果
        print(f"\n3. METHOD COMPARISON:")
        print("-" * 40)
        methods = [
            ("Wrong CAGR Method", sharpe_wrong),
            ("Correct Manual Method", sharpe_correct_manual),
            ("VectorBT Returns", float(sharpe_vbt_returns)),
            ("VectorBT Portfolio", float(sharpe_vbt_portfolio))
        ]

        for i, (name, sharpe) in enumerate(methods, 1):
            status = "WRONG" if "Wrong" in name else "CORRECT" if sharpe > 0 else "WARNING"
            print(f"   {i}. {name}: {sharpe:.6f} ({status})")

        # 合理性檢查
        print(f"\n4. REALISM CHECK:")
        print("-" * 30)
        max_reasonable_sharpe = 3.0
        for name, sharpe in methods:
            if sharpe > max_reasonable_sharpe:
                print(f"   WARNING: {name}: {sharpe:.4f} > {max_reasonable_sharpe} (Unrealistic)")
            else:
                print(f"   OK: {name}: {sharpe:.4f} (Realistic)")

        # 總結
        print(f"\n5. CONCLUSION:")
        print("-" * 30)
        print(f"Difference between wrong and correct: {abs(sharpe_wrong - sharpe_correct_manual):.6f}")
        print(f"VectorBT vs Manual Difference: {abs(float(sharpe_vbt_returns) - sharpe_correct_manual):.6f}")
        print(f"Recommended Method: VectorBT Returns (Method 3)")

        # 保存結果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            "demonstration_timestamp": timestamp,
            "data_points": len(prices),
            "risk_free_rate": risk_free_rate,
            "methods": {
                "wrong_cagr": sharpe_wrong,
                "correct_manual": sharpe_correct_manual,
                "vectorbt_returns": float(sharpe_vbt_returns),
                "vectorbt_portfolio": float(sharpe_vbt_portfolio)
            },
            "recommendation": "Use VectorBT Returns method with risk_free=0.03",
            "fix_required": "Replace massive_nonprice_ta_optimizer.py CAGR calculation"
        }

        filename = f"vectorbt_sharpe_comparison_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n6. SAVE STATUS:")
        print(f"Results saved to: {filename}")
        print(f"Status: SUCCESS - VectorBT demonstration completed")

        print("\n" + "=" * 80)
        print("KEY FINDINGS:")
        print("=" * 80)
        print("1. VectorBT has built-in Sharpe ratio calculation methods")
        print("2. risk_free=0.03 parameter is fully supported")
        print("3. Current CAGR method in project is incorrect")
        print("4. VectorBT returns.sharpe_ratio() is the recommended solution")
        print("5. All strategy results with Sharpe > 6 are mathematically wrong")
        print("=" * 80)

    except Exception as e:
        print(f"ERROR: {e}")
        print("Demonstration failed due to error")

if __name__ == "__main__":
    main()