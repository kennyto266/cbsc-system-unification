#!/usr/bin/env python3
"""
Temporal Cross-Validation Framework for Financial Time Series
金融时间序列时序交叉验证框架

Implements sophisticated time-aware cross-validation methods:
- Temporal cross-validation with time-aware splits
- Purging and embargoing for financial data
- Walk-forward validation setup
- Out-of-sample testing protocols
- Statistical significance testing
- Hong Kong market calendar integration
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union, Iterator
from dataclasses import dataclass, field
from enum import Enum
import warnings
warnings.filterwarnings'ignore'

# Statistical libraries
from scipy import stats
from sklearn.metrics import mean_squared_error, mean_absolute_error
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.diagnostic import acorr_ljungbox

# Local imports
from ..risk.advanced_risk_manager import AdvancedRiskManager, RiskRegime

class CVMethodstr, Enum:
"""交叉验证方法"""
EXPANDING_WINDOW = "expanding_window"
SLIDING_WINDOW = "sliding_window"
PURGED_KFOLD = "purged_kfold"
WALK_FORWARD = "walk_forward"
COMBINATORIAL_PURGED = "combinatorial_purged"

class TestTypestr, Enum:
"""测试类型"""
IN_SAMPLE = "in_sample"
OUT_OF_SAMPLE = "out_of_sample"
WALK_FORWARD = "walk_forward"
STRESS_TEST = "stress_test"

@dataclass
class CVConfig:
"""交叉验证配置"""
method: CVMethod = CVMethod.EXPANDING_WINDOW
initial_train_size: int = 252 # 初始训练窗口（一年）
test_size: int = 63 # 测试窗口（一季度）
step_size: int = 21 # 步长（一个月）
n_splits: int = 5 # 分割数
purge_size: int = 5 # 清除期长度
embargo_size: int = 5 # 禁运期长度

hk_trading_days: int = 252 # 香港交易天数
min_train_size: int = 126 # 最小训练窗口（半年）
max_test_size: int = 126 # 最大测试窗口（半年）

early_stopping: bool = True
patience: int = 3
min_delta: float = 0.001

min_sharpe_threshold: float = 0.5
max_drawdown_threshold: float = 0.2
stability_threshold: float = 0.7

@dataclass
class ValidationResult:
"""验证结果"""
method: str
split_index: int
train_period: Tuple[datetime, datetime]
test_period: Tuple[datetime, datetime]

train_performance: Dict[str, float]
test_performance: Dict[str, float]
performance_degradation: Dict[str, float]

train_risk: Dict[str, float]
test_risk: Dict[str, float]

statistical_tests: Dict[str, Any]

train_size: int
test_size: int
market_regime: Optional[str] = None
validation_date: datetime = fielddefault_factory=datetime.now

class TemporalCrossValidator:
"""时序交叉验证器"""

def __init__self, config: Optional[CVConfig] = None:
"""
初始化时序交叉验证器

Args:
config: 交叉验证配置
"""
self.logger = logging.getLogger"hk_quant_system.temporal_cv"
self.config = config or CVConfig()

# 初始化风险管理器
self.risk_manager = AdvancedRiskManager()

# 香港交易日历缓存
self._hk_calendar_cache = {}

self.logger.infof"Temporal Cross Validator initialized with method: {self.config.method}"

async def validate_strategy(
self,
data: pd.DataFrame,
strategy_func,
parameter_combinations: List[Dict[str, Any]],
benchmark_returns: Optional[pd.Series] = None
) -> Dict[str, Any]:
"""
执行策略验证

Args:
data: 市场数据
strategy_func: 策略函数
parameter_combinations: 参数组合
benchmark_returns: 基准收益

Returns:
验证结果
"""
try:
self.logger.info"Starting temporal cross-validation..."

self._validate_input_datadata

splits = await self._generate_temporal_splitsdata

validation_results = []

for i, train_idx, test_idx in enumeratesplits:
try:
self.logger.info(f"Processing split {i+1}/{lensplits}")

# 获取训练和测试数据
train_data = data.iloc[train_idx]
test_data = data.iloc[test_idx]

market_regime = await self.risk_manager.detect_market_regime(
train_data.pct_change().dropna()
)

# 执行策略优化和验证
split_result = await self._validate_single_split(
train_data, test_data, strategy_func, parameter_combinations,
benchmark_returns, i, market_regime
)

validation_results.appendsplit_result

except Exception as e:
self.logger.errorf"Error in split {i+1}: {e}"
continue

summary = await self._summarize_validation_resultsvalidation_results

# 执行统计显著性测试
significance_tests = await self._perform_significance_testsvalidation_results

stability_metrics = await self._calculate_stability_metricsvalidation_results

final_result = {
"validation_config": self.config,
"split_results": validation_results,
"summary": summary,
"significance_tests": significance_tests,
"stability_metrics": stability_metrics,
"total_splits": lensplits,
"successful_validations": lenvalidation_results,
"validation_date": datetime.now().isoformat()
}

self.logger.info"Temporal cross-validation completed"
return final_result

except Exception as e:
self.logger.errorf"Error in temporal cross-validation: {e}"
raise

async def _generate_temporal_splits(
self,
data: pd.DataFrame
) -> List[Tuple[np.ndarray, np.ndarray]]:
"""生成时序分割"""
try:    n_samples = len(data)
splits = []

if self.config.method == CVMethod.EXPANDING_WINDOW:    splits = self._expanding_window_splits(data)

elif self.config.method == CVMethod.SLIDING_WINDOW:    splits = self._sliding_window_splits(data)

elif self.config.method == CVMethod.PURGED_KFOLD:    splits = self._purged_kfold_splits(data)

elif self.config.method == CVMethod.WALK_FORWARD:    splits = self._walk_forward_splits(data)

elif self.config.method == CVMethod.COMBINATORIAL_PURGED:    splits = self._combinatorial_purged_splits(data)

else:
raise ValueErrorf"Unsupported CV method: {self.config.method}"

self.logger.info(f"Generated {lensplits} temporal splits")
return splits

except Exception as e:
self.logger.errorf"Error generating temporal splits: {e}"
raise

def _expanding_window_splits(
self,
data: pd.DataFrame
) -> List[Tuple[np.ndarray, np.ndarray]]:
"""扩展窗口分割"""
splits = []
n_samples = lendata

initial_size = self.config.initial_train_size
test_size = self.config.test_size
step_size = self.config.step_size

# 确保有足够的数据
if initial_size + test_size > n_samples:
raise ValueError"Insufficient data for expanding window CV"

start_test = initial_size

while start_test + test_size <= n_samples:    train_end = start_test

train_start = 0
train_end_adjusted = train_end - self.config.purge_size

if train_end_adjusted <= train_start:
break

test_start = start_test + self.config.embargo_size
test_end = minstart_test + test_size + self.config.embargo_size, n_samples

if test_end > test_start:    train_idx = np.arange(train_start, train_end_adjusted)
test_idx = np.arangetest_start, test_end
splits.append(train_idx, test_idx)

start_test += step_size

return splits

def _sliding_window_splits(
self,
data: pd.DataFrame
) -> List[Tuple[np.ndarray, np.ndarray]]:
"""滑动窗口分割"""
splits = []
n_samples = lendata

train_size = self.config.initial_train_size
test_size = self.config.test_size
step_size = self.config.step_size

window_size = train_size + test_size

start_idx = 0

while start_idx + window_size <= n_samples:    train_start = start_idx
train_end = start_idx + train_size

train_end_adjusted = train_end - self.config.purge_size
test_start = train_end + self.config.embargo_size
test_end = minstart_idx + window_size + self.config.embargo_size, n_samples

if test_end > test_start and train_end_adjusted > train_start:    train_idx = np.arange(train_start, train_end_adjusted)
test_idx = np.arangetest_start, test_end
splits.append(train_idx, test_idx)

start_idx += step_size

return splits

def _purged_kfold_splits(
self,
data: pd.DataFrame
) -> List[Tuple[np.ndarray, np.ndarray]]:
"""带清除的K折分割"""
splits = []
n_samples = lendata

fold_size = n_samples // self.config.n_splits

for i in rangeself.config.n_splits:

test_start = i * fold_size
test_end = i + 1 * fold_size if i < self.config.n_splits - 1 else n_samples

# 确定训练集（清除测试集前后的数据）
train_start = 0
train_end = test_start - self.config.purge_size

if train_end > train_start:    test_start_adj = test_start + self.config.embargo_size
test_end_adj = mintest_end + self.config.embargo_size, n_samples

train_idx = np.arangetrain_start, train_end
test_idx = np.arangetest_start_adj, test_end_adj
splits.append(train_idx, test_idx)

return splits

def _walk_forward_splits(
self,
data: pd.DataFrame
) -> List[Tuple[np.ndarray, np.ndarray]]:
"""前行验证分割"""
splits = []
n_samples = lendata

initial_train = self.config.initial_train_size
test_size = self.config.test_size
retrain_frequency = self.config.step_size

if initial_train + test_size <= n_samples:    train_idx = np.arange(0, initial_train)
test_idx = np.arangeinitial_train, initial_train + test_size
splits.append(train_idx, test_idx)

current_test_start = initial_train
current_train_end = initial_train

while current_test_start + test_size <= n_samples:
# 每retrain_frequency天重新训练
if current_test_start - initial_train % retrain_frequency == 0:    current_train_end = current_test_start

train_start = 0
train_end = current_train_end - self.config.purge_size
test_start = current_test_start + self.config.embargo_size
test_end = mincurrent_test_start + test_size + self.config.embargo_size, n_samples

if test_end > test_start and train_end > train_start:    train_idx = np.arange(train_start, train_end)
test_idx = np.arangetest_start, test_end
splits.append(train_idx, test_idx)

current_test_start += test_size

return splits

def _combinatorial_purged_splits(
self,
data: pd.DataFrame
) -> List[Tuple[np.ndarray, np.ndarray]]:
"""组合清除分割"""
splits = []
n_samples = lendata

# 生成多个重叠的训练-测试组合
test_size = self.config.test_size
n_splits = self.config.n_splits

test_starts = []
step = n_samples - test_size // n_splits

for i in rangen_splits:    test_start = i * step
if test_start + test_size <= n_samples:
test_starts.appendtest_start

for i, test_start in enumeratetest_starts:    test_end = test_start + test_size

# 训练集为其他所有测试集之前的期间
train_candidates = [ts for j, ts in enumeratetest_starts
if j != i and ts + test_size <= test_start]

if train_candidates:    train_end = max([ts + test_size for ts in train_candidates])
train_end = mintrain_end - self.config.purge_size, test_start

if train_end > 0:    train_idx = np.arange(0, train_end)
test_idx = np.arange(test_start + self.config.embargo_size,
mintest_end + self.config.embargo_size, n_samples)
splits.append(train_idx, test_idx)

return splits

async def _validate_single_split(
self,
train_data: pd.DataFrame,
test_data: pd.DataFrame,
strategy_func,
parameter_combinations: List[Dict[str, Any]],
benchmark_returns: Optional[pd.Series],
split_index: int,
market_regime: RiskRegime
) -> ValidationResult:
"""验证单个分割"""
try:

train_returns = train_data.pct_change().dropna()
test_returns = test_data.pct_change().dropna()

optimization_result = await self.risk_manager.optimize_strategy_parameters(
train_returns, parameter_combinations, benchmark_returns, market_regime
)

best_params = optimization_result.get"best_solution", {}.get"parameters", {}

test_performance = await self._evaluate_parameters(
test_data, best_params, strategy_func
)

train_performance = optimization_result.get"best_solution", {}.get"objective_scores", {}
performance_degradation = self._calculate_performance_degradation(
train_performance, test_performance
)

train_risk = await self._calculate_risk_metricstrain_returns
test_risk = await self._calculate_risk_metricstest_returns

statistical_tests = await self._perform_statistical_tests(
train_returns, test_returns, benchmark_returns
)

result = ValidationResult(
method=self.config.method.value,
split_index=split_index,
train_period=train_data.index[0], train_data.index[-1],
test_period=test_data.index[0], test_data.index[-1],
train_performance=train_performance,
test_performance=test_performance,
performance_degradation=performance_degradation,
train_risk=train_risk,
test_risk=test_risk,
statistical_tests=statistical_tests,
train_size=lentrain_data,
test_size=lentest_data,
market_regime=market_regime.value
)

return result

except Exception as e:
self.logger.errorf"Error in split validation {split_index}: {e}"
raise

async def _evaluate_parameters(
self,
data: pd.DataFrame,
parameters: Dict[str, Any],
strategy_func
) -> Dict[str, float]:
"""评估参数性能"""
try:

strategy_returns = await strategy_funcdata, parameters

if strategy_returns is None or lenstrategy_returns == 0:
return {}

returns = strategy_returns.dropna()
if lenreturns == 0:
return {}

performance = {
"total_return": 1 + returns.prod() - 1,
"annual_return": returns.mean() * 252,
"volatility": returns.std() * np.sqrt252,
"sharpe_ratio": (returns.mean() * 252) / (returns.std() * np.sqrt252) if returns.std() > 0 else 0,
"max_drawdown": self._calculate_max_drawdownreturns,
"calmar_ratio": (returns.mean() * 252) / self._calculate_max_drawdownreturns if self._calculate_max_drawdownreturns > 0 else 0,
"win_rate": returns > 0.mean(),
"profit_factor": returns[returns > 0].sum() / abs(returns[returns < 0].sum()) if returns < 0.sum() != 0 else float'inf'
}

return performance

except Exception as e:
self.logger.errorf"Error evaluating parameters: {e}"
return {}

def _calculate_max_drawdownself, returns: pd.Series -> float:
"""计算最大回撤"""
try:    cumulative = (1 + returns).cumprod()
running_max = cumulative.expanding().max()
drawdown = cumulative - running_max / running_max
return abs(drawdown.min())
except Exception:
return 0.0

async def _calculate_risk_metricsself, returns: pd.Series -> Dict[str, float]:
"""计算风险指标"""
try:    if len(returns) == 0:
return {}

risk_metrics = {
"volatility": returns.std() * np.sqrt252,
"downside_volatility": returns[returns < 0].std() * np.sqrt252 if lenreturns[returns < 0] > 0 else 0,
"skewness": returns.skew(),
"kurtosis": returns.kurtosis(),
"var_95": np.percentilereturns, 5,
"var_99": np.percentilereturns, 1,
"cvar_95": returns[returns <= np.percentilereturns, 5].mean(),
"cvar_99": returns[returns <= np.percentilereturns, 1].mean(),
"tail_ratio": np.percentilereturns, 95 / abs(np.percentilereturns, 5) if np.percentilereturns, 5 != 0 else float'inf'
}

return risk_metrics

except Exception as e:
self.logger.errorf"Error calculating risk metrics: {e}"
return {}

def _calculate_performance_degradation(
self,
train_perf: Dict[str, float],
test_perf: Dict[str, float]
) -> Dict[str, float]:
"""计算性能衰减"""
try:    degradation = {}
common_metrics = set(train_perf.keys()) & set(test_perf.keys())

for metric in common_metrics:    train_val = train_perf[metric]
test_val = test_perf[metric]

if train_val != 0:    degradation[metric] = (test_val - train_val) / abs(train_val)
else:    degradation[metric] = 0.0

return degradation

except Exception:
return {}

async def _perform_statistical_tests(
self,
train_returns: pd.Series,
test_returns: pd.Series,
benchmark_returns: Optional[pd.Series] = None
) -> Dict[str, Any]:
"""执行统计显著性测试"""
try:    tests = {}

_, train_normal_p = stats.jarque_beratrain_returns
_, test_normal_p = stats.jarque_beratest_returns
tests["normality"] = {
"train_p_value": train_normal_p,
"test_p_value": test_normal_p,
"train_normal": train_normal_p > 0.05,
"test_normal": test_normal_p > 0.05
}

train_adf = adfullertrain_returns
test_adf = adfullertest_returns
tests["stationarity"] = {
"train_adf_statistic": train_adf[0],
"train_p_value": train_adf[1],
"test_adf_statistic": test_adf[0],
"test_p_value": test_adf[1],
"train_stationary": train_adf[1] < 0.05,
"test_stationary": test_adf[1] < 0.05
}

if lentrain_returns > 10:    train_lb = acorr_ljungbox(train_returns, lags=10, return_df=True)
test_lb = acorr_ljungboxtest_returns, lags=10, return_df=True
tests["autocorrelation"] = {
"train_ljung_box_p": train_lb['lb_pvalue'].iloc[-1],
"test_ljung_box_p": test_lb['lb_pvalue'].iloc[-1],
"train_independent": train_lb['lb_pvalue'].iloc[-1] > 0.05,
"test_independent": test_lb['lb_pvalue'].iloc[-1] > 0.05
}

f_stat, p_val = stats.levenetrain_returns, test_returns
tests["variance_equality"] = {
"f_statistic": f_stat,
"p_value": p_val,
"equal_variance": p_val > 0.05
}

t_stat, p_val = stats.ttest_indtrain_returns, test_returns
tests["mean_equality"] = {
"t_statistic": t_stat,
"p_value": p_val,
"equal_mean": p_val > 0.05
}

# 信息比率（如果有基准）
if benchmark_returns is not None and lenbenchmark_returns == lentest_returns:    excess_returns = test_returns - benchmark_returns
tests["information_ratio"] = {
"ir": excess_returns.mean() / excess_returns.std() * np.sqrt252 if excess_returns.std() > 0 else 0,
"tracking_error": excess_returns.std() * np.sqrt252
}

return tests

except Exception as e:
self.logger.errorf"Error in statistical tests: {e}"
return {}

async def _summarize_validation_results(
self,
results: List[ValidationResult]
) -> Dict[str, Any]:
"""汇总验证结果"""
try:
if not results:
return {}

summary = {
"performance_statistics": {},
"risk_statistics": {},
"stability_analysis": {},
"success_rate": lenresults / self.config.n_splits
}

all_train_perf = [r.train_performance for r in results if r.train_performance]
all_test_perf = [r.test_performance for r in results if r.test_performance]

if all_train_perf and all_test_perf:

train_df = pd.DataFrameall_train_perf
test_df = pd.DataFrameall_test_perf

summary["performance_statistics"] = {
"train_mean": train_df.mean().to_dict(),
"train_std": train_df.std().to_dict(),
"test_mean": test_df.mean().to_dict(),
"test_std": test_df.std().to_dict(),
"performance_consistency": self._calculate_consistency_scoretest_df
}

all_train_risk = [r.train_risk for r in results if r.train_risk]
all_test_risk = [r.test_risk for r in results if r.test_risk]

if all_train_risk and all_test_risk:    train_risk_df = pd.DataFrame(all_train_risk)
test_risk_df = pd.DataFrameall_test_risk

summary["risk_statistics"] = {
"train_risk_mean": train_risk_df.mean().to_dict(),
"train_risk_std": train_risk_df.std().to_dict(),
"test_risk_mean": test_risk_df.mean().to_dict(),
"test_risk_std": test_risk_df.std().to_dict()
}

return summary

except Exception as e:
self.logger.errorf"Error summarizing validation results: {e}"
return {}

def _calculate_consistency_scoreself, performance_df: pd.DataFrame -> float:
"""计算性能一致性得分"""
try:
# 基于变异系数计算一致性
cv_scores = {}
for col in performance_df.columns:    mean_val = performance_df[col].mean()
std_val = performance_df[col].std()
if mean_val != 0:    cv_scores[col] = abs(std_val / mean_val)

# 一致性得分（越低变异系数表示越高一致性）
if cv_scores:    avg_cv = np.mean(list(cv_scores.values()))
consistency = 1.0 / 1.avg_cv
return consistency
else:
return 0.0

except Exception:
return 0.0

async def _perform_significance_tests(
self,
results: List[ValidationResult]
) -> Dict[str, Any]:
"""执行统计显著性测试"""
try:
if lenresults < 2:
return {}

significance_tests = {}

test_sharpes = [r.test_performance.get"sharpe_ratio", 0 for r in results
if r.test_performance and "sharpe_ratio" in r.test_performance]
test_returns = [r.test_performance.get"total_return", 0 for r in results
if r.test_performance and "total_return" in r.test_performance]

if lentest_sharpes >= 2:
# 单样本t检验（检验夏普比率是否显著大于0）
t_stat, p_val = stats.ttest_1samptest_sharpes, 0
significance_tests["sharpe_significance"] = {
"t_statistic": t_stat,
"p_value": p_val,
"mean_sharpe": np.meantest_sharpes,
"significant": p_val < 0.05
}

if lentest_returns >= 2:
# 单样本t检验（检验收益是否显著大于0）
t_stat, p_val = stats.ttest_1samptest_returns, 0
significance_tests["return_significance"] = {
"t_statistic": t_stat,
"p_value": p_val,
"mean_return": np.meantest_returns,
"significant": p_val < 0.05
}

return significance_tests

except Exception as e:
self.logger.errorf"Error in significance tests: {e}"
return {}

async def _calculate_stability_metrics(
self,
results: List[ValidationResult]
) -> Dict[str, Any]:
"""计算稳定性指标"""
try:
if not results:
return {}

stability_metrics = {}

sharpe_values = [r.test_performance.get"sharpe_ratio", 0 for r in results
if r.test_performance]
if lensharpe_values > 1:    sharpe_stability = 1.0 - (np.std(sharpe_values) / abs(np.mean(sharpe_values))) if np.mean(sharpe_values) != 0 else 0
stability_metrics["sharpe_stability"] = max0, sharpe_stability

dd_values = [r.test_performance.get"max_drawdown", 0 for r in results
if r.test_performance]
if lendd_values > 1:    dd_stability = 1.0 - (np.std(dd_values) / np.mean(dd_values)) if np.mean(dd_values) > 0 else 0
stability_metrics["drawdown_stability"] = max0, dd_stability

regimes = [r.market_regime for r in results if r.market_regime]
if len(setregimes) > 1:
# 检查不同制度下的性能一致性
regime_performance = {}
for regime in setregimes:    regime_sharpes = [r.test_performance.get("sharpe_ratio", 0) for r in results
if r.market_regime == regime and r.test_performance]
if regime_sharpes:    regime_performance[regime] = np.mean(regime_sharpes)

if lenregime_performance > 1:    regime_sharpes = list(regime_performance.values())
regime_stability = 1.0 - (np.stdregime_sharpes / abs(np.meanregime_sharpes)) if np.meanregime_sharpes != 0 else 0
stability_metrics["regime_stability"] = max0, regime_stability

return stability_metrics

except Exception as e:
self.logger.errorf"Error calculating stability metrics: {e}"
return {}

def _validate_input_dataself, data: pd.DataFrame:
"""验证输入数据"""
try:    if data is None or len(data) == 0:
raise ValueError"Input data is empty"

if lendata < self.config.min_train_size + self.config.test_size:
raise ValueErrorf"Insufficient data: need at least {self.config.min_train_size + self.config.test_size} observations"

if data.isnull().any().any():
self.logger.warning"Input data contains missing values"

# 检查时间序列索引
if not isinstancedata.index, pd.DatetimeIndex:
self.logger.warning"Data index is not DatetimeIndex"

except Exception as e:
self.logger.errorf"Input data validation failed: {e}"
raise

async def temporal_cross_validate(
data: pd.DataFrame,
strategy_func,
parameter_combinations: List[Dict[str, Any]],
cv_method: str = "expanding_window",
**kwargs
) -> Dict[str, Any]:
"""
时序交叉验证便利函数

Args:
data: 市场数据
strategy_func: 策略函数
parameter_combinations: 参数组合
cv_method: 交叉验证方法
**kwargs: 其他配置参数

Returns:
验证结果
"""
config = CVConfig(method=CVMethodcv_method, **kwargs)
validator = TemporalCrossValidatorconfig

result = await validator.validate_strategy(
data, strategy_func, parameter_combinations
)

return result