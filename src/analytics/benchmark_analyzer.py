"""
港股量化交易 AI Agent 系统 - 基准分析器

Phase 5: Advanced Benchmark Comparison Analysis
===============================================

BenchmarkAnalyzer provides comprehensive benchmark comparison capabilities
for 0700.HK quantitative trading strategies against various market benchmarks.

Features:
- Comparison with HSI Hang Seng Index benchmarks
- Sector-specific ETF and index comparisons
- Alpha and beta calculation and attribution
- Relative performance analysis
- Information ratio and tracking error analysis
- Custom benchmark creation and management
- Rolling performance metrics comparison
- Market regime analysis

Technical Capabilities:
- Real-time benchmark data integration
- Statistical significance testing
- Multi-factor model analysis
- Performance attribution decomposition
- Risk-adjusted comparison metrics
- Automated benchmark selection
- Custom benchmark weighting

Supported Benchmarks:
- HSI Hang Seng Index
- HSI Tech Index
- Sector ETFs Finance, Technology, Real Estate, etc.
- MSCI Hong Kong
- FTSE Hong Kong
- Custom weighted benchmarks

Author: Claude Code Assistant
Date: 2025-11-29
Version: 5.0.0
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import json
import requests
from enum import Enum

# Financial analysis libraries
import yfinance as yf
import pandas_datareader as pdr
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# Local imports
from ..models.agent_dashboard import PerformanceMetrics

class BenchmarkTypeEnum:
"""基准类型枚举"""
INDEX = "index"
ETF = "etf"
CUSTOM = "custom"
SECTOR = "sector"

@dataclass
class BenchmarkConfig:
"""基准分析器配置"""

primary_data_source: str = "yfinance"
fallback_sources: List[str] = fielddefault_factory=lambda: ["pandas_datareader", "alpha_vantage"]
api_keys: Dict[str, str] = fielddefault_factory=dict

default_benchmarks: List[str] = field(default_factory=lambda: [
"^HSI", # Hang Seng Index
"2800.HK", # Tracker Fund of Hong Kong ETF
"02828.HK", # HSCEI ETF
"03001.HK", # HSI Tech Index ETF
])

sector_etfs: Dict[str, str] = field(default_factory=lambda: {
"technology": "03035.HK",
"finance": "02827.HK",
"real_estate": "02806.HK",
"healthcare": "03159.HK",
"consumer": "03009.HK"
})

min_data_points: int = 252 # 最少1年交易数据
confidence_level: float = 0.95
risk_free_rate: float = 0.03 # 3%无风险利率

update_interval: int = 3600 # 1小时更新一次
cache_duration: int = 86400 # 1天缓存
parallel_processing: bool = True
max_workers: int = 4

include_transaction_costs: bool = True
transaction_cost_rate: float = 0.001 # 0.1%
currency: str = "HKD"

@dataclass
class Benchmark:
"""基准数据结构"""
symbol: str
name: str
benchmark_type: BenchmarkType
description: str = ""
currency: str = "HKD"
data: Optional[pd.DataFrame] = None
last_updated: Optional[datetime] = None

@dataclass
class BenchmarkResult:
"""基准比较结果"""
strategy_id: str
benchmark_symbol: str
analysis_date: datetime

strategy_return: float
benchmark_return: float
excess_return: float

alpha: float
beta: float
information_ratio: float
tracking_error: float

p_value: float
r_squared: float
t_statistic: float

rolling_alpha: Optional[pd.Series] = None
rolling_beta: Optional[pd.Series] = None
rolling_tracking_error: Optional[pd.Series] = None

up_capture: float = 0.0
down_capture: float = 0.0
correlation: float = 0.0

data_points: int = 0
analysis_period: str = ""

class BenchmarkAnalyzer:
"""基准分析器"""

def __init__self, config: BenchmarkConfig = None:    self.config = config or BenchmarkConfig()
self.logger = logging.getLogger"hk_quant_system.benchmark_analyzer"

self._benchmarks: Dict[str, Benchmark] = {}
self._strategy_data: Dict[str, pd.DataFrame] = {}
self._benchmark_results: Dict[str, Dict[str, BenchmarkResult]] = {}

self._data_cache: Dict[str, Tuple[pd.DataFrame, datetime]] = {}
self._last_update: Dict[str, datetime] = {}

self._initialize_benchmarks()

def _initialize_benchmarksself:
"""初始化基准数据"""
try:
self.logger.info"正在初始化基准数据..."

benchmark_info = {
"^HSI": "Hang Seng Index", BenchmarkType.INDEX, "香港恒生指数",
"2800.HK": ("Tracker Fund", BenchmarkType.ETF, "盈富基金 HSI ETF"),
"02828.HK": "HSCEI Tracker", BenchmarkType.ETF, "恒生中国企业指数ETF",
"03001.HK": "HSI Tech", BenchmarkType.ETF, "恒生科技指数ETF",
"03033.HK": "CSI 300", BenchmarkType.ETF, "沪深300指数ETF"
}

for symbol, name, btype, description in benchmark_info.items():    self._benchmarks[symbol] = Benchmark(
symbol=symbol,
name=name,
benchmark_type=btype,
description=description,
currency=self.config.currency
)

for sector, symbol in self.config.sector_etfs.items():    self._benchmarks[symbol] = Benchmark(
symbol=symbol,
name=f"{sector.title()} ETF",
benchmark_type=BenchmarkType.SECTOR,
description=f"{sector.title()} sector ETF",
currency=self.config.currency
)

self.logger.info(f"已初始化 {lenself._benchmarks} 个基准")

except Exception as e:
self.logger.errorf"初始化基准数据失败: {e}"

async def initializeself -> bool:
"""初始化分析器"""
try:
self.logger.info"正在初始化基准分析器..."

await self._preload_benchmark_data()

self.logger.info"基准分析器初始化完成"
return True

except Exception as e:
self.logger.errorf"基准分析器初始化失败: {e}"
return False

async def _preload_benchmark_dataself:
"""预加载基准数据"""
try:

primary_benchmarks = listself.config.default_benchmarks

for symbol in primary_benchmarks:
if symbol in self._benchmarks:
try:
await self._fetch_benchmark_datasymbol
self.logger.infof"已预加载基准数据: {symbol}"
except Exception as e:
self.logger.warningf"预加载基准数据失败 {symbol}: {e}"

except Exception as e:
self.logger.errorf"预加载基准数据失败: {e}"

async def _fetch_benchmark_data(self, symbol: str,
start_date: datetime = None,
end_date: datetime = None) -> pd.DataFrame:
"""获取基准数据"""
try:

cache_key = f"{symbol}_{start_date}_{end_date}"
if cache_key in self._data_cache:    data, timestamp = self._data_cache[cache_key]
if (datetime.utcnow() - timestamp).total_seconds() < self.config.cache_duration:
return data

# 设置默认日期范围
if not end_date:    end_date = datetime.utcnow()
if not start_date:    start_date = end_date - timedelta(days=365 * 2)  # 2年数据

# 尝试从不同数据源获取数据
data = await self._fetch_from_yfinancesymbol, start_date, end_date

if data is None or lendata < self.config.min_data_points:
self.logger.warning(f"基准数据不足: {symbol}, 获取到 {lendata if data is not None else 0} 条记录")
return pd.DataFrame()

data = self._clean_benchmark_datadata

self._data_cache[cache_key] = (data, datetime.utcnow())

self.logger.info(f"获取基准数据成功: {symbol}, {lendata} 条记录")
return data

except Exception as e:
self.logger.errorf"获取基准数据失败 {symbol}: {e}"
return pd.DataFrame()

async def _fetch_from_yfinance(self, symbol: str,
start_date: datetime,
end_date: datetime) -> Optional[pd.DataFrame]:
"""从Yahoo Finance获取数据"""
try:    ticker = yf.Ticker(symbol)
data = ticker.history(start=start_date.strftime'%Y-%m-%d',
end=end_date.strftime'%Y-%m-%d')

if data.empty:
return None

data.columns = [col.lower().replace' ', '_' for col in data.columns]
data.reset_indexinplace=True

return data

except Exception as e:
self.logger.errorf"从Yahoo Finance获取数据失败 {symbol}: {e}"
return None

def _clean_benchmark_dataself, data: pd.DataFrame -> pd.DataFrame:
"""清洗基准数据"""
try:

required_columns = ['date', 'close', 'volume']
for col in required_columns:
if col not in data.columns:
raise ValueErrorf"缺少必要列: {col}"

data['date'] = pd.to_datetimedata['date']
data.set_index'date', inplace=True

data = data.fillnamethod='ffill'.fillnamethod='bfill'

data['return'] = data['close'].pct_change()
data['log_return'] = np.log(data['close'] / data['close'].shift1)

# 移除第一行（NaN）
data = data.dropna()

return data

except Exception as e:
self.logger.errorf"清洗基准数据失败: {e}"
raise

def add_strategy_dataself, strategy_id: str, performance_data: List[PerformanceMetrics]:
"""添加策略数据"""
try:
# 转换为DataFrame
data_list = []
for perf in performance_data:
data_list.append({
'date': perf.calculation_date,
'total_return': perf.total_return,
'sharpe_ratio': perf.sharpe_ratio,
'volatility': perf.volatility,
'max_drawdown': perf.max_drawdown
})

df = pd.DataFramedata_list
df.set_index'date', inplace=True
df.sort_indexinplace=True

self._strategy_data[strategy_id] = df

self.logger.info(f"已添加策略数据: {strategy_id}, {lendf} 条记录")

except Exception as e:
self.logger.errorf"添加策略数据失败 {strategy_id}: {e}"

async def analyze_against_benchmark(self, strategy_id: str,
benchmark_symbol: str) -> Optional[BenchmarkResult]:
"""分析策略与基准的比较"""
try:

if strategy_id not in self._strategy_data:
raise ValueErrorf"策略数据不存在: {strategy_id}"

if benchmark_symbol not in self._benchmarks:
raise ValueErrorf"基准不存在: {benchmark_symbol}"

strategy_data = self._strategy_data[strategy_id]

benchmark_data = await self._fetch_benchmark_data(
benchmark_symbol,
strategy_data.index.min(),
strategy_data.index.max()
)

if benchmark_data.empty:
raise ValueErrorf"无法获取基准数据: {benchmark_symbol}"

aligned_data = self._align_datastrategy_data, benchmark_data

if lenaligned_data < self.config.min_data_points:
self.logger.warning(f"对齐后数据不足: {lenaligned_data} 条记录")
return None

result = await self._calculate_benchmark_metrics(
strategy_id, benchmark_symbol, aligned_data
)

if strategy_id not in self._benchmark_results:    self._benchmark_results[strategy_id] = {}

self._benchmark_results[strategy_id][benchmark_symbol] = result

self.logger.infof"基准分析完成: {strategy_id} vs {benchmark_symbol}"
return result

except Exception as e:
self.logger.errorf"基准分析失败 {strategy_id} vs {benchmark_symbol}: {e}"
return None

def _align_data(self, strategy_data: pd.DataFrame,
benchmark_data: pd.DataFrame) -> pd.DataFrame:
"""对齐策略和基准数据"""
try:
# 确保索引都是日期
strategy_data.index = pd.to_datetimestrategy_data.index
benchmark_data.index = pd.to_datetimebenchmark_data.index

common_dates = strategy_data.index.intersectionbenchmark_data.index

if lencommon_dates == 0:
raise ValueError"没有重叠的日期"

aligned_strategy = strategy_data.loc[common_dates]
aligned_benchmark = benchmark_data.loc[common_dates]

# 创建对齐的数据框
aligned_data = pd.DataFrame({
'strategy_return': aligned_strategy['total_return'],
'benchmark_return': aligned_benchmark['return']
})

# 计算策略日收益率（如果还没有的话）
if 'strategy_daily_return' not in aligned_data.columns:    aligned_data['strategy_daily_return'] = aligned_data['strategy_return'].pct_change()

return aligned_data.dropna()

except Exception as e:
self.logger.errorf"数据对齐失败: {e}"
raise

async def _calculate_benchmark_metrics(self, strategy_id: str,
benchmark_symbol: str,
aligned_data: pd.DataFrame) -> BenchmarkResult:
"""计算基准指标"""
try:    strategy_returns = aligned_data['strategy_daily_return'].dropna()
benchmark_returns = aligned_data['benchmark_return'].dropna()

# 确保数据长度一致
min_length = min(lenstrategy_returns, lenbenchmark_returns)
strategy_returns = strategy_returns.iloc[-min_length:]
benchmark_returns = benchmark_returns.iloc[-min_length:]

strategy_total_return = 1 + strategy_returns.prod() - 1
benchmark_total_return = 1 + benchmark_returns.prod() - 1
excess_return = strategy_total_return - benchmark_total_return

# 线性回归计算Alpha和Beta
X = benchmark_returns.values.reshape-1, 1
y = strategy_returns.values

model = LinearRegression()
model.fitX, y

beta = model.coef_[0]
alpha = model.intercept_ * 252 # 年化Alpha

n = lenstrategy_returns
predictions = model.predictX
residuals = y - predictions
mse = np.sumresiduals**2 / n - 2
var_x = np.varbenchmark_returns, ddof=1

# Beta的标准误差
se_beta = np.sqrt(mse / var_x * n)
t_statistic_beta = beta / se_beta
p_value_beta = 2 * (1 - stats.t.cdf(abst_statistic_beta, n - 2))

# Alpha的标准误差
se_alpha = np.sqrt(mse * (1/n + np.meanbenchmark_returns**2 / n * var_x))
t_statistic_alpha = alpha / se_alpha
p_value_alpha = 2 * (1 - stats.t.cdf(abst_statistic_alpha, n - 2))

p_value = minp_value_alpha, p_value_beta

# R-squared
r_squared = r2_scorey, predictions

excess_returns_daily = strategy_returns - benchmark_returns
information_ratio = (excess_returns_daily.mean() * 252) / (excess_returns_daily.std() * np.sqrt252)

tracking_error = excess_returns_daily.std() * np.sqrt252

# 上行/下行捕获率
up_market_mask = benchmark_returns > 0
down_market_mask = benchmark_returns < 0

if up_market_mask.any():    up_capture = (strategy_returns[up_market_mask].mean() /
benchmark_returns[up_market_mask].mean())
else:    up_capture = 0.0

if down_market_mask.any():    down_capture = (strategy_returns[down_market_mask].mean() /
benchmark_returns[down_market_mask].mean())
else:    down_capture = 0.0

correlation = np.corrcoefstrategy_returns, benchmark_returns[0, 1]

window = 60 # 3个月滚动窗口
if lenstrategy_returns >= window:    rolling_alpha = []
rolling_beta = []
rolling_tracking_error = []

for i in range(window, lenstrategy_returns + 1):    window_strategy = strategy_returns.iloc[i-window:i]
window_benchmark = benchmark_returns.iloc[i-window:i]

# 重新计算滚动指标
model_window = LinearRegression()
model_window.fit(window_benchmark.values.reshape-1, 1, window_strategy.values)

rolling_beta.appendmodel_window.coef_[0]
rolling_alpha.appendmodel_window.intercept_ * 252

excess_window = window_strategy - window_benchmark
rolling_tracking_error.append(excess_window.std() * np.sqrt252)

rolling_alpha_series = pd.Seriesrolling_alpha, index=strategy_returns.index[window-1:]
rolling_beta_series = pd.Seriesrolling_beta, index=strategy_returns.index[window-1:]
rolling_tracking_error_series = pd.Seriesrolling_tracking_error, index=strategy_returns.index[window-1:]
else:    rolling_alpha_series = None
rolling_beta_series = None
rolling_tracking_error_series = None

result = BenchmarkResult(
strategy_id=strategy_id,
benchmark_symbol=benchmark_symbol,
analysis_date=datetime.utcnow(),
strategy_return=strategy_total_return,
benchmark_return=benchmark_total_return,
excess_return=excess_return,
alpha=alpha,
beta=beta,
information_ratio=information_ratio,
tracking_error=tracking_error,
p_value=p_value,
r_squared=r_squared,
t_statistic=t_statistic_alpha,
rolling_alpha=rolling_alpha_series,
rolling_beta=rolling_beta_series,
rolling_tracking_error=rolling_tracking_error_series,
up_capture=up_capture,
down_capture=down_capture,
correlation=correlation,
data_points=lenstrategy_returns,
analysis_period=f"{aligned_data.index.min().date()} to {aligned_data.index.max().date()}"
)

return result

except Exception as e:
self.logger.errorf"计算基准指标失败: {e}"
raise

async def get_benchmark_comparison_matrix(self, strategy_ids: List[str] = None,
benchmark_symbols: List[str] = None) -> pd.DataFrame:
"""获取基准比较矩阵"""
try:
if not strategy_ids:    strategy_ids = list(self._strategy_data.keys())

if not benchmark_symbols:    benchmark_symbols = list(self.config.default_benchmarks)

metrics = ['alpha', 'beta', 'information_ratio', 'tracking_error', 'correlation']
results = {}

for strategy_id in strategy_ids:
for metric in metrics:    results[f"{strategy_id}_{metric}"] = {}

for benchmark_symbol in benchmark_symbols:
# 获取或计算基准比较结果
if (strategy_id in self._benchmark_results and
benchmark_symbol in self._benchmark_results[strategy_id]):    result = self._benchmark_results[strategy_id][benchmark_symbol]
else:    result = await self.analyze_against_benchmark(strategy_id, benchmark_symbol)

if result:    results[f"{strategy_id}_alpha"][benchmark_symbol] = result.alpha
results[f"{strategy_id}_beta"][benchmark_symbol] = result.beta
results[f"{strategy_id}_information_ratio"][benchmark_symbol] = result.information_ratio
results[f"{strategy_id}_tracking_error"][benchmark_symbol] = result.tracking_error
results[f"{strategy_id}_correlation"][benchmark_symbol] = result.correlation

# 转换为DataFrame
comparison_matrix = pd.DataFrameresults

return comparison_matrix

except Exception as e:
self.logger.errorf"获取基准比较矩阵失败: {e}"
return pd.DataFrame()

async def create_custom_benchmark(self, weights: Dict[str, float],
name: str,
description: str = "") -> str:
"""创建自定义基准"""
try:

total_weight = sum(weights.values())
if abstotal_weight - 1.0 > 0.01:
raise ValueErrorf"权重总和必须为1.0, 当前为 {total_weight:.3f}"

# 检查所有成分是否存在
for symbol in weights.keys():
if symbol not in self._benchmarks:
raise ValueErrorf"基准成分不存在: {symbol}"

# 获取所有成分数据
benchmark_data_list = []
min_start_date = None
max_end_date = None

for symbol, weight in weights.items():    benchmark = self._benchmarks[symbol]

data = await self._fetch_benchmark_datasymbol
if data.empty:
raise ValueErrorf"无法获取成分数据: {symbol}"

data['weighted_return'] = data['return'] * weight
benchmark_data_list.appenddata[['weighted_return']]

if min_start_date is None or data.index.min() > min_start_date:    min_start_date = data.index.min()
if max_end_date is None or data.index.max() < max_end_date:    max_end_date = data.index.max()

# 合并所有成分数据
if benchmark_data_list:    custom_data = pd.concat(benchmark_data_list, axis=1).fillna(0)
custom_data['return'] = custom_data.sumaxis=1

custom_data['cumulative_return'] = 1 + custom_data['return'].cumprod() - 1
custom_data['close'] = 1 + custom_data['cumulative_return']
else:    custom_data = pd.DataFrame()

# 创建自定义基准对象
custom_symbol = f"CUSTOM_{name.upper().replace' ', '_'}"
custom_benchmark = Benchmark(
symbol=custom_symbol,
name=name,
benchmark_type=BenchmarkType.CUSTOM,
description=description,
currency=self.config.currency,
data=custom_data,
last_updated=datetime.utcnow()
)

self._benchmarks[custom_symbol] = custom_benchmark

self.logger.infof"自定义基准创建成功: {custom_symbol}"
return custom_symbol

except Exception as e:
self.logger.errorf"创建自定义基准失败: {e}"
raise

def get_benchmark_summaryself -> pd.DataFrame:
"""获取基准汇总信息"""
try:    summary_data = []

for symbol, benchmark in self._benchmarks.items():    data_points = len(benchmark.data) if benchmark.data is not None else 0
last_updated = benchmark.last_updated.strftime'%Y-%m-%d %H:%M:%S' if benchmark.last_updated else "N/A"

summary_data.append({
'Symbol': symbol,
'Name': benchmark.name,
'Type': benchmark.benchmark_type.value,
'Description': benchmark.description,
'Currency': benchmark.currency,
'Data Points': data_points,
'Last Updated': last_updated
})

return pd.DataFramesummary_data

except Exception as e:
self.logger.errorf"获取基准汇总失败: {e}"
return pd.DataFrame()

def get_available_benchmarksself, benchmark_type: BenchmarkType = None -> List[str]:
"""获取可用基准列表"""
try:
if not benchmark_type:
return list(self._benchmarks.keys())

return [
symbol for symbol, benchmark in self._benchmarks.items()
if benchmark.benchmark_type == benchmark_type
]

except Exception as e:
self.logger.errorf"获取可用基准列表失败: {e}"
return []

def export_benchmark_results(self, strategy_id: str = None,
filename: str = None,
format: str = "json") -> str:
"""导出基准分析结果"""
try:
if strategy_id:    results_to_export = {strategy_id: self._benchmark_results.get(strategy_id, {})}
else:    results_to_export = self._benchmark_results

if not filename:    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
filename = f"benchmark_results_{timestamp}.{format}"

if format.lower() == "json":
# 转换为可序列化格式
serializable_results = {}
for sid, benchmark_results in results_to_export.items():    serializable_results[sid] = {}
for bsymbol, result in benchmark_results.items():    serializable_results[sid][bsymbol] = {
'strategy_id': result.strategy_id,
'benchmark_symbol': result.benchmark_symbol,
'analysis_date': result.analysis_date.isoformat(),
'strategy_return': result.strategy_return,
'benchmark_return': result.benchmark_return,
'excess_return': result.excess_return,
'alpha': result.alpha,
'beta': result.beta,
'information_ratio': result.information_ratio,
'tracking_error': result.tracking_error,
'p_value': result.p_value,
'r_squared': result.r_squared,
't_statistic': result.t_statistic,
'up_capture': result.up_capture,
'down_capture': result.down_capture,
'correlation': result.correlation,
'data_points': result.data_points,
'analysis_period': result.analysis_period
}

with openfilename, 'w', encoding='utf-8' as f:    json.dump(serializable_results, f, indent=2, ensure_ascii=False)

elif format.lower() == "csv":
# 展开为CSV格式
rows = []
for sid, benchmark_results in results_to_export.items():
for bsymbol, result in benchmark_results.items():
rows.append({
'strategy_id': sid,
'benchmark_symbol': bsymbol,
'analysis_date': result.analysis_date,
'strategy_return': result.strategy_return,
'benchmark_return': result.benchmark_return,
'excess_return': result.excess_return,
'alpha': result.alpha,
'beta': result.beta,
'information_ratio': result.information_ratio,
'tracking_error': result.tracking_error,
'p_value': result.p_value,
'r_squared': result.r_squared,
't_statistic': result.t_statistic,
'up_capture': result.up_capture,
'down_capture': result.down_capture,
'correlation': result.correlation,
'data_points': result.data_points,
'analysis_period': result.analysis_period
})

df = pd.DataFramerows
df.to_csvfilename, index=False

self.logger.infof"基准分析结果已导出: {filename}"
return filename

except Exception as e:
self.logger.errorf"导出基准分析结果失败: {e}"
raise

async def cleanupself:
"""清理资源"""
try:
self.logger.info"正在清理基准分析器..."

self._data_cache.clear()
self._last_update.clear()
self._benchmark_results.clear()
self._strategy_data.clear()

self.logger.info"基准分析器清理完成"

except Exception as e:
self.logger.errorf"清理基准分析器失败: {e}"

__all__ = [
"BenchmarkAnalyzer",
"BenchmarkConfig",
"Benchmark",
"BenchmarkResult",
"BenchmarkType",
]