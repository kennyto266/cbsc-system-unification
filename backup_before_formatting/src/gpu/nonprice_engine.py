#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非價格數據GPU加速TA引擎
專門為非價格數據優化的GPU計算引擎
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import time
import concurrent.futures

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.gpu_config import get_gpu_config_manager
from vectorization.time_series import get_time_series_vectorizer, VectorizedData

logger = logging.getLogger(__name__)

@dataclass
class OptimizationResult:
    """優化結果"""
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    execution_time: float
    strategy_id: str
    data_length: int

class NonPriceGPUEngine:
    """非價格數據GPU引擎"""

    def __init__(self):
        self.gpu_config = get_gpu_config_manager()
        self.vectorizer = get_time_series_vectorizer()
        self.gpu_available = self.gpu_config.get_config_summary()['gpu_available']

        # 性能緩存
        self._performance_cache = {}

        # CUDA核心函數（延遲導入）
        self._cuda_kernels = None
        self._init_cuda_kernels()

        logger.info(f"Non-Price GPU Engine initialized. GPU available: {self.gpu_available}")

    def _init_cuda_kernels(self):
        """初始化CUDA核心函數"""
        if not self.gpu_available:
            logger.info("GPU not available, using CPU kernels")
            return

        try:
            import cupy as cp

            # 自定義CUDA核心函數
            self._cuda_kernels = {
                'rsi': self._create_rsi_kernel(cp),
                'macd': self._create_macd_kernel(cp),
                'bollinger': self._create_bollinger_kernel(cp),
                'moving_average': self._create_moving_average_kernel(cp),
                'sharpe': self._create_sharpe_kernel(cp)
            }

            logger.info("CUDA kernels initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize CUDA kernels: {e}")
            self._cuda_kernels = None

    def _create_rsi_kernel(self, cp):
        """創建RSI CUDA核心函數"""
        # 簡化版RSI實現，使用向量化操作
        def rsi_kernel(prices, period):
            # 預處理
            if len(prices) < period:
                return cp.full(len(prices), 50.0, dtype=cp.float32)

            # 計算價格變化
            delta = cp.diff(prices, n=1, prepend=cp.array([0]))

            # 分離漲跌
            gain = cp.where(delta > 0, delta, 0.0)
            loss = cp.where(delta < 0, -delta, 0.0)

            # 計算移動平均（使用cumsum替代convolve提高效率）
            gain_ma = self._moving_average_cupy(gain, period)
            loss_ma = self._moving_average_cupy(loss, period)

            # 計算RS和RSI
            rs = gain_ma / cp.where(loss_ma == 0, 1e-10, loss_ma)
            rsi = 100 - (100 / (1 + rs))

            # 填充前period-1個值
            result = cp.full(len(prices), 50.0, dtype=cp.float32)
            result[period:] = rsi[:len(prices)-period]

            return result

        return rsi_kernel

    def _create_macd_kernel(self, cp):
        """創建MACD CUDA核心函數"""
        def macd_kernel(prices, fast_period, slow_period, signal_period):
            if len(prices) < slow_period:
                return cp.zeros(3, dtype=cp.float32)

            # 計算EMA
            ema_fast = self._ema_cupy(prices, fast_period)
            ema_slow = self._ema_cupy(prices, slow_period)

            # MACD線
            macd_line = ema_fast - ema_slow

            # 信號線
            signal_line = self._ema_cupy(macd_line, signal_period)

            # 柱狀線
            histogram = macd_line - signal_line

            return macd_line, signal_line, histogram

        return macd_kernel

    def _create_bollinger_kernel(self, cp):
        """創建布林帶CUDA核心函數"""
        def bollinger_kernel(prices, period, num_std):
            if len(prices) < period:
                return cp.zeros(3, dtype=cp.float32)

            # 計算移動平均
            ma = self._moving_average_cupy(prices, period)

            # 計算標準差
            std = self._rolling_std_cupy(prices, period)

            # 計算上下軌
            upper_band = ma + num_std * std
            lower_band = ma - num_std * std

            return ma, upper_band, lower_band

        return bollinger_kernel

    def _create_moving_average_kernel(self, cp):
        """創建移動平均CUDA核心函數"""
        def ma_kernel(prices, period):
            return self._moving_average_cupy(prices, period)
        return ma_kernel

    def _create_sharpe_kernel(self, cp):
        """創建Sharpe比率CUDA核心函數"""
        def sharpe_kernel(returns, risk_free_rate=0.03):
            if len(returns) == 0:
                return 0.0

            mean_return = cp.mean(returns)
            std_return = cp.std(returns)

            if std_return == 0:
                return 0.0 if mean_return > risk_free_rate else -1.0

            # 年化Sharpe比率
            sharpe = (mean_return - risk_free_rate) / std_return
            return sharpe

        return sharpe_kernel

    def _moving_average_cupy(self, data, period):
        """CuPy移動平均實現"""
        if period <= 1:
            return data

        # 使用cumsum實現移動平均
        cumsum = cp.cumsum(data, dtype=cp.float32)
        result = cp.zeros_like(data, dtype=cp.float32)
        result[period:] = (cumsum[period:] - cumsum[:-period]) / period
        result[:period] = data[:period]  # 填充前period個值

        return result

    def _ema_cupy(self, data, period):
        """CuPy EMA實現"""
        if period <= 1:
            return data

        alpha = 2.0 / (period + 1)
        result = cp.zeros_like(data, dtype=cp.float32)
        result[0] = data[0]

        for i in range(1, len(data)):
            result[i] = alpha * data[i] + (1 - alpha) * result[i-1]

        return result

    def _rolling_std_cupy(self, data, period):
        """CuPy滾動標準差實現"""
        if period <= 1:
            return cp.zeros_like(data)

        # 計算移動平均
        ma = self._moving_average_cupy(data, period)

        # 計算方差
        squared_diff = (data - ma) ** 2
        variance = self._moving_average_cupy(squared_diff, period)

        return cp.sqrt(variance)

    def optimize_rsi_parameters_gpu(self, vectorized_data: VectorizedData,
                                    param_range: Tuple[int, int] = (1, 300),
                                    step: int = 1) -> List[OptimizationResult]:
        """
        GPU加速的RSI參數優化

        Args:
            vectorized_data: 向量化數據
            param_range: 參數範圍 (min, max)
            step: 參數步長

        Returns:
            優化結果列表
        """
        if not self.gpu_available or self._cuda_kernels is None:
            return self._optimize_rsi_parameters_cpu(vectorized_data, param_range, step)

        try:
            import cupy as cp

            # 轉換數據到GPU
            prices_gpu = cp.asarray(vectorized_data.values)

            # 生成參數網格
            param_list = list(range(param_range[0], param_range[1] + 1, step))

            # 批量處理參數
            batch_size = min(1000, len(param_list))  # 批處理大小
            results = []

            start_time = time.time()

            for i in range(0, len(param_list), batch_size):
                batch_params = param_list[i:i + batch_size]
                batch_results = []

                for period in batch_params:
                    # 使用CUDA核心計算RSI
                    rsi_values = self._cuda_kernels['rsi'](prices_gpu, period)

                    # 計算回測指標
                    returns = self._calculate_returns_from_rsi(rsi_values)
                    sharpe = self._cuda_kernels['sharpe'](returns)
                    max_dd = self._calculate_max_drawdown(returns)

                    # 創建結果
                    result = OptimizationResult(
                        parameters={'period': period},
                        metrics={
                            'sharpe_ratio': float(sharpe),
                            'max_drawdown': float(max_dd),
                            'total_return': float(cp.sum(returns)),
                            'win_rate': float(cp.mean(returns > 0))
                        },
                        execution_time=0.0,
                        strategy_id=f'RSI_{period}',
                        data_length=len(vectorized_data.values)
                    )

                    batch_results.append(result)

                results.extend(batch_results)

                # 定期清理GPU內存
                if i % (batch_size * 10) == 0:
                    cp.get_default_memory_pool().free_all_blocks()

            total_time = time.time() - start_time

            # 更新執行時間
            for result in results:
                result.execution_time = total_time / len(results)

            logger.info(f"GPU RSI optimization completed: {len(results)} parameters in {total_time:.4f}s")

            # 按Sharpe比率排序
            results.sort(key=lambda x: x.metrics['sharpe_ratio'], reverse=True)

            return results

        except Exception as e:
            logger.error(f"GPU RSI optimization failed: {e}")
            return self._optimize_rsi_parameters_cpu(vectorized_data, param_range, step)

    def optimize_rsi_parameters_cpu(self, vectorized_data: VectorizedData,
                                   param_range: Tuple[int, int] = (1, 300),
                                   step: int = 1) -> List[OptimizationResult]:
        """CPU版本的RSI參數優化"""
        results = []
        prices = vectorized_data.values

        start_time = time.time()

        for period in range(param_range[0], param_range[1] + 1, step):
            try:
                # CPU版本RSI計算
                rsi_values = self._calculate_rsi_cpu(prices, period)

                # 計算回測指標
                returns = self._calculate_returns_from_rsi(rsi_values)
                sharpe = self._calculate_sharpe_ratio_cpu(returns)
                max_dd = self._calculate_max_drawdown_cpu(returns)

                result = OptimizationResult(
                    parameters={'period': period},
                    metrics={
                        'sharpe_ratio': sharpe,
                        'max_drawdown': max_dd,
                        'total_return': float(np.sum(returns)),
                        'win_rate': float(np.mean(returns > 0))
                    },
                    execution_time=0.0,
                    strategy_id=f'RSI_{period}',
                    data_length=len(prices)
                )

                results.append(result)

            except Exception as e:
                logger.error(f"RSI calculation failed for period {period}: {e}")
                continue

        total_time = time.time() - start_time

        # 更新執行時間
        for result in results:
            result.execution_time = total_time / len(results)

        # 按Sharpe比率排序
        results.sort(key=lambda x: x.metrics['sharpe_ratio'], reverse=True)

        return results

    def _calculate_rsi_cpu(self, prices, period):
        """CPU版本的RSI計算"""
        if len(prices) < period:
            return np.full(len(prices), 50.0, dtype=np.float32)

        # 計算價格變化
        delta = np.diff(prices, prepend=0)

        # 分離漲跌
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)

        # 計算移動平均
        avg_gain = np.convolve(gain, np.ones(period), mode='valid') / period
        avg_loss = np.convolve(loss, np.ones(period), mode='valid') / period

        # 計算RS和RSI
        rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
        rsi = 100 - (100 / (1 + rs))

        # 填充前period-1個值
        result = np.full(len(prices), 50.0, dtype=np.float32)
        result[period:] = rsi

        return result

    def _calculate_returns_from_rsi(self, rsi_values):
        """從RSI值計算回報率"""
        if len(rsi_values) < 2:
            return np.zeros(len(rsi_values))

        # 簡單的交易信號：RSI < 30買入，RSI > 70賣出
        signals = np.where(rsi_values < 30, 1, np.where(rsi_values > 70, -1, 0))

        # 計算回報（簡化版本，假設1%的固定回報）
        returns = signals * 0.01

        return returns

    def _calculate_sharpe_ratio_cpu(self, returns, risk_free_rate=0.03):
        """CPU版本Sharpe比率計算"""
        if len(returns) == 0:
            return 0.0

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0 if mean_return > risk_free_rate else -1.0

        # 年化Sharpe比率（假設252個交易日）
        sharpe = (mean_return * 252 - risk_free_rate) / (std_return * np.sqrt(252))
        return sharpe

    def _calculate_max_drawdown_cpu(self, returns):
        """CPU版本最大回撤計算"""
        if len(returns) == 0:
            return 0.0

        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = cumulative - running_max
        max_drawdown = np.min(drawdowns)

        return max_drawdown if max_drawdown < 0 else 0.0

    def batch_optimize_multiple_sources(self, data_dict: Dict[str, VectorizedData],
                                       optimization_config: Dict[str, Any]) -> Dict[str, List[OptimizationResult]]:
        """
        批量優化多個數據源

        Args:
            data_dict: 向量化數據字典
            optimization_config: 優化配置

        Returns:
            優化結果字典
        """
        results = {}

        # 使用線程池並行處理
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(data_dict))) as executor:
            future_to_source = {}

            # 提交所有優化任務
            for source_id, vectorized_data in data_dict.items():
                future = executor.submit(
                    self.optimize_single_source,
                    source_id,
                    vectorized_data,
                    optimization_config
                )
                future_to_source[future] = source_id

            # 收集結果
            for future in concurrent.futures.as_completed(future_to_source):
                source_id = future_to_source[future]
                try:
                    source_results = future.result()
                    results[source_id] = source_results
                    logger.info(f"Completed optimization for {source_id}: {len(source_results)} strategies")
                except Exception as e:
                    logger.error(f"Failed to optimize {source_id}: {e}")
                    results[source_id] = []

        return results

    def optimize_single_source(self, source_id: str, vectorized_data: VectorizedData,
                              config: Dict[str, Any]) -> List[OptimizationResult]:
        """
        優化單個數據源

        Args:
            source_id: 數據源ID
            vectorized_data: 向量化數據
            config: 優化配置

        Returns:
            優化結果列表
        """
        # 根據配置選擇優化方法
        strategy = config.get('strategy', 'rsi')

        if strategy == 'rsi':
            param_range = config.get('rsi_range', (1, 300))
            step = config.get('rsi_step', 1)
            return self.optimize_rsi_parameters_gpu(vectorized_data, param_range, step)

        else:
            logger.warning(f"Unsupported strategy: {strategy}")
            return []

    def get_performance_summary(self, results: List[OptimizationResult]) -> Dict[str, Any]:
        """
        獲取性能摘要

        Args:
            results: 優化結果列表

        Returns:
            性能摘要字典
        """
        if not results:
            return {'error': 'No results provided'}

        # 計算統計指標
        sharpe_ratios = [r.metrics['sharpe_ratio'] for r in results]
        max_drawdowns = [r.metrics['max_drawdown'] for r in results]
        execution_times = [r.execution_time for r in results]

        summary = {
            'total_strategies': len(results),
            'best_sharpe': max(sharpe_ratios) if sharpe_ratios else 0.0,
            'avg_sharpe': np.mean(sharpe_ratios) if sharpe_ratios else 0.0,
            'max_sharpe_strategy': max(results, key=lambda x: x.metrics['sharpe_ratio']).parameters,
            'avg_max_drawdown': np.mean(max_drawdowns) if max_drawdowns else 0.0,
            'min_max_drawdown': min(max_drawdowns) if max_drawdowns else 0.0,
            'avg_execution_time': np.mean(execution_times) if execution_times else 0.0,
            'gpu_utilized': self.gpu_available,
            'data_length': results[0].data_length if results else 0
        }

        # 計算性能指標
        total_time = sum(execution_times)
        if total_time > 0:
            summary['strategies_per_second'] = len(results) / total_time
        else:
            summary['strategies_per_second'] = 0

        return summary

    def cleanup(self):
        """清理GPU資源"""
        if self.gpu_available:
            try:
                import cupy as cp
                cp.get_default_memory_pool().free_all_blocks()
                logger.info("GPU memory cleaned up")
            except Exception as e:
                logger.error(f"Failed to cleanup GPU memory: {e}")

# 全局引擎實例
_nonprice_engine = None

def get_nonprice_gpu_engine() -> NonPriceGPUEngine:
    """獲取非價格GPU引擎實例"""
    global _nonprice_engine
    if _nonprice_engine is None:
        _nonprice_engine = NonPriceGPUEngine()
    return _nonprice_engine