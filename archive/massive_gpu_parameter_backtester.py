#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Massive GPU Parameter Backtester - 0-300 Full Range Testing
GPU vs CPU Performance Comparison with Full Parameter Space
"""

import sys
import os
import time
import numpy as np
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import cpu_count
import json
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system', 'src'))

def get_0700hk_data():
    """Get 0700.HK real data for backtesting"""
    print("=== Getting 0700.HK Data for Backtesting ===")

    url = "http://18.180.162.113:9191/inst/getInst"
    params = {"symbol": "0700.hk", "duration": 1095}  # 3 years

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        dates = list(data['data']['close'].keys())
        close_prices = list(data['data']['close'].values())

        df = pd.DataFrame({
            'close': close_prices
        }, index=pd.to_datetime(dates))

        print(f"Data retrieved: {len(df)} records")
        print(f"Data range: {df.index[0].date()} to {df.index[-1].date()}")

        return df['close'].values

    except Exception as e:
        print(f"Data retrieval failed: {e}")
        return None

class ParameterSpaceOptimizer:
    """Massive Parameter Space Optimizer with GPU vs CPU Comparison"""

    def __init__(self, use_gpu=True, n_workers=None):
        self.use_gpu = use_gpu
        self.n_workers = n_workers or min(cpu_count(), 16)  # Limit workers

        # Initialize indicators
        if self.use_gpu:
            try:
                from final_optimized_gpu_indicators import FinalOptimizedGPUTechnicalIndicators
                self.indicators = FinalOptimizedGPUTechnicalIndicators(use_gpu=True)
                print(f"GPU Optimizer initialized: {self.indicators.get_backend_info()['backend']}")
            except ImportError:
                print("GPU indicators not available, falling back to CPU")
                self.use_gpu = False

        if not self.use_gpu:
            from final_optimized_gpu_indicators import FinalOptimizedGPUTechnicalIndicators
            self.indicators = FinalOptimizedGPUTechnicalIndicators(use_gpu=False)
            print("CPU Optimizer initialized")

    def calculate_sharpe_ratio(self, returns, risk_free_rate=0.03):
        """Calculate Sharpe Ratio with 3% risk-free rate"""
        if len(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate

        if np.std(excess_returns) == 0:
            return 0.0

        sharpe = np.mean(excess_returns) / np.std(excess_returns)
        return sharpe * np.sqrt(252)  # Annualized

    def calculate_max_drawdown(self, returns):
        """Calculate Maximum Drawdown"""
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)

    def backtest_rsi_strategy(self, prices, period, oversold=30, overbought=70):
        """Backtest RSI strategy with given parameters"""
        try:
            # Calculate RSI
            rsi = self.indicators.rsi(prices, period)

            # Handle RSI length (RSI is shorter than prices due to diff)
            rsi_length = len(rsi)
            prices_aligned = prices[-rsi_length:]  # Align prices with RSI

            # Generate signals (aligned with RSI)
            signals = np.zeros(rsi_length)

            # Buy when RSI crosses above oversold
            buy_signals = (rsi > oversold) & (np.roll(rsi, 1) <= oversold)

            # Sell when RSI crosses below overbought
            sell_signals = (rsi < overbought) & (np.roll(rsi, 1) >= overbought)

            signals[buy_signals] = 1
            signals[sell_signals] = -1

            # Calculate returns (aligned with RSI)
            returns = np.zeros(rsi_length)
            position = 0

            for i in range(1, rsi_length):
                if signals[i] == 1 and position <= 0:
                    position = 1
                elif signals[i] == -1 and position >= 0:
                    position = 0

                if position != 0:
                    returns[i] = (prices_aligned[i] - prices_aligned[i-1]) / prices_aligned[i-1]

            # Calculate metrics
            total_return = np.sum(returns)
            sharpe_ratio = self.calculate_sharpe_ratio(returns)
            max_drawdown = self.calculate_max_drawdown(returns)

            # Quality score (weighted)
            quality_score = (sharpe_ratio * 50 + total_return * 100 - abs(max_drawdown) * 200)

            return {
                'period': period,
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'quality_score': quality_score,
                'trade_count': np.sum(buy_signals),
                'final_rsi': rsi[-1] if len(rsi) > 0 and not np.isnan(rsi[-1]) else 50
            }

        except Exception as e:
            print(f"Error in RSI backtest for period {period}: {e}")
            return None

    def optimize_rsi_0_300(self, prices, step=1):
        """Optimize RSI parameters from 0-300 with given step"""
        print(f"\n{'='*60}")
        print(f"RSI OPTIMIZATION: 0-300 Range (Step: {step})")
        print(f"Total combinations: {301//step}")
        print(f"Backend: {self.indicators.get_backend_info()['backend']}")
        print(f"{'='*60}")

        # Generate parameter combinations
        periods = list(range(1, 301, step))  # 1-300

        print(f"Testing {len(periods)} RSI periods...")

        results = []
        start_time = time.time()

        for i, period in enumerate(periods):
            if i % 50 == 0:
                elapsed = time.time() - start_time
                eta = elapsed / (i + 1) * (len(periods) - i - 1)
                print(f"Progress: {i+1}/{len(periods)} ({(i+1)/len(periods)*100:.1f}%) - ETA: {eta:.1f}s")

            result = self.backtest_rsi_strategy(prices, period)
            if result:
                results.append(result)

        total_time = time.time() - start_time

        # Sort by quality score
        results.sort(key=lambda x: x['quality_score'], reverse=True)

        print(f"\nCompleted {len(results)} backtests in {total_time:.2f}s")
        print(f"Average time per backtest: {total_time/len(results)*1000:.2f}ms")
        print(f"Backtests per second: {len(results)/total_time:.1f}")

        return results

    def optimize_macd_0_300(self, prices, step=1):
        """Optimize MACD parameters from 0-300"""
        print(f"\n{'='*60}")
        print(f"MACD OPTIMIZATION: 0-300 Range (Step: {step})")
        print(f"Backend: {self.indicators.get_backend_info()['backend']}")
        print(f"{'='*60}")

        # Generate parameter combinations
        fast_periods = list(range(1, 51, step))      # Fast: 1-50
        slow_periods = list(range(51, 301, step))    # Slow: 51-300
        signal_periods = list(range(1, 21, step))    # Signal: 1-20

        combinations = []
        for fast in fast_periods:
            for slow in slow_periods:
                if fast < slow:  # Fast must be less than slow
                    for signal in signal_periods:
                        combinations.append((fast, slow, signal))

        print(f"Testing {len(combinations)} MACD combinations...")

        results = []
        start_time = time.time()

        for i, (fast, slow, signal) in enumerate(combinations[:1000]):  # Limit to 1000 for demo
            if i % 100 == 0:
                elapsed = time.time() - start_time
                eta = elapsed / (i + 1) * (len(combinations[:1000]) - i - 1)
                print(f"Progress: {i+1}/{min(1000, len(combinations))} ({(i+1)/min(1000, len(combinations))*100:.1f}%) - ETA: {eta:.1f}s")

            result = self.backtest_macd_strategy(prices, fast, slow, signal)
            if result:
                results.append(result)

        total_time = time.time() - start_time

        results.sort(key=lambda x: x['quality_score'], reverse=True)

        print(f"\nCompleted {len(results)} MACD backtests in {total_time:.2f}s")
        print(f"Average time per backtest: {total_time/len(results)*1000:.2f}ms")

        return results

    def backtest_macd_strategy(self, prices, fast, slow, signal):
        """Backtest MACD strategy"""
        try:
            # Calculate MACD
            macd_result = self.indicators.macd(prices, fast, slow, signal)
            macd_line = macd_result['MACD']
            signal_line = macd_result['SIGNAL']

            # Generate signals
            buy_signals = (macd_line > signal_line) & (np.roll(macd_line, 1) <= np.roll(signal_line, 1))
            sell_signals = (macd_line < signal_line) & (np.roll(macd_line, 1) >= np.roll(signal_line, 1))

            # Calculate returns
            returns = np.zeros(len(prices))
            position = 0

            for i in range(max(fast, slow), len(prices)):
                if buy_signals[i] and position <= 0:
                    position = 1
                elif sell_signals[i] and position >= 0:
                    position = 0

                if position != 0 and i > 0:
                    returns[i] = (prices[i] - prices[i-1]) / prices[i-1]

            # Calculate metrics
            total_return = np.sum(returns)
            sharpe_ratio = self.calculate_sharpe_ratio(returns)
            max_drawdown = self.calculate_max_drawdown(returns)

            quality_score = (sharpe_ratio * 50 + total_return * 100 - abs(max_drawdown) * 200)

            return {
                'fast': fast, 'slow': slow, 'signal': signal,
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'quality_score': quality_score,
                'trade_count': np.sum(buy_signals),
                'final_macd': macd_line[-1]
            }

        except Exception as e:
            return None

def run_massive_backtest_comparison():
    """Run massive backtest comparing GPU vs CPU"""
    print("=" * 80)
    print("MASSIVE PARAMETER BACKTEST - GPU vs CPU COMPARISON")
    print("Testing 0-300 full parameter range")
    print("=" * 80)

    # Get data
    prices = get_0700hk_data()
    if prices is None:
        print("Failed to get data")
        return

    print(f"Using {len(prices)} price points for backtesting")

    # Test configurations
    configs = [
        {"use_gpu": True, "name": "GPU", "step": 5},
        {"use_gpu": False, "name": "CPU", "step": 5}
    ]

    results = {}

    for config in configs:
        print(f"\n{'#'*20} {config['name']} BACKTEST {'#'*20}")

        optimizer = ParameterSpaceOptimizer(use_gpu=config['use_gpu'])

        # RSI Optimization
        rsi_results = optimizer.optimize_rsi_0_300(prices, step=config['step'])

        # MACD Optimization (limited for demo)
        macd_results = optimizer.optimize_macd_0_300(prices, step=config['step'])

        results[config['name']] = {
            'rsi_results': rsi_results[:10],  # Top 10
            'macd_results': macd_results[:5],  # Top 5
            'backend_info': optimizer.indicators.get_backend_info()
        }

    # Generate comparison report
    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON RESULTS")
    print("=" * 80)

    for backend, data in results.items():
        print(f"\n{backend} Results:")
        print(f"Backend: {data['backend_info']['backend']}")

        if data['rsi_results']:
            print(f"Top RSI: Period {data['rsi_results'][0]['period']} - "
                  f"Sharpe: {data['rsi_results'][0]['sharpe_ratio']:.3f}, "
                  f"Quality: {data['rsi_results'][0]['quality_score']:.1f}")

        if data['macd_results']:
            best_macd = data['macd_results'][0]
            print(f"Top MACD: ({best_macd['fast']},{best_macd['slow']},{best_macd['signal']}) - "
                  f"Sharpe: {best_macd['sharpe_ratio']:.3f}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"massive_backtest_comparison_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to: {filename}")

    return results

if __name__ == "__main__":
    results = run_massive_backtest_comparison()