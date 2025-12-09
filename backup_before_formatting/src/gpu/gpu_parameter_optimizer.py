#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU加速參數優化器 - 深度集成版本
GPU-Accelerated Parameter Optimizer - Deep Integration Version

提供高性能的GPU加速參數優化，支持大規模並行策略優化
Provides high-performance GPU-accelerated parameter optimization with large-scale parallel strategy optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional, Union, Callable
import time
import logging
import json
from datetime import datetime
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
from abc import ABC, abstractmethod
import pickle
import hashlib

# 導入我們的GPU指標引擎
from .gpu_accelerated_indicators import get_gpu_indicators, GPUAcceleratedIndicators, GPUIndicatorConfig
from ..performance.parallel_optimizer import global_parallel_optimizer

# 導入回測引擎
try:
    from simplified_system.src.backtest.vectorbt_engine import VectorBTEngine
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    VectorBTEngine = None

# 配置日誌
logger = logging.getLogger(__name__)

@dataclass
class OptimizationConfig:
    """優化配置"""
    # 基本配置
    max_workers: int = field(default_factory=lambda: min(mp.cpu_count(), 16))
    batch_size: int = 1000
    max_combinations: int = 50000

    # GPU配置
    gpu_enabled: bool = True
    gpu_batch_size: int = 10000
    gpu_memory_fraction: float = 0.8

    # 優化配置
    optimization_metric: str = "sharpe_ratio"
    minimize_metric: bool = False
    early_stopping: bool = True
    early_stopping_patience: int = 100

    # 並行配置
    use_multiprocessing: bool = True
    chunk_size: int = 100

    # 緩存配置
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1小時

@dataclass
class OptimizationResult:
    """優化結果"""
    strategy_name: str
    symbol: str

    # 最佳參數
    best_parameters: Dict[str, Any]
    best_score: float
    best_performance: Dict[str, float]

    # 統計信息
    total_combinations: int
    successful_combinations: int
    execution_time: float
    strategies_per_second: float

    # 性能統計
    performance_stats: Dict[str, Any]

    # 所有結果（可選）
    top_results: List[Dict[str, Any]] = field(default_factory=list)
    all_results: Optional[List[Dict[str, Any]]] = None

    # 元數據
    optimization_method: str = "GPU Accelerated"
    gpu_used: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class GPUParameterOptimizer:
    """
    GPU加速參數優化器

    核心特性：
    - 大規模並行參數優化
    - GPU加速技術指標計算
    - 智能批處理和內存管理
    - 多種優化算法支持
    - 實時性能監控
    """

    def __init__(self, config: Optional[OptimizationConfig] = None):
        """
        初始化GPU參數優化器

        Args:
            config: 優化配置
        """
        self.config = config or OptimizationConfig()

        # 初始化組件
        self.gpu_indicators = get_gpu_indicators(GPUIndicatorConfig(
            batch_size=self.config.gpu_batch_size,
            memory_limit=self.config.gpu_memory_fraction,
            precision="float32"
        ))

        self.vectorbt_engine = VectorBTEngine() if VECTORBT_AVAILABLE else None

        # 性能統計
        self.optimization_stats = {
            'total_optimizations': 0,
            'total_strategies_tested': 0,
            'total_execution_time': 0.0,
            'gpu_utilization': 0.0,
            'cache_hit_rate': 0.0
        }

        # 緩存系統
        self._result_cache = {}

        logger.info(f"GPU Parameter Optimizer initialized: gpu_enabled={self.config.gpu_enabled}, workers={self.config.max_workers}")

    def optimize_rsi_strategy(self, data: pd.DataFrame, symbol: str = "UNKNOWN",
                            param_ranges: Optional[Dict[str, List]] = None) -> OptimizationResult:
        """
        優化RSI策略參數

        Args:
            data: 價格數據
            symbol: 股票代碼
            param_ranges: 參數範圍

        Returns:
            優化結果
        """
        if param_ranges is None:
            param_ranges = {
                'period': list(range(5, 51)),           # 5-50
                'oversold': [20, 25, 30, 35, 40],      # 超賣水平
                'overbought': [60, 65, 70, 75, 80]     # 超買水平
            }

        logger.info(f"Starting RSI optimization for {symbol}")
        start_time = time.time()

        # 生成參數組合
        param_combinations = self._generate_parameter_combinations(param_ranges)
        logger.info(f"Generated {len(param_combinations)} RSI parameter combinations")

        # 執行優化
        results = self._execute_parameter_optimization(
            data, symbol, "RSI_MEAN_REVERSION", param_combinations
        )

        execution_time = time.time() - start_time

        # 創建結果對象
        optimization_result = self._create_optimization_result(
            "RSI_MEAN_REVERSION", symbol, results, execution_time
        )

        # 更新統計信息
        self._update_optimization_stats(optimization_result)

        logger.info(f"RSI optimization completed for {symbol}: {len(results)} combinations in {execution_time:.2f}s")
        return optimization_result

    def optimize_macd_strategy(self, data: pd.DataFrame, symbol: str = "UNKNOWN",
                             param_ranges: Optional[Dict[str, List]] = None) -> OptimizationResult:
        """
        優化MACD策略參數

        Args:
            data: 價格數據
            symbol: 股票代碼
            param_ranges: 參數範圍

        Returns:
            優化結果
        """
        if param_ranges is None:
            param_ranges = {
                'fast': list(range(5, 26)),              # 5-25
                'slow': list(range(26, 101)),            # 26-100
                'signal': list(range(5, 21))             # 5-20
            }

        logger.info(f"Starting MACD optimization for {symbol}")
        start_time = time.time()

        # 生成參數組合
        param_combinations = self._generate_parameter_combinations(param_ranges)

        # 限制MACD組合數量以避免過度計算
        if len(param_combinations) > self.config.max_combinations:
            param_combinations = param_combinations[:self.config.max_combinations]
            logger.info(f"Limited MACD combinations to {self.config.max_combinations}")

        logger.info(f"Generated {len(param_combinations)} MACD parameter combinations")

        # 執行優化
        results = self._execute_parameter_optimization(
            data, symbol, "MACD_CROSSOVER", param_combinations
        )

        execution_time = time.time() - start_time

        # 創建結果對象
        optimization_result = self._create_optimization_result(
            "MACD_CROSSOVER", symbol, results, execution_time
        )

        # 更新統計信息
        self._update_optimization_stats(optimization_result)

        logger.info(f"MACD optimization completed for {symbol}: {len(results)} combinations in {execution_time:.2f}s")
        return optimization_result

    def optimize_bollinger_strategy(self, data: pd.DataFrame, symbol: str = "UNKNOWN",
                                  param_ranges: Optional[Dict[str, List]] = None) -> OptimizationResult:
        """
        優化布林帶策略參數

        Args:
            data: 價格數據
            symbol: 股票代碼
            param_ranges: 參數範圍

        Returns:
            優化結果
        """
        if param_ranges is None:
            param_ranges = {
                'period': list(range(10, 51)),           # 10-50
                'std_dev': [1.5, 2.0, 2.5, 3.0]         # 標準差倍數
            }

        logger.info(f"Starting Bollinger Bands optimization for {symbol}")
        start_time = time.time()

        # 生成參數組合
        param_combinations = self._generate_parameter_combinations(param_ranges)
        logger.info(f"Generated {len(param_combinations)} Bollinger Bands parameter combinations")

        # 執行優化
        results = self._execute_parameter_optimization(
            data, symbol, "BOLLINGER_BANDS", param_combinations
        )

        execution_time = time.time() - start_time

        # 創建結果對象
        optimization_result = self._create_optimization_result(
            "BOLLINGER_BANDS", symbol, results, execution_time
        )

        # 更新統計信息
        self._update_optimization_stats(optimization_result)

        logger.info(f"Bollinger Bands optimization completed for {symbol}: {len(results)} combinations in {execution_time:.2f}s")
        return optimization_result

    def optimize_dual_strategy(self, data: pd.DataFrame, symbol: str = "UNKNOWN") -> OptimizationResult:
        """
        優化雙策略組合（RSI + MACD）

        Args:
            data: 價格數據
            symbol: 股票代碼

        Returns:
            優化結果
        """
        logger.info(f"Starting dual strategy optimization for {symbol}")
        start_time = time.time()

        # 分別優化兩個策略
        rsi_result = self.optimize_rsi_strategy(data, symbol)
        macd_result = self.optimize_macd_strategy(data, symbol)

        # 組合最佳參數
        dual_params = {
            'rsi_period': rsi_result.best_parameters.get('period', 14),
            'rsi_oversold': rsi_result.best_parameters.get('oversold', 30),
            'rsi_overbought': rsi_result.best_parameters.get('overbought', 70),
            'macd_fast': macd_result.best_parameters.get('fast', 12),
            'macd_slow': macd_result.best_parameters.get('slow', 26),
            'macd_signal': macd_result.best_parameters.get('signal', 9)
        }

        # 測試雙策略
        dual_performance = self._test_dual_strategy(data, dual_params, symbol)

        execution_time = time.time() - start_time

        # 創建結果對象
        optimization_result = OptimizationResult(
            strategy_name="RSI_MACD_DUAL",
            symbol=symbol,
            best_parameters=dual_params,
            best_score=dual_performance[self.config.optimization_metric],
            best_performance=dual_performance,
            total_combinations=rsi_result.total_combinations + macd_result.total_combinations,
            successful_combinations=rsi_result.successful_combinations + macd_result.successful_combinations,
            execution_time=execution_time,
            strategies_per_second=(rsi_result.successful_combinations + macd_result.successful_combinations) / execution_time,
            performance_stats=self._get_current_performance_stats(),
            optimization_method="Dual Strategy GPU",
            gpu_used=self.gpu_indicators.available,
            timestamp=datetime.now().isoformat()
        )

        logger.info(f"Dual strategy optimization completed for {symbol} in {execution_time:.2f}s")
        return optimization_result

    def _generate_parameter_combinations(self, param_ranges: Dict[str, List]) -> List[Dict[str, Any]]:
        """生成參數組合"""
        import itertools

        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())

        combinations = list(itertools.product(*param_values))
        param_combinations = [dict(zip(param_names, combo)) for combo in combinations]

        return param_combinations

    def _execute_parameter_optimization(self, data: pd.DataFrame, symbol: str,
                                     strategy: str, param_combinations: List[Dict]) -> List[Dict]:
        """執行參數優化"""
        # 檢查緩存
        cache_key = self._generate_cache_key(data, strategy, param_combinations[:100])
        if self.config.enable_cache and cache_key in self._result_cache:
            logger.info(f"Using cached results for {strategy} optimization")
            return self._result_cache[cache_key]

        results = []
        total_combinations = len(param_combinations)

        if self.config.use_multiprocessing and total_combinations > self.config.chunk_size:
            results = self._parallel_optimization(data, symbol, strategy, param_combinations)
        else:
            results = self._sequential_optimization(data, symbol, strategy, param_combinations)

        # 緩存結果
        if self.config.enable_cache:
            self._result_cache[cache_key] = results

        return results

    def _parallel_optimization(self, data: pd.DataFrame, symbol: str,
                              strategy: str, param_combinations: List[Dict]) -> List[Dict]:
        """並行優化"""
        results = []
        chunk_size = self.config.chunk_size

        # 數據準備（避免重複處理）
        if self.config.gpu_enabled and self.gpu_indicators.available:
            # 預計算GPU指標
            self._precompute_gpu_indicators(data, strategy)

        # 分塊處理
        with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = []

            for i in range(0, len(param_combinations), chunk_size):
                chunk = param_combinations[i:i + chunk_size]
                future = executor.submit(self._process_parameter_chunk, data, symbol, strategy, chunk)
                futures.append(future)

            # 收集結果
            for future in as_completed(futures):
                try:
                    chunk_results = future.result()
                    results.extend(chunk_results)
                except Exception as e:
                    logger.warning(f"Parallel optimization chunk failed: {e}")

        return results

    def _sequential_optimization(self, data: pd.DataFrame, symbol: str,
                                strategy: str, param_combinations: List[Dict]) -> List[Dict]:
        """順序優化"""
        results = []

        # 數據準備
        if self.config.gpu_enabled and self.gpu_indicators.available:
            self._precompute_gpu_indicators(data, strategy)

        # 批量處理
        batch_size = self.config.batch_size

        for i in range(0, len(param_combinations), batch_size):
            batch = param_combinations[i:i + batch_size]
            batch_results = self._process_parameter_chunk(data, symbol, strategy, batch)
            results.extend(batch_results)

            # 進度報告
            if (i // batch_size + 1) % 10 == 0:
                logger.info(f"Processed {min(i + batch_size, len(param_combinations))}/{len(param_combinations)} combinations")

        return results

    def _precompute_gpu_indicators(self, data: pd.DataFrame, strategy: str):
        """預計算GPU指標"""
        prices = data['close']

        try:
            if strategy == "RSI_MEAN_REVERSION":
                # 預計算所有可能的RSI週期
                periods = list(range(5, 51))
                self._precomputed_rsi = self.gpu_indicators.calculate_rsi_batch_gpu(prices, periods)

            elif strategy == "MACD_CROSSOVER":
                # 預計算所有可能的MACD參數組合
                fast_periods = list(range(5, 26))
                slow_periods = list(range(26, 51))  # 限制範圍以節省內存
                signal_periods = list(range(5, 21))
                self._precomputed_macd = self.gpu_indicators.calculate_macd_batch_gpu(
                    prices, fast_periods, slow_periods, signal_periods
                )

            elif strategy == "BOLLINGER_BANDS":
                # 預計算布林帶
                periods = list(range(10, 51))
                std_devs = [1.5, 2.0, 2.5, 3.0]
                self._precomputed_bb = self.gpu_indicators.calculate_bollinger_bands_gpu(
                    prices, periods, std_devs
                )

            logger.info(f"GPU indicators precomputed for {strategy}")

        except Exception as e:
            logger.warning(f"GPU precomputation failed for {strategy}: {e}")

    def _process_parameter_chunk(self, data: pd.DataFrame, symbol: str,
                               strategy: str, param_chunk: List[Dict]) -> List[Dict]:
        """處理參數塊"""
        chunk_results = []

        for params in param_chunk:
            try:
                # 使用預計算的指標（如果可用）
                result = self._evaluate_single_strategy(data, symbol, strategy, params)
                if result is not None:
                    chunk_results.append(result)

            except Exception as e:
                logger.warning(f"Strategy evaluation failed for {params}: {e}")
                continue

        return chunk_results

    def _evaluate_single_strategy(self, data: pd.DataFrame, symbol: str,
                                strategy: str, params: Dict) -> Optional[Dict]:
        """評估單個策略"""
        try:
            if self.vectorbt_engine is not None:
                # 使用VectorBT回測
                result = self.vectorbt_engine.backtest_strategy(data, strategy, params, symbol)

                return {
                    'parameters': params,
                    'total_return': result.total_return,
                    'sharpe_ratio': result.sharpe_ratio,
                    'max_drawdown': result.max_drawdown,
                    'win_rate': result.win_rate,
                    'profit_factor': result.profit_factor,
                    'total_trades': result.total_trades,
                    'annual_return': result.annual_return,
                    'execution_time': result.execution_time,
                    'success': True
                }
            else:
                # 使用簡化回測
                return self._simple_backtest(data, strategy, params)

        except Exception as e:
            logger.warning(f"Strategy evaluation error: {e}")
            return None

    def _simple_backtest(self, data: pd.DataFrame, strategy: str, params: Dict) -> Dict:
        """簡化回測實現"""
        prices = data['close']
        returns = prices.pct_change().dropna()

        # 生成信號
        signals = np.zeros(len(returns))

        if strategy == "RSI_MEAN_REVERSION":
            # 使用預計算的RSI（如果可用）
            if hasattr(self, '_precomputed_rsi') and params['period'] in self._precomputed_rsi:
                rsi = self._precomputed_rsi[params['period']]
            else:
                rsi = self.gpu_indicators.calculate_rsi_batch_gpu(prices, [params['period']])[params['period']]

            buy_signals = rsi[:-1] < params['oversold']
            sell_signals = rsi[:-1] > params['overbought']
            signals[buy_signals] = 1
            signals[sell_signals] = -1

        elif strategy == "MACD_CROSSOVER":
            # 使用預計算的MACD（如果可用）
            macd_key = f"MACD_{params['fast']}_{params['slow']}_{params['signal']}"
            if hasattr(self, '_precomputed_macd') and macd_key in self._precomputed_macd:
                macd_data = self._precomputed_macd[macd_key]
                macd = macd_data['MACD']
                signal = macd_data['SIGNAL']
            else:
                macd_data = self.gpu_indicators.calculate_macd_batch_gpu(
                    prices, [params['fast']], [params['slow']], [params['signal']]
                )
                macd = macd_data[f"MACD_{params['fast']}_{params['slow']}_{params['signal']}"]['MACD']
                signal = macd_data[f"MACD_{params['fast']}_{params['slow']}_{params['signal']}"]['SIGNAL']

            golden_cross = (macd > signal) & (np.roll(macd, 1) <= np.roll(signal, 1))
            death_cross = (macd < signal) & (np.roll(macd, 1) >= np.roll(signal, 1))
            signals[golden_cross] = 1
            signals[death_cross] = -1

        # 計算策略回報
        strategy_returns = signals * returns

        # 計算性能指標
        total_return = np.prod(1 + strategy_returns) - 1
        annual_return = (1 + total_return) ** (252 / len(strategy_returns)) - 1

        if len(strategy_returns) > 0 and strategy_returns.std() > 0:
            sharpe_ratio = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0

        # 最大回撤
        cumulative = np.cumprod(1 + strategy_returns)
        rolling_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - rolling_max) / rolling_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

        return {
            'parameters': params,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'annual_return': annual_return,
            'win_rate': 0.5,  # 簡化計算
            'profit_factor': 1.0,  # 簡化計算
            'total_trades': int(np.sum(np.abs(np.diff(signals)) > 0)),
            'execution_time': 0.0,
            'success': True
        }

    def _test_dual_strategy(self, data: pd.DataFrame, params: Dict, symbol: str) -> Dict[str, float]:
        """測試雙策略"""
        # 生成RSI和MACD信號
        prices = data['close']
        returns = prices.pct_change().dropna()

        # RSI信號
        rsi_periods = [params['rsi_period']]
        rsi_results = self.gpu_indicators.calculate_rsi_batch_gpu(prices, rsi_periods)
        rsi = rsi_results[params['rsi_period']]

        # MACD信號
        macd_results = self.gpu_indicators.calculate_macd_batch_gpu(
            prices, [params['macd_fast']], [params['macd_slow']], [params['macd_signal']]
        )
        macd_key = f"MACD_{params['macd_fast']}_{params['macd_slow']}_{params['macd_signal']}"
        macd_data = macd_results[macd_key]
        macd = macd_data['MACD']
        signal = macd_data['SIGNAL']

        # 組合信號
        rsi_buy = rsi[:-1] < params['rsi_oversold']
        rsi_sell = rsi[:-1] > params['rsi_overbought']

        macd_golden = (macd > signal) & (np.roll(macd, 1) <= np.roll(signal, 1))
        macd_death = (macd < signal) & (np.roll(macd, 1) >= np.roll(signal, 1))

        # 雙信號確認（AND邏輯）
        buy_signals = rsi_buy & macd_golden
        sell_signals = rsi_sell & macd_death

        signals = np.zeros(len(returns))
        signals[buy_signals] = 1
        signals[sell_signals] = -1

        # 計算策略回報和性能指標
        strategy_returns = signals * returns

        total_return = np.prod(1 + strategy_returns) - 1
        annual_return = (1 + total_return) ** (252 / len(strategy_returns)) - 1

        if len(strategy_returns) > 0 and strategy_returns.std() > 0:
            sharpe_ratio = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0

        # 最大回撤
        cumulative = np.cumprod(1 + strategy_returns)
        rolling_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - rolling_max) / rolling_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'annual_return': annual_return,
            'win_rate': 0.5,
            'profit_factor': 1.0,
            'total_trades': int(np.sum(np.abs(np.diff(signals)) > 0))
        }

    def _create_optimization_result(self, strategy: str, symbol: str,
                                  results: List[Dict], execution_time: float) -> OptimizationResult:
        """創建優化結果對象"""
        if not results:
            # 創建空結果
            return OptimizationResult(
                strategy_name=strategy,
                symbol=symbol,
                best_parameters={},
                best_score=0.0,
                best_performance={},
                total_combinations=0,
                successful_combinations=0,
                execution_time=execution_time,
                strategies_per_second=0.0,
                performance_stats=self._get_current_performance_stats(),
                gpu_used=self.gpu_indicators.available
            )

        # 排序結果
        if self.config.minimize_metric:
            results.sort(key=lambda x: x.get(self.config.optimization_metric, float('inf')))
        else:
            results.sort(key=lambda x: x.get(self.config.optimization_metric, -float('inf')), reverse=True)

        best_result = results[0]

        return OptimizationResult(
            strategy_name=strategy,
            symbol=symbol,
            best_parameters=best_result['parameters'],
            best_score=best_result[self.config.optimization_metric],
            best_performance=best_result,
            total_combinations=len(results),
            successful_combinations=len(results),
            execution_time=execution_time,
            strategies_per_second=len(results) / execution_time,
            performance_stats=self._get_current_performance_stats(),
            top_results=results[:10],
            all_results=results if len(results) <= 1000 else results[:1000],  # 限制存儲
            optimization_method="GPU Accelerated",
            gpu_used=self.gpu_indicators.available
        )

    def _get_current_performance_stats(self) -> Dict[str, Any]:
        """獲取當前性能統計"""
        gpu_stats = self.gpu_indicators.get_performance_stats()

        return {
            'gpu_backend': gpu_stats['backend'],
            'gpu_available': gpu_stats['gpu_available'],
            'gpu_utilization': gpu_stats['gpu_utilization'],
            'total_gpu_operations': gpu_stats['total_operations'],
            'cache_hit_rate': gpu_stats['cache_hit_rate']
        }

    def _update_optimization_stats(self, result: OptimizationResult):
        """更新優化統計信息"""
        self.optimization_stats['total_optimizations'] += 1
        self.optimization_stats['total_strategies_tested'] += result.successful_combinations
        self.optimization_stats['total_execution_time'] += result.execution_time

        # 更新GPU利用率
        if self.optimization_stats['total_optimizations'] > 0:
            total_gpu = sum(1 for _ in [1] if result.gpu_used)
            self.optimization_stats['gpu_utilization'] = total_gpu / self.optimization_stats['total_optimizations']

    def _generate_cache_key(self, data: pd.DataFrame, strategy: str, sample_params: List[Dict]) -> str:
        """生成緩存鍵"""
        # 使用數據形狀和策略名稱
        data_hash = hashlib.md5(f"{data.shape}{strategy}".encode()).hexdigest()
        param_hash = hashlib.md5(str(sample_params[:10]).encode()).hexdigest()
        return f"{data_hash}_{param_hash}"

    def get_optimization_stats(self) -> Dict[str, Any]:
        """獲取優化統計信息"""
        return self.optimization_stats.copy()

    def clear_cache(self):
        """清除緩存"""
        self._result_cache.clear()
        logger.info("Optimization cache cleared")

# 全局優化器實例
_gpu_optimizer_instance = None

def get_gpu_optimizer(config: Optional[OptimizationConfig] = None) -> GPUParameterOptimizer:
    """獲取全局GPU優化器實例"""
    global _gpu_optimizer_instance
    if _gpu_optimizer_instance is None:
        _gpu_optimizer_instance = GPUParameterOptimizer(config)
    return _gpu_optimizer_instance

def reset_gpu_optimizer():
    """重置全局GPU優化器"""
    global _gpu_optimizer_instance
    _gpu_optimizer_instance = None