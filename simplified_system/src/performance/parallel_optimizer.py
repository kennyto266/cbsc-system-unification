#!/usr / bin / env python3
"""
并行计算优化器
Parallel computation optimizer for multi - core CPU utilization
"""

import concurrent.futures
import logging
import multiprocessing as mp
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ParallelConfig:
    """并行计算配置"""

    max_workers: Optional[int] = None
    chunk_size: int = 1
    use_processes: bool = True
    memory_limit_mb: Optional[int] = None
    timeout: Optional[float] = None


class ParallelOptimizer:
    """
    并行计算优化器

    特性:
    - 智能工作线程数量检测
    - 内存使用优化
    - 动态负载均衡
    - 异常处理和恢复
    - 进度监控
    """

    def __init__(self, config: Optional[ParallelConfig] = None):
        self.config = config or ParallelConfig()
        self.cpu_count = mp.cpu_count()
        self.optimal_workers = self._detect_optimal_workers()
        self.memory_usage = 0
        self.task_stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_time": 0.0,
            "average_task_time": 0.0,
        }

        logger.info(
            f"Parallel optimizer initialized with {self.optimal_workers} workers"
        )

    def _detect_optimal_workers(self) -> int:
        """检测最优工作线程数量"""
        if self.config.max_workers is not None:
            return min(self.config.max_workers, self.cpu_count)

        # 智能检测：考虑CPU核心数和任务类型
        if self.config.use_processes:
            # 进程池：通常使用所有核心减1（保留一个给主进程）
            return max(1, self.cpu_count - 1)
        else:
            # 线程池：对于I / O密集型任务可以使用更多线程
            return min(self.cpu_count * 2, 32)

    def parallel_execute(
        self,
        func: Callable,
        tasks: List[Any],
        task_args: Optional[List[Tuple]] = None,
        task_kwargs: Optional[List[Dict]] = None,
        progress_callback: Optional[Callable] = None,
    ) -> List[Any]:
        """
        并行执行任务列表

        Args:
            func: 要执行的函数
            tasks: 任务参数列表
            task_args: 额外的位置参数列表
            task_kwargs: 额外的关键字参数列表
            progress_callback: 进度回调函数

        Returns:
            执行结果列表
        """
        if not tasks:
            return []

        self.task_stats["total_tasks"] = len(tasks)
        start_time = time.time()

        # 准备任务参数
        prepared_tasks = self._prepare_tasks(func, tasks, task_args, task_kwargs)

        # 选择执行方式
        if len(prepared_tasks) == 1:
            # 单个任务直接执行
            results = [self._execute_single_task(prepared_tasks[0])]
        else:
            # 多个任务并行执行
            results = self._execute_parallel_tasks(prepared_tasks, progress_callback)

        # 更新统计
        execution_time = time.time() - start_time
        self.task_stats["total_time"] += execution_time
        self.task_stats["completed_tasks"] = len(results)
        self.task_stats["average_task_time"] = execution_time / len(tasks)

        logger.info(
            f"Parallel execution completed: {len(tasks)} tasks in {execution_time:.2f}s"
        )

        return results

    def _prepare_tasks(
        self,
        func: Callable,
        tasks: List[Any],
        task_args: Optional[List[Tuple]],
        task_kwargs: Optional[List[Dict]],
    ) -> List[Dict]:
        """准备任务参数"""
        prepared_tasks = []

        for i, task in enumerate(tasks):
            task_dict = {"func": func, "args": (task,) if task is not None else ()}

            # 添加额外的位置参数
            if task_args and i < len(task_args):
                task_dict["args"] = task_dict["args"] + task_args[i]

            # 添加关键字参数
            if task_kwargs and i < len(task_kwargs):
                task_dict["kwargs"] = task_kwargs[i]
            else:
                task_dict["kwargs"] = {}

            prepared_tasks.append(task_dict)

        return prepared_tasks

    def _execute_single_task(self, task: Dict) -> Any:
        """执行单个任务"""
        try:
            return task["func"](*task["args"], **task["kwargs"])
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self.task_stats["failed_tasks"] += 1
            raise

    def _execute_parallel_tasks(
        self, tasks: List[Dict], progress_callback: Optional[Callable]
    ) -> List[Any]:
        """并行执行多个任务"""
        results = [None] * len(tasks)
        completed_count = 0

        # 选择执行器类型
        executor_class = (
            mp.ProcessPoolExecutor
            if self.config.use_processes
            else concurrent.futures.ThreadPoolExecutor
        )

        with executor_class(max_workers = self.optimal_workers) as executor:
            # 提交所有任务
            future_to_index = {}
            for i, task in enumerate(tasks):
                future = executor.submit(self._execute_single_task, task)
                future_to_index[future] = i

            # 收集结果
            for future in concurrent.futures.as_completed(
                future_to_index, timeout = self.config.timeout
            ):
                index = future_to_index[future]

                try:
                    result = future.result()
                    results[index] = result
                    completed_count += 1

                    # 调用进度回调
                    if progress_callback:
                        progress_callback(completed_count, len(tasks))

                except Exception as e:
                    logger.error(f"Task {index} failed: {e}")
                    results[index] = None
                    self.task_stats["failed_tasks"] += 1
                    completed_count += 1

                    if progress_callback:
                        progress_callback(completed_count, len(tasks))

        return results

    def parallel_map(
        self,
        func: Callable,
        iterable: List[Any],
        chunk_size: Optional[int] = None,
        progress_callback: Optional[Callable] = None,
    ) -> List[Any]:
        """
        并行map操作

        Args:
            func: 映射函数
            iterable: 可迭代对象
            chunk_size: 分块大小
            progress_callback: 进度回调

        Returns:
            映射结果列表
        """
        if chunk_size is None:
            chunk_size = self.config.chunk_size

        # 分块处理大数据集
        if len(iterable) > chunk_size * 10:
            return self._chunked_parallel_map(
                func, iterable, chunk_size, progress_callback
            )
        else:
            # 直接并行处理
            tasks = list(iterable)
            return self.parallel_execute(
                func, tasks, progress_callback = progress_callback
            )

    def _chunked_parallel_map(
        self,
        func: Callable,
        iterable: List[Any],
        chunk_size: int,
        progress_callback: Optional[Callable],
    ) -> List[Any]:
        """分块并行map操作"""

        def process_chunk(chunk):
            return [func(item) for item in chunk]

        # 分块
        chunks = [
            iterable[i : i + chunk_size] for i in range(0, len(iterable), chunk_size)
        ]

        # 并行处理每个块
        chunk_results = self.parallel_execute(
            process_chunk, chunks, progress_callback = progress_callback
        )

        # 合并结果
        results = []
        for chunk_result in chunk_results:
            if chunk_result:
                results.extend(chunk_result)

        return results

    def parallel_dataframe_apply(
        self,
        df: pd.DataFrame,
        func: Callable,
        axis: int = 0,
        progress_callback: Optional[Callable] = None,
    ) -> pd.Series:
        """
        并行DataFrame apply操作

        Args:
            df: DataFrame
            func: 应用函数
            axis: 应用轴 (0 = 行, 1 = 列)
            progress_callback: 进度回调

        Returns:
            应用结果Series
        """
        if axis == 0:
            # 按行并行处理
            rows = [row for _, row in df.iterrows()]
            results = self.parallel_execute(
                func, rows, progress_callback = progress_callback
            )
            return pd.Series(results, index = df.index)
        else:
            # 按列并行处理
            columns = [df[col] for col in df.columns]
            results = self.parallel_execute(
                func, columns, progress_callback = progress_callback
            )
            return pd.Series(results, index = df.columns)

    def optimize_parameter_combinations(
        self,
        param_combinations: List[Dict[str, Any]],
        objective_func: Callable,
        progress_callback: Optional[Callable] = None,
    ) -> List[Dict[str, Any]]:
        """
        并行参数组合优化

        Args:
            param_combinations: 参数组合列表
            objective_func: 目标函数
            progress_callback: 进度回调

        Returns:
            优化结果列表
        """

        def evaluate_params(params):
            try:
                start_time = time.time()
                result = objective_func(params)
                execution_time = time.time() - start_time

                return {
                    "parameters": params,
                    "result": result,
                    "execution_time": execution_time,
                    "success": True,
                }
            except Exception as e:
                logger.warning(f"Parameter evaluation failed: {params}, Error: {e}")
                return {
                    "parameters": params,
                    "result": None,
                    "execution_time": 0,
                    "success": False,
                    "error": str(e),
                }

        # 并行评估所有参数组合
        results = self.parallel_execute(
            evaluate_params, param_combinations, progress_callback = progress_callback
        )

        # 过滤成功的评估
        successful_results = [r for r in results if r.get("success", False)]

        logger.info(
            f"Parameter optimization completed: {len(successful_results)}/{len(param_combinations)} successful"
        )

        return successful_results

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        total_tasks = self.task_stats["total_tasks"]
        success_rate = 1.0

        if total_tasks > 0:
            success_rate = (total_tasks - self.task_stats["failed_tasks"]) / total_tasks

        return {
            "worker_configuration": {
                "cpu_count": self.cpu_count,
                "optimal_workers": self.optimal_workers,
                "use_processes": self.config.use_processes,
                "max_workers": self.config.max_workers,
            },
            "task_statistics": {
                "total_tasks": total_tasks,
                "completed_tasks": self.task_stats["completed_tasks"],
                "failed_tasks": self.task_stats["failed_tasks"],
                "success_rate": success_rate,
                "total_execution_time": self.task_stats["total_time"],
                "average_task_time": self.task_stats["average_task_time"],
                "tasks_per_second": (
                    total_tasks / self.task_stats["total_time"]
                    if self.task_stats["total_time"] > 0
                    else 0
                ),
            },
            "configuration": {
                "chunk_size": self.config.chunk_size,
                "timeout": self.config.timeout,
                "memory_limit_mb": self.config.memory_limit_mb,
            },
        }

    def reset_stats(self) -> None:
        """重置性能统计"""
        self.task_stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_time": 0.0,
            "average_task_time": 0.0,
        }


# 全局并行优化器实例
global_parallel_optimizer = ParallelOptimizer()


# 便利函数
def parallel_execute(func: Callable, tasks: List[Any], **kwargs) -> List[Any]:
    """便利函数：并行执行"""
    return global_parallel_optimizer.parallel_execute(func, tasks, **kwargs)


def parallel_map(func: Callable, iterable: List[Any], **kwargs) -> List[Any]:
    """便利函数：并行map"""
    return global_parallel_optimizer.parallel_map(func, iterable, **kwargs)


def parallel_optimize_parameters(
    param_combinations: List[Dict], objective_func: Callable, **kwargs
) -> List[Dict]:
    """便利函数：并行参数优化"""
    return global_parallel_optimizer.optimize_parameter_combinations(
        param_combinations, objective_func, **kwargs
    )


def get_parallel_stats() -> Dict[str, Any]:
    """获取并行计算统计"""
    return global_parallel_optimizer.get_performance_stats()
