#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VectorBT GPU加速演示 - 0700.HK專用
展示CuPy集成和GPU加速技術指標計算
"""

import numpy as np
import pandas as pd
import time
import requests
from datetime import datetime

# GPU檢測和導入
try:
    import cupy as cp
    GPU_AVAILABLE = True
    print("[GPU] CuPy已安裝")
    try:
        gpu_count = cp.cuda.runtime.getDeviceCount()
        if gpu_count > 0:
            print(f"[GPU] 檢測到{gpu_count}個CUDA設備")
            print(f"[GPU] 使用設備0進行計算")
            cp.cuda.Device(0).use()
        else:
            print("[GPU] 無CUDA設備，將使用CPU模式")
            GPU_AVAILABLE = False
    except Exception as e:
        print(f"[GPU] CUDA初始化失敗: {e}")
        GPU_AVAILABLE = False
except ImportError:
    print("[GPU] CuPy未安裝，使用CPU模式")
    GPU_AVAILABLE = False

# VectorBT導入
try:
    import vectorbt as vbt
    print(f"[VectorBT] 版本: {vbt.__version__}")
except ImportError:
    print("[ERROR] VectorBT未安裝")
    exit(1)

class VectorBTGPUDemo:
    """VectorBT GPU加速演示類"""

    def __init__(self):
        self.gpu_available = GPU_AVAILABLE
        self.data = None

    def fetch_0700_data(self):
        """獲取0700.HK真實數據"""
        try:
            print("[API] 獲取0700.HK數據...")
            url = "http://18.180.162.113:9191/inst/getInst"
            params = {"symbol": "0700.hk", "duration": 365}

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # 解析數據
            dates = list(data['data']['close'].keys())
            close_prices = list(data['data']['close'].values())

            self.data = pd.DataFrame({
                'close': close_prices
            }, index=pd.to_datetime(dates))

            # 生成OHLC數據
            np.random.seed(42)
            self.data['high'] = self.data['close'] * (1 + np.random.uniform(0, 0.02, len(self.data)))
            self.data['low'] = self.data['close'] * (1 - np.random.uniform(0, 0.02, len(self.data)))
            self.data['open'] = self.data['close'].shift(1).fillna(self.data['close'].iloc[0])
            self.data['volume'] = np.random.randint(1000000, 10000000, len(self.data))

            print(f"[API] 獲取{len(self.data)}條記錄成功")
            return True

        except Exception as e:
            print(f"[ERROR] 數據獲取失敗: {e}")
            return False

    def rsi_gpu_calculation(self, prices, period=14):
        """GPU加速RSI計算"""
        if not self.gpu_available:
            return self.rsi_cpu_calculation(prices, period)

        try:
            # GPU版本計算
            prices_gpu = cp.asarray(prices)
            delta = cp.diff(prices_gpu)
            gain = cp.where(delta > 0, delta, 0)
            loss = cp.where(delta < 0, -delta, 0)

            # 使用rolling window
            avg_gain = cp.convolve(gain, cp.ones(period), mode='valid') / period
            avg_loss = cp.convolve(loss, cp.ones(period), mode='valid') / period

            # 避免除零
            rs = avg_gain / cp.where(avg_loss == 0, 1e-10, avg_loss)
            rsi = 100 - (100 / (1 + rs))

            # 填充前面NaN值
            rsi_full = cp.concatenate([cp.full(period-1, cp.nan), rsi])
            return cp.asnumpy(rsi_full)

        except Exception as e:
            print(f"[GPU] RSI計算失敗，回退到CPU: {e}")
            return self.rsi_cpu_calculation(prices, period)

    def rsi_cpu_calculation(self, prices, period=14):
        """CPU版本RSI計算"""
        delta = np.diff(prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = pd.Series(gain).rolling(window=period).mean()
        avg_loss = pd.Series(loss).rolling(window=period).mean()

        rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
        rsi = 100 - (100 / (1 + rs))

        return rsi.values

    def macd_gpu_calculation(self, prices, fast=12, slow=26, signal=9):
        """GPU加速MACD計算"""
        if not self.gpu_available:
            return self.macd_cpu_calculation(prices, fast, slow, signal)

        try:
            prices_gpu = cp.asarray(prices)

            # EMA計算
            def ema_gpu(data, period):
                alpha = 2 / (period + 1)
                ema = cp.zeros_like(data)
                ema[0] = data[0]
                for i in range(1, len(data)):
                    ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
                return ema

            ema_fast = ema_gpu(prices_gpu, fast)
            ema_slow = ema_gpu(prices_gpu, slow)
            macd_line = ema_fast - ema_slow
            signal_line = ema_gpu(macd_line, signal)
            histogram = macd_line - signal_line

            return {
                'MACD': cp.asnumpy(macd_line),
                'SIGNAL': cp.asnumpy(signal_line),
                'HIST': cp.asnumpy(histogram)
            }

        except Exception as e:
            print(f"[GPU] MACD計算失敗，回退到CPU: {e}")
            return self.macd_cpu_calculation(prices, fast, slow, signal)

    def macd_cpu_calculation(self, prices, fast=12, slow=26, signal=9):
        """CPU版本MACD計算"""
        prices_series = pd.Series(prices)
        ema_fast = prices_series.ewm(span=fast).mean()
        ema_slow = prices_series.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line

        return {
            'MACD': macd_line.values,
            'SIGNAL': signal_line.values,
            'HIST': histogram.values
        }

    def performance_test(self):
        """性能測試比較"""
        if self.data is None:
            print("[ERROR] 無數據進行測試")
            return

        prices = self.data['close'].values
        print(f"\n[PERF] 性能測試開始，數據量: {len(prices)}")

        # RSI性能測試
        print("\n[RSI] RSI計算性能測試...")

        # CPU版本
        start_time = time.time()
        rsi_cpu = self.rsi_cpu_calculation(prices, 14)
        cpu_time = time.time() - start_time
        print(f"  CPU時間: {cpu_time:.4f}秒")

        # GPU版本（如果可用）
        if self.gpu_available:
            start_time = time.time()
            rsi_gpu = self.rsi_gpu_calculation(prices, 14)
            gpu_time = time.time() - start_time
            print(f"  GPU時間: {gpu_time:.4f}秒")
            print(f"  加速比: {cpu_time/gpu_time:.2f}x")

            # 檢查結果一致性
            diff = np.abs(rsi_cpu - rsi_gpu)
            max_diff = np.nanmax(diff)
            print(f"  最大差異: {max_diff:.6f}")
        else:
            print("  GPU不可用")

        # MACD性能測試
        print("\n[MACD] MACD計算性能測試...")

        # CPU版本
        start_time = time.time()
        macd_cpu = self.macd_cpu_calculation(prices)
        cpu_time = time.time() - start_time
        print(f"  CPU時間: {cpu_time:.4f}秒")

        # GPU版本（如果可用）
        if self.gpu_available:
            start_time = time.time()
            macd_gpu = self.macd_gpu_calculation(prices)
            gpu_time = time.time() - start_time
            print(f"  GPU時間: {gpu_time:.4f}秒")
            print(f"  加速比: {cpu_time/gpu_time:.2f}x")
        else:
            print("  GPU不可用")

    def vectorbt_integration_demo(self):
        """VectorBT集成演示"""
        if self.data is None:
            print("[ERROR] 無數據進行VectorBT測試")
            return

        print("\n[VBT] VectorBT集成演示...")

        try:
            # 創建價格數據
            price_data = self.data['close']

            # RSI策略測試
            print("  測試RSI策略...")
            rsi = vbt.RSI.run(price_data, window=14)
            print(f"  RSI計算完成，最新值: {rsi.rsi.iloc[-1]:.2f}")

            # MACD策略測試
            print("  測試MACD策略...")
            macd = vbt.MACD.run(price_data, fast=12, slow=26, signal=9)
            print(f"  MACD計算完成，最新值: {macd.macd.iloc[-1]:.4f}")

            # 簡單回測
            print("  執行簡單回測...")
            entries = rsi.rsi_below(30)  # RSI < 30 買入
            exits = rsi.rsi_above(70)    # RSI > 70 賣出

            pf = vbt.Portfolio.from_signals(price_data, entries, exits)
            print(f"  總回報: {pf.total_return():.2%}")
            print(f"  Sharpe比率: {pf.sharpe_ratio():.3f}")

        except Exception as e:
            print(f"  VectorBT測試失敗: {e}")

    def run_full_demo(self):
        """運行完整演示"""
        print("=" * 60)
        print("VectorBT GPU加速演示 - 0700.HK")
        print("=" * 60)

        # 數據獲取
        if not self.fetch_0700_data():
            print("[ERROR] 數據獲取失敗")
            return

        # 性能測試
        self.performance_test()

        # VectorBT集成
        self.vectorbt_integration_demo()

        print("\n" + "=" * 60)
        print("演示完成!")
        print(f"GPU加速: {'可用' if self.gpu_available else '不可用'}")
        print(f"數據記錄: {len(self.data)} 條")
        print(f"當前價格: ${self.data['close'].iloc[-1]:.2f}")
        print("=" * 60)

def main():
    """主函數"""
    demo = VectorBTGPUDemo()
    demo.run_full_demo()

if __name__ == "__main__":
    main()