#!/usr/bin/env python3
import sys
sys.path.append('.')
import pandas as pd
import numpy as np
import json
from datetime import datetime
from src.backtest.vectorbt_engine import VectorBTEngine

def main():
    print("=" * 60)
    print(" Simple Alpha Factor Discovery Demo")
    print("=" * 60)

    # Create realistic market data
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", periods=252, freq="D")

    # Generate price data with trend and volatility
    base_price = 400.0
    returns = np.random.normal(0.001, 0.02, 252)
    returns[50] = 0.05  # Add a jump
    returns[100] = -0.03  # Add a drop

    prices = [base_price]
    for r in returns:
        new_price = prices[-1] * (1 + r)
        prices.append(max(new_price, base_price * 0.5))

    close = np.array(prices[:-1])
    high = close * 1.02
    low = close * 0.98
    open_price = np.roll(close, 1)
    open_price[0] = close[0]
    volume = np.ones(252) * 1000000

    data = pd.DataFrame({
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }, index=dates)

    print(f"Generated {len(data)} days of market data")
    print(f"Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
    print(f"Total return: {(data['close'].iloc[-1]/data['close'].iloc[0] - 1):.2%}")

    # Test strategies
    engine = VectorBTEngine()
    strategies = [
        ("RSI_MEAN_REVERSION", {"period": 14, "oversold": 30, "overbought": 70}),
        ("MACD_CROSSOVER", {"fast": 12, "slow": 26, "signal": 9}),
        ("DUAL_MOVING_AVERAGE", {"short_period": 10, "long_period": 30}),
        ("BOLLINGER_BANDS", {"period": 20, "std_dev": 2}),
        ("MOMENTUM_BREAKOUT", {"period": 14, "threshold": 0.02}),
    ]

    print("\nTesting strategies...")
    print("-" * 50)

    results = []
    for i, (strategy, params) in enumerate(strategies, 1):
        try:
            result = engine.backtest_strategy(data, strategy, params)

            # Quality score
            score = 0
            if result.total_return > 0:
                score += min(result.total_return * 50, 40)
            if 0 < result.sharpe_ratio < 10:
                score += result.sharpe_ratio * 10
            if result.win_rate > 0.5:
                score += result.win_rate * 20

            results.append({
                "strategy": strategy,
                "params": params,
                "total_return": result.total_return,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown": result.max_drawdown,
                "win_rate": result.win_rate,
                "total_trades": result.total_trades,
                "quality_score": score
            })

            print(f"{i:2d}. {strategy:25s} | Return: {result.total_return:7.1%} | "
                  f"Sharpe: {result.sharpe_ratio:6.2f} | Win: {result.win_rate:5.1%} | "
                  f"Quality: {score:5.1f}")

        except Exception as e:
            print(f"{i:2d}. {strategy:25s} | ERROR: {str(e)[:20]}")

    # Results analysis
    print("\n" + "=" * 60)
    print(" Alpha Factor Analysis Results")
    print("=" * 60)

    valid_results = [r for r in results if r['total_trades'] > 0]

    if valid_results:
        top_strategies = sorted(valid_results, key=lambda x: x['quality_score'], reverse=True)[:3]

        print("\nTop 3 Alpha Factors:")
        print("-" * 40)
        for i, strategy in enumerate(top_strategies, 1):
            params_str = ", ".join([f"{k}={v}" for k, v in strategy['params'].items()])
            print(f"{i}. {strategy['strategy']:25s}")
            print(f"   ({params_str})")
            print(f"   Quality: {strategy['quality_score']:6.2f} | Return: {strategy['total_return']:7.1%}")
            print(f"   Sharpe: {strategy['sharpe_ratio']:6.2f} | Win Rate: {strategy['win_rate']:5.1%}")
            print()

        # Portfolio suggestion
        total_score = sum(s['quality_score'] for s in top_strategies)
        print("Portfolio Allocation:")
        print("-" * 25)
        for strategy in top_strategies:
            weight = strategy['quality_score'] / total_score
            print(f"{strategy['strategy']:20s}: {weight:5.1%}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"simple_alpha_results_{timestamp}.json"

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "strategies_tested": len(strategies),
            "valid_strategies": len(valid_results),
            "top_strategies": top_strategies if valid_results else [],
            "all_results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {result_file}")
    print("Alpha Factor Discovery Complete!")

if __name__ == "__main__":
    main()