#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU加速參數優化引擎
專門為0-300全方位參數優化設計的高性能引擎
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
import time
import concurrent.futures
from itertools import product

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from gpu.nonprice_engine import NonPriceGPUEngine, OptimizationResult
from utils.gpu_config import get_gpu_config_manager
from vectorization.time_series import get_time_series_vectorizer, VectorizedData

logger = logging.getLogger(__name__)

@dataclass
class OptimizationConfig:
    """優化配置"""
    strategy_type: str = 'rsi'  # rsi, macd, bollinger, multi
    param_ranges: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    param_steps: Dict[str, int] = field(default_factory=dict)
    optimization_metric: str = 'sharpe_ratio'  # sharpe_ratio, total_return, win_rate
    risk_free_rate: float = 0.03
    batch_size: int = 1000
    max_workers: int = 4
    use_gpu: bool = True
    enable_parallel: bool = True

@dataclass
class OptimizationReport:
    """優化報告"""
    optimization_id: str
    config: OptimizationConfig
    results: List[OptimizationResult]
    execution_time: float
    best_strategy: OptimizationResult
    statistics: Dict[str, Any]
    gpu_utilized: bool
    data_sources: List[str]

class GPUParameterOptimizer:
    """GPU加速參數優化器"""

    def __init__(self):
        self.gpu_engine = NonPriceGPUEngine()
        self.vectorizer = get_time_series_vectorizer()
        self.gpu_config = get_gpu_config_manager()

        # 預設參數範圍
        self.default_param_ranges = {
            'rsi': {'period': (1, 300)},
            'macd': {
                'fast_period': (1, 50),
                'slow_period': (51, 300),
                'signal_period': (1, 20)
            },
            'bollinger': {
                'period': (1, 300),
                'num_std': (1, 5)
            },
            'moving_average': {
                'short_period': (1, 100),
                'long_period': (101, 300)
            },
            'kdj': {
                'period': (1, 300),
                'smooth_k': (1, 20),
                'smooth_d': (1, 20)
            }
        }

        logger.info("GPU Parameter Optimizer initialized")

    def create_optimization_config(self,
                                  strategy_type: str,
                                  custom_ranges: Optional[Dict[str, Tuple[int, int]]] = None,
                                  **kwargs) -> OptimizationConfig:
        """
        創建優化配置

        Args:
            strategy_type: 策略類型
            custom_ranges: 自定義參數範圍
            **kwargs: 其他配置參數

        Returns:
            優化配置
        """
        # 使用預設範圍或自定義範圍
        param_ranges = custom_ranges or self.default_param_ranges.get(strategy_type, {})

        config = OptimizationConfig(
            strategy_type=strategy_type,
            param_ranges=param_ranges,
            **kwargs
        )

        return config

    def generate_parameter_grid(self, config: OptimizationConfig) -> List[Dict[str, Any]]:
        """
        生成參數網格

        Args:
            config: 優化配置

        Returns:
            參數列表
        """
        param_list = []
        param_names = list(config.param_ranges.keys())
        param_values = []

        # 為每個參數生成值列表
        for param_name in param_names:
            min_val, max_val = config.param_ranges[param_name]
            step = config.param_steps.get(param_name, 1)
            values = list(range(min_val, max_val + 1, step))
            param_values.append(values)

        # 生成所有組合
        for combination in product(*param_values):
            param_dict = dict(zip(param_names, combination))
            param_list.append(param_dict)

        logger.info(f"Generated {len(param_list)} parameter combinations for {config.strategy_type}")
        return param_list

    def optimize_single_source(self,
                              vectorized_data: VectorizedData,
                              config: OptimizationConfig) -> OptimizationReport:
        """
        優化單個數據源

        Args:
            vectorized_data: 向量化數據
            config: 優化配置

        Returns:
            優化報告
        """
        optimization_id = f"{config.strategy_type}_{vectorized_data.source_id}_{int(time.time())}"
        start_time = time.time()

        try:
            # 生成參數網格
            param_grid = self.generate_parameter_grid(config)

            logger.info(f"Starting optimization {optimization_id}: {len(param_grid)} parameter combinations")

            # 執行優化
            results = self._execute_optimization(vectorized_data, config, param_grid)

            # 找到最佳策略
            best_strategy = self._find_best_strategy(results, config.optimization_metric)

            # 計算統計信息
            statistics = self._calculate_statistics(results)

            execution_time = time.time() - start_time

            report = OptimizationReport(
                optimization_id=optimization_id,
                config=config,
                results=results,
                execution_time=execution_time,
                best_strategy=best_strategy,
                statistics=statistics,
                gpu_utilized=self.gpu_engine.gpu_available and config.use_gpu,
                data_sources=[vectorized_data.source_id]
            )

            logger.info(f"Optimization {optimization_id} completed in {execution_time:.2f}s")
            return report

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise

    def optimize_multiple_sources(self,
                                 data_dict: Dict[str, VectorizedData],
                                 config: OptimizationConfig) -> OptimizationReport:
        """
        優化多個數據源

        Args:
            data_dict: 向量化數據字典
            config: 優化配置

        Returns:
            優化報告
        """
        optimization_id = f"multi_{config.strategy_type}_{int(time.time())}"
        start_time = time.time()

        try:
            all_results = []
            source_results = {}

            # 並行處理多個數據源
            if config.enable_parallel and len(data_dict) > 1:
                with concurrent.futures.ThreadPoolExecutor(max_workers=config.max_workers) as executor:
                    future_to_source = {}

                    for source_id, vectorized_data in data_dict.items():
                        future = executor.submit(
                            self._optimize_source_with_config,
                            vectorized_data,
                            config,
                            f"{optimization_id}_{source_id}"
                        )
                        future_to_source[future] = source_id

                    for future in concurrent.futures.as_completed(future_to_source):
                        source_id = future_to_source[future]
                        try:
                            source_opt_results = future.result()
                            all_results.extend(source_opt_results)
                            source_results[source_id] = source_opt_results
                            logger.info(f"Completed optimization for {source_id}: {len(source_opt_results)} strategies")
                        except Exception as e:
                            logger.error(f"Failed to optimize {source_id}: {e}")
            else:
                # 順序處理
                for source_id, vectorized_data in data_dict.items():
                    source_opt_results = self._optimize_source_with_config(
                        vectorized_data,
                        config,
                        f"{optimization_id}_{source_id}"
                    )
                    all_results.extend(source_opt_results)
                    source_results[source_id] = source_opt_results

            # 全局最佳策略
            best_strategy = self._find_best_strategy(all_results, config.optimization_metric)
            statistics = self._calculate_statistics(all_results, by_source=True)
            execution_time = time.time() - start_time

            report = OptimizationReport(
                optimization_id=optimization_id,
                config=config,
                results=all_results,
                execution_time=execution_time,
                best_strategy=best_strategy,
                statistics=statistics,
                gpu_utilized=self.gpu_engine.gpu_available and config.use_gpu,
                data_sources=list(data_dict.keys())
            )

            logger.info(f"Multi-source optimization {optimization_id} completed in {execution_time:.2f}s")
            return report

        except Exception as e:
            logger.error(f"Multi-source optimization failed: {e}")
            raise

    def _optimize_source_with_config(self,
                                   vectorized_data: VectorizedData,
                                   config: OptimizationConfig,
                                   optimization_id: str) -> List[OptimizationResult]:
        """優化單個數據源（內部方法）"""
        param_grid = self.generate_parameter_grid(config)
        return self._execute_optimization(vectorized_data, config, param_grid)

    def _execute_optimization(self,
                             vectorized_data: VectorizedData,
                             config: OptimizationConfig,
                             param_grid: List[Dict[str, Any]]) -> List[OptimizationResult]:
        """
        執行優化

        Args:
            vectorized_data: 向量化數據
            config: 優化配置
            param_grid: 參數網格

        Returns:
            優化結果列表
        """
        results = []

        if config.strategy_type == 'rsi':
            results = self._optimize_rsi(vectorized_data, param_grid, config)
        elif config.strategy_type == 'macd':
            results = self._optimize_macd(vectorized_data, param_grid, config)
        elif config.strategy_type == 'bollinger':
            results = self._optimize_bollinger(vectorized_data, param_grid, config)
        elif config.strategy_type == 'multi':
            results = self._optimize_multi_strategies(vectorized_data, param_grid, config)
        else:
            logger.warning(f"Unsupported strategy type: {config.strategy_type}")
            return []

        return results

    def _optimize_rsi(self,
                      vectorized_data: VectorizedData,
                      param_grid: List[Dict[str, Any]],
                      config: OptimizationConfig) -> List[OptimizationResult]:
        """RSI參數優化"""
        if self.gpu_engine.gpu_available and config.use_gpu:
            # GPU優化
            periods = [params['period'] for params in param_grid]
            min_period, max_period = min(periods), max(periods)

            gpu_results = self.gpu_engine.optimize_rsi_parameters_gpu(
                vectorized_data,
                param_range=(min_period, max_period),
                step=config.param_steps.get('period', 1)
            )

            # 過濾只包含指定的參數
            filtered_results = [
                result for result in gpu_results
                if result.parameters['period'] in periods
            ]

            return filtered_results
        else:
            # CPU優化
            return self.gpu_engine.optimize_rsi_parameters_cpu(
                vectorized_data,
                param_range=(min(param_grid, key=lambda x: x['period'])['period'],
                           max(param_grid, key=lambda x: x['period'])['period']),
                step=config.param_steps.get('period', 1)
            )

    def _optimize_macd(self,
                       vectorized_data: VectorizedData,
                       param_grid: List[Dict[str, Any]],
                       config: OptimizationConfig) -> List[OptimizationResult]:
        """MACD參數優化"""
        results = []

        for params in param_grid:
            try:
                # 模擬MACD優化（實際實現需要擴展GPU引擎）
                result = OptimizationResult(
                    parameters=params,
                    metrics={
                        'sharpe_ratio': np.random.normal(0.5, 0.3),  # 模擬結果
                        'max_drawdown': np.random.uniform(-0.2, -0.05),
                        'total_return': np.random.uniform(-0.1, 0.3),
                        'win_rate': np.random.uniform(0.3, 0.7)
                    },
                    execution_time=0.001,
                    strategy_id=f"MACD_{params['fast_period']}_{params['slow_period']}_{params['signal_period']}",
                    data_length=len(vectorized_data.values)
                )
                results.append(result)

            except Exception as e:
                logger.error(f"MACD optimization failed for {params}: {e}")
                continue

        return results

    def _optimize_bollinger(self,
                           vectorized_data: VectorizedData,
                           param_grid: List[Dict[str, Any]],
                           config: OptimizationConfig) -> List[OptimizationResult]:
        """布林帶參數優化"""
        results = []

        for params in param_grid:
            try:
                # 模擬布林帶優化
                result = OptimizationResult(
                    parameters=params,
                    metrics={
                        'sharpe_ratio': np.random.normal(0.6, 0.25),
                        'max_drawdown': np.random.uniform(-0.15, -0.05),
                        'total_return': np.random.uniform(0.05, 0.25),
                        'win_rate': np.random.uniform(0.4, 0.8)
                    },
                    execution_time=0.001,
                    strategy_id=f"BOLL_{params['period']}_{params['num_std']}",
                    data_length=len(vectorized_data.values)
                )
                results.append(result)

            except Exception as e:
                logger.error(f"Bollinger optimization failed for {params}: {e}")
                continue

        return results

    def _optimize_multi_strategies(self,
                                   vectorized_data: VectorizedData,
                                   param_grid: List[Dict[str, Any]],
                                   config: OptimizationConfig) -> List[OptimizationResult]:
        """多策略組合優化"""
        # 這是一個複雜的多策略組合優化實現
        # 簡化版本，實際應用中需要更複雜的組合邏輯
        results = []

        for i, params in enumerate(param_grid[:100]):  # 限制數量以避免過長時間
            try:
                result = OptimizationResult(
                    parameters=params,
                    metrics={
                        'sharpe_ratio': np.random.normal(0.8, 0.4),
                        'max_drawdown': np.random.uniform(-0.1, -0.02),
                        'total_return': np.random.uniform(0.1, 0.4),
                        'win_rate': np.random.uniform(0.5, 0.9)
                    },
                    execution_time=0.002,
                    strategy_id=f"MULTI_{i}",
                    data_length=len(vectorized_data.values)
                )
                results.append(result)

            except Exception as e:
                logger.error(f"Multi-strategy optimization failed for {params}: {e}")
                continue

        return results

    def _find_best_strategy(self,
                           results: List[OptimizationResult],
                           metric: str) -> OptimizationResult:
        """找到最佳策略"""
        if not results:
            raise ValueError("No results provided")

        return max(results, key=lambda x: x.metrics.get(metric, 0))

    def _calculate_statistics(self,
                             results: List[OptimizationResult],
                             by_source: bool = False) -> Dict[str, Any]:
        """計算統計信息"""
        if not results:
            return {}

        sharpe_ratios = [r.metrics.get('sharpe_ratio', 0) for r in results]
        total_returns = [r.metrics.get('total_return', 0) for r in results]
        max_drawdowns = [r.metrics.get('max_drawdown', 0) for r in results]

        stats = {
            'total_strategies': len(results),
            'sharpe_ratio': {
                'mean': np.mean(sharpe_ratios),
                'std': np.std(sharpe_ratios),
                'min': np.min(sharpe_ratios),
                'max': np.max(sharpe_ratios)
            },
            'total_return': {
                'mean': np.mean(total_returns),
                'std': np.std(total_returns),
                'min': np.min(total_returns),
                'max': np.max(total_returns)
            },
            'max_drawdown': {
                'mean': np.mean(max_drawdowns),
                'std': np.std(max_drawdowns),
                'min': np.min(max_drawdowns),
                'max': np.max(max_drawdowns)
            }
        }

        # 添加高性能策略統計
        high_sharpe = [r for r in results if r.metrics.get('sharpe_ratio', 0) > 1.0]
        stats['high_sharpe_strategies'] = len(high_sharpe)
        stats['high_sharpe_percentage'] = len(high_sharpe) / len(results) * 100

        return stats

    def run_comprehensive_optimization(self,
                                     data_dict: Dict[str, VectorizedData],
                                     strategy_types: List[str] = None) -> Dict[str, OptimizationReport]:
        """
        運行全面優化（多策略類型）

        Args:
            data_dict: 向量化數據字典
            strategy_types: 策略類型列表

        Returns:
            優化報告字典
        """
        if strategy_types is None:
            strategy_types = ['rsi', 'macd', 'bollinger']

        comprehensive_results = {}

        for strategy_type in strategy_types:
            logger.info(f"Starting comprehensive optimization for {strategy_type}")

            config = self.create_optimization_config(
                strategy_type=strategy_type,
                use_gpu=self.gpu_engine.gpu_available,
                enable_parallel=True
            )

            try:
                report = self.optimize_multiple_sources(data_dict, config)
                comprehensive_results[strategy_type] = report

                logger.info(f"{strategy_type} optimization completed: Best Sharpe {report.best_strategy.metrics.get('sharpe_ratio', 0):.3f}")

            except Exception as e:
                logger.error(f"Comprehensive optimization failed for {strategy_type}: {e}")
                continue

        return comprehensive_results

    def cleanup(self):
        """清理資源"""
        if self.gpu_engine:
            self.gpu_engine.cleanup()

# 全局優化器實例
_parameter_optimizer = None

def get_gpu_parameter_optimizer() -> GPUParameterOptimizer:
    """獲取GPU參數優化器實例"""
    global _parameter_optimizer
    if _parameter_optimizer is None:
        _parameter_optimizer = GPUParameterOptimizer()
    return _parameter_optimizer