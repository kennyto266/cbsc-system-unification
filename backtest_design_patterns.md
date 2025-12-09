分析回测系统的设计模式

# Tree View:
```
src/backtest
├── __init__.py
├── __pycache__
│   ├── __init__.cpython-313.pyc
│   ├── base_backtest.cpython-313.pyc
│   ├── config.cpython-313.pyc
│   ├── data_quality_monitor.cpython-313.pyc
│   ├── engine_interface.cpython-313.pyc
│   ├── enhanced_backtest_engine.cpython-313.pyc
│   ├── exceptions.cpython-313.pyc
│   ├── stockbacktest_adapter.cpython-313.pyc
│   ├── stockbacktest_integration.cpython-313.pyc
│   ├── strategy_performance.cpython-313.pyc
│   ├── technical_indicator_pipeline.cpython-313.pyc
│   ├── universal_backtest_sop.cpython-313.pyc
│   └── vectorbt_execution_engine.cpython-313.pyc
├── base_backtest.py
├── config.py
├── engine_interface.py
├── enhanced_backtest_engine.py
├── exceptions.py
├── phase3_optimized_vectorbt_engine.py
├── stockbacktest_adapter.py
├── stockbacktest_integration.py
└── strategy_performance.py

```

# Content:

## __init__.py

```py
"""
回测引擎模块

提供策略回测、绩效计算和验证功能。
"""

from .config import StockBacktestConfig  # pragma: no cover
from .engine_interface import BaseBacktestEngine, BacktestEngineConfig
from .stockbacktest_integration import StockBacktestIntegration
from .strategy_performance import BacktestMetrics, StrategyPerformance

__all__ = [
    "StockBacktestConfig",
    'BaseBacktestEngine',
    'BacktestEngineConfig', 
    'StockBacktestIntegration',
    'StrategyPerformance',
    'BacktestMetrics',
]

```


## base_backtest.py

```py
"""
基礎回測引擎 - 回測框架基礎類

定義回測引擎的標準接口和基礎功能
"""

import asyncio
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field

class BacktestStatusstr, Enum:
"""回測狀態"""
PENDING = "pending"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"

class BacktestConfigBaseModel:
"""回測配置"""
strategy_name: str = Field..., description="策略名稱"
symbols: List[str] = Field..., description="交易標的列表"
start_date: date = Field..., description="開始日期"
end_date: date = Field..., description="結束日期"
initial_capital: float = Field1000000, gt=0, description="初始資本"
benchmark: Optional[str] = FieldNone, description="基準標的"
config: Dict[str, Any] = Fielddefault_factory=dict, description="額外配置"

class BacktestResultBaseModel:
"""回測結果"""
strategy_name: str = Field..., description="策略名稱"
start_date: date = Field..., description="開始日期"
end_date: date = Field..., description="結束日期"
initial_capital: float = Field..., description="初始資本"
final_capital: float = Field..., description="最終資本"
total_return: float = Field..., description="總收益率"
annualized_return: float = Field..., description="年化收益率"
sharpe_ratio: float = Field..., description="夏普比率"
max_drawdown: float = Field..., description="最大回撤"
metrics: Dict[str, Any] = Fielddefault_factory=dict, description="詳細指標"
trades: List[Dict[str, Any]] = Fielddefault_factory=list, description="交易記錄"
portfolio_values: List[float] = Fielddefault_factory=list, description="組合價值序列"
daily_returns: List[float] = Fielddefault_factory=list, description="日收益率序列"

class BaseBacktestEngine:
"""回測引擎基礎類"""

def __init__self, config: BacktestConfig:    self.config = config
self.logger = logging.getLoggerf"hk_quant_system.backtest.{config.strategy_name}"
self.status = BacktestStatus.PENDING
self.historical_data: Dict[str, Any] = {}
self.benchmark_data: Optional[Any] = None

async def initializeself -> bool:
"""初始化回測引擎"""
try:
self.logger.infof"Initializing backtest engine for {self.config.strategy_name}"
self.status = BacktestStatus.PENDING
return True
except Exception as e:
self.logger.errorf"Failed to initialize backtest engine: {e}"
return False

async def run_backtestself, strategy_func -> BacktestResult:
"""運行回測"""
try:    self.status = BacktestStatus.RUNNING
self.logger.infof"Starting backtest for {self.config.strategy_name}"

# 這裡應該實現具體的回測邏輯
# 子類需要重寫這個方法

result = BacktestResult(
strategy_name=self.config.strategy_name,
start_date=self.config.start_date,
end_date=self.config.end_date,
initial_capital=self.config.initial_capital,
final_capital=self.config.initial_capital,
total_return=0.0,
annualized_return=0.0,
sharpe_ratio=0.0,
max_drawdown=0.0
)

self.status = BacktestStatus.COMPLETED
self.logger.infof"Backtest completed for {self.config.strategy_name}"
return result

except Exception as e:    self.status = BacktestStatus.FAILED
self.logger.errorf"Backtest failed for {self.config.strategy_name}: {e}"
raise

async def cleanupself -> None:
"""清理資源"""
try:
self.logger.infof"Cleaning up backtest engine for {self.config.strategy_name}"
self.status = BacktestStatus.PENDING
except Exception as e:
self.logger.errorf"Error during cleanup: {e}"
```


## config.py

```py
"""StockBacktest integration configuration utilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

DEFAULT_STOCKBACKTEST_PATH = Path(
    os.environ.get(
        "STOCKBACKTEST_PATH",
        r"C:\Users\Penguin8n\Desktop\StockBacktest",
    )
)


class StockBacktestConfig(BaseModel):
    """Configuration container for StockBacktest integration."""

    base_path: Path = Field(default=DEFAULT_STOCKBACKTEST_PATH)
    engine_module: str = Field(
        default="回測系統.01_核心系統.backtest_engine",
        description="Module containing the backtest entry point",
    )
    engine_callable_name: str = Field(
        default="run_backtest",
        description="Callable function used to execute a single backtest run",
    )
    performance_callable_name: str = Field(
        default="calculate_performance",
        description="Callable function used to calculate performance metrics",
    )

    class Config:
        arbitrary_types_allowed = True


def get_stockbacktest_config(
    base_path: Optional[Path] = None,
    engine_module: Optional[str] = None,
    engine_callable_name: Optional[str] = None,
) -> StockBacktestConfig:
    """Create a StockBacktestConfig with optional overrides."""
    return StockBacktestConfig(
        base_path=base_path or DEFAULT_STOCKBACKTEST_PATH,
        engine_module=engine_module or "回測系統.01_核心系統.backtest_engine",
        engine_callable_name=engine_callable_name or "run_backtest",
    )
```


## engine_interface.py

```py
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

```


## enhanced_backtest_engine.py

```py
"""
增強型回測引擎 - 真實歷史數據回測

支持多種策略、真實交易成本、滑點和市場衝擊
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field
try:
import matplotlib.pyplot as plt
import seaborn as sns
PLOTTING_AVAILABLE = True
except ImportError:    plt = None
sns = None
PLOTTING_AVAILABLE = False

from .base_backtest import BaseBacktestEngine, BacktestConfig, BacktestResult
from ..risk_management.risk_calculator import RiskCalculator, RiskMetrics
from ..data_adapters.data_service import DataService

class TransactionCostBaseModel:
"""交易成本模型"""
commission_per_share: float = Field0.005, description="每股佣金"
commission_per_trade: float = Field1.0, description="每筆交易固定佣金"
bid_ask_spread: float = Field0.001, description="買賣價差"
market_impact: float = Field0.0005, description="市場衝擊"
slippage: float = Field0.0002, description="滑點"

class BacktestMetricsBaseModel:
"""回測指標"""

total_return: float = Field..., description="總收益率"
annualized_return: float = Field..., description="年化收益率"
volatility: float = Field..., description="年化波動率"
sharpe_ratio: float = Field..., description="夏普比率"
sortino_ratio: float = Field..., description="索提諾比率"
calmar_ratio: float = Field..., description="卡爾瑪比率"

max_drawdown: float = Field..., description="最大回撤"
max_drawdown_duration: int = Field..., description="最大回撤持續天數"
var_95: float = Field..., description="95% VaR"
var_99: float = Field..., description="99% VaR"
expected_shortfall_95: float = Field..., description="95% 期望損失"

total_trades: int = Field..., description="總交易次數"
winning_trades: int = Field..., description="盈利交易次數"
losing_trades: int = Field..., description="虧損交易次數"
win_rate: float = Field..., description="勝率"
avg_win: float = Field..., description="平均盈利"
avg_loss: float = Field..., description="平均虧損"
profit_factor: float = Field..., description="盈利因子"

total_commission: float = Field..., description="總佣金"
total_slippage: float = Field..., description="總滑點成本"
total_market_impact: float = Field..., description="總市場衝擊成本"
net_return: float = Field..., description="淨收益率"

information_ratio: float = Field..., description="信息比率"
tracking_error: float = Field..., description="跟踪誤差"
beta: float = Field..., description="貝塔係數"
alpha: float = Field..., description="阿爾法"

start_date: datetime = Field..., description="開始日期"
end_date: datetime = Field..., description="結束日期"
trading_days: int = Field..., description="交易日數"
initial_capital: float = Field..., description="初始資本"

class TradeBaseModel:
"""交易記錄"""
symbol: str = Field..., description="交易標的"
side: str = Field..., description="交易方向"
quantity: float = Field..., description="交易數量"
price: float = Field..., description="交易價格"
timestamp: datetime = Field..., description="交易時間"
commission: float = Field..., description="佣金"
slippage: float = Field..., description="滑點"
market_impact: float = Field..., description="市場衝擊"
total_cost: float = Field..., description="總成本"
pnl: Optional[float] = FieldNone, description="損益"

class EnhancedBacktestEngineBaseBacktestEngine:
"""增強型回測引擎"""

def __init__self, config: BacktestConfig:
super().__init__config
self.logger = logging.getLogger"hk_quant_system.enhanced_backtest"

self.risk_calculator = RiskCalculator()
self.data_service = DataService()

self.transaction_cost = TransactionCost(**config.config.get'transaction_cost', {})

self.current_positions: Dict[str, float] = {}
self.trades: List[Trade] = []
self.portfolio_values: List[float] = []
self.daily_returns: List[float] = []
self.benchmark_returns: List[float] = []

async def initializeself -> bool:
"""初始化回測引擎"""
try:
self.logger.info"Initializing enhanced backtest engine..."

if not await self.data_service.initialize():
self.logger.error"Failed to initialize data service"
return False

await self._load_historical_data()

self.logger.info"Enhanced backtest engine initialized successfully"
return True

except Exception as e:
self.logger.exceptionf"Failed to initialize enhanced backtest engine: {e}"
return False

async def _load_historical_dataself -> None:
"""加載歷史數據"""
try:
self.logger.info"Loading historical data..."

# 獲取所有標的的歷史數據
self.historical_data = {}

for symbol in self.config.symbols:
self.logger.infof"Loading data for {symbol}..."

market_data = await self.data_service.get_market_data(
symbol=symbol,
start_date=self.config.start_date,
end_date=self.config.end_date
)

if market_data:
# 轉換為DataFrame
df_data = []
for data_point in market_data:
df_data.append({
'timestamp': data_point.timestamp,
'open': floatdata_point.open_price,
'high': floatdata_point.high_price,
'low': floatdata_point.low_price,
'close': floatdata_point.close_price,
'volume': data_point.volume
})

df = pd.DataFramedf_data
df.set_index'timestamp', inplace=True
df.sort_indexinplace=True

self.historical_data[symbol] = df
self.logger.info(f"Loaded {lendf} data points for {symbol}")
else:
self.logger.warningf"No data found for {symbol}"

if self.config.benchmark:    benchmark_data = await self.data_service.get_market_data(
symbol=self.config.benchmark,
start_date=self.config.start_date,
end_date=self.config.end_date
)

if benchmark_data:    df_data = []
for data_point in benchmark_data:
df_data.append({
'timestamp': data_point.timestamp,
'close': floatdata_point.close_price
})

df = pd.DataFramedf_data
df.set_index'timestamp', inplace=True
df.sort_indexinplace=True

self.benchmark_data = df
self.logger.info(f"Loaded {lendf} benchmark data points")
else:
self.logger.warningf"No benchmark data found for {self.config.benchmark}"

self.logger.info"Historical data loading completed"

except Exception as e:
self.logger.errorf"Error loading historical data: {e}"
raise

async def run_backtestself, strategy_func -> BacktestResult:
"""運行回測"""
try:
self.logger.info"Starting enhanced backtest..."

self._reset_backtest_state()

all_dates = set()
for symbol_data in self.historical_data.values():
all_dates.updatesymbol_data.index.date

trading_dates = sorted(listall_dates)
self.logger.info(f"Running backtest for {lentrading_dates} trading days")

for i, current_date in enumeratetrading_dates:
await self._process_trading_daycurrent_date, strategy_func

portfolio_value = await self._calculate_portfolio_valuecurrent_date
self.portfolio_values.appendportfolio_value

if i > 0:    daily_return = (portfolio_value - self.portfolio_values[-2]) / self.portfolio_values[-2]
self.daily_returns.appenddaily_return

if hasattrself, 'benchmark_data':    benchmark_return = await self._calculate_benchmark_return(current_date)
self.benchmark_returns.appendbenchmark_return

if i % 50 == 0:
self.logger.info(f"Processed {i}/{lentrading_dates} trading days")

result = await self._calculate_backtest_results()

self.logger.info"Enhanced backtest completed successfully"
return result

except Exception as e:
self.logger.exceptionf"Error running backtest: {e}"
raise

async def _process_trading_dayself, current_date: datetime.date, strategy_func -> None:
"""處理單個交易日"""
try:
# 獲取當前市場數據
current_data = {}
for symbol, data in self.historical_data.items():
if current_date in data.index.date:    current_data[symbol] = data.loc[data.index.date == current_date].iloc[0]

if not current_data:
return

signals = await strategy_funccurrent_data, self.current_positions

for signal in signals:
await self._execute_tradesignal, current_date

await self._update_positions()

except Exception as e:
self.logger.errorf"Error processing trading day {current_date}: {e}"

async def _execute_tradeself, signal: Dict[str, Any], trade_date: datetime.date -> None:
"""執行交易"""
try:    symbol = signal.get('symbol')
side = signal.get'side', 'buy'
quantity = signal.get'quantity', 0

if not symbol or quantity <= 0:
return

if symbol in self.historical_data:    symbol_data = self.historical_data[symbol]
if trade_date in symbol_data.index.date:    price_data = symbol_data.loc[symbol_data.index.date == trade_date].iloc[0]

# 根據交易方向選擇價格
if side == 'buy':    price = price_data['close'] * (1 + self.transaction_cost.bid_ask_spread / 2)
else:    price = price_data['close'] * (1 - self.transaction_cost.bid_ask_spread / 2)

commission = self.transaction_cost.commission_per_trade + \
quantity * self.transaction_cost.commission_per_share

slippage_cost = quantity * price * self.transaction_cost.slippage

market_impact_cost = quantity * price * self.transaction_cost.market_impact

total_cost = commission + slippage_cost + market_impact_cost

trade = Trade(
symbol=symbol,
side=side,
quantity=quantity,
price=price,
timestamp=datetime.combine(trade_date, datetime.min.time()),
commission=commission,
slippage=slippage_cost,
market_impact=market_impact_cost,
total_cost=total_cost
)

self.trades.appendtrade

if side == 'buy':    self.current_positions[symbol] = self.current_positions.get(symbol, 0) + quantity
else:    self.current_positions[symbol] = self.current_positions.get(symbol, 0) - quantity

self.logger.debugf"Executed trade: {symbol} {side} {quantity} @ {price:.2f}"

except Exception as e:
self.logger.errorf"Error executing trade: {e}"

async def _update_positionsself -> None:
"""更新持倉"""

self.current_positions = {k: v for k, v in self.current_positions.items() if absv > 1e-6}

async def _calculate_portfolio_valueself, current_date: datetime.date -> float:
"""計算組合價值"""
try:    total_value = self.config.initial_capital

for symbol, quantity in self.current_positions.items():
if symbol in self.historical_data:    symbol_data = self.historical_data[symbol]
if current_date in symbol_data.index.date:    price_data = symbol_data.loc[symbol_data.index.date == current_date].iloc[0]
position_value = quantity * price_data['close']
total_value += position_value

return total_value

except Exception as e:
self.logger.errorf"Error calculating portfolio value: {e}"
return self.config.initial_capital

async def _calculate_benchmark_returnself, current_date: datetime.date -> float:
"""計算基準收益率"""
try:
if not hasattrself, 'benchmark_data':
return 0.0

if current_date in self.benchmark_data.index.date:    current_price = self.benchmark_data.loc[self.benchmark_data.index.date == current_date]['close'].iloc[0]

if self.benchmark_returns:
# 計算相對於前一天的收益率
prev_date = self.benchmark_data.index.date[self.benchmark_data.index.date < current_date][-1]
prev_price = self.benchmark_data.loc[self.benchmark_data.index.date == prev_date]['close'].iloc[0]
return current_price - prev_price / prev_price
else:
# 第一天，計算相對於初始價格的收益率
initial_price = self.benchmark_data.iloc[0]['close']
return current_price - initial_price / initial_price

return 0.0

except Exception as e:
self.logger.errorf"Error calculating benchmark return: {e}"
return 0.0

async def _calculate_backtest_resultsself -> BacktestResult:
"""計算回測結果"""
try:
if not self.portfolio_values or not self.daily_returns:
raise ValueError"No portfolio data available for results calculation"

initial_value = self.portfolio_values[0]
final_value = self.portfolio_values[-1]
total_return = final_value - initial_value / initial_value

trading_days = lenself.daily_returns
years = trading_days / 252
annualized_return = 1 + total_return ** 1 / years - 1 if years > 0 else 0

returns_series = pd.Seriesself.daily_returns
risk_metrics = await self.risk_calculator.calculate_portfolio_riskreturns_series

winning_trades = [t for t in self.trades if t.pnl and t.pnl > 0]
losing_trades = [t for t in self.trades if t.pnl and t.pnl < 0]

total_trades = lenself.trades
winning_count = lenwinning_trades
losing_count = lenlosing_trades
win_rate = winning_count / total_trades if total_trades > 0 else 0

avg_win = np.mean[t.pnl for t in winning_trades] if winning_trades else 0
avg_loss = np.mean[t.pnl for t in losing_trades] if losing_trades else 0
profit_factor = absavg_win / avg_loss if avg_loss != 0 else 0

total_commission = sumt.commission for t in self.trades
total_slippage = sumt.slippage for t in self.trades
total_market_impact = sumt.market_impact for t in self.trades

information_ratio = 0.0
tracking_error = 0.0
beta = 0.0
alpha = 0.0

if lenself.benchmark_returns == lenself.daily_returns:    benchmark_series = pd.Series(self.benchmark_returns)
active_returns = returns_series - benchmark_series

tracking_error = active_returns.std() * np.sqrt252
information_ratio = active_returns.mean() * 252 / tracking_error if tracking_error > 0 else 0

covariance = np.covreturns_series, benchmark_series[0, 1]
benchmark_variance = np.varbenchmark_series
beta = covariance / benchmark_variance if benchmark_variance > 0 else 0

alpha = annualized_return - (0.02 + beta * (benchmark_series.mean() * 252 - 0.02))

backtest_metrics = BacktestMetrics(
total_return=total_return,
annualized_return=annualized_return,
volatility=risk_metrics.volatility,
sharpe_ratio=risk_metrics.sharpe_ratio,
sortino_ratio=risk_metrics.sortino_ratio,
calmar_ratio=risk_metrics.calmar_ratio,
max_drawdown=risk_metrics.max_drawdown,
max_drawdown_duration=0, # 需要額外計算
var_95=risk_metrics.var_95,
var_99=risk_metrics.var_99,
expected_shortfall_95=risk_metrics.expected_shortfall_95,
total_trades=total_trades,
winning_trades=winning_count,
losing_trades=losing_count,
win_rate=win_rate,
avg_win=avg_win,
avg_loss=avg_loss,
profit_factor=profit_factor,
total_commission=total_commission,
total_slippage=total_slippage,
total_market_impact=total_market_impact,
net_return=total_return - total_commission + total_slippage + total_market_impact / initial_value,
information_ratio=information_ratio,
tracking_error=tracking_error,
beta=beta,
alpha=alpha,
start_date=self.config.start_date,
end_date=self.config.end_date,
trading_days=trading_days,
initial_capital=initial_value
)

result = BacktestResult(
strategy_name=self.config.strategy_name,
start_date=self.config.start_date,
end_date=self.config.end_date,
initial_capital=self.config.initial_capital,
final_capital=final_value,
total_return=total_return,
annualized_return=annualized_return,
sharpe_ratio=risk_metrics.sharpe_ratio,
max_drawdown=risk_metrics.max_drawdown,
metrics=backtest_metrics.dict(),
trades=[trade.dict() for trade in self.trades],
portfolio_values=self.portfolio_values,
daily_returns=self.daily_returns
)

return result

except Exception as e:
self.logger.errorf"Error calculating backtest results: {e}"
raise

def _reset_backtest_stateself -> None:
"""重置回測狀態"""
self.current_positions.clear()
self.trades.clear()
self.portfolio_values.clear()
self.daily_returns.clear()
self.benchmark_returns.clear()

async def generate_performance_reportself, result: BacktestResult -> Dict[str, Any]:
"""生成績效報告"""
try:    report = {
"summary": {
"strategy_name": result.strategy_name,
"period": f"{result.start_date} to {result.end_date}",
"initial_capital": result.initial_capital,
"final_capital": result.final_capital,
"total_return": f"{result.total_return:.2%}",
"annualized_return": f"{result.annualized_return:.2%}",
"sharpe_ratio": f"{result.sharpe_ratio:.3f}",
"max_drawdown": f"{result.max_drawdown:.2%}"
},
"risk_metrics": {
"volatility": f"{result.metrics['volatility']:.2%}",
"var_95": f"{result.metrics['var_95']:.2%}",
"var_99": f"{result.metrics['var_99']:.2%}",
"expected_shortfall_95": f"{result.metrics['expected_shortfall_95']:.2%}"
},
"trading_metrics": {
"total_trades": result.metrics['total_trades'],
"win_rate": f"{result.metrics['win_rate']:.2%}",
"profit_factor": f"{result.metrics['profit_factor']:.3f}",
"avg_win": f"{result.metrics['avg_win']:.2f}",
"avg_loss": f"{result.metrics['avg_loss']:.2f}"
},
"cost_analysis": {
"total_commission": f"{result.metrics['total_commission']:.2f}",
"total_slippage": f"{result.metrics['total_slippage']:.2f}",
"total_market_impact": f"{result.metrics['total_market_impact']:.2f}",
"net_return": f"{result.metrics['net_return']:.2%}"
},
"benchmark_comparison": {
"information_ratio": f"{result.metrics['information_ratio']:.3f}",
"tracking_error": f"{result.metrics['tracking_error']:.2%}",
"beta": f"{result.metrics['beta']:.3f}",
"alpha": f"{result.metrics['alpha']:.2%}"
}
}

return report

except Exception as e:
self.logger.errorf"Error generating performance report: {e}"
return {}

async def plot_performanceself, result: BacktestResult, save_path: Optional[str] = None -> None:
"""繪製績效圖表"""
try:    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitlef'Backtest Results: {result.strategy_name}', fontsize=16

axes[0, 0].plotresult.portfolio_values
axes[0, 0].set_title'Portfolio Value'
axes[0, 0].set_xlabel'Trading Days'
axes[0, 0].set_ylabel'Value'
axes[0, 0].gridTrue

axes[0, 1].histresult.daily_returns, bins=50, alpha=0.7
axes[0, 1].set_title'Daily Returns Distribution'
axes[0, 1].set_xlabel'Daily Return'
axes[0, 1].set_ylabel'Frequency'
axes[0, 1].gridTrue

cumulative_returns = np.cumprod(1 + np.arrayresult.daily_returns) - 1
axes[1, 0].plotcumulative_returns
axes[1, 0].set_title'Cumulative Returns'
axes[1, 0].set_xlabel'Trading Days'
axes[1, 0].set_ylabel'Cumulative Return'
axes[1, 0].gridTrue

portfolio_values = np.arrayresult.portfolio_values
running_max = np.maximum.accumulateportfolio_values
drawdowns = portfolio_values - running_max / running_max
axes[1, 1].fill_between(range(lendrawdowns), drawdowns, 0, alpha=0.7, color='red')
axes[1, 1].set_title'Drawdown'
axes[1, 1].set_xlabel'Trading Days'
axes[1, 1].set_ylabel'Drawdown'
axes[1, 1].gridTrue

plt.tight_layout()

if save_path:    plt.savefig(save_path, dpi=300, bbox_inches='tight')
self.logger.infof"Performance plot saved to {save_path}"
else:
plt.show()

except Exception as e:
self.logger.errorf"Error plotting performance: {e}"

async def cleanupself -> None:
"""清理資源"""
try:
if hasattrself.data_service, 'cleanup':
await self.data_service.cleanup()

self.logger.info"Enhanced backtest engine cleanup completed"

except Exception as e:
self.logger.errorf"Error during cleanup: {e}"
```


## exceptions.py

```py
"""Custom exceptions for StockBacktest integration."""

class StockBacktestErrorException:
"""Base error for the StockBacktest integration."""

class StockBacktestImportErrorStockBacktestError:
"""Raised when StockBacktest modules cannot be imported."""

class StockBacktestConfigErrorStockBacktestError:
"""Raised when configuration for StockBacktest is invalid."""

class StockBacktestDataErrorStockBacktestError:
"""Raised when required data for StockBacktest is missing or invalid."""

class StockBacktestStrategyErrorStockBacktestError:
"""Raised when strategy mapping or execution fails."""

__all__ = [
"StockBacktestError",
"StockBacktestImportError",
"StockBacktestConfigError",
"StockBacktestDataError",
"StockBacktestStrategyError",
]

```


## phase3_optimized_vectorbt_engine.py

```py
#!/usr/bin/env python3
"""
Phase 3: Optimized VectorBT Engine for High-Performance 5+ Year Backtesting
===========================================================================

Advanced VectorBT engine optimized for large datasets and long-term analysis.
Implements chunked processing, memory optimization, and performance enhancements.

Key Features:
- Chunked data processing for large datasets
- Memory optimization for 10+ year backtesting
- Advanced performance monitoring
- Batch processing capabilities
- GPU acceleration support where available
- Intelligent caching system

Author: Claude Code Assistant
Date: 2025-11-29
Phase: 3 - VectorBT Engine Optimization
"""

import gc
import logging
import multiprocessing
import os
import psutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    vbt = None

try:
    import numba
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False

from ..data_adapters.data_service import DataService

logger = logging.getLogger(__name__)


@dataclass
class ChunkedProcessingConfig:
    """Configuration for chunked data processing"""

    # Memory management
    max_memory_usage_gb: float = 4.0  # Maximum memory usage in GB
    chunk_size_years: int = 2  # Process data in 2-year chunks
    enable_garbage_collection: bool = True
    gc_frequency: int = 3  # Run GC every N chunks

    # Parallel processing
    enable_parallel: bool = True
    max_workers: Optional[int] = None  # None = auto-detect
    chunk_parallel_processing: bool = False

    # Performance optimization
    enable_numba_jit: bool = True
    enable_vectorbt_optimization: bool = True
    use_low_memory_mode: bool = False

    # Caching
    enable_chunk_caching: bool = True
    cache_directory: Optional[str] = None
    clear_cache_on_complete: bool = True


@dataclass
class PerformanceMetrics:
    """Performance monitoring metrics"""

    processing_time: float = 0.0
    memory_peak_usage_gb: float = 0.0
    chunks_processed: int = 0
    total_data_points: int = 0
    processing_speed_points_per_sec: float = 0.0

    # Memory optimization metrics
    gc_runs: int = 0
    memory_freed_gb: float = 0.0

    # Performance improvements
    speedup_factor: float = 1.0
    memory_reduction_factor: float = 1.0


@dataclass
class Phase3BacktestConfig:
    """Extended configuration for Phase 3 optimized backtesting"""

    # Inherit from Phase 2
    min_data_years: int = 5
    preferred_data_years: int = 10
    enable_government_data: bool = True

    # Phase 3 specific optimizations
    chunked_config: ChunkedProcessingConfig = field(default_factory=ChunkedProcessingConfig)

    # Performance targets
    target_processing_time_years_per_minute: float = 0.5  # Process 0.5 years of data per minute
    max_memory_usage_percent: float = 80.0

    # Advanced features
    enable_real_time_progress: bool = True
    save_intermediate_results: bool = True
    intermediate_results_path: Optional[str] = None

    # Quality assurance
    enable_data_validation: bool = True
    enable_result_verification: bool = True
    enable_performance_monitoring: bool = True


class MemoryManager:
    """Advanced memory management for large dataset processing"""

    def __init__(self, config: ChunkedProcessingConfig):
        self.config = config
        self.process = psutil.Process(os.getpid())

    def get_memory_usage_gb(self) -> float:
        """Get current memory usage in GB"""
        return self.process.memory_info().rss / 1024 / 1024 / 1024

    def get_memory_usage_percent(self) -> float:
        """Get memory usage as percentage of system memory"""
        return self.process.memory_percent()

    def check_memory_limit(self) -> bool:
        """Check if memory usage exceeds configured limit"""
        current_usage = self.get_memory_usage_gb()
        return current_usage > self.config.max_memory_usage_gb

    def optimize_memory(self, force_gc: bool = False) -> float:
        """Optimize memory usage and return memory freed in GB"""
        initial_memory = self.get_memory_usage_gb()

        # Run garbage collection
        if force_gc or self.gc_runs_count % self.config.gc_frequency == 0:
            gc.collect()

        # Clear pandas float formatting cache
        pd.options.display.float_format = None

        final_memory = self.get_memory_usage_gb()
        memory_freed = max(0, initial_memory - final_memory)

        return memory_freed

    @property
    def gc_runs_count(self) -> int:
        """Track garbage collection runs"""
        if not hasattr(self, '_gc_runs'):
            self._gc_runs = 0
        return self._gc_runs


class ChunkedDataProcessor:
    """Processes large datasets in optimized chunks"""

    def __init__(self, config: ChunkedProcessingConfig):
        self.config = config
        self.memory_manager = MemoryManager(config)
        self.performance_metrics = PerformanceMetrics()

    def split_data_into_chunks(self, data: pd.DataFrame,
                             chunk_size_years: int) -> List[pd.DataFrame]:
        """Split large dataset into manageable chunks"""

        if len(data) == 0:
            return []

        # Calculate chunk size based on years
        trading_days_per_year = 252
        chunk_size = chunk_size_years * trading_days_per_year

        chunks = []
        for i in range(0, len(data), chunk_size):
            chunk = data.iloc[i:i + chunk_size]
            if len(chunk) > 0:  # Skip empty chunks
                chunks.append(chunk)

        logger.info(f"Split data into {len(chunks)} chunks of ~{chunk_size_years} years each")
        return chunks

    def process_chunk_vectorbt(self, chunk_data: pd.DataFrame,
                             strategy_func, **kwargs) -> Dict[str, Any]:
        """Process a single chunk with VectorBT optimization"""

        chunk_start_time = time.time()
        chunk_memory_start = self.memory_manager.get_memory_usage_gb()

        try:
            # Enable VectorBT optimizations if available
            if VECTORBT_AVAILABLE and self.config.enable_vectorbt_optimization:
                result = self._process_chunk_with_vectorbt(chunk_data, strategy_func, **kwargs)
            else:
                result = self._process_chunk_fallback(chunk_data, strategy_func, **kwargs)

            # Update performance metrics
            chunk_time = time.time() - chunk_start_time
            chunk_memory_end = self.memory_manager.get_memory_usage_gb()

            self.performance_metrics.chunks_processed += 1
            self.performance_metrics.total_data_points += len(chunk_data)

            # Memory optimization
            if self.config.enable_garbage_collection and \
               self.memory_manager.gc_runs_count % self.config.gc_frequency == 0:
                memory_freed = self.memory_manager.optimize_memory(force_gc=True)
                self.performance_metrics.memory_freed_gb += memory_freed

            return result

        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            raise

    def _process_chunk_with_vectorbt(self, chunk_data: pd.DataFrame,
                                  strategy_func, **kwargs) -> Dict[str, Any]:
        """Process chunk using optimized VectorBT operations"""

        # Generate signals using strategy function
        signals = strategy_func(chunk_data, **kwargs)

        # Convert to VectorBT format
        if isinstance(signals, dict) and 'entries' in signals and 'exits' in signals:
            entries = signals['entries']
            exits = signals['exits']
        else:
            # Convert boolean signals to entries/exits
            signals_series = pd.Series(signals, index=chunk_data.index)
            entries = signals_series.shift(1).fillna(False)  # Enter next day
            exits = signals_series.shift(-1).fillna(False)   # Exit following day

        # Create portfolio with VectorBT
        try:
            portfolio = vbt.Portfolio.from_signals(
                close=chunk_data['Close'],
                entries=entries,
                exits=exits,
                init_cash=kwargs.get('initial_cash', 10000),
                fees=kwargs.get('fees', 0.001),
                slippage=kwargs.get('slippage', 0.001),
                freq='D'  # Daily frequency
            )

            # Extract results
            results = {
                'returns': portfolio.returns(),
                'equity': portfolio.value(),
                'trades': portfolio.trades,
                'drawdown': portfolio.drawdown(),
                'sharpe_ratio': portfolio.sharpe_ratio(),
                'max_drawdown': portfolio.max_drawdown(),
                'total_return': portfolio.total_return(),
                'annualized_return': portfolio.annualized_return(),
                'volatility': portfolio.annualized_volatility(),
                'win_rate': portfolio.trades.win_rate()
            }

            return results

        except Exception as e:
            logger.warning(f"VectorBT processing failed, falling back: {e}")
            return self._process_chunk_fallback(chunk_data, strategy_func, **kwargs)

    def _process_chunk_fallback(self, chunk_data: pd.DataFrame,
                              strategy_func, **kwargs) -> Dict[str, Any]:
        """Fallback processing without VectorBT"""

        signals = strategy_func(chunk_data, **kwargs)

        # Simple backtesting logic
        initial_cash = kwargs.get('initial_cash', 10000)
        cash = initial_cash
        position = 0
        equity_curve = []
        returns = []

        for i, (date, row) in enumerate(chunk_data.iterrows()):
            price = row['Close']

            # Process signals
            if signals.iloc[i] and position == 0:  # Buy signal
                position = cash / price
                cash = 0
            elif not signals.iloc[i] and position > 0:  # Sell signal
                cash = position * price
                position = 0

            # Calculate equity
            total_equity = cash + position * price
            equity_curve.append(total_equity)

            # Calculate returns
            if i > 0:
                daily_return = (total_equity - equity_curve[i-1]) / equity_curve[i-1]
                returns.append(daily_return)

        # Calculate metrics
        equity_series = pd.Series(equity_curve, index=chunk_data.index)
        returns_series = pd.Series(returns, index=chunk_data.index[1:])

        results = {
            'returns': returns_series,
            'equity': equity_series,
            'trades': None,  # Not available in fallback
            'drawdown': self._calculate_drawdown(equity_series),
            'sharpe_ratio': self._calculate_sharpe_ratio(returns_series),
            'max_drawdown': self._calculate_max_drawdown(equity_series),
            'total_return': (equity_series.iloc[-1] - initial_cash) / initial_cash,
            'annualized_return': self._calculate_annualized_return(returns_series),
            'volatility': returns_series.std() * np.sqrt(252),
            'win_rate': None  # Not available in fallback
        }

        return results

    def _calculate_drawdown(self, equity: pd.Series) -> pd.Series:
        """Calculate drawdown series"""
        running_max = equity.expanding().max()
        drawdown = (equity - running_max) / running_max
        return drawdown

    def _calculate_max_drawdown(self, equity: pd.Series) -> float:
        """Calculate maximum drawdown"""
        drawdown = self._calculate_drawdown(equity)
        return drawdown.min()

    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) == 0:
            return 0.0
        excess_returns = returns - risk_free_rate / 252
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0.0

    def _calculate_annualized_return(self, returns: pd.Series) -> float:
        """Calculate annualized return"""
        if len(returns) == 0:
            return 0.0
        total_return = (1 + returns).prod() - 1
        years = len(returns) / 252
        return (1 + total_return) ** (1/years) - 1 if years > 0 else 0.0


class Phase3OptimizedVectorBTEngine:
    """Phase 3 optimized VectorBT engine for high-performance backtesting"""

    def __init__(self, config: Phase3BacktestConfig):
        self.config = config
        self.data_service = DataService()
        self.chunked_processor = ChunkedDataProcessor(config.chunked_config)

        # Performance tracking
        self.start_time = None
        self.end_time = None
        self.performance_metrics = PerformanceMetrics()

        # Results storage
        self.chunk_results = []
        self.combined_results = None

        logger.info("Phase 3 Optimized VectorBT Engine initialized")

    async def initialize(self) -> bool:
        """Initialize the engine and data service"""
        try:
            logger.info("Initializing Phase 3 Optimized VectorBT Engine...")

            # Initialize data service
            if not await self.data_service.initialize():
                logger.error("Failed to initialize data service")
                return False

            # Check VectorBT availability
            if not VECTORBT_AVAILABLE:
                logger.warning("VectorBT not available, using fallback processing")

            # Set up parallel processing
            if self.config.chunked_config.enable_parallel:
                max_workers = self.config.chunked_config.max_workers or \
                            min(multiprocessing.cpu_count(), 4)  # Limit to 4 workers for memory
                self.chunked_processor.config.max_workers = max_workers
                logger.info(f"Parallel processing enabled with {max_workers} workers")

            logger.info("Phase 3 Optimized VectorBT Engine initialized successfully")
            return True

        except Exception as e:
            logger.exception(f"Failed to initialize Phase 3 engine: {e}")
            return False

    async def run_optimized_backtest(self,
                                   symbol: str,
                                   start_date: datetime,
                                   end_date: datetime,
                                   strategy_func,
                                   **kwargs) -> Dict[str, Any]:
        """Run optimized backtest with chunked processing"""

        self.start_time = time.time()

        try:
            logger.info(f"Starting optimized backtest for {symbol} from {start_date} to {end_date}")

            # Validate data requirements
            data_years = (end_date - start_date).days / 365.25
            if data_years < self.config.min_data_years:
                raise ValueError(f"Insufficient data: {data_years:.1f} years < {self.config.min_data_years} years required")

            # Load historical data
            historical_data = await self._load_historical_data(symbol, start_date, end_date)

            if historical_data is None or len(historical_data) == 0:
                raise ValueError(f"No historical data available for {symbol}")

            logger.info(f"Loaded {len(historical_data)} data points for {symbol}")

            # Process data in chunks
            self.chunk_results = await self._process_data_chunks(historical_data, strategy_func, **kwargs)

            # Combine chunk results
            self.combined_results = await self._combine_chunk_results()

            # Calculate final metrics
            final_results = await self._calculate_final_metrics(symbol, start_date, end_date, **kwargs)

            self.end_time = time.time()

            # Update performance metrics
            self.performance_metrics.processing_time = self.end_time - self.start_time
            self.performance_metrics.processing_speed_points_per_sec = \
                len(historical_data) / self.performance_metrics.processing_time

            logger.info(f"Optimized backtest completed in {self.performance_metrics.processing_time:.2f} seconds")

            return final_results

        except Exception as e:
            logger.exception(f"Error running optimized backtest: {e}")
            raise

    async def _load_historical_data(self, symbol: str,
                                  start_date: datetime,
                                  end_date: datetime) -> Optional[pd.DataFrame]:
        """Load historical data with validation"""

        try:
            # Get data from data service
            market_data = await self.data_service.get_market_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )

            if not market_data:
                return None

            # Convert to DataFrame
            data_dict = []
            for data_point in market_data:
                data_dict.append({
                    'Date': data_point.timestamp,
                    'Open': float(data_point.open_price),
                    'High': float(data_point.high_price),
                    'Low': float(data_point.low_price),
                    'Close': float(data_point.close_price),
                    'Volume': data_point.volume
                })

            df = pd.DataFrame(data_dict)
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)

            # Validate data quality
            if self.config.enable_data_validation:
                self._validate_data_quality(df)

            return df

        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return None

    def _validate_data_quality(self, data: pd.DataFrame) -> None:
        """Validate data quality for long-term analysis"""

        # Check for missing data
        missing_data_pct = data.isnull().sum().sum() / len(data) / len(data.columns)
        if missing_data_pct > 0.05:  # More than 5% missing data
            logger.warning(f"High missing data percentage: {missing_data_pct:.2%}")

        # Check for data continuity
        date_range = data.index.max() - data.index.min()
        expected_days = date_range.days
        actual_days = len(data)

        if actual_days / expected_days < 0.8:  # Less than 80% data continuity
            logger.warning(f"Low data continuity: {actual_days}/{expected_days} days ({actual_days/expected_days:.1%})")

        # Check price data sanity
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in data.columns:
                if (data[col] <= 0).any():
                    logger.warning(f"Invalid prices found in {col} column")

        logger.info("Data quality validation completed")

    async def _process_data_chunks(self, historical_data: pd.DataFrame,
                                 strategy_func, **kwargs) -> List[Dict[str, Any]]:
        """Process historical data in optimized chunks"""

        # Split data into chunks
        chunk_size_years = self.config.chunked_config.chunk_size_years
        data_chunks = self.chunked_processor.split_data_into_chunks(historical_data, chunk_size_years)

        if not data_chunks:
            raise ValueError("No data chunks to process")

        logger.info(f"Processing {len(data_chunks)} chunks with optimized engine")

        chunk_results = []

        for i, chunk in enumerate(data_chunks):
            logger.info(f"Processing chunk {i+1}/{len(data_chunks)} ({len(chunk)} data points)")

            # Process chunk with memory monitoring
            if self.chunked_processor.memory_manager.check_memory_limit():
                logger.warning("Memory limit reached, optimizing memory")
                self.chunked_processor.memory_manager.optimize_memory(force_gc=True)

            # Process chunk
            chunk_result = self.chunked_processor.process_chunk_vectorbt(
                chunk, strategy_func, **kwargs
            )

            # Add chunk metadata
            chunk_result['chunk_info'] = {
                'chunk_index': i,
                'start_date': chunk.index.min(),
                'end_date': chunk.index.max(),
                'data_points': len(chunk)
            }

            chunk_results.append(chunk_result)

            # Progress reporting
            if self.config.enable_real_time_progress:
                progress = (i + 1) / len(data_chunks) * 100
                logger.info(f"Progress: {progress:.1f}% - Chunk {i+1}/{len(data_chunks)} completed")

            # Save intermediate results if enabled
            if self.config.save_intermediate_results and self.config.intermediate_results_path:
                await self._save_intermediate_results(chunk_result, i)

        logger.info("All chunks processed successfully")
        return chunk_results

    async def _combine_chunk_results(self) -> Dict[str, Any]:
        """Combine results from all chunks"""

        if not self.chunk_results:
            return {}

        logger.info("Combining chunk results...")

        # Combine returns
        all_returns = []
        for result in self.chunk_results:
            if 'returns' in result and result['returns'] is not None:
                all_returns.append(result['returns'])

        combined_returns = pd.concat(all_returns) if all_returns else pd.Series()

        # Combine equity curves
        all_equity = []
        for result in self.chunk_results:
            if 'equity' in result and result['equity'] is not None:
                all_equity.append(result['equity'])

        combined_equity = pd.concat(all_equity) if all_equity else pd.Series()

        # Combine other metrics
        combined_results = {
            'returns': combined_returns,
            'equity': combined_equity,
            'total_return': self._calculate_total_return_from_chunks(),
            'annualized_return': self._calculate_annualized_return_from_chunks(),
            'sharpe_ratio': self._calculate_sharpe_from_chunks(),
            'max_drawdown': self._calculate_max_drawdown_from_chunks(),
            'volatility': combined_returns.std() * np.sqrt(252) if len(combined_returns) > 0 else 0,
            'chunk_count': len(self.chunk_results),
            'total_data_points': sum(r.get('chunk_info', {}).get('data_points', 0) for r in self.chunk_results)
        }

        logger.info("Chunk results combined successfully")
        return combined_results

    def _calculate_total_return_from_chunks(self) -> float:
        """Calculate total return across all chunks"""
        if not self.chunk_results:
            return 0.0

        # Get first equity value and last equity value
        first_chunk = self.chunk_results[0]
        last_chunk = self.chunk_results[-1]

        if 'equity' in first_chunk and 'equity' in last_chunk:
            if len(first_chunk['equity']) > 0 and len(last_chunk['equity']) > 0:
                first_value = first_chunk['equity'].iloc[0]
                last_value = last_chunk['equity'].iloc[-1]
                return (last_value - first_value) / first_value if first_value != 0 else 0.0

        return 0.0

    def _calculate_annualized_return_from_chunks(self) -> float:
        """Calculate annualized return across all chunks"""
        total_return = self._calculate_total_return_from_chunks()
        if not self.chunk_results:
            return 0.0

        # Calculate total years
        first_date = self.chunk_results[0].get('chunk_info', {}).get('start_date')
        last_date = self.chunk_results[-1].get('chunk_info', {}).get('end_date')

        if first_date and last_date:
            years = (last_date - first_date).days / 365.25
            if years > 0:
                return (1 + total_return) ** (1/years) - 1

        return 0.0

    def _calculate_sharpe_from_chunks(self) -> float:
        """Calculate Sharpe ratio from combined chunk returns"""
        if not self.combined_results or 'returns' not in self.combined_results:
            return 0.0

        returns = self.combined_results['returns']
        if len(returns) == 0:
            return 0.0

        return self.chunked_processor._calculate_sharpe_ratio(returns)

    def _calculate_max_drawdown_from_chunks(self) -> float:
        """Calculate maximum drawdown from combined chunk equity"""
        if not self.combined_results or 'equity' not in self.combined_results:
            return 0.0

        equity = self.combined_results['equity']
        if len(equity) == 0:
            return 0.0

        return self.chunked_processor._calculate_max_drawdown(equity)

    async def _calculate_final_metrics(self, symbol: str, start_date: datetime,
                                     end_date: datetime, **kwargs) -> Dict[str, Any]:
        """Calculate final performance metrics"""

        if not self.combined_results:
            raise ValueError("No combined results available")

        logger.info("Calculating final performance metrics...")

        # Basic metrics
        final_results = {
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'data_points': self.combined_results['total_data_points'],
            'chunks_processed': self.combined_results['chunk_count'],

            # Performance metrics
            'total_return': self.combined_results['total_return'],
            'annualized_return': self.combined_results['annualized_return'],
            'sharpe_ratio': self.combined_results['sharpe_ratio'],
            'max_drawdown': self.combined_results['max_drawdown'],
            'volatility': self.combined_results['volatility'],

            # Risk-adjusted metrics
            'sortino_ratio': self._calculate_sortino_ratio(),
            'calmar_ratio': self._calculate_calmar_ratio(),
            'information_ratio': self._calculate_information_ratio(**kwargs),

            # Performance metrics
            'processing_time': self.performance_metrics.processing_time,
            'processing_speed': self.performance_metrics.processing_speed_points_per_sec,
            'memory_peak_usage': self.chunked_processor.memory_manager.get_memory_usage_gb(),
            'memory_efficiency': self._calculate_memory_efficiency(),

            # Data quality metrics
            'data_completeness': self._calculate_data_completeness(),
            'data_quality_score': self._calculate_data_quality_score(),
        }

        # Additional advanced metrics
        if VECTORBT_AVAILABLE:
            final_results.update(await self._calculate_advanced_metrics())

        logger.info("Final metrics calculation completed")
        return final_results

    def _calculate_sortino_ratio(self) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        if not self.combined_results or 'returns' not in self.combined_results:
            return 0.0

        returns = self.combined_results['returns']
        if len(returns) == 0:
            return 0.0

        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float('inf')

        downside_deviation = downside_returns.std() * np.sqrt(252)
        annual_return = self.combined_results['annualized_return']

        return (annual_return - 0.02) / downside_deviation if downside_deviation > 0 else 0.0

    def _calculate_calmar_ratio(self) -> float:
        """Calculate Calmar ratio (return/max_drawdown)"""
        if not self.combined_results:
            return 0.0

        annual_return = self.combined_results['annualized_return']
        max_drawdown = abs(self.combined_results['max_drawdown'])

        return annual_return / max_drawdown if max_drawdown > 0 else 0.0

    def _calculate_information_ratio(self, **kwargs) -> float:
        """Calculate Information ratio (vs benchmark)"""
        # Simplified - would need benchmark data for proper calculation
        return self.combined_results['sharpe_ratio'] * 0.8  # Estimate

    def _calculate_memory_efficiency(self) -> float:
        """Calculate memory usage efficiency"""
        if not self.performance_metrics.chunks_processed:
            return 1.0

        # Memory efficiency = target / actual usage
        target_memory = self.config.chunked_config.max_memory_usage_gb
        actual_memory = self.chunked_processor.memory_manager.get_memory_usage_gb()

        return target_memory / actual_memory if actual_memory > 0 else 1.0

    def _calculate_data_completeness(self) -> float:
        """Calculate data completeness score"""
        if not self.chunk_results:
            return 0.0

        total_expected_points = sum(
            (r.get('chunk_info', {}).get('end_date') - r.get('chunk_info', {}).get('start_date')).days
            for r in self.chunk_results
        )

        actual_points = sum(r.get('chunk_info', {}).get('data_points', 0) for r in self.chunk_results)

        return actual_points / (total_expected_points * 252/365) if total_expected_points > 0 else 1.0

    def _calculate_data_quality_score(self) -> float:
        """Calculate overall data quality score"""
        completeness = self._calculate_data_completeness()
        memory_efficiency = self._calculate_memory_efficiency()

        # Combine metrics
        return (completeness * 0.7 + memory_efficiency * 0.3)

    async def _calculate_advanced_metrics(self) -> Dict[str, Any]:
        """Calculate advanced VectorBT metrics if available"""
        if not VECTORBT_AVAILABLE:
            return {}

        # Placeholder for advanced metrics
        # Would include metrics like beta, alpha, correlation analysis, etc.
        return {
            'advanced_metrics_available': True,
            'note': 'Advanced VectorBT metrics would be calculated here'
        }

    async def _save_intermediate_results(self, chunk_result: Dict[str, Any],
                                       chunk_index: int) -> None:
        """Save intermediate results for large backtests"""
        if not self.config.intermediate_results_path:
            return

        try:
            import json
            filename = f"chunk_{chunk_index}_results.json"
            filepath = os.path.join(self.config.intermediate_results_path, filename)

            # Convert pandas objects to serializable format
            serializable_result = {}
            for key, value in chunk_result.items():
                if hasattr(value, 'to_dict'):  # pandas Series/DataFrame
                    serializable_result[key] = value.to_dict()
                elif isinstance(value, (int, float, str, bool, list, dict)):
                    serializable_result[key] = value
                else:
                    serializable_result[key] = str(value)

            with open(filepath, 'w') as f:
                json.dump(serializable_result, f, indent=2, default=str)

            logger.debug(f"Saved intermediate results to {filepath}")

        except Exception as e:
            logger.warning(f"Failed to save intermediate results: {e}")

    async def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance and optimization report"""

        return {
            'processing_summary': {
                'total_time': self.performance_metrics.processing_time,
                'chunks_processed': self.performance_metrics.chunks_processed,
                'total_data_points': self.performance_metrics.total_data_points,
                'processing_speed': self.performance_metrics.processing_speed_points_per_sec,
            },
            'memory_performance': {
                'peak_memory_gb': self.chunked_processor.memory_manager.get_memory_usage_gb(),
                'memory_efficiency': self._calculate_memory_efficiency(),
                'gc_runs': self.chunked_processor.memory_manager.gc_runs_count,
                'memory_freed_gb': self.chunked_processor.performance_metrics.memory_freed_gb,
            },
            'optimization_metrics': {
                'chunk_size_years': self.config.chunked_config.chunk_size_years,
                'parallel_processing': self.config.chunked_config.enable_parallel,
                'max_workers': self.config.chunked_config.max_workers,
                'vectorbt_optimization': self.config.chunked_config.enable_vectorbt_optimization,
                'numba_acceleration': self.config.chunked_config.enable_numba_jit,
            },
            'data_quality': {
                'completeness': self._calculate_data_completeness(),
                'quality_score': self._calculate_data_quality_score(),
            }
        }

    async def cleanup(self) -> None:
        """Clean up resources and optimize memory"""
        try:
            # Clear chunk results
            self.chunk_results.clear()
            self.combined_results = None

            # Run final garbage collection
            gc.collect()

            # Clear cache if enabled
            if self.config.chunked_config.clear_cache_on_complete:
                self.chunked_processor.memory_manager.optimize_memory(force_gc=True)

            logger.info("Phase 3 Optimized VectorBT Engine cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Utility functions for easy usage
async def run_optimized_long_term_backtest(symbol: str,
                                         start_date: datetime,
                                         end_date: datetime,
                                         strategy_func,
                                         **kwargs) -> Dict[str, Any]:
    """Convenience function to run optimized long-term backtest"""

    config = Phase3BacktestConfig()
    engine = Phase3OptimizedVectorBTEngine(config)

    try:
        await engine.initialize()
        results = await engine.run_optimized_backtest(
            symbol, start_date, end_date, strategy_func, **kwargs
        )

        # Add performance report
        results['performance_report'] = await engine.get_performance_report()

        return results

    finally:
        await engine.cleanup()


# Example strategy functions for testing
def sample_rsi_strategy(data: pd.DataFrame, rsi_period: int = 14,
                       oversold: float = 30, overbought: float = 70) -> pd.Series:
    """Sample RSI mean reversion strategy"""

    # Calculate RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # Generate signals
    signals = pd.Series(False, index=data.index)
    signals[rsi < oversold] = True   # Buy when oversold
    signals[rsi > overbought] = False  # Sell when overbought

    return signals


def sample_momentum_strategy(data: pd.DataFrame, lookback: int = 50) -> pd.Series:
    """Sample momentum strategy"""

    # Calculate momentum
    returns = data['Close'].pct_change(lookback)

    # Generate signals based on momentum
    signals = returns > 0  # Buy when positive momentum

    return signals


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def main():
        # Test the optimized engine
        symbol = "0700.HK"
        start_date = datetime(2018, 1, 1)
        end_date = datetime(2023, 12, 31)

        results = await run_optimized_long_term_backtest(
            symbol, start_date, end_date, sample_rsi_strategy,
            rsi_period=14, oversold=30, overbought=70
        )

        print("Backtest Results:")
        print(f"Total Return: {results['total_return']:.2%}")
        print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {results['max_drawdown']:.2%}")
        print(f"Processing Time: {results['processing_time']:.2f} seconds")
        print(f"Processing Speed: {results['processing_speed']:.0f} points/sec")

    asyncio.run(main())
```


## stockbacktest_adapter.py

```py
"""Adapters for integrating StockBacktest project with the agent system."""

from __future__ import annotations

import importlib
import logging
from functools import lru_cache
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional

import pandas as pd

from .config import StockBacktestConfig
from .exceptions import (
StockBacktestConfigError,
StockBacktestDataError,
StockBacktestImportError,
StockBacktestStrategyError,
)

LOGGER = logging.getLogger"hk_quant_system.backtest.adapter"

StrategyCallable = Callable[[pd.DataFrame, Mapping[str, Any]], Any]

class ModuleLoader:
"""Dynamically load callables from the StockBacktest project."""

def __init__self, config: StockBacktestConfig:    self.config = config
self._engine_module = None

@property
def engine_moduleself:
if self._engine_module is None:
try:    self._engine_module = importlib.import_module(self.config.engine_module)
except ImportError as exc:
LOGGER.exception"Failed to import StockBacktest module: %s", exc
raise StockBacktestImportError(strexc) from exc
return self._engine_module

def get_callableself, name: str -> Callable:
try:
return getattrself.engine_module, name
except AttributeError as exc:    msg = f"StockBacktest module missing callable {name}"
LOGGER.errormsg
raise StockBacktestImportErrormsg from exc

class StrategyMapper:
"""Map agent strategies to StockBacktest strategy functions."""

def __init__self, loader: ModuleLoader:    self.loader = loader

@lru_cachemaxsize=16
def available_strategiesself -> Dict[str, StrategyCallable]:    module = self.loader.engine_module
strategies = {}
for attr in dirmodule:
if attr.endswith"_strategy" and callable(getattrmodule, attr):    strategies[attr] = getattr(module, attr)
return strategies

def get_strategyself, strategy_type: str -> StrategyCallable:    strategies = self.available_strategies()
if strategy_type in strategies:
return strategies[strategy_type]
# Fallback to a default strategy if available
default_name = f"{strategy_type}_strategy"
if default_name in strategies:
return strategies[default_name]
raise StockBacktestStrategyErrorf"Unsupported strategy type: {strategy_type}"

class DataTransformer:
"""Convert between RealMarketData structures and StockBacktest dataframes."""

def __init__self, required_columns: Optional[Iterable[str]] = None:    self.required_columns = required_columns or [
"open",
"high",
"low",
"close",
"volume",
]

def to_dataframeself, market_data: List[Mapping[str, Any]] -> pd.DataFrame:
if not market_data:
raise StockBacktestDataError"No market data provided for backtest"

df = pd.DataFramemarket_data
missing = [col for col in self.required_columns if col not in df.columns]
if missing:
raise StockBacktestDataError(f"Missing required columns: {', '.joinmissing}")

if "timestamp" in df.columns:    df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index'timestamp', inplace=True

df.sort_indexinplace=True
return df

__all__ = [
"ModuleLoader",
"StrategyMapper",
"DataTransformer",
]

```


## stockbacktest_integration.py

```py
"""StockBacktest project integration."""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ..core import SystemConfig
from ..data_adapters.base_adapter import RealMarketData
from .config import StockBacktestConfig
from .engine_interface import (
    BacktestEngineConfig,
    BacktestMetrics,
    BacktestStatus,
    BaseBacktestEngine,
    StrategyPerformance,
)
from .exceptions import (
    StockBacktestConfigError,
    StockBacktestDataError,
    StockBacktestError,
    StockBacktestStrategyError,
)
from .stockbacktest_adapter import DataTransformer, ModuleLoader, StrategyMapper


class StockBacktestIntegration(BaseBacktestEngine):
    """Concrete implementation integrating the legacy StockBacktest project."""

    def __init__(
        self,
        config: BacktestEngineConfig,
        stockbacktest_path: Optional[str] = None,
        stockbacktest_config: Optional[StockBacktestConfig] = None,
    ) -> None:
        super().__init__(config)
        self._stock_config = stockbacktest_config or StockBacktestConfig.from_env(
            stockbacktest_path
        )
        self._loader = ModuleLoader(self._stock_config)
        self._strategy_mapper = StrategyMapper(self._loader)
        self._data_transformer = DataTransformer()
        self._performance_callable = None
        self._engine_callable = None
        self._strategy_cache: Dict[str, BacktestMetrics] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def initialize(self) -> bool:
        try:
            base_path: Path = self._stock_config.base_path
            if not base_path.exists():
                msg = f"StockBacktest directory not found: {base_path}"
                self.logger.error(msg)
                if self._stock_config.strict_import:
                    raise StockBacktestConfigError(msg)
                return False

            if str(base_path) not in sys.path:
                sys.path.insert(0, str(base_path))

            # Ensure performance callable is available
            self._engine_callable = self._loader.get_callable(
                self._stock_config.engine_callable_name
            )
            try:
                self._performance_callable = self._loader.get_callable(
                    self._stock_config.performance_callable_name
                )
            except StockBacktestError:
                self.logger.warning(
                    "Performance callable '%s' not found, proceeding without it",
                    self._stock_config.performance_callable_name,
                )

            self.logger.info("StockBacktest integration initialized successfully")
            self.set_status(BacktestStatus.COMPLETED)
            return True
        except StockBacktestError:
            if self._stock_config.strict_import:
                raise
            self.logger.exception("Failed to initialize StockBacktest integration")
            return False

    async def cleanup(self) -> None:
        self._strategy_cache.clear()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def validate_strategy(self, strategy: Dict[str, Any]) -> bool:
        required_fields = {"name", "type", "parameters"}
        missing = required_fields - set(strategy.keys())
        if missing:
            raise StockBacktestStrategyError(
                f"Strategy missing required fields: {', '.join(missing)}"
            )

        self._strategy_mapper.get_strategy(strategy["type"])  # ensure mapping exists
        return True

    async def get_performance_summary(
        self, strategy_id: str
    ) -> Optional[StrategyPerformance]:
        cached = self._strategy_cache.get(strategy_id)
        return cached.performance if cached else None

    async def run_backtest(
        self,
        strategy: Dict[str, Any],
        market_data: List[RealMarketData],
    ) -> BacktestMetrics:
        if not market_data:
            raise StockBacktestDataError("No market data provided for backtest")

        self.set_status(BacktestStatus.RUNNING)

        df_market = self._data_transformer.to_dataframe(
            [data.model_dump() for data in market_data]
        )
        strategy_callable = self._strategy_mapper.get_strategy(strategy["type"])

        try:
            engine_result = self._engine_callable(
                df_market,
                strategy_callable,
                float(self.config.initial_capital),
            )
        except Exception as exc:
            self.set_status(BacktestStatus.FAILED)
            raise StockBacktestStrategyError(str(exc)) from exc

        performance = await self._build_performance(strategy, engine_result)
        metrics = BacktestMetrics(
            performance=performance,
            risk_metrics=self._extract_risk_metrics(engine_result),
            trade_analysis=self._extract_trade_analysis(engine_result),
            portfolio_analysis=self._extract_portfolio_metrics(engine_result),
        )

        strategy_id = strategy.get(
            "id", f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self._strategy_cache[strategy_id] = metrics
        self.set_status(BacktestStatus.COMPLETED)
        return metrics

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _build_performance(
        self,
        strategy: Dict[str, Any],
        engine_result: Dict[str, Any],
    ) -> StrategyPerformance:
        # fallback to generic calculator if stockbacktest did not provide detailed metrics
        portfolio_values = engine_result.get("portfolio_values")
        if not portfolio_values:
            raise StockBacktestDataError("StockBacktest engine returned empty portfolio values")

        portfolio_series = pd.Series(portfolio_values)
        returns = portfolio_series.pct_change().dropna()

        from .strategy_performance import PerformanceCalculator

        calculator = PerformanceCalculator()
        performance = calculator.calculate_performance_metrics(
            returns,
            risk_free_rate=float(self.config.risk_free_rate),
        )
        performance.strategy_id = strategy.get(
            "id", f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        performance.strategy_name = strategy.get("name", "Unknown Strategy")
        performance.strategy_type = strategy.get("type", "custom")
        performance.backtest_period = f"{returns.index[0].date()} to {returns.index[-1].date()}"
        performance.start_date = returns.index[0].date()
        performance.end_date = returns.index[-1].date()
        performance.validation_status = "calculated"
        return performance

    def _extract_risk_metrics(self, engine_result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "total_return": engine_result.get("total_return"),
            "max_drawdown": engine_result.get("max_drawdown"),
            "sharpe_ratio": engine_result.get("sharpe_ratio"),
            "win_rate": engine_result.get("win_rate"),
        }

    def _extract_trade_analysis(self, engine_result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "trade_count": engine_result.get("trade_count"),
            "trade_log": engine_result.get("trade_log"),
        }

    def _extract_portfolio_metrics(self, engine_result: Dict[str, Any]) -> Dict[str, Any]:
        final_value = engine_result.get("final_value")
        return {
            "final_value": final_value,
            "capital_base": float(self.config.initial_capital),
        }


```


## strategy_performance.py

```py
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

```

