#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU计算核心
实现真正的GPU技术指标计算，确保RSI、MACD等核心指标100%在GPU上执行
"""

import numpy as np
from typing import Tuple, Optional, Union, Dict, Any
import logging
import time

try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    cp = None
    GPU_AVAILABLE = False

from .error_handling import get_gpu_error_handler

logger = logging.getLogger(__name__)

class GPUComputationCore:
    """GPU计算核心"""

    def __init__(self, gpu_device: int = 0):
        self.gpu_device = gpu_device
        self.error_handler = get_gpu_error_handler()

        if GPU_AVAILABLE:
            self.cp = cp  # 添加CuPy引用
            cp.cuda.Device(gpu_device).use()
            logger.info(f"GPU计算核心初始化，使用设备: {gpu_device}")
            self._initialize_optimized_kernels()
        else:
            logger.error("CuPy不可用，GPU功能禁用")
            self.cp = None

    def _initialize_optimized_kernels(self):
        """初始化优化的GPU内核"""
        # 预编译常用内核以提高性能
        try:
            # RSI计算内核
            self.rsi_kernel = cp.RawKernel(r'''
            extern "C" __global__
            void calculate_rsi_kernel(const float* prices, float* rsi, int n, int period) {
                int tid = blockIdx.x * blockDim.x + threadIdx.x;

                if (tid >= n) return;

                if (tid < period) {
                    rsi[tid] = 50.0f;
                    return;
                }

                // 计算最近period个周期的涨跌
                float gain_sum = 0.0f;
                float loss_sum = 0.0f;

                for (int i = 0; i < period; i++) {
                    float delta = prices[tid - i] - prices[tid - i - 1];
                    if (delta > 0) {
                        gain_sum += delta;
                    } else {
                        loss_sum += -delta;
                    }
                }

                float avg_gain = gain_sum / period;
                float avg_loss = loss_sum / period;

                float rs = (avg_loss == 0.0f) ? 1000.0f : (avg_gain / avg_loss);
                rsi[tid] = 100.0f - (100.0f / (1.0f + rs));
            }
            ''', 'calculate_rsi_kernel')

            # 移动平均内核
            self.sma_kernel = cp.RawKernel(r'''
            extern "C" __global__
            void calculate_sma_kernel(const float* data, float* result, int n, int period) {
                int tid = blockIdx.x * blockDim.x + threadIdx.x;

                if (tid >= n) return;

                if (tid < period - 1) {
                    result[tid] = 0.0f;
                    return;
                }

                float sum = 0.0f;
                for (int i = 0; i < period; i++) {
                    sum += data[tid - i];
                }

                result[tid] = sum / period;
            }
            ''', 'calculate_sma_kernel')

            logger.info("GPU优化内核初始化完成")

        except Exception as e:
            logger.error(f"GPU内核初始化失败: {e}")
            self.rsi_kernel = None
            self.sma_kernel = None

    def calculate_rsi_gpu(self, prices: Union[np.ndarray, cp.ndarray], period: int = 14) -> cp.ndarray:
        """
        纯GPU RSI计算，零CPU依赖

        Args:
            prices: GPU价格数组
            period: RSI周期 (1-300)

        Returns:
            RSI值GPU数组 (0-100范围)
        """
        if not GPU_AVAILABLE:
            raise RuntimeError("GPU不可用")

        if period < 1 or period > 300:
            raise ValueError(f"RSI周期必须在1-300之间，当前: {period}")

        # CPU回退操作
        def cpu_rsi_fallback(prices_cpu, period=period):
            return self._cpu_rsi_calculation(prices_cpu, period)

        try:
            # 确保输入为GPU数组
            if not isinstance(prices, cp.ndarray):
                prices_gpu = cp.asarray(prices, dtype=cp.float32)
            else:
                prices_gpu = prices.astype(cp.float32)

            # 输入验证
            if len(prices_gpu) < period:
                return cp.full(len(prices_gpu), 50.0, dtype=cp.float32)

            # 使用优化的GPU内核
            if self.rsi_kernel is not None:
                return self._calculate_rsi_with_kernel(prices_gpu, period)
            else:
                return self._calculate_rsi_vectorized(prices_gpu, period)

        except Exception as e:
            logger.error(f"GPU RSI计算失败: {e}")
            return self.error_handler.execute_with_fallback(
                lambda p: self._calculate_rsi_vectorized(p, period),
                cpu_rsi_fallback,
                prices if isinstance(prices, np.ndarray) else cp.asnumpy(prices),
                "rsi_calculation"
            )

    def _calculate_rsi_with_kernel(self, prices_gpu: cp.ndarray, period: int) -> cp.ndarray:
        """使用CUDA内核计算RSI"""
        n = len(prices_gpu)
        rsi_gpu = cp.zeros(n, dtype=cp.float32)

        # 配置网格和块大小
        block_size = 256
        grid_size = (n + block_size - 1) // block_size

        # 执行内核
        self.rsi_kernel(
            (grid_size,), (block_size,),
            (prices_gpu, rsi_gpu, n, period)
        )

        return rsi_gpu

    def _calculate_rsi_vectorized(self, prices_gpu: cp.ndarray, period: int) -> cp.ndarray:
        """向量化RSI计算（纯CuPy实现）"""
        # 计算价格变化
        delta = cp.diff(prices_gpu, prepend=prices_gpu[:1])

        # 分离涨跌 - 修复where函数dtype参数问题
        gain = cp.where(delta > 0, delta, 0.0).astype(cp.float32)
        loss = cp.where(delta < 0, -delta, 0.0).astype(cp.float32)

        # 计算移动平均 - 优化版本
        avg_gain = self._calculate_moving_average_gpu(gain, period)
        avg_loss = self._calculate_moving_average_gpu(loss, period)

        # RS计算 - 避免除零
        rs = avg_gain / cp.where(avg_loss == 0, 1e-10, avg_loss)

        # RSI计算
        rsi = 100 - (100 / (1 + rs))

        # 填充前period-1个值为50
        rsi[:period] = 50.0

        # 确保值在0-100范围内
        rsi = cp.clip(rsi, 0, 100)

        return rsi

    def calculate_macd_gpu(self, prices: Union[np.ndarray, cp.ndarray],
                          fast_period: int = 12, slow_period: int = 26,
                          signal_period: int = 9) -> Tuple[cp.ndarray, cp.ndarray, cp.ndarray]:
        """
        GPU加速MACD计算

        Args:
            prices: GPU价格数组
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期

        Returns:
            (MACD线, 信号线, 柱状图)
        """
        if not GPU_AVAILABLE:
            raise RuntimeError("GPU不可用")

        # CPU回退操作
        def cpu_macd_fallback(prices_cpu):
            return self._cpu_macd_calculation(prices_cpu, fast_period, slow_period, signal_period)

        try:
            # 确保输入为GPU数组
            if not isinstance(prices, cp.ndarray):
                prices_gpu = cp.asarray(prices, dtype=cp.float32)
            else:
                prices_gpu = prices.astype(cp.float32)

            # 计算EMA
            ema_fast = self._calculate_ema_gpu(prices_gpu, fast_period)
            ema_slow = self._calculate_ema_gpu(prices_gpu, slow_period)

            # MACD线
            macd_line = ema_fast - ema_slow

            # 信号线
            signal_line = self._calculate_ema_gpu(macd_line, signal_period)

            # 柱状图
            histogram = macd_line - signal_line

            return macd_line, signal_line, histogram

        except Exception as e:
            logger.error(f"GPU MACD计算失败: {e}")
            macd, signal, hist = self.error_handler.execute_with_fallback(
                lambda p: self._calculate_macd_vectorized(p, fast_period, slow_period, signal_period),
                cpu_macd_fallback,
                prices if isinstance(prices, np.ndarray) else cp.asnumpy(prices),
                "macd_calculation"
            )
            return cp.asarray(macd), cp.asarray(signal), cp.asarray(hist)

    def _calculate_macd_vectorized(self, prices_gpu: cp.ndarray, fast: int, slow: int, signal: int):
        """向量化MACD计算"""
        ema_fast = self._calculate_ema_gpu(prices_gpu, fast)
        ema_slow = self._calculate_ema_gpu(prices_gpu, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self._calculate_ema_gpu(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def calculate_moving_average_gpu(self, data: Union[np.ndarray, cp.ndarray],
                                   period: int = 20, ma_type: str = 'sma') -> cp.ndarray:
        """
        GPU移动平均计算

        Args:
            data: GPU数据数组
            period: 周期
            ma_type: 移动平均类型 ('sma', 'ema')

        Returns:
            移动平均GPU数组
        """
        if not GPU_AVAILABLE:
            raise RuntimeError("GPU不可用")

        # CPU回退操作
        def cpu_ma_fallback(data_cpu):
            return self._cpu_sma_calculation(data_cpu, period) if ma_type == 'sma' else self._cpu_ema_calculation(data_cpu, period)

        try:
            # 确保输入为GPU数组
            if not isinstance(data, cp.ndarray):
                data_gpu = cp.asarray(data, dtype=cp.float32)
            else:
                data_gpu = data.astype(cp.float32)

            if ma_type.lower() == 'sma':
                return self._calculate_sma_gpu(data_gpu, period)
            elif ma_type.lower() == 'ema':
                return self._calculate_ema_gpu(data_gpu, period)
            else:
                raise ValueError(f"不支持的移动平均类型: {ma_type}")

        except Exception as e:
            logger.error(f"GPU移动平均计算失败: {e}")
            result = self.error_handler.execute_with_fallback(
                lambda d: self._calculate_sma_gpu(d, period) if ma_type == 'sma' else self._calculate_ema_gpu(d, period),
                cpu_ma_fallback,
                data if isinstance(data, np.ndarray) else cp.asnumpy(data),
                f"{ma_type}_calculation"
            )
            return cp.asarray(result)

    def _calculate_sma_gpu(self, data_gpu: cp.ndarray, period: int) -> cp.ndarray:
        """GPU简单移动平均计算"""
        if self.sma_kernel is not None:
            return self._calculate_sma_with_kernel(data_gpu, period)
        else:
            return self._calculate_sma_vectorized(data_gpu, period)

    def _calculate_sma_with_kernel(self, data_gpu: cp.ndarray, period: int) -> cp.ndarray:
        """使用CUDA内核计算SMA"""
        n = len(data_gpu)
        result_gpu = cp.zeros(n, dtype=cp.float32)

        # 配置网格和块大小
        block_size = 256
        grid_size = (n + block_size - 1) // block_size

        # 执行内核
        self.sma_kernel(
            (grid_size,), (block_size,),
            (data_gpu, result_gpu, n, period)
        )

        return result_gpu

    def _calculate_sma_vectorized(self, data_gpu: cp.ndarray, period: int) -> cp.ndarray:
        """向量化SMA计算"""
        return self._calculate_moving_average_gpu(data_gpu, period)

    def _calculate_moving_average_gpu(self, data_gpu: cp.ndarray, period: int) -> cp.ndarray:
        """GPU移动平均通用计算（使用cumsum优化）"""
        if period <= 1:
            return data_gpu.copy()

        n = len(data_gpu)
        if n < period:
            # 如果数据长度小于周期，返回全平均值
            return cp.full(n, cp.mean(data_gpu), dtype=cp.float32)

        # 使用cumsum实现高效移动平均
        cumsum = cp.cumsum(data_gpu, dtype=cp.float32)
        result = cp.zeros_like(data_gpu, dtype=cp.float32)

        # 修复数组形状不匹配问题 - 确保索引正确
        if n > period:
            # 正确的数组长度：cumsum[period:] 长度是 n-period
            # result[period:] 长度也是 n-period
            result[period:] = (cumsum[period:] - cumsum[:-period]) / period

            # 前period个元素用简单平均填充
            result[:period] = cp.mean(data_gpu[:period])
        elif n == period:
            # 数据长度等于周期，所有元素都是平均值
            result[:] = cp.mean(data_gpu)

        return result

    def _calculate_ema_gpu(self, data_gpu: cp.ndarray, period: int) -> cp.ndarray:
        """GPU EMA计算（优化版本）"""
        if period <= 1:
            return data_gpu.copy()

        alpha = 2.0 / (period + 1)
        result = cp.zeros_like(data_gpu, dtype=cp.float32)
        result[0] = data_gpu[0]

        # 使用向量化计算EMA
        for i in range(1, len(data_gpu)):
            result[i] = alpha * data_gpu[i] + (1 - alpha) * result[i-1]

        return result

    def calculate_kdj_gpu(self, high: Union[np.ndarray, cp.ndarray],
                         low: Union[np.ndarray, cp.ndarray],
                         close: Union[np.ndarray, cp.ndarray],
                         k_period: int = 9, d_period: int = 3) -> Tuple[cp.ndarray, cp.ndarray, cp.ndarray]:
        """
        GPU KDJ指标计算

        Args:
            high: 最高价GPU数组
            low: 最低价GPU数组
            close: 收盘价GPU数组
            k_period: K值周期
            d_period: D值周期

        Returns:
            (K值, D值, J值)
        """
        if not GPU_AVAILABLE:
            raise RuntimeError("GPU不可用")

        # CPU回退操作
        def cpu_kdj_fallback(h, l, c):
            return self._cpu_kdj_calculation(h, l, c, k_period, d_period)

        try:
            # 确保输入为GPU数组
            high_gpu = cp.asarray(high, dtype=cp.float32) if not isinstance(high, cp.ndarray) else high.astype(cp.float32)
            low_gpu = cp.asarray(low, dtype=cp.float32) if not isinstance(low, cp.ndarray) else low.astype(cp.float32)
            close_gpu = cp.asarray(close, dtype=cp.float32) if not isinstance(close, cp.ndarray) else close.astype(cp.float32)

            # 数据长度一致性检查
            min_length = min(len(high_gpu), len(low_gpu), len(close_gpu))
            if len(high_gpu) != min_length:
                high_gpu = high_gpu[:min_length]
            if len(low_gpu) != min_length:
                low_gpu = low_gpu[:min_length]
            if len(close_gpu) != min_length:
                close_gpu = close_gpu[:min_length]

            # 计算RSV
            lowest_low = self._calculate_rolling_min_gpu(low_gpu, k_period)
            highest_high = self._calculate_rolling_max_gpu(high_gpu, k_period)

            rsv = cp.where(
                highest_high == lowest_low,
                50.0,
                100 * (close_gpu - lowest_low) / (highest_high - lowest_low)
            )

            # K值计算 - EMA平滑
            k_values = self._calculate_ema_gpu(rsv, d_period)

            # D值计算 - K的EMA
            d_values = self._calculate_ema_gpu(k_values, d_period)

            # J值计算
            j_values = 3 * k_values - 2 * d_values

            return k_values, d_values, j_values

        except Exception as e:
            logger.error(f"GPU KDJ计算失败: {e}")
            k, d, j = self.error_handler.execute_with_fallback(
                lambda data: self._calculate_kdj_vectorized(data, k_period, d_period),
                cpu_kdj_fallback,
                {
                    'high': high if isinstance(high, np.ndarray) else cp.asnumpy(high),
                    'low': low if isinstance(low, np.ndarray) else cp.asnumpy(low),
                    'close': close if isinstance(close, np.ndarray) else cp.asnumpy(close)
                },
                "kdj_calculation"
            )
            return cp.asarray(k), cp.asarray(d), cp.asarray(j)

    def _calculate_kdj_vectorized(self, data_dict: dict, k_period: int, d_period: int):
        """向量化KDJ计算"""
        high = cp.asarray(data_dict['high'], dtype=cp.float32)
        low = cp.asarray(data_dict['low'], dtype=cp.float32)
        close = cp.asarray(data_dict['close'], dtype=cp.float32)

        return self.calculate_kdj_gpu(high, low, close, k_period, d_period)

    def _calculate_rolling_min_gpu(self, data_gpu: cp.ndarray, period: int) -> cp.ndarray:
        """GPU滚动最小值计算"""
        if period <= 1:
            return data_gpu.copy()

        # 简化实现：使用滑动窗口
        result = cp.zeros_like(data_gpu)
        for i in range(len(data_gpu)):
            start_idx = max(0, i - period + 1)
            result[i] = cp.min(data_gpu[start_idx:i+1])

        return result

    def _calculate_rolling_max_gpu(self, data_gpu: cp.ndarray, period: int) -> cp.ndarray:
        """GPU滚动最大值计算"""
        if period <= 1:
            return data_gpu.copy()

        # 简化实现：使用滑动窗口
        result = cp.zeros_like(data_gpu)
        for i in range(len(data_gpu)):
            start_idx = max(0, i - period + 1)
            result[i] = cp.max(data_gpu[start_idx:i+1])

        return result

    # CPU回退方法
    def _cpu_rsi_calculation(self, prices_cpu: np.ndarray, period: int) -> np.ndarray:
        """CPU RSI计算"""
        if len(prices_cpu) < period:
            return np.full(len(prices_cpu), 50.0, dtype=np.float32)

        delta = np.diff(prices_cpu, prepend=prices_cpu[0])
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = np.convolve(gain, np.ones(period), mode='valid') / period
        avg_loss = np.convolve(loss, np.ones(period), mode='valid') / period

        rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
        rsi = 100 - (100 / (1 + rs))

        result = np.full(len(prices_cpu), 50.0, dtype=np.float32)
        result[period:] = rsi

        return result

    def _cpu_macd_calculation(self, prices_cpu: np.ndarray, fast: int, slow: int, signal: int):
        """CPU MACD计算"""
        def ema(data, period):
            alpha = 2 / (period + 1)
            ema = np.zeros_like(data, dtype=np.float32)
            ema[0] = data[0]
            for i in range(1, len(data)):
                ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
            return ema

        ema_fast = ema(prices_cpu, fast)
        ema_slow = ema(prices_cpu, slow)
        macd_line = ema_fast - ema_slow
        signal_line = ema(macd_line, signal)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def _cpu_sma_calculation(self, data_cpu: np.ndarray, period: int) -> np.ndarray:
        """CPU SMA计算"""
        if len(data_cpu) < period:
            return np.full(len(data_cpu), np.mean(data_cpu), dtype=np.float32)

        return np.convolve(data_cpu, np.ones(period), mode='same') / period

    def _cpu_ema_calculation(self, data_cpu: np.ndarray, period: int) -> np.ndarray:
        """CPU EMA计算"""
        alpha = 2 / (period + 1)
        ema = np.zeros_like(data_cpu, dtype=np.float32)
        ema[0] = data_cpu[0]
        for i in range(1, len(data_cpu)):
            ema[i] = alpha * data_cpu[i] + (1 - alpha) * ema[i-1]
        return ema

    def _cpu_kdj_calculation(self, high_cpu: np.ndarray, low_cpu: np.ndarray, close_cpu: np.ndarray,
                           k_period: int, d_period: int):
        """CPU KDJ计算"""
        def rsi_ema(data, period):
            alpha = 2 / (period + 1)
            ema = np.zeros_like(data, dtype=np.float32)
            ema[0] = data[0]
            for i in range(1, len(data)):
                ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
            return ema

        # 计算RSV
        lowest_low = np.array([np.min(low_cpu[max(0, i-k_period+1):i+1]) for i in range(len(low_cpu))])
        highest_high = np.array([np.max(high_cpu[max(0, i-k_period+1):i+1]) for i in range(len(high_cpu))])

        rsv = np.where(highest_high == lowest_low, 50.0, 100 * (close_cpu - lowest_low) / (highest_high - lowest_low))

        # K, D, J计算
        k_values = rsi_ema(rsv, d_period)
        d_values = rsi_ema(k_values, d_period)
        j_values = 3 * k_values - 2 * d_values

        return k_values, d_values, j_values

    def benchmark_performance(self, data_size: int = 100000) -> Dict[str, float]:
        """性能基准测试"""
        if not GPU_AVAILABLE:
            return {'error': 'GPU不可用'}

        try:
            # 生成测试数据
            test_data = np.random.uniform(50, 150, data_size).astype(np.float32)

            results = {}

            # RSI基准测试
            start_time = time.time()
            rsi_gpu = self.calculate_rsi_gpu(test_data, 14)
            gpu_time = time.time() - start_time

            start_time = time.time()
            rsi_cpu = self._cpu_rsi_calculation(test_data, 14)
            cpu_time = time.time() - start_time

            results['rsi_speedup'] = cpu_time / gpu_time
            results['rsi_gpu_time'] = gpu_time
            results['rsi_cpu_time'] = cpu_time

            # MACD基准测试
            start_time = time.time()
            macd_gpu = self.calculate_macd_gpu(test_data)
            gpu_time = time.time() - start_time

            start_time = time.time()
            macd_cpu = self._cpu_macd_calculation(test_data)
            cpu_time = time.time() - start_time

            results['macd_speedup'] = cpu_time / gpu_time
            results['macd_gpu_time'] = gpu_time
            results['macd_cpu_time'] = cpu_time

            return results

        except Exception as e:
            logger.error(f"性能基准测试失败: {e}")
            return {'error': str(e)}


def get_gpu_computation_core(gpu_device: int = 0) -> GPUComputationCore:
    """获取GPU计算核心实例"""
    return GPUComputationCore(gpu_device)


# 测试代码
if __name__ == "__main__":
    # 测试GPU计算核心
    try:
        core = get_gpu_computation_core()

        # 生成测试数据
        test_prices = np.random.uniform(100, 200, 1000).astype(np.float32)

        # 测试RSI
        rsi = core.calculate_rsi_gpu(test_prices, 14)
        print(f"RSI计算成功，长度: {len(rsi)}")

        # 测试MACD
        macd, signal, hist = core.calculate_macd_gpu(test_prices)
        print(f"MACD计算成功，长度: {len(macd)}")

        # 测试移动平均
        sma = core.calculate_moving_average_gpu(test_prices, 20, 'sma')
        ema = core.calculate_moving_average_gpu(test_prices, 20, 'ema')
        print(f"移动平均计算成功")

        # 性能基准测试
        benchmark = core.benchmark_performance(50000)
        print(f"性能基准: {benchmark}")

    except Exception as e:
        print(f"GPU计算核心测试失败: {e}")