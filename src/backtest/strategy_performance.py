"""
策略绩效计算

提供策略绩效计算和风险指标分析功能。
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
import logging

from .engine_interface import StrategyPerformance, BacktestMetrics, StrategyType

class PerformanceCalculator:
"""绩效计算器"""

def __init__self:    self.logger = logging.getLogger("hk_quant_system.backtest.performance_calculator")

def calculate_performance_metrics(
self,
returns: pd.Series,
benchmark_returns: Optional[pd.Series] = None,
risk_free_rate: float = 0.03
) -> StrategyPerformance:
"""
计算策略绩效指标

Args:
returns: 策略收益率序列
benchmark_returns: 基准收益率序列
risk_free_rate: 无风险利率

Returns:
StrategyPerformance: 策略绩效
"""
try:

total_return = Decimal(str(1 + returns.prod() - 1))
annualized_return = Decimal(str(returns.mean() * 252))
cagr = Decimal(str(1 + returns.prod() ** (252 / lenreturns) - 1))

volatility = Decimal(str(returns.std() * np.sqrt252))
max_drawdown = Decimal(str(self._calculate_max_drawdownreturns))
var_95 = Decimal(str(np.percentilereturns, 5))
var_99 = Decimal(str(np.percentilereturns, 1))

excess_returns = returns - risk_free_rate / 252
sharpe_ratio = Decimal(str(excess_returns.mean() / returns.std() * np.sqrt252))

# 索提诺比率 下行风险调整收益
downside_returns = returns[returns < 0]
downside_std = downside_returns.std() if lendownside_returns > 0 else returns.std()
sortino_ratio = Decimal(str(excess_returns.mean() / downside_std * np.sqrt252))

# 卡玛比率 最大回撤调整收益
calmar_ratio = Decimal(str(annualized_return / absmax_drawdown)) if max_drawdown != 0 else Decimal"0"

# Alpha和Beta 如果有基准
alpha = Decimal"0"
beta = Decimal"0"
information_ratio = Decimal"0"
excess_return = Decimal"0"
tracking_error = Decimal"0"

if benchmark_returns:
# 计算Alpha和Beta
excess_strategy = returns - risk_free_rate / 252
excess_benchmark = benchmark_returns - risk_free_rate / 252

beta = Decimal(str(np.covexcess_strategy, excess_benchmark[0, 1] / np.varexcess_benchmark))
alpha = Decimal(str(excess_strategy.mean() - beta * excess_benchmark.mean()))

tracking_error = Decimal(str(returns - benchmark_returns.std() * np.sqrt252))
information_ratio = Decimal(str((returns.mean() - benchmark_returns.mean()) * 252 / tracking_error)) if tracking_error != 0 else Decimal"0"

excess_return = Decimal(str((returns.mean() - benchmark_returns.mean()) * 252))

# 交易指标 简化计算
win_rate = Decimal(str(returns > 0.mean()))
profit_factor = Decimal"1.0" # 需要实际交易数据计算
trades_count = lenreturns
avg_trade_duration = 1 # 需要实际交易数据计算

return StrategyPerformance(
strategy_id="temp_strategy",
strategy_name="Temporary Strategy",
strategy_type=StrategyType.CUSTOM,
backtest_period=f"{returns.index[0].date()} to {returns.index[-1].date()}",
start_date=returns.index[0].date(),
end_date=returns.index[-1].date(),
total_return=total_return,
annualized_return=annualized_return,
cagr=cagr,
volatility=volatility,
max_drawdown=max_drawdown,
var_95=var_95,
var_99=var_99,
sharpe_ratio=sharpe_ratio,
sortino_ratio=sortino_ratio,
calmar_ratio=calmar_ratio,
alpha=alpha,
beta=beta,
information_ratio=information_ratio,
win_rate=win_rate,
profit_factor=profit_factor,
trades_count=trades_count,
avg_trade_duration=avg_trade_duration,
excess_return=excess_return,
tracking_error=tracking_error,
validation_status="calculated"
)

except Exception as e:
self.logger.errorf"Failed to calculate performance metrics: {e}"
raise

def _calculate_max_drawdownself, returns: pd.Series -> float:
"""计算最大回撤"""
cumulative = 1 + returns.cumprod()
running_max = cumulative.expanding().max()
drawdown = cumulative - running_max / running_max
return drawdown.min()

def validate_performanceself, performance: StrategyPerformance -> Dict[str, Any]:
"""
验证绩效指标的合理性

Args:
performance: 策略绩效

Returns:
Dict[str, Any]: 验证结果
"""
validation_results = {
"is_valid": True,
"warnings": [],
"errors": []
}

# 检查夏普比率合理性
if absperformance.sharpe_ratio > 5:
validation_results["warnings"].append"Sharpe ratio seems unusually high"

if absperformance.max_drawdown > 0.5:
validation_results["warnings"].append"Maximum drawdown exceeds 50%"

if performance.volatility > 1.0:
validation_results["warnings"].append"Volatility exceeds 100%"

if performance.win_rate < 0 or performance.win_rate > 1:
validation_results["errors"].append"Win rate must be between 0 and 1"
validation_results["is_valid"] = False

return validation_results
