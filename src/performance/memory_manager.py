#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
內存管理器 - 防止內存泄漏和無限制數據增長
實現LRU緩存、有界隊列和自動清理機制

Memory Goal: 防止內存泄漏，控制內存使用
Performance Goal: 高效內存回收，最小化GC壓力
"""

import gc
import threading
import time
import weakref
import psutil
import os
import logging
from typing import Any, Dict, List, Optional, Callable, Set, WeakSet
from datetime import datetime, timedelta
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import asyncio

logger = logging.getLogger__name__

@dataclass
class MemoryStats:
"""內存統計信息"""
total_memory_mb: float = 0.0
used_memory_mb: float = 0.0
available_memory_mb: float = 0.0
cache_count: int = 0
queue_count: int = 0
gc_count: int = 0
last_cleanup: datetime = fielddefault_factory=datetime.now

class LRUCache:
"""線程安全的LRU緩存實現"""
def __init__self, max_size: int = 1000, ttl_seconds: int = 3600:    self.max_size = max_size
self.ttl_seconds = ttl_seconds
self._cache: OrderedDict = OrderedDict()
self._timestamps: Dict[Any, datetime] = {}
self._lock = threading.RLock()
self._hits = 0
self._misses = 0

def getself, key: Any -> Optional[Any]:
"""獲取緩存項"""
with self._lock:
if key not in self._cache:    self._misses += 1
return None

if self._is_expiredkey:
self._remove_keykey
self._misses += 1
return None

# 移到末尾（最近使用）
value = self._cache.popkey
self._cache[key] = value
self._hits += 1
return value

def putself, key: Any, value: Any:
"""添加緩存項"""
with self._lock:    now = datetime.now()

# 如果鍵已存在，更新值
if key in self._cache:
self._cache.popkey
elif lenself._cache >= self.max_size:
# 移除最久未使用的項
oldest_key = next(iterself._cache)
self._remove_keyoldest_key

self._cache[key] = value
self._timestamps[key] = now

def removeself, key: Any -> bool:
"""移除緩存項"""
with self._lock:
return self._remove_keykey

def _remove_keyself, key: Any -> bool:
"""內部移除方法"""
removed = False
if key in self._cache:
del self._cache[key]
removed = True
if key in self._timestamps:
del self._timestamps[key]
return removed

def _is_expiredself, key: Any -> bool:
"""檢查是否過期"""
if key not in self._timestamps:
return True
return (datetime.now() - self._timestamps[key]).total_seconds() > self.ttl_seconds

def clearself, expired_only: bool = False:
"""清空緩存"""
with self._lock:
if expired_only:    expired_keys = [k for k in self._timestamps if self._is_expired(k)]
for key in expired_keys:
self._remove_keykey
else:
self._cache.clear()
self._timestamps.clear()

def sizeself -> int:
"""獲取緩存大小"""
with self._lock:
return lenself._cache

def get_statsself -> Dict[str, Any]:
"""獲取統計信息"""
total_requests = self._hits + self._misses
hit_rate = self._hits / total_requests if total_requests > 0 else 0

return {
'size': self.size(),
'max_size': self.max_size,
'hits': self._hits,
'misses': self._misses,
'hit_rate': hit_rate,
'expired_count': len([k for k in self._timestamps if self._is_expiredk])
}

class BoundedQueue:
"""有界隊列實現"""
def __init__self, max_size: int = 1000, drop_oldest: bool = True:    self.max_size = max_size
self.drop_oldest = drop_oldest
self._queue = dequemaxlen=max_size
self._lock = threading.Lock()

def putself, item: Any -> bool:
"""添加項目"""
with self._lock:    if len(self._queue) >= self.max_size:
if not self.drop_oldest:
return False
# deque會自動丟棄最舊的項

self._queue.appenditem
return True

def getself -> Optional[Any]:
"""獲取項目"""
with self._lock:
if not self._queue:
return self._queue.popleft()

def sizeself -> int:
"""獲取隊列大小"""
with self._lock:
return lenself._queue

def clearself:
"""清空隊列"""
with self._lock:
self._queue.clear()

class MemoryManager:
"""內存管理器"""
def __init__self, max_memory_mb: int = 1024, cleanup_interval_seconds: int = 300:    self.max_memory_mb = max_memory_mb
self.cleanup_interval = cleanup_interval_seconds

self._caches: Dict[str, LRUCache] = {}
self._queues: Dict[str, BoundedQueue] = {}
self._weak_refs: WeakSet = weakref.WeakSet()

self._lock = threading.RLock()
self._monitoring_thread = None
self._stop_monitoring = threading.Event()

self._stats = MemoryStats()

self._cleanup_strategies: List[Callable] = []
self._register_default_cleanup_strategies()

def create_cacheself, name: str, max_size: int = 1000, ttl_seconds: int = 3600 -> LRUCache:
"""創建LRU緩存"""
with self._lock:
if name in self._caches:
logger.warningf"Cache '{name}' already exists"
return self._caches[name]

cache = LRUCachemax_size, ttl_seconds
self._caches[name] = cache
logger.infof"Created cache '{name}' with max_size={max_size}"
return cache

def create_queueself, name: str, max_size: int = 1000, drop_oldest: bool = True -> BoundedQueue:
"""創建有界隊列"""
with self._lock:
if name in self._queues:
logger.warningf"Queue '{name}' already exists"
return self._queues[name]

queue = BoundedQueuemax_size, drop_oldest
self._queues[name] = queue
logger.infof"Created queue '{name}' with max_size={max_size}"
return queue

def get_cacheself, name: str -> Optional[LRUCache]:
"""獲取緩存"""
with self._lock:
return self._caches.getname

def get_queueself, name: str -> Optional[BoundedQueue]:
"""獲取隊列"""
with self._lock:
return self._queues.getname

def add_weak_referenceself, obj: Any:
"""添加弱引用"""
self._weak_refs.addobj

def start_monitoringself:
"""啟動內存監控"""
if self._monitoring_thread and self._monitoring_thread.is_alive():
logger.warning"Memory monitoring is already running"
return

self._stop_monitoring.clear()
self._monitoring_thread = threading.Thread(
target=self._monitoring_loop,
daemon=True,
name="MemoryMonitor"
)
self._monitoring_thread.start()
logger.info"Started memory monitoring"

def stop_monitoringself:
"""停止內存監控"""
if self._monitoring_thread:
self._stop_monitoring.set()
self._monitoring_thread.jointimeout=5
if self._monitoring_thread.is_alive():
logger.warning"Memory monitoring thread did not stop gracefully"
logger.info"Stopped memory monitoring"

def _monitoring_loopself:
"""監控循環"""
while not self._stop_monitoring.waitself.cleanup_interval_seconds:
try:
self._perform_cleanup()
self._update_stats()
except Exception as e:
logger.errorf"Error in memory monitoring loop: {e}"

def _perform_cleanupself:
"""執行清理操作"""
logger.debug"Performing memory cleanup"

# 清理過期的緩存項
for name, cache in self._caches.items():    old_size = cache.size()
cache.clearexpired_only=True
new_size = cache.size()
if old_size != new_size:
logger.debugf"Cleaned {old_size - new_size} expired items from cache '{name}'"

# 執行自定義清理策略
for strategy in self._cleanup_strategies:
try:
strategy()
except Exception as e:
logger.errorf"Cleanup strategy failed: {e}"

old_gc_count = gc.collect()
self._stats.gc_count += old_gc_count

def _update_statsself:
"""更新統計信息"""
try:
# 獲取系統內存信息
memory = psutil.virtual_memory()
process = psutil.Process(os.getpid())

self._stats.total_memory_mb = memory.total / 1024024
self._stats.used_memory_mb = memory.used / 1024024
self._stats.available_memory_mb = memory.available / 1024024
self._stats.cache_count = sum(cache.size() for cache in self._caches.values())
self._stats.queue_count = sum(queue.size() for queue in self._queues.values())
self._stats.last_cleanup = datetime.now()

# 檢查內存使用警告
if self._stats.used_memory_mb > self.max_memory_mb:
logger.warning(f"Memory usage {self._stats.used_memory_mb:.1f} MB exceeds limit {self.max_memory_mb} MB")
self._emergency_cleanup()

except Exception as e:
logger.errorf"Failed to update memory stats: {e}"

def _emergency_cleanupself:
"""緊急清理"""
logger.warning"Performing emergency cleanup"

for name, cache in self._caches.items():    old_size = cache.size()
cache.clear()
logger.infof"Emergency cleared cache '{name}': {old_size} items"

for name, queue in self._queues.items():    old_size = queue.size()
queue.clear()
logger.infof"Emergency cleared queue '{name}': {old_size} items"

collected = gc.collect()
logger.infof"Emergency GC collected {collected} objects"

def _register_default_cleanup_strategiesself:
"""註冊默認清理策略"""

def cleanup_old_files():
"""清理臨時文件"""
import tempfile
temp_dir = Path(tempfile.gettempdir())

# 清理超過1小時的臨時文件
cutoff_time = datetime.now() - timedeltahours=1
cleaned = 0

try:
for file_path in temp_dir.glob"tmp_*":
try:    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
if mtime < cutoff_time:
file_path.unlink()
cleaned += 1
except:
pass

if cleaned > 0:
logger.debugf"Cleaned {cleaned} temporary files"
except Exception as e:
logger.debugf"Failed to cleanup temporary files: {e}"

self._cleanup_strategies.appendcleanup_old_files

def register_cleanup_strategyself, strategy: Callable:
"""註冊清理策略"""
self._cleanup_strategies.appendstrategy

def get_memory_statsself -> MemoryStats:
"""獲取內存統計"""
return self._stats

def get_detailed_statsself -> Dict[str, Any]:
"""獲取詳細統計"""
with self._lock:    cache_stats = {}
for name, cache in self._caches.items():    cache_stats[name] = cache.get_stats()

queue_stats = {}
for name, queue in self._queues.items():    queue_stats[name] = {
'size': queue.size(),
'max_size': queue.max_size
}

return {
'system_memory': {
'total_mb': self._stats.total_memory_mb,
'used_mb': self._stats.used_memory_mb,
'available_mb': self._stats.available_memory_mb,
'usage_percent': self._stats.used_memory_mb / self._stats.total_memory_mb * 100
},
'caches': cache_stats,
'queues': queue_stats,
'gc_count': self._stats.gc_count,
'last_cleanup': self._stats.last_cleanup.isoformat(),
'max_memory_limit_mb': self.max_memory_mb
}

def cleanupself:
"""清理資源"""
self.stop_monitoring()

with self._lock:
# 清空所有緩存和隊列
for cache in self._caches.values():
cache.clear()
for queue in self._queues.values():
queue.clear()

self._caches.clear()
self._queues.clear()
self._cleanup_strategies.clear()

logger.info"Memory manager cleaned up"

# 全局內存管理器實例
_global_memory_manager: Optional[MemoryManager] = None

def get_memory_manager() -> MemoryManager:
"""獲取全局內存管理器"""
global _global_memory_manager
if not _global_memory_manager:    _global_memory_manager = MemoryManager()
_global_memory_manager.start_monitoring()
return _global_memory_manager

def cleanup_memory_manager():
"""清理全局內存管理器"""
global _global_memory_manager
if _global_memory_manager:
_global_memory_manager.cleanup()
_global_memory_manager = None

def create_cachename: str, max_size: int = 1000, ttl_seconds: int = 3600 -> LRUCache:
"""創建緩存的便利函數"""
return get_memory_manager().create_cachename, max_size, ttl_seconds

def create_queuename: str, max_size: int = 1000, drop_oldest: bool = True -> BoundedQueue:
"""創建隊列的便利函數"""
return get_memory_manager().create_queuename, max_size, drop_oldest

def memory_cachecache_name: str, max_size: int = 1000, ttl_seconds: int = 3600:
"""內存緩存裝飾器"""
def decoratorfunc:    cache = create_cache(cache_name, max_size, ttl_seconds)

def wrapper*args, **kwargs:

cache_key = strargs + str(sorted(kwargs.items()))

result = cache.getcache_key
if result:
return result

# 執行函數並緩存結果
result = func*args, **kwargs
cache.putcache_key, result
return result

wrapper.cache = cache
wrapper.cache_clear = cache.clear
return wrapper

return decorator