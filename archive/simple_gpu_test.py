#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化GPU測試 - 避免編碼問題
"""

import sys
import os
import numpy as np
import pandas as pd
import time
import requests

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system', 'src'))

def test_gpu_environment():
    """測試GPU環境"""
    print("=== GPU Environment Test ===")

    try:
        from utils.gpu_detector import get_gpu_environment, is_gpu_available

        gpu_env = get_gpu_environment()
        gpu_info = gpu_env.get_system_info()

        print(f"GPU Available: {is_gpu_available()}")
        print(f"Backend: {gpu_env.get_compute_backend()}")
        print(f"CuPy Available: {gpu_info['cupy_available']}")
        print(f"CUDA Available: {gpu_info['cuda_available']}")
        print(f"GPU Count: {gpu_info['gpu_count']}")

        if gpu_info['gpu_count'] > 0:
            print(f"GPU Memory: {gpu_info['gpu_memory_gb']:.1f} GB")

        return gpu_env.is_gpu_available()

    except Exception as e:
        print(f"GPU Test Error: {e}")
        return False

def test_gpu_indicators():
    """測試GPU技術指標"""
    print("\n=== GPU Indicators Test ===")

    try:
        from indicators.gpu_indicators import GPUTechnicalIndicators

        # 生成測試數據
        np.random.seed(42)
        prices = np.cumprod(1 + np.random.normal(0.001, 0.02, 500)) * 100

        print("Creating GPU indicators...")
        gpu_indicators = GPUTechnicalIndicators(use_gpu=True)

        # 測試RSI
        print("Calculating RSI...")
        start_time = time.time()
        rsi = gpu_indicators.rsi(prices, 14)
        rsi_time = time.time() - start_time
        print(f"RSI Time: {rsi_time:.4f}s")
        print(f"RSI Latest: {rsi[-1]:.2f}")

        # 測試MACD
        print("Calculating MACD...")
        start_time = time.time()
        macd = gpu_indicators.macd(prices, 12, 26, 9)
        macd_time = time.time() - start_time
        print(f"MACD Time: {macd_time:.4f}s")
        print(f"MACD Latest: {macd['MACD'][-1]:.4f}")

        # 批量計算
        print("Batch calculation...")
        indicators_config = {
            'rsi': {'period': 14},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9}
        }

        start_time = time.time()
        all_indicators = gpu_indicators.calculate_multiple_indicators(prices, indicators_config)
        batch_time = time.time() - start_time
        print(f"Batch Time: {batch_time:.4f}s")
        print(f"Indicators Count: {len(all_indicators)}")

        # 後端信息
        backend_info = gpu_indicators.get_backend_info()
        print(f"Backend Info: {backend_info['backend']}")

        return True

    except Exception as e:
        print(f"GPU Indicators Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vectorbt_gpu():
    """測試VectorBT GPU引擎"""
    print("\n=== VectorBT GPU Engine Test ===")

    try:
        from backtest.vectorbt_engine import VectorBTEngine

        print("Initializing VectorBT GPU engine...")
        engine = VectorBTEngine(use_gpu=True)

        # GPU性能信息
        gpu_info = engine.get_gpu_performance_info()
        print(f"GPU Available: {gpu_info['gpu_available']}")
        print(f"GPU Environment: {gpu_info['gpu_environment']['gpu_acceleration_possible']}")

        # 獲取測試數據
        print("Fetching 0700.HK data...")
        url = "http://18.180.162.113:9191/inst/getInst"
        params = {"symbol": "0700.hk", "duration": 180}

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        dates = list(data['data']['close'].keys())
        close_prices = list(data['data']['close'].values())

        df = pd.DataFrame({
            'close': close_prices
        }, index=pd.to_datetime(dates))

        print(f"Data loaded: {len(df)} records")

        # 測試GPU指標計算
        indicators_config = {
            'rsi': {'period': 14},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9}
        }

        print("Calculating indicators with GPU...")
        start_time = time.time()
        indicators = engine.calculate_indicators_gpu(df, indicators_config)
        calc_time = time.time() - start_time

        print(f"Calculation Time: {calc_time:.4f}s")
        print(f"Calculated Indicators: {list(indicators.keys())}")

        if 'RSI' in indicators:
            rsi_latest = indicators['RSI'][-1]
            print(f"Latest RSI: {rsi_latest:.2f}")

        if 'MACD' in indicators:
            macd_latest = indicators['MACD'][-1]
            print(f"Latest MACD: {macd_latest:.4f}")

        return True

    except Exception as e:
        print(f"VectorBT GPU Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cpu_fallback():
    """測試CPU回退功能"""
    print("\n=== CPU Fallback Test ===")

    try:
        from indicators.gpu_indicators import GPUTechnicalIndicators

        print("Creating CPU indicators (GPU disabled)...")
        cpu_indicators = GPUTechnicalIndicators(use_gpu=False)

        # 生成測試數據
        np.random.seed(42)
        prices = np.cumprod(1 + np.random.normal(0.001, 0.02, 500)) * 100

        print("Calculating RSI with CPU...")
        start_time = time.time()
        rsi = cpu_indicators.rsi(prices, 14)
        cpu_time = time.time() - start_time
        print(f"CPU RSI Time: {cpu_time:.4f}s")
        print(f"CPU RSI Latest: {rsi[-1]:.2f}")

        # 後端信息
        backend_info = cpu_indicators.get_backend_info()
        print(f"CPU Backend: {backend_info['backend']}")

        return True

    except Exception as e:
        print(f"CPU Fallback Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("VectorBT GPU Acceleration Test")
    print("=" * 60)

    tests = [
        ("GPU Environment", test_gpu_environment),
        ("GPU Indicators", test_gpu_indicators),
        ("VectorBT GPU Engine", test_vectorbt_gpu),
        ("CPU Fallback", test_cpu_fallback)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\nStarting: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "PASSED" if result else "FAILED"
            print(f"{test_name}: {status}")
        except Exception as e:
            print(f"{test_name}: ERROR - {e}")
            results.append((test_name, False))

    # 總結
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:20}: {status}")
        if result:
            passed += 1

    print(f"\nResult: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("All tests PASSED!")
        print("VectorBT GPU integration is working correctly.")
    else:
        print("Some tests failed.")
        print("Check the error messages above.")

    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)