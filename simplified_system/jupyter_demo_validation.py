# Jupyter Notebook Prototype Demo

import numpy as np
import pandas as pd
import plotly.graph_objects as go

print("Jupyter Notebook Prototype Demo")
print("=" * 50)

# Generate mock 0700.HK data
np.random.seed(42)
dates = pd.date_range("2022 - 01 - 01", "2023 - 12 - 31", freq="D")
base_price = 400
trend = np.linspace(base_price, base_price * 1.3, len(dates))
volatility = np.random.randn(len(dates)) * 10
prices = trend + volatility
prices = np.maximum(prices, 50)

# Create DataFrame
df = pd.DataFrame(
    {"Close": prices, "Volume": np.random.randint(10000000, 30000000, len(dates))},
    index = dates,
)

print(f"Mock data generated: {len(df)} records")
print(f"Time range: {df.index[0].date()} to {df.index[-1].date()}")

# Calculate technical indicators
df["MA5"] = df["Close"].rolling(window = 5).mean()
df["MA20"] = df["Close"].rolling(window = 20).mean()

# RSI calculation
delta = df["Close"].diff()
gain = (delta.where(delta > 0, 0)).rolling(window = 14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window = 14).mean()
rs = gain / loss
df["RSI14"] = 100 - (100 / (1 + rs))

print(f"Technical indicators calculated")
print(f"   Latest Close: {df['Close'].iloc[-1]:.2f}")
print(f"   RSI(14): {df['RSI14'].iloc[-1]:.2f}")
print(f"   MA5: {df['MA5'].iloc[-1]:.2f}")
print(f"   MA20: {df['MA20'].iloc[-1]:.2f}")

# Create interactive chart
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x = df.index,
        y = df["Close"],
        mode="lines",
        name="0700.HK Close Price",
        line = dict(color="blue", width = 2),
    )
)

fig.add_trace(
    go.Scatter(
        x = df.index,
        y = df["MA5"],
        mode="lines",
        name="MA5",
        line = dict(color="orange", dash="dash"),
    )
)

fig.add_trace(
    go.Scatter(
        x = df.index,
        y = df["MA20"],
        mode="lines",
        name="MA20",
        line = dict(color="green", dash="dash"),
    )
)

fig.update_layout(
    title="0700.HK Technical Analysis Chart (Jupyter Prototype Demo)",
    xaxis_title="Date",
    yaxis_title="Price (HKD)",
    hovermode="x unified",
    width = 800,
    height = 500,
)

# Show chart (will auto - render in Jupyter)
fig.show()

print("SUCCESS: Jupyter Notebook prototype demo completed!")
print("Concept validation successful!")
