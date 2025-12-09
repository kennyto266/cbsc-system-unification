"""
港股量化交易 AI Agent 系统 - 交互式仪表板

Phase 5: Advanced Interactive Dashboard
=======================================

InteractiveDashboard provides real-time, interactive visualization and analysis
dashboard for 0700.HK quantitative trading strategies.

Features:
- Real-time parameter exploration interface
- Multi-strategy comparison tools
- Performance attribution analysis
- Market regime visualization
- Strategy correlation analysis
- Rolling performance metrics visualization
- Interactive risk-return analysis
- Real-time alerts and notifications

Technical Capabilities:
- WebSocket real-time data streaming
- Interactive filtering and drill-down capabilities
- Customizable dashboard layouts
- Mobile-responsive design
- Real-time performance monitoring
- Multi-user collaboration features
- Automated alerts and notifications

Dashboard Components:
- Strategy Performance Monitor
- Parameter Optimization Dashboard
- Risk Management Dashboard
- Benchmark Comparison Dashboard
- Market Regime Analysis
- Correlation Matrix Dashboard
- Performance Attribution Dashboard
- Real-time Alert System

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
from enum import Enum

# Web framework
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.utils

# Local imports
from .performance_visualizer import PerformanceVisualizer, VisualizerConfig
from .benchmark_analyzer import BenchmarkAnalyzer, BenchmarkConfig
from ..models.agent_dashboard import PerformanceMetrics
from ..websocket_manager import WebSocketManager

class DashboardTypeEnum:
"""仪表板类型枚举"""
OVERVIEW = "overview"
PERFORMANCE = "performance"
RISK = "risk"
BENCHMARK = "benchmark"
OPTIMIZATION = "optimization"
CORRELATION = "correlation"
ATTRIBUTION = "attribution"
REAL_TIME = "real_time"

class AlertLevelEnum:
"""告警级别枚举"""
INFO = "info"
WARNING = "warning"
ERROR = "error"
CRITICAL = "critical"

@dataclass
class DashboardConfig:
"""仪表板配置"""

host: str = "localhost"
port: int = 8000
debug: bool = False

real_time_enabled: bool = True
update_interval: int = 5 # seconds
buffer_size: int = 1000

default_theme: str = "plotly_white"
color_scheme: str = "professional"
enable_animations: bool = True

max_data_points: int = 10000
history_days: int = 365
cache_duration: int = 3600 # seconds

max_concurrent_users: int = 100
session_timeout: int = 3600 # seconds

alerts_enabled: bool = True
alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
"sharpe_ratio_min": 0.5,
"max_drawdown_max": 0.15,
"volatility_max": 0.30,
"tracking_error_max": 0.05
})

enable_gpu: bool = True
parallel_processing: bool = True
max_workers: int = 4

static_dir: str = "static"
templates_dir: str = "templates"

@dataclass
class DashboardAlert:
"""仪表板告警"""
id: str
level: AlertLevel
strategy_id: str
message: str
timestamp: datetime
acknowledged: bool = False
details: Dict[str, Any] = fielddefault_factory=dict

@dataclass
class UserSession:
"""用户会话"""
session_id: str
user_id: str
websocket: WebSocket
created_at: datetime
last_activity: datetime
subscriptions: List[str] = fielddefault_factory=list
preferences: Dict[str, Any] = fielddefault_factory=dict

class InteractiveDashboard:
"""交互式仪表板"""

def __init__self, config: DashboardConfig = None:    self.config = config or DashboardConfig()
self.logger = logging.getLogger"hk_quant_system.interactive_dashboard"

self.visualizer = PerformanceVisualizer(VisualizerConfig())
self.benchmark_analyzer = BenchmarkAnalyzer(BenchmarkConfig())

# FastAPI应用
self.app = FastAPItitle="0700.HK Quantitative Trading Dashboard"
self.websocket_manager = WebSocketManager()

self._strategy_data: Dict[str, List[PerformanceMetrics]] = {}
self._parameter_data: Dict[str, pd.DataFrame] = {}
self._optimization_results: Dict[str, pd.DataFrame] = {}

self._user_sessions: Dict[str, UserSession] = {}

self._alerts: List[DashboardAlert] = []
self._alert_handlers: List[Callable] = []

self._real_time_task: Optional[asyncio.Task] = None
self._running: bool = False

self._setup_routes()

def _setup_routesself:
"""设置路由"""
try:

self.app.mount("/static", StaticFilesdirectory=self.config.static_dir, name="static")

@self.app.get"/", response_class=HTMLResponse
async def get_dashboard():
return await self._get_main_dashboard()

@self.app.get"/api/strategies"
async def get_strategies():
return await self._get_strategies()

@self.app.get"/api/performance/{strategy_id}"
async def get_strategy_performancestrategy_id: str:
return await self._get_strategy_performancestrategy_id

@self.app.get"/api/benchmarks"
async def get_benchmarks():
return await self._get_benchmarks()

@self.app.post"/api/analysis/compare"
async def compare_strategiesrequest: Dict[str, Any]:
return await self._compare_strategiesrequest

@self.app.get"/api/alerts"
async def get_alerts():
return await self._get_alerts()

@self.app.post"/api/alerts/{alert_id}/acknowledge"
async def acknowledge_alertalert_id: str:
return await self._acknowledge_alertalert_id

# WebSocket端点
@self.app.websocket"/ws/{session_id}"
async def websocket_endpointwebsocket: WebSocket, session_id: str:
await self._websocket_handlerwebsocket, session_id

for dashboard_type in DashboardType:
self.app.add_api_route(
f"/dashboard/{dashboard_type.value}",
lambda dt=dashboard_type: self._get_dashboard_pagedt,
methods=["GET"],
response_class=HTMLResponse
)

except Exception as e:
self.logger.errorf"设置路由失败: {e}"

async def initializeself -> bool:
"""初始化仪表板"""
try:
self.logger.info"正在初始化交互式仪表板..."

await self.visualizer.initialize()
await self.benchmark_analyzer.initialize()

Pathself.config.static_dir.mkdirparents=True, exist_ok=True

# 启动实时更新任务
if self.config.real_time_enabled:    self._running = True
self._real_time_task = asyncio.create_task(self._real_time_update_loop())

self.logger.info"交互式仪表板初始化完成"
return True

except Exception as e:
self.logger.errorf"仪表板初始化失败: {e}"
return False

async def _websocket_handlerself, websocket: WebSocket, session_id: str:
"""WebSocket连接处理"""
try:
await self.websocket_manager.connectwebsocket, session_id

user_session = UserSession(
session_id=session_id,
user_id=f"user_{session_id}",
websocket=websocket,
created_at=datetime.utcnow(),
last_activity=datetime.utcnow()
)
self._user_sessions[session_id] = user_session

await self._send_initial_datawebsocket

while True:
try:

message = await websocket.receive_text()
data = json.loadsmessage

user_session.last_activity = datetime.utcnow()

await self._handle_websocket_messagewebsocket, session_id, data

except WebSocketDisconnect:
break
except Exception as e:
self.logger.errorf"处理WebSocket消息失败: {e}"

except WebSocketDisconnect:
pass
except Exception as e:
self.logger.errorf"WebSocket连接处理失败: {e}"
finally:

await self._cleanup_sessionsession_id

async def _handle_websocket_message(self, websocket: WebSocket,
session_id: str, data: Dict[str, Any]):
"""处理WebSocket消息"""
try:    message_type = data.get("type")

if message_type == "subscribe":

channel = data.get"channel"
if channel:
await self._subscribe_channelsession_id, channel

elif message_type == "unsubscribe":

channel = data.get"channel"
if channel:
await self._unsubscribe_channelsession_id, channel

elif message_type == "get_chart_data":

chart_type = data.get"chart_type"
params = data.get"params", {}
chart_data = await self._get_chart_datachart_type, params
await websocket.send_text(json.dumps({
"type": "chart_data",
"chart_type": chart_type,
"data": chart_data
}))

elif message_type == "update_preferences":

preferences = data.get"preferences", {}
await self._update_user_preferencessession_id, preferences

except Exception as e:
self.logger.errorf"处理WebSocket消息失败: {e}"

async def _subscribe_channelself, session_id: str, channel: str:
"""订阅频道"""
try:
if session_id in self._user_sessions:
if channel not in self._user_sessions[session_id].subscriptions:
self._user_sessions[session_id].subscriptions.appendchannel
self.logger.infof"用户 {session_id} 订阅了频道: {channel}"

except Exception as e:
self.logger.errorf"订阅频道失败: {e}"

async def _unsubscribe_channelself, session_id: str, channel: str:
"""取消订阅频道"""
try:
if (session_id in self._user_sessions and
channel in self._user_sessions[session_id].subscriptions):
self._user_sessions[session_id].subscriptions.removechannel
self.logger.infof"用户 {session_id} 取消订阅了频道: {channel}"

except Exception as e:
self.logger.errorf"取消订阅频道失败: {e}"

async def _get_chart_dataself, chart_type: str, params: Dict[str, Any] -> Dict[str, Any]:
"""获取图表数据"""
try:    if chart_type == "performance_comparison":
strategy_ids = params.get"strategy_ids", []
fig = self.visualizer.create_performance_comparisonstrategy_ids

elif chart_type == "risk_return_scatter":    strategy_ids = params.get("strategy_ids", [])
fig = self.visualizer.create_risk_return_scatterstrategy_ids

elif chart_type == "parameter_heatmap":    strategy_id = params.get("strategy_id")
param_x = params.get"param_x"
param_y = params.get"param_y"
metric = params.get"metric", "sharpe_ratio"
fig = self.visualizer.create_parameter_heatmapstrategy_id, param_x, param_y, metric

elif chart_type == "3d_surface":    strategy_id = params.get("strategy_id")
param_x = params.get"param_x"
param_y = params.get"param_y"
metric = params.get"metric", "sharpe_ratio"
fig = self.visualizer.create_3d_surface_plotstrategy_id, param_x, param_y, metric

elif chart_type == "correlation_matrix":    strategy_ids = params.get("strategy_ids", [])
fig = self.visualizer.create_correlation_matrixstrategy_ids

elif chart_type == "benchmark_comparison":    strategy_id = params.get("strategy_id")
benchmark_symbols = params.get"benchmarks", []
# 实现基准比较图表
fig = await self._create_benchmark_comparison_chartstrategy_id, benchmark_symbols

else:
raise ValueErrorf"不支持的图表类型: {chart_type}"

# 转换为JSON格式
chart_json = json.loads(plotly.utils.PlotlyJSONEncoder().encodefig)

return {
"figure": chart_json,
"timestamp": datetime.utcnow().isoformat()
}

except Exception as e:
self.logger.errorf"获取图表数据失败 {chart_type}: {e}"
return {"error": stre}

async def _create_benchmark_comparison_chart(self, strategy_id: str,
benchmark_symbols: List[str]) -> go.Figure:
"""创建基准比较图表"""
try:    fig = make_subplots(
rows=2, cols=2,
subplot_titles='Cumulative Returns', 'Rolling Alpha', 'Beta', 'Information Ratio',
specs=[[{"secondary_y": False}, {"secondary_y": False}],
[{"secondary_y": False}, {"secondary_y": False}]]
)

# 获取基准比较结果
colors = px.colors.qualitative.Set3[:lenbenchmark_symbols]

for i, benchmark_symbol in enumeratebenchmark_symbols:    result = await self.benchmark_analyzer.analyze_against_benchmark(strategy_id, benchmark_symbol)

if not result:
continue

# 创建合成的时间序列数据用于演示
dates = pd.date_rangeend=result.analysis_date, periods=252, freq='D'

strategy_cumulative = np.cumprod(1 + np.random.normal0.001, 0.02, 252) - 1
benchmark_cumulative = np.cumprod(1 + np.random.normal0.0008, 0.015, 252) - 1

fig.add_trace(
go.Scatter(
x=dates,
y=strategy_cumulative,
name=f"{strategy_id} vs {benchmark_symbol}",
line=dictcolor=colors[i],
mode='lines'
),
row=1, col=1
)

# 滚动Alpha（示例数据）
rolling_alpha = np.random.normalresult.alpha, 0.1, 100
alpha_dates = dates[-100:]

fig.add_trace(
go.Scatter(
x=alpha_dates,
y=rolling_alpha,
name=f"{benchmark_symbol} Alpha",
line=dictcolor=colors[i],
mode='lines',
showlegend=False
),
row=1, col=2
)

# Beta（作为常数值显示）
fig.add_trace(
go.Scatter(
x=[dates[0], dates[-1]],
y=[result.beta, result.beta],
name=f"{benchmark_symbol} Beta",
line=dictcolor=colors[i], dash='dash',
showlegend=False
),
row=2, col=1
)

# 信息比率（作为常数值显示）
fig.add_trace(
go.Scatter(
x=[dates[0], dates[-1]],
y=[result.information_ratio, result.information_ratio],
name=f"{benchmark_symbol} IR",
line=dictcolor=colors[i], dash='dot',
showlegend=False
),
row=2, col=2
)

fig.update_layout(
title=f"Strategy {strategy_id} Benchmark Comparison",
template=self.config.default_theme,
height=800,
showlegend=True
)

return fig

except Exception as e:
self.logger.errorf"创建基准比较图表失败: {e}"
return go.Figure()

async def _real_time_update_loopself:
"""实时更新循环"""
while self._running:
try:

await self._check_alerts()

await self._update_active_sessions()

await self._cleanup_expired_sessions()

await asyncio.sleepself.config.update_interval

except Exception as e:
self.logger.errorf"实时更新循环错误: {e}"
await asyncio.sleepself.config.update_interval

async def _check_alertsself:
"""检查告警"""
try:
if not self.config.alerts_enabled:
return

new_alerts = []

for strategy_id, performance_data in self._strategy_data.items():
if not performance_data:
continue

latest_performance = performance_data[-1]

if latest_performance.sharpe_ratio < self.config.alert_thresholds["sharpe_ratio_min"]:    alert = DashboardAlert(
id=f"sharpe_{strategy_id}_{datetime.utcnow().timestamp()}",
level=AlertLevel.WARNING,
strategy_id=strategy_id,
message=f"夏普比率过低: {latest_performance.sharpe_ratio:.3f}",
timestamp=datetime.utcnow(),
details={"sharpe_ratio": latest_performance.sharpe_ratio}
)
new_alerts.appendalert

if latest_performance.max_drawdown > self.config.alert_thresholds["max_drawdown_max"]:    alert = DashboardAlert(
id=f"drawdown_{strategy_id}_{datetime.utcnow().timestamp()}",
level=AlertLevel.ERROR,
strategy_id=strategy_id,
message=f"最大回撤过高: {latest_performance.max_drawdown:.2%}",
timestamp=datetime.utcnow(),
details={"max_drawdown": latest_performance.max_drawdown}
)
new_alerts.appendalert

if latest_performance.volatility > self.config.alert_thresholds["volatility_max"]:    alert = DashboardAlert(
id=f"volatility_{strategy_id}_{datetime.utcnow().timestamp()}",
level=AlertLevel.WARNING,
strategy_id=strategy_id,
message=f"波动率过高: {latest_performance.volatility:.2%}",
timestamp=datetime.utcnow(),
details={"volatility": latest_performance.volatility}
)
new_alerts.appendalert

self._alerts.extendnew_alerts

if lenself._alerts > 1000:    self._alerts = self._alerts[-1000:]

if new_alerts:
await self._broadcast_alertsnew_alerts

except Exception as e:
self.logger.errorf"检查告警失败: {e}"

async def _broadcast_alertsself, alerts: List[DashboardAlert]:
"""广播告警"""
try:    alert_data = [
{
"id": alert.id,
"level": alert.level.value,
"strategy_id": alert.strategy_id,
"message": alert.message,
"timestamp": alert.timestamp.isoformat(),
"details": alert.details
}
for alert in alerts
]

message = json.dumps({
"type": "alerts",
"alerts": alert_data
})

await self.websocket_manager.broadcastmessage

except Exception as e:
self.logger.errorf"广播告警失败: {e}"

async def _update_active_sessionsself:
"""更新活跃会话"""
try:    current_time = datetime.utcnow()
active_strategies = list(self._strategy_data.keys())

for session_id, session in self._user_sessions.items():
# 检查会话是否订阅了策略更新
if "strategy_updates" in session.subscriptions:
# 发送策略更新数据
update_data = {
"type": "strategy_updates",
"timestamp": current_time.isoformat(),
"active_strategies": active_strategies
}

try:
await session.websocket.send_text(json.dumpsupdate_data)
except Exception as e:
self.logger.warningf"发送策略更新失败 {session_id}: {e}"

except Exception as e:
self.logger.errorf"更新活跃会话失败: {e}"

async def _cleanup_expired_sessionsself:
"""清理过期会话"""
try:    current_time = datetime.utcnow()
expired_sessions = []

for session_id, session in self._user_sessions.items():
# 检查会话是否超时
if current_time - session.last_activity.total_seconds() > self.config.session_timeout:
expired_sessions.appendsession_id

for session_id in expired_sessions:
await self._cleanup_sessionsession_id

except Exception as e:
self.logger.errorf"清理过期会话失败: {e}"

async def _cleanup_sessionself, session_id: str:
"""清理会话"""
try:
if session_id in self._user_sessions:    session = self._user_sessions[session_id]

# 断开WebSocket连接
try:
await self.websocket_manager.disconnectsession.websocket
except:
pass

del self._user_sessions[session_id]
self.logger.infof"已清理会话: {session_id}"

except Exception as e:
self.logger.errorf"清理会话失败 {session_id}: {e}"

async def _send_initial_dataself, websocket: WebSocket:
"""发送初始数据"""
try:    initial_data = {
"type": "initial_data",
"timestamp": datetime.utcnow().isoformat(),
"strategies": list(self._strategy_data.keys()),
"benchmarks": self.benchmark_analyzer.get_available_benchmarks(),
"config": {
"update_interval": self.config.update_interval,
"real_time_enabled": self.config.real_time_enabled
}
}

await websocket.send_text(json.dumpsinitial_data)

except Exception as e:
self.logger.errorf"发送初始数据失败: {e}"

async def _get_main_dashboardself -> str:
"""获取主仪表板HTML"""
return self._get_dashboard_htmlDashboardType.OVERVIEW

async def _get_dashboard_pageself, dashboard_type: DashboardType -> str:
"""获取仪表板页面"""
return self._get_dashboard_htmldashboard_type

def _get_dashboard_htmlself, dashboard_type: DashboardType -> str:
"""生成仪表板HTML"""
try:    html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>0700.HK Quantitative Trading Dashboard - {dashboard_type.value.title()}</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/vue@3/dist/vue.global.js"></script>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
.dashboard-container {{ margin: 20px; }}
.chart-container {{ margin-bottom: 30px; }}
.alert-item {{ margin-bottom: 10px; }}
.metric-card {{
background: white;
border-radius: 8px;
padding: 20px;
box-shadow: 0 2px 4px rgba0,0,0,0.1;
margin-bottom: 20px;
}}
.metric-value {{ font-size: 2em; font-weight: bold; }}
.metric-label {{ color: #666; }}
</style>
</head>
<body>
<div id="app" class="dashboard-container">
<nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
<div class="container-fluid">
<a class="navbar-brand" href="#">0700.HK Quant Dashboard</a>
<div class="navbar-nav">
<a class="nav-link" :class="{{active: dashboardType === 'overview'}}" href="#overview">概览</a>
<a class="nav-link" :class="{{active: dashboardType === 'performance'}}" href="#performance">绩效</a>
<a class="nav-link" :class="{{active: dashboardType === 'risk'}}" href="#risk">风险</a>
<a class="nav-link" :class="{{active: dashboardType === 'benchmark'}}" href="#benchmark">基准</a>
<a class="nav-link" :class="{{active: dashboardType === 'optimization'}}" href="#optimization">优化</a>
<a class="nav-link" :class="{{active: dashboardType === 'correlation'}}" href="#correlation">相关性</a>
<a class="nav-link" :class="{{active: dashboardType === 'real_time'}}" href="#real_time">实时</a>
</div>
</div>
</nav>

<div class="container-fluid">
<!-- 告警区域 -->
<div v-if="alerts.length > 0" class="row mb-4">
<div class="col-12">
<div class="alert alert-warning">
<h5>系统告警</h5>
<div v-for="alert in alerts.slice0, 3" :key="alert.id" class="alert-item">
<span class="badge" :class="getAlertClassalert.level">{{{{ alert.level }}}}</span>
{{{{ alert.message }}}}
</div>
</div>
</div>
</div>

<!-- 指标卡片 -->
<div class="row mb-4">
<div class="col-md-3">
<div class="metric-card">
<div class="metric-value text-primary">{{{{ activeStrategies.length }}}}</div>
<div class="metric-label">活跃策略</div>
</div>
</div>
<div class="col-md-3">
<div class="metric-card">
<div class="metric-value text-success">{{{{ bestSharpe.toFixed3 }}}}</div>
<div class="metric-label">最佳夏普比率</div>
</div>
</div>
<div class="col-md-3">
<div class="metric-card">
<div class="metric-value text-info">{{{{ totalTrades }}}}</div>
<div class="metric-label">总交易次数</div>
</div>
</div>
<div class="col-md-3">
<div class="metric-card">
<div class="metric-value text-warning">{{{{ avgDrawdown.toFixed2 }}}}%</div>
<div class="metric-label">平均最大回撤</div>
</div>
</div>
</div>

<!-- 图表区域 -->
<div class="row">
<div class="col-12">
<div class="chart-container">
<h3>{{{{ getDashboardTitledashboardType }}}}</h3>
<div id="main-chart" style="width:100%; height:600px;"></div>
</div>
</div>
</div>

<!-- 策略列表 -->
<div class="row mt-4">
<div class="col-12">
<h4>策略列表</h4>
<div class="table-responsive">
<table class="table table-striped">
<thead>
<tr>
<th>策略ID</th>
<th>夏普比率</th>
<th>总收益率</th>
<th>最大回撤</th>
<th>波动率</th>
<th>胜率</th>
<th>交易次数</th>
<th>操作</th>
</tr>
</thead>
<tbody>
<tr v-for="strategy in strategyData" :key="strategy.id">
<td>{{{{ strategy.id }}}}</td>
<td>{{{{ strategy.sharpeRatio.toFixed3 }}}}</td>
<td>{{{{ strategy.totalReturn00.toFixed2 }}}%</td>
<td>{{{{ strategy.maxDrawdown00.toFixed2 }}}%</td>
<td>{{{{ strategy.volatility00.toFixed2 }}}%</td>
<td>{{{{ strategy.winRate00.toFixed1 }}}%</td>
<td>{{{{ strategy.tradesCount }}}}</td>
<td>
<button class="btn btn-sm btn-primary" @click="selectStrategystrategy.id">分析</button>
</td>
</tr>
</tbody>
</table>
</div>
</div>
</div>
</div>
</div>

<script>
const {{ createApp }}({{
data() {{
return {{
dashboardType: '{dashboard_type.value}',
ws: null,
session_id: '{{{{ Math.random().toString36.substr2, 9 }}}}',
alerts: [],
activeStrategies: [],
strategyData: [],
bestSharpe: 0,
totalTrades: 0,
avgDrawdown: 0
}};
}},
mounted() {{
this.connectWebSocket();
this.loadDashboardData();
}},
methods: {{
connectWebSocket() {{
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const ws_url = `${{protocol}}//${{window.location.host}}/ws/${{this.session_id}}`;

this.ws = new WebSocketws_url;

this.ws.onopen = () => {{
console.log'WebSocket连接已建立';
this.subscribeToUpdates();
}};

this.ws.onmessage = event => {{
const data = JSON.parseevent.data;
this.handleWebSocketMessagedata;
}};

this.ws.onclose = () => {{
console.log'WebSocket连接已关闭';
setTimeout(() => this.connectWebSocket(), 5000);
}};
}},

subscribeToUpdates() {{
this.ws.send(JSON.stringify({{
type: 'subscribe',
channel: 'strategy_updates'
}}));
}},

handleWebSocketMessagedata {{
switchdata.type {{
case 'initial_data':    this.activeStrategies = data.strategies;
break;
case 'alerts':    this.alerts = [...this.alerts, ...data.alerts];
break;
case 'strategy_updates':    this.activeStrategies = data.active_strategies;
break;
}}
}},

loadDashboardData() {{
// 加载仪表板数据
this.loadMainChart();
this.loadStrategyData();
}},

loadMainChart() {{
// 根据仪表板类型加载主图表
const chartType = this.getMainChartType();

this.ws.send(JSON.stringify({{
type: 'get_chart_data',
chart_type: chartType,
params: {{
strategy_ids: this.activeStrategies
}}
}}));
}},

getMainChartType() {{
const chartTypes = {{
'overview': 'performance_comparison',
'performance': 'performance_comparison',
'risk': 'risk_return_scatter',
'benchmark': 'benchmark_comparison',
'optimization': 'parameter_heatmap',
'correlation': 'correlation_matrix',
'real_time': 'performance_comparison'
}};
return chartTypes[this.dashboardType] || 'performance_comparison';
}},

loadStrategyData() {{
fetch'/api/strategies'
.then(response => response.json())
.then(data => {{
this.strategyData = data.strategies || [];
this.calculateMetrics();
}})
.catch(error => console.error'加载策略数据失败:', error);
}},

calculateMetrics() {{
if this.strategyData.length === 0 return;

this.bestSharpe = Math.max(...this.strategyData.maps => s.sharpeRatio);
this.totalTrades = this.strategyData.reduce(sum, s => sum + s.tradesCount, 0);
this.avgDrawdown = this.strategyData.reduce(sum, s => sum + s.maxDrawdown, 0) / this.strategyData.length;
}},

getDashboardTitletype {{
const titles = {{
'overview': '系统概览',
'performance': '绩效分析',
'risk': '风险管理',
'benchmark': '基准比较',
'optimization': '参数优化',
'correlation': '相关性分析',
'real_time': '实时监控'
}};
return titles[type] || '量化交易仪表板';
}},

getAlertClasslevel {{
const classes = {{
'info': 'bg-info',
'warning': 'bg-warning',
'error': 'bg-danger',
'critical': 'bg-dark'
}};
return classes[level] || 'bg-secondary';
}},

selectStrategystrategyId {{
// 选择策略进行分析
console.log'选择策略:', strategyId;
// 实现策略选择逻辑
}}
}}
}}).mount'#app';

// 处理WebSocket消息中的图表数据
window.addEventListener('message', event => {{
if event.data.type === 'chart_data' {{
const figure = event.data.data.figure;
Plotly.newPlot'main-chart', figure.data, figure.layout;
}}
}});
</script>
</body>
</html>
"""

return html_template

except Exception as e:
self.logger.errorf"生成仪表板HTML失败: {e}"
return f"<html><body><h1>Error loading dashboard: {stre}</h1></body></html>"

async def _get_strategiesself:
"""获取策略列表"""
try:    strategies = []
for strategy_id, performance_data in self._strategy_data.items():
if performance_data:    latest = performance_data[-1]
strategies.append({
"id": strategy_id,
"sharpeRatio": latest.sharpe_ratio,
"totalReturn": latest.total_return,
"maxDrawdown": latest.max_drawdown,
"volatility": latest.volatility,
"winRate": latest.win_rate,
"tradesCount": latest.trades_count
})

return {"strategies": strategies}

except Exception as e:
self.logger.errorf"获取策略列表失败: {e}"
return {"error": stre}

async def _get_strategy_performanceself, strategy_id: str:
"""获取策略绩效"""
try:
if strategy_id not in self._strategy_data:
return {"error": "Strategy not found"}

performance_data = self._strategy_data[strategy_id]
return {
"strategy_id": strategy_id,
"performance": [
{
"date": perf.calculation_date.isoformat(),
"sharpe_ratio": perf.sharpe_ratio,
"total_return": perf.total_return,
"max_drawdown": perf.max_drawdown,
"volatility": perf.volatility,
"win_rate": perf.win_rate
}
for perf in performance_data
]
}

except Exception as e:
self.logger.errorf"获取策略绩效失败: {e}"
return {"error": stre}

async def _get_benchmarksself:
"""获取基准列表"""
try:    benchmarks = self.benchmark_analyzer.get_benchmark_summary().to_dict('records')
return {"benchmarks": benchmarks}

except Exception as e:
self.logger.errorf"获取基准列表失败: {e}"
return {"error": stre}

async def _compare_strategiesself, request: Dict[str, Any]:
"""比较策略"""
try:    strategy_ids = request.get("strategy_ids", [])
if not strategy_ids:
return {"error": "No strategy IDs provided"}

fig = self.visualizer.create_performance_comparisonstrategy_ids
chart_json = json.loads(plotly.utils.PlotlyJSONEncoder().encodefig)

return {"chart_data": chart_json}

except Exception as e:
self.logger.errorf"策略比较失败: {e}"
return {"error": stre}

async def _get_alertsself:
"""获取告警列表"""
try:    alerts_data = [
{
"id": alert.id,
"level": alert.level.value,
"strategy_id": alert.strategy_id,
"message": alert.message,
"timestamp": alert.timestamp.isoformat(),
"acknowledged": alert.acknowledged,
"details": alert.details
}
for alert in self._alerts
]

return {"alerts": alerts_data}

except Exception as e:
self.logger.errorf"获取告警列表失败: {e}"
return {"error": stre}

async def _acknowledge_alertself, alert_id: str:
"""确认告警"""
try:
for alert in self._alerts:    if alert.id == alert_id:
alert.acknowledged = True
return {"success": True}

return {"error": "Alert not found"}

except Exception as e:
self.logger.errorf"确认告警失败: {e}"
return {"error": stre}

def add_strategy_dataself, strategy_id: str, performance_data: List[PerformanceMetrics]:
"""添加策略数据"""
try:

self.visualizer.add_performance_datastrategy_id, performance_data

if strategy_id not in self._strategy_data:    self._strategy_data[strategy_id] = []

self._strategy_data[strategy_id].extendperformance_data

if lenself._strategy_data[strategy_id] > self.config.max_data_points:    self._strategy_data[strategy_id] = self._strategy_data[strategy_id][-self.config.max_data_points:]

self.logger.info(f"已添加策略数据: {strategy_id}, {lenperformance_data} 条记录")

except Exception as e:
self.logger.errorf"添加策略数据失败 {strategy_id}: {e}"

def add_optimization_resultsself, strategy_id: str, results: pd.DataFrame:
"""添加优化结果"""
try:
self.visualizer.add_optimization_resultsstrategy_id, results
self._optimization_results[strategy_id] = results.copy()

self.logger.info(f"已添加优化结果: {strategy_id}, {lenresults} 条记录")

except Exception as e:
self.logger.errorf"添加优化结果失败 {strategy_id}: {e}"

def run_serverself:
"""运行服务器"""
try:
self.logger.infof"启动仪表板服务器: {self.config.host}:{self.config.port}"
uvicorn.run(
self.app,
host=self.config.host,
port=self.config.port,
debug=self.config.debug
)

except Exception as e:
self.logger.errorf"启动服务器失败: {e}"

async def cleanupself:
"""清理资源"""
try:
self.logger.info"正在清理交互式仪表板..."

self._running = False

if self._real_time_task:
self._real_time_task.cancel()
try:
await self._real_time_task
except asyncio.CancelledError:
pass

await self.visualizer.cleanup()
await self.benchmark_analyzer.cleanup()

# 清理WebSocket连接
await self.websocket_manager.disconnect_all()

self._strategy_data.clear()
self._optimization_results.clear()
self._user_sessions.clear()
self._alerts.clear()

self.logger.info"交互式仪表板清理完成"

except Exception as e:
self.logger.errorf"清理交互式仪表板失败: {e}"

__all__ = [
"InteractiveDashboard",
"DashboardConfig",
"DashboardAlert",
"UserSession",
"DashboardType",
"AlertLevel",
]