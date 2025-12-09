#!/usr/bin/env python3
"""
High-Performance Parameter Optimization Architecture
機構級性能參數優化架構

支持百萬參數組合處理能力 (Selection 3.C):
- Parallel Processing: 32-core distributed optimization engine
- Memory Optimization: Streaming algorithms for large datasets
- Intelligent Caching: Redis-based result caching and persistence
- Load Balancing: Dynamic resource allocation across optimization jobs
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional, Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio
import redis
import pickle
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing as mp
import threading
import queue
import psutil
import gc
from functools import lru_cache
import zlib
import time
from pathlib import Path

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """快取策略"""
    NO_CACHE = "no_cache"
    MEMORY_CACHE = "memory_cache"
    REDIS_CACHE = "redis_cache"
    DISTRIBUTED_CACHE = "distributed_cache"

class OptimizationMode(Enum):
    """優化模式"""
    STREAMING = "streaming"      # 流式處理，適合大數據集
    BATCH = "batch"             # 批次處理，適合中等數據集
    INCREMENTAL = "incremental"  # 增量處理，適合實時更新

@dataclass
class PerformanceConfig:
    """性能配置"""
    max_workers: int = 32
    memory_limit_gb: float = 16.0
    cache_strategy: CacheStrategy = CacheStrategy.REDIS_CACHE
    streaming_chunk_size: int = 10000
    enable_load_balancing: bool = True
    enable_memory_monitoring: bool = True
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    cache_ttl_seconds: int = 3600
    max_cache_size_mb: int = 1024

@dataclass
class ResourceMetrics:
    """資源指標"""
    cpu_usage: float
    memory_usage: float
    memory_available_gb: float
    active_workers: int
    queue_depth: int
    combinations_per_second: float
    cache_hit_rate: float

@dataclass
class LoadBalancingInfo:
    """負載平衡信息"""
    worker_id: str
    current_load: float
    max_capacity: int
    estimated_completion_time: datetime
    current_job_id: str

class StreamingParameterGenerator:
    """流式參數生成器 - 支持百萬參數組合而不耗盡記憶體"""

    def __init__(self, chunk_size: int = 10000):
        self.chunk_size = chunk_size
        self.total_combinations = 0
        self.generated_count = 0

    def generate_streaming_combinations(self,
                                       parameter_ranges: Dict[str, List[Any]],
                                       max_combinations: int = 1000000) -> Iterator[List[Dict[str, Any]]]:
        """流式生成參數組合"""

        # 預先計算總組合數
        param_names = list(parameter_ranges.keys())
        param_values = list(parameter_ranges.values())

        total_combinations = 1
        for values in param_values:
            total_combinations *= len(values)

        # 限制組合數量
        total_combinations = min(total_combinations, max_combinations)
        self.total_combinations = total_combinations

        logger.info(f"Generating {total_combinations:,} parameter combinations in streaming mode")

        # 使用增量生成避免記憶體爆炸
        if total_combinations > self.chunk_size * 10:
            # 對於大型參數空間，使用智能採樣
            yield from self._generate_intelligent_sample(parameter_ranges, total_combinations)
        else:
            # 對於中小型參數空間，使用標準生成
            yield from self._generate_standard_chunks(parameter_ranges, total_combinations)

    def _generate_intelligent_sample(self,
                                   parameter_ranges: Dict[str, List[Any]],
                                   total_combinations: int) -> Iterator[List[Dict[str, Any]]]:
        """智能採樣生成"""

        # 使用拉丁超立方採樣確保覆蓋率
        n_samples = total_combinations

        # 為每個參數生成採樣點
        param_names = list(parameter_ranges.keys())
        sampled_params = {}

        for param_name, param_values in parameter_ranges.items():
            if len(param_values) <= n_samples:
                # 如果參數值較少，直接使用
                sampled_params[param_name] = param_values
            else:
                # 使用等間距採樣
                indices = np.linspace(0, len(param_values) - 1, n_samples, dtype=int)
                sampled_params[param_name] = [param_values[i] for i in indices]

        # 生成組合
        chunk = []
        for i in range(n_samples):
            param_dict = {}
            for param_name in param_names:
                param_dict[param_name] = sampled_params[param_name][i % len(sampled_params[param_name])]

            chunk.append(param_dict)
            self.generated_count += 1

            if len(chunk) >= self.chunk_size:
                yield chunk
                chunk = []

        if chunk:
            yield chunk

    def _generate_standard_chunks(self,
                                parameter_ranges: Dict[str, List[Any]],
                                total_combinations: int) -> Iterator[List[Dict[str, Any]]]:
        """標準分塊生成"""

        import itertools
        param_names = list(parameter_ranges.keys())
        param_values = list(parameter_ranges.values())

        chunk = []
        for combo in itertools.product(*param_values):
            if self.generated_count >= total_combinations:
                break

            param_dict = dict(zip(param_names, combo))
            chunk.append(param_dict)
            self.generated_count += 1

            if len(chunk) >= self.chunk_size:
                yield chunk
                chunk = []

        if chunk:
            yield chunk

class MemoryOptimizedCache:
    """記憶體優化快取系統"""

    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.memory_cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0}
        self.redis_client = None

        if config.cache_strategy == CacheStrategy.REDIS_CACHE:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host=config.redis_host,
                    port=config.redis_port,
                    db=config.redis_db,
                    decode_responses=False
                )
                self.redis_client.ping()
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using memory cache")
                self.config.cache_strategy = CacheStrategy.MEMORY_CACHE

    def _generate_cache_key(self, params: Dict[str, Any], strategy_hash: str) -> str:
        """生成快取鍵"""
        param_str = json.dumps(params, sort_keys=True)
        combined = f"{strategy_hash}:{param_str}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get_cached_result(self, params: Dict[str, Any], strategy_hash: str) -> Optional[Any]:
        """獲取快取結果"""
        cache_key = self._generate_cache_key(params, strategy_hash)

        if self.config.cache_strategy == CacheStrategy.REDIS_CACHE and self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    self.cache_stats['hits'] += 1
                    return pickle.loads(zlib.decompress(cached_data))
            except Exception as e:
                logger.warning(f"Redis cache get failed: {e}")

        elif cache_key in self.memory_cache:
            self.cache_stats['hits'] += 1
            return self.memory_cache[cache_key]

        self.cache_stats['misses'] += 1
        return None

    def cache_result(self, params: Dict[str, Any], strategy_hash: str, result: Any) -> None:
        """快取結果"""
        cache_key = self._generate_cache_key(params, strategy_hash)

        try:
            serialized = pickle.dumps(result)
            compressed = zlib.compress(serialized)

            # 檢查記憶體限制
            if len(compressed) > self.config.max_cache_size_mb * 1024 * 1024:
                logger.warning(f"Result too large for cache: {len(compressed)} bytes")
                return

            if self.config.cache_strategy == CacheStrategy.REDIS_CACHE and self.redis_client:
                self.redis_client.setex(cache_key, self.config.cache_ttl_seconds, compressed)
            else:
                # 檢查記憶體快取大小
                if len(self.memory_cache) < 10000:  # 限制記憶體快取項目數
                    self.memory_cache[cache_key] = result

        except Exception as e:
            logger.warning(f"Cache set failed: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取快取統計"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / max(1, total_requests)

        stats = {
            'hit_rate': hit_rate,
            'total_requests': total_requests,
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'memory_cache_size': len(self.memory_cache)
        }

        if self.redis_client:
            try:
                info = self.redis_client.info('memory')
                stats['redis_memory_used'] = info.get('used_memory', 0)
                stats['redis_memory_human'] = info.get('used_memory_human', 'N/A')
            except Exception as e:
                logger.warning(f"Redis info failed: {e}")

        return stats

class HighPerformanceOptimizer:
    """高性能參數優化器"""

    def __init__(self, config: Optional[PerformanceConfig] = None):
        self.config = config or PerformanceConfig()
        self.cache = MemoryOptimizedCache(self.config)
        self.streaming_generator = StreamingParameterGenerator(self.config.streaming_chunk_size)
        self.active_jobs = {}
        self.worker_pool = None
        self.resource_monitor = None
        self.load_balancer = None

        # 啟動資源監控
        if self.config.enable_memory_monitoring:
            self._start_resource_monitoring()

        # 初始化工作池
        self._initialize_worker_pool()

    def _initialize_worker_pool(self):
        """初始化工作池"""
        try:
            # 根據系統資源動態調整工作線程數
            cpu_count = mp.cpu_count()
            optimal_workers = min(self.config.max_workers, cpu_count)

            self.worker_pool = ProcessPoolExecutor(max_workers=optimal_workers)
            logger.info(f"Initialized worker pool with {optimal_workers} workers")
        except Exception as e:
            logger.error(f"Failed to initialize worker pool: {e}")
            self.worker_pool = ThreadPoolExecutor(max_workers=4)

    def _start_resource_monitoring(self):
        """啟動資源監控"""
        self.resource_monitor = threading.Thread(target=self._monitor_resources, daemon=True)
        self.resource_monitor.start()

    def _monitor_resources(self):
        """監控系統資源"""
        while True:
            try:
                process = psutil.Process()
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                memory_gb = memory_info.rss / 1024 / 1024 / 1024

                # 如果記憶體使用超過限制，強制垃圾回收
                if memory_gb > self.config.memory_limit_gb * 0.8:
                    logger.warning(f"Memory usage high: {memory_gb:.1f}GB, forcing GC")
                    gc.collect()

                time.sleep(5)  # 每5秒監控一次

            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                time.sleep(10)

    def optimize_large_scale(self,
                           parameter_ranges: Dict[str, List[Any]],
                           objective_func: Callable,
                           strategy_config: Dict[str, Any],
                           max_combinations: int = 1000000) -> Dict[str, Any]:
        """大規模優化 - 支援百萬參數組合"""

        logger.info(f"Starting large-scale optimization with up to {max_combinations:,} combinations")

        start_time = time.time()
        job_id = strategy_config.get('job_id', f"job_{int(start_time)}")

        # 註冊任務
        self.active_jobs[job_id] = {
            'start_time': start_time,
            'status': 'running',
            'total_combinations': 0,
            'tested_combinations': 0,
            'best_score': -float('inf'),
            'best_params': {}
        }

        try:
            # 生成策略哈希用於快取
            strategy_hash = self._generate_strategy_hash(strategy_config)

            # 使用流式處理避免記憶體爆炸
            best_score = -float('inf')
            best_params = {}
            total_tested = 0

            for chunk in self.streaming_generator.generate_streaming_combinations(
                parameter_ranges, max_combinations
            ):
                # 評估當前塊
                chunk_results = self._evaluate_parameter_chunk(
                    chunk, objective_func, strategy_hash
                )

                # 更新最佳結果
                for params, score in chunk_results:
                    if score > best_score:
                        best_score = score
                        best_params = params

                total_tested += len(chunk)

                # 更新進度
                self.active_jobs[job_id].update({
                    'tested_combinations': total_tested,
                    'best_score': best_score,
                    'best_params': best_params
                })

                # 強制垃圾回收釋放記憶體
                if total_tested % (self.config.streaming_chunk_size * 10) == 0:
                    gc.collect()

            # 計算性能指標
            execution_time = time.time() - start_time
            combinations_per_second = total_tested / execution_time if execution_time > 0 else 0

            # 獲取資源指標
            resource_metrics = self._get_resource_metrics()

            result = {
                'job_id': job_id,
                'best_parameters': best_params,
                'best_score': best_score,
                'combinations_tested': total_tested,
                'total_combinations': self.streaming_generator.total_combinations,
                'execution_time_seconds': execution_time,
                'combinations_per_second': combinations_per_second,
                'resource_metrics': resource_metrics,
                'cache_stats': self.cache.get_cache_stats(),
                'strategy_config': strategy_config,
                'completed_at': datetime.now().isoformat()
            }

            # 更新任務狀態
            self.active_jobs[job_id].update({
                'status': 'completed',
                'result': result
            })

            return result

        except Exception as e:
            logger.error(f"Large-scale optimization failed: {e}")
            self.active_jobs[job_id]['status'] = 'failed'
            self.active_jobs[job_id]['error'] = str(e)
            raise

    def _evaluate_parameter_chunk(self,
                                 parameter_chunk: List[Dict[str, Any]],
                                 objective_func: Callable,
                                 strategy_hash: str) -> List[Tuple[Dict[str, Any], float]]:
        """評估參數塊"""

        results = []
        futures = []

        # 提交任務到工作池
        for params in parameter_chunk:
            # 檢查快取
            cached_result = self.cache.get_cached_result(params, strategy_hash)
            if cached_result is not None:
                results.append((params, cached_result))
                continue

            # 提交新任務
            if self.worker_pool:
                future = self.worker_pool.submit(
                    self._safe_evaluate_single, params, objective_func
                )
                futures.append((future, params))

        # 收集結果
        for future, params in futures:
            try:
                score = future.result(timeout=30)  # 30秒超時
                results.append((params, score))

                # 快取結果
                self.cache.cache_result(params, strategy_hash, score)

            except Exception as e:
                logger.warning(f"Parameter evaluation failed: {e}")
                results.append((params, -float('inf')))

        return results

    def _safe_evaluate_single(self, params: Dict[str, Any], objective_func: Callable) -> float:
        """安全地評估單組參數"""
        try:
            return objective_func(params)
        except Exception as e:
            logger.warning(f"Single parameter evaluation failed: {e}")
            return -float('inf')

    def _generate_strategy_hash(self, strategy_config: Dict[str, Any]) -> str:
        """生成策略哈希"""
        config_str = json.dumps(strategy_config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()

    def _get_resource_metrics(self) -> ResourceMetrics:
        """獲取資源指標"""
        try:
            process = psutil.Process()
            cpu_usage = process.cpu_percent()
            memory_info = process.memory_info()
            memory_usage = memory_info.rss / 1024 / 1024 / 1024
            memory_available = psutil.virtual_memory().available / 1024 / 1024 / 1024

            # 計算活躍工作線程數
            active_workers = 0
            if self.worker_pool and hasattr(self.worker_pool, '_max_workers'):
                active_workers = self.worker_pool._max_workers

            return ResourceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                memory_available_gb=memory_available,
                active_workers=active_workers,
                queue_depth=len(self.active_jobs),
                combinations_per_second=0.0,  # 需要從其他地方計算
                cache_hit_rate=self.cache.get_cache_stats()['hit_rate']
            )
        except Exception as e:
            logger.error(f"Failed to get resource metrics: {e}")
            return ResourceMetrics(0, 0, 0, 0, 0, 0, 0)

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """獲取任務狀態"""
        return self.active_jobs.get(job_id)

    def get_performance_stats(self) -> Dict[str, Any]:
        """獲取性能統計"""
        stats = {
            'active_jobs': len(self.active_jobs),
            'cache_stats': self.cache.get_cache_stats(),
            'resource_metrics': self._get_resource_metrics(),
            'config': {
                'max_workers': self.config.max_workers,
                'memory_limit_gb': self.config.memory_limit_gb,
                'cache_strategy': self.config.cache_strategy.value,
                'streaming_chunk_size': self.config.streaming_chunk_size
            }
        }

        # 添加任務統計
        completed_jobs = sum(1 for job in self.active_jobs.values() if job.get('status') == 'completed')
        failed_jobs = sum(1 for job in self.active_jobs.values() if job.get('status') == 'failed')
        running_jobs = sum(1 for job in self.active_jobs.values() if job.get('status') == 'running')

        stats['job_stats'] = {
            'total': len(self.active_jobs),
            'completed': completed_jobs,
            'failed': failed_jobs,
            'running': running_jobs
        }

        return stats

    def cleanup(self):
        """清理資源"""
        if self.worker_pool:
            self.worker_pool.shutdown(wait=True)

        if self.redis_client:
            self.redis_client.close()

        logger.info("High-performance optimizer cleanup completed")

# 全局實例
_high_perf_optimizer = None

def get_high_performance_optimizer(config: Optional[PerformanceConfig] = None) -> HighPerformanceOptimizer:
    """獲取高性能優化器實例"""
    global _high_perf_optimizer
    if _high_perf_optimizer is None:
        _high_perf_optimizer = HighPerformanceOptimizer(config)
    return _high_perf_optimizer

async def optimize_with_high_performance(parameter_ranges: Dict[str, List[Any]],
                                      objective_func: Callable,
                                      strategy_config: Dict[str, Any],
                                      max_combinations: int = 1000000) -> Dict[str, Any]:
    """高性能優化接口"""
    optimizer = get_high_performance_optimizer()

    # 在異步上下文中運行同步優化
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        optimizer.optimize_large_scale,
        parameter_ranges,
        objective_func,
        strategy_config,
        max_combinations
    )

    return result