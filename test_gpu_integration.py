#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的GPU集成測試
Simplified GPU Integration Test
"""

import sys
import os
import time
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gpu_environment():
    """測試GPU環境"""
    print("GPU Environment Test")
    print("-" * 30)

    # 檢查CuPy
    try:
        import cupy as cp
        print(f"CuPy available: Yes")
        print(f"CUDA version: {cp.cuda.runtime.runtimeGetVersion()}")
        print(f"GPU count: {cp.cuda.runtime.getDeviceCount()}")
        return True, "cupy"
    except ImportError:
        print("CuPy available: No")

    # 檢查PyTorch
    try:
        import torch
        if torch.cuda.is_available():
            print(f"PyTorch CUDA available: Yes")
            print(f"CUDA version: {torch.version.cuda}")
            print(f"GPU count: {torch.cuda.device_count()}")
            return True, "pytorch"
        else:
            print("PyTorch CUDA available: No")
    except ImportError:
        print("PyTorch available: No")

    print("No GPU backend available")
    return False, None

def test_simple_gpu_calculations():
    """測試簡單GPU計算"""
    print("\nSimple GPU Calculation Test")
    print("-" * 30)

    gpu_available, backend = test_gpu_environment()

    if not gpu_available:
        print("Skipping GPU tests - no GPU available")
        return False

    # 生成測試數據
    np.random.seed(42)
    data = np.random.randn(10000).cumsum() + 100

    try:
        if backend == "cupy":
            import cupy as cp

            # 簡單的向量化計算
            start_time = time.time()
            gpu_data = cp.asarray(data)
            gpu_result = cp.mean(gpu_data)
            cpu_time = time.time() - start_time

            print(f"CuPy mean calculation: {gpu_result:.4f}")
            print(f"GPU calculation time: {cpu_time:.6f}s")

        elif backend == "pytorch":
            import torch

            # 簡單的向量化計算
            start_time = time.time()
            gpu_data = torch.from_numpy(data).cuda()
            gpu_result = torch.mean(gpu_data)
            cpu_time = time.time() - start_time

            print(f"PyTorch mean calculation: {gpu_result:.4f}")
            print(f"GPU calculation time: {cpu_time:.6f}s")

        return True

    except Exception as e:
        print(f"GPU calculation test failed: {e}")
        return False

def test_rsi_calculation():
    """測試RSI計算"""
    print("\nRSI Calculation Test")
    print("-" * 30)

    # 生成測試數據
    np.random.seed(42)
    prices = np.random.randn(1000).cumsum() + 100

    gpu_available, backend = test_gpu_environment()

    if gpu_available:
        try:
            if backend == "cupy":
                import cupy as cp

                def calculate_rsi_gpu(prices, period=14):
                    prices_gpu = cp.asarray(prices, dtype=np.float32)
                    delta_gpu = cp.diff(prices_gpu)
                    gain_gpu = cp.where(delta_gpu > 0, delta_gpu, 0)
                    loss_gpu = cp.where(delta_gpu < 0, -delta_gpu, 0)

                    # 使用移動平均
                    kernel = cp.ones(period, dtype=np.float32) / period
                    avg_gain_gpu = cp.convolve(gain_gpu, kernel, mode='full')[:len(gain_gpu)+1-period]
                    avg_loss_gpu = cp.convolve(loss_gpu, kernel, mode='full')[:len(loss_gpu)+1-period]

                    rs_gpu = avg_gain_gpu / cp.where(avg_loss_gpu == 0, 1e-10, avg_loss_gpu)
                    rsi_gpu = 100 - (100 / (1 + rs_gpu))

                    # 填充NaN值
                    result_gpu = cp.concatenate([cp.full(period-1, cp.nan, dtype=np.float32), rsi_gpu])
                    return cp.asnumpy(result_gpu)

                start_time = time.time()
                rsi_gpu = calculate_rsi_gpu(prices, 14)
                gpu_time = time.time() - start_time

                print(f"GPU RSI calculation time: {gpu_time:.6f}s")
                print(f"Final RSI value: {rsi_gpu[-1]:.4f}")

            elif backend == "pytorch":
                import torch

                def calculate_rsi_gpu(prices, period=14):
                    prices_tensor = torch.from_numpy(prices.astype(np.float32)).cuda()
                    delta_tensor = torch.diff(prices_tensor)
                    gain_tensor = torch.where(delta_tensor > 0, delta_tensor, torch.tensor(0.0).cuda())
                    loss_tensor = torch.where(delta_tensor < 0, -delta_tensor, torch.tensor(0.0).cuda())

                    # 簡化的移動平均
                    alpha = 2 / (period + 1)
                    avg_gain_tensor = torch.zeros_like(gain_tensor)
                    avg_loss_tensor = torch.zeros_like(loss_tensor)

                    avg_gain_tensor[0] = gain_tensor[0]
                    avg_loss_tensor[0] = loss_tensor[0]

                    for i in range(1, len(gain_tensor)):
                        avg_gain_tensor[i] = alpha * gain_tensor[i] + (1 - alpha) * avg_gain_tensor[i-1]
                        avg_loss_tensor[i] = alpha * loss_tensor[i] + (1 - alpha) * avg_loss_tensor[i-1]

                    rs_tensor = avg_gain_tensor / torch.where(avg_loss_tensor == 0, torch.tensor(1e-10).cuda(), avg_loss_tensor)
                    rsi_tensor = 100 - (100 / (1 + rs_tensor))

                    # 填充NaN值
                    nan_padding = torch.full(period-1, float('nan')).cuda()
                    result_tensor = torch.cat([nan_padding, rsi_tensor])

                    return result_tensor.cpu().numpy()

                start_time = time.time()
                rsi_gpu = calculate_rsi_gpu(prices, 14)
                gpu_time = time.time() - start_time

                print(f"GPU RSI calculation time: {gpu_time:.6f}s")
                print(f"Final RSI value: {rsi_gpu[-1]:.4f}")

        except Exception as e:
            print(f"GPU RSI test failed: {e}")
            return False

    # CPU版本對比
    def calculate_rsi_cpu(prices, period=14):
        delta = np.diff(prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = pd.Series(gain).rolling(window=period).mean()
        avg_loss = pd.Series(loss).rolling(window=period).mean()

        rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
        rsi = 100 - (100 / (1 + rs))

        return rsi.values

    start_time = time.time()
    rsi_cpu = calculate_rsi_cpu(prices, 14)
    cpu_time = time.time() - start_time

    print(f"CPU RSI calculation time: {cpu_time:.6f}s")
    print(f"Final RSI value: {rsi_cpu[-1]:.4f}")

    if gpu_available:
        speedup = cpu_time / gpu_time if gpu_time > 0 else 0
        print(f"GPU speedup: {speedup:.2f}x")

    return True

def test_batch_processing():
    """測試批處理"""
    print("\nBatch Processing Test")
    print("-" * 30)

    gpu_available, backend = test_gpu_environment()

    if not gpu_available:
        print("Skipping batch test - no GPU available")
        return False

    # 生成測試數據
    np.random.seed(42)
    prices = np.random.randn(5000).cumsum() + 100

    try:
        if backend == "cupy":
            import cupy as cp

            # 批量RSI計算
            periods = [10, 20, 30, 50]
            start_time = time.time()

            prices_gpu = cp.asarray(prices, dtype=np.float32)
            results = {}

            for period in periods:
                delta_gpu = cp.diff(prices_gpu)
                gain_gpu = cp.where(delta_gpu > 0, delta_gpu, 0)
                loss_gpu = cp.where(delta_gpu < 0, -delta_gpu, 0)

                kernel = cp.ones(period, dtype=np.float32) / period
                avg_gain_gpu = cp.convolve(gain_gpu, kernel, mode='full')[:len(gain_gpu)+1-period]
                avg_loss_gpu = cp.convolve(loss_gpu, kernel, mode='full')[:len(loss_gpu)+1-period]

                rs_gpu = avg_gain_gpu / cp.where(avg_loss_gpu == 0, 1e-10, avg_loss_gpu)
                rsi_gpu = 100 - (100 / (1 + rs_gpu))

                result_gpu = cp.concatenate([cp.full(period-1, cp.nan, dtype=np.float32), rsi_gpu])
                results[period] = cp.asnumpy(result_gpu)

            batch_time = time.time() - start_time

            print(f"GPU batch RSI calculation for periods {periods}")
            print(f"Total time: {batch_time:.6f}s")
            print(f"Time per period: {batch_time/len(periods):.6f}s")
            print(f"Speed: {len(periods)/batch_time:.1f} indicators/second")

            return True

    except Exception as e:
        print(f"Batch processing test failed: {e}")
        return False

def test_memory_usage():
    """測試內存使用"""
    print("\nMemory Usage Test")
    print("-" * 30)

    gpu_available, backend = test_gpu_environment()

    if not gpu_available:
        print("Skipping memory test - no GPU available")
        return False

    try:
        if backend == "cupy":
            import cupy as cp

            # 測試大數據集
            print("Testing with large dataset...")
            large_data = np.random.randn(100000).astype(np.float32)
            print(f"CPU data size: {large_data.nbytes / (1024**2):.1f}MB")

            # GPU內存分配
            start_time = time.time()
            gpu_data = cp.asarray(large_data)
            alloc_time = time.time() - start_time

            print(f"GPU allocation time: {alloc_time:.6f}s")

            # 簡單計算
            start_time = time.time()
            gpu_result = cp.mean(gpu_data)
            calc_time = time.time() - start_time

            print(f"GPU calculation time: {calc_time:.6f}s")
            print(f"Result: {float(gpu_result):.4f}")

            # 釋放內存
            del gpu_data
            cp.get_default_memory_pool().free_all_blocks()
            print("GPU memory freed")

            return True

    except Exception as e:
        print(f"Memory usage test failed: {e}")
        return False

def generate_test_report(results):
    """生成測試報告"""
    print("\nTest Report")
    print("-" * 30)

    report = {
        'timestamp': datetime.now().isoformat(),
        'tests': results,
        'summary': {
            'gpu_available': results.get('gpu_environment', {}).get('available', False),
            'backend': results.get('gpu_environment', {}).get('backend', None),
            'successful_tests': sum(1 for r in results.values() if r.get('success', False)),
            'total_tests': len(results) - 1  # Exclude gpu_environment from count
        }
    }

    # 保存報告
    filename = f"gpu_integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    print(f"Report saved to: {filename}")

    # 顯示摘要
    summary = report['summary']
    print(f"GPU Available: {summary['gpu_available']}")
    print(f"Backend: {summary['backend']}")
    print(f"Successful Tests: {summary['successful_tests']}/{summary['total_tests']}")

    return report

def main():
    """主測試函數"""
    print("GPU Integration Test Suite")
    print("=" * 50)

    results = {}

    # 測試GPU環境
    gpu_available, backend = test_gpu_environment()
    results['gpu_environment'] = {
        'available': gpu_available,
        'backend': backend,
        'success': True
    }

    # 運行測試
    if gpu_available:
        results['simple_calculation'] = {
            'success': test_simple_gpu_calculations()
        }
        results['rsi_calculation'] = {
            'success': test_rsi_calculation()
        }
        results['batch_processing'] = {
            'success': test_batch_processing()
        }
        results['memory_usage'] = {
            'success': test_memory_usage()
        }
    else:
        print("\nSkipping all GPU tests - no GPU backend available")

    # 生成報告
    report = generate_test_report(results)

    print("\nTest suite completed!")
    return report

if __name__ == "__main__":
    main()