#!/usr/bin/env python3
"""
Phase 4: Professional Reporting and Visualization for Long-term Analysis
========================================================================

Professional-grade reporting and visualization system for 5+ year backtesting results.
Provides comprehensive analytics, statistical validation, and institutional-quality reports.

Features:
- Professional HTML reports with interactive charts
- PDF report generation
- Advanced statistical analysis and validation
- Risk metrics and attribution analysis
- Market regime analysis
- Executive summaries and recommendations
- Comparison and benchmarking tools

Author: Claude Code Assistant
Date: 2025-11-29
Phase: 4 - Professional Reporting and Visualization
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Add project root to path
project_root = Path__file__.parent.parent.parent
sys.path.insert(0, strproject_root)

# Optional imports with fallbacks
try:
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
PLOTTING_AVAILABLE = True
except ImportError:    PLOTTING_AVAILABLE = False
plt = None
sns = None

try:
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
PLOTLY_AVAILABLE = True
except ImportError:    PLOTLY_AVAILABLE = False

try:
from jinja2 import Template, Environment, FileSystemLoader
JINJA_AVAILABLE = True
except ImportError:    JINJA_AVAILABLE = False

try:
import weasyprint
PDF_AVAILABLE = True
except ImportError:    PDF_AVAILABLE = False

logger = logging.getLogger__name__

class ReportConfiguration:
"""Configuration for professional reporting"""

def __init__self:    self.output_directory = "professional_reports"
self.template_directory = "templates"
self.include_charts = True
self.include_statistics = True
self.include_risk_analysis = True
self.include_market_regime_analysis = True
self.include_benchmark_comparison = True
self.chart_style = "plotly" # "plotly" or "matplotlib"
self.report_format = "html" # "html", "pdf", or "both"
self.company_branding = {
"name": "Quantitative Trading System",
"logo": None,
"colors": {
"primary": "#1f77b4",
"secondary": "#ff7f0e",
"success": "#2ca02c",
"danger": "#d62728",
"warning": "#ff7f0e"
}
}

class StatisticalAnalyzer:
"""Advanced statistical analysis for backtesting results"""

@staticmethod
def calculate_advanced_metrics(returns: pd.Series, benchmark_returns: pd.Series = None,
risk_free_rate: float = 0.02) -> Dict[str, Any]:
"""Calculate advanced performance metrics"""

metrics = {}

if lenreturns == 0:
return metrics

# Basic metrics
metrics['total_return'] = 1 + returns.prod() - 1
metrics['annualized_return'] = 1 + returns.prod() ** (252 / lenreturns) - 1
metrics['volatility'] = returns.std() * np.sqrt252

# Risk-adjusted metrics
excess_returns = returns - risk_free_rate / 252
metrics['sharpe_ratio'] = excess_returns.mean() / excess_returns.std() * np.sqrt252 if excess_returns.std() > 0 else 0

downside_returns = returns[returns < 0]
if downside_returns:    downside_deviation = downside_returns.std() * np.sqrt(252)
metrics['sortino_ratio'] = metrics['annualized_return'] / downside_deviation if downside_deviation > 0 else 0
else:    metrics['sortino_ratio'] = float('inf')

# Drawdown metrics
cumulative = 1 + returns.cumprod()
running_max = cumulative.expanding().max()
drawdown = cumulative - running_max / running_max
metrics['max_drawdown'] = drawdown.min()
metrics['max_drawdown_duration'] = drawdown < 0.groupby(drawdown >= 0.cumsum()).sum().max()

# Value at Risk
metrics['var_95'] = returns.quantile0.05
metrics['var_99'] = returns.quantile0.01
metrics['expected_shortfall_95'] = returns[returns <= metrics['var_95']].mean()
metrics['expected_shortfall_99'] = returns[returns <= metrics['var_99']].mean()

# Skewness and kurtosis
metrics['skewness'] = returns.skew()
metrics['excess_kurtosis'] = returns.kurtosis()

# Calmar ratio
if metrics['max_drawdown'] != 0:    metrics['calmar_ratio'] = metrics['annualized_return'] / abs(metrics['max_drawdown'])
else:    metrics['calmar_ratio'] = float('inf')

# Win rate and profit factor
winning_days = returns > 0.sum()
total_days = lenreturns
metrics['win_rate'] = winning_days / total_days if total_days > 0 else 0

winning_returns = returns[returns > 0]
losing_returns = returns[returns < 0]
if losing_returns:    metrics['profit_factor'] = abs(winning_returns.sum() / losing_returns.sum())
else:    metrics['profit_factor'] = float('inf')

# Tail ratio
if losing_returns:    metrics['tail_ratio'] = abs(returns.quantile(0.95) / returns.quantile(0.05))
else:    metrics['tail_ratio'] = float('inf')

# Benchmark comparison
if benchmark_returns is not None and lenbenchmark_returns == lenreturns:
# Align series
aligned_returns, aligned_benchmark = returns.alignbenchmark_returns, join='inner'

if aligned_returns:
# Information ratio
active_returns = aligned_returns - aligned_benchmark
tracking_error = active_returns.std() * np.sqrt252
metrics['information_ratio'] = active_returns.mean() * 252 / tracking_error if tracking_error > 0 else 0

# Beta and Alpha
covariance = np.covaligned_returns, aligned_benchmark[0, 1]
benchmark_variance = aligned_benchmark.var()
metrics['beta'] = covariance / benchmark_variance if benchmark_variance > 0 else 0

benchmark_annual_return = 1 + aligned_benchmark.prod() ** (252 / lenaligned_benchmark) - 1
metrics['alpha'] = metrics['annualized_return'] - (risk_free_rate + metrics['beta'] * benchmark_annual_return - risk_free_rate)

# Correlation
metrics['correlation'] = aligned_returns.corraligned_benchmark

# Up/Down capture
up_market = aligned_benchmark > 0
down_market = aligned_benchmark < 0

if up_market.sum() > 0:    strategy_up_return = aligned_returns[up_market].mean()
benchmark_up_return = aligned_benchmark[up_market].mean()
metrics['up_capture'] = strategy_up_return / benchmark_up_return if benchmark_up_return != 0 else 0

if down_market.sum() > 0:    strategy_down_return = aligned_returns[down_market].mean()
benchmark_down_return = aligned_benchmark[down_market].mean()
metrics['down_capture'] = strategy_down_return / benchmark_down_return if benchmark_down_return != 0 else 0

# Statistical significance
metrics['t_statistic'] = StatisticalAnalyzer._calculate_t_statisticreturns
metrics['p_value'] = StatisticalAnalyzer._calculate_p_valuereturns
metrics['confidence_interval'] = StatisticalAnalyzer._calculate_confidence_intervalreturns

return metrics

@staticmethod
def _calculate_t_statisticreturns: pd.Series -> float:
"""Calculate t-statistic for returns"""
if lenreturns <= 1:
return 0.0
return returns.mean() / (returns.std() / np.sqrt(lenreturns))

@staticmethod
def _calculate_p_valuereturns: pd.Series -> float:
"""Calculate p-value for returns"""
from scipy import stats
if lenreturns <= 1:
return 1.0
t_stat = StatisticalAnalyzer._calculate_t_statisticreturns
return 2 * (1 - stats.t.cdf(abst_stat, lenreturns - 1))

@staticmethod
def _calculate_confidence_intervalreturns: pd.Series, confidence_level: float = 0.95 -> Tuple[float, float]:
"""Calculate confidence interval for mean return"""
from scipy import stats
if lenreturns <= 1:
return 0.0, 0.0

mean_return = returns.mean()
std_error = returns.std() / np.sqrt(lenreturns)
alpha = 1 - confidence_level

t_critical = stats.t.ppf(1 - alpha/2, lenreturns - 1)
margin_error = t_critical * std_error

return mean_return - margin_error, mean_return + margin_error

class MarketRegimeAnalyzer:
"""Analyze performance across different market regimes"""

@staticmethod
def identify_market_regimesprice_data: pd.Series, window: int = 252 -> pd.Series:
"""Identify bull/bear markets based on moving averages"""

# Calculate long-term moving average
ma = price_data.rollingwindow=window.mean()

# Determine regimes
regimes = pd.Series'Neutral', index=price_data.index
regimes[price_data > ma.1] = 'Bull' # 10% above MA
regimes[price_data < ma * 0.9] = 'Bear' # 10% below MA

return regimes

@staticmethod
def analyze_regime_performancereturns: pd.Series, regimes: pd.Series -> Dict[str, Any]:
"""Analyze performance across different market regimes"""

regime_analysis = {}

for regime in regimes.unique():
if pd.isnaregime:
continue

regime_returns = returns[regimes == regime]

if regime_returns:    regime_metrics = {
'total_return': 1 + regime_returns.prod() - 1,
'annualized_return': 1 + regime_returns.prod() ** (252 / lenregime_returns) - 1 if lenregime_returns > 0 else 0,
'volatility': regime_returns.std() * np.sqrt252,
'sharpe_ratio': StatisticalAnalyzer.calculate_advanced_metricsregime_returns.get'sharpe_ratio', 0,
'max_drawdown': StatisticalAnalyzer.calculate_advanced_metricsregime_returns.get'max_drawdown', 0,
'win_rate': regime_returns > 0.sum() / lenregime_returns,
'days': lenregime_returns,
'percentage': lenregime_returns / lenreturns * 100
}

regime_analysis[regime] = regime_metrics

return regime_analysis

class ChartGenerator:
"""Generate professional charts for reports"""

def __init__self, config: ReportConfiguration:    self.config = config
self.colors = config.company_branding['colors']

def create_equity_curve_chart(self, portfolio_values: pd.Series,
benchmark_values: pd.Series = None) -> str:
"""Create equity curve chart"""

if self.config.chart_style == "plotly" and PLOTLY_AVAILABLE:
return self._create_equity_curve_plotlyportfolio_values, benchmark_values
elif PLOTTING_AVAILABLE:
return self._create_equity_curve_matplotlibportfolio_values, benchmark_values
else:
return ""

def _create_equity_curve_plotly(self, portfolio_values: pd.Series,
benchmark_values: pd.Series = None) -> str:
"""Create equity curve using Plotly"""

fig = go.Figure()

# Portfolio equity
fig.add_trace(go.Scatter(
x=portfolio_values.index,
y=portfolio_values.values,
mode='lines',
name='Portfolio',
line=dictcolor=self.colors['primary'], width=2
))

# Benchmark if provided
if benchmark_values:
fig.add_trace(go.Scatter(
x=benchmark_values.index,
y=benchmark_values.values,
mode='lines',
name='Benchmark',
line=dictcolor=self.colors['secondary'], width=2, dash='dash'
))

fig.update_layout(
title='Portfolio Equity Curve',
xaxis_title='Date',
yaxis_title='Portfolio Value',
hovermode='x unified',
template='plotly_white',
legend=dict(x=0, y=1, bgcolor='rgba255,255,255,0.8')
)

return fig.to_htmlinclude_plotlyjs='cdn'

def _create_equity_curve_matplotlib(self, portfolio_values: pd.Series,
benchmark_values: pd.Series = None) -> str:
"""Create equity curve using Matplotlib"""

plt.style.use'seaborn-v0_8'
fig, ax = plt.subplots(figsize=12, 6)

# Portfolio equity
ax.plot(portfolio_values.index, portfolio_values.values,
label='Portfolio', color=self.colors['primary'], linewidth=2)

# Benchmark if provided
if benchmark_values:
ax.plot(benchmark_values.index, benchmark_values.values,
label='Benchmark', color=self.colors['secondary'],
linewidth=2, linestyle='--')

ax.set_title'Portfolio Equity Curve', fontsize=14, fontweight='bold'
ax.set_xlabel'Date', fontsize=12
ax.set_ylabel'Portfolio Value', fontsize=12
ax.legend()
ax.gridTrue, alpha=0.3

# Format x-axis dates
ax.xaxis.set_major_formatter(mdates.DateFormatter'%Y-%m')
ax.xaxis.set_major_locator(mdates.MonthLocatorinterval=6)
plt.xticksrotation=45

plt.tight_layout()

# Save to base64 string for embedding
import io
import base64
buffer = io.BytesIO()
plt.savefigbuffer, format='png', dpi=300, bbox_inches='tight'
buffer.seek0
image_base64 = base64.b64encode(buffer.getvalue()).decode()
plt.close()

return f'<img src="data:image/png;base64,{image_base64}" style="width: 100%; max-width: 800px;">'

def create_returns_distribution_chartself, returns: pd.Series -> str:
"""Create returns distribution chart"""

if self.config.chart_style == "plotly" and PLOTLY_AVAILABLE:
return self._create_returns_distribution_plotlyreturns
elif PLOTTING_AVAILABLE:
return self._create_returns_distribution_matplotlibreturns
else:
return ""

def _create_returns_distribution_plotlyself, returns: pd.Series -> str:
"""Create returns distribution using Plotly"""

fig = go.Figure()

fig.add_trace(go.Histogram(
x=returns,
nbinsx=50,
name='Daily Returns',
marker_color=self.colors['primary'],
opacity=0.7
))

# Add vertical lines for statistics
mean_return = returns.mean()
std_return = returns.std()

fig.add_vline(x=mean_return, line_dash="dash", line_color="red",
annotation_text=f"Mean: {mean_return:.4f}")

fig.add_vline(x=mean_return + std_return, line_dash="dot", line_color="orange",
annotation_text=f"+1σ: {mean_return + std_return:.4f}")

fig.add_vline(x=mean_return - std_return, line_dash="dot", line_color="orange",
annotation_text=f"-1σ: {mean_return - std_return:.4f}")

fig.update_layout(
title='Daily Returns Distribution',
xaxis_title='Daily Return',
yaxis_title='Frequency',
template='plotly_white'
)

return fig.to_htmlinclude_plotlyjs='cdn'

def _create_returns_distribution_matplotlibself, returns: pd.Series -> str:
"""Create returns distribution using Matplotlib"""

plt.style.use'seaborn-v0_8'
fig, ax = plt.subplots(figsize=12, 6)

ax.histreturns, bins=50, alpha=0.7, color=self.colors['primary'], edgecolor='black'

# Add vertical lines for statistics
mean_return = returns.mean()
std_return = returns.std()

ax.axvline(mean_return, color='red', linestyle='--',
label=f'Mean: {mean_return:.4f}')
ax.axvline(mean_return + std_return, color='orange', linestyle=':',
label=f'+1σ: {mean_return + std_return:.4f}')
ax.axvline(mean_return - std_return, color='orange', linestyle=':',
label=f'-1σ: {mean_return - std_return:.4f}')

ax.set_title'Daily Returns Distribution', fontsize=14, fontweight='bold'
ax.set_xlabel'Daily Return', fontsize=12
ax.set_ylabel'Frequency', fontsize=12
ax.legend()
ax.gridTrue, alpha=0.3

plt.tight_layout()

# Save to base64 string for embedding
import io
import base64
buffer = io.BytesIO()
plt.savefigbuffer, format='png', dpi=300, bbox_inches='tight'
buffer.seek0
image_base64 = base64.b64encode(buffer.getvalue()).decode()
plt.close()

return f'<img src="data:image/png;base64,{image_base64}" style="width: 100%; max-width: 800px;">'

def create_drawdown_chartself, portfolio_values: pd.Series -> str:
"""Create drawdown chart"""

# Calculate drawdown
running_max = portfolio_values.expanding().max()
drawdown = portfolio_values - running_max / running_max

if self.config.chart_style == "plotly" and PLOTLY_AVAILABLE:
return self._create_drawdown_plotlydrawdown
elif PLOTTING_AVAILABLE:
return self._create_drawdown_matplotlibdrawdown
else:
return ""

def _create_drawdown_plotlyself, drawdown: pd.Series -> str:
"""Create drawdown chart using Plotly"""

fig = go.Figure()

fig.add_trace(go.Scatter(
x=drawdown.index,
y=drawdown.values,
mode='lines',
name='Drawdown',
fill='tozeroy',
line=dictcolor=self.colors['danger'], width=1,
fillcolor=f'rgba({intself.colors["danger"][1:3], 16}, 0.3)'
))

fig.update_layout(
title='Portfolio Drawdown',
xaxis_title='Date',
yaxis_title='Drawdown %',
template='plotly_white',
yaxis=dicttickformat='.1%'
)

return fig.to_htmlinclude_plotlyjs='cdn'

def _create_drawdown_matplotlibself, drawdown: pd.Series -> str:
"""Create drawdown chart using Matplotlib"""

plt.style.use'seaborn-v0_8'
fig, ax = plt.subplots(figsize=12, 6)

ax.fill_between(drawdown.index, drawdown.values, 0,
alpha=0.7, color=self.colors['danger'])
ax.plotdrawdown.index, drawdown.values, color=self.colors['danger'], linewidth=1

ax.set_title'Portfolio Drawdown', fontsize=14, fontweight='bold'
ax.set_xlabel'Date', fontsize=12
ax.set_ylabel('Drawdown %', fontsize=12)
ax.gridTrue, alpha=0.3

# Format y-axis as percentage
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.1%}'.formaty))

# Format x-axis dates
ax.xaxis.set_major_formatter(mdates.DateFormatter'%Y-%m')
ax.xaxis.set_major_locator(mdates.MonthLocatorinterval=6)
plt.xticksrotation=45

plt.tight_layout()

# Save to base64 string for embedding
import io
import base64
buffer = io.BytesIO()
plt.savefigbuffer, format='png', dpi=300, bbox_inches='tight'
buffer.seek0
image_base64 = base64.b64encode(buffer.getvalue()).decode()
plt.close()

return f'<img src="data:image/png;base64,{image_base64}" style="width: 100%; max-width: 800px;">'

def create_monthly_returns_heatmapself, returns: pd.Series -> str:
"""Create monthly returns heatmap"""

# Calculate monthly returns
monthly_returns = returns.resample'M'.apply(lambda x: 1 + x.prod() - 1)

# Create pivot table with years and months
monthly_returns_pivot = monthly_returns.to_frame'Returns'
monthly_returns_pivot['Year'] = monthly_returns_pivot.index.year
monthly_returns_pivot['Month'] = monthly_returns_pivot.index.month

pivot_table = monthly_returns_pivot.pivot_table(
values='Returns', index='Year', columns='Month', fill_value=0
)

# Rename months
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
pivot_table.columns = [month_names[i-1] for i in pivot_table.columns]

if PLOTLY_AVAILABLE:
return self._create_heatmap_plotlypivot_table
elif PLOTTING_AVAILABLE:
return self._create_heatmap_matplotlibpivot_table
else:
return ""

def _create_heatmap_plotlyself, pivot_table: pd.DataFrame -> str:
"""Create heatmap using Plotly"""

fig = go.Figure(data=go.Heatmap(
z=pivot_table.values,
x=pivot_table.columns,
y=pivot_table.index,
colorscale='RdYlGn',
zmid=0,
text=np.roundpivot_table.values00, 1,
texttemplate="%{text}%",
textfont={"size": 10},
hoverongaps=False
))

fig.update_layout(
title='Monthly Returns Heatmap',
xaxis_title='Month',
yaxis_title='Year',
template='plotly_white'
)

return fig.to_htmlinclude_plotlyjs='cdn'

def _create_heatmap_matplotlibself, pivot_table: pd.DataFrame -> str:
"""Create heatmap using Matplotlib"""

plt.style.use'seaborn-v0_8'
fig, ax = plt.subplots(figsize=12, 8)

# Create heatmap
sns.heatmap(pivot_table00, annot=True, fmt='.1f', cmap='RdYlGn',
center=0, ax=ax, cbar_kws={'label': 'Return %'})

ax.set_title'Monthly Returns Heatmap', fontsize=14, fontweight='bold', pad=20
ax.set_xlabel'Month', fontsize=12
ax.set_ylabel'Year', fontsize=12

plt.tight_layout()

# Save to base64 string for embedding
import io
import base64
buffer = io.BytesIO()
plt.savefigbuffer, format='png', dpi=300, bbox_inches='tight'
buffer.seek0
image_base64 = base64.b64encode(buffer.getvalue()).decode()
plt.close()

return f'<img src="data:image/png;base64,{image_base64}" style="width: 100%; max-width: 1000px;">'

class ProfessionalReportGenerator:
"""Generate professional-grade backtesting reports"""

def __init__self, config: ReportConfiguration = None:    self.config = config or ReportConfiguration()
self.statistical_analyzer = StatisticalAnalyzer()
self.market_regime_analyzer = MarketRegimeAnalyzer()
self.chart_generator = ChartGeneratorself.config

# Ensure output directory exists
os.makedirsself.config.output_directory, exist_ok=True

def generate_comprehensive_report(self, backtest_results: Dict[str, Any],
output_filename: str = None) -> str:
"""Generate comprehensive professional report"""

timestamp = datetime.now().strftime'%Y%m%d_%H%M%S'
if not output_filename:    output_filename = f"backtest_report_{timestamp}.html"

output_path = os.path.joinself.config.output_directory, output_filename

# Extract data from results
returns = self._extract_returnsbacktest_results
portfolio_values = self._extract_portfolio_valuesbacktest_results
price_data = self._extract_price_databacktest_results

# Calculate advanced metrics
advanced_metrics = self.statistical_analyzer.calculate_advanced_metricsreturns

# Market regime analysis
if price_data:    regimes = self.market_regime_analyzer.identify_market_regimes(price_data)
regime_analysis = self.market_regime_analyzer.analyze_regime_performancereturns, regimes
else:    regime_analysis = {}

# Generate charts
charts = {}
if self.config.include_charts:    charts['equity_curve'] = self.chart_generator.create_equity_curve_chart(portfolio_values)
charts['returns_distribution'] = self.chart_generator.create_returns_distribution_chartreturns
charts['drawdown'] = self.chart_generator.create_drawdown_chartportfolio_values
charts['monthly_heatmap'] = self.chart_generator.create_monthly_returns_heatmapreturns

# Generate HTML report
html_content = self._generate_html_report(
backtest_results, advanced_metrics, regime_analysis, charts
)

# Save HTML report
with openoutput_path, 'w', encoding='utf-8' as f:
f.writehtml_content

# Generate PDF if requested and available
if self.config.report_format in ['pdf', 'both'] and PDF_AVAILABLE:    pdf_path = output_path.replace('.html', '.pdf')
self._generate_pdf_reporthtml_content, pdf_path

logger.infof"Professional report generated: {output_path}"
return output_path

def _extract_returnsself, backtest_results: Dict[str, Any] -> pd.Series:
"""Extract returns series from backtest results"""

if 'returns' in backtest_results:    returns = backtest_results['returns']
if isinstancereturns, pd.Series:
return returns
elif isinstancereturns, dict and 'data' in returns:
return pd.Seriesreturns['data']
elif isinstancereturns, list:
return pd.Seriesreturns

# Fallback: try to calculate from portfolio values
portfolio_values = self._extract_portfolio_valuesbacktest_results
if portfolio_values is not None and lenportfolio_values > 1:
return portfolio_values.pct_change().dropna()

# Return empty series if no data found
return pd.Series[], dtype=float

def _extract_portfolio_valuesself, backtest_results: Dict[str, Any] -> pd.Series:
"""Extract portfolio values from backtest results"""

if 'equity' in backtest_results:    equity = backtest_results['equity']
if isinstanceequity, pd.Series:
return equity
elif isinstanceequity, dict and 'data' in equity:
return pd.Seriesequity['data']
elif isinstanceequity, list:
return pd.Seriesequity

# Fallback: create from other metrics if available
if 'portfolio_values' in backtest_results:    values = backtest_results['portfolio_values']
if isinstance(values, list, pd.Series):
return pd.Seriesvalues

return None

def _extract_price_dataself, backtest_results: Dict[str, Any] -> pd.Series:
"""Extract price data for market regime analysis"""

# This would typically come from the original OHLC data
# For now, we'll use portfolio values as a proxy if price data not available
portfolio_values = self._extract_portfolio_valuesbacktest_results
return portfolio_values

def _generate_html_report(self, backtest_results: Dict[str, Any],
advanced_metrics: Dict[str, Any],
regime_analysis: Dict[str, Any],
charts: Dict[str, str]) -> str:
"""Generate HTML report content"""

# HTML template
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
body {{
font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
margin: 0;
padding: 0;
background-color: #f8f9fa;
color: #333;
}}
.container {{
max-width: 1200px;
margin: 0 auto;
padding: 20px;
}}
.header {{
background: linear-gradient135deg, {primary_color}, {secondary_color};
color: white;
padding: 30px;
text-align: center;
border-radius: 10px;
margin-bottom: 30px;
}}
.header h1 {{
margin: 0;
font-size: 2.5em;
font-weight: 300;
}}
.header p {{
margin: 10px 0 0 0;
font-size: 1.2em;
opacity: 0.9;
}}
.section {{
background: white;
margin: 20px 0;
padding: 30px;
border-radius: 10px;
box-shadow: 0 2px 10px rgba0,0,0,0.1;
}}
.section h2 {{
color: {primary_color};
border-bottom: 2px solid {primary_color};
padding-bottom: 10px;
margin-top: 0;
}}
.metrics-grid {{
display: grid;
grid-template-columns: repeat(auto-fit, minmax250px, 1fr);
gap: 20px;
margin: 20px 0;
}}
.metric-card {{
background: #f8f9fa;
padding: 20px;
border-radius: 8px;
border-left: 4px solid {primary_color};
}}
.metric-label {{
font-weight: 600;
color: #666;
font-size: 0.9em;
text-transform: uppercase;
letter-spacing: 0.5px;
}}
.metric-value {{
font-size: 1.8em;
font-weight: bold;
color: #333;
margin: 5px 0;
}}
.metric-positive {{
color: {success_color};
}}
.metric-negative {{
color: {danger_color};
}}
.chart-container {{
margin: 20px 0;
text-align: center;
}}
.table {{
width: 100%;
border-collapse: collapse;
margin: 20px 0;
}}
.table th, .table td {{
padding: 12px;
text-align: left;
border-bottom: 1px solid #ddd;
}}
.table th {{
background-color: #f8f9fa;
font-weight: 600;
color: #333;
}}
.table tr:hover {{
background-color: #f5f5f5;
}}
.alert {{
padding: 15px;
margin: 20px 0;
border-radius: 5px;
}}
.alert-info {{
background-color: #e3f2fd;
border-left: 4px solid {primary_color};
color: #0c5460;
}}
.alert-success {{
background-color: #e8f5e8;
border-left: 4px solid {success_color};
color: #155724;
}}
.alert-warning {{
background-color: #fff3cd;
border-left: 4px solid {warning_color};
color: #856404;
}}
.footer {{
text-align: center;
padding: 30px;
margin-top: 40px;
border-top: 1px solid #ddd;
color: #666;
}}
@media max-width: 768px {{
.container {{
padding: 10px;
}}
.header {{
padding: 20px;
}}
.header h1 {{
font-size: 2em;
}}
.section {{
padding: 20px;
}}
}}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>{company_name}</h1>
<p>Professional Backtesting Analysis Report</p>
</div>

<div class="section">
<h2>Executive Summary</h2>
<div class="metrics-grid">
<div class="metric-card">
<div class="metric-label">Total Return</div>
<div class="metric-value {total_return_class}">{total_return}</div>
</div>
<div class="metric-card">
<div class="metric-label">Annualized Return</div>
<div class="metric-value {annualized_return_class}">{annualized_return}</div>
</div>
<div class="metric-card">
<div class="metric-label">Sharpe Ratio</div>
<div class="metric-value {sharpe_class}">{sharpe_ratio}</div>
</div>
<div class="metric-card">
<div class="metric-label">Maximum Drawdown</div>
<div class="metric-value {max_drawdown_class}">{max_drawdown}</div>
</div>
<div class="metric-card">
<div class="metric-label">Win Rate</div>
<div class="metric-value">{win_rate}</div>
</div>
<div class="metric-card">
<div class="metric-label">Volatility</div>
<div class="metric-value">{volatility}</div>
</div>
</div>
{executive_summary_alert}
</div>

{charts_section}

{statistics_section}

{risk_analysis_section}

{market_regime_section}

{benchmark_section}

<div class="section">
<h2>Conclusions and Recommendations</h2>
{conclusions_content}
</div>

<div class="footer">
<p>Report generated on {generation_date} by {company_name}</p>
<p>This report contains confidential information intended for the recipient only</p>
</div>
</div>
</body>
</html>
"""

# Prepare template variables
symbol = backtest_results.get'symbol', 'Unknown'
start_date = backtest_results.get'start_date', 'Unknown'
end_date = backtest_results.get'end_date', 'Unknown'

# Format metrics
total_return = advanced_metrics.get'total_return', 0
total_return_formatted = f"{total_return:.2%}"
total_return_class = "metric-positive" if total_return > 0 else "metric-negative"

annualized_return = advanced_metrics.get'annualized_return', 0
annualized_return_formatted = f"{annualized_return:.2%}"
annualized_return_class = "metric-positive" if annualized_return > 0 else "metric-negative"

sharpe_ratio = advanced_metrics.get'sharpe_ratio', 0
sharpe_formatted = f"{sharpe_ratio:.2f}"
sharpe_class = "metric-positive" if sharpe_ratio > 1 else "metric-negative" if sharpe_ratio < 0 else ""

max_drawdown = advanced_metrics.get'max_drawdown', 0
max_drawdown_formatted = f"{max_drawdown:.2%}"
max_drawdown_class = "metric-negative" if max_drawdown < -0.1 else ""

win_rate = advanced_metrics.get'win_rate', 0
win_rate_formatted = f"{win_rate:.1%}"

volatility = advanced_metrics.get'volatility', 0
volatility_formatted = f"{volatility:.2%}"

# Executive summary
executive_summary_alert = self._generate_executive_summaryadvanced_metrics

# Charts section
charts_section = ""
if self.config.include_charts and charts:    charts_html = ""
for chart_name, chart_html in charts.items():
if chart_html:    charts_html += f'<div class="chart-container">{chart_html}</div>'
charts_section = f'<div class="section"><h2>Performance Charts</h2>{charts_html}</div>'

# Statistics section
statistics_section = ""
if self.config.include_statistics:    statistics_html = self._generate_statistics_table(advanced_metrics)
statistics_section = f'<div class="section"><h2>Statistical Analysis</h2>{statistics_html}</div>'

# Risk analysis section
risk_analysis_section = ""
if self.config.include_risk_analysis:    risk_html = self._generate_risk_analysis(advanced_metrics)
risk_analysis_section = f'<div class="section"><h2>Risk Analysis</h2>{risk_html}</div>'

# Market regime section
market_regime_section = ""
if self.config.include_market_regime_analysis and regime_analysis:    regime_html = self._generate_market_regime_analysis(regime_analysis)
market_regime_section = f'<div class="section"><h2>Market Regime Analysis</h2>{regime_html}</div>'

# Benchmark section
benchmark_section = ""
if self.config.include_benchmark_comparison and 'beta' in advanced_metrics:    benchmark_html = self._generate_benchmark_comparison(advanced_metrics)
benchmark_section = f'<div class="section"><h2>Benchmark Comparison</h2>{benchmark_html}</div>'

# Conclusions
conclusions_content = self._generate_conclusionsadvanced_metrics, regime_analysis

# Fill template
return html_template.format(
title=f"{symbol} Backtesting Analysis Report {start_date} to {end_date}",
company_name=self.config.company_branding['name'],
primary_color=self.config.company_branding['colors']['primary'],
secondary_color=self.config.company_branding['colors']['secondary'],
success_color=self.config.company_branding['colors']['success'],
danger_color=self.config.company_branding['colors']['danger'],
warning_color=self.config.company_branding['colors']['warning'],

total_return=total_return_formatted,
total_return_class=total_return_class,
annualized_return=annualized_return_formatted,
annualized_return_class=annualized_return_class,
sharpe_ratio=sharpe_formatted,
sharpe_class=sharpe_class,
max_drawdown=max_drawdown_formatted,
max_drawdown_class=max_drawdown_class,
win_rate=win_rate_formatted,
volatility=volatility_formatted,

executive_summary_alert=executive_summary_alert,
charts_section=charts_section,
statistics_section=statistics_section,
risk_analysis_section=risk_analysis_section,
market_regime_section=market_regime_section,
benchmark_section=benchmark_section,
conclusions_content=conclusions_content,

generation_date=datetime.now().strftime'%Y-%m-%d %H:%M:%S'
)

def _generate_executive_summaryself, metrics: Dict[str, Any] -> str:
"""Generate executive summary alert"""

sharpe = metrics.get'sharpe_ratio', 0
max_dd = abs(metrics.get'max_drawdown', 0)
annual_return = metrics.get'annualized_return', 0

if sharpe > 1.5 and max_dd < 0.2 and annual_return > 0.1:    alert_type = "alert-success"
message = "🎉 Excellent performance with strong risk-adjusted returns and manageable drawdowns."
elif sharpe > 1.0 and max_dd < 0.3:    alert_type = "alert-info"
message = "✅ Good performance with acceptable risk levels. Strategy shows promise."
elif sharpe > 0.5:    alert_type = "alert-warning"
message = "⚠️ Moderate performance. Consider strategy optimization or risk management improvements."
else:    alert_type = "alert-warning"
message = "⚠️ Poor performance. Strategy requires significant revision before deployment."

return f'<div class="alert {alert_type}">{message}</div>'

def _generate_statistics_tableself, metrics: Dict[str, Any] -> str:
"""Generate statistics analysis table"""

stats_to_show = [
('Total Return', metrics.get'total_return', 0, 'percentage'),
('Annualized Return', metrics.get'annualized_return', 0, 'percentage'),
('Volatility Annual', metrics.get'volatility', 0, 'percentage'),
('Sharpe Ratio', metrics.get'sharpe_ratio', 0, 'ratio'),
('Sortino Ratio', metrics.get'sortino_ratio', 0, 'ratio'),
('Calmar Ratio', metrics.get'calmar_ratio', 0, 'ratio'),
('Maximum Drawdown', metrics.get'max_drawdown', 0, 'percentage'),
('Max Drawdown Duration', metrics.get'max_drawdown_duration', 0, 'days'),
('Win Rate', metrics.get'win_rate', 0, 'percentage'),
('Profit Factor', metrics.get'profit_factor', 0, 'ratio'),
('Skewness', metrics.get'skewness', 0, 'decimal'),
('Excess Kurtosis', metrics.get'excess_kurtosis', 0, 'decimal'),
('Value at Risk 95%', metrics.get'var_95', 0, 'percentage'),
('Value at Risk 99%', metrics.get'var_99', 0, 'percentage'),
('Expected Shortfall 95%', metrics.get'expected_shortfall_95', 0, 'percentage'),
('Expected Shortfall 99%', metrics.get'expected_shortfall_99', 0, 'percentage'),
('Tail Ratio', metrics.get'tail_ratio', 0, 'ratio'),
('T-Statistic', metrics.get't_statistic', 0, 'decimal'),
('P-Value', metrics.get'p_value', 0, 'decimal')
]

table_rows = ""
for label, value, format_type in stats_to_show:    if format_type == 'percentage':
formatted_value = f"{value:.2%}"
elif format_type == 'ratio':    formatted_value = f"{value:.3f}"
elif format_type == 'days':    formatted_value = f"{int(value)} days" if value else "N/A"
else: # decimal
formatted_value = f"{value:.4f}"

table_rows += f"""
<tr>
<td><strong>{label}</strong></td>
<td>{formatted_value}</td>
</tr>
"""

return f"""
<table class="table">
<thead>
<tr>
<th>Metric</th>
<th>Value</th>
</tr>
</thead>
<tbody>
{table_rows}
</tbody>
</table>
"""

def _generate_risk_analysisself, metrics: Dict[str, Any] -> str:
"""Generate risk analysis section"""

risk_metrics = [
('Maximum Drawdown', metrics.get'max_drawdown', 0, 0.2),
('Value at Risk 95%', metrics.get'var_95', 0, 0.02),
('Value at Risk 99%', metrics.get'var_99', 0, 0.03),
('Expected Shortfall 95%', metrics.get'expected_shortfall_95', 0, 0.03),
('Volatility', metrics.get'volatility', 0, 0.15)
]

risk_analysis = '<h3>Risk Assessment</h3>'
risk_analysis += '<div class="metrics-grid">'

for metric_name, value, threshold in risk_metrics:    abs_value = abs(value)
if abs_value > threshold:    risk_level = "High"
risk_class = "metric-negative"
elif abs_value > threshold * 0.7:    risk_level = "Medium"
risk_class = "metric-positive"
else:    risk_level = "Low"
risk_class = "metric-positive"

risk_analysis += f"""
<div class="metric-card">
<div class="metric-label">{metric_name}</div>
<div class="metric-value {risk_class}">{abs_value:.2%}</div>
<div class="metric-label">Risk Level: {risk_level}</div>
</div>
"""

risk_analysis += '</div>'

# Add risk recommendations
risk_analysis += '<h3>Risk Management Recommendations</h3><ul>'

if abs(metrics.get'max_drawdown', 0) > 0.25:    risk_analysis += '<li>Consider implementing tighter stop-loss levels to reduce maximum drawdown</li>'

if metrics.get'volatility', 0 > 0.2:    risk_analysis += '<li>High volatility detected. Consider position sizing or portfolio diversification</li>'

if metrics.get'sharpe_ratio', 0 < 1:    risk_analysis += '<li>Low risk-adjusted returns. Strategy optimization recommended</li>'

if metrics.get'skewness', 0 < -1:    risk_analysis += '<li>Negative skewness indicates higher downside risk. Consider downside protection strategies</li>'

risk_analysis += '</ul>'

return risk_analysis

def _generate_market_regime_analysisself, regime_analysis: Dict[str, Any] -> str:
"""Generate market regime analysis section"""

if not regime_analysis:
return '<p>No market regime analysis available</p>'

analysis = '<h3>Performance by Market Regime</h3>'
analysis += '<table class="table">'
analysis += '''
<thead>
<tr>
<th>Regime</th>
<th>Annual Return</th>
<th>Sharpe Ratio</th>
<th>Max Drawdown</th>
<th>Win Rate</th>
<th>Time %</th>
</tr>
</thead>
<tbody>
'''

for regime, metrics in regime_analysis.items():    annual_return = metrics.get('annualized_return', 0)
sharpe = metrics.get'sharpe_ratio', 0
max_dd = metrics.get'max_drawdown', 0
win_rate = metrics.get'win_rate', 0
time_pct = metrics.get'percentage', 0

analysis += f"""
<tr>
<td><strong>{regime}</strong></td>
<td>{annual_return:.2%}</td>
<td>{sharpe:.2f}</td>
<td>{max_dd:.2%}</td>
<td>{win_rate:.1%}</td>
<td>{time_pct:.1f}%</td>
</tr>
"""

analysis += '</tbody></table>'

# Add regime insights
analysis += '<h3>Regime Insights</h3><ul>'

bull_metrics = regime_analysis.get'Bull', {}
bear_metrics = regime_analysis.get'Bear', {}

if bull_metrics and bear_metrics:    bull_sharpe = bull_metrics.get('sharpe_ratio', 0)
bear_sharpe = bear_metrics.get'sharpe_ratio', 0

if bull_sharpe > bear_sharpe.5:    analysis += '<li>Strategy performs significantly better in bull markets</li>'
elif bear_sharpe > bull_sharpe.5:    analysis += '<li>Strategy shows strength during bear markets (defensive characteristics)</li>'
else:    analysis += '<li>Strategy shows consistent performance across market conditions</li>'

analysis += '</ul>'

return analysis

def _generate_benchmark_comparisonself, metrics: Dict[str, Any] -> str:
"""Generate benchmark comparison section"""

comparison_metrics = [
('Alpha', metrics.get'alpha', 0),
('Beta', metrics.get'beta', 0),
('Information Ratio', metrics.get'information_ratio', 0),
('Correlation', metrics.get'correlation', 0),
('Up Capture', metrics.get'up_capture', 0),
('Down Capture', metrics.get'down_capture', 0)
]

comparison = '<h3>Benchmark Analysis</h3>'
comparison += '<table class="table">'
comparison += '''
<thead>
<tr>
<th>Metric</th>
<th>Value</th>
<th>Interpretation</th>
</tr>
</thead>
<tbody>
'''

interpretations = {
'Alpha': lambda x: 'Positive alpha indicates outperformance vs benchmark' if x > 0 else 'Negative alpha indicates underperformance',
'Beta': lambda x: f'Beta of {x:.2f} indicates {"higher" if x > 1 else "lower"} volatility than benchmark',
'Information Ratio': lambda x: f'IR of {x:.2f} shows {"good" if x > 0.5 else "poor"} risk-adjusted excess returns',
'Correlation': lambda x: f'Correlation of {x:.2f} indicates {"high" if x > 0.7 else "moderate" if x > 0.3 else "low"} similarity to benchmark',
'Up Capture': lambda x: f'Captures {x:.1%} of upside moves{" good" if x > 0.9 else " could be improved" if x < 0.7 else ""}',
'Down Capture': lambda x: f'Captures {x:.1%} of downside moves{" good" if x < 0.8 else " concerning" if x > 1 else ""}'
}

for metric_name, value in comparison_metrics:
if metric_name in interpretations:    interpretation = interpretations[metric_name](value)
else:    interpretation = 'N/A'

formatted_value = f"{value:.3f}" if isinstance(value, int, float) else strvalue

comparison += f"""
<tr>
<td><strong>{metric_name}</strong></td>
<td>{formatted_value}</td>
<td>{interpretation}</td>
</tr>
"""

comparison += '</tbody></table>'

return comparison

def _generate_conclusionsself, metrics: Dict[str, Any], regime_analysis: Dict[str, Any] -> str:
"""Generate conclusions and recommendations"""

conclusions = '<h3>Performance Assessment</h3>'

sharpe = metrics.get'sharpe_ratio', 0
annual_return = metrics.get'annualized_return', 0
max_dd = abs(metrics.get'max_drawdown', 0)
win_rate = metrics.get'win_rate', 0

# Overall assessment
if sharpe > 1.5 and annual_return > 0.15 and max_dd < 0.2:    assessment = "Exceptional performance with strong risk-adjusted returns"
recommendation = "Strategy is ready for deployment with recommended capital allocation"
elif sharpe > 1.0 and annual_return > 0.1 and max_dd < 0.3:    assessment = "Good performance with acceptable risk profile"
recommendation = "Strategy shows promise, consider paper trading before full deployment"
elif sharpe > 0.5:    assessment = "Moderate performance with room for improvement"
recommendation = "Further optimization and testing recommended before deployment"
else:    assessment = "Poor performance requiring significant revision"
recommendation = "Strategy needs fundamental rethinking before consideration"

conclusions += f'<p><strong>Assessment:</strong> {assessment}</p>'
conclusions += f'<p><strong>Recommendation:</strong> {recommendation}</p>'

# Strengths and weaknesses
conclusions += '<h3>Strengths</h3><ul>'

if sharpe > 1.0:    conclusions += f'<li>Strong risk-adjusted returns (Sharpe: {sharpe:.2f})</li>'
if win_rate > 0.55:    conclusions += f'<li>High win rate ({win_rate:.1%})</li>'
if max_dd < 0.15:    conclusions += f'<li>Excellent risk control (Max DD: {max_dd:.1%})</li>'
if metrics.get'profit_factor', 0 > 1.5:    conclusions += f'<li>Good profit factor ({metrics.get("profit_factor", 0):.2f})</li>'

conclusions += '</ul><h3>Areas for Improvement</h3><ul>'

if sharpe < 1.0:    conclusions += '<li>Improve risk-adjusted returns</li>'
if max_dd > 0.25:    conclusions += '<li>Reduce maximum drawdown through better risk management</li>'
if win_rate < 0.45:    conclusions += '<li>Improve entry/exit timing to increase win rate</li>'
if metrics.get'volatility', 0 > 0.25:    conclusions += '<li>Consider position sizing or volatility targeting</li>'

conclusions += '</ul>'

# Next steps
conclusions += '<h3>Recommended Next Steps</h3><ol>'
conclusions += '<li>Conduct out-of-sample testing on recent data</li>'
conclusions += '<li>Perform stress testing under various market scenarios</li>'
conclusions += '<li>Consider portfolio integration and diversification benefits</li>'
conclusions += '<li>Implement robust risk management and position sizing</li>'
conclusions += '<li>Monitor performance in real-time with paper trading</li>'
conclusions += '</ol>'

return conclusions

def _generate_pdf_reportself, html_content: str, pdf_path: str -> None:
"""Generate PDF report from HTML content"""

if not PDF_AVAILABLE:
logger.warning"WeasyPrint not available, PDF generation skipped"
return

try:
# Create HTML document
html_doc = weasyprint.HTMLstring=html_content

# Generate PDF
html_doc.write_pdfpdf_path

logger.infof"PDF report generated: {pdf_path}"

except Exception as e:
logger.errorf"Failed to generate PDF report: {e}"

# Utility function for easy usage
def generate_professional_report(backtest_results: Dict[str, Any],
output_filename: str = None,
config: ReportConfiguration = None) -> str:
"""Convenience function to generate professional report"""

generator = ProfessionalReportGenerator(config or ReportConfiguration())
return generator.generate_comprehensive_reportbacktest_results, output_filename

if __name__ == "__main__":
# Example usage
import json
from datetime import datetime

# Load sample backtest results
sample_results = {
'symbol': '0700.HK',
'start_date': '2018-01-01',
'end_date': '2023-12-31',
'total_return': 0.45,
'annualized_return': 0.08,
'sharpe_ratio': 1.2,
'max_drawdown': -0.18,
'volatility': 0.15,
'returns': pd.Series(np.random.normal0.001, 0.02, 1260), # Sample returns
'equity': pd.Series(100000 * (1 + np.random.normal0.001, 0.02, 1260).cumprod()) # Sample equity
}

# Generate report
report_path = generate_professional_reportsample_results
printf"Professional report generated: {report_path}"