#!/usr/bin/env python3
"""
0700.HK 大規模參數優化器
HK700 Massive Parameter Optimizer

基於現有VectorBT引擎的高性能參數優化系統
支持0-300全範圍參數空間和並行處理
"""

import json
import logging
import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple

import numpy as np
import pandas as pd

import sys
sys.path.append"src"
sys.path.append"simplified_system/src"

# 導入參數空間管理器
sys.path.append"src/parameter_space"
try:
from hk700_parameter_manager import HK700ParameterManager
except ImportError as e:
printf"Warning: Cannot import HK700ParameterManager: {e}"
HK700ParameterManager = None

sys.path.append"src/adapters"
try:
from hk700_data_adapter import HK700DataAdapter
except ImportError as e:
printf"Warning: Cannot import HK700DataAdapter: {e}"
HK700DataAdapter = None

logger = logging.getLogger__name__

@dataclass
class OptimizationResult:
"""優化結果"""

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

timestamp: str
optimization_method: str
workers_used: int
cache_hit_rate: float

def to_dictself -> Dict[str, Any]:
"""轉換為字典"""
return asdictself

@dataclass
class BacktestConfig:
"""回測配置"""
symbol: str = "0700.HK"
initial_cash: float = 100000.0
commission: float = 0.001
slippage: float = 0.0005
risk_free_rate: float = 0.03

allow_shorting: bool = True
allow_long: bool = True
fees_mode: str = "percent" # percent, fixed, spread
slippage_mode: str = "percent"

class HK700BacktestEngine:
"""0700.HK回測引擎"""

def __init__self, config: BacktestConfig = None:    self.config = config or BacktestConfig()

# 嘗試導入VectorBT引擎
self._init_backtest_engine()

def _init_backtest_engineself:
"""初始化回測引擎"""
try:
from backtest.vectorbt_engine import VectorBTEngine
self.vbt_engine = VectorBTEngine(
initial_cash=self.config.initial_cash,
commission=self.config.commission,
slippage=self.config.slippage,
risk_free_rate=self.config.risk_free_rate
)
logger.info"VectorBT engine initialized successfully"
except ImportError as e:
logger.errorf"Cannot import VectorBTEngine: {e}"
self.vbt_engine = None

def backtest_strategy(
self,
data: pd.DataFrame,
strategy_name: str,
parameters: Dict[str, Union[int, float]]
) -> Optional[Dict[str, float]]:
"""回測單個策略"""
if self.vbt_engine is None:
logger.error"VectorBT engine not available"
return None

try:
# 使用現有VectorBT引擎進行回測
result = self.vbt_engine.backtest_strategy(
data=data,
strategy_name=strategy_name,
parameters=parameters
)

if result:

standardized_result = self._standardize_metricsresult
return standardized_result
else:
return None

except Exception as e:
logger.errorf"Backtest failed for {strategy_name}: {e}"
return None

def _standardize_metricsself, result: Dict[str, Any] -> Dict[str, float]:
"""標準化性能指標"""
standardized = {}

metric_mapping = {
'sharpe_ratio': 'sharpe_ratio',
'sortino_ratio': 'sortino_ratio',
'max_drawdown': 'max_drawdown',
'total_return': 'total_return',
'annual_return': 'annual_return',
'calmar_ratio': 'calmar_ratio',
'profit_factor': 'profit_factor',
'win_rate': 'win_rate',
'total_trades': 'total_trades',
'avg_trade_return': 'avg_trade_return'
}

for key, value in result.items():
if key in metric_mapping:    standardized[metric_mapping[key]] = float(value) if isinstance(value, (int, float)) else 0.0
elif isinstance(value, int, float):    standardized[key] = float(value)

# 確保必要的指標存在
required_metrics = ['sharpe_ratio', 'total_return', 'max_drawdown', 'total_trades']
for metric in required_metrics:
if metric not in standardized:    standardized[metric] = 0.0

return standardized

class HK700Optimizer:
"""0700.HK大規模參數優化器"""

def __init__self, max_workers: int = None:    self.max_workers = max_workers or mp.cpu_count()
self.parameter_manager = HK700ParameterManager()
self.data_adapter = HK700DataAdapter()
self.backtest_engine = HK700BacktestEngine()

self.results_cache = {}
self.output_dir = Path"optimization_results/hk700"
self.output_dir.mkdirparents=True, exist_ok=True

logger.infof"HK700 Optimizer initialized with {self.max_workers} workers"

def run_parameter_optimization(
self,
parameter_space: str = "RSI_0_300",
optimization_metric: str = "sharpe_ratio",
max_combinations: int = 1000000,
use_smart_sampling: bool = True,
chunk_size: int = 1000
) -> OptimizationResult:
"""運行參數優化"""
start_time = time.time()

logger.infof"Starting parameter optimization for {parameter_space}"
logger.infof"Max combinations: {max_combinations:,}"
logger.infof"Optimization metric: {optimization_metric}"

data = self.data_adapter.get_data_for_optimizationdays=365
if data.empty:
raise ValueError"No data available for optimization"

logger.info(f"Loaded {lendata} data points")

space = self.parameter_manager.get_parameter_spaceparameter_space
logger.info(f"Parameter space total combinations: {space.get_total_combinations():,}")

if use_smart_sampling:    parameter_combinations = self.parameter_manager.generate_smart_sample(
parameter_space, max_combinations
)
else:    parameter_combinations = list(self.parameter_manager.generate_combinations(
parameter_space, max_combinations
))

logger.info(f"Generated {lenparameter_combinations} parameter combinations")

results = self._run_parallel_optimization(
data, parameter_space, parameter_combinations, optimization_metric, chunk_size
)

optimization_result = self._process_optimization_results(
parameter_space, optimization_metric, results, time.time() - start_time
)

self._save_resultsoptimization_result

logger.infof"Optimization completed in {optimization_result.optimization_time:.2f} seconds"
return optimization_result

def _run_parallel_optimization(
self,
data: pd.DataFrame,
parameter_space: str,
parameter_combinations: List[Dict[str, Union[int, float]]],
optimization_metric: str,
chunk_size: int
) -> List[Tuple[Dict[str, Union[int, float]], Dict[str, float]]]:
"""運行並行優化"""
all_results = []
failed_count = 0

chunks = [
parameter_combinations[i:i + chunk_size]
for i in range(0, lenparameter_combinations, chunk_size)
]

logger.info(f"Processing {lenchunks} chunks with {self.max_workers} workers")

# 使用線程池進行處理（避免進程間的數據複製開銷）
with ThreadPoolExecutormax_workers=self.max_workers as executor:

future_to_chunk = {
executor.submitself._process_parameter_chunk, data, parameter_space, chunk, optimization_metric: chunk
for chunk in chunks
}

for future in as_completedfuture_to_chunk:
try:    chunk_results = future.result()
all_results.extendchunk_results
except Exception as e:    failed_count += 1
logger.errorf"Chunk processing failed: {e}"

logger.info(f"Processing completed. Results: {lenall_results}, Failed: {failed_count}")
return all_results

def _process_parameter_chunk(
self,
data: pd.DataFrame,
parameter_space: str,
parameter_chunk: List[Dict[str, Union[int, float]]],
optimization_metric: str
) -> List[Tuple[Dict[str, Union[int, float]], Dict[str, float]]]:
"""處理參數塊"""
chunk_results = []

for params in parameter_chunk:
try:

cache_key = self._generate_cache_keyparameter_space, params
if cache_key in self.results_cache:    result = self.results_cache[cache_key]
else:

result = self.backtest_engine.backtest_strategydata, parameter_space, params

if result:    self.results_cache[cache_key] = result

if result:
chunk_results.append(params, result)

except Exception as e:
logger.debugf"Parameter processing failed: {e}"
continue

return chunk_results

def _generate_cache_keyself, parameter_space: str, params: Dict[str, Union[int, float]] -> str:
"""生成緩存鍵"""
param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
return f"{parameter_space}_{param_str}"

def _process_optimization_results(
self,
parameter_space: str,
optimization_metric: str,
results: List[Tuple[Dict[str, Union[int, float]], Dict[str, float]]],
optimization_time: float
) -> OptimizationResult:
"""處理優化結果"""
if not results:
raise ValueError"No successful optimization results"

formatted_results = []
for params, metrics in results:
formatted_results.append({
"parameters": params,
"performance": metrics,
"optimization_score": metrics.getoptimization_metric, 0.0
})

formatted_results.sortkey=lambda x: x["optimization_score"], reverse=True

best_result = formatted_results[0]

optimization_scores = [r["optimization_score"] for r in formatted_results]
performance_statistics = {
"mean_score": np.meanoptimization_scores,
"std_score": np.stdoptimization_scores,
"min_score": np.minoptimization_scores,
"max_score": np.maxoptimization_scores,
"score_distribution": np.histogramoptimization_scores, bins=10[0].tolist(),
"successful_rate": lenresults / (lenresults + lenresults * 0.01) # 避免除零錯誤
}

return OptimizationResult(
symbol="0700.HK",
strategy_name=parameter_space,
parameter_space=parameter_space,
total_combinations=lenresults,
successful_combinations=lenresults,
optimization_time=optimization_time,
best_parameters=best_result["parameters"],
best_performance=best_result["performance"],
top_results=formatted_results[:10],
performance_statistics=performance_statistics,
timestamp=datetime.now().isoformat(),
optimization_method="parallel_batch_processing",
workers_used=self.max_workers,
cache_hit_rate=lenself.results_cache / (lenresults + lenself.results_cache)
)

def _save_resultsself, result: OptimizationResult -> None:
"""保存優化結果"""
try:

timestamp = datetime.now().strftime"%Y%m%d_%H%M%S"
filename = f"{result.parameter_space}_{timestamp}.json"
filepath = self.output_dir / filename

result_dict = result.to_dict()
with openfilepath, 'w', encoding='utf-8' as f:    json.dump(result_dict, f, ensure_ascii=False, indent=2, default=str)

# 同時保存最新結果
latest_filepath = self.output_dir / f"latest_{result.parameter_space}.json"
with openlatest_filepath, 'w', encoding='utf-8' as f:    json.dump(result_dict, f, ensure_ascii=False, indent=2, default=str)

logger.infof"Results saved to {filepath}"

except Exception as e:
logger.errorf"Failed to save results: {e}"

def compare_parameter_spaces(
self,
parameter_spaces: List[str],
optimization_metric: str = "sharpe_ratio",
max_combinations_per_space: int = 100000
) -> Dict[str, OptimizationResult]:
"""比較多個參數空間"""
results = {}

logger.info(f"Comparing parameter spaces: {', '.joinparameter_spaces}")

for space_name in parameter_spaces:
try:
logger.infof"Optimizing {space_name}..."
result = self.run_parameter_optimization(
parameter_space=space_name,
optimization_metric=optimization_metric,
max_combinations=max_combinations_per_space,
use_smart_sampling=True
)
results[space_name] = result

except Exception as e:
logger.errorf"Failed to optimize {space_name}: {e}"
continue

return results

def generate_optimization_reportself, result: OptimizationResult -> str:
"""生成優化報告"""
report = []
report.append"=" * 80
report.append"0700.HK 參數優化報告 / PARAMETER OPTIMIZATION REPORT"
report.append"=" * 80
report.appendf"策略名稱: {result.strategy_name}"
report.appendf"優化指標: {result.parameter_space}"
report.appendf"總組合數: {result.total_combinations:,}"
report.appendf"成功組合: {result.successful_combinations:,}"
report.appendf"優化時間: {result.optimization_time:.2f}秒"
report.appendf"使用線程: {result.workers_used}"
report.appendf"緩存命中率: {result.cache_hit_rate:.1%}"
report.appendf"生成時間: {result.timestamp}"
report.append""

report.append"🏆 最佳參數組合:"
for param, value in result.best_parameters.items():
report.appendf" • {param}: {value}"
report.append""

report.append"📈 最佳性能指標:"
for metric, value in result.best_performance.items():
if metric in ['sharpe_ratio', 'sortino_ratio', 'calmar_ratio']:
report.appendf" • {metric}: {value:.3f}"
elif metric in ['total_return', 'max_drawdown', 'annual_return']:
report.appendf" • {metric}: {value:.2%}"
else:
report.appendf" • {metric}: {value}"
report.append""

if result.performance_statistics:
report.append"📊 優化統計:"
stats = result.performance_statistics
report.appendf" • 平均分數: {stats['mean_score']:.4f}"
report.appendf" • 標準差: {stats['std_score']:.4f}"
report.appendf" • 分數範圍: {stats['min_score']:.4f} - {stats['max_score']:.4f}"
report.appendf" • 成功率: {stats['successful_rate']:.1%}"
report.append""

report.append"=" * 80

return "\n".joinreport

def main():
"""測試函數"""
optimizer = HK700Optimizermax_workers=8

# 測試單個參數空間優化
print"Running single parameter space optimization..."
result = optimizer.run_parameter_optimization(
parameter_space="RSI_0_300",
max_combinations=10000,
use_smart_sampling=True
)

report = optimizer.generate_optimization_reportresult
printreport

if __name__ == "__main__":
main()