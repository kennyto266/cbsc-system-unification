#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VectorBT GPU集成測試
測試GPU加速技術指標計算和回測功能
"""

import sys
import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system', 'src'))

def fetch_0700_data():
    """獲取0700.HK真實數據"""
    try:
        print("[API] 獲取0700.HK真實數據...")
        url = "http://18.180.162.113:9191/inst/getInst"
        params = {"symbol": "0700.hk", "duration": 730}

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # 解析數據
        dates = list(data['data']['close'].keys())
        close_prices = list(data['data']['close'].values())

        df = pd.DataFrame({
            'close': close_prices
        }, index=pd.to_datetime(dates))

        # 生成OHLC數據
        np.random.seed(42)
        df['high'] = df['close'] * (1 + np.random.uniform(0, 0.02, len(df)))
        df['low'] = df['close'] * (1 - np.random.uniform(0, 0.02, len(df)))
        df['open'] = df['close'].shift(1).fillna(df['close'].iloc[0])
        df['volume'] = np.random.randint(1000000, 10000000, len(df))

        print(f"[API] 成功獲取{len(df)}條記錄")
        return df.sort_index()

    except Exception as e:
        print(f"[ERROR] 數據獲取失敗: {e}")
        return None

def test_gpu_detection():
    """測試GPU檢測功能"""
    print("\n=== GPU檢測測試 ===")

    try:
        from utils.gpu_detector import get_gpu_environment, is_gpu_available

        gpu_env = get_gpu_environment()
        gpu_info = gpu_env.get_system_info()

        print(f"GPU可用性: {is_gpu_available()}")
        print(f"計算後端: {gpu_env.get_compute_backend()}")
        print(f"CuPy可用: {gpu_info['cupy_available']}")
        print(f"CUDA可用: {gpu_info['cuda_available']}")
        print(f"GPU數量: {gpu_info['gpu_count']}")

        if gpu_info['gpu_count'] > 0:
            print(f"GPU內存: {gpu_info['gpu_memory_gb']:.1f} GB")

        # 測試GPU計算
        test_result = gpu_env.test_gpu_computation(1000)
        if test_result['gpu_test_passed']:
            print(f"GPU計算測試: 通過")
            print(f"加速比: {test_result['speedup']:.2f}x")
        else:
            print(f"GPU計算測試: 失敗 - {test_result['error']}")

        return gpu_env.is_gpu_available()

    except Exception as e:
        print(f"[ERROR] GPU檢測測試失敗: {e}")
        return False

def test_gpu_indicators():
    """測試GPU加速技術指標"""
    print("\n=== GPU技術指標測試 ===")

    try:
        from indicators.gpu_indicators import GPUTechnicalIndicators

        # 生成測試數據
        np.random.seed(42)
        prices = np.cumprod(1 + np.random.normal(0.001, 0.02, 1000)) * 100

        # 測試GPU版本
        print("[GPU] 初始化GPU技術指標...")
        gpu_indicators = GPUTechnicalIndicators(use_gpu=True)

        # 計算RSI
        print("[GPU] 計算RSI...")
        start_time = time.time()
        rsi_gpu = gpu_indicators.rsi(prices, 14)
        gpu_time = time.time() - start_time
        print(f"GPU RSI時間: {gpu_time:.4f}秒")

        # 計算MACD
        print("[GPU] 計算MACD...")
        start_time = time.time()
        macd_gpu = gpu_indicators.macd(prices, 12, 26, 9)
        gpu_time = time.time() - start_time
        print(f"GPU MACD時間: {gpu_time:.4f}秒")

        # 計算布林帶
        print("[GPU] 計算布林帶...")
        start_time = time.time()
        bb_gpu = gpu_indicators.bollinger_bands(prices, 20, 2.0)
        gpu_time = time.time() - start_time
        print(f"GPU 布林帶時間: {gpu_time:.4f}秒")

        # 批量計算
        print("[GPU] 批量計算技術指標...")
        indicators_config = {
            'rsi': {'period': 14},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9},
            'bollinger': {'period': 20, 'std_dev': 2.0}
        }

        start_time = time.time()
        all_indicators = gpu_indicators.calculate_multiple_indicators(prices, indicators_config)
        batch_time = time.time() - start_time
        print(f"GPU 批量計算時間: {batch_time:.4f}秒")
        print(f"計算指標數量: {len(all_indicators)}")

        # 顯示後端信息
        backend_info = gpu_indicators.get_backend_info()
        print(f"後端信息: {backend_info}")

        return True

    except Exception as e:
        print(f"[ERROR] GPU技術指標測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vectorbt_gpu_engine():
    """測試VectorBT GPU引擎"""
    print("\n=== VectorBT GPU引擎測試 ===")

    try:
        from backtest.vectorbt_engine import VectorBTEngine

        print("[VBT] 初始化VectorBT GPU引擎...")
        engine = VectorBTEngine(use_gpu=True)

        # 獲取GPU性能信息
        gpu_info = engine.get_gpu_performance_info()
        print(f"GPU可用: {gpu_info['gpu_available']}")
        print(f"GPU環境: {gpu_info['gpu_environment']}")

        # 獲取測試數據
        data = fetch_0700_data()
        if data is None:
            print("[ERROR] 無法獲取測試數據")
            return False

        print(f"[VBT] 測試數據: {len(data)}條記錄")

        # 測試GPU指標計算
        print("[VBT] 測試GPU指標計算...")
        indicators_config = {
            'rsi': {'period': 14},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9}
        }

        start_time = time.time()
        indicators = engine.calculate_indicators_gpu(data, indicators_config)
        calc_time = time.time() - start_time

        print(f"指標計算完成，耗時: {calc_time:.4f}秒")
        print(f"計算指標: {list(indicators.keys())}")

        # 顯示一些結果
        if 'RSI' in indicators:
            rsi_latest = indicators['RSI'][-1]
            print(f"最新RSI: {rsi_latest:.2f}")

        if 'MACD' in indicators:
            macd_latest = indicators['MACD'][-1]
            print(f"最新MACD: {macd_latest:.4f}")

        return True

    except Exception as e:
        print(f"[ERROR] VectorBT GPU引擎測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gpu_optimization():
    """測試GPU參數優化"""
    print("\n=== GPU參數優化測試 ===")

    try:
        from backtest.vectorbt_engine import VectorBTEngine

        # 獲取測試數據（使用較少數據加快測試）
        data = fetch_0700_data()
        if data is None:
            print("[ERROR] 無法獲取測試數據")
            return False

        # 使用最近的數據
        data = data.tail(100)  # 只用最近100條記錄
        print(f"[OPT] 使用{len(data)}條數據進行優化測試")

        # 初始化GPU引擎
        engine = VectorBTEngine(use_gpu=True)

        # 定義參數範圍（較小範圍加快測試）
        param_ranges = {
            'period': [10, 14, 20, 25],
            'oversold': [20, 25, 30],
            'overbought': [70, 75, 80]
        }

        print("[OPT] 開始GPU參數優化...")
        start_time = time.time()

        optimization_result = engine.gpu_optimize_parameters(
            data=data,
            strategy="RSI_MEAN_REVERSION",
            param_ranges=param_ranges,
            symbol="0700.HK",
            optimization_metric="sharpe_ratio"
        )

        optimization_time = time.time() - start_time

        print(f"[OPT] 優化完成，耗時: {optimization_time:.2f}秒")
        print(f"[OPT] 測試組合數: {optimization_result['total_combinations']}")
        print(f"[OPT] 成功組合數: {optimization_result['successful_combinations']}")
        print(f"[OPT] 處理速度: {optimization_result['strategies_per_second']:.1f} 策略/秒")

        # 顯示最佳結果
        best_perf = optimization_result['best_performance']
        print(f"[OPT] 最佳Sharpe: {best_perf['performance']['sharpe_ratio']:.3f}")
        print(f"[OPT] 最佳回報: {best_perf['performance']['total_return']:.2f}%")
        print(f"[OPT] 最佳參數: {optimization_result['best_parameters']}")

        return True

    except Exception as e:
        print(f"[ERROR] GPU參數優化測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("=" * 80)
    print("VectorBT GPU集成測試")
    print("=" * 80)

    # 運行所有測試
    tests = [
        ("GPU檢測", test_gpu_detection),
        ("GPU技術指標", test_gpu_indicators),
        ("VectorBT GPU引擎", test_vectorbt_gpu_engine),
        ("GPU參數優化", test_gpu_optimization)
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n開始測試: {test_name}")
        try:
            results[test_name] = test_func()
            status = "通過" if results[test_name] else "失敗"
            print(f"✓ {test_name}: {status}")
        except Exception as e:
            print(f"✗ {test_name}: 錯誤 - {e}")
            results[test_name] = False

    # 總結
    print("\n" + "=" * 80)
    print("測試結果總結")
    print("=" * 80)

    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:20}: {status}")

    passed = sum(results.values())
    total = len(results)
    print(f"\n總體結果: {passed}/{total} 測試通過")

    if passed == total:
        print("🎉 所有測試通過！VectorBT GPU集成成功！")
    else:
        print("⚠️ 部分測試失敗，請檢查錯誤信息")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)