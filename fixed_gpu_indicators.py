#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復版GPU加速技術指標計算模塊
基於CuPy 13.6最佳實踐優化
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

class FixedGPUTechnicalIndicators:
    """修復版GPU加速技術指標計算類 - 基於CuPy 13.6最佳實踐"""

    def __init__(self, use_gpu: bool = True):
        """
        初始化修復版GPU技術指標計算器

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

                # CuPy 13.6優化設置
                self._setup_cupy_optimization()

                logger.info("Fixed GPU Technical Indicators initialized with CuPy 13.6")
            except ImportError:
                logger.warning("CuPy not available, falling back to CPU")
                self.use_gpu = False
                self.backend = 'cpu'
                self.cp = None
        else:
            self.cp = None

        logger.info(f"Fixed GPU Technical Indicators initialized with backend: {self.backend}")

    def _setup_cupy_optimization(self):
        """設置CuPy 13.6的優化配置"""
        import cupy as cp

        # 設置CUDA流以優化性能
        self.stream = cp.cuda.Stream()

        # 預分配內存池以減少分配開銷
        try:
            cp.get_default_memory_pool().set_limit(size=2**30)  # 1GB
            cp.get_default_pinned_memory_pool().set_limit(size=2**28)  # 256MB
        except:
            pass  # 如果設置失敗，繼續使用默認設置

    def _to_gpu(self, data: np.ndarray) -> Union[np.ndarray, 'cp.ndarray']:
        """將數據轉移到GPU（優化版）"""
        if self.use_gpu and self.cp is not None:
            with self.stream:
                return self.cp.asarray(data)
        return data

    def _to_cpu(self, data: Union[np.ndarray, 'cp.ndarray']) -> np.ndarray:
        """將數據從GPU轉移到CPU（優化版）"""
        if self.use_gpu and self.cp is not None and hasattr(data, 'get'):
            with self.stream:
                return data.get()
        return data

    def rsi(self, prices: Union[np.ndarray, pd.Series], period: int = 14) -> np.ndarray:
        """
        計算RSI指標（優化版GPU加速）

        Args:
            prices: 價格數據
            period: RSI週期

        Returns:
            RSI值數組
        """
        if isinstance(prices, pd.Series):
            prices = prices.values

        if self.use_gpu and len(prices) >= period * 2:  # 只有數據夠大才使用GPU
            return self._rsi_gpu_optimized(prices, period)
        else:
            return self._rsi_cpu(prices, period)

    def _rsi_gpu_optimized(self, prices: np.ndarray, period: int) -> np.ndarray:
        """GPU優化版本的RSI計算"""
        try:
            # 轉移到GPU
            with self.stream:
                prices_gpu = self._to_gpu(prices)

                # 使用CuPy 13.6優化的向量化操作
                delta = self.cp.diff(prices_gpu)

                # 向量化漲跌計算
                gain = self.cp.maximum(delta, 0)
                loss = self.cp.maximum(-delta, 0)

                # 使用cupyx優化的移動平均
                try:
                    import cupyx
                    # 如果cupyx可用，使用cupyx的優化函數
                    avg_gain = cupyx.ndimage.uniform_filter1d(gain, size=period, mode='mirror')
                    avg_loss = cupyx.ndimage.uniform_filter1d(loss, size=period, mode='mirror')
                except ImportError:
                    # 回退到自定義移動平均
                    kernel = self.cp.ones(period) / period
                    avg_gain = self.cp.convolve(gain, kernel, mode='same')
                    avg_loss = self.cp.convolve(loss, kernel, mode='same')

                # 避免除零錯誤並計算RS
                rs = avg_gain / self.cp.maximum(avg_loss, 1e-10)
                rsi = 100 - (100 / (1 + rs))

                # 處理前period-1個值為NaN
                rsi[:period-1] = self.cp.nan

                return self._to_cpu(rsi)

        except Exception as e:
            logger.warning(f"Optimized GPU RSI calculation failed, falling back to CPU: {e}")
            return self._rsi_cpu(prices, period)

    def _rsi_cpu(self, prices: np.ndarray, period: int) -> np.ndarray:
        """CPU版本的RSI計算（優化）"""
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
        計算MACD指標（優化版GPU加速）

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

        if self.use_gpu and len(prices) >= slow * 2:  # 數據夠大才使用GPU
            return self._macd_gpu_optimized(prices, fast, slow, signal)
        else:
            return self._macd_cpu(prices, fast, slow, signal)

    def _macd_gpu_optimized(self, prices: np.ndarray, fast: int, slow: int, signal: int) -> Dict[str, np.ndarray]:
        """GPU優化版本的MACD計算"""
        try:
            with self.stream:
                prices_gpu = self._to_gpu(prices)

                # 使用向量化EMA計算（避免循環）
                def ema_vectorized(data, period):
                    """向量化EMA計算"""
                    alpha = 2.0 / (period + 1)
                    beta = 1 - alpha

                    # 使用CuPy的累積函數
                    ema = self.cp.zeros_like(data, dtype=data.dtype)
                    ema[0] = data[0]

                    # 使用 cumsum 和向量化操作避免循環
                    weights = self.cp.power(beta, self.cp.arange(len(data)))
                    weighted_sum = self.cp.cumsum(data * weights)
                    cum_weights = self.cp.cumsum(weights)

                    # 避免除零
                    ema[1:] = (weighted_sum[1:] - data[0]) / cum_weights[1:] + data[0] * beta
                    return ema

                # 計算EMA
                ema_fast = ema_vectorized(prices_gpu, fast)
                ema_slow = ema_vectorized(prices_gpu, slow)

                # MACD線
                macd_line = ema_fast - ema_slow

                # 信號線
                signal_line = ema_vectorized(macd_line, signal)

                # 柱狀圖
                histogram = macd_line - signal_line

                return {
                    'MACD': self._to_cpu(macd_line),
                    'SIGNAL': self._to_cpu(signal_line),
                    'HIST': self._to_cpu(histogram)
                }

        except Exception as e:
            logger.warning(f"Optimized GPU MACD calculation failed, falling back to CPU: {e}")
            return self._macd_cpu(prices, fast, slow, signal)

    def _macd_cpu(self, prices: np.ndarray, fast: int, slow: int, signal: int) -> Dict[str, np.ndarray]:
        """CPU版本的MACD計算（優化）"""
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
        計算布林帶指標（優化版GPU加速）

        Args:
            prices: 價格數據
            period: 週期
            std_dev: 標準差倍數

        Returns:
            包含上軌、中軌、下軌的字典
        """
        if isinstance(prices, pd.Series):
            prices = prices.values

        if self.use_gpu and len(prices) >= period * 3:  # 數據夠大才使用GPU
            return self._bollinger_bands_gpu_optimized(prices, period, std_dev)
        else:
            return self._bollinger_bands_cpu(prices, period, std_dev)

    def _bollinger_bands_gpu_optimized(self, prices: np.ndarray, period: int, std_dev: float) -> Dict[str, np.ndarray]:
        """GPU優化版本的布林帶計算"""
        try:
            with self.stream:
                prices_gpu = self._to_gpu(prices)

                # 使用CuPy的優化移動窗口計算
                # 中軌 - 移動平均
                kernel = self.cp.ones(period) / period
                middle_band = self.cp.convolve(prices_gpu, kernel, mode='same')

                # 使用優化的滾動標準差計算
                # 計算每個窗口的統計量
                from cupyx.lib.stride_tricks import sliding_window_view

                # 創建滾動窗口視圖
                windows = sliding_window_view(prices_gpu, window_shape=period)

                # 向量化計算每個窗口的標準差
                rolling_mean = self.cp.mean(windows, axis=1)
                rolling_var = self.cp.var(windows, axis=1)
                rolling_std = self.cp.sqrt(rolling_var)

                # 處理邊界
                # 前面period//2個點的標準差設置為第一個有效窗口的值
                valid_start = period // 2
                valid_end = len(rolling_std) - valid_start

                # 填充邊界
                padding_start = self.cp.full(valid_start, rolling_std[0])
                padding_end = self.cp.full(valid_start, rolling_std[-1])

                full_rolling_std = self.cp.concatenate([padding_start, rolling_std, padding_end])
                full_rolling_std = full_rolling_std[:len(prices_gpu)]

                # 計算上下軌
                upper_band = middle_band + (full_rolling_std * std_dev)
                lower_band = middle_band - (full_rolling_std * std_dev)

                return {
                    'UPPER': self._to_cpu(upper_band),
                    'MIDDLE': self._to_cpu(middle_band),
                    'LOWER': self._to_cpu(lower_band)
                }

        except Exception as e:
            logger.warning(f"Optimized GPU Bollinger Bands calculation failed, falling back to CPU: {e}")
            return self._bollinger_bands_cpu(prices, period, std_dev)

    def _bollinger_bands_cpu(self, prices: np.ndarray, period: int, std_dev: float) -> Dict[str, np.ndarray]:
        """CPU版本的布林帶計算（優化）"""
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
        批量計算多個技術指標（GPU優化版）

        Args:
            prices: 價格數據
            indicators_config: 指標配置字典

        Returns:
            所有指標結果的字典
        """
        results = {}

        # 根據數據大小決定是否使用GPU
        data_size = len(prices) if hasattr(prices, '__len__') else len(prices.values)
        use_gpu_for_batch = self.use_gpu and data_size >= 500  # 只有數據足夠大才使用GPU

        for indicator_name, config in indicators_config.items():
            try:
                if indicator_name == 'rsi':
                    period = config.get('period', 14)
                    if use_gpu_for_batch:
                        results['RSI'] = self.rsi(prices, period)
                    else:
                        results['RSI'] = self._rsi_cpu(prices.values if isinstance(prices, pd.Series) else prices, period)

                elif indicator_name == 'macd':
                    fast = config.get('fast', 12)
                    slow = config.get('slow', 26)
                    signal = config.get('signal', 9)
                    if use_gpu_for_batch:
                        macd_results = self.macd(prices, fast, slow, signal)
                    else:
                        macd_results = self._macd_cpu(prices.values if isinstance(prices, pd.Series) else prices, fast, slow, signal)
                    results.update(macd_results)

                elif indicator_name == 'bollinger':
                    period = config.get('period', 20)
                    std_dev = config.get('std_dev', 2.0)
                    if use_gpu_for_batch:
                        bb_results = self.bollinger_bands(prices, period, std_dev)
                    else:
                        bb_results = self._bollinger_bands_cpu(prices.values if isinstance(prices, pd.Series) else prices, period, std_dev)
                    results.update({
                        'BB_UPPER': bb_results['UPPER'],
                        'BB_MIDDLE': bb_results['MIDDLE'],
                        'BB_LOWER': bb_results['LOWER']
                    })

            except Exception as e:
                logger.warning(f"Failed to calculate {indicator_name}: {e}")

        return results

    def get_backend_info(self) -> Dict[str, any]:
        """獲取後端信息（優化版）"""
        info = {
            'backend': self.backend,
            'use_gpu': self.use_gpu,
            'gpu_available': self.gpu_env.is_gpu_available(),
            'gpu_info': self.gpu_env.get_system_info() if self.use_gpu else None,
            'optimization_enabled': True
        }

        if self.use_gpu and hasattr(self, 'stream'):
            info['cuda_stream'] = True

        return info

    def benchmark_performance(self, data_size: int = 10000) -> Dict[str, float]:
        """性能基準測試"""
        import time
        import numpy as np

        # 生成測試數據
        np.random.seed(42)
        test_data = np.random.randn(data_size).cumsum() + 100
        test_data = np.abs(test_data)  # 確保為正數

        results = {}

        # 測試RSI性能
        start_time = time.time()
        self.rsi(test_data, 14)
        rsi_time = time.time() - start_time
        results['rsi_time'] = rsi_time

        # 測試MACD性能
        start_time = time.time()
        self.macd(test_data, 12, 26, 9)
        macd_time = time.time() - start_time
        results['macd_time'] = macd_time

        # 測試布林帶性能
        start_time = time.time()
        self.bollinger_bands(test_data, 20, 2.0)
        bb_time = time.time() - start_time
        results['bollinger_time'] = bb_time

        results['total_time'] = rsi_time + macd_time + bb_time
        results['data_size'] = data_size
        results['backend'] = self.backend

        return results