#!/usr / bin / env python3
"""
Phase 4 參數優化集成系統
Parameter Optimization Integration System for Phase 4

專為互動式量化交易平台設計的高級參數優化模組
Advanced parameter optimization module designed for interactive quantitative trading platform

Features:
- 大規模參數優化 Massive Parameter Optimization
- 實時進度顯示 Real - time Progress Display
- 多策略並行優化 Multi - strategy Parallel Optimization
- 結果分析和可視化 Result Analysis and Visualization
- 最佳策略展示 Best Strategy Showcase
- GPU加速支持 GPU Acceleration Support
"""

import json
import logging
import multiprocessing as mp
import queue
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

import pandas as pd

# 嘗試導入可視化庫
try:
from tqdm import tqdm

TQDM_AVAILABLE = True
except ImportError:    TQDM_AVAILABLE = False

try:
from tabulate import tabulate

TABULATE_AVAILABLE = True
except ImportError:    TABULATE_AVAILABLE = False

# 導入項目模塊 - 修復導入路徑
project_root = Path__file__.parent.parent.parent
simplified_system_path = project_root / "simplified_system" / "src"
sys.path.insert(0, strsimplified_system_path)

# 安全導入，避免相對導入錯誤
try:
from backtest.vectorbt_engine import BacktestResult, VectorBTEngine
except ImportError as e:
printf"Warning: Cannot import VectorBTEngine: {e}"
VectorBTEngine = None
BacktestResult = None

try:
from api.stock_api import get_hk_stock_data
except ImportError as e:
printf"Warning: Cannot import get_hk_stock_data: {e}"
get_hk_stock_data = None

try:
from indicators.core_indicators import CoreIndicators
except ImportError as e:
printf"Warning: Cannot import CoreIndicators: {e}"
CoreIndicators = None

# 導入配置和依賴管理
utils_path = project_root / "src" / "utils"
sys.path.insert(0, strutils_path)
try:
from dependency_manager import DependencyManager
except ImportError:    DependencyManager = None

try:
from config_manager import ConfigManager
except ImportError:    ConfigManager = None

logger = logging.getLogger__name__

@dataclass
class OptimizationConfig:
"""優化配置"""

symbol: str = "0700.HK"
duration: int = 252
strategy: str = "RSI_MEAN_REVERSION"

optimization_metric: str = (
"sharpe_ratio" # sharpe_ratio, total_return, max_drawdown, calmar_ratio
)
max_combinations: int = 1000
use_gpu: bool = True
parallel_cores: int = -1 # -1表示使用所有核心

show_progress: bool = True
save_intermediate: bool = True
output_dir: str = "optimization_results"

use_vectorbt_opt: bool = True
multi_objective: bool = False
objectives: List[str] = None

def __post_init__self:
if self.objectives is None:    self.objectives = ["sharpe_ratio", "max_drawdown", "total_return"]
if self.parallel_cores == -1:    self.parallel_cores = mp.cpu_count()

@dataclass
class OptimizationResult:
"""優化結果"""

symbol: str
strategy: str
optimization_config: OptimizationConfig

total_combinations: int
successful_combinations: int
optimization_time: float

best_parameters: Dict[str, Any]
best_performance: Dict[str, float]

# 所有結果（前N個）
top_results: List[Dict[str, Any]]

performance_statistics: Dict[str, float]

timestamp: str
optimization_method: str
gpu_accelerated: bool

def to_dictself -> Dict[str, Any]:
"""轉換為字典"""
return asdictself

class ProgressTracker:
"""進度追蹤器"""

def __init__self, total_tasks: int, show_progress: bool = True:    self.total_tasks = total_tasks
self.completed_tasks = 0
self.start_time = time.time()
self.show_progress = show_progress and TQDM_AVAILABLE
self.progress_bar = None
self.status_queue = queue.Queue()

if self.show_progress:    self.progress_bar = tqdm(
total = total_tasks,
desc="優化進度",
unit="組合",
bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
)

def updateself, increment: int = 1:
"""更新進度"""
self.completed_tasks += increment
if self.progress_bar:
self.progress_bar.updateincrement

def closeself:
"""關閉進度條"""
if self.progress_bar:
self.progress_bar.close()

def get_statusself -> Dict[str, Any]:
"""獲取當前狀態"""
elapsed = time.time() - self.start_time
progress_pct = (
self.completed_tasks / self.total_tasks00
if self.total_tasks > 0
else 0
)

if self.completed_tasks > 0:    avg_time_per_task = elapsed / self.completed_tasks
remaining_tasks = self.total_tasks - self.completed_tasks
eta_seconds = avg_time_per_task * remaining_tasks
eta = str(inteta_seconds // 60) + "m " + str(inteta_seconds % 60) + "s"
else:    eta = "N / A"

return {
"completed": self.completed_tasks,
"total": self.total_tasks,
"progress_pct": progress_pct,
"elapsed_time": str(intelapsed // 60)
+ "m "
+ str(intelapsed % 60)
+ "s",
"eta": eta,
"tasks_per_second": self.completed_tasks / elapsed if elapsed > 0 else 0,
}

class ParameterOptimizer:
"""參數優化器主類"""

def __init__self, config: Optional[OptimizationConfig] = None:
"""
初始化優化器

Args:
config: 優化配置
"""
self.config = config or OptimizationConfig()

self._init_system_components()

self.output_dir = Pathself.config.output_dir
self.output_dir.mkdirexist_ok = True

self._init_optimization_engine()

logger.infof"Parameter Optimizer initialized for {self.config.symbol}"

def _init_system_componentsself:
"""初始化系統組件"""
try:

self.config_manager = ConfigManager()

self.dependency_manager = DependencyManager()

# 檢查GPU可用性
self.gpu_available = (
self.config.use_gpu and self.dependency_manager.gpu_available
)

# 檢查VectorBT可用性
self.vectorbt_available = self.dependency_manager.vectorbt_available

logger.infof"GPU Available: {self.gpu_available}"
logger.infof"VectorBT Available: {self.vectorbt_available}"

except Exception as e:
logger.errorf"System components initialization failed: {e}"

self.gpu_available = False
self.vectorbt_available = False

def _init_optimization_engineself:
"""初始化優化引擎"""
try:
# VectorBT引擎配置
backtest_config = {
"initial_cash": 100000.0,
"fees": 0.001,
"slippage": 0.0005,
"risk_free_rate": 0.03,
}

self.vbt_engine = VectorBTEngineuse_gpu = self.gpu_available

logger.info"VectorBT engine initialized successfully"

except Exception as e:
logger.errorf"Optimization engine initialization failed: {e}"
self.vbt_engine = None

def get_parameter_rangesself, strategy: str -> Dict[str, Union[List, range]]:
"""
獲取策略的參數範圍

Args:
strategy: 策略名稱

Returns:
參數範圍字典
"""
parameter_ranges = {
"RSI_MEAN_REVERSION": {
"period": range5, 51, 2,
"oversold": [20, 25, 30, 35, 40],
"overbought": [60, 65, 70, 75, 80],
},
"MACD_CROSSOVER": {
"fast": range5, 21, 2,
"slow": range21, 41, 3,
"signal": range5, 16, 2,
},
"BOLLINGER_BANDS": {
"period": range10, 31, 2,
"std_dev": [1.5, 2.0, 2.5, 3.0],
},
"DUAL_MOVING_AVERAGE": {
"short_period": range5, 21, 2,
"long_period": range21, 61, 4,
},
"MOMENTUM_BREAKOUT": {
"lookback": range5, 31, 3,
"threshold": [0.01, 0.015, 0.02, 0.025, 0.03],
},
"VOLATILITY_BREAKOUT": {
"atr_period": range10, 26, 2,
"multiplier": [1.5, 2.0, 2.5, 3.0, 3.5],
},
}

return parameter_ranges.getstrategy, {}

def run_optimization(
self,
symbol: Optional[str] = None,
strategy: Optional[str] = None,
param_ranges: Optional[Dict[str, Union[List, range]]] = None,
) -> OptimizationResult:
"""
運行參數優化

Args:
symbol: 股票代碼
strategy: 策略名稱
param_ranges: 參數範圍

Returns:
優化結果
"""
# 使用配置或傳入的參數
symbol = symbol or self.config.symbol
strategy = strategy or self.config.strategy
param_ranges = param_ranges or self.get_parameter_rangesstrategy

logger.infof"Starting optimization for {symbol} - {strategy}"

data = self._get_market_datasymbol, self.config.duration
if data is None or lendata == 0:
raise ValueErrorf"Failed to get market data for {symbol}"

if self.config.multi_objective:    result = self._run_multi_objective_optimization(
data, strategy, param_ranges, symbol
)
else:    result = self._run_single_objective_optimization(
data, strategy, param_ranges, symbol
)

self._save_resultsresult

logger.info"Optimization completed successfully"
return result

def _run_single_objective_optimization(
self,
data: pd.DataFrame,
strategy: str,
param_ranges: Dict[str, Union[List, range]],
symbol: str,
) -> OptimizationResult:
"""運行單目標優化"""
start_time = time.time()

if self.vectorbt_available and self.config.use_vectorbt_opt:    optimization_result = self.vbt_engine.optimize_parameters(
data = data,
strategy = strategy,
param_ranges = param_ranges,
symbol = symbol,
optimization_metric = self.config.optimization_metric,
max_combinations = self.config.max_combinations,
use_vectorbt_opt = True,
)
else:    optimization_result = self.vbt_engine.optimize_parameters(
data = data,
strategy = strategy,
param_ranges = param_ranges,
symbol = symbol,
optimization_metric = self.config.optimization_metric,
max_combinations = self.config.max_combinations,
use_vectorbt_opt = False,
)

optimization_time = time.time() - start_time

result = OptimizationResult(
symbol = symbol,
strategy = strategy,
optimization_config = self.config,
total_combinations = optimization_result.get"total_combinations", 0,
successful_combinations = optimization_result.get(
"successful_combinations", 0
),
optimization_time = optimization_time,
best_parameters = optimization_result.get"best_parameters", {},
best_performance = optimization_result.get"best_performance", {},
top_results = optimization_result.get"all_results", [][:10],
performance_statistics = optimization_result.get(
"performance_statistics", {}
),
timestamp = datetime.now().isoformat(),
optimization_method = optimization_result.get(
"optimization_method", "Unknown"
),
gpu_accelerated = self.gpu_available,
)

return result

def _run_multi_objective_optimization(
self,
data: pd.DataFrame,
strategy: str,
param_ranges: Dict[str, Union[List, range]],
symbol: str,
) -> OptimizationResult:
"""運行多目標優化"""
start_time = time.time()

if self.vbt_engine:    optimization_result = self.vbt_engine.multi_objective_optimize(
data = data,
strategy = strategy,
param_ranges = param_ranges,
symbol = symbol,
objectives = self.config.objectives,
use_vectorbt_opt = self.config.use_vectorbt_opt,
)
else:
# 降級到單目標優化
logger.warning(
"Multi - objective optimization not available, falling back to single objective"
)
return self._run_single_objective_optimization(
data, strategy, param_ranges, symbol
)

optimization_time = time.time() - start_time

best_compromise = optimization_result.get"best_compromise", {}
solution = best_compromise.get"solution", {}

result = OptimizationResult(
symbol = symbol,
strategy = strategy,
optimization_config = self.config,
total_combinations = optimization_result.get(
"total_optimization_time", 0
), # 這裡需要調整
successful_combinations = len(optimization_result.get"pareto_frontier", []),
optimization_time = optimization_time,
best_parameters = solution.get"parameters", {},
best_performance = solution.get"objectives", {},
top_results = optimization_result.get"pareto_frontier", [][:10],
performance_statistics = best_compromise,
timestamp = datetime.now().isoformat(),
optimization_method = optimization_result.get(
"optimization_method", "Multi - Objective"
),
gpu_accelerated = self.gpu_available,
)

return result

def _get_market_dataself, symbol: str, duration: int -> Optional[pd.DataFrame]:
"""獲取市場數據"""
try:
# 首先嘗試從simplified_system獲取數據
data = get_hk_stock_datasymbol, duration

if data is not None and lendata > 0:
logger.info(
f"Successfully retrieved {lendata} data points for {symbol}"
)
return data
else:
logger.warningf"No data retrieved from simplified_system for {symbol}"

# 可以在這裡添加備用數據源
return None

except Exception as e:
logger.errorf"Failed to get market data for {symbol}: {e}"
return None

def _save_resultsself, result: OptimizationResult:
"""保存優化結果"""
try:

timestamp = datetime.now().strftime"%Y%m%d_%H%M%S"
filename = f"{result.symbol}_{result.strategy}_{timestamp}.json"
filepath = self.output_dir / filename

result_dict = result.to_dict()
with openfilepath, "w", encoding="utf - 8" as f:    json.dump(result_dict, f, ensure_ascii = False, indent = 2, default = str)

logger.infof"Results saved to {filepath}"

# 同時保存最新結果
latest_filepath = (
self.output_dir / f"latest_{result.symbol}_{result.strategy}.json"
)
with openlatest_filepath, "w", encoding="utf - 8" as f:    json.dump(result_dict, f, ensure_ascii = False, indent = 2, default = str)

except Exception as e:
logger.errorf"Failed to save results: {e}"

def load_resultsself, filepath: str -> Optional[OptimizationResult]:
"""加載優化結果"""
try:    with open(filepath, "r", encoding="utf - 8") as f:
result_dict = json.loadf

# 重構OptimizationConfig
if "optimization_config" in result_dict:    config_dict = result_dict["optimization_config"]
config = OptimizationConfig**config_dict
result_dict["optimization_config"] = config

result = OptimizationResult**result_dict
logger.infof"Results loaded from {filepath}"
return result

except Exception as e:
logger.errorf"Failed to load results from {filepath}: {e}"
return None

def display_resultsself, result: OptimizationResult, detailed: bool = True:
"""顯示優化結果"""
printf"\n{'='*80}"
printf"🎯 參數優化結果報告 / PARAMETER OPTIMIZATION REPORT"
printf"{'='*80}"

printf"📊 股票代碼: {result.symbol}"
printf"🔧 策略名稱: {result.strategy}"
printf"⏱️ 優化時間: {result.optimization_time:.2f}秒"
print(
f"🔢 測試組合: {result.successful_combinations}/{result.total_combinations}"
)
printf"🚀 加速方式: {'GPU' if result.gpu_accelerated else 'CPU'}"
printf"📅 優化時間: {result.timestamp}"

printf"\n🏆 最佳參數組合:"
if result.best_parameters:
for param, value in result.best_parameters.items():
printf" • {param}: {value}"
else:
print" • 無可用參數"

printf"\n📈 最佳性能指標:"
if result.best_performance:
for metric, value in result.best_performance.items():
if metric in ["sharpe_ratio", "sortino_ratio", "calmar_ratio"]:
printf" • {metric}: {value:.3f}"
elif metric in ["total_return", "max_drawdown", "annual_return"]:
printf" • {metric}: {value:.2%}"
else:
printf" • {metric}: {value}"
else:
print" • 無可用性能數據"

if detailed:

printf"\n🔝 前5個最佳結果:"
if result.top_results and lenresult.top_results > 0:    table_data = []
headers = ["排名", "參數", f"{self.config.optimization_metric}"]

for i, item in enumerateresult.top_results[:5], 1:    params_str = ", ".join(
[f"{k}={v}" for k, v in item.get"parameters", {}.items()]
)
metric_value = item.get"metric", 0

if self.config.optimization_metric in [
"sharpe_ratio",
"sortino_ratio",
"calmar_ratio",
]:    metric_str = f"{metric_value:.3f}"
elif self.config.optimization_metric in [
"total_return",
"max_drawdown",
]:    metric_str = f"{metric_value:.2%}"
else:    metric_str = str(metric_value)

table_data.append[i, params_str, metric_str]

if TABULATE_AVAILABLE:    print(tabulate(table_data, headers = headers, tablefmt="grid"))
else:
for row in table_data:
printf" {row[0]}. {row[1]} -> {row[2]}"
else:
print" • 無可用結果數據"

printf"\n📊 性能統計:"
if result.performance_statistics:
for stat, value in result.performance_statistics.items():
printf" • {stat}: {value:.4f}"
else:
print" • 無可用統計數據"

printf"\n{'='*80}"

def compare_strategies(
self,
symbol: str,
strategies: List[str],
param_ranges: Optional[Dict[str, Dict[str, Union[List, range]]]] = None,
) -> Dict[str, OptimizationResult]:
"""
比較多個策略的優化結果

Args:
symbol: 股票代碼
strategies: 策略列表
param_ranges: 每個策略的參數範圍

Returns:
策略比較結果
"""
results = {}

printf"\n🔄 開始多策略比較優化..."
printf"股票: {symbol}"
print(f"策略: {', '.joinstrategies}")

for strategy in strategies:
printf"\n🔧 正在優化策略: {strategy}"

# 獲取策略參數範圍
strategy_params = None
if param_ranges and strategy in param_ranges:    strategy_params = param_ranges[strategy]
else:    strategy_params = self.get_parameter_ranges(strategy)

try:    result = self.run_optimization(symbol, strategy, strategy_params)
results[strategy] = result

print(
f" ✅ 完成 - 最佳Sharpe: {result.best_performance.get'sharpe_ratio', 'N / A':.3f}"
)

except Exception as e:
logger.errorf"Failed to optimize strategy {strategy}: {e}"
print(f" ❌ 失敗 - {stre}")

self._display_strategy_comparisonresults

return results

def _display_strategy_comparisonself, results: Dict[str, OptimizationResult]:
"""顯示策略比較結果"""
printf"\n{'='*80}"
printf"📊 策略比較結果 / STRATEGY COMPARISON RESULTS"
printf"{'='*80}"

if not results:
print" • 無可用比較結果"
return

table_data = []
headers = [
"策略",
"最佳Sharpe",
"總回報",
"最大回撤",
"交易次數",
"優化時間秒",
]

for strategy, result in results.items():    perf = result.best_performance
sharpe = perf.get"sharpe_ratio", 0
total_return = perf.get"total_return", 0
max_dd = perf.get"max_drawdown", 0
trades = perf.get"total_trades", 0
opt_time = result.optimization_time

table_data.append(
[
strategy,
f"{sharpe:.3f}",
f"{total_return:.2%}",
f"{max_dd:.2%}",
strtrades,
f"{opt_time:.2f}",
]
)

if TABULATE_AVAILABLE:    print(tabulate(table_data, headers = headers, tablefmt="grid"))
else:
for row in table_data:
print(f" {' | '.joinrow}")

best_strategy = max(
results.items(), key = lambda x: x[1].best_performance.get"sharpe_ratio", 0
)
print(
f"\n🏆 最佳策略: {best_strategy[0]} (Sharpe: {best_strategy[1].best_performance.get'sharpe_ratio', 0:.3f})"
)
printf"{'='*80}"

def quick_optimize(
symbol: str = "0700.HK",
strategy: str = "RSI_MEAN_REVERSION",
max_combinations: int = 500,
) -> OptimizationResult:
"""
快速優化便利函數

Args:
symbol: 股票代碼
strategy: 策略名稱
max_combinations: 最大組合數

Returns:
優化結果
"""
config = OptimizationConfig(
symbol = symbol,
strategy = strategy,
max_combinations = max_combinations,
show_progress = True,
save_intermediate = True,
)

optimizer = ParameterOptimizerconfig
result = optimizer.run_optimization()
optimizer.display_resultsresult

return result

def compare_all_strategiessymbol: str = "0700.HK" -> Dict[str, OptimizationResult]:
"""
比較所有策略便利函數

Args:
symbol: 股票代碼

Returns:
策略比較結果
"""
strategies = [
"RSI_MEAN_REVERSION",
"MACD_CROSSOVER",
"BOLLINGER_BANDS",
"DUAL_MOVING_AVERAGE",
"MOMENTUM_BREAKOUT",
"VOLATILITY_BREAKOUT",
]

optimizer = ParameterOptimizer()
return optimizer.compare_strategiessymbol, strategies
