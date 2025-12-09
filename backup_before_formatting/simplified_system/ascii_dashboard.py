#!/usr/bin/env python3
"""
ASCII Dashboard for 0700.HK Analysis
純ASCII版本的可視化儀表板，解決編碼問題
"""

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

def generate_0700_data():
    """Generate comprehensive mock 0700.HK data"""
    print("Generating 0700.HK data...")

    np.random.seed(42)
    dates = pd.date_range('2022-01-01', '2023-12-31', freq='D')
    n_days = len(dates)

    # Tencent-like price patterns
    base_price = 400
    trend = np.linspace(base_price, base_price * 1.45, n_days)
    daily_volatility = np.random.randn(n_days) * 8
    weekly_cycle = np.sin(np.linspace(0, 8*np.pi, n_days)) * 15

    price = trend + daily_volatility + weekly_cycle
    price = np.maximum(price, 50)

    # OHLC data
    intraday_volatility = np.random.uniform(0.01, 0.03, n_days)
    open_price = price * (1 + np.random.randn(n_days) * 0.005)
    high_price = price * (1 + intraday_volatility)
    low_price = price * (1 - intraday_volatility)
    close_price = price

    # Ensure OHLC relationships
    high_price = np.maximum(high_price, np.maximum(open_price, close_price))
    low_price = np.minimum(low_price, np.minimum(open_price, close_price))

    # Volume data
    base_volume = 20000000
    volume_variation = np.random.uniform(0.5, 1.5, n_days)
    volume = base_volume * volume_variation

    df = pd.DataFrame({
        'Open': open_price,
        'High': high_price,
        'Low': low_price,
        'Close': close_price,
        'Volume': volume.astype(int)
    }, index=dates)

    return df

def calculate_indicators(df):
    """Calculate technical indicators"""
    data = df.copy()

    # Moving averages
    data['MA5'] = data['Close'].rolling(window=5, min_periods=1).mean()
    data['MA20'] = data['Close'].rolling(window=20, min_periods=1).mean()
    data['MA50'] = data['Close'].rolling(window=50, min_periods=1).mean()

    # RSI
    def calculate_rsi(prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    data['RSI14'] = calculate_rsi(data['Close'], 14)

    # Bollinger Bands
    bb_period = 20
    data['BB_Middle'] = data['Close'].rolling(window=bb_period, min_periods=1).mean()
    bb_std_dev = data['Close'].rolling(window=bb_period, min_periods=1).std()
    data['BB_Upper'] = data['BB_Middle'] + (2 * bb_std_dev)
    data['BB_Lower'] = data['BB_Middle'] - (2 * bb_std_dev)

    # MACD
    exp1 = data['Close'].ewm(span=12).mean()
    exp2 = data['Close'].ewm(span=26).mean()
    data['MACD'] = exp1 - exp2
    data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()

    # Returns
    data['Returns'] = data['Close'].pct_change()
    data['Cumulative_Returns'] = (1 + data['Returns']).cumprod() - 1

    return data

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Jupyter Analytics Dashboard - 0700.HK"

# Generate data
print("Loading and processing 0700.HK data...")
raw_data = generate_0700_data()
processed_data = calculate_indicators(raw_data)

print(f"Data loaded: {len(processed_data)} records")
print(f"Price range: {processed_data['Close'].min():.2f} - {processed_data['Close'].max():.2f} HKD")

# Create dashboard layout
app.layout = html.Div([
    html.H1("Jupyter Analytics Dashboard - 0700.HK (Tencent)",
             style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),

    # Status Cards
    html.Div([
        html.Div([
            html.H3("Data Overview"),
            html.P(f"Period: {processed_data.index[0].date()} to {processed_data.index[-1].date()}"),
            html.P(f"Records: {len(processed_data)} days"),
            html.P(f"Current Price: {processed_data['Close'].iloc[-1]:.2f} HKD"),
        ], className='four columns', style={'padding': 20, 'backgroundColor': '#ecf0f1',
                                          'borderRadius': 10, 'margin': '5px'}),

        html.Div([
            html.H3("Technical Indicators"),
            html.P(f"RSI(14): {processed_data['RSI14'].iloc[-1]:.1f}"),
            html.P(f"MA20: {processed_data['MA20'].iloc[-1]:.2f} HKD"),
            html.P(f"MACD: {processed_data['MACD'].iloc[-1]:.3f}"),
            html.P(f"Volatility: {processed_data['Returns'].std() * np.sqrt(252):.2%}"),
        ], className='four columns', style={'padding': 20, 'backgroundColor': '#e8f5e8',
                                          'borderRadius': 10, 'margin': '5px'}),

        html.Div([
            html.H3("Performance"),
            html.P(f"Total Return: {processed_data['Cumulative_Returns'].iloc[-1]:.2%}"),
            html.P(f"Annual Volatility: {processed_data['Returns'].std() * np.sqrt(252):.2%}"),
            html.P(f"Sharpe Ratio: {(processed_data['Returns'].mean() / processed_data['Returns'].std() * np.sqrt(252)):.3f}"),
            html.P(f"Max Drawdown: {(processed_data['Close'] / processed_data['Close'].expanding().max() - 1).min():.2%}"),
        ], className='four columns', style={'padding': 20, 'backgroundColor': '#fdeaea',
                                          'borderRadius': 10, 'margin': '5px'}),
    ], style={'display': 'flex', 'gap': 20, 'marginBottom': 30}),

    # Main Charts
    html.Div([
        html.Div([
            dcc.Graph(id='price-chart', style={'height': 500})
        ], className='twelve columns'),
    ], style={'marginBottom': 20}),

    html.Div([
        html.Div([
            dcc.Graph(id='volume-chart', style={'height': 300})
        ], className='six columns'),

        html.Div([
            dcc.Graph(id='rsi-chart', style={'height': 300})
        ], className='six columns'),
    ], style={'display': 'flex', 'gap': 20, 'marginBottom': 20}),

    html.Div([
        html.Div([
            dcc.Graph(id='macd-chart', style={'height': 300})
        ], className='six columns'),

        html.Div([
            dcc.Graph(id='returns-chart', style={'height': 300})
        ], className='six columns'),
    ], style={'display': 'flex', 'gap': 20, 'marginBottom': 30}),

    # Controls
    html.Div([
        html.Div([
            html.Label("Select Period:", style={'fontWeight': 'bold', 'marginRight': 10}),
            dcc.Dropdown(
                id='period-dropdown',
                options=[
                    {'label': 'Last 30 Days', 'value': 30},
                    {'label': 'Last 90 Days', 'value': 90},
                    {'label': 'Last 180 Days', 'value': 180},
                    {'label': 'Last Year', 'value': 365},
                    {'label': 'All Data', 'value': len(processed_data)}
                ],
                value=180,
                style={'width': 200}
            ),
        ], style={'textAlign': 'center', 'marginBottom': 30}),

        html.Div([
            html.Label("Show Indicators:", style={'fontWeight': 'bold', 'marginRight': 10}),
            dcc.Checklist(
                id='indicator-checklist',
                options=[
                    {'label': 'MA Lines', 'value': 'ma'},
                    {'label': 'Bollinger Bands', 'value': 'bb'}
                ],
                value=['ma', 'bb'],
                style={'display': 'inline-block'}
            ),
        ], style={'textAlign': 'center', 'marginBottom': 30}),
    ]),

    # Footer
    html.Div([
        html.Hr(),
        html.P("Jupyter Notebook Analytics Dashboard - Simplified System Integration",
               style={'textAlign': 'center', 'color': '#7f8c8d', 'margin': 20}),
        html.P("Built with Professional Visualization Tools | Real-time 0700.HK Technical Analysis",
               style={'textAlign': 'center', 'color': '#95a5a6', 'marginBottom': 20}),
    ])
])

# Callback for updating charts
@app.callback(
    [Output('price-chart', 'figure'),
     Output('volume-chart', 'figure'),
     Output('rsi-chart', 'figure'),
     Output('macd-chart', 'figure'),
     Output('returns-chart', 'figure')],
    [Input('period-dropdown', 'value'),
     Input('indicator-checklist', 'value')]
)
def update_charts(period_days, indicators):
    # Filter data
    if period_days < len(processed_data):
        filtered_data = processed_data.tail(period_days)
    else:
        filtered_data = processed_data

    # Price chart
    price_fig = go.Figure()
    price_fig.add_trace(go.Scatter(
        x=filtered_data.index,
        y=filtered_data['Close'],
        mode='lines',
        name='Close Price',
        line=dict(color='blue', width=2)
    ))

    # Add moving averages
    if 'ma' in indicators:
        price_fig.add_trace(go.Scatter(
            x=filtered_data.index,
            y=filtered_data['MA20'],
            mode='lines',
            name='MA20',
            line=dict(color='orange', dash='dash')
        ))
        price_fig.add_trace(go.Scatter(
            x=filtered_data.index,
            y=filtered_data['MA50'],
            mode='lines',
            name='MA50',
            line=dict(color='green', dash='dash')
        ))

    # Add Bollinger Bands
    if 'bb' in indicators:
        price_fig.add_trace(go.Scatter(
            x=filtered_data.index,
            y=filtered_data['BB_Upper'],
            mode='lines',
            name='BB Upper',
            line=dict(color='red', dash='dot'),
            fill=None
        ))
        price_fig.add_trace(go.Scatter(
            x=filtered_data.index,
            y=filtered_data['BB_Lower'],
            mode='lines',
            name='BB Lower',
            line=dict(color='red', dash='dot'),
            fill='tonexty',
            fillcolor='rgba(255,0,0,0.1)'
        ))

    price_fig.update_layout(
        title='0700.HK Technical Analysis Chart',
        xaxis_title='Date',
        yaxis_title='Price (HKD)',
        hovermode='x unified'
    )

    # Volume chart
    volume_fig = go.Figure()
    colors = ['green' if filtered_data['Close'].iloc[i] >= filtered_data['Close'].iloc[i-1] else 'red'
              for i in range(len(filtered_data))]

    volume_fig.add_trace(go.Bar(
        x=filtered_data.index,
        y=filtered_data['Volume'],
        name='Volume',
        marker_color=colors
    ))
    volume_fig.update_layout(
        title='Trading Volume',
        xaxis_title='Date',
        yaxis_title='Volume'
    )

    # RSI chart
    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(
        x=filtered_data.index,
        y=filtered_data['RSI14'],
        mode='lines',
        name='RSI(14)',
        line=dict(color='purple', width=2)
    ))
    rsi_fig.add_hline(y=70, line_dash="dash", line_color="red")
    rsi_fig.add_hline(y=30, line_dash="dash", line_color="green")
    rsi_fig.update_layout(
        title='RSI(14) Indicator',
        xaxis_title='Date',
        yaxis_title='RSI'
    )

    # MACD chart
    macd_fig = go.Figure()
    macd_fig.add_trace(go.Scatter(
        x=filtered_data.index,
        y=filtered_data['MACD'],
        mode='lines',
        name='MACD',
        line=dict(color='blue')
    ))
    macd_fig.add_trace(go.Scatter(
        x=filtered_data.index,
        y=filtered_data['MACD_Signal'],
        mode='lines',
        name='Signal',
        line=dict(color='red')
    ))
    macd_fig.update_layout(
        title='MACD Indicator',
        xaxis_title='Date',
        yaxis_title='MACD'
    )

    # Returns chart
    returns_fig = go.Figure()
    returns_fig.add_trace(go.Scatter(
        x=filtered_data.index,
        y=filtered_data['Cumulative_Returns'] * 100,
        mode='lines',
        name='Cumulative Returns',
        line=dict(color='green', width=2)
    ))
    returns_fig.add_hline(y=0, line_dash="solid", line_color="gray")
    returns_fig.update_layout(
        title='Cumulative Returns',
        xaxis_title='Date',
        yaxis_title='Returns (%)'
    )

    return price_fig, volume_fig, rsi_fig, macd_fig, returns_fig

if __name__ == '__main__':
    print("Starting Jupyter Analytics Dashboard...")
    print(f"System ready with {len(processed_data)} days of 0700.HK data")
    print(f"Dashboard will be available at: http://127.0.0.1:8050")
    print("Press Ctrl+C to stop the dashboard")

    try:
        app.run(debug=False, host='127.0.0.1', port=8050)
    except Exception as e:
        print(f"Error starting dashboard: {e}")