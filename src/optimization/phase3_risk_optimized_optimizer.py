#!/usr/bin/env python3
"""
Phase 3 Risk-Optimized Parameter Optimizer
第三阶段风险优化参数优化器

Integrates advanced risk management with existing optimization pipeline:
- Multi-objective risk-aware optimization
- Temporal cross-validation integration
- Market regime adaptive optimization
- Overfitting prevention mechanisms
- Hong Kong market-specific optimization
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

# Import existing optimization components
from .parameter_optimizer import ParameterOptimizer, OptimizationConfig, OptimizationResult
from ..risk.advanced_risk_manager import AdvancedRiskManager, MultiObjectiveConfig, OptimizationObjective
from ..risk.market_regime_detector import MarketRegimeDetector, RegimeConfig, RegimeType
from ..validation.temporal_cv import TemporalCrossValidator, CVConfig, CVMethod
from ..validation.overfitting_detector import OverfittingDetector, OverfittingConfig
from ..risk.performance_attribution import PerformanceAnalytics

# Import technical analysis if available
try:
from indicators.core_indicators import CoreIndicators
INDICATORS_AVAILABLE = True
except ImportError:    INDICATORS_AVAILABLE = False

class OptimizationStatusstr, Enum:
"""优化状态"""
INITIALIZED = "initialized"
DATA_PREPARATION = "data_preparation"
REGIME_DETECTION = "regime_detection"
RISK_ANALYSIS = "risk_analysis"
PARAMETER_OPTIMIZATION = "parameter_optimization"
CROSS_VALIDATION = "cross_validation"
OVERFITTING_CHECK = "overfitting_check"
FINAL_SELECTION = "final_selection"
COMPLETED = "completed"
FAILED = "failed"

@dataclass
class Phase3OptimizationConfig:
"""第三阶段优化配置"""

base_config: OptimizationConfig = fielddefault_factory=OptimizationConfig
risk_config: Optional[MultiObjectiveConfig] = None
regime_config: Optional[RegimeConfig] = None
cv_config: Optional[CVConfig] = None
overfitting_config: Optional[OverfittingConfig] = None

# 香港市场特定设置
hk_market_aware: bool = True
regime_aware_optimization: bool = True
sector_constraints: bool = True

enable_risk_constraints: bool = True
max_portfolio_volatility: float = 0.25
max_drawdown_limit: float = 0.20
min_sharpe_threshold: float = 0.8

max_iterations: int = 100
convergence_tolerance: float = 1e-6
early_stopping_patience: int = 10

save_intermediate_results: bool = True
generate_detailed_report: bool = True
enable_parallel_processing: bool = True

def __post_init__self:
"""初始化后处理"""
if self.risk_config is None:
# 创建默认的多目标配置
self.risk_config = MultiObjectiveConfig(
objectives=[
OptimizationObjective.SHARPE_RATIO,
OptimizationObjective.SORTINO_RATIO,
OptimizationObjective.CALMAR_RATIO
],
optimization_method="nsga2"
)

if self.regime_config is None:    self.regime_config = RegimeConfig()

if self.cv_config is None:    self.cv_config = CVConfig(
method=CVMethod.EXPANDING_WINDOW,
initial_train_size=252,
test_size=63
)

if self.overfitting_config is None:    self.overfitting_config = OverfittingConfig()

@dataclass
class Phase3OptimizationResult:
"""第三阶段优化结果"""

base_result: OptimizationResult

risk_optimization_result: Dict[str, Any]
market_regime: Optional[RegimeType]
cross_validation_result: Dict[str, Any]
overfitting_analysis: Dict[str, Any]

risk_adjusted_metrics: Dict[str, float]
performance_attribution: Dict[str, Any]

optimization_status: OptimizationStatus
total_optimization_time: float
phase_details: Dict[str, float]
warnings: List[str]
recommendations: List[str]

hk_market_analysis: Dict[str, Any]

def to_dictself -> Dict[str, Any]:
"""转换为字典"""
return {
"base_result": self.base_result.__dict__ if hasattrself.base_result, '__dict__' else strself.base_result,
"risk_optimization_result": self.risk_optimization_result,
"market_regime": self.market_regime.value if self.market_regime else None,
"cross_validation_result": self.cross_validation_result,
"overfitting_analysis": self.overfitting_analysis,
"risk_adjusted_metrics": self.risk_adjusted_metrics,
"performance_attribution": self.performance_attribution,
"optimization_status": self.optimization_status.value,
"total_optimization_time": self.total_optimization_time,
"phase_details": self.phase_details,
"warnings": self.warnings,
"recommendations": self.recommendations,
"hk_market_analysis": self.hk_market_analysis,
"timestamp": datetime.now().isoformat()
}

class Phase3RiskOptimizedOptimizer:
"""第三阶段风险优化参数优化器"""

def __init__self, config: Optional[Phase3OptimizationConfig] = None:
"""
初始化第三阶段优化器

Args:
config: 第三阶段优化配置
"""
self.logger = logging.getLogger"hk_quant_system.phase3_optimizer"
self.config = config or Phase3OptimizationConfig()

self.base_optimizer = ParameterOptimizerself.config.base_config
self.risk_manager = AdvancedRiskManagerself.config.risk_config
self.regime_detector = MarketRegimeDetectorself.config.regime_config
self.cross_validator = TemporalCrossValidatorself.config.cv_config
self.overfitting_detector = OverfittingDetectorself.config.overfitting_config
self.performance_analytics = PerformanceAnalytics()

self.current_status = OptimizationStatus.INITIALIZED
self.optimization_log = []
self.phase_timings = {}

self.hk_trading_days = 252

self.logger.info"Phase 3 Risk-Optimized Optimizer initialized"

async def optimize_with_risk_management(
self,
symbol: str = "0700.HK",
strategy: str = "RSI_MEAN_REVERSION",
param_ranges: Optional[Dict[str, Union[List, range]]] = None,
benchmark_data: Optional[pd.DataFrame] = None,
external_factors: Optional[Dict[str, pd.DataFrame]] = None
) -> Phase3OptimizationResult:
"""
执行带风险管理的优化

Args:
symbol: 股票代码
strategy: 策略名称
param_ranges: 参数范围
benchmark_data: 基准数据
external_factors: 外部因素数据

Returns:
第三阶段优化结果
"""
try:    start_time = datetime.now()
self.logger.infof"Starting Phase 3 risk-optimized optimization for {symbol} - {strategy}"

# 阶段1: 数据准备
self._update_statusOptimizationStatus.DATA_PREPARATION
market_data, parameter_combinations = await self._prepare_data_and_parameters(
symbol, strategy, param_ranges
)

# 阶段2: 市场制度检测
self._update_statusOptimizationStatus.REGIME_DETECTION
market_regime = await self._detect_market_regimemarket_data, external_factors

# 阶段3: 风险分析和约束设定
self._update_statusOptimizationStatus.RISK_ANALYSIS
risk_constraints = await self._analyze_risk_constraintsmarket_data, benchmark_data

# 阶段4: 风险感知参数优化
self._update_statusOptimizationStatus.PARAMETER_OPTIMIZATION
risk_optimization_result = await self._risk_aware_optimization(
market_data, parameter_combinations, risk_constraints, benchmark_data, market_regime
)

# 阶段5: 时序交叉验证
self._update_statusOptimizationStatus.CROSS_VALIDATION
cv_result = await self._perform_cross_validation(
market_data, risk_optimization_result, benchmark_data
)

# 阶段6: 过拟合检测
self._update_statusOptimizationStatus.OVERFITTING_CHECK
overfitting_result = await self._detect_overfitting(
market_data, risk_optimization_result, cv_result
)

# 阶段7: 最终选择和性能分析
self._update_statusOptimizationStatus.FINAL_SELECTION
final_selection = await self._select_final_strategy(
risk_optimization_result, cv_result, overfitting_result
)

# 阶段8: 性能归因和分析
risk_adjusted_metrics = await self._calculate_risk_adjusted_metrics(
final_selection, market_data, benchmark_data
)

performance_attribution = await self._perform_performance_attribution(
final_selection, market_data, benchmark_data
)

# 香港市场特定分析
hk_market_analysis = await self._analyze_hk_market_specifics(
final_selection, market_data, market_regime
)

# 获取基础优化结果
base_result = await self.base_optimizer.run_optimizationsymbol, strategy, param_ranges

warnings, recommendations = await self._generate_warnings_and_recommendations(
risk_optimization_result, cv_result, overfitting_result, final_selection
)

total_time = (datetime.now() - start_time).total_seconds()

result = Phase3OptimizationResult(
base_result=base_result,
risk_optimization_result=risk_optimization_result,
market_regime=market_regime,
cross_validation_result=cv_result,
overfitting_analysis=overfitting_result,
risk_adjusted_metrics=risk_adjusted_metrics,
performance_attribution=performance_attribution,
optimization_status=OptimizationStatus.COMPLETED,
total_optimization_time=total_time,
phase_details=self.phase_timings,
warnings=warnings,
recommendations=recommendations,
hk_market_analysis=hk_market_analysis
)

self._update_statusOptimizationStatus.COMPLETED

if self.config.save_intermediate_results:
await self._save_optimization_resultresult, symbol, strategy

self.logger.infof"Phase 3 optimization completed in {total_time:.2f} seconds"
return result

except Exception as e:
self.logger.errorf"Error in Phase 3 optimization: {e}"
self._update_statusOptimizationStatus.FAILED
raise

async def _prepare_data_and_parameters(
self,
symbol: str,
strategy: str,
param_ranges: Optional[Dict[str, Union[List, range]]]
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
"""准备数据和参数"""
try:    start_phase = datetime.now()

market_data = await self._get_market_datasymbol, self.config.base_config.duration

if not param_ranges:    param_ranges = self.base_optimizer.get_parameter_ranges(strategy)

parameter_combinations = self._generate_parameter_combinationsparam_ranges

self.phase_timings["data_preparation"] = (datetime.now() - start_phase).total_seconds()

return market_data, parameter_combinations

except Exception as e:
self.logger.errorf"Error in data preparation: {e}"
raise

async def _get_market_dataself, symbol: str, duration: int -> pd.DataFrame:
"""获取市场数据"""
try:
# 使用现有优化器的数据获取方法
data = self.base_optimizer._get_market_datasymbol, duration

if data is None or lendata == 0:
raise ValueErrorf"Failed to get market data for {symbol}"

return data

except Exception as e:
self.logger.errorf"Error getting market data: {e}"
raise

def _generate_parameter_combinations(
self,
param_ranges: Dict[str, Union[List, range]]
) -> List[Dict[str, Any]]:
"""生成参数组合"""
try:
from itertools import product

# 转换range为list
param_values = {}
for param, values in param_ranges.items():
if isinstancevalues, range:    param_values[param] = list(values)
else:    param_values[param] = values

param_names = list(param_values.keys())
param_value_lists = list(param_values.values())

combinations = []
for combination in product*param_value_lists:    param_dict = dict(zip(param_names, combination))
combinations.appendparam_dict

max_combinations = self.config.base_config.max_combinations
if lencombinations > max_combinations:

np.random.shufflecombinations
combinations = combinations[:max_combinations]

return combinations

except Exception as e:
self.logger.errorf"Error generating parameter combinations: {e}"
return []

async def _detect_market_regime(
self,
market_data: pd.DataFrame,
external_factors: Optional[Dict[str, pd.DataFrame]]
) -> Optional[RegimeType]:
"""检测市场制度"""
try:    start_phase = datetime.now()

if not self.config.regime_aware_optimization:    self.phase_timings["regime_detection"] = (datetime.now() - start_phase).total_seconds()
return None

regime_signal = await self.regime_detector.detect_current_regime(
market_data, benchmark_data=None, volume_data=None,
external_factors=external_factors
)

self.phase_timings["regime_detection"] = (datetime.now() - start_phase).total_seconds()
return regime_signal.regime

except Exception as e:
self.logger.errorf"Error detecting market regime: {e}"
return None

async def _analyze_risk_constraints(
self,
market_data: pd.DataFrame,
benchmark_data: Optional[pd.DataFrame]
) -> Dict[str, Any]:
"""分析风险约束"""
try:    start_phase = datetime.now()

if not self.config.enable_risk_constraints:    self.phase_timings["risk_analysis"] = (datetime.now() - start_phase).total_seconds()
return {}

# 计算基础风险指标
returns = market_data.pct_change().dropna()

risk_constraints = {
"max_volatility": self.config.max_portfolio_volatility,
"max_drawdown": self.config.max_drawdown_limit,
"min_sharpe": self.config.min_sharpe_threshold,
"var_limit": returns.std() * 2.5, # 2.5 sigma
"correlation_limit": 0.7
}

# 如果有基准数据，计算相对风险约束
if benchmark_data:    benchmark_returns = benchmark_data.pct_change().dropna()
aligned_returns, aligned_benchmark = returns.alignbenchmark_returns, join='inner'

if aligned_returns:    correlation = aligned_returns.corr(aligned_benchmark)
risk_constraints["correlation_with_benchmark"] = correlation
risk_constraints["tracking_error_limit"] = 0.02 # 2%

self.phase_timings["risk_analysis"] = (datetime.now() - start_phase).total_seconds()
return risk_constraints

except Exception as e:
self.logger.errorf"Error analyzing risk constraints: {e}"
return {}

async def _risk_aware_optimization(
self,
market_data: pd.DataFrame,
parameter_combinations: List[Dict[str, Any]],
risk_constraints: Dict[str, Any],
benchmark_data: Optional[pd.DataFrame],
market_regime: Optional[RegimeType]
) -> Dict[str, Any]:
"""风险感知优化"""
try:    start_phase = datetime.now()

# 转换数据为收益格式
returns_data = market_data.pct_change().dropna()

if lenreturns_data == 0:
raise ValueError"No valid return data for optimization"

# 执行多目标风险优化
optimization_result = await self.risk_manager.optimize_strategy_parameters(
returns_data=returns_data,
parameter_combinations=parameter_combinations,
benchmark_returns=benchmark_data.pct_change().dropna() if benchmark_data is not None else None,
market_regime=market_regime
)

self.phase_timings["risk_optimization"] = (datetime.now() - start_phase).total_seconds()
return optimization_result

except Exception as e:
self.logger.errorf"Error in risk-aware optimization: {e}"
return {"status": "failed", "message": stre}

async def _perform_cross_validation(
self,
market_data: pd.DataFrame,
optimization_result: Dict[str, Any],
benchmark_data: Optional[pd.DataFrame]
) -> Dict[str, Any]:
"""执行交叉验证"""
try:    start_phase = datetime.now()

# 从优化结果中提取最佳参数
best_parameters = optimization_result.get"best_solution", {}.get"parameters", {}

# 定义策略函数（简化版本）
async def strategy_functiondata, params:
# 这里需要实现具体的策略逻辑
# 目前返回简单的买入持有收益
returns = data.pct_change().dropna()
return returns

# 执行时序交叉验证
cv_result = await self.cross_validator.validate_strategy(
data=market_data,
strategy_func=strategy_function,
parameter_combinations=[best_parameters],
benchmark_returns=benchmark_data.pct_change().dropna() if benchmark_data is not None else None
)

self.phase_timings["cross_validation"] = (datetime.now() - start_phase).total_seconds()
return cv_result

except Exception as e:
self.logger.errorf"Error in cross validation: {e}"
return {"status": "failed", "message": stre}

async def _detect_overfitting(
self,
market_data: pd.DataFrame,
optimization_result: Dict[str, Any],
cv_result: Dict[str, Any]
) -> Dict[str, Any]:
"""检测过拟合"""
try:    start_phase = datetime.now()

best_solution = optimization_result.get"best_solution", {}
in_sample_performance = best_solution.get"objective_scores", {}

# 从交叉验证结果中提取样本外性能
out_of_sample_performance = {}
if cv_result.get"split_results":    avg_test_performance = {}
for split in cv_result["split_results"]:
for metric, value in split.test_performance.items():
if metric not in avg_test_performance:    avg_test_performance[metric] = []
avg_test_performance[metric].appendvalue

for metric, values in avg_test_performance.items():    out_of_sample_performance[metric] = np.mean(values)

parameter_combinations = [best_solution.get"parameters", {}] if best_solution.get"parameters" else []

overfitting_report = await self.overfitting_detector.detect_overfitting(
in_sample_performance=in_sample_performance,
out_of_sample_performance=out_of_sample_performance,
parameter_combinations=parameter_combinations,
in_sample_data=market_data,
out_of_sample_data=market_data.iloc[-63:], # 使用最近63天作为样本外
strategy_complexity=len(best_solution.get"parameters", {})
)

self.phase_timings["overfitting_detection"] = (datetime.now() - start_phase).total_seconds()
return overfitting_report.__dict__ if hasattroverfitting_report, '__dict__' else stroverfitting_report

except Exception as e:
self.logger.errorf"Error in overfitting detection: {e}"
return {"status": "failed", "message": stre}

async def _select_final_strategy(
self,
optimization_result: Dict[str, Any],
cv_result: Dict[str, Any],
overfitting_result: Dict[str, Any]
) -> Dict[str, Any]:
"""选择最终策略"""
try:
# 从优化结果中获取最佳解决方案
best_solution = optimization_result.get"best_solution", {}

# 检查是否有过拟合
is_overfitted = overfitting_result.get"is_overfitted", False
risk_score = overfitting_result.get"overall_risk_score", 0.0

# 如果存在过拟合，调整选择
if is_overfitted or risk_score > 0.5:
# 选择更保守的参数或帕累托前沿中的稳定解
pareto_frontier = optimization_result.get"pareto_frontier", []
if pareto_frontier:
# 选择具有最低风险的解
stable_solution = min(pareto_frontier, key=lambda x: x.get"constraint_violations", {}.get("penalty", float'inf'))
final_selection = stable_solution
else:    final_selection = best_solution
else:    final_selection = best_solution

final_selection["selection_rationale"] = {
"overfitting_detected": is_overfitted,
"risk_score": risk_score,
"selected_from_pareto": len(optimization_result.get"pareto_frontier", []) > 0,
"conservative_selection": is_overfitted or risk_score > 0.3
}

return final_selection

except Exception as e:
self.logger.errorf"Error in final strategy selection: {e}"
return optimization_result.get"best_solution", {}

async def _calculate_risk_adjusted_metrics(
self,
final_selection: Dict[str, Any],
market_data: pd.DataFrame,
benchmark_data: Optional[pd.DataFrame]
) -> Dict[str, float]:
"""计算风险调整指标"""
try:
# 计算策略收益（简化版本）
strategy_returns = market_data.pct_change().dropna()

benchmark_returns = benchmark_data.pct_change().dropna() if benchmark_data is not None else None

# 计算综合性能指标
metrics = await self.performance_analytics.calculate_comprehensive_metrics(
returns=strategy_returns,
benchmark_returns=benchmark_returns
)

risk_adjusted_metrics = {
"sharpe_ratio": metrics.sharpe_ratio,
"sortino_ratio": metrics.sortino_ratio,
"calmar_ratio": metrics.calmar_ratio,
"information_ratio": metrics.information_ratio,
"alpha": metrics.alpha,
"beta": metrics.beta,
"max_drawdown": metrics.max_drawdown,
"volatility": metrics.volatility,
"win_rate": metrics.win_rate,
"profit_factor": metrics.profit_factor
}

return risk_adjusted_metrics

except Exception as e:
self.logger.errorf"Error calculating risk-adjusted metrics: {e}"
return {}

async def _perform_performance_attribution(
self,
final_selection: Dict[str, Any],
market_data: pd.DataFrame,
benchmark_data: Optional[pd.DataFrame]
) -> Dict[str, Any]:
"""执行性能归因"""
try:
if not benchmark_data:
return {"message": "No benchmark data available for attribution"}

strategy_returns = market_data.pct_change().dropna()
benchmark_returns = benchmark_data.pct_change().dropna()

attribution_result = await self.performance_analytics.performance_attribution(
returns=strategy_returns,
benchmark_returns=benchmark_returns
)

attribution = {
"total_return": attribution_result.total_return,
"benchmark_return": attribution_result.benchmark_return,
"active_return": attribution_result.active_return,
"market_timing_return": attribution_result.market_timing_return,
"sector_return": attribution_result.sector_return,
"mainland_influence_return": attribution_result.mainland_influence_return,
"us_market_influence_return": attribution_result.us_market_influence_return
}

return attribution

except Exception as e:
self.logger.errorf"Error in performance attribution: {e}"
return {"message": f"Attribution analysis failed: {stre}"}

async def _analyze_hk_market_specifics(
self,
final_selection: Dict[str, Any],
market_data: pd.DataFrame,
market_regime: Optional[RegimeType]
) -> Dict[str, Any]:
"""分析香港市场特定因素"""
try:    hk_analysis = {
"market_regime": market_regime.value if market_regime else "unknown",
"trading_days_analyzed": lenmarket_data,
"data_period": f"{market_data.index[0].date()} to {market_data.index[-1].date()}",
"hk_specific_features": {}
}

# 分析香港市场特征
returns = market_data.pct_change().dropna()

if returns:

hk_analysis["hk_specific_features"]["volatility_regime"] = self._classify_volatility_regime(returns.std())

hk_analysis["hk_specific_features"]["trend_characteristics"] = self._analyze_trend_characteristicsreturns

# 季节性特征（简化版本）
hk_analysis["hk_specific_features"]["seasonal_patterns"] = self._analyze_seasonal_patternsreturns

# 与市场制度的关系
if market_regime:    hk_analysis["regime_specific_analysis"] = {
"regime": market_regime.value,
"regime_appropriate_strategy": self._assess_regime_appropriatenessfinal_selection, market_regime
}

return hk_analysis

except Exception as e:
self.logger.errorf"Error analyzing HK market specifics: {e}"
return {"message": f"HK market analysis failed: {stre}"}

def _classify_volatility_regimeself, volatility: float -> str:
"""分类波动率制度"""
if volatility < 0.015:
return "low_volatility"
elif volatility < 0.025:
return "normal_volatility"
elif volatility < 0.035:
return "high_volatility"
else:
return "extreme_volatility"

def _analyze_trend_characteristicsself, returns: pd.Series -> Dict[str, Any]:
"""分析趋势特征"""
try:

ma_short = returns.rolling20.mean()
ma_long = returns.rolling60.mean()

trend_strength = absma_short.iloc[-1] - ma_long.iloc[-1] if lenma_short > 60 and lenma_long > 60 else 0

return {
"trend_strength": floattrend_strength,
"short_term_trend": floatma_short.iloc[-1] if lenma_short > 0 else 0,
"long_term_trend": floatma_long.iloc[-1] if lenma_long > 0 else 0,
"trend_persistence": float(ma_short > ma_long.mean()) if lenma_short > 0 and lenma_long > 0 else 0.5
}

except Exception:
return {"message": "Trend analysis failed"}

def _analyze_seasonal_patternsself, returns: pd.Series -> Dict[str, Any]:
"""分析季节性模式"""
try:
# 按月分析平均收益
monthly_returns = returns.groupbyreturns.index.month.mean()

# 识别表现最好和最差的月份
best_month = monthly_returns.idxmax()
worst_month = monthly_returns.idxmin()

return {
"best_performing_month": intbest_month,
"worst_performing_month": intworst_month,
"monthly_volatility": float(monthly_returns.std()),
"seasonal_strength": float(monthly_returns.std() / returns.std()) if returns.std() > 0 else 0
}

except Exception:
return {"message": "Seasonal analysis failed"}

def _assess_regime_appropriatenessself, strategy: Dict[str, Any], regime: RegimeType -> str:
"""评估策略对制度的适应性"""
# 简化的策略-制度匹配逻辑
if regime == RegimeType.BULL_MARKET:
return "appropriate_for_trend_following"
elif regime == RegimeType.BEAR_MARKET:
return "consider_defensive_strategies"
elif regime == RegimeType.HIGH_VOLATILITY:
return "risk_management_critical"
else:
return "general_applicability"

async def _generate_warnings_and_recommendations(
self,
optimization_result: Dict[str, Any],
cv_result: Dict[str, Any],
overfitting_result: Dict[str, Any],
final_selection: Dict[str, Any]
) -> Tuple[List[str], List[str]]:
"""生成警告和建议"""
try:    warnings = []
recommendations = []

if overfitting_result.get"is_overfitted", False:
warnings.append"⚠️ Strategy shows signs of overfitting"
recommendations.append"Consider simplifying parameter space or increasing regularization"

risk_score = overfitting_result.get"overall_risk_score", 0.0
if risk_score > 0.7:
warnings.append"🚨 High overfitting risk detected"
recommendations.append"Strategy validation recommended before deployment"
elif risk_score > 0.4:
warnings.append"⚠️ Moderate overfitting risk"
recommendations.append"Monitor strategy performance closely"

# 交叉验证相关警告
cv_success_rate = cv_result.get"successful_validations", 0 / cv_result.get"total_splits", 1
if cv_success_rate < 0.8:
warnings.append"⚠️ Low cross-validation success rate"
recommendations.append"Strategy may not be robust across different market conditions"

# 优化结果相关警告
best_sharpe = optimization_result.get"best_solution", {}.get"objective_scores", {}.get"sharpe_ratio", 0
if best_sharpe < 0.5:
warnings.append"⚠️ Low Sharpe ratio detected"
recommendations.append"Consider alternative strategies or parameter adjustments"

if lenwarnings == 0:
recommendations.append"Strategy appears robust - suitable for paper trading validation"
else:
recommendations.append"Recommend extensive backtesting before live deployment"

# 香港市场特定建议
if self.config.hk_market_aware:
recommendations.append("Monitor HK market-specific risks currency, mainland influence")

return warnings, recommendations

except Exception as e:
self.logger.errorf"Error generating warnings and recommendations: {e}"
return [], ["Error generating recommendations - manual review required"]

def _update_statusself, status: OptimizationStatus:
"""更新优化状态"""
self.current_status = status
self.optimization_log.append({
"timestamp": datetime.now(),
"status": status.value,
"message": f"Entered {status.value} phase"
})
self.logger.infof"Optimization status: {status.value}"

async def _save_optimization_result(
self,
result: Phase3OptimizationResult,
symbol: str,
strategy: str
):
"""保存优化结果"""
try:

output_dir = Pathself.config.base_config.output_dir
output_dir.mkdirexist_ok=True

timestamp = datetime.now().strftime"%Y%m%d_%H%M%S"
filename = f"phase3_{symbol}_{strategy}_{timestamp}.json"
filepath = output_dir / filename

result_dict = result.to_dict()
with openfilepath, 'w', encoding='utf-8' as f:
import json
json.dumpresult_dict, f, ensure_ascii=False, indent=2, default=str

self.logger.infof"Optimization result saved to {filepath}"

except Exception as e:
self.logger.errorf"Error saving optimization result: {e}"

def get_optimization_summaryself, result: Phase3OptimizationResult -> str:
"""获取优化摘要"""
try:    summary = []
summary.append"=" * 80
summary.append"PHASE 3 RISK-OPTIMIZED OPTIMIZATION SUMMARY"
summary.append"=" * 80

summary.appendf"Status: {result.optimization_status.value}"
summary.appendf"Total Time: {result.total_optimization_time:.2f} seconds"
summary.appendf"Market Regime: {result.market_regime.value if result.market_regime else 'Not detected'}"

if result.risk_adjusted_metrics:
summary.append"\n--- RISK-ADJUSTED PERFORMANCE ---"
for metric, value in result.risk_adjusted_metrics.items():
if metric in ["sharpe_ratio", "sortino_ratio", "calmar_ratio"]:
summary.append(f"{metric.replace'_', ' '.title()}: {value:.3f}")
else:
summary.append(f"{metric.replace'_', ' '.title()}: {value:.2%}")

if result.warnings:
summary.append"\n--- WARNINGS ---"
summary.extendresult.warnings

if result.recommendations:
summary.append"\n--- RECOMMENDATIONS ---"
summary.extendresult.recommendations

if result.hk_market_analysis:
summary.append"\n--- HK MARKET ANALYSIS ---"
analysis = result.hk_market_analysis
if "market_regime" in analysis:
summary.appendf"Market Regime: {analysis['market_regime']}"
if "trading_days_analyzed" in analysis:
summary.appendf"Trading Days Analyzed: {analysis['trading_days_analyzed']}"

summary.append"=" * 80

return "\n".joinsummary

except Exception as e:
self.logger.errorf"Error generating optimization summary: {e}"
return "Error generating summary"

async def optimize_with_risk_management_phase3(
symbol: str = "0700.HK",
strategy: str = "RSI_MEAN_REVERSION",
**kwargs
) -> Phase3OptimizationResult:
"""
第三阶段风险管理优化便利函数

Args:
symbol: 股票代码
strategy: 策略名称
**kwargs: 其他配置参数

Returns:
第三阶段优化结果
"""
config = Phase3OptimizationConfig**kwargs
optimizer = Phase3RiskOptimizedOptimizerconfig

result = await optimizer.optimize_with_risk_managementsymbol, strategy

return result