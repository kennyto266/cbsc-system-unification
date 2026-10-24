#!/usr/bin/env python3
"""
Phase 3.2: Parallel Parameter Optimization Engine
並行參數優化引擎

Parallel Parameter Optimizer for large-scale optimization
Supports multi-process/multi-threading with intelligent workload balancing
"""

import json
import logging
import time
import hashlib
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from pathlib import Path
from datetime import datetime
import multiprocessing as mp
from functools import partial
import threading
import queue
import pickle

import numpy as np
from tqdm import tqdm

logger = logging.getLogger(__name__)

class OptimizationTask:
    """優化任務"""
    def __init__(self,
                 task_id: str,
                 indicator_name: str,
                 parameters: Dict[str, Any],
                 priority: int = 1,
                 created_time: datetime = None):
        self.task_id = task_id
        self.indicator_name = indicator_name
        self.parameters = parameters
        self.priority = priority
        self.created_time = created_time or datetime.now()

    def __lt__(self, other):
        # 用於優先級隊列比較，優先級高的排在前面
        if not isinstance(other, OptimizationTask):
            return NotImplemented
        return self.priority > other.priority  # 注意：這裡反轉比較，因為PriorityQueue是最小堆

    def __eq__(self, other):
        if not isinstance(other, OptimizationTask):
            return NotImplemented
        return self.task_id == other.task_id

    def __hash__(self):
        return hash(self.task_id)

@dataclass
class OptimizationResult:
    """優化結果"""
    task_id: str
    indicator_name: str
    parameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    execution_time: float
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class WorkerStats:
    """工作線程統計"""
    worker_id: int
    tasks_completed: int = 0
    total_time: float = 0.0
    errors_count: int = 0
    last_activity: datetime = field(default_factory=datetime.now)

class ResultCache:
    """結果緩存系統"""

    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.memory_cache: Dict[str, OptimizationResult] = {}
        self.cache_lock = threading.Lock()

    def _generate_cache_key(self, indicator_name: str, parameters: Dict) -> str:
        """生成緩存鍵"""
        param_str = json.dumps(parameters, sort_keys=True)
        return hashlib.md5(f"{indicator_name}_{param_str}".encode()).hexdigest()

    def get(self, indicator_name: str, parameters: Dict) -> Optional[OptimizationResult]:
        """獲取緩存結果"""
        cache_key = self._generate_cache_key(indicator_name, parameters)

        # 先檢查內存緩存
        with self.cache_lock:
            if cache_key in self.memory_cache:
                return self.memory_cache[cache_key]

        # 檢查磁盤緩存
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    result = pickle.load(f)

                with self.cache_lock:
                    self.memory_cache[cache_key] = result

                return result
            except Exception as e:
                logger.warning(f"Failed to load cache file {cache_file}: {e}")

        return None

    def put(self, result: OptimizationResult):
        """存儲結果到緩存"""
        cache_key = self._generate_cache_key(result.indicator_name, result.parameters)

        # 存儲到內存緩存
        with self.cache_lock:
            self.memory_cache[cache_key] = result

        # 存儲到磁盤緩存
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
        except Exception as e:
            logger.warning(f"Failed to save cache file {cache_file}: {e}")

    def clear(self):
        """清空緩存"""
        with self.cache_lock:
            self.memory_cache.clear()

        # 刪除磁盤緩存文件
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")

class WorkloadBalancer:
    """工作負載平衡器"""

    def __init__(self, num_workers: int):
        self.num_workers = num_workers
        self.task_queue = queue.PriorityQueue()
        self.worker_stats = {i: WorkerStats(worker_id=i) for i in range(num_workers)}
        self.stats_lock = threading.Lock()

    def add_task(self, task: OptimizationTask):
        """添加任務到隊列"""
        # 直接添加任務，因為OptimizationTask已經實現了順序比較
        self.task_queue.put(task)

    def get_next_task(self) -> Optional[OptimizationTask]:
        """獲取下一個任務"""
        try:
            task = self.task_queue.get_nowait()
            return task
        except queue.Empty:
            return None

    def update_worker_stats(self, worker_id: int, task_time: float, error: bool = False):
        """更新工作線程統計"""
        with self.stats_lock:
            stats = self.worker_stats[worker_id]
            stats.tasks_completed += 1
            stats.total_time += task_time
            stats.last_activity = datetime.now()
            if error:
                stats.errors_count += 1

    def get_worker_stats(self) -> Dict[int, WorkerStats]:
        """獲取所有工作線程統計"""
        with self.stats_lock:
            return self.worker_stats.copy()

    def get_queue_size(self) -> int:
        """獲取隊列大小"""
        return self.task_queue.qsize()

class ParallelParameterOptimizer:
    """並行參數優化引擎"""

    def __init__(self,
                 objective_function: Callable,
                 num_workers: Optional[int] = None,
                 use_multiprocessing: bool = True,
                 cache_dir: str = "cache",
                 enable_progress_bar: bool = True):
        """
        初始化並行優化引擎

        Args:
            objective_function: 目標函數，接受(indicator_name, parameters)返回性能指標
            num_workers: 工作線程數量，默認使用CPU核心數
            use_multiprocessing: 是否使用多進程，True為多進程，False為多線程
            cache_dir: 緩存目錄
            enable_progress_bar: 是否顯示進度條
        """
        self.objective_function = objective_function
        self.num_workers = num_workers or min(32, (mp.cpu_count() or 1) + 4)
        self.use_multiprocessing = use_multiprocessing
        self.enable_progress_bar = enable_progress_bar

        # 初始化組件
        self.cache = ResultCache(cache_dir)
        self.workload_balancer = WorkloadBalancer(self.num_workers)

        # 統計信息
        self.total_tasks = 0
        self.completed_tasks = 0
        self.cached_tasks = 0
        self.error_tasks = 0
        self.start_time = None

        logger.info(f"ParallelParameterOptimizer initialized: {self.num_workers} workers, "
                   f"{'multiprocessing' if use_multiprocessing else 'multithreading'}")

    def optimize_indicators(self,
                           indicator_tasks: List[Tuple[str, List[Dict]]],
                           max_tasks_per_indicator: Optional[int] = None) -> List[OptimizationResult]:
        """
        優化多個指標

        Args:
            indicator_tasks: 指標任務列表，每個元素是(indicator_name, parameter_combinations)
            max_tasks_per_indicator: 每個指標的最大任務數量

        Returns:
            優化結果列表
        """
        self.start_time = time.time()

        # 準備任務
        all_tasks = self._prepare_tasks(indicator_tasks, max_tasks_per_indicator)
        self.total_tasks = len(all_tasks)

        logger.info(f"Starting optimization: {self.total_tasks} total tasks")

        if self.total_tasks == 0:
            logger.warning("No tasks to optimize")
            return []

        # 執行優化
        results = self._execute_parallel_optimization(all_tasks)

        # 生成報告
        self._log_optimization_report()

        return results

    def _prepare_tasks(self,
                      indicator_tasks: List[Tuple[str, List[Dict]]],
                      max_tasks_per_indicator: Optional[int]) -> List[OptimizationTask]:
        """準備優化任務"""
        all_tasks = []

        for indicator_name, parameter_combinations in indicator_tasks:
            # 限制任務數量
            if max_tasks_per_indicator and len(parameter_combinations) > max_tasks_per_indicator:
                # 均勻採樣
                step = len(parameter_combinations) // max_tasks_per_indicator
                parameter_combinations = parameter_combinations[::step]

            for i, parameters in enumerate(parameter_combinations):
                task = OptimizationTask(
                    task_id=f"{indicator_name}_{i}",
                    indicator_name=indicator_name,
                    parameters=parameters,
                    priority=1
                )
                all_tasks.append(task)

        return all_tasks

    def _execute_parallel_optimization(self, tasks: List[OptimizationTask]) -> List[OptimizationResult]:
        """執行並行優化"""
        results = []

        # 添加任務到負載平衡器
        for task in tasks:
            self.workload_balancer.add_task(task)

        # 選擇執行器類型
        executor_class = ProcessPoolExecutor if self.use_multiprocessing else ThreadPoolExecutor

        with executor_class(max_workers=self.num_workers) as executor:
            # 提交任務
            future_to_task = {}

            for worker_id in range(self.num_workers):
                future = executor.submit(self._worker_loop, worker_id)
                future_to_task[future] = worker_id

            # 收集結果
            completed_futures = as_completed(future_to_task)

            if self.enable_progress_bar:
                completed_futures = tqdm(completed_futures,
                                       total=self.num_workers,
                                       desc="Optimizing")

            for future in completed_futures:
                try:
                    worker_results = future.result()
                    results.extend(worker_results)
                except Exception as e:
                    worker_id = future_to_task[future]
                    logger.error(f"Worker {worker_id} failed: {e}")

        return results

    def _worker_loop(self, worker_id: int) -> List[OptimizationResult]:
        """工作線程循環"""
        results = []

        while True:
            # 獲取下一個任務
            task = self.workload_balancer.get_next_task()
            if task is None:
                break

            # 檢查緩存
            cached_result = self.cache.get(task.indicator_name, task.parameters)
            if cached_result:
                results.append(cached_result)
                self.cached_tasks += 1
                continue

            # 執行優化
            start_time = time.time()
            try:
                performance_metrics = self.objective_function(task.indicator_name, task.parameters)
                execution_time = time.time() - start_time

                result = OptimizationResult(
                    task_id=task.task_id,
                    indicator_name=task.indicator_name,
                    parameters=task.parameters,
                    performance_metrics=performance_metrics,
                    execution_time=execution_time
                )

                # 存儲到緩存
                self.cache.put(result)

                results.append(result)
                self.completed_tasks += 1

                # 更新統計
                self.workload_balancer.update_worker_stats(worker_id, execution_time, False)

            except Exception as e:
                execution_time = time.time() - start_time

                result = OptimizationResult(
                    task_id=task.task_id,
                    indicator_name=task.indicator_name,
                    parameters=task.parameters,
                    performance_metrics={},
                    execution_time=execution_time,
                    error=str(e)
                )

                results.append(result)
                self.error_tasks += 1

                # 更新統計
                self.workload_balancer.update_worker_stats(worker_id, execution_time, True)

                logger.warning(f"Task {task.task_id} failed: {e}")

        return results

    def _log_optimization_report(self):
        """記錄優化報告"""
        total_time = time.time() - self.start_time if self.start_time else 0

        logger.info("=== Optimization Report ===")
        logger.info(f"Total tasks: {self.total_tasks}")
        logger.info(f"Completed: {self.completed_tasks}")
        logger.info(f"Cached: {self.cached_tasks}")
        logger.info(f"Errors: {self.error_tasks}")
        logger.info(f"Total time: {total_time:.2f}s")

        if total_time > 0:
            throughput = (self.completed_tasks + self.cached_tasks) / total_time
            logger.info(f"Throughput: {throughput:.2f} tasks/sec")

        # 工作線程統計
        worker_stats = self.workload_balancer.get_worker_stats()
        for worker_id, stats in worker_stats.items():
            if stats.tasks_completed > 0:
                avg_time = stats.total_time / stats.tasks_completed
                logger.info(f"Worker {worker_id}: {stats.tasks_completed} tasks, "
                          f"avg {avg_time:.3f}s, {stats.errors_count} errors")

    def get_best_results(self,
                        results: List[OptimizationResult],
                        metric: str = "sharpe_ratio",
                        top_n: int = 10) -> List[OptimizationResult]:
        """獲取最佳結果"""
        # 過濾掉有錯誤的結果
        valid_results = [r for r in results if not r.error and metric in r.performance_metrics]

        # 按指定指標排序
        sorted_results = sorted(valid_results,
                               key=lambda x: x.performance_metrics[metric],
                               reverse=True)

        return sorted_results[:top_n]

    def export_results(self,
                      results: List[OptimizationResult],
                      file_path: str = None) -> str:
        """導出優化結果"""
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"optimization_results_{timestamp}.json"

        # 準備導出數據
        export_data = {
            "metadata": {
                "total_tasks": self.total_tasks,
                "completed_tasks": self.completed_tasks,
                "cached_tasks": self.cached_tasks,
                "error_tasks": self.error_tasks,
                "num_workers": self.num_workers,
                "execution_time": time.time() - self.start_time if self.start_time else 0,
                "timestamp": datetime.now().isoformat()
            },
            "results": []
        }

        for result in results:
            result_data = {
                "task_id": result.task_id,
                "indicator_name": result.indicator_name,
                "parameters": result.parameters,
                "performance_metrics": result.performance_metrics,
                "execution_time": result.execution_time,
                "error": result.error,
                "timestamp": result.timestamp.isoformat()
            }
            export_data["results"].append(result_data)

        # 保存到文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Results exported to {file_path}")
        return file_path

    def clear_cache(self):
        """清空緩存"""
        self.cache.clear()
        logger.info("Cache cleared")

def dummy_objective_function(indicator_name: str, parameters: Dict) -> Dict[str, float]:
    """虛擬目標函數（用於測試）"""
    # 模擬計算延遲
    time.sleep(0.01)

    # 生成隨機性能指標
    return {
        "sharpe_ratio": np.random.normal(1.0, 0.5),
        "max_drawdown": np.random.uniform(-0.2, -0.05),
        "total_return": np.random.uniform(0.1, 0.5),
        "win_rate": np.random.uniform(0.4, 0.7)
    }

if __name__ == "__main__":
    # 測試代碼
    logging.basicConfig(level=logging.INFO)

    # 創建優化器
    optimizer = ParallelParameterOptimizer(
        objective_function=dummy_objective_function,
        num_workers=4,
        use_multiprocessing=True,
        enable_progress_bar=True
    )

    # 準備測試任務
    test_tasks = [
        ("RSI", [{"period": 14, "oversold": 30, "overbought": 70},
                 {"period": 21, "oversold": 25, "overbought": 75}]),
        ("MACD", [{"fast_period": 12, "slow_period": 26, "signal_period": 9},
                  {"fast_period": 5, "slow_period": 35, "signal_period": 5}])
    ]

    # 執行優化
    results = optimizer.optimize_indicators(test_tasks)

    print(f"\nOptimization completed: {len(results)} results")

    # 獲取最佳結果
    best_results = optimizer.get_best_results(results, "sharpe_ratio", top_n=5)
    print(f"\nTop 5 results by Sharpe ratio:")
    for i, result in enumerate(best_results, 1):
        print(f"{i}. {result.indicator_name}: {result.performance_metrics['sharpe_ratio']:.3f}")

    # 導出結果
    result_file = optimizer.export_results(results)
    print(f"\nResults exported to: {result_file}")