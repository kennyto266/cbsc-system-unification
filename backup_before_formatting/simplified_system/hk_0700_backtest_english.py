#!/usr/bin/env python3
"""
0700.HK Comprehensive Backtest Optimization System
Test different parameter combinations for Sharpe Ratio and Max Drawdown

Target:
1. Test multiple technical indicator strategies
2. Optimize parameters for highest Sharpe Ratio
3. Control maximum drawdown within acceptable range
4. Generate detailed performance reports
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

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from src.api.stock_api import get_hk_stock_data
from src.indicators.core_indicators import CoreIndicators
from src.backtest.vectorbt_engine import VectorBTEngine

def get_0700_historical_data():
    """Get 0700.HK historical data"""
    print("=" * 60)
    print("0700.HK Tencent - Historical Data Acquisition")
    print("=" * 60)

    try:
        # Get 3 years historical data
        data = get_hk_stock_data('0700.HK', 1095)  # 3 years

        if data is not None and len(data) > 0:
            print(f"[OK] Successfully got data: {len(data)} records")
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
            print("[FAIL] Cannot get real data, using synthetic data")
            return generate_synthetic_data()

    except Exception as e:
        print(f"[WARN] Real data acquisition failed: {e}")
        print("[INFO] Using high-quality synthetic data for backtest")
        return generate_synthetic_data()

def generate_synthetic_data():
    """Generate high-quality synthetic data"""
    # Create synthetic data with Tencent stock characteristics
    dates = pd.date_range(end=datetime.now(), periods=1095, freq='D')
    np.random.seed(42)  # Ensure reproducible results

    # Simulate Tencent stock price characteristics
    initial_price = 400.0
    returns = np.random.normal(0.0008, 0.025, len(dates))  # Daily return and volatility

    # Add some trend and seasonality
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
    base_volume = 20000000  # 20 million shares base volume
    volume_variation = np.random.lognormal(0, 0.5, len(dates))
    data['volume'] = base_volume * volume_variation

    # Handle first day's open price
    data.loc[dates[0], 'open'] = initial_price

    print(f"[OK] Generated synthetic data: {len(data)} records")
    print(f"    Price range: ${data['low'].min():.2f} - ${data['high'].max():.2f}")

    return data

def calculate_sharpe_ratio(returns, risk_free_rate=0.03):
    """Calculate Sharpe Ratio (risk-free rate default 3%)"""
    if len(returns) == 0 or returns.std() == 0:
        return 0.0

    excess_returns = returns - risk_free_rate/252  # Daily risk-free rate
    sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)

    return sharpe

def calculate_max_drawdown(equity_curve):
    """Calculate maximum drawdown"""
    if len(equity_curve) == 0:
        return 0.0

    cumulative = (1 + equity_curve).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max

    return drawdown.min()

def test_rsi_strategies(data):
    """Test RSI strategies with different parameter combinations"""
    print("\n" + "="*50)
    print("RSI Strategy Optimization")
    print("="*50)

    indicators = CoreIndicators()
    engine = VectorBTEngine()

    # RSI parameter ranges
    rsi_periods = [5, 7, 10, 14, 20, 25, 30]
    oversold_levels = [20, 25, 30, 35]
    overbought_levels = [65, 70, 75, 80]

    results = []
    total_combinations = len(rsi_periods) * len(oversold_levels) * len(overbought_levels)
    current_test = 0

    print(f"Testing {total_combinations} RSI parameter combinations...")

    for period in rsi_periods:
        rsi = indicators.calculate_rsi(data['close'], period)

        for oversold in oversold_levels:
            for overbought in overbought_levels:
                current_test += 1
                progress = (current_test / total_combinations) * 100

                try:
                    # Execute backtest
                    result = engine.backtest_strategy(
                        data,
                        'RSI_MEAN_REVERSION',
                        {
                            'period': period,
                            'oversold': oversold,
                            'overbought': overbought
                        }
                    )

                    if result:
                        # Calculate additional metrics
                        returns = pd.Series(result.returns) if hasattr(result, 'returns') else pd.Series([0])
                        sharpe = calculate_sharpe_ratio(returns)
                        max_dd = calculate_max_drawdown(returns)

                        results.append({
                            'strategy': 'RSI_MEAN_REVERSION',
                            'period': period,
                            'oversold': oversold,
                            'overbought': overbought,
                            'total_return': result.total_return,
                            'sharpe_ratio': sharpe,
                            'max_drawdown': max_dd,
                            'win_rate': getattr(result, 'win_rate', 0),
                            'trades_count': getattr(result, 'trades_count', 0)
                        })

                        # Show progress and excellent results
                        if sharpe > 1.0 or max_dd > -0.15:
                            print(f"  [EXCELLENT] RSI({period},{oversold},{overbought}): "
                                  f"SR={sharpe:.3f}, MDD={max_dd:.1%}, Return={result.total_return:.1%}")

                except Exception as e:
                    print(f"  [ERROR] RSI({period},{oversold},{overbought}): {e}")
                    continue

    # Sort and return best results
    if results:
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        print(f"\nRSI strategy test completed, tested {len(results)} valid combinations")

        # Show top 5 results
        print("\nTop 5 RSI strategies:")
        for i, res in enumerate(results[:5]):
            print(f"{i+1}. RSI({res['period']}, {res['oversold']}, {res['overbought']}): "
                  f"SR={res['sharpe_ratio']:.3f}, MDD={res['max_drawdown']:.1%}, "
                  f"Return={res['total_return']:.1%}")

    return results

def test_macd_strategies(data):
    """Test MACD strategies with different parameter combinations"""
    print("\n" + "="*50)
    print("MACD Strategy Optimization")
    print("="*50)

    indicators = CoreIndicators()
    engine = VectorBTEngine()

    # MACD parameter ranges
    fast_periods = [8, 10, 12, 15]
    slow_periods = [20, 24, 26, 30, 35]
    signal_periods = [6, 8, 9, 12]

    results = []
    total_combinations = len(fast_periods) * len(slow_periods) * len(signal_periods)
    current_test = 0

    print(f"Testing {total_combinations} MACD parameter combinations...")

    for fast in fast_periods:
        for slow in slow_periods:
            if fast >= slow:
                continue  # Skip invalid combinations

            for signal in signal_periods:
                current_test += 1

                try:
                    # Execute backtest
                    result = engine.backtest_strategy(
                        data,
                        'MACD_CROSSOVER',
                        {
                            'fast': fast,
                            'slow': slow,
                            'signal': signal
                        }
                    )

                    if result:
                        # Calculate additional metrics
                        returns = pd.Series(result.returns) if hasattr(result, 'returns') else pd.Series([0])
                        sharpe = calculate_sharpe_ratio(returns)
                        max_dd = calculate_max_drawdown(returns)

                        results.append({
                            'strategy': 'MACD_CROSSOVER',
                            'fast': fast,
                            'slow': slow,
                            'signal': signal,
                            'total_return': result.total_return,
                            'sharpe_ratio': sharpe,
                            'max_drawdown': max_dd,
                            'win_rate': getattr(result, 'win_rate', 0),
                            'trades_count': getattr(result, 'trades_count', 0)
                        })

                        # Show excellent results
                        if sharpe > 1.0 or max_dd > -0.20:
                            print(f"  [EXCELLENT] MACD({fast},{slow},{signal}): "
                                  f"SR={sharpe:.3f}, MDD={max_dd:.1%}, Return={result.total_return:.1%}")

                except Exception as e:
                    continue

    # Sort and return best results
    if results:
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        print(f"\nMACD strategy test completed, tested {len(results)} valid combinations")

        # Show top 5 results
        print("\nTop 5 MACD strategies:")
        for i, res in enumerate(results[:5]):
            print(f"{i+1}. MACD({res['fast']}, {res['slow']}, {res['signal']}): "
                  f"SR={res['sharpe_ratio']:.3f}, MDD={res['max_drawdown']:.1%}, "
                  f"Return={res['total_return']:.1%}")

    return results

def test_moving_average_strategies(data):
    """Test moving average strategies"""
    print("\n" + "="*50)
    print("Moving Average Strategy Optimization")
    print("="*50)

    engine = VectorBTEngine()

    # Moving average parameter ranges
    short_periods = [5, 10, 15, 20, 25, 30]
    long_periods = [40, 50, 60, 80, 100, 120]

    results = []
    total_combinations = len(short_periods) * len(long_periods)
    current_test = 0

    print(f"Testing {total_combinations} moving average parameter combinations...")

    for short in short_periods:
        for long in long_periods:
            if short >= long:
                continue  # Skip invalid combinations

            current_test += 1

            try:
                # Execute backtest
                result = engine.backtest_strategy(
                    data,
                    'DUAL_MOVING_AVERAGE',
                    {
                        'short_period': short,
                        'long_period': long
                    }
                )

                if result:
                    # Calculate additional metrics
                    returns = pd.Series(result.returns) if hasattr(result, 'returns') else pd.Series([0])
                    sharpe = calculate_sharpe_ratio(returns)
                    max_dd = calculate_max_drawdown(returns)

                    results.append({
                        'strategy': 'DUAL_MOVING_AVERAGE',
                        'short_period': short,
                        'long_period': long,
                        'total_return': result.total_return,
                        'sharpe_ratio': sharpe,
                        'max_drawdown': max_dd,
                        'win_rate': getattr(result, 'win_rate', 0),
                        'trades_count': getattr(result, 'trades_count', 0)
                    })

                    # Show excellent results
                    if sharpe > 0.8 or max_dd > -0.15:
                        print(f"  [EXCELLENT] MA({short},{long}): "
                              f"SR={sharpe:.3f}, MDD={max_dd:.1%}, Return={result.total_return:.1%}")

            except Exception as e:
                continue

    # Sort and return best results
    if results:
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        print(f"\nMoving average strategy test completed, tested {len(results)} valid combinations")

        # Show top 5 results
        print("\nTop 5 Moving Average strategies:")
        for i, res in enumerate(results[:5]):
            print(f"{i+1}. MA({res['short_period']}, {res['long_period']}): "
                  f"SR={res['sharpe_ratio']:.3f}, MDD={res['max_drawdown']:.1%}, "
                  f"Return={res['total_return']:.1%}")

    return results

def analyze_best_strategies(all_results):
    """Analyze best performing strategies across all"""
    print("\n" + "="*60)
    print("Comprehensive Strategy Analysis")
    print("="*60)

    if not all_results:
        print("[WARN] No valid strategy results")
        return

    # Combine all results
    combined_results = []
    for strategy_results in all_results:
        if strategy_results:
            combined_results.extend(strategy_results)

    if not combined_results:
        print("[WARN] No valid strategy results")
        return

    # Sort by Sharpe Ratio
    combined_results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)

    print(f"Total tested {len(combined_results)} strategy combinations")

    # Show comprehensive top 10
    print("\nTop 10 Strategies Overall:")
    print("-" * 80)
    print(f"{'Rank':<4} {'Strategy Type':<20} {'Parameters':<25} {'Sharpe':<8} {'Max DD':<10} {'Return':<8}")
    print("-" * 80)

    for i, res in enumerate(combined_results[:10]):
        strategy_name = res['strategy'].replace('_', ' ')

        # Format parameters
        if 'period' in res and 'oversold' in res:  # RSI
            params = f"({res['period']}, {res['oversold']}, {res['overbought']})"
        elif 'fast' in res:  # MACD
            params = f"({res['fast']}, {res['slow']}, {res['signal']})"
        elif 'short_period' in res:  # MA
            params = f"({res['short_period']}, {res['long_period']})"
        else:
            params = "N/A"

        print(f"{i+1:<4} {strategy_name:<20} {params:<25} "
              f"{res['sharpe_ratio']:<8.3f} {res['max_drawdown']:<10.1%} "
              f"{res['total_return']:<8.1%}")

    # Analyze best strategy
    best_strategy = combined_results[0]
    print(f"\nBest Strategy: {best_strategy['strategy']}")
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
    if best_strategy['sharpe_ratio'] > 1.5:
        recommendation = "Excellent strategy, recommend live testing"
    elif best_strategy['sharpe_ratio'] > 1.0:
        recommendation = "Good strategy, consider small capital testing"
    elif best_strategy['sharpe_ratio'] > 0.5:
        recommendation = "Average strategy, needs further optimization"
    else:
        recommendation = "Poor performance, recommend readjustment"

    print(f"   Recommendation: {recommendation}")

    return combined_results[:10]

def save_results(data, all_results, top_strategies):
    """Save test results"""
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
            'ma_strategies': all_results[2] if len(all_results) > 2 else []
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
    json_filename = f'hk_0700_backtest_results_{timestamp}.json'
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    # Save CSV report
    if top_strategies:
        df = pd.DataFrame(top_strategies)
        csv_filename = f'hk_0700_top_strategies_{timestamp}.csv'
        df.to_csv(csv_filename, index=False)

        print(f"\nResults saved:")
        print(f"   Detailed report: {json_filename}")
        print(f"   Strategy list: {csv_filename}")

    return json_filename

def main():
    """Main execution function"""
    print("=" * 80)
    print("0700.HK Tencent - Comprehensive Backtest Optimization System")
    print("=" * 80)

    start_time = time.time()

    # 1. Get data
    data = get_0700_historical_data()

    if data is None or len(data) == 0:
        print("[ERROR] Cannot get data, program terminated")
        return

    # 2. Test various strategies
    print(f"\nStarting strategy optimization testing...")

    all_results = []

    # Test RSI strategies
    rsi_results = test_rsi_strategies(data)
    all_results.append(rsi_results)

    # Test MACD strategies
    macd_results = test_macd_strategies(data)
    all_results.append(macd_results)

    # Test moving average strategies
    ma_results = test_moving_average_strategies(data)
    all_results.append(ma_results)

    # 3. Analyze best strategies
    top_strategies = analyze_best_strategies(all_results)

    # 4. Save results
    report_file = save_results(data, all_results, top_strategies)

    # 5. Summary
    total_time = time.time() - start_time
    total_strategies = sum(len(r) for r in all_results if r)

    print("\n" + "=" * 80)
    print("Test Completion Summary")
    print("=" * 80)
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Strategies tested: {total_strategies}")
    print(f"Data days: {len(data)}")
    print(f"Best Sharpe: {top_strategies[0]['sharpe_ratio']:.3f}" if top_strategies else "N/A")
    print(f"Max drawdown control: {top_strategies[0]['max_drawdown']:.1%}" if top_strategies else "N/A")

    if top_strategies and top_strategies[0]['sharpe_ratio'] > 1.0:
        print("\nFound excellent strategy! Recommend live simulation testing")
    elif top_strategies:
        print("\nStrategy performance is average, recommend parameter adjustment and retest")
    else:
        print("\nNo valid strategies found, recommend checking data and strategy logic")

    print(f"\nDetailed report saved: {report_file}")

if __name__ == "__main__":
    main()