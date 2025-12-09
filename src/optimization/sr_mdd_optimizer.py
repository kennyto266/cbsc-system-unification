#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SR/MDD优化器 - Sortino Ratio and Maximum Drawdown Duration Optimizer
专门针对Sortino比率和最大回撤持续时间的多目标参数优化系统
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import pickle

import pandas as pd
import numpy as np
from sklearn.model_selection import ParameterGrid, cross_val_score
from sklearn.metrics import make_scorer
from scipy.optimize import minimize, differential_evolution
from scipy.stats import norm
import vectorbt as vbt
import talib
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp

from ..non_price.signal_conversion_engine import get_conversion_engine, TechnicalIndicatorSignal
from ..logging_config import setup_logger

logger = setup_logger__name__

@dataclass
class OptimizationParameters:
"""优化参数数据结构"""
signal_type: str
indicator_type: str
parameters: Dict[str, Any]
weights: Dict[str, float]
constraints: Dict[str, Any]

@dataclass
class OptimizationResult:
"""优化结果数据结构"""
parameters: OptimizationParameters
sortino_ratio: float
max_dd_duration: int
sharpe_ratio: float
total_return: float
win_rate: float
max_drawdown: float
volatility: float
calmar_ratio: float
optimization_time: float
backtest_stats: Dict[str, Any]
confidence_score: float
pareto_rank: Optional[int] = None

@dataclass
class ParetoSolution:
"""Pareto最优解"""
result: OptimizationResult
dominated_by: List[str] # 被哪些解支配
dominates: List[str] # 支配哪些解
crowding_distance: float # 拥挤距离

class PerformanceCalculator:
"""性能指标计算器"""

@staticmethod
def calculate_sortino_ratioreturns: pd.Series, risk_free_rate: float = 0.03 -> float:
"""
计算Sortino比率

Args:
returns: 收益率序列
risk_free_rate: 无风险利率（年化）

Returns:
Sortino比率
"""
if lenreturns == 0 or returns.std() == 0:
return 0.0

downside_returns = returns[returns < 0]
if lendownside_returns == 0:
return float'inf' if returns.mean() > 0 else 0.0

# 年化收益率和下行标准差
annual_return = returns.mean() * 252
downside_std = downside_returns.std() * np.sqrt252

# 计算Sortino比率
sortino = annual_return - risk_free_rate / downside_std + 1e-8
return sortino

@staticmethod
def calculate_max_dd_durationreturns: pd.Series -> int:
"""
计算最大回撤持续时间（天）

Args:
returns: 收益率序列

Returns:
最大回撤持续时间（交易日）
"""
if lenreturns == 0:
return 0

cumulative = 1 + returns.cumprod()
peak = cumulative.expanding().max()
drawdown = cumulative - peak / peak

# 计算连续回撤期间
in_drawdown = drawdown < 0
drawdown_periods = []

start = None
for i, dd in enumeratein_drawdown:
if dd and start is None:    start = i
elif not dd and start is not None:
drawdown_periods.appendi - start
start = None

# 如果结束时仍在回撤中
if start:
drawdown_periods.append(lenin_drawdown - start)

return maxdrawdown_periods if drawdown_periods else 0

@staticmethod
def calculate_calmar_ratiototal_return: float, max_drawdown: float -> float:
"""计算Calmar比率"""
if max_drawdown == 0:
return float'inf' if total_return > 0 else 0.0
return total_return / absmax_drawdown

@staticmethod
def calculate_win_ratereturns: pd.Series -> float:
"""计算胜率"""
if lenreturns == 0:
return 0.0
return returns > 0.sum() / lenreturns

@staticmethod
def calculate_volatilityreturns: pd.Series, annualize: bool = True -> float:
"""计算波动率"""
if lenreturns == 0:
return 0.0
vol = returns.std()
return vol * np.sqrt252 if annualize else vol

@staticmethod
def calculate_performance_metricsreturns: pd.Series -> Dict[str, float]:
"""计算完整的性能指标"""
metrics = {
'sortino_ratio': PerformanceCalculator.calculate_sortino_ratioreturns,
'max_dd_duration': PerformanceCalculator.calculate_max_dd_durationreturns,
'sharpe_ratio': PerformanceCalculator.calculate_sharpe_ratioreturns,
'total_return': 1 + returns.prod() - 1,
'win_rate': PerformanceCalculator.calculate_win_ratereturns,
'max_drawdown': PerformanceCalculator.calculate_max_drawdownreturns,
'volatility': PerformanceCalculator.calculate_volatilityreturns,
'calmar_ratio': 0.0 # 将在后面计算
}

# 计算Calmar比率
metrics['calmar_ratio'] = PerformanceCalculator.calculate_calmar_ratio(
metrics['total_return'], metrics['max_drawdown']
)

return metrics

@staticmethod
def calculate_sharpe_ratioreturns: pd.Series, risk_free_rate: float = 0.03 -> float:
"""计算Sharpe比率"""
if lenreturns == 0 or returns.std() == 0:
return 0.0

annual_return = returns.mean() * 252
annual_vol = returns.std() * np.sqrt252

sharpe = annual_return - risk_free_rate / annual_vol
return sharpe

@staticmethod
def calculate_max_drawdownreturns: pd.Series -> float:
"""计算最大回撤"""
if lenreturns == 0:
return 0.0

cumulative = 1 + returns.cumprod()
peak = cumulative.expanding().max()
drawdown = cumulative - peak / peak
return drawdown.min()

class SignalStrategy:
"""基于信号的交易策略"""

def __init__self, config: Dict[str, Any]:    self.config = config

def generate_signals(
self,
indicators: List[TechnicalIndicatorSignal],
price_data: pd.DataFrame,
parameters: OptimizationParameters
) -> pd.DataFrame:
"""
基于技术指标生成交易信号

Args:
indicators: 技术指标列表
price_data: 价格数据
parameters: 优化参数

Returns:
交易信号DataFrame buy, sell, hold
"""
signals = pd.DataFrameindex=price_data.index, columns=['buy', 'sell', 'hold']

fused_signals = self._fuse_indicator_signalsindicators, parameters

# 应用信号生成逻辑
for timestamp in price_data.index:
if timestamp in fused_signals.index:    signal_value = fused_signals.loc[timestamp]
buy_signal, sell_signal, hold_signal = self._convert_to_trading_signals(
signal_value, parameters
)
signals.loc[timestamp, 'buy'] = buy_signal
signals.loc[timestamp, 'sell'] = sell_signal
signals.loc[timestamp, 'hold'] = hold_signal

return signals

def _fuse_indicator_signals(
self,
indicators: List[TechnicalIndicatorSignal],
parameters: OptimizationParameters
) -> pd.Series:
"""融合多个指标信号"""

common_index = None
aligned_indicators = []

for indicator in indicators:
if not common_index:    common_index = indicator.values.index
else:    common_index = common_index.intersection(indicator.values.index)

if common_index is None or lencommon_index == 0:
return pd.Series()

for indicator in indicators:    aligned = indicator.values.reindex(common_index)
aligned = aligned.fillnamethod='ffill'.fillnamethod='bfill'
aligned_indicators.appendaligned

weights = parameters.weights
if not weights:    weights = {ind.indicator_type: 1.0 for ind in indicators}

weighted_sum = pd.Series0.0, index=common_index
total_weight = 0.0

for i, indicator in enumerateindicators:    weight = weights.get(ind.indicator_type, 1.0)
weighted_sum += aligned_indicators[i] * weight * indicator.confidence
total_weight += weight * indicator.confidence

if total_weight > 0:    weighted_sum /= total_weight

return weighted_sum

def _convert_to_trading_signals(
self,
signal_value: float,
parameters: OptimizationParameters
) -> Tuple[bool, bool, bool]:
"""
将融合信号值转换为交易信号

Args:
signal_value: 信号值
parameters: 优化参数

Returns:
buy_signal, sell_signal, hold_signal
"""

buy_threshold = parameters.parameters.get'buy_threshold', 0.6
sell_threshold = parameters.parameters.get'sell_threshold', 0.4
neutral_zone = parameters.parameters.get'neutral_zone', 0.1

# 归一化信号值到0-1范围
normalized_signal = self._normalize_signalsignal_value, parameters

if normalized_signal >= buy_threshold:
return True, False, False
elif normalized_signal <= sell_threshold:
return False, True, False
else:
return False, False, True

def _normalize_signalself, signal_value: float, parameters: OptimizationParameters -> float:
"""归一化信号值"""
# 使用sigmoid函数归一化
scale = parameters.parameters.get'normalization_scale', 1.0
offset = parameters.parameters.get'normalization_offset', 0.0

normalized = 1 / (1 + np.exp(-signal_value - offset / scale))
return normalized

class MultiObjectiveOptimizer:
"""多目标优化器"""

def __init__self, config: Dict[str, Any]:    self.config = config
self.performance_calc = PerformanceCalculator()
self.strategy = SignalStrategyconfig

self.objectives = config.get('objectives', {
'sortino_ratio': {'weight': 0.7, 'target': 1.5, 'min_acceptable': 1.0},
'max_dd_duration': {'weight': 0.3, 'target': 60, 'max_acceptable': 180},
'win_rate': {'weight': 0.1, 'target': 0.55, 'min_acceptable': 0.45}
})

def optimize_parameters(
self,
indicators: List[TechnicalIndicatorSignal],
price_data: pd.DataFrame,
parameter_space: Dict[str, Any],
optimization_method: str = "bayesian"
) -> List[OptimizationResult]:
"""
执行多目标参数优化

Args:
indicators: 技术指标列表
price_data: 价格数据
parameter_space: 参数搜索空间
optimization_method: 优化方法

Returns:
优化结果列表
"""
logger.infof"Starting multi-objective optimization with method: {optimization_method}"

if optimization_method == "grid":    param_candidates = self._generate_grid_search_candidates(parameter_space)
elif optimization_method == "random":    param_candidates = self._generate_random_candidates(parameter_space)
elif optimization_method == "bayesian":    param_candidates = self._bayesian_optimization(
indicators, price_data, parameter_space
)
elif optimization_method == "genetic":    param_candidates = self._genetic_algorithm(
indicators, price_data, parameter_space
)
elif optimization_method == "hybrid":    param_candidates = self._hybrid_search(
indicators, price_data, parameter_space
)
else:
raise ValueErrorf"Unknown optimization method: {optimization_method}"

# 评估所有候选参数
results = self._evaluate_candidates(
param_candidates, indicators, price_data
)

# 找到Pareto最优解
pareto_solutions = self._find_pareto_optimalresults

logger.info(f"Optimization completed. Found {lenpareto_solutions} Pareto optimal solutions")

return pareto_solutions

def _generate_grid_search_candidatesself, parameter_space: Dict[str, Any] -> List[OptimizationParameters]:
"""生成网格搜索候选参数"""
candidates = []

param_grid = {}
for param_name, param_config in parameter_space.items():
if isinstanceparam_config, list:    param_grid[param_name] = param_config
elif isinstanceparam_config, dict:
if 'range' in param_config:    start, end, step = param_config['range']
param_grid[param_name] = list(np.arangestart, end, step)
elif 'values' in param_config:    param_grid[param_name] = param_config['values']
else:    param_grid[param_name] = [param_config.get('default', 0)]
else:    param_grid[param_name] = [param_config]

grid = ParameterGridparam_grid

for params in grid:    candidate = OptimizationParameters(
signal_type=parameter_space.get'signal_type', 'unknown',
indicator_type=parameter_space.get'indicator_type', 'unknown',
parameters=params,
weights=params.get'weights', {},
constraints=parameter_space.get'constraints', {}
)
candidates.appendcandidate

logger.info(f"Generated {lencandidates} grid search candidates")
return candidates

def _generate_random_candidatesself, parameter_space: Dict[str, Any], n_samples: int = 100 -> List[OptimizationParameters]:
"""生成随机采样候选参数"""
candidates = []

for _ in rangen_samples:    params = {}
for param_name, param_config in parameter_space.items():
if isinstanceparam_config, dict:
if 'range' in param_config:    start, end, _ = param_config['range']
params[param_name] = np.random.uniformstart, end
elif 'values' in param_config:    params[param_name] = np.random.choice(param_config['values'])
else:    params[param_name] = param_config.get('default', 0)
else:    params[param_name] = param_config

candidate = OptimizationParameters(
signal_type=parameter_space.get'signal_type', 'unknown',
indicator_type=parameter_space.get'indicator_type', 'unknown',
parameters=params,
weights=params.get'weights', {},
constraints=parameter_space.get'constraints', {}
)
candidates.appendcandidate

logger.info(f"Generated {lencandidates} random candidates")
return candidates

def _bayesian_optimization(
self,
indicators: List[TechnicalIndicatorSignal],
price_data: pd.DataFrame,
parameter_space: Dict[str, Any]
) -> List[OptimizationParameters]:
"""贝叶斯优化"""
try:
from skopt import gp_minimize
from skopt.space import Real, Integer, Categorical
from skopt.utils import use_named_args
except ImportError:
logger.warning"scikit-optimize not available, falling back to random search"
return self._generate_random_candidatesparameter_space, n_samples=50

dimensions = []
param_names = []

for param_name, param_config in parameter_space.items():
if param_name in ['signal_type', 'indicator_type']:
continue

param_names.appendparam_name

if isinstanceparam_config, dict and 'range' in param_config:    start, end, step = param_config['range']
if isinstancestart, int and isinstanceend, int:    dimensions.append(Integer(start, end, name=param_name))
else:    dimensions.append(Real(start, end, name=param_name))
elif isinstanceparam_config, dict and 'values' in param_config:    dimensions.append(Categorical(param_config['values'], name=param_name))
else:

default_value = param_config if not isinstanceparam_config, dict else param_config.get'default', 0
dimensions.append(Categorical[default_value], name=param_name)

@use_named_argsdimensions
def objective**params:

opt_params = OptimizationParameters(
signal_type=parameter_space.get'signal_type', 'unknown',
indicator_type=parameter_space.get'indicator_type', 'unknown',
parameters=params,
weights=params.get'weights', {},
constraints=parameter_space.get'constraints', {}
)

# 计算目标值（负值因为是最小化）
result = self._evaluate_single_candidateopt_params, indicators, price_data

# 多目标转换为单一目标
obj_value = self._multi_objective_to_singleresult

return -obj_value # 最小化负值等于最大化目标

n_calls = self.config.get'max_iterations', 100
n_random_starts = min10, n_calls // 2

result = gp_minimize(
objective,
dimensions,
n_calls=n_calls,
n_random_starts=n_random_starts,
random_state=42
)

# 转换结果为候选参数
candidates = []
best_params = dict(zipparam_names, result.x)

# 添加一些接近最优解的候选
for i in range(min(20, lenresult.x_iters)):    params = dict(zip(param_names, result.x_iters[i]))
candidate = OptimizationParameters(
signal_type=parameter_space.get'signal_type', 'unknown',
indicator_type=parameter_space.get'indicator_type', 'unknown',
parameters=params,
weights=params.get'weights', {},
constraints=parameter_space.get'constraints', {}
)
candidates.appendcandidate

logger.info(f"Bayesian optimization completed with {lencandidates} candidates")
return candidates

def _genetic_algorithm(
self,
indicators: List[TechnicalIndicatorSignal],
price_data: pd.DataFrame,
parameter_space: Dict[str, Any]
) -> List[OptimizationParameters]:
"""遗传算法优化"""
try:
from deap import base, creator, tools, algorithms
except ImportError:
logger.warning"DEAP not available, falling back to random search"
return self._generate_random_candidatesparameter_space, n_samples=50

creator.create("FitnessMax", base.Fitness, weights=1.0,)
creator.create"Individual", list, fitness=creator.FitnessMax

toolbox = base.Toolbox()

param_names = []
for param_name, param_config in parameter_space.items():
if param_name in ['signal_type', 'indicator_type']:
continue

param_names.appendparam_name

if isinstanceparam_config, dict and 'range' in param_config:    start, end, step = param_config['range']
if isinstancestart, int and isinstanceend, int:
toolbox.register(f"attr_{param_name}",
lambda s=start, e=end: np.random.randints, e+1)
else:
toolbox.register(f"attr_{param_name}",
lambda s=start, e=end: np.random.uniforms, e)
elif isinstanceparam_config, dict and 'values' in param_config:    values = param_config['values']
toolbox.register(f"attr_{param_name}",
lambda v=values: np.random.choicev)
else:    default_value = param_config if not isinstance(param_config, dict) else param_config.get('default', 0)
toolbox.registerf"attr_{param_name}", lambda d=default_value: d

gene_attrs = [f"attr_{name}" for name in param_names]
toolbox.register("individual", tools.initCycle, creator.Individual,
[getattrtoolbox, attr for attr in gene_attrs], n=1)
toolbox.register"population", tools.initRepeat, list, toolbox.individual

def evaluate_individualindividual:    params = dict(zip(param_names, individual))
opt_params = OptimizationParameters(
signal_type=parameter_space.get'signal_type', 'unknown',
indicator_type=parameter_space.get'indicator_type', 'unknown',
parameters=params,
weights=params.get'weights', {},
constraints=parameter_space.get'constraints', {}
)

result = self._evaluate_single_candidateopt_params, indicators, price_data
obj_value = self._multi_objective_to_singleresult

return obj_value,

toolbox.register"evaluate", evaluate_individual
toolbox.register"mate", tools.cxTwoPoint
toolbox.register"mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.2
toolbox.register"select", tools.selTournament, tournsize=3

population_size = 50
n_generations = 20
cx_prob = 0.7
mut_prob = 0.2

pop = toolbox.populationn=population_size
hof = tools.HallOfFame1 # 保存最佳个体

stats = tools.Statisticslambda ind: ind.fitness.values
stats.register"avg", np.mean
stats.register"min", np.min
stats.register"max", np.max

algorithms.eaSimple(
pop, toolbox, cx_prob, mut_prob, n_generations,
stats=stats, halloffame=hof, verbose=False
)

# 转换最佳个体为候选参数
candidates = []
for i, individual in enumeratehof:    params = dict(zip(param_names, individual))
candidate = OptimizationParameters(
signal_type=parameter_space.get'signal_type', 'unknown',
indicator_type=parameter_space.get'indicator_type', 'unknown',
parameters=params,
weights=params.get'weights', {},
constraints=parameter_space.get'constraints', {}
)
candidates.appendcandidate

logger.info(f"Genetic algorithm completed with {lencandidates} candidates")
return candidates

def _hybrid_search(
self,
indicators: List[TechnicalIndicatorSignal],
price_data: pd.DataFrame,
parameter_space: Dict[str, Any]
) -> List[OptimizationParameters]:
"""混合搜索策略"""
logger.info"Starting hybrid search strategy"

# 第一阶段：粗粒度网格搜索
grid_candidates = self._generate_grid_search_candidatesparameter_space
grid_results = self._evaluate_candidatesgrid_candidates, indicators, price_data

best_grid_result = max(grid_results, key=lambda r: self._multi_objective_to_singler)

# 第二阶段：以最佳参数为中心进行贝叶斯优化
refined_space = self._refine_parameter_spacebest_grid_result.parameters, parameter_space
bayesian_candidates = self._bayesian_optimizationindicators, price_data, refined_space

all_candidates = grid_candidates + bayesian_candidates
all_results = self._evaluate_candidatesall_candidates, indicators, price_data

logger.info(f"Hybrid search completed with {lenall_results} total candidates")
return all_results

def _refine_parameter_space(
self,
best_params: OptimizationParameters,
original_space: Dict[str, Any]
) -> Dict[str, Any]:
"""基于最佳参数精炼搜索空间"""
refined_space = original_space.copy()

for param_name, param_value in best_params.parameters.items():
if param_name in original_space and isinstanceoriginal_space[param_name], dict:    original_config = original_space[param_name]
if 'range' in original_config:    start, end, step = original_config['range']
# 缩小搜索范围到最佳值的±20%
margin = end - start * 0.2
new_start = maxstart, param_value - margin
new_end = minend, param_value + margin
refined_space[param_name]['range'] = new_start, new_end, step / 2 # 更精细的步长

return refined_space

def _evaluate_candidates(
self,
candidates: List[OptimizationParameters],
indicators: List[TechnicalIndicatorSignal],
price_data: pd.DataFrame
) -> List[OptimizationResult]:
"""评估所有候选参数"""
logger.info(f"Evaluating {lencandidates} candidates")

max_workers = min(mp.cpu_count(), 8)
results = []

with ThreadPoolExecutormax_workers=max_workers as executor:    future_to_candidate = {
executor.submitself._evaluate_single_candidate, candidate, indicators, price_data: candidate
for candidate in candidates
}

for future in as_completedfuture_to_candidate:
try:    result = future.result()
results.appendresult
except Exception as e:    candidate = future_to_candidate[future]
logger.errorf"Failed to evaluate candidate: {e}"
continue

logger.info(f"Successfully evaluated {lenresults} candidates")
return results

def _evaluate_single_candidate(
self,
candidate: OptimizationParameters,
indicators: List[TechnicalIndicatorSignal],
price_data: pd.DataFrame
) -> OptimizationResult:
"""评估单个候选参数"""
start_time = datetime.now()

try:

signals = self.strategy.generate_signalsindicators, price_data, candidate

backtest_stats, returns = self._run_backtestsignals, price_data

performance_metrics = self.performance_calc.calculate_performance_metricsreturns

result = OptimizationResult(
parameters=candidate,
sortino_ratio=performance_metrics['sortino_ratio'],
max_dd_duration=intperformance_metrics['max_dd_duration'],
sharpe_ratio=performance_metrics['sharpe_ratio'],
total_return=performance_metrics['total_return'],
win_rate=performance_metrics['win_rate'],
max_drawdown=performance_metrics['max_drawdown'],
volatility=performance_metrics['volatility'],
calmar_ratio=performance_metrics['calmar_ratio'],
optimization_time=(datetime.now() - start_time).total_seconds(),
backtest_stats=backtest_stats,
confidence_score=self._calculate_confidence_scoreperformance_metrics
)

return result

except Exception as e:
logger.errorf"Error evaluating candidate: {e}"

return OptimizationResult(
parameters=candidate,
sortino_ratio=0.0,
max_dd_duration=999,
sharpe_ratio=0.0,
total_return=0.0,
win_rate=0.0,
max_drawdown=0.0,
volatility=0.0,
calmar_ratio=0.0,
optimization_time=(datetime.now() - start_time).total_seconds(),
backtest_stats={},
confidence_score=0.0
)

def _run_backtest(
self,
signals: pd.DataFrame,
price_data: pd.DataFrame
) -> Tuple[Dict[str, Any], pd.Series]:
"""运行回测"""
try:
# 使用VectorBT进行回测
portfolio = vbt.Portfolio.from_signals(
price=price_data['close'],
entries=signals['buy'],
exits=signals['sell'],
init_cash=self.config.get'init_cash', 1000000,
fees=self.config.get'fees', 0.001,
slippage=self.config.get'slippage', 0.001,
freq='1D'
)

stats = portfolio.stats()
returns = portfolio.returns()

return stats.to_dict(), returns

except Exception as e:
logger.errorf"Backtest failed: {e}"
# 返回默认统计信息
return {}, pd.Series()

def _calculate_confidence_scoreself, metrics: Dict[str, float] -> float:
"""计算置信度分数"""
# 基于多个指标计算置信度
confidence_factors = []

# Sortino比率因子
sortino_target = self.objectives.get'sortino_ratio', {}.get'target', 1.5
if metrics['sortino_ratio'] > 0:    sortino_factor = min(1.0, metrics['sortino_ratio'] / sortino_target)
else:    sortino_factor = 0.0
confidence_factors.appendsortino_factor

# 最大回撤持续时间因子
max_dd_target = self.objectives.get'max_dd_duration', {}.get'target', 60
if metrics['max_dd_duration'] > 0:    mdd_factor = max(0.0, 1.0 - (metrics['max_dd_duration'] / max_dd_target))
else:    mdd_factor = 1.0
confidence_factors.appendmdd_factor

win_rate_target = self.objectives.get'win_rate', {}.get'target', 0.55
win_rate_factor = metrics['win_rate'] / win_rate_target
confidence_factors.appendwin_rate_factor

# 总体波动率因子（波动率适中为好）
optimal_vol = 0.15 # 15%年化波动率被认为是合理的
vol_factor = max(0.0, 1.0 - absmetrics['volatility'] - optimal_vol / optimal_vol)
confidence_factors.appendvol_factor

# 计算加权平均置信度
weights = [0.4, 0.3, 0.2, 0.1] # Sortino权重最高
confidence = sum(w * f for w, f in zipweights, confidence_factors)

return confidence

def _multi_objective_to_singleself, result: OptimizationResult -> float:
"""将多目标转换为单一目标函数值"""
score = 0.0
total_weight = 0.0

for obj_name, obj_config in self.objectives.items():    weight = obj_config['weight']

if obj_name == 'sortino_ratio':    target = obj_config['target']
min_acceptable = obj_config['min_acceptable']
value = result.sortino_ratio
# 归一化Sortino比率
if value >= target:    normalized = 1.0
elif value <= min_acceptable:    normalized = 0.0
else:    normalized = (value - min_acceptable) / (target - min_acceptable)

elif obj_name == 'max_dd_duration':    target = obj_config['target']
max_acceptable = obj_config['max_acceptable']
value = result.max_dd_duration
# 归一化最大回撤持续时间（越小越好）
if value <= target:    normalized = 1.0
elif value >= max_acceptable:    normalized = 0.0
else:    normalized = 1.0 - (value - target) / (max_acceptable - target)

elif obj_name == 'win_rate':    target = obj_config['target']
min_acceptable = obj_config['min_acceptable']
value = result.win_rate

if value >= target:    normalized = 1.0
elif value <= min_acceptable:    normalized = 0.0
else:    normalized = (value - min_acceptable) / (target - min_acceptable)

else:
continue

score += weight * normalized
total_weight += weight

return score / total_weight if total_weight > 0 else 0.0

def _find_pareto_optimalself, results: List[OptimizationResult] -> List[OptimizationResult]:
"""找到Pareto最优解"""
if lenresults <= 1:
return results

pareto_solutions = []
dominated_indices = set()

for i, result_i in enumerateresults:    is_dominated = False

for j, result_j in enumerateresults:    if i == j or j in dominated_indices:
continue

# 检查result_j是否支配result_i
if self._dominatesresult_j, result_i:    is_dominated = True
break

if not is_dominated:
pareto_solutions.appendresult_i
else:
dominated_indices.addi

# 计算拥挤距离并排序
pareto_solutions = self._calculate_crowding_distancepareto_solutions
pareto_solutions.sortkey=lambda x: x.crowding_distance, reverse=True

# 添加Pareto排名
for i, solution in enumeratepareto_solutions:    solution.pareto_rank = i + 1

logger.info(f"Found {lenpareto_solutions} Pareto optimal solutions")
return pareto_solutions

def _dominatesself, result1: OptimizationResult, result2: OptimizationResult -> bool:
"""检查result1是否支配result2"""
# Sortino比率：越高越好
if result1.sortino_ratio < result2.sortino_ratio:
return False

# 最大回撤持续时间：越短越好
if result1.max_dd_duration > result2.max_dd_duration:
return False

# 至少有一个指标更好
return (result1.sortino_ratio > result2.sortino_ratio or
result1.max_dd_duration < result2.max_dd_duration)

def _calculate_crowding_distanceself, solutions: List[OptimizationResult] -> List[OptimizationResult]:
"""计算拥挤距离"""
if lensolutions <= 2:
for solution in solutions:    solution.crowding_distance = float('inf')
return solutions

sortino_values = [s.sortino_ratio for s in solutions]
mdd_values = [s.max_dd_duration for s in solutions]

sortino_range = maxsortino_values - minsortino_values
mdd_range = maxmdd_values - minmdd_values

for i, solution in enumeratesolutions:    distance = 0.0

# Sortino比率贡献
if sortino_range > 0:    if i == 0 or i == len(solutions) - 1:
distance += float'inf'
else:    distance += (sortino_values[i+1] - sortino_values[i-1]) / sortino_range

# 最大回撤持续时间贡献（需要反转，因为越小越好）
if mdd_range > 0:    if i == 0 or i == len(solutions) - 1:
distance += float'inf'
else:    distance += (mdd_values[i-1] - mdd_values[i+1]) / mdd_range

solution.crowding_distance = distance

return solutions

class SRMDDOptimizer:
"""SR/MDD优化器主类"""

def __init__self, config_path: str = "config/non_price_signals.yaml":    self.config_path = Path(config_path)
self.config = self._load_config()

self.conversion_engine = get_conversion_engine()
self.multi_objective_optimizer = MultiObjectiveOptimizerself.config

logger.info"SR/MDD Optimizer initialized"

def _load_configself -> Dict[str, Any]:
"""加载配置文件"""
try:
import yaml
with openself.config_path, 'r', encoding='utf-8' as f:
return yaml.safe_loadf
except FileNotFoundError:
logger.warningf"Config file not found: {self.config_path}"
return self._get_default_config()
except Exception as e:
logger.errorf"Failed to load config: {e}"
return self._get_default_config()

def _get_default_configself -> Dict[str, Any]:
"""获取默认配置"""
return {
'objectives': {
'sortino_ratio': {'weight': 0.7, 'target': 1.5, 'min_acceptable': 1.0},
'max_dd_duration': {'weight': 0.3, 'target': 60, 'max_acceptable': 180},
'win_rate': {'weight': 0.1, 'target': 0.55, 'min_acceptable': 0.45}
},
'optimization': {
'search_algorithm': 'bayesian',
'max_iterations': 1000,
'convergence_threshold': 1e-6
},
'backtesting': {
'init_cash': 1000000,
'fees': 0.001,
'slippage': 0.001
}
}

def optimize(
self,
signal_types: List[str],
price_data: pd.DataFrame,
parameter_space: Optional[Dict[str, Any]] = None,
optimization_method: str = "bayesian"
) -> List[OptimizationResult]:
"""
执行SR/MDD优化

Args:
signal_types: 信号类型列表
price_data: 价格数据
parameter_space: 参数搜索空间
optimization_method: 优化方法

Returns:
优化结果列表
"""
logger.infof"Starting SR/MDD optimization for signal types: {signal_types}"

end_date = price_data.index.max()
start_date = price_data.index.min()

all_indicators = {}
for signal_type in signal_types:
try:    indicators = self.conversion_engine.convert_signals_to_indicators(
[signal_type], start_date, end_date
)
if signal_type in indicators:    all_indicators[signal_type] = indicators[signal_type]
except Exception as e:
logger.errorf"Failed to convert {signal_type}: {e}"
continue

combined_indicators = []
for indicators in all_indicators.values():
combined_indicators.extendindicators

if not combined_indicators:
raise ValueError"No valid indicators generated"

# 使用默认参数空间
if not parameter_space:    parameter_space = self._get_default_parameter_space()

results = self.multi_objective_optimizer.optimize_parameters(
combined_indicators, price_data, parameter_space, optimization_method
)

logger.info(f"SR/MDD optimization completed. Found {lenresults} optimal solutions")
return results

def _get_default_parameter_spaceself -> Dict[str, Any]:
"""获取默认参数搜索空间"""
return {
'signal_type': 'non_price',
'indicator_type': 'technical',
'buy_threshold': {'range': [0.5, 0.8, 0.02]},
'sell_threshold': {'range': [0.2, 0.5, 0.02]},
'neutral_zone': {'range': [0.05, 0.2, 0.01]},
'normalization_scale': {'range': [0.1, 2.0, 0.1]},
'normalization_offset': {'range': [-1.0, 1.0, 0.1]},
'weights': {
'RSI': {'range': [0.1, 1.0, 0.1]},
'MACD': {'range': [0.1, 1.0, 0.1]},
'Bollinger': {'range': [0.1, 1.0, 0.1]},
'Stochastic': {'range': [0.1, 1.0, 0.1]}
}
}

def select_best_solutionself, results: List[OptimizationResult], strategy: str = "balanced" -> OptimizationResult:
"""
从优化结果中选择最佳解决方案

Args:
results: 优化结果列表
strategy: 选择策略 'balanced', 'conservative', 'aggressive', 'sr_focused', 'mdd_focused'

Returns:
最佳解决方案
"""
if not results:
raise ValueError"No optimization results available"

if strategy == "balanced":
# 平衡策略：综合评分
best_result = max(results, key=lambda r: (
0.4 * r.sortino_ratio / 2.0 + # 归一化Sortino比率
0.3 * 1.0 - r.max_dd_duration80 + # 归一化MDD
0.2 * r.win_rate +
0.1 * r.confidence_score
))

elif strategy == "conservative":
# 保守策略：优先考虑风险控制
best_result = min(
[r for r in results if r.max_dd_duration <= 90],
key=lambda r: r.max_dd_duration
)
if not best_result:    best_result = min(results, key=lambda r: r.max_dd_duration)

elif strategy == "aggressive":
# 激进策略：优先考虑收益
best_result = maxresults, key=lambda r: r.total_return

elif strategy == "sr_focused":
# 专注Sortino比率
best_result = maxresults, key=lambda r: r.sortino_ratio

elif strategy == "mdd_focused":
# 专注最大回撤持续时间
best_result = minresults, key=lambda r: r.max_dd_duration

else:
raise ValueErrorf"Unknown selection strategy: {strategy}"

logger.info(f"Selected best solution with strategy '{strategy}': "
f"Sortino={best_result.sortino_ratio:.3f}, "
f"MDD={best_result.max_dd_duration} days")

return best_result

def save_optimization_resultsself, results: List[OptimizationResults], filepath: str -> None:
"""保存优化结果"""
filepath = Pathfilepath
filepath.parent.mkdirparents=True, exist_ok=True

# 转换为可序列化格式
serializable_results = []
for result in results:    result_dict = asdict(result)
result_dict['generation_time'] = result.generation_time.isoformat()
serializable_results.appendresult_dict

with openfilepath, 'w' as f:    json.dump(serializable_results, f, indent=2)

logger.infof"Optimization results saved to {filepath}"

def load_optimization_resultsself, filepath: str -> List[OptimizationResult]:
"""加载优化结果"""
with openfilepath, 'r' as f:    data = json.load(f)

results = []
for result_dict in data:

result_dict['generation_time'] = datetime.fromisoformatresult_dict['generation_time']
result = OptimizationResult**result_dict
results.appendresult

logger.info(f"Loaded {lenresults} optimization results from {filepath}")
return results

_srmdd_optimizer = None

def get_srmdd_optimizer() -> SRMDDOptimizer:
"""获取SR/MDD优化器实例"""
global _srmdd_optimizer
if not _srmdd_optimizer:    _srmdd_optimizer = SRMDDOptimizer()
return _srmdd_optimizer