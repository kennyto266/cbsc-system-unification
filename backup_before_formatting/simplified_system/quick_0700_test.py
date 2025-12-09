#!/usr/bin/env python3
"""
Quick 0700.HK Backtest Test
"""

import sys
import os
import time
import numpy as np
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.dirname(__file__))

from src.api.stock_api import get_hk_stock_data
from src.indicators.core_indicators import CoreIndicators

def get_data():
    """Get 0700.HK data"""
    try:
        data = get_hk_stock_data('0700.HK', 1095)
        if data is not None and len(data) > 0:
            print(f"Got data: {len(data)} records")
            print(f"Date range: {data.index[0].date()} to {data.index[-1].date()}")
            print(f"Price range: ${data['low'].min():.2f} - ${data['high'].max():.2f}")
            return data
        else:
            print("Using synthetic data")
            return generate_synthetic_data()
    except Exception as e:
        print(f"Error: {e}, using synthetic data")
        return generate_synthetic_data()

def generate_synthetic_data():
    """Generate synthetic data"""
    dates = pd.date_range(end=datetime.now(), periods=1095, freq='D')
    np.random.seed(42)

    initial_price = 400.0
    returns = np.random.normal(0.0005, 0.02, len(dates))
    trend = np.linspace(0, 0.2, len(dates))
    price_changes = returns + trend/len(dates)
    prices = initial_price * np.exp(np.cumsum(price_changes))

    data = pd.DataFrame(index=dates)
    data['close'] = prices
    data['open'] = data['close'].shift(1) * (1 + np.random.normal(0, 0.005, len(dates)))
    data['high'] = np.maximum(data['open'], data['close']) * 1.02
    data['low'] = np.minimum(data['open'], data['close']) * 0.98
    data['volume'] = np.random.randint(10000000, 50000000, len(dates))
    data.loc[dates[0], 'open'] = initial_price

    print(f"Generated synthetic data: {len(data)} records")
    return data

def calculate_sharpe(returns, risk_free_rate=0.03):
    """Calculate Sharpe Ratio"""
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    excess_returns = returns - risk_free_rate/252
    return excess_returns.mean() / excess_returns.std() * np.sqrt(252)

def calculate_max_drawdown(returns):
    """Calculate Maximum Drawdown"""
    if len(returns) == 0:
        return 0.0
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    return drawdown.min()

def backtest_rsi(data, period, oversold, overbought):
    """RSI strategy backtest"""
    indicators = CoreIndicators()

    try:
        rsi = indicators.calculate_rsi(data['close'], period)
        signals = pd.Series(0, index=data.index)

        buy_signals = (rsi > oversold) & (rsi.shift(1) <= oversold)
        signals[buy_signals] = 1

        sell_signals = (rsi < overbought) & (rsi.shift(1) >= overbought)
        signals[sell_signals] = -1

        positions = signals.shift(1).fillna(0)
        returns = positions * data['close'].pct_change().fillna(0)

        total_return = (1 + returns).prod() - 1
        sharpe = calculate_sharpe(returns)
        max_dd = calculate_max_drawdown(returns)
        win_rate = len(returns[returns > 0]) / len(returns[returns != 0]) if len(returns[returns != 0]) > 0 else 0

        return {
            'strategy': 'RSI',
            'period': period,
            'oversold': oversold,
            'overbought': overbought,
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate
        }
    except Exception as e:
        return None

def backtest_macd(data, fast, slow, signal):
    """MACD strategy backtest"""
    indicators = CoreIndicators()

    try:
        macd_data = indicators.calculate_macd(data['close'], fast, slow, signal)
        signals = pd.Series(0, index=data.index)

        buy_signals = (macd_data['macd'] > macd_data['signal']) & (macd_data['macd'].shift(1) <= macd_data['signal'].shift(1))
        signals[buy_signals] = 1

        sell_signals = (macd_data['macd'] < macd_data['signal']) & (macd_data['macd'].shift(1) >= macd_data['signal'].shift(1))
        signals[sell_signals] = -1

        positions = signals.shift(1).fillna(0)
        returns = positions * data['close'].pct_change().fillna(0)

        total_return = (1 + returns).prod() - 1
        sharpe = calculate_sharpe(returns)
        max_dd = calculate_max_drawdown(returns)
        win_rate = len(returns[returns > 0]) / len(returns[returns != 0]) if len(returns[returns != 0]) > 0 else 0

        return {
            'strategy': 'MACD',
            'fast': fast,
            'slow': slow,
            'signal': signal,
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate
        }
    except Exception as e:
        return None

def test_strategies(data):
    """Test all strategies"""
    print("\n" + "="*50)
    print("TESTING STRATEGIES")
    print("="*50)

    results = []

    # Test RSI strategies
    print("\nTesting RSI strategies...")
    rsi_params = [
        (5, 20, 80), (10, 25, 75), (14, 30, 70),
        (20, 30, 70), (25, 35, 65), (30, 40, 60)
    ]

    for period, oversold, overbought in rsi_params:
        result = backtest_rsi(data, period, oversold, overbought)
        if result:
            results.append(result)
            if result['sharpe_ratio'] > 0.5:
                print(f"  Good RSI({period},{oversold},{overbought}): SR={result['sharpe_ratio']:.3f}")

    # Test MACD strategies
    print("\nTesting MACD strategies...")
    macd_params = [
        (12, 26, 9), (8, 24, 8), (10, 30, 12), (15, 35, 10)
    ]

    for fast, slow, signal in macd_params:
        if fast < slow:
            result = backtest_macd(data, fast, slow, signal)
            if result:
                results.append(result)
                if result['sharpe_ratio'] > 0.3:
                    print(f"  Good MACD({fast},{slow},{signal}): SR={result['sharpe_ratio']:.3f}")

    return results

def analyze_results(results):
    """Analyze and display results"""
    if not results:
        print("No valid results found")
        return

    results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)

    print("\n" + "="*60)
    print("TOP STRATEGIES BY SHARPE RATIO")
    print("="*60)

    print(f"{'Rank':<4} {'Strategy':<8} {'Params':<15} {'Sharpe':<8} {'Max DD':<10} {'Return':<8}")
    print("-" * 60)

    for i, result in enumerate(results[:10]):
        if result['strategy'] == 'RSI':
            params = f"{result['period']},{result['oversold']},{result['overbought']}"
        else:  # MACD
            params = f"{result['fast']},{result['slow']},{result['signal']}"

        print(f"{i+1:<4} {result['strategy']:<8} {params:<15} "
              f"{result['sharpe_ratio']:<8.3f} {result['max_drawdown']:<10.1%} "
              f"{result['total_return']:<8.1%}")

    # Best strategy
    best = results[0]
    print(f"\nBEST STRATEGY: {best['strategy']}")
    print(f"  Sharpe Ratio: {best['sharpe_ratio']:.3f}")
    print(f"  Max Drawdown: {best['max_drawdown']:.1%}")
    print(f"  Total Return: {best['total_return']:.1%}")
    print(f"  Win Rate: {best['win_rate']:.1%}")

    # Risk assessment
    if best['max_drawdown'] > -0.20:
        risk = "HIGH"
    elif best['max_drawdown'] > -0.15:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    print(f"  Risk Level: {risk}")

    # Recommendation
    if best['sharpe_ratio'] > 1.0:
        rec = "EXCELLENT - Recommended for testing"
    elif best['sharpe_ratio'] > 0.5:
        rec = "GOOD - Consider with risk management"
    else:
        rec = "FAIR - Needs optimization"

    print(f"  Recommendation: {rec}")

    return results

def main():
    """Main function"""
    print("=" * 80)
    print("0700.HK TENCENT - QUICK STRATEGY BACKTEST")
    print("=" * 80)
    print("Finding optimal parameter combinations for Sharpe Ratio and Max Drawdown")

    start_time = time.time()

    # Get data
    data = get_data()

    if data is None or len(data) < 100:
        print("Insufficient data")
        return

    print(f"Testing with {len(data)} days of data...")

    # Test strategies
    results = test_strategies(data)

    # Analyze results
    top_results = analyze_results(results)

    # Summary
    total_time = time.time() - start_time
    print(f"\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total execution time: {total_time:.1f} seconds")
    print(f"Strategies tested: {len(results)}")
    print(f"Data analyzed: {len(data)} days")

    if top_results:
        print(f"Best Sharpe Ratio: {top_results[0]['sharpe_ratio']:.3f}")
        print(f"Best Max Drawdown: {top_results[0]['max_drawdown']:.1%}")
        print(f"Best Total Return: {top_results[0]['total_return']:.1%}")

        # Save results
        try:
            df = pd.DataFrame(top_results)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = f'0700_results_{timestamp}.csv'
            df.to_csv(csv_file, index=False)
            print(f"\nResults saved to: {csv_file}")
        except Exception as e:
            print(f"Could not save results: {e}")

if __name__ == "__main__":
    main()