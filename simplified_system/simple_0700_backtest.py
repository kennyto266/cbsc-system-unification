#!/usr / bin / env python3
"""
Simple 0700.HK Backtest System
Focus on testing different RSI, MACD, and MA parameter combinations for optimal Sharpe and MDD
"""

import json
import os
import sys
import time
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from src.api.stock_api import get_hk_stock_data
from src.indicators.core_indicators import CoreIndicators


def get_0700_data():
    """Get 0700.HK data"""
    print("=" * 60)
    print("0700.HK Tencent Data Acquisition")
    print("=" * 60)

    try:
        data = get_hk_stock_data("0700.HK", 1095)

        if data is not None and len(data) > 0:
            print(f"[OK] Got real data: {len(data)} records")
            print(f"    Date range: {data.index[0].date()} to {data.index[-1].date()}")
            print(
                f"    Price range: ${data['low'].min():.2f} - ${data['high'].max():.2f}"
            )
            print(f"    Current price: ${data['close'].iloc[-1]:.2f}")

            total_return = (data["close"].iloc[-1] / data["close"].iloc[0] - 1) * 100
            print(f"    Total return: {total_return:.2f}%")

            return data
        else:
            print("[WARN] Using synthetic data")
            return generate_synthetic_data()
    except Exception as e:
        print(f"[WARN] Real data failed: {e}, using synthetic")
        return generate_synthetic_data()


def generate_synthetic_data():
    """Generate synthetic data"""
    dates = pd.date_range(end = datetime.now(), periods = 1095, freq="D")
    np.random.seed(42)

    initial_price = 400.0
    returns = np.random.normal(0.0005, 0.02, len(dates))

    trend = np.linspace(0, 0.2, len(dates))
    price_changes = returns + trend / len(dates)
    prices = initial_price * np.exp(np.cumsum(price_changes))

    data = pd.DataFrame(index = dates)
    data["close"] = prices
    data["open"] = data["close"].shift(1) * (1 + np.random.normal(0, 0.005, len(dates)))
    data["high"] = np.maximum(data["open"], data["close"]) * (
        1 + np.abs(np.random.normal(0, 0.01, len(dates)))
    )
    data["low"] = np.minimum(data["open"], data["close"]) * (
        1 - np.abs(np.random.normal(0, 0.01, len(dates)))
    )
    data["volume"] = np.random.randint(10000000, 50000000, len(dates))

    data.loc[dates[0], "open"] = initial_price

    print(f"[OK] Generated synthetic data: {len(data)} records")
    return data


def calculate_sharpe(returns, risk_free_rate = 0.03):
    """Calculate Sharpe Ratio"""
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    excess_returns = returns - risk_free_rate / 252
    return excess_returns.mean() / excess_returns.std() * np.sqrt(252)


def calculate_max_drawdown(returns):
    """Calculate Maximum Drawdown"""
    if len(returns) == 0:
        return 0.0
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    return drawdown.min()


def backtest_rsi_strategy(data, period, oversold, overbought):
    """Simple RSI strategy backtest"""
    indicators = CoreIndicators()

    try:
        # Calculate RSI
        rsi = indicators.calculate_rsi(data["close"], period)

        # Generate signals
        signals = pd.Series(0, index = data.index)

        # Buy when RSI crosses above oversold
        buy_signals = (rsi > oversold) & (rsi.shift(1) <= oversold)
        signals[buy_signals] = 1

        # Sell when RSI crosses below overbought
        sell_signals = (rsi < overbought) & (rsi.shift(1) >= overbought)
        signals[sell_signals] = -1

        # Calculate returns
        positions = signals.shift(1).fillna(0)
        returns = positions * data["close"].pct_change().fillna(0)

        # Calculate performance metrics
        total_return = (1 + returns).prod() - 1
        sharpe = calculate_sharpe(returns)
        max_dd = calculate_max_drawdown(returns)
        win_rate = (
            len(returns[returns > 0]) / len(returns[returns != 0])
            if len(returns[returns != 0]) > 0
            else 0
        )
        trades_count = len(signals[signals != 0])

        return {
            "strategy": "RSI",
            "period": period,
            "oversold": oversold,
            "overbought": overbought,
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "win_rate": win_rate,
            "trades_count": trades_count,
        }

    except Exception as e:
        return None


def backtest_macd_strategy(data, fast, slow, signal):
    """Simple MACD strategy backtest"""
    indicators = CoreIndicators()

    try:
        # Calculate MACD
        macd_data = indicators.calculate_macd(data["close"], fast, slow, signal)

        # Generate signals
        signals = pd.Series(0, index = data.index)

        # Buy when MACD crosses above signal
        buy_signals = (macd_data["macd"] > macd_data["signal"]) & (
            macd_data["macd"].shift(1) <= macd_data["signal"].shift(1)
        )
        signals[buy_signals] = 1

        # Sell when MACD crosses below signal
        sell_signals = (macd_data["macd"] < macd_data["signal"]) & (
            macd_data["macd"].shift(1) >= macd_data["signal"].shift(1)
        )
        signals[sell_signals] = -1

        # Calculate returns
        positions = signals.shift(1).fillna(0)
        returns = positions * data["close"].pct_change().fillna(0)

        # Calculate performance metrics
        total_return = (1 + returns).prod() - 1
        sharpe = calculate_sharpe(returns)
        max_dd = calculate_max_drawdown(returns)
        win_rate = (
            len(returns[returns > 0]) / len(returns[returns != 0])
            if len(returns[returns != 0]) > 0
            else 0
        )
        trades_count = len(signals[signals != 0])

        return {
            "strategy": "MACD",
            "fast": fast,
            "slow": slow,
            "signal": signal,
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "win_rate": win_rate,
            "trades_count": trades_count,
        }

    except Exception as e:
        return None


def backtest_ma_strategy(data, short_period, long_period):
    """Simple Moving Average strategy backtest"""
    indicators = CoreIndicators()

    try:
        # Calculate moving averages
        short_ma = indicators.calculate_sma(data["close"], short_period)
        long_ma = indicators.calculate_sma(data["close"], long_period)

        # Generate signals
        signals = pd.Series(0, index = data.index)

        # Buy when short MA crosses above long MA
        buy_signals = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
        signals[buy_signals] = 1

        # Sell when short MA crosses below long MA
        sell_signals = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))
        signals[sell_signals] = -1

        # Calculate returns
        positions = signals.shift(1).fillna(0)
        returns = positions * data["close"].pct_change().fillna(0)

        # Calculate performance metrics
        total_return = (1 + returns).prod() - 1
        sharpe = calculate_sharpe(returns)
        max_dd = calculate_max_drawdown(returns)
        win_rate = (
            len(returns[returns > 0]) / len(returns[returns != 0])
            if len(returns[returns != 0]) > 0
            else 0
        )
        trades_count = len(signals[signals != 0])

        return {
            "strategy": "MA",
            "short_period": short_period,
            "long_period": long_period,
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "win_rate": win_rate,
            "trades_count": trades_count,
        }

    except Exception as e:
        return None


def test_rsi_combinations(data):
    """Test RSI parameter combinations"""
    print("\nTesting RSI Strategy Combinations...")
    print("=" * 50)

    rsi_periods = [5, 7, 10, 14, 20, 25, 30]
    oversold_levels = [20, 25, 30, 35]
    overbought_levels = [65, 70, 75, 80]

    results = []
    len(rsi_periods) * len(oversold_levels) * len(overbought_levels)
    current_test = 0

    for period in rsi_periods:
        for oversold in oversold_levels:
            for overbought in overbought_levels:
                current_test += 1

                result = backtest_rsi_strategy(data, period, oversold, overbought)
                if result:
                    results.append(result)

                    if result["sharpe_ratio"] > 1.0:
                        print(
                            f"  [EXCELLENT] RSI({period},{oversold},{overbought}): "
                            f"SR={result['sharpe_ratio']:.3f}, MDD={result['max_drawdown']:.1%}"
                        )

    # Sort by Sharpe ratio
    results.sort(key = lambda x: x["sharpe_ratio"], reverse = True)
    print(f"\nRSI testing complete. Best result:")
    if results:
        best = results[0]
        print(
            f"  RSI({best['period']}, {best['oversold']}, {best['overbought']}): "
            f"SR={best['sharpe_ratio']:.3f}, MDD={best['max_drawdown']:.1%}, "
            f"Return={best['total_return']:.1%}"
        )

    return results


def test_macd_combinations(data):
    """Test MACD parameter combinations"""
    print("\nTesting MACD Strategy Combinations...")
    print("=" * 50)

    fast_periods = [8, 10, 12, 15]
    slow_periods = [20, 24, 26, 30, 35]
    signal_periods = [6, 8, 9, 12]

    results = []

    for fast in fast_periods:
        for slow in slow_periods:
            if fast >= slow:
                continue
            for signal in signal_periods:

                result = backtest_macd_strategy(data, fast, slow, signal)
                if result:
                    results.append(result)

                    if result["sharpe_ratio"] > 1.0:
                        print(
                            f"  [EXCELLENT] MACD({fast},{slow},{signal}): "
                            f"SR={result['sharpe_ratio']:.3f}, MDD={result['max_drawdown']:.1%}"
                        )

    # Sort by Sharpe ratio
    results.sort(key = lambda x: x["sharpe_ratio"], reverse = True)
    print(f"\nMACD testing complete. Best result:")
    if results:
        best = results[0]
        print(
            f"  MACD({best['fast']}, {best['slow']}, {best['signal']}): "
            f"SR={best['sharpe_ratio']:.3f}, MDD={best['max_drawdown']:.1%}, "
            f"Return={best['total_return']:.1%}"
        )

    return results


def test_ma_combinations(data):
    """Test Moving Average parameter combinations"""
    print("\nTesting Moving Average Strategy Combinations...")
    print("=" * 50)

    short_periods = [5, 10, 15, 20, 25, 30]
    long_periods = [40, 50, 60, 80, 100, 120]

    results = []

    for short in short_periods:
        for long in long_periods:
            if short >= long:
                continue

            result = backtest_ma_strategy(data, short, long)
            if result:
                results.append(result)

                if result["sharpe_ratio"] > 0.8:
                    print(
                        f"  [GOOD] MA({short},{long}): "
                        f"SR={result['sharpe_ratio']:.3f}, MDD={result['max_drawdown']:.1%}"
                    )

    # Sort by Sharpe ratio
    results.sort(key = lambda x: x["sharpe_ratio"], reverse = True)
    print(f"\nMoving Average testing complete. Best result:")
    if results:
        best = results[0]
        print(
            f"  MA({best['short_period']}, {best['long_period']}): "
            f"SR={best['sharpe_ratio']:.3f}, MDD={best['max_drawdown']:.1%}, "
            f"Return={best['total_return']:.1%}"
        )

    return results


def analyze_results(rsi_results, macd_results, ma_results):
    """Analyze all results and find best strategies"""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE ANALYSIS")
    print("=" * 60)

    # Combine all results
    all_results = []
    if rsi_results:
        all_results.extend(rsi_results)
    if macd_results:
        all_results.extend(macd_results)
    if ma_results:
        all_results.extend(ma_results)

    if not all_results:
        print("[ERROR] No valid results")
        return

    # Sort by Sharpe ratio
    all_results.sort(key = lambda x: x["sharpe_ratio"], reverse = True)

    print(f"\nTotal strategies tested: {len(all_results)}")
    print(
        f"Data period: {len(all_results[0].get('returns', []))} days"
        if all_results
        else ""
    )

    # Show top 10 strategies
    print(f"\nTOP 10 STRATEGIES BY SHARPE RATIO:")
    print("-" * 80)
    print(
        f"{'Rank':<4} {'Strategy':<10} {'Parameters':<20} {'Sharpe':<8} {'Max DD':<10} {'Return':<8}"
    )
    print("-" * 80)

    for i, result in enumerate(all_results[:10]):
        # Format parameters
        if result["strategy"] == "RSI":
            params = f"({result['period']},{result['oversold']},{result['overbought']})"
        elif result["strategy"] == "MACD":
            params = f"({result['fast']},{result['slow']},{result['signal']})"
        else:  # MA
            params = f"({result['short_period']},{result['long_period']})"

        print(
            f"{i + 1:<4} {result['strategy']:<10} {params:<20} "
            f"{result['sharpe_ratio']:<8.3f} {result['max_drawdown']:<10.1%} "
            f"{result['total_return']:<8.1%}"
        )

    # Best strategy analysis
    best = all_results[0]
    print(f"\n🏆 BEST OVERALL STRATEGY:")
    print(f"   Strategy: {best['strategy']} {params}")
    print(f"   Sharpe Ratio: {best['sharpe_ratio']:.3f}")
    print(f"   Max Drawdown: {best['max_drawdown']:.1%}")
    print(f"   Total Return: {best['total_return']:.1%}")
    print(f"   Win Rate: {best['win_rate']:.1%}")
    print(f"   Number of Trades: {best['trades_count']}")

    # Risk assessment
    if best["max_drawdown"] > -0.30:
        risk = "VERY HIGH RISK"
    elif best["max_drawdown"] > -0.20:
        risk = "HIGH RISK"
    elif best["max_drawdown"] > -0.15:
        risk = "MEDIUM RISK"
    else:
        risk = "LOW RISK"

    print(f"   Risk Level: {risk}")

    # Investment recommendation
    if best["sharpe_ratio"] > 2.0:
        rec = "OUTSTANDING - Highly recommended for live trading"
    elif best["sharpe_ratio"] > 1.5:
        rec = "EXCELLENT - Recommended for paper trading first"
    elif best["sharpe_ratio"] > 1.0:
        rec = "GOOD - Consider with small position sizing"
    elif best["sharpe_ratio"] > 0.5:
        rec = "FAIR - Needs optimization before use"
    else:
        rec = "POOR - Not recommended"

    print(f"   Recommendation: {rec}")

    return all_results[:20]  # Return top 20


def save_results(data, results, timestamp):
    """Save results to files"""
    try:
        # Save JSON
        report = {
            "test_info": {
                "symbol": "0700.HK",
                "company": "Tencent Holdings Limited",
                "test_date": timestamp.isoformat(),
                "data_start": data.index[0].date().isoformat(),
                "data_end": data.index[-1].date().isoformat(),
                "data_records": len(data),
            },
            "price_info": {
                "start_price": float(data["close"].iloc[0]),
                "end_price": float(data["close"].iloc[-1]),
                "min_price": float(data["low"].min()),
                "max_price": float(data["high"].max()),
                "total_return": float(
                    (data["close"].iloc[-1] / data["close"].iloc[0] - 1) * 100
                ),
            },
            "strategies": results,
            "summary": {
                "total_strategies": len(results),
                "best_sharpe": results[0]["sharpe_ratio"] if results else 0,
                "best_strategy": results[0]["strategy"] if results else None,
                "best_mdd": results[0]["max_drawdown"] if results else 0,
            },
        }

        json_file = f'0700_hk_backtest_{timestamp.strftime("%Y%m%d_%H%M%S")}.json'
        with open(json_file, "w", encoding="utf - 8") as f:
            json.dump(report, f, indent = 2, ensure_ascii = False)

        # Save CSV
        if results:
            df = pd.DataFrame(results)
            csv_file = f'0700_hk_strategies_{timestamp.strftime("%Y%m%d_%H%M%S")}.csv'
            df.to_csv(csv_file, index = False)

            print(f"\n✅ Results saved:")
            print(f"   Detailed JSON: {json_file}")
            print(f"   Strategy CSV: {csv_file}")

            return json_file
    except Exception as e:
        print(f"[ERROR] Could not save results: {e}")
        return None


def main():
    """Main function"""
    print("=" * 80)
    print("0700.HK TENCENT - STRATEGY BACKTEST OPTIMIZATION")
    print("=" * 80)
    print("Finding optimal parameter combinations for Sharpe Ratio and Max Drawdown")

    start_time = time.time()
    timestamp = datetime.now()

    # Get data
    data = get_0700_data()

    if data is None or len(data) < 100:
        print("[ERROR] Insufficient data")
        return

    # Test strategies
    print(f"\nStarting optimization with {len(data)} days of data...")

    rsi_results = test_rsi_combinations(data)
    macd_results = test_macd_combinations(data)
    ma_results = test_ma_combinations(data)

    # Analyze results
    top_results = analyze_results(rsi_results, macd_results, ma_results)

    # Save results
    report_file = save_results(data, top_results, timestamp)

    # Summary
    total_time = time.time() - start_time
    total_strategies = len(rsi_results) + len(macd_results) + len(ma_results)

    print("\n" + "=" * 80)
    print("BACKTEST COMPLETION SUMMARY")
    print("=" * 80)
    print(f"⏱️  Total execution time: {total_time:.1f} seconds")
    print(f"📊 Data analyzed: {len(data)} days")
    print(f"🔢 Strategies tested: {total_strategies}")
    print(
        f"📈 Best Sharpe Ratio: {top_results[0]['sharpe_ratio']:.3f}"
        if top_results
        else "N / A"
    )
    print(
        f"📉 Best Max Drawdown: {top_results[0]['max_drawdown']:.1%}"
        if top_results
        else "N / A"
    )

    if report_file:
        print(f"📄 Detailed report: {report_file}")

    # Final recommendation
    if top_results and top_results[0]["sharpe_ratio"] > 1.5:
        print("\n🎯 EXCELLENT STRATEGY FOUND!")
        print("   This strategy shows strong potential for real - world application")
        print("   Recommended: Start with paper trading before committing real capital")
    elif top_results and top_results[0]["sharpe_ratio"] > 1.0:
        print("\n✅ GOOD STRATEGY IDENTIFIED")
        print("   Consider further optimization or combine with risk management")
    else:
        print("\n⚠️  STRATEGIES NEED IMPROVEMENT")
        print(
            "   Consider different timeframes, risk management, or strategy combinations"
        )

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
