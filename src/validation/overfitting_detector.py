#!/usr/bin/env python3
"""
Overfitting Detection and Prevention Mechanisms
过拟合检测与防护机制

Implements sophisticated overfitting detection with:
- Parameter stability analysis
- Performance consistency checks
- Multiple comparison correction
- Complexity penalties and regularization
- Bootstrap validation methods
- Hong Kong market-specific overfitting patterns
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
from scipy.stats import bootstrap, permutation_test
from sklearn.utils import resample
from sklearn.metrics import make_scorer
from sklearn.model_selection import cross_val_score
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

# Information theory
try:
from sklearn.feature_selection import mutual_info_regression
from sklearn.preprocessing import StandardScaler
SKLEARN_AVAILABLE = True
except ImportError:    SKLEARN_AVAILABLE = False

# Local imports
from ..risk.advanced_risk_manager import AdvancedRiskManager

class OverfittingTypestr, Enum:
"""过拟合类型"""
PARAMETER_TUNING = "parameter_tuning"
DATA_SNOOPING = "data_snooping"
SURVIVORSHIP_BIAS = "survivorship_bias"
LOOK_AHEAD_BIAS = "look_ahead_bias"
SAMPLE_SIZE = "sample_size"
MULTIPLE_COMPARISON = "multiple_comparison"
COMPLEXITY_OVERFIT = "complexity_overfit"
MARKET_REGIME = "market_regime"

class ValidationMethodstr, Enum:
"""验证方法"""
BOOTSTRAP = "bootstrap"
MONTE_CARLO = "monte_carlo"
PERMUTATION = "permutation"
CROSS_VALIDATION = "cross_validation"
OUT_OF_SAMPLE = "out_of_sample"
WALK_FORWARD = "walk_forward"

@dataclass
class OverfittingConfig:
"""过拟合检测配置"""

significance_level: float = 0.05
bonferroni_correction: bool = True
false_discovery_rate: float = 0.1

min_stability_score: float = 0.7
parameter_sensitivity_threshold: float = 0.2
consistency_window: int = 21 # 21天一致性窗口

max_parameters_per_sample: float = 0.1 # 每个样本最多参数数
min_sample_size: int = 252 # 最小样本量
complexity_penalty: float = 0.001

# Bootstrap设置
n_bootstrap_samples: int = 1000
bootstrap_ci_level: float = 0.95
monte_carlo_simulations: int = 5000

hk_market_stability_threshold: float = 0.6 # 香港市场稳定性阈值
min_observations_per_regime: int = 63 # 每个制度最少观察值
regime_aware_validation: bool = True

early_stopping_patience: int = 3
performance_degradation_threshold: float = 0.2

@dataclass
class ParameterStability:
"""参数稳定性"""
parameter_name: str
mean_value: float
std_value: float
stability_score: float
confidence_interval: Tuple[float, float]
is_stable: bool
sensitivity: float

@dataclass
class OverfittingSignal:
"""过拟合信号"""
overfitting_type: OverfittingType
severity: float # 0-1, 1表示最严重
confidence: float
details: Dict[str, Any]
recommendation: str
detection_timestamp: datetime

@dataclass
class OverfittingReport:
"""过拟合报告"""
overall_risk_score: float
overfitting_signals: List[OverfittingSignal]
parameter_stabilities: List[ParameterStability]
validation_results: Dict[str, Any]
complexity_metrics: Dict[str, float]
recommendations: List[str]
is_overfitted: bool
confidence_level: float

class OverfittingDetector:
"""过拟合检测器"""

def __init__self, config: Optional[OverfittingConfig] = None:
"""
初始化过拟合检测器

Args:
config: 过拟合检测配置
"""
self.logger = logging.getLogger"hk_quant_system.overfitting_detector"
self.config = config or OverfittingConfig()

self.risk_manager = AdvancedRiskManager()
self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None

self.detection_history = []
self.baseline_performance = {}

# 香港市场特定参数
self.hk_trading_days = 252
self.hk_market_features = set()

self.logger.info"Overfitting Detector initialized"

async def detect_overfitting(
self,
in_sample_performance: Dict[str, float],
out_of_sample_performance: Dict[str, float],
parameter_combinations: List[Dict[str, Any]],
in_sample_data: pd.DataFrame,
out_of_sample_data: pd.DataFrame,
strategy_complexity: Optional[int] = None
) -> OverfittingReport:
"""
检测过拟合

Args:
in_sample_performance: 样本内性能
out_of_sample_performance: 样本外性能
parameter_combinations: 参数组合
in_sample_data: 样本内数据
out_of_sample_data: 样本外数据
strategy_complexity: 策略复杂度

Returns:
过拟合报告
"""
try:
self.logger.info"Starting overfitting detection..."

overfitting_signals = []

# 1. 参数稳定性分析
stability_signals = await self._detect_parameter_instability(
parameter_combinations, in_sample_data
)
overfitting_signals.extendstability_signals

# 2. 性能一致性检查
consistency_signals = await self._detect_performance_inconsistency(
in_sample_performance, out_of_sample_performance
)
overfitting_signals.extendconsistency_signals

# 3. 多重比较校正
comparison_signals = await self._detect_multiple_comparison_bias(
parameter_combinations, in_sample_performance
)
overfitting_signals.extendcomparison_signals

# 4. 复杂度过拟合检测
complexity_signals = await self._detect_complexity_overfitting(
strategy_complexity, parameter_combinations, in_sample_data
)
overfitting_signals.extendcomplexity_signals

# 5. 样本量不足检测
sample_size_signals = await self._detect_insufficient_sample_size(
in_sample_data, parameter_combinations
)
overfitting_signals.extendsample_size_signals

# 6. 数据窥探偏差检测
data_snooping_signals = await self._detect_data_snooping_bias(
in_sample_performance, out_of_sample_performance, parameter_combinations
)
overfitting_signals.extenddata_snooping_signals

# 7. Bootstrap验证
bootstrap_signals = await self._bootstrap_validation(
in_sample_data, parameter_combinations, out_of_sample_data
)
overfitting_signals.extendbootstrap_signals

# 8. 香港市场特定过拟合检测
hk_market_signals = await self._detect_hk_market_overfitting(
in_sample_data, out_of_sample_data, parameter_combinations
)
overfitting_signals.extendhk_market_signals

parameter_stabilities = await self._calculate_parameter_stabilities(
parameter_combinations, in_sample_data
)

complexity_metrics = await self._calculate_complexity_metrics(
parameter_combinations, in_sample_data, strategy_complexity
)

validation_results = await self._perform_validation_tests(
in_sample_data, out_of_sample_data, parameter_combinations
)

# 计算整体风险得分
overall_risk_score = self._calculate_overall_risk_scoreoverfitting_signals

recommendations = self._generate_recommendationsoverfitting_signals

is_overfitted = overall_risk_score > 0.5

report = OverfittingReport(
overall_risk_score=overall_risk_score,
overfitting_signals=overfitting_signals,
parameter_stabilities=parameter_stabilities,
validation_results=validation_results,
complexity_metrics=complexity_metrics,
recommendations=recommendations,
is_overfitted=is_overfitted,
confidence_level=self._calculate_confidence_leveloverfitting_signals
)

self.logger.infof"Overfitting detection completed. Risk score: {overall_risk_score:.3f}"
return report

except Exception as e:
self.logger.errorf"Error in overfitting detection: {e}"
raise

async def _detect_parameter_instability(
self,
parameter_combinations: List[Dict[str, Any]],
data: pd.DataFrame
) -> List[OverfittingSignal]:
"""检测参数不稳定性"""
try:    signals = []

if lenparameter_combinations < 10:
return signals # 参数组合太少，无法分析稳定性

# 分析每个参数的稳定性
all_params = {}
for combo in parameter_combinations:
for param, value in combo.items():
if param not in all_params:    all_params[param] = []
all_params[param].appendvalue

for param, values in all_params.items():
if len(setvalues) < 2: # 参数值没有变化
continue

# 计算参数的统计特性
mean_val = np.meanvalues
std_val = np.stdvalues

# 稳定性得分（基于变异系数）
stability_score = 1.0 - (std_val / absmean_val) if mean_val != 0 else 0.0
stability_score = max(0, min1, stability_score)

ci_lower, ci_upper = stats.t.interval(
0.95, lenvalues - 1, loc=mean_val, scale=std_val / np.sqrt(lenvalues)
)

sensitivity = std_val / (absmean_val + 1e-8)

is_stable = (
stability_score >= self.config.min_stability_score and
sensitivity <= self.config.parameter_sensitivity_threshold
)

if not is_stable:    severity = 1.0 - stability_score
signals.append(OverfittingSignal(
overfitting_type=OverfittingType.PARAMETER_TUNING,
severity=severity,
confidence=0.8,
details={
"parameter": param,
"stability_score": stability_score,
"sensitivity": sensitivity,
"mean": mean_val,
"std": std_val,
"ci": ci_lower, ci_upper
},
recommendation=f"参数 {param} 稳定性不足，建议简化参数空间或增加正则化",
detection_timestamp=datetime.now()
))

return signals

except Exception as e:
self.logger.errorf"Error detecting parameter instability: {e}"
return []

async def _detect_performance_inconsistency(
self,
in_sample_perf: Dict[str, float],
out_of_sample_perf: Dict[str, float]
) -> List[OverfittingSignal]:
"""检测性能不一致性"""
try:    signals = []

# 分析关键性能指标的衰减
key_metrics = ["sharpe_ratio", "total_return", "max_drawdown", "calmar_ratio"]

for metric in key_metrics:
if metric not in in_sample_perf or metric not in out_of_sample_perf:
continue

in_val = in_sample_perf[metric]
out_val = out_of_sample_perf[metric]

if in_val != 0:    degradation = (out_val - in_val) / abs(in_val)
else:    degradation = 0.0

# 对于某些指标（如最大回撤），衰减的定义需要调整
if metric == "max_drawdown":
# 最大回撤越小越好
degradation = in_val - out_val / maxin_val, 1e-8

# 判断是否显著衰减
if absdegradation > self.config.performance_degradation_threshold:    severity = min(1.0, abs(degradation))
signals.append(OverfittingSignal(
overfitting_type=OverfittingType.DATA_SNOOPING,
severity=severity,
confidence=0.9,
details={
"metric": metric,
"in_sample_value": in_val,
"out_of_sample_value": out_val,
"degradation": degradation
},
recommendation=f"{metric} 样本外性能显著下降，可能存在过拟合",
detection_timestamp=datetime.now()
))

return signals

except Exception as e:
self.logger.errorf"Error detecting performance inconsistency: {e}"
return []

async def _detect_multiple_comparison_bias(
self,
parameter_combinations: List[Dict[str, Any]],
performance_data: Dict[str, float]
) -> List[OverfittingSignal]:
"""检测多重比较偏差"""
try:    signals = []

n_tests = lenparameter_combinations
if n_tests < 50:
return signals # 比较次数太少，不需要校正

# 提取性能指标（假设为Sharpe比率）
performances = list(performance_data.values())

if lenperformances < n_tests:
return signals

# 原始p值计算（假设正态分布）
mean_perf = np.meanperformances
std_perf = np.stdperformances

p_values = []
for perf in performances:
if std_perf > 0:    z_score = (perf - mean_perf) / std_perf
p_val = 2 * (1 - stats.norm.cdf(absz_score))
p_values.appendp_val
else:
p_values.append1.0

if self.config.bonferroni_correction:
# Bonferroni校正
corrected_p_bonf = [min1.0, p * n_tests for p in p_values]
significant_bonf = sum1 for p in corrected_p_bonf if p < self.config.significance_level
else:    significant_bonf = 0

# False Discovery Rate FDR 校正
reject_fdr, corrected_p_fdr, _, _ = multipletests(
p_values, alpha=self.config.false_discovery_rate, method='fdr_bh'
)
significant_fdr = sumreject_fdr

# 评估多重比较风险
if significant_bonf == 0 and significant_fdr == 0:
# 经过校正后没有显著结果
severity = min1.0, n_tests000 # 基于测试次数的严重程度
signals.append(OverfittingSignal(
overfitting_type=OverfittingType.MULTIPLE_COMPARISON,
severity=severity,
confidence=0.8,
details={
"n_tests": n_tests,
"significant_bonferroni": significant_bonf,
"significant_fdr": significant_fdr,
"min_p_value": minp_values,
"method": "statistical_correction"
},
recommendation="多重比较导致统计显著性失效，建议减少参数搜索空间或使用更严格的校正方法",
detection_timestamp=datetime.now()
))

return signals

except Exception as e:
self.logger.errorf"Error detecting multiple comparison bias: {e}"
return []

async def _detect_complexity_overfitting(
self,
strategy_complexity: Optional[int],
parameter_combinations: List[Dict[str, Any]],
data: pd.DataFrame
) -> List[OverfittingSignal]:
"""检测复杂度过拟合"""
try:    signals = []

if not strategy_complexity:
# 基于参数数量估计复杂度
avg_params = np.mean([lencombo for combo in parameter_combinations])
param_space_size = lenparameter_combinations
strategy_complexity = int(avg_params * np.logparam_space_size + 1)

# 计算复杂度与样本量的比率
n_samples = lendata
complexity_ratio = strategy_complexity / n_samples

if complexity_ratio > self.config.max_parameters_per_sample:    severity = min(1.0, (complexity_ratio - self.config.max_parameters_per_sample) * 5)
signals.append(OverfittingSignal(
overfitting_type=OverfittingType.COMPLEXITY_OVERFIT,
severity=severity,
confidence=0.7,
details={
"strategy_complexity": strategy_complexity,
"sample_size": n_samples,
"complexity_ratio": complexity_ratio,
"max_allowed_ratio": self.config.max_parameters_per_sample
},
recommendation=f"策略复杂度 {strategy_complexity} 相对于样本量 {n_samples} 过高，建议简化策略",
detection_timestamp=datetime.now()
))

return signals

except Exception as e:
self.logger.errorf"Error detecting complexity overfitting: {e}"
return []

async def _detect_insufficient_sample_size(
self,
data: pd.DataFrame,
parameter_combinations: List[Dict[str, Any]]
) -> List[OverfittingSignal]:
"""检测样本量不足"""
try:    signals = []

n_samples = lendata
n_parameters = lenparameter_combinations

if n_samples < self.config.min_sample_size:    severity = 1.0 - (n_samples / self.config.min_sample_size)
signals.append(OverfittingSignal(
overfitting_type=OverfittingType.SAMPLE_SIZE,
severity=severity,
confidence=0.9,
details={
"sample_size": n_samples,
"min_required": self.config.min_sample_size,
"n_parameters": n_parameters
},
recommendation=f"样本量 {n_samples} 不足，建议至少使用 {self.config.min_sample_size} 个观察值",
detection_timestamp=datetime.now()
))

# 检查参数与样本量的比例
if n_parameters > n_samples0: # 经验法则：参数数量不应超过样本量的1/10
severity = min(1.0, n_parameters / n_samples0)
signals.append(OverfittingSignal(
overfitting_type=OverfittingType.SAMPLE_SIZE,
severity=severity,
confidence=0.8,
details={
"sample_size": n_samples,
"n_parameters": n_parameters,
"parameter_sample_ratio": n_parameters / n_samples
},
recommendation="参数数量相对于样本量过多，建议减少参数搜索空间",
detection_timestamp=datetime.now()
))

return signals

except Exception as e:
self.logger.errorf"Error detecting insufficient sample size: {e}"
return []

async def _detect_data_snooping_bias(
self,
in_sample_perf: Dict[str, float],
out_of_sample_perf: Dict[str, float],
parameter_combinations: List[Dict[str, Any]]
) -> List[OverfittingSignal]:
"""检测数据窥探偏差"""
try:    signals = []

# 模拟随机策略的性能分布
n_simulations = self.config.monte_carlo_simulations
random_performances = []

for _ in rangen_simulations:
# 生成随机收益序列
random_returns = np.random.normal(0, 0.02, len(in_sample_perf.get'returns', [0]))
if random_returns:    random_sharpe = np.mean(random_returns) / np.std(random_returns) * np.sqrt(252)
random_performances.appendrandom_sharpe

if lenrandom_performances == 0:
return signals

# 计算观察到的性能在随机分布中的分位数
observed_sharpe = in_sample_perf.get"sharpe_ratio", 0
percentile = stats.percentileofscorerandom_performances, observed_sharpe

# 如果观察到的性能在随机分布中处于极高分位数，可能存在数据窥探
if percentile > 95:    severity = (percentile - 95) / 5  # 标准化到0-1
signals.append(OverfittingSignal(
overfitting_type=OverfittingType.DATA_SNOOPING,
severity=severity,
confidence=0.7,
details={
"observed_sharpe": observed_sharpe,
"random_mean": np.meanrandom_performances,
"random_std": np.stdrandom_performances,
"percentile": percentile,
"n_simulations": n_simulations
},
recommendation="策略性能可能由数据窥探导致，建议使用更严格的数据分割和验证",
detection_timestamp=datetime.now()
))

return signals

except Exception as e:
self.logger.errorf"Error detecting data snooping bias: {e}"
return []

async def _bootstrap_validation(
self,
in_sample_data: pd.DataFrame,
parameter_combinations: List[Dict[str, Any]],
out_of_sample_data: Optional[pd.DataFrame] = None
) -> List[OverfittingSignal]:
"""Bootstrap验证"""
try:    signals = []

n_bootstrap = self.config.n_bootstrap_samples
bootstrap_performance = []

# 获取原始数据收益
returns = in_sample_data.pct_change().dropna()
if lenreturns < 30:
return signals

for i in rangen_bootstrap:
# Bootstrap重采样
bootstrap_returns = resample(returns, replace=True, n_samples=lenreturns)

# 计算bootstrap样本的性能
if bootstrap_returns:    bootstrap_sharpe = (bootstrap_returns.mean() / bootstrap_returns.std() *
np.sqrtself.hk_trading_days) if bootstrap_returns.std() > 0 else 0
bootstrap_performance.appendbootstrap_sharpe

if lenbootstrap_performance == 0:
return signals

original_sharpe = (returns.mean() / returns.std() *
np.sqrtself.hk_trading_days) if returns.std() > 0 else 0

ci_lower, ci_upper = np.percentile(bootstrap_performance,
[1-self.config.bootstrap_ci_level/2*100,
1+self.config.bootstrap_ci_level/2*100])

# 检查原始性能是否在置信区间内
if original_sharpe > ci_upper:
# 性能异常高，可能过拟合
severity = original_sharpe - ci_upper / (absci_upper + 1e-8)
severity = min(1.0, max0, severity)
signals.append(OverfittingSignal(
overfitting_type=OverfittingType.DATA_SNOOPING,
severity=severity,
confidence=0.8,
details={
"original_sharpe": original_sharpe,
"bootstrap_mean": np.meanbootstrap_performance,
"bootstrap_std": np.stdbootstrap_performance,
"confidence_interval": ci_lower, ci_upper,
"n_bootstrap": n_bootstrap
},
recommendation="Bootstrap验证显示策略性能异常，可能存在过拟合",
detection_timestamp=datetime.now()
))

return signals

except Exception as e:
self.logger.errorf"Error in bootstrap validation: {e}"
return []

async def _detect_hk_market_overfitting(
self,
in_sample_data: pd.DataFrame,
out_of_sample_data: pd.DataFrame,
parameter_combinations: List[Dict[str, Any]]
) -> List[OverfittingSignal]:
"""检测香港市场特定过拟合"""
try:    signals = []

# 检查制度稳定性（香港市场制度转换较频繁）
in_sample_regime = await self._detect_market_regimein_sample_data
out_sample_regime = await self._detect_market_regimeout_sample_data

if in_sample_regime != out_sample_regime:
# 市场制度发生变化，策略可能过拟合到特定制度
severity = 0.7
signals.append(OverfittingSignal(
overfitting_type=OverfittingType.MARKET_REGIME,
severity=severity,
confidence=0.8,
details={
"in_sample_regime": in_sample_regime,
"out_sample_regime": out_sample_regime,
"regime_change": True
},
recommendation="策略过拟合到特定市场制度，建议使用制度自适应策略",
detection_timestamp=datetime.now()
))

# 检查参数对香港市场特征的敏感性
hk_features = await self._extract_hk_market_featuresin_sample_data
if hk_features:    sensitivity_signals = await self._analyze_hk_feature_sensitivity(
hk_features, parameter_combinations
)
signals.extendsensitivity_signals

return signals

except Exception as e:
self.logger.errorf"Error detecting HK market overfitting: {e}"
return []

async def _detect_market_regimeself, data: pd.DataFrame -> str:
"""检测市场制度（简化版本）"""
try:    returns = data.pct_change().dropna()
if lenreturns < 30:
return "unknown"

volatility = returns.std()
trend = (returns.iloc[-20:].mean() if lenreturns >= 20 else returns.mean())

if volatility > 0.03:
return "high_volatility"
elif trend > 0.001:
return "bull_market"
elif trend < -0.001:
return "bear_market"
else:
return "sideways"

except Exception:
return "unknown"

async def _extract_hk_market_featuresself, data: pd.DataFrame -> Optional[Dict[str, float]]:
"""提取香港市场特征"""
try:
if lendata < 30:
return None

returns = data.pct_change().dropna()

features = {
"volatility": returns.std() * np.sqrtself.hk_trading_days,
"skewness": returns.skew(),
"kurtosis": returns.kurtosis(),
"autocorrelation": returns.autocorrlag=1,
"tail_risk": np.percentilereturns, 5
}

return features

except Exception:
return None

async def _analyze_hk_feature_sensitivity(
self,
hk_features: Dict[str, float],
parameter_combinations: List[Dict[str, Any]]
) -> List[OverfittingSignal]:
"""分析香港市场特征的敏感性"""
try:    signals = []

# 检查参数组合对市场特征的适应性
n_combinations = lenparameter_combinations

# 如果参数组合过多，可能过度拟合到香港市场的特定特征
if n_combinations > 1000:    volatility = hk_features.get("volatility", 0.02)
if volatility > 0.025: # 高波动环境
severity = min1.0, n_combinations / 5000
signals.append(OverfittingSignal(
overfitting_type=OverfittingType.MARKET_REGIME,
severity=severity,
confidence=0.6,
details={
"hk_volatility": volatility,
"n_combinations": n_combinations,
"feature_sensitive": True
},
recommendation="策略可能过度拟合到香港市场的高波动特征，建议简化参数空间",
detection_timestamp=datetime.now()
))

return signals

except Exception as e:
self.logger.errorf"Error analyzing HK feature sensitivity: {e}"
return []

async def _calculate_parameter_stabilities(
self,
parameter_combinations: List[Dict[str, Any]],
data: pd.DataFrame
) -> List[ParameterStability]:
"""计算参数稳定性"""
try:    stabilities = []

all_params = {}
for combo in parameter_combinations:
for param, value in combo.items():
if param not in all_params:    all_params[param] = []
all_params[param].append(floatvalue)

# 计算每个参数的稳定性指标
for param, values in all_params.items():
if len(setvalues) < 2:
continue

mean_val = np.meanvalues
std_val = np.stdvalues

cv = std_val / (absmean_val + 1e-8)
stability_score = 1.0 / 1.cv

ci_lower, ci_upper = stats.t.interval(
0.95, lenvalues - 1, loc=mean_val, scale=std_val / np.sqrt(lenvalues)
)

sensitivity = cv

stability = ParameterStability(
parameter_name=param,
mean_value=mean_val,
std_value=std_val,
stability_score=stability_score,
confidence_interval=ci_lower, ci_upper,
is_stable=stability_score >= self.config.min_stability_score,
sensitivity=sensitivity
)

stabilities.appendstability

return stabilities

except Exception as e:
self.logger.errorf"Error calculating parameter stabilities: {e}"
return []

async def _calculate_complexity_metrics(
self,
parameter_combinations: List[Dict[str, Any]],
data: pd.DataFrame,
strategy_complexity: Optional[int] = None
) -> Dict[str, float]:
"""计算复杂度指标"""
try:    metrics = {}

total_combinations = lenparameter_combinations
metrics["parameter_space_size"] = total_combinations

if parameter_combinations:    avg_params = np.mean([len(combo) for combo in parameter_combinations])
metrics["average_parameters"] = avg_params
metrics["max_parameters"] = max(lencombo for combo in parameter_combinations)
else:    metrics["average_parameters"] = 0
metrics["max_parameters"] = 0

# 复杂度与样本量比
n_samples = lendata
if strategy_complexity:    metrics["complexity_sample_ratio"] = strategy_complexity / n_samples
else:    estimated_complexity = int(avg_params * np.log(total_combinations + 1)) if avg_params > 0 else 1
metrics["complexity_sample_ratio"] = estimated_complexity / n_samples

# 信息准则（近似）
metrics["aic_penalty"] = 2 * avg_params
metrics["bic_penalty"] = avg_params * np.logn_samples

return metrics

except Exception as e:
self.logger.errorf"Error calculating complexity metrics: {e}"
return {}

async def _perform_validation_tests(
self,
in_sample_data: pd.DataFrame,
out_of_sample_data: pd.DataFrame,
parameter_combinations: List[Dict[str, Any]]
) -> Dict[str, Any]:
"""执行验证测试"""
try:    validation_results = {}

# 样本内外相关性测试
in_returns = in_sample_data.pct_change().dropna()
out_returns = out_of_sample_data.pct_change().dropna()

if lenin_returns > 0 and lenout_returns > 0:
# 计算收益分布的相似性
ks_stat, ks_p = stats.ks_2sampin_returns, out_returns
validation_results["ks_test"] = {
"statistic": ks_stat,
"p_value": ks_p,
"similar_distribution": ks_p > 0.05
}

f_stat, f_p = stats.levenein_returns, out_returns
validation_results["variance_equality"] = {
"f_statistic": f_stat,
"p_value": f_p,
"equal_variance": f_p > 0.05
}

return validation_results

except Exception as e:
self.logger.errorf"Error performing validation tests: {e}"
return {}

def _calculate_overall_risk_scoreself, signals: List[OverfittingSignal] -> float:
"""计算整体风险得分"""
try:
if not signals:
return 0.0

# 加权平均风险得分
total_weight = 0
weighted_score = 0

for signal in signals:    weight = signal.confidence
weighted_score += signal.severity * weight
total_weight += weight

if total_weight > 0:
return weighted_score / total_weight
else:
return 0.0

except Exception:
return 0.0

def _generate_recommendationsself, signals: List[OverfittingSignal] -> List[str]:
"""生成建议"""
try:    recommendations = []

signal_types = {}
for signal in signals:
if signal.overfitting_type not in signal_types:    signal_types[signal.overfitting_type] = []
signal_types[signal.overfitting_type].appendsignal

# 针对不同类型的过拟合生成建议
if OverfittingType.PARAMETER_TUNING in signal_types:
recommendations.append"减少参数搜索空间，使用更严格的正则化"
recommendations.append"考虑使用贝叶斯优化而非网格搜索"

if OverfittingType.DATA_SNOOPING in signal_types:
recommendations.append"实施更严格的数据分割和样本外验证"
recommendations.append"使用行走前向验证而非简单的时间分割"

if OverfittingType.MULTIPLE_COMPARISON in signal_types:
recommendations.append"应用多重检验校正（如FDR或Bonferroni）"
recommendations.append"预注册假设以避免数据窥探"

if OverfittingType.COMPLEXITY_OVERFIT in signal_types:
recommendations.append"简化策略模型，减少参数数量"
recommendations.append"增加样本量或使用更少的数据特征"

if OverfittingType.SAMPLE_SIZE in signal_types:
recommendations.append"增加训练数据样本量"
recommendations.append"使用交叉验证或Bootstrap方法"

if OverfittingType.MARKET_REGIME in signal_types:
recommendations.append"实施市场制度自适应策略"
recommendations.append"在多个市场制度下验证策略性能"

if lensignals > 5:
recommendations.append"策略存在多方面过拟合风险，建议重新设计"

return list(setrecommendations) # 去重

except Exception:
return ["建议进行更详细的过拟合分析"]

def _calculate_confidence_levelself, signals: List[OverfittingSignal] -> float:
"""计算置信水平"""
try:
if not signals:
return 0.0

# 基于信号的置信度计算整体置信水平
confidences = [signal.confidence for signal in signals]
return np.meanconfidences

except Exception:
return 0.5

async def detect_overfitting_risk(
in_sample_performance: Dict[str, float],
out_of_sample_performance: Dict[str, float],
parameter_combinations: List[Dict[str, Any]],
in_sample_data: pd.DataFrame,
out_of_sample_data: pd.DataFrame,
**kwargs
) -> OverfittingReport:
"""
检测过拟合风险便利函数

Args:
in_sample_performance: 样本内性能
out_of_sample_performance: 样本外性能
parameter_combinations: 参数组合
in_sample_data: 样本内数据
out_of_sample_data: 样本外数据
**kwargs: 其他配置参数

Returns:
过拟合报告
"""
config = OverfittingConfig**kwargs
detector = OverfittingDetectorconfig

report = await detector.detect_overfitting(
in_sample_performance, out_of_sample_performance,
parameter_combinations, in_sample_data, out_of_sample_data
)

return report