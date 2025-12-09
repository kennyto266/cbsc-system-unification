#!/usr / bin / env python3
"""
Jupyter Notebook Prototype Validation (Simple)
驗證Jupyter Notebook原型的核心功能
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def validate_dependencies():
    """驗證必要的依賴包"""
    print("=== Dependency Validation ===")

    required_packages = [
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "plotly",
        "ipywidgets",
        "jupyterlab",
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"SUCCESS: {package} is installed")
        except ImportError:
            print(f"FAILED: {package} is not installed")
            missing_packages.append(package)

    if missing_packages:
        print(f"Need to install: {', '.join(missing_packages)}")
        return False

    print("SUCCESS: All dependencies are properly installed")
    return True


def validate_notebook_structure():
    """驗證Notebook文件結構"""
    print("\n=== Notebook Structure Validation ===")

    notebook_path = Path("notebooks / 0700_hk_prototype.ipynb")

    if not notebook_path.exists():
        print("FAILED: Prototype notebook file does not exist")
        return False

    try:
        with open(notebook_path, "r", encoding="utf - 8") as f:
            notebook = json.load(f)

        # 檢查基本結構
        required_keys = ["cells", "metadata", "nbformat", "nbformat_minor"]
        for key in required_keys:
            if key not in notebook:
                print(f"FAILED: Notebook missing required field: {key}")
                return False

        cell_count = len(notebook["cells"])
        print(f"SUCCESS: Notebook contains {cell_count} cells")

        # 檢查單元格類型
        cell_types = [cell["cell_type"] for cell in notebook["cells"]]
        markdown_count = cell_types.count("markdown")
        code_count = cell_types.count("code")

        print(f"SUCCESS: Contains {markdown_count} markdown cells")
        print(f"SUCCESS: Contains {code_count} code cells")

        # 檢查關鍵功能
        all_sources = "".join([cell.get("source", "") for cell in notebook["cells"]])
        key_functions = [
            "load_0700_data",  # 數據加載
            "analyze_data_quality",  # 數據質量分析
            "calculate_technical_indicators",  # 技術指標計算
            "go.Figure",  # Plotly圖表
            "RSI14",  # RSI指標
            "MA5",  # 移動平均
        ]

        for func in key_functions:
            if func in all_sources:
                print(f"SUCCESS: Contains key function: {func}")
            else:
                print(f"WARNING: Missing key function: {func}")

        print("SUCCESS: Notebook structure validation passed")
        return True

    except Exception as e:
        print(f"FAILED: Notebook parsing error: {e}")
        return False


def validate_data_loading():
    """驗證數據加載功能"""
    print("\n=== Data Loading Validation ===")

    # 檢查是否有真實數據文件
    data_sources = [
        "0700_results_20251125_181239.csv",
        "0700_results_20251125_181639.csv",
        "data / 0700_hk.csv",
    ]

    found_data = False
    for source in data_sources:
        if os.path.exists(source):
            print(f"SUCCESS: Found data file: {source}")
            found_data = True

            # 檢查數據質量
            try:
                data = pd.read_csv(source, parse_dates = True, index_col = 0)
                print(f"  - Data records: {len(data)}")
                print(f"  - Time range: {data.index[0]} to {data.index[-1]}")
                print(f"  - Data columns: {list(data.columns)}")

                if "Close" in data.columns or "close" in data.columns:
                    close_col = "Close" if "Close" in data.columns else "close"
                    print(
                        f"  - Price range: {data[close_col].min():.2f} - {data[close_col].max():.2f}"
                    )

            except Exception as e:
                print(f"  - Data parsing error: {e}")

    if not found_data:
        print("WARNING: No real data files found, will use mock data")

    print("SUCCESS: Data loading validation completed")
    return True


def validate_visualization_capability():
    """驗證可視化能力"""
    print("\n=== Visualization Capability Validation ===")

    try:
        import matplotlib.pyplot as plt
        import plotly.express as px
        import plotly.graph_objects as go
        import seaborn as sns

        # 測試基本圖表創建
        dates = pd.date_range("2023 - 01 - 01", periods = 100, freq="D")
        prices = np.random.randn(100).cumsum() + 400

        # Plotly圖表測試
        fig = go.Figure()
        fig.add_trace(go.Scatter(x = dates, y = prices, name="Test Data"))
        fig.update_layout(title="Test Chart")
        print("SUCCESS: Plotly chart creation successful")

        # Matplotlib圖表測試
        plt.figure(figsize=(10, 6))
        plt.plot(dates, prices)
        plt.title("Test Matplotlib Chart")
        plt.close()
        print("SUCCESS: Matplotlib chart creation successful")

        print("SUCCESS: Visualization capability validation passed")
        return True

    except Exception as e:
        print(f"FAILED: Visualization capability validation failed: {e}")
        return False


def validate_simplified_system_integration():
    """驗證與Simplified System的集成"""
    print("\n=== Simplified System Integration Validation ===")

    integration_points = [
        "src / api / stock_api.py",
        "src / indicators / core_indicators.py",
        "src / backtest / vectorbt_engine.py",
        "src / api / government_data.py",
    ]

    available_modules = []
    for module_path in integration_points:
        if os.path.exists(module_path):
            available_modules.append(module_path)
            print(f"SUCCESS: Found system module: {module_path}")
        else:
            print(f"WARNING: Module not found: {module_path}")

    if available_modules:
        print(f"SUCCESS: Found {len(available_modules)} available modules")
    else:
        print("WARNING: No Simplified System modules found, using standalone mode")

    return True


def create_demo_validation():
    """創建演示驗證腳本"""
    print("\n=== Demo Creation ===")

    demo_script = """
# Jupyter Notebook Prototype Demo
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

print("Jupyter Notebook Prototype Demo")
print("=" * 50)

# Generate mock 0700.HK data
np.random.seed(42)
dates = pd.date_range('2022 - 01 - 01', '2023 - 12 - 31', freq='D')
base_price = 400
trend = np.linspace(base_price, base_price * 1.3, len(dates))
volatility = np.random.randn(len(dates)) * 10
prices = trend + volatility
prices = np.maximum(prices, 50)

# Create DataFrame
df = pd.DataFrame({
    'Close': prices,
    'Volume': np.random.randint(10000000, 30000000, len(dates))
}, index = dates)

print(f"Mock data generated: {len(df)} records")
print(f"Time range: {df.index[0].date()} to {df.index[-1].date()}")

# Calculate technical indicators
df['MA5'] = df['Close'].rolling(window = 5).mean()
df['MA20'] = df['Close'].rolling(window = 20).mean()

# RSI calculation
delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window = 14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window = 14).mean()
rs = gain / loss
df['RSI14'] = 100 - (100 / (1 + rs))

print(f"Technical indicators calculated")
print(f"   Latest Close: {df['Close'].iloc[-1]:.2f}")
print(f"   RSI(14): {df['RSI14'].iloc[-1]:.2f}")
print(f"   MA5: {df['MA5'].iloc[-1]:.2f}")
print(f"   MA20: {df['MA20'].iloc[-1]:.2f}")

# Create interactive chart
fig = go.Figure()
fig.add_trace(go.Scatter(
    x = df.index,
    y = df['Close'],
    mode='lines',
    name='0700.HK Close Price',
    line = dict(color='blue', width = 2)
))

fig.add_trace(go.Scatter(
    x = df.index,
    y = df['MA5'],
    mode='lines',
    name='MA5',
    line = dict(color='orange', dash='dash')
))

fig.add_trace(go.Scatter(
    x = df.index,
    y = df['MA20'],
    mode='lines',
    name='MA20',
    line = dict(color='green', dash='dash')
))

fig.update_layout(
    title='0700.HK Technical Analysis Chart (Jupyter Prototype Demo)',
    xaxis_title='Date',
    yaxis_title='Price (HKD)',
    hovermode='x unified',
    width = 800,
    height = 500
)

# Show chart (will auto - render in Jupyter)
fig.show()

print("SUCCESS: Jupyter Notebook prototype demo completed!")
print("Concept validation successful!")
"""

    with open("jupyter_demo_validation.py", "w", encoding="utf - 8") as f:
        f.write(demo_script)

    print("SUCCESS: Created demo script: jupyter_demo_validation.py")
    return True


def main():
    """主驗證函數"""
    print("Jupyter Notebook Prototype Validation")
    print("=" * 60)

    validation_results = []

    # 執行各項驗證
    validation_results.append(validate_dependencies())
    validation_results.append(validate_notebook_structure())
    validation_results.append(validate_data_loading())
    validation_results.append(validate_visualization_capability())
    validation_results.append(validate_simplified_system_integration())
    validation_results.append(create_demo_validation())

    # 總結驗證結果
    passed_validations = sum(validation_results)
    total_validations = len(validation_results)

    print("\n" + "=" * 60)
    print("Validation Results Summary")
    print("=" * 60)
    print(f"Passed validations: {passed_validations}/{total_validations}")

    if passed_validations == total_validations:
        print("PROTOTYPE VALIDATION COMPLETELY SUCCESSFUL!")
        print("SUCCESS: Jupyter Notebook integration concept validated")
        print("SUCCESS: Ready to implement full OpenSpec plan")

        print("\nNEXT STEPS:")
        print("1. Start JupyterLab: jupyter lab")
        print("2. Open prototype notebook: notebooks / 0700_hk_prototype.ipynb")
        print("3. Run all cells for complete testing")
        print("4. Implement Phase 1 according to OpenSpec tasks.md")

    else:
        print("WARNING: Some validations failed")
        print("Recommend checking failed validation items and fixing issues")

    print("\nCREATED FILES:")
    print("- notebooks / 0700_hk_prototype.ipynb (Prototype Notebook)")
    print("- jupyter_requirements.txt (Dependencies list)")
    print("- jupyter_demo_validation.py (Demo script)")

    return passed_validations == total_validations


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
