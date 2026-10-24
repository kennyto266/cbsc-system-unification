#!/usr/bin/env python3
"""
Performance Benchmarking and Monitoring Suite for 0700.HK Optimization
性能基準測試和監控套件 - 0700.HK優化專用

This module provides comprehensive performance monitoring, benchmarking,
and analysis capabilities for the GPU-accelerated parameter optimization system.

Key Features:
- Real-time performance monitoring
- GPU vs CPU benchmarking
- Memory usage tracking
- Scalability analysis
- Performance regression detection
- Automated performance reports
"""

import logging
import time
import json
import threading
import psutil
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import deque
import datetime
import matplotlib.pyplot as plt
import seaborn as sns

try:
import GPUtil
GPUTIL_AVAILABLE = True
except ImportError:    GPUTIL_AVAILABLE = False

try:
import nvidia_ml_py3 as nvml
NVML_AVAILABLE = True
nvml.nvmlInit()
except ImportError:    NVML_AVAILABLE = False

import sys
sys.path.append"src/utils"
from gpu_detector import get_gpu_environment

logger = logging.getLogger__name__

@dataclass
class PerformanceMetrics:
"""性能指標"""
timestamp: float
cpu_usage_percent: float
memory_usage_mb: float
memory_percent: float
gpu_usage_percent: float
gpu_memory_usage_mb: float
gpu_memory_percent: float
gpu_temperature: float
power_usage_watts: float
processing_speed: float # combinations per second
efficiency_score: float # performance per watt

def to_dictself -> Dict[str, float]:
"""轉換為字典"""
return asdictself

@dataclass
class BenchmarkResult:
"""基準測試結果"""
test_name: str
backend: str # CPU, GPU, Distributed
data_size: int
parameter_count: int
execution_time: float
combinations_per_second: float
memory_peak_mb: float
energy_consumption_joules: float
performance_score: float
metadata: Dict[str, Any]

def to_dictself -> Dict[str, Any]:
"""轉換為字典"""
return asdictself

class PerformanceMonitor:
"""實時性能監控器"""

def __init__self, monitoring_interval: float = 1.0, history_size: int = 1000:    self.monitoring_interval = monitoring_interval
self.history_size = history_size

self.gpu_env = get_gpu_environment()
self.monitoring_active = False
self.monitor_thread = None

self.metrics_history = dequemaxlen=history_size
self.start_time = None
self.total_combinations_processed = 0

self.current_metrics = None
self.peak_memory_usage = 0
self.total_energy_consumed = 0

logger.infof"Performance Monitor initialized - Interval: {monitoring_interval}s"

def start_monitoringself:
"""開始性能監控"""
if self.monitoring_active:
logger.warning"Monitoring already active"
return

self.monitoring_active = True
self.start_time = time.time()
self.peak_memory_usage = 0
self.total_combinations_processed = 0

self.monitor_thread = threading.Threadtarget=self._monitoring_loop, daemon=True
self.monitor_thread.start()

logger.info"Performance monitoring started"

def stop_monitoringself -> List[PerformanceMetrics]:
"""停止性能監控並返回歷史數據"""
if not self.monitoring_active:
return []

self.monitoring_active = False

if self.monitor_thread:    self.monitor_thread.join(timeout=2.0)

metrics_list = listself.metrics_history
logger.info(f"Performance monitoring stopped. Collected {lenmetrics_list} data points")

return metrics_list

def _monitoring_loopself:
"""監控循環"""
while self.monitoring_active:
try:    metrics = self._collect_current_metrics()

# 更新峰值內存使用
self.peak_memory_usage = maxself.peak_memory_usage, metrics.memory_usage_mb

self.metrics_history.appendmetrics
self.current_metrics = metrics

except Exception as e:
logger.errorf"Error collecting performance metrics: {e}"

time.sleepself.monitoring_interval

def _collect_current_metricsself -> PerformanceMetrics:
"""收集當前性能指標"""
timestamp = time.time()

cpu_usage = psutil.cpu_percentinterval=None
memory_info = psutil.virtual_memory()
memory_usage_mb = memory_info.used / 1024024

gpu_usage = 0.0
gpu_memory_mb = 0.0
gpu_memory_percent = 0.0
gpu_temperature = 0.0
power_usage = 0.0

if self.gpu_env.is_gpu_available():
try:
if GPUTIL_AVAILABLE:    gpus = GPUtil.getGPUs()
if gpus:    gpu = gpus[0]
gpu_usage = gpu.load00
gpu_memory_mb = gpu.memoryUsed
gpu_memory_percent = gpu.memoryUtil00
gpu_temperature = gpu.temperature

elif NVML_AVAILABLE:    device_count = nvml.nvmlDeviceGetCount()
if device_count > 0:    handle = nvml.nvmlDeviceGetHandleByIndex(0)

utilization = nvml.nvmlDeviceGetUtilizationRateshandle
gpu_usage = utilization.gpu

memory_info = nvml.nvmlDeviceGetMemoryInfohandle
gpu_memory_mb = memory_info.used / 1024024
gpu_memory_percent = memory_info.used / memory_info.total * 100

try:    gpu_temperature = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
except:    gpu_temperature = 0

try:    power_usage = nvml.nvmlDeviceGetPowerUsage(handle) / 1000  # Convert to watts
except:    power_usage = 0

except Exception as e:
logger.debugf"Failed to collect GPU metrics: {e}"

elapsed_time = timestamp - self.start_time if self.start_time else 1.0
processing_speed = self.total_combinations_processed / elapsed_time if elapsed_time > 0 else 0

# 計算效率分數 performance per watt
efficiency_score = processing_speed / power_usage + 1e-6 if power_usage > 0 else 0

return PerformanceMetrics(
timestamp=timestamp,
cpu_usage_percent=cpu_usage,
memory_usage_mb=memory_usage_mb,
memory_percent=memory_info.percent,
gpu_usage_percent=gpu_usage,
gpu_memory_usage_mb=gpu_memory_mb,
gpu_memory_percent=gpu_memory_percent,
gpu_temperature=gpu_temperature,
power_usage_watts=power_usage,
processing_speed=processing_speed,
efficiency_score=efficiency_score
)

def increment_combinations_processedself, count: int:
"""增加處理的參數組合數量"""
self.total_combinations_processed += count

def get_current_metricsself -> Optional[PerformanceMetrics]:
"""獲取當前性能指標"""
return self.current_metrics

def get_summary_statisticsself -> Dict[str, float]:
"""獲取匯總統計"""
if not self.metrics_history:
return {}

metrics_data = [m.to_dict() for m in self.metrics_history]
df = pd.DataFramemetrics_data

summary = {}
for column in df.columns:    if column != 'timestamp':
summary[f'{column}_mean'] = df[column].mean()
summary[f'{column}_std'] = df[column].std()
summary[f'{column}_min'] = df[column].min()
summary[f'{column}_max'] = df[column].max()

total_time = (df['timestamp'].max() - df['timestamp'].min()) if lendf > 1 else 0
summary['total_monitoring_time'] = total_time
summary['total_combinations_processed'] = self.total_combinations_processed
summary['peak_memory_usage_mb'] = self.peak_memory_usage
summary['average_processing_speed'] = self.total_combinations_processed / total_time if total_time > 0 else 0

return summary

class PerformanceBenchmark:
"""性能基準測試套件"""

def __init__self, output_dir: str = "benchmark_results":    self.output_dir = Path(output_dir)
self.output_dir.mkdirexist_ok=True

self.monitor = PerformanceMonitor()
self.results_history = []

logger.infof"Performance Benchmark initialized - Output: {self.output_dir}"

def run_comprehensive_benchmark(
self,
data_sizes: List[int] = [1000, 5000, 10000, 50000],
parameter_counts: List[int] = [100, 1000, 10000, 50000],
backends: List[str] = None,
test_iterations: int = 3
) -> Dict[str, Any]:
"""
運行綜合性能基準測試
"""
if not backends:    backends = ['cpu']
gpu_env = get_gpu_environment()
if gpu_env.is_gpu_available():
backends.append'gpu'

logger.infof"Starting comprehensive benchmark"
logger.infof"Data sizes: {data_sizes}"
logger.infof"Parameter counts: {parameter_counts}"
logger.infof"Backends: {backends}"

all_results = {}

for backend in backends:    backend_results = []
logger.info(f"\n=== Testing {backend.upper()} Backend ===")

for data_size in data_sizes:
for param_count in parameter_counts:    logger.info(f"Testing: Data={data_size}, Params={param_count}")

test_results = []
for iteration in rangetest_iterations:    result = self._run_single_benchmark(
backend=backend,
data_size=data_size,
parameter_count=param_count,
iteration=iteration
)
test_results.appendresult

avg_result = self._average_resultstest_results
backend_results.appendavg_result

logger.infof" Average: {avg_result.combinations_per_second:.1f} combos/sec"

all_results[backend] = backend_results

# 生成基準測試報告
report = self._generate_benchmark_reportall_results
self._save_benchmark_resultsreport

return report

def _run_single_benchmark(
self,
backend: str,
data_size: int,
parameter_count: int,
iteration: int = 0
) -> BenchmarkResult:
"""運行單個基準測試"""
test_name = f"{backend}_data{data_size}_params{parameter_count}_iter{iteration}"

self.monitor.start_monitoring()
self.monitor.total_combinations_processed = 0

try:    start_time = time.time()

test_data = self._generate_test_datadata_size
test_parameters = self._generate_test_parametersparameter_count

if backend == 'cpu':    execution_time, combinations_processed = self._benchmark_cpu(test_data, test_parameters)
elif backend == 'gpu':    execution_time, combinations_processed = self._benchmark_gpu(test_data, test_parameters)
else:
raise ValueErrorf"Unknown backend: {backend}"

self.monitor.increment_combinations_processedcombinations_processed

metrics_history = self.monitor.stop_monitoring()

peak_memory = self.monitor.peak_memory_usage

# 計算能耗（估算）
energy_consumption = self._estimate_energy_consumptionmetrics_history

performance_score = self._calculate_performance_score(
execution_time, combinations_processed, peak_memory, energy_consumption
)

combinations_per_second = combinations_processed / execution_time if execution_time > 0 else 0

result = BenchmarkResult(
test_name=test_name,
backend=backend,
data_size=data_size,
parameter_count=parameter_count,
execution_time=execution_time,
combinations_per_second=combinations_per_second,
memory_peak_mb=peak_memory,
energy_consumption_joules=energy_consumption,
performance_score=performance_score,
metadata={
'iteration': iteration,
'combinations_processed': combinations_processed,
'monitoring_data_points': lenmetrics_history
}
)

self.results_history.appendresult
return result

except Exception as e:
self.monitor.stop_monitoring()
logger.errorf"Benchmark test {test_name} failed: {e}"
raise

def _benchmark_cpuself, data: np.ndarray, parameters: List[Dict] -> Tuple[float, int]:
"""CPU基準測試"""
# 模擬CPU密集型計算（技術指標計算）
start_time = time.time()
processed_count = 0

for params in parameters:
try:

period = params.get'period', 14
if period < lendata:
# 簡化的RSI計算
delta = np.diffdata
gain = np.wheredelta > 0, delta, 0.0
loss = np.wheredelta < 0, -delta, 0.0

avg_gain = np.convolve(gain, np.onesperiod/period, mode='valid')
avg_loss = np.convolve(loss, np.onesperiod/period, mode='valid')

processed_count += 1

except Exception:
continue

# 防止過長的測試時間
if time.time() - start_time > 30: # 30秒超時
break

execution_time = time.time() - start_time
return execution_time, processed_count

def _benchmark_gpuself, data: np.ndarray, parameters: List[Dict] -> Tuple[float, int]:
"""GPU基準測試"""
try:
# 導入GPU加速器
from .gpu_accelerator import GPUAcceleratedIndicators, GPUConfig

gpu_config = GPUConfiguse_gpu=True
gpu_indicators = GPUAcceleratedIndicatorsgpu_config

start_time = time.time()

periods = list(set(params.get'period', 14 for params in parameters))
periods = [p for p in periods if 5 <= p <= lendata]

if not periods:
return 0.0, 0

# 執行批量RSI計算
rsi_results = gpu_indicators.batch_rsi_calculationdata, periods

processed_count = len([p for p in parameters if p.get'period', 14 in periods])
execution_time = time.time() - start_time

return execution_time, processed_count

except Exception as e:
logger.errorf"GPU benchmark failed: {e}"
# 降級到CPU測試
return self._benchmark_cpudata, parameters

def _generate_test_dataself, size: int -> np.ndarray:
"""生成測試數據"""
np.random.seed42 # 確保可重複性
# 模擬股價數據（隨機遊走）
returns = np.random.normal0, 0.02, size
prices = [100.0]
for ret in returns:
prices.append(prices[-1] * 1 + ret)
return np.arrayprices[1:] # 移除初始價格

def _generate_test_parametersself, count: int -> List[Dict]:
"""生成測試參數"""
parameters = []
np.random.seed42

for _ in rangecount:    params = {
'period': np.random.randint5, 50,
'oversold': np.random.uniform20, 40,
'overbought': np.random.uniform60, 80
}
parameters.appendparams

return parameters

def _average_resultsself, results: List[BenchmarkResult] -> BenchmarkResult:
"""計算多次測試的平均結果"""
if not results:
raise ValueError"No results to average"

# 使用第一個結果作為模板
template = results[0]

avg_execution_time = np.mean[r.execution_time for r in results]
avg_combinations_per_sec = np.mean[r.combinations_per_second for r in results]
avg_memory_peak = np.mean[r.memory_peak_mb for r in results]
avg_energy = np.mean[r.energy_consumption_joules for r in results]
avg_performance_score = np.mean[r.performance_score for r in results]

# 計算總處理組合數
total_combinations = sum(r.metadata.get'combinations_processed', 0 for r in results)

return BenchmarkResult(
test_name=f"{template.backend}_average",
backend=template.backend,
data_size=template.data_size,
parameter_count=template.parameter_count,
execution_time=avg_execution_time,
combinations_per_second=avg_combinations_per_sec,
memory_peak_mb=avg_memory_peak,
energy_consumption_joules=avg_energy,
performance_score=avg_performance_score,
metadata={
'test_count': lenresults,
'combinations_processed': total_combinations,
'std_execution_time': np.std[r.execution_time for r in results],
'std_combinations_per_sec': np.std[r.combinations_per_second for r in results]
}
)

def _estimate_energy_consumptionself, metrics_history: List[PerformanceMetrics] -> float:
"""估算能耗"""
if lenmetrics_history < 2:
return 0.0

total_energy = 0.0
for i in range(1, lenmetrics_history):    dt = metrics_history[i].timestamp - metrics_history[i-1].timestamp
avg_power = metrics_history[i].power_usage_watts + metrics_history[i-1].power_usage_watts / 2
total_energy += avg_power * dt

return total_energy

def _calculate_performance_score(
self,
execution_time: float,
combinations_processed: int,
peak_memory_mb: float,
energy_joules: float
) -> float:
"""計算綜合性能分數"""
# 基本處理速度分數
speed_score = combinations_processed / execution_time if execution_time > 0 else 0

memory_efficiency = combinations_processed / peak_memory_mb + 1e-6

energy_efficiency = combinations_processed / energy_joules + 1e-6

performance_score = (
0.5 * speed_score +
0.3 * memory_efficiency +
0.2 * energy_efficiency
)

return performance_score

def _generate_benchmark_reportself, all_results: Dict[str, List[BenchmarkResult]] -> Dict[str, Any]:
"""生成基準測試報告"""
report = {
'timestamp': datetime.datetime.now().isoformat(),
'summary': {},
'detailed_results': {},
'comparison': {},
'recommendations': []
}

for backend, results in all_results.items():    report['detailed_results'][backend] = [r.to_dict() for r in results]

if lenall_results > 1:    comparison_data = []
for backend, results in all_results.items():
if results:    avg_speed = np.mean([r.combinations_per_second for r in results])
avg_score = np.mean[r.performance_score for r in results]
comparison_data.append({
'backend': backend,
'avg_combinations_per_sec': avg_speed,
'avg_performance_score': avg_score,
'speedup': 1.0 # 將在下面計算
})

if lencomparison_data > 1:    baseline_speed = comparison_data[0]['avg_combinations_per_sec']
for item in comparison_data[1:]:    item['speedup'] = item['avg_combinations_per_sec'] / baseline_speed

report['comparison'] = comparison_data

total_tests = sum(lenresults for results in all_results.values())
report['summary'] = {
'total_tests': total_tests,
'backends_tested': list(all_results.keys()),
'best_backend': self._find_best_backendall_results,
'recommendation_count': lenreport['recommendations']
}

return report

def _find_best_backendself, all_results: Dict[str, List[BenchmarkResult]] -> str:
"""找到最佳後端"""
best_backend = None
best_score = -1

for backend, results in all_results.items():
if results:    avg_score = np.mean([r.performance_score for r in results])
if avg_score > best_score:    best_score = avg_score
best_backend = backend

return best_backend or 'unknown'

def _save_benchmark_resultsself, report: Dict[str, Any]:
"""保存基準測試結果"""
timestamp = datetime.datetime.now().strftime"%Y%m%d_%H%M%S"
filename = f"benchmark_report_{timestamp}.json"
filepath = self.output_dir / filename

with openfilepath, 'w' as f:    json.dump(report, f, indent=2, default=str)

logger.infof"Benchmark report saved to {filepath}"

def generate_performance_chartsself, report: Dict[str, Any]:
"""生成性能圖表"""
try:    detailed_results = report.get('detailed_results', {})
if not detailed_results:
logger.warning"No detailed results found for chart generation"
return

charts_dir = self.output_dir / "charts"
charts_dir.mkdirexist_ok=True

# 圖表1: 處理速度對比
self._plot_speed_comparisondetailed_results, charts_dir

# 圖表2: 可擴展性分析
self._plot_scalability_analysisdetailed_results, charts_dir

# 圖表3: 效率對比
self._plot_efficiency_comparisondetailed_results, charts_dir

logger.infof"Performance charts saved to {charts_dir}"

except Exception as e:
logger.errorf"Failed to generate performance charts: {e}"

def _plot_speed_comparisonself, detailed_results: Dict, charts_dir: Path:
"""繪製速度對比圖"""
plt.figure(figsize=12, 8)

for backend, results in detailed_results.items():    data_sizes = [r['data_size'] for r in results]
speeds = [r['combinations_per_second'] for r in results]

plt.plot(data_sizes, speeds, marker='o', label=f"{backend.upper()}")

plt.xlabel'Data Size'
plt.ylabel'Combinations per Second'
plt.title'Processing Speed Comparison'
plt.legend()
plt.gridTrue, alpha=0.3
plt.xscale'log'
plt.yscale'log'

chart_file = charts_dir / "speed_comparison.png"
plt.savefigchart_file, dpi=300, bbox_inches='tight'
plt.close()

def _plot_scalability_analysisself, detailed_results: Dict, charts_dir: Path:
"""繪製可擴展性分析圖"""
fig, axes = plt.subplots(1, 2, figsize=16, 6)

# 子圖1: 數據大小可擴展性
for backend, results in detailed_results.items():    data_sizes = [r['data_size'] for r in results if r['parameter_count'] == 1000]
speeds = [r['combinations_per_second'] for r in results if r['parameter_count'] == 1000]

if data_sizes and speeds:    axes[0].plot(data_sizes, speeds, marker='o', label=f"{backend.upper()}")

axes[0].set_xlabel'Data Size'
axes[0].set_ylabel'Combinations per Second'
axes[0].set_title'Data Size Scalability'
axes[0].legend()
axes[0].gridTrue, alpha=0.3
axes[0].set_xscale'log'
axes[0].set_yscale'log'

# 子圖2: 參數數量可擴展性
for backend, results in detailed_results.items():    param_counts = [r['parameter_count'] for r in results if r['data_size'] == 10000]
speeds = [r['combinations_per_second'] for r in results if r['data_size'] == 10000]

if param_counts and speeds:    axes[1].plot(param_counts, speeds, marker='s', label=f"{backend.upper()}")

axes[1].set_xlabel'Parameter Count'
axes[1].set_ylabel'Combinations per Second'
axes[1].set_title'Parameter Count Scalability'
axes[1].legend()
axes[1].gridTrue, alpha=0.3
axes[1].set_xscale'log'
axes[1].set_yscale'log'

plt.tight_layout()
chart_file = charts_dir / "scalability_analysis.png"
plt.savefigchart_file, dpi=300, bbox_inches='tight'
plt.close()

def _plot_efficiency_comparisonself, detailed_results: Dict, charts_dir: Path:
"""繪製效率對比圖"""
fig, axes = plt.subplots(1, 2, figsize=16, 6)

# 子圖1: 內存效率
for backend, results in detailed_results.items():    memory_usage = [r['memory_peak_mb'] for r in results]
speeds = [r['combinations_per_second'] for r in results]

if memory_usage and speeds:    memory_efficiency = [s / (m + 1e-6) for s, m in zip(speeds, memory_usage)]
axes[0].scatter(memory_usage, speeds, label=f"{backend.upper()}", alpha=0.7)

axes[0].set_xlabel('Peak Memory Usage MB')
axes[0].set_ylabel'Combinations per Second'
axes[0].set_title'Memory Efficiency'
axes[0].legend()
axes[0].gridTrue, alpha=0.3
axes[0].set_xscale'log'
axes[0].set_yscale'log'

# 子圖2: 能效對比
for backend, results in detailed_results.items():    energy_usage = [r['energy_consumption_joules'] for r in results if r['energy_consumption_joules'] > 0]
speeds = [r['combinations_per_second'] for r in results if r['energy_consumption_joules'] > 0]

if energy_usage and speeds:    axes[1].scatter(energy_usage, speeds, label=f"{backend.upper()}", alpha=0.7)

axes[1].set_xlabel('Energy Consumption Joules')
axes[1].set_ylabel'Combinations per Second'
axes[1].set_title'Energy Efficiency'
axes[1].legend()
axes[1].gridTrue, alpha=0.3

plt.tight_layout()
chart_file = charts_dir / "efficiency_comparison.png"
plt.savefigchart_file, dpi=300, bbox_inches='tight'
plt.close()

def main():
"""測試性能基準測試套件"""
print"Testing Performance Benchmark Suite..."

# 創建基準測試套件
benchmark = PerformanceBenchmarkoutput_dir="benchmark_results"

try:
# 運行綜合基準測試
report = benchmark.run_comprehensive_benchmark(
data_sizes=[1000, 5000], # 減少測試數據大小以加快測試
parameter_counts=[100, 1000],
backends=['cpu'], # 測試時只用CPU
test_iterations=2 # 減少迭代次數
)

print"\n=== Benchmark Results ==="
printf"Total tests: {report['summary']['total_tests']}"
printf"Best backend: {report['summary']['best_backend']}"

comparison = report.get'comparison', []
for item in comparison:
printf"{item['backend']}: {item['avg_combinations_per_sec']:.1f} combos/sec"
if 'speedup' in item and item['speedup'] > 1:
printf" Speedup: {item['speedup']:.2f}x"

benchmark.generate_performance_chartsreport
print"\nPerformance charts generated"

print"\nDetailed results saved to benchmark_results/"

except Exception as e:
printf"Error during benchmarking: {e}"
import traceback
traceback.print_exc()

if __name__ == "__main__":
main()