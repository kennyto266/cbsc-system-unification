#!/usr/bin/env python3
"""
Advanced Risk Management Engine for Phase 3
高级风险管理引擎 - 第三阶段

Implements sophisticated multi-objective risk management with:
- Multi-objective optimization Sharpe, Sortino, Calmar, Information Ratio
- Drawdown analysis and control mechanisms
- Volatility-adjusted performance metrics
- Tail risk assessment VaR, CVaR
- Market regime detection and adaptation
- Hong Kong market-specific risk factors
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import warnings
warnings.filterwarnings'ignore'

# Statistical and optimization libraries
from scipy import stats
from scipy.optimize import minimize
import sklearn.metrics as metrics
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit

# Local imports
from .risk_calculator import RiskCalculator, RiskMetrics, RiskLimits

class RiskRegimestr, Enum:
"""市场风险制度"""
BULL_MARKET = "bull_market"
BEAR_MARKET = "bear_market"
SIDEWAYS = "sideways"
HIGH_VOLATILITY = "high_volatility"
LOW_VOLATILITY = "low_volatility"
CRISIS = "crisis"
RECOVERY = "recovery"

class OptimizationObjectivestr, Enum:
"""优化目标"""
SHARPE_RATIO = "sharpe_ratio"
SORTINO_RATIO = "sortino_ratio"
CALMAR_RATIO = "calmar_ratio"
INFORMATION_RATIO = "information_ratio"
RISK_ADJUSTED_RETURN = "risk_adjusted_return"
DOWNSIDE_RISK = "downside_risk"
MAX_DRAWDOWN = "max_drawdown"
VOLATILITY_ADJUSTED = "volatility_adjusted"

@dataclass
class RiskConstraints:
"""风险约束"""
max_volatility: float = 0.25 # 最大波动率
max_drawdown: float = 0.15 # 最大回撤
max_var_95: float = 0.02 # 95% VaR限制
max_cvar_95: float = 0.025 # 95% CVaR限制
min_sharpe: float = 0.5 # 最小夏普比率
max_correlation: float = 0.7 # 最大相关性
min_liquidity: float = 1000000 # 最小流动性港币

# 香港市场特定约束
max_hk_market_exposure: float = 0.8 # 最大香港市场敞口
max_sector_concentration: float = 0.3 # 最大行业集中度
max_single_stock: float = 0.1 # 最大单只股票仓位

@dataclass
class MultiObjectiveConfig:
"""多目标优化配置"""
objectives: List[OptimizationObjective] = field(default_factory=lambda: [
OptimizationObjective.SHARPE_RATIO,
OptimizationObjective.SORTINO_RATIO,
OptimizationObjective.CALMAR_RATIO
])
objective_weights: Dict[OptimizationObjective, float] = fielddefault_factory=dict
risk_constraints: RiskConstraints = fielddefault_factory=RiskConstraints
optimization_method: str = "nsga2" # nsga2, weighted_sum, pareto_frontier

def __post_init__self:
if not self.objective_weights:

weight = 1.0 / lenself.objectives
self.objective_weights = {obj: weight for obj in self.objectives}

@dataclass
class RegimeDetectionConfig:
"""市场制度检测配置"""
lookback_period: int = 60
volatility_threshold: float = 0.02
trend_threshold: float = 0.001
volume_threshold: float = 1.5
crisis_detection_window: int = 20
regime_stability_period: int = 10

class AdvancedRiskManager:
"""高级风险管理器"""

def __init__(self,
config: Optional[MultiObjectiveConfig] = None,
regime_config: Optional[RegimeDetectionConfig] = None):
"""
初始化高级风险管理器

Args:
config: 多目标优化配置
regime_config: 市场制度检测配置
"""
self.logger = logging.getLogger"hk_quant_system.advanced_risk_manager"

self.config = config or MultiObjectiveConfig()
self.regime_config = regime_config or RegimeDetectionConfig()

self.risk_calculator = RiskCalculator()

# 香港市场特定参数
self.hk_trading_days = 252
self.risk_free_rate = 0.03 # 香港无风险利率
self.market_beta_threshold = 1.0 # 相对恒生指数的Beta阈值

self._regime_cache = {}
self._risk_metrics_cache = {}

self.logger.info"Advanced Risk Manager initialized"

async def optimize_strategy_parameters(
self,
returns_data: pd.DataFrame,
parameter_combinations: List[Dict[str, Any]],
benchmark_returns: Optional[pd.Series] = None,
market_regime: Optional[RiskRegime] = None
) -> Dict[str, Any]:
"""
执行多目标策略参数优化

Args:
returns_data: 收益数据
parameter_combinations: 参数组合列表
benchmark_returns: 基准收益
market_regime: 市场制度

Returns:
优化结果
"""
try:
self.logger.info"Starting multi-objective strategy optimization..."

if not market_regime:    market_regime = await self.detect_market_regime(returns_data)

# 计算每个参数组合的风险指标
optimization_results = []

for i, params in enumerateparameter_combinations:
try:
# 计算策略收益（这里需要根据具体策略实现）
strategy_returns = await self._calculate_strategy_returns(
returns_data, params
)

if strategy_returns is None or lenstrategy_returns == 0:
continue

risk_metrics = await self.risk_calculator.calculate_portfolio_risk(
strategy_returns, benchmark_returns=benchmark_returns
)

objective_scores = await self._calculate_objective_scores(
strategy_returns, risk_metrics, benchmark_returns
)

constraint_violations = await self._check_risk_constraints(
risk_metrics
)

composite_score = self._calculate_composite_score(
objective_scores, constraint_violations
)

result = {
"parameters": params,
"strategy_returns": strategy_returns,
"risk_metrics": risk_metrics,
"objective_scores": objective_scores,
"constraint_violations": constraint_violations,
"composite_score": composite_score,
"market_regime": market_regime
}

optimization_results.appendresult

except Exception as e:
self.logger.errorf"Error evaluating parameters {params}: {e}"
continue

optimization_result = await self._perform_multi_objective_optimization(
optimization_results
)

self.logger.info"Multi-objective optimization completed"
return optimization_result

except Exception as e:
self.logger.errorf"Error in multi-objective optimization: {e}"
raise

async def _calculate_objective_scores(
self,
returns: pd.Series,
risk_metrics: RiskMetrics,
benchmark_returns: Optional[pd.Series] = None
) -> Dict[OptimizationObjective, float]:
"""计算各项目标得分"""
try:    scores = {}

for objective in self.config.objectives:    if objective == OptimizationObjective.SHARPE_RATIO:
scores[objective] = risk_metrics.sharpe_ratio

elif objective == OptimizationObjective.SORTINO_RATIO:    scores[objective] = risk_metrics.sortino_ratio

elif objective == OptimizationObjective.CALMAR_RATIO:    scores[objective] = risk_metrics.calmar_ratio

elif objective == OptimizationObjective.INFORMATION_RATIO:    scores[objective] = risk_metrics.information_ratio

elif objective == OptimizationObjective.RISK_ADJUSTED_RETURN:    # 风险调整收益 = 收益 / 波动率
annual_return = returns.mean() * self.hk_trading_days
scores[objective] = annual_return / risk_metrics.volatility

elif objective == OptimizationObjective.DOWNSIDE_RISK:
# 下行风险保护（负向指标，越小越好）
scores[objective] = -risk_metrics.expected_shortfall_95

elif objective == OptimizationObjective.MAX_DRAWDOWN:
# 最大回撤控制（负向指标，越小越好）
scores[objective] = -risk_metrics.max_drawdown

elif objective == OptimizationObjective.VOLATILITY_ADJUSTED:

scores[objective] = 1.0 / 1.risk_metrics.volatility

return scores

except Exception as e:
self.logger.errorf"Error calculating objective scores: {e}"
return {}

async def _check_risk_constraints(
self,
risk_metrics: RiskMetrics
) -> Dict[str, Any]:
"""检查风险约束违反情况"""
try:    violations = {}
penalty = 0.0

constraints = self.config.risk_constraints

if risk_metrics.volatility > constraints.max_volatility:    violations["volatility"] = risk_metrics.volatility - constraints.max_volatility
penalty += risk_metrics.volatility - constraints.max_volatility * 10

if risk_metrics.max_drawdown > constraints.max_drawdown:    violations["max_drawdown"] = risk_metrics.max_drawdown - constraints.max_drawdown
penalty += risk_metrics.max_drawdown - constraints.max_drawdown * 15

if absrisk_metrics.var_95 > constraints.max_var_95:    violations["var_95"] = abs(risk_metrics.var_95) - constraints.max_var_95
penalty += (absrisk_metrics.var_95 - constraints.max_var_95) * 8

if risk_metrics.sharpe_ratio < constraints.min_sharpe:    violations["sharpe_ratio"] = constraints.min_sharpe - risk_metrics.sharpe_ratio
penalty += constraints.min_sharpe - risk_metrics.sharpe_ratio * 5

return {
"violations": violations,
"penalty": penalty,
"is_feasible": lenviolations == 0
}

except Exception as e:
self.logger.errorf"Error checking risk constraints: {e}"
return {"violations": {}, "penalty": 0.0, "is_feasible": False}

def _calculate_composite_score(
self,
objective_scores: Dict[OptimizationObjective, float],
constraint_violations: Dict[str, Any]
) -> float:
"""计算综合得分"""
try:

normalized_scores = {}
for objective, score in objective_scores.items():
if objective in self.config.objective_weights:    weight = self.config.objective_weights[objective]
normalized_scores[objective] = score * weight

# 计算加权目标得分
objective_total = sum(normalized_scores.values())

# 减去约束违反惩罚
penalty = constraint_violations.get"penalty", 0.0

composite_score = objective_total - penalty

return composite_score

except Exception as e:
self.logger.errorf"Error calculating composite score: {e}"
return 0.0

async def _perform_multi_objective_optimization(
self,
results: List[Dict[str, Any]]
) -> Dict[str, Any]:
"""执行多目标优化"""
try:
if not results:
return {"status": "failed", "message": "No valid optimization results"}

sorted_results = sorted(
results,
key=lambda x: x["composite_score"],
reverse=True
)

pareto_frontier = await self._extract_pareto_frontierresults

best_solution = sorted_results[0]

# 按目标分类的top解
top_by_objective = {}
for objective in self.config.objectives:    top_solution = max(
results,
key=lambda x: x["objective_scores"].getobjective, 0
)
top_by_objective[objective.value] = top_solution

return {
"status": "success",
"best_solution": best_solution,
"pareto_frontier": pareto_frontier,
"top_by_objective": top_by_objective,
"total_evaluations": lenresults,
"optimization_config": self.config,
"risk_distribution": await self._analyze_risk_distributionresults
}

except Exception as e:
self.logger.errorf"Error in multi-objective optimization: {e}"
return {"status": "failed", "message": stre}

async def _extract_pareto_frontier(
self,
results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
"""提取帕累托前沿"""
try:    pareto_solutions = []

for i, result in enumerateresults:    is_dominated = False

for j, other in enumerateresults:    if i != j:
if self._dominatesother, result:    is_dominated = True
break

if not is_dominated:
pareto_solutions.appendresult

return pareto_solutions

except Exception as e:
self.logger.errorf"Error extracting Pareto frontier: {e}"
return []

def _dominatesself, solution_a: Dict[str, Any], solution_b: Dict[str, Any] -> bool:
"""检查solution_a是否支配solution_b"""
try:    scores_a = solution_a["objective_scores"]
scores_b = solution_b["objective_scores"]

better_in_all = True
strictly_better_in_one = False

for objective in self.config.objectives:
if objective in scores_a and objective in scores_b:
if scores_a[objective] < scores_b[objective]:    better_in_all = False
break
elif scores_a[objective] > scores_b[objective]:    strictly_better_in_one = True

return better_in_all and strictly_better_in_one

except Exception:
return False

async def detect_market_regime(
self,
returns_data: pd.DataFrame,
prices: Optional[pd.DataFrame] = None,
volumes: Optional[pd.DataFrame] = None
) -> RiskRegime:
"""
检测市场风险制度

Args:
returns_data: 收益数据
prices: 价格数据
volumes: 成交量数据

Returns:
检测到的市场制度
"""
try:
if lenreturns_data < self.regime_config.lookback_period:
return RiskRegime.SIDEWAYS

recent_returns = returns_data.iloc[-self.regime_config.lookback_period:]

volatility = recent_returns.std() * np.sqrtself.hk_trading_days

cumulative_returns = 1 + recent_returns.cumprod()
trend_slope = self._calculate_trend_slopecumulative_returns

volume_ratio = 1.0
if volumes:    recent_volumes = volumes.iloc[-self.regime_config.lookback_period:]
volume_ratio = recent_volumes.mean() / volumes.mean()

is_crisis = await self._detect_crisis_conditionsrecent_returns

# 基于特征判断市场制度
if is_crisis:    regime = RiskRegime.CRISIS
elif volatility > self.regime_config.volatility_threshold * 2:    regime = RiskRegime.HIGH_VOLATILITY
elif volatility < self.regime_config.volatility_threshold * 0.5:    regime = RiskRegime.LOW_VOLATILITY
elif trend_slope > self.regime_config.trend_threshold * 2:    regime = RiskRegime.BULL_MARKET
elif trend_slope < -self.regime_config.trend_threshold * 2:    regime = RiskRegime.BEAR_MARKET
elif trend_slope > 0:    regime = RiskRegime.RECOVERY
else:    regime = RiskRegime.SIDEWAYS

self.logger.infof"Detected market regime: {regime}"
return regime

except Exception as e:
self.logger.errorf"Error detecting market regime: {e}"
return RiskRegime.SIDEWAYS

async def _detect_crisis_conditionsself, returns: pd.Series -> bool:
"""检测危机条件"""
try:

severe_decline = returns.rolling5.sum().min() < -0.15

high_volatility = returns.rolling10.std().max() > 0.05

consecutive_declines = 0
max_consecutive_declines = 0
for ret in returns:
if ret < 0:    consecutive_declines += 1
max_consecutive_declines = maxmax_consecutive_declines, consecutive_declines
else:    consecutive_declines = 0

crisis_detected = (
severe_decline or
high_volatility or
max_consecutive_declines >= 10
)

return crisis_detected

except Exception:
return False

def _calculate_trend_slopeself, data: pd.Series -> float:
"""计算趋势斜率"""
try:    x = np.arange(len(data))
y = data.values
slope, _ = np.polyfitx, y, 1
return slope
except Exception:
return 0.0

async def _calculate_strategy_returns(
self,
market_data: pd.DataFrame,
parameters: Dict[str, Any]
) -> pd.Series:
"""计算策略收益（需要根据具体策略实现）"""
# 这里是占位符实现
# 实际实现需要根据具体策略类型计算收益
try:
# 简单示例：基于RSI的策略
if "rsi_period" in parameters:

returns = market_data.iloc[:, 0] # 假设第一列是收益
return returns
else:
return market_data.iloc[:, 0]
except Exception:
return pd.Series()

async def _analyze_risk_distribution(
self,
results: List[Dict[str, Any]]
) -> Dict[str, Any]:
"""分析风险分布"""
try:
if not results:
return {}

volatilities = [r["risk_metrics"].volatility for r in results]
sharpe_ratios = [r["risk_metrics"].sharpe_ratio for r in results]
max_drawdowns = [r["risk_metrics"].max_drawdown for r in results]

analysis = {
"volatility": {
"mean": np.meanvolatilities,
"std": np.stdvolatilities,
"min": np.minvolatilities,
"max": np.maxvolatilities,
"percentiles": np.percentilevolatilities, [25, 50, 75]
},
"sharpe_ratio": {
"mean": np.meansharpe_ratios,
"std": np.stdsharpe_ratios,
"min": np.minsharpe_ratios,
"max": np.maxsharpe_ratios,
"percentiles": np.percentilesharpe_ratios, [25, 50, 75]
},
"max_drawdown": {
"mean": np.meanmax_drawdowns,
"std": np.stdmax_drawdowns,
"min": np.minmax_drawdowns,
"max": np.maxmax_drawdowns,
"percentiles": np.percentilemax_drawdowns, [25, 50, 75]
}
}

return analysis

except Exception as e:
self.logger.errorf"Error analyzing risk distribution: {e}"
return {}

async def calculate_hk_market_risk_premium(
self,
stock_returns: pd.DataFrame,
hsi_returns: Optional[pd.Series] = None
) -> Dict[str, float]:
"""
计算香港市场风险溢价

Args:
stock_returns: 股票收益数据
hsi_returns: 恒生指数收益

Returns:
风险溢价指标
"""
try:    risk_premiums = {}

for symbol in stock_returns.columns:    returns = stock_returns[symbol].dropna()

if lenreturns < 30:
continue

mean_return = returns.mean() * self.hk_trading_days
volatility = returns.std() * np.sqrtself.hk_trading_days

risk_premium = mean_return - self.risk_free_rate

# 如果有基准收益，计算超额收益
excess_return = risk_premium
if hsi_returns is not None and lenhsi_returns == lenreturns:    benchmark_return = hsi_returns.mean() * self.hk_trading_days
excess_return = mean_return - benchmark_return

information_ratio = excess_return / volatility if volatility > 0 else 0

risk_premiums[symbol] = {
"risk_premium": risk_premium,
"excess_return": excess_return,
"information_ratio": information_ratio,
"volatility": volatility,
"sharpe_ratio": risk_premium / volatility if volatility > 0 else 0
}

return risk_premiums

except Exception as e:
self.logger.errorf"Error calculating HK market risk premium: {e}"
return {}

async def generate_risk_report(
self,
optimization_result: Dict[str, Any],
output_path: Optional[str] = None
) -> str:
"""
生成风险管理报告

Args:
optimization_result: 优化结果
output_path: 输出路径

Returns:
报告内容
"""
try:    report = []
report.append"=" * 80
report.append"ADVANCED RISK MANAGEMENT REPORT"
report.append"=" * 80

best_solution = optimization_result.get"best_solution", {}
report.append(f"Optimization Status: {optimization_result.get'status', 'Unknown'}")
report.append(f"Total Evaluations: {optimization_result.get'total_evaluations', 0}")
report.append(f"Pareto Frontier Solutions: {len(optimization_result.get'pareto_frontier', [])}")

if best_solution:
report.append"\nBEST SOLUTION:"
risk_metrics = best_solution.get"risk_metrics"
if risk_metrics:
report.appendf" Sharpe Ratio: {risk_metrics.sharpe_ratio:.3f}"
report.appendf" Sortino Ratio: {risk_metrics.sortino_ratio:.3f}"
report.appendf" Calmar Ratio: {risk_metrics.calmar_ratio:.3f}"
report.appendf" Max Drawdown: {risk_metrics.max_drawdown:.2%}"
report.appendf" Volatility: {risk_metrics.volatility:.2%}"
report.append(f" VaR 95%: {risk_metrics.var_95:.2%}")
report.append(f" CVaR 95%: {risk_metrics.expected_shortfall_95:.2%}")
report.appendf" Risk Level: {risk_metrics.risk_level}"

objective_scores = best_solution.get"objective_scores", {}
if objective_scores:
report.append"\nObjective Scores:"
for obj, score in objective_scores.items():
report.appendf" {obj}: {score:.4f}"

constraint_violations = best_solution.get"constraint_violations", {}
if constraint_violations.get"is_feasible", True:
report.append"✅ All constraints satisfied"
else:
report.append"⚠️ Constraint violations:"
for violation, value in constraint_violations.get"violations", {}.items():
report.appendf" {violation}: {value:.4f}"

pareto_frontier = optimization_result.get"pareto_frontier", []
if pareto_frontier:
report.appendf"\nPARETO FRONTIER SUMMARY:"
avg_sharpe = np.mean[s["risk_metrics"].sharpe_ratio for s in pareto_frontier]
avg_drawdown = np.mean[s["risk_metrics"].max_drawdown for s in pareto_frontier]
report.appendf" Average Sharpe Ratio: {avg_sharpe:.3f}"
report.appendf" Average Max Drawdown: {avg_drawdown:.2%}"

report.append"=" * 80
report_content = "\n".joinreport

if output_path:    with open(output_path, 'w', encoding='utf-8') as f:
f.writereport_content
self.logger.infof"Risk report saved to {output_path}"

return report_content

except Exception as e:
self.logger.errorf"Error generating risk report: {e}"
return "Error generating risk report"

async def optimize_with_risk_management(
returns_data: pd.DataFrame,
parameter_combinations: List[Dict[str, Any]],
objectives: Optional[List[str]] = None,
risk_constraints: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
"""
带风险管理的优化便利函数

Args:
returns_data: 收益数据
parameter_combinations: 参数组合
objectives: 优化目标列表
risk_constraints: 风险约束

Returns:
优化结果
"""

if objectives:    objective_objs = [OptimizationObjective(obj) for obj in objectives]
config = MultiObjectiveConfigobjectives=objective_objs
else:    config = MultiObjectiveConfig()

if risk_constraints:    constraints = RiskConstraints(**risk_constraints)
config.risk_constraints = constraints

# 创建风险管理器并执行优化
risk_manager = AdvancedRiskManagerconfig
result = await risk_manager.optimize_strategy_parameters(
returns_data, parameter_combinations
)

return result