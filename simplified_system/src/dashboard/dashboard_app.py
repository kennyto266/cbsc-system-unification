#!/usr / bin / env python3
"""
交互式性能仪表板主应用
Interactive Performance Dashboard

专业的量化交易实时仪表板，支持：
- 实时数据更新
- 交互式图表
- 投资组合监控
- 性能归因分析
- 风险指标展示
"""

import json
import logging
from typing import Any, Dict, List, Optional

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash import Input, Output, State, callback_context, dash_table, dcc, html
from plotly.subplots import make_subplots

# 导入系统组件
from ..api.stock_api import get_hk_stock_data, get_multiple_stocks
from ..backtest.vectorbt_engine import BacktestResult, VectorBTEngine
from ..indicators.core_indicators import CoreIndicators
from ..indicators.technical_analyzer import TechnicalAnalyzer
from .performance_charts import PerformanceCharts
from .real_time_updater import RealTimeUpdater

logger = logging.getLogger(__name__)


class QuantDashboard:
    """量化交易仪表板主类"""

    def __init__(self, debug: bool = False, port: int = 8050):
        """
        初始化仪表板

        Args:
            debug: 调试模式
            port: 服务端口
        """
        self.debug = debug
        self.port = port

        # 初始化系统组件
        self.indicators = CoreIndicators()
        self.analyzer = TechnicalAnalyzer()
        self.backtest_engine = VectorBTEngine()
        self.performance_charts = PerformanceCharts()
        self.real_time_updater = RealTimeUpdater()

        # 数据缓存
        self.data_cache = {}
        self.results_cache = {}

        # 初始化Dash应用
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[
                dbc.themes.CYBORG,
                "https://codepen.io / chriddyp / pen / bWLwgP.css",
            ],
            suppress_callback_exceptions = True,
        )

        # 配置应用
        self.app.title = "量化交易性能仪表板"

        # 设置布局
        self.setup_layout()

        # 注册回调
        self.register_callbacks()

        logger.info("Dashboard initialized successfully")

    def setup_layout(self):
        """设置仪表板布局"""
        self.app.layout = dbc.Container(
            [
                # Header
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H1(
                                    "量化交易性能仪表板",
                                    className="text - center mb - 4",
                                    style={"color": "#00D4AA"},
                                ),
                                html.Hr(),
                            ]
                        )
                    ]
                ),
                # 控制面板
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.H5(
                                                    "控制面板", className="card - title"
                                                ),
                                                # 股票选择
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                html.Label("选择股票:"),
                                                                dcc.Dropdown(
                                                                    id="stock - selector",
                                                                    options=[
                                                                        {
                                                                            "label": "腾讯控股 (0700.HK)",
                                                                            "value": "0700.HK",
                                                                        },
                                                                        {
                                                                            "label": "阿里巴巴 (09988.HK)",
                                                                            "value": "09988.HK",
                                                                        },
                                                                        {
                                                                            "label": "美团 (03690.HK)",
                                                                            "value": "03690.HK",
                                                                        },
                                                                        {
                                                                            "label": "小米集团 (01810.HK)",
                                                                            "value": "01810.HK",
                                                                        },
                                                                        {
                                                                            "label": "港交所 (00388.HK)",
                                                                            "value": "00388.HK",
                                                                        },
                                                                    ],
                                                                    value="0700.HK",
                                                                    multi = False,
                                                                ),
                                                            ],
                                                            width = 6,
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                html.Label("时间范围:"),
                                                                dcc.Dropdown(
                                                                    id="time - range - selector",
                                                                    options=[
                                                                        {
                                                                            "label": "1个月",
                                                                            "value": 30,
                                                                        },
                                                                        {
                                                                            "label": "3个月",
                                                                            "value": 90,
                                                                        },
                                                                        {
                                                                            "label": "6个月",
                                                                            "value": 180,
                                                                        },
                                                                        {
                                                                            "label": "1年",
                                                                            "value": 365,
                                                                        },
                                                                        {
                                                                            "label": "2年",
                                                                            "value": 730,
                                                                        },
                                                                    ],
                                                                    value = 365,
                                                                ),
                                                            ],
                                                            width = 6,
                                                        ),
                                                    ],
                                                    className="mb - 3",
                                                ),
                                                # 策略选择
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                html.Label("选择策略:"),
                                                                dcc.Dropdown(
                                                                    id="strategy - selector",
                                                                    options=[
                                                                        {
                                                                            "label": "RSI均值回归",
                                                                            "value": "RSI_MEAN_REVERSION",
                                                                        },
                                                                        {
                                                                            "label": "MACD交叉",
                                                                            "value": "MACD_CROSSOVER",
                                                                        },
                                                                        {
                                                                            "label": "布林带",
                                                                            "value": "BOLLINGER_BANDS",
                                                                        },
                                                                        {
                                                                            "label": "双移动平均",
                                                                            "value": "DUAL_MOVING_AVERAGE",
                                                                        },
                                                                        {
                                                                            "label": "动量突破",
                                                                            "value": "MOMENTUM_BREAKOUT",
                                                                        },
                                                                        {
                                                                            "label": "波动率突破",
                                                                            "value": "VOLATILITY_BREAKOUT",
                                                                        },
                                                                    ],
                                                                    value="RSI_MEAN_REVERSION",
                                                                ),
                                                            ],
                                                            width = 6,
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                html.Label("基准比较:"),
                                                                dcc.Dropdown(
                                                                    id="benchmark - selector",
                                                                    options=[
                                                                        {
                                                                            "label": "恒生指数",
                                                                            "value": "HSI",
                                                                        },
                                                                        {
                                                                            "label": "沪深300",
                                                                            "value": "CSI300",
                                                                        },
                                                                        {
                                                                            "label": "无基准",
                                                                            "value": "None",
                                                                        },
                                                                    ],
                                                                    value="HSI",
                                                                ),
                                                            ],
                                                            width = 6,
                                                        ),
                                                    ],
                                                    className="mb - 3",
                                                ),
                                                # 更新按钮
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                dbc.Button(
                                                                    "更新数据",
                                                                    id="update - button",
                                                                    color="primary",
                                                                    className="w - 100",
                                                                ),
                                                            ],
                                                            width = 4,
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                dbc.Button(
                                                                    "运行回测",
                                                                    id="backtest - button",
                                                                    color="success",
                                                                    className="w - 100",
                                                                ),
                                                            ],
                                                            width = 4,
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                dbc.Button(
                                                                    "实时模式",
                                                                    id="realtime - button",
                                                                    color="info",
                                                                    className="w - 100",
                                                                ),
                                                            ],
                                                            width = 4,
                                                        ),
                                                    ]
                                                ),
                                            ]
                                        )
                                    ]
                                )
                            ],
                            width = 12,
                        )
                    ],
                    className="mb - 4",
                ),
                # 主要指标卡片
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.H4(
                                                    "总回报率", className="card - title"
                                                ),
                                                html.H2(
                                                    id="total - return - metric",
                                                    className="text - success",
                                                ),
                                                html.P(
                                                    "年化回报率", className="card - text"
                                                ),
                                                html.H4(
                                                    id="annual - return - metric",
                                                    className="text - primary",
                                                ),
                                            ]
                                        )
                                    ]
                                )
                            ],
                            width = 3,
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.H4(
                                                    "Sharpe比率", className="card - title"
                                                ),
                                                html.H2(
                                                    id="sharpe - metric",
                                                    className="text - info",
                                                ),
                                                html.P(
                                                    "最大回撤", className="card - text"
                                                ),
                                                html.H4(
                                                    id="max - drawdown - metric",
                                                    className="text - danger",
                                                ),
                                            ]
                                        )
                                    ]
                                )
                            ],
                            width = 3,
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.H4("胜率", className="card - title"),
                                                html.H2(
                                                    id="win - rate - metric",
                                                    className="text - warning",
                                                ),
                                                html.P(
                                                    "总交易次数", className="card - text"
                                                ),
                                                html.H4(id="total - trades - metric"),
                                            ]
                                        )
                                    ]
                                )
                            ],
                            width = 3,
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.H4(
                                                    "Calmar比率", className="card - title"
                                                ),
                                                html.H2(
                                                    id="calmar - metric",
                                                    className="text - secondary",
                                                ),
                                                html.P(
                                                    "Sortino比率", className="card - text"
                                                ),
                                                html.H4(id="sortino - metric"),
                                            ]
                                        )
                                    ]
                                )
                            ],
                            width = 3,
                        ),
                    ],
                    className="mb - 4",
                ),
                # 图表区域
                dbc.Row(
                    [
                        # 价格和策略信号图表
                        dbc.Col([dcc.Graph(id="price - chart")], width = 8),
                        # 绩效指标雷达图
                        dbc.Col([dcc.Graph(id="performance - radar")], width = 4),
                    ],
                    className="mb - 4",
                ),
                dbc.Row(
                    [
                        # 收益率分布
                        dbc.Col([dcc.Graph(id="returns - distribution")], width = 6),
                        # 回撤图
                        dbc.Col([dcc.Graph(id="drawdown - chart")], width = 6),
                    ],
                    className="mb - 4",
                ),
                dbc.Row(
                    [
                        # 相关性热力图
                        dbc.Col([dcc.Graph(id="correlation - heatmap")], width = 6),
                        # 月度收益热力图
                        dbc.Col([dcc.Graph(id="monthly - returns - heatmap")], width = 6),
                    ],
                    className="mb - 4",
                ),
                # 交易记录表格
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.H5(
                                                    "交易记录", className="card - title"
                                                ),
                                                dash_table.DataTable(
                                                    id="trades - table",
                                                    columns=[
                                                        {"name": "日期", "id": "date"},
                                                        {
                                                            "name": "方向",
                                                            "id": "direction",
                                                        },
                                                        {"name": "价格", "id": "price"},
                                                        {"name": "数量", "id": "size"},
                                                        {"name": "盈亏", "id": "pnl"},
                                                    ],
                                                    page_size = 10,
                                                    style_table={"overflowX": "auto"},
                                                    style_cell={
                                                        "textAlign": "center",
                                                        "padding": "10px",
                                                    },
                                                    style_data_conditional=[
                                                        {
                                                            "if": {"row_index": "odd"},
                                                            "backgroundColor": "rgb(50, 50, 50)",
                                                        }
                                                    ],
                                                ),
                                            ]
                                        )
                                    ]
                                )
                            ]
                        )
                    ],
                    className="mb - 4",
                ),
                # 实时状态指示器
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    id="status - indicator",
                                    children=[
                                        html.Span("● 就绪", style={"color": "green"})
                                    ],
                                )
                            ]
                        )
                    ]
                ),
                # 自动更新组件
                dcc.Interval(
                    id="interval - component",
                    interval = 30 * 1000,  # 30秒更新一次
                    n_intervals = 0,
                ),
                # 存储组件
                dcc.Store(id="data - store"),
                dcc.Store(id="results - store"),
                dcc.Store(id="realtime - status - store", data={"active": False}),
            ],
            fluid = True,
        )

    def register_callbacks(self):
        """注册所有回调函数"""

        @self.app.callback(
            [Output("data - store", "data"), Output("status - indicator", "children")],
            [
                Input("update - button", "n_clicks"),
                Input("stock - selector", "value"),
                Input("time - range - selector", "value"),
            ],
        )
        def update_data(n_clicks, stock_symbol, time_range):
            """更新股票数据"""
            try:
                # 获取股票数据
                if stock_symbol:
                    data = get_hk_stock_data(stock_symbol, time_range)

                    # 计算技术指标
                    data_with_indicators = self.calculate_indicators(data)

                    # 缓存数据
                    self.data_cache[stock_symbol] = data_with_indicators

                    status = html.Span("● 数据已更新", style={"color": "green"})

                    return data_with_indicators.to_json(date_format="iso"), status
                else:
                    return None, html.Span("● 请选择股票", style={"color": "orange"})

            except Exception as e:
                logger.error(f"Error updating data: {e}")
                return None, html.Span("● 数据更新失败", style={"color": "red"})

        @self.app.callback(
            [
                Output("results - store", "data"),
                Output("total - return - metric", "children"),
                Output("annual - return - metric", "children"),
                Output("sharpe - metric", "children"),
                Output("max - drawdown - metric", "children"),
                Output("win - rate - metric", "children"),
                Output("total - trades - metric", "children"),
                Output("calmar - metric", "children"),
                Output("sortino - metric", "children"),
            ],
            [
                Input("backtest - button", "n_clicks"),
                Input("data - store", "data"),
                Input("strategy - selector", "value"),
            ],
        )
        def run_backtest(n_clicks, data_json, strategy):
            """运行回测"""
            if not n_clicks or not data_json:
                return None, "-", "-", "-", "-", "-", "-", "-", "-"

            try:
                # 解析数据
                data = pd.read_json(data_json)

                # 获取策略参数
                strategy_params = self.get_strategy_parameters(strategy)

                # 运行回测
                result = self.backtest_engine.backtest_strategy(
                    data = data,
                    strategy = strategy,
                    parameters = strategy_params,
                    symbol="SELECTED_STOCK",
                )

                # 更新指标显示
                metrics = self.format_metrics(result)

                # 缓存结果
                self.results_cache[strategy] = result

                return result.to_json(), *metrics

            except Exception as e:
                logger.error(f"Error running backtest: {e}")
                return (
                    None,
                    "错误",
                    "错误",
                    "错误",
                    "错误",
                    "错误",
                    "错误",
                    "错误",
                    "错误",
                )

        @self.app.callback(
            [
                Output("price - chart", "figure"),
                Output("performance - radar", "figure"),
                Output("returns - distribution", "figure"),
                Output("drawdown - chart", "figure"),
                Output("correlation - heatmap", "figure"),
                Output("monthly - returns - heatmap", "figure"),
                Output("trades - table", "data"),
            ],
            [
                Input("data - store", "data"),
                Input("results - store", "data"),
                Input("benchmark - selector", "value"),
            ],
        )
        def update_charts(data_json, results_json, benchmark):
            """更新所有图表"""
            if not data_json:
                empty_fig = go.Figure()
                return (
                    empty_fig,
                    empty_fig,
                    empty_fig,
                    empty_fig,
                    empty_fig,
                    empty_fig,
                    [],
                )

            try:
                # 解析数据
                data = pd.read_json(data_json)

                # 生成图表
                price_fig = self.performance_charts.create_price_chart(data)

                radar_fig = self.performance_charts.create_performance_radar(
                    results_json if results_json else None
                )

                returns_fig = self.performance_charts.create_returns_distribution(data)

                drawdown_fig = self.performance_charts.create_drawdown_chart(data)

                correlation_fig = self.performance_charts.create_correlation_heatmap(
                    data
                )

                monthly_fig = self.performance_charts.create_monthly_returns_heatmap(
                    data
                )

                # 处理交易记录
                trades_data = self.extract_trades_data(results_json)

                return (
                    price_fig,
                    radar_fig,
                    returns_fig,
                    drawdown_fig,
                    correlation_fig,
                    monthly_fig,
                    trades_data,
                )

            except Exception as e:
                logger.error(f"Error updating charts: {e}")
                empty_fig = go.Figure()
                return (
                    empty_fig,
                    empty_fig,
                    empty_fig,
                    empty_fig,
                    empty_fig,
                    empty_fig,
                    [],
                )

        @self.app.callback(
            Output("realtime - status - store", "data"),
            Input("realtime - button", "n_clicks"),
            State("realtime - status - store", "data"),
        )
        def toggle_realtime(n_clicks, current_status):
            """切换实时模式"""
            if n_clicks:
                new_status = {"active": not current_status.get("active", False)}

                if new_status["active"]:
                    self.real_time_updater.start()
                    logger.info("Real - time updates enabled")
                else:
                    self.real_time_updater.stop()
                    logger.info("Real - time updates disabled")

                return new_status

            return current_status

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        try:
            data_with_indicators = data.copy()

            # RSI
            data_with_indicators["RSI_14"] = self.indicators.calculate_rsi(
                data["close"], 14
            )

            # 移动平均
            data_with_indicators["SMA_20"] = self.indicators.calculate_sma(
                data["close"], 20
            )
            data_with_indicators["SMA_50"] = self.indicators.calculate_sma(
                data["close"], 50
            )

            # MACD
            macd_result = self.indicators.calculate_macd(data["close"], 12, 26, 9)
            data_with_indicators["MACD"] = macd_result["macd"]
            data_with_indicators["MACD_Signal"] = macd_result["signal"]

            # 布林带
            bb_result = self.indicators.calculate_bollinger_bands(data["close"], 20, 2)
            data_with_indicators["BB_Upper"] = bb_result["upper"]
            data_with_indicators["BB_Lower"] = bb_result["lower"]

            return data_with_indicators

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return data

    def get_strategy_parameters(self, strategy: str) -> Dict[str, Any]:
        """获取策略参数"""
        default_params = {
            "RSI_MEAN_REVERSION": {"period": 14, "oversold": 30, "overbought": 70},
            "MACD_CROSSOVER": {"fast": 12, "slow": 26, "signal": 9},
            "BOLLINGER_BANDS": {"period": 20, "std_dev": 2.0},
            "DUAL_MOVING_AVERAGE": {"short_period": 20, "long_period": 50},
            "MOMENTUM_BREAKOUT": {"lookback": 20, "threshold": 0.02},
            "VOLATILITY_BREAKOUT": {"atr_period": 14, "multiplier": 2.0},
        }

        return default_params.get(strategy, {})

    def format_metrics(self, result: BacktestResult) -> tuple:
        """格式化指标显示"""
        return (
            f"{result.total_return:.2%}",
            f"{result.annual_return:.2%}",
            f"{result.sharpe_ratio:.3f}",
            f"{result.max_drawdown:.2%}",
            f"{result.win_rate:.2%}",
            str(result.total_trades),
            f"{result.calmar_ratio:.3f}",
            f"{result.sortino_ratio:.3f}",
        )

    def extract_trades_data(self, results_json: str) -> List[Dict]:
        """提取交易记录数据"""
        if not results_json:
            return []

        try:
            result_data = json.loads(results_json)
            trades = result_data.get("trades", [])

            formatted_trades = []
            for trade in trades[:10]:  # 只显示最近10笔交易
                formatted_trades.append(
                    {
                        "date": trade.get("date", ""),
                        "direction": trade.get("direction", ""),
                        "price": f"{trade.get('price', 0):.2f}",
                        "size": str(trade.get("size", 0)),
                        "pnl": f"{trade.get('pnl', 0):.2f}",
                    }
                )

            return formatted_trades

        except Exception as e:
            logger.error(f"Error extracting trades data: {e}")
            return []

    def run(self, host: str = "127.0.0.1", port: Optional[int] = None):
        """运行仪表板应用"""
        run_port = port or self.port

        logger.info(f"Starting dashboard on http://{host}:{run_port}")

        self.app.run_server(
            debug = self.debug, host = host, port = run_port, use_reloader = False
        )


# 便利函数
def create_dashboard(debug: bool = False, port: int = 8050) -> QuantDashboard:
    """创建仪表板实例"""
    return QuantDashboard(debug = debug, port = port)


def run_dashboard(debug: bool = False, port: int = 8050, host: str = "127.0.0.1"):
    """直接运行仪表板"""
    dashboard = create_dashboard(debug = debug, port = port)
    dashboard.run(host = host)


if __name__ == "__main__":
    run_dashboard(debug = True)
