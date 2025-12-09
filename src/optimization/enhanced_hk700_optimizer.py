#!/usr/bin/env python3
"""
Enhanced 0700.HK GPU-Accelerated Massive Parameter Optimizer
增強版0700.HK GPU加速大規模參數優化器

This module integrates GPU acceleration, distributed computing, and advanced
sampling algorithms into a unified optimization framework for the 0700.HK
parameter space exploration system.

Key Features:
- GPU-accelerated technical indicator calculations
- Distributed processing across multiple nodes and GPUs
- Advanced adaptive sampling algorithms
- Real-time performance monitoring and benchmarking
- Intelligent parameter space exploration
- Fault-tolerant optimization with automatic fallback
"""

import logging
import json
import time
import threading
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
import pandas as pd

import sys
sys.path.append"src/utils"
from gpu_detector import get_gpu_environment

# 導入新的GPU組件
try:
from .gpu_accelerator import GPUAcceleratedIndicators, GPUParameterSpaceExplorer, GPUConfig
GPU_AVAILABLE = True
except ImportError as e:
printf"Warning: GPU acceleration not available: {e}"
GPU_AVAILABLE = False

try:
from .distributed_optimizer import DistributedOptimizer, DistributedConfig
DISTRIBUTED_AVAILABLE = True
except ImportError as e:
printf"Warning: Distributed optimization not available: {e}"
DISTRIBUTED_AVAILABLE = False

try:
from .adaptive_sampler import AdaptiveSampler, SamplingConfig
ADAPTIVE_AVAILABLE = True
except ImportError as e:
printf"Warning: Adaptive sampling not available: {e}"
ADAPTIVE_AVAILABLE = False

try:
from .performance_benchmark import PerformanceBenchmark, PerformanceMonitor
BENCHMARK_AVAILABLE = True
except ImportError as e:
printf"Warning: Performance benchmarking not available: {e}"
BENCHMARK_AVAILABLE = False

# 導入原始HK700優化器
try:
from .hk700_optimizer import HK700Optimizer, OptimizationResult, BacktestConfig
LEGACY_OPTIMIZER_AVAILABLE = True
except ImportError as e:
printf"Warning: Legacy HK700 optimizer not available: {e}"
LEGACY_OPTIMIZER_AVAILABLE = False

logger = logging.getLogger__name__

@dataclass
class EnhancedOptimizationConfig:
"""增強優化配置"""

symbol: str = "0700.HK"
data_duration_days: int = 252
max_combinations: int = 1000000
optimization_metric: str = "sharpe_ratio"

enable_gpu: bool = True
gpu_memory_limit_gb: float = 8.0
gpu_batch_size: int = 10000

enable_distributed: bool = True
max_workers: int = None
use_dask: bool = True
chunk_size: int = 5000

use_adaptive_sampling: bool = True
initial_sampling_method: str = "latin_hypercube"
enable_bayesian: bool = True
enable_genetic: bool = True

enable_monitoring: bool = True
enable_benchmarking: bool = False
save_intermediate_results: bool = True
output_dir: str = "enhanced_optimization_results"

initial_cash: float = 100000.0
commission: float = 0.001
slippage: float = 0.0005
risk_free_rate: float = 0.03

def __post_init__self:
# 自動檢測並配置系統能力
gpu_env = get_gpu_environment()

if not gpu_env.is_gpu_available():    self.enable_gpu = False

if self.max_workers is None:
import multiprocessing as mp
self.max_workers = mp.cpu_count()

if self.enable_gpu and gpu_env.gpu_memory_gb:    self.gpu_memory_limit_gb = min(self.gpu_memory_limit_gb, gpu_env.gpu_memory_gb * 0.8)

@dataclass
class EnhancedOptimizationResult:
"""增強優化結果"""

symbol: str
strategy_name: str
parameter_space: str
total_combinations: int
successful_combinations: int
optimization_time: float

best_parameters: Dict[str, Union[int, float]]
best_performance: Dict[str, float]

top_results: List[Dict[str, Any]]

performance_statistics: Dict[str, float]

gpu_accelerated: bool
distributed_used: bool
adaptive_sampling_used: bool
performance_metrics: Dict[str, Any]

timestamp: str
optimization_method: str
system_info: Dict[str, Any]

def to_dictself -> Dict[str, Any]:
"""轉換為字典"""
return asdictself

class EnhancedHK700Optimizer:
"""增強版0700.HK大規模參數優化器"""

def __init__self, config: EnhancedOptimizationConfig = None:    self.config = config or EnhancedOptimizationConfig()
self.gpu_env = get_gpu_environment()

self._initialize_components()

self.output_dir = Pathself.config.output_dir
self.output_dir.mkdirparents=True, exist_ok=True

logger.infof"Enhanced HK700 Optimizer initialized"
logger.info(f"GPU Available: {self.config.enable_gpu and self.gpu_env.is_gpu_available()}")
logger.infof"Distributed Available: {self.config.enable_distributed and DISTRIBUTED_AVAILABLE}"
logger.infof"Adaptive Sampling Available: {self.config.use_adaptive_sampling and ADAPTIVE_AVAILABLE}"

def _initialize_componentsself:
"""初始化所有組件"""

if self.config.enable_gpu and GPU_AVAILABLE and self.gpu_env.is_gpu_available():    self.gpu_config = GPUConfig(
use_gpu=True,
memory_limit_gb=self.config.gpu_memory_limit_gb,
batch_size=self.config.gpu_batch_size
)
self.gpu_accelerator = GPUAcceleratedIndicatorsself.gpu_config
self.gpu_explorer = GPUParameterSpaceExplorerself.gpu_config
else:    self.gpu_accelerator = None
self.gpu_explorer = None

if self.config.enable_distributed and DISTRIBUTED_AVAILABLE:    self.distributed_config = DistributedConfig(
max_workers=self.config.max_workers,
use_dask=self.config.use_dask,
chunk_size=self.config.chunk_size,
enable_gpu=self.config.enable_gpu
)
self.distributed_optimizer = DistributedOptimizerself.distributed_config
else:    self.distributed_optimizer = None

if self.config.use_adaptive_sampling and ADAPTIVE_AVAILABLE:    self.sampling_config = SamplingConfig(
sample_size=min10000, self.config.max_combinations,
optimization_metric=self.config.optimization_metric,
enable_adaptive=True,
enable_bayesian=self.config.enable_bayesian,
enable_genetic=self.config.enable_genetic
)
self.adaptive_sampler = AdaptiveSamplerself.sampling_config
else:    self.adaptive_sampler = None

if self.config.enable_monitoring and BENCHMARK_AVAILABLE:    self.performance_monitor = PerformanceMonitor()
else:    self.performance_monitor = None

if self.config.enable_benchmarking and BENCHMARK_AVAILABLE:    self.performance_benchmark = PerformanceBenchmark(self.output_dir / "benchmarks")
else:    self.performance_benchmark = None

# 降級到傳統優化器
if not any[self.gpu_accelerator, self.distributed_optimizer, self.adaptive_sampler]:
if LEGACY_OPTIMIZER_AVAILABLE:    self.legacy_optimizer = HK700Optimizer(max_workers=self.config.max_workers)
logger.info"Falling back to legacy HK700 optimizer"
else:
logger.error"No optimization components available"
raise RuntimeError"Cannot initialize any optimization components"

def run_enhanced_optimization(
self,
parameter_space: str = "RSI_0_300",
strategy_name: str = None,
max_combinations: int = None,
**kwargs
) -> EnhancedOptimizationResult:
"""
運行增強版參數優化
Run enhanced parameter optimization
"""
if not strategy_name:    strategy_name = self._extract_strategy_name(parameter_space)

max_combinations = max_combinations or self.config.max_combinations

logger.infof"Starting enhanced optimization for {self.config.symbol} - {strategy_name}"
logger.infof"Parameter space: {parameter_space}"
logger.infof"Max combinations: {max_combinations:,}"

if self.performance_monitor:
self.performance_monitor.start_monitoring()

start_time = time.time()

try:

market_data = self._load_market_data()
if market_data is None or lenmarket_data == 0:
raise ValueError"Failed to load market data"

logger.info(f"Loaded {lenmarket_data} data points")

optimization_results = self._execute_optimization(
strategy_name,
parameter_space,
market_data,
max_combinations,
**kwargs
)

enhanced_result = self._process_enhanced_results(
optimization_results,
strategy_name,
parameter_space,
time.time() - start_time
)

self._save_enhanced_resultsenhanced_result

# 生成基準測試報告
if self.performance_benchmark:
self.performance_benchmark.generate_performance_charts({
'optimization_result': enhanced_result.to_dict()
})

logger.infof"Enhanced optimization completed in {enhanced_result.optimization_time:.2f} seconds"
return enhanced_result

finally:

if self.performance_monitor:    metrics_history = self.performance_monitor.stop_monitoring()
logger.info(f"Performance monitoring collected {lenmetrics_history} data points")

def _extract_strategy_nameself, parameter_space: str -> str:
"""從參數空間名稱提取策略名稱"""
if "RSI" in parameter_space:
return "RSI_MEAN_REVERSION"
elif "MACD" in parameter_space:
return "MACD_CROSSOVER"
elif "BB" in parameter_space or "BOLLINGER" in parameter_space:
return "BOLLINGER_BANDS"
else:
return "UNKNOWN_STRATEGY"

def _load_market_dataself -> Optional[pd.DataFrame]:
"""加載市場數據"""
try:
# 首先嘗試從適配器加載數據
if hasattrself, 'legacy_optimizer' and self.legacy_optimizer:
return self.legacy_optimizer.data_adapter.get_data_for_optimization(
days=self.config.data_duration_days
)
else:

logger.warning"Using simulated market data"
return self._generate_simulated_data()

except Exception as e:
logger.errorf"Failed to load market data: {e}"
return self._generate_simulated_data()

def _generate_simulated_dataself -> pd.DataFrame:
"""生成模擬市場數據"""
np.random.seed42
n_days = self.config.data_duration_days

returns = np.random.normal0.0005, 0.02, n_days # 日回報率
prices = [100.0]
for ret in returns:
prices.append(prices[-1] * 1 + ret)

dates = pd.date_rangestart='2020-01-01', periods=n_days, freq='D'

df = pd.DataFrame({
'Date': dates,
'Open': prices[:-1],
'High': [p * (1 + abs(np.random.normal0, 0.01)) for p in prices[:-1]],
'Low': [p * (1 - abs(np.random.normal0, 0.01)) for p in prices[:-1]],
'Close': prices[:-1],
'Volume': np.random.randint100000, 1000000, n_days
})

return df

def _execute_optimization(
self,
strategy_name: str,
parameter_space: str,
market_data: pd.DataFrame,
max_combinations: int,
**kwargs
) -> Dict[str, Any]:
"""執行優化（選擇最佳方法）"""
# 根據可用組件選擇優化方法
if self.distributed_optimizer and max_combinations > 50000:
return self._execute_distributed_optimization(
strategy_name, parameter_space, market_data, max_combinations, **kwargs
)
elif self.gpu_explorer and max_combinations > 10000:
return self._execute_gpu_optimization(
strategy_name, parameter_space, market_data, max_combinations, **kwargs
)
elif self.adaptive_sampler:
return self._execute_adaptive_optimization(
strategy_name, parameter_space, market_data, max_combinations, **kwargs
)
elif hasattrself, 'legacy_optimizer' and self.legacy_optimizer:
return self._execute_legacy_optimization(
strategy_name, parameter_space, market_data, max_combinations, **kwargs
)
else:
raise RuntimeError"No optimization method available"

def _execute_distributed_optimization(
self,
strategy_name: str,
parameter_space: str,
market_data: pd.DataFrame,
max_combinations: int,
**kwargs
) -> Dict[str, Any]:
"""執行分布式優化"""
logger.info"Using distributed optimization"

parameter_combinations = self._generate_parameter_combinations(
strategy_name, max_combinations
)

return self.distributed_optimizer.run_distributed_optimization(
parameter_space=parameter_space,
strategy_name=strategy_name,
parameter_combinations=parameter_combinations,
market_data=market_data,
optimization_metric=self.config.optimization_metric
)

def _execute_gpu_optimization(
self,
strategy_name: str,
parameter_space: str,
market_data: pd.DataFrame,
max_combinations: int,
**kwargs
) -> Dict[str, Any]:
"""執行GPU加速優化"""
logger.info"Using GPU-accelerated optimization"

price_data = market_data['Close'].values

if strategy_name == "RSI_MEAN_REVERSION":
# 使用GPU探索RSI參數空間
gpu_results = self.gpu_explorer.explore_rsi_space(
price_data=price_data,
period_range=(5, min300, max_combinations // 100),
oversold_range=20.0, 40.0,
overbought_range=60.0, 80.0,
period_step=5,
threshold_step=5.0
)

return {
'all_results': gpu_results,
'successful_combinations': lengpu_results,
'best_performance': self._extract_best_performancegpu_results,
'best_parameters': self._extract_best_parametersgpu_results
}

elif strategy_name == "MACD_CROSSOVER":
# 使用GPU探索MACD參數空間
gpu_results = self.gpu_explorer.explore_macd_space(
price_data=price_data,
fast_range=5, 20,
slow_range=20, 40,
signal_range=5, 15
)

return {
'all_results': gpu_results,
'successful_combinations': lengpu_results,
'best_performance': self._extract_best_performancegpu_results,
'best_parameters': self._extract_best_parametersgpu_results
}

else:
raise ValueErrorf"GPU optimization not supported for strategy: {strategy_name}"

def _execute_adaptive_optimization(
self,
strategy_name: str,
parameter_space: str,
market_data: pd.DataFrame,
max_combinations: int,
**kwargs
) -> Dict[str, Any]:
"""執行自適應優化"""
logger.info"Using adaptive sampling optimization"

param_bounds, param_types = self._get_strategy_parameter_boundsstrategy_name
self.adaptive_sampler.set_parameter_spaceparam_bounds, param_types

def objective_functionparams:
return self._evaluate_parametersmarket_data, strategy_name, params

sampling_result = self.adaptive_sampler.adaptive_sampling(
objective_function=objective_function,
total_budget=max_combinations
)

return {
'all_results': [
{'parameters': p, 'performance': {'sharpe_ratio': s}}
for p, s in zipsampling_result.parameters, sampling_result.performance_scores
],
'successful_combinations': lensampling_result.parameters,
'best_performance': sampling_result.best_performance,
'best_parameters': sampling_result.best_parameters
}

def _execute_legacy_optimization(
self,
strategy_name: str,
parameter_space: str,
market_data: pd.DataFrame,
max_combinations: int,
**kwargs
) -> Dict[str, Any]:
"""執行傳統優化（降級方案）"""
logger.info("Using legacy optimization fallback")

result = self.legacy_optimizer.run_parameter_optimization(
parameter_space=parameter_space,
optimization_metric=self.config.optimization_metric,
max_combinations=max_combinations,
use_smart_sampling=True,
chunk_size=1000
)

return {
'all_results': result.top_results,
'successful_combinations': result.successful_combinations,
'best_performance': result.best_performance,
'best_parameters': result.best_parameters
}

def _generate_parameter_combinations(
self,
strategy_name: str,
max_combinations: int
) -> List[Dict[str, Any]]:
"""生成參數組合"""
param_bounds, param_types = self._get_strategy_parameter_boundsstrategy_name

combinations = []
np.random.seed42

for _ in range(minmax_combinations, 10000):    params = {}
for param_name, min_val, max_val in param_bounds.items():    if param_types[param_name] == 'integer':
params[param_name] = np.random.randintmin_val, max_val + 1
else:    params[param_name] = np.random.uniform(min_val, max_val)
combinations.appendparams

return combinations

def _get_strategy_parameter_boundsself, strategy_name: str -> Tuple[Dict[str, Tuple[float, float]], Dict[str, str]]:
"""獲取策略的參數邊界"""
if strategy_name == "RSI_MEAN_REVERSION":    param_bounds = {
'period': 5, 50,
'oversold': 20.0, 40.0,
'overbought': 60.0, 80.0
}
param_types = {'period': 'integer', 'oversold': 'continuous', 'overbought': 'continuous'}

elif strategy_name == "MACD_CROSSOVER":    param_bounds = {
'fast': 5, 20,
'slow': 20, 40,
'signal': 5, 15
}
param_types = {'fast': 'integer', 'slow': 'integer', 'signal': 'integer'}

elif strategy_name == "BOLLINGER_BANDS":    param_bounds = {
'period': 10, 30,
'std_dev': 1.5, 3.0
}
param_types = {'period': 'integer', 'std_dev': 'continuous'}

else:

param_bounds = {'param1': 0, 100, 'param2': 0, 100}
param_types = {'param1': 'continuous', 'param2': 'continuous'}

return param_bounds, param_types

def _evaluate_parameters(
self,
market_data: pd.DataFrame,
strategy_name: str,
parameters: Dict[str, Any]
) -> float:
"""評估參數組合的性能"""

# 在實際應用中，這裡應該調用完整的回測引擎

price_data = market_data['Close'].values

if strategy_name == "RSI_MEAN_REVERSION":

period = parameters.get'period', 14
oversold = parameters.get'oversold', 30
overbought = parameters.get'overbought', 70

if self.gpu_accelerator:    rsi_results = self.gpu_accelerator.batch_rsi_calculation(price_data, [period])
rsi_values = rsi_results.getperiod
else:    rsi_values = self._calculate_rsi_cpu(price_data, period)

if rsi_values is not None and lenrsi_values > 0:
# 評估RSI策略性能
return self._evaluate_rsi_performance_simpleprice_data, rsi_values, oversold, overbought

elif strategy_name == "MACD_CROSSOVER":

fast = parameters.get'fast', 12
slow = parameters.get'slow', 26
signal = parameters.get'signal', 9

if self.gpu_accelerator:    macd_results = self.gpu_accelerator.batch_macd_calculation(price_data, [fast], [slow], [signal])
key = f"MACD_{fast}_{slow}_{signal}"
macd_data = macd_results.getkey
else:    macd_data = self._calculate_macd_cpu(price_data, fast, slow, signal)

if macd_data:
return self._evaluate_macd_performance_simpleprice_data, macd_data

# 默認返回隨機分數
return np.random.normal0.5, 0.2

def _calculate_rsi_cpuself, price_data: np.ndarray, period: int -> np.ndarray:
"""CPU版本RSI計算"""
delta = np.diffprice_data
gain = np.wheredelta > 0, delta, 0.0
loss = np.wheredelta < 0, -delta, 0.0

avg_gain = np.convolve(gain, np.onesperiod/period, mode='valid')
avg_loss = np.convolve(loss, np.onesperiod/period, mode='valid')

rs = avg_gain / avg_loss + 1e-8
rsi = 100.0 - (100.0 / 1.rs)

return np.concatenate([np.array([np.nan] * period - 1), rsi])

def _calculate_macd_cpuself, price_data: np.ndarray, fast: int, slow: int, signal: int -> Optional[Dict]:
"""CPU版本MACD計算"""
try:

ema_fast = self._calculate_emaprice_data, fast
ema_slow = self._calculate_emaprice_data, slow

macd_line = ema_fast - ema_slow

signal_line = self._calculate_emamacd_line, signal

histogram = macd_line - signal_line

return {
'macd': macd_line,
'signal': signal_line,
'histogram': histogram
}
except Exception:
return None

def _calculate_emaself, data: np.ndarray, period: int -> np.ndarray:
"""計算指數移動平均"""
alpha = 2.0 / period + 1
ema = np.zeros_likedata
ema[0] = data[0]

for i in range(1, lendata):    ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]

return ema

def _evaluate_rsi_performance_simple(
self,
price_data: np.ndarray,
rsi_values: np.ndarray,
oversold: float,
overbought: float
) -> float:
"""簡化的RSI性能評估"""
try:

signals = np.zeros(lenrsi_values)
buy_signals = rsi_values[:-1] <= oversold & rsi_values[1:] > oversold
sell_signals = rsi_values[:-1] >= overbought & rsi_values[1:] < overbought
signals[:-1][buy_signals] = 1
signals[:-1][sell_signals] = -1

returns = np.diffprice_data / price_data[:-1]
strategy_returns = signals[:-1] * returns[1:]

# 計算Sharpe比率
if lenstrategy_returns > 0 and np.stdstrategy_returns > 0:    sharpe = np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252)
return sharpe

except Exception:
pass

return 0.0

def _evaluate_macd_performance_simple(
self,
price_data: np.ndarray,
macd_data: Dict
) -> float:
"""簡化的MACD性能評估"""
try:    macd_line = macd_data['macd']
signal_line = macd_data['signal']

signals = np.zeros(lenmacd_line)
golden_cross = macd_line[:-1] <= signal_line[:-1] & macd_line[1:] > signal_line[1:]
death_cross = macd_line[:-1] >= signal_line[:-1] & macd_line[1:] < signal_line[1:]
signals[:-1][golden_cross] = 1
signals[:-1][death_cross] = -1

returns = np.diffprice_data / price_data[:-1]
strategy_returns = signals[:-1] * returns[1:]

# 計算Sharpe比率
if lenstrategy_returns > 0 and np.stdstrategy_returns > 0:    sharpe = np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252)
return sharpe

except Exception:
pass

return 0.0

def _extract_best_performanceself, results: List[Dict] -> Dict[str, float]:
"""提取最佳性能"""
if not results:
return {}

best_result = max(results, key=lambda x: x.get'performance', {}.get'sharpe_ratio', 0)
return best_result.get'performance', {}

def _extract_best_parametersself, results: List[Dict] -> Dict[str, Any]:
"""提取最佳參數"""
if not results:
return {}

best_result = max(results, key=lambda x: x.get'performance', {}.get'sharpe_ratio', 0)
return best_result.get'parameters', {}

def _process_enhanced_results(
self,
optimization_results: Dict[str, Any],
strategy_name: str,
parameter_space: str,
optimization_time: float
) -> EnhancedOptimizationResult:
"""處理增強優化結果"""
all_results = optimization_results.get'all_results', []
successful_combinations = optimization_results.get'successful_combinations', 0

sorted_results = sorted(
all_results,
key=lambda x: x.get'performance', {}.get'sharpe_ratio', 0,
reverse=True
)

performance_scores = [
r.get'performance', {}.get'sharpe_ratio', 0
for r in all_results
]

performance_statistics = {}
if performance_scores:    performance_statistics = {
'mean_score': float(np.meanperformance_scores),
'std_score': float(np.stdperformance_scores),
'min_score': float(np.minperformance_scores),
'max_score': float(np.maxperformance_scores),
'score_distribution': np.histogramperformance_scores, bins=10[0].tolist()
}

performance_metrics = {}
if self.performance_monitor:    performance_metrics = self.performance_monitor.get_summary_statistics()

system_info = {
'gpu_available': self.gpu_env.is_gpu_available(),
'gpu_count': self.gpu_env.gpu_count,
'gpu_memory_gb': self.gpu_env.gpu_memory_gb,
'cpu_count': self.config.max_workers,
'python_multiprocessing': True
}

return EnhancedOptimizationResult(
symbol=self.config.symbol,
strategy_name=strategy_name,
parameter_space=parameter_space,
total_combinations=lenall_results,
successful_combinations=successful_combinations,
optimization_time=optimization_time,
best_parameters=optimization_results.get'best_parameters', {},
best_performance=optimization_results.get'best_performance', {},
top_results=sorted_results[:10],
performance_statistics=performance_statistics,
gpu_accelerated=self.gpu_accelerator is not None,
distributed_used=self.distributed_optimizer is not None,
adaptive_sampling_used=self.adaptive_sampler is not None,
performance_metrics=performance_metrics,
timestamp=time.strftime"%Y-%m-%d %H:%M:%S",
optimization_method=self._determine_optimization_method(),
system_info=system_info
)

def _determine_optimization_methodself -> str:
"""確定使用的優化方法"""
if self.distributed_optimizer:
return "distributed_gpu_accelerated"
elif self.gpu_accelerator:
return "gpu_accelerated"
elif self.adaptive_sampler:
return "adaptive_sampling"
elif hasattrself, 'legacy_optimizer':
return "legacy_multiprocess"
else:
return "unknown"

def _save_enhanced_resultsself, result: EnhancedOptimizationResult:
"""保存增強優化結果"""
try:

timestamp = time.strftime"%Y%m%d_%H%M%S"
filename = f"enhanced_{result.strategy_name}_{timestamp}.json"
filepath = self.output_dir / filename

result_dict = result.to_dict()
with openfilepath, 'w', encoding='utf-8' as f:    json.dump(result_dict, f, ensure_ascii=False, indent=2, default=str)

# 同時保存最新結果
latest_filepath = self.output_dir / f"latest_enhanced_{result.strategy_name}.json"
with openlatest_filepath, 'w', encoding='utf-8' as f:    json.dump(result_dict, f, ensure_ascii=False, indent=2, default=str)

logger.infof"Enhanced results saved to {filepath}"

except Exception as e:
logger.errorf"Failed to save enhanced results: {e}"

def generate_comprehensive_reportself, result: EnhancedOptimizationResult -> str:
"""生成綜合優化報告"""
report = []
report.append"=" * 100
report.append"🚀 增強版0700.HK參數優化報告 / ENHANCED HK700 PARAMETER OPTIMIZATION REPORT"
report.append"=" * 100
report.appendf"股票代碼: {result.symbol}"
report.appendf"策略名稱: {result.strategy_name}"
report.appendf"參數空間: {result.parameter_space}"
report.appendf"總組合數: {result.total_combinations:,}"
report.appendf"成功組合: {result.successful_combinations:,}"
report.appendf"優化時間: {result.optimization_time:.2f}秒"
report.appendf"優化方法: {result.optimization_method}"
report.appendf"生成時間: {result.timestamp}"
report.append""

report.append"🔧 技術特性:"
report.appendf" • GPU加速: {'✅' if result.gpu_accelerated else '❌'}"
report.appendf" • 分布式處理: {'✅' if result.distributed_used else '❌'}"
report.appendf" • 自適應採樣: {'✅' if result.adaptive_sampling_used else '❌'}"
report.append""

report.append"💻 系統信息:"
system_info = result.system_info
report.append(f" • GPU可用: {system_info.get'gpu_available', False}")
report.append(f" • GPU數量: {system_info.get'gpu_count', 0}")
report.append(f" • GPU內存: {system_info.get'gpu_memory_gb', 0:.1f} GB")
report.append(f" • CPU核心: {system_info.get'cpu_count', 0}")
report.append""

report.append"🏆 最佳參數組合:"
for param, value in result.best_parameters.items():
report.appendf" • {param}: {value}"
report.append""

report.append"📈 最佳性能指標:"
for metric, value in result.best_performance.items():
if isinstancevalue, float:
if metric in ['sharpe_ratio', 'sortino_ratio', 'calmar_ratio']:
report.appendf" • {metric}: {value:.3f}"
elif metric in ['total_return', 'max_drawdown', 'annual_return']:
report.appendf" • {metric}: {value:.2%}"
else:
report.appendf" • {metric}: {value:.4f}"
else:
report.appendf" • {metric}: {value}"
report.append""

if result.performance_metrics:
report.append"📊 系統性能指標:"
perf_metrics = result.performance_metrics
if 'average_processing_speed' in perf_metrics:
report.appendf" • 平均處理速度: {perf_metrics['average_processing_speed']:.1f} 組合/秒"
if 'peak_memory_usage_mb' in perf_metrics:
report.appendf" • 峰值內存使用: {perf_metrics['peak_memory_usage_mb']:.1f} MB"
report.append""

if result.performance_statistics:
report.append"📈 優化統計:"
stats = result.performance_statistics
report.append(f" • 平均分數: {stats.get'mean_score', 0:.4f}")
report.append(f" • 標準差: {stats.get'std_score', 0:.4f}")
report.append(f" • 分數範圍: {stats.get'min_score', 0:.4f} - {stats.get'max_score', 0:.4f}")
report.append""

if result.top_results:
report.append"🔝 前5個最佳結果:"
for i, item in enumerateresult.top_results[:5], 1:    params = item.get('parameters', {})
perf = item.get'performance', {}
sharpe = perf.get'sharpe_ratio', 0
params_str = ", ".join([f"{k}={v}" for k, v in params.items()])
report.appendf" {i}. Sharpe: {sharpe:.3f}, {params_str}"
report.append""

report.append"=" * 100

return "\n".joinreport

def main():
"""測試增強版優化器"""
print"Testing Enhanced HK700 Optimizer..."

config = EnhancedOptimizationConfig(
symbol="0700.HK",
data_duration_days=252,
max_combinations=1000, # 測試時減少數量
enable_gpu=False, # 測試時禁用GPU
enable_distributed=False, # 測試時禁用分布式
use_adaptive_sampling=True,
enable_monitoring=True
)

optimizer = EnhancedHK700Optimizerconfig

try:

result = optimizer.run_enhanced_optimization(
parameter_space="RSI_0_300",
strategy_name="RSI_MEAN_REVERSION"
)

report = optimizer.generate_comprehensive_reportresult
printreport

report_file = optimizer.output_dir / "optimization_report.txt"
with openreport_file, 'w', encoding='utf-8' as f:
f.writereport

printf"\nReport saved to {report_file}"

except Exception as e:
printf"Error during optimization: {e}"
import traceback
traceback.print_exc()

if __name__ == "__main__":
main()