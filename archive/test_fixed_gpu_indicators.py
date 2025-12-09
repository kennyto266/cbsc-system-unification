#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試修復版GPU指標系統
Test Fixed GPU Indicators System
"""

import sys
import os
import time
import numpy as np
import requests
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system', 'src'))

def get_0700hk_data():
    """獲取0700.HK數據"""
    print("=== 獲取0700.HK真實數據 ===")

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

        print(f"✅ 數據獲取成功: {len(df)} 條記錄")
        print(f"📅 數據範圍: {df.index[0].date()} 至 {df.index[-1].date()}")
        print(f"💰 價格範圍: {df['close'].min():.2f} - {df['close'].max():.2f} HKD")

        return df.values  # 返回numpy array

    except Exception as e:
        print(f"❌ 數據獲取失敗: {e}")
        return None

def test_original_vs_fixed():
    """測試原始版本 vs 修復版本"""
    print("\n=== 原始版本 vs 修復版本對比測試 ===")

    try:
        # 導入兩個版本
        from indicators.gpu_indicators import GPUTechnicalIndicators as OriginalGPU
        from fixed_gpu_indicators import FixedGPUTechnicalIndicators as FixedGPU

        # 獲取真實數據
        prices = get_0700hk_data()
        if prices is None:
            return False

        print(f"📊 測試數據: {len(prices)} 個價格點")

        # 測試參數
        rsi_period = 14
        macd_fast, macd_slow, macd_signal = 12, 26, 9
        bb_period, bb_std = 20, 2.0

        results = {}

        # 測試原始版本（CPU）
        print("\n🔄 測試原始版本...")
        original_gpu = OriginalGPU(use_gpu=True)  # 會回退CPU

        start = time.time()
        original_rsi = original_gpu.rsi(prices, rsi_period)
        original_rsi_time = time.time() - start

        start = time.time()
        original_macd = original_gpu.macd(prices, macd_fast, macd_slow, macd_signal)
        original_macd_time = time.time() - start

        print(f"原始 RSI時間: {original_rsi_time:.6f}s")
        print(f"原始 MACD時間: {original_macd_time:.6f}s")
        print(f"原始後端: {original_gpu.get_backend_info()['backend']}")

        # 測試修復版本
        print("\n🚀 測試修復版本...")
        fixed_gpu = FixedGPUTechnicalIndicators(use_gpu=True)

        start = time.time()
        fixed_rsi = fixed_gpu.rsi(prices, rsi_period)
        fixed_rsi_time = time.time() - start

        start = time.time()
        fixed_macd = fixed_gpu.macd(prices, macd_fast, macd_slow, macd_signal)
        fixed_macd_time = time.time() - start

        print(f"修復 RSI時間: {fixed_rsi_time:.6f}s")
        print(f"修復 MACD時間: {fixed_macd_time:.6f}s")
        print(f"修復後端: {fixed_gpu.get_backend_info()['backend']}")

        # 結果一致性檢查
        rsi_diff = np.mean(np.abs(original_rsi - fixed_rsi))
        macd_diff = {
            'MACD': np.mean(np.abs(original_macd['MACD'] - fixed_macd['MACD'])),
            'SIGNAL': np.mean(np.abs(original_macd['SIGNAL'] - fixed_macd['SIGNAL'])),
            'HIST': np.mean(np.abs(original_macd['HIST'] - fixed_macd['HIST']))
        }

        print(f"\n✅ 結果一致性檢查:")
        print(f"RSI差異: {rsi_diff:.8f}")
        print(f"MACD差異: {macd_diff}")

        # 性能比較
        print(f"\n📈 性能比較:")
        rsi_speedup = original_rsi_time / fixed_rsi_time if fixed_rsi_time > 0 else 0
        macd_speedup = original_macd_time / fixed_macd_time if fixed_macd_time > 0 else 0

        print(f"RSI性能比: {rsi_speedup:.2f}x")
        print(f"MACD性能比: {macd_speedup:.2f}x")

        # 顯示最新值
        print(f"\n📊 最新指標值 (0700.HK):")
        current_price = prices[-1]
        print(f"當前價格: {current_price:.2f} HKD")
        print(f"RSI (14): {fixed_rsi[-1]:.2f}")
        print(f"MACD: {fixed_macd['MACD'][-1]:.4f}")
        print(f"Signal: {fixed_macd['SIGNAL'][-1]:.4f}")

        # 交易信號分析
        current_rsi = fixed_rsi[-1]
        if current_rsi > 70:
            rsi_signal = "RSI超買 - 考慮賣出"
        elif current_rsi < 30:
            rsi_signal = "RSI超賣 - 考慮買入"
        else:
            rsi_signal = "RSI中性區間 - 觀望"

        print(f"🎯 交易信號: {rsi_signal}")

        return True

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_with_different_sizes():
    """測試不同數據大小的性能"""
    print("\n=== 不同數據大小性能測試 ===")

    try:
        from fixed_gpu_indicators import FixedGPUTechnicalIndicators

        # 測試不同大小的數據
        data_sizes = [100, 500, 1000, 5000, 10000]

        gpu_indicators = FixedGPUTechnicalIndicators(use_gpu=True)
        cpu_indicators = FixedGPUTechnicalIndicators(use_gpu=False)

        print(f"{'數據大小':<10} {'GPU時間(s)':<12} {'CPU時間(s)':<12} {'加速比':<8}")
        print("-" * 50)

        for size in data_sizes:
            # 生成測試數據
            np.random.seed(42)
            test_data = np.random.randn(size).cumsum() + 100
            test_data = np.abs(test_data)

            # GPU測試
            start = time.time()
            gpu_rsi = gpu_indicators.rsi(test_data, 14)
            gpu_time = time.time() - start

            # CPU測試
            start = time.time()
            cpu_rsi = cpu_indicators.rsi(test_data, 14)
            cpu_time = time.time() - start

            # 計算加速比
            speedup = cpu_time / gpu_time if gpu_time > 0 else 0

            print(f"{size:<10} {gpu_time:<12.6f} {cpu_time:<12.6f} {speedup:<8.2f}")

        return True

    except Exception as e:
        print(f"❌ 性能測試失敗: {e}")
        return False

def test_batch_optimization():
    """測試批量計算優化"""
    print("\n=== 批量計算優化測試 ===")

    try:
        from fixed_gpu_indicators import FixedGPUTechnicalIndicators

        # 獲取數據
        prices = get_0700hk_data()
        if prices is None:
            return False

        gpu_indicators = FixedGPUTechnicalIndicators(use_gpu=True)

        # 批量計算配置
        indicators_config = {
            'rsi': {'period': 14},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9},
            'bollinger': {'period': 20, 'std_dev': 2.0}
        }

        print("📦 批量計算指標...")
        start = time.time()
        results = gpu_indicators.calculate_batch_indicators(prices, indicators_config)
        batch_time = time.time() - start

        print(f"批量計算時間: {batch_time:.6f}s")
        print(f"計算的指標數: {len(results)}")
        print(f"指標列表: {list(results.keys())}")

        # 顯示部分結果
        if 'RSI' in results:
            print(f"RSI最新值: {results['RSI'][-1]:.2f}")
        if 'MACD' in results:
            print(f"MACD最新值: {results['MACD'][-1]:.4f}")

        return True

    except Exception as e:
        print(f"❌ 批量測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("修復版GPU指標系統測試")
    print("=" * 60)

    tests = [
        ("原始 vs 修復版本對比", test_original_vs_fixed),
        ("不同數據大小性能", test_performance_with_different_sizes),
        ("批量計算優化", test_batch_optimization)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🔄 開始測試: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"{test_name}: {status}")
        except Exception as e:
            print(f"{test_name}: ❌ 錯誤 - {e}")
            results.append((test_name, False))

    # 總結
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:25}: {status}")
        if result:
            passed += 1

    print(f"\n總體結果: {passed}/{len(results)} 測試通過")

    if passed == len(results):
        print("🎉 所有修復版測試通過！GPU優化成功！")
    else:
        print("⚠️ 部分測試失敗，需要進一步調整。")

    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)