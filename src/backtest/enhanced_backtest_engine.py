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