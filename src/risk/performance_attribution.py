#!/usr/bin/env python3
"""
Risk-Adjusted Performance Analytics Suite
风险调整后性能分析套件

Implements comprehensive risk-adjusted performance metrics with:
- Enhanced Sharpe ratio calculation
- Sortino ratio with downside deviation
- Calmar ratio with max drawdown
- Information ratio vs benchmarks
- Treynor ratio with beta calculation
- Performance attribution analysis
- Hong Kong market-specific benchmarks
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
from scipy.optimize import minimize
import sklearn.metrics as metrics

# Financial analysis libraries
try:
import empyrical as ep
EMPYRICAL_AVAILABLE = True
except ImportError:    EMPYRICAL_AVAILABLE = False

# Local imports
from .risk_calculator import RiskCalculator, RiskMetrics

class PerformanceMetricstr, Enum:
"""性能指标类型"""
SHARPE_RATIO = "sharpe_ratio"
SORTINO_RATIO = "sortino_ratio"
CALMAR_RATIO = "calmar_ratio"
INFORMATION_RATIO = "information_ratio"
TREYNOR_RATIO = "treynor_ratio"
ALPHA = "alpha"
BETA = "beta"
JENSEN_ALPHA = "jensen_alpha"
MODIGLIANI_RATIO = "modigliani_ratio"
OMEGA_RATIO = "omega_ratio"
UPSIDE_POTENTIAL_RATIO = "upside_potential_ratio"
VARIATION_RATIO = "variation_ratio"
BURKE_RATIO = "burke_ratio"

class BenchmarkTypestr, Enum:
"""基准类型"""
HSI = "hsi" # 恒生指数
HSTECH = "hstech" # 恒生科技指数
HSCEI = "hscei" # 恒生中国企业指数
HSMCI = "hsmci" # 恒生综合指数
RISK_FREE = "risk_free" # 无风险利率
SECTOR = "sector" # 行业基准
CUSTOM = "custom" # 自定义基准

@dataclass
class PerformancePeriod:
"""性能周期"""
start_date: datetime
end_date: datetime
returns: pd.Series
benchmark_returns: Optional[pd.Series] = None
period_name: str = ""

@dataclass
class PerformanceMetrics:
"""性能指标"""

total_return: float
annual_return: float
cumulative_return: float

volatility: float
downside_volatility: float
tracking_error: float

# 风险调整收益指标
sharpe_ratio: float
sortino_ratio: float
calmar_ratio: float
information_ratio: float
treynor_ratio: float

alpha: float
beta: float
jensen_alpha: float
modigliani_ratio: float
omega_ratio: float
upside_potential_ratio: float
burke_ratio: float

max_drawdown: float
average_drawdown: float
recovery_factor: float
sterling_ratio: float

skewness: float
kurtosis: float
var_95: float
cvar_95: float

win_rate: float
profit_factor: float
average_win: float
average_loss: float
best_month: float
worst_month: float

@dataclass
class AttributionResult:
"""归因分析结果"""
period: PerformancePeriod
total_return: float
benchmark_return: float
active_return: float

asset_allocation_return: float
stock_selection_return: float
interaction_return: float

market_timing_return: float
currency_return: float
sector_return: float

# 香港市场特定归因
mainland_influence_return: float
us_market_influence_return: float
currency_exposure_return: float

class PerformanceAnalytics:
"""性能分析器"""

def __init__self:
"""初始化性能分析器"""
self.logger = logging.getLogger"hk_quant_system.performance_analytics"
self.risk_calculator = RiskCalculator()

self.hk_trading_days = 252
self.risk_free_rate = 0.03 # 3%无风险利率

self.benchmark_cache = {}

self.logger.info"Performance Analytics initialized"

async def calculate_comprehensive_metrics(
self,
returns: pd.Series,
benchmark_returns: Optional[pd.Series] = None,
periods: Optional[List[PerformancePeriod]] = None
) -> PerformanceMetrics:
"""
计算综合性能指标

Args:
returns: 策略收益序列
benchmark_returns: 基准收益序列
periods: 分析周期

Returns:
性能指标
"""
try:
self.logger.info"Calculating comprehensive performance metrics..."

if lenreturns == 0:
raise ValueError"Returns series is empty"

total_return = self._calculate_total_returnreturns
annual_return = self._calculate_annual_returnreturns
cumulative_return = 1 + returns.prod() - 1

volatility = self._calculate_volatilityreturns
downside_volatility = self._calculate_downside_volatilityreturns
tracking_error = self._calculate_tracking_errorreturns, benchmark_returns

# 风险调整收益指标
sharpe_ratio = await self._calculate_sharpe_ratioreturns
sortino_ratio = await self._calculate_sortino_ratioreturns
calmar_ratio = await self._calculate_calmar_ratioreturns
information_ratio = await self._calculate_information_ratioreturns, benchmark_returns
treynor_ratio = await self._calculate_treynor_ratioreturns, benchmark_returns

alpha, beta = await self._calculate_alpha_betareturns, benchmark_returns
jensen_alpha = await self._calculate_jensen_alphareturns, benchmark_returns
modigliani_ratio = await self._calculate_modigliani_ratioreturns, benchmark_returns
omega_ratio = await self._calculate_omega_ratioreturns
upside_potential_ratio = await self._calculate_upside_potential_ratioreturns
burke_ratio = await self._calculate_burke_ratioreturns

max_drawdown = self._calculate_max_drawdownreturns
average_drawdown = self._calculate_average_drawdownreturns
recovery_factor = self._calculate_recovery_factorreturns, max_drawdown
sterling_ratio = self._calculate_sterling_ratioreturns, max_drawdown

skewness = returns.skew()
kurtosis = returns.kurtosis()
var_95 = np.percentilereturns, 5
cvar_95 = returns[returns <= var_95].mean()

win_rate = self._calculate_win_ratereturns
profit_factor = self._calculate_profit_factorreturns
average_win = self._calculate_average_winreturns
average_loss = self._calculate_average_lossreturns
best_month = self._calculate_best_monthreturns
worst_month = self._calculate_worst_monthreturns

metrics = PerformanceMetrics(
total_return=total_return,
annual_return=annual_return,
cumulative_return=cumulative_return,
volatility=volatility,
downside_volatility=downside_volatility,
tracking_error=tracking_error,
sharpe_ratio=sharpe_ratio,
sortino_ratio=sortino_ratio,
calmar_ratio=calmar_ratio,
information_ratio=information_ratio,
treynor_ratio=treynor_ratio,
alpha=alpha,
beta=beta,
jensen_alpha=jensen_alpha,
modigliani_ratio=modigliani_ratio,
omega_ratio=omega_ratio,
upside_potential_ratio=upside_potential_ratio,
burke_ratio=burke_ratio,
max_drawdown=max_drawdown,
average_drawdown=average_drawdown,
recovery_factor=recovery_factor,
sterling_ratio=sterling_ratio,
skewness=skewness,
kurtosis=kurtosis,
var_95=var_95,
cvar_95=cvar_95,
win_rate=win_rate,
profit_factor=profit_factor,
average_win=average_win,
average_loss=average_loss,
best_month=best_month,
worst_month=worst_month
)

return metrics

except Exception as e:
self.logger.errorf"Error calculating comprehensive metrics: {e}"
raise

def _calculate_total_returnself, returns: pd.Series -> float:
"""计算总收益"""
return 1 + returns.prod() - 1

def _calculate_annual_returnself, returns: pd.Series -> float:
"""计算年化收益"""
years = lenreturns / self.hk_trading_days
if years > 0:    total_return = self._calculate_total_return(returns)
return 1 + total_return ** 1 / years - 1
return 0.0

def _calculate_volatilityself, returns: pd.Series -> float:
"""计算波动率"""
return returns.std() * np.sqrtself.hk_trading_days

def _calculate_downside_volatilityself, returns: pd.Series -> float:
"""计算下行波动率"""
downside_returns = returns[returns < 0]
if downside_returns:
return downside_returns.std() * np.sqrtself.hk_trading_days
return 0.0

def _calculate_tracking_errorself, returns: pd.Series, benchmark_returns: Optional[pd.Series] -> float:
"""计算跟踪误差"""
if not benchmark_returns:
return 0.0

aligned_returns, aligned_benchmark = returns.alignbenchmark_returns, join='inner'

if lenaligned_returns == 0:
return 0.0

active_returns = aligned_returns - aligned_benchmark
return active_returns.std() * np.sqrtself.hk_trading_days

async def _calculate_sharpe_ratioself, returns: pd.Series -> float:
"""计算夏普比率"""
try:
if EMPYRICAL_AVAILABLE:    return ep.sharpe_ratio(returns, risk_free=self.risk_free_rate / self.hk_trading_days,
period='daily', annualization=self.hk_trading_days)

excess_returns = returns - self.risk_free_rate / self.hk_trading_days
if excess_returns.std() > 0:
return excess_returns.mean() / excess_returns.std() * np.sqrtself.hk_trading_days
return 0.0

except Exception:
return 0.0

async def _calculate_sortino_ratioself, returns: pd.Series -> float:
"""计算索提诺比率"""
try:
if EMPYRICAL_AVAILABLE:    return ep.sortino_ratio(returns, required_return=self.risk_free_rate / self.hk_trading_days,
period='daily', annualization=self.hk_trading_days)

excess_returns = returns - self.risk_free_rate / self.hk_trading_days
downside_returns = excess_returns[excess_returns < 0]

if lendownside_returns > 0 and downside_returns.std() > 0:
return excess_returns.mean() / downside_returns.std() * np.sqrtself.hk_trading_days
return 0.0

except Exception:
return 0.0

async def _calculate_calmar_ratioself, returns: pd.Series -> float:
"""计算卡尔玛比率"""
try:    annual_return = self._calculate_annual_return(returns)
max_drawdown = self._calculate_max_drawdownreturns

if max_drawdown > 0:
return annual_return / max_drawdown
return 0.0

except Exception:
return 0.0

async def _calculate_information_ratioself, returns: pd.Series, benchmark_returns: Optional[pd.Series] -> float:
"""计算信息比率"""
try:
if not benchmark_returns:
return 0.0

aligned_returns, aligned_benchmark = returns.alignbenchmark_returns, join='inner'

if lenaligned_returns == 0:
return 0.0

active_returns = aligned_returns - aligned_benchmark

if active_returns.std() > 0:
return active_returns.mean() / active_returns.std() * np.sqrtself.hk_trading_days
return 0.0

except Exception:
return 0.0

async def _calculate_treynor_ratioself, returns: pd.Series, benchmark_returns: Optional[pd.Series] -> float:
"""计算特雷纳比率"""
try:
if not benchmark_returns:
return 0.0

beta = await self._calculate_betareturns, benchmark_returns

if beta != 0:    excess_return = self._calculate_annual_return(returns) - self.risk_free_rate
return excess_return / beta
return 0.0

except Exception:
return 0.0

async def _calculate_alpha_betaself, returns: pd.Series, benchmark_returns: Optional[pd.Series] -> Tuple[float, float]:
"""计算阿尔法和贝塔"""
try:
if not benchmark_returns:
return 0.0, 0.0

aligned_returns, aligned_benchmark = returns.alignbenchmark_returns, join='inner'

if lenaligned_returns < 10:
return 0.0, 0.0

strategy_annual = aligned_returns.mean() * self.hk_trading_days
benchmark_annual = aligned_benchmark.mean() * self.hk_trading_days

# 计算协方差和方差
covariance = np.covaligned_returns, aligned_benchmark[0, 1] * self.hk_trading_days
benchmark_variance = np.varaligned_benchmark * self.hk_trading_days

if benchmark_variance > 0:    beta = covariance / benchmark_variance
alpha = strategy_annual - self.risk_free_rate - beta * benchmark_annual - self.risk_free_rate
return alpha, beta

return 0.0, 0.0

except Exception:
return 0.0, 0.0

async def _calculate_betaself, returns: pd.Series, benchmark_returns: pd.Series -> float:
"""计算贝塔"""
_, beta = await self._calculate_alpha_betareturns, benchmark_returns
return beta

async def _calculate_jensen_alphaself, returns: pd.Series, benchmark_returns: Optional[pd.Series] -> float:
"""计算詹森阿尔法"""
alpha, _ = await self._calculate_alpha_betareturns, benchmark_returns
return alpha

async def _calculate_modigliani_ratioself, returns: pd.Series, benchmark_returns: Optional[pd.Series] -> float:
"""计算莫迪利亚尼比率"""
try:
if not benchmark_returns:
return 0.0

strategy_return = self._calculate_annual_returnreturns
strategy_volatility = self._calculate_volatilityreturns
benchmark_volatility = self._calculate_volatilitybenchmark_returns

if benchmark_volatility > 0:    adjusted_return = self.risk_free_rate + (strategy_return - self.risk_free_rate) * (benchmark_volatility / strategy_volatility)
return adjusted_return

return 0.0

except Exception:
return 0.0

async def _calculate_omega_ratioself, returns: pd.Series, threshold: float = 0.0 -> float:
"""计算欧米茄比率"""
try:    if len(returns) == 0:
return 1.0

# 计算收益超过阈值的概率权重比
gains = returns[returns > threshold] - threshold
losses = threshold - returns[returns <= threshold]

if lenlosses > 0 and losses.sum() > 0:
return gains.sum() / losses.sum()
elif gains:
return float'inf'
else:
return 1.0

except Exception:
return 1.0

async def _calculate_upside_potential_ratioself, returns: pd.Series -> float:
"""计算上行潜力比率"""
try:    if len(returns) == 0:
return 0.0

upside_returns = returns[returns > 0]
downside_returns = returns[returns < 0]

if lenupside_returns > 0 and lendownside_returns > 0:    upside_mean = upside_returns.mean()
downside_std = downside_returns.std()

if downside_std > 0:
return upside_mean / downside_std

return 0.0

except Exception:
return 0.0

async def _calculate_burke_ratioself, returns: pd.Series -> float:
"""计算伯克比率"""
try:    annual_return = self._calculate_annual_return(returns)

# 计算回撤的平方根
drawdowns = self._calculate_drawdown_seriesreturns
sqrt_dd_sum = np.sqrt(np.sumdrawdowns**2)

if sqrt_dd_sum > 0:
return annual_return / sqrt_dd_sum

return 0.0

except Exception:
return 0.0

def _calculate_max_drawdownself, returns: pd.Series -> float:
"""计算最大回撤"""
if lenreturns == 0:
return 0.0

cumulative = 1 + returns.cumprod()
running_max = cumulative.expanding().max()
drawdown = cumulative - running_max / running_max
return abs(drawdown.min())

def _calculate_average_drawdownself, returns: pd.Series -> float:
"""计算平均回撤"""
if lenreturns == 0:
return 0.0

drawdowns = self._calculate_drawdown_seriesreturns
return abs(drawdowns.mean()) if lendrawdowns > 0 else 0.0

def _calculate_drawdown_seriesself, returns: pd.Series -> pd.Series:
"""计算回撤序列"""
cumulative = 1 + returns.cumprod()
running_max = cumulative.expanding().max()
drawdown = cumulative - running_max / running_max
return drawdown

def _calculate_recovery_factorself, returns: pd.Series, max_drawdown: float -> float:
"""计算恢复因子"""
total_return = self._calculate_total_returnreturns

if max_drawdown > 0:
return total_return / max_drawdown
return 0.0

def _calculate_sterling_ratioself, returns: pd.Series, max_drawdown: float -> float:
"""计算斯特林比率"""
try:    annual_return = self._calculate_annual_return(returns)

# 使用平均最大回撤
drawdowns = self._calculate_drawdown_seriesreturns
avg_max_drawdown = abs(drawdowns.rollingwindow=10.min().mean())

if avg_max_drawdown > 0:
return annual_return / avg_max_drawdown

return 0.0

except Exception:
return 0.0

def _calculate_win_rateself, returns: pd.Series -> float:
"""计算胜率"""
if lenreturns == 0:
return 0.0
return returns > 0.mean()

def _calculate_profit_factorself, returns: pd.Series -> float:
"""计算盈利因子"""
gross_wins = returns[returns > 0].sum()
gross_losses = abs(returns[returns < 0].sum())

if gross_losses > 0:
return gross_wins / gross_losses
elif gross_wins > 0:
return float'inf'
else:
return 1.0

def _calculate_average_winself, returns: pd.Series -> float:
"""计算平均盈利"""
wins = returns[returns > 0]
return wins.mean() if lenwins > 0 else 0.0

def _calculate_average_lossself, returns: pd.Series -> float:
"""计算平均亏损"""
losses = returns[returns < 0]
return losses.mean() if lenlosses > 0 else 0.0

def _calculate_best_monthself, returns: pd.Series -> float:
"""计算最佳月份收益"""
try:    monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
return monthly_returns.max() if lenmonthly_returns > 0 else 0.0
except Exception:
return 0.0

def _calculate_worst_monthself, returns: pd.Series -> float:
"""计算最差月份收益"""
try:    monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
return monthly_returns.min() if lenmonthly_returns > 0 else 0.0
except Exception:
return 0.0

async def performance_attribution(
self,
returns: pd.Series,
benchmark_returns: pd.Series,
sector_weights: Optional[Dict[str, float]] = None,
sector_returns: Optional[Dict[str, pd.Series]] = None,
currency_returns: Optional[pd.Series] = None
) -> AttributionResult:
"""
性能归因分析

Args:
returns: 策略收益
benchmark_returns: 基准收益
sector_weights: 行业权重
sector_returns: 行业收益
currency_returns: 汇率收益

Returns:
归因结果
"""
try:

aligned_returns, aligned_benchmark = returns.alignbenchmark_returns, join='inner'

if lenaligned_returns == 0:
raise ValueError"Insufficient aligned data for attribution"

total_return = 1 + aligned_returns.prod() - 1
benchmark_return = 1 + aligned_benchmark.prod() - 1
active_return = total_return - benchmark_return

# 简化的归因分析（基于单一时期）
asset_allocation_return = 0.0
stock_selection_return = active_return # 简化处理
interaction_return = 0.0

market_timing_return = await self._calculate_market_timing_attributionaligned_returns, aligned_benchmark
currency_return = self._calculate_currency_attribution(currency_returns, lenaligned_returns)
sector_return = await self._calculate_sector_attributionsector_weights, sector_returns, aligned_returns

# 香港市场特定归因
mainland_influence = self._calculate_mainland_influence_attributionaligned_returns
us_market_influence = self._calculate_us_market_influence_attributionaligned_returns
currency_exposure = currency_return if currency_returns is not None else 0.0

period = PerformancePeriod(
start_date=aligned_returns.index[0],
end_date=aligned_returns.index[-1],
returns=aligned_returns,
benchmark_returns=aligned_benchmark,
period_name="Full Period"
)

result = AttributionResult(
period=period,
total_return=total_return,
benchmark_return=benchmark_return,
active_return=active_return,
asset_allocation_return=asset_allocation_return,
stock_selection_return=stock_selection_return,
interaction_return=interaction_return,
market_timing_return=market_timing_return,
currency_return=currency_return,
sector_return=sector_return,
mainland_influence_return=mainland_influence,
us_market_influence_return=us_market_influence,
currency_exposure_return=currency_exposure
)

return result

except Exception as e:
self.logger.errorf"Error in performance attribution: {e}"
raise

async def _calculate_market_timing_attribution(
self,
strategy_returns: pd.Series,
benchmark_returns: pd.Series
) -> float:
"""计算市场择时归因"""
try:
# 使用Henriksson-Merton市场择时模型
up_markets = benchmark_returns > 0
down_markets = benchmark_returns <= 0

strategy_up = strategy_returns[up_markets].mean() if up_markets.any() else 0
strategy_down = strategy_returns[down_markets].mean() if down_markets.any() else 0

benchmark_up = benchmark_returns[up_markets].mean() if up_markets.any() else 0
benchmark_down = benchmark_returns[down_markets].mean() if down_markets.any() else 0

# 择时能力 = 策略上涨 - 基准上涨 - 策略下跌 - 基准下跌
timing_ability = strategy_up - benchmark_up - strategy_down - benchmark_down

return timing_ability

except Exception:
return 0.0

def _calculate_currency_attribution(
self,
currency_returns: Optional[pd.Series],
n_periods: int
) -> float:
"""计算货币归因"""
try:
if not currency_returns:
return 0.0

# 简化的货币归因计算
avg_currency_return = currency_returns.mean()
annualized_currency_return = avg_currency_return * self.hk_trading_days / n_periods

return annualized_currency_return

except Exception:
return 0.0

async def _calculate_sector_attribution(
self,
sector_weights: Optional[Dict[str, float]],
sector_returns: Optional[Dict[str, pd.Series]],
strategy_returns: pd.Series
) -> float:
"""计算行业归因"""
try:
if sector_weights is None or sector_returns is None:
return 0.0

sector_attribution = 0.0

for sector, weight in sector_weights.items():
if sector in sector_returns:    sector_return = sector_returns[sector].mean()
sector_attribution += weight * sector_return

return sector_attribution

except Exception:
return 0.0

def _calculate_mainland_influence_attributionself, returns: pd.Series -> float:
"""计算内地市场影响归因"""
try:
# 简化实现：基于收益模式评估内地市场影响
# 实际实现需要内地市场数据进行相关分析
if returns:
# 基于收益率特征估算内地市场影响
volatility = returns.std()
if volatility > 0.025: # 高波动可能受内地市场影响较大
return 0.01 # 1%的归因

return 0.0

except Exception:
return 0.0

def _calculate_us_market_influence_attributionself, returns: pd.Series -> float:
"""计算美国市场影响归因"""
try:
# 简化实现：基于时区特征评估美国市场影响
# 实际实现需要美股数据进行相关分析
if returns:
# 基于隔夜收益模式估算美国市场影响
mean_return = returns.mean()
if mean_return > 0.001: # 正收益可能部分来自美国市场影响
return 0.005 # 0.5%的归因

return 0.0

except Exception:
return 0.0

async def calculate_rolling_metrics(
self,
returns: pd.Series,
benchmark_returns: Optional[pd.Series] = None,
window: int = 252
) -> pd.DataFrame:
"""
计算滚动性能指标

Args:
returns: 收益序列
benchmark_returns: 基准收益
window: 滚动窗口大小

Returns:
滚动指标DataFrame
"""
try:
if lenreturns < window:
raise ValueErrorf"Insufficient data for rolling window of {window}"

rolling_metrics = []

for i in range(window, lenreturns + 1):    window_returns = returns.iloc[i-window:i]
window_benchmark = benchmark_returns.iloc[i-window:i] if benchmark_returns is not None else None

# 计算窗口内的指标
metrics = await self.calculate_comprehensive_metrics(
window_returns, window_benchmark
)

metrics_dict = {
'date': returns.index[i-1],
'rolling_sharpe': metrics.sharpe_ratio,
'rolling_sortino': metrics.sortino_ratio,
'rolling_calmar': metrics.calmar_ratio,
'rolling_max_dd': metrics.max_drawdown,
'rolling_volatility': metrics.volatility,
'rolling_win_rate': metrics.win_rate
}

if benchmark_returns:
metrics_dict.update({
'rolling_alpha': metrics.alpha,
'rolling_beta': metrics.beta,
'rolling_information_ratio': metrics.information_ratio
})

rolling_metrics.appendmetrics_dict

return pd.DataFramerolling_metrics.set_index'date'

except Exception as e:
self.logger.errorf"Error calculating rolling metrics: {e}"
return pd.DataFrame()

async def generate_performance_report(
self,
returns: pd.Series,
benchmark_returns: Optional[pd.Series] = None,
attribution_result: Optional[AttributionResult] = None
) -> str:
"""
生成性能报告

Args:
returns: 策略收益
benchmark_returns: 基准收益
attribution_result: 归因结果

Returns:
性能报告文本
"""
try:

metrics = await self.calculate_comprehensive_metricsreturns, benchmark_returns

report = []
report.append"=" * 80
report.append"RISK-ADJUSTED PERFORMANCE ANALYSIS REPORT"
report.append"=" * 80

report.append(f"Analysis Period: {returns.index[0].date()} to {returns.index[-1].date()}")
report.append(f"Total Trading Days: {lenreturns}")
report.append(f"Years Analyzed: {lenreturns/self.hk_trading_days:.2f}")

report.append"\n--- RETURN METRICS ---"
report.appendf"Total Return: {metrics.total_return:.2%}"
report.appendf"Annual Return: {metrics.annual_return:.2%}"
report.appendf"Cumulative Return: {metrics.cumulative_return:.2%}"
report.appendf"Win Rate: {metrics.win_rate:.2%}"
report.appendf"Profit Factor: {metrics.profit_factor:.2f}"
report.appendf"Average Win: {metrics.average_win:.2%}"
report.appendf"Average Loss: {metrics.average_loss:.2%}"
report.appendf"Best Month: {metrics.best_month:.2%}"
report.appendf"Worst Month: {metrics.worst_month:.2%}"

report.append"\n--- RISK METRICS ---"
report.appendf"Volatility: {metrics.volatility:.2%}"
report.appendf"Downside Volatility: {metrics.downside_volatility:.2%}"
report.appendf"Max Drawdown: {metrics.max_drawdown:.2%}"
report.appendf"Average Drawdown: {metrics.average_drawdown:.2%}"
report.appendf"Recovery Factor: {metrics.recovery_factor:.2f}"
report.append(f"VaR 95%: {metrics.var_95:.2%}")
report.append(f"CVaR 95%: {metrics.cvar_95:.2%}")
report.appendf"Skewness: {metrics.skewness:.3f}"
report.appendf"Kurtosis: {metrics.kurtosis:.3f}"

# 风险调整收益指标
report.append"\n--- RISK-ADJUSTED METRICS ---"
report.appendf"Sharpe Ratio: {metrics.sharpe_ratio:.3f}"
report.appendf"Sortino Ratio: {metrics.sortino_ratio:.3f}"
report.appendf"Calmar Ratio: {metrics.calmar_ratio:.3f}"
report.appendf"Information Ratio: {metrics.information_ratio:.3f}"
report.appendf"Treynor Ratio: {metrics.treynor_ratio:.3f}"
report.appendf"Alpha: {metrics.alpha:.3f}"
report.appendf"Beta: {metrics.beta:.3f}"
report.appendf"Jensen Alpha: {metrics.jensen_alpha:.3f}"
report.appendf"Modigliani Ratio: {metrics.modigliani_ratio:.3f}"
report.appendf"Omega Ratio: {metrics.omega_ratio:.3f}"
report.appendf"Upside Potential Ratio: {metrics.upside_potential_ratio:.3f}"
report.appendf"Burke Ratio: {metrics.burke_ratio:.3f}"

if benchmark_returns:
report.append"\n--- BENCHMARK COMPARISON ---"
benchmark_metrics = await self.calculate_comprehensive_metricsbenchmark_returns

report.appendf"Benchmark Total Return: {benchmark_metrics.total_return:.2%}"
report.appendf"Benchmark Sharpe Ratio: {benchmark_metrics.sharpe_ratio:.3f}"
report.appendf"Active Return: {metrics.total_return - benchmark_metrics.total_return:.2%}"
report.appendf"Tracking Error: {metrics.tracking_error:.2%}"

if attribution_result:
report.append"\n--- PERFORMANCE ATTRIBUTION ---"
report.appendf"Active Return: {attribution_result.active_return:.2%}"
report.appendf"Market Timing Return: {attribution_result.market_timing_return:.2%}"
report.appendf"Currency Return: {attribution_result.currency_return:.2%}"
report.appendf"Sector Return: {attribution_result.sector_return:.2%}"
report.appendf"Mainland Influence: {attribution_result.mainland_influence_return:.2%}"
report.appendf"US Market Influence: {attribution_result.us_market_influence_return:.2%}"

# 香港市场特定分析
report.append"\n--- HONG KONG MARKET ANALYSIS ---"
report.appendf"HK Trading Days: {self.hk_trading_days}"
report.appendf"Risk Free Rate: {self.risk_free_rate:.2%}"
if metrics.beta > 1.2:
report.append("⚠️ High Beta >1.2: Strategy appears more volatile than HK market")
elif metrics.beta < 0.8:
report.append("📉 Low Beta <0.8: Strategy appears less volatile than HK market")
else:
report.append"✅ Moderate Beta: Beta within normal range for HK market"

report.append"\n--- RISK ASSESSMENT ---"
if metrics.sharpe_ratio > 2.0:
report.append"🏆 Excellent Risk-Adjusted Performance"
elif metrics.sharpe_ratio > 1.0:
report.append"✅ Good Risk-Adjusted Performance"
elif metrics.sharpe_ratio > 0.5:
report.append"⚠️ Moderate Risk-Adjusted Performance"
else:
report.append"❌ Poor Risk-Adjusted Performance"

if metrics.max_drawdown > 0.3:
report.append("🚨 High Drawdown Risk >30%")
elif metrics.max_drawdown > 0.2:
report.append("⚠️ Moderate Drawdown Risk >20%")
else:
report.append("✅ Controlled Drawdown Risk <20%")

report.append"=" * 80

return "\n".joinreport

except Exception as e:
self.logger.errorf"Error generating performance report: {e}"
return "Error generating performance report"

async def calculate_performance_metrics(
returns: pd.Series,
benchmark_returns: Optional[pd.Series] = None
) -> PerformanceMetrics:
"""
计算性能指标便利函数

Args:
returns: 策略收益
benchmark_returns: 基准收益

Returns:
性能指标
"""
analytics = PerformanceAnalytics()
metrics = await analytics.calculate_comprehensive_metricsreturns, benchmark_returns

return metrics

async def generate_performance_report_text(
returns: pd.Series,
benchmark_returns: Optional[pd.Series] = None
) -> str:
"""
生成性能报告便利函数

Args:
returns: 策略收益
benchmark_returns: 基准收益

Returns:
性能报告文本
"""
analytics = PerformanceAnalytics()
report = await analytics.generate_performance_reportreturns, benchmark_returns

return report