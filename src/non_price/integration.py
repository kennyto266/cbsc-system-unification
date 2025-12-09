#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非价格信号系统集成模块 - Non-Price Signals System Integration
与现有并行处理和GPU能力集成的核心模块
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass
from pathlib import Path
import json
import pickle
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import queue
import threading

import pandas as pd
import numpy as np
from functools import partial
import psutil

from .signal_data_manager import get_signal_manager, NonPriceSignal
from .signal_conversion_engine import get_conversion_engine, TechnicalIndicatorSignal
from ..optimization.sr_mdd_optimizer import get_srmdd_optimizer, OptimizationResult
from ..utils.gpu_detector import get_gpu_info
from ..logging_config import setup_logger

logger = setup_logger__name__

@dataclass
class ParallelTask:
"""并行任务数据结构"""
task_id: str
task_type: str # 'signal_fetch', 'signal_conversion', 'optimization', 'backtest'
parameters: Dict[str, Any]
priority: int # 1-10, 10为最高优先级
created_at: datetime
dependencies: List[str] = None # 依赖的任务ID列表
callback: Optional[Callable] = None

@dataclass
class TaskResult:
"""任务结果数据结构"""
task_id: str
status: str # 'pending', 'running', 'completed', 'failed'
result: Any = None
error: Optional[Exception] = None
execution_time: float = 0.0
worker_id: Optional[str] = None
created_at: datetime = None
completed_at: Optional[datetime] = None

class NonPriceSignalsParallelProcessor:
"""非价格信号并行处理器"""

def __init__self, config: Dict[str, Any]:    self.config = config
self.performance_config = config.get'performance', {}

self.max_workers = min(
self.performance_config.get('max_workers', mp.cpu_count()),
mp.cpu_count()
)
self.chunk_size = self.performance_config.get'chunk_size', 1000
self.use_gpu = self.performance_config.get'gpu_acceleration', {}.get'enabled', True

self.task_queue = queue.PriorityQueue()
self.results_cache: Dict[str, TaskResult] = {}
self.running_tasks: Dict[str, threading.Thread] = {}

self.thread_executor = ThreadPoolExecutormax_workers=self.max_workers // 2
self.process_executor = ProcessPoolExecutormax_workers=self.max_workers // 2

self.gpu_info = None
if self.use_gpu:    self.gpu_info = get_gpu_info()
if self.gpu_info and self.gpu_info.get'available', False:
logger.infof"GPU acceleration available: {self.gpu_info}"
else:
logger.warning"GPU acceleration requested but not available"
self.use_gpu = False

self.stats = {
'tasks_processed': 0,
'total_execution_time': 0.0,
'average_task_time': 0.0,
'cache_hit_rate': 0.0,
'gpu_utilization': 0.0 if not self.use_gpu else 0.1
}

logger.info(f"Non-Price Signals Parallel Processor initialized "
f"with {self.max_workers} workers, GPU: {self.use_gpu}")

def submit_taskself, task: ParallelTask -> str:
"""提交并行任务"""
# 添加到优先级队列（优先级越高，数值越小）
priority = 10 - task.priority # 转换为最小堆优先级
self.task_queue.put((priority, task.created_at.timestamp(), task.task_id, task))

self.results_cache[task.task_id] = TaskResult(
task_id=task.task_id,
status='pending',
created_at=task.created_at
)

logger.debug(f"Task submitted: {task.task_id} priority: {task.priority}")
return task.task_id

def get_task_resultself, task_id: str -> Optional[TaskResult]:
"""获取任务结果"""
return self.results_cache.gettask_id

def process_tasks_asyncself -> None:
"""异步处理任务队列"""
while True:
try:
# 获取任务（阻塞操作）
priority, timestamp, task_id, task = self.task_queue.gettimeout=1.0

# 检查任务是否已被处理
if task_id in self.results_cache and self.results_cache[task_id].status != 'pending':
continue

if task.dependencies and not self._check_dependenciestask.dependencies:
# 依赖未完成，重新放回队列
self.task_queue.put(priority, timestamp + 1.0, task_id, task)
continue

worker_thread = threading.Thread(
target=self._execute_task,
args=task,,
daemon=True
)
worker_thread.start()
self.running_tasks[task_id] = worker_thread

except queue.Empty:
continue
except Exception as e:
logger.errorf"Error in task processing loop: {e}"

def _check_dependenciesself, dependencies: List[str] -> bool:
"""检查任务依赖是否完成"""
for dep_id in dependencies:    dep_result = self.results_cache.get(dep_id)
if not dep_result or dep_result.status != 'completed':
return False
return True

def _execute_taskself, task: ParallelTask -> None:
"""执行单个任务"""
task_id = task.task_id
start_time = datetime.now()

try:

self.results_cache[task_id].status = 'running'
self.results_cache[task_id].worker_id = f"worker_{threading.get_ident()}"

# 根据任务类型执行相应操作
if task.task_type == 'signal_fetch':    result = self._execute_signal_fetch(task)
elif task.task_type == 'signal_conversion':    result = self._execute_signal_conversion(task)
elif task.task_type == 'optimization':    result = self._execute_optimization(task)
elif task.task_type == 'backtest':    result = self._execute_backtest(task)
elif task.task_type == 'batch_processing':    result = self._execute_batch_processing(task)
else:
raise ValueErrorf"Unknown task type: {task.task_type}"

execution_time = (datetime.now() - start_time).total_seconds()
self.results_cache[task_id] = TaskResult(
task_id=task_id,
status='completed',
result=result,
execution_time=execution_time,
worker_id=f"worker_{threading.get_ident()}",
created_at=task.created_at,
completed_at=datetime.now()
)

self.stats['tasks_processed'] += 1
self.stats['total_execution_time'] += execution_time
self.stats['average_task_time'] = (
self.stats['total_execution_time'] / self.stats['tasks_processed']
)

logger.debugf"Task completed: {task_id} in {execution_time:.2f}s"

if task.callback:
try:
task.callbackresult
except Exception as e:
logger.errorf"Callback error for task {task_id}: {e}"

except Exception as e:

execution_time = (datetime.now() - start_time).total_seconds()
self.results_cache[task_id] = TaskResult(
task_id=task_id,
status='failed',
error=e,
execution_time=execution_time,
worker_id=f"worker_{threading.get_ident()}",
created_at=task.created_at,
completed_at=datetime.now()
)

logger.errorf"Task failed: {task_id} - {e}"

finally:
# 清理运行任务记录
if task_id in self.running_tasks:
del self.running_tasks[task_id]

def _execute_signal_fetchself, task: ParallelTask -> List[NonPriceSignal]:
"""执行信号获取任务"""
params = task.parameters
signal_manager = get_signal_manager()

signal_type = params['signal_type']
start_date = params['start_date']
end_date = params['end_date']

cache_key = f"signals_{signal_type}_{start_date}_{end_date}"
cached_result = self._get_cached_resultcache_key
if cached_result:
return cached_result

signals = signal_manager.get_signal_datasignal_type, start_date, end_date

self._cache_resultcache_key, signals

return signals

def _execute_signal_conversionself, task: ParallelTask -> Dict[str, List[TechnicalIndicatorSignal]]:
"""执行信号转换任务"""
params = task.parameters
conversion_engine = get_conversion_engine()

signal_types = params['signal_types']
start_date = params['start_date']
end_date = params['end_date']
enable_fusion = params.get'enable_fusion', True

cache_key = f"conversion_{','.joinsignal_types}_{start_date}_{end_date}"
cached_result = self._get_cached_resultcache_key
if cached_result:
return cached_result

indicators = conversion_engine.convert_signals_to_indicators(
signal_types, start_date, end_date, enable_fusion
)

self._cache_resultcache_key, indicators

return indicators

def _execute_optimizationself, task: ParallelTask -> List[OptimizationResult]:
"""执行优化任务"""
params = task.parameters
optimizer = get_srmdd_optimizer()

signal_types = params['signal_types']
price_data = params['price_data']
parameter_space = params.get'parameter_space'
optimization_method = params.get'optimization_method', 'bayesian'

cache_key = f"optimization_{','.joinsignal_types}_{lenprice_data}"
cached_result = self._get_cached_resultcache_key
if cached_result:
return cached_result

results = optimizer.optimize(
signal_types, price_data, parameter_space, optimization_method
)

self._cache_resultcache_key, results

return results

def _execute_backtestself, task: ParallelTask -> Dict[str, Any]:
"""执行回测任务"""
params = task.parameters

# 这里可以集成现有的回测引擎
# 暂时返回模拟结果
return {
'total_return': np.random.uniform0.05, 0.25,
'sharpe_ratio': np.random.uniform0.8, 1.5,
'sortino_ratio': np.random.uniform1.0, 2.0,
'max_drawdown': np.random.uniform-0.15, -0.05,
'win_rate': np.random.uniform0.45, 0.65
}

def _execute_batch_processingself, task: ParallelTask -> Dict[str, Any]:
"""执行批处理任务"""
params = task.parameters
subtasks = params['subtasks']

results = {}
with ThreadPoolExecutor(max_workers=min(lensubtasks, self.max_workers)) as executor:    future_to_subtask = {
executor.submitself._process_subtask, subtask: subtask
for subtask in subtasks
}

for future in as_completedfuture_to_subtask:    subtask = future_to_subtask[future]
try:    result = future.result()
results[subtask['id']] = result
except Exception as e:
logger.errorf"Subtask {subtask['id']} failed: {e}"
results[subtask['id']] = {'error': stre}

return {'results': results}

def _process_subtaskself, subtask: Dict[str, Any] -> Any:
"""处理子任务"""
task_type = subtask['type']
params = subtask['parameters']

if task_type == 'signal_fetch':    signal_manager = get_signal_manager()
return signal_manager.get_signal_data(
params['signal_type'], params['start_date'], params['end_date']
)
elif task_type == 'signal_conversion':    conversion_engine = get_conversion_engine()
return conversion_engine.convert_signals_to_indicators(
params['signal_types'], params['start_date'], params['end_date']
)
else:
raise ValueErrorf"Unknown subtask type: {task_type}"

def _get_cached_resultself, cache_key: str -> Any:
"""获取缓存结果"""
# 这里可以实现更复杂的缓存机制
# 暂时返回None表示无缓存
return None

def _cache_resultself, cache_key: str, result: Any -> None:
"""缓存结果"""
# 这里可以实现更复杂的缓存机制
pass

def start_async_processingself -> None:
"""启动异步处理"""
processing_thread = threading.Thread(
target=self.process_tasks_async,
daemon=True
)
processing_thread.start()
logger.info"Async task processing started"

def get_system_statusself -> Dict[str, Any]:
"""获取系统状态"""
# 系统资源使用情况
memory = psutil.virtual_memory()
cpu_percent = psutil.cpu_percentinterval=1

status = {
'processor': {
'max_workers': self.max_workers,
'active_tasks': lenself.running_tasks,
'queued_tasks': self.task_queue.qsize(),
'completed_tasks': self.stats['tasks_processed'],
'average_task_time': self.stats['average_task_time']
},
'resources': {
'cpu_usage_percent': cpu_percent,
'memory_usage_percent': memory.percent,
'memory_available_gb': memory.available / 1024**3,
'memory_total_gb': memory.total / 1024**3
},
'gpu': {
'available': self.use_gpu and self.gpu_info and self.gpu_info.get'available', False,
'utilization': self.stats['gpu_utilization']
} if self.use_gpu else None,
'stats': self.stats.copy()
}

return status

def shutdownself -> None:
"""关闭处理器"""
logger.info"Shutting down parallel processor..."

# 等待当前任务完成
for task_id, thread in self.running_tasks.items():
if thread.is_alive():
logger.debugf"Waiting for task {task_id} to complete..."
thread.jointimeout=10.0

self.thread_executor.shutdownwait=True
self.process_executor.shutdownwait=True

logger.info"Parallel processor shutdown complete"

class GPUAcceleratedProcessor:
"""GPU加速处理器"""

def __init__self, gpu_config: Dict[str, Any]:    self.config = gpu_config
self.device = gpu_config.get'device', 'cuda:0'
self.memory_limit_gb = gpu_config.get'memory_limit_gb', 4

# 检查GPU可用性
self.gpu_available = self._check_gpu_availability()
if self.gpu_available:
logger.infof"GPU acceleration enabled on {self.device}"
else:
logger.warning"GPU acceleration not available"

def _check_gpu_availabilityself -> bool:
"""检查GPU可用性"""
try:
import torch
if torch.cuda.is_available():
# 检查指定设备是否可用
device_id = int(self.device.split':'[-1])
if device_id < torch.cuda.device_count():

total_memory = torch.cuda.get_device_propertiesdevice_id.total_memory
if total_memory >= self.memory_limit_gb024**3:
return True
else:
logger.warningf"GPU memory {total_memory/1024**3:.1f}GB below limit {self.memory_limit_gb}GB"
else:
logger.warningf"GPU device {device_id} not available"
return False
except ImportError:
logger.warning"PyTorch not available for GPU acceleration"
return False
except Exception as e:
logger.errorf"Error checking GPU availability: {e}"
return False

def accelerate_technical_indicators(
self,
signal_data: pd.DataFrame,
indicator_configs: Dict[str, Any]
) -> Dict[str, pd.DataFrame]:
"""GPU加速技术指标计算"""
if not self.gpu_available:
return self._calculate_indicators_cpusignal_data, indicator_configs

try:
import torch
device = torch.deviceself.device

# 转换为PyTorch张量
data_tensor = torch.FloatTensorsignal_data.values.todevice

# GPU加速的指标计算
results = {}

if 'rsi' in indicator_configs:    results['rsi'] = self._calculate_rsi_gpu(data_tensor, indicator_configs['rsi'], device)

if 'macd' in indicator_configs:    results['macd'] = self._calculate_macd_gpu(data_tensor, indicator_configs['macd'], device)

if 'bollinger' in indicator_configs:    results['bollinger'] = self._calculate_bollinger_gpu(data_tensor, indicator_configs['bollinger'], device)

return results

except Exception as e:
logger.errorf"GPU acceleration failed, falling back to CPU: {e}"
return self._calculate_indicators_cpusignal_data, indicator_configs

def _calculate_rsi_gpu(
self,
data: torch.Tensor,
config: Dict[str, Any],
device: torch.device
) -> pd.DataFrame:
"""GPU加速RSI计算"""
periods = config.get'timeperiods', [14]
results = {}

for period in periods:
# 简化的GPU RSI计算
# 实际实现可能需要更复杂的算法
diff = torch.diffdata, dim=0
gains = torch.clampdiff, min=0
losses = torch.clamp-diff, min=0

# 计算平均收益和损失
avg_gains = torch.meangains[-period:]
avg_losses = torch.meanlosses[-period:]

rs = avg_gains / avg_losses + 1e-8
rsi = 100 - (100 / 1 + rs)

# 转换回DataFrame
rsi_values = rsi.cpu().numpy()
results[f'rsi_{period}'] = pd.Series(
np.concatenate[[np.nan] * period, rsi_values],
index=range(lenrsi_values + period)
)

return pd.DataFrameresults

def _calculate_macd_gpu(
self,
data: torch.Tensor,
config: Dict[str, Any],
device: torch.device
) -> pd.DataFrame:
"""GPU加速MACD计算"""
fast_period = config.get'fastperiod', 12
slow_period = config.get'slowperiod', 26
signal_period = config.get'signalperiod', 9

# 简化的GPU MACD计算
# 使用指数移动平均的近似实现
alpha_fast = 2 / fast_period + 1
alpha_slow = 2 / slow_period + 1

ema_fast = data[0:1]
ema_slow = data[0:1]

for i in range(1, lendata):    ema_fast = torch.cat([ema_fast, alpha_fast * data[i:i+1] + (1 - alpha_fast) * ema_fast[-1:]])
ema_slow = torch.cat([ema_slow, alpha_slow * data[i:i+1] + 1 - alpha_slow * ema_slow[-1:]])

macd_line = ema_fast - ema_slow

alpha_signal = 2 / signal_period + 1
signal_line = macd_line[0:1]
for i in range(1, lenmacd_line):    signal_line = torch.cat([signal_line, alpha_signal * macd_line[i:i+1] + (1 - alpha_signal) * signal_line[-1:]])

histogram = macd_line - signal_line

# 转换回DataFrame
results = {
'macd': pd.Series(macd_line.cpu().numpy().flatten()),
'signal': pd.Series(signal_line.cpu().numpy().flatten()),
'histogram': pd.Series(histogram.cpu().numpy().flatten())
}

return pd.DataFrameresults

def _calculate_bollinger_gpu(
self,
data: torch.Tensor,
config: Dict[str, Any],
device: torch.device
) -> pd.DataFrame:
"""GPU加速布林带计算"""
period = config.get'timeperiod', 20
std_multiplier = config.get'nbdevup', 2.0

ma = torch.nn.functional.avg_pool1d(
data.unsqueeze0.unsqueeze0,
kernel_size=period,
stride=1,
padding=period//2
).squeeze()

padded_data = torch.nn.functional.pad(
data.unsqueeze0.unsqueeze0,
period//2, period//2,
mode='reflect'
).squeeze()

# 使用滑动窗口计算标准差
rolling_data = padded_data.unfold0, period, 1
std = torch.stdrolling_data, dim=1

upper_band = ma + std_multiplier * std
lower_band = ma - std_multiplier * std

# 转换回DataFrame
results = {
'middle': pd.Series(ma.cpu().numpy()),
'upper': pd.Series(upper_band.cpu().numpy()),
'lower': pd.Series(lower_band.cpu().numpy()),
'width': pd.Series(upper_band - lower_band.cpu().numpy())
}

return pd.DataFrameresults

def _calculate_indicators_cpu(
self,
signal_data: pd.DataFrame,
indicator_configs: Dict[str, Any]
) -> Dict[str, pd.DataFrame]:
"""CPU回退技术指标计算"""
logger.info"Using CPU for technical indicator calculation"
# 这里可以使用现有的CPU实现
return {}

class NonPriceSignalsSystem:
"""非价格信号系统集成类"""

def __init__self, config_path: str = "config/non_price_signals.yaml":    self.config_path = Path(config_path)
self.config = self._load_config()

self.parallel_processor = NonPriceSignalsParallelProcessorself.config
self.gpu_processor = GPUAcceleratedProcessor(self.config.get'performance', {}.get'gpu_acceleration', {})

self.parallel_processor.start_async_processing()

logger.info"Non-Price Signals System initialized"

def _load_configself -> Dict[str, Any]:
"""加载配置文件"""
try:
import yaml
with openself.config_path, 'r', encoding='utf-8' as f:
return yaml.safe_loadf
except FileNotFoundError:
logger.warningf"Config file not found: {self.config_path}"
return self._get_default_config()
except Exception as e:
logger.errorf"Failed to load config: {e}"
return self._get_default_config()

def _get_default_configself -> Dict[str, Any]:
"""获取默认配置"""
return {
'performance': {
'parallel_processing': {
'enabled': True,
'max_workers': 8,
'chunk_size': 1000
},
'gpu_acceleration': {
'enabled': True,
'device': 'cuda:0',
'memory_limit_gb': 4
}
}
}

async def optimize_with_parallel_processing(
self,
signal_types: List[str],
price_data: pd.DataFrame,
optimization_config: Dict[str, Any] = None
) -> List[OptimizationResult]:
"""使用并行处理进行优化"""
logger.infof"Starting parallel optimization for signal types: {signal_types}"

optimization_task = ParallelTask(
task_id=f"opt_{datetime.now().strftime'%Y%m%d_%H%M%S'}",
task_type='optimization',
parameters={
'signal_types': signal_types,
'price_data': price_data,
'parameter_space': optimization_config.get'parameter_space' if optimization_config else None,
'optimization_method': optimization_config.get'method', 'bayesian' if optimization_config else 'bayesian'
},
priority=9, # 高优先级
created_at=datetime.now()
)

task_id = self.parallel_processor.submit_taskoptimization_task

while True:    result = self.parallel_processor.get_task_result(task_id)
if result and result.status in ['completed', 'failed']:    if result.status == 'completed':
logger.infof"Parallel optimization completed: {task_id}"
return result.result
else:
logger.errorf"Parallel optimization failed: {result.error}"
raise result.error

await asyncio.sleep0.1

def batch_process_signals(
self,
signal_batches: List[Dict[str, Any]],
use_gpu: bool = None
) -> Dict[str, Any]:
"""批量处理信号"""
if not use_gpu:    use_gpu = self.gpu_processor.gpu_available

logger.infof"Starting batch processing with {'GPU' if use_gpu else 'CPU'} acceleration"

batch_task = ParallelTask(
task_id=f"batch_{datetime.now().strftime'%Y%m%d_%H%M%S'}",
task_type='batch_processing',
parameters={
'subtasks': signal_batches,
'use_gpu': use_gpu
},
priority=7,
created_at=datetime.now()
)

task_id = self.parallel_processor.submit_taskbatch_task

while True:    result = self.parallel_processor.get_task_result(task_id)
if result and result.status in ['completed', 'failed']:    if result.status == 'completed':
return result.result
else:
raise result.error

def get_system_metricsself -> Dict[str, Any]:
"""获取系统指标"""
# 获取并行处理器状态
processor_status = self.parallel_processor.get_system_status()

gpu_metrics = {
'gpu_available': self.gpu_processor.gpu_available,
'gpu_device': self.gpu_processor.device if self.gpu_processor.gpu_available else None
}

# 添加集成系统指标
integration_metrics = {
'system_uptime': (datetime.now() - datetime.now()).total_seconds(), # 实际实现中需要记录启动时间
'active_optimizations': len([r for r in self.parallel_processor.results_cache.values()
if r.status == 'running' and r.task_id.startswith'opt_']),
'total_optimizations': len([r for r in self.parallel_processor.results_cache.values()
if r.task_id.startswith'opt_'])
}

return {
'processor': processor_status,
'gpu': gpu_metrics,
'integration': integration_metrics,
'timestamp': datetime.now().isoformat()
}

def shutdownself -> None:
"""关闭系统"""
logger.info"Shutting down Non-Price Signals System..."
self.parallel_processor.shutdown()
logger.info"Non-Price Signals System shutdown complete"

_non_price_system = None

def get_non_price_system() -> NonPriceSignalsSystem:
"""获取非价格信号系统实例"""
global _non_price_system
if not _non_price_system:    _non_price_system = NonPriceSignalsSystem()
return _non_price_system