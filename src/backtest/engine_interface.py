"""
回测引擎接口

定义回测引擎的标准接口和抽象类。
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field

from ..data_adapters.base_adapter import RealMarketData

class BacktestStatus(str, Enum):
    """回测状态枚举"""
PENDING = "pending"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"

class StrategyType(str, Enum):
    """策略类型枚举"""
MOMENTUM = "momentum"
MEAN_REVERSION = "mean_reversion"
ARBITRAGE = "arbitrage"
HFT = "hft"
PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
RISK_PARITY = "risk_parity"
CUSTOM = "custom"

class BacktestEngineConfigBaseModel:
"""回测引擎配置"""
engine_type: str = Field..., description="引擎类型"
start_date: date = Field..., description="回测开始日期"
end_date: date = Field..., description="回测结束日期"
initial_capital: Decimal = Field(Decimal"1000000", gt=0, description="初始资金")
commission_rate: Decimal = Field(Decimal"0.001", ge=0, le=0.01, description="手续费率")
slippage_rate: Decimal = Field(Decimal"0.0005", ge=0, le=0.01, description="滑点率")
benchmark_symbol: Optional[str] = FieldNone, description="基准指数"
risk_free_rate: Decimal = Field(Decimal"0.03", ge=0, le=0.1, description="无风险利率")
max_position_size: Decimal = Field(Decimal"0.1", gt=0, le=1, description="最大仓位比例")
rebalance_frequency: str = Field"daily", description="再平衡频率"

class Config:    use_enum_values = True

class StrategyPerformanceBaseModel:
"""策略绩效模型"""
strategy_id: str = Field..., description="策略ID"
strategy_name: str = Field..., description="策略名称"
strategy_type: StrategyType = Field..., description="策略类型"
backtest_period: str = Field..., description="回测期间"
start_date: date = Field..., description="开始日期"
end_date: date = Field..., description="结束日期"

total_return: Decimal = Field..., description="总收益率"
annualized_return: Decimal = Field..., description="年化收益率"
cagr: Decimal = Field..., description="复合年均增长率"

volatility: Decimal = Field..., description="年化波动率"
max_drawdown: Decimal = Field..., description="最大回撤"
var_95: Decimal = Field..., description="95% VaR"
var_99: Decimal = Field..., description="99% VaR"

sharpe_ratio: Decimal = Field..., description="夏普比率"
sortino_ratio: Decimal = Field..., description="索提诺比率"
calmar_ratio: Decimal = Field..., description="卡玛比率"

alpha: Decimal = Field..., description="Alpha值"
beta: Decimal = Field..., description="Beta值"
information_ratio: Decimal = Field..., description="信息比率"

win_rate: Decimal = Field..., description="胜率"
profit_factor: Decimal = Field..., description="盈亏比"
trades_count: int = Field..., description="交易次数"
avg_trade_duration: int = Field..., description="平均持仓天数"

excess_return: Decimal = Field..., description="超额收益"
tracking_error: Decimal = Field..., description="跟踪误差"

created_at: datetime = Fielddefault_factory=datetime.now, description="创建时间"
last_updated: datetime = Fielddefault_factory=datetime.now, description="最后更新时间"
validation_status: str = Field"pending", description="验证状态"

class Config:    use_enum_values = True

class BacktestMetricsBaseModel:
"""回测指标模型"""
performance: StrategyPerformance = Field..., description="策略绩效"
benchmark_performance: Optional[StrategyPerformance] = FieldNone, description="基准绩效"
risk_metrics: Dict[str, Any] = Fielddefault_factory=dict, description="风险指标"
trade_analysis: Dict[str, Any] = Fielddefault_factory=dict, description="交易分析"
portfolio_analysis: Dict[str, Any] = Fielddefault_factory=dict, description="投资组合分析"

class Config:    use_enum_values = True

class BaseBacktestEngineABC:
"""回测引擎基础类"""

def __init__self, config: BacktestEngineConfig:    self.config = config
self.logger = logging.getLoggerf"hk_quant_system.backtest.{config.engine_type}"
self._status = BacktestStatus.PENDING

@property
def statusself -> BacktestStatus:
"""获取回测状态"""
return self._status

@abstractmethod
async def initializeself -> bool:
"""
初始化回测引擎

Returns:
bool: 初始化是否成功
"""
pass

@abstractmethod
async def run_backtest(
self,
strategy: Dict[str, Any],
market_data: List[RealMarketData]
) -> BacktestMetrics:
"""
运行回测

Args:
strategy: 策略参数
market_data: 市场数据

Returns:
BacktestMetrics: 回测结果
"""
pass

@abstractmethod
async def validate_strategyself, strategy: Dict[str, Any] -> bool:
"""
验证策略

Args:
strategy: 策略参数

Returns:
bool: 策略是否有效
"""
pass

@abstractmethod
async def get_performance_summaryself, strategy_id: str -> Optional[StrategyPerformance]:
"""
获取策略绩效摘要

Args:
strategy_id: 策略ID

Returns:
StrategyPerformance: 策略绩效
"""
pass

@abstractmethod
async def cleanupself -> None:
"""清理资源"""
pass

def set_statusself, status: BacktestStatus -> None:
"""设置状态"""
self._status = status
self.logger.infof"Backtest status changed to: {status}"

async def health_checkself -> Dict[str, Any]:
"""健康检查"""
return {
"status": self._status,
"engine_type": self.config.engine_type,
"config": self.config.dict(),
"timestamp": datetime.now()
}
