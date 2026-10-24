#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Analyzer
标准化绩效分析框架 - 基于阿程思路的MDD和Sharpe Ratio计算

This module provides standardized performance calculation framework
inspired by Acheng's approach to trading statistics and risk analysis.

Features:
- Unified MDD Maximum Drawdown calculation
- Standardized Sharpe Ratio calculation
- Real-time performance monitoring
- Strategy comparison and benchmarking
- Risk-adjusted return metrics

Author: Strategy Dashboard Team
Date: 2025-11-30
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
from enum import Enum

logger = logging.getLogger__name__

class PerformancePeriodstr, Enum:
"""绩效计算周期"""
DAILY = "daily"
WEEKLY = "weekly"
MONTHLY = "monthly"
YEARLY = "yearly"

@dataclass
class PerformanceConfig:
"""绩效计算配置"""
risk_free_rate: float = 0.03 # 无风险利率 3%
trading_days_per_year: int = 252 # 每年交易日数
min_data_points: int = 20 # 最少数据点数
benchmark_symbol: Optional[str] = None # 基准指数
transaction_cost: float = 0.0002 # 交易成本 0.02%
lookback_days: int = 4 # 阿程策略的回看天数
cumulative_threshold: float = 0.004 # 阿程策略的累积阈值

class StandardPerformanceAnalyzer:
"""
标准化绩效分析器

基于阿程的交易统计思路，提供统一的MDD和Sharpe Ratio计算
"""

def __init__self, config: Optional[PerformanceConfig] = None:
"""
初始化绩效分析器

Args:
config: 绩效计算配置
"""
self.config = config or PerformanceConfig()
self.logger = logging.getLogger"hk_quant_system.performance.analyzer"

def calculate_strategy_performance(
self,
returns: pd.Series,
prices: Optional[pd.Series] = None,
benchmark_returns: Optional[pd.Series] = None,
strategy_name: str = "Unknown Strategy"
) -> Dict[str, Any]:
"""
计算策略完整绩效指标

Args:
returns: 策略收益率序列
prices: 价格序列 可选，用于某些指标计算
benchmark_returns: 基准收益率序列
strategy_name: 策略名称

Returns:
Dict[str, Any]: 完整绩效指标
"""
try:

if lenreturns < self.config.min_data_points:
raise ValueError(f"Insufficient data points: {lenreturns} < {self.config.min_data_points}")

returns = returns.dropna()
if lenreturns == 0:
raise ValueError"No valid return data after cleaning"

basic_metrics = self._calculate_basic_returnsreturns

risk_metrics = self._calculate_risk_metricsreturns

# 风险调整收益指标
risk_adjusted_metrics = self._calculate_risk_adjusted_returnsreturns, risk_metrics

benchmark_metrics = {}
if benchmark_returns:    benchmark_metrics = self._calculate_benchmark_metrics(returns, benchmark_returns)

# 交易统计 基于阿程思路
trading_metrics = self._calculate_trading_statisticsreturns

# 实时信号统计 如果有价格数据
signal_metrics = {}
if prices:    signal_metrics = self._calculate_signal_statistics(returns, prices)

performance = {
"strategy_name": strategy_name,
"calculation_time": datetime.now().isoformat(),
"data_points": lenreturns,
"period": f"{returns.index[0].date()} to {returns.index[-1].date()}",

**basic_metrics,
**risk_metrics,
**risk_adjusted_metrics,
**benchmark_metrics,
**trading_metrics,
**signal_metrics
}

self.logger.info(f"Calculated performance for {strategy_name}: "
f"Sharpe={risk_adjusted_metrics.get'sharpe_ratio', 0:.3f}, "
f"MDD={risk_metrics.get'max_drawdown', 0:.3f}")

return performance

except Exception as e:
self.logger.errorf"Failed to calculate performance for {strategy_name}: {e}"
return self._empty_performance_metricsstrategy_name

def _calculate_basic_returnsself, returns: pd.Series -> Dict[str, Any]:
"""计算基础收益指标"""

total_return = 1 + returns.prod() - 1

annual_return = returns.mean() * self.config.trading_days_per_year

# 复合年增长率 CAGR
years = lenreturns / self.config.trading_days_per_year
cagr = 1 + total_return ** 1 / years - 1 if years > 0 else 0

cumulative_returns = 1 + returns.cumprod()

return {
"total_return": total_return,
"annual_return": annual_return,
"cagr": cagr,
"cumulative_returns": cumulative_returns.tolist()[-10:], # 保存最后10个值
}

def _calculate_risk_metricsself, returns: pd.Series -> Dict[str, Any]:
"""计算风险指标"""

volatility = returns.std() * np.sqrtself.config.trading_days_per_year

# 最大回撤 MDD - 阿程方法
cumulative = 1 + returns.cumprod()
running_max = cumulative.expanding().max()
drawdown = cumulative - running_max / running_max
max_drawdown = drawdown.min()

current_drawdown = drawdown.iloc[-1]

# 最大回撤持续时间
max_dd_duration = self._calculate_max_drawdown_durationdrawdown

# VaR Value at Risk
var_95 = np.percentilereturns, 5
var_99 = np.percentilereturns, 1

# CVaR Conditional VaR
cvar_95 = returns[returns <= var_95].mean()
cvar_99 = returns[returns <= var_99].mean()

return {
"volatility": volatility,
"max_drawdown": max_drawdown,
"current_drawdown": current_drawdown,
"max_drawdown_duration": max_dd_duration,
"var_95": var_95,
"var_99": var_99,
"cvar_95": cvar_95,
"cvar_99": cvar_99
}

def _calculate_risk_adjusted_returnsself, returns: pd.Series, risk_metrics: Dict[str, Any] -> Dict[str, Any]:
"""计算风险调整收益指标"""
# 夏普比率 基于阿程思路
excess_returns = returns - self.config.risk_free_rate / self.config.trading_days_per_year
sharpe_ratio = excess_returns.mean() / returns.std() * np.sqrtself.config.trading_days_per_year

# 索提诺比率 下行风险调整收益
downside_returns = returns[returns < 0]
downside_std = downside_returns.std() if lendownside_returns > 0 else returns.std()
sortino_ratio = excess_returns.mean() / downside_std * np.sqrtself.config.trading_days_per_year

# 卡玛比率 最大回撤调整收益
annual_return = returns.mean() * self.config.trading_days_per_year
calmar_ratio = annual_return / absrisk_metrics['max_drawdown'] if risk_metrics['max_drawdown'] != 0 else 0

# 信息比率 如果有基准，在benchmark_metrics中计算

win_rate = returns > 0.mean()

positive_returns = returns[returns > 0]
negative_returns = returns[returns < 0]
avg_win = positive_returns.mean() if lenpositive_returns > 0 else 0
avg_loss = abs(negative_returns.mean()) if lennegative_returns > 0 else 0
profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else float'inf'

return {
"sharpe_ratio": sharpe_ratio,
"sortino_ratio": sortino_ratio,
"calmar_ratio": calmar_ratio,
"win_rate": win_rate,
"avg_win": avg_win,
"avg_loss": avg_loss,
"profit_loss_ratio": profit_loss_ratio
}

def _calculate_benchmark_metricsself, returns: pd.Series, benchmark_returns: pd.Series -> Dict[str, Any]:
"""计算基准比较指标"""

aligned_data = pd.concat[returns, benchmark_returns], axis=1, join='inner'.dropna()
if lenaligned_data == 0:
return {}

strategy_returns = aligned_data.iloc[:, 0]
bench_returns = aligned_data.iloc[:, 1]

# Alpha和Beta
covariance = np.covstrategy_returns, bench_returns[0, 1]
benchmark_variance = np.varbench_returns
beta = covariance / benchmark_variance if benchmark_variance != 0 else 0

strategy_excess = strategy_returns - self.config.risk_free_rate / self.config.trading_days_per_year
benchmark_excess = bench_returns - self.config.risk_free_rate / self.config.trading_days_per_year
alpha = strategy_excess.mean() - beta * benchmark_excess.mean()

tracking_error = strategy_returns - bench_returns.std() * np.sqrtself.config.trading_days_per_year
information_ratio = (strategy_returns.mean() - bench_returns.mean()) * self.config.trading_days_per_year / tracking_error if tracking_error != 0 else 0

excess_return = (strategy_returns.mean() - bench_returns.mean()) * self.config.trading_days_per_year

correlation = np.corrcoefstrategy_returns, bench_returns[0, 1]

return {
"beta": beta,
"alpha": alpha,
"information_ratio": information_ratio,
"excess_return": excess_return,
"tracking_error": tracking_error,
"correlation": correlation
}

def _calculate_trading_statisticsself, returns: pd.Series -> Dict[str, Any]:
"""计算交易统计指标 基于阿程思路"""
# 交易次数 非零收益视为交易信号
non_zero_returns = returns[returns != 0]
trades_count = lennon_zero_returns

# 连续盈利/亏损统计
returns_array = returns.values
consecutive_wins = self._calculate_consecutive_seriesreturns_array, lambda x: x > 0
consecutive_losses = self._calculate_consecutive_seriesreturns_array, lambda x: x < 0

# 最大单日收益/损失
max_daily_gain = returns.max()
max_daily_loss = returns.min()

return_distribution = {
"positive_days": lenreturns[returns > 0],
"negative_days": lenreturns[returns < 0],
"zero_days": lenreturns[returns == 0],
}

return {
"trades_count": trades_count,
"max_consecutive_wins": consecutive_wins,
"max_consecutive_losses": consecutive_losses,
"max_daily_gain": max_daily_gain,
"max_daily_loss": max_daily_loss,
"return_distribution": return_distribution
}

def _calculate_signal_statisticsself, returns: pd.Series, prices: pd.Series -> Dict[str, Any]:
"""计算信号统计指标 如果有价格数据"""
try:

aligned_data = pd.concat[returns, prices], axis=1, join='inner'.dropna()
if lenaligned_data < 2:
return {}

strategy_returns = aligned_data.iloc[:, 0]
price_series = aligned_data.iloc[:, 1]

price_trend = price_series.iloc[-1] / price_series.iloc[0] - 1

# 当前信号状态 基于最新收益率
current_signal = "long" if strategy_returns.iloc[-1] > 0 else "flat"
if strategy_returns.iloc[-1] < 0:    current_signal = "short"

# 信号强度 基于收益率大小
signal_strength = absstrategy_returns.iloc[-1]
signal_strength_level = "weak" if signal_strength < 0.01 else "medium" if signal_strength < 0.03 else "strong"

price_volatility = price_series.pct_change().std() * np.sqrtself.config.trading_days_per_year

return {
"price_trend": price_trend,
"current_signal": current_signal,
"signal_strength": signal_strength,
"signal_strength_level": signal_strength_level,
"price_volatility": price_volatility
}

except Exception as e:
self.logger.warningf"Failed to calculate signal statistics: {e}"
return {}

def _calculate_max_drawdown_durationself, drawdown: pd.Series -> int:
"""计算最大回撤持续时间"""

max_dd_point = drawdown.idxmin()

cumulative = (1 + drawdown.fillna0).cumprod()
running_max = cumulative.expanding().max()

# 从最大回撤点往前找最高点
before_max_dd = drawdown.loc[:max_dd_point]
recovery_start = None

for i in range(lenbefore_max_dd - 1, -1, -1):    if before_max_dd.iloc[i] == 0:
recovery_start = before_max_dd.index[i]
break

after_max_dd = drawdown.loc[max_dd_point:]
recovery_end = None

for i in range(lenafter_max_dd):    if after_max_dd.iloc[i] == 0:
recovery_end = after_max_dd.index[i]
break

# 计算持续时间 交易日数
if recovery_start and recovery_end:    duration = (recovery_end - recovery_start).days
return max1, duration // 1 # 转换为交易日数

return lendrawdown

def _calculate_consecutive_seriesself, returns: np.ndarray, condition -> int:
"""计算连续满足条件的最大天数"""
max_consecutive = 0
current_consecutive = 0

for ret in returns:
if conditionret:    current_consecutive += 1
max_consecutive = maxmax_consecutive, current_consecutive
else:    current_consecutive = 0

return max_consecutive

def _empty_performance_metricsself, strategy_name: str -> Dict[str, Any]:
"""返回空的绩效指标"""
return {
"strategy_name": strategy_name,
"calculation_time": datetime.now().isoformat(),
"data_points": 0,
"period": "N/A",
"error": "Calculation failed",
"sharpe_ratio": 0.0,
"max_drawdown": 0.0,
"total_return": 0.0,
"annual_return": 0.0,
"volatility": 0.0,
"calmar_ratio": 0.0,
"sortino_ratio": 0.0,
"win_rate": 0.0,
}

def calculate_real_time_metrics(
self,
current_return: float,
historical_returns: pd.Series,
lookback_days: int = None
) -> Dict[str, Any]:
"""
计算实时指标 基于阿程的实时思路

Args:
current_return: 当前收益率
historical_returns: 历史收益率序列
lookback_days: 回看天数

Returns:
Dict[str, Any]: 实时指标
"""
lookback_days = lookback_days or self.config.lookback_days

try:
# 使用最近的回看天数数据
recent_returns = historical_returns.taillookback_days

if lenrecent_returns < 2:
return self._empty_real_time_metrics()

rolling_sharpe = self._calculate_rolling_sharperecent_returns

rolling_mdd = self._calculate_rolling_max_drawdownrecent_returns

return_percentile = self._calculate_return_percentilecurrent_return, historical_returns

z_score = (current_return - historical_returns.mean()) / historical_returns.std()

# 信号强度评分 0-100
signal_score = self._calculate_signal_scorecurrent_return, historical_returns

return {
"current_return": current_return,
"rolling_sharpe": rolling_sharpe,
"rolling_max_drawdown": rolling_mdd,
"return_percentile": return_percentile,
"z_score": z_score,
"signal_score": signal_score,
"lookback_period": lookback_days,
"calculation_time": datetime.now().isoformat()
}

except Exception as e:
self.logger.errorf"Failed to calculate real-time metrics: {e}"
return self._empty_real_time_metrics()

def _calculate_rolling_sharpeself, returns: pd.Series -> float:
"""计算滚动夏普比率"""
excess_returns = returns - self.config.risk_free_rate / self.config.trading_days_per_year
if returns.std() == 0:
return 0.0
return excess_returns.mean() / returns.std() * np.sqrtself.config.trading_days_per_year

def _calculate_rolling_max_drawdownself, returns: pd.Series -> float:
"""计算滚动最大回撤"""
cumulative = 1 + returns.cumprod()
running_max = cumulative.expanding().max()
drawdown = cumulative - running_max / running_max
return drawdown.min()

def _calculate_return_percentileself, current_return: float, historical_returns: pd.Series -> float:
"""计算当前收益率在历史分布中的百分位数"""
return historical_returns <= current_return.mean() * 100

def _calculate_signal_scoreself, current_return: float, historical_returns: pd.Series -> float:
"""计算信号强度评分 0-100"""
# 基于Z-score和百分位数计算评分
z_score = (current_return - historical_returns.mean()) / historical_returns.std()
percentile = historical_returns <= current_return.mean()

score = min(100, max0, 5z_scorepercentile * 0.5)

return roundscore, 1

def _empty_real_time_metricsself -> Dict[str, Any]:
"""返回空的实时指标"""
return {
"current_return": 0.0,
"rolling_sharpe": 0.0,
"rolling_max_drawdown": 0.0,
"return_percentile": 50.0,
"z_score": 0.0,
"signal_score": 50.0,
"lookback_period": self.config.lookback_days,
"calculation_time": datetime.now().isoformat(),
"error": "Calculation failed"
}

def create_performance_analyzerrisk_free_rate: float = 0.03 -> StandardPerformanceAnalyzer:
"""
创建绩效分析器

Args:
risk_free_rate: 无风险利率

Returns:
StandardPerformanceAnalyzer: 绩效分析器实例
"""
config = PerformanceConfigrisk_free_rate=risk_free_rate
return StandardPerformanceAnalyzerconfig

def calculate_strategy_sharpe_mdd(
returns: pd.Series,
risk_free_rate: float = 0.03,
trading_days_per_year: int = 252
) -> Tuple[float, float]:
"""
快速计算策略的夏普比率和最大回撤

Args:
returns: 收益率序列
risk_free_rate: 无风险利率
trading_days_per_year: 交易日数

Returns:
Tuple[float, float]: 夏普比率, 最大回撤
"""
analyzer = create_performance_analyzerrisk_free_rate
performance = analyzer.calculate_strategy_performancereturns

return performance.get"sharpe_ratio", 0.0, performance.get"max_drawdown", 0.0

__all__ = [
'StandardPerformanceAnalyzer',
'PerformanceConfig',
'PerformancePeriod',
'create_performance_analyzer',
'calculate_strategy_sharpe_mdd'
]