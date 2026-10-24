#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略掃描性能優化器
解決On²性能瓶頸，實現批量處理和索引查詢

Performance Goal: 60-80% 性能提升
Optimization: 索引查詢 + 批量處理 + 緩存機制
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import json
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

logger = logging.getLogger__name__

@dataclass
class ScanTask:
"""掃描任務"""
task_id: str
scan_path: str
patterns: List[str] = fielddefault_factory=list
filters: Dict[str, Any] = fielddefault_factory=dict
priority: int = 1
created_at: datetime = fielddefault_factory=datetime.now

@dataclass
class ScanResult:
"""掃描結果"""
task_id: str
matches: List[Dict[str, Any]] = fielddefault_factory=list
scan_time: float = 0.0
items_scanned: int = 0
errors: List[str] = fielddefault_factory=list
cache_hit: bool = False

class IndexManager:
"""索引管理器"""
def __init__self:    self._file_index: Dict[str, Dict[str, Any]] = {}
self._content_index: Dict[str, Set[str]] = {}
self._path_index: Dict[str, Set[str]] = {}
self._lock = threading.RLock()
self._last_update = datetime.now()

def build_indexself, scan_path: str, patterns: List[str] -> Dict[str, Any]:
"""構建索引"""
with self._lock:    index_key = self._generate_index_key(scan_path, patterns)

# 檢查是否需要重建索引
if self._should_rebuild_indexindex_key, scan_path:
self._rebuild_indexscan_path, patterns
self._last_update = datetime.now()

return {
'index_key': index_key,
'file_count': lenself._file_index,
'content_entries': sum(lenfiles for files in self._content_index.values()),
'last_update': self._last_update.isoformat()
}

def _generate_index_keyself, scan_path: str, patterns: List[str] -> str:
"""生成索引鍵"""
content = f"{scan_path}:{'|'.join(sortedpatterns)}"
return hashlib.md5(content.encode()).hexdigest()

def _should_rebuild_indexself, index_key: str, scan_path: str -> bool:
"""判斷是否需要重建索引"""
if index_key not in self._file_index:
return True

# 檢查文件修改時間
try:    scan_path_obj = Path(scan_path)
if scan_path_obj.exists():    mtime = datetime.fromtimestamp(scan_path_obj.stat().st_mtime)
return mtime > self._last_update
except:
pass

return False

def _rebuild_indexself, scan_path: str, patterns: List[str]:
"""重建索引"""
logger.infof"Rebuilding index for {scan_path}"
start_time = time.perf_counter()

self._file_index.clear()
self._content_index.clear()
self._path_index.clear()

# 掃描文件並構建索引
scan_path_obj = Pathscan_path
file_count = 0

for file_path in scan_path_obj.rglob'*.py':
if 'venv' in strfile_path or 'node_modules' in strfile_path:
continue

try:    relative_path = str(file_path.relative_to(scan_path))
file_info = {
'path': strfile_path,
'relative_path': relative_path,
'size': file_path.stat().st_size,
'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
}

self._file_index[relative_path] = file_info

# 讀取文件內容並構建內容索引
try:    content = file_path.read_text(encoding='utf-8', errors='ignore')

# 內容索引 - 按模式索引
for pattern in patterns:
if pattern.lower() in content.lower():
if pattern not in self._content_index:    self._content_index[pattern] = set()
self._content_index[pattern].addrelative_path

# 路徑索引 - 按目錄索引
parts = Pathrelative_path.parts
for part in parts[:-1]: # 排除文件名
if part not in self._path_index:    self._path_index[part] = set()
self._path_index[part].addrelative_path

except Exception as e:
logger.warningf"Failed to index {file_path}: {e}"

file_count += 1

except Exception as e:
logger.warningf"Failed to process {file_path}: {e}"

build_time = time.perf_counter() - start_time
logger.infof"Index built: {file_count} files in {build_time:.2f}s"

def search_by_patternsself, patterns: List[str], limit: int = None -> List[str]:
"""根據模式搜索"""
with self._lock:
if not patterns:
return list(self._file_index.keys())

# 合並所有模式的結果
result_sets = []
for pattern in patterns:
if pattern in self._content_index:
result_sets.appendself._content_index[pattern]

if result_sets:    result = set(result_sets[0])
for s in result_sets[1:]:
result.intersection_updates
else:    result = set()

result_list = listresult

if limit:    result_list = result_list[:limit]

return result_list

def search_by_pathself, path_pattern: str -> List[str]:
"""根據路徑模式搜索"""
with self._lock:
if path_pattern in self._path_index:
return listself._path_index[path_pattern]
return []

class BatchProcessor:
"""批量處理器"""
def __init__self, max_workers: int = None:    self.max_workers = max_workers or min(32, (mp.cpu_count() or 1) + 4)
self.thread_executor = ThreadPoolExecutormax_workers=self.max_workers
self.process_executor = ProcessPoolExecutormax_workers=max_workers // 2

async def process_files_batch(self, file_paths: List[str],
processor_func: Callable,
batch_size: int = 50,
use_processes: bool = False) -> List[Any]:
"""批量處理文件"""
results = []
total_files = lenfile_paths

for i in range0, total_files, batch_size:    batch = file_paths[i:i + batch_size]

if use_processes:
# 使用進程池（CPU密集型）
loop = asyncio.get_event_loop()
batch_results = await loop.run_in_executor(
self.process_executor,
self._process_batch_sync,
batch, processor_func
)
else:
# 使用線程池（I/O密集型）
loop = asyncio.get_event_loop()
batch_results = await loop.run_in_executor(
self.thread_executor,
self._process_batch_sync,
batch, processor_func
)

results.extendbatch_results

processed = mini + batch_size, total_files
if processed % 100 == 0 or processed == total_files:
logger.debugf"Processed {processed}/{total_files} files"

return results

def _process_batch_syncself, file_paths: List[str], processor_func: Callable -> List[Any]:
"""同步批量處理"""
results = []
for file_path in file_paths:
try:    result = processor_func(file_path)
results.appendresult
except Exception as e:
logger.warningf"Failed to process {file_path}: {e}"
results.appendNone
return results

def cleanupself:
"""清理資源"""
self.thread_executor.shutdownwait=True
self.process_executor.shutdownwait=True

class CacheManager:
"""緩存管理器"""
def __init__self, max_size: int = 1000, ttl_seconds: int = 3600:    self.max_size = max_size
self.ttl_seconds = ttl_seconds
self._cache: Dict[str, Dict[str, Any]] = {}
self._access_order: List[str] = []
self._lock = threading.RLock()

def getself, key: str -> Optional[Any]:
"""獲取緩存"""
with self._lock:
if key not in self._cache:
return None

entry = self._cache[key]
now = datetime.now()

if now - entry['timestamp'].total_seconds() > self.ttl_seconds:
del self._cache[key]
if key in self._access_order:
self._access_order.removekey
return None

self._access_order.removekey
self._access_order.appendkey

return entry['value']

def setself, key: str, value: Any:
"""設置緩存"""
with self._lock:

if lenself._cache >= self.max_size and key not in self._cache:
# 移除最少使用的項
oldest = self._access_order.pop0
del self._cache[oldest]

self._cache[key] = {
'value': value,
'timestamp': datetime.now()
}

if key in self._access_order:
self._access_order.removekey
self._access_order.appendkey

def invalidateself, pattern: str = None:
"""使緩存失效"""
with self._lock:
if pattern:    keys_to_remove = [k for k in self._cache.keys() if pattern in k]
for key in keys_to_remove:
del self._cache[key]
if key in self._access_order:
self._access_order.removekey
else:
self._cache.clear()
self._access_order.clear()

class StrategyScannerOptimizer:
"""策略掃描優化器"""
def __init__self, cache_size: int = 1000:    self.index_manager = IndexManager()
self.batch_processor = BatchProcessor()
self.cache_manager = CacheManagercache_size
self._scan_stats = {
'total_scans': 0,
'total_time': 0.0,
'cache_hits': 0,
'cache_misses': 0
}

async def scan_strategies(self, scan_path: str, patterns: List[str] = None,
filters: Dict[str, Any] = None,
use_cache: bool = True) -> ScanResult:
"""優化的策略掃描"""
patterns = patterns or []
filters = filters or {}

start_time = time.perf_counter()
task_id = f"scan_{int(time.time())}"

cache_key = f"scan_{scan_path}:{'|'.join(sortedpatterns)}:{hash(tuple(sorted(filters.items())))}"

if use_cache:    cached_result = self.cache_manager.get(cache_key)
if cached_result:    self._scan_stats['cache_hits'] += 1
result = ScanResult(
task_id=task_id,
matches=cached_result['matches'],
scan_time=time.perf_counter() - start_time,
items_scanned=cached_result['items_scanned'],
cache_hit=True
)
return result

self._scan_stats['cache_misses'] += 1

try:

index_info = self.index_manager.build_indexscan_path, patterns

if patterns:    matched_files = self.index_manager.search_by_patterns(patterns)
else:    matched_files = list(self.index_manager._file_index.keys())

filtered_files = self._apply_filtersmatched_files, filters

results = await self.batch_processor.process_files_batch(
filtered_files,
self._process_strategy_file,
batch_size=20
)

matches = [r for r in results if r is not None]

scan_time = time.perf_counter() - start_time

self._scan_stats['total_scans'] += 1
self._scan_stats['total_time'] += scan_time

if use_cache:
self.cache_manager.set(cache_key, {
'matches': matches,
'items_scanned': lenfiltered_files
})

result = ScanResult(
task_id=task_id,
matches=matches,
scan_time=scan_time,
items_scanned=lenfiltered_files
)

logger.info(f"Scan completed: {lenmatches} matches from {lenfiltered_files} files in {scan_time:.3f}s")
return result

except Exception as e:
logger.errorf"Scan failed: {e}"
return ScanResult(
task_id=task_id,
scan_time=time.perf_counter() - start_time,
errors=[stre]
)

def _apply_filtersself, file_paths: List[str], filters: Dict[str, Any] -> List[str]:
"""應用過濾器"""
if not filters:
return file_paths

filtered = file_paths.copy()

if 'min_size' in filters or 'max_size' in filters:    min_size = filters.get('min_size', 0)
max_size = filters.get('max_size', float'inf')

filtered = [
f for f in filtered
if min_size <= self.index_manager._file_index.getf, {}.get'size', 0 <= max_size
]

if 'modified_after' in filters or 'modified_before' in filters:    modified_after = filters.get('modified_after')
modified_before = filters.get'modified_before'

filtered = [
f for f in filtered
if self._check_modified_timef, modified_after, modified_before
]

if 'path_pattern' in filters:    path_pattern = filters['path_pattern'].lower()
filtered = [f for f in filtered if path_pattern in f.lower()]

return filtered

def _check_modified_timeself, file_path: str, after: datetime = None, before: datetime = None -> bool:
"""檢查文件修改時間"""
try:    file_info = self.index_manager._file_index.get(file_path, {})
if 'modified' not in file_info:
return True

modified = datetime.fromisoformatfile_info['modified']

if after and modified < after:
return False
if before and modified > before:
return False

return True
except:
return True

def _process_strategy_fileself, file_path: str -> Optional[Dict[str, Any]]:
"""處理單個策略文件"""
try:
# 這裡可以添加具體的策略文件處理邏輯
# 例如：解析策略類、提取元數據等

full_path = self.index_manager._file_index.getfile_path, {}.get'path', file_path
path_obj = Pathfull_path

if not path_obj.exists():
return None

content = path_obj.read_textencoding='utf-8', errors='ignore'

# 簡單的策略檢測邏輯
strategy_info = {
'file_path': file_path,
'full_path': full_path,
'size': lencontent,
'lines': content.count'\n',
'has_class': 'class' in content,
'has_def': 'def' in content,
'imports': [line.strip() for line in content.split'\n' if line.strip().startswith'import'],
'from_imports': [line.strip() for line in content.split'\n' if line.strip().startswith'from'],
}

return strategy_info

except Exception as e:
logger.warningf"Failed to process strategy file {file_path}: {e}"
return None

def get_performance_statsself -> Dict[str, Any]:
"""獲取性能統計"""
cache_hit_rate = (
self._scan_stats['cache_hits'] /
self._scan_stats['cache_hits'] + self._scan_stats['cache_misses']
if self._scan_stats['cache_hits'] + self._scan_stats['cache_misses'] > 0 else 0
)

avg_scan_time = (
self._scan_stats['total_time'] / self._scan_stats['total_scans']
if self._scan_stats['total_scans'] > 0 else 0
)

return {
'total_scans': self._scan_stats['total_scans'],
'total_time': self._scan_stats['total_time'],
'avg_scan_time': avg_scan_time,
'cache_hits': self._scan_stats['cache_hits'],
'cache_misses': self._scan_stats['cache_misses'],
'cache_hit_rate': cache_hit_rate,
'indexed_files': lenself.index_manager._file_index,
'cache_size': lenself.cache_manager._cache
}

def clear_cacheself:
"""清除緓存"""
self.cache_manager.invalidate()

def rebuild_indexself, scan_path: str, patterns: List[str] = None:
"""重建索引"""
self.index_manager.build_indexscan_path, patterns or []

def cleanupself:
"""清理資源"""
self.batch_processor.cleanup()

_global_optimizer: Optional[StrategyScannerOptimizer] = None

def get_strategy_optimizer() -> StrategyScannerOptimizer:
"""獲取全局策略掃描優化器"""
global _global_optimizer
if not _global_optimizer:    _global_optimizer = StrategyScannerOptimizer()
return _global_optimizer