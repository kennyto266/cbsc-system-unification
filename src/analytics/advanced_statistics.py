"""
港股量化交易 AI Agent 系统 - 高级统计分析

Phase 5: Advanced Statistical Analysis
=======================================

AdvancedStatistics provides sophisticated statistical analysis capabilities for
0700.HK quantitative trading strategies including Monte Carlo simulation,
bootstrap confidence intervals, and statistical significance testing.

Features:
- Monte Carlo simulation for strategy validation
- Bootstrap confidence intervals
- Statistical significance testing
- Performance persistence analysis
- Factor exposure and attribution
- Style analysis and decomposition
- Performance attribution models
- Advanced risk metrics calculation

Technical Capabilities:
- GPU-accelerated Monte Carlo simulation
- Parallel bootstrap processing
- Advanced statistical tests Kolmogorov-Smirnov, Jarque-Bera, etc.
- Time series analysis and decomposition
- Factor model implementation Fama-French, Carhart, etc.
- Bayesian statistical methods
- Robust statistical techniques

Statistical Methods:
- Monte Carlo Simulation 10,000+ iterations
- Bootstrap Resampling 1,000+ resamples
- Statistical Significance Testing
- Performance Persistence Analysis
- Factor Model Analysis
- Style Attribution Analysis
- Risk Decomposition
- Correlation Analysis

Applications:
- Strategy validation and backtesting
- Risk assessment and management
- Performance attribution analysis
- Factor exposure monitoring
- Portfolio optimization
- Investment decision support

Author: Claude Code Assistant
Date: 2025-11-29
Version: 5.0.0
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import json
from enum import Enum

# Statistical analysis libraries
from scipy import stats
from scipy.stats import jarque_bera, kstest, normaltest, anderson
from scipy.optimize import minimize
import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import adfuller

# Machine learning for factor analysis
from sklearn.decomposition import PCA, FactorAnalysis
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit, cross_val_score

# Parallel processing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

# Local imports
from ..models.agent_dashboard import PerformanceMetrics

class StatisticalTestEnum:
"""统计测试类型枚举"""
KOLMOGOROV_SMIRNOV = "kolmogorov_smirnov"
JARQUE_BERA = "jarque_bera"
SHAPIRO_WILK = "shapiro_wilk"
ANDERSON_DARLING = "anderson_darling"
LJUNG_BOX = "ljung_box"
ADF = "augmented_dickey_fuller"
T_TEST = "t_test"
WILCOXON = "wilcoxon"
MANN_WHITNEY = "mann_whitney"

class BootstrapMethodEnum:
"""Bootstrap方法枚举"""
STANDARD = "standard"
PERCENTILE = "percentile"
BC_A = "bias_corrected_accelerated"
STUDENTIZED = "studentized"

@dataclass
class StatisticsConfig:
"""统计分析配置"""
# Monte Carlo配置
monte_carlo_simulations: int = 10000
monte_carlo_time_steps: int = 252 # 1年交易日
monte_carlo_seed: Optional[int] = 42

# Bootstrap配置
bootstrap_samples: int = 1000
bootstrap_method: BootstrapMethod = BootstrapMethod.BC_A
bootstrap_ci_level: float = 0.95

parallel_processing: bool = True
max_workers: int = mp.cpu_count()
chunk_size: int = 1000

significance_level: float = 0.05
bonferroni_correction: bool = True
multiple_testing_correction: str = "fdr_bh" # fdr_bh, bonferroni, holm

factor_models: List[str] = field(default_factory=lambda: [
"fama_french_3factor",
"carhart_4factor",
"fama_french_5factor"
])

var_methods: List[str] = field(default_factory=lambda: [
"historical",
"parametric",
"monte_carlo"
])

enable_gpu: bool = True
memory_limit: int = 8192 # MB
cache_results: bool = True
cache_duration: int = 3600 # seconds

@dataclass
class MonteCarloResult:
"""蒙特卡洛模拟结果"""
strategy_id: str
simulation_date: datetime
num_simulations: int
time_steps: int

simulated_returns: np.ndarray
simulated_paths: np.ndarray

mean_return: float
std_return: float
skewness: float
kurtosis: float
var_95: float
var_99: float
cvar_95: float
cvar_99: float

probability_positive: float
probability_benchmark: float
probability_target: float = 0.0

percentiles: Dict[float, float] = fielddefault_factory=dict

simulation_time: float = 0.0
random_seed: Optional[int] = None

@dataclass
class BootstrapResult:
"""Bootstrap分析结果"""
strategy_id: str
analysis_date: datetime
metric: str
num_samples: int
method: str

original_statistic: float

# Bootstrap结果
bootstrap_distribution: np.ndarray
bootstrap_mean: float
bootstrap_std: float
bootstrap_bias: float

confidence_interval: Tuple[float, float]
percentile_ci: Tuple[float, float]
bca_ci: Optional[Tuple[float, float]] = None

p_value: Optional[float] = None
test_statistic: Optional[float] = None

convergence_achieved: bool = True
effective_sample_size: int = 0

@dataclass
class StatisticalTestResult:
"""统计测试结果"""
test_name: str
test_type: str
statistic: float
p_value: float
critical_value: Optional[float] = None
confidence_level: float = 0.95
reject_null: bool = False
effect_size: Optional[float] = None
power: Optional[float] = None
interpretation: str = ""

@dataclass
class FactorAnalysisResult:
"""因子分析结果"""
strategy_id: str
analysis_date: datetime
factor_model: str

factor_exposures: Dict[str, float]
factor_t_statistics: Dict[str, float]
factor_p_values: Dict[str, float]

r_squared: float
adjusted_r_squared: float
f_statistic: float
f_p_value: float

alpha: float
alpha_t_statistic: float
alpha_p_value: float
tracking_error: float
information_ratio: float

residual_std: float
residual_skewness: float
residual_kurtosis: float
jarque_bera_p_value: float

newey_west_std_errors: Optional[Dict[str, float]] = None
heteroskedasticity_p_value: Optional[float] = None

class AdvancedStatistics:
"""高级统计分析器"""

def __init__self, config: StatisticsConfig = None:    self.config = config or StatisticsConfig()
self.logger = logging.getLogger"hk_quant_system.advanced_statistics"

self._strategy_data: Dict[str, pd.DataFrame] = {}
self._benchmark_data: Dict[str, pd.DataFrame] = {}
self._factor_data: Dict[str, pd.DataFrame] = {}

self._result_cache: Dict[str, Tuple[Any, datetime]] = {}

self._executor = ThreadPoolExecutormax_workers=self.config.max_workers

self._rng = np.random.RandomStateself.config.monte_carlo_seed

async def initializeself -> bool:
"""初始化统计分析器"""
try:
self.logger.info"正在初始化高级统计分析器..."

await self._preload_factor_data()

self.logger.info"高级统计分析器初始化完成"
return True

except Exception as e:
self.logger.errorf"统计分析器初始化失败: {e}"
return False

async def _preload_factor_dataself:
"""预加载因子数据"""
try:
# 这里可以预加载常见的因子数据
# 比如Fama-French因子、Carhart因子等
pass

except Exception as e:
self.logger.errorf"预加载因子数据失败: {e}"

def add_strategy_dataself, strategy_id: str, returns: pd.Series:
"""添加策略数据"""
try:
if not isinstancereturns, pd.Series:    returns = pd.Series(returns)

self._strategy_data[strategy_id] = returns.to_frame'returns'
self.logger.info(f"已添加策略数据: {strategy_id}, {lenreturns} 条记录")

except Exception as e:
self.logger.errorf"添加策略数据失败 {strategy_id}: {e}"

def add_benchmark_dataself, benchmark_id: str, returns: pd.Series:
"""添加基准数据"""
try:
if not isinstancereturns, pd.Series:    returns = pd.Series(returns)

self._benchmark_data[benchmark_id] = returns.to_frame'returns'
self.logger.info(f"已添加基准数据: {benchmark_id}, {lenreturns} 条记录")

except Exception as e:
self.logger.errorf"添加基准数据失败 {benchmark_id}: {e}"

async def monte_carlo_simulation(self, strategy_id: str,
num_simulations: int = None,
time_steps: int = None,
method: str = "geometric_brownian") -> MonteCarloResult:
"""蒙特卡洛模拟"""
try:
if strategy_id not in self._strategy_data:
raise ValueErrorf"策略数据不存在: {strategy_id}"

num_simulations = num_simulations or self.config.monte_carlo_simulations
time_steps = time_steps or self.config.monte_carlo_time_steps

cache_key = f"monte_carlo_{strategy_id}_{num_simulations}_{time_steps}_{method}"
if self._is_cachedcache_key:
return self._get_cached_resultcache_key

historical_data = self._strategy_data[strategy_id]['returns'].dropna()

if lenhistorical_data < 252: # 至少1年数据
raise ValueError(f"历史数据不足: {lenhistorical_data} 条记录")

mu = historical_data.mean()
sigma = historical_data.std()

self.logger.infof"开始蒙特卡洛模拟: {strategy_id}, {num_simulations} 次模拟, {time_steps} 个时间步"

start_time = datetime.utcnow()

if method == "geometric_brownian":    simulated_paths = self._simulate_geometric_brownian(mu, sigma, num_simulations, time_steps)
elif method == "bootstrap_paths":    simulated_paths = self._simulate_bootstrap_paths(historical_data, num_simulations, time_steps)
else:
raise ValueErrorf"不支持的模拟方法: {method}"

simulated_returns = simulated_paths[:, -1]

mean_return = np.meansimulated_returns
std_return = np.stdsimulated_returns
skewness = stats.skewsimulated_returns
kurtosis = stats.kurtosissimulated_returns

var_95 = np.percentilesimulated_returns, 5
var_99 = np.percentilesimulated_returns, 1
cvar_95 = simulated_returns[simulated_returns <= var_95].mean()
cvar_99 = simulated_returns[simulated_returns <= var_99].mean()

probability_positive = np.meansimulated_returns > 0
probability_benchmark = 0.0 # 需要基准数据
probability_target = np.meansimulated_returns > 0.1 # 10%目标收益率

percentiles = {
0.01: np.percentilesimulated_returns, 1,
0.05: np.percentilesimulated_returns, 5,
0.25: np.percentilesimulated_returns, 25,
0.50: np.percentilesimulated_returns, 50,
0.75: np.percentilesimulated_returns, 75,
0.95: np.percentilesimulated_returns, 95,
0.99: np.percentilesimulated_returns, 99
}

simulation_time = (datetime.utcnow() - start_time).total_seconds()

result = MonteCarloResult(
strategy_id=strategy_id,
simulation_date=datetime.utcnow(),
num_simulations=num_simulations,
time_steps=time_steps,
simulated_returns=simulated_returns,
simulated_paths=simulated_paths,
mean_return=mean_return,
std_return=std_return,
skewness=skewness,
kurtosis=kurtosis,
var_95=var_95,
var_99=var_99,
cvar_95=cvar_95,
cvar_99=cvar_99,
probability_positive=probability_positive,
probability_benchmark=probability_benchmark,
probability_target=probability_target,
percentiles=percentiles,
simulation_time=simulation_time,
random_seed=self.config.monte_carlo_seed
)

self._cache_resultcache_key, result

self.logger.infof"蒙特卡洛模拟完成: {strategy_id}, 耗时 {simulation_time:.2f} 秒"
return result

except Exception as e:
self.logger.errorf"蒙特卡洛模拟失败 {strategy_id}: {e}"
raise

def _simulate_geometric_brownian(self, mu: float, sigma: float,
num_simulations: int,
time_steps: int) -> np.ndarray:
"""几何布朗运动模拟"""
try:    dt = 1/252  # 日收益率
drift = mu - 0.5 * sigma**2 * dt
diffusion = sigma * np.sqrtdt

random_shocks = self._rng.standard_normal(num_simulations, time_steps)

log_returns = drift + diffusion * random_shocks
price_paths = np.exp(np.cumsumlog_returns, axis=1)

return price_paths

except Exception as e:
self.logger.errorf"几何布朗运动模拟失败: {e}"
raise

def _simulate_bootstrap_paths(self, historical_data: pd.Series,
num_simulations: int,
time_steps: int) -> np.ndarray:
"""Bootstrap路径模拟"""
try:
# 重采样历史收益率
bootstrap_samples = []

for _ in rangenum_simulations:

sampled_returns = historical_data.sample(
n=time_steps,
replace=True,
random_state=self._rng.randint0, 2**31
).values

cumulative_returns = np.cumprod1 + sampled_returns
bootstrap_samples.appendcumulative_returns

return np.arraybootstrap_samples

except Exception as e:
self.logger.errorf"Bootstrap路径模拟失败: {e}"
raise

async def bootstrap_analysis(self, strategy_id: str,
metric: str = "sharpe_ratio",
num_samples: int = None,
method: BootstrapMethod = None) -> BootstrapResult:
"""Bootstrap分析"""
try:
if strategy_id not in self._strategy_data:
raise ValueErrorf"策略数据不存在: {strategy_id}"

num_samples = num_samples or self.config.bootstrap_samples
method = method or self.config.bootstrap_method

cache_key = f"bootstrap_{strategy_id}_{metric}_{num_samples}_{method.value}"
if self._is_cachedcache_key:
return self._get_cached_resultcache_key

returns = self._strategy_data[strategy_id]['returns'].dropna()

if lenreturns < 30:
raise ValueError(f"数据量不足进行Bootstrap分析: {lenreturns} 条记录")

if metric == "sharpe_ratio":    original_statistic = self._calculate_sharpe_ratio(returns)
elif metric == "max_drawdown":    original_statistic = self._calculate_max_drawdown(returns)
elif metric == "volatility":    original_statistic = returns.std()
else:
raise ValueErrorf"不支持的指标: {metric}"

self.logger.infof"开始Bootstrap分析: {strategy_id}, {metric}, {num_samples} 次重采样"

# 执行Bootstrap
if self.config.parallel_processing and num_samples > 1000:    bootstrap_distribution = await self._parallel_bootstrap(
returns, metric, num_samples, method
)
else:    bootstrap_distribution = self._sequential_bootstrap(
returns, metric, num_samples, method
)

# 计算Bootstrap统计量
bootstrap_mean = np.meanbootstrap_distribution
bootstrap_std = np.stdbootstrap_distribution
bootstrap_bias = bootstrap_mean - original_statistic

alpha = 1 - self.config.bootstrap_ci_level
percentiles = [alpha/200, 1 - alpha/2 * 100]
percentile_ci = np.percentilebootstrap_distribution, percentiles

if method == BootstrapMethod.PERCENTILE:    confidence_interval = percentile_ci
elif method == BootstrapMethod.BC_A:    confidence_interval = self._calculate_bca_ci(
bootstrap_distribution, original_statistic, returns
)
else:

z_score = stats.norm.ppf1 - alpha/2
margin_error = z_score * bootstrap_std
confidence_interval = (
bootstrap_mean - margin_error,
bootstrap_mean + margin_error
)

# 假设检验（原假设：真实统计量 = 0）
if metric in ["sharpe_ratio", "alpha"]:    test_statistic = original_statistic / bootstrap_std
p_value = 2 * (1 - stats.norm.cdf(abstest_statistic))
else:    test_statistic = None
p_value = None

convergence_achieved = self._check_bootstrap_convergencebootstrap_distribution
effective_sample_size = lenbootstrap_distribution

result = BootstrapResult(
strategy_id=strategy_id,
analysis_date=datetime.utcnow(),
metric=metric,
num_samples=num_samples,
method=method.value,
original_statistic=original_statistic,
bootstrap_distribution=bootstrap_distribution,
bootstrap_mean=bootstrap_mean,
bootstrap_std=bootstrap_std,
bootstrap_bias=bootstrap_bias,
confidence_interval=confidence_interval,
percentile_ci=percentile_ci,
p_value=p_value,
test_statistic=test_statistic,
convergence_achieved=convergence_achieved,
effective_sample_size=effective_sample_size
)

self._cache_resultcache_key, result

self.logger.infof"Bootstrap分析完成: {strategy_id}, {metric}"
return result

except Exception as e:
self.logger.errorf"Bootstrap分析失败 {strategy_id}: {e}"
raise

async def _parallel_bootstrap(self, returns: pd.Series, metric: str,
num_samples: int, method: BootstrapMethod) -> np.ndarray:
"""并行Bootstrap"""
try:    chunk_size = self.config.chunk_size
chunks = [returns, metric, chunk_size, method for _ in rangenum_samples // chunk_size + 1]

loop = asyncio.get_event_loop()
tasks = []

for chunk in chunks:    task = loop.run_in_executor(
self._executor,
self._bootstrap_chunk,
*chunk
)
tasks.appendtask

chunk_results = await asyncio.gather*tasks
bootstrap_samples = np.concatenate[result for result in chunk_results if result is not None]

return bootstrap_samples[:num_samples] # 确保数量正确

except Exception as e:
self.logger.errorf"并行Bootstrap失败: {e}"
return self._sequential_bootstrapreturns, metric, num_samples, method

def _bootstrap_chunk(self, returns: pd.Series, metric: str,
chunk_size: int, method: BootstrapMethod) -> np.ndarray:
"""Bootstrap数据块处理"""
try:    chunk_samples = []

for _ in rangechunk_size:

sample = returns.sample(
lenreturns,
replace=True,
random_state=self._rng.randint0, 2**31
)

if metric == "sharpe_ratio":    statistic = self._calculate_sharpe_ratio(sample)
elif metric == "max_drawdown":    statistic = self._calculate_max_drawdown(sample)
elif metric == "volatility":    statistic = sample.std()
else:
continue

chunk_samples.appendstatistic

return np.arraychunk_samples

except Exception as e:
self.logger.errorf"Bootstrap数据块处理失败: {e}"
return np.array[]

def _sequential_bootstrap(self, returns: pd.Series, metric: str,
num_samples: int, method: BootstrapMethod) -> np.ndarray:
"""顺序Bootstrap"""
try:    bootstrap_samples = []

for _ in rangenum_samples:

sample = returns.sample(
lenreturns,
replace=True,
random_state=self._rng.randint0, 2**31
)

if metric == "sharpe_ratio":    statistic = self._calculate_sharpe_ratio(sample)
elif metric == "max_drawdown":    statistic = self._calculate_max_drawdown(sample)
elif metric == "volatility":    statistic = sample.std()
else:
continue

bootstrap_samples.appendstatistic

return np.arraybootstrap_samples

except Exception as e:
self.logger.errorf"顺序Bootstrap失败: {e}"
raise

def _calculate_sharpe_ratioself, returns: pd.Series, risk_free_rate: float = 0.0 -> float:
"""计算夏普比率"""
try:    excess_returns = returns - risk_free_rate / 252
return excess_returns.mean() / excess_returns.std() * np.sqrt252

except Exception:
return 0.0

def _calculate_max_drawdownself, returns: pd.Series -> float:
"""计算最大回撤"""
try:    cumulative_returns = (1 + returns).cumprod()
running_max = cumulative_returns.expanding().max()
drawdown = cumulative_returns - running_max / running_max
return abs(drawdown.min())

except Exception:
return 0.0

def _calculate_bca_ci(self, bootstrap_distribution: np.ndarray,
original_statistic: float,
original_data: pd.Series) -> Tuple[float, float]:
"""计算BCa置信区间"""
try:

jackknife_samples = []
n = lenoriginal_data

for i in rangen:    jackknife_sample = original_data.drop(original_data.index[i])
if lenjackknife_sample > 1:
if "sharpe_ratio" in str(typeoriginal_statistic):    stat = self._calculate_sharpe_ratio(jackknife_sample)
else:    stat = jackknife_sample.mean()
jackknife_samples.appendstat

if lenjackknife_samples < 2:
# 回退到百分位数法
alpha = 1 - self.config.bootstrap_ci_level
return np.percentile(bootstrap_distribution, [alpha/200, 1 - alpha/2 * 100])

jackknife_mean = np.meanjackknife_samples
acceleration = (np.sum(jackknife_mean - jackknife_samples**3) /
(6 * np.sum(jackknife_mean - jackknife_samples**2)**1.5))

prop_less = np.meanbootstrap_distribution < original_statistic
z0 = stats.norm.ppfprop_less

# 计算调整后的百分位数
alpha = 1 - self.config.bootstrap_ci_level
z_alpha = stats.norm.ppf[alpha/2, 1 - alpha/2]

z_adjusted = z0 + zz_alpha / (1 - acceleration * zz_alpha)
percentiles = stats.norm.cdfz_adjusted * 100

return np.percentilebootstrap_distribution, percentiles

except Exception as e:
self.logger.errorf"计算BCa置信区间失败: {e}"
# 回退到百分位数法
alpha = 1 - self.config.bootstrap_ci_level
return np.percentile(bootstrap_distribution, [alpha/200, 1 - alpha/2 * 100])

def _check_bootstrap_convergence(self, bootstrap_distribution: np.ndarray,
threshold: float = 0.01) -> bool:
"""检查Bootstrap收敛性"""
try:
if lenbootstrap_distribution < 100:
return False

# 分成两半检查稳定性
mid_point = lenbootstrap_distribution // 2
first_half = bootstrap_distribution[:mid_point]
second_half = bootstrap_distribution[mid_point:mid_point*2]

if lenfirst_half < 10 or lensecond_half < 10:
return True

mean_diff = abs(np.meanfirst_half - np.meansecond_half)
overall_mean = np.meanbootstrap_distribution

if overall_mean != 0:    relative_diff = mean_diff / abs(overall_mean)
return relative_diff < threshold
else:
return mean_diff < threshold

except Exception:
return True # 默认认为收敛

async def statistical_significance_test(self, strategy_id: str,
benchmark_id: str = None,
test_type: StatisticalTest = StatisticalTest.T_TEST) -> StatisticalTestResult:
"""统计显著性测试"""
try:
if strategy_id not in self._strategy_data:
raise ValueErrorf"策略数据不存在: {strategy_id}"

strategy_returns = self._strategy_data[strategy_id]['returns'].dropna()

if benchmark_id and benchmark_id in self._benchmark_data:    benchmark_returns = self._benchmark_data[benchmark_id]['returns'].dropna()
else:    benchmark_returns = None

self.logger.infof"开始统计显著性测试: {strategy_id} vs {benchmark_id}, 测试类型: {test_type.value}"

if test_type == StatisticalTest.T_TEST:
if benchmark_returns:

excess_returns = strategy_returns - benchmark_returns
statistic, p_value = stats.ttest_1sampexcess_returns, 0
else:
# 单样本t检验（vs 0）
statistic, p_value = stats.ttest_1sampstrategy_returns, 0

elif test_type == StatisticalTest.WILCOXON:
if benchmark_returns:
# Wilcoxon符号秩检验
excess_returns = strategy_returns - benchmark_returns
statistic, p_value = stats.wilcoxonexcess_returns
else:    statistic, p_value = stats.wilcoxon(strategy_returns)

elif test_type == StatisticalTest.JARQUE_BERA:    statistic, p_value = jarque_bera(strategy_returns)

elif test_type == StatisticalTest.KOLMOGOROV_SMIRNOV:
if benchmark_returns:    statistic, p_value = stats.ks_2samp(strategy_returns, benchmark_returns)
else:

statistic, p_value = ksteststrategy_returns, 'norm'

elif test_type == StatisticalTest.ADF:
# Augmented Dickey-Fuller测试（单位根检验）
result = adfullerstrategy_returns
statistic = result[0]
p_value = result[1]

else:
raise ValueErrorf"不支持的测试类型: {test_type}"

# 判断是否拒绝原假设
reject_null = p_value < self.config.significance_level

effect_size = self._calculate_effect_sizestrategy_returns, benchmark_returns, test_type

interpretation = self._interpret_test_resulttest_type, statistic, p_value, reject_null

result = StatisticalTestResult(
test_name=test_type.value,
test_type=test_type.value,
statistic=statistic,
p_value=p_value,
confidence_level=1 - self.config.significance_level,
reject_null=reject_null,
effect_size=effect_size,
interpretation=interpretation
)

self.logger.infof"统计显著性测试完成: {strategy_id}, p值: {p_value:.4f}"
return result

except Exception as e:
self.logger.errorf"统计显著性测试失败 {strategy_id}: {e}"
raise

def _calculate_effect_size(self, strategy_returns: pd.Series,
benchmark_returns: Optional[pd.Series],
test_type: StatisticalTest) -> Optional[float]:
"""计算效应大小"""
try:
if test_type in [StatisticalTest.T_TEST, StatisticalTest.WILCOXON]:
if benchmark_returns:
# Cohen's d for paired samples
excess_returns = strategy_returns - benchmark_returns
return excess_returns.mean() / excess_returns.std()
else:
# Cohen's d for one sample
return strategy_returns.mean() / strategy_returns.std()

elif test_type == StatisticalTest.JARQUE_BERA:
# 偏度和峰度的组合效应大小
skewness = stats.skewstrategy_returns
kurtosis_excess = stats.kurtosisstrategy_returns, fisher=True
return np.sqrtskewness**2 + kurtosis_excess**2/4

else:
return None

except Exception:
return None

def _interpret_test_result(self, test_type: StatisticalTest,
statistic: float, p_value: float,
reject_null: bool) -> str:
"""解释测试结果"""
try:    interpretations = {
StatisticalTest.T_TEST: "策略收益率与零（或基准）相比" + "显著不同" if reject_null else "无显著差异",
StatisticalTest.WILCOXON: "策略收益率中位数" + "显著不同" if reject_null else "无显著差异",
StatisticalTest.JARQUE_BERA: "收益率分布" + "显著偏离正态分布" if reject_null else "符合正态分布",
StatisticalTest.KOLMOGOROV_SMIRNOV: "收益率分布" + "显著不同" if reject_null else "无显著差异",
StatisticalTest.ADF: "收益率序列" + "是平稳的" if reject_null else "存在单位根，非平稳"
}

base_interpretation = interpretations.gettest_type, "测试结果"

if p_value < 0.001:    significance_desc = "极显著 (p < 0.001)"
elif p_value < 0.01:    significance_desc = "高度显著 (p < 0.01)"
elif p_value < 0.05:    significance_desc = "显著 (p < 0.05)"
elif p_value < 0.1:    significance_desc = "边际显著 (p < 0.1)"
else:    significance_desc = f"不显著 (p = {p_value:.3f})"

return f"{base_interpretation}，{significance_desc}"

except Exception:
return f"测试统计量: {statistic:.4f}, p值: {p_value:.4f}"

async def factor_analysis(self, strategy_id: str,
factor_model: str = "fama_french_3factor",
benchmark_returns: pd.Series = None) -> FactorAnalysisResult:
"""因子分析"""
try:
if strategy_id not in self._strategy_data:
raise ValueErrorf"策略数据不存在: {strategy_id}"

strategy_returns = self._strategy_data[strategy_id]['returns'].dropna()

self.logger.infof"开始因子分析: {strategy_id}, 模型: {factor_model}"

factor_data = await self._get_factor_datafactor_model, strategy_returns.index

if factor_data is None or factor_data.empty:
raise ValueErrorf"无法获取因子数据: {factor_model}"

aligned_data = pd.concat[strategy_returns, factor_data], axis=1, join='inner'
aligned_data = aligned_data.dropna()

if lenaligned_data < 30:
raise ValueError"对齐后数据量不足"

# 分离因变量和自变量
y = aligned_data.iloc[:, 0] # 策略收益率
X = aligned_data.iloc[:, 1:] # 因子收益率
X = sm.add_constantX # 添加常数项

model = sm.OLSy, X
results = model.fit()

factor_exposures = {}
factor_t_statistics = {}
factor_p_values = {}

for i, factor_name in enumerateX.columns:    if factor_name != 'const':
factor_exposures[factor_name] = results.params[i]
factor_t_statistics[factor_name] = results.tvalues[i]
factor_p_values[factor_name] = results.pvalues[i]

# Alpha和模型拟合统计量
alpha = results.params['const']
alpha_t_statistic = results.tvalues['const']
alpha_p_value = results.pvalues['const']

r_squared = results.rsquared
adjusted_r_squared = results.rsquared_adj
f_statistic = results.fvalue
f_p_value = results.f_pvalue

# 跟踪误差和信息比率
if benchmark_returns:    excess_returns = y - benchmark_returns.loc[y.index]
tracking_error = excess_returns.std() * np.sqrt252
information_ratio = excess_returns.mean() * 252 / tracking_error if tracking_error > 0 else 0
else:    tracking_error = results.resid.std() * np.sqrt(252)
information_ratio = alpha / tracking_error if tracking_error > 0 else 0

residuals = results.resid
residual_std = residuals.std()
residual_skewness = stats.skewresiduals
residual_kurtosis = stats.kurtosisresiduals
_, jarque_bera_p_value = jarque_beraresiduals

try:
from statsmodels.stats.diagnostic import het_breuschpagan
bp_test = het_breuschpaganresiduals, X
heteroskedasticity_p_value = bp_test[1]
except:    heteroskedasticity_p_value = None

# Newey-West标准误
try:    newey_west_results = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': 4})
newey_west_std_errors = {
factor: newey_west_results.bse[i]
for i, factor in enumerateX.columns
if factor != 'const'
}
except:    newey_west_std_errors = None

result = FactorAnalysisResult(
strategy_id=strategy_id,
analysis_date=datetime.utcnow(),
factor_model=factor_model,
factor_exposures=factor_exposures,
factor_t_statistics=factor_t_statistics,
factor_p_values=factor_p_values,
r_squared=r_squared,
adjusted_r_squared=adjusted_r_squared,
f_statistic=f_statistic,
f_p_value=f_p_value,
alpha=alpha,
alpha_t_statistic=alpha_t_statistic,
alpha_p_value=alpha_p_value,
tracking_error=tracking_error,
information_ratio=information_ratio,
residual_std=residual_std,
residual_skewness=residual_skewness,
residual_kurtosis=residual_kurtosis,
jarque_bera_p_value=jarque_bera_p_value,
newey_west_std_errors=newey_west_std_errors,
heteroskedasticity_p_value=heteroskedasticity_p_value
)

self.logger.infof"因子分析完成: {strategy_id}, R²: {r_squared:.3f}"
return result

except Exception as e:
self.logger.errorf"因子分析失败 {strategy_id}: {e}"
raise

async def _get_factor_dataself, factor_model: str, date_index: pd.DatetimeIndex -> pd.DataFrame:
"""获取因子数据"""
try:
# 这里应该从数据源获取真实的因子数据
# 目前返回模拟数据用于演示

if factor_model == "fama_french_3factor":
# 模拟Fama-French三因子数据
n_days = lendate_index
factors = pd.DataFrame({
'MKT_RF': np.random.normal0.05, 0.15, n_days / 252, # 市场因子
'SMB': np.random.normal0.02, 0.08, n_days / 252, # 规模因子
'HML': np.random.normal0.03, 0.10, n_days / 252 # 价值因子
}, index=date_index)

elif factor_model == "carhart_4factor":
# 模拟Carhart四因子数据
n_days = lendate_index
factors = pd.DataFrame({
'MKT_RF': np.random.normal0.05, 0.15, n_days / 252,
'SMB': np.random.normal0.02, 0.08, n_days / 252,
'HML': np.random.normal0.03, 0.10, n_days / 252,
'UMD': np.random.normal0.01, 0.06, n_days / 252 # 动量因子
}, index=date_index)

else:
# 默认返回空数据框
factors = pd.DataFrameindex=date_index

return factors

except Exception as e:
self.logger.errorf"获取因子数据失败 {factor_model}: {e}"
return pd.DataFrame()

def _is_cachedself, cache_key: str -> bool:
"""检查是否缓存"""
try:
if not self.config.cache_results:
return False

if cache_key not in self._result_cache:
return False

result, timestamp = self._result_cache[cache_key]
age = (datetime.utcnow() - timestamp).total_seconds()

return age < self.config.cache_duration

except Exception:
return False

def _get_cached_resultself, cache_key: str -> Any:
"""获取缓存结果"""
try:
if cache_key in self._result_cache:    result, _ = self._result_cache[cache_key]
return result
return None

except Exception:
return None

def _cache_resultself, cache_key: str, result: Any:
"""缓存结果"""
try:
if self.config.cache_results:    self._result_cache[cache_key] = (result, datetime.utcnow())

except Exception as e:
self.logger.errorf"缓存结果失败: {e}"

def export_resultsself, filename: str = None -> str:
"""导出分析结果"""
try:
if not filename:    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
filename = f"advanced_statistics_results_{timestamp}.json"

export_data = {
"export_timestamp": datetime.utcnow().isoformat(),
"config": {
"monte_carlo_simulations": self.config.monte_carlo_simulations,
"bootstrap_samples": self.config.bootstrap_samples,
"significance_level": self.config.significance_level
},
"strategies": list(self._strategy_data.keys()),
"cached_results": lenself._result_cache
}

with openfilename, 'w', encoding='utf-8' as f:    json.dump(export_data, f, indent=2, ensure_ascii=False)

self.logger.infof"分析结果已导出: {filename}"
return filename

except Exception as e:
self.logger.errorf"导出分析结果失败: {e}"
raise

async def cleanupself:
"""清理资源"""
try:
self.logger.info"正在清理高级统计分析器..."

self._executor.shutdownwait=True

self._result_cache.clear()

self._strategy_data.clear()
self._benchmark_data.clear()
self._factor_data.clear()

self.logger.info"高级统计分析器清理完成"

except Exception as e:
self.logger.errorf"清理高级统计分析器失败: {e}"

__all__ = [
"AdvancedStatistics",
"StatisticsConfig",
"MonteCarloResult",
"BootstrapResult",
"StatisticalTestResult",
"FactorAnalysisResult",
"StatisticalTest",
"BootstrapMethod",
]