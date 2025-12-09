#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接VectorBT GPU測試 - 繞過相對導入問題
Direct VectorBT GPU Test - Bypass relative import issues
"""

import sys
import os
import time
import requests
import pandas as pd
import numpy as np

def test_vectorbt_direct():
    """直接測試VectorBT GPU引擎"""
    print("=== Direct VectorBT GPU Test ===")

    try:
        # 直接導入，避免__init__.py的問題
        sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system', 'src'))

        print("[IMPORT] Testing GPU environment...")
        from utils.gpu_detector import get_gpu_environment, is_gpu_available

        gpu_env = get_gpu_environment()
        gpu_info = gpu_env.get_system_info()

        print(f"GPU Available: {is_gpu_available()}")
        print(f"Backend: {gpu_env.get_compute_backend()}")
        print(f"CuPy Available: {gpu_info['cupy_available']}")
        print(f"CUDA Available: {gpu_info['cuda_available']}")
        print(f"GPU Count: {gpu_info['gpu_count']}")

        print("\n[IMPORT] Testing VectorBT Engine...")
        # 直接導入VectorBT引擎模塊
        from backtest.vectorbt_engine import VectorBTEngine, BacktestConfig

        print("[VBT] Initializing VectorBT GPU engine...")
        engine = VectorBTEngine(use_gpu=True)

        # GPU性能信息
        gpu_info = engine.get_gpu_performance_info()
        print(f"GPU Available: {gpu_info['gpu_available']}")
        print(f"GPU Environment configured: {gpu_info['gpu_environment']}")

        # 獲取測試數據
        print("\n[DATA] Fetching 0700.HK data...")
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

        print("\n[CALC] Testing GPU indicator calculation...")
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
        print(f"[ERROR] VectorBT Direct Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("Direct VectorBT GPU Test")
    print("=" * 60)

    result = test_vectorbt_direct()

    print("\n" + "=" * 60)
    print("Test Result")
    print("=" * 60)

    status = "SUCCESS" if result else "FAILED"
    print(f"VectorBT GPU Engine: {status}")

    if result:
        print("GPU acceleration is working correctly!")
    else:
        print("GPU acceleration test failed.")

    return result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)