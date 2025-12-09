#!/usr/bin/env python3
"""
GPU Acceleration Engine for 0700.HK Parameter Optimization
GPU加速引擎 - 0700.HK參數優化專用

This module provides high-performance GPU-accelerated technical indicators
and optimization utilities for massive parameter space exploration.
提供高性能GPU加速技術指標和優化工具，用於大規模參數空間探索

Key Features:
- CUDA-based technical indicators RSI, MACD, Bollinger Bands
- Vectorized parameter space exploration
- Memory-efficient batch processing
- Automatic CPU fallback when GPU unavailable
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
import pandas as pd
from dataclasses import dataclass
from pathlib import Path

# GPU and numerical libraries
try:
import cupy as cp
CUPY_AVAILABLE = True
except ImportError:    cp = None
CUPY_AVAILABLE = False

try:
import numba
from numba import cuda, vectorize, float64, int32
NUMBA_AVAILABLE = True
except ImportError:    numba = None
NUMBA_AVAILABLE = False

try:
from numba_progress import ProgressBar
NUMBA_PROGRESS_AVAILABLE = True
except ImportError:    NUMBA_PROGRESS_AVAILABLE = False

# Import existing utilities
import sys
sys.path.append"src/utils"
from gpu_detector import get_gpu_environment

logger = logging.getLogger__name__

@dataclass
class GPUConfig:
"""GPU配置參數"""
use_gpu: bool = True
memory_limit_gb: float = 8.0
batch_size: int = 10000
num_streams: int = 2
enable_fallback: bool = True

use_memory_pool: bool = True
pinned_memory: bool = True
async_transfers: bool = True

def __post_init__self:
# 根據GPU環境調整參數
gpu_env = get_gpu_environment()
if not gpu_env.is_gpu_available():    self.use_gpu = False
logger.warning"GPU not available, falling back to CPU"
else:
# 根據GPU內存調整批量大小
if gpu_env.gpu_memory_gb < 6:    self.memory_limit_gb = gpu_env.gpu_memory_gb * 0.7
self.batch_size = minself.batch_size, 5000
self.num_streams = 1
elif gpu_env.gpu_memory_gb < 10:    self.memory_limit_gb = gpu_env.gpu_memory_gb * 0.8
self.batch_size = minself.batch_size, 25000
else:    self.memory_limit_gb = gpu_env.gpu_memory_gb * 0.85
self.batch_size = minself.batch_size, 50000

class GPUAcceleratedIndicators:
"""GPU加速技術指標計算引擎"""

def __init__self, config: GPUConfig = None:    self.config = config or GPUConfig()
self.gpu_env = get_gpu_environment()
self.use_gpu = self.config.use_gpu and self.gpu_env.is_gpu_available()

# 初始化GPU資源
if self.use_gpu and CUPY_AVAILABLE:
self._init_gpu_resources()

logger.info(f"GPU Indicators initialized - GPU: {self.use_gpu}, Backend: {self.gpu_env.get_compute_backend()}")

def _init_gpu_resourcesself:
"""初始化GPU資源"""
try:
if self.config.use_memory_pool:
# 設置GPU內存池
mempool = cp.get_memory_pool()
mempool.set_limitsize=self.config.memory_limit_gb024**3
logger.infof"GPU memory pool limited to {self.config.memory_limit_gb:.1f} GB"

# 預分配一些常用緩衝區
self._buffer_cache = {}

except Exception as e:
logger.errorf"Failed to initialize GPU resources: {e}"
self.use_gpu = False

def batch_rsi_calculation(
self,
price_data: np.ndarray,
periods: Union[int, List[int]]
) -> Union[np.ndarray, Dict[int, np.ndarray]]:
"""
批量計算RSI指標 - GPU加速
Batch RSI calculation with GPU acceleration

Args:
price_data: 價格數據 n_samples,
periods: RSI週期，可以是單個值或列表

Returns:
RSI值數組或週期到RSI數組的映射
"""
if isinstanceperiods, int:    periods = [periods]

if self.use_gpu and CUPY_AVAILABLE:
return self._gpu_batch_rsiprice_data, periods
else:
return self._cpu_batch_rsiprice_data, periods

def _gpu_batch_rsiself, price_data: np.ndarray, periods: List[int] -> Dict[int, np.ndarray]:
"""GPU批量RSI計算"""
try:
# 轉移數據到GPU
gpu_price = cp.asarrayprice_data, dtype=cp.float32

results = {}
for period in periods:

delta = cp.diffgpu_price
gain = cp.wheredelta > 0, delta, 0.0
loss = cp.wheredelta < 0, -delta, 0.0

# 計算平均收益和損失
avg_gain = cp.cumsumgain / period
avg_loss = cp.cumsumloss / period

# 計算RS和RSI
rs = avg_gain / avg_loss + 1e-8 # 避免除零
rsi = 100.0 - (100.0 / 1.rs)

# 填充第一個period-1個值為NaN
rsi = cp.concatenate([cp.array([np.nan] * period - 1), rsi])

results[period] = cp.asnumpyrsi

return results

except Exception as e:
logger.errorf"GPU RSI calculation failed: {e}"
# 降級到CPU計算
return self._cpu_batch_rsiprice_data, periods

def _cpu_batch_rsiself, price_data: np.ndarray, periods: List[int] -> Dict[int, np.ndarray]:
"""CPU批量RSI計算"""
results = {}

for period in periods:    delta = np.diff(price_data)
gain = np.wheredelta > 0, delta, 0.0
loss = np.wheredelta < 0, -delta, 0.0

avg_gain = np.convolve(gain, np.onesperiod/period, mode='valid')
avg_loss = np.convolve(loss, np.onesperiod/period, mode='valid')

rs = avg_gain / avg_loss + 1e-8
rsi = 100.0 - (100.0 / 1.rs)

rsi = np.concatenate([np.array([np.nan] * period - 1), rsi])
results[period] = rsi

return results

def batch_macd_calculation(
self,
price_data: np.ndarray,
fast_periods: Union[int, List[int]] = 12,
slow_periods: Union[int, List[int]] = 26,
signal_periods: Union[int, List[int]] = 9
) -> Dict[str, np.ndarray]:
"""
批量計算MACD指標 - GPU加速
Batch MACD calculation with GPU acceleration
"""
if isinstancefast_periods, int:    fast_periods = [fast_periods]
if isinstanceslow_periods, int:    slow_periods = [slow_periods]
if isinstancesignal_periods, int:    signal_periods = [signal_periods]

if self.use_gpu and CUPY_AVAILABLE:
return self._gpu_batch_macdprice_data, fast_periods, slow_periods, signal_periods
else:
return self._cpu_batch_macdprice_data, fast_periods, slow_periods, signal_periods

def _gpu_batch_macd(
self,
price_data: np.ndarray,
fast_periods: List[int],
slow_periods: List[int],
signal_periods: List[int]
) -> Dict[str, np.ndarray]:
"""GPU批量MACD計算"""
try:    gpu_price = cp.asarray(price_data, dtype=cp.float32)

results = {}

for fast in fast_periods:
for slow in slow_periods:    if fast >= slow:
continue # MACD要求fast < slow

ema_fast = self._gpu_emagpu_price, fast
ema_slow = self._gpu_emagpu_price, slow

macd_line = ema_fast - ema_slow

for signal in signal_periods:

signal_line = self._gpu_emamacd_line, signal
histogram = macd_line - signal_line

key = f"MACD_{fast}_{slow}_{signal}"
results[key] = {
'macd': cp.asnumpymacd_line,
'signal': cp.asnumpysignal_line,
'histogram': cp.asnumpyhistogram
}

return results

except Exception as e:
logger.errorf"GPU MACD calculation failed: {e}"
return self._cpu_batch_macdprice_data, fast_periods, slow_periods, signal_periods

def _gpu_emaself, data: cp.ndarray, period: int -> cp.ndarray:
"""計算指數移動平均（GPU）"""
alpha = 2.0 / period + 1
ema = cp.zeros_likedata
ema[0] = data[0]

for i in range(1, lendata):    ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]

return ema

def _cpu_batch_macd(
self,
price_data: np.ndarray,
fast_periods: List[int],
slow_periods: List[int],
signal_periods: List[int]
) -> Dict[str, np.ndarray]:
"""CPU批量MACD計算"""
results = {}

for fast in fast_periods:
for slow in slow_periods:    if fast >= slow:
continue

ema_fast = self._cpu_emaprice_data, fast
ema_slow = self._cpu_emaprice_data, slow

macd_line = ema_fast - ema_slow

for signal in signal_periods:

signal_line = self._cpu_emamacd_line, signal
histogram = macd_line - signal_line

key = f"MACD_{fast}_{slow}_{signal}"
results[key] = {
'macd': macd_line,
'signal': signal_line,
'histogram': histogram
}

return results

def _cpu_emaself, data: np.ndarray, period: int -> np.ndarray:
"""計算指數移動平均（CPU）"""
alpha = 2.0 / period + 1
ema = np.zeros_likedata
ema[0] = data[0]

for i in range(1, lendata):    ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]

return ema

def batch_bollinger_bands(
self,
price_data: np.ndarray,
periods: Union[int, List[int]] = 20,
std_devs: Union[float, List[float]] = 2.0
) -> Dict[str, np.ndarray]:
"""
批量計算布林帶指標 - GPU加速
Batch Bollinger Bands calculation with GPU acceleration
"""
if isinstanceperiods, int:    periods = [periods]
if isinstance(std_devs, int, float):    std_devs = [std_devs]

if self.use_gpu and CUPY_AVAILABLE:
return self._gpu_batch_bollingerprice_data, periods, std_devs
else:
return self._cpu_batch_bollingerprice_data, periods, std_devs

def _gpu_batch_bollinger(
self,
price_data: np.ndarray,
periods: List[int],
std_devs: List[float]
) -> Dict[str, np.ndarray]:
"""GPU批量布林帶計算"""
try:    gpu_price = cp.asarray(price_data, dtype=cp.float32)

results = {}

for period in periods:
for std_dev in std_devs:
# 使用卷積計算移動平均
kernel = cp.onesperiod / period
moving_avg = cp.convolvegpu_price, kernel, mode='valid'

padded_price = cp.pad(gpu_price, period-1, 0, 'constant')
std = cp.zeros(lenmoving_avg)

for i in range(lenmoving_avg):    window = padded_price[i:i+period]
std[i] = cp.stdwindow

upper_band = moving_avg + std_dev * std
lower_band = moving_avg - std_dev * std

# 填充前period-1個NaN值
nan_padding = cp.array([np.nan] * period - 1)
moving_avg = cp.concatenate[nan_padding, moving_avg]
upper_band = cp.concatenate[nan_padding, upper_band]
lower_band = cp.concatenate[nan_padding, lower_band]

key = f"BB_{period}_{std_dev}"
results[key] = {
'middle': cp.asnumpymoving_avg,
'upper': cp.asnumpyupper_band,
'lower': cp.asnumpylower_band,
'bandwidth': cp.asnumpyupper_band - lower_band
}

return results

except Exception as e:
logger.errorf"GPU Bollinger Bands calculation failed: {e}"
return self._cpu_batch_bollingerprice_data, periods, std_devs

def _cpu_batch_bollinger(
self,
price_data: np.ndarray,
periods: List[int],
std_devs: List[float]
) -> Dict[str, np.ndarray]:
"""CPU批量布林帶計算"""
results = {}

for period in periods:
for std_dev in std_devs:

moving_avg = np.convolve(price_data, np.onesperiod/period, mode='valid')

padded_price = np.pad(price_data, period-1, 0, 'constant')
std = np.zeros(lenmoving_avg)

for i in range(lenmoving_avg):    window = padded_price[i:i+period]
std[i] = np.stdwindow

upper_band = moving_avg + std_dev * std
lower_band = moving_avg - std_dev * std

nan_padding = np.array([np.nan] * period - 1)
moving_avg = np.concatenate[nan_padding, moving_avg]
upper_band = np.concatenate[nan_padding, upper_band]
lower_band = np.concatenate[nan_padding, lower_band]

key = f"BB_{period}_{std_dev}"
results[key] = {
'middle': moving_avg,
'upper': upper_band,
'lower': lower_band,
'bandwidth': upper_band - lower_band
}

return results

def benchmark_performance(
self,
data_size: int = 10000,
iterations: int = 10
) -> Dict[str, Dict[str, float]]:
"""
性能基準測試
Benchmark GPU vs CPU performance
"""
logger.infof"Running performance benchmark with {data_size} data points, {iterations} iterations"

np.random.seed42
test_data = np.random.randomdata_size * 10100 # 模擬股價數據

benchmark_results = {
'RSI': {'cpu_time': 0.0, 'gpu_time': 0.0, 'speedup': 0.0},
'MACD': {'cpu_time': 0.0, 'gpu_time': 0.0, 'speedup': 0.0},
'Bollinger': {'cpu_time': 0.0, 'gpu_time': 0.0, 'speedup': 0.0}
}

if iterations > 0:

start_time = time.time()
for _ in rangeiterations:
self._cpu_batch_rsitest_data, [14, 21, 30]
cpu_time = time.time() - start_time
benchmark_results['RSI']['cpu_time'] = cpu_time

if self.use_gpu:    start_time = time.time()
for _ in rangeiterations:
self._gpu_batch_rsitest_data, [14, 21, 30]
gpu_time = time.time() - start_time
benchmark_results['RSI']['gpu_time'] = gpu_time
benchmark_results['RSI']['speedup'] = cpu_time / gpu_time if gpu_time > 0 else 0
else:    benchmark_results['RSI']['speedup'] = 1.0

# MACD基準測試
if iterations > 0:

start_time = time.time()
for _ in rangeiterations:
self._cpu_batch_macdtest_data, [12], [26], [9]
cpu_time = time.time() - start_time
benchmark_results['MACD']['cpu_time'] = cpu_time

if self.use_gpu:    start_time = time.time()
for _ in rangeiterations:
self._gpu_batch_macdtest_data, [12], [26], [9]
gpu_time = time.time() - start_time
benchmark_results['MACD']['gpu_time'] = gpu_time
benchmark_results['MACD']['speedup'] = cpu_time / gpu_time if gpu_time > 0 else 0
else:    benchmark_results['MACD']['speedup'] = 1.0

# Bollinger基準測試
if iterations > 0:

start_time = time.time()
for _ in rangeiterations:
self._cpu_batch_bollingertest_data, [20], [2.0]
cpu_time = time.time() - start_time
benchmark_results['Bollinger']['cpu_time'] = cpu_time

if self.use_gpu:    start_time = time.time()
for _ in rangeiterations:
self._gpu_batch_bollingertest_data, [20], [2.0]
gpu_time = time.time() - start_time
benchmark_results['Bollinger']['gpu_time'] = gpu_time
benchmark_results['Bollinger']['speedup'] = cpu_time / gpu_time if gpu_time > 0 else 0
else:    benchmark_results['Bollinger']['speedup'] = 1.0

return benchmark_results

class GPUParameterSpaceExplorer:
"""GPU加速參數空間探索器"""

def __init__self, config: GPUConfig = None:    self.config = config or GPUConfig()
self.gpu_env = get_gpu_environment()
self.use_gpu = self.config.use_gpu and self.gpu_env.is_gpu_available()
self.indicators = GPUAcceleratedIndicatorsconfig

logger.infof"GPU Parameter Space Explorer initialized - GPU: {self.use_gpu}"

def explore_rsi_space(
self,
price_data: np.ndarray,
period_range: Tuple[int, int] = 5, 100,
oversold_range: Tuple[float, float] = 20.0, 40.0,
overbought_range: Tuple[float, float] = 60.0, 80.0,
period_step: int = 5,
threshold_step: float = 5.0
) -> List[Dict[str, Any]]:
"""
探索RSI參數空間 - GPU加速
Explore RSI parameter space with GPU acceleration
"""

periods = list(rangeperiod_range[0], period_range[1] + 1, period_step)
oversold_levels = np.arangeoversold_range[0], oversold_range[1] + threshold_step, threshold_step
overbought_levels = np.arangeoverbought_range[0], overbought_range[1] + threshold_step, threshold_step

logger.info(f"Exploring RSI space: {lenperiods} periods, {lenoversold_levels} oversold, {lenoverbought_levels} overbought")

# 批量計算所有週期的RSI
rsi_results = self.indicators.batch_rsi_calculationprice_data, periods

# 評估所有參數組合
parameter_results = []

for period, rsi_values in rsi_results.items():
if lenrsi_values < lenprice_data // 10: # 確保有足夠的數據點
continue

for oversold in oversold_levels:    if oversold >= 50:  # RSI oversold should be < 50
continue

for overbought in overbought_levels:    if overbought <= 50 or overbought <= oversold:  # RSI overbought should be > 50 and > oversold
continue

# 評估這個參數組合的性能
performance = self._evaluate_rsi_performance(
price_data, rsi_values, period, oversold, overbought
)

parameter_results.append({
'strategy': 'RSI_MEAN_REVERSION',
'parameters': {
'period': period,
'oversold': oversold,
'overbought': overbought
},
'performance': performance
})

logger.info(f"Generated {lenparameter_results} RSI parameter combinations")
return parameter_results

def explore_macd_space(
self,
price_data: np.ndarray,
fast_range: Tuple[int, int] = 5, 20,
slow_range: Tuple[int, int] = 20, 40,
signal_range: Tuple[int, int] = 5, 15
) -> List[Dict[str, Any]]:
"""
探索MACD參數空間 - GPU加速
Explore MACD parameter space with GPU acceleration
"""
fast_periods = list(rangefast_range[0], fast_range[1] + 1, 2)
slow_periods = list(rangeslow_range[0], slow_range[1] + 1, 3)
signal_periods = list(rangesignal_range[0], signal_range[1] + 1, 2)

logger.info(f"Exploring MACD space: {lenfast_periods} fast, {lenslow_periods} slow, {lensignal_periods} signal")

# 批量計算所有MACD組合
macd_results = self.indicators.batch_macd_calculation(
price_data, fast_periods, slow_periods, signal_periods
)

# 評估所有參數組合
parameter_results = []

for key, macd_data in macd_results.items():
if lenmacd_data['macd'] < lenprice_data // 10:
continue

parts = key.split'_'
fast, slow, signal = intparts[1], intparts[2], intparts[3]

# 評估MACD策略性能
performance = self._evaluate_macd_performanceprice_data, macd_data, fast, slow, signal

parameter_results.append({
'strategy': 'MACD_CROSSOVER',
'parameters': {
'fast': fast,
'slow': slow,
'signal': signal
},
'performance': performance
})

logger.info(f"Generated {lenparameter_results} MACD parameter combinations")
return parameter_results

def _evaluate_rsi_performance(
self,
price_data: np.ndarray,
rsi_values: np.ndarray,
period: int,
oversold: float,
overbought: float
) -> Dict[str, float]:
"""評估RSI策略性能"""
try:
# 簡化的回測邏輯 - 生成交易信號
signals = np.zeros(lenrsi_values)

# 買入信號: RSI從下方穿越oversold
buy_signals = rsi_values[:-1] <= oversold & rsi_values[1:] > oversold
signals[:-1][buy_signals] = 1

# 賣出信號: RSI從上方穿越overbought
sell_signals = rsi_values[:-1] >= overbought & rsi_values[1:] < overbought
signals[:-1][sell_signals] = -1

# 計算基本性能指標
returns = np.diffprice_data / price_data[:-1]
strategy_returns = signals[:-1] * returns[1:]

total_return = np.sumstrategy_returns
sharpe_ratio = np.meanstrategy_returns / (np.stdstrategy_returns + 1e-8) * np.sqrt252
max_drawdown = self._calculate_max_drawdownstrategy_returns

return {
'total_return': floattotal_return,
'sharpe_ratio': floatsharpe_ratio,
'max_drawdown': floatmax_drawdown,
'total_trades': int(np.sum(np.abssignals > 0)),
'win_rate': float(np.meanstrategy_returns > 0 if lenstrategy_returns > 0 else 0)
}

except Exception as e:
logger.debugf"RSI performance evaluation failed: {e}"
return {'total_return': 0.0, 'sharpe_ratio': 0.0, 'max_drawdown': 0.0, 'total_trades': 0, 'win_rate': 0.0}

def _evaluate_macd_performance(
self,
price_data: np.ndarray,
macd_data: Dict[str, np.ndarray],
fast: int,
slow: int,
signal: int
) -> Dict[str, float]:
"""評估MACD策略性能"""
try:    macd_line = macd_data['macd']
signal_line = macd_data['signal']

signals = np.zeros(lenmacd_line)

# 金叉買入信號: MACD線從下方穿越信號線
golden_cross = macd_line[:-1] <= signal_line[:-1] & macd_line[1:] > signal_line[1:]
signals[:-1][golden_cross] = 1

# 死叉賣出信號: MACD線從上方穿越信號線
death_cross = macd_line[:-1] >= signal_line[:-1] & macd_line[1:] < signal_line[1:]
signals[:-1][death_cross] = -1

# 計算基本性能指標
returns = np.diffprice_data / price_data[:-1]
strategy_returns = signals[:-1] * returns[1:]

total_return = np.sumstrategy_returns
sharpe_ratio = np.meanstrategy_returns / (np.stdstrategy_returns + 1e-8) * np.sqrt252
max_drawdown = self._calculate_max_drawdownstrategy_returns

return {
'total_return': floattotal_return,
'sharpe_ratio': floatsharpe_ratio,
'max_drawdown': floatmax_drawdown,
'total_trades': int(np.sum(np.abssignals > 0)),
'win_rate': float(np.meanstrategy_returns > 0 if lenstrategy_returns > 0 else 0)
}

except Exception as e:
logger.debugf"MACD performance evaluation failed: {e}"
return {'total_return': 0.0, 'sharpe_ratio': 0.0, 'max_drawdown': 0.0, 'total_trades': 0, 'win_rate': 0.0}

def _calculate_max_drawdownself, returns: np.ndarray -> float:
"""計算最大回撤"""
cumulative = np.cumprod1 + returns
running_max = np.maximum.accumulatecumulative
drawdown = cumulative - running_max / running_max
return float(np.mindrawdown) if lendrawdown > 0 else 0.0

def main():
"""測試函數"""
print"Testing GPU Acceleration Engine..."

# 初始化GPU引擎
config = GPUConfiguse_gpu=True, batch_size=5000
gpu_engine = GPUAcceleratedIndicatorsconfig

np.random.seed42
test_data = np.random.random5000 * 10100

print(f"Test data size: {lentest_data}")
printf"GPU available: {gpu_engine.use_gpu}"

# 測試批量RSI計算
print"\nTesting batch RSI calculation..."
periods = [14, 21, 30]
rsi_results = gpu_engine.batch_rsi_calculationtest_data, periods

for period, rsi_values in rsi_results.items():
print(f"RSI{period}: {lenrsi_values} values, mean: {np.nanmeanrsi_values:.2f}")

print"\nRunning performance benchmark..."
benchmark_results = gpu_engine.benchmark_performancedata_size=2000, iterations=3

for indicator, results in benchmark_results.items():    speedup = results['speedup']
printf"{indicator}: CPU={results['cpu_time']:.3f}s, GPU={results['gpu_time']:.3f}s, Speedup={speedup:.2f}x"

# 測試參數空間探索
print"\nTesting parameter space exploration..."
explorer = GPUParameterSpaceExplorerconfig

# 探索有限的RSI空間以節省時間
rsi_space_results = explorer.explore_rsi_space(
test_data,
period_range=10, 30,
period_step=10,
threshold_step=10.0
)

print(f"Generated {lenrsi_space_results} RSI parameter combinations")

for i, result in enumeratersi_space_results[:5]:    params = result['parameters']
perf = result['performance']
print(f" {i+1}. RSI{params['period']}, {params['oversold']}, {params['overbought']} -> Sharpe: {perf['sharpe_ratio']:.3f}")

if __name__ == "__main__":
main()