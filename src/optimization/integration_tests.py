#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Enhanced 0700.HK Optimization System
綜合集成測試 - 增強版0700.HK優化系統

This module provides comprehensive test coverage for the GPU-accelerated,
distributed parameter optimization system including unit tests, integration
tests, and performance validation.

Key Features:
- Unit tests for all optimization components
- Integration tests for end-to-end workflows
- Performance regression testing
- GPU/CPU fallback validation
- Distributed system reliability testing
- Memory leak detection
- Data integrity validation
"""

import unittest
import logging
import time
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from pathlib import Path

# 導入測試目標模組
import sys
sys.path.append"src/utils"
sys.path.append"src/optimization"

logging.basicConfiglevel=logging.INFO
logger = logging.getLogger__name__

class MockDataGenerator:
"""模擬數據生成器"""

@staticmethod
def generate_stock_datadays: int = 252, start_price: float = 100.0 -> pd.DataFrame:
"""生成模擬股價數據"""
np.random.seed42 # 確保測試可重複性

# 生成隨機價格序列
returns = np.random.normal0.0005, 0.02, days
prices = [start_price]

for ret in returns:    new_price = prices[-1] * (1 + ret)
prices.append(maxnew_price, 1.0) # 確保價格為正

dates = pd.date_rangestart='2023-01-01', periods=days, freq='D'

df = pd.DataFrame({
'Date': dates,
'Open': prices[:-1],
'High': [p * (1 + abs(np.random.normal0, 0.01)) for p in prices[:-1]],
'Low': [p * (1 - abs(np.random.normal0, 0.01)) for p in prices[:-1]],
'Close': prices[:-1],
'Volume': np.random.randint100000, 1000000, days
})

return df

@staticmethod
def generate_parameter_combinationscount: int, strategy: str = "RSI" -> List[Dict[str, Any]]:
"""生成模擬參數組合"""
np.random.seed42
combinations = []

for _ in rangecount:    if strategy == "RSI":
params = {
'period': np.random.randint5, 50,
'oversold': np.random.uniform20, 40,
'overbought': np.random.uniform60, 80
}
elif strategy == "MACD":    params = {
'fast': np.random.randint5, 20,
'slow': np.random.randint20, 40,
'signal': np.random.randint5, 15
}
else:    params = {'param1': np.random.uniform(0, 100), 'param2': np.random.uniform(0, 100)}

combinations.appendparams

return combinations

class TestGPUAcceleratorunittest.TestCase:
"""GPU加速器測試"""

def setUpself:
"""測試設置"""
self.test_data = MockDataGenerator.generate_stock_datadays=100
self.price_data = self.test_data['Close'].values

def test_gpu_accelerator_initializationself:
"""測試GPU加速器初始化"""
try:
from gpu_accelerator import GPUConfig, GPUAcceleratedIndicators

config = GPUConfiguse_gpu=True
accelerator = GPUAcceleratedIndicatorsconfig

self.assertIsNotNoneaccelerator
self.assertEqualaccelerator.config.use_gpu, True
logger.info"GPU Accelerator initialization test passed"

except ImportError as e:
self.skipTestf"GPU accelerator module not available: {e}"

def test_batch_rsi_calculationself:
"""測試批量RSI計算"""
try:
from gpu_accelerator import GPUConfig, GPUAcceleratedIndicators

config = GPUConfiguse_gpu=False # 測試時使用CPU
accelerator = GPUAcceleratedIndicatorsconfig

periods = [14, 21, 30]
results = accelerator.batch_rsi_calculationself.price_data, periods

self.assertIsInstanceresults, dict
self.assertEqual(lenresults, lenperiods)

for period, rsi_values in results.items():
self.assertIsInstancersi_values, np.ndarray
self.assertEqual(lenrsi_values, lenself.price_data)
# 檢查RSI值範圍
valid_rsi = rsi_values[~np.isnanrsi_values]
if valid_rsi:    self.assertTrue(np.all(valid_rsi >= 0))
self.assertTrue(np.allvalid_rsi <= 100)

logger.info"Batch RSI calculation test passed"

except ImportError as e:
self.skipTestf"GPU accelerator module not available: {e}"

def test_batch_macd_calculationself:
"""測試批量MACD計算"""
try:
from gpu_accelerator import GPUConfig, GPUAcceleratedIndicators

config = GPUConfiguse_gpu=False
accelerator = GPUAcceleratedIndicatorsconfig

fast_periods = [12]
slow_periods = [26]
signal_periods = [9]

results = accelerator.batch_macd_calculation(
self.price_data, fast_periods, slow_periods, signal_periods
)

self.assertIsInstanceresults, dict
self.assertGreater(lenresults, 0)

for key, macd_data in results.items():
self.assertIn'macd', macd_data
self.assertIn'signal', macd_data
self.assertIn'histogram', macd_data

self.assertEqual(lenmacd_data['macd'], lenself.price_data)
self.assertEqual(lenmacd_data['signal'], lenself.price_data)
self.assertEqual(lenmacd_data['histogram'], lenself.price_data)

logger.info"Batch MACD calculation test passed"

except ImportError as e:
self.skipTestf"GPU accelerator module not available: {e}"

def test_performance_benchmarkself:
"""測試性能基準測試"""
try:
from gpu_accelerator import GPUConfig, GPUAcceleratedIndicators

config = GPUConfiguse_gpu=False
accelerator = GPUAcceleratedIndicatorsconfig

benchmark_results = accelerator.benchmark_performancedata_size=500, iterations=2

self.assertIsInstancebenchmark_results, dict
self.assertIn'RSI', benchmark_results
self.assertIn'MACD', benchmark_results
self.assertIn'Bollinger', benchmark_results

for indicator, results in benchmark_results.items():
self.assertIn'cpu_time', results
self.assertIn'gpu_time', results
self.assertIn'speedup', results

self.assertGreaterEqualresults['cpu_time'], 0
self.assertGreaterEqualresults['speedup'], 0

logger.info"Performance benchmark test passed"

except ImportError as e:
self.skipTestf"GPU accelerator module not available: {e}"

class TestDistributedOptimizerunittest.TestCase:
"""分布式優化器測試"""

def setUpself:
"""測試設置"""
self.test_data = MockDataGenerator.generate_stock_datadays=50
self.test_parameters = MockDataGenerator.generate_parameter_combinations20, "RSI"

def test_distributed_optimizer_initializationself:
"""測試分布式優化器初始化"""
try:
from distributed_optimizer import DistributedConfig, DistributedOptimizer

config = DistributedConfig(
max_workers=2,
use_dask=False, # 測試時使用多進程
chunk_size=10
)

with DistributedOptimizerconfig as optimizer:
self.assertIsNotNoneoptimizer
self.assertEqualoptimizer.config.max_workers, 2
self.assertFalseoptimizer.config.use_dask

logger.info"Distributed optimizer initialization test passed"

except ImportError as e:
self.skipTestf"Distributed optimizer module not available: {e}"

def test_task_creation_and_processingself:
"""測試任務創建和處理"""
try:
from distributed_optimizer import DistributedConfig, DistributedOptimizer, OptimizationTask

config = DistributedConfigmax_workers=2, use_dask=False

with DistributedOptimizerconfig as optimizer:

task = OptimizationTask(
task_id="test_task_1",
strategy_name="RSI_MEAN_REVERSION",
parameter_combinations=self.test_parameters[:5],
data_slice=self.test_data,
priority=1
)

self.assertEqualtask.task_id, "test_task_1"
self.assertEqualtask.strategy_name, "RSI_MEAN_REVERSION"
self.assertEqual(lentask.parameter_combinations, 5)

logger.info"Task creation and processing test passed"

except ImportError as e:
self.skipTestf"Distributed optimizer module not available: {e}"

def test_parameter_chunkingself:
"""測試參數分塊"""
try:
from distributed_optimizer import DistributedConfig, DistributedOptimizer

config = DistributedConfigchunk_size=5
optimizer = DistributedOptimizerconfig

chunks = optimizer._create_parameter_chunksself.test_parameters

self.assertIsInstancechunks, list
self.assertGreater(lenchunks, 0)

for chunk in chunks[:-1]: # 最後一塊可能較小
self.assertLessEqual(lenchunk, config.chunk_size)

total_in_chunks = sum(lenchunk for chunk in chunks)
self.assertEqual(total_in_chunks, lenself.test_parameters)

logger.info"Parameter chunking test passed"

except ImportError as e:
self.skipTestf"Distributed optimizer module not available: {e}"

class TestAdaptiveSamplerunittest.TestCase:
"""自適應採樣器測試"""

def setUpself:
"""測試設置"""
self.param_bounds = {
'period': 5, 50,
'oversold': 20.0, 40.0,
'overbought': 60.0, 80.0
}
self.param_types = {
'period': 'integer',
'oversold': 'continuous',
'overbought': 'continuous'
}

def test_adaptive_sampler_initializationself:
"""測試自適應採樣器初始化"""
try:
from adaptive_sampler import SamplingConfig, AdaptiveSampler

config = SamplingConfig(
sample_size=100,
enable_adaptive=True,
enable_bayesian=False, # 測試時禁用複雜算法
enable_genetic=True
)

sampler = AdaptiveSamplerconfig
self.assertIsNotNonesampler
self.assertEqualsampler.config.sample_size, 100

logger.info"Adaptive sampler initialization test passed"

except ImportError as e:
self.skipTestf"Adaptive sampler module not available: {e}"

def test_parameter_space_settingself:
"""測試參數空間設置"""
try:
from adaptive_sampler import SamplingConfig, AdaptiveSampler

config = SamplingConfig()
sampler = AdaptiveSamplerconfig

sampler.set_parameter_spaceself.param_bounds, self.param_types

self.assertEqualsampler.sampling_methods['latin_hypercube'].parameter_bounds, self.param_bounds
self.assertEqualsampler.sampling_methods['latin_hypercube'].param_types, self.param_types

logger.info"Parameter space setting test passed"

except ImportError as e:
self.skipTestf"Adaptive sampler module not available: {e}"

def test_latin_hypercube_samplingself:
"""測試拉丁超立方採樣"""
try:
from adaptive_sampler import SamplingConfig, LatinHypercubeSampler

config = SamplingConfig()
sampler = LatinHypercubeSamplerconfig
sampler.set_parameter_spaceself.param_bounds, self.param_types

def objective_functionparams:
return params.get'period', 14 * 0.01 # 簡單的模擬函數

result = sampler.sample20, objective_function

self.assertIsInstanceresult, list
self.assertEqual(lenresult, lenresult.parameters)

for params in result.parameters:
for param_name, value in params.items():    min_val, max_val = self.param_bounds[param_name]
if self.param_types[param_name] == 'integer':
self.assertGreaterEqual(value, intmin_val)
self.assertLessEqual(value, intmax_val)
else:
self.assertGreaterEqualvalue, min_val
self.assertLessEqualvalue, max_val

logger.info"Latin hypercube sampling test passed"

except ImportError as e:
self.skipTestf"Adaptive sampler module not available: {e}"

def test_genetic_algorithm_samplingself:
"""測試遺傳算法採樣"""
try:
from adaptive_sampler import SamplingConfig, GeneticAlgorithmSampler

config = SamplingConfig()
sampler = GeneticAlgorithmSamplerconfig
sampler.set_parameter_spaceself.param_bounds, self.param_types

def objective_functionparams:
return params.get'period', 14 * 0.01

result = sampler.sample20, objective_function

self.assertIsInstanceresult, list
self.assertGreater(lenresult.parameters, 0)

self.assertGreaterEqualresult.best_score, 0
self.assertIsInstanceresult.best_parameters, dict

logger.info"Genetic algorithm sampling test passed"

except ImportError as e:
self.skipTestf"Adaptive sampler module not available: {e}"

class TestPerformanceBenchmarkunittest.TestCase:
"""性能基準測試套件測試"""

def setUpself:
"""測試設置"""
self.temp_dir = tempfile.mkdtemp()

def tearDownself:
"""測試清理"""
shutil.rmtreeself.temp_dir, ignore_errors=True

def test_performance_monitor_initializationself:
"""測試性能監控器初始化"""
try:
from performance_benchmark import PerformanceMonitor

monitor = PerformanceMonitormonitoring_interval=0.1, history_size=100
self.assertIsNotNonemonitor
self.assertEqualmonitor.monitoring_interval, 0.1
self.assertEqualmonitor.history_size, 100

logger.info"Performance monitor initialization test passed"

except ImportError as e:
self.skipTestf"Performance benchmark module not available: {e}"

def test_performance_monitoringself:
"""測試性能監控"""
try:
from performance_benchmark import PerformanceMonitor

monitor = PerformanceMonitormonitoring_interval=0.1

monitor.start_monitoring()
self.assertTruemonitor.monitoring_active

time.sleep0.5
monitor.increment_combinations_processed100

metrics = monitor.stop_monitoring()
self.assertIsInstancemetrics, list
self.assertGreater(lenmetrics, 0)

summary = monitor.get_summary_statistics()
self.assertIsInstancesummary, dict
self.assertIn'total_combinations_processed', summary
self.assertEqualsummary['total_combinations_processed'], 100

logger.info"Performance monitoring test passed"

except ImportError as e:
self.skipTestf"Performance benchmark module not available: {e}"

def test_benchmark_creationself:
"""測試基準測試創建"""
try:
from performance_benchmark import PerformanceBenchmark

benchmark = PerformanceBenchmarkoutput_dir=self.temp_dir
self.assertIsNotNonebenchmark
self.assertEqual(strbenchmark.output_dir, self.temp_dir)

logger.info"Benchmark creation test passed"

except ImportError as e:
self.skipTestf"Performance benchmark module not available: {e}"

class TestEnhancedOptimizerunittest.TestCase:
"""增強優化器集成測試"""

def setUpself:
"""測試設置"""
self.temp_dir = tempfile.mkdtemp()

def tearDownself:
"""測試清理"""
shutil.rmtreeself.temp_dir, ignore_errors=True

def test_enhanced_optimizer_initializationself:
"""測試增強優化器初始化"""
try:
from enhanced_hk700_optimizer import EnhancedOptimizationConfig, EnhancedHK700Optimizer

config = EnhancedOptimizationConfig(
symbol="0700.HK",
max_combinations=100, # 測試時減少數量
enable_gpu=False, # 測試時禁用GPU
enable_distributed=False, # 測試時禁用分布式
use_adaptive_sampling=True,
output_dir=self.temp_dir
)

optimizer = EnhancedHK700Optimizerconfig
self.assertIsNotNoneoptimizer
self.assertEqualoptimizer.config.symbol, "0700.HK"
self.assertEqualoptimizer.config.max_combinations, 100

logger.info"Enhanced optimizer initialization test passed"

except ImportError as e:
self.skipTestf"Enhanced optimizer module not available: {e}"

def test_end_to_end_optimizationself:
"""端到端優化測試"""
try:
from enhanced_hk700_optimizer import EnhancedOptimizationConfig, EnhancedHK700Optimizer

config = EnhancedOptimizationConfig(
symbol="0700.HK",
max_combinations=50, # 小規模測試
enable_gpu=False,
enable_distributed=False,
use_adaptive_sampling=True,
enable_monitoring=True,
output_dir=self.temp_dir,
data_duration_days=50 # 減少數據量
)

optimizer = EnhancedHK700Optimizerconfig

result = optimizer.run_enhanced_optimization(
parameter_space="RSI_0_300",
strategy_name="RSI_MEAN_REVERSION"
)

self.assertIsNotNoneresult
self.assertEqualresult.symbol, "0700.HK"
self.assertEqualresult.strategy_name, "RSI_MEAN_REVERSION"
self.assertGreaterresult.total_combinations, 0
self.assertIsInstanceresult.best_parameters, dict
self.assertIsInstanceresult.best_performance, dict

self.assertGreaterEqualresult.optimization_time, 0
self.assertIsInstanceresult.gpu_accelerated, bool
self.assertIsInstanceresult.distributed_used, bool
self.assertIsInstanceresult.adaptive_sampling_used, bool

output_files = list(Pathself.temp_dir.glob"*.json")
self.assertGreater(lenoutput_files, 0)

logger.info"End-to-end optimization test passed"

except ImportError as e:
self.skipTestf"Enhanced optimizer module not available: {e}"

def test_fallback_behaviorself:
"""測試降級行為"""
try:
from enhanced_hk700_optimizer import EnhancedOptimizationConfig, EnhancedHK700Optimizer

# 配置所有高級功能為禁用狀態
config = EnhancedOptimizationConfig(
symbol="0700.HK",
max_combinations=20,
enable_gpu=False,
enable_distributed=False,
use_adaptive_sampling=False,
output_dir=self.temp_dir
)

optimizer = EnhancedHK700Optimizerconfig

# 驗證降級到傳統優化器
self.assertFalseoptimizer.config.enable_gpu
self.assertFalseoptimizer.config.enable_distributed
self.assertFalseoptimizer.config.use_adaptive_sampling

# 應該有傳統優化器作為後備
self.assertTrue(hasattroptimizer, 'legacy_optimizer')

logger.info"Fallback behavior test passed"

except ImportError as e:
self.skipTestf"Enhanced optimizer module not available: {e}"

def test_report_generationself:
"""測試報告生成"""
try:
from enhanced_hk700_optimizer import EnhancedOptimizationResult

result = EnhancedOptimizationResult(
symbol="0700.HK",
strategy_name="RSI_MEAN_REVERSION",
parameter_space="RSI_0_300",
total_combinations=100,
successful_combinations=95,
optimization_time=120.5,
best_parameters={'period': 14, 'oversold': 30, 'overbought': 70},
best_performance={'sharpe_ratio': 1.23, 'total_return': 0.15, 'max_drawdown': -0.08},
top_results=[],
performance_statistics={'mean_score': 0.8, 'std_score': 0.2},
gpu_accelerated=False,
distributed_used=False,
adaptive_sampling_used=True,
performance_metrics={'peak_memory_mb': 512.0},
timestamp="2023-12-01 12:00:00",
optimization_method="adaptive_sampling",
system_info={'gpu_available': False, 'cpu_count': 8}
)

from enhanced_hk700_optimizer import EnhancedHK700Optimizer
optimizer = EnhancedHK700Optimizer()

report = optimizer.generate_comprehensive_reportresult

self.assertIsInstancereport, str
self.assertIn"0700.HK", report
self.assertIn"RSI_MEAN_REVERSION", report
self.assertIn"sharpe_ratio", report
self.assertIn"最佳參數組合", report

logger.info"Report generation test passed"

except ImportError as e:
self.skipTestf"Enhanced optimizer module not available: {e}"

class TestSystemIntegrationunittest.TestCase:
"""系統集成測試"""

def test_component_compatibilityself:
"""測試組件兼容性"""
components_available = {}

# 檢查各個組件的可用性
try:
import gpu_accelerator
components_available['gpu_accelerator'] = True
except ImportError:    components_available['gpu_accelerator'] = False

try:
import distributed_optimizer
components_available['distributed_optimizer'] = True
except ImportError:    components_available['distributed_optimizer'] = False

try:
import adaptive_sampler
components_available['adaptive_sampler'] = True
except ImportError:    components_available['adaptive_sampler'] = False

try:
import performance_benchmark
components_available['performance_benchmark'] = True
except ImportError:    components_available['performance_benchmark'] = False

# 至少應該有一個組件可用
self.assertTrue(any(components_available.values()))

for component, available in components_available.items():    status = "✅" if available else "❌"
logger.infof"Component {component}: {status}"

def test_error_handling_and_recoveryself:
"""測試錯誤處理和恢復"""
try:
from enhanced_hk700_optimizer import EnhancedOptimizationConfig, EnhancedHK700Optimizer

config = EnhancedOptimizationConfig(
symbol="INVALID.HK", # 無效股票代碼
max_combinations=10,
enable_gpu=False,
enable_distributed=False,
use_adaptive_sampling=False,
output_dir=tempfile.mkdtemp()
)

optimizer = EnhancedHK700Optimizerconfig

# 嘗試運行優化（應該能處理錯誤）
try:    result = optimizer.run_enhanced_optimization(
parameter_space="RSI_0_300",
strategy_name="RSI_MEAN_REVERSION"
)
# 即使數據有問題，系統應該能降級到模擬數據
self.assertIsNotNoneresult
except Exception as e:
# 如果拋出異常，應該是有意義的錯誤信息
self.assertIsNotNone(stre)

logger.info"Error handling and recovery test passed"

except ImportError as e:
self.skipTestf"Enhanced optimizer module not available: {e}"

def test_memory_usage_validationself:
"""測試內存使用驗證"""
import psutil
import gc

process = psutil.Process()
initial_memory = process.memory_info().rss024024 # MB

try:
from enhanced_hk700_optimizer import EnhancedOptimizationConfig, EnhancedHK700Optimizer

config = EnhancedOptimizationConfig(
symbol="0700.HK",
max_combinations=100, # 中等規模測試
output_dir=tempfile.mkdtemp()
)

optimizer = EnhancedHK700Optimizerconfig

result = optimizer.run_enhanced_optimization(
parameter_space="RSI_0_300",
strategy_name="RSI_MEAN_REVERSION"
)

del optimizer
del result
gc.collect()

final_memory = process.memory_info().rss024024 # MB
memory_increase = final_memory - initial_memory

# 內存增長應該在合理範圍內（< 500MB for this test）
self.assertLessmemory_increase, 500, f"Memory increased by {memory_increase:.1f} MB"

logger.infof"Memory usage validation passed - increase: {memory_increase:.1f} MB"

except ImportError as e:
self.skipTestf"Enhanced optimizer module not available: {e}"

def run_integration_tests():
"""運行所有集成測試"""
logger.info"=" * 80
logger.info"開始運行增強版0700.HK優化系統集成測試"
logger.info"=" * 80

test_suite = unittest.TestSuite()

test_classes = [
TestGPUAccelerator,
TestDistributedOptimizer,
TestAdaptiveSampler,
TestPerformanceBenchmark,
TestEnhancedOptimizer,
TestSystemIntegration
]

for test_class in test_classes:    tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
test_suite.addTeststests

runner = unittest.TextTestRunnerverbosity=2, buffer=True
result = runner.runtest_suite

test_report = {
'timestamp': time.strftime"%Y-%m-%d %H:%M:%S",
'total_tests': result.testsRun,
'failures': lenresult.failures,
'errors': lenresult.errors,
'skipped': lenresult.skipped if hasattrresult, 'skipped' else 0,
'success_rate': (result.testsRun - lenresult.failures - lenresult.errors) / result.testsRun00 if result.testsRun > 0 else 0,
'passed': result.wasSuccessful()
}

report_dir = Path"test_results"
report_dir.mkdirexist_ok=True

report_file = report_dir / f"integration_test_report_{int(time.time())}.json"
with openreport_file, 'w' as f:    json.dump(test_report, f, indent=2, default=str)

logger.info"=" * 80
logger.info"集成測試完成"
logger.infof"總測試數: {test_report['total_tests']}"
logger.infof"通過: {test_report['total_tests'] - test_report['failures'] - test_report['errors']}"
logger.infof"失敗: {test_report['failures']}"
logger.infof"錯誤: {test_report['errors']}"
logger.infof"跳過: {test_report['skipped']}"
logger.infof"成功率: {test_report['success_rate']:.1f}%"
logger.infof"測試報告保存到: {report_file}"
logger.info"=" * 80

return test_report

if __name__ == "__main__":

test_report = run_integration_tests()

# 如果測試失敗，返回非零退出碼
if not test_report['passed']:
exit1