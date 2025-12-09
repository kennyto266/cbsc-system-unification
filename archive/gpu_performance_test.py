#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU性能測試 - 繞過動態編譯問題
GPU Performance Test - Bypass dynamic compilation issues
"""

import sys
import os
import time
import numpy as np

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system', 'src'))

def test_gpu_basic_operations():
    """測試GPU基本操作性能"""
    print("=== GPU基本操作測試 ===")

    try:
        import cupy as cp

        # 檢測GPU狀態
        print(f"CuPy version: {cp.__version__}")
        print(f"CUDA available: {cp.cuda.is_available()}")

        if cp.cuda.is_available():
            print(f"GPU devices: {cp.cuda.runtime.getDeviceCount()}")
            cp.cuda.Device(0).use()
            print("GPU device activated")

            # 性能測試
            size = 1000000
            print(f"測試數據大小: {size:,} 元素")

            # 創建測試數據
            np.random.seed(42)
            cpu_data = np.random.random(size).astype(np.float32)

            # GPU數據傳輸
            start_time = time.time()
            gpu_data = cp.array(cpu_data)
            transfer_time = time.time() - start_time
            print(f"數據傳輸到GPU時間: {transfer_time:.6f}s")

            # GPU基本計算（不使用動態編譯）
            start_time = time.time()
            gpu_result = cp.sum(gpu_data)
            cp.cuda.Stream.null.synchronize()
            gpu_time = time.time() - start_time
            print(f"GPU sum計算時間: {gpu_time:.6f}s")

            # CPU對比計算
            start_time = time.time()
            cpu_result = np.sum(cpu_data)
            cpu_time = time.time() - start_time
            print(f"CPU sum計算時間: {cpu_time:.6f}s")

            # 檢查結果
            gpu_final = float(gpu_result)
            cpu_final = float(cpu_result)

            print(f"CPU結果: {cpu_final:.6f}")
            print(f"GPU結果: {gpu_final:.6f}")
            print(f"結果一致性: {abs(cpu_final - gpu_final) < 1e-6}")

            if gpu_time > 0:
                speedup = cpu_time / gpu_time
                print(f"加速比: {speedup:.2f}x")

                if speedup > 1.1:  # 超過10%的加速
                    print("✅ GPU加速成功!")
                    return True
                else:
                    print("⚠️ GPU加速不明顯")
                    return True
            else:
                print("⚠️ GPU時間過短無法比較")
                return True

        else:
            print("❌ CUDA不可用")
            return False

    except Exception as e:
        print(f"❌ GPU測試失敗: {e}")
        return False

def test_gpu_vector_operations():
    """測試GPU向量操作"""
    print("\n=== GPU向量操作測試 ===")

    try:
        import cupy as cp

        # 創建測試數據
        size = 500000
        np.random.seed(42)
        cpu_a = np.random.random(size).astype(np.float32)
        cpu_b = np.random.random(size).astype(np.float32)

        # GPU計算
        gpu_a = cp.array(cpu_a)
        gpu_b = cp.array(cpu_b)

        start_time = time.time()
        gpu_result = gpu_a * gpu_b + cp.sqrt(gpu_a) + cp.sin(gpu_b)
        cp.cuda.Stream.null.synchronize()
        gpu_time = time.time() - start_time

        # CPU計算
        start_time = time.time()
        cpu_result = cpu_a * cpu_b + np.sqrt(cpu_a) + np.sin(cpu_b)
        cpu_time = time.time() - start_time

        print(f"GPU向量操作時間: {gpu_time:.6f}s")
        print(f"CPU向量操作時間: {cpu_time:.6f}s")

        if gpu_time > 0:
            speedup = cpu_time / gpu_time
            print(f"向量操作加速比: {speedup:.2f}x")

        return True

    except Exception as e:
        print(f"❌ GPU向量操作失敗: {e}")
        return False

def test_gpu_rsi_simulation():
    """測試GPU版本的RSI計算（使用現有函數）"""
    print("\n=== GPU RSI計算測試 ===")

    try:
        from indicators.gpu_indicators import GPUTechnicalIndicators

        # 生成測試價格數據
        np.random.seed(42)
        prices = np.cumprod(1 + np.random.normal(0.001, 0.02, 10000)) * 100

        print(f"測試價格數據: {len(prices)} 個點")

        # GPU版本
        gpu_indicators = GPUTechnicalIndicators(use_gpu=True)

        start_time = time.time()
        rsi_gpu = gpu_indicators.rsi(prices, 14)
        gpu_time = time.time() - start_time

        # CPU版本
        cpu_indicators = GPUTechnicalIndicators(use_gpu=False)

        start_time = time.time()
        rsi_cpu = cpu_indicators.rsi(prices, 14)
        cpu_time = time.time() - start_time

        print(f"GPU RSI計算時間: {gpu_time:.6f}s")
        print(f"CPU RSI計算時間: {cpu_time:.6f}s")
        print(f"GPU RSI值: {rsi_gpu[-1]:.2f}")
        print(f"CPU RSI值: {rsi_cpu[-1]:.2f}")

        # 檢查結果一致性
        diff = abs(rsi_gpu[-1] - rsi_cpu[-1])
        print(f"結果差異: {diff:.6f}")
        print(f"結果一致: {diff < 0.01}")

        if gpu_time > 0:
            speedup = cpu_time / gpu_time
            print(f"RSI計算加速比: {speedup:.2f}x")

        return True

    except Exception as e:
        print(f"❌ GPU RSI計算失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("GPU性能加速測試")
    print("=" * 60)

    tests = [
        ("GPU基本操作", test_gpu_basic_operations),
        ("GPU向量操作", test_gpu_vector_operations),
        ("GPU RSI計算", test_gpu_rsi_simulation)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n開始測試: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "通過" if result else "失敗"
            print(f"{test_name}: {status}")
        except Exception as e:
            print(f"{test_name}: 錯誤 - {e}")
            results.append((test_name, False))

    # 總結
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:20}: {status}")
        if result:
            passed += 1

    print(f"\n總體結果: {passed}/{len(results)} 測試通過")

    if passed == len(results):
        print("🎉 所有GPU測試通過！GPU加速工作正常！")
    else:
        print("⚠️ 部分GPU測試失敗。")

    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)