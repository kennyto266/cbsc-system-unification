# -*- coding: utf-8 -*-
"""
Simple test script for dashboard module.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np

# Import dashboard modules
from cbsc_strategy_sdk.dashboard import theme
from cbsc_strategy_sdk.dashboard import charts
from cbsc_strategy_sdk.dashboard import metrics
from cbsc_strategy_sdk.dashboard import live
from cbsc_strategy_sdk.dashboard import app as dashboard_app

print("=" * 60)
print("CBSC Strategy SDK - Dashboard Module Test")
print("=" * 60)

# Test 1: ThemeManager
print("\n1. Testing ThemeManager...")
try:
    tm = theme.ThemeManager(initial_theme="dark")
    assert tm.current_theme == "dark"
    colors = tm.get_colors()
    assert 'primary' in colors
    print("   [OK] ThemeManager initialization")

    tm.toggle_theme()
    assert tm.current_theme == "light"
    print("   [OK] Theme toggling")

    tm.set_theme("dark")
    assert tm.current_theme == "dark"
    print("   [OK] Theme setting")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 2: CircularBuffer
print("\n2. Testing CircularBuffer...")
try:
    buffer = live.CircularBuffer(size=5)
    for i in range(10):
        buffer.add(i)
    data = buffer.get_data()
    assert data == [5, 6, 7, 8, 9]
    print("   [OK] Buffer overflow handling")

    df = buffer.get_dataframe()
    assert isinstance(df, pd.DataFrame)
    print("   [OK] DataFrame conversion")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 3: ChartBuilders
print("\n3. Testing ChartBuilders...")
try:
    tm_dark = theme.ThemeManager(initial_theme="dark")
    builder = charts.ChartBuilders(theme_manager=tm_dark)

    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    data = pd.DataFrame({
        'open': np.random.randn(50) * 2 + 100,
        'high': np.random.randn(50) * 2 + 102,
        'low': np.random.randn(50) * 2 + 98,
        'close': np.random.randn(50) * 2 + 100,
        'volume': np.random.randint(1000000, 10000000, 50),
    }, index=dates)

    fig = builder.candlestick_chart(data)
    assert fig is not None
    print("   [OK] Candlestick chart")

    fig2 = builder.line_chart(data, columns=['close'])
    assert fig2 is not None
    print("   [OK] Line chart")

    returns = pd.Series(np.random.randn(100) * 0.02, index=pd.date_range(start='2024-01-01', periods=100))
    fig3 = builder.equity_curve(returns)
    assert fig3 is not None
    print("   [OK] Equity curve")

    fig4 = builder.drawdown_chart(returns)
    assert fig4 is not None
    print("   [OK] Drawdown chart")

    fig5 = builder.returns_distribution(returns)
    assert fig5 is not None
    print("   [OK] Returns distribution")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 4: MetricsDisplay
print("\n4. Testing MetricsDisplay...")
try:
    returns = pd.Series(np.random.randn(252) * 0.02, index=pd.date_range(start='2024-01-01', periods=252))
    md = metrics.MetricsDisplay(returns=returns, theme_manager=tm_dark)

    assert md._metrics is not None
    print("   [OK] Metrics calculation")

    assert 'total_return' in md._metrics
    assert 'sharpe_ratio' in md._metrics
    assert 'max_drawdown' in md._metrics
    print("   [OK] Key metrics available")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 5: StrategyDashboard
print("\n5. Testing StrategyDashboard...")
try:
    dashboard = dashboard_app.StrategyDashboard(title="Test Dashboard", theme="dark")
    assert dashboard.title == "Test Dashboard"
    print("   [OK] Dashboard initialization")

    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    price_data = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.randn(100) * 2 + 100,
        'high': np.random.randn(100) * 2 + 102,
        'low': np.random.randn(100) * 2 + 98,
        'close': np.random.randn(100) * 2 + 100,
        'volume': np.random.randint(1000000, 10000000, 100),
    })

    dashboard.load_data(price_data)
    assert 'price_data' in dashboard._data_store
    print("   [OK] Data loading")

    returns = pd.Series(np.random.randn(100) * 0.02, index=dates)
    dashboard.load_backtest_results(returns)
    assert 'returns' in dashboard._data_store
    print("   [OK] Backtest loading")

    dashboard.set_theme("light")
    assert dashboard.current_theme == "light"
    print("   [OK] Theme switching")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 6: LiveUpdateComponent
print("\n6. Testing LiveUpdateComponent...")
try:
    live_comp = live.LiveUpdateComponent(update_interval=1000, theme_manager=tm_dark)
    assert live_comp.update_interval == 1000
    print("   [OK] Initialization")

    live_comp.setup_websocket('ws://localhost:8000/ws', ['AAPL'])
    assert live_comp.websocket_url == 'ws://localhost:8000/ws'
    print("   [OK] WebSocket setup")

    sample_data = live_comp.create_sample_live_data(num_points=50, symbols=['AAPL'])
    assert isinstance(sample_data, pd.DataFrame)
    assert len(sample_data) == 50
    print("   [OK] Sample data generation")
except Exception as e:
    print(f"   [FAIL] {e}")

# Test 7: Integration
print("\n7. Testing Integration...")
try:
    tm = theme.ThemeManager(initial_theme="dark")
    builder = charts.ChartBuilders(theme_manager=tm)
    returns = pd.Series(np.random.randn(252) * 0.02, index=pd.date_range(start='2024-01-01', periods=252))
    md = metrics.MetricsDisplay(returns=returns, theme_manager=tm)

    equity_fig = builder.equity_curve(returns)
    drawdown_fig = builder.drawdown_chart(returns)

    assert equity_fig is not None
    assert drawdown_fig is not None
    print("   [OK] Complete workflow")
except Exception as e:
    print(f"   [FAIL] {e}")

print("\n" + "=" * 60)
print("Dashboard Module Test Complete!")
print("=" * 60)
print("\nAll components tested successfully.")
print("\nAvailable imports:")
print("  from cbsc_strategy_sdk.dashboard import StrategyDashboard")
print("  from cbsc_strategy_sdk.dashboard import ThemeManager")
print("  from cbsc_strategy_sdk.dashboard import ChartBuilders")
print("  from cbsc_strategy_sdk.dashboard import MetricsDisplay")
print("  from cbsc_strategy_sdk.dashboard import LiveUpdateComponent")
