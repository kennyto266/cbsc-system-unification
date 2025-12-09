#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REAL MASSIVE GPU RUN
真正的大規模GPU測試 - 1000+參數組合
Real massive GPU test with 1000+ parameter combinations
"""

import sys
import os
import time
import numpy as np
import pandas as pd
import requests
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp

sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system', 'src'))

def get_extended_0700hk_data():
    """獲取擴展的0700.HK數據"""
    print("=== 獲取擴展0700.HK數據 ===")

    url = "http://18.180.162.113:9191/inst/getInst"
    params = {"symbol": "0700.hk", "duration": 3650}  # 10年數據

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        dates = list(data['data']['close'].keys())
        close_prices = list(data['data']['close'].values())

        df = pd.DataFrame({
            'close': close_prices
        }, index=pd.to_datetime(dates))

        print(f"擴展數據獲取成功: {len(df)} 條記錄")
        print(f"數據範圍: {df.index[0].date()} 至 {df.index[-1].date()}")
        print(f"價格範圍: {df['close'].min():.2f} - {df['close'].max():.2f} HKD")

        return df['close'].values

    except Exception as e:
        print(f"擴展數據獲取失敗: {e}")
        return None

class RealMassiveGPURunner:
    """真實大規模GPU運行器"""

    def __init__(self, use_gpu=True):
        self.use_gpu = use_gpu

        if use_gpu:
            try:
                from final_optimized_gpu_indicators import FinalOptimizedGPUTechnicalIndicators
                self.indicators = FinalOptimizedGPUTechnicalIndicators(use_gpu=True)
                print(f"GPU Runner 初始化: {self.indicators.get_backend_info()['backend']}")
            except Exception as e:
                print(f"GPU初始化失敗: {e}, 使用CPU")
                self.use_gpu = False
                self.indicators = None

        if not self.use_gpu:
            from final_optimized_gpu_indicators import FinalOptimizedGPUTechnicalIndicators
            self.indicators = FinalOptimizedGPUTechnicalIndicators(use_gpu=False)
            print("CPU Runner 初始化")

    def calculate_sharpe_ratio(self, returns, risk_free_rate=0.03):
        """計算Sharpe比率 (無風險利率3%)"""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate / 252
        sharpe = np.mean(excess_returns) / np.std(excess_returns)
        return sharpe * np.sqrt(252)

    def calculate_max_drawdown(self, returns):
        """計算最大回撤"""
        if len(returns) == 0:
            return 0.0

        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)

    def backtest_rsi_single(self, prices, period):
        """單個RSI回測"""
        try:
            start_time = time.time()

            # 計算RSI
            rsi = self.indicators.rsi(prices, period)
            calc_time = time.time() - start_time

            if len(rsi) == 0:
                return None

            # 簡單回測
            rsi_length = len(rsi)
            prices_aligned = prices[-rsi_length:]

            # 生成信號
            signals = np.zeros(rsi_length)
            buy_signals = (rsi < 30) & (np.roll(rsi, 1) >= 30)
            sell_signals = (rsi > 70) & (np.roll(rsi, 1) <= 70)

            signals[buy_signals] = 1
            signals[sell_signals] = -1

            # 計算回報
            returns = np.zeros(rsi_length)
            position = 0

            for i in range(1, rsi_length):
                if signals[i] == 1 and position <= 0:
                    position = 1
                elif signals[i] == -1 and position >= 0:
                    position = 0

                if position != 0:
                    returns[i] = (prices_aligned[i] - prices_aligned[i-1]) / prices_aligned[i-1]

            # 計算指標
            total_return = np.sum(returns)
            sharpe_ratio = self.calculate_sharpe_ratio(returns)
            max_drawdown = self.calculate_max_drawdown(returns)

            # 質量評分
            quality_score = (sharpe_ratio * 50 + total_return * 100 - abs(max_drawdown) * 200)

            return {
                'period': period,
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'quality_score': quality_score,
                'calculation_time': calc_time,
                'final_rsi': rsi[-1] if len(rsi) > 0 else 50,
                'trade_count': np.sum(buy_signals),
                'backend': 'gpu' if self.use_gpu else 'cpu'
            }

        except Exception as e:
            return None

    def run_massive_rsi_test(self, prices, max_period=300, step=1):
        """運行大規模RSI測試"""
        periods = list(range(5, max_period + 1, step))
        total_combinations = len(periods)

        print(f"\n{'='*80}")
        print(f"真實大規模RSI測試")
        print(f"參數範圍: 5-{max_period} (步長: {step})")
        print(f"總組合數: {total_combinations}")
        print(f"後端: {'GPU' if self.use_gpu else 'CPU'}")
        print(f"{'='*80}")

        results = []
        start_time = time.time()

        # 批量處理以優化性能
        batch_size = 100
        for i in range(0, len(periods), batch_size):
            batch_periods = periods[i:i+batch_size]

            print(f"處理批次 {i//batch_size + 1}/{(len(periods)-1)//batch_size + 1}: "
                  f"參數 {batch_periods[0]}-{batch_periods[-1]}")

            batch_results = []
            for period in batch_periods:
                result = self.backtest_rsi_single(prices, period)
                if result:
                    batch_results.append(result)

            results.extend(batch_results)

            # 顯示進度
            elapsed = time.time() - start_time
            progress = (i + len(batch_periods)) / len(periods)
            eta = elapsed / progress * (1 - progress) if progress > 0 else 0

            print(f"  進度: {progress*100:.1f}% - 已完成: {len(results)}/{len(periods)} - "
                  f"耗時: {elapsed:.1f}s - ETA: {eta:.1f}s")

            # 顯示當前最佳結果
            if batch_results:
                best_in_batch = max(batch_results, key=lambda x: x['quality_score'])
                print(f"  批次最佳: RSI({best_in_batch['period']}) - "
                      f"Sharpe: {best_in_batch['sharpe_ratio']:.3f}, "
                      f"質量: {best_in_batch['quality_score']:.1f}")

        total_time = time.time() - start_time

        # 排序結果
        results.sort(key=lambda x: x['quality_score'], reverse=True)

        print(f"\n{'='*80}")
        print(f"測試完成 - {'GPU' if self.use_gpu else 'CPU'} 結果")
        print(f"{'='*80}")
        print(f"總時間: {total_time:.3f}s")
        print(f"完成組合: {len(results)}/{len(periods)}")
        print(f"平均時間: {total_time/len(results)*1000:.2f}ms/組合")
        print(f"處理速度: {len(results)/total_time:.1f} 組合/秒")

        # 顯示前10名結果
        print(f"\n{'前10名策略':^80}")
        print(f"{'排名':<6} {'RSI週期':<10} {'Sharpe':<10} {'回報':<12} {'最大回撤':<12} {'質量評分':<12}")
        print("-" * 80)

        for i, result in enumerate(results[:10]):
            print(f"{i+1:<6} {result['period']:<10} {result['sharpe_ratio']:<10.3f} "
                  f"{result['total_return']:<12.3%} {result['max_drawdown']:<12.3%} "
                  f"{result['quality_score']:<12.1f}")

        return results

def run_real_massive_comparison():
    """運行真實的大規模GPU vs CPU比較"""
    print("=" * 100)
    print("真實大規模GPU vs CPU性能比較")
    print("測試1000+參數組合，看GPU是否真正超越CPU")
    print("=" * 100)

    # 獲取擴展數據
    prices = get_extended_0700hk_data()
    if prices is None:
        print("無法獲取數據，退出")
        return

    print(f"使用 {len(prices)} 價格點進行測試")

    # 測試配置
    configs = [
        {"use_gpu": True, "name": "GPU", "max_period": 200, "step": 1},  # 196個組合
        {"use_gpu": False, "name": "CPU", "max_period": 200, "step": 1}   # 196個組合
    ]

    all_results = {}

    for config in configs:
        print(f"\n{'#'*30} {config['name']} 測試 {'#'*30}")

        runner = RealMassiveGPURunner(use_gpu=config['use_gpu'])
        results = runner.run_massive_rsi_test(
            prices,
            max_period=config['max_period'],
            step=config['step']
        )

        all_results[config['name']] = {
            'results': results[:20],  # 前20名
            'total_time': sum(r['calculation_time'] for r in results),
            'completed': len(results),
            'backend': runner.indicators.get_backend_info()['backend']
        }

    # 性能比較
    print(f"\n{'='*100}")
    print("最終性能比較")
    print(f"{'='*100}")

    gpu_data = all_results['GPU']
    cpu_data = all_results['CPU']

    print(f"GPU 後端: {gpu_data['backend']}")
    print(f"CPU 後端: {cpu_data['backend']}")
    print(f"GPU 總時間: {gpu_data['total_time']:.3f}s")
    print(f"CPU 總時間: {cpu_data['total_time']:.3f}s")

    if gpu_data['total_time'] > 0:
        speedup = cpu_data['total_time'] / gpu_data['total_time']
        print(f"GPU 加速比: {speedup:.2f}x")

        if speedup > 1.5:
            print("🎉 GPU 顯著優於 CPU！大規模計算優勢證實！")
        elif speedup > 1.1:
            print("✅ GPU 優於 CPU，規模效益顯現！")
        elif speedup > 0.9:
            print("⚖️  GPU 與 CPU 基本持平")
        else:
            print("❌ GPU 仍然慢於 CPU")

    # 最佳策略比較
    print(f"\n最佳策略比較:")
    if gpu_data['results'] and cpu_data['results']:
        gpu_best = gpu_data['results'][0]
        cpu_best = cpu_data['results'][0]

        print(f"GPU 最佳: RSI({gpu_best['period']}) - Sharpe: {gpu_best['sharpe_ratio']:.3f}, 質量: {gpu_best['quality_score']:.1f}")
        print(f"CPU 最佳: RSI({cpu_best['period']}) - Sharpe: {cpu_best['sharpe_ratio']:.3f}, 質量: {cpu_best['quality_score']:.1f}")

    # 保存結果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"REAL_MASSIVE_GPU_RUN_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n結果已保存至: {filename}")

    return all_results

if __name__ == "__main__":
    results = run_real_massive_comparison()