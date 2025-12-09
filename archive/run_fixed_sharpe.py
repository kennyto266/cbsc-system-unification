#!/usr/bin/env python3
"""
Run Fixed Sharpe Ratio Optimization
運行修復後的Sharpe比率優化
"""

import numpy as np
import pandas as pd
import requests
import json
from datetime import datetime

def main():
    """主函數"""
    print("=" * 80)
    print("FIXED SHARPE RATIO OPTIMIZATION")
    print("修復Sharpe比率計算錯誤並重新運行優化")
    print("=" * 80)

    # 配置
    base_url = "http://18.180.162.113:9191/inst/getInst"
    risk_free_rate = 0.03  # 3%無風險利率

    print(f"\nCONFIGURATION:")
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

        # 生成測試策略
        print(f"\n2. TESTING FIXED STRATEGIES...")

        strategies = []

        # 策略1: RSI策略
        strategy1 = test_rsi_strategy(prices, risk_free_rate)
        strategies.append(strategy1)
        print(f"   RSI[14]: Sharpe={strategy1['sharpe']:.4f}, Return={strategy1['annual_return']*100:.2f}%")

        # 策略2: KDJ策略
        strategy2 = test_kdj_strategy(prices, risk_free_rate)
        strategies.append(strategy2)
        print(f"   KDJ[9,3]: Sharpe={strategy2['sharpe']:.4f}, Return={strategy2['annual_return']*100:.2f}%")

        # 策略3: 簡單移動平均
        strategy3 = test_ma_strategy(prices, risk_free_rate)
        strategies.append(strategy3)
        print(f"   MA[20,50]: Sharpe={strategy3['sharpe']:.4f}, Return={strategy3['annual_return']*100:.2f}%")

        # 按Sharpe排序
        strategies.sort(key=lambda x: x['sharpe'], reverse=True)

        # 顯示結果
        print(f"\n3. FIXED OPTIMIZATION RESULTS:")
        print("-" * 60)
        print(f"{'Rank':<4} {'Strategy':<15} {'Sharpe':<8} {'Return':<10} {'Drawdown':<10}")
        print("-" * 60)

        for i, strategy in enumerate(strategies, 1):
            name = strategy['name'][:14]
            sharpe = strategy['sharpe']
            ret = strategy['annual_return'] * 100
            dd = strategy['max_drawdown'] * 100
            print(f"{i:<4} {name:<15} {sharpe:>7.3f} {ret:>9.2f}% {dd:>9.2f}%")

        # 分析結果
        print(f"\n4. RESULT ANALYSIS:")
        print("-" * 40)

        best_strategy = strategies[0]
        print(f"Best Strategy: {best_strategy['name']}")
        print(f"Fixed Sharpe: {best_strategy['sharpe']:.4f}")
        print(f"Annual Return: {best_strategy['annual_return']*100:.2f}%")
        print(f"Max Drawdown: {best_strategy['max_drawdown']*100:.2f}%")

        # 檢查合理性
        if best_strategy['sharpe'] > 3:
            print(f"\nWARNING: Sharpe > 3 is still very high!")
            print(f"Further investigation needed for data quality.")
        elif best_strategy['sharpe'] > 2:
            print(f"\nGOOD: Excellent Sharpe ratio (>2)")
        else:
            print(f"\nOK: Reasonable Sharpe ratio")

        # 保存結果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            "optimization_type": "FIXED_SHARPE_RATIO",
            "risk_free_rate": risk_free_rate,
            "calculation_method": "Correct arithmetic mean with daily risk-free adjustment",
            "strategies_tested": len(strategies),
            "data_points": len(prices),
            "timestamp": timestamp,
            "strategies": strategies
        }

        filename = f"fixed_sharpe_results_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n5. RESULTS SAVED:")
        print(f"File: {filename}")
        print(f"Status: SUCCESS")

        print(f"\n" + "=" * 80)
        print("FIXED OPTIMIZATION COMPLETED!")
        print(f"✅ Sharpe calculation errors have been fixed")
        print(f"✅ 3% risk-free rate properly applied")
        print(f"✅ Results saved to {filename}")
        print("=" * 80)

    except Exception as e:
        print(f"ERROR: {e}")
        print("Optimization failed due to error")

def test_rsi_strategy(prices, risk_free_rate):
    """測試RSI策略"""
    prices_array = np.array(prices)

    # 計算RSI
    deltas = np.diff(prices_array)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    period = 14
    avg_gains = pd.Series(gains).rolling(period).mean()
    avg_losses = pd.Series(losses).rolling(period).mean()

    rs = avg_gains / (avg_losses + 1e-10)
    rsi = 100 - (100 / (1 + rs))

    # 生成信號
    signals = np.where(rsi < 30, 1, np.where(rsi > 70, -1, 0))

    # 計算收益率
    price_changes = np.diff(prices_array) / prices_array[:-1]
    strategy_returns = signals[:-1] * price_changes[1:]

    return calculate_metrics(strategy_returns, risk_free_rate, "RSI[14]")

def test_kdj_strategy(prices, risk_free_rate):
    """測試KDJ策略"""
    prices_array = np.array(prices)

    # 簡化的KDJ計算
    period = 9
    df = pd.DataFrame({'close': prices_array})
    high = df['close'].rolling(period).max()
    low = df['close'].rolling(period).min()
    rsv = (df['close'] - low) / (high - low + 1e-10) * 100
    k = pd.Series(rsv).ewm(alpha=1/period).mean()

    # 生成信號
    signals = np.where(k < 20, 1, np.where(k > 80, -1, 0))

    # 計算收益率
    price_changes = np.diff(prices_array) / prices_array[:-1]
    strategy_returns = signals[:-1] * price_changes[1:]

    return calculate_metrics(strategy_returns, risk_free_rate, "KDJ[9,3]")

def test_ma_strategy(prices, risk_free_rate):
    """測試移動平均策略"""
    prices_array = np.array(prices)

    # 計算移動平均
    ma_short = pd.Series(prices_array).rolling(20).mean()
    ma_long = pd.Series(prices_array).rolling(50).mean()

    # 生成信號（金叉死叉）
    signals = np.where(ma_short > ma_long, 1, -1)

    # 計算收益率
    price_changes = np.diff(prices_array) / prices_array[:-1]
    strategy_returns = signals[:-1] * price_changes[1:]

    return calculate_metrics(strategy_returns, risk_free_rate, "MA[20,50]")

def calculate_metrics(returns, risk_free_rate, strategy_name):
    """計算性能指標（修復版本）"""
    if len(returns) == 0:
        return {
            'name': strategy_name,
            'sharpe': 0.0,
            'annual_return': 0.0,
            'max_drawdown': 0.0,
            'volatility': 0.0
        }

    returns_array = np.array(returns)

    # 計算日無風險利率
    daily_risk_free = risk_free_rate / 365

    # 計算日超額收益率
    excess_returns = returns_array - daily_risk_free

    # 正確的Sharpe比率計算
    if returns_array.std() > 0:
        sharpe_ratio = excess_returns.mean() / returns_array.std() * np.sqrt(365)
    else:
        sharpe_ratio = 0.0

    # 年化回報（算術平均）
    annual_return = returns_array.mean() * 365

    # 波動率
    volatility = returns_array.std() * np.sqrt(365)

    # 最大回撤
    cumulative = np.cumprod(1 + returns_array)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0

    return {
        'name': strategy_name,
        'sharpe': sharpe_ratio,
        'annual_return': annual_return,
        'max_drawdown': max_drawdown,
        'volatility': volatility
    }

if __name__ == "__main__":
    main()