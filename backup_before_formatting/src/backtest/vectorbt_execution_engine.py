#!/usr/bin/env python3
"""
VectorBT執行引擎 - 高性能並行回測執行
VectorBT Execution Engine - High-performance parallel backtesting
"""

import logging
import asyncio
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import vectorbt as vbt
from functools import partial
import time
import psutil

logger = logging.getLogger(__name__)


@dataclass
class BacktestTask:
    """回測任務定義"""
    task_id: str
    symbol: str
    parameters: Dict[str, Any]
    data: pd.DataFrame
    economic_data: Dict[str, pd.DataFrame] = field(default_factory=dict)
    priority: int = 0  # 任務優先級，數字越大優先級越高


@dataclass
class ExecutionResult:
    """執行結果"""
    task_id: str
    symbol: str
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    performance_stats: Dict[str, Any] = field(default_factory=dict)


class VectorBTParallelExecutor:
    """VectorBT並行執行器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_workers = self.config.get('max_workers', mp.cpu_count() - 1)
        self.chunk_size = self.config.get('chunk_size', 100)
        self.use_memory_mapping = self.config.get('use_memory_mapping', True)
        self.enable_profiling = self.config.get('enable_profiling', False)
        
        # 性能監控
        self.performance_metrics = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'total_execution_time': 0.0,
            'average_task_time': 0.0,
            'parallel_efficiency': 0.0,
            'memory_usage_mb': 0.0,
            'cpu_utilization': 0.0
        }
        
        # 任務隊列管理
        self.task_queue = asyncio.Queue()
        self.result_queue = asyncio.Queue()
        self.active_workers = set()
        
        logger.info(f"VectorBT Parallel Executor initialized with {self.max_workers} workers")
    
    async def execute_backtest_batch(self, 
                                   tasks: List[BacktestTask],
                                   execution_mode: str = 'multiprocess') -> List[ExecutionResult]:
        """
        批量執行回測任務
        
        Args:
            tasks: 回測任務列表
            execution_mode: 執行模式 ('multiprocess', 'multithread', 'async')
        
        Returns:
            執行結果列表
        """
        logger.info(f"Starting batch execution with {len(tasks)} tasks using {execution_mode}")
        
        self.performance_metrics['total_tasks'] = len(tasks)
        start_time = time.time()
        
        # 根據執行模式選擇執行器
        if execution_mode == 'multiprocess':
            results = await self._execute_multiprocess(tasks)
        elif execution_mode == 'multithread':
            results = await self._execute_multithread(tasks)
        elif execution_mode == 'async':
            results = await self._execute_async(tasks)
        else:
            raise ValueError(f"Unsupported execution mode: {execution_mode}")
        
        # 更新性能指標
        total_time = time.time() - start_time
        self.performance_metrics['total_execution_time'] = total_time
        self.performance_metrics['completed_tasks'] = len([r for r in results if r.success])
        self.performance_metrics['failed_tasks'] = len([r for r in results if not r.success])
        
        if results:
            self.performance_metrics['average_task_time'] = (
                sum(r.execution_time for r in results) / len(results)
            )
            
            # 計算並行效率
            serial_time_estimate = sum(r.execution_time for r in results)
            self.performance_metrics['parallel_efficiency'] = serial_time_estimate / (total_time * self.max_workers)
        
        logger.info(f"Batch execution completed in {total_time:.2f}s - "
                   f"{self.performance_metrics['completed_tasks']}/{len(tasks)} successful")
        
        return results
    
    async def _execute_multiprocess(self, tasks: List[BacktestTask]) -> List[ExecutionResult]:
        """多進程執行"""
        # 將任務分塊以減少進程間通信開銷
        task_chunks = self._chunk_tasks(tasks, self.chunk_size)
        
        results = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任務塊
            future_to_chunk = {
                executor.submit(self._execute_task_chunk, chunk): chunk 
                for chunk in task_chunks
            }
            
            # 收集結果
            for future in as_completed(future_to_chunk):
                try:
                    chunk_results = future.result()
                    results.extend(chunk_results)
                except Exception as e:
                    chunk = future_to_chunk[future]
                    logger.error(f"Task chunk failed: {e}")
                    # 為失敗的塊創建錯誤結果
                    for task in chunk:
                        results.append(ExecutionResult(
                            task_id=task.task_id,
                            symbol=task.symbol,
                            parameters=task.parameters,
                            metrics={},
                            execution_time=0.0,
                            success=False,
                            error_message=str(e)
                        ))
        
        return results
    
    async def _execute_multithread(self, tasks: List[BacktestTask]) -> List[ExecutionResult]:
        """多線程執行"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任務
            future_to_task = {
                executor.submit(self._execute_single_task, task): task 
                for task in tasks
            }
            
            # 收集結果
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Task {task.task_id} failed: {e}")
                    results.append(ExecutionResult(
                        task_id=task.task_id,
                        symbol=task.symbol,
                        parameters=task.parameters,
                        metrics={},
                        execution_time=0.0,
                        success=False,
                        error_message=str(e)
                    ))
        
        return results
    
    async def _execute_async(self, tasks: List[BacktestTask]) -> List[ExecutionResult]:
        """異步執行"""
        # 創建信號量控制並發數
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def execute_with_semaphore(task):
            async with semaphore:
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._execute_single_task, task
                )
        
        # 並行執行所有任務
        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )
        
        # 處理結果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task = tasks[i]
                logger.error(f"Async task {task.task_id} failed: {result}")
                processed_results.append(ExecutionResult(
                    task_id=task.task_id,
                    symbol=task.symbol,
                    parameters=task.parameters,
                    metrics={},
                    execution_time=0.0,
                    success=False,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _chunk_tasks(self, tasks: List[BacktestTask], chunk_size: int) -> List[List[BacktestTask]]:
        """將任務分塊"""
        chunks = []
        for i in range(0, len(tasks), chunk_size):
            chunks.append(tasks[i:i + chunk_size])
        return chunks
    
    @staticmethod
    def _execute_task_chunk(tasks: List[BacktestTask]) -> List[ExecutionResult]:
        """執行任務塊（在進程中運行）"""
        results = []
        for task in tasks:
            try:
                result = VectorBTParallelExecutor._execute_single_task(task)
                results.append(result)
            except Exception as e:
                logger.error(f"Task {task.task_id} in chunk failed: {e}")
                results.append(ExecutionResult(
                    task_id=task.task_id,
                    symbol=task.symbol,
                    parameters=task.parameters,
                    metrics={},
                    execution_time=0.0,
                    success=False,
                    error_message=str(e)
                ))
        return results
    
    @staticmethod
    def _execute_single_task(task: BacktestTask) -> ExecutionResult:
        """執行單個回測任務"""
        start_time = time.time()
        
        try:
            # 提取價格數據
            if 'close' not in task.data.columns:
                raise ValueError("Price data must have 'close' column")
            
            close_prices = task.data['close'].dropna()
            if len(close_prices) < 20:  # 最少需要20個數據點
                raise ValueError(f"Insufficient data points: {len(close_prices)}")
            
            # 準備技術指標參數
            params = task.parameters
            
            # VectorBT RSI策略實現
            rsi_indicator = vbt.RSI.run(close_prices, window=params.get('window', 14))
            rsi_values = rsi_indicator.rsi
            
            # 生成交易信號（一買一賣邏輯）
            buy_signals = (rsi_values < params.get('buy_threshold', 30)) & (~(rsi_values.shift(1) < params.get('buy_threshold', 30)))
            sell_signals = (rsi_values > params.get('sell_threshold', 70)) & (~(rsi_values.shift(1) > params.get('sell_threshold', 70)))
            
            # 確保一買一賣配對
            # 簡化版本：直接使用原始信號
            entries = buy_signals
            exits = sell_signals
            
            # 執行回測
            portfolio = vbt.Portfolio.from_signals(
                close=close_prices,
                entries=entries,
                exits=exits,
                init_cash=100000,  # 初始資金10萬
                fees=0.001,        # 0.1%手續費
                slippage=0.0005,   # 0.05%滑點
            )
            
            # 計算性能指標
            returns = portfolio.returns()
            stats = portfolio.stats()
            
            # 計算Sharpe比率（3%無風險利率）
            risk_free_rate = 0.03
            excess_returns = returns - risk_free_rate / 252
            sharpe_ratio = excess_returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
            
            # 計算其他指標
            total_return = portfolio.total_return()
            max_drawdown = portfolio.max_drawdown()
            win_rate = portfolio.trades.win_rate()
            profit_factor = portfolio.trades.profit_factor()
            
            # 計算交易次數（確保一買一賣）
            num_trades = len(portfolio.trades.records_readable)
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                task_id=task.task_id,
                symbol=task.symbol,
                parameters=params,
                metrics={
                    'total_return': float(total_return),
                    'sharpe_ratio': float(sharpe_ratio),
                    'max_drawdown': float(max_drawdown),
                    'win_rate': float(win_rate),
                    'profit_factor': float(profit_factor),
                    'num_trades': int(num_trades),
                    'avg_return': float(returns.mean() * 252),
                    'volatility': float(returns.std() * np.sqrt(252)),
                    'calmar_ratio': float(total_return / abs(max_drawdown)) if max_drawdown != 0 else 0.0
                },
                execution_time=execution_time,
                success=True,
                performance_stats={
                    'data_points': len(close_prices),
                    'signals_generated': int(buy_signals.sum() + sell_signals.sum()),
                    'portfolio_value': float(portfolio.value()[-1]) if len(portfolio.value()) > 0 else 100000.0
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Task {task.task_id} execution failed: {e}")
            
            return ExecutionResult(
                task_id=task.task_id,
                symbol=task.symbol,
                parameters=task.parameters,
                metrics={},
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
    
    def create_parameter_grid(self, param_ranges: Dict[str, range]) -> List[Dict[str, Any]]:
        """
        創建參數網格
        
        Args:
            param_ranges: 參數範圍字典，例如 {'fast': range(5, 50, 5), 'slow': range(20, 100, 10)}
        
        Returns:
            參數組合列表
        """
        import itertools
        
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        
        # 生成所有參數組合
        combinations = itertools.product(*param_values)
        
        # 轉換為字典格式
        param_combinations = [
            dict(zip(param_names, combo)) 
            for combo in combinations
        ]
        
        logger.info(f"Generated {len(param_combinations)} parameter combinations")
        return param_combinations
    
    def optimize_parameters(self, 
                           symbol: str,
                           data: pd.DataFrame,
                           param_ranges: Dict[str, range],
                           optimization_metric: str = 'sharpe_ratio',
                           execution_mode: str = 'multiprocess') -> Dict[str, Any]:
        """
        參數優化
        
        Args:
            symbol: 股票代碼
            data: 價格數據
            param_ranges: 參數範圍
            optimization_metric: 優化目標指標
            execution_mode: 執行模式
        
        Returns:
            優化結果
        """
        logger.info(f"Starting parameter optimization for {symbol}")
        
        # 生成參數組合
        param_combinations = self.create_parameter_grid(param_ranges)
        
        # 創建任務
        tasks = []
        for i, params in enumerate(param_combinations):
            task = BacktestTask(
                task_id=f"{symbol}_opt_{i}",
                symbol=symbol,
                parameters=params,
                data=data
            )
            tasks.append(task)
        
        # 執行批量回測
        start_time = time.time()
        results = asyncio.run(self.execute_backtest_batch(tasks, execution_mode))
        optimization_time = time.time() - start_time
        
        # 分析結果
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            logger.error("No successful backtest results for optimization")
            return {
                'success': False,
                'error': 'All backtest tasks failed',
                'total_combinations': len(param_combinations),
                'successful_combinations': 0
            }
        
        # 找到最佳參數
        best_result = max(successful_results, key=lambda r: r.metrics.get(optimization_metric, 0))
        
        # 統計分析
        metric_values = [r.metrics.get(optimization_metric, 0) for r in successful_results]
        
        optimization_summary = {
            'success': True,
            'symbol': symbol,
            'total_combinations': len(param_combinations),
            'successful_combinations': len(successful_results),
            'optimization_time': optimization_time,
            'best_parameters': best_result.parameters,
            'best_performance': best_result.metrics,
            'optimization_metric': optimization_metric,
            'performance_statistics': {
                'mean': np.mean(metric_values),
                'std': np.std(metric_values),
                'min': np.min(metric_values),
                'max': np.max(metric_values),
                'median': np.median(metric_values)
            },
            'execution_statistics': self.performance_metrics
        }
        
        logger.info(f"Optimization completed for {symbol}: "
                   f"Best {optimization_metric}={best_result.metrics.get(optimization_metric, 0):.4f}")
        
        return optimization_summary
    
    def get_performance_report(self) -> Dict[str, Any]:
        """獲取性能報告"""
        current_memory = psutil.virtual_memory().used / (1024 * 1024)  # MB
        current_cpu = psutil.cpu_percent()
        
        return {
            'execution_metrics': self.performance_metrics,
            'system_resources': {
                'current_memory_mb': current_memory,
                'current_cpu_percent': current_cpu,
                'max_workers': self.max_workers
            },
            'efficiency_analysis': {
                'tasks_per_second': (
                    self.performance_metrics['completed_tasks'] / max(1, self.performance_metrics['total_execution_time'])
                ),
                'parallel_efficiency': self.performance_metrics['parallel_efficiency'],
                'success_rate': (
                    self.performance_metrics['completed_tasks'] / max(1, self.performance_metrics['total_tasks'])
                )
            }
        }


class AdaptiveExecutionManager:
    """自適應執行管理器 - 根據系統負載動態調整執行策略"""
    
    def __init__(self, base_config: Optional[Dict[str, Any]] = None):
        self.base_config = base_config or {}
        self.executor = None
        self.monitoring_enabled = True
        self.load_history = []
        
    def get_optimal_worker_count(self) -> int:
        """根據當前系統負載確定最優工作進程數"""
        current_cpu = psutil.cpu_percent(interval=1)
        current_memory = psutil.virtual_memory().percent
        
        # 基於CPU和內存使用率調整
        cpu_workers = max(1, int(mp.cpu_count() * (1 - current_cpu / 100)))
        memory_workers = max(1, int(mp.cpu_count() * (1 - current_memory / 100)))
        
        # 取較小值以避免過載
        optimal_workers = min(cpu_workers, memory_workers, mp.cpu_count() - 1)
        
        # 保存負載歷史
        self.load_history.append({
            'timestamp': datetime.now(),
            'cpu_percent': current_cpu,
            'memory_percent': current_memory,
            'optimal_workers': optimal_workers
        })
        
        # 只保留最近100條記錄
        self.load_history = self.load_history[-100:]
        
        return optimal_workers
    
    def should_use_multiprocess(self, task_count: int) -> bool:
        """決定是否使用多進程"""
        # 少量任務使用多線程，大量任務使用多進程
        return task_count > 10
    
    async def execute_with_adaptive_strategy(self, 
                                            tasks: List[BacktestTask]) -> List[ExecutionResult]:
        """使用自適應策略執行任務"""
        # 動態確定配置
        optimal_workers = self.get_optimal_worker_count()
        use_multiprocess = self.should_use_multiprocess(len(tasks))
        execution_mode = 'multiprocess' if use_multiprocess else 'multithread'
        
        # 更新執行器配置
        adaptive_config = self.base_config.copy()
        adaptive_config.update({
            'max_workers': optimal_workers,
            'execution_mode': execution_mode
        })
        
        logger.info(f"Adaptive execution: {execution_mode} with {optimal_workers} workers")
        
        # 創建執行器並執行
        self.executor = VectorBTParallelExecutor(adaptive_config)
        return await self.executor.execute_backtest_batch(tasks, execution_mode)