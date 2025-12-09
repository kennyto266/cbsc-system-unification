#!/usr / bin / env python3
"""
Simple Visualization Dashboard
簡化版可視化儀表板，使用已安裝的依賴
"""

import sys

import dash
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

# Add src path for Simplified System integration
sys.path.append("src")

try:
    from api.stock_api import get_hk_stock_data
    from indicators.core_indicators import CoreIndicators

    SIMPLIFIED_SYSTEM_AVAILABLE = True
except ImportError:
    SIMPLIFIED_SYSTEM_AVAILABLE = False
    print("Simplified System not fully available, using mock data")

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Jupyter Analytics Dashboard - 0700.HK"


def generate_mock_data():
    """Generate mock 0700.HK data"""
    np.random.seed(42)
    dates = pd.date_range("2022 - 01 - 01", "2023 - 12 - 31", freq="D")
    base_price = 400
    trend = np.linspace(base_price, base_price * 1.5, len(dates))
    volatility = np.random.randn(len(dates)) * 8
    price = trend + volatility
    price = np.maximum(price, 50)

    df = pd.DataFrame(
        {
            "Open": price * (1 + np.random.randn(len(dates)) * 0.01),
            "High": price * (1 + np.random.rand(len(dates)) * 0.02),
            "Low": price * (1 - np.random.rand(len(dates)) * 0.02),
            "Close": price,
            "Volume": np.random.randint(10000000, 30000000, len(dates)),
        },
        index = dates,
    )

    return df


def load_data():
    """Load real or mock data"""
    if SIMPLIFIED_SYSTEM_AVAILABLE:
        try:
            # Try to load real data
            data = get_hk_stock_data("0700.HK", 365)
            if data is not None and len(data) > 0:
                print(f"Loaded real 0700.HK data: {len(data)} records")
                return data
        except Exception as e:
            print(f"Failed to load real data: {e}")

    # Fallback to mock data
    print("Using mock 0700.HK data")
    return generate_mock_data()


def calculate_indicators(data):
    """Calculate technical indicators"""
    df = data.copy()

    # RSI (14)
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window = 14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window = 14).mean()
    rs = gain / loss
    df["RSI14"] = 100 - (100 / (1 + rs))

    # Moving averages
    df["MA5"] = df["Close"].rolling(window = 5).mean()
    df["MA20"] = df["Close"].rolling(window = 20).mean()
    df["MA50"] = df["Close"].rolling(window = 50).mean()

    # Bollinger Bands
    df["BB_Middle"] = df["Close"].rolling(window = 20).mean()
    df["BB_Upper"] = df["BB_Middle"] + 2 * df["Close"].rolling(window = 20).std()
    df["BB_Lower"] = df["BB_Middle"] - 2 * df["Close"].rolling(window = 20).std()

    # MACD
    exp1 = df["Close"].ewm(span = 12).mean()
    exp2 = df["Close"].ewm(span = 26).mean()
    df["MACD"] = exp1 - exp2
    df["MACD_Signal"] = df["MACD"].ewm(span = 9).mean()

    # Daily returns
    df["Returns"] = df["Close"].pct_change()

    # Cumulative returns
    df["Cumulative_Returns"] = (1 + df["Returns"]).cumprod() - 1

    return df


# Load and process data
print("Loading 0700.HK data...")
raw_data = load_data()
processed_data = calculate_indicators(raw_data)

# Create dashboard layout
app.layout = html.Div(
    [
        html.H1(
            "🎯 Jupyter Analytics Dashboard - 0700.HK",
            style={"textAlign": "center", "color": "#2c3e50", "marginBottom": 30},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H3("Data Source Status", style={"color": "#34495e"}),
                        html.P(
                            f"Simplified System: {'✅ Available' if SIMPLIFIED_SYSTEM_AVAILABLE else '⚠️ Mock Data'}",
                            style={
                                "color": (
                                    "green" if SIMPLIFIED_SYSTEM_AVAILABLE else "orange"
                                )
                            },
                        ),
                        html.P(f"Data Records: {len(processed_data)}"),
                        html.P(
                            f"Date Range: {processed_data.index[0].date()} to {processed_data.index[-1].date()}"
                        ),
                    ],
                    className="four columns",
                    style={
                        "padding": 20,
                        "backgroundColor": "#ecf0f1",
                        "borderRadius": 10,
                    },
                ),
                html.Div(
                    [
                        html.H3("Latest Indicators", style={"color": "#34495e"}),
                        html.P(
                            f"Close Price: {processed_data['Close'].iloc[-1]:.2f} HKD"
                        ),
                        html.P(f"RSI(14): {processed_data['RSI14'].iloc[-1]:.2f}"),
                        html.P(f"MA20: {processed_data['MA20'].iloc[-1]:.2f} HKD"),
                        html.P(
                            f"Daily Return: {processed_data['Returns'].iloc[-1]:.2%}"
                        ),
                    ],
                    className="four columns",
                    style={
                        "padding": 20,
                        "backgroundColor": "#e8f5e8",
                        "borderRadius": 10,
                    },
                ),
                html.Div(
                    [
                        html.H3("Performance Stats", style={"color": "#34495e"}),
                        html.P(
                            f"Total Return: {processed_data['Cumulative_Returns'].iloc[-1]:.2%}"
                        ),
                        html.P(f"Volatility: {processed_data['Returns'].std():.2%}"),
                        html.P(
                            f"Max Drawdown: {(processed_data['Close'] / processed_data['Close'].expanding().max() - 1).min():.2%}"
                        ),
                        html.P(
                            f"Sharpe Ratio: {processed_data['Returns'].mean() / processed_data['Returns'].std() * np.sqrt(252):.3f}"
                        ),
                    ],
                    className="four columns",
                    style={
                        "padding": 20,
                        "backgroundColor": "#fdeaea",
                        "borderRadius": 10,
                    },
                ),
            ],
            style={"display": "flex", "gap": 20, "marginBottom": 30},
        ),
        # Charts
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="price - chart", style={"height": 400})],
                    className="six columns",
                ),
                html.Div(
                    [dcc.Graph(id="volume - chart", style={"height": 400})],
                    className="six columns",
                ),
            ],
            style={"display": "flex", "gap": 20, "marginBottom": 30},
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="rsi - chart", style={"height": 300})],
                    className="four columns",
                ),
                html.Div(
                    [dcc.Graph(id="returns - chart", style={"height": 300})],
                    className="four columns",
                ),
                html.Div(
                    [dcc.Graph(id="macd - chart", style={"height": 300})],
                    className="four columns",
                ),
            ],
            style={"display": "flex", "gap": 20, "marginBottom": 30},
        ),
        # Interactive controls
        html.Div(
            [
                html.Label(
                    "Select Date Range:",
                    style={"fontWeight": "bold", "marginRight": 10},
                ),
                dcc.DatePickerRange(
                    id="date - picker - range",
                    start_date = processed_data.index[0].date(),
                    end_date = processed_data.index[-1].date(),
                    display_format="YYYY - MM - DD",
                ),
            ],
            style={"textAlign": "center", "marginBottom": 30},
        ),
        # Footer
        html.Div(
            [
                html.Hr(),
                html.P(
                    "🎉 Jupyter Notebook Analytics Dashboard",
                    style={"textAlign": "center", "color": "#7f8c8d", "margin": 20},
                ),
                html.P(
                    "Built with Simplified System Integration | Real - time 0700.HK Analysis",
                    style={
                        "textAlign": "center",
                        "color": "#95a5a6",
                        "marginBottom": 20,
                    },
                ),
            ]
        ),
    ]
)


# Callback for updating charts based on date range
@app.callback(
    [
        Output("price - chart", "figure"),
        Output("volume - chart", "figure"),
        Output("rsi - chart", "figure"),
        Output("returns - chart", "figure"),
        Output("macd - chart", "figure"),
    ],
    [Input("date - picker - range", "start_date"), Input("date - picker - range", "end_date")],
)
def update_charts(start_date, end_date):
    # Filter data based on date range
    filtered_data = processed_data.loc[start_date:end_date]

    # Price chart
    price_fig = go.Figure()
    price_fig.add_trace(
        go.Scatter(
            x = filtered_data.index,
            y = filtered_data["Close"],
            mode="lines",
            name="Close Price",
            line = dict(color="blue", width = 2),
        )
    )
    price_fig.add_trace(
        go.Scatter(
            x = filtered_data.index,
            y = filtered_data["MA20"],
            mode="lines",
            name="MA20",
            line = dict(color="orange", dash="dash"),
        )
    )
    price_fig.update_layout(
        title="0700.HK Price Chart",
        xaxis_title="Date",
        yaxis_title="Price (HKD)",
        hovermode="x unified",
    )

    # Volume chart
    volume_fig = go.Figure()
    volume_fig.add_trace(
        go.Bar(
            x = filtered_data.index,
            y = filtered_data["Volume"],
            name="Volume",
            marker_color="lightblue",
        )
    )
    volume_fig.update_layout(
        title="Trading Volume", xaxis_title="Date", yaxis_title="Volume"
    )

    # RSI chart
    rsi_fig = go.Figure()
    rsi_fig.add_trace(
        go.Scatter(
            x = filtered_data.index,
            y = filtered_data["RSI14"],
            mode="lines",
            name="RSI(14)",
            line = dict(color="purple"),
        )
    )
    rsi_fig.add_hline(
        y = 70, line_dash="dash", line_color="red", annotation_text="Overbought"
    )
    rsi_fig.add_hline(
        y = 30, line_dash="dash", line_color="green", annotation_text="Oversold"
    )
    rsi_fig.update_layout(
        title="RSI(14) Indicator", xaxis_title="Date", yaxis_title="RSI"
    )

    # Returns chart
    returns_fig = go.Figure()
    returns_fig.add_trace(
        go.Scatter(
            x = filtered_data.index,
            y = filtered_data["Returns"] * 100,
            mode="lines",
            name="Daily Returns",
            line = dict(color="green"),
        )
    )
    returns_fig.update_layout(
        title="Daily Returns", xaxis_title="Date", yaxis_title="Returns (%)"
    )

    # MACD chart
    macd_fig = go.Figure()
    macd_fig.add_trace(
        go.Scatter(
            x = filtered_data.index,
            y = filtered_data["MACD"],
            mode="lines",
            name="MACD",
            line = dict(color="blue"),
        )
    )
    macd_fig.add_trace(
        go.Scatter(
            x = filtered_data.index,
            y = filtered_data["MACD_Signal"],
            mode="lines",
            name="Signal",
            line = dict(color="red"),
        )
    )
    macd_fig.update_layout(
        title="MACD Indicator", xaxis_title="Date", yaxis_title="MACD"
    )

    return price_fig, volume_fig, rsi_fig, returns_fig, macd_fig


if __name__ == "__main__":
    print("🚀 Starting Jupyter Analytics Dashboard...")
    print(f"📊 Data loaded: {len(processed_data)} records")
    print(f"📈 Latest price: {processed_data['Close'].iloc[-1]:.2f} HKD")
    print(f"🌐 Dashboard will be available at: http://127.0.0.1:8050")
    print("⚡ Press Ctrl + C to stop the dashboard")

    app.run_server(debug = False, host="127.0.0.1", port = 8050)
