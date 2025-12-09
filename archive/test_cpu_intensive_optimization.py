#!/usr/bin/env python3
"""
CPU密集型優化測試
CPU-Intensive Optimization Test

測試真正的CPU佔用率和並行性能
"""

import time
import concurrent.futures
import multiprocessing
import psutil
import os
import numpy as np
from typing import List, Dict, Any
import json
from datetime import datetime

class CPUIntensiveOptimizer:
    """真正的CPU密集型優化器"""

    def __init__(self):
        self.max_workers = multiprocessing.cpu_count() - 2  # 保留2個核心
        print(f"[CPU-OPTIMIZER] 使用 {self.max_workers} 個CPU核心")

    def generate_heavy_workload(self, strategy_id: str, data_size: int = 10000):
        """生成CPU密集型工作負載"""

        # 模擬大量的技術指標計算
        data = np.random.random(data_size)

        # 大量的數學運算 (CPU密集)
        result = 0
        for i in range(100):  # 100次迭代
            # RSI計算 (CPU密集)
            deltas = np.diff(data)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)

            avg_gain = np.mean(gains[:14]) if len(gains) >= 14 else np.mean(gains)
            avg_loss = np.mean(losses[:14]) if len(losses) >= 14 else np.mean(losses)

            if avg_loss > 0:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                result += rsi

            # MACD計算 (CPU密集)
            exp1 = np.convolve(data, np.ones(12)/12, mode='valid')
            exp2 = np.convolve(data, np.ones(26)/26, mode='valid')
            macd = exp1[-len(exp2):] - exp2

            result += np.sum(np.abs(macd))

            # 隨機矩陣運算 (CPU密集)
            matrix = np.random.random((100, 100))
            eigenvals = np.linalg.eigvals(matrix)
            result += np.sum(np.real(eigenvals))

        return {
            'strategy_id': strategy_id,
            'result': result,
            'data_size': data_size,
            'compute_time': time.time()
        }

    def run_cpu_stress_test(self, num_strategies: int = 1000):
        """運行CPU壓力測試"""

        print(f"[CPU-STRESS] 開始壓力測試: {num_strategies:,} 個策略")
        print(f"[CPU-STRESS] 並行核心: {self.max_workers}")

        # 生成策略列表
        strategies = [f"STRAT_{i:05d}" for i in range(num_strategies)]

        # 監控初始CPU使用率
        initial_cpu = psutil.cpu_percent(interval=1)
        print(f"[CPU-STRESS] 初始CPU使用率: {initial_cpu:.1f}%")

        start_time = time.time()

        # 使用不同的並行策略測試
        results = []

        # 方法1: ProcessPoolExecutor (大批次)
        print(f"\n[CPU-STRESS] 測試ProcessPoolExecutor (大批次)...")
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 大批次減少進程創建開銷
            batch_size = max(100, num_strategies // (self.max_workers * 2))

            futures = []
            for i in range(0, len(strategies), batch_size):
                batch = strategies[i:i+batch_size]
                for strategy in batch:
                    future = executor.submit(self.generate_heavy_workload, strategy, 5000)
                    futures.append(future)

            # 收集結果
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    print(f"[ERROR] 策略執行失敗: {e}")

        execution_time = time.time() - start_time
        successful_strategies = len(results)

        print(f"\n[CPU-STRESS] 執行完成!")
        print(f"[CPU-STRESS] 成功策略: {successful_strategies:,}/{num_strategies:,}")
        print(f"[CPU-STRESS] 總執行時間: {execution_time:.2f}秒")
        print(f"[CPU-STRESS] 平均每策略: {execution_time/num_strategies*1000:.2f}ms")
        print(f"[CPU-STRESS] 策略/秒: {num_strategies/execution_time:.1f}")

        # 監控峰值CPU使用率
        peak_cpu = psutil.cpu_percent(interval=1)
        print(f"[CPU-STRESS] 峰值CPU使用率: {peak_cpu:.1f}%")

        # 監控內存使用
        memory_info = psutil.virtual_memory()
        print(f"[CPU-STRESS] 內存使用: {memory_info.percent:.1f}% ({memory_info.used/1024/1024/1024:.1f}GB/{memory_info.total/1024/1024/1024:.1f}GB)")

        return {
            'total_strategies': num_strategies,
            'successful_strategies': successful_strategies,
            'execution_time': execution_time,
            'strategies_per_second': num_strategies/execution_time,
            'peak_cpu_usage': peak_cpu,
            'memory_usage_percent': memory_info.percent,
            'workers_used': self.max_workers
        }

    def test_different_batch_sizes(self):
        """測試不同批次大小的性能"""

        print(f"\n[BATCH-TEST] 測試不同批次大小...")
        num_strategies = 5000

        batch_sizes = [50, 100, 200, 500, 1000, 2000]
        results = []

        for batch_size in batch_sizes:
            print(f"\n[BATCH-TEST] 測試批次大小: {batch_size}")

            strategies = [f"STRAT_{i:05d}" for i in range(num_strategies)]

            start_time = time.time()

            with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # 使用指定批次大小
                futures = []
                for i in range(0, len(strategies), batch_size):
                    batch = strategies[i:i+batch_size]
                    for strategy in batch:
                        future = executor.submit(self.generate_heavy_workload, strategy, 3000)
                        futures.append(future)

                # 等待所有完成
                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result(timeout=10)
                        completed += 1
                    except Exception as e:
                        print(f"[ERROR] {e}")

            execution_time = time.time() - start_time

            result = {
                'batch_size': batch_size,
                'execution_time': execution_time,
                'strategies_per_second': num_strategies/execution_time,
                'completed_strategies': completed
            }
            results.append(result)

            print(f"[BATCH-TEST] 批次{batch_size}: {execution_time:.2f}s, {result['strategies_per_second']:.1f} 策略/秒")

        # 找出最佳批次大小
        best_batch = max(results, key=lambda x: x['strategies_per_second'])
        print(f"\n[BATCH-TEST] 最佳批次大小: {best_batch['batch_size']} ({best_batch['strategies_per_second']:.1f} 策略/秒)")

        return results

def monitor_cpu_usage():
    """監控CPU使用率"""
    cpu_usage = []
    for i in range(10):
        cpu = psutil.cpu_percent(interval=0.5)
        cpu_usage.append(cpu)
        print(f"[MONITOR] CPU使用率: {cpu:.1f}%")
        time.sleep(0.5)

    print(f"[MONITOR] 平均CPU使用率: {np.mean(cpu_usage):.1f}%")
    print(f"[MONITOR] 最高CPU使用率: {np.max(cpu_usage):.1f}%")

if __name__ == "__main__":
    print("=" * 60)
    print("CPU密集型優化測試")
    print("=" * 60)

    # 系統信息
    print(f"系統核心數: {multiprocessing.cpu_count()}")
    print(f"邏輯核心: {psutil.cpu_count(logical=True)}")
    print(f"物理核心: {psutil.cpu_count(logical=False)}")
    print(f"當前進程數: {len(psutil.pids())}")

    # 創建優化器
    optimizer = CPUIntensiveOptimizer()

    # 測試不同負載
    workloads = [1000, 2000, 5000]

    for workload in workloads:
        print(f"\n{'='*40}")
        print(f"測試負載: {workload:,} 個策略")
        print(f"{'='*40}")

        result = optimizer.run_cpu_stress_test(workload)

        # 保存結果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cpu_stress_test_{workload}_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"[SAVE] 結果已保存到: {filename}")

        # 短暫休息
        time.sleep(2)

    # 測試批次大小
    print(f"\n{'='*40}")
    print("批次大小優化測試")
    print(f"{'='*40}")

    batch_results = optimizer.test_different_batch_sizes()

    # 保存批次測試結果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_filename = f"batch_optimization_{timestamp}.json"

    with open(batch_filename, 'w', encoding='utf-8') as f:
        json.dump(batch_results, f, indent=2, ensure_ascii=False)

    print(f"[SAVE] 批次測試結果已保存到: {batch_filename}")

    print(f"\n{'='*60}")
    print("CPU密集型優化測試完成!")
    print("=" * 60)