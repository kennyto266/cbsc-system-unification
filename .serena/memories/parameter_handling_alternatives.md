# Parameter Handling Alternatives to Marimo

## Current Marimo Implementation Analysis

### How Parameters Are Currently Handled
The current system uses Marimo for interactive parameter controls:

```python
# From cbsc_marimo_production.py
rsi_period = mo.ui.slider(5, 50, value=14, label="RSI 週期")
sentiment_threshold = mo.ui.slider(0.1, 1.0, value=0.7, step=0.05, label="情緒閾值")
ma_short = mo.ui.slider(5, 30, value=10, label="短期均線")
ma_long = mo.ui.slider(20, 100, value=30, label="長期均線")
enable_analysis = mo.ui.switch(label="啟用詳細分析", value=True)
```

**Advantages of Current Marimo Setup:**
- Simple, declarative UI components
- Automatic reactive updates
- Good for notebook-based workflows
- Built-in state management

**Limitations:**
- Requires Marimo runtime environment
- Limited to notebook context
- Not easily integrated into web dashboards
- Dependency on Marimo framework

## Alternative Interactive Control Solutions

### 1. **FastAPI + HTML/CSS/JavaScript (Recommended)**
**Architecture**: FastAPI backend + HTML/CSS/JavaScript frontend

**Implementation Example**:
```html
<!-- HTML Controls -->
<div class="parameter-controls">
    <label>RSI Period: <input type="range" id="rsiPeriod" min="5" max="50" value="14"></label>
    <label>Sentiment Threshold: <input type="range" id="sentimentThreshold" min="0.1" max="1.0" step="0.05" value="0.7"></label>
    <button onclick="updateStrategy()">Update Strategy</button>
</div>

<script>
async function updateStrategy() {
    const params = {
        rsi_period: document.getElementById('rsiPeriod').value,
        sentiment_threshold: document.getElementById('sentimentThreshold').value
    };
    
    const response = await fetch('/api/strategy/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(params)
    });
    
    const results = await response.json();
    updateCharts(results);
}
</script>
```

**Backend (FastAPI)**:
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class StrategyParameters(BaseModel):
    rsi_period: int = 14
    sentiment_threshold: float = 0.7
    ma_short: int = 10
    ma_long: int = 30

@app.post("/api/strategy/update")
async def update_strategy(params: StrategyParameters):
    # Use existing strategy calculation logic
    results = calculate_cbsc_strategy(params.dict())
    return results
```

**Pros:**
- ✅ Already integrated in current dashboard (`src/dashboard/dashboard_ui.py`)
- ✅ Full control over UI/UX design
- ✅ Scalable to production web applications
- ✅ No additional dependencies beyond current stack
- ✅ Can be easily integrated with existing WebSocket system

**Cons:**
- ❌ Requires more frontend development work
- ❌ Manual state management needed

### 2. **Plotly Dash Integration**
**Architecture**: Plotly Dash web application framework

**Implementation Example**:
```python
import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("CBSC Strategy Controls"),
    
    dcc.Slider(
        id='rsi-period-slider',
        min=5, max=50, step=1, value=14,
        marks={i: str(i) for i in range(5, 51, 10)}
    ),
    
    dcc.Slider(
        id='sentiment-threshold-slider',
        min=0.1, max=1.0, step=0.05, value=0.7,
        marks={i/10: f"{i/10:.1f}" for i in range(1, 11)}
    ),
    
    dcc.Graph(id='strategy-chart'),
    html.Div(id='strategy-metrics')
])

@app.callback(
    [Output('strategy-chart', 'figure'),
     Output('strategy-metrics', 'children')],
    [Input('rsi-period-slider', 'value'),
     Input('sentiment-threshold-slider', 'value')]
)
def update_strategy(rsi_period, sentiment_threshold):
    # Use existing CBSC strategy calculation
    results = calculate_cbsc_strategy({
        'rsi_period': rsi_period,
        'sentiment_threshold': sentiment_threshold
    })
    
    figure = create_strategy_chart(results)
    metrics = create_metrics_display(results)
    
    return figure, metrics

if __name__ == '__main__':
    app.run_server(debug=True)
```

**Pros:**
- ✅ Professional interactive components
- ✅ Built-in charts and visualizations
- ✅ Reactive updates like Marimo
- ✅ Production-ready framework
- ✅ Integrates well with Plotly (already in dependencies)

**Cons:**
- ❌ Additional dependency to learn
- ❌ Different architecture from current FastAPI dashboard
- ❌ May duplicate existing dashboard functionality

### 3. **Streamlit Integration**
**Architecture**: Streamlit web application framework

**Implementation Example**:
```python
import streamlit as st
import pandas as pd
import numpy as np

st.title("CBSC Strategy Parameter Optimizer")

# Parameter controls
st.sidebar.header("Strategy Parameters")
rsi_period = st.sidebar.slider("RSI Period", 5, 50, 14)
sentiment_threshold = st.sidebar.slider("Sentiment Threshold", 0.1, 1.0, 0.05, 0.7)
ma_short = st.sidebar.slider("MA Short", 5, 30, 10)
ma_long = st.sidebar.slider("MA Long", 20, 100, 30)

# Strategy calculation
if st.sidebar.button("Calculate Strategy"):
    params = {
        'rsi_period': rsi_period,
        'sentiment_threshold': sentiment_threshold,
        'ma_short': ma_short,
        'ma_long': ma_long
    }
    
    results = calculate_cbsc_strategy(params)
    
    # Display results
    st.header("Strategy Results")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Sharpe Ratio", f"{results['sharpe_ratio']:.3f}")
    col2.metric("Total Return", f"{results['total_return']:.2%}")
    col3.metric("Max Drawdown", f"{results['max_drawdown']:.2%}")
    col4.metric("Win Rate", f"{results['win_rate']:.1%}")
    
    # Charts
    st.subheader("Equity Curve")
    st.line_chart(results['equity_curve'])
```

**Pros:**
- ✅ Very simple to implement
- ✅ Automatic reactive updates
- ✅ Built-in components and charts
- ✅ Low learning curve

**Cons:**
- ❌ Less flexible than custom HTML/CSS
- ❌ Different styling from current dashboard
- ❌ May not integrate well with existing FastAPI architecture

### 4. **Jupyter Widgets + Voilà**
**Architecture**: Jupyter widgets with Voilà for web deployment

**Implementation Example**:
```python
import ipywidgets as widgets
from IPython.display import display
import matplotlib.pyplot as plt

# Create interactive widgets
rsi_period = widgets.IntSlider(value=14, min=5, max=50, description='RSI Period:')
sentiment_threshold = widgets.FloatSlider(value=0.7, min=0.1, max=1.0, step=0.05, description='Sentiment Threshold:')
calculate_btn = widgets.Button(description='Calculate Strategy')

# Output widget for results
output = widgets.Output()

def calculate_strategy_callback(b):
    with output:
        output.clear_output()
        
        params = {
            'rsi_period': rsi_period.value,
            'sentiment_threshold': sentiment_threshold.value
        }
        
        results = calculate_cbsc_strategy(params)
        
        # Display results
        print(f"Sharpe Ratio: {results['sharpe_ratio']:.3f}")
        print(f"Total Return: {results['total_return']:.2%}")
        
        # Plot results
        plt.figure(figsize=(10, 6))
        plt.plot(results['equity_curve'])
        plt.title('Strategy Equity Curve')
        plt.show()

calculate_btn.on_click(calculate_strategy_callback)

# Display widgets
display(widgets.VBox([rsi_period, sentiment_threshold, calculate_btn, output]))
```

**Pros:**
- ✅ Good for notebook workflows
- ✅ Interactive widgets similar to Marimo
- ✅ Can use existing calculation code

**Cons:**
- ❌ Still requires notebook environment
- ❌ Voilà deployment adds complexity
- ❌ Not as flexible as web application

## Recommended Approach: FastAPI + HTML/CSS/JavaScript

Given the current system architecture and requirements, I recommend **Option 1: FastAPI + HTML/CSS/JavaScript** for the following reasons:

### Integration Strategy
1. **Leverage Existing Architecture**: The system already has a FastAPI dashboard (`src/dashboard/dashboard_ui.py`)
2. **WebSocket Integration**: Use existing WebSocket system for real-time updates
3. **Modular Design**: Create parameter controls as reusable components
4. **API Integration**: Use existing strategy calculation APIs

### Implementation Plan
1. **Extend Current Dashboard**: Add parameter control components to existing dashboard
2. **Create Strategy API Endpoints**: RESTful endpoints for parameter updates and calculations
3. **Real-time Updates**: Use WebSocket for immediate feedback on parameter changes
4. **Responsive Design**: Mobile-friendly interface that works with existing UI

### Technical Integration Points
- **File**: `src/dashboard/dashboard_ui.py` - Add parameter control routes
- **File**: `src/dashboard/html_generator.py` - Generate interactive control HTML
- **File**: `src/dashboard/websocket_manager.py` - Real-time parameter updates
- **File**: `cbsc_parameter_optimizer.py` - Reuse existing calculation logic

This approach provides the best balance of functionality, integration ease, and maintainability while avoiding the dependency limitations of Marimo.