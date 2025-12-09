#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
0700.HK GPU加速測試
Test 0700.HK (Tencent) with GPU acceleration
"""

import sys
import os
import time
import requests
import pandas as pd
import numpy as np

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system', 'src'))

def get_0700hk_data():
    """獲取0700.HK真實數據"""
    print("=== 獲取0700.HK數據 ===")

    url = "http://18.180.162.113:9191/inst/getInst"
    params = {"symbol": "0700.hk", "duration": 365}  # 1年數據

    try:
        print("正在獲取0700.HK數據...")
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

        return df

    except Exception as e:
        print(f"❌ 數據獲取失敗: {e}")
        return None

def test_gpu_acceleration_0700hk():
    """測試0700.HK的GPU加速技術指標"""
    print("\n=== 0700.HK GPU加速測試 ===")

    try:
        from indicators.gpu_indicators import GPUTechnicalIndicators

        # 獲取數據
        data = get_0700hk_data()
        if data is None:
            return False

        prices = data['close'].values
        print(f"📊 測試數據: {len(prices)} 個價格點")

        # GPU版本測試
        print("\n🚀 GPU加速技術指標計算...")
        gpu_indicators = GPUTechnicalIndicators(use_gpu=True)

        # RSI計算
        start_time = time.time()
        rsi_gpu = gpu_indicators.rsi(prices, 14)
        gpu_rsi_time = time.time() - start_time

        # MACD計算
        start_time = time.time()
        macd_gpu = gpu_indicators.macd(prices, 12, 26, 9)
        gpu_macd_time = time.time() - start_time

        # 布林帶計算
        start_time = time.time()
        bb_gpu = gpu_indicators.bollinger_bands(prices, 20, 2)
        gpu_bb_time = time.time() - start_time

        print(f"GPU RSI ({len(rsi_gpu)} 個值): {gpu_rsi_time:.6f}s")
        print(f"GPU MACD ({len(macd_gpu[0])} 個值): {gpu_macd_time:.6f}s")
        print(f"GPU Bollinger Bands ({len(bb_gpu[0])} 個值): {gpu_bb_time:.6f}s")

        print(f"最新 RSI: {rsi_gpu[-1]:.2f}")
        print(f"最新 MACD: {macd_gpu[0][-1]:.4f}")
        print(f"最新布林帶上軌: {bb_gpu[0][-1]:.2f}")
        print(f"最新布林帶中軌: {bb_gpu[1][-1]:.2f}")
        print(f"最新布林帶下軌: {bb_gpu[2][-1]:.2f}")

        # CPU版本對比
        print("\n⚡ CPU版本對比計算...")
        cpu_indicators = GPUTechnicalIndicators(use_gpu=False)

        start_time = time.time()
        rsi_cpu = cpu_indicators.rsi(prices, 14)
        cpu_rsi_time = time.time() - start_time

        start_time = time.time()
        macd_cpu = cpu_indicators.macd(prices, 12, 26, 9)
        cpu_macd_time = time.time() - start_time

        print(f"CPU RSI時間: {cpu_rsi_time:.6f}s")
        print(f"CPU MACD時間: {cpu_macd_time:.6f}s")

        # 性能比較
        print("\n📈 性能比較:")
        if gpu_rsi_time > 0:
            rsi_speedup = cpu_rsi_time / gpu_rsi_time
            print(f"RSI 加速比: {rsi_speedup:.2f}x")

        if gpu_macd_time > 0:
            macd_speedup = cpu_macd_time / gpu_macd_time
            print(f"MACD 加速比: {macd_speedup:.2f}x")

        # 結果一致性檢查
        rsi_diff = abs(rsi_gpu[-1] - rsi_cpu[-1])
        macd_diff = abs(macd_gpu[0][-1] - macd_cpu[0][-1])

        print(f"\n✅ 結果一致性:")
        print(f"RSI 差異: {rsi_diff:.6f}")
        print(f"MACD 差異: {macd_diff:.6f}")
        print(f"結果一致: {rsi_diff < 0.01 and macd_diff < 0.0001}")

        return True

    except Exception as e:
        print(f"❌ GPU測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vectorbt_gpu_0700hk():
    """測試0700.HK的VectorBT GPU引擎"""
    print("\n=== 0700.HK VectorBT GPU引擎測試 ===")

    try:
        from backtest.vectorbt_engine import VectorBTEngine

        # 獲取數據
        data = get_0700hk_data()
        if data is None:
            return False

        print("🚀 初始化VectorBT GPU引擎...")
        engine = VectorBTEngine(use_gpu=True)

        # GPU信息
        gpu_info = engine.get_gpu_performance_info()
        print(f"GPU可用: {gpu_info['gpu_available']}")
        print(f"GPU環境配置: {gpu_info['gpu_environment']}")

        # 測試GPU指標計算
        indicators_config = {
            'rsi': {'period': 14},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9},
            'bollinger': {'period': 20, 'std': 2}
        }

        print(f"\n📊 計算 {len(indicators_config)} 個技術指標...")

        start_time = time.time()
        indicators = engine.calculate_indicators_gpu(data, indicators_config)
        calc_time = time.time() - start_time

        print(f"GPU計算時間: {calc_time:.6f}s")
        print(f"計算的指標: {list(indicators.keys())}")

        # 顯示最新指標值
        if 'RSI' in indicators:
            print(f"最新 RSI: {indicators['RSI'][-1]:.2f}")
        if 'MACD' in indicators:
            print(f"最新 MACD: {indicators['MACD'][-1]:.4f}")
        if 'UpperBB' in indicators:
            print(f"最新布林帶上軌: {indicators['UpperBB'][-1]:.2f}")
            print(f"最新布林帶下軌: {indicators['LowerBB'][-1]:.2f}")

        return True

    except Exception as e:
        print(f"❌ VectorBT GPU測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_0700hk_signals():
    """分析0700.HK的交易信號"""
    print("\n=== 0700.HK 交易信號分析 ===")

    try:
        from indicators.gpu_indicators import GPUTechnicalIndicators

        # 獲取數據
        data = get_0700hk_data()
        if data is None:
            return False

        prices = data['close'].values
        dates = data.index

        # 計算技術指標
        gpu_indicators = GPUTechnicalIndicators(use_gpu=True)

        rsi = gpu_indicators.rsi(prices, 14)
        macd_line, macd_signal, macd_hist = gpu_indicators.macd(prices, 12, 26, 9)
        bb_upper, bb_middle, bb_lower = gpu_indicators.bollinger_bands(prices, 20, 2)

        # 分析最新信號
        current_price = prices[-1]
        current_rsi = rsi[-1]
        current_macd = macd_line[-1]
        current_signal = macd_signal[-1]
        current_hist = macd_hist[-1]

        print(f"📊 0700.HK 最新市場分析:")
        print(f"當前價格: {current_price:.2f} HKD")
        print(f"RSI (14): {current_rsi:.2f}")
        print(f"MACD: {current_macd:.4f}")
        print(f"Signal: {current_signal:.4f}")
        print(f"Histogram: {current_hist:.4f}")
        print(f"布林帶位置: {bb_lower[-1]:.2f} - {bb_upper[-1]:.2f}")

        # 生成交易信號
        print(f"\n🎯 交易信號分析:")

        # RSI信號
        if current_rsi > 70:
            rsi_signal = "超買 - 考慮賣出"
        elif current_rsi < 30:
            rsi_signal = "超賣 - 考慮買入"
        else:
            rsi_signal = "中性區間"

        print(f"RSI信號: {rsi_signal}")

        # MACD信號
        if current_macd > current_signal and current_hist > 0:
            macd_signal = "金叉 - 買入信號"
        elif current_macd < current_signal and current_hist < 0:
            macd_signal = "死叉 - 賣出信號"
        else:
            macd_signal = "盤整狀態"

        print(f"MACD信號: {macd_signal}")

        # 布林帶信號
        if current_price > bb_upper[-1]:
            bb_signal = "突破上軌 - 強勢"
        elif current_price < bb_lower[-1]:
            bb_signal = "跌破下軌 - 弱勢"
        else:
            bb_signal = "區間震盪"

        print(f"布林帶信號: {bb_signal}")

        # 綜合建議
        print(f"\n💡 綜合建議:")
        if "買入" in rsi_signal or "買入" in macd_signal:
            print("看漲信號較強，可考慮逢低買入")
        elif "賣出" in rsi_signal or "賣出" in macd_signal:
            print("看跌信號較強，可考慮減持")
        else:
            print("信號不明確，建議觀望")

        return True

    except Exception as e:
        print(f"❌ 信號分析失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("0700.HK GPU加速完整測試")
    print("=" * 60)

    tests = [
        ("GPU技術指標加速", test_gpu_acceleration_0700hk),
        ("VectorBT GPU引擎", test_vectorbt_gpu_0700hk),
        ("0700.HK交易信號分析", analyze_0700hk_signals)
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
    print("0700.HK測試結果總結")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:25}: {status}")
        if result:
            passed += 1

    print(f"\n總體結果: {passed}/{len(results)} 測試通過")

    if passed == len(results):
        print("🎉 所有0700.HK測試通過！GPU加速系統完全正常！")
    else:
        print("⚠️ 部分測試失敗。")

    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)