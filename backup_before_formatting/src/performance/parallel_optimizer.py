#!/usr/bin/env python3
"""
并行优化器
专门用于VectorBT大规模参数优化和并行回测
"""

import logging
import multiprocessing as mp
import os
import numpy as np
import pandas as pd
import asyncio
import time
import psutil
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Callable, Iterator
from dataclasses import dataclass, field
from functools import lru_cache, partial
import pickle
import hashlib
import gc
import threading
from queue import Queue, Empty
import json

from .vectorbt_engine import VectorBTComputeEngine, BacktestConfig, OptimizationResult

logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """优化配置"""
    max_processes: Optional[int] = None
    use_threading: bool = False
    chunk_size: int = 10
    memory_limit: float = 0.8  # 80%内存使用限制
    cache_enabled: bool = True
    gpu_acceleration: bool = False
    timeout_per_task: int = 300  # 5分钟超时
    progress_callback: Optional[Callable] = None
    error_handling: str = "continue"  # "continue", "stop", "retry"
    max_retries: int = 3


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    parameters: Dict[str, Any]
    result: Optional[Any]
    execution_time: float
    memory_usage: float
    success: bool
    error_message: Optional[str] = None


class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self, memory_limit: float = 0.8):
        self.memory_limit = memory_limit
        self.process = psutil.Process()
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """开始监控内存使用"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_memory, daemon=True)
            self.monitor_thread.start()
            
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
            
    def _monitor_memory(self):
        """内存监控线程"""
        while self.monitoring:
            try:
                memory_percent = self.process.memory_percent()
                if memory_percent > self.memory_limit * 100:
                    logger.warning(f"内存使用过高: {memory_percent:.1f}% > {self.memory_limit * 100}%")
                    # 强制垃圾回收
                    gc.collect()
                    time.sleep(5)  # 给GC一些时间
                time.sleep(1)
            except Exception as e:
                logger.error(f"内存监控错误: {e}")
                break
                
    def get_memory_usage(self) -> float:
        """获取当前内存使用率"""
        return self.process.memory_percent() / 100.0


class TaskDistributor:
    """任务分发器"""
    
    def __init__(self, tasks: List[Dict[str, Any]], chunk_size: int = 10):
        self.tasks = tasks
        self.chunk_size = chunk_size
        self.task_queue = Queue()
        self.completed_tasks = set()
        self.failed_tasks = set()
        
    def create_chunks(self) -> List[List[Dict[str, Any]]]:
        """创建任务块"""
        chunks = []
        for i in range(0, len(self.tasks), self.chunk_size):
            chunk = self.tasks[i:i + self.chunk_size]
            chunks.append(chunk)
        return chunks
        
    def get_next_chunk(self) -> Optional[List[Dict[str, Any]]]:
        """获取下一个任务块"""
        try:
            chunk = self.task_queue.get_nowait()
            return chunk
        except Empty:
            return None
            
    def setup_queue(self):
        """设置任务队列"""
        chunks = self.create_chunks()
        for chunk in chunks:
            self.task_queue.put(chunk)
            
    def mark_completed(self, task_ids: List[str]):
        """标记任务完成"""
        self.completed_tasks.update(task_ids)
        
    def mark_failed(self, task_ids: List[str]):
        """标记任务失败"""
        self.failed_tasks.update(task_ids)
        
    def get_progress(self) -> Tuple[int, int, int]:
        """获取进度 (完成, 失败, 总计)"""
        total = len(self.tasks)
        completed = len(self.completed_tasks)
        failed = len(self.failed_tasks)
        return completed, failed, total


class ParallelOptimizer:
    """并行优化器"""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.memory_monitor = MemoryMonitor(config.memory_limit)
        self.vectorbt_engine = VectorBTComputeEngine(
            max_processes=config.max_processes,
            use_gpu=config.gpu_acceleration,
            cache_enabled=config.cache_enabled
        )
        self._setup_process_pool()
        
    def _setup_process_pool(self):
        """设置进程池"""
        if self.config.use_threading:
            self.executor_class = ThreadPoolExecutor
            self.max_workers = self.config.max_processes or min(32, (os.cpu_count() or 1) * 4)
        else:
            self.executor_class = ProcessPoolExecutor
            self.max_workers = self.config.max_processes or min(os.cpu_count(), 8)
            
    def optimize_parameters_parallel(self,
                                   symbols: List[str],
                                   price_data: Dict[str, pd.DataFrame],
                                   economic_data: Dict[str, pd.DataFrame],
                                   param_grid: Dict[str, List[Any]],
                                   backtest_config: BacktestConfig) -> List[OptimizationResult]:
        """并行参数优化"""
        logger.info(f"开始并行参数优化，标的数量: {len(symbols)}, 参数组合数: {self._count_combinations(param_grid)}")
        
        # 开始内存监控
        self.memory_monitor.start_monitoring()
        
        try:
            # 生成参数组合
            param_combinations = self._generate_param_combinations(param_grid)
            if not param_combinations:
                logger.warning("无有效参数组合")
                return []
            
            # 创建任务
            tasks = []
            for i, params in enumerate(param_combinations):
                task = {
                    'task_id': f"opt_{i}",
                    'parameters': params,
                    'symbols': symbols[:5],  # 限制标的数量以提高速度
                    'price_data': price_data,
                    'economic_data': economic_data,
                    'backtest_config': backtest_config
                }
                tasks.append(task)
            
            # 分发并执行任务
            results = self._execute_tasks(tasks)
            
            # 转换结果格式
            optimization_results = []
            for task_result in results:
                if task_result.success and task_result.result:
                    optimization_results.append(task_result.result)
            
            # 按质量评分排序
            optimization_results.sort(key=lambda x: x.quality_score, reverse=True)
            
            logger.info(f"并行参数优化完成，有效结果: {len(optimization_results)}/{len(tasks)}")
            return optimization_results
            
        except Exception as e:
            logger.error(f"并行参数优化失败: {e}")
            return []
        finally:
            self.memory_monitor.stop_monitoring()
    
    def batch_backtest_parallel(self,
                               symbols: List[str],
                               price_data: Dict[str, pd.DataFrame],
                               signals: Dict[str, pd.DataFrame],
                               backtest_config: BacktestConfig) -> Dict[str, Any]:
        """批量并行回测"""
        logger.info(f"开始批量并行回测，标的数量: {len(symbols)}")
        
        self.memory_monitor.start_monitoring()
        
        try:
            # 创建回测任务
            tasks = []
            for symbol in symbols:
                if symbol in price_data and symbol in signals:
                    task = {
                        'task_id': f"bt_{symbol}",
                        'symbol': symbol,
                        'price_data': price_data[symbol],
                        'signals': signals[symbol],
                        'backtest_config': backtest_config
                    }
                    tasks.append(task)
            
            # 分发并执行任务
            task_results = self._execute_tasks(tasks)
            
            # 收集回测结果
            backtest_results = {}
            successful_count = 0
            
            for task_result in task_results:
                if task_result.success and task_result.result:
                    symbol = task_result.parameters.get('symbol', task_result.task_id.replace('bt_', ''))
                    backtest_results[symbol] = task_result.result
                    successful_count += 1
                else:
                    logger.warning(f"回测失败: {task_result.task_id} - {task_result.error_message}")
            
            # 生成汇总报告
            summary = self._generate_backtest_summary(backtest_results, successful_count, len(tasks))
            
            logger.info(f"批量并行回测完成，成功: {successful_count}/{len(tasks)}")
            return {
                'results': backtest_results,
                'summary': summary,
                'success_rate': successful_count / len(tasks) if tasks else 0
            }
            
        except Exception as e:
            logger.error(f"批量并行回测失败: {e}")
            return {}
        finally:
            self.memory_monitor.stop_monitoring()
    
    def _execute_tasks(self, tasks: List[Dict[str, Any]]) -> List[TaskResult]:
        """执行任务列表"""
        results = []
        
        # 设置任务分发器
        task_distributor = TaskDistributor(tasks, self.config.chunk_size)
        task_distributor.setup_queue()
        
        with self.executor_class(max_workers=self.max_workers) as executor:
            futures = []
            
            # 提交任务
            while True:
                chunk = task_distributor.get_next_chunk()
                if chunk is None:
                    break
                
                # 提交任务块
                future = executor.submit(self._execute_task_chunk, chunk)
                futures.append((future, [task['task_id'] for task in chunk]))
            
            # 收集结果
            for future, task_ids in futures:
                try:
                    chunk_results = future.result(timeout=self.config.timeout_per_task * len(task_ids))
                    
                    # 处理任务块结果
                    for task_result in chunk_results:
                        results.append(task_result)
                        
                        # 更新任务状态
                        if task_result.success:
                            task_distributor.mark_completed([task_result.task_id])
                        else:
                            task_distributor.mark_failed([task_result.task_id])
                    
                    # 进度回调
                    if self.config.progress_callback:
                        completed, failed, total = task_distributor.get_progress()
                        progress = (completed + failed) / total
                        self.config.progress_callback(progress, completed, failed, total)
                        
                except Exception as e:
                    logger.error(f"任务块执行失败: {e}")
                    # 标记所有任务为失败
                    task_distributor.mark_failed(task_ids)
                    
                    # 创建失败结果
                    for task_id in task_ids:
                        results.append(TaskResult(
                            task_id=task_id,
                            parameters={},
                            result=None,
                            execution_time=0,
                            memory_usage=0,
                            success=False,
                            error_message=str(e)
                        ))
        
        return results
    
    def _execute_task_chunk(self, tasks: List[Dict[str, Any]]) -> List[TaskResult]:
        """执行任务块"""
        chunk_results = []
        start_memory = self.memory_monitor.get_memory_usage()
        
        for task in tasks:
            try:
                task_start_time = time.time()
                
                # 执行具体任务
                if task['task_id'].startswith('opt_'):
                    result = self._execute_optimization_task(task)
                elif task['task_id'].startswith('bt_'):
                    result = self._execute_backtest_task(task)
                else:
                    raise ValueError(f"未知任务类型: {task['task_id']}")
                
                execution_time = time.time() - task_start_time
                end_memory = self.memory_monitor.get_memory_usage()
                
                chunk_results.append(TaskResult(
                    task_id=task['task_id'],
                    parameters=task,
                    result=result,
                    execution_time=execution_time,
                    memory_usage=end_memory - start_memory,
                    success=True
                ))
                
            except Exception as e:
                logger.error(f"任务执行失败 {task['task_id']}: {e}")
                
                chunk_results.append(TaskResult(
                    task_id=task['task_id'],
                    parameters=task,
                    result=None,
                    execution_time=0,
                    memory_usage=0,
                    success=False,
                    error_message=str(e)
                ))
                
                # 错误处理策略
                if self.config.error_handling == "stop":
                    break
                elif self.config.error_handling == "retry":
                    # 简单重试机制（可以扩展）
                    continue
        
        # 强制垃圾回收
        gc.collect()
        
        return chunk_results
    
    def _execute_optimization_task(self, task: Dict[str, Any]) -> Optional[OptimizationResult]:
        """执行优化任务"""
        try:
            # 调用VectorBT引擎的优化功能
            result = self.vectorbt_engine._optimize_single_param_set(
                symbols=task['symbols'],
                price_data=task['price_data'],
                economic_data=task['economic_data'],
                params=task['parameters'],
                config=task['backtest_config']
            )
            
            return result
            
        except Exception as e:
            logger.error(f"优化任务失败 {task['task_id']}: {e}")
            raise
    
    def _execute_backtest_task(self, task: Dict[str, Any]) -> Optional[Any]:
        """执行回测任务"""
        try:
            # 调用VectorBT引擎的回测功能
            result = self.vectorbt_engine._backtest_single_symbol(
                symbol=task['symbol'],
                price_data=task['price_data'],
                signals=task['signals'],
                config=task['backtest_config']
            )
            
            return result
            
        except Exception as e:
            logger.error(f"回测任务失败 {task['task_id']}: {e}")
            raise
    
    def _generate_backtest_summary(self, 
                                 backtest_results: Dict[str, Any],
                                 successful_count: int,
                                 total_count: int) -> Dict[str, Any]:
        """生成回测汇总"""
        try:
            if not backtest_results:
                return {'status': 'no_results'}
            
            # 收集所有指标
            all_metrics = []
            sharpe_ratios = []
            total_returns = []
            max_drawdowns = []
            
            for symbol, result in backtest_results.items():
                if hasattr(result, 'metrics'):
                    metrics = result.metrics
                    all_metrics.append(metrics)
                    
                    sharpe_ratios.append(metrics.get('sharpe_ratio', 0))
                    total_returns.append(metrics.get('total_return', 0))
                    max_drawdowns.append(metrics.get('max_drawdown', 0))
            
            if not all_metrics:
                return {'status': 'no_metrics'}
            
            # 计算汇总统计
            summary = {
                'status': 'success',
                'successful_backtests': successful_count,
                'total_backtests': total_count,
                'success_rate': successful_count / total_count,
                
                # 性能统计
                'avg_sharpe_ratio': np.mean(sharpe_ratios),
                'median_sharpe_ratio': np.median(sharpe_ratios),
                'best_sharpe_ratio': max(sharpe_ratios) if sharpe_ratios else 0,
                'worst_sharpe_ratio': min(sharpe_ratios) if sharpe_ratios else 0,
                
                'avg_total_return': np.mean(total_returns),
                'median_total_return': np.median(total_returns),
                'best_total_return': max(total_returns) if total_returns else 0,
                'worst_total_return': min(total_returns) if total_returns else 0,
                
                'avg_max_drawdown': np.mean(max_drawdowns),
                'worst_max_drawdown': max(max_drawdowns) if max_drawdowns else 0,
                
                # 胜率统计
                'positive_sharpe_count': sum(1 for r in sharpe_ratios if r > 0),
                'positive_return_count': sum(1 for r in total_returns if r > 0),
                'profitable_strategies': sum(1 for r in total_returns if r > 0.1),  # 10%以上收益
                
                # 风险统计
                'high_drawdown_count': sum(1 for r in max_drawdowns if abs(r) > 0.2),  # 20%以上回撤
                'volatility_analysis': {
                    'sharpe_volatility': np.std(sharpe_ratios) if sharpe_ratios else 0,
                    'return_volatility': np.std(total_returns) if total_returns else 0,
                }
            }
            
            # 添加最佳和最差策略信息
            if total_returns:
                best_idx = np.argmax(total_returns)
                worst_idx = np.argmin(total_returns)
                
                summary['best_strategy'] = {
                    'symbol': list(backtest_results.keys())[best_idx],
                    'sharpe_ratio': sharpe_ratios[best_idx],
                    'total_return': total_returns[best_idx],
                    'max_drawdown': max_drawdowns[best_idx]
                }
                
                summary['worst_strategy'] = {
                    'symbol': list(backtest_results.keys())[worst_idx],
                    'sharpe_ratio': sharpe_ratios[worst_idx],
                    'total_return': total_returns[worst_idx],
                    'max_drawdown': max_drawdowns[worst_idx]
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"生成回测汇总失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _count_combinations(self, param_grid: Dict[str, List[Any]]) -> int:
        """计算参数组合数量"""
        if not param_grid:
            return 0
        
        count = 1
        for values in param_grid.values():
            count *= len(values)
        
        return count
    
    def _generate_param_combinations(self, param_grid: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """生成参数组合"""
        if not param_grid:
            return []
        
        import itertools
        
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        combinations = []
        for combination in itertools.product(*values):
            param_dict = dict(zip(keys, combination))
            combinations.append(param_dict)
        
        return combinations
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            'memory_usage': self.memory_monitor.get_memory_usage(),
            'max_workers': self.max_workers,
            'executor_type': 'ThreadPoolExecutor' if self.config.use_threading else 'ProcessPoolExecutor',
            'gpu_acceleration': self.config.gpu_acceleration,
            'cache_enabled': self.config.cache_enabled
        }
    
    def cleanup(self):
        """清理资源"""
        self.memory_monitor.stop_monitoring()
        self.vectorbt_engine.clear_cache()
        gc.collect()


# 便利函数
def create_parallel_optimizer(max_processes: Optional[int] = None,
                             use_threading: bool = False,
                             gpu_acceleration: bool = False) -> ParallelOptimizer:
    """创建并行优化器的便利函数"""
    config = OptimizationConfig(
        max_processes=max_processes,
        use_threading=use_threading,
        gpu_acceleration=gpu_acceleration
    )
    return ParallelOptimizer(config)


def optimize_strategy_parameters(symbols: List[str],
                               price_data: Dict[str, pd.DataFrame],
                               economic_data: Dict[str, pd.DataFrame],
                               param_grid: Dict[str, List[Any]],
                               backtest_config: BacktestConfig,
                               **kwargs) -> List[OptimizationResult]:
    """策略参数优化的便利函数"""
    optimizer = create_parallel_optimizer(**kwargs)
    return optimizer.optimize_parameters_parallel(
        symbols, price_data, economic_data, param_grid, backtest_config
    )


def batch_backtest_strategies(symbols: List[str],
                             price_data: Dict[str, pd.DataFrame],
                             signals: Dict[str, pd.DataFrame],
                             backtest_config: BacktestConfig,
                             **kwargs) -> Dict[str, Any]:
    """批量回测策略的便利函数"""
    optimizer = create_parallel_optimizer(**kwargs)
    return optimizer.batch_backtest_parallel(
        symbols, price_data, signals, backtest_config
    )