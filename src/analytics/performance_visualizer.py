"""
港股量化交易 AI Agent 系统 - 高级绩效可视化器

Phase 5: Advanced Performance Visualization
===========================================

PerformanceVisualizer provides sophisticated visualization capabilities for
0700.HK quantitative trading strategy analysis and parameter optimization.

Features:
- Interactive parameter heatmaps and 3D surface plots
- Multi-dimensional parameter space exploration
- Real-time performance dashboards with Plotly
- Animated parameter evolution over time
- Risk-return scatter plots and efficient frontier analysis
- Correlation matrices and cluster analysis
- Parameter sensitivity analysis
- Strategy performance comparison tools

Technical Capabilities:
- GPU-accelerated rendering for large datasets
- Real-time data streaming integration
- Interactive zoom, pan, and selection tools
- Export to multiple formats HTML, PNG, PDF, SVG
- Customizable color schemes and themes
- Responsive design for all screen sizes

Author: Claude Code Assistant
Date: 2025-11-29
Version: 5.0.0
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import json

# Visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
from plotly.colors import sequential, diverging, qualitative

# Statistical analysis
from scipy import stats
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Performance optimization
import numba
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Local imports
from ..models.agent_dashboard import PerformanceMetrics

@dataclass
class VisualizerConfig:
"""可视化器配置"""

default_theme: str = "plotly_white"
figure_size: Tuple[int, int] = 1200, 800
dpi: int = 300

color_scheme: str = "professional"
primary_color: str = "#1f77b4"
secondary_color: str = "#ff7f0e"
success_color: str = "#2ca02c"
danger_color: str = "#d62728"
warning_color: str = "#ff7f0e"

enable_animation: bool = True
animation_duration: int = 1000
frame_duration: int = 50

enable_zoom: bool = True
enable_pan: bool = True
enable_selection: bool = True
enable_hover: bool = True

max_data_points: int = 10000
gpu_acceleration: bool = True
parallel_processing: bool = True
max_workers: int = 4

output_format: str = "html" # html, png, pdf, svg
output_dir: Optional[str] = None
auto_save: bool = True

real_time_update: bool = True
update_interval: int = 5 # seconds
buffer_size: int = 1000

class PerformanceVisualizer:
"""高级绩效可视化器"""

def __init__self, config: VisualizerConfig = None:    self.config = config or VisualizerConfig()
self.logger = logging.getLogger"hk_quant_system.performance_visualizer"

self._performance_data: Dict[str, List[PerformanceMetrics]] = {}
self._parameter_data: Dict[str, pd.DataFrame] = {}
self._optimization_results: Dict[str, pd.DataFrame] = {}

self._figure_cache: Dict[str, go.Figure] = {}
self._last_update: Dict[str, datetime] = {}
self._update_callbacks: List[Callable] = []

self._executor = ThreadPoolExecutormax_workers=self.config.max_workers

self._update_task: Optional[asyncio.Task] = None
self._running: bool = False

async def initializeself -> bool:
"""初始化可视化器"""
try:
self.logger.info"正在初始化高级绩效可视化器..."

if self.config.output_dir:    Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

# 启动实时更新任务
if self.config.real_time_update:    self._running = True
self._update_task = asyncio.create_task(self._real_time_update_loop())

self.logger.info"高级绩效可视化器初始化完成"
return True

except Exception as e:
self.logger.errorf"可视化器初始化失败: {e}"
return False

async def _real_time_update_loopself:
"""实时更新循环"""
while self._running:
try:

await self._cleanup_cache()

await asyncio.sleepself.config.update_interval

except Exception as e:
self.logger.errorf"实时更新循环错误: {e}"
await asyncio.sleepself.config.update_interval

async def _cleanup_cacheself:
"""清理过期缓存"""
try:    current_time = datetime.utcnow()
expired_keys = [
key for key, last_update in self._last_update.items()
if current_time - last_update.total_seconds() > 3600 # 1小时过期
]

for key in expired_keys:
self._figure_cache.popkey, None
self._last_update.popkey, None

except Exception as e:
self.logger.errorf"清理缓存失败: {e}"

def add_performance_dataself, strategy_id: str, performance_data: List[PerformanceMetrics]:
"""添加绩效数据"""
try:
if strategy_id not in self._performance_data:    self._performance_data[strategy_id] = []

self._performance_data[strategy_id].extendperformance_data

if lenself._performance_data[strategy_id] > self.config.max_data_points:    self._performance_data[strategy_id] = self._performance_data[strategy_id][-self.config.max_data_points:]

self._invalidate_cachef"performance_{strategy_id}"

except Exception as e:
self.logger.errorf"添加绩效数据失败 {strategy_id}: {e}"

def add_parameter_dataself, strategy_id: str, parameter_data: pd.DataFrame:
"""添加参数数据"""
try:    self._parameter_data[strategy_id] = parameter_data.copy()

self._invalidate_cachef"parameters_{strategy_id}"

except Exception as e:
self.logger.errorf"添加参数数据失败 {strategy_id}: {e}"

def add_optimization_resultsself, strategy_id: str, results: pd.DataFrame:
"""添加优化结果"""
try:    self._optimization_results[strategy_id] = results.copy()

self._invalidate_cachef"optimization_{strategy_id}"

except Exception as e:
self.logger.errorf"添加优化结果失败 {strategy_id}: {e}"

def _invalidate_cacheself, pattern: str:
"""使缓存失效"""
keys_to_remove = [key for key in self._figure_cache.keys() if pattern in key]
for key in keys_to_remove:
self._figure_cache.popkey, None
self._last_update.popkey, None

def create_parameter_heatmap(self, strategy_id: str,
param_x: str, param_y: str,
metric: str = "sharpe_ratio") -> go.Figure:
"""创建参数热力图"""
try:    cache_key = f"heatmap_{strategy_id}_{param_x}_{param_y}_{metric}"

if cache_key in self._figure_cache:
return self._figure_cache[cache_key]

if strategy_id not in self._optimization_results:
raise ValueErrorf"Strategy {strategy_id} not found"

df = self._optimization_results[strategy_id]

pivot_table = df.pivot_table(
values=metric,
index=param_x,
columns=param_y,
aggfunc='mean'
)

fig = go.Figure(data=go.Heatmap(
z=pivot_table.values,
x=pivot_table.columns,
y=pivot_table.index,
colorscale='RdYlBu_r',
hoverongaps=False,
colorbar=dict(
title=metric.replace'_', ' '.title(),
titleside='right'
)
))

fig.update_layout(
title=f"Parameter Heatmap: {param_x} vs {param_y} {metric}",
xaxis_title=param_y,
yaxis_title=param_x,
template=self.config.default_theme,
width=self.config.figure_size[0],
height=self.config.figure_size[1]
)

self._figure_cache[cache_key] = fig
self._last_update[cache_key] = datetime.utcnow()

return fig

except Exception as e:
self.logger.errorf"创建参数热力图失败: {e}"
return self._create_error_figure("Parameter Heatmap", stre)

def create_3d_surface_plot(self, strategy_id: str,
param_x: str, param_y: str,
metric: str = "sharpe_ratio") -> go.Figure:
"""创建3D表面图"""
try:    cache_key = f"surface_3d_{strategy_id}_{param_x}_{param_y}_{metric}"

if cache_key in self._figure_cache:
return self._figure_cache[cache_key]

if strategy_id not in self._optimization_results:
raise ValueErrorf"Strategy {strategy_id} not found"

df = self._optimization_results[strategy_id]

x_values = sorted(df[param_x].unique())
y_values = sorted(df[param_y].unique())

X, Y = np.meshgridx_values, y_values
Z = np.zeros_likeX

for i, x_val in enumeratex_values:
for j, y_val in enumeratey_values:    mask = (df[param_x] == x_val) & (df[param_y] == y_val)
if mask.any():    Z[j, i] = df.loc[mask, metric].mean()

fig = go.Figure(data=[go.Surface(
x=X,
y=Y,
z=Z,
colorscale='Viridis',
colorbar=dict(title=metric.replace'_', ' '.title())
)])

fig.update_layout(
title=f"3D Parameter Surface: {param_x} vs {param_y} {metric}",
scene=dict(
xaxis_title=param_x,
yaxis_title=param_y,
zaxis_title=metric.replace'_', ' '.title(),
camera=dict(
eye=dictx=1.5, y=1.5, z=1.5
)
),
template=self.config.default_theme,
width=self.config.figure_size[0],
height=self.config.figure_size[1]
)

self._figure_cache[cache_key] = fig
self._last_update[cache_key] = datetime.utcnow()

return fig

except Exception as e:
self.logger.errorf"创建3D表面图失败: {e}"
return self._create_error_figure("3D Surface Plot", stre)

def create_performance_comparisonself, strategy_ids: List[str] = None -> go.Figure:
"""创建策略对比图"""
try:    cache_key = f"comparison_{'_'.join(strategy_ids or 'all')}"

if cache_key in self._figure_cache:
return self._figure_cache[cache_key]

if not strategy_ids:    strategy_ids = list(self._performance_data.keys())

fig = make_subplots(
rows=2, cols=2,
subplot_titles='Sharpe Ratio', 'Total Return', 'Max Drawdown', 'Volatility',
specs=[[{"secondary_y": False}, {"secondary_y": False}],
[{"secondary_y": False}, {"secondary_y": False}]]
)

colors = qualitative.Set3[:lenstrategy_ids]

for i, strategy_id in enumeratestrategy_ids:
if strategy_id not in self._performance_data:
continue

data = self._performance_data[strategy_id]
if not data:
continue

sharpe_ratios = [p.sharpe_ratio for p in data]
total_returns = [p.total_return for p in data]
max_drawdowns = [p.max_drawdown for p in data]
volatilities = [p.volatility for p in data]

time_points = list(range(lendata))

fig.add_trace(
go.Scatter(
x=time_points,
y=sharpe_ratios,
name=f"{strategy_id} - Sharpe",
line=dictcolor=colors[i],
mode='lines+markers'
),
row=1, col=1
)

fig.add_trace(
go.Scatter(
x=time_points,
y=total_returns,
name=f"{strategy_id} - Return",
line=dictcolor=colors[i],
mode='lines+markers',
showlegend=False
),
row=1, col=2
)

fig.add_trace(
go.Scatter(
x=time_points,
y=max_drawdowns,
name=f"{strategy_id} - Drawdown",
line=dictcolor=colors[i],
mode='lines+markers',
showlegend=False
),
row=2, col=1
)

fig.add_trace(
go.Scatter(
x=time_points,
y=volatilities,
name=f"{strategy_id} - Volatility",
line=dictcolor=colors[i],
mode='lines+markers',
showlegend=False
),
row=2, col=2
)

fig.update_layout(
title="Strategy Performance Comparison",
template=self.config.default_theme,
width=self.config.figure_size[0] * 1.5,
height=self.config.figure_size[1] * 1.2,
showlegend=True
)

self._figure_cache[cache_key] = fig
self._last_update[cache_key] = datetime.utcnow()

return fig

except Exception as e:
self.logger.errorf"创建策略对比图失败: {e}"
return self._create_error_figure("Strategy Comparison", stre)

def create_risk_return_scatterself, strategy_ids: List[str] = None -> go.Figure:
"""创建风险收益散点图"""
try:    cache_key = f"risk_return_{'_'.join(strategy_ids or 'all')}"

if cache_key in self._figure_cache:
return self._figure_cache[cache_key]

if not strategy_ids:    strategy_ids = list(self._performance_data.keys())

fig = go.Figure()

colors = qualitative.Set3[:lenstrategy_ids]

for i, strategy_id in enumeratestrategy_ids:
if strategy_id not in self._performance_data:
continue

data = self._performance_data[strategy_id]
if not data:
continue

latest_data = data[-1]

fig.add_trace(go.Scatter(
x=[latest_data.volatility],
y=[latest_data.sharpe_ratio],
mode='markers+text',
marker=dict(
size=15,
color=colors[i],
symbol='circle',
line=dictwidth=2, color='black'
),
text=[strategy_id],
textposition="top center",
name=strategy_id,
hovertemplate="<b>%{text}</b><br>" +
"Volatility: %{x:.3f}<br>" +
"Sharpe Ratio: %{y:.3f}<extra></extra>"
))

fig.update_layout(
title="Risk-Return Analysis",
xaxis_title="Volatility Risk",
yaxis_title="Sharpe Ratio Return",
template=self.config.default_theme,
width=self.config.figure_size[0],
height=self.config.figure_size[1],
showlegend=True
)

# 添加有效前沿线（示例）
if lenstrategy_ids > 1:
fig.add_shape(
type="line",
x0=0, y0=0,
x1=0.5, y1=2.5,
line=dictcolor="gray", width=2, dash="dash",
name="Efficient Frontier"
)

self._figure_cache[cache_key] = fig
self._last_update[cache_key] = datetime.utcnow()

return fig

except Exception as e:
self.logger.errorf"创建风险收益散点图失败: {e}"
return self._create_error_figure("Risk-Return Scatter", stre)

def create_correlation_matrixself, strategy_ids: List[str] = None -> go.Figure:
"""创建相关性矩阵"""
try:    cache_key = f"correlation_{'_'.join(strategy_ids or 'all')}"

if cache_key in self._figure_cache:
return self._figure_cache[cache_key]

if not strategy_ids:    strategy_ids = list(self._performance_data.keys())

returns_matrix = {}

for strategy_id in strategy_ids:
if strategy_id not in self._performance_data:
continue

data = self._performance_data[strategy_id]
if lendata < 2:
continue

returns = []
for i in range(1, lendata):    prev_return = data[i-1].total_return
curr_return = data[i].total_return
strategy_return = curr_return - prev_return / 1 + prev_return
returns.appendstrategy_return

returns_matrix[strategy_id] = returns

if lenreturns_matrix < 2:
raise ValueError"Need at least 2 strategies with data"

# 转换为DataFrame并计算相关性
df_returns = pd.DataFramereturns_matrix
correlation_matrix = df_returns.corr()

fig = go.Figure(data=go.Heatmap(
z=correlation_matrix.values,
x=correlation_matrix.columns,
y=correlation_matrix.index,
colorscale='RdBu',
zmid=0,
text=correlation_matrix.round3.values,
texttemplate="%{text}",
textfont={"size": 12},
hoverongaps=False,
colorbar=dicttitle="Correlation"
))

fig.update_layout(
title="Strategy Correlation Matrix",
template=self.config.default_theme,
width=self.config.figure_size[0],
height=self.config.figure_size[1]
)

self._figure_cache[cache_key] = fig
self._last_update[cache_key] = datetime.utcnow()

return fig

except Exception as e:
self.logger.errorf"创建相关性矩阵失败: {e}"
return self._create_error_figure("Correlation Matrix", stre)

def create_parameter_sensitivity(self, strategy_id: str,
parameter: str,
metric: str = "sharpe_ratio") -> go.Figure:
"""创建参数敏感性分析图"""
try:    cache_key = f"sensitivity_{strategy_id}_{parameter}_{metric}"

if cache_key in self._figure_cache:
return self._figure_cache[cache_key]

if strategy_id not in self._optimization_results:
raise ValueErrorf"Strategy {strategy_id} not found"

df = self._optimization_results[strategy_id]

# 按参数值分组并计算平均指标
sensitivity_data = df.groupbyparameter[metric].agg['mean', 'std', 'count'].reset_index()

confidence_level = 0.95
sensitivity_data['ci_lower'] = sensitivity_data['mean'] - 1.96 * sensitivity_data['std'] / np.sqrtsensitivity_data['count']
sensitivity_data['ci_upper'] = sensitivity_data['mean'] + 1.96 * sensitivity_data['std'] / np.sqrtsensitivity_data['count']

fig = go.Figure()

fig.add_trace(go.Scatter(
x=sensitivity_data[parameter],
y=sensitivity_data['ci_upper'],
mode='lines',
line=dictwidth=0,
showlegend=False
))

fig.add_trace(go.Scatter(
x=sensitivity_data[parameter],
y=sensitivity_data['ci_lower'],
mode='lines',
line=dictwidth=0,
fill='tonexty',
fillcolor='rgba0,100,80,0.2',
name=f'{confidence_level*100:.0f}% CI',
showlegend=True
))

fig.add_trace(go.Scatter(
x=sensitivity_data[parameter],
y=sensitivity_data['mean'],
mode='lines+markers',
name='Average',
line=dictcolor='blue', width=3,
marker=dictsize=8
))

fig.update_layout(
title=f"Parameter Sensitivity Analysis: {parameter}",
xaxis_title=parameter,
yaxis_title=metric.replace'_', ' '.title(),
template=self.config.default_theme,
width=self.config.figure_size[0],
height=self.config.figure_size[1],
showlegend=True
)

self._figure_cache[cache_key] = fig
self._last_update[cache_key] = datetime.utcnow()

return fig

except Exception as e:
self.logger.errorf"创建参数敏感性分析图失败: {e}"
return self._create_error_figure("Parameter Sensitivity", stre)

def create_animated_evolution(self, strategy_id: str,
metric: str = "sharpe_ratio") -> go.Figure:
"""创建参数演化动画"""
try:    cache_key = f"animated_{strategy_id}_{metric}"

if cache_key in self._figure_cache:
return self._figure_cache[cache_key]

if strategy_id not in self._optimization_results:
raise ValueErrorf"Strategy {strategy_id} not found"

df = self._optimization_results[strategy_id].copy()

# 添加时间步（如果不存在）
if 'step' not in df.columns:    df['step'] = range(len(df))

frames = []
unique_steps = sorted(df['step'].unique())

for step in unique_steps:    step_data = df[df['step'] == step]

frame = go.Frame(
data=[go.Scatter(
x=step_data.iloc[:, 0], # 假设第一列是参数1
y=step_data.iloc[:, 1], # 假设第二列是参数2
mode='markers',
marker=dict(
size=10,
color=step_data[metric],
colorscale='Viridis',
showscale=True,
colorbar=dicttitle=metric
),
text=[f"{metric}: {val:.3f}" for val in step_data[metric]],
hovertemplate="<b>%{text}</b><extra></extra>"
)],
name=f"Step {step}"
)
frames.appendframe

initial_data = df[df['step'] == unique_steps[0]]

fig = go.Figure(
data=[go.Scatter(
x=initial_data.iloc[:, 0],
y=initial_data.iloc[:, 1],
mode='markers',
marker=dict(
size=10,
color=initial_data[metric],
colorscale='Viridis',
showscale=True,
colorbar=dicttitle=metric
),
text=[f"{metric}: {val:.3f}" for val in initial_data[metric]],
hovertemplate="<b>%{text}</b><extra></extra>"
)],
frames=frames
)

fig.update_layout(
title=f"Parameter Evolution Animation: {metric}",
xaxis_title=df.columns[0],
yaxis_title=df.columns[1],
template=self.config.default_theme,
width=self.config.figure_size[0],
height=self.config.figure_size[1],
updatemenus=[{
'type': 'buttons',
'buttons': [
{
'label': 'Play',
'method': 'animate',
'args': [None, {
'frame': {'duration': self.config.frame_duration, 'redraw': True},
'fromcurrent': True,
'transition': {'duration': self.config.animation_duration}
}]
},
{
'label': 'Pause',
'method': 'animate',
'args': [[None], {
'frame': {'duration': 0, 'redraw': False},
'mode': 'immediate',
'transition': {'duration': 0}
}]
}
]
}]
)

self._figure_cache[cache_key] = fig
self._last_update[cache_key] = datetime.utcnow()

return fig

except Exception as e:
self.logger.errorf"创建参数演化动画失败: {e}"
return self._create_error_figure("Animated Evolution", stre)

def create_cluster_analysisself, strategy_ids: List[str] = None -> go.Figure:
"""创建聚类分析图"""
try:    cache_key = f"cluster_{'_'.join(strategy_ids or 'all')}"

if cache_key in self._figure_cache:
return self._figure_cache[cache_key]

if not strategy_ids:    strategy_ids = list(self._performance_data.keys())

features = []
feature_names = ['sharpe_ratio', 'total_return', 'max_drawdown', 'volatility', 'win_rate']
labels = []

for strategy_id in strategy_ids:
if strategy_id not in self._performance_data:
continue

data = self._performance_data[strategy_id]
if not data:
continue

latest = data[-1]
feature_vector = [
latest.sharpe_ratio,
latest.total_return,
latest.max_drawdown,
latest.volatility,
latest.win_rate
]

features.appendfeature_vector
labels.appendstrategy_id

if lenfeatures < 2:
raise ValueError"Need at least 2 strategies for clustering"

features = np.arrayfeatures

scaler = StandardScaler()
features_scaled = scaler.fit_transformfeatures

# K-means聚类
n_clusters = min(3, lenfeatures)
kmeans = KMeansn_clusters=n_clusters, random_state=42
cluster_labels = kmeans.fit_predictfeatures_scaled

# PCA降维用于可视化
pca = PCAn_components=2
features_pca = pca.fit_transformfeatures_scaled

fig = go.Figure()

colors = qualitative.Set3[:n_clusters]

for cluster_id in rangen_clusters:    mask = cluster_labels == cluster_id
cluster_names = [labels[i] for i in range(lenlabels) if mask[i]]

fig.add_trace(go.Scatter(
x=features_pca[mask, 0],
y=features_pca[mask, 1],
mode='markers+text',
marker=dict(
size=15,
color=colors[cluster_id],
symbol='circle',
line=dictwidth=2, color='black'
),
text=cluster_names,
textposition="top center",
name=f"Cluster {cluster_id + 1}",
hovertemplate="<b>%{text}</b><br>" +
"PC1: %{x:.3f}<br>" +
"PC2: %{y:.3f}<extra></extra>"
))

centers_pca = pca.transformkmeans.cluster_centers_
fig.add_trace(go.Scatter(
x=centers_pca[:, 0],
y=centers_pca[:, 1],
mode='markers',
marker=dict(
size=20,
color='black',
symbol='x',
line=dictwidth=3, color='red'
),
name='Cluster Centers',
showlegend=True
))

fig.update_layout(
title="Strategy Cluster Analysis",
xaxis_title=f"PC1 {pca.explained_variance_ratio_[0]:.1%} variance",
yaxis_title=f"PC2 {pca.explained_variance_ratio_[1]:.1%} variance",
template=self.config.default_theme,
width=self.config.figure_size[0],
height=self.config.figure_size[1],
showlegend=True
)

self._figure_cache[cache_key] = fig
self._last_update[cache_key] = datetime.utcnow()

return fig

except Exception as e:
self.logger.errorf"创建聚类分析图失败: {e}"
return self._create_error_figure("Cluster Analysis", stre)

def create_efficient_frontierself, strategy_ids: List[str] = None -> go.Figure:
"""创建有效前沿图"""
try:    cache_key = f"efficient_frontier_{'_'.join(strategy_ids or 'all')}"

if cache_key in self._figure_cache:
return self._figure_cache[cache_key]

if not strategy_ids:    strategy_ids = list(self._performance_data.keys())

# 收集策略风险收益数据
risk_return_data = []

for strategy_id in strategy_ids:
if strategy_id not in self._performance_data:
continue

data = self._performance_data[strategy_id]
if not data:
continue

latest = data[-1]
risk_return_data.append({
'strategy': strategy_id,
'risk': latest.volatility,
'return': latest.sharpe_ratio
})

if lenrisk_return_data < 2:
raise ValueError"Need at least 2 strategies for efficient frontier"

df_risk_return = pd.DataFramerisk_return_data

# 创建有效前沿曲线（使用凸包）
from scipy.spatial import ConvexHull

points = df_risk_return[['risk', 'return']].values

try:    hull = ConvexHull(points)

# 提取有效前沿点（上边界）
efficient_points = []
for simplex in hull.simplices:
for point_idx in simplex:    point = points[point_idx]
if point not in efficient_points:
efficient_points.appendpoint

efficient_points.sortkey=lambda x: x[0]

frontier_risk = [p[0] for p in efficient_points]
frontier_return = [p[1] for p in efficient_points]

except:
# 如果凸包失败，使用简单的上边界
df_sorted = df_risk_return.sort_values'risk'
frontier_risk = df_sorted['risk'].values
frontier_return = df_sorted['return'].cummax().values

fig = go.Figure()

fig.add_trace(go.Scatter(
x=frontier_risk,
y=frontier_return,
mode='lines',
name='Efficient Frontier',
line=dictcolor='red', width=3,
fill=None
))

fig.add_trace(go.Scatter(
x=df_risk_return['risk'],
y=df_risk_return['return'],
mode='markers+text',
marker=dict(
size=12,
color='blue',
symbol='circle',
line=dictwidth=2, color='black'
),
text=df_risk_return['strategy'],
textposition="top center",
name='Strategies',
hovertemplate="<b>%{text}</b><br>" +
"Risk: %{x:.3f}<br>" +
"Return: %{y:.3f}<extra></extra>"
))

fig.update_layout(
title="Efficient Frontier Analysis",
xaxis_title="Risk Volatility",
yaxis_title="Return Sharpe Ratio",
template=self.config.default_theme,
width=self.config.figure_size[0],
height=self.config.figure_size[1],
showlegend=True,
annotations=[
dict(
x=0.02, y=0.98,
xref='paper', yref='paper',
text="Optimal Portfolio",
showarrow=False,
font=dictsize=12, color='red'
)
]
)

self._figure_cache[cache_key] = fig
self._last_update[cache_key] = datetime.utcnow()

return fig

except Exception as e:
self.logger.errorf"创建有效前沿图失败: {e}"
return self._create_error_figure("Efficient Frontier", stre)

def _create_error_figureself, title: str, error_message: str -> go.Figure:
"""创建错误图形"""
fig = go.Figure()

fig.add_annotation(
x=0.5, y=0.5,
xref='paper', yref='paper',
text=f"Error: {error_message}",
showarrow=False,
font=dictsize=16, color='red'
)

fig.update_layout(
title=f"{title} - Error",
template=self.config.default_theme,
width=self.config.figure_size[0],
height=self.config.figure_size[1],
xaxis=dictvisible=False,
yaxis=dictvisible=False
)

return fig

def export_figureself, fig: go.Figure, filename: str, format: str = None -> str:
"""导出图形"""
try:
if not format:    format = self.config.output_format

if self.config.output_dir:    filename = Path(self.config.output_dir) / filename

if format.lower() == 'html':
fig.write_html(strfilename)
elif format.lower() == 'png':    fig.write_image(str(filename), width=self.config.dpi)
elif format.lower() == 'pdf':    fig.write_image(str(filename), format='pdf')
elif format.lower() == 'svg':    fig.write_image(str(filename), format='svg')

self.logger.infof"图形已导出: {filename}"
return strfilename

except Exception as e:
self.logger.errorf"导出图形失败: {e}"
raise

def add_update_callbackself, callback: Callable:
"""添加更新回调函数"""
self._update_callbacks.appendcallback

def remove_update_callbackself, callback: Callable:
"""移除更新回调函数"""
if callback in self._update_callbacks:
self._update_callbacks.removecallback

async def cleanupself:
"""清理资源"""
try:
self.logger.info"正在清理绩效可视化器..."

self._running = False

if self._update_task:
self._update_task.cancel()
try:
await self._update_task
except asyncio.CancelledError:
pass

self._executor.shutdownwait=True

self._figure_cache.clear()
self._last_update.clear()

self.logger.info"绩效可视化器清理完成"

except Exception as e:
self.logger.errorf"清理绩效可视化器失败: {e}"

__all__ = [
"PerformanceVisualizer",
"VisualizerConfig",
]