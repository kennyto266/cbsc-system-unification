#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU加速技術指標計算引擎 - 深度集成版本
GPU-Accelerated Technical Indicators Engine - Deep Integration Version

提供高性能的GPU加速技術指標計算，支持大規模並行處理
Provides high-performance GPU-accelerated technical indicator calculations with large-scale parallel processing
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional, Union
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
import warnings

# GPU框架導入和自動回退
GPU_BACKEND = None
GPU_AVAILABLE = False

try:
    import cupy as cp
    GPU_BACKEND = "cupy"
    GPU_AVAILABLE = True
    print("[GPU] CuPy backend initialized for accelerated computations")
except ImportError:
    try:
        import torch
        if torch.cuda.is_available():
            GPU_BACKEND = "pytorch"
            GPU_AVAILABLE = True
            print(f"[GPU] PyTorch CUDA backend initialized: {torch.cuda.get_device_name()}")
        else:
            print("[GPU] PyTorch available but CUDA not detected")
    except ImportError:
        print("[GPU] Neither CuPy nor PyTorch CUDA available, using CPU fallback")

# 配置日誌
logger = logging.getLogger(__name__)

@dataclass
class GPUIndicatorConfig:
    """GPU指標計算配置"""
    batch_size: int = 8192  # 批處理大小
    memory_limit: float = 0.8  # GPU內存使用限制
    precision: str = "float32"  # 計算精度
    use_mixed_precision: bool = False  # 混合精度計算
    enable_profiling: bool = False  # 性能分析

@dataclass
class GPUComputeStats:
    """GPU計算統計信息"""
    total_operations: int = 0
    gpu_operations: int = 0
    cpu_fallback_operations: int = 0
    total_computation_time: float = 0.0
    memory_allocated: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

class GPUAcceleratedIndicators:
    """
    GPU加速技術指標計算引擎

    核心特性：
    - 自動GPU檢測和回退機制
    - 大規模並行計算支持
    - 內存優化和批處理
    - 多GPU框架支持（CuPy, PyTorch）
    - 性能監控和統計
    """

    def __init__(self, config: Optional[GPUIndicatorConfig] = None):
        """
        初始化GPU指標引擎

        Args:
            config: GPU計算配置
        """
        self.config = config or GPUIndicatorConfig()
        self.backend = GPU_BACKEND
        self.available = GPU_AVAILABLE

        # 性能統計
        self.stats = GPUComputeStats()
        self.performance_cache = {}

        # GPU環境檢查
        if self.available:
            self._initialize_gpu_environment()

        logger.info(f"GPU Indicators Engine initialized: backend={self.backend}, available={self.available}")

    def _initialize_gpu_environment(self):
        """初始化GPU環境"""
        try:
            if self.backend == "cupy":
                # CuPy環境設置
                self.gpu_device = cp.cuda.Device()
                self.gpu_memory = self.gpu_device.mem_info
                self.gpu_context = cp.cuda.Stream()

                # 設置內存池
                mempool = cp.get_default_memory_pool()
                mempool.set_limit(size=int(self.config.memory_limit * self.gpu_memory[1]))

            elif self.backend == "pytorch":
                # PyTorch環境設置
                self.gpu_device = torch.cuda.current_device()
                self.gpu_memory = torch.cuda.get_device_properties(self.gpu_device).total_memory

                # 設置精度
                if self.config.precision == "float16":
                    torch.set_default_tensor_type(torch.cuda.Float16Tensor)

            logger.info(f"GPU environment initialized successfully on device {self.gpu_device}")

        except Exception as e:
            logger.warning(f"GPU initialization failed: {e}, falling back to CPU")
            self.available = False
            self.backend = None

    def _to_gpu(self, array: np.ndarray) -> Any:
        """將數據轉移到GPU"""
        if not self.available:
            return array

        try:
            if self.backend == "cupy":
                return cp.asarray(array, dtype=self.config.precision)
            elif self.backend == "pytorch":
                return torch.from_numpy(array).cuda()
            return array
        except Exception as e:
            logger.warning(f"GPU transfer failed: {e}")
            self.stats.cpu_fallback_operations += 1
            return array

    def _to_cpu(self, gpu_array: Any) -> np.ndarray:
        """將數據從GPU轉移到CPU"""
        if not self.available or gpu_array is None:
            return gpu_array

        try:
            if self.backend == "cupy":
                return cp.asnumpy(gpu_array)
            elif self.backend == "pytorch":
                return gpu_array.cpu().numpy()
            return gpu_array
        except Exception as e:
            logger.warning(f"CPU transfer failed: {e}")
            return gpu_array

    def calculate_rsi_batch_gpu(self, prices: Union[np.ndarray, pd.Series],
                               periods: List[int]) -> Dict[int, np.ndarray]:
        """
        GPU批量RSI計算

        Args:
            prices: 價格數據
            periods: RSI週期列表

        Returns:
            週期到RSI值的映射
        """
        start_time = time.time()

        if isinstance(prices, pd.Series):
            prices = prices.values.astype(np.float32)

        self.stats.total_operations += len(periods)
        results = {}

        if self.available and len(prices) > 1000:  # GPU只在數據量足夠時使用
            try:
                self.stats.gpu_operations += len(periods)
                results = self._calculate_rsi_batch_gpu_core(prices, periods)
            except Exception as e:
                logger.warning(f"GPU RSI calculation failed: {e}, using CPU fallback")
                self.stats.cpu_fallback_operations += len(periods)
                results = self._calculate_rsi_batch_cpu(prices, periods)
        else:
            self.stats.cpu_fallback_operations += len(periods)
            results = self._calculate_rsi_batch_cpu(prices, periods)

        computation_time = time.time() - start_time
        self.stats.total_computation_time += computation_time

        logger.debug(f"RSI batch calculation completed: {len(periods)} periods in {computation_time:.3f}s")
        return results

    def _calculate_rsi_batch_gpu_core(self, prices: np.ndarray, periods: List[int]) -> Dict[int, np.ndarray]:
        """GPU核心RSI批量計算"""
        if self.backend == "cupy":
            return self._rsi_batch_cupy(prices, periods)
        elif self.backend == "pytorch":
            return self._rsi_batch_pytorch(prices, periods)
        else:
            return self._calculate_rsi_batch_cpu(prices, periods)

    def _rsi_batch_cupy(self, prices: np.ndarray, periods: List[int]) -> Dict[int, np.ndarray]:
        """CuPy版本的RSI批量計算"""
        prices_gpu = self._to_gpu(prices)
        results = {}

        # 計算delta和gain/loss（一次性計算）
        delta_gpu = cp.diff(prices_gpu)
        gain_gpu = cp.where(delta_gpu > 0, delta_gpu, 0)
        loss_gpu = cp.where(delta_gpu < 0, -delta_gpu, 0)

        for period in periods:
            # 使用卷積進行高效的移動平均計算
            kernel = cp.ones(period, dtype=self.config.precision) / period
            avg_gain_gpu = cp.convolve(gain_gpu, kernel, mode='full')[:len(gain_gpu)+1-period]
            avg_loss_gpu = cp.convolve(loss_gpu, kernel, mode='full')[:len(loss_gpu)+1-period]

            # 計算RS和RSI
            rs_gpu = avg_gain_gpu / cp.where(avg_loss_gpu == 0, 1e-10, avg_loss_gpu)
            rsi_gpu = 100 - (100 / (1 + rs_gpu))

            # 填充NaN值
            rsi_with_nan_gpu = cp.concatenate([cp.full(period-1, cp.nan, dtype=self.config.precision), rsi_gpu])

            results[period] = self._to_cpu(rsi_with_nan_gpu)

        return results

    def _rsi_batch_pytorch(self, prices: np.ndarray, periods: List[int]) -> Dict[int, np.ndarray]:
        """PyTorch版本的RSI批量計算"""
        prices_tensor = self._to_gpu(prices)
        results = {}

        # 計算delta和gain/loss
        delta_tensor = torch.diff(prices_tensor)
        gain_tensor = torch.where(delta_tensor > 0, delta_tensor, torch.tensor(0.0).cuda())
        loss_tensor = torch.where(delta_tensor < 0, -delta_tensor, torch.tensor(0.0).cuda())

        for period in periods:
            # PyTorch移動平均
            avg_gain_tensor = torch.nn.functional.conv1d(
                gain_tensor.unsqueeze(0).unsqueeze(0),
                torch.ones(1, 1, period, dtype=self.config.precision).cuda() / period,
                padding=0
            ).squeeze()

            avg_loss_tensor = torch.nn.functional.conv1d(
                loss_tensor.unsqueeze(0).unsqueeze(0),
                torch.ones(1, 1, period, dtype=self.config.precision).cuda() / period,
                padding=0
            ).squeeze()

            # 計算RS和RSI
            rs_tensor = avg_gain_tensor / torch.where(avg_loss_tensor == 0, torch.tensor(1e-10).cuda(), avg_loss_tensor)
            rsi_tensor = 100 - (100 / (1 + rs_tensor))

            # 填充NaN值
            nan_padding = torch.full(period-1, float('nan'), dtype=self.config.precision).cuda()
            rsi_with_nan_tensor = torch.cat([nan_padding, rsi_tensor])

            results[period] = self._to_cpu(rsi_with_nan_tensor)

        return results

    def _calculate_rsi_batch_cpu(self, prices: np.ndarray, periods: List[int]) -> Dict[int, np.ndarray]:
        """CPU版本的RSI批量計算（回退）"""
        results = {}
        prices_series = pd.Series(prices)

        for period in periods:
            delta = prices_series.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()

            rs = avg_gain / avg_loss.replace(0, 1e-10)
            rsi = 100 - (100 / (1 + rs))

            results[period] = rsi.values

        return results

    def calculate_macd_batch_gpu(self, prices: Union[np.ndarray, pd.Series],
                               fast_periods: List[int], slow_periods: List[int],
                               signal_periods: List[int]) -> Dict[str, Dict[str, np.ndarray]]:
        """
        GPU批量MACD計算

        Args:
            prices: 價格數據
            fast_periods: 快線週期列表
            slow_periods: 慢線週期列表
            signal_periods: 信號線週期列表

        Returns:
            MACD結果字典
        """
        start_time = time.time()

        if isinstance(prices, pd.Series):
            prices = prices.values.astype(np.float32)

        total_combinations = len(fast_periods) * len(slow_periods) * len(signal_periods)
        self.stats.total_operations += total_combinations

        results = {}

        if self.available and len(prices) > 1000:
            try:
                self.stats.gpu_operations += total_combinations
                results = self._calculate_macd_batch_gpu_core(prices, fast_periods, slow_periods, signal_periods)
            except Exception as e:
                logger.warning(f"GPU MACD calculation failed: {e}, using CPU fallback")
                self.stats.cpu_fallback_operations += total_combinations
                results = self._calculate_macd_batch_cpu(prices, fast_periods, slow_periods, signal_periods)
        else:
            self.stats.cpu_fallback_operations += total_combinations
            results = self._calculate_macd_batch_cpu(prices, fast_periods, slow_periods, signal_periods)

        computation_time = time.time() - start_time
        self.stats.total_computation_time += computation_time

        logger.debug(f"MACD batch calculation completed: {total_combinations} combinations in {computation_time:.3f}s")
        return results

    def _calculate_macd_batch_gpu_core(self, prices: np.ndarray, fast_periods: List[int],
                                     slow_periods: List[int], signal_periods: List[int]) -> Dict[str, Dict[str, np.ndarray]]:
        """GPU核心MACD批量計算"""
        if self.backend == "cupy":
            return self._macd_batch_cupy(prices, fast_periods, slow_periods, signal_periods)
        elif self.backend == "pytorch":
            return self._macd_batch_pytorch(prices, fast_periods, slow_periods, signal_periods)
        else:
            return self._calculate_macd_batch_cpu(prices, fast_periods, slow_periods, signal_periods)

    def _macd_batch_cupy(self, prices: np.ndarray, fast_periods: List[int],
                        slow_periods: List[int], signal_periods: List[int]) -> Dict[str, Dict[str, np.ndarray]]:
        """CuPy版本的MACD批量計算"""
        prices_gpu = self._to_gpu(prices)
        results = {}

        # 預計算所有EMA值
        ema_cache = {}
        all_periods = set(fast_periods + slow_periods + signal_periods)

        for period in all_periods:
            alpha = 2 / (period + 1)
            ema_gpu = cp.zeros_like(prices_gpu)
            ema_gpu[0] = prices_gpu[0]

            for i in range(1, len(prices_gpu)):
                ema_gpu[i] = alpha * prices_gpu[i] + (1 - alpha) * ema_gpu[i-1]

            ema_cache[period] = ema_gpu

        # 組合計算MACD
        for fast in fast_periods:
            for slow in slow_periods:
                if fast >= slow:
                    continue

                macd_line_gpu = ema_cache[fast] - ema_cache[slow]

                for signal in signal_periods:
                    alpha_signal = 2 / (signal + 1)
                    signal_line_gpu = cp.zeros_like(macd_line_gpu)
                    signal_line_gpu[0] = macd_line_gpu[0]

                    for i in range(1, len(macd_line_gpu)):
                        signal_line_gpu[i] = alpha_signal * macd_line_gpu[i] + (1 - alpha_signal) * signal_line_gpu[i-1]

                    histogram_gpu = macd_line_gpu - signal_line_gpu

                    key = f"MACD_{fast}_{slow}_{signal}"
                    results[key] = {
                        'MACD': self._to_cpu(macd_line_gpu),
                        'SIGNAL': self._to_cpu(signal_line_gpu),
                        'HISTOGRAM': self._to_cpu(histogram_gpu)
                    }

        return results

    def _macd_batch_pytorch(self, prices: np.ndarray, fast_periods: List[int],
                           slow_periods: List[int], signal_periods: List[int]) -> Dict[str, Dict[str, np.ndarray]]:
        """PyTorch版本的MACD批量計算"""
        prices_tensor = self._to_gpu(prices)
        results = {}

        # 預計算所有EMA值
        ema_cache = {}
        all_periods = set(fast_periods + slow_periods + signal_periods)

        for period in all_periods:
            alpha = 2 / (period + 1)
            ema_tensor = torch.zeros_like(prices_tensor)
            ema_tensor[0] = prices_tensor[0]

            for i in range(1, len(prices_tensor)):
                ema_tensor[i] = alpha * prices_tensor[i] + (1 - alpha) * ema_tensor[i-1]

            ema_cache[period] = ema_tensor

        # 組合計算MACD
        for fast in fast_periods:
            for slow in slow_periods:
                if fast >= slow:
                    continue

                macd_line_tensor = ema_cache[fast] - ema_cache[slow]

                for signal in signal_periods:
                    alpha_signal = 2 / (signal + 1)
                    signal_line_tensor = torch.zeros_like(macd_line_tensor)
                    signal_line_tensor[0] = macd_line_tensor[0]

                    for i in range(1, len(macd_line_tensor)):
                        signal_line_tensor[i] = alpha_signal * macd_line_tensor[i] + (1 - alpha_signal) * signal_line_tensor[i-1]

                    histogram_tensor = macd_line_tensor - signal_line_tensor

                    key = f"MACD_{fast}_{slow}_{signal}"
                    results[key] = {
                        'MACD': self._to_cpu(macd_line_tensor),
                        'SIGNAL': self._to_cpu(signal_line_tensor),
                        'HISTOGRAM': self._to_cpu(histogram_tensor)
                    }

        return results

    def _calculate_macd_batch_cpu(self, prices: np.ndarray, fast_periods: List[int],
                                 slow_periods: List[int], signal_periods: List[int]) -> Dict[str, Dict[str, np.ndarray]]:
        """CPU版本的MACD批量計算（回退）"""
        results = {}
        prices_series = pd.Series(prices)

        for fast in fast_periods:
            for slow in slow_periods:
                if fast >= slow:
                    continue

                ema_fast = prices_series.ewm(span=fast).mean()
                ema_slow = prices_series.ewm(span=slow).mean()
                macd_line = ema_fast - ema_slow

                for signal in signal_periods:
                    signal_line = macd_line.ewm(span=signal).mean()
                    histogram = macd_line - signal_line

                    key = f"MACD_{fast}_{slow}_{signal}"
                    results[key] = {
                        'MACD': macd_line.values,
                        'SIGNAL': signal_line.values,
                        'HISTOGRAM': histogram.values
                    }

        return results

    def calculate_bollinger_bands_gpu(self, prices: Union[np.ndarray, pd.Series],
                                    periods: List[int], std_devs: List[float]) -> Dict[str, Dict[str, np.ndarray]]:
        """
        GPU批量布林帶計算

        Args:
            prices: 價格數據
            periods: 週期列表
            std_devs: 標準差倍數列表

        Returns:
            布林帶結果字典
        """
        start_time = time.time()

        if isinstance(prices, pd.Series):
            prices = prices.values.astype(np.float32)

        total_combinations = len(periods) * len(std_devs)
        self.stats.total_operations += total_combinations

        results = {}

        if self.available and len(prices) > 1000:
            try:
                self.stats.gpu_operations += total_combinations
                results = self._calculate_bollinger_batch_gpu_core(prices, periods, std_devs)
            except Exception as e:
                logger.warning(f"GPU Bollinger Bands calculation failed: {e}, using CPU fallback")
                self.stats.cpu_fallback_operations += total_combinations
                results = self._calculate_bollinger_batch_cpu(prices, periods, std_devs)
        else:
            self.stats.cpu_fallback_operations += total_combinations
            results = self._calculate_bollinger_batch_cpu(prices, periods, std_devs)

        computation_time = time.time() - start_time
        self.stats.total_computation_time += computation_time

        logger.debug(f"Bollinger Bands batch calculation completed: {total_combinations} combinations in {computation_time:.3f}s")
        return results

    def _calculate_bollinger_batch_gpu_core(self, prices: np.ndarray, periods: List[int],
                                          std_devs: List[float]) -> Dict[str, Dict[str, np.ndarray]]:
        """GPU核心布林帶批量計算"""
        if self.backend == "cupy":
            return self._bollinger_batch_cupy(prices, periods, std_devs)
        elif self.backend == "pytorch":
            return self._bollinger_batch_pytorch(prices, periods, std_devs)
        else:
            return self._calculate_bollinger_batch_cpu(prices, periods, std_devs)

    def _bollinger_batch_cupy(self, prices: np.ndarray, periods: List[int],
                             std_devs: List[float]) -> Dict[str, Dict[str, np.ndarray]]:
        """CuPy版本的布林帶批量計算"""
        prices_gpu = self._to_gpu(prices)
        results = {}

        # 預計算移動平均和標準差
        ma_cache = {}
        std_cache = {}

        for period in periods:
            # 使用卷積進行高效移動平均
            kernel = cp.ones(period, dtype=self.config.precision) / period
            ma_gpu = cp.convolve(prices_gpu, kernel, mode='full')[:len(prices_gpu)+1-period]
            ma_gpu = cp.concatenate([cp.full(period-1, cp.nan, dtype=self.config.precision), ma_gpu])
            ma_cache[period] = ma_gpu

            # 計算移動標準差
            squared_diff = cp.square(prices_gpu - ma_gpu)
            var_gpu = cp.convolve(squared_diff, kernel, mode='full')[:len(squared_diff)+1-period]
            var_gpu = cp.concatenate([cp.full(period-1, cp.nan, dtype=self.config.precision), var_gpu])
            std_gpu = cp.sqrt(var_gpu)
            std_cache[period] = std_gpu

        # 組合計算布林帶
        for period in periods:
            for std_dev in std_devs:
                upper_band_gpu = ma_cache[period] + std_cache[period] * std_dev
                lower_band_gpu = ma_cache[period] - std_cache[period] * std_dev

                key = f"BB_{period}_{std_dev}"
                results[key] = {
                    'MIDDLE': self._to_cpu(ma_cache[period]),
                    'UPPER': self._to_cpu(upper_band_gpu),
                    'LOWER': self._to_cpu(lower_band_gpu),
                    'WIDTH': self._to_cpu(upper_band_gpu - lower_band_gpu)
                }

        return results

    def _bollinger_batch_pytorch(self, prices: np.ndarray, periods: List[int],
                               std_devs: List[float]) -> Dict[str, Dict[str, np.ndarray]]:
        """PyTorch版本的布林帶批量計算"""
        prices_tensor = self._to_gpu(prices)
        results = {}

        # 預計算移動平均和標準差
        ma_cache = {}
        std_cache = {}

        for period in periods:
            # PyTorch卷積進行移動平均
            kernel = torch.ones(1, 1, period, dtype=self.config.precision).cuda() / period
            prices_reshaped = prices_tensor.unsqueeze(0).unsqueeze(0)
            ma_tensor = torch.nn.functional.conv1d(prices_reshaped, kernel, padding=0).squeeze()

            # 填充NaN
            nan_padding = torch.full(period-1, float('nan'), dtype=self.config.precision).cuda()
            ma_tensor = torch.cat([nan_padding, ma_tensor])
            ma_cache[period] = ma_tensor

            # 計算移動標準差
            squared_diff = torch.square(prices_tensor - ma_tensor)
            var_tensor = torch.nn.functional.conv1d(squared_diff.unsqueeze(0).unsqueeze(0), kernel, padding=0).squeeze()
            var_tensor = torch.cat([nan_padding, var_tensor])
            std_tensor = torch.sqrt(var_tensor)
            std_cache[period] = std_tensor

        # 組合計算布林帶
        for period in periods:
            for std_dev in std_devs:
                upper_band_tensor = ma_cache[period] + std_cache[period] * std_dev
                lower_band_tensor = ma_cache[period] - std_cache[period] * std_dev

                key = f"BB_{period}_{std_dev}"
                results[key] = {
                    'MIDDLE': self._to_cpu(ma_cache[period]),
                    'UPPER': self._to_cpu(upper_band_tensor),
                    'LOWER': self._to_cpu(lower_band_tensor),
                    'WIDTH': self._to_cpu(upper_band_tensor - lower_band_tensor)
                }

        return results

    def _calculate_bollinger_batch_cpu(self, prices: np.ndarray, periods: List[int],
                                     std_devs: List[float]) -> Dict[str, Dict[str, np.ndarray]]:
        """CPU版本的布林帶批量計算（回退）"""
        results = {}
        prices_series = pd.Series(prices)

        for period in periods:
            ma = prices_series.rolling(window=period).mean()
            std = prices_series.rolling(window=period).std()

            for std_dev in std_devs:
                upper_band = ma + std * std_dev
                lower_band = ma - std * std_dev

                key = f"BB_{period}_{std_dev}"
                results[key] = {
                    'MIDDLE': ma.values,
                    'UPPER': upper_band.values,
                    'LOWER': lower_band.values,
                    'WIDTH': (upper_band - lower_band).values
                }

        return results

    def get_performance_stats(self) -> Dict[str, Any]:
        """獲取性能統計信息"""
        gpu_utilization = 0.0
        if self.stats.total_operations > 0:
            gpu_utilization = self.stats.gpu_operations / self.stats.total_operations

        avg_computation_time = 0.0
        if self.stats.total_operations > 0:
            avg_computation_time = self.stats.total_computation_time / self.stats.total_operations

        cache_hit_rate = 0.0
        total_cache_ops = self.stats.cache_hits + self.stats.cache_misses
        if total_cache_ops > 0:
            cache_hit_rate = self.stats.cache_hits / total_cache_ops

        return {
            'backend': self.backend,
            'gpu_available': self.available,
            'gpu_utilization': gpu_utilization,
            'total_operations': self.stats.total_operations,
            'gpu_operations': self.stats.gpu_operations,
            'cpu_fallback_operations': self.stats.cpu_fallback_operations,
            'total_computation_time': self.stats.total_computation_time,
            'average_computation_time': avg_computation_time,
            'memory_allocated': self.stats.memory_allocated,
            'cache_hit_rate': cache_hit_rate,
            'cache_hits': self.stats.cache_hits,
            'cache_misses': self.stats.cache_misses
        }

    def benchmark_performance(self, data_size: int = 10000) -> Dict[str, float]:
        """性能基準測試"""
        logger.info(f"Running GPU performance benchmark with data size: {data_size}")

        # 生成測試數據
        np.random.seed(42)
        test_prices = np.random.randn(data_size).cumsum() + 100

        benchmark_results = {}

        # RSI基準測試
        rsi_periods = [14, 30, 50]
        start_time = time.time()
        self.calculate_rsi_batch_gpu(test_prices, rsi_periods)
        benchmark_results['rsi_batch_time'] = time.time() - start_time

        # MACD基準測試
        macd_fast = [12, 26]
        macd_slow = [50, 100]
        macd_signal = [9, 12]
        start_time = time.time()
        self.calculate_macd_batch_gpu(test_prices, macd_fast, macd_slow, macd_signal)
        benchmark_results['macd_batch_time'] = time.time() - start_time

        # 布林帶基準測試
        bb_periods = [20, 50]
        bb_std = [2.0, 2.5]
        start_time = time.time()
        self.calculate_bollinger_bands_gpu(test_prices, bb_periods, bb_std)
        benchmark_results['bollinger_batch_time'] = time.time() - start_time

        total_time = sum(benchmark_results.values())
        benchmark_results['total_time'] = total_time
        benchmark_results['operations_per_second'] = (len(rsi_periods) + len(macd_fast) * len(macd_slow) * len(macd_signal) + len(bb_periods) * len(bb_std)) / total_time

        logger.info(f"Benchmark completed: {benchmark_results['operations_per_second']:.1f} operations/second")
        return benchmark_results

# 全局GPU指標引擎實例
_gpu_indicators_instance = None

def get_gpu_indicators(config: Optional[GPUIndicatorConfig] = None) -> GPUAcceleratedIndicators:
    """獲取全局GPU指標引擎實例"""
    global _gpu_indicators_instance
    if _gpu_indicators_instance is None:
        _gpu_indicators_instance = GPUAcceleratedIndicators(config)
    return _gpu_indicators_instance

def reset_gpu_indicators():
    """重置全局GPU指標引擎"""
    global _gpu_indicators_instance
    _gpu_indicators_instance = None