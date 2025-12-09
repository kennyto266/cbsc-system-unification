#!/usr / bin / env python3
"""
大規模並行參數優化引擎
Massive Parallel Parameter Optimization Engine

高性能並行處理系統，支持百萬級參數組合優化：
- 多進程 / 多線程支持 (目標32核並行)
- 工作負載均衡和任務調度
- 實時進度監控和狀態報告
- 結果緩存和持久化機制
- 並行效率優化 (>80%)
"""

import json
import logging
import os
import pickle
import threading
import time
import warnings
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from multiprocessing import Lock, Queue, cpu_count
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from .parameter_space import ParameterSpaceManager, StrategyParameterSpace

# 導入回測引擎
from .vectorbt_engine import BacktestResult, VectorBTEngine

logger = logging.getLogger(__name__)


@dataclass
class OptimizationTask:
    """優化任務定義"""

    task_id: str
    strategy_name: str
    parameters: Dict[str, Any]
    data: pd.DataFrame
    symbol: str
    priority: int = 1  # 任務優先級
    created_time: float = field(default_factory = time.time)


@dataclass
class OptimizationResult:
    """優化結果定義"""

    task_id: str
    strategy_name: str
    parameters: Dict[str, Any]
    backtest_result: Optional[BacktestResult] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    completed_time: float = field(default_factory = time.time)


@dataclass
class OptimizationConfig:
    """優化配置"""

    # 並行配置
    max_workers: int = cpu_count()  # 最大工作進程 / 線程數
    use_processes: bool = True  # 是否使用多進程 (True) 或多線程 (False)
    chunk_size: int = 10  # 每個工作單元的任務數量

    # 性能配置
    enable_gpu: bool = True  # 是否啟用GPU加速
    cache_results: bool = True  # 是否啟用結果緩存
    save_intermediate: bool = True  # 是否保存中間結果

    # 監控配置
    progress_update_interval: float = 5.0  # 進度更新間隔（秒）
    enable_detailed_logging: bool = False  # 是否啟用詳細日誌

    # 資源限制
    memory_limit_mb: Optional[int] = None  # 內存限制（MB）
    timeout_per_task: Optional[float] = None  # 每個任務超時時間（秒）

    # 輸出配置
    results_dir: str = "optimization_results"
    save_top_n: int = 100  # 保存前N個最佳結果


class ParallelOptimizer:
    """
    並行參數優化引擎

    提供高性能的並行參數優化能力：
    - 支持百萬級參數組合
    - 自動負載均衡
    - 實時進度監控
    - 結果緩存和持久化
    """

    def __init__(self, config: Optional[OptimizationConfig] = None):
        """
        初始化並行優化引擎

        Args:
            config: 優化配置
        """
        self.config = config or OptimizationConfig()
        self.parameter_space = ParameterSpaceManager()

        # 任務管理
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.completed_tasks = {}
        self.failed_tasks = {}

        # 進度監控
        self.total_tasks = 0
        self.completed_count = 0
        self.failed_count = 0
        self.start_time = None
        self.progress_lock = Lock()

        # 結果緩存
        self.results_cache = {}
        self.cache_file = os.path.join(
            self.config.results_dir, "optimization_cache.pkl"
        )

        # 統計信息
        self.stats = {
            "total_execution_time": 0.0,
            "average_task_time": 0.0,
            "tasks_per_second": 0.0,
            "parallel_efficiency": 0.0,
            "cache_hit_rate": 0.0,
        }

        # 創建結果目錄
        Path(self.config.results_dir).mkdir(parents = True, exist_ok = True)

        # 加載緩存
        if self.config.cache_results and os.path.exists(self.cache_file):
            self._load_cache()

        logger.info(
            f"Parallel optimizer initialized with {self.config.max_workers} workers"
        )

    def optimize_strategy(
        self,
        strategy_name: str,
        data: pd.DataFrame,
        symbol: str = "UNKNOWN",
        param_space: Optional[StrategyParameterSpace] = None,
        optimization_metric: str = "sharpe_ratio",
        max_combinations: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        單策略參數優化

        Args:
            strategy_name: 策略名稱
            data: OHLCV數據
            symbol: 股票代碼
            param_space: 參數空間定義
            optimization_metric: 優化目標指標
            max_combinations: 最大參數組合數

        Returns:
            優化結果
        """
        logger.info(f"Starting parallel optimization for {strategy_name} on {symbol}")

        self.start_time = time.time()

        # 獲取參數空間
        if param_space is None:
            param_space = self.parameter_space.get_strategy_space(strategy_name)

        if param_space is None:
            raise ValueError(f"Parameter space not found for strategy: {strategy_name}")

        # 生成參數組合
        if max_combinations:
            param_space.max_combinations = max_combinations

        parameter_combinations = param_space.generate_parameter_combinations()
        self.total_tasks = len(parameter_combinations)

        logger.info(f"Generated {self.total_tasks} parameter combinations")

        # 創建任務
        tasks = [
            OptimizationTask(
                task_id = f"{strategy_name}_{i}",
                strategy_name = strategy_name,
                parameters = params,
                data = data,
                symbol = symbol,
            )
            for i, params in enumerate(parameter_combinations)
        ]

        # 執行並行優化
        results = self._execute_parallel_tasks(tasks)

        # 分析結果
        analysis = self._analyze_results(results, optimization_metric)

        # 保存結果
        if self.config.save_intermediate:
            self._save_results(strategy_name, symbol, analysis)

        # 更新統計
        self._update_statistics()

        logger.info(
            f"Optimization completed for {strategy_name}. "
            f"Best {optimization_metric}: {analysis['best_metric']:.4f}"
        )

        return analysis

    def optimize_multiple_strategies(
        self,
        strategy_names: List[str],
        data: pd.DataFrame,
        symbol: str = "UNKNOWN",
        max_combinations_per_strategy: Optional[int] = None,
        optimization_metric: str = "sharpe_ratio",
    ) -> Dict[str, Dict[str, Any]]:
        """
        多策略並行優化

        Args:
            strategy_names: 策略名稱列表
            data: OHLCV數據
            symbol: 股票代碼
            max_combinations_per_strategy: 每個策略的最大組合數
            optimization_metric: 優化目標指標

        Returns:
            多策略優化結果
        """
        logger.info(
            f"Starting multi - strategy optimization for {len(strategy_names)} strategies"
        )

        self.start_time = time.time()

        # 生成所有策略的任務
        all_tasks = []
        strategy_task_map = {}

        for strategy_name in strategy_names:
            param_space = self.parameter_space.get_strategy_space(strategy_name)
            if param_space is None:
                logger.warning(
                    f"Parameter space not found for strategy: {strategy_name}"
                )
                continue

            if max_combinations_per_strategy:
                param_space.max_combinations = max_combinations_per_strategy

            parameter_combinations = param_space.generate_parameter_combinations()

            strategy_tasks = [
                OptimizationTask(
                    task_id = f"{strategy_name}_{i}",
                    strategy_name = strategy_name,
                    parameters = params,
                    data = data,
                    symbol = symbol,
                )
                for i, params in enumerate(parameter_combinations)
            ]

            all_tasks.extend(strategy_tasks)
            strategy_task_map[strategy_name] = len(strategy_tasks)

        self.total_tasks = len(all_tasks)
        logger.info(f"Generated {self.total_tasks} total tasks across all strategies")

        # 執行並行優化
        results = self._execute_parallel_tasks(all_tasks)

        # 按策略分析結果
        strategy_results = {}
        for strategy_name in strategy_names:
            strategy_results_list = [
                result
                for result in results
                if result.strategy_name == strategy_name
                and result.backtest_result is not None
            ]

            if strategy_results_list:
                analysis = self._analyze_results(
                    strategy_results_list, optimization_metric
                )
                strategy_results[strategy_name] = analysis
            else:
                strategy_results[strategy_name] = {
                    "strategy_name": strategy_name,
                    "symbol": symbol,
                    "total_combinations": 0,
                    "successful_combinations": 0,
                    "best_parameters": None,
                    "best_metric": float("-inf"),
                    "error": "No successful results",
                }

        # 保存結果
        if self.config.save_intermediate:
            self._save_multi_strategy_results(symbol, strategy_results)

        # 更新統計
        self._update_statistics()

        logger.info(f"Multi - strategy optimization completed for {symbol}")

        return strategy_results

    def _execute_parallel_tasks(
        self, tasks: List[OptimizationTask]
    ) -> List[OptimizationResult]:
        """執行並行任務"""
        results = []

        # 選擇執行器類型
        executor_class = (
            ProcessPoolExecutor if self.config.use_processes else ThreadPoolExecutor
        )

        # 設置進度監控線程
        progress_thread = threading.Thread(target = self._progress_monitor)
        progress_thread.daemon = True
        progress_thread.start()

        try:
            with executor_class(max_workers = self.config.max_workers) as executor:
                # 分批提交任務
                futures = []
                for i in range(0, len(tasks), self.config.chunk_size):
                    chunk = tasks[i : i + self.config.chunk_size]
                    for task in chunk:
                        future = executor.submit(self._execute_single_task, task)
                        futures.append(future)

                # 收集結果
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout = self.config.timeout_per_task)
                        results.append(result)

                        with self.progress_lock:
                            if result.backtest_result is not None:
                                self.completed_count += 1
                                self.completed_tasks[result.task_id] = result
                            else:
                                self.failed_count += 1
                                self.failed_tasks[result.task_id] = result

                    except Exception as e:
                        logger.error(f"Task execution failed: {e}")
                        with self.progress_lock:
                            self.failed_count += 1

        except Exception as e:
            logger.error(f"Parallel execution failed: {e}")

        # 等待進度監控線程結束
        progress_thread.join(timeout = 1.0)

        return results

    def _execute_single_task(self, task: OptimizationTask) -> OptimizationResult:
        """執行單個優化任務"""
        start_time = time.time()

        # 檢查緩存
        cache_key = self._get_cache_key(task.strategy_name, task.parameters)
        if self.config.cache_results and cache_key in self.results_cache:
            cached_result = self.results_cache[cache_key]
            return OptimizationResult(
                task_id = task.task_id,
                strategy_name = task.strategy_name,
                parameters = task.parameters,
                backtest_result = cached_result,
                execution_time = 0.0,  # 緩存命中不計算執行時間
                completed_time = time.time(),
            )

        try:
            # 創建回測引擎
            engine = VectorBTEngine(use_gpu = self.config.enable_gpu)

            # 執行回測
            backtest_result = engine.backtest_strategy(
                data = task.data,
                strategy = task.strategy_name,
                parameters = task.parameters,
                symbol = task.symbol,
            )

            execution_time = time.time() - start_time

            # 緩存結果
            if self.config.cache_results:
                self.results_cache[cache_key] = backtest_result

            return OptimizationResult(
                task_id = task.task_id,
                strategy_name = task.strategy_name,
                parameters = task.parameters,
                backtest_result = backtest_result,
                execution_time = execution_time,
                completed_time = time.time(),
            )

        except Exception as e:
            logger.warning(f"Task {task.task_id} failed: {e}")
            return OptimizationResult(
                task_id = task.task_id,
                strategy_name = task.strategy_name,
                parameters = task.parameters,
                error = str(e),
                execution_time = time.time() - start_time,
                completed_time = time.time(),
            )

    def _progress_monitor(self):
        """進度監控線程"""
        last_update = 0

        while True:
            current_time = time.time()
            time.sleep(1.0)

            if current_time - last_update >= self.config.progress_update_interval:
                with self.progress_lock:
                    total_processed = self.completed_count + self.failed_count
                    if self.total_tasks > 0:
                        progress_percent = (total_processed / self.total_tasks) * 100
                        elapsed_time = (
                            current_time - self.start_time if self.start_time else 0
                        )
                        rate = total_processed / elapsed_time if elapsed_time > 0 else 0

                        logger.info(
                            f"Progress: {total_processed}/{self.total_tasks} "
                            f"({progress_percent:.1f}%) | "
                            f"Completed: {self.completed_count} | "
                            f"Failed: {self.failed_count} | "
                            f"Rate: {rate:.1f} tasks / sec"
                        )

                        # 保存中間進度
                        if self.config.save_intermediate:
                            self._save_progress()

                    last_update = current_time

    def _analyze_results(
        self, results: List[OptimizationResult], optimization_metric: str
    ) -> Dict[str, Any]:
        """分析優化結果"""
        successful_results = [
            result for result in results if result.backtest_result is not None
        ]

        if not successful_results:
            return {
                "strategy_name": results[0].strategy_name if results else "UNKNOWN",
                "symbol": results[0].symbol if results else "UNKNOWN",
                "total_combinations": len(results),
                "successful_combinations": 0,
                "best_parameters": None,
                "best_metric": float("-inf"),
                "error": "No successful results",
                "all_results": [],
            }

        # 根據優化指標排序
        successful_results.sort(
            key = lambda r: getattr(r.backtest_result, optimization_metric, 0),
            reverse = True,
        )

        best_result = successful_results[0]
        best_metric = getattr(best_result.backtest_result, optimization_metric, 0)

        # 計算統計信息
        metric_values = [
            getattr(r.backtest_result, optimization_metric, 0)
            for r in successful_results
        ]

        execution_times = [r.execution_time for r in successful_results]

        analysis = {
            "strategy_name": best_result.strategy_name,
            "symbol": best_result.backtest_result.symbol,
            "total_combinations": len(results),
            "successful_combinations": len(successful_results),
            "best_parameters": best_result.parameters,
            "best_backtest_result": best_result.backtest_result.to_dict(),
            "best_metric": best_metric,
            "optimization_metric": optimization_metric,
            # 統計信息
            "performance_statistics": {
                "metric_mean": np.mean(metric_values),
                "metric_std": np.std(metric_values),
                "metric_min": np.min(metric_values),
                "metric_max": np.max(metric_values),
                "metric_median": np.median(metric_values),
                "execution_time_mean": np.mean(execution_times),
                "execution_time_std": np.std(execution_times),
            },
            # 前N個結果
            "top_results": [
                {
                    "rank": i + 1,
                    "parameters": result.parameters,
                    "metric": getattr(result.backtest_result, optimization_metric, 0),
                    "backtest_result": result.backtest_result.to_dict(),
                    "execution_time": result.execution_time,
                }
                for i, result in enumerate(successful_results[: self.config.save_top_n])
            ],
            # 元數據
            "analysis_time": datetime.now().isoformat(),
            "optimization_config": {
                "max_workers": self.config.max_workers,
                "use_processes": self.config.use_processes,
                "enable_gpu": self.config.enable_gpu,
            },
        }

        return analysis

    def _get_cache_key(self, strategy_name: str, parameters: Dict[str, Any]) -> str:
        """生成緩存鍵"""
        # 創建基於策略名稱和參數的哈希鍵
        import hashlib

        param_str = json.dumps(parameters, sort_keys = True)
        cache_key = hashlib.md5(f"{strategy_name}_{param_str}".encode()).hexdigest()
        return cache_key

    def _load_cache(self):
        """加載結果緩存"""
        try:
            with open(self.cache_file, "rb") as f:
                self.results_cache = pickle.load(f)
            logger.info(f"Loaded {len(self.results_cache)} cached results")
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            self.results_cache = {}

    def _save_cache(self):
        """保存結果緩存"""
        try:
            with open(self.cache_file, "wb") as f:
                pickle.dump(self.results_cache, f)
            logger.info(f"Saved {len(self.results_cache)} results to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def _save_results(self, strategy_name: str, symbol: str, analysis: Dict[str, Any]):
        """保存優化結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{strategy_name}_{symbol}_{timestamp}.json"
        filepath = os.path.join(self.config.results_dir, filename)

        try:
            with open(filepath, "w", encoding="utf - 8") as f:
                json.dump(analysis, f, indent = 2, ensure_ascii = False, default = str)
            logger.info(f"Results saved to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

    def _save_multi_strategy_results(
        self, symbol: str, strategy_results: Dict[str, Dict[str, Any]]
    ):
        """保存多策略優化結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"multi_strategy_{symbol}_{timestamp}.json"
        filepath = os.path.join(self.config.results_dir, filename)

        combined_results = {
            "symbol": symbol,
            "timestamp": timestamp,
            "strategies": strategy_results,
            "summary": {
                "total_strategies": len(strategy_results),
                "successful_strategies": len(
                    [
                        r
                        for r in strategy_results.values()
                        if r.get("successful_combinations", 0) > 0
                    ]
                ),
                "best_strategy": self._find_best_overall_strategy(strategy_results),
            },
        }

        try:
            with open(filepath, "w", encoding="utf - 8") as f:
                json.dump(
                    combined_results, f, indent = 2, ensure_ascii = False, default = str
                )
            logger.info(f"Multi - strategy results saved to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save multi - strategy results: {e}")

    def _find_best_overall_strategy(
        self, strategy_results: Dict[str, Dict[str, Any]]
    ) -> str:
        """找到整體最佳策略"""
        best_strategy = ""
        best_metric = float("-inf")

        for strategy_name, results in strategy_results.items():
            if "best_metric" in results and results["best_metric"] > best_metric:
                best_metric = results["best_metric"]
                best_strategy = strategy_name

        return best_strategy

    def _save_progress(self):
        """保存中間進度"""
        progress_data = {
            "timestamp": datetime.now().isoformat(),
            "total_tasks": self.total_tasks,
            "completed_count": self.completed_count,
            "failed_count": self.failed_count,
            "progress_percent": (self.completed_count + self.failed_count)
            / self.total_tasks
            * 100,
            "elapsed_time": time.time() - self.start_time if self.start_time else 0,
        }

        filepath = os.path.join(self.config.results_dir, "progress.json")
        try:
            with open(filepath, "w", encoding="utf - 8") as f:
                json.dump(progress_data, f, indent = 2)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")

    def _update_statistics(self):
        """更新統計信息"""
        total_time = time.time() - self.start_time if self.start_time else 0
        self.stats["total_execution_time"] = total_time

        if self.completed_count > 0:
            self.stats["average_task_time"] = total_time / self.completed_count
            self.stats["tasks_per_second"] = self.completed_count / total_time

        # 計算並行效率
        ideal_time = total_time / self.config.max_workers
        actual_time = self.stats["average_task_time"] if self.completed_count > 0 else 0
        if ideal_time > 0 and actual_time > 0:
            self.stats["parallel_efficiency"] = (ideal_time / actual_time) * 100

        # 計算緩存命中率
        if self.config.cache_results:
            cache_hits = sum(
                1 for r in self.completed_tasks.values() if r.execution_time == 0
            )
            self.stats["cache_hit_rate"] = (
                (cache_hits / self.completed_count) * 100
                if self.completed_count > 0
                else 0
            )

        # 保存緩存
        if self.config.cache_results:
            self._save_cache()

        logger.info(f"Optimization statistics: {self.stats}")

    def get_optimization_report(self) -> Dict[str, Any]:
        """獲取優化報告"""
        return {
            "configuration": {
                "max_workers": self.config.max_workers,
                "use_processes": self.config.use_processes,
                "enable_gpu": self.config.enable_gpu,
                "chunk_size": self.config.chunk_size,
                "cache_results": self.config.cache_results,
            },
            "performance": self.stats,
            "results_summary": {
                "total_tasks": self.total_tasks,
                "completed_count": self.completed_count,
                "failed_count": self.failed_count,
                "success_rate": (
                    (self.completed_count / self.total_tasks) * 100
                    if self.total_tasks > 0
                    else 0
                ),
            },
            "cache_statistics": {
                "cache_size": len(self.results_cache),
                "cache_hit_rate": self.stats.get("cache_hit_rate", 0),
            },
        }


# 全局實例
parallel_optimizer = ParallelOptimizer()


# 便利函數
def optimize_strategy_parallel(
    strategy_name: str,
    data: pd.DataFrame,
    symbol: str = "UNKNOWN",
    max_combinations: int = 1000,
    optimization_metric: str = "sharpe_ratio",
) -> Dict[str, Any]:
    """便利函數：並行策略優化"""
    return parallel_optimizer.optimize_strategy(
        strategy_name = strategy_name,
        data = data,
        symbol = symbol,
        max_combinations = max_combinations,
        optimization_metric = optimization_metric,
    )


def optimize_all_strategies_parallel(
    data: pd.DataFrame,
    symbol: str = "UNKNOWN",
    max_combinations_per_strategy: int = 500,
    optimization_metric: str = "sharpe_ratio",
) -> Dict[str, Dict[str, Any]]:
    """便利函數：並行多策略優化"""
    strategy_names = [
        "RSI_MEAN_REVERSION",
        "MACD_CROSSOVER",
        "BOLLINGER_BANDS",
        "DUAL_MOVING_AVERAGE",
        "MOMENTUM_BREAKOUT",
        "VOLATILITY_BREAKOUT",
    ]

    return parallel_optimizer.optimize_multiple_strategies(
        strategy_names = strategy_names,
        data = data,
        symbol = symbol,
        max_combinations_per_strategy = max_combinations_per_strategy,
        optimization_metric = optimization_metric,
    )
