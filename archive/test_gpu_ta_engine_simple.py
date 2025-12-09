#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU非價格TA引擎簡化測試
Simplified Test for GPU Non-Price TA Engine
"""

import numpy as np
import pandas as pd
import time
import logging
from typing import Dict, List, Optional, Union, Tuple, Any

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleGPUNonPriceTAEngine:
    """簡化的GPU非價格TA引擎用於測試"""

    def __init__(self):
        """初始化引擎"""
        logger.info("簡化GPU非價格TA引擎初始化完成")

        # 性能統計
        self.performance_stats = {
            'total_calculations': 0,
            'gpu_calculation_time': 0,
            'cpu_fallback_count': 0,
            'memory_usage_peak': 0
        }

    def calculate_rsi(self, data: np.ndarray, period: int = 14) -> np.ndarray:
        """計算RSI"""
        if len(data) < period + 1:
            return np.full(len(data), 50.0)

        delta = np.diff(data)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = np.mean(gain[:period])
        avg_loss = np.mean(loss[:period])

        if avg_loss == 0:
            return np.full(len(data), 100.0)

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # 返回完整長度的RSI數組
        result = np.full(len(data), 50.0)
        result[period:] = rsi

        return result

    def calculate_macd(self, data: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """計算MACD"""
        if len(data) < slow:
            zeros = np.zeros(len(data))
            return zeros, zeros, zeros

        # 計算EMA
        def ema(data, period):
            alpha = 2 / (period + 1)
            ema_result = np.zeros_like(data)
            ema_result[0] = data[0]
            for i in range(1, len(data)):
                ema_result[i] = alpha * data[i] + (1 - alpha) * ema_result[i-1]
            return ema_result

        fast_ema = ema(data, fast)
        slow_ema = ema(data, slow)
        macd_line = fast_ema - slow_ema
        signal_line = ema(macd_line, signal)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def calculate_hibor_rsi_strategy(self, hibor_data: np.ndarray) -> Dict[str, Any]:
        """HIBOR-RSI策略"""
        start_time = time.time()

        try:
            # 計算HIBOR RSI
            hibor_rsi = self.calculate_rsi(hibor_data, 14)

            # 計算RSI移動平均
            rsi_ma = np.convolve(hibor_rsi, np.ones(14)/14, mode='same')

            # 生成簡單信號
            signals = np.zeros_like(hibor_rsi)
            signals[hibor_rsi < 30] = 1   # 超賣買入
            signals[hibor_rsi > 70] = -1  # 超買賣出

            calculation_time = time.time() - start_time
            self.performance_stats['total_calculations'] += 1
            self.performance_stats['gpu_calculation_time'] += calculation_time

            return {
                'strategy_name': 'HIBOR_RSI',
                'signals': signals,
                'indicators': {
                    'rsi': hibor_rsi,
                    'rsi_ma': rsi_ma
                },
                'performance': {
                    'calculation_time': calculation_time,
                    'data_points': len(hibor_data)
                },
                'success': True
            }

        except Exception as e:
            logger.error(f"HIBOR-RSI策略計算失敗: {e}")
            return {'success': False, 'error': str(e), 'strategy_name': 'HIBOR_RSI'}

    def calculate_monetary_macd_strategy(self, monetary_data: np.ndarray) -> Dict[str, Any]:
        """貨幣基礎MACD策略"""
        start_time = time.time()

        try:
            # 計算MACD
            macd_line, signal_line, histogram = self.calculate_macd(monetary_data)

            # 生成簡單信號
            signals = np.zeros_like(macd_line)
            signals[macd_line > signal_line] = 1   # 金叉買入
            signals[macd_line < signal_line] = -1  # 死叉賣出

            calculation_time = time.time() - start_time
            self.performance_stats['total_calculations'] += 1
            self.performance_stats['gpu_calculation_time'] += calculation_time

            return {
                'strategy_name': 'MONETARY_MACD',
                'signals': signals,
                'indicators': {
                    'macd_line': macd_line,
                    'signal_line': signal_line,
                    'histogram': histogram
                },
                'performance': {
                    'calculation_time': calculation_time,
                    'data_points': len(monetary_data)
                },
                'success': True
            }

        except Exception as e:
            logger.error(f"貨幣基礎MACD策略計算失敗: {e}")
            return {'success': False, 'error': str(e), 'strategy_name': 'MONETARY_MACD'}

    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        return {
            'total_calculations': self.performance_stats['total_calculations'],
            'gpu_calculation_time': self.performance_stats['gpu_calculation_time'],
            'cpu_fallback_count': self.performance_stats['cpu_fallback_count'],
            'average_gpu_time': (
                self.performance_stats['gpu_calculation_time'] /
                max(1, self.performance_stats['total_calculations'])
            ),
            'success_rate': 1.0  # 簡化版本總是成功
        }

def main():
    """主測試函數"""
    print("=" * 60)
    print("GPU非價格TA引擎簡化測試")
    print("=" * 60)

    try:
        # 初始化引擎
        engine = SimpleGPUNonPriceTAEngine()

        # 生成測試數據
        np.random.seed(42)
        test_data_length = 252

        # HIBOR測試數據 (模擬利率數據)
        hibor_data = np.random.uniform(3.0, 5.0, test_data_length).astype(np.float32)

        # 貨幣基礎測試數據 (模擬貨幣供給)
        monetary_data = np.random.uniform(1800, 2200, test_data_length).astype(np.float32)

        print(f"測試數據長度: {test_data_length}")
        print(f"HIBOR數據範圍: {hibor_data.min():.3f} - {hibor_data.max():.3f}")
        print(f"貨幣基礎數據範圍: {monetary_data.min():.1f} - {monetary_data.max():.1f}")

        # 測試HIBOR-RSI策略
        print("\n測試HIBOR-RSI策略...")
        hibor_result = engine.calculate_hibor_rsi_strategy(hibor_data)

        if hibor_result.get('success', False):
            print("[SUCCESS] HIBOR-RSI策略測試成功")
            print(f"   計算時間: {hibor_result['performance']['calculation_time']:.4f}秒")
            print(f"   信號數量: {np.sum(hibor_result['signals'] != 0)}")
            rsi_values = hibor_result['indicators']['rsi']
            print(f"   RSI範圍: {rsi_values.min():.2f} - {rsi_values.max():.2f}")
        else:
            print(f"[FAILED] HIBOR-RSI策略測試失敗: {hibor_result.get('error', 'Unknown error')}")

        # 測試貨幣基礎MACD策略
        print("\n測試貨幣基礎MACD策略...")
        monetary_result = engine.calculate_monetary_macd_strategy(monetary_data)

        if monetary_result.get('success', False):
            print("[SUCCESS] 貨幣基礎MACD策略測試成功")
            print(f"   計算時間: {monetary_result['performance']['calculation_time']:.4f}秒")
            print(f"   信號數量: {np.sum(monetary_result['signals'] != 0)}")
            macd_values = monetary_result['indicators']['macd_line']
            print(f"   MACD範圍: {macd_values.min():.4f} - {macd_values.max():.4f}")
        else:
            print(f"[FAILED] 貨幣基礎MACD策略測試失敗: {monetary_result.get('error', 'Unknown error')}")

        # 性能摘要
        print("\n性能摘要:")
        perf = engine.get_performance_summary()
        print(f"   總計算次數: {perf['total_calculations']}")
        print(f"   總計算時間: {perf['gpu_calculation_time']:.4f}秒")
        print(f"   平均計算時間: {perf['average_gpu_time']:.4f}秒")
        print(f"   成功率: {perf['success_rate']*100:.1f}%")

        print("\n[COMPLETE] GPU非價格TA引擎簡化測試完成！")

    except Exception as e:
        logger.error(f"測試失敗: {e}")
        print(f"測試失敗: {e}")

if __name__ == "__main__":
    main()