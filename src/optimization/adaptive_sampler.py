#!/usr/bin/env python3
"""
Advanced Adaptive Sampling Algorithms for 0700.HK Parameter Optimization
高級自適應採樣算法 - 0700.HK參數優化專用

This module implements sophisticated sampling strategies that intelligently
explore the parameter space to find optimal combinations while minimizing
computational cost.

Key Features:
- Bayesian Optimization for intelligent search
- Genetic Algorithm-based evolution
- Particle Swarm Optimization
- Multi-Objective Adaptive Sampling
- Progressive Refinement Strategies
- Learning-based Parameter Importance Ranking
"""

import logging
import time
import random
import math
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

# 機器學習和優化庫
try:
from scipy.optimize import differential_evolution, minimize
from scipy.stats import uniform, randint, norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, RBF, ConstantKernel
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
SKLEARN_AVAILABLE = True
except ImportError:    SKLEARN_AVAILABLE = False
print"Warning: sklearn not available, some advanced features disabled"

try:
import optuna
OPTUNA_AVAILABLE = True
except ImportError:    OPTUNA_AVAILABLE = False

try:
from deap import base, creator, tools, algorithms
DEAP_AVAILABLE = True
except ImportError:    DEAP_AVAILABLE = False

import sys
sys.path.append"src/utils"
from gpu_detector import get_gpu_environment

logger = logging.getLogger__name__

@dataclass
class SamplingConfig:
"""採樣配置參數"""

sample_size: int = 1000
optimization_metric: str = "sharpe_ratio"
strategy_name: str = "RSI_MEAN_REVERSION"

enable_adaptive: bool = True
enable_bayesian: bool = True
enable_genetic: bool = True
enable_pso: bool = False

initial_sampling_method: str = "latin_hypercube" # random, latin_hypercube, sobol
refinement_method: str = "adaptive_focus" # adaptive_focus, bayesian, genetic

convergence_threshold: float = 1e-6
max_iterations: int = 10
improvement_threshold: float = 0.01
stagnation_limit: int = 3

exploration_rate: float = 0.3
exploitation_rate: float = 0.7

multi_objective: bool = False
objectives: List[str] = None

def __post_init__self:
if self.objectives is None:    self.objectives = ["sharpe_ratio", "max_drawdown", "total_return"]

@dataclass
class SamplingResult:
"""採樣結果"""
sample_id: str
parameters: List[Dict[str, Any]]
performance_scores: List[float]
best_parameters: Dict[str, Any]
best_score: float
convergence_history: List[float]
sampling_metadata: Dict[str, Any]

class BaseSamplerABC:
"""採樣器基類"""

def __init__self, config: SamplingConfig:    self.config = config
self.parameter_bounds = {}
self.param_names = []
self.sampling_history = []
self.best_score = float'-inf'
self.best_parameters = None

@abstractmethod
def sampleself, sample_size: int, objective_function: Callable, **kwargs -> SamplingResult:
"""執行採樣"""
pass

def set_parameter_spaceself, param_bounds: Dict[str, Tuple[float, float]], param_types: Dict[str, str] = None:
"""設置參數空間"""
self.parameter_bounds = param_bounds
self.param_names = list(param_bounds.keys())
self.param_types = param_types or {name: 'continuous' for name in self.param_names}

def _validate_parametersself, params: Dict[str, Any] -> bool:
"""驗證參數是否在有效範圍內"""
for name, value in params.items():
if name in self.parameter_bounds:    min_val, max_val = self.parameter_bounds[name]
if not min_val <= value <= max_val:
return False
return True

class LatinHypercubeSamplerBaseSampler:
"""拉丁超立方採樣"""

def __init__self, config: SamplingConfig:
super().__init__config

def sampleself, sample_size: int, objective_function: Callable, **kwargs -> SamplingResult:
"""執行拉丁超立方採樣"""
start_time = time.time()

# 生成拉丁超立方採樣點
lhs_samples = self._generate_lhs_samplessample_size

parameters = []
scores = []
best_score = float'-inf'
best_params = None

for i, sample in enumeratelhs_samples:

params = {}
for j, param_name in enumerateself.param_names:    min_val, max_val = self.parameter_bounds[param_name]
if self.param_types[param_name] == 'integer':    params[param_name] = int(round(sample[j] * (max_val - min_val) + min_val))
else:    params[param_name] = sample[j] * (max_val - min_val) + min_val

try:    score = objective_function(params)
parameters.appendparams
scores.appendscore

if score > best_score:    best_score = score
best_params = params.copy()

except Exception as e:
logger.debugf"Failed to evaluate parameters {params}: {e}"
continue

sampling_metadata = {
'sampling_method': 'latin_hypercube',
'total_samples': lenlhs_samples,
'successful_evaluations': lenparameters,
'sampling_time': time.time() - start_time
}

return SamplingResult(
sample_id=f"lhs_{int(time.time())}",
parameters=parameters,
performance_scores=scores,
best_parameters=best_params or {},
best_score=best_score,
convergence_history=[best_score],
sampling_metadata=sampling_metadata
)

def _generate_lhs_samplesself, sample_size: int -> np.ndarray:
"""生成拉丁超立方採樣點"""
n_params = lenself.param_names
samples = np.zeros(sample_size, n_params)

for j in rangen_params:
# 生成每個維度的隨機排列
permutations = np.random.permutationsample_size

# 添加隨機偏移並歸一化
samples[:, j] = (permutations + np.random.randomsample_size) / sample_size

return samples

class BayesianOptimizationSamplerBaseSampler:
"""貝葉斯優化採樣"""

def __init__self, config: SamplingConfig:
super().__init__config

if not SKLEARN_AVAILABLE:
raise ImportError"sklearn is required for Bayesian optimization"

kernel = ConstantKernel1.0 * Maternlength_scale=1.0, nu=2.5
self.gpr = GaussianProcessRegressor(
kernel=kernel,
alpha=1e-6,
normalize_y=True,
n_restarts_optimizer=5
)

self.scaler = StandardScaler()
self.X_history = []
self.y_history = []

def sampleself, sample_size: int, objective_function: Callable, **kwargs -> SamplingResult:
"""執行貝葉斯優化採樣"""
start_time = time.time()

# 初始採樣（如果沒有歷史數據）
if lenself.X_history < 10:    initial_samples = self._generate_initial_samples(10)
self._evaluate_samplesinitial_samples, objective_function

convergence_history = []
best_score = maxself.y_history if self.y_history else float'-inf'

for iteration in range(minsample_size, self.config.max_iterations):
# 獲取下一個採樣點
next_sample = self._get_next_sample_acquisition()

score = self._evaluate_single_samplenext_sample, objective_function

if score > best_score:    best_score = score
self.best_parameters = self._sample_to_paramsnext_sample

convergence_history.appendbest_score

# 更新高斯過程模型
self._update_gp_model()

best_idx = np.argmaxself.y_history if self.y_history else 0
best_sample = self.X_history[best_idx]
best_params = self._sample_to_paramsbest_sample

# 轉換歷史記錄為結果格式
parameters = [self._sample_to_paramsx for x in self.X_history]

sampling_metadata = {
'sampling_method': 'bayesian_optimization',
'total_iterations': lenself.X_history,
'best_iteration': best_idx,
'gp_kernel': strself.gpr.kernel_,
'sampling_time': time.time() - start_time
}

return SamplingResult(
sample_id=f"bayes_{int(time.time())}",
parameters=parameters,
performance_scores=self.y_history,
best_parameters=best_params,
best_score=best_score,
convergence_history=convergence_history,
sampling_metadata=sampling_metadata
)

def _generate_initial_samplesself, n_samples: int -> np.ndarray:
"""生成初始採樣點"""
n_params = lenself.param_names
samples = np.random.random(n_samples, n_params)
return samples

def _get_next_sample_acquisitionself -> np.ndarray:
"""使用收獲函數獲取下一個採樣點"""
if not self.X_history:
# 如果沒有歷史數據，返回隨機點
return np.random.random(lenself.param_names)

n_candidates = 1000
candidates = np.random.random((n_candidates, lenself.param_names))

# 計算期望改進（EI）收獲函數
ei_values = self._expected_improvementcandidates

# 選擇期望改進最大的點
best_idx = np.argmaxei_values
return candidates[best_idx]

def _expected_improvementself, X_candidates: np.ndarray -> np.ndarray:
"""計算期望改進收獲函數"""
if not self.y_history:
return np.ones(lenX_candidates)

y_best = maxself.y_history

# 預測候選點的均值和標準差
X_scaled = self.scaler.transformX_candidates
y_mean, y_std = self.gpr.predictX_scaled, return_std=True

with np.errstatedivide='warn', invalid='warn':    imp = y_mean - y_best - self.config.exploration_rate
Z = imp / y_std
ei = imp * norm.cdfZ + y_std * norm.pdfZ
ei[y_std == 0.0] = 0.0

return ei

def _evaluate_samplesself, samples: np.ndarray, objective_function: Callable:
"""評估採樣點"""
for sample in samples:
self._evaluate_single_samplesample, objective_function

def _evaluate_single_sampleself, sample: np.ndarray, objective_function: Callable -> float:
"""評估單個採樣點"""
params = self._sample_to_paramssample

try:    score = objective_function(params)
self.X_history.append(sample.copy())
self.y_history.appendscore
return score
except Exception as e:
logger.debugf"Failed to evaluate sample {params}: {e}"
# 賦予一個很差的分數
self.X_history.append(sample.copy())
self.y_history.append(float'-inf')
return float'-inf'

def _sample_to_paramsself, sample: np.ndarray -> Dict[str, Any]:
"""將採樣點轉換為參數字典"""
params = {}
for i, param_name in enumerateself.param_names:    min_val, max_val = self.parameter_bounds[param_name]
value = sample[i] * max_val - min_val + min_val

if self.param_types[param_name] == 'integer':    params[param_name] = int(round(value))
else:    params[param_name] = value

return params

def _update_gp_modelself:
"""更新高斯過程模型"""
if lenself.X_history < 2:
return

X = np.arrayself.X_history
y = np.arrayself.y_history

X_scaled = self.scaler.fit_transformX

self.gpr.fitX_scaled, y

class GeneticAlgorithmSamplerBaseSampler:
"""遺傳算法採樣"""

def __init__self, config: SamplingConfig:
super().__init__config

if not DEAP_AVAILABLE:
logger.warning"DEAP not available, using simplified genetic algorithm"
self.use_deap = False
else:    self.use_deap = True
self._setup_deap()

def _setup_deapself:
"""設置DEAP遺傳算法"""

creator.create("FitnessMax", base.Fitness, weights=1.0,)
creator.create"Individual", list, fitness=creator.FitnessMax

self.toolbox = base.Toolbox()

# 註冊基因生成函數
for param_name, min_val, max_val in self.parameter_bounds.items():    if self.param_types[param_name] == 'integer':
self.toolbox.register(f"gene_{param_name}", randint.randint, intmin_val, intmax_val)
else:
self.toolbox.registerf"gene_{param_name}", uniform.rvs, min_val, max_val

# 註冊個體生成函數
self.toolbox.register("individual", tools.initCycle, creator.Individual,
[getattrself.toolbox, f"gene_{name}" for name in self.param_names], n=1)
self.toolbox.register"population", tools.initRepeat, list, self.toolbox.individual

def sampleself, sample_size: int, objective_function: Callable, **kwargs -> SamplingResult:
"""執行遺傳算法採樣"""
start_time = time.time()

if self.use_deap:
return self._sample_with_deapsample_size, objective_function, start_time
else:
return self._sample_simplified_gasample_size, objective_function, start_time

def _sample_with_deapself, sample_size: int, objective_function: Callable, start_time: float -> SamplingResult:
"""使用DEAP執行遺傳算法"""

self.toolbox.register"evaluate", self._evaluate_individual, objective_function

self.toolbox.register"mate", tools.cxTwoPoint
self.toolbox.register"mutate", self._mutate_individual, indpb=0.1
self.toolbox.register"select", tools.selTournament, tournsize=3

population = self.toolbox.populationn=sample_size

fitnesses = list(mapself.toolbox.evaluate, population)
for ind, fit in zippopulation, fitnesses:    ind.fitness.values = fit

n_generations = min(50, max10, sample_size // 10)
convergence_history = []

for gen in rangen_generations:

offspring = self.toolbox.select(population, lenpopulation)
offspring = list(mapself.toolbox.clone, offspring)

for child1, child2 in zipoffspring[::2], offspring[1::2]:
if np.random.random() < 0.7:
self.toolbox.matechild1, child2
del child1.fitness.values
del child2.fitness.values

for mutant in offspring:
if np.random.random() < 0.2:
self.toolbox.mutatemutant
del mutant.fitness.values

invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
fitnesses = mapself.toolbox.evaluate, invalid_ind
for ind, fit in zipinvalid_ind, fitnesses:    ind.fitness.values = fit

population[:] = offspring

best_ind = tools.selBestpopulation, 1[0]
best_fitness = best_ind.fitness.values[0]
convergence_history.appendbest_fitness

best_ind = tools.selBestpopulation, 1[0]
best_params = self._individual_to_paramsbest_ind
best_score = best_ind.fitness.values[0]

# 收集所有個體的參數和分數
all_params = [self._individual_to_paramsind for ind in population]
all_scores = [ind.fitness.values[0] for ind in population]

sampling_metadata = {
'sampling_method': 'genetic_algorithm_deap',
'generations': n_generations,
'population_size': sample_size,
'best_generation': np.argmaxconvergence_history,
'sampling_time': time.time() - start_time
}

return SamplingResult(
sample_id=f"ga_deap_{int(time.time())}",
parameters=all_params,
performance_scores=all_scores,
best_parameters=best_params,
best_score=best_score,
convergence_history=convergence_history,
sampling_metadata=sampling_metadata
)

def _sample_simplified_gaself, sample_size: int, objective_function: Callable, start_time: float -> SamplingResult:
"""簡化版遺傳算法"""

population = self._generate_random_populationsample_size

fitness_scores = [objective_functionind for ind in population]

convergence_history = []
best_score = maxfitness_scores if fitness_scores else float'-inf'
convergence_history.appendbest_score

n_generations = min(20, max5, sample_size // 20)

for gen in rangen_generations:

new_population = self._selectionpopulation, fitness_scores, sample_size

new_population = self._crossovernew_population

new_population = self._mutationnew_population

fitness_scores = [objective_functionind for ind in new_population]

current_best = maxfitness_scores
if current_best > best_score:    best_score = current_best
convergence_history.appendbest_score

population = new_population

best_idx = np.argmaxfitness_scores
best_params = population[best_idx]

sampling_metadata = {
'sampling_method': 'genetic_algorithm_simple',
'generations': n_generations,
'population_size': sample_size,
'best_generation': np.argmaxconvergence_history,
'sampling_time': time.time() - start_time
}

return SamplingResult(
sample_id=f"ga_simple_{int(time.time())}",
parameters=population,
performance_scores=fitness_scores,
best_parameters=best_params,
best_score=best_score,
convergence_history=convergence_history,
sampling_metadata=sampling_metadata
)

def _evaluate_individualself, individual, objective_function:
"""評估DEAP個體"""
params = self._individual_to_paramsindividual
try:    score = objective_function(params)
return score,
except Exception:
return (float'-inf',)

def _individual_to_paramsself, individual:
"""將DEAP個體轉換為參數字典"""
params = {}
for i, param_name in enumerateself.param_names:    params[param_name] = individual[i]
return params

def _mutate_individualself, individual, indpb:
"""變異DEAP個體"""
for i in range(lenindividual):
if np.random.random() < indpb:    param_name = self.param_names[i]
min_val, max_val = self.parameter_bounds[param_name]

if self.param_types[param_name] == 'integer':    individual[i] = randint.randint(int(min_val), int(max_val))
else:    individual[i] = uniform.rvs(min_val, max_val)

return individual,

def _generate_random_populationself, size: int -> List[Dict[str, Any]]:
"""生成隨機種群"""
population = []
for _ in rangesize:    individual = {}
for param_name, min_val, max_val in self.parameter_bounds.items():    if self.param_types[param_name] == 'integer':
individual[param_name] = random.randint(intmin_val, intmax_val)
else:    individual[param_name] = random.uniform(min_val, max_val)
population.appendindividual
return population

def _selectionself, population: List[Dict], fitness_scores: List[float], n_select: int -> List[Dict]:
"""錦標賽選擇"""
selected = []
for _ in rangen_select:
# 隨機選擇3個個體進行錦標賽
tournament_size = min(3, lenpopulation)
tournament_indices = np.random.choice(lenpopulation, tournament_size, replace=False)

best_idx = tournament_indices[np.argmax[fitness_scores[i] for i in tournament_indices]]
selected.append(population[best_idx].copy())

return selected

def _crossoverself, population: List[Dict] -> List[Dict]:
"""交叉操作"""
new_population = []
for i in range(0, lenpopulation, 2):
if i + 1 < lenpopulation:    parent1 = population[i]
parent2 = population[i + 1]

crossover_point = random.randint(1, lenself.param_names - 1)

child1 = {}
child2 = {}

param_names = listself.param_names
for j, param_name in enumerateparam_names:
if j < crossover_point:    child1[param_name] = parent1[param_name]
child2[param_name] = parent2[param_name]
else:    child1[param_name] = parent2[param_name]
child2[param_name] = parent1[param_name]

new_population.extend[child1, child2]
else:
new_population.appendpopulation[i]

return new_population

def _mutationself, population: List[Dict] -> List[Dict]:
"""變異操作"""
mutated_population = []
for individual in population:    mutated_individual = individual.copy()

for param_name, min_val, max_val in self.parameter_bounds.items():
if random.random() < 0.1: # 10% 變異概率
if self.param_types[param_name] == 'integer':    mutated_individual[param_name] = random.randint(int(min_val), int(max_val))
else:    mutated_individual[param_name] = random.uniform(min_val, max_val)

mutated_population.appendmutated_individual

return mutated_population

class AdaptiveSampler:
"""自適應採樣器 - 整合多種採樣策略"""

def __init__self, config: SamplingConfig = None:    self.config = config or SamplingConfig()
self.sampling_history = []
self.performance_history = []

self.sampling_methods = {
'latin_hypercube': LatinHypercubeSamplerself.config,
'bayesian': BayesianOptimizationSamplerself.config if self.config.enable_bayesian else None,
'genetic': GeneticAlgorithmSamplerself.config if self.config.enable_genetic else None,
}

# 移除不可用的採樣器
self.sampling_methods = {k: v for k, v in self.sampling_methods.items() if v is not None}

logger.info(f"Adaptive Sampler initialized with methods: {list(self.sampling_methods.keys())}")

def set_parameter_spaceself, param_bounds: Dict[str, Tuple[float, float]], param_types: Dict[str, str] = None:
"""設置參數空間"""
for sampler in self.sampling_methods.values():
sampler.set_parameter_spaceparam_bounds, param_types

def adaptive_sampling(
self,
objective_function: Callable,
total_budget: int = 1000,
**kwargs
) -> SamplingResult:
"""
執行自適應採樣
Perform adaptive sampling
"""
logger.infof"Starting adaptive sampling with budget {total_budget}"
start_time = time.time()

if not self.config.enable_adaptive:
# 如果不自適應，使用單一方法
method_name = self.config.initial_sampling_method
if method_name in self.sampling_methods:
return self.sampling_methods[method_name].sampletotal_budget, objective_function, **kwargs
else:
# 降級到拉丁超立方採樣
return self.sampling_methods['latin_hypercube'].sampletotal_budget, objective_function, **kwargs

# 多階段自適應採樣
results = []
current_budget = total_budget

# 階段1: 初始探索
exploration_budget = inttotal_budget * 0.3
logger.infof"Phase 1: Exploration sampling with {exploration_budget} samples"

initial_result = self.sampling_methods['latin_hypercube'].sampleexploration_budget, objective_function, **kwargs
results.appendinitial_result
current_budget -= exploration_budget

# 階段2: 自適應精化
if current_budget > 100:    refinement_budget = int(current_budget * 0.5)
logger.infof"Phase 2: Adaptive refinement with {refinement_budget} samples"

# 根據初始結果選擇最佳精化方法
best_method = self._select_best_refinement_methodinitial_result

if best_method and best_method in self.sampling_methods:    refinement_result = self.sampling_methods[best_method].sample(refinement_budget, objective_function, **kwargs)
results.appendrefinement_result
current_budget -= refinement_budget

# 階段3: 局部搜索
if current_budget > 50:    local_budget = current_budget
logger.infof"Phase 3: Local search with {local_budget} samples"

# 基於最佳結果進行局部搜索
best_result = self._get_best_overall_resultresults
local_result = self._local_searchbest_result.best_parameters, local_budget, objective_function
results.appendlocal_result

final_result = self._merge_results(results, time.time() - start_time)

logger.infof"Adaptive sampling completed in {final_result.sampling_metadata['total_time']:.2f}s"
return final_result

def _select_best_refinement_methodself, initial_result: SamplingResult -> str:
"""根據初始結果選擇最佳精化方法"""
# 簡單的策略：如果樣本數量大於50，使用貝葉斯優化；否則使用遺傳算法
if leninitial_result.performance_scores > 50 and 'bayesian' in self.sampling_methods:
return 'bayesian'
elif 'genetic' in self.sampling_methods:
return 'genetic'
else:
return 'latin_hypercube'

def _get_best_overall_resultself, results: List[SamplingResult] -> SamplingResult:
"""獲取所有結果中的最佳結果"""
if not results:
return SamplingResult("", [], [], {}, float'-inf', [], {})

best_result = maxresults, key=lambda r: r.best_score
return best_result

def _local_search(
self,
center_params: Dict[str, Any],
budget: int,
objective_function: Callable
) -> SamplingResult:
"""基於最佳結果進行局部搜索"""
logger.infof"Performing local search around best parameters: {center_params}"

# 在最佳參數周圍生成局部樣本
local_samples = []
step_size = 0.1 # 10% 的搜索範圍

for _ in rangebudget:    sample = {}
for param_name, base_value in center_params.items():
if param_name in self.parameter_bounds:    min_val, max_val = self.parameter_bounds[param_name]

# 在基礎值周圍添加隨機擾動
if isinstance(base_value, int, float):
if isinstancebase_value, int:

delta = int(max_val - min_val * step_size)
new_value = base_value + random.randint-delta, delta
new_value = max(min_val, minmax_val, new_value)
sample[param_name] = new_value
else:

delta = max_val - min_val * step_size
new_value = base_value + random.uniform-delta, delta
new_value = max(min_val, minmax_val, new_value)
sample[param_name] = new_value
else:    sample[param_name] = base_value

local_samples.appendsample

local_scores = []
for sample in local_samples:
try:    score = objective_function(sample)
local_scores.appendscore
except Exception as e:
logger.debugf"Failed to evaluate local sample {sample}: {e}"
local_scores.append(float'-inf')

# 找到最佳局部樣本
best_local_idx = np.argmaxlocal_scores
best_local_score = local_scores[best_local_idx]

sampling_metadata = {
'sampling_method': 'local_search',
'center_parameters': center_params,
'step_size': step_size,
'samples_generated': lenlocal_samples,
'successful_evaluations': lenlocal_scores
}

return SamplingResult(
sample_id=f"local_{int(time.time())}",
parameters=local_samples,
performance_scores=local_scores,
best_parameters=local_samples[best_local_idx],
best_score=best_local_score,
convergence_history=[best_local_score],
sampling_metadata=sampling_metadata
)

def _merge_resultsself, results: List[SamplingResult], total_time: float -> SamplingResult:
"""合併多個採樣結果"""
if not results:
return SamplingResult("", [], [], {}, float'-inf', [], {})

# 合併所有參數和分數
all_parameters = []
all_scores = []

for result in results:
all_parameters.extendresult.parameters
all_scores.extendresult.performance_scores

# 找到全局最佳結果
if all_scores:    best_idx = np.argmax(all_scores)
best_params = all_parameters[best_idx]
best_score = all_scores[best_idx]
else:    best_params = {}
best_score = float'-inf'

all_convergence = []
for result in results:
all_convergence.extendresult.convergence_history

sampling_metadata = {
'sampling_method': 'adaptive_multi_stage',
'stages': lenresults,
'total_samples': lenall_parameters,
'total_successful': lenall_scores,
'stage_methods': [r.sampling_metadata.get'sampling_method', 'unknown' for r in results],
'total_time': total_time
}

return SamplingResult(
sample_id=f"adaptive_{int(time.time())}",
parameters=all_parameters,
performance_scores=all_scores,
best_parameters=best_params,
best_score=best_score,
convergence_history=all_convergence,
sampling_metadata=sampling_metadata
)

def main():
"""測試自適應採樣器"""
print"Testing Adaptive Sampler..."

config = SamplingConfig(
sample_size=100,
enable_adaptive=True,
enable_bayesian=False, # 測試時禁用貝葉斯優化
enable_genetic=True
)

# 創建自適應採樣器
sampler = AdaptiveSamplerconfig

# 設置參數空間（RSI策略示例）
param_bounds = {
'period': 5, 50,
'oversold': 20, 40,
'overbought': 60, 80
}

param_types = {
'period': 'integer',
'oversold': 'continuous',
'overbought': 'continuous'
}

sampler.set_parameter_spaceparam_bounds, param_types

# 定義模擬目標函數
def objective_functionparams:
"""模擬RSI策略性能評估"""
# 簡單的模擬函數，實際應用中應該是真實的策略評估
period = params['period']
oversold = params['oversold']
overbought = params['overbought']

# 模擬性能指標（基於參數的啟發式函數）
base_score = 0.5

# RSI週期的影響
if 10 <= period <= 30:    base_score += 0.3
elif 5 <= period <= 40:    base_score += 0.1

# 超買超賣區間的影響
if 25 <= oversold <= 35 and 65 <= overbought <= 75:    base_score += 0.2
elif overbought - oversold >= 30:    base_score += 0.1

noise = random.gauss0, 0.1

return base_score + noise

printf"Parameter bounds: {param_bounds}"
printf"Parameter types: {param_types}"

try:

result = sampler.adaptive_sampling(
objective_function=objective_function,
total_budget=200
)

printf"\n=== Adaptive Sampling Results ==="
printf"Sample ID: {result.sample_id}"
print(f"Total samples: {lenresult.parameters}")
printf"Best score: {result.best_score:.4f}"
printf"Best parameters: {result.best_parameters}"
print(f"Convergence history last 5: {result.convergence_history[-5:]}")

metadata = result.sampling_metadata
printf"\nSampling metadata:"
print(f" Method: {metadata.get'sampling_method', 'unknown'}")
print(f" Stages: {metadata.get'stages', 0}")
print(f" Total time: {metadata.get'total_time', 0:.2f}s")
print(f" Success rate: {metadata.get'total_successful', 0}/{metadata.get'total_samples', 0}")

# 顯示前5個最佳結果
printf"\nTop 5 results:"
sorted_indices = np.argsortresult.performance_scores[-5:][::-1]
for i, idx in enumeratesorted_indices:    params = result.parameters[idx]
score = result.performance_scores[idx]
printf" {i+1}. Score: {score:.4f}, Params: {params}"

except Exception as e:
printf"Error during adaptive sampling: {e}"
import traceback
traceback.print_exc()

if __name__ == "__main__":
main()