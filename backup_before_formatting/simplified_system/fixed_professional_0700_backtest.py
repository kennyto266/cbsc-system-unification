#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
0700.HK Professional Backtest System - Fixed Version
Fixed encoding and module loading issues
"""

import sys
import os
import time
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Force UTF-8 encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from src.api.stock_api import get_hk_stock_data
from src.indicators.core_indicators import CoreIndicators

def get_0700_historical_data():
    """Get 0700.HK real historical data"""
    print("=" * 80)
    print("0700.HK TENCENT - PROFESSIONAL BACKTEST SYSTEM")
    print("=" * 80)
    print("Finding optimal parameter combinations for Sharpe Ratio and Max Drawdown")

    try:
        # Get 3 years historical data
        data = get_hk_stock_data('0700.HK', 1095)

        if data is not None and len(data) > 10:
            print(f"[OK] Got real data: {len(data)} records")
            print(f"    Date range: {data.index[0].date()} to {data.index[-1].date()}")
            print(f"    Price range: ${data['low'].min():.2f} - ${data['high'].max():.2f}")
            print(f"    Current price: ${data['close'].iloc[-1]:.2f}")

            # Calculate basic statistics
            total_return = (data['close'].iloc[-1] / data['close'].iloc[0] - 1) * 100
            volatility = data['close'].pct_change().std() * np.sqrt(252) * 100

            print(f"    Total return: {total_return:.2f}%")
            print(f"    Annual volatility: {volatility:.2f}%")

            return data
        else:
            print("[WARN] Cannot get real data, using synthetic data")
            return generate_synthetic_data()

    except Exception as e:
        print(f"[WARN] Real data acquisition failed: {e}")
        print("[INFO] Using high-quality synthetic data for backtest")
        return generate_synthetic_data()

def generate_synthetic_data():
    """Generate high-quality synthetic data"""
    print("Generating synthetic 0700.HK data...")

    dates = pd.date_range(end=datetime.now(), periods=1095, freq='D')
    np.random.seed(42)

    # Simulate Tencent stock price characteristics
    initial_price = 400.0
    returns = np.random.normal(0.0008, 0.025, len(dates))

    # Add trend and seasonality
    trend = np.linspace(0, 0.3, len(dates))
    seasonal = 0.05 * np.sin(2 * np.pi * np.arange(len(dates)) / 252)

    price_changes = returns + trend/len(dates) + seasonal/len(dates)
    prices = initial_price * np.exp(np.cumsum(price_changes))

    # Generate OHLCV data
    data = pd.DataFrame(index=dates)
    data['close'] = prices

    # Generate reasonable open, high, low prices
    daily_range = 0.02 + 0.01 * np.abs(np.random.randn(len(dates)))
    data['open'] = data['close'].shift(1) * (1 + np.random.normal(0, 0.005, len(dates)))
    data['high'] = np.maximum(data['open'], data['close']) * (1 + daily_range)
    data['low'] = np.minimum(data['open'], data['close']) * (1 - daily_range)

    # Generate volume
    base_volume = 20000000
    volume_variation = np.random.lognormal(0, 0.5, len(dates))
    data['volume'] = base_volume * volume_variation

    # Handle first day's open price
    data.loc[dates[0], 'open'] = initial_price

    print(f"[OK] Generated synthetic data: {len(data)} records")
    print(f"    Price range: ${data['low'].min():.2f} - ${data['high'].max():.2f}")

    return data

def calculate_sharpe_ratio(returns, risk_free_rate=0.03):
    """Calculate Sharpe Ratio (3% risk-free rate default)"""
    if len(returns) == 0 or returns.std() == 0:
        return 0.0

    excess_returns = returns - risk_free_rate/252
    sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)

    return sharpe

def calculate_max_drawdown(equity_curve):
    """Calculate Maximum Drawdown"""
    if len(equity_curve) == 0:
        return 0.0

    cumulative = (1 + equity_curve).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max

    return drawdown.min()

def backtest_rsi_strategy(data, period, oversold, overbought):
    """RSI strategy backtest implementation"""
    indicators = CoreIndicators()

    try:
        # Calculate RSI
        rsi = indicators.calculate_rsi(data['close'], period)

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Buy when RSI crosses above oversold
        buy_signals = (rsi > oversold) & (rsi.shift(1) <= oversold)
        signals[buy_signals] = 1

        # Sell when RSI crosses below overbought
        sell_signals = (rsi < overbought) & (rsi.shift(1) >= overbought)
        signals[sell_signals] = -1

        # Calculate returns
        positions = signals.shift(1).fillna(0)
        returns = positions * data['close'].pct_change().fillna(0)

        # Calculate performance metrics
        total_return = (1 + returns).prod() - 1
        sharpe = calculate_sharpe_ratio(returns)
        max_dd = calculate_max_drawdown(returns)
        win_rate = len(returns[returns > 0]) / len(returns[returns != 0]) if len(returns[returns != 0]) > 0 else 0
        trades_count = len(signals[signals != 0])

        return {
            'strategy': 'RSI_MEAN_REVERSION',
            'period': period,
            'oversold': oversold,
            'overbought': overbought,
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'trades_count': trades_count
        }

    except Exception as e:
        return None

def backtest_macd_strategy(data, fast, slow, signal):
    """MACD strategy backtest implementation"""
    indicators = CoreIndicators()

    try:
        # Calculate MACD
        macd_data = indicators.calculate_macd(data['close'], fast, slow, signal)

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Buy when MACD crosses above signal
        buy_signals = (macd_data['macd'] > macd_data['signal']) & (macd_data['macd'].shift(1) <= macd_data['signal'].shift(1))
        signals[buy_signals] = 1

        # Sell when MACD crosses below signal
        sell_signals = (macd_data['macd'] < macd_data['signal']) & (macd_data['macd'].shift(1) >= macd_data['signal'].shift(1))
        signals[sell_signals] = -1

        # Calculate returns
        positions = signals.shift(1).fillna(0)
        returns = positions * data['close'].pct_change().fillna(0)

        # Calculate performance metrics
        total_return = (1 + returns).prod() - 1
        sharpe = calculate_sharpe_ratio(returns)
        max_dd = calculate_max_drawdown(returns)
        win_rate = len(returns[returns > 0]) / len(returns[returns != 0]) if len(returns[returns != 0]) > 0 else 0
        trades_count = len(signals[signals != 0])

        return {
            'strategy': 'MACD_CROSSOVER',
            'fast': fast,
            'slow': slow,
            'signal': signal,
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'trades_count': trades_count
        }

    except Exception as e:
        return None

def backtest_ma_strategy(data, short_period, long_period):
    """Moving Average strategy backtest implementation"""
    indicators = CoreIndicators()

    try:
        # Calculate moving averages
        short_ma = indicators.calculate_sma(data['close'], short_period)
        long_ma = indicators.calculate_sma(data['close'], long_period)

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Buy when short MA crosses above long MA
        buy_signals = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
        signals[buy_signals] = 1

        # Sell when short MA crosses below long MA
        sell_signals = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))
        signals[sell_signals] = -1

        # Calculate returns
        positions = signals.shift(1).fillna(0)
        returns = positions * data['close'].pct_change().fillna(0)

        # Calculate performance metrics
        total_return = (1 + returns).prod() - 1
        sharpe = calculate_sharpe_ratio(returns)
        max_dd = calculate_max_drawdown(returns)
        win_rate = len(returns[returns > 0]) / len(returns[returns != 0]) if len(returns[returns != 0]) > 0 else 0
        trades_count = len(signals[signals != 0])

        return {
            'strategy': 'DUAL_MOVING_AVERAGE',
            'short_period': short_period,
            'long_period': long_period,
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'trades_count': trades_count
        }

    except Exception as e:
        return None

def backtest_bollinger_strategy(data, period, std_dev):
    """Bollinger Bands strategy backtest implementation"""
    indicators = CoreIndicators()

    try:
        # Calculate Bollinger Bands
        bb_data = indicators.calculate_bollinger_bands(data['close'], period, std_dev)

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Buy when price touches lower band
        buy_signals = data['close'] <= bb_data['lower_band']
        signals[buy_signals] = 1

        # Sell when price touches upper band
        sell_signals = data['close'] >= bb_data['upper_band']
        signals[sell_signals] = -1

        # Calculate returns
        positions = signals.shift(1).fillna(0)
        returns = positions * data['close'].pct_change().fillna(0)

        # Calculate performance metrics
        total_return = (1 + returns).prod() - 1
        sharpe = calculate_sharpe_ratio(returns)
        max_dd = calculate_max_drawdown(returns)
        win_rate = len(returns[returns > 0]) / len(returns[returns != 0]) if len(returns[returns != 0]) > 0 else 0
        trades_count = len(signals[signals != 0])

        return {
            'strategy': 'BOLLINGER_BANDS_MEAN_REVERSION',
            'period': period,
            'std_dev': std_dev,
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'trades_count': trades_count
        }

    except Exception as e:
        return None

def test_rsi_strategies(data):
    """Test RSI strategies with different parameter combinations"""
    print("\n" + "="*60)
    print("RSI STRATEGY OPTIMIZATION")
    print("="*60)

    # RSI parameter ranges
    rsi_periods = [5, 7, 10, 14, 20, 25, 30]
    oversold_levels = [20, 25, 30, 35]
    overbought_levels = [65, 70, 75, 80]

    results = []
    total_combinations = len(rsi_periods) * len(oversold_levels) * len(overbought_levels)

    print(f"Testing {total_combinations} RSI parameter combinations...")

    for period in rsi_periods:
        for oversold in oversold_levels:
            for overbought in overbought_levels:
                result = backtest_rsi_strategy(data, period, oversold, overbought)
                if result and result['sharpe_ratio'] > 0:
                    results.append(result)

                    # Show excellent results
                    if result['sharpe_ratio'] > 1.0:
                        print(f"  [EXCELLENT] RSI({period},{oversold},{overbought}): "
                              f"SR={result['sharpe_ratio']:.3f}, MDD={result['max_drawdown']:.1%}, "
                              f"Return={result['total_return']:.1%}")
                    elif result['sharpe_ratio'] > 0.5:
                        print(f"  [GOOD] RSI({period},{oversold},{overbought}): "
                              f"SR={result['sharpe_ratio']:.3f}, MDD={result['max_drawdown']:.1%}")

    # Sort and return best results
    if results:
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        print(f"\nRSI strategy testing complete. Tested {len(results)} valid combinations")

        # Show top 5 results
        print("\nTop 5 RSI Strategies:")
        for i, res in enumerate(results[:5]):
            print(f"{i+1}. RSI({res['period']}, {res['oversold']}, {res['overbought']}): "
                  f"SR={res['sharpe_ratio']:.3f}, MDD={res['max_drawdown']:.1%}, "
                  f"Return={res['total_return']:.1%}")

    return results

def test_macd_strategies(data):
    """Test MACD strategies with different parameter combinations"""
    print("\n" + "="*60)
    print("MACD STRATEGY OPTIMIZATION")
    print("="*60)

    # MACD parameter ranges
    fast_periods = [8, 10, 12, 15]
    slow_periods = [20, 24, 26, 30, 35]
    signal_periods = [6, 8, 9, 12]

    results = []

    print(f"Testing MACD parameter combinations...")

    for fast in fast_periods:
        for slow in slow_periods:
            if fast >= slow:
                continue

            for signal in signal_periods:
                result = backtest_macd_strategy(data, fast, slow, signal)
                if result and result['sharpe_ratio'] > 0:
                    results.append(result)

                    # Show excellent results
                    if result['sharpe_ratio'] > 0.8:
                        print(f"  [EXCELLENT] MACD({fast},{slow},{signal}): "
                              f"SR={result['sharpe_ratio']:.3f}, MDD={result['max_drawdown']:.1%}")

    # Sort and return best results
    if results:
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        print(f"\nMACD strategy testing complete. Tested {len(results)} valid combinations")

        # Show top 5 results
        print("\nTop 5 MACD Strategies:")
        for i, res in enumerate(results[:5]):
            print(f"{i+1}. MACD({res['fast']}, {res['slow']}, {res['signal']}): "
                  f"SR={res['sharpe_ratio']:.3f}, MDD={res['max_drawdown']:.1%}, "
                  f"Return={res['total_return']:.1%}")

    return results

def test_moving_average_strategies(data):
    """Test Moving Average strategies"""
    print("\n" + "="*60)
    print("MOVING AVERAGE STRATEGY OPTIMIZATION")
    print("="*60)

    # Moving Average parameter ranges
    short_periods = [5, 10, 15, 20, 25, 30]
    long_periods = [40, 50, 60, 80, 100, 120]

    results = []

    print(f"Testing Moving Average parameter combinations...")

    for short in short_periods:
        for long in long_periods:
            if short >= long:
                continue

            result = backtest_ma_strategy(data, short, long)
            if result and result['sharpe_ratio'] > 0:
                results.append(result)

                # Show excellent results
                if result['sharpe_ratio'] > 0.8:
                    print(f"  [EXCELLENT] MA({short},{long}): "
                          f"SR={result['sharpe_ratio']:.3f}, MDD={result['max_drawdown']:.1%}")

    # Sort and return best results
    if results:
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        print(f"\nMoving Average strategy testing complete. Tested {len(results)} valid combinations")

        # Show top 5 results
        print("\nTop 5 Moving Average Strategies:")
        for i, res in enumerate(results[:5]):
            print(f"{i+1}. MA({res['short_period']}, {res['long_period']}): "
                  f"SR={res['sharpe_ratio']:.3f}, MDD={res['max_drawdown']:.1%}, "
                  f"Return={res['total_return']:.1%}")

    return results

def test_bollinger_strategies(data):
    """Test Bollinger Bands strategies"""
    print("\n" + "="*60)
    print("BOLLINGER BANDS STRATEGY OPTIMIZATION")
    print("="*60)

    # Bollinger Bands parameter ranges
    periods = [10, 15, 20, 25, 30]
    std_devs = [1.5, 2.0, 2.5]

    results = []

    print(f"Testing Bollinger Bands parameter combinations...")

    for period in periods:
        for std_dev in std_devs:
            result = backtest_bollinger_strategy(data, period, std_dev)
            if result and result['sharpe_ratio'] > 0:
                results.append(result)

                # Show excellent results
                if result['sharpe_ratio'] > 0.8:
                    print(f"  [EXCELLENT] BB({period},{std_dev}): "
                          f"SR={result['sharpe_ratio']:.3f}, MDD={result['max_drawdown']:.1%}")

    # Sort and return best results
    if results:
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        print(f"\nBollinger Bands strategy testing complete. Tested {len(results)} valid combinations")

        # Show top 5 results
        print("\nTop 5 Bollinger Bands Strategies:")
        for i, res in enumerate(results[:5]):
            print(f"{i+1}. BB({res['period']}, {res['std_dev']}): "
                  f"SR={res['sharpe_ratio']:.3f}, MDD={res['max_drawdown']:.1%}, "
                  f"Return={res['total_return']:.1%}")

    return results

def analyze_comprehensive_results(all_results):
    """Analyze all strategies for best performance"""
    print("\n" + "="*80)
    print("COMPREHENSIVE STRATEGY ANALYSIS")
    print("="*80)

    # Combine all results
    combined_results = []
    for strategy_results in all_results:
        if strategy_results:
            combined_results.extend(strategy_results)

    if not combined_results:
        print("[WARN] No valid strategy results")
        return []

    # Sort by Sharpe Ratio
    combined_results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)

    print(f"Total strategies tested: {len(combined_results)}")

    # Show comprehensive top 10
    print("\nTop 10 Strategies:")
    print("-" * 100)
    print(f"{'Rank':<4} {'Strategy Type':<25} {'Parameters':<20} {'Sharpe':<8} {'Max DD':<10} {'Return':<8}")
    print("-" * 100)

    for i, res in enumerate(combined_results[:10]):
        strategy_name = res['strategy'].replace('_', ' ')

        # Format parameters
        if 'period' in res and 'oversold' in res:  # RSI
            params = f"({res['period']}, {res['oversold']}, {res['overbought']})"
        elif 'fast' in res:  # MACD
            params = f"({res['fast']}, {res['slow']}, {res['signal']})"
        elif 'short_period' in res:  # MA
            params = f"({res['short_period']}, {res['long_period']})"
        elif 'std_dev' in res:  # Bollinger Bands
            params = f"({res['period']}, {res['std_dev']})"
        else:
            params = "N/A"

        print(f"{i+1:<4} {strategy_name:<25} {params:<20} "
              f"{res['sharpe_ratio']:<8.3f} {res['max_drawdown']:<10.1%} "
              f"{res['total_return']:<8.1%}")

    # Analyze best strategy
    best_strategy = combined_results[0]
    print(f"\nBEST STRATEGY: {best_strategy['strategy']}")
    print(f"   Sharpe Ratio: {best_strategy['sharpe_ratio']:.3f}")
    print(f"   Max Drawdown: {best_strategy['max_drawdown']:.1%}")
    print(f"   Total Return: {best_strategy['total_return']:.1%}")

    # Risk assessment
    if best_strategy['max_drawdown'] > -0.25:
        risk_level = "HIGH RISK"
    elif best_strategy['max_drawdown'] > -0.15:
        risk_level = "MEDIUM RISK"
    else:
        risk_level = "LOW RISK"

    print(f"   Risk Level: {risk_level}")

    # Investment recommendation
    if best_strategy['sharpe_ratio'] > 2.0:
        recommendation = "OUTSTANDING - Recommended for live trading"
    elif best_strategy['sharpe_ratio'] > 1.5:
        recommendation = "EXCELLENT - Recommended for paper trading first"
    elif best_strategy['sharpe_ratio'] > 1.0:
        recommendation = "GOOD - Consider with small position sizing"
    elif best_strategy['sharpe_ratio'] > 0.5:
        recommendation = "FAIR - Needs optimization before use"
    else:
        recommendation = "POOR - Not recommended"

    print(f"   Recommendation: {recommendation}")

    return combined_results[:20]

def save_comprehensive_results(data, all_results, top_strategies):
    """Save comprehensive test results"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Prepare result data
    report_data = {
        'test_info': {
            'symbol': '0700.HK',
            'company': 'Tencent Holdings Limited',
            'test_date': datetime.now().isoformat(),
            'data_period': {
                'start': data.index[0].date().isoformat(),
                'end': data.index[-1].date().isoformat(),
                'total_days': len(data)
            },
            'price_info': {
                'start_price': float(data['close'].iloc[0]),
                'end_price': float(data['close'].iloc[-1]),
                'min_price': float(data['low'].min()),
                'max_price': float(data['high'].max()),
                'total_return': float((data['close'].iloc[-1] / data['close'].iloc[0] - 1) * 100)
            }
        },
        'strategy_results': {
            'rsi_strategies': all_results[0] if len(all_results) > 0 else [],
            'macd_strategies': all_results[1] if len(all_results) > 1 else [],
            'ma_strategies': all_results[2] if len(all_results) > 2 else [],
            'bb_strategies': all_results[3] if len(all_results) > 3 else []
        },
        'top_strategies': top_strategies,
        'summary': {
            'total_strategies_tested': sum(len(r) for r in all_results if r),
            'best_sharpe_ratio': top_strategies[0]['sharpe_ratio'] if top_strategies else 0,
            'best_max_drawdown': top_strategies[0]['max_drawdown'] if top_strategies else 0,
            'best_total_return': top_strategies[0]['total_return'] if top_strategies else 0
        }
    }

    # Save JSON report
    json_filename = f'fixed_professional_0700_backtest_{timestamp}.json'
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    # Save CSV report
    if top_strategies:
        df = pd.DataFrame(top_strategies)
        csv_filename = f'fixed_professional_0700_top_strategies_{timestamp}.csv'
        df.to_csv(csv_filename, index=False)

        print(f"\nResults saved:")
        print(f"   Detailed Report: {json_filename}")
        print(f"   Strategy List: {csv_filename}")

    return json_filename

def main():
    """Main execution function"""
    start_time = time.time()

    # 1. Get data
    data = get_0700_historical_data()

    if data is None or len(data) == 0:
        print("[ERROR] Cannot get data, program terminated")
        return

    # 2. Test various strategies
    print(f"\nStarting comprehensive strategy optimization testing...")

    all_results = []

    # Test RSI strategies
    rsi_results = test_rsi_strategies(data)
    all_results.append(rsi_results)

    # Test MACD strategies
    macd_results = test_macd_strategies(data)
    all_results.append(macd_results)

    # Test Moving Average strategies
    ma_results = test_moving_average_strategies(data)
    all_results.append(ma_results)

    # Test Bollinger Bands strategies
    bb_results = test_bollinger_strategies(data)
    all_results.append(bb_results)

    # 3. Analyze best strategies
    top_strategies = analyze_comprehensive_results(all_results)

    # 4. Save results
    report_file = save_comprehensive_results(data, all_results, top_strategies)

    # 5. Summary
    total_time = time.time() - start_time
    total_strategies = sum(len(r) for r in all_results if r)

    print("\n" + "="*80)
    print("PROFESSIONAL BACKTEST COMPLETION SUMMARY")
    print("="*80)
    print(f"Total execution time: {total_time:.2f} seconds")
    print(f"Strategies tested: {total_strategies}")
    print(f"Data analyzed: {len(data)} days")
    print(f"Best Sharpe Ratio: {top_strategies[0]['sharpe_ratio']:.3f}" if top_strategies else "N/A")
    print(f"Best Max Drawdown: {top_strategies[0]['max_drawdown']:.1%}" if top_strategies else "N/A")

    if top_strategies and top_strategies[0]['sharpe_ratio'] > 1.5:
        print("\nEXCELLENT STRATEGY FOUND!")
        print("   This strategy shows strong potential for real-world application")
        print("   Recommended: Start with paper trading before committing real capital")
    elif top_strategies and top_strategies[0]['sharpe_ratio'] > 1.0:
        print("\nGOOD STRATEGY IDENTIFIED")
        print("   Consider further optimization or combine with risk management")
    else:
        print("\nSTRATEGIES NEED IMPROVEMENT")
        print("   Consider different timeframes, risk management, or strategy combinations")

    print(f"\nDetailed report saved: {report_file}")
    print("="*80)

if __name__ == "__main__":
    main()