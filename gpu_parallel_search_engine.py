#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU並行參數搜索引擎
GPU Parallel Parameter Search Engine

專為0-300全參數範圍優化設計的高性能GPU並行搜索引擎
High-performance GPU parallel search engine designed for 0-300 full parameter range optimization
"""

import numpy as np
import pandas as pd
import time
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import concurrent.futures
from itertools import product
import json
from pathlib import Path

# GPU加速庫
try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    cp = None

# 導入核心模塊
from simplified_system.src.backtest.vectorbt_engine import VectorBTEngine, BacktestResult
from simplified_system.src.indicators.gpu_indicators import GPUTechnicalIndicators
from simplified_system.src.utils.gpu_detector import get_gpu_environment
from comprehensive_parameter_optimizer import OptimizationConfig, ParameterSpace

logger = logging.getLogger(__name__)

@dataclass
class GPUSearchConfig:
    """GPU搜索配置"""
    # GPU配置
    use_gpu: bool = True
    gpu_memory_fraction: float = 0.8  # GPU內存使用比例
    batch_multiplier: int = 4  # GPU批量大小的倍數

    # 並行配置
    max_cpu_workers: int = 16  # CPU工作線程數
    gpu_stream_count: int = 2  # GPU流數量

    # 搜索策略
    search_strategy: str = "hybrid"  # "grid", "random", "genetic", "hybrid"
    random_samples_ratio: float = 0.3  # 隨機採樣比例
    genetic_population_size: int = 100  # 遺傳算法種群大小
    genetic_generations: int = 10  # 遺傳算法代數

    # 性能優化
    enable_caching: bool = True
    cache_size: int = 10000
    enable_early_stopping: bool = True
    performance_threshold: float = 2.0  # Sharpe閾值

class GPUParallelSearchEngine:
    """
    GPU並行參數搜索引擎

    實現高性能的大規模參數搜索，支持：
    - GPU批量計算加速
    - 多GPU並行處理
    - 智能搜索算法
    - 動態負載均衡
    - 內存優化管理
    """

    def __init__(self, config: Optional[GPUSearchConfig] = None):
        """
        初始化GPU並行搜索引擎

        Args:
            config: GPU搜索配置
        """
        self.config = config or GPUSearchConfig()

        # 初始化環境
        self.gpu_env = get_gpu_environment()
        self.use_gpu = self.config.use_gpu and self.gpu_env.is_gpu_available() and GPU_AVAILABLE

        # 初始化核心組件
        self.vectorbt_engine = VectorBTEngine(use_gpu=self.use_gpu)
        self.gpu_indicators = GPUTechnicalIndicators(use_gpu=self.use_gpu) if self.use_gpu else None

        # GPU緩存和流管理
        self.gpu_cache = {} if self.config.enable_caching else None
        self.gpu_streams = []

        # 性能統計
        self.search_stats = {
            'total_searches': 0,
            'total_combinations_tested': 0,
            'total_gpu_time': 0.0,
            'total_cpu_time': 0.0,
            'gpu_speedup': 0.0,
            'best_sharpe_found': 0.0
        }

        # 初始化GPU流
        if self.use_gpu:
            self._initialize_gpu_streams()

        logger.info(f"GPU Parallel Search Engine initialized")
        logger.info(f"GPU Available: {self.use_gpu}")
        logger.info(f"Search Strategy: {self.config.search_strategy}")

    def _initialize_gpu_streams(self) -> None:
        """初始化GPU流"""
        try:
            if GPU_AVAILABLE and self.use_gpu:
                for i in range(self.config.gpu_stream_count):
                    stream = cp.cuda.Stream()
                    self.gpu_streams.append(stream)
                logger.info(f"Initialized {len(self.gpu_streams)} GPU streams")
        except Exception as e:
            logger.warning(f"Failed to initialize GPU streams: {e}")
            self.use_gpu = False

    def hibor_rsi_grid_search(
        self,
        data: pd.DataFrame,
        government_data: Optional[pd.DataFrame] = None,
        max_combinations: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        HIBOR-RSI策略的GPU網格搜索

        Args:
            data: 股票數據
            government_data: 政府數據
            max_combinations: 最大組合數限制

        Returns:
            搜索結果
        """
        logger.info("Starting GPU-accelerated HIBOR-RSI grid search...")

        # 定義HIBOR-RSI參數空間
        rsi_period_range = list(range(1, 301))          # RSI週期: 1-300
        rsi_oversold_range = list(range(10, 50))         # RSI超賣: 10-49
        rsi_overbought_range = list(range(51, 95))       # RSI超買: 51-94

        total_combinations = (
            len(rsi_period_range) * len(rsi_oversold_range) * len(rsi_overbought_range)
        )

        logger.info(f"HIBOR-RSI parameter space: {total_combinations:,} combinations")

        if max_combinations and max_combinations < total_combinations:
            total_combinations = max_combinations

        # 選擇搜索策略
        if self.config.search_strategy == "grid":
            combinations = self._generate_grid_combinations(
                [rsi_period_range, rsi_oversold_range, rsi_overbought_range],
                max_combinations
            )
        elif self.config.search_strategy == "random":
            combinations = self._generate_random_combinations(
                [rsi_period_range, rsi_oversold_range, rsi_overbought_range],
                int(total_combinations * self.config.random_samples_ratio)
            )
        elif self.config.search_strategy == "genetic":
            combinations = self._genetic_algorithm_search(
                [rsi_period_range, rsi_oversold_range, rsi_overbought_range],
                data, "HIBOR_RSI"
            )
        else:  # hybrid
            grid_combinations = self._generate_grid_combinations(
                [rsi_period_range, rsi_oversold_range, rsi_overbought_range],
                max_combinations // 2 if max_combinations else total_combinations // 2
            )
            random_combinations = self._generate_random_combinations(
                [rsi_period_range, rsi_oversold_range, rsi_overbought_range],
                len(grid_combinations)
            )
            combinations = grid_combinations + random_combinations

        logger.info(f"Generated {len(combinations):,} parameter combinations for testing")

        # 執行GPU並行搜索
        return self._execute_gpu_parallel_search(
            combinations, data, government_data, "HIBOR_RSI"
        )

    def monetary_macd_grid_search(
        self,
        data: pd.DataFrame,
        government_data: Optional[pd.DataFrame] = None,
        max_combinations: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Monetary-MACD策略的GPU網格搜索

        Args:
            data: 股票數據
            government_data: 政府數據
            max_combinations: 最大組合數限制

        Returns:
            搜索結果
        """
        logger.info("Starting GPU-accelerated Monetary-MACD grid search...")

        # 定義Monetary-MACD參數空間
        macd_fast_range = list(range(5, 51))            # MACD快線: 5-50
        macd_slow_range = list(range(51, 301))          # MACD慢線: 51-300
        macd_signal_range = list(range(1, 31))          # MACD信號: 1-30

        total_combinations = (
            len(macd_fast_range) * len(macd_slow_range) * len(macd_signal_range)
        )

        logger.info(f"Monetary-MACD parameter space: {total_combinations:,} combinations")

        if max_combinations and max_combinations < total_combinations:
            total_combinations = max_combinations

        # 選擇搜索策略
        if self.config.search_strategy == "grid":
            combinations = self._generate_grid_combinations(
                [macd_fast_range, macd_slow_range, macd_signal_range],
                max_combinations
            )
        elif self.config.search_strategy == "random":
            combinations = self._generate_random_combinations(
                [macd_fast_range, macd_slow_range, macd_signal_range],
                int(total_combinations * self.config.random_samples_ratio)
            )
        elif self.config.search_strategy == "genetic":
            combinations = self._genetic_algorithm_search(
                [macd_fast_range, macd_slow_range, macd_signal_range],
                data, "MONETARY_MACD"
            )
        else:  # hybrid
            grid_combinations = self._generate_grid_combinations(
                [macd_fast_range, macd_slow_range, macd_signal_range],
                max_combinations // 2 if max_combinations else total_combinations // 2
            )
            random_combinations = self._generate_random_combinations(
                [macd_fast_range, macd_slow_range, macd_signal_range],
                len(grid_combinations)
            )
            combinations = grid_combinations + random_combinations

        logger.info(f"Generated {len(combinations):,} parameter combinations for testing")

        # 執行GPU並行搜索
        return self._execute_gpu_parallel_search(
            combinations, data, government_data, "MONETARY_MACD"
        )

    def _generate_grid_combinations(
        self,
        param_ranges: List[List[int]],
        max_combinations: Optional[int]
    ) -> List[Dict[str, int]]:
        """生成網格搜索組合"""
        combinations = []
        param_names = ['param1', 'param2', 'param3']  # 通用名稱，將在具體策略中重新映射

        for combo in product(*param_ranges):
            params = dict(zip(param_names, combo))

            # 驗證參數有效性
            if self._validate_hibor_rsi_params(params) or self._validate_monetary_macd_params(params):
                combinations.append(params)

            if max_combinations and len(combinations) >= max_combinations:
                break

        return combinations

    def _generate_random_combinations(
        self,
        param_ranges: List[List[int]],
        num_samples: int
    ) -> List[Dict[str, int]]:
        """生成隨機採樣組合"""
        import random

        combinations = []
        param_names = ['param1', 'param2', 'param3']

        for _ in range(num_samples):
            # 隨機選擇參數
            params = {
                'param1': random.choice(param_ranges[0]),
                'param2': random.choice(param_ranges[1]),
                'param3': random.choice(param_ranges[2])
            }

            # 驗證參數有效性
            if self._validate_hibor_rsi_params(params) or self._validate_monetary_macd_params(params):
                combinations.append(params)

        return combinations

    def _genetic_algorithm_search(
        self,
        param_ranges: List[List[int]],
        data: pd.DataFrame,
        strategy_type: str
    ) -> List[Dict[str, int]]:
        """遺傳算法搜索"""
        logger.info(f"Running genetic algorithm search for {strategy_type}")

        # 初始化種群
        population_size = min(self.config.genetic_population_size, 1000)
        population = self._initialize_genetic_population(param_ranges, population_size)

        best_individuals = []

        for generation in range(self.config.genetic_generations):
            logger.info(f"Genetic algorithm generation {generation + 1}/{self.config.genetic_generations}")

            # 評估種群適應度
            fitness_scores = self._evaluate_population_fitness(population, data, strategy_type)

            # 選擇最佳個體
            sorted_population = [x for _, x in sorted(zip(fitness_scores, population), key=lambda x: x[0], reverse=True)]

            # 保留精英個體
            elite_size = population_size // 10
            best_individuals.extend(sorted_population[:elite_size])

            # 生成新一代
            if generation < self.config.genetic_generations - 1:
                population = self._generate_next_generation(sorted_population, param_ranges, population_size)

        return best_individuals

    def _initialize_genetic_population(
        self,
        param_ranges: List[List[int]],
        size: int
    ) -> List[Dict[str, int]]:
        """初始化遺傳算法種群"""
        import random

        population = []
        param_names = ['param1', 'param2', 'param3']

        while len(population) < size:
            params = {
                'param1': random.choice(param_ranges[0]),
                'param2': random.choice(param_ranges[1]),
                'param3': random.choice(param_ranges[2])
            }

            # 驗證參數有效性
            if self._validate_hibor_rsi_params(params) or self._validate_monetary_macd_params(params):
                population.append(params)

        return population

    def _evaluate_population_fitness(
        self,
        population: List[Dict[str, int]],
        data: pd.DataFrame,
        strategy_type: str
    ) -> List[float]:
        """評估種群適應度"""
        fitness_scores = []

        # 分批評估以提高效率
        batch_size = min(100, len(population))

        for i in range(0, len(population), batch_size):
            batch = population[i:i + batch_size]
            batch_results = self._evaluate_parameter_batch(batch, data, strategy_type)

            for params, fitness in zip(batch, batch_results):
                fitness_scores.append(fitness)

        return fitness_scores

    def _evaluate_parameter_batch(
        self,
        batch: List[Dict[str, int]],
        data: pd.DataFrame,
        strategy_type: str
    ) -> List[float]:
        """評估參數批次的適應度"""
        fitness_scores = []

        for params in batch:
            try:
                # 轉換參數格式
                if strategy_type == "HIBOR_RSI":
                    strategy_params = {
                        'period': params['param1'],
                        'oversold': params['param2'],
                        'overbought': params['param3']
                    }
                else:  # MONETARY_MACD
                    strategy_params = {
                        'fast': params['param1'],
                        'slow': params['param2'],
                        'signal': params['param3']
                    }

                # 執行回測
                result = self.vectorbt_engine.backtest_strategy(
                    data=data,
                    strategy="RSI_MEAN_REVERSION" if strategy_type == "HIBOR_RSI" else "MACD_CROSSOVER",
                    parameters=strategy_params,
                    symbol="0700.HK"
                )

                # 計算適應度（使用Sharpe比率）
                fitness = result.sharpe_ratio
                fitness_scores.append(fitness)

            except Exception as e:
                logger.warning(f"Failed to evaluate parameters {params}: {e}")
                fitness_scores.append(-float('inf'))

        return fitness_scores

    def _generate_next_generation(
        self,
        sorted_population: List[Dict[str, int]],
        param_ranges: List[List[int]],
        size: int
    ) -> List[Dict[str, int]]:
        """生成下一代種群"""
        import random

        next_generation = []

        # 精英保留
        elite_size = size // 10
        next_generation.extend(sorted_population[:elite_size])

        # 交叉和變異
        while len(next_generation) < size:
            # 選擇父母
            parent1, parent2 = random.sample(sorted_population[:size//2], 2)

            # 交叉
            child = self._crossover(parent1, parent2)

            # 變異
            child = self._mutate(child, param_ranges)

            # 驗證有效性
            if self._validate_hibor_rsi_params(child) or self._validate_monetary_macd_params(child):
                next_generation.append(child)

        return next_generation[:size]

    def _crossover(self, parent1: Dict[str, int], parent2: Dict[str, int]) -> Dict[str, int]:
        """交叉操作"""
        import random
        child = {}
        for key in parent1.keys():
            child[key] = parent1[key] if random.random() < 0.5 else parent2[key]
        return child

    def _mutate(self, individual: Dict[str, int], param_ranges: List[List[int]]) -> Dict[str, int]:
        """變異操作"""
        import random

        mutated = individual.copy()
        param_names = list(individual.keys())

        # 隨機選擇一個參數進行變異
        if random.random() < 0.3:  # 30%的變異概率
            param_idx = random.randint(0, len(param_names) - 1)
            param_name = param_names[param_idx]
            mutated[param_name] = random.choice(param_ranges[param_idx])

        return mutated

    def _execute_gpu_parallel_search(
        self,
        combinations: List[Dict[str, int]],
        data: pd.DataFrame,
        government_data: Optional[pd.DataFrame],
        strategy_type: str
    ) -> Dict[str, Any]:
        """執行GPU並行搜索"""
        logger.info(f"Executing GPU parallel search for {len(combinations):,} combinations")

        start_time = time.time()
        results = []

        if self.use_gpu and len(combinations) > 1000:
            # 使用GPU加速的大批量處理
            results = self._gpu_batch_processing(combinations, data, strategy_type)
        else:
            # 使用CPU並行處理
            results = self._cpu_parallel_processing(combinations, data, strategy_type)

        search_time = time.time() - start_time

        # 分析結果
        if results:
            # 排序並提取最優結果
            results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
            top_results = results[:20]

            # 計算統計信息
            sharpe_values = [r['sharpe_ratio'] for r in results]
            performance_stats = {
                'total_tested': len(results),
                'sharpe_mean': np.mean(sharpe_values),
                'sharpe_std': np.std(sharpe_values),
                'sharpe_max': np.max(sharpe_values),
                'sharpe_min': np.min(sharpe_values),
                'success_rate': len([r for r in results if r['sharpe_ratio'] > 1.0]) / len(results)
            }

            # 更新統計
            self._update_search_stats(len(combinations), search_time, np.max(sharpe_values))

            return {
                'strategy_type': strategy_type,
                'total_combinations': len(combinations),
                'successful_combinations': len(results),
                'search_time': search_time,
                'search_speed': len(results) / search_time,
                'top_results': top_results,
                'performance_statistics': performance_stats,
                'gpu_acceleration': self.use_gpu
            }
        else:
            return {
                'strategy_type': strategy_type,
                'total_combinations': len(combinations),
                'successful_combinations': 0,
                'search_time': search_time,
                'error': 'No successful combinations found'
            }

    def _gpu_batch_processing(
        self,
        combinations: List[Dict[str, int]],
        data: pd.DataFrame,
        strategy_type: str
    ) -> List[Dict[str, Any]]:
        """GPU批量處理"""
        logger.info("Using GPU batch processing for parameter evaluation")

        results = []
        batch_size = self.config.batch_multiplier * 1000  # 動態批量大小

        # 準備GPU數據
        prices_gpu = None
        if self.use_gpu and GPU_AVAILABLE:
            prices_gpu = cp.asarray(data['close'].values.astype(np.float32))

        for batch_start in range(0, len(combinations), batch_size):
            batch_end = min(batch_start + batch_size, len(combinations))
            batch_combinations = combinations[batch_start:batch_end]

            logger.info(f"Processing GPU batch {batch_start//batch_size + 1}: {len(batch_combinations)} combinations")

            # 並行處理批次
            batch_results = self._process_gpu_batch(batch_combinations, data, prices_gpu, strategy_type)
            results.extend(batch_results)

            # 早停檢查
            if self.config.enable_early_stopping and results:
                best_sharpe = max(r['sharpe_ratio'] for r in results)
                if best_sharpe > self.config.performance_threshold:
                    logger.info(f"Early stopping triggered with Sharpe {best_sharpe:.3f}")
                    break

        return results

    def _process_gpu_batch(
        self,
        batch_combinations: List[Dict[str, int]],
        data: pd.DataFrame,
        prices_gpu: Any,
        strategy_type: str
    ) -> List[Dict[str, Any]]:
        """處理GPU批次"""
        batch_results = []

        # 使用線程池並行處理
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_cpu_workers) as executor:
            # 提交任務
            future_to_params = {}

            for params in batch_combinations:
                if strategy_type == "HIBOR_RSI":
                    future = executor.submit(self._test_hibor_rsi_gpu, params, data, prices_gpu)
                else:
                    future = executor.submit(self._test_monetary_macd_gpu, params, data, prices_gpu)

                future_to_params[future] = params

            # 收集結果
            for future in concurrent.futures.as_completed(future_to_params):
                params = future_to_params[future]
                try:
                    result = future.result()
                    if result:
                        batch_results.append(result)
                except Exception as e:
                    logger.warning(f"GPU batch processing failed for {params}: {e}")
                    continue

        return batch_results

    def _test_hibor_rsi_gpu(
        self,
        params: Dict[str, int],
        data: pd.DataFrame,
        prices_gpu: Any
    ) -> Optional[Dict[str, Any]]:
        """GPU測試HIBOR-RSI參數組合"""
        try:
            # 轉換參數
            period = params['param1']
            oversold = params['param2']
            overbought = params['param3']

            # 檢查緩存
            cache_key = f"rsi_{period}_{oversold}_{overbought}"
            if self.gpu_cache and cache_key in self.gpu_cache:
                return self.gpu_cache[cache_key]

            # 使用VectorBT回測（已經是GPU加速的）
            strategy_params = {
                'period': period,
                'oversold': oversold,
                'overbought': overbought
            }

            result = self.vectorbt_engine.backtest_strategy(
                data=data,
                strategy="RSI_MEAN_REVERSION",
                parameters=strategy_params,
                symbol="0700.HK"
            )

            # 構建結果
            backtest_result = {
                'parameters': strategy_params,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'win_rate': result.win_rate,
                'total_return': result.total_return,
                'calmar_ratio': result.calmar_ratio,
                'total_trades': result.total_trades
            }

            # 緩存結果
            if self.gpu_cache and len(self.gpu_cache) < self.config.cache_size:
                self.gpu_cache[cache_key] = backtest_result

            return backtest_result

        except Exception as e:
            logger.warning(f"GPU HIBOR-RSI test failed for {params}: {e}")
            return None

    def _test_monetary_macd_gpu(
        self,
        params: Dict[str, int],
        data: pd.DataFrame,
        prices_gpu: Any
    ) -> Optional[Dict[str, Any]]:
        """GPU測試Monetary-MACD參數組合"""
        try:
            # 轉換參數
            fast = params['param1']
            slow = params['param2']
            signal = params['param3']

            # 檢查緩存
            cache_key = f"macd_{fast}_{slow}_{signal}"
            if self.gpu_cache and cache_key in self.gpu_cache:
                return self.gpu_cache[cache_key]

            # 使用VectorBT回測（已經是GPU加速的）
            strategy_params = {
                'fast': fast,
                'slow': slow,
                'signal': signal
            }

            result = self.vectorbt_engine.backtest_strategy(
                data=data,
                strategy="MACD_CROSSOVER",
                parameters=strategy_params,
                symbol="0700.HK"
            )

            # 構建結果
            backtest_result = {
                'parameters': strategy_params,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'win_rate': result.win_rate,
                'total_return': result.total_return,
                'calmar_ratio': result.calmar_ratio,
                'total_trades': result.total_trades
            }

            # 緩存結果
            if self.gpu_cache and len(self.gpu_cache) < self.config.cache_size:
                self.gpu_cache[cache_key] = backtest_result

            return backtest_result

        except Exception as e:
            logger.warning(f"GPU Monetary-MACD test failed for {params}: {e}")
            return None

    def _cpu_parallel_processing(
        self,
        combinations: List[Dict[str, int]],
        data: pd.DataFrame,
        strategy_type: str
    ) -> List[Dict[str, Any]]:
        """CPU並行處理（回退方案）"""
        logger.info("Using CPU parallel processing")

        results = []
        batch_size = 100

        for batch_start in range(0, len(combinations), batch_size):
            batch_end = min(batch_start + batch_size, len(combinations))
            batch_combinations = combinations[batch_start:batch_end]

            # 並行處理批次
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_cpu_workers) as executor:
                future_to_params = {}

                for params in batch_combinations:
                    if strategy_type == "HIBOR_RSI":
                        future = executor.submit(self._test_hibor_rsi_gpu, params, data, None)
                    else:
                        future = executor.submit(self._test_monetary_macd_gpu, params, data, None)

                    future_to_params[future] = params

                for future in concurrent.futures.as_completed(future_to_params):
                    params = future_to_params[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                    except Exception as e:
                        logger.warning(f"CPU processing failed for {params}: {e}")
                        continue

        return results

    def _validate_hibor_rsi_params(self, params: Dict[str, int]) -> bool:
        """驗證HIBOR-RSI參數"""
        period = params.get('param1', 14)
        oversold = params.get('param2', 30)
        overbought = params.get('param3', 70)

        return (
            1 <= period <= 300 and
            10 <= oversold <= 49 and
            51 <= overbought <= 94 and
            oversold < overbought
        )

    def _validate_monetary_macd_params(self, params: Dict[str, int]) -> bool:
        """驗證Monetary-MACD參數"""
        fast = params.get('param1', 12)
        slow = params.get('param2', 26)
        signal = params.get('param3', 9)

        return (
            5 <= fast <= 50 and
            51 <= slow <= 300 and
            1 <= signal <= 30 and
            fast < slow
        )

    def _update_search_stats(self, combinations_tested: int, search_time: float, best_sharpe: float) -> None:
        """更新搜索統計"""
        self.search_stats['total_searches'] += 1
        self.search_stats['total_combinations_tested'] += combinations_tested

        if self.use_gpu:
            self.search_stats['total_gpu_time'] += search_time
        else:
            self.search_stats['total_cpu_time'] += search_time

        self.search_stats['best_sharpe_found'] = max(self.search_stats['best_sharpe_found'], best_sharpe)

        # 計算GPU加速比
        if self.search_stats['total_cpu_time'] > 0 and self.search_stats['total_gpu_time'] > 0:
            self.search_stats['gpu_speedup'] = self.search_stats['total_cpu_time'] / self.search_stats['total_gpu_time']

    def get_search_performance_report(self) -> Dict[str, Any]:
        """獲取搜索性能報告"""
        return {
            'search_statistics': self.search_stats,
            'gpu_environment': self.gpu_env.get_system_info(),
            'configuration': {
                'use_gpu': self.use_gpu,
                'search_strategy': self.config.search_strategy,
                'max_cpu_workers': self.config.max_cpu_workers,
                'batch_multiplier': self.config.batch_multiplier,
                'enable_caching': self.config.enable_caching,
                'cache_size': len(self.gpu_cache) if self.gpu_cache else 0
            }
        }

    def save_search_results(self, results: Dict[str, Any], filename: str) -> None:
        """保存搜索結果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"gpu_search_results_{filename}_{timestamp}.json"

        # 添加性能報告
        results['performance_report'] = self.get_search_performance_report()

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Search results saved to: {output_file}")

# 便利函數
def run_gpu_parallel_search(
    symbol: str = "0700.HK",
    data_period: int = 365,
    max_combinations: Optional[int] = 10000,
    search_strategy: str = "hybrid"
) -> Dict[str, Any]:
    """
    運行GPU並行參數搜索

    Args:
        symbol: 股票代碼
        data_period: 數據天數
        max_combinations: 最大組合數
        search_strategy: 搜索策略

    Returns:
        搜索結果
    """
    # 配置GPU搜索引擎
    config = GPUSearchConfig(
        use_gpu=True,
        search_strategy=search_strategy,
        max_cpu_workers=16,
        batch_multiplier=8,
        enable_early_stopping=True,
        performance_threshold=2.0
    )

    engine = GPUParallelSearchEngine(config)

    # 獲取數據
    from simplified_system.src.api.stock_api import get_hk_stock_data
    data = get_hk_stock_data(symbol, data_period)

    all_results = {}

    # 運行HIBOR-RSI搜索
    logger.info("Starting HIBOR-RSI GPU parallel search...")
    hibor_rsi_results = engine.hibor_rsi_grid_search(data, max_combinations=max_combinations)
    all_results['HIBOR_RSI'] = hibor_rsi_results
    engine.save_search_results(hibor_rsi_results, "hibor_rsi")

    # 運行Monetary-MACD搜索
    logger.info("Starting Monetary-MACD GPU parallel search...")
    monetary_macd_results = engine.monetary_macd_grid_search(data, max_combinations=max_combinations)
    all_results['MONETARY_MACD'] = monetary_macd_results
    engine.save_search_results(monetary_macd_results, "monetary_macd")

    # 生成性能報告
    performance_report = engine.get_search_performance_report()

    # 保存總結果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_file = f"gpu_parallel_search_summary_{timestamp}.json"

    summary_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'symbol': symbol,
        'data_period': data_period,
        'max_combinations': max_combinations,
        'search_strategy': search_strategy,
        'results': all_results,
        'performance_report': performance_report
    }

    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    logger.info(f"GPU parallel search completed! Summary saved to: {summary_file}")

    return all_results

if __name__ == "__main__":
    # 運行GPU並行搜索示例
    print("開始0700.HK GPU並行參數搜索...")
    results = run_gpu_parallel_search(
        symbol="0700.HK",
        data_period=365,
        max_combinations=5000,
        search_strategy="hybrid"
    )

    for strategy, result in results.items():
        print(f"\n{strategy} 搜索結果:")
        if result.get('top_results'):
            best = result['top_results'][0]
            print(f"  最佳Sharpe: {best['sharpe_ratio']:.3f}")
            print(f"  最大回撤: {best['max_drawdown']*100:.2f}%")
            print(f"  勝率: {best['win_rate']*100:.2f}%")
            print(f"  最佳參數: {best['parameters']}")
            print(f"  搜索速度: {result['search_speed']:.1f} 組合/秒")