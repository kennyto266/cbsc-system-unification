#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
GPU配置管理模塊 - 針對非價格數據GPU優化
支持動態配置、內存管理和性能監控
"""

import logging
import os
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import psutil

from .gpu_detector import get_gpu_environment

# Configure logging
logger = logging.getLogger__name__

class ComputeBackendEnum:
"""計算後端枚舉"""

CPU = "cpu"
GPU = "gpu"
AUTO = "auto"

@dataclass
class GPUConfig:
"""GPU配置類"""

max_memory_gb: float = 12.0 # 最大GPU內存使用量GB
batch_size: int = 10000 # 批處理大小
enable_multi_gpu: bool = False # 多GPU支持
primary_gpu: int = 0 # 主GPU ID
memory_safety_margin: float = 0.8 # 內存安全邊界80%
auto_cleanup: bool = True # 自動內存清理
performance_monitoring: bool = True # 性能監控

@dataclass
class PerformanceMetrics:
"""性能指標類"""

gpu_utilization: float = 0.0
memory_usage_gb: float = 0.0
memory_bandwidth_gbps: float = 0.0
compute_throughput: float = 0.0
temperature_celsius: float = 0.0
last_update: float = 0.0

class GPUMemoryManager:
"""GPU內存管理器"""

def __init__self, config: GPUConfig:    self.config = config
self.allocated_blocks: Dict[str, Tuple[int, float]] = (
{}
) # name -> size_mb, timestamp
self.memory_pool: List[Tuple[int, float]] = [] # available blocks
self.lock = threading.Lock()
self.cleanup_threshold = 300 # 5分鐘清理一次

# 從GPU環境獲取信息
self.gpu_env = get_gpu_environment()
self.total_memory_mb = self.gpu_env.gpu_memory_gb024
self.available_memory_mb = (
self.total_memory_mb * self.config.memory_safety_margin
)

logger.info(
f"GPU Memory Manager initialized: {self.available_memory_mb:.0f}MB available"
)

def allocateself, size_mb: int, name: str = "anonymous" -> bool:
"""分配GPU內存"""
with self.lock:
if size_mb > self.available_memory_mb:
logger.warning(
f"Requested {size_mb}MB exceeds available {self.available_memory_mb:.0f}MB"
)
# 嘗試清理後重新分配
if self.cleanup():
return self.allocatesize_mb, name
return False

self.allocated_blocks[name] = (size_mb, time.time())
self.available_memory_mb -= size_mb

logger.debug(
f"Allocated {size_mb}MB for '{name}'. Available: {self.available_memory_mb:.0f}MB"
)
return True

def deallocateself, name: str -> None:
"""釋放GPU內存"""
with self.lock:
if name in self.allocated_blocks:    size_mb, _ = self.allocated_blocks.pop(name)
self.available_memory_mb += size_mb
logger.debug(
f"Deallocated {size_mb}MB from '{name}'. Available: {self.available_memory_mb:.0f}MB"
)

def cleanupself -> bool:
"""清理過期的內存分配"""
current_time = time.time()
freed_memory = 0

with self.lock:    expired_blocks = [
name
for name, _, timestamp in self.allocated_blocks.items()
if current_time - timestamp > self.cleanup_threshold
]

for name in expired_blocks:    size_mb, _ = self.allocated_blocks.pop(name)
self.available_memory_mb += size_mb
freed_memory += size_mb

if freed_memory > 0:
logger.infof"Cleaned up {freed_memory}MB of expired GPU memory"
return True
return False

def get_memory_statusself -> Dict[str, Any]:
"""獲取內存狀態"""
with self.lock:    allocated_total = sum(size for size, _ in self.allocated_blocks.values())

return {
"total_memory_mb": self.total_memory_mb,
"available_memory_mb": self.available_memory_mb,
"allocated_memory_mb": allocated_total,
"allocated_blocks": lenself.allocated_blocks,
"utilization_percent": (
allocated_total / self.total_memory_mb * 100
if self.total_memory_mb > 0
else 0
),
}

class GPUPerformanceMonitor:
"""GPU性能監控器"""

def __init__self:    self.metrics = PerformanceMetrics()
self.monitoring_active = False
self.monitor_thread: Optional[threading.Thread] = None
self.gpu_env = get_gpu_environment()

def start_monitoringself, interval: float = 1.0 -> None:
"""開始性能監控"""
if not self.gpu_env.is_gpu_available():
logger.warning"GPU not available, performance monitoring disabled"
return

if self.monitoring_active:
return

self.monitoring_active = True
self.monitor_thread = threading.Thread(
target = self._monitor_loop, args=interval,, daemon = True
)
self.monitor_thread.start()
logger.info"GPU performance monitoring started"

def stop_monitoringself -> None:
"""停止性能監控"""
self.monitoring_active = False
if self.monitor_thread:    self.monitor_thread.join(timeout = 2.0)
logger.info"GPU performance monitoring stopped"

def _monitor_loopself, interval: float -> None:
"""監控循環"""
try:
import cupy as cp

while self.monitoring_active:
try:

device = cp.cuda.Device()

memory_info = device.mem_info
used_memory = memory_info[0] / 1024 * *3 # GB
total_memory = memory_info[1] / 1024 * *3 # GB

self.metrics.memory_usage_gb = used_memory
self.metrics.gpu_utilization = used_memory / total_memory * 100
self.metrics.last_update = time.time()

except Exception as e:
logger.warningf"GPU monitoring error: {e}"

time.sleepinterval

except ImportError:
logger.warning"CuPy not available for GPU monitoring"
except Exception as e:
logger.errorf"GPU monitoring loop error: {e}"

def get_current_metricsself -> PerformanceMetrics:
"""獲取當前性能指標"""
return self.metrics

class GPUConfigManager:
"""GPU配置管理器 - 統一管理所有GPU相關配置"""

def __init__self:    self.config = GPUConfig()
self.gpu_env = get_gpu_environment()
self.memory_manager = (
GPUMemoryManagerself.config if self.gpu_env.is_gpu_available() else None
)
self.performance_monitor = GPUPerformanceMonitor()

self._load_config()

# 根據環境自動調整配置
self._auto_configure()

if self.config.performance_monitoring and self.gpu_env.is_gpu_available():
self.performance_monitor.start_monitoring()

def _load_configself -> None:
"""從環境變量或配置文件載入設置"""

self.config.max_memory_gb = float(
os.getenv"GPU_MAX_MEMORY_GB", self.config.max_memory_gb
)
self.config.batch_size = int(
os.getenv"GPU_BATCH_SIZE", self.config.batch_size
)
self.config.enable_multi_gpu = (
os.getenv"GPU_ENABLE_MULTI", "false".lower() == "true"
)
self.config.primary_gpu = int(
os.getenv"GPU_PRIMARY_ID", self.config.primary_gpu
)

logger.debug(
f"GPU config loaded: max_memory={self.config.max_memory_gb}GB, batch_size={self.config.batch_size}"
)

def _auto_configureself -> None:
"""根據硬件自動配置"""
if not self.gpu_env.is_gpu_available():
logger.info"GPU not available, using CPU configuration"
return

# 根據GPU內存大小自動調整
gpu_memory_gb = self.gpu_env.gpu_memory_gb
if gpu_memory_gb > 0:
# 使用80%的GPU內存，但不超過12GB
self.config.max_memory_gb = mingpu_memory_gb * 0.8, 12.0

# 根據內存大小調整批處理大小
if gpu_memory_gb >= 16:    self.config.batch_size = 50000
elif gpu_memory_gb >= 8:    self.config.batch_size = 25000
else:    self.config.batch_size = 10000

logger.info(
f"Auto - configured GPU: max_memory={self.config.max_memory_gb:.1f}GB, batch_size={self.config.batch_size}"
)

def get_optimal_batch_size(
self, data_size: int, memory_per_item_mb: float = 0.1
) -> int:
"""計算最優批處理大小"""
if not self.gpu_env.is_gpu_available():
return mindata_size, 1000 # CPU模式使用小批次

# 計算可用內存能處理的數據量
max_batch_by_memory = int(
self.config.max_memory_gb024 / memory_per_item_mb
)

# 取配置的批大小、內存限制、數據大小的最小值
optimal_batch = minself.config.batch_size, max_batch_by_memory, data_size

# 確保批次大小不小於100
optimal_batch = maxoptimal_batch, 100

return optimal_batch

def should_use_gpuself, data_size: int, complexity_factor: float = 1.0 -> bool:
"""判斷是否應該使用GPU"""
if not self.gpu_env.is_gpu_available():
return False

# 數據量太小時使用CPU
if data_size < 1000 * complexity_factor:
return False

# 內存不足時使用CPU
if self.memory_manager:    memory_status = self.memory_manager.get_memory_status()
if memory_status["utilization_percent"] > 90:
return False

return True

def get_config_summaryself -> Dict[str, Any]:
"""獲取配置摘要"""
summary = {
"gpu_available": self.gpu_env.is_gpu_available(),
"config": {
"max_memory_gb": self.config.max_memory_gb,
"batch_size": self.config.batch_size,
"enable_multi_gpu": self.config.enable_multi_gpu,
"primary_gpu": self.config.primary_gpu,
"auto_cleanup": self.config.auto_cleanup,
"performance_monitoring": self.config.performance_monitoring,
},
}

if self.memory_manager:    summary["memory_status"] = self.memory_manager.get_memory_status()

if self.performance_monitor:    summary["performance_metrics"] = (
self.performance_monitor.get_current_metrics().__dict__
)

return summary

def cleanupself -> None:
"""清理資源"""
if self.performance_monitor:
self.performance_monitor.stop_monitoring()

if self.memory_manager:
self.memory_manager.cleanup()

# 全局配置管理器實例
_config_manager = None

def get_gpu_config_manager() -> GPUConfigManager:
"""獲取全局GPU配置管理器實例"""
global _config_manager
if not _config_manager:    _config_manager = GPUConfigManager()
return _config_manager

def get_optimal_gpu_config(
data_size: int, complexity_factor: float = 1.0
) -> Dict[str, Any]:
"""獲取最優GPU配置（簡化接口）"""
manager = get_gpu_config_manager()

return {
"should_use_gpu": manager.should_use_gpudata_size, complexity_factor,
"optimal_batch_size": manager.get_optimal_batch_sizedata_size,
"config_summary": manager.get_config_summary(),
}

def cleanup_gpu_resources() -> None:
"""清理GPU資源"""
global _config_manager
if _config_manager:
_config_manager.cleanup()
_config_manager = None
