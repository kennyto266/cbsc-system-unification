#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
0700.HK GPU加速簡化測試
Simple 0700.HK GPU acceleration test
"""

import sys
import os
import time
import requests
import pandas as pd
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system', 'src'))

def get_0700hk_data():
    """獲取0700.HK數據"""
    print("=== 獲取0700.HK數據 ===")

    url = "http://18.180.162.113:9191/inst/getInst"
    params = {"symbol": "0700.hk", "duration": 365}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        dates = list(data['data']['close'].keys())
        close_prices = list(data['data']['close'].values())

        df = pd.DataFrame({
            'close': close_prices
        }, index=pd.to_datetime(dates))

        print(f"數據獲取成功: {len(df)} 條記錄")
        print(f"數據範圍: {df.index[0].date()} 至 {df.index[-1].date()}")
        print(f"價格範圍: {df['close'].min():.2f} - {df['close'].max():.2f} HKD")

        return df

    except Exception as e:
        print(f"數據獲取失敗: {e}")
        return None

def test_gpu_0700hk():
    """測試0700.HK GPU加速"""
    print("\n=== 0700.HK GPU加速測試 ===")

    try:
        from indicators.gpu_indicators import GPUTechnicalIndicators

        # 獲取數據
        data = get_0700hk_data()
        if data is None:
            return False

        prices = data['close'].values
        print(f"測試數據: {len(prices)} 個價格點")

        # GPU測試
        print("\nGPU加速計算...")
        gpu_indicators = GPUTechnicalIndicators(use_gpu=True)

        # RSI
        start = time.time()
        rsi_gpu = gpu_indicators.rsi(prices, 14)
        gpu_time = time.time() - start
        print(f"GPU RSI: {gpu_time:.6f}s")

        # MACD
        start = time.time()
        macd_gpu = gpu_indicators.macd(prices, 12, 26, 9)
        macd_time = time.time() - start
        print(f"GPU MACD: {macd_time:.6f}s")

        # CPU對比
        print("\nCPU對比計算...")
        cpu_indicators = GPUTechnicalIndicators(use_gpu=False)

        start = time.time()
        rsi_cpu = cpu_indicators.rsi(prices, 14)
        cpu_time = time.time() - start
        print(f"CPU RSI: {cpu_time:.6f}s")

        # 性能比較
        if gpu_time > 0:
            speedup = cpu_time / gpu_time
            print(f"\n性能比較:")
            print(f"RSI加速比: {speedup:.2f}x")

        # 結果檢查
        rsi_diff = abs(rsi_gpu[-1] - rsi_cpu[-1])
        print(f"結果一致性: {rsi_diff < 0.01}")

        # 顯示結果
        print(f"\n最新指標:")
        print(f"當前價格: {prices[-1]:.2f} HKD")
        print(f"RSI (14): {rsi_gpu[-1]:.2f}")
        print(f"MACD: {macd_gpu[0][-1]:.4f}")

        # 交易信號
        current_rsi = rsi_gpu[-1]
        if current_rsi > 70:
            signal = "RSI超買 - 考慮賣出"
        elif current_rsi < 30:
            signal = "RSI超賣 - 考慮買入"
        else:
            signal = "RSI中性區間"

        print(f"交易信號: {signal}")

        return True

    except Exception as e:
        print(f"測試失敗: {e}")
        return False

def main():
    print("=" * 50)
    print("0700.HK GPU加速測試")
    print("=" * 50)

    result = test_gpu_0700hk()

    if result:
        print("\n測試結果: 成功")
        print("0700.HK GPU加速系統正常工作!")
    else:
        print("\n測試結果: 失敗")

    return result

if __name__ == "__main__":
    main()