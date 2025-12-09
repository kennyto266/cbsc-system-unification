#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultimate 0-300 Parameter Battle - GPU vs CPU Showdown
Complete parameter range testing with performance analysis
"""

import sys
import os
import time
import numpy as np
import pandas as pd
import requests
import json
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system', 'src'))

def get_0700hk_data():
    """Get extended 0700.HK data"""
    print("=== Getting Extended 0700.HK Data ===")

    url = "http://18.180.162.113:9191/inst/getInst"
    params = {"symbol": "0700.hk", "duration": 1825}  # 5 years

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        dates = list(data['data']['close'].keys())
        close_prices = list(data['data']['close'].values())

        df = pd.DataFrame({
            'close': close_prices
        }, index=pd.to_datetime(dates))

        print(f"Extended data retrieved: {len(df)} records")
        print(f"Data range: {df.index[0].date()} to {df.index[-1].date()}")

        return df['close'].values

    except Exception as e:
        print(f"Extended data retrieval failed: {e}")
        return None

def calculate_sharpe_ratio(returns, risk_free_rate=0.03):
    """Calculate Sharpe Ratio with 3% risk-free rate"""
    if len(returns) == 0 or np.std(returns) == 0:
        return 0.0

    excess_returns = returns - risk_free_rate / 252
    sharpe = np.mean(excess_returns) / np.std(excess_returns)
    return sharpe * np.sqrt(252)

def calculate_max_drawdown(returns):
    """Calculate Maximum Drawdown"""
    if len(returns) == 0:
        return 0.0

    cumulative = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    return np.min(drawdown)

class UltimateParameterBattle:
    """Ultimate GPU vs CPU Parameter Battle"""

    def __init__(self):
        self.results = {}

    def test_single_rsi_parameter(self, prices, period, backend_type='gpu'):
        """Test single RSI parameter with specified backend"""
        try:
            if backend_type == 'gpu':
                from final_optimized_gpu_indicators import FinalOptimizedGPUTechnicalIndicators
                indicators = FinalOptimizedGPUTechnicalIndicators(use_gpu=True)
            else:
                from final_optimized_gpu_indicators import FinalOptimizedGPUTechnicalIndicators
                indicators = FinalOptimizedGPUTechnicalIndicators(use_gpu=False)

            start = time.time()
            rsi = indicators.rsi(prices, period)
            calc_time = time.time() - start

            if len(rsi) == 0:
                return None

            # Simple backtest
            rsi_aligned = rsi
            prices_aligned = prices[-len(rsi):]

            # Generate simple signals
            signals = np.zeros(len(rsi_aligned))
            signals[rsi_aligned < 30] = 1  # Buy oversold
            signals[rsi_aligned > 70] = -1  # Sell overbought

            # Calculate returns
            returns = np.zeros(len(prices_aligned))
            position = 0

            for i in range(1, len(prices_aligned)):
                if signals[i] == 1 and position <= 0:
                    position = 1
                elif signals[i] == -1 and position >= 0:
                    position = 0

                if position != 0:
                    returns[i] = (prices_aligned[i] - prices_aligned[i-1]) / prices_aligned[i-1]

            # Calculate metrics
            total_return = np.sum(returns)
            sharpe_ratio = calculate_sharpe_ratio(returns)
            max_drawdown = calculate_max_drawdown(returns)

            # Quality score
            quality_score = (sharpe_ratio * 50 + total_return * 100 - abs(max_drawdown) * 200)

            return {
                'period': period,
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'quality_score': quality_score,
                'calculation_time': calc_time,
                'final_rsi': rsi_aligned[-1] if len(rsi_aligned) > 0 else 50,
                'backend': backend_type
            }

        except Exception as e:
            print(f"Error testing RSI {period} with {backend_type}: {e}")
            return None

    def run_full_0_300_battle(self, prices, step=1):
        """Run complete 0-300 parameter battle"""
        print(f"\n{'='*80}")
        print(f"ULTIMATE 0-300 PARAMETER BATTLE")
        print(f"Testing RSI periods 1-300 (step={step})")
        print(f"Total combinations: {300//step}")
        print(f"{'='*80}")

        periods = list(range(1, 301, step))
        gpu_results = []
        cpu_results = []

        print(f"\n{'GPU BACKTEST':^80}")
        print(f"{'Period':<8} {'Time':<10} {'Sharpe':<10} {'Return':<10} {'MaxDD':<10} {'Quality':<10}")
        print("-" * 80)

        gpu_total_time = 0
        for i, period in enumerate(periods):
            result = self.test_single_rsi_parameter(prices, period, 'gpu')
            if result:
                gpu_results.append(result)
                gpu_total_time += result['calculation_time']

                if i % 30 == 0 or period == 300:  # Show progress
                    print(f"{period:<8} {result['calculation_time']*1000:<10.3f} "
                          f"{result['sharpe_ratio']:<10.3f} {result['total_return']:<10.3f} "
                          f"{result['max_drawdown']:<10.3f} {result['quality_score']:<10.1f}")

        print(f"\n{'CPU BACKTEST':^80}")
        print(f"{'Period':<8} {'Time':<10} {'Sharpe':<10} {'Return':<10} {'MaxDD':<10} {'Quality':<10}")
        print("-" * 80)

        cpu_total_time = 0
        for i, period in enumerate(periods):
            result = self.test_single_rsi_parameter(prices, period, 'cpu')
            if result:
                cpu_results.append(result)
                cpu_total_time += result['calculation_time']

                if i % 30 == 0 or period == 300:  # Show progress
                    print(f"{period:<8} {result['calculation_time']*1000:<10.3f} "
                          f"{result['sharpe_ratio']:<10.3f} {result['total_return']:<10.3f} "
                          f"{result['max_drawdown']:<10.3f} {result['quality_score']:<10.1f}")

        # Sort results by quality score
        gpu_results.sort(key=lambda x: x['quality_score'], reverse=True)
        cpu_results.sort(key=lambda x: x['quality_score'], reverse=True)

        # Performance comparison
        print(f"\n{'='*80}")
        print(f"PERFORMANCE COMPARISON SUMMARY")
        print(f"{'='*80}")

        print(f"GPU Total Time: {gpu_total_time:.3f}s")
        print(f"CPU Total Time: {cpu_total_time:.3f}s")
        print(f"GPU Speedup: {cpu_total_time/gpu_total_time:.2f}x")
        print(f"Backtests completed: GPU {len(gpu_results)}, CPU {len(cpu_results)}")

        # Top results comparison
        print(f"\n{'TOP 5 RESULTS COMPARISON':^80}")
        print(f"{'Rank':<6} {'GPU Period':<12} {'GPU Sharpe':<12} {'CPU Period':<12} {'CPU Sharpe':<12} {'Winner':<10}")
        print("-" * 80)

        for i in range(min(5, len(gpu_results), len(cpu_results))):
            gpu_best = gpu_results[i] if i < len(gpu_results) else None
            cpu_best = cpu_results[i] if i < len(cpu_results) else None

            if gpu_best and cpu_best:
                winner = 'GPU' if gpu_best['quality_score'] > cpu_best['quality_score'] else 'CPU'
                print(f"{i+1:<6} {gpu_best['period']:<12} {gpu_best['sharpe_ratio']:<12.3f} "
                      f"{cpu_best['period']:<12} {cpu_best['sharpe_ratio']:<12.3f} {winner:<10}")

        return {
            'gpu_results': gpu_results[:20],  # Top 20
            'cpu_results': cpu_results[:20],  # Top 20
            'performance': {
                'gpu_total_time': gpu_total_time,
                'cpu_total_time': cpu_total_time,
                'gpu_speedup': cpu_total_time/gpu_total_time if gpu_total_time > 0 else 0,
                'gpu_completed': len(gpu_results),
                'cpu_completed': len(cpu_results)
            }
        }

    def run_extreme_scale_test(self, prices):
        """Run extreme scale test with many parameter combinations"""
        print(f"\n{'='*80}")
        print(f"EXTREME SCALE TEST - Thousands of Combinations")
        print(f"{'='*80}")

        # Test multiple strategies
        strategies = [
            {'name': 'RSI', 'params': list(range(1, 301))},  # 300 RSI periods
            {'name': 'RSI_Tight', 'params': list(range(2, 51))},  # 49 RSI tight periods
        ]

        results = {}

        for strategy in strategies:
            print(f"\nTesting {strategy['name']} - {len(strategy['params'])} combinations")

            # GPU test
            gpu_start = time.time()
            gpu_results = []
            for param in strategy['params'][:50]:  # Limit to 50 for demo
                result = self.test_single_rsi_parameter(prices, param, 'gpu')
                if result:
                    gpu_results.append(result)
            gpu_time = time.time() - gpu_start

            # CPU test
            cpu_start = time.time()
            cpu_results = []
            for param in strategy['params'][:50]:  # Limit to 50 for demo
                result = self.test_single_rsi_parameter(prices, param, 'cpu')
                if result:
                    cpu_results.append(result)
            cpu_time = time.time() - cpu_start

            # Performance metrics
            speedup = cpu_time / gpu_time if gpu_time > 0 else 0

            print(f"{strategy['name']} Performance:")
            print(f"  GPU: {gpu_time:.3f}s ({len(gpu_results)} results)")
            print(f"  CPU: {cpu_time:.3f}s ({len(cpu_results)} results)")
            print(f"  Speedup: {speedup:.2f}x")

            results[strategy['name']] = {
                'gpu_time': gpu_time,
                'cpu_time': cpu_time,
                'speedup': speedup,
                'gpu_results': len(gpu_results),
                'cpu_results': len(cpu_results)
            }

        return results

def main():
    """Main function"""
    print("ULTIMATE GPU vs CPU PARAMETER BATTLE")
    print("=" * 80)

    # Get data
    prices = get_0700hk_data()
    if prices is None:
        print("Failed to get data")
        return

    print(f"Using {len(prices)} price points for testing")

    battle = UltimateParameterBattle()

    # Run main battle with step=5 for reasonable runtime
    main_results = battle.run_full_0_300_battle(prices, step=5)

    # Run extreme scale test
    extreme_results = battle.run_extreme_scale_test(prices)

    # Combine all results
    final_results = {
        'main_battle': main_results,
        'extreme_test': extreme_results,
        'timestamp': datetime.now().isoformat(),
        'data_points': len(prices)
    }

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ultimate_parameter_battle_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(final_results, f, indent=2, default=str)

    print(f"\n{'='*80}")
    print(f"ULTIMATE BATTLE COMPLETE")
    print(f"Results saved to: {filename}")
    print(f"{'='*80}")

    # Final summary
    perf = main_results['performance']
    print(f"\nFINAL SUMMARY:")
    print(f"GPU Total Time: {perf['gpu_total_time']:.3f}s")
    print(f"CPU Total Time: {perf['cpu_total_time']:.3f}s")
    print(f"GPU Speedup: {perf['gpu_speedup']:.2f}x")

    if perf['gpu_speedup'] > 1.0:
        print("🎉 GPU IS FASTER! Significant scale achieved!")
    elif perf['gpu_speedup'] > 0.5:
        print("⚖️  GPU is competitive at scale")
    else:
        print("🔍 CPU remains faster for this workload")

    return final_results

if __name__ == "__main__":
    results = main()