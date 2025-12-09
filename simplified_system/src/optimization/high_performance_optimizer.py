"""
高性能并行优化引擎
实现32核并行处理，目标2000+策略/秒
"""

import asyncio
import multiprocessing as mp
import concurrent.futures
import time
import logging
from typing import Dict, List, Any, Tuple, Optional, Callable
from dataclasses import dataclass, field
from functools import partial
import numpy as np
import pandas as pd
from queue import Queue, Empty
import threading
import psutil
import gc

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class OptimizationTask:
    """优化任务"""
    task_id: str
    strategy_name: str
    parameters: Dict[str, Any]
    data: pd.DataFrame
    priority: int = 1
    created_at: float = field(default_factory=time.time)

@dataclass
class OptimizationResult:
    """优化结果"""
    task_id: str
    strategy_name: str
    parameters: Dict[str, Any]
    sharpe_ratio: float
    total_return: float
    max_drawdown: float
    win_rate: float
    execution_time: float
    error: Optional[str] = None

@dataclass
class PerformanceMetrics:
    """性能指标"""
    tasks_completed: int = 0
    total_execution_time: float = 0.0
    tasks_per_second: float = 0.0
    avg_execution_time: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    cache_hit_rate: float = 0.0

class HighPerformanceOptimizer:
    """高性能并行优化引擎"""
    
    def __init__(self, max_workers: int = None, chunk_size: int = 100):
        self.cpu_count = mp.cpu_count()
        self.max_workers = max_workers or min(32, self.cpu_count * 4)  # 最多32个worker
        self.chunk_size = chunk_size
        
        logger.info(f"Initializing optimizer with {self.max_workers} workers on {self.cpu_count} CPU cores")
        
        # 任务队列和结果存储
        self.task_queue = asyncio.Queue()
        self.result_queue = asyncio.Queue()
        self.priority_queue = asyncio.PriorityQueue()
        
        # 性能缓存
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # 性能统计
        self.metrics = PerformanceMetrics()
        self.start_time = time.time()
        
        # 运行状态
        self._running = False
        self._workers = []
        
        # 优化参数空间
        self.parameter_spaces = self._generate_parameter_spaces()
        
        # 内存管理
        self.memory_threshold = 0.85  # 85%内存使用率阈值
        self.cleanup_interval = 100   # 每100个任务清理一次
        
    def _generate_parameter_spaces(self) -> Dict[str, Dict[str, List[Any]]]:
        """生成参数空间配置"""
        return {
            'RSI': {
                'period': list(range(5, 51)),
                'oversold': list(range(20, 41)),
                'overbought': list(range(60, 81))
            },
            'MACD': {
                'fast': list(range(5, 21)),
                'slow': list(range(21, 51)),
                'signal': list(range(5, 16))
            },
            'BOLLINGER': {
                'period': list(range(10, 31)),
                'std_dev': [1.5, 2.0, 2.5, 3.0]
            },
            'SMA_CROSS': {
                'short_period': list(range(5, 21)),
                'long_period': list(range(21, 51))
            },
            'STOCHASTIC': {
                'k_period': list(range(5, 26)),
                'd_period': list(range(2, 11)),
                'overbought': list(range(70, 91)),
                'oversold': list(range(10, 31))
            }
        }
    
    def _get_cache_key(self, strategy_name: str, parameters: Dict[str, Any]) -> str:
        """生成缓存键"""
        param_str = "_".join(f"{k}:{v}" for k, v in sorted(parameters.items()))
        return f"{strategy_name}_{param_str}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[OptimizationResult]:
        """获取缓存结果"""
        if cache_key in self.cache:
            self.cache_hits += 1
            return self.cache[cache_key]
        self.cache_misses += 1
        return None
    
    def _cache_result(self, cache_key: str, result: OptimizationResult):
        """缓存结果"""
        # 限制缓存大小
        if len(self.cache) > 10000:
            # 删除最旧的1000个条目
            keys_to_remove = list(self.cache.keys())[:1000]
            for key in keys_to_remove:
                del self.cache[key]
        
        self.cache[cache_key] = result
    
    def _calculate_strategy_performance(self, task: OptimizationTask) -> OptimizationResult:
        """计算策略性能指标"""
        start_time = time.perf_counter()
        
        try:
            # 检查缓存
            cache_key = self._get_cache_key(task.strategy_name, task.parameters)
            cached_result = self._get_cached_result(cache_key)
            
            if cached_result:
                cached_result.task_id = task.task_id  # 更新任务ID
                return cached_result
            
            # 模拟策略计算（实际应用中替换为真实策略逻辑）
            np.random.seed(hash(str(task.parameters)) % (2**32))
            
            # 计算技术指标
            if task.strategy_name == 'RSI':
                result = self._calculate_rsi_strategy(task.data, task.parameters)
            elif task.strategy_name == 'MACD':
                result = self._calculate_macd_strategy(task.data, task.parameters)
            elif task.strategy_name == 'BOLLINGER':
                result = self._calculate_bollinger_strategy(task.data, task.parameters)
            elif task.strategy_name == 'SMA_CROSS':
                result = self._calculate_sma_cross_strategy(task.data, task.parameters)
            elif task.strategy_name == 'STOCHASTIC':
                result = self._calculate_stochastic_strategy(task.data, task.parameters)
            else:
                raise ValueError(f"Unknown strategy: {task.strategy_name}")
            
            execution_time = time.perf_counter() - start_time
            
            optimization_result = OptimizationResult(
                task_id=task.task_id,
                strategy_name=task.strategy_name,
                parameters=task.parameters,
                sharpe_ratio=result['sharpe_ratio'],
                total_return=result['total_return'],
                max_drawdown=result['max_drawdown'],
                win_rate=result['win_rate'],
                execution_time=execution_time
            )
            
            # 缓存结果
            self._cache_result(cache_key, optimization_result)
            
            return optimization_result
            
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            logger.error(f"Strategy calculation failed for {task.strategy_name}: {e}")
            
            return OptimizationResult(
                task_id=task.task_id,
                strategy_name=task.strategy_name,
                parameters=task.parameters,
                sharpe_ratio=0.0,
                total_return=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                execution_time=execution_time,
                error=str(e)
            )
    
    def _calculate_rsi_strategy(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, float]:
        """计算RSI策略性能"""
        period = params['period']
        oversold = params['oversold']
        overbought = params['overbought']
        
        # 简化的RSI计算
        returns = data['close'].pct_change()
        gains = returns.where(returns > 0, 0).rolling(window=period).mean()
        losses = -returns.where(returns < 0, 0).rolling(window=period).mean()
        rs = gains / losses
        rsi = 100 - (100 / (1 + rs))
        
        # 生成交易信号
        signals = pd.DataFrame(index=data.index)
        signals['rsi'] = rsi
        signals['signal'] = 0
        signals.loc[rsi < oversold, 'signal'] = 1  # 买入
        signals.loc[rsi > overbought, 'signal'] = -1  # 卖出
        
        return self._calculate_performance_metrics(data, signals['signal'])
    
    def _calculate_macd_strategy(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, float]:
        """计算MACD策略性能"""
        fast = params['fast']
        slow = params['slow']
        signal = params['signal']
        
        # 简化的MACD计算
        exp1 = data['close'].ewm(span=fast).mean()
        exp2 = data['close'].ewm(span=slow).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        # 生成交易信号
        trading_signals = pd.DataFrame(index=data.index)
        trading_signals['signal'] = 0
        trading_signals.loc[histogram > 0, 'signal'] = 1
        trading_signals.loc[histogram < 0, 'signal'] = -1
        
        return self._calculate_performance_metrics(data, trading_signals['signal'])
    
    def _calculate_bollinger_strategy(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, float]:
        """计算布林带策略性能"""
        period = params['period']
        std_dev = params['std_dev']
        
        # 计算布林带
        sma = data['close'].rolling(window=period).mean()
        std = data['close'].rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        # 生成交易信号
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals.loc[data['close'] < lower_band, 'signal'] = 1  # 买入
        signals.loc[data['close'] > upper_band, 'signal'] = -1  # 卖出
        
        return self._calculate_performance_metrics(data, signals['signal'])
    
    def _calculate_sma_cross_strategy(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, float]:
        """计算双移动平均交叉策略性能"""
        short_period = params['short_period']
        long_period = params['long_period']
        
        # 计算移动平均
        short_sma = data['close'].rolling(window=short_period).mean()
        long_sma = data['close'].rolling(window=long_period).mean()
        
        # 生成交易信号
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals.loc[short_sma > long_sma, 'signal'] = 1
        signals.loc[short_sma < long_sma, 'signal'] = -1
        
        return self._calculate_performance_metrics(data, signals['signal'])
    
    def _calculate_stochastic_strategy(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, float]:
        """计算随机指标策略性能"""
        k_period = params['k_period']
        d_period = params['d_period']
        overbought = params['overbought']
        oversold = params['oversold']
        
        # 简化的随机指标计算
        lowest_low = data['low'].rolling(window=k_period).min()
        highest_high = data['high'].rolling(window=k_period).max()
        k_percent = 100 * ((data['close'] - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        # 生成交易信号
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals.loc[k_percent < oversold, 'signal'] = 1
        signals.loc[k_percent > overbought, 'signal'] = -1
        
        return self._calculate_performance_metrics(data, signals['signal'])
    
    def _calculate_performance_metrics(self, data: pd.DataFrame, signals: pd.Series) -> Dict[str, float]:
        """计算性能指标"""
        try:
            # 计算收益
            returns = data['close'].pct_change().dropna()
            strategy_returns = returns * signals.shift(1).fillna(0)
            
            # 基础指标
            total_return = (1 + strategy_returns).prod() - 1
            mean_return = strategy_returns.mean()
            std_return = strategy_returns.std()
            
            # Sharpe比率（无风险利率设为3%）
            risk_free_rate = 0.03 / 252  # 日化无风险利率
            if std_return > 0:
                sharpe_ratio = (mean_return - risk_free_rate) / std_return * np.sqrt(252)
            else:
                sharpe_ratio = 0
            
            # 最大回撤
            cumulative = (1 + strategy_returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # 胜率
            winning_trades = strategy_returns[strategy_returns > 0]
            win_rate = len(winning_trades) / len(strategy_returns[strategy_returns != 0]) if len(strategy_returns[strategy_returns != 0]) > 0 else 0
            
            return {
                'sharpe_ratio': float(sharpe_ratio),
                'total_return': float(total_return),
                'max_drawdown': float(max_drawdown),
                'win_rate': float(win_rate)
            }
            
        except Exception as e:
            logger.error(f"Performance calculation failed: {e}")
            return {
                'sharpe_ratio': 0.0,
                'total_return': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0
            }
    
    def _process_task_batch(self, tasks: List[OptimizationTask]) -> List[OptimizationResult]:
        """处理任务批次"""
        results = []
        
        for task in tasks:
            try:
                result = self._calculate_strategy_performance(task)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process task {task.task_id}: {e}")
                error_result = OptimizationResult(
                    task_id=task.task_id,
                    strategy_name=task.strategy_name,
                    parameters=task.parameters,
                    sharpe_ratio=0.0,
                    total_return=0.0,
                    max_drawdown=0.0,
                    win_rate=0.0,
                    execution_time=0.0,
                    error=str(e)
                )
                results.append(error_result)
        
        return results
    
    async def _worker_process(self, process_id: int):
        """工作进程"""
        logger.info(f"Worker {process_id} started")
        
        while self._running:
            try:
                # 获取任务批次
                batch = []
                for _ in range(self.chunk_size):
                    try:
                        task = self.task_queue.get_nowait()
                        batch.append(task)
                    except asyncio.QueueEmpty:
                        break
                
                if not batch:
                    await asyncio.sleep(0.01)
                    continue
                
                # 处理任务批次
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    results = await loop.run_in_executor(
                        executor, 
                        self._process_task_batch, 
                        batch
                    )
                
                # 将结果放入结果队列
                for result in results:
                    await self.result_queue.put(result)
                
                # 更新性能指标
                self.metrics.tasks_completed += len(batch)
                
                # 定期清理内存
                if self.metrics.tasks_completed % self.cleanup_interval == 0:
                    gc.collect()
                    
            except Exception as e:
                logger.error(f"Worker {process_id} error: {e}")
                await asyncio.sleep(0.1)
        
        logger.info(f"Worker {process_id} stopped")
    
    def generate_optimization_tasks(self, strategy_name: str, data: pd.DataFrame, 
                                  sample_size: Optional[int] = None) -> List[OptimizationTask]:
        """生成优化任务"""
        if strategy_name not in self.parameter_spaces:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        param_space = self.parameter_spaces[strategy_name]
        tasks = []
        
        # 生成参数组合
        param_names = list(param_space.keys())
        param_values = list(param_space.values())
        
        total_combinations = 1
        for values in param_values:
            total_combinations *= len(values)
        
        # 限制样本大小以避免内存问题
        if sample_size and total_combinations > sample_size:
            # 随机采样
            combinations = []
            for _ in range(sample_size):
                params = {}
                for i, name in enumerate(param_names):
                    params[name] = np.random.choice(param_values[i])
                combinations.append(params)
        else:
            # 生成所有组合
            import itertools
            combinations = []
            for combo in itertools.product(*param_values):
                params = dict(zip(param_names, combo))
                combinations.append(params)
        
        # 创建任务
        for i, params in enumerate(combinations):
            task = OptimizationTask(
                task_id=f"{strategy_name}_{i}",
                strategy_name=strategy_name,
                parameters=params,
                data=data.copy(),  # 使用数据副本避免并发问题
                priority=1
            )
            tasks.append(task)
        
        return tasks
    
    async def run_optimization(self, strategy_name: str, data: pd.DataFrame, 
                            sample_size: Optional[int] = None) -> List[OptimizationResult]:
        """运行优化"""
        logger.info(f"Starting optimization for {strategy_name}")
        start_time = time.time()
        
        # 生成任务
        tasks = self.generate_optimization_tasks(strategy_name, data, sample_size)
        total_tasks = len(tasks)
        logger.info(f"Generated {total_tasks} optimization tasks")
        
        # 将任务放入队列
        for task in tasks:
            await self.task_queue.put(task)
        
        # 启动工作进程
        self._running = True
        worker_tasks = []
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker_process(i))
            worker_tasks.append(worker)
        
        # 收集结果
        results = []
        completed_tasks = 0
        
        while completed_tasks < total_tasks:
            try:
                result = await asyncio.wait_for(self.result_queue.get(), timeout=1.0)
                results.append(result)
                completed_tasks += 1
                
                # 进度报告
                if completed_tasks % 100 == 0:
                    progress = (completed_tasks / total_tasks) * 100
                    current_tps = completed_tasks / (time.time() - start_time)
                    logger.info(f"Progress: {progress:.1f}% ({completed_tasks}/{total_tasks}), {current_tps:.1f} tasks/sec")
                    
            except asyncio.TimeoutError:
                # 检查工作进程状态
                if not any(w.done() for w in worker_tasks):
                    continue
                else:
                    break
        
        # 停止工作进程
        self._running = False
        for worker in worker_tasks:
            worker.cancel()
        
        # 计算最终性能指标
        total_time = time.time() - start_time
        self.metrics.total_execution_time += total_time
        self.metrics.tasks_per_second = total_tasks / total_time
        self.metrics.cache_hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        
        # 更新系统资源使用情况
        self.metrics.cpu_usage = psutil.cpu_percent()
        self.metrics.memory_usage = psutil.virtual_memory().percent
        
        logger.info(f"Optimization completed: {len(results)} results in {total_time:.2f}s")
        logger.info(f"Performance: {self.metrics.tasks_per_second:.1f} tasks/sec, Cache hit rate: {self.metrics.cache_hit_rate:.1%}")
        
        return results
    
    def get_top_strategies(self, results: List[OptimizationResult], 
                         top_n: int = 10) -> List[OptimizationResult]:
        """获取表现最佳的策略"""
        # 过滤出有效结果
        valid_results = [r for r in results if r.error is None and r.sharpe_ratio > 0]
        
        # 按Sharpe比率排序
        sorted_results = sorted(valid_results, key=lambda x: x.sharpe_ratio, reverse=True)
        
        return sorted_results[:top_n]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        return {
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "total_execution_time": self.metrics.total_execution_time,
                "tasks_per_second": self.metrics.tasks_per_second,
                "cache_hit_rate": self.metrics.cache_hit_rate,
                "cpu_usage": self.metrics.cpu_usage,
                "memory_usage": self.metrics.memory_usage,
                "cache_size": len(self.cache)
            },
            "configuration": {
                "max_workers": self.max_workers,
                "chunk_size": self.chunk_size,
                "cpu_count": self.cpu_count,
                "strategies": list(self.parameter_spaces.keys())
            }
        }

async def main():
    """主函数 - 性能测试"""
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=1000, freq='D')
    prices = 100 + np.cumsum(np.random.normal(0.001, 0.02, 1000))
    
    data = pd.DataFrame({
        'open': prices * (1 + np.random.uniform(-0.005, 0.005, 1000)),
        'high': prices * (1 + np.random.uniform(0, 0.02, 1000)),
        'low': prices * (1 - np.random.uniform(0, 0.02, 1000)),
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 1000)
    }, index=dates)
    
    # 创建高性能优化器
    optimizer = HighPerformanceOptimizer(max_workers=16, chunk_size=50)
    
    # 测试不同策略
    strategies = ['RSI', 'MACD', 'BOLLINGER', 'SMA_CROSS', 'STOCHASTIC']
    
    for strategy in strategies:
        print(f"\n=== Testing {strategy} Strategy ===")
        
        # 运行优化（样本大小限制为1000以节省时间）
        results = await optimizer.run_optimization(strategy, data, sample_size=1000)
        
        # 获取最佳策略
        top_strategies = optimizer.get_top_strategies(results, top_n=5)
        
        print(f"Total results: {len(results)}")
        print(f"Valid results: {len([r for r in results if r.error is None])}")
        print(f"Top 5 strategies:")
        for i, result in enumerate(top_strategies, 1):
            print(f"  {i}. Sharpe: {result.sharpe_ratio:.3f}, "
                  f"Return: {result.total_return:.2%}, "
                  f"Max DD: {result.max_drawdown:.2%}, "
                  f"Win Rate: {result.win_rate:.2%}")
        
        # 显示性能摘要
        summary = optimizer.get_performance_summary()
        print(f"Performance: {summary['metrics']['tasks_per_second']:.1f} tasks/sec")
        print(f"Cache hit rate: {summary['metrics']['cache_hit_rate']:.1%}")

if __name__ == "__main__":
    asyncio.run(main())