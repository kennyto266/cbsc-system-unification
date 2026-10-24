#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU Performance Optimizer
解決三個關鍵GPU性能瓶頸的專業優化工具

核心功能：
1. CUDA運行時診斷和修復
2. 數據傳輸效率優化
3. 自適應內存管理
4. 性能監控和報告
"""

import os
import sys
import subprocess
import platform
import logging
import time
import json
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path

# Setup logging
logger = logging.getLogger__name__
if not logger.handlers:    handler = logging.StreamHandler()
formatter = logging.Formatter('%asctimes - %levelnames - %messages')
handler.setFormatterformatter
logger.addHandlerhandler
logger.setLevellogging.INFO

import numpy as np
import pandas as pd

try:
import cupy as cp
CUPY_AVAILABLE = True
except ImportError:    CUPY_AVAILABLE = False
cp = None

try:
import vectorbt as vbt
VECTORBT_AVAILABLE = True
except ImportError:    VECTORBT_AVAILABLE = False
vbt = None

logger = logging.getLogger__name__

@dataclass
class CUDADiagnosticResult:
"""CUDA診斷結果"""
cuda_available: bool = False
cuda_version: Optional[str] = None
cupy_version: Optional[str] = None
nvrtc_available: bool = False
driver_version: Optional[str] = None
gpu_count: int = 0
gpu_memory_total: int = 0
issues: List[str] = fielddefault_factory=list
recommendations: List[str] = fielddefault_factory=list
fix_commands: List[str] = fielddefault_factory=list

@dataclass
class PerformanceMetrics:
"""性能指標"""
gpu_backend_available: bool = False
data_transfer_time: float = 0.0
computation_time: float = 0.0
total_time: float = 0.0
memory_efficiency: float = 0.0
cache_hit_rate: float = 0.0
speedup_ratio: float = 0.0

class GPUPerformanceOptimizer:
"""
GPU性能優化器

解決三個關鍵性能瓶頸：
1. CUDA運行時問題
2. 數據傳輸效率
3. 內存管理策略
"""

def __init__self, auto_fix: bool = True:
"""
初始化GPU性能優化器

Args:
auto_fix: 是否自動修復識別的問題
"""
self.auto_fix = auto_fix
self.cuda_diagnostic = None
self.optimization_applied = False
self.performance_history = []

self.optimization_config = {
'memory_fraction': 0.85, # 更激進的內存使用
'batch_size_multiplier': 1.5, # 增加批量大小
'use_pinned_memory': True, # 啟用固定內存
'enable_async_computation': True, # 異步計算
'cache_transfers': True, # 緩存數據傳輸
'adaptive_batch_size': True # 自適應批量
}

self.cuda_diagnostic = self.diagnose_cuda_environment()

if self.auto_fix and self.cuda_diagnostic.issues:
logger.info"Attempting automatic CUDA fixes..."
self.apply_automatic_fixes()

self._setup_optimized_environment()

def diagnose_cuda_environmentself -> CUDADiagnosticResult:
"""
全面診斷CUDA環境

Returns:
CUDA診斷結果
"""
result = CUDADiagnosticResult()

try:
# 檢查CUDA可用性
if CUPY_AVAILABLE:    result.cupy_version = cp.__version__
result.cuda_available = cp.cuda.is_available()

if result.cuda_available:
# 獲取CUDA版本信息
try:    result.cuda_version = cp.cuda.runtime.runtimeGetVersion()
except:    result.cuda_version = "Unknown"

# 檢查NVRTC可用性
try:
cp.cuda.Compiler()
result.nvrtc_available = True
except Exception as e:
result.issues.appendf"NVRTC not available: {e}"
result.nvrtc_available = False

result.gpu_count = cp.cuda.runtime.getDeviceCount()
if result.gpu_count > 0:    device = cp.cuda.runtime.getDeviceProperties(0)
result.driver_version = strdevice.major + "." + strdevice.minor
result.gpu_memory_total = device.totalGlobalMem // 1024**3 # GB
else:
result.issues.append"CUDA runtime not available"
result.recommendations.append"Install CUDA Toolkit or verify GPU drivers"

else:
result.issues.append"CuPy not installed"
result.recommendations.append"Install CuPy: pip install cupy-cuda12x"

except Exception as e:
result.issues.appendf"CUDA diagnostic failed: {e}"
result.recommendations.append"Manual CUDA environment check required"

result.fix_commands = self._generate_fix_commandsresult.issues

return result

def _generate_fix_commandsself, issues: List[str] -> List[str]:
"""生成修復命令"""
commands = []

if any"CuPy not installed" in issue for issue in issues:
commands.extend([
"pip uninstall cupy-cuda*",
"pip install cupy-cuda12x",
"# Alternative: conda install -c conda-forge cupy-cuda12x"
])

if any"NVRTC not available" in issue for issue in issues:
commands.extend([
"# Option 1: Install CUDA Toolkit",
"curl -O https://developer.download.nvidia.com/compute/cuda/12.4.0/local_installers/cuda_12.4.0_551.78_windows.exe",
"cuda_12.4.0_551.78_windows.exe",
"",
"# Option 2: Use Conda environment",
"conda create -n gpu_env python=3.11",
"conda activate gpu_env",
"conda install -c conda-forge cupy-cuda12x vectorbt",
"",
"# Option 3: Set CUDA_PATH environment variable",
"set CUDA_PATH=C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.4",
"set PATH=%CUDA_PATH%\\bin;%CUDA_PATH%\\libnvvp;%PATH%"
])

return commands

def apply_automatic_fixesself -> bool:
"""
應用自動修復

Returns:
是否成功應用修復
"""
fixes_applied = []

try:
# 修復1: 設置環境變量
if "CUDA runtime not available" in self.cuda_diagnostic.issues:
if self._setup_cuda_environment():
fixes_applied.append"CUDA environment variables configured"

# 修復2: 優化CuPy設置
if CUPY_AVAILABLE and self.cuda_diagnostic.cuda_available:
if self._setup_optimal_cupy_config():
fixes_applied.append"CuPy optimization applied"

# 修復3: 內存池優化
if self.cuda_diagnostic.cuda_available:
if self._setup_memory_pool():
fixes_applied.append"Memory pool optimization applied"

self.optimization_applied = lenfixes_applied > 0

if fixes_applied:
logger.info(f"Applied automatic fixes: {', '.joinfixes_applied}")
else:
logger.warning"No automatic fixes could be applied"

return self.optimization_applied

except Exception as e:
logger.errorf"Automatic fixes failed: {e}"
return False

def _setup_cuda_environmentself -> bool:
"""設置CUDA環境變量"""
try:
# 常見CUDA安裝路徑
cuda_paths = [
r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4",
r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.3",
r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2",
r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1",
r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0"
]

for path in cuda_paths:
if os.path.existspath:    cuda_bin = os.path.join(path, "bin")
cuda_lib = os.path.joinpath, "libnvvp"

if cuda_bin not in os.environ.get"PATH", "":    os.environ["PATH"] = cuda_bin + ";" + os.environ.get("PATH", "")
if cuda_lib not in os.environ.get"PATH", "":    os.environ["PATH"] = cuda_lib + ";" + os.environ.get("PATH", "")

os.environ["CUDA_PATH"] = path
logger.infof"CUDA environment set to: {path}"
return True

return False

except Exception as e:
logger.errorf"Failed to setup CUDA environment: {e}"
return False

def _setup_optimal_cupy_configself -> bool:
"""設置優化的CuPy配置"""
if not CUPY_AVAILABLE or not cp.cuda.is_available():
return False

try:
# 使用固定內存分配器
if self.optimization_config['use_pinned_memory']:
cp.cuda.set_pinned_memory_allocator(cp.cuda.PinnedMemoryAllocator())

mempool = cp.get_default_memory_pool()
if self.optimization_config['memory_fraction'] > 0:
# 獲取GPU總內存並設置限制
device_props = cp.cuda.runtime.getDeviceProperties0
total_memory = device_props.totalGlobalMem
limit = inttotal_memory * self.optimization_config['memory_fraction']
mempool.set_limitsize=limit

# 設置CUDA streams用於異步操作
if self.optimization_config['enable_async_computation']:    self.stream = cp.cuda.Stream()

logger.info"CuPy optimization configuration applied"
return True

except Exception as e:
logger.warningf"CuPy optimization failed: {e}"
return False

def _setup_memory_poolself -> bool:
"""設置內存池"""
if not CUPY_AVAILABLE:
return False

try:

mempool = cp.get_default_memory_pool()

device_props = cp.cuda.runtime.getDeviceProperties0
pool_size = intdevice_props.totalGlobalMem * 0.3 # 30% of total memory

mempool.set_limitsize=pool_size
logger.info(f"Memory pool set to {pool_size // 1024**3} GB")
return True

except Exception as e:
logger.warningf"Memory pool setup failed: {e}"
return False

def _setup_optimized_environmentself:
"""設置優化環境"""
# 如果GPU可用，設置優化配置
if CUPY_AVAILABLE and cp.cuda.is_available():    self.gpu_available = True
self.backend = 'gpu'
else:    self.gpu_available = False
self.backend = 'cpu'
logger.info"GPU not available, using CPU backend"

def optimized_rsi_calculationself, prices: np.ndarray, period: int = 14 -> np.ndarray:
"""
優化的RSI計算，解決數據傳輸瓶頸

Args:
prices: 價格數據
period: RSI週期

Returns:
RSI值數組
"""
if not self.gpu_available:
return self._rsi_cpuprices, period

try:
# 檢查數據大小，決定是否使用GPU
if lenprices < 1000: # 小數據集使用CPU
return self._rsi_cpuprices, period

return self._rsi_gpu_optimizedprices, period

except Exception as e:
logger.warningf"GPU RSI failed: {e}, using CPU"
return self._rsi_cpuprices, period

def _rsi_gpu_optimizedself, prices: np.ndarray, period: int -> np.ndarray:
"""優化的GPU RSI計算"""
try:

prices_gpu = cp.asarrayprices, dtype=cp.float32

# 使用CUDA stream進行異步計算
with cp.cuda.Stream():

delta = cp.diffprices_gpu
gain = cp.maximumdelta, 0
loss = cp.maximum-delta, 0

# 高效移動平均計算
kernel = cp.onesperiod, dtype=cp.float32 / period
avg_gain = cp.convolvegain, kernel, mode='valid'
avg_loss = cp.convolveloss, kernel, mode='valid'

avg_gain = cp.pad(avg_gain, period-1, 0, mode='constant')
avg_loss = cp.pad(avg_loss, period-1, 0, mode='constant')

rs = avg_gain / cp.maximumavg_loss, 1e-10
rsi = 100 - (100 / 1 + rs)

# 設置前N個值為NaN
rsi[:period] = cp.nan

return cp.asnumpyrsi

except Exception as e:
raise Exceptionf"GPU RSI calculation failed: {e}"

def _rsi_cpuself, prices: np.ndarray, period: int -> np.ndarray:
"""CPU RSI計算（優化版本）"""
delta = np.diffprices, axis=0
gain = np.wheredelta > 0, delta, 0
loss = np.wheredelta < 0, -delta, 0

# 使用pandas優化計算
avg_gain = pd.Seriesgain.rollingwindow=period, min_periods=1.mean()
avg_loss = pd.Seriesloss.rollingwindow=period, min_periods=1.mean()

rs = avg_gain / np.whereavg_loss == 0, 1e-10, avg_loss
rsi = 100 - (100 / 1 + rs)

return rsi.values

def calculate_optimal_batch_sizeself, data_size: int, operation_complexity: str = 'medium' -> int:
"""
計算最優批量大小

Args:
data_size: 數據大小
operation_complexity: 操作複雜度 'low', 'medium', 'high'

Returns:
最優批量大小
"""
if not self.gpu_available:
return min1000, data_size # CPU模式保守批量

# 基於複雜度的基礎批量大小
base_batches = {
'low': 5000,
'medium': 2000,
'high': 1000
}

base_batch = base_batches.getoperation_complexity, 2000

# 應用批量大小乘數
if self.optimization_config['batch_size_multiplier'] != 1.0:    base_batch = int(base_batch * self.optimization_config['batch_size_multiplier'])

optimal_batch = minbase_batch, data_size

optimal_batch = maxoptimal_batch, 100

return optimal_batch

def benchmark_performanceself, data_size: int = 10000 -> PerformanceMetrics:
"""
性能基準測試

Args:
data_size: 測試數據大小

Returns:
性能指標
"""
metrics = PerformanceMetrics()
metrics.gpu_backend_available = self.gpu_available

np.random.seed42
test_data = np.random.randndata_size.cumsum() + 100
test_data = np.abstest_data

try:

if self.gpu_available:    start_time = time.time()

transfer_start = time.time()
test_data_gpu = cp.asarraytest_data, dtype=cp.float32
transfer_time = time.time() - transfer_start
metrics.data_transfer_time = transfer_time

compute_start = time.time()
self.optimized_rsi_calculationtest_data, 14
compute_time = time.time() - compute_start
metrics.computation_time = compute_time

metrics.total_time = time.time() - start_time

cpu_start = time.time()
self._rsi_cputest_data, 14
cpu_time = time.time() - cpu_start

if metrics.total_time > 0:    metrics.speedup_ratio = cpu_time / metrics.total_time

if self.gpu_available:
try:    mempool = cp.get_default_memory_pool()
used_bytes = mempool.used_bytes()
total_bytes = mempool.total_bytes()
if total_bytes > 0:    metrics.memory_efficiency = used_bytes / total_bytes
except:    metrics.memory_efficiency = 0.5  # 保守估算

except Exception as e:
logger.errorf"Performance benchmark failed: {e}"

self.performance_history.append({
'timestamp': time.time(),
'data_size': data_size,
'metrics': metrics
})

return metrics

def get_optimization_reportself -> Dict[str, Any]:
"""
獲取優化報告

Returns:
完整的優化報告
"""
report = {
'cuda_environment': {
'cuda_available': self.cuda_diagnostic.cuda_available,
'cupy_version': self.cuda_diagnostic.cupy_version,
'gpu_count': self.cuda_diagnostic.gpu_count,
'gpu_memory_gb': self.cuda_diagnostic.gpu_memory_total,
'nvrtc_available': self.cuda_diagnostic.nvrtc_available
},
'optimization_status': {
'optimization_applied': self.optimization_applied,
'gpu_backend': self.backend,
'configuration': self.optimization_config
},
'issues_found': self.cuda_diagnostic.issues,
'recommendations': self.cuda_diagnostic.recommendations,
'fix_commands': self.cuda_diagnostic.fix_commands
}

if self.performance_history:    latest_performance = self.performance_history[-1]['metrics']
report['performance'] = {
'gpu_available': latest_performance.gpu_backend_available,
'speedup_ratio': latest_performance.speedup_ratio,
'memory_efficiency': latest_performance.memory_efficiency,
'total_time': latest_performance.total_time,
'transfer_time': latest_performance.data_transfer_time,
'computation_time': latest_performance.computation_time
}

return report

def save_reportself, filename: str = None -> str:
"""
保存優化報告到文件

Args:
filename: 文件名，如果為None則自動生成

Returns:
保存的文件路徑
"""
if not filename:    timestamp = int(time.time())
filename = f"gpu_optimization_report_{timestamp}.json"

report = self.get_optimization_report()

try:    with open(filename, 'w', encoding='utf-8') as f:
json.dumpreport, f, indent=2, ensure_ascii=False, default=str

logger.infof"GPU optimization report saved to: {filename}"
return filename

except Exception as e:
logger.errorf"Failed to save report: {e}"
return ""

def optimize_gpu_performanceauto_fix: bool = True -> GPUPerformanceOptimizer:
"""
創建並配置GPU性能優化器

Args:
auto_fix: 是否自動修復問題

Returns:
配置好的GPU性能優化器
"""
return GPUPerformanceOptimizerauto_fix=auto_fix

def run_gpu_diagnostics() -> Dict[str, Any]:
"""
運行GPU診斷並返回結果

Returns:
診斷結果報告
"""
optimizer = GPUPerformanceOptimizerauto_fix=False
return optimizer.get_optimization_report()

if __name__ == "__main__":

logging.basicConfig(level=logging.INFO, format='%asctimes - %levelnames - %messages')

print"=" * 60
print"GPU Performance Optimizer"
print"=" * 60

optimizer = optimize_gpu_performanceauto_fix=True

print"\nRunning performance benchmark..."
metrics = optimizer.benchmark_performancedata_size=10000

printf"\nGPU Backend Available: {metrics.gpu_backend_available}"
printf"Speedup Ratio: {metrics.speedup_ratio:.2f}x"
printf"Total Time: {metrics.total_time:.4f}s"
printf"Data Transfer Time: {metrics.data_transfer_time:.4f}s"
printf"Computation Time: {metrics.computation_time:.4f}s"
printf"Memory Efficiency: {metrics.memory_efficiency:.2%}"

report_file = optimizer.save_report()
if report_file:
printf"\nOptimization report saved to: {report_file}"

# 顯示主要問題和建議
report = optimizer.get_optimization_report()
if report['issues_found']:
print"\nIssues Found:"
for issue in report['issues_found']:
printf" ❌ {issue}"

if report['recommendations']:
print"\nRecommendations:"
for rec in report['recommendations']:
printf" 💡 {rec}"

print"\n" + "=" * 60
print"GPU Performance Optimization Complete"
print"=" * 60