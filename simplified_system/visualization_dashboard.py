#!/usr / bin / env python3
"""
🌐 Quantitative Trading Visualization Dashboard
量化交易可視化儀表板

Advanced interactive dashboard for quantitative trading analysis
高級交互式量化交易分析儀表板

Features:
- Real - time stock data visualization
- Technical indicators analysis
- Portfolio performance tracking
- Risk management dashboard
- Multi - asset correlation analysis

Author: Claude Code Assistant
Date: 2025 - 11 - 27
Version: 1.0
"""

import sys
from datetime import datetime

# Add Simplified System path
sys.path.append("src")
sys.path.append(".")

# Dash framework
import dash
import dash_bootstrap_components as dbc
import numpy as np

# Data processing
import pandas as pd

# Advanced visualization
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go

# Financial data
import talib
import yfinance as yf
from dash import Input, Output, State, callback, dash_table, dcc, html
from plotly.subplots import make_subplots

# Add Simplified System path and try imports
try:
    from api.government_data import get_latest_government_data
    from api.stock_api import get_hk_stock_data, get_multiple_stocks
    from indicators.core_indicators import CoreIndicators

    from backtest.vectorbt_engine import VectorBTEngine

    SIMPLIFIED_SYSTEM_AVAILABLE = True
    print("✅ Simplified System modules loaded successfully")
except ImportError as e:
    print(f"⚠️ Simplified System modules not available: {e}")
    print("Using mock data for demonstration")
    SIMPLIFIED_SYSTEM_AVAILABLE = False


class QuantitativeVisualizationDashboard:
    """量化交易可視化儀表板主類

    Main class for quantitative trading visualization dashboard
    """

    def __init__(self, debug = False):
        """初始化儀表板

        Initialize dashboard
        """
        self.debug = debug
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
            title="量化交易可視化分析平台",
            suppress_callback_exceptions = True,
        )

        # Initialize components
        self.chart_templates = self._init_chart_templates()
        self.data_cache = {}
        self.cache_timeout = 300  # 5 minutes

        # Available stocks
        self.available_stocks = [
            {"label": "0700.HK - 騰訊控股 Tencent Holdings", "value": "0700.HK"},
            {"label": "0941.HK - 中國移動 China Mobile", "value": "0941.HK"},
            {"label": "1398.HK - 工商銀行 ICBC", "value": "1398.HK"},
            {"label": "0388.HK - 港交所 HKEX", "value": "0388.HK"},
            {"label": "0005.HK - 匯豐 HSBC", "value": "0005.HK"},
            {"label": "1299.HK - 友邦保險 AIA", "value": "1299.HK"},
            {"label": "2318.HK - 中國平安 Ping An", "value": "2318.HK"},
            {"label": "3690.HK - 美團 Meituan", "value": "3690.HK"},
        ]

        # Setup layout and callbacks
        self._setup_layout()
        self._setup_callbacks()

    def _init_chart_templates(self):
        """初始化圖表模板

        Initialize chart templates
        """
        # Quantitative color palette
        colors = {
            "primary": "#1f77b4",
            "success": "#2ca02c",
            "danger": "#d62728",
            "warning": "#ff7f0e",
            "info": "#17becf",
            "dark": "#7f7f7f",
            "light": "#e377c2",
            "bull": "#00d084",  # Green - bullish
            "bear": "#ff4757",  # Red - bearish
        }

        return {
            "colors": colors,
            "template": "plotly_white",
            "font_family": "Arial, SimHei",
        }

    def _setup_layout(self):
        """設置應用佈局

        Setup application layout
        """
        self.app.layout = dbc.Container(
            [
                # Header
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.H1(
                                            "📊 量化交易可視化分析平台",
                                            className="display - 4 text - center mb - 2",
                                            style={
                                                "color": "#2c3e50",
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        html.H5(
                                            "Quantitative Trading Visualization Platform",
                                            className="text - center text - muted mb - 4",
                                        ),
                                        html.Hr(),
                                    ]
                                )
                            ]
                        )
                    ]
                ),
                # Loading state
                dcc.Loading(
                    id="loading",
                    type="circle",
                    children=[
                        # Control Panel
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardHeader(
                                                    html.H5(
                                                        "🎛️ 控制面板 Control Panel",
                                                        className="mb - 0",
                                                    )
                                                ),
                                                dbc.CardBody(
                                                    [
                                                        dbc.Row(
                                                            [
                                                                # Stock selection
                                                                dbc.Col(
                                                                    [
                                                                        dbc.Label(
                                                                            "選擇股票 Select Stock:"
                                                                        ),
                                                                        dcc.Dropdown(
                                                                            id="stock - selector",
                                                                            options = self.available_stocks,
                                                                            value="0700.HK",
                                                                            className="mb - 3",
                                                                        ),
                                                                    ],
                                                                    width = 6,
                                                                    md = 3,
                                                                ),
                                                                # Time range
                                                                dbc.Col(
                                                                    [
                                                                        dbc.Label(
                                                                            "時間範圍 Time Range:"
                                                                        ),
                                                                        dcc.Dropdown(
                                                                            id="period - selector",
                                                                            options=[
                                                                                {
                                                                                    "label": "1個月 1M",
                                                                                    "value": 30,
                                                                                },
                                                                                {
                                                                                    "label": "3個月 3M",
                                                                                    "value": 90,
                                                                                },
                                                                                {
                                                                                    "label": "6個月 6M",
                                                                                    "value": 180,
                                                                                },
                                                                                {
                                                                                    "label": "1年 1Y",
                                                                                    "value": 365,
                                                                                },
                                                                                {
                                                                                    "label": "2年 2Y",
                                                                                    "value": 730,
                                                                                },
                                                                                {
                                                                                    "label": "3年 3Y",
                                                                                    "value": 1095,
                                                                                },
                                                                            ],
                                                                            value = 365,
                                                                            className="mb - 3",
                                                                        ),
                                                                    ],
                                                                    width = 6,
                                                                    md = 3,
                                                                ),
                                                                # Chart type
                                                                dbc.Col(
                                                                    [
                                                                        dbc.Label(
                                                                            "圖表類型 Chart Type:"
                                                                        ),
                                                                        dcc.Dropdown(
                                                                            id="chart - type - selector",
                                                                            options=[
                                                                                {
                                                                                    "label": "K線圖 Candlestick",
                                                                                    "value": "candlestick",
                                                                                },
                                                                                {
                                                                                    "label": "技術指標 Technical",
                                                                                    "value": "technical",
                                                                                },
                                                                                {
                                                                                    "label": "成交量 Volume",
                                                                                    "value": "volume",
                                                                                },
                                                                                {
                                                                                    "label": "相關性 Correlation",
                                                                                    "value": "correlation",
                                                                                },
                                                                            ],
                                                                            value="candlestick",
                                                                            className="mb - 3",
                                                                        ),
                                                                    ],
                                                                    width = 6,
                                                                    md = 3,
                                                                ),
                                                                # Update button
                                                                dbc.Col(
                                                                    [
                                                                        dbc.Label(
                                                                            "更新 Update:"
                                                                        ),
                                                                        dbc.Button(
                                                                            [
                                                                                html.I(
                                                                                    className="bi bi - arrow - clockwise me - 2"
                                                                                ),
                                                                                "更新圖表",
                                                                            ],
                                                                            id="update - button",
                                                                            color="primary",
                                                                            className="w - 100 mb - 3",
                                                                        ),
                                                                    ],
                                                                    width = 6,
                                                                    md = 3,
                                                                ),
                                                            ]
                                                        ),
                                                        # Technical indicators
                                                        dbc.Row(
                                                            [
                                                                dbc.Col(
                                                                    [
                                                                        dbc.Label(
                                                                            "技術指標 Technical Indicators:"
                                                                        ),
                                                                        dcc.Checklist(
                                                                            id="indicator - selector",
                                                                            options=[
                                                                                {
                                                                                    "label": "MA5",
                                                                                    "value": "MA5",
                                                                                },
                                                                                {
                                                                                    "label": "MA20",
                                                                                    "value": "MA20",
                                                                                },
                                                                                {
                                                                                    "label": "MA50",
                                                                                    "value": "MA50",
                                                                                },
                                                                                {
                                                                                    "label": "RSI(14)",
                                                                                    "value": "RSI14",
                                                                                },
                                                                                {
                                                                                    "label": "MACD",
                                                                                    "value": "MACD",
                                                                                },
                                                                                {
                                                                                    "label": "布林帶 BB",
                                                                                    "value": "BB",
                                                                                },
                                                                                {
                                                                                    "label": "成交量 Volume",
                                                                                    "value": "Volume",
                                                                                },
                                                                            ],
                                                                            value=[
                                                                                "MA5",
                                                                                "MA20",
                                                                                "RSI14",
                                                                                "Volume",
                                                                            ],
                                                                            className="mb - 0",
                                                                        ),
                                                                    ],
                                                                    width = 12,
                                                                )
                                                            ]
                                                        ),
                                                    ]
                                                ),
                                            ]
                                        )
                                    ],
                                    width = 12,
                                )
                            ],
                            className="mb - 4",
                        ),
                        # Main Content Area
                        dbc.Row(
                            [
                                # Charts Column
                                dbc.Col(
                                    [
                                        # Main Chart
                                        dcc.Graph(
                                            id="main - chart",
                                            style={"height": "600px"},
                                            config={
                                                "displayModeBar": True,
                                                "scrollZoom": True,
                                            },
                                        ),
                                        # Secondary Charts Row
                                        dbc.Row(
                                            [
                                                # Volume Chart
                                                dbc.Col(
                                                    [
                                                        dcc.Graph(
                                                            id="volume - chart",
                                                            style={"height": "300px"},
                                                            config={
                                                                "displayModeBar": False
                                                            },
                                                        )
                                                    ],
                                                    width = 6,
                                                ),
                                                # Indicators Chart
                                                dbc.Col(
                                                    [
                                                        dcc.Graph(
                                                            id="indicators - chart",
                                                            style={"height": "300px"},
                                                            config={
                                                                "displayModeBar": False
                                                            },
                                                        )
                                                    ],
                                                    width = 6,
                                                ),
                                            ],
                                            className="mt - 3",
                                        ),
                                    ],
                                    width = 8,
                                ),
                                # Side Panel
                                dbc.Col(
                                    [
                                        # Statistics Card
                                        dbc.Card(
                                            [
                                                dbc.CardHeader(
                                                    html.H6(
                                                        "📊 統計信息 Statistics",
                                                        className="mb - 0",
                                                    )
                                                ),
                                                dbc.CardBody(
                                                    [html.Div(id="statistics - info")]
                                                ),
                                            ],
                                            className="mb - 3",
                                        ),
                                        # Technical Analysis Card
                                        dbc.Card(
                                            [
                                                dbc.CardHeader(
                                                    html.H6(
                                                        "🔬 技術分析 Technical",
                                                        className="mb - 0",
                                                    )
                                                ),
                                                dbc.CardBody(
                                                    [
                                                        html.Div(
                                                            id="technical - analysis - info"
                                                        )
                                                    ]
                                                ),
                                            ],
                                            className="mb - 3",
                                        ),
                                        # Risk Metrics Card
                                        dbc.Card(
                                            [
                                                dbc.CardHeader(
                                                    html.H6(
                                                        "⚠️ 風險指標 Risk Metrics",
                                                        className="mb - 0",
                                                    )
                                                ),
                                                dbc.CardBody(
                                                    [html.Div(id="risk - metrics - info")]
                                                ),
                                            ]
                                        ),
                                    ],
                                    width = 4,
                                ),
                            ],
                            className="mb - 4",
                        ),
                        # Advanced Analysis Section
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Tabs(
                                            [
                                                dbc.Tab(
                                                    label="📈 投資組合 Portfolio",
                                                    tab_id="portfolio",
                                                ),
                                                dbc.Tab(
                                                    label="🔗 相關性 Correlation",
                                                    tab_id="correlation",
                                                ),
                                                dbc.Tab(
                                                    label="📊 回測分析 Backtest",
                                                    tab_id="backtest",
                                                ),
                                            ],
                                            id="analysis - tabs",
                                            active_tab="portfolio",
                                        ),
                                        html.Div(
                                            id="analysis - content", className="mt - 3"
                                        ),
                                    ]
                                )
                            ]
                        ),
                        # Footer
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.Hr(),
                                                html.P(
                                                    [
                                                        "🏆 Simplified System Quantitative Trading Platform ",
                                                        html.Span(
                                                            f"| Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                                            className="text - muted",
                                                        ),
                                                    ],
                                                    className="text - center text - muted small",
                                                ),
                                            ]
                                        )
                                    ]
                                )
                            ]
                        ),
                    ],
                ),
                # Auto - refresh interval
                dcc.Interval(
                    id="auto - refresh - interval",
                    interval = 30 * 1000,  # 30 seconds
                    n_intervals = 0,
                    disabled = True,
                ),
                # Data store
                dcc.Store(id="data - store"),
                dcc.Store(id="indicators - store"),
            ],
            fluid = True,
        )

    def _setup_callbacks(self):
        """設置回調函數

        Setup callback functions
        """

        @self.app.callback(
            [Output("data - store", "data"), Output("indicators - store", "data")],
            [
                Input("update - button", "n_clicks"),
                Input("auto - refresh - interval", "n_intervals"),
            ],
            [State("stock - selector", "value"), State("period - selector", "value")],
        )
        def update_data(n_clicks, n_intervals, stock, period):
            """更新數據存儲

            Update data storage
            """
            try:
                # Load data
                df = self._load_stock_data(stock, period)

                if df is not None and not df.empty:
                    # Calculate indicators
                    df_indicators = self._calculate_indicators(df)

                    # Convert to JSON for storage
                    data_json = df.reset_index().to_json("records", date_format="iso")
                    indicators_json = df_indicators.reset_index().to_json(
                        "records", date_format="iso"
                    )

                    return data_json, indicators_json
                else:
                    return None, None

            except Exception as e:
                print(f"Error updating data: {e}")
                return None, None

        @self.app.callback(
            [
                Output("main - chart", "figure"),
                Output("volume - chart", "figure"),
                Output("indicators - chart", "figure"),
                Output("statistics - info", "children"),
                Output("technical - analysis - info", "children"),
                Output("risk - metrics - info", "children"),
            ],
            [
                Input("data - store", "data"),
                Input("indicators - store", "data"),
                Input("chart - type - selector", "value"),
                Input("indicator - selector", "value"),
            ],
            [State("stock - selector", "value")],
        )
        def update_charts(
            data_json, indicators_json, chart_type, selected_indicators, stock
        ):
            """更新所有圖表和信息面板

            Update all charts and information panels
            """
            if not data_json or not indicators_json:
                return (
                    {},
                    {},
                    {},
                    html.P("等待數據..."),
                    html.P("等待數據..."),
                    html.P("等待數據..."),
                )

            try:
                # Parse data
                df = pd.read_json(data_json)
                df_indicators = pd.read_json(indicators_json)

                # Set datetime index
                df["date"] = pd.to_datetime(df["date"])
                df.set_index("date", inplace = True)
                df_indicators["date"] = pd.to_datetime(df_indicators["date"])
                df_indicators.set_index("date", inplace = True)

                # Generate charts based on type
                if chart_type == "candlestick":
                    main_fig = self._create_candlestick_chart(
                        df, df_indicators, selected_indicators, stock
                    )
                elif chart_type == "technical":
                    main_fig = self._create_technical_chart(
                        df_indicators, selected_indicators, stock
                    )
                elif chart_type == "volume":
                    main_fig = self._create_volume_chart(df, stock)
                else:
                    main_fig = self._create_candlestick_chart(
                        df, df_indicators, selected_indicators, stock
                    )

                # Volume chart
                volume_fig = self._create_volume_chart(df, stock)

                # Indicators chart
                indicators_fig = self._create_indicators_chart(
                    df_indicators, selected_indicators, stock
                )

                # Statistics info
                stats_info = self._generate_statistics_info(df, stock)

                # Technical analysis info
                technical_info = self._generate_technical_analysis_info(
                    df_indicators, selected_indicators
                )

                # Risk metrics info
                risk_info = self._generate_risk_metrics_info(df, df_indicators)

                return (
                    main_fig,
                    volume_fig,
                    indicators_fig,
                    stats_info,
                    technical_info,
                    risk_info,
                )

            except Exception as e:
                print(f"Error updating charts: {e}")
                error_fig = go.Figure()
                error_fig.add_annotation(
                    text = f"Error: {str(e)}",
                    xref="paper",
                    yref="paper",
                    x = 0.5,
                    y = 0.5,
                    showarrow = False,
                )
                return (
                    error_fig,
                    {},
                    {},
                    html.P(f"Error: {str(e)}"),
                    html.P("Error"),
                    html.P("Error"),
                )

        @self.app.callback(
            Output("analysis - content", "children"),
            [Input("analysis - tabs", "active_tab"), Input("data - store", "data")],
        )
        def update_analysis_content(active_tab, data_json):
            """更新分析內容

            Update analysis content
            """
            if not data_json:
                return html.P("等待數據...")

            try:
                df = pd.read_json(data_json)
                df["date"] = pd.to_datetime(df["date"])
                df.set_index("date", inplace = True)

                if active_tab == "portfolio":
                    return self._create_portfolio_analysis(df)
                elif active_tab == "correlation":
                    return self._create_correlation_analysis(df)
                elif active_tab == "backtest":
                    return self._create_backtest_analysis(df)
                else:
                    return html.P("選擇分析標籤...")

            except Exception as e:
                return html.P(f"Error: {str(e)}")

    def _load_stock_data(self, symbol, days):
        """加載股票數據

        Load stock data
        """
        cache_key = f"{symbol}_{days}"

        # Check cache
        if cache_key in self.data_cache:
            cache_time, cache_data = self.data_cache[cache_key]
            if (datetime.now() - cache_time).seconds < self.cache_timeout:
                return cache_data

        try:
            if SIMPLIFIED_SYSTEM_AVAILABLE:
                # Try to get real data from Simplified System
                data = get_hk_stock_data(symbol, days)
                if data is not None and not data.empty:
                    # Rename columns to standard format
                    column_mapping = {
                        "open": "Open",
                        "high": "High",
                        "low": "Low",
                        "close": "Close",
                        "volume": "Volume",
                    }
                    data = data.rename(
                        columns={
                            col: standard
                            for col, standard in column_mapping.items()
                            if col in data.columns
                        }
                    )

                    # Cache the data
                    self.data_cache[cache_key] = (datetime.now(), data)
                    return data

            # Fallback to mock data
            print(f"Using mock data for {symbol}")
            mock_data = self._generate_mock_data(symbol, days)
            self.data_cache[cache_key] = (datetime.now(), mock_data)
            return mock_data

        except Exception as e:
            print(f"Error loading data for {symbol}: {e}")
            return self._generate_mock_data(symbol, days)

    def _generate_mock_data(self, symbol, days):
        """生成模擬數據

        Generate mock data
        """
        np.random.seed(42)
        dates = pd.date_range(end = datetime.now(), periods = days, freq="D")

        # Base prices for different stocks
        base_prices = {
            "0700.HK": 400,  # Tencent
            "0941.HK": 50,  # China Mobile
            "1398.HK": 4,  # ICBC
            "0388.HK": 300,  # HKEX
            "0005.HK": 350,  # HSBC
            "1299.HK": 60,  # AIA
            "2318.HK": 45,  # Ping An
            "3690.HK": 150,  # Meituan
        }

        base_price = base_prices.get(symbol, 100)

        # Generate realistic price movements
        returns = np.random.normal(0.0005, 0.02, days)
        prices = [base_price]

        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, base_price * 0.3))

        prices = np.array(prices)

        # Generate OHLC
        open_price = np.roll(prices, 1)
        open_price[0] = base_price

        high = np.maximum(prices, open_price) * (1 + np.random.uniform(0, 0.03, days))
        low = np.minimum(prices, open_price) * (1 - np.random.uniform(0, 0.03, days))

        # Volume correlated with price changes
        price_changes = np.abs(np.diff(prices, prepend = prices[0]))
        base_volume = np.random.uniform(1000000, 15000000, days)
        volume = (base_volume * (1 + price_changes / prices * 3)).astype(int)

        df = pd.DataFrame(
            {
                "Open": open_price,
                "High": high,
                "Low": low,
                "Close": prices,
                "Volume": volume,
            },
            index = dates,
        )

        return df

    def _calculate_indicators(self, df):
        """計算技術指標

        Calculate technical indicators
        """
        df_indicators = df.copy()

        # Moving averages
        df_indicators["MA5"] = df["Close"].rolling(window = 5).mean()
        df_indicators["MA20"] = df["Close"].rolling(window = 20).mean()
        df_indicators["MA50"] = df["Close"].rolling(window = 50).mean()

        # RSI
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window = 14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window = 14).mean()
        rs = gain / loss
        df_indicators["RSI14"] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df["Close"].ewm(span = 12, adjust = False).mean()
        exp2 = df["Close"].ewm(span = 26, adjust = False).mean()
        df_indicators["MACD"] = exp1 - exp2
        df_indicators["MACD_signal"] = (
            df_indicators["MACD"].ewm(span = 9, adjust = False).mean()
        )
        df_indicators["MACD_histogram"] = (
            df_indicators["MACD"] - df_indicators["MACD_signal"]
        )

        # Bollinger Bands
        df_indicators["BB_upper"] = df_indicators["MA20"] + (
            df["Close"].rolling(window = 20).std() * 2
        )
        df_indicators["BB_lower"] = df_indicators["MA20"] - (
            df["Close"].rolling(window = 20).std() * 2
        )
        df_indicators["BB_middle"] = df_indicators["MA20"]

        # Performance metrics
        df_indicators["Returns"] = df["Close"].pct_change()
        df_indicators["Cumulative_Returns"] = (
            1 + df_indicators["Returns"]
        ).cumprod() - 1

        # Drawdown
        cummax = df_indicators["Cumulative_Returns"].cummax()
        df_indicators["Drawdown"] = (
            (df_indicators["Cumulative_Returns"] / cummax) - 1
        ) * 100

        # Volatility
        df_indicators["Volatility_20d"] = df_indicators["Returns"].rolling(
            window = 20
        ).std() * np.sqrt(252)

        return df_indicators

    def _create_candlestick_chart(self, df, df_indicators, selected_indicators, stock):
        """創建K線圖

        Create candlestick chart
        """
        fig = go.Figure()

        # Candlestick
        fig.add_trace(
            go.Candlestick(
                x = df.index,
                open = df["Open"],
                high = df["High"],
                low = df["Low"],
                close = df["Close"],
                name="股價",
                increasing_line_color = self.chart_templates["colors"]["bull"],
                decreasing_line_color = self.chart_templates["colors"]["bear"],
            )
        )

        # Add selected indicators
        for indicator in selected_indicators:
            if indicator in df_indicators.columns:
                if indicator == "BB":
                    # Add Bollinger Bands
                    fig.add_trace(
                        go.Scatter(
                            x = df_indicators.index,
                            y = df_indicators["BB_upper"],
                            mode="lines",
                            name="BB Upper",
                            line = dict(color="orange", dash="dash"),
                            opacity = 0.7,
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x = df_indicators.index,
                            y = df_indicators["BB_lower"],
                            mode="lines",
                            name="BB Lower",
                            line = dict(color="orange", dash="dash"),
                            fill="tonexty",
                            fillcolor="rgba(255,165,0,0.2)",
                            opacity = 0.7,
                        )
                    )
                elif indicator == "Volume":
                    # Skip volume as it's shown separately
                    continue
                else:
                    # Add other indicators
                    fig.add_trace(
                        go.Scatter(
                            x = df_indicators.index,
                            y = df_indicators[indicator],
                            mode="lines",
                            name = indicator,
                            line = dict(width = 2),
                        )
                    )

        fig.update_layout(
            title = f"{stock} K線圖與技術指標",
            template = self.chart_templates["template"],
            xaxis_rangeslider_visible = False,
            height = 600,
            legend = dict(
                orientation="h", yanchor="bottom", y = 1.02, xanchor="right", x = 1
            ),
        )

        return fig

    def _create_volume_chart(self, df, stock):
        """創建成交量圖表

        Create volume chart
        """
        # Determine colors based on price movement
        colors = [
            (
                self.chart_templates["colors"]["bull"]
                if close >= open
                else self.chart_templates["colors"]["bear"]
            )
            for close, open in zip(df["Close"], df["Open"])
        ]

        fig = go.Figure()
        fig.add_trace(
            go.Bar(x = df.index, y = df["Volume"], name="成交量", marker_color = colors)
        )

        fig.update_layout(
            title = f"{stock} 成交量",
            template = self.chart_templates["template"],
            height = 300,
            showlegend = False,
        )

        return fig

    def _create_indicators_chart(self, df_indicators, selected_indicators, stock):
        """創建指標圖表

        Create indicators chart
        """
        fig = go.Figure()

        for indicator in selected_indicators:
            if indicator in df_indicators.columns and indicator not in ["Volume"]:
                if indicator == "RSI14":
                    # RSI with overbought / oversold levels
                    fig.add_trace(
                        go.Scatter(
                            x = df_indicators.index,
                            y = df_indicators[indicator],
                            mode="lines",
                            name="RSI(14)",
                            line = dict(color="purple"),
                        )
                    )
                    fig.add_hline(
                        y = 70, line_dash="dash", line_color="red", annotation_text="超買"
                    )
                    fig.add_hline(
                        y = 30,
                        line_dash="dash",
                        line_color="green",
                        annotation_text="超賣",
                    )
                elif indicator == "MACD":
                    # MACD with signal and histogram
                    fig.add_trace(
                        go.Scatter(
                            x = df_indicators.index,
                            y = df_indicators["MACD"],
                            mode="lines",
                            name="MACD",
                            line = dict(color="blue"),
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x = df_indicators.index,
                            y = df_indicators["MACD_signal"],
                            mode="lines",
                            name="Signal",
                            line = dict(color="red"),
                        )
                    )
                else:
                    fig.add_trace(
                        go.Scatter(
                            x = df_indicators.index,
                            y = df_indicators[indicator],
                            mode="lines",
                            name = indicator,
                        )
                    )

        fig.update_layout(
            title = f"{stock} 技術指標",
            template = self.chart_templates["template"],
            height = 300,
        )

        return fig

    def _create_technical_chart(self, df_indicators, selected_indicators, stock):
        """創建技術分析圖表

        Create technical analysis chart
        """
        fig = make_subplots(
            rows = 3,
            cols = 1,
            shared_xaxes = True,
            vertical_spacing = 0.05,
            subplot_titles=(f"{stock} 價格與均線", "RSI指標", "MACD指標"),
            row_heights=[0.5, 0.25, 0.25],
        )

        # Price and moving averages
        fig.add_trace(
            go.Scatter(
                x = df_indicators.index,
                y = df_indicators["Close"],
                mode="lines",
                name="Close Price",
                line = dict(color="black", width = 2),
            ),
            row = 1,
            col = 1,
        )

        if "MA5" in selected_indicators:
            fig.add_trace(
                go.Scatter(
                    x = df_indicators.index,
                    y = df_indicators["MA5"],
                    mode="lines",
                    name="MA5",
                    line = dict(color="blue"),
                ),
                row = 1,
                col = 1,
            )

        if "MA20" in selected_indicators:
            fig.add_trace(
                go.Scatter(
                    x = df_indicators.index,
                    y = df_indicators["MA20"],
                    mode="lines",
                    name="MA20",
                    line = dict(color="red"),
                ),
                row = 1,
                col = 1,
            )

        # RSI
        if "RSI14" in selected_indicators:
            fig.add_trace(
                go.Scatter(
                    x = df_indicators.index,
                    y = df_indicators["RSI14"],
                    mode="lines",
                    name="RSI(14)",
                    line = dict(color="purple"),
                ),
                row = 2,
                col = 1,
            )

            fig.add_hline(y = 70, line_dash="dash", line_color="red", row = 2, col = 1)
            fig.add_hline(y = 30, line_dash="dash", line_color="green", row = 2, col = 1)

        # MACD
        if "MACD" in selected_indicators:
            fig.add_trace(
                go.Scatter(
                    x = df_indicators.index,
                    y = df_indicators["MACD"],
                    mode="lines",
                    name="MACD",
                    line = dict(color="blue"),
                ),
                row = 3,
                col = 1,
            )

            fig.add_trace(
                go.Scatter(
                    x = df_indicators.index,
                    y = df_indicators["MACD_signal"],
                    mode="lines",
                    name="Signal",
                    line = dict(color="red"),
                ),
                row = 3,
                col = 1,
            )

        fig.update_layout(height = 600, template = self.chart_templates["template"])

        return fig

    def _generate_statistics_info(self, df, stock):
        """生成統計信息

        Generate statistics information
        """
        if df.empty:
            return [html.P("無數據")]

        latest_price = df["Close"].iloc[-1]
        price_change = df["Close"].iloc[-1] - df["Close"].iloc[0]
        price_change_pct = (price_change / df["Close"].iloc[0]) * 100

        period_high = df["High"].max()
        period_low = df["Low"].min()
        avg_volume = df["Volume"].mean()

        return [
            html.P([html.Strong("股票: "), stock]),
            html.P([html.Strong("最新價格: "), f"{latest_price:.2f} HKD"]),
            html.P(
                [
                    html.Strong("期間變化: "),
                    html.Span(
                        f"{price_change:+.2f}",
                        style={"color": "green" if price_change > 0 else "red"},
                    ),
                    f" ({price_change_pct:+.2f}%)",
                ]
            ),
            html.P([html.Strong("期間最高: "), f"{period_high:.2f} HKD"]),
            html.P([html.Strong("期間最低: "), f"{period_low:.2f} HKD"]),
            html.P([html.Strong("平均成交量: "), f"{avg_volume:,.0f}"]),
            html.P([html.Strong("數據天數: "), f"{len(df)} 天"]),
        ]

    def _generate_technical_analysis_info(self, df_indicators, selected_indicators):
        """生成技術分析信息

        Generate technical analysis information
        """
        if df_indicators.empty:
            return [html.P("無數據")]

        info = []

        # RSI Analysis
        if "RSI14" in selected_indicators and "RSI14" in df_indicators.columns:
            latest_rsi = df_indicators["RSI14"].iloc[-1]
            if not pd.isna(latest_rsi):
                if latest_rsi > 70:
                    rsi_status = "超買"
                    color = "red"
                elif latest_rsi < 30:
                    rsi_status = "超賣"
                    color = "green"
                else:
                    rsi_status = "中性"
                    color = "blue"

                info.append(
                    html.P(
                        [
                            html.Strong("RSI(14): "),
                            f"{latest_rsi:.1f} ",
                            html.Span(f"({rsi_status})", style={"color": color}),
                        ]
                    )
                )

        # Moving averages analysis
        if "MA5" in selected_indicators and "MA20" in selected_indicators:
            if all(col in df_indicators.columns for col in ["MA5", "MA20"]):
                latest_close = df_indicators["Close"].iloc[-1]
                latest_ma5 = df_indicators["MA5"].iloc[-1]
                latest_ma20 = df_indicators["MA20"].iloc[-1]

                if not any(pd.isna([latest_close, latest_ma5, latest_ma20])):
                    if latest_close > latest_ma5 > latest_ma20:
                        ma_trend = "強勢上漲"
                        trend_color = "green"
                    elif latest_close < latest_ma5 < latest_ma20:
                        ma_trend = "弱勢下跌"
                        trend_color = "red"
                    else:
                        ma_trend = "盤整"
                        trend_color = "orange"

                    info.append(
                        html.P(
                            [
                                html.Strong("均線趨勢: "),
                                html.Span(ma_trend, style={"color": trend_color}),
                            ]
                        )
                    )

        # MACD Analysis
        if "MACD" in selected_indicators and "MACD" in df_indicators.columns:
            latest_macd = df_indicators["MACD"].iloc[-1]
            latest_signal = df_indicators["MACD_signal"].iloc[-1]

            if not any(pd.isna([latest_macd, latest_signal])):
                if latest_macd > latest_signal and latest_macd > 0:
                    macd_signal = "買入信號"
                    signal_color = "green"
                elif latest_macd < latest_signal and latest_macd < 0:
                    macd_signal = "賣出信號"
                    signal_color = "red"
                else:
                    macd_signal = "觀望"
                    signal_color = "blue"

                info.append(
                    html.P(
                        [
                            html.Strong("MACD信號: "),
                            html.Span(macd_signal, style={"color": signal_color}),
                        ]
                    )
                )

        return info if info else [html.P("請選擇技術指標")]

    def _generate_risk_metrics_info(self, df, df_indicators):
        """生成風險指標信息

        Generate risk metrics information
        """
        if df.empty or df_indicators.empty:
            return [html.P("無數據")]

        try:
            # Calculate returns
            returns = df["Close"].pct_change().dropna()

            if len(returns) == 0:
                return [html.P("無足夠數據計算風險指標")]

            # Basic risk metrics
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            max_drawdown = (
                df_indicators["Drawdown"].min()
                if "Drawdown" in df_indicators.columns
                else 0
            )
            sharpe_ratio = (
                (returns.mean() * 252 - 0.03) / (returns.std() * np.sqrt(252))
                if returns.std() > 0
                else 0
            )

            # Value at Risk (5%)
            var_5 = returns.quantile(0.05)

            # Maximum daily loss
            max_daily_loss = returns.min()

            return [
                html.P([html.Strong("年化波動率: "), f"{volatility:.2%}"]),
                html.P(
                    [
                        html.Strong("最大回撤: "),
                        html.Span(
                            f"{max_drawdown:.2%}",
                            style={"color": "red" if max_drawdown < -0.1 else "orange"},
                        ),
                    ]
                ),
                html.P(
                    [
                        html.Strong("Sharpe比率: "),
                        html.Span(
                            f"{sharpe_ratio:.3f}",
                            style={"color": "green" if sharpe_ratio > 1 else "red"},
                        ),
                    ]
                ),
                html.P([html.Strong("VaR(5%): "), f"{var_5:.2%}"]),
                html.P([html.Strong("最大日損失: "), f"{max_daily_loss:.2%}"]),
                html.P(
                    [
                        html.Strong("風險評級: "),
                        self._get_risk_rating(volatility, max_drawdown),
                    ]
                ),
            ]

        except Exception as e:
            return [html.P(f"風險計算錯誤: {str(e)}")]

    def _get_risk_rating(self, volatility, max_drawdown):
        """獲取風險評級

        Get risk rating
        """
        if volatility < 0.15 and max_drawdown > -0.1:
            return html.Span("低風險", style={"color": "green"})
        elif volatility < 0.25 and max_drawdown > -0.2:
            return html.Span("中等風險", style={"color": "orange"})
        else:
            return html.Span("高風險", style={"color": "red"})

    def _create_portfolio_analysis(self, df):
        """創建投資組合分析

        Create portfolio analysis
        """
        # Mock portfolio data
        portfolio_data = {
            "Stock": ["0700.HK", "0941.HK", "1398.HK"],
            "Weight": [0.4, 0.3, 0.3],
            "Return": [0.15, 0.08, 0.12],
            "Risk": [0.25, 0.15, 0.20],
        }

        portfolio_df = pd.DataFrame(portfolio_data)

        return dbc.Row(
            [
                dbc.Col(
                    [
                        html.H6("模擬投資組合"),
                        dash_table.DataTable(
                            data = portfolio_df.to_dict("records"),
                            columns=[
                                {"name": i, "id": i} for i in portfolio_df.columns
                            ],
                            style_cell={"textAlign": "center"},
                            style_header={
                                "backgroundColor": "rgb(230, 230, 230)",
                                "fontWeight": "bold",
                            },
                        ),
                    ],
                    width = 6,
                ),
                dbc.Col(
                    [
                        html.H6("投資組合表現"),
                        dcc.Graph(
                            figure = px.pie(
                                portfolio_df,
                                values="Weight",
                                names="Stock",
                                title="投資組合權重分佈",
                            )
                        ),
                    ],
                    width = 6,
                ),
            ]
        )

    def _create_correlation_analysis(self, df):
        """創建相關性分析

        Create correlation analysis
        """
        return html.Div(
            [
                html.H6("資產相關性分析", className="mb - 3"),
                html.P("多資產相關性分析需要加載多隻股票數據，此功能正在開發中..."),
                html.P(
                    "Multi - asset correlation analysis requires loading multiple stocks data, this feature is under development..."
                ),
            ]
        )

    def _create_backtest_analysis(self, df):
        """創建回測分析

        Create backtest analysis
        """
        return html.Div(
            [
                html.H6("策略回測分析", className="mb - 3"),
                html.P("策略回測功能正在開發中，將支持多種交易策略測試..."),
                html.P(
                    "Strategy backtesting functionality is under development, will support multiple trading strategy testing..."
                ),
            ]
        )

    def run(self, host="127.0.0.1", port = 8050, debug = False):
        """運行儀表板

        Run dashboard
        """
        print(f"🌐 Starting Quantitative Trading Visualization Dashboard...")
        print(f"📊 Access URL: http://{host}:{port}")
        print(f"🎯 Features: Real - time charts, Technical analysis, Risk metrics")
        print(f"🔧 Debug mode: {debug}")

        self.app.run_server(
            host = host, port = port, debug = debug, dev_tools_hot_reload = debug
        )


def main():
    """主函數

    Main function
    """
    # Initialize dashboard
    dashboard = QuantitativeVisualizationDashboard(debug = True)

    # Run the application
    dashboard.run(host="127.0.0.1", port = 8050, debug = True)


if __name__ == "__main__":
    main()
