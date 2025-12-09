#!/usr / bin / env python3
"""
Phase 5: System Integration and Optimization
異步處理與並行優化系統 - Async Processor & Parallel Optimization

提供高性能的異步處理和並行計算能力，支持：
- 大規模並行驗證處理
- 智能任務調度和負載均衡
- 資源池管理和性能優化
- 容錯和重試機制
- 實時性能監控
"""

import asyncio
import gc
import logging
import multiprocessing as mp
import time
from collections import defaultdict, deque
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import psutil

# Setup logging
logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """任務優先級"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """任務狀態"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AsyncTask:
    """異步任務數據結構"""

    task_id: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: float = field(default_factory = time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory = dict)
    dependencies: List[str] = field(default_factory = list)

    def __hash__(self):
        return hash(self.task_id)

    def can_retry(self) -> bool:
        """檢查是否可以重試"""
        return self.retry_count < self.max_retries and self.status == TaskStatus.FAILED

    def get_execution_time(self) -> Optional[float]:
        """獲取執行時間"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class ResourcePool:
    """資源池管理器"""

    def __init__(self, max_workers: int = None, pool_type: str = "thread"):
        self.pool_type = pool_type
        self.max_workers = max_workers or min(32, (mp.cpu_count() or 1) + 4)

        # 創建執行器
        if pool_type == "thread":
            self.executor = ThreadPoolExecutor(max_workers = self.max_workers)
        elif pool_type == "process":
            self.executor = ProcessPoolExecutor(max_workers = self.max_workers)
        else:
            raise ValueError(f"Unknown pool type: {pool_type}")

        # 統計信息
        self.active_tasks = set()
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.total_execution_time = 0.0

        logger.info(
            f"ResourcePool initialized - Type: {pool_type}, Workers: {self.max_workers}"
        )

    async def submit(self, task: AsyncTask) -> asyncio.Future:
        """提交任務到資源池"""
        # 更新任務狀態
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        self.active_tasks.add(task.task_id)

        # 創建Future
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        try:
            # 在線程池中執行
            if self.pool_type == "thread":
                result_future = self.executor.submit(self._execute_task, task)
            else:
                result_future = self.executor.submit(self._execute_task_process, task)

            # 設置回調
            result_future.add_done_callback(
                lambda f: self._task_completed(future, task, f)
            )

            return future

        except Exception as e:
            # 設置錯誤結果
            task.status = TaskStatus.FAILED
            task.error = e
            task.completed_at = time.time()
            self.active_tasks.discard(task.task_id)
            self.failed_tasks += 1

            future.set_exception(e)
            return future

    def _execute_task(self, task: AsyncTask) -> Any:
        """執行任務（線程池版本）"""
        try:
            # 檢查超時
            if task.timeout:
                start_time = time.time()

            # 執行任務
            result = task.func(*task.args, **task.kwargs)

            # 檢查超時
            if task.timeout and (time.time() - start_time) > task.timeout:
                raise TimeoutError(
                    f"Task {task.task_id} timed out after {task.timeout}s"
                )

            return result

        except Exception as e:
            logger.error(f"Task execution error: {e}")
            raise

    def _execute_task_process(self, task: AsyncTask) -> Any:
        """執行任務（進程池版本）"""
        # 進程池版本需要確保函數和參數可以pickle
        try:
            return self._execute_task(task)
        except Exception as e:
            logger.error(f"Process task execution error: {e}")
            raise

    def _task_completed(self, future: asyncio.Future, task: AsyncTask, result_future):
        """任務完成回調"""
        try:
            # 獲取結果
            result = result_future.result()

            # 更新任務狀態
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = time.time()

            # 更新統計
            self.active_tasks.discard(task.task_id)
            self.completed_tasks += 1

            exec_time = task.get_execution_time()
            if exec_time:
                self.total_execution_time += exec_time

            # 設置Future結果
            future.set_result(result)

        except Exception as e:
            # 更新任務狀態
            task.status = TaskStatus.FAILED
            task.error = e
            task.completed_at = time.time()

            # 更新統計
            self.active_tasks.discard(task.task_id)
            self.failed_tasks += 1

            # 設置Future異常
            future.set_exception(e)

    def get_stats(self) -> Dict[str, Any]:
        """獲取資源池統計"""
        avg_time = (
            self.total_execution_time / self.completed_tasks
            if self.completed_tasks > 0
            else 0
        )

        return {
            "pool_type": self.pool_type,
            "max_workers": self.max_workers,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "total_tasks": self.completed_tasks + self.failed_tasks,
            "success_rate": (
                self.completed_tasks / (self.completed_tasks + self.failed_tasks)
                if (self.completed_tasks + self.failed_tasks) > 0
                else 0
            ),
            "average_execution_time": avg_time,
        }

    def shutdown(self, wait: bool = True):
        """關閉資源池"""
        self.executor.shutdown(wait = wait)
        logger.info(f"ResourcePool ({self.pool_type}) shutdown completed")


class LoadBalancer:
    """負載均衡器"""

    def __init__(self, pools: List[ResourcePool]):
        self.pools = pools
        self.current_pool_index = 0
        self.pool_stats = defaultdict(dict)
        self.last_stats_update = 0

    def get_best_pool(self) -> ResourcePool:
        """獲取最佳資源池（基於負載）"""
        if not self.pools:
            raise ValueError("No resource pools available")

        # 簡單的輪詢負載均衡
        best_pool = self.pools[self.current_pool_index]
        self.current_pool_index = (self.current_pool_index + 1) % len(self.pools)

        return best_pool

    def get_least_loaded_pool(self) -> ResourcePool:
        """獲取負載最少的資源池"""
        if not self.pools:
            raise ValueError("No resource pools available")

        # 基於活躍任務數量選擇最少負載的池
        min_active = float("inf")
        best_pool = self.pools[0]

        for pool in self.pools:
            stats = pool.get_stats()
            active_tasks = stats["active_tasks"]

            if active_tasks < min_active:
                min_active = active_tasks
                best_pool = pool

        return best_pool

    def get_stats(self) -> Dict[str, Any]:
        """獲取負載均衡統計"""
        pool_stats = {}
        total_active = 0
        total_completed = 0

        for i, pool in enumerate(self.pools):
            stats = pool.get_stats()
            pool_stats[f"pool_{i}"] = stats
            total_active += stats["active_tasks"]
            total_completed += stats["completed_tasks"]

        return {
            "pool_count": len(self.pools),
            "total_active_tasks": total_active,
            "total_completed_tasks": total_completed,
            "pool_stats": pool_stats,
        }


class TaskScheduler:
    """任務調度器"""

    def __init__(self, load_balancer: LoadBalancer):
        self.load_balancer = load_balancer
        self.task_queues = {
            TaskPriority.CRITICAL: asyncio.Queue(),
            TaskPriority.HIGH: asyncio.Queue(),
            TaskPriority.NORMAL: asyncio.Queue(),
            TaskPriority.LOW: asyncio.Queue(),
        }
        self.running_tasks = {}
        self.completed_tasks = {}
        self.task_dependencies = {}
        self.is_running = False
        self.scheduler_task = None

        # 統計信息
        self.stats = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
        }

    async def start(self):
        """啟動調度器"""
        if self.is_running:
            return

        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("TaskScheduler started")

    async def stop(self):
        """停止調度器"""
        if not self.is_running:
            return

        self.is_running = False

        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

        # 取消所有運行中的任務
        for task_id, task in self.running_tasks.items():
            task.status = TaskStatus.CANCELLED

        logger.info("TaskScheduler stopped")

    async def _scheduler_loop(self):
        """調度器主循環"""
        while self.is_running:
            try:
                # 按優先級順序檢查任務隊列
                for priority in [
                    TaskPriority.CRITICAL,
                    TaskPriority.HIGH,
                    TaskPriority.NORMAL,
                    TaskPriority.LOW,
                ]:
                    queue = self.task_queues[priority]

                    try:
                        # 非阻塞獲取任務
                        task = queue.get_nowait()

                        # 檢查依賴
                        if self._check_dependencies(task):
                            # 提交任務
                            await self._submit_task(task)
                        else:
                            # 依賴未滿足，重新放入隊列
                            await queue.put(task)

                    except asyncio.QueueEmpty:
                        continue

                # 短暫休眠避免忙等待
                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(1)

    def _check_dependencies(self, task: AsyncTask) -> bool:
        """檢查任務依賴"""
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
        return True

    async def _submit_task(self, task: AsyncTask):
        """提交任務到資源池"""
        try:
            # 選擇最佳資源池
            pool = self.load_balancer.get_best_pool()

            # 提交任務
            future = await pool.submit(task)

            # 添加回調
            future.add_done_callback(lambda f: self._task_completed(task, f))

            # 記錄運行中的任務
            self.running_tasks[task.task_id] = task

            logger.debug(f"Task {task.task_id} submitted to pool")

        except Exception as e:
            logger.error(f"Error submitting task {task.task_id}: {e}")
            task.status = TaskStatus.FAILED
            task.error = e
            self._task_completed(task, None)

    def _task_completed(self, task: AsyncTask, future: Optional[asyncio.Future]):
        """任務完成處理"""
        # 從運行中移除
        self.running_tasks.pop(task.task_id, None)

        # 更新統計
        if task.status == TaskStatus.COMPLETED:
            self.stats["tasks_completed"] += 1
            self.completed_tasks[task.task_id] = task
        elif task.status == TaskStatus.FAILED:
            self.stats["tasks_failed"] += 1

            # 檢查是否需要重試
            if task.can_retry():
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.started_at = None
                task.completed_at = None

                # 重新提交
                asyncio.create_task(self._resubmit_task(task))
            else:
                self.completed_tasks[task.task_id] = task
        elif task.status == TaskStatus.CANCELLED:
            self.stats["tasks_cancelled"] += 1
            self.completed_tasks[task.task_id] = task

        logger.debug(f"Task {task.task_id} completed with status: {task.status}")

    async def _resubmit_task(self, task: AsyncTask):
        """重新提交任務"""
        await asyncio.sleep(1)  # 重試延遲
        await self.task_queues[task.priority].put(task)

    async def submit_task(self, task: AsyncTask) -> str:
        """提交任務"""
        if not self.is_running:
            raise RuntimeError("TaskScheduler is not running")

        # 生成任務ID
        if not task.task_id:
            task.task_id = (
                f"task_{int(time.time() * 1000000)}_{hash(str(task.func)) % 10000}"
            )

        # 添加依賴關係
        for dep_id in task.dependencies:
            if dep_id not in self.task_dependencies:
                self.task_dependencies[dep_id] = []
            self.task_dependencies[dep_id].append(task.task_id)

        # 提交到對應優先級隊列
        await self.task_queues[task.priority].put(task)
        self.stats["tasks_submitted"] += 1

        logger.debug(f"Task {task.task_id} submitted with priority {task.priority}")
        return task.task_id

    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """獲取任務狀態"""
        if task_id in self.running_tasks:
            return self.running_tasks[task_id].status
        elif task_id in self.completed_tasks:
            return self.completed_tasks[task_id].status
        else:
            return None

    async def get_task_result(self, task_id: str) -> Optional[Any]:
        """獲取任務結果"""
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            if task.status == TaskStatus.COMPLETED:
                return task.result
            elif task.status == TaskStatus.FAILED and task.error:
                raise task.error
        return None

    def get_stats(self) -> Dict[str, Any]:
        """獲取調度器統計"""
        queue_sizes = {
            priority.name.lower(): queue.qsize()
            for priority, queue in self.task_queues.items()
        }

        return {
            "is_running": self.is_running,
            "queue_sizes": queue_sizes,
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "stats": self.stats.copy(),
            "load_balancer_stats": self.load_balancer.get_stats(),
        }


class AsyncProcessor:
    """異步處理器主類"""

    def __init__(
        self,
        max_workers: int = None,
        thread_pools: int = 2,
        process_pools: int = 1,
        enable_monitoring: bool = True,
    ):

        # 創建資源池
        self.pools = []

        # 線程池（適用於I / O密集型任務）
        for i in range(thread_pools):
            workers = max_workers // thread_pools if max_workers else None
            pool = ResourcePool(workers, "thread")
            self.pools.append(pool)

        # 進程池（適用於CPU密集型任務）
        for i in range(process_pools):
            workers = max_workers // process_pools if max_workers else None
            pool = ResourcePool(workers, "process")
            self.pools.append(pool)

        # 創建負載均衡器
        self.load_balancer = LoadBalancer(self.pools)

        # 創建任務調度器
        self.scheduler = TaskScheduler(self.load_balancer)

        # 監控系統
        self.enable_monitoring = enable_monitoring
        self.monitoring_data = deque(maxlen = 1000)
        self.monitoring_task = None

        # 性能統計
        self.performance_metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "avg_execution_time": 0.0,
            "throughput_per_second": 0.0,
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
        }

        logger.info("AsyncProcessor initialized")

    async def start(self):
        """啟動異步處理器"""
        await self.scheduler.start()

        if self.enable_monitoring:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info("AsyncProcessor started")

    async def stop(self):
        """停止異步處理器"""
        await self.scheduler.stop()

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        # 關閉所有資源池
        for pool in self.pools:
            pool.shutdown()

        logger.info("AsyncProcessor stopped")

    async def submit_task(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        max_retries: int = 3,
        dependencies: List[str] = None,
        task_id: str = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """提交任務"""
        kwargs = kwargs or {}
        dependencies = dependencies or []
        metadata = metadata or {}

        task = AsyncTask(
            task_id = task_id,
            func = func,
            args = args,
            kwargs = kwargs,
            priority = priority,
            timeout = timeout,
            max_retries = max_retries,
            dependencies = dependencies,
            metadata = metadata,
        )

        return await self.scheduler.submit_task(task)

    async def submit_batch(
        self,
        tasks: List[Tuple[Callable, tuple, dict]],
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        max_retries: int = 3,
    ) -> List[str]:
        """批量提交任務"""
        task_ids = []

        for func, args, kwargs in tasks:
            task_id = await self.submit_task(
                func = func,
                args = args,
                kwargs = kwargs,
                priority = priority,
                timeout = timeout,
                max_retries = max_retries,
            )
            task_ids.append(task_id)

        return task_ids

    async def process_parallel(
        self,
        data_items: List[Any],
        processor_func: Callable,
        batch_size: int = 10,
        max_concurrent: int = 50,
    ) -> List[Any]:
        """並行處理數據項"""
        results = [None] * len(data_items)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_item(index: int, item: Any):
            async with semaphore:
                try:
                    result = await self.submit_task(processor_func, (item,))
                    results[index] = result
                except Exception as e:
                    logger.error(f"Error processing item {index}: {e}")
                    results[index] = e

        # 創建任務
        tasks = [process_item(i, item) for i, item in enumerate(data_items)]

        # 等待所有任務完成
        await asyncio.gather(*tasks, return_exceptions = True)

        return results

    async def map_parallel(
        self, func: Callable, items: List[Any], max_concurrent: int = None
    ) -> List[Any]:
        """並行映射函數到列表"""
        if max_concurrent is None:
            max_concurrent = min(50, len(items))

        results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_item(item):
            async with semaphore:
                return await self.submit_task(func, (item,))

        tasks = [process_item(item) for item in items]
        task_results = await asyncio.gather(*tasks, return_exceptions = True)

        # 獲取實際結果
        for task_result in task_results:
            if isinstance(task_result, Exception):
                results.append(task_result)
            else:
                # task_result是任務ID，需要獲取實際結果
                try:
                    result = await self.scheduler.get_task_result(task_result)
                    results.append(result)
                except Exception as e:
                    results.append(e)

        return results

    async def _monitoring_loop(self):
        """監控循環"""
        while True:
            try:
                # 收集性能指標
                cpu_usage = psutil.cpu_percent()
                memory_info = psutil.virtual_memory()

                # 獲取調度器統計
                scheduler_stats = self.scheduler.get_stats()

                # 計算吞吐量
                current_time = time.time()
                if self.monitoring_data:
                    time_window = current_time - self.monitoring_data[0]["timestamp"]
                    recent_tasks = [
                        d
                        for d in self.monitoring_data
                        if current_time - d["timestamp"] < 60
                    ]  # 最近1分鐘
                    throughput = len(recent_tasks) / max(time_window, 1)
                else:
                    throughput = 0

                # 更新性能指標
                self.performance_metrics.update(
                    {
                        "cpu_usage": cpu_usage,
                        "memory_usage": memory_info.percent,
                        "throughput_per_second": throughput,
                    }
                )

                # 記錄監控數據
                monitoring_entry = {
                    "timestamp": current_time,
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_info.percent,
                    "scheduler_stats": scheduler_stats,
                    "load_balancer_stats": self.load_balancer.get_stats(),
                }
                self.monitoring_data.append(monitoring_entry)

                # 等待下次監控
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(10)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        return {
            "performance_metrics": self.performance_metrics.copy(),
            "scheduler_stats": self.scheduler.get_stats(),
            "load_balancer_stats": self.load_balancer.get_stats(),
            "resource_pool_stats": [pool.get_stats() for pool in self.pools],
            "monitoring_data_points": len(self.monitoring_data),
        }

    async def wait_for_completion(
        self, task_ids: List[str], timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """等待任務完成"""
        start_time = time.time()
        results = {}

        while task_ids:
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Timeout waiting for tasks completion")

            completed_tasks = []
            for task_id in task_ids:
                status = await self.scheduler.get_task_status(task_id)

                if status in [
                    TaskStatus.COMPLETED,
                    TaskStatus.FAILED,
                    TaskStatus.CANCELLED,
                ]:
                    try:
                        result = await self.scheduler.get_task_result(task_id)
                        results[task_id] = result
                    except Exception as e:
                        results[task_id] = e
                    completed_tasks.append(task_id)

            # 移除已完成的任務
            for task_id in completed_tasks:
                task_ids.remove(task_id)

            # 短暫休眠
            if task_ids:
                await asyncio.sleep(0.1)

        return results


# 全局異步處理器實例
async_processor = AsyncProcessor(
    max_workers = 32, thread_pools = 2, process_pools = 1, enable_monitoring = True
)


# 便捷函數
async def submit_async_task(
    func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    priority: TaskPriority = TaskPriority.NORMAL,
) -> str:
    """提交異步任務"""
    return await async_processor.submit_task(func, args, kwargs, priority)


async def process_parallel(
    data_items: List[Any],
    processor_func: Callable,
    batch_size: int = 10,
    max_concurrent: int = 50,
) -> List[Any]:
    """並行處理數據"""
    return await async_processor.process_parallel(
        data_items, processor_func, batch_size, max_concurrent
    )


async def map_parallel(
    func: Callable, items: List[Any], max_concurrent: int = None
) -> List[Any]:
    """並行映射函數"""
    return await async_processor.map_parallel(func, items, max_concurrent)


def get_processor_metrics() -> Dict[str, Any]:
    """獲取處理器指標"""
    return async_processor.get_performance_metrics()


async def start_async_processor():
    """啟動異步處理器"""
    await async_processor.start()


async def stop_async_processor():
    """停止異步處理器"""
    await async_processor.stop()


if __name__ == "__main__":

    async def test_function(x: int, delay: float = 0.1) -> int:
        """測試函數"""
        await asyncio.sleep(delay)
        return x * x

    async def test_async_processor():
        """測試異步處理器"""
        print("Testing Async Processor...")

        # 啟動處理器
        await start_async_processor()

        try:
            # 測試單個任務
            print("\n1. Testing single task...")
            task_id = await submit_async_task(test_function, (5,))
            print(f"Task submitted: {task_id}")

            # 等待完成
            await asyncio.sleep(1)
            result = await async_processor.scheduler.get_task_result(task_id)
            print(f"Task result: {result}")

            # 測試並行處理
            print("\n2. Testing parallel processing...")
            data_items = list(range(10))
            results = await process_parallel(data_items, test_function, 0.05, 5)
            print(f"Parallel results: {results}")

            # 測試並行映射
            print("\n3. Testing parallel map...")
            items = list(range(5))
            map_results = await map_parallel(lambda x: x * *3, items, 3)
            print(f"Map results: {map_results}")

            # 顯示性能指標
            print("\n4. Performance metrics:")
            metrics = get_processor_metrics()
            print(f"Performance metrics: {metrics['performance_metrics']}")
            print(f"Scheduler stats: {metrics['scheduler_stats']}")
            print(f"Load balancer stats: {metrics['load_balancer_stats']}")

        finally:
            # 停止處理器
            await stop_async_processor()

        print("\nAsync Processor test completed!")

    # 運行測試
    asyncio.run(test_async_processor())
