#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试GPU RSI计算问题
"""

import numpy as np
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

def debug_rsi_calculation():
    """调试RSI计算问题"""
    print("=== Debugging GPU RSI Calculation ===")

    try:
        from src.gpu.gpu_computation_core import get_gpu_computation_core

        # 创建GPU核心
        gpu_core = get_gpu_computation_core(0)
        print("GPU Core created successfully")

        # 生成测试数据
        test_data = np.random.uniform(100, 200, 100).astype(np.float32)  # 使用更小的数据集
        print(f"Generated test data: {len(test_data)} samples, shape: {test_data.shape}")
        print(f"Data range: {test_data.min():.2f} - {test_data.max():.2f}")

        # 测试移动平均单独计算
        print("\n--- Testing Moving Average ---")
        try:
            ma_result = gpu_core._calculate_moving_average_gpu(
                gpu_core.cp.asarray(test_data), 14
            )
            print(f"MA calculation successful: {len(ma_result)} samples")
            print(f"MA result range: {ma_result.min():.4f} - {ma_result.max():.4f}")
        except Exception as e:
            print(f"MA calculation failed: {e}")
            import traceback
            traceback.print_exc()

        # 测试RSI计算逐步分解
        print("\n--- Testing RSI Step by Step ---")
        try:
            prices_gpu = gpu_core.cp.asarray(test_data)
            print(f"GPU array shape: {prices_gpu.shape}")

            # Step 1: 计算delta
            delta = gpu_core.cp.diff(prices_gpu, prepend=prices_gpu[:1])
            print(f"Delta shape: {delta.shape}")

            # Step 2: 分离涨跌
            gain = gpu_core.cp.where(delta > 0, delta, 0.0).astype(gpu_core.cp.float32)
            loss = gpu_core.cp.where(delta < 0, -delta, 0.0).astype(gpu_core.cp.float32)
            print(f"Gain shape: {gain.shape}")
            print(f"Loss shape: {loss.shape}")

            # Step 3: 计算移动平均
            avg_gain = gpu_core._calculate_moving_average_gpu(gain, 14)
            avg_loss = gpu_core._calculate_moving_average_gpu(loss, 14)
            print(f"Avg Gain shape: {avg_gain.shape}")
            print(f"Avg Loss shape: {avg_loss.shape}")

            # Step 4: 检查是否有长度不匹配
            if len(avg_gain) != len(avg_loss):
                print(f"ERROR: Length mismatch! avg_gain: {len(avg_gain)}, avg_loss: {len(avg_loss)}")
                return False

            # Step 5: 计算RS
            rs = avg_gain / gpu_core.cp.where(avg_loss == 0, 1e-10, avg_loss)
            print(f"RS calculation successful, shape: {rs.shape}")

            # Step 6: 计算RSI
            rsi = 100 - (100 / (1 + rs))
            print(f"RSI calculation successful, shape: {rs.shape}")

            # Step 7: 填充
            rsi[:14] = 50.0
            print(f"Padding successful")

            # Step 8: 裁剪
            rsi = gpu_core.cp.clip(rsi, 0, 100)
            print(f"Clipping successful")

            print(f"RSI calculation SUCCESS: shape {rsi.shape}, range {rsi.min():.2f} - {rsi.max():.2f}")

            # 将结果移回CPU验证
            rsi_cpu = rsi.get()
            print(f"RSI CPU version shape: {rsi_cpu.shape}")
            print(f"RSI CPU range: {rsi_cpu.min():.2f} - {rsi_cpu.max():.2f}")

            return True

        except Exception as e:
            print(f"RSI step-by-step failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"GPU Core creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_rsi():
    """直接测试RSI计算"""
    print("\n=== Testing Direct RSI Calculation ===")

    try:
        from src.gpu.gpu_computation_core import get_gpu_computation_core

        gpu_core = get_gpu_computation_core(0)

        # 测试不同大小的数据
        test_sizes = [10, 14, 20, 50, 100, 500]

        for size in test_sizes:
            print(f"\nTesting with {size} data points:")
            test_data = np.random.uniform(100, 200, size).astype(np.float32)

            try:
                rsi_result = gpu_core.calculate_rsi_gpu(test_data, 14)
                print(f"  SUCCESS: shape {rsi_result.shape}, range {rsi_result.min():.2f}-{rsi_result.max():.2f}")
            except Exception as e:
                print(f"  FAILED: {e}")

    except Exception as e:
        print(f"Direct RSI test failed: {e}")

if __name__ == "__main__":
    success1 = debug_rsi_calculation()
    test_direct_rsi()

    if success1:
        print("\n=== RSI Debugging Completed Successfully ===")
    else:
        print("\n=== RSI Debugging Failed ===")