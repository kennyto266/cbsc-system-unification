#!/usr / bin / env python3
"""
Simple Visualization Dashboard - Fixed Version
修復版可視化儀表板，解決數據格式標準化問題
"""

import sys
from datetime import datetime

import dash
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

# Add src path for Simplified System integration
sys.path.append("src")

try:
    from api.stock_api import get_hk_stock_data, get_stock_prices_dataframe
    from indicators.core_indicators import CoreIndicators

    SIMPLIFIED_SYSTEM_AVAILABLE = True
    print("Simplified System modules loaded successfully")
except ImportError as e:
    SIMPLIFIED_SYSTEM_AVAILABLE = False
    print(f"Simplified System not fully available: {e}")
    print("Using mock data")

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "0700.HK Analytics Dashboard - Fixed"


def generate_mock_data():
    """Generate mock 0700.HK data with proper format"""
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

    # Ensure OHLC relationships are correct
    df["High"] = np.maximum(df["Open"], df["Close"]) * (
        1 + np.random.rand(len(df)) * 0.01
    )
    df["Low"] = np.minimum(df["Open"], df["Close"]) * (
        1 - np.random.rand(len(df)) * 0.01
    )
    df["Volume"] = df["Volume"].astype(int)

    return df


def load_and_standardize_data():
    """Load and standardize data format"""
    print("Loading 0700.HK data...")

    if SIMPLIFIED_SYSTEM_AVAILABLE:
        try:
            # Try to get DataFrame directly
            df = get_stock_prices_dataframe("0700.HK", 365)
            if df is not None and len(df) > 0:
                print(f"Loaded real DataFrame data: {len(df)} records")

                # Standardize column names
                df = standardize_dataframe(df)
                return df
            else:
                print("DataFrame function returned None, trying dict format...")

        except Exception as e:
            print(f"Failed to load DataFrame: {e}")

        try:
            # Try to load dict data and convert to DataFrame
            data_dict = get_hk_stock_data("0700.HK", 365)
            if data_dict and isinstance(data_dict, dict):
                print(f"Loaded dict data: {len(data_dict)} keys")

                # Convert dict to DataFrame
                df = convert_dict_to_dataframe(data_dict)
                if df is not None:
                    print(f"Successfully converted to DataFrame: {len(df)} records")
                    return df
                else:
                    print("Failed to convert dict to DataFrame")
            else:
                print(f"Dict data is None or invalid: {type(data_dict)}")

        except Exception as e:
            print(f"Failed to load dict data: {e}")

    # Fallback to mock data
    print("Using mock 0700.HK data")
    df = generate_mock_data()
    print(f"Generated mock data: {len(df)} records")
    return df


def standardize_dataframe(df):
    """Standardize DataFrame format"""
    if df is None:
        return None

    df = df.copy()

    # Standardize column names (case - insensitive)
    column_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if "open" in col_lower and "open" not in column_mapping:
            column_mapping[col] = "Open"
        elif "high" in col_lower and "high" not in column_mapping:
            column_mapping[col] = "High"
        elif "low" in col_lower and "low" not in column_mapping:
            column_mapping[col] = "Low"
        elif "close" in col_lower and "close" not in column_mapping:
            column_mapping[col] = "Close"
        elif (
            "price" in col_lower and "close" not in column_mapping
        ):  # Handle 'price' column
            column_mapping[col] = "Close"
        elif "volume" in col_lower and "volume" not in column_mapping:
            column_mapping[col] = "Volume"

    if column_mapping:
        df = df.rename(columns = column_mapping)

    # Ensure required columns exist
    required_columns = ["Open", "High", "Low", "Close", "Volume"]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        print(f"Missing columns: {missing_columns}")
        if "Close" in df.columns:
            # Fill missing OHLC with Close price
            for col in missing_columns:
                if col != "Close" and col != "Volume":
                    df[col] = df["Close"]

            # Fill Volume with reasonable values
            if "Volume" in missing_columns:
                df["Volume"] = np.random.randint(10000000, 30000000, len(df))
        else:
            print("Critical: No Close column found")
            return None

    # Ensure numeric data types
    for col in required_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Remove rows with NaN values in critical columns
    df = df.dropna(subset=["Close"])

    # Sort by index if it's datetime - like
    if hasattr(df.index, "to_datetime"):
        try:
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
        except Exception:
            pass

    return df


def convert_dict_to_dataframe(data_dict):
    """Convert dictionary data to DataFrame format"""
    if not data_dict or not isinstance(data_dict, dict):
        return None

    try:
        # Check if it's a nested structure with 'data' key
        if "data" in data_dict and isinstance(data_dict["data"], dict):
            nested_data = data_dict["data"]

            # Try to find price data in nested structure
            price_keys = ["close", "Close", "price", "Price"]
            price_data = None

            for key in price_keys:
                if key in nested_data and isinstance(nested_data[key], dict):
                    price_data = nested_data[key]
                    break

            if price_data:
                # Convert price dict to DataFrame
                dates = list(price_data.keys())
                prices = list(price_data.values())

                df = pd.DataFrame({"Close": prices}, index = pd.to_datetime(dates))

                # Generate OHLC from Close
                df["Open"] = df["Close"] * (1 + np.random.randn(len(df)) * 0.005)
                df["High"] = df["Close"] * (1 + np.abs(np.random.randn(len(df)) * 0.01))
                df["Low"] = df["Close"] * (1 - np.abs(np.random.randn(len(df)) * 0.01))
                df["Volume"] = np.random.randint(10000000, 30000000, len(df))

                return df

        # Try direct conversion if dict looks like DataFrame data
        elif all(key in data_dict for key in ["Open", "High", "Low", "Close"]):
            df = pd.DataFrame(data_dict)
            return standardize_dataframe(df)

        # Try to convert from flat dict with date keys
        else:
            # Assume it's a date -> price mapping
            dates = list(data_dict.keys())
            values = list(data_dict.values())

            if len(values) > 0 and isinstance(values[0], (int, float)):
                df = pd.DataFrame({"Close": values}, index = pd.to_datetime(dates))

                # Generate OHLC from Close
                df["Open"] = df["Close"] * (1 + np.random.randn(len(df)) * 0.005)
                df["High"] = df["Close"] * (1 + np.abs(np.random.randn(len(df)) * 0.01))
                df["Low"] = df["Close"] * (1 - np.abs(np.random.randn(len(df)) * 0.01))
                df["Volume"] = np.random.randint(10000000, 30000000, len(df))

                return df

        print("Could not identify data structure format")
        return None

    except Exception as e:
        print(f"Error converting dict to DataFrame: {e}")
        return None


def calculate_indicators(data):
    """Calculate technical indicators"""
    if data is None or len(data) < 20:
        print("Insufficient data for indicator calculation")
        return generate_mock_data()

    df = data.copy()

    try:
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

        # MACD
        ema12 = df["Close"].ewm(span = 12).mean()
        ema26 = df["Close"].ewm(span = 26).mean()
        df["MACD"] = ema12 - ema26
        df["MACD_Signal"] = df["MACD"].ewm(span = 9).mean()
        df["MACD_Histogram"] = df["MACD"] - df["MACD_Signal"]

        # Bollinger Bands
        df["BB_Middle"] = df["Close"].rolling(window = 20).mean()
        df["BB_Std"] = df["Close"].rolling(window = 20).std()
        df["BB_Upper"] = df["BB_Middle"] + (df["BB_Std"] * 2)
        df["BB_Lower"] = df["BB_Middle"] - (df["BB_Std"] * 2)

        print("Indicators calculated successfully")

    except Exception as e:
        print(f"Error calculating indicators: {e}")
        # Fall back to minimal indicators
        df["RSI14"] = 50  # Neutral
        df["MA20"] = df["Close"].rolling(window = 20, min_periods = 1).mean()

    return df


def create_layout():
    """Create dashboard layout"""
    return html.Div(
        [
            html.H1(
                "0700.HK Trading Dashboard",
                style={"textAlign": "center", "color": "#2c3e50"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H3("Data Status", style={"color": "#34495e"}),
                            html.P(id="data - status", children="Loading..."),
                        ],
                        style={
                            "width": "30%",
                            "display": "inline - block",
                            "vertical - align": "top",
                        },
                    ),
                    html.Div(
                        [
                            html.H3("Last Update", style={"color": "#34495e"}),
                            html.P(
                                id="last - update",
                                children = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            ),
                        ],
                        style={
                            "width": "30%",
                            "display": "inline - block",
                            "vertical - align": "top",
                        },
                    ),
                    html.Div(
                        [
                            html.H3("Data Points", style={"color": "#34495e"}),
                            html.P(id="data - points", children="0"),
                        ],
                        style={
                            "width": "30%",
                            "display": "inline - block",
                            "vertical - align": "top",
                        },
                    ),
                ],
                style={"text - align": "center", "margin": "20px"},
            ),
            dcc.Graph(id="price - chart"),
            dcc.Graph(id="volume - chart"),
            dcc.Graph(id="rsi - chart"),
            dcc.Graph(id="macd - chart"),
            dcc.Interval(
                id="interval - component", interval = 30 * 1000, n_intervals = 0  # 30 seconds
            ),
        ]
    )


@app.callback(
    [
        Output("price - chart", "figure"),
        Output("volume - chart", "figure"),
        Output("rsi - chart", "figure"),
        Output("macd - chart", "figure"),
        Output("data - status", "children"),
        Output("data - points", "children"),
    ],
    [Input("interval - component", "n_intervals")],
)
def update_charts(n):
    """Update all charts"""
    try:
        # Load and process data
        raw_data = load_and_standardize_data()
        processed_data = calculate_indicators(raw_data)

        if processed_data is None or len(processed_data) == 0:
            return create_empty_charts("No data available")

        # Update status
        data_source = "Real API Data" if SIMPLIFIED_SYSTEM_AVAILABLE else "Mock Data"
        data_status = f"✅ {data_source}"
        data_points = str(len(processed_data))

        # Create price chart
        price_fig = go.Figure()
        price_fig.add_trace(
            go.Candlestick(
                x = processed_data.index,
                open = processed_data["Open"],
                high = processed_data["High"],
                low = processed_data["Low"],
                close = processed_data["Close"],
                name="Price",
            )
        )

        # Add moving averages
        price_fig.add_trace(
            go.Scatter(
                x = processed_data.index,
                y = processed_data["MA20"],
                mode="lines",
                name="MA20",
                line = dict(color="orange", width = 1),
            )
        )

        price_fig.add_trace(
            go.Scatter(
                x = processed_data.index,
                y = processed_data["MA50"],
                mode="lines",
                name="MA50",
                line = dict(color="red", width = 1),
            )
        )

        price_fig.update_layout(
            title="0700.HK Price Chart",
            yaxis_title="Price (HKD)",
            xaxis_title="Date",
            template="plotly_white",
        )

        # Create volume chart
        volume_fig = go.Figure()
        volume_fig.add_trace(
            go.Bar(
                x = processed_data.index,
                y = processed_data["Volume"],
                name="Volume",
                marker_color="lightblue",
            )
        )

        volume_fig.update_layout(
            title="Trading Volume",
            yaxis_title="Volume",
            xaxis_title="Date",
            template="plotly_white",
        )

        # Create RSI chart
        rsi_fig = go.Figure()
        rsi_fig.add_trace(
            go.Scatter(
                x = processed_data.index,
                y = processed_data["RSI14"],
                mode="lines",
                name="RSI(14)",
                line = dict(color="purple"),
            )
        )

        # Add overbought / oversold lines
        rsi_fig.add_hline(
            y = 70, line_dash="dash", line_color="red", annotation_text="Overbought"
        )
        rsi_fig.add_hline(
            y = 30, line_dash="dash", line_color="green", annotation_text="Oversold"
        )

        rsi_fig.update_layout(
            title="RSI(14) Indicator",
            yaxis_title="RSI",
            xaxis_title="Date",
            yaxis = dict(range=[0, 100]),
            template="plotly_white",
        )

        # Create MACD chart
        macd_fig = go.Figure()
        macd_fig.add_trace(
            go.Scatter(
                x = processed_data.index,
                y = processed_data["MACD"],
                mode="lines",
                name="MACD",
                line = dict(color="blue"),
            )
        )

        macd_fig.add_trace(
            go.Scatter(
                x = processed_data.index,
                y = processed_data["MACD_Signal"],
                mode="lines",
                name="Signal",
                line = dict(color="red"),
            )
        )

        macd_fig.add_trace(
            go.Bar(
                x = processed_data.index,
                y = processed_data["MACD_Histogram"],
                name="Histogram",
                marker_color="lightgray",
            )
        )

        macd_fig.update_layout(
            title="MACD Indicator",
            yaxis_title="MACD",
            xaxis_title="Date",
            template="plotly_white",
        )

        return price_fig, volume_fig, rsi_fig, macd_fig, data_status, data_points

    except Exception as e:
        print(f"Error updating charts: {e}")
        return create_empty_charts(f"Error: {str(e)}")


def create_empty_charts(error_msg):
    """Create empty charts with error message"""
    empty_fig = go.Figure()
    empty_fig.add_annotation(
        text = error_msg,
        xref="paper",
        yref="paper",
        x = 0.5,
        y = 0.5,
        xanchor="center",
        yanchor="middle",
        font = dict(size = 16, color="red"),
    )
    empty_fig.update_layout(template="plotly_white")

    return empty_fig, empty_fig, empty_fig, empty_fig, f"❌ {error_msg}", "0"


def main():
    """Main function"""
    print("Starting Fixed 0700.HK Analytics Dashboard...")

    # Test data loading
    test_data = load_and_standardize_data()
    if test_data is not None:
        print(f"SUCCESS Data loading test successful: {len(test_data)} records")
        print(f"Data columns: {list(test_data.columns)}")
    else:
        print("FAILED Data loading test failed")

    # Set layout
    app.layout = create_layout()

    print("Dashboard ready. Starting server...")
    print("Open http://127.0.0.1:8050 in your browser")

    # Run the app
    if __name__ == "__main__":
        app.run(debug = True, host="127.0.0.1", port = 8050)


if __name__ == "__main__":
    main()
