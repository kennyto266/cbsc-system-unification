#!/usr/bin/env python3
"""
Alpha因子發現系統演示
"""

import sys
sys.path.append('.')
import pandas as pd
import numpy as np
from src.backtest.vectorbt_engine import VectorBTEngine
from src.backtest.safe_sharpe_calculator import safe_calculate_sharpe_ratio

def create_demo_data(days: int = 252) -> pd.DataFrame:
    """創建演示用的股價數據"""
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", periods=days, freq="D")

    # 模擬股價走勢
    base_price = 400.0
    returns = np.random.normal(0.001, 0.025, days)
    prices = [base_price]

    for i in range(1, days):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(max(new_price, base_price * 0.5))

    close = np.array(prices)
    high = close * 1.02
    low = close * 0.98
    open_price = np.roll(close, 1)
    open_price[0] = close[0]
    volume = np.ones(days) * 2000000

    return pd.DataFrame({
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }, index=dates)

def alpha_factor_discovery():
    """Alpha因子發現主函數"""
    print("=" * 80)
    print(" 專業Alpha因子發現系統演示")
    print("=" * 80)

    # 創建演示數據
    data = create_demo_data(252)
    print(f"成功生成 {len(data)} 條測試數據")

    # 創建VectorBT引擎
    engine = VectorBTEngine()

    print("\nAlpha因子發現測試中...")
    print("-" * 60)

    # 定義多個Alpha因子策略
    strategies = [
        ("RSI_MEAN_REVERSION", {"period": 14, "oversold": 30, "overbought": 70}),
        ("RSI_MEAN_REVERSION", {"period": 21, "oversold": 25, "overbought": 75}),
        ("RSI_MEAN_REVERSION", {"period": 7, "oversold": 20, "overbought": 80}),
        ("MACD_CROSSOVER", {"fast": 12, "slow": 26, "signal": 9}),
        ("MACD_CROSSOVER", {"fast": 5, "slow": 13, "signal": 5}),
        ("MACD_CROSSOVER", {"fast": 8, "slow": 21, "signal": 7}),
        ("DUAL_MOVING_AVERAGE", {"short_period": 10, "long_period": 30}),
        ("DUAL_MOVING_AVERAGE", {"short_period": 20, "long_period": 50}),
        ("DUAL_MOVING_AVERAGE", {"short_period": 15, "long_period": 45}),
        ("BOLLINGER_BANDS", {"period": 20, "std_dev": 2}),
        ("BOLLINGER_BANDS", {"period": 10, "std_dev": 1.5}),
        ("BOLLINGER_BANDS", {"period": 15, "std_dev": 2.2}),
        ("MOMENTUM_BREAKOUT", {"period": 14, "threshold": 0.02}),
        ("MOMENTUM_BREAKOUT", {"period": 21, "threshold": 0.015}),
        ("VOLATILITY_BREAKOUT", {"period": 20, "multiplier": 2.0}),
        ("VOLATILITY_BREAKOUT", {"period": 15, "multiplier": 1.8}),
    ]

    results = []

    # 測試每個策略
    for i, (strategy, params) in enumerate(strategies, 1):
        try:
            result = engine.backtest_strategy(data, strategy, params)

            # 使用安全的Sharpe計算驗證結果
            returns = data["close"].pct_change().dropna()
            safe_sharpe = safe_calculate_sharpe_ratio(returns, result.total_trades)

            # 計算質量評分 (綜合評分)
            score = 0
            if abs(result.sharpe_ratio) < 10:  # 合理的Sharpe範圍
                score += min(abs(result.sharpe_ratio) * 10, 50)  # Sharpe評分
            if result.total_return > 0:
                score += min(result.total_return * 20, 30)  # 回報評分
            if result.max_drawdown > -0.2:  # 控制回撤
                score += 20

            results.append({
                "strategy": strategy,
                "params": params,
                "total_return": result.total_return,
                "sharpe_ratio": result.sharpe_ratio,
                "safe_sharpe": safe_sharpe,
                "max_drawdown": result.max_drawdown,
                "win_rate": result.win_rate,
                "total_trades": result.total_trades,
                "quality_score": score
            })

            # 格式化輸出
            status = "OK" if result.sharpe_ratio < 10 else "WARN"
            print(f"{status} {i:2d}. {strategy:25s} | Return: {result.total_return:8.2%} | "
                  f"Sharpe: {result.sharpe_ratio:7.3f} | WinRate: {result.win_rate:5.1%} | "
                  f"Trades: {result.total_trades:3d} | Quality: {score:4.1f}")

        except Exception as e:
            print(f"FAIL {i:2d}. {strategy:25s} | Error: {str(e)[:30]}")

    print("\n" + "=" * 80)
    print(" Alpha因子分析結果")
    print("=" * 80)

    # 按質量評分排序
    valid_results = [r for r in results if r["sharpe_ratio"] < 10 and r["quality_score"] > 0]
    top_strategies = sorted(valid_results, key=lambda x: x["quality_score"], reverse=True)[:5]

    print("\n排名前5的Alpha因子:")
    print("-" * 80)
    for i, strategy in enumerate(top_strategies, 1):
        params_str = ", ".join([f"{k}={v}" for k, v in strategy["params"].items()])
        print(f"{i}. {strategy['strategy']:25s} ({params_str})")
        print(f"   Quality: {strategy['quality_score']:6.2f} | Return: {strategy['total_return']:8.2%} | "
              f"Sharpe: {strategy['sharpe_ratio']:7.3f} | MaxDD: {strategy['max_drawdown']:8.2%}")
        print(f"   WinRate: {strategy['win_rate']:6.1%} | Trades: {strategy['total_trades']:3d}")
        print()

    # 計算最佳組合權重
    print("智能組合建議:")
    print("-" * 40)
    if len(top_strategies) >= 2:
        total_score = sum(s["quality_score"] for s in top_strategies)
        for i, strategy in enumerate(top_strategies):
            weight = strategy["quality_score"] / total_score
            print(f"{strategy['strategy']:20s}: Weight {weight:5.1%} "
                  f"(Quality Score: {strategy['quality_score']:5.2f})")

    # 保存結果
    import json
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"alpha_factor_results_{timestamp}.json"

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "total_strategies_tested": len(strategies),
            "successful_strategies": len(valid_results),
            "top_strategies": top_strategies,
            "all_results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n結果已保存到: {result_file}")
    print("\nAlpha因子發現完成！系統已識別出最優策略組合。")

    return top_strategies

if __name__ == "__main__":
    alpha_factor_discovery()