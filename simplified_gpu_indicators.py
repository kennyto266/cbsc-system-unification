#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化但有效的GPU加速技術指標計算模塊
基於CuPy 13.6，移除複雜依賴，專注實際GPU加速
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Union, Tuple

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.gpu_detector import get_gpu_environment

logger = logging.getLogger(__name__)

class SimplifiedGPUTechnicalIndicators:
    """簡化但高效的GPU加速技術指標計算類"""

    def __init__(self, use_gpu: bool = True):
        """
        初始化簡化GPU技術指標計算器

        Args:
            use_gpu: 是否使用GPU加速（默認為True）
        """
        self.gpu_env = get_gpu_environment()
        self.use_gpu = use_gpu and self.gpu_env.is_gpu_available()
        self.backend = 'gpu' if self.use_gpu else 'cpu'

        if self.use_gpu:
            try:
                import cupy as cp
                self.cp = cp

                # 簡單的CUDA流設置
                self.stream = cp.cuda.Stream()

                logger.info("Simplified GPU Technical Indicators initialized")
            except ImportError:
                logger.warning("CuPy not available, falling back to CPU")
                self.use_gpu = False
                self.backend = 'cpu'
                self.cp = None
        else:
            self.cp = None

        logger.info(f"Simplified GPU Technical Indicators initialized with backend: {self.backend}")

    def _to_gpu(self, data: np.ndarray) -> Union[np.ndarray, 'cp.ndarray']:
        """將數據轉移到GPU"""
        if self.use_gpu and self.cp is not None:
            with self.stream:
                return self.cp.asarray(data)
        return data

    def _to_cpu(self, data: Union[np.ndarray, 'cp.ndarray']) -> np.ndarray:
        """將數據從GPU轉移到CPU"""
        if self.use_gpu and self.cp is not None and hasattr(data, 'get'):
            with self.stream:
                return data.get()
        return data

    def rsi(self, prices: Union[np.ndarray, pd.Series], period: int = 14) -> np.ndarray:
        """
        計算RSI指標（簡化GPU加速）

        Args:
            prices: 價格數據
            period: RSI週期

        Returns:
            RSI值數組
        """
        if isinstance(prices, pd.Series):
            prices = prices.values

        # 只有數據足夠大且數據質量好才使用GPU
        if self.use_gpu and len(prices) >= period * 3 and np.std(prices) > 1e-6:
            return self._rsi_gpu_simple(prices, period)
        else:
            return self._rsi_cpu(prices, period)

    def _rsi_gpu_simple(self, prices: np.ndarray, period: int) -> np.ndarray:
        """GPU簡化版本的RSI計算"""
        try:
            with self.stream:
                prices_gpu = self._to_gpu(prices)

                # 簡單高效的向量化計算
                delta = self.cp.diff(prices_gpu)
                gain = self.cp.where(delta > 0, delta, 0)
                loss = self.cp.where(delta < 0, -delta, 0)

                # 使用簡單的移動平均（避免複雜的cupyx依賴）
                # 使用累積和避免循環
                kernel_size = period
                kernel = self.cp.ones(kernel_size) / kernel_size

                # 計算滾動平均（使用full模式以保持長度）
                avg_gain = self.cp.convolve(gain, kernel, mode='same')
                avg_loss = self.cp.convolve(loss, kernel, mode='same')

                # 避免除零
                rs = avg_gain / self.cp.maximum(avg_loss, 1e-10)
                rsi = 100 - (100 / (1 + rs))

                # 處理前幾個值
                rsi[:period] = self.cp.nan

                return self._to_cpu(rsi)

        except Exception as e:
            logger.warning(f"GPU RSI calculation failed, falling back to CPU: {e}")
            return self._rsi_cpu(prices, period)

    def _rsi_cpu(self, prices: np.ndarray, period: int) -> np.ndarray:
        """CPU版本的RSI計算"""
        delta = np.diff(prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        # 使用pandas的優化rolling計算
        avg_gain = pd.Series(gain).rolling(window=period, min_periods=1).mean()
        avg_loss = pd.Series(loss).rolling(window=period, min_periods=1).mean()

        rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
        rsi = 100 - (100 / (1 + rs))

        return rsi.values

    def macd(self, prices: Union[np.ndarray, pd.Series],
             fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, np.ndarray]:
        """
        計算MACD指標（簡化GPU加速）

        Args:
            prices: 價格數據
            fast: 快線週期
            slow: 慢線週期
            signal: 信號線週期

        Returns:
            包含MACD, SIGNAL, HIST的字典
        """
        if isinstance(prices, pd.Series):
            prices = prices.values

        # 只有數據足夠大才使用GPU
        if self.use_gpu and len(prices) >= slow * 3:
            return self._macd_gpu_simple(prices, fast, slow, signal)
        else:
            return self._macd_cpu(prices, fast, slow, signal)

    def _macd_gpu_simple(self, prices: np.ndarray, fast: int, slow: int, signal: int) -> Dict[str, np.ndarray]:
        """GPU簡化版本的MACD計算"""
        try:
            with self.stream:
                prices_gpu = self._to_gpu(prices)

                # 使用向量化EMA計算（避免循環）
                def ema_vectorized(data, period):
                    alpha = 2.0 / (period + 1)
                    beta = 1 - alpha

                    # 使用cumsum實現高效EMA
                    ema = self.cp.zeros_like(data)
                    ema[0] = data[0]

                    # 向量化計算
                    exp_alpha = self.cp.exp(self.cp.arange(len(data)) * self.cp.log(beta))
                    weighted_sum = self.cp.cumsum(data * exp_alpha)
                    cum_weights = self.cp.cumsum(exp_alpha)

                    # 避免除零並保持第一個值
                    ema[1:] = (weighted_sum[1:] - data[0] * cum_weights[:1]) / cum_weights[1:] + data[0] * beta
                    return ema

                # 計算EMA
                ema_fast = ema_vectorized(prices_gpu, fast)
                ema_slow = ema_vectorized(prices_gpu, slow)

                # MACD線和信號線
                macd_line = ema_fast - ema_slow
                signal_line = ema_vectorized(macd_line, signal)
                histogram = macd_line - signal_line

                return {
                    'MACD': self._to_cpu(macd_line),
                    'SIGNAL': self._to_cpu(signal_line),
                    'HIST': self._to_cpu(histogram)
                }

        except Exception as e:
            logger.warning(f"GPU MACD calculation failed, falling back to CPU: {e}")
            return self._macd_cpu(prices, fast, slow, signal)

    def _macd_cpu(self, prices: np.ndarray, fast: int, slow: int, signal: int) -> Dict[str, np.ndarray]:
        """CPU版本的MACD計算"""
        prices_series = pd.Series(prices)

        # 使用pandas的優化ewm計算
        ema_fast = prices_series.ewm(span=fast, adjust=False).mean()
        ema_slow = prices_series.ewm(span=slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            'MACD': macd_line.values,
            'SIGNAL': signal_line.values,
            'HIST': histogram.values
        }

    def bollinger_bands(self, prices: Union[np.ndarray, pd.Series],
                        period: int = 20, std_dev: float = 2.0) -> Dict[str, np.ndarray]:
        """
        計算布林帶指標（簡化GPU加速）

        Args:
            prices: 價格數據
            period: 週期
            std_dev: 標準差倍數

        Returns:
            包含上軌、中軌、下軌的字典
        """
        if isinstance(prices, pd.Series):
            prices = prices.values

        # 只有數據足夠大才使用GPU
        if self.use_gpu and len(prices) >= period * 3:
            return self._bollinger_bands_gpu_simple(prices, period, std_dev)
        else:
            return self._bollinger_bands_cpu(prices, period, std_dev)

    def _bollinger_bands_gpu_simple(self, prices: np.ndarray, period: int, std_dev: float) -> Dict[str, np.ndarray]:
        """GPU簡化版本的布林帶計算"""
        try:
            with self.stream:
                prices_gpu = self._to_gpu(prices)

                # 中軌 - 移動平均
                kernel = self.cp.ones(period) / period
                middle_band = self.cp.convolve(prices_gpu, kernel, mode='same')

                # 滾動標準差（使用簡單方法）
                # 分割數據為窗口
                num_windows = len(prices_gpu) - period + 1
                if num_windows <= 0:
                    # 數據太小，返回全NaN
                    std_values = self.cp.full_like(prices_gpu, self.cp.nan)
                else:
                    # 創建2D數組進行向量化標準差計算
                    windows = self.cp.empty((num_windows, period))
                    for i in range(num_windows):
                        windows[i] = prices_gpu[i:i+period]

                    std_values_full = self.cp.concatenate([
                        self.cp.full(period//2, self.cp.nan),
                        self.cp.std(windows, axis=1),
                        self.cp.full(period//2, self.cp.nan)
                    ])

                # 計算上下軌
                upper_band = middle_band + (std_values_full * std_dev)
                lower_band = middle_band - (std_values_full * std_dev)

                return {
                    'UPPER': self._to_cpu(upper_band),
                    'MIDDLE': self._to_cpu(middle_band),
                    'LOWER': self._to_cpu(lower_band)
                }

        except Exception as e:
            logger.warning(f"GPU Bollinger Bands calculation failed, falling back to CPU: {e}")
            return self._bollinger_bands_cpu(prices, period, std_dev)

    def _bollinger_bands_cpu(self, prices: np.ndarray, period: int, std_dev: float) -> Dict[str, np.ndarray]:
        """CPU版本的布林帶計算"""
        prices_series = pd.Series(prices)

        middle_band = prices_series.rolling(window=period).mean()
        rolling_std = prices_series.rolling(window=period).std()

        upper_band = middle_band + (rolling_std * std_dev)
        lower_band = middle_band - (rolling_std * std_dev)

        return {
            'UPPER': upper_band.values,
            'MIDDLE': middle_band.values,
            'LOWER': lower_band.values
        }

    def calculate_batch_indicators(self, prices: Union[np.ndarray, pd.Series],
                                   indicators_config: Dict[str, Dict]) -> Dict[str, np.ndarray]:
        """
        批量計算多個技術指標（智能選擇後端）

        Args:
            prices: 價格數據
            indicators_config: 指標配置字典

        Returns:
            所有指標結果的字典
        """
        results = {}

        # 根據數據大小和特性決定是否使用GPU
        data_size = len(prices) if hasattr(prices, '__len__') else len(prices.values)
        data_std = np.std(prices) if hasattr(prices, 'std') else np.std(prices.values)

        # 數據大小和質量門檻
        gpu_threshold = 500
        std_threshold = 1e-6
        use_gpu_for_batch = (self.use_gpu and
                           data_size >= gpu_threshold and
                           data_std > std_threshold)

        if isinstance(prices, pd.Series):
            prices_values = prices.values
        else:
            prices_values = prices

        for indicator_name, config in indicators_config.items():
            try:
                if indicator_name == 'rsi':
                    period = config.get('period', 14)
                    if use_gpu_for_batch:
                        results['RSI'] = self.rsi(prices_values, period)
                    else:
                        results['RSI'] = self._rsi_cpu(prices_values, period)

                elif indicator_name == 'macd':
                    fast = config.get('fast', 12)
                    slow = config.get('slow', 26)
                    signal = config.get('signal', 9)
                    if use_gpu_for_batch:
                        macd_results = self.macd(prices_values, fast, slow, signal)
                    else:
                        macd_results = self._macd_cpu(prices_values, fast, slow, signal)
                    results.update(macd_results)

                elif indicator_name == 'bollinger':
                    period = config.get('period', 20)
                    std_dev = config.get('std_dev', 2.0)
                    if use_gpu_for_batch:
                        bb_results = self.bollinger_bands(prices_values, period, std_dev)
                    else:
                        bb_results = self.bollinger_bands_cpu(prices_values, period, std_dev)
                    results.update({
                        'BB_UPPER': bb_results['UPPER'],
                        'BB_MIDDLE': bb_results['MIDDLE'],
                        'BB_LOWER': bb_results['LOWER']
                    })

            except Exception as e:
                logger.warning(f"Failed to calculate {indicator_name}: {e}")

        return results

    def get_backend_info(self) -> Dict[str, any]:
        """獲取後端信息"""
        return {
            'backend': self.backend,
            'use_gpu': self.use_gpu,
            'gpu_available': self.gpu_env.is_gpu_available(),
            'gpu_info': self.gpu_env.get_system_info() if self.use_gpu else None,
            'cuda_stream': self.use_gpu and hasattr(self, 'stream')
        }

    def benchmark_performance(self, data_size: int = 1000) -> Dict[str, float]:
        """性能基準測試"""
        import time

        # 生成測試數據
        np.random.seed(42)
        test_data = np.random.randn(data_size).cumsum() + 100
        test_data = np.abs(test_data)

        results = {}

        # 測試RSI性能
        start_time = time.time()
        self.rsi(test_data, 14)
        results['rsi_time'] = time.time() - start_time

        # 測試MACD性能
        start_time = time.time()
        self.macd(test_data, 12, 26, 9)
        results['macd_time'] = time.time() - start_time

        # 測試布林帶性能
        start_time = time.time()
        self.bollinger_bands(test_data, 20, 2.0)
        results['bollinger_time'] = time.time() - start_time

        results['total_time'] = results['rsi_time'] + results['macd_time'] + results['bollinger_time']
        results['data_size'] = data_size
        results['backend'] = self.backend

        return results