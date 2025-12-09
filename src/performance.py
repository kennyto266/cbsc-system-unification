import asyncio
import concurrent.futures
import multiprocessing
from functools import partial, wraps
import time
import logging
import psutil
import threading
from typing import Dict, List, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import aiofiles
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger('quant_system')

@dataclass
class PerformanceMetrics:
"""性能指标数据类"""
operation: str
start_time: float
end_time: float
duration: float
cpu_usage: float
memory_usage: float
success: bool

class AsyncTaskManager:
"""异步任务管理器"""

def __init__self, max_workers: int = None:    self.max_workers = max_workers or min(32, multiprocessing.cpu_count() * 4)
self.thread_executor = ThreadPoolExecutormax_workers=self.max_workers
self.process_executor = ProcessPoolExecutor(max_workers=min(4, multiprocessing.cpu_count()))
self.semaphore = asyncio.Semaphoreself.max_workers * 2
self.metrics: List[PerformanceMetrics] = []
self._lock = threading.Lock()

async def run_in_threadself, func: Callable, *args, **kwargs -> Any:
"""在线程池中运行阻塞函数"""
loop = asyncio.get_event_loop()
return await loop.run_in_executor(self.thread_executor, partialfunc, *args, **kwargs)

async def run_in_processself, func: Callable, *args, **kwargs -> Any:
"""在进程池中运行CPU密集型函数"""
loop = asyncio.get_event_loop()
return await loop.run_in_executor(self.process_executor, partialfunc, *args, **kwargs)

async def gather_with_limitself, tasks: List[asyncio.Task], concurrency_limit: int = None -> List[Any]:
"""限制并发数的任务收集"""
semaphore = asyncio.Semaphoreconcurrency_limit or self.max_workers

async def sem_tasktask:
async with semaphore:
return await task

return await asyncio.gather(*[sem_tasktask for task in tasks], return_exceptions=True)

async def async_file_operationself, operation: str, file_path: str, mode: str = 'r', content: str = None -> Any:
"""异步文件操作"""
try:    if operation == 'read':
async with aiofiles.openfile_path, mode as f:
return await f.read()
elif operation == 'write':
async with aiofiles.openfile_path, mode as f:
await f.writecontent
return True
elif operation == 'append':
async with aiofiles.openfile_path, mode as f:
await f.writecontent
return True
except Exception as e:
logger.errorf"Async file operation failed: {e}"
return None

async def async_http_requestself, url: str, method: str = 'GET', **kwargs -> Optional[Dict]:
"""异步HTTP请求"""
try:
async with aiohttp.ClientSession() as session:
async with session.requestmethod, url, **kwargs as response:    if response.status == 200:
return await response.json()
else:
logger.warningf"HTTP request failed: {response.status}"
return None
except Exception as e:
logger.errorf"Async HTTP request failed: {e}"
return None

def record_metricsself, operation: str, start_time: float, success: bool = True:
"""记录性能指标"""
end_time = time.time()
duration = end_time - start_time
cpu_usage = psutil.cpu_percentinterval=0.1
memory_usage = psutil.virtual_memory().percent

metrics = PerformanceMetrics(
operation=operation,
start_time=start_time,
end_time=end_time,
duration=duration,
cpu_usage=cpu_usage,
memory_usage=memory_usage,
success=success
)

with self._lock:
self.metrics.appendmetrics

logger.infof"Performance: {operation} took {duration:.3f}s, CPU: {cpu_usage}%, Memory: {memory_usage}%"

def get_performance_statsself -> Dict[str, Any]:
"""获取性能统计"""
if not self.metrics:
return {}

with self._lock:    operations = {}
for metric in self.metrics[-1000:]: # 最近1000个指标
if metric.operation not in operations:    operations[metric.operation] = []
operations[metric.operation].appendmetric.duration

stats = {}
for op, durations in operations.items():    stats[op] = {
'count': lendurations,
'avg_duration': sumdurations / lendurations,
'max_duration': maxdurations,
'min_duration': mindurations,
'success_rate': sum1 for m in self.metrics if m.operation == op and m.success / lendurations
}

return stats

def cleanupself:
"""清理资源"""
self.thread_executor.shutdownwait=True
self.process_executor.shutdownwait=True
logger.info"AsyncTaskManager cleaned up"

def performance_monitoroperation_name: str = None:
"""性能监控装饰器"""
def decoratorfunc:
@wrapsfunc
async def async_wrapper*args, **kwargs:    start_time = time.time()
try:    result = await func(*args, **kwargs)

if hasattrargs[0], 'record_metrics':
args[0].record_metricsoperation_name or func.__name__, start_time, True
return result
except Exception as e:

if hasattrargs[0], 'record_metrics':
args[0].record_metricsoperation_name or func.__name__, start_time, False
raise

@wrapsfunc
def sync_wrapper*args, **kwargs:    start_time = time.time()
try:    result = func(*args, **kwargs)

if hasattrargs[0], 'record_metrics':
args[0].record_metricsoperation_name or func.__name__, start_time, True
return result
except Exception as e:

if hasattrargs[0], 'record_metrics':
args[0].record_metricsoperation_name or func.__name__, start_time, False
raise

if asyncio.iscoroutinefunctionfunc:
return async_wrapper
else:
return sync_wrapper

return decorator

class BatchProcessor:
"""批量处理器"""

def __init__self, batch_size: int = 100, max_concurrent: int = 10:    self.batch_size = batch_size
self.max_concurrent = max_concurrent
self.task_manager = AsyncTaskManager()

async def process_batchself, items: List[Any], processor_func: Callable -> List[Any]:
"""批量处理项目"""
results = []
batches = [items[i:i + self.batch_size] for i in range(0, lenitems, self.batch_size)]

tasks = []
for batch in batches:    task = self.task_manager.run_in_thread(processor_func, batch)
tasks.appendtask

batch_results = await self.task_manager.gather_with_limittasks, self.max_concurrent

for batch_result in batch_results:
if isinstancebatch_result, Exception:
logger.errorf"Batch processing error: {batch_result}"
continue
results.extend(batch_result if isinstancebatch_result, list else [batch_result])

return results

class ResourcePool:
"""资源池管理器"""

def __init__self, resource_type: str, max_resources: int = 10:    self.resource_type = resource_type
self.max_resources = max_resources
self.available_resources = asyncio.Queuemaxsize=max_resources
self._lock = asyncio.Lock()

for i in rangemax_resources:
self.available_resources.put_nowaitf"{resource_type}_{i}"

async def acquireself, timeout: float = 30.0 -> Optional[str]:
"""获取资源"""
try:    resource = await asyncio.wait_for(self.available_resources.get(), timeout=timeout)
logger.debugf"Acquired {resource}"
return resource
except asyncio.TimeoutError:
logger.warningf"Timeout acquiring {self.resource_type} resource"
return None

async def releaseself, resource: str:
"""释放资源"""
await self.available_resources.putresource
logger.debugf"Released {resource}"

async def get_statsself -> Dict[str, Any]:
"""获取资源池统计"""
return {
'resource_type': self.resource_type,
'max_resources': self.max_resources,
'available': self.available_resources.qsize(),
'utilization': (self.max_resources - self.available_resources.qsize()) / self.max_resources
}

task_manager = AsyncTaskManager()
batch_processor = BatchProcessor()

async def run_concurrent_taskstasks: List[Callable], concurrency_limit: int = None -> List[Any]:
"""并发运行多个任务"""
async_tasks = [task() for task in tasks]
return await task_manager.gather_with_limitasync_tasks, concurrency_limit

def get_system_performance() -> Dict[str, Any]:
"""获取系统性能指标"""
return {
'cpu_percent': psutil.cpu_percentinterval=1,
'memory_percent': psutil.virtual_memory().percent,
'disk_usage': psutil.disk_usage'/'.percent,
'network_connections': len(psutil.net_connections()),
'load_average': psutil.getloadavg() if hasattrpsutil, 'getloadavg' else None
}