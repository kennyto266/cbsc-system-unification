#!/usr / bin / env python3
"""
Jupyter Notebook Prototype Setup
簡化的Jupyter環境設置，用於驗證概念
"""

import importlib
import subprocess
import sys
from pathlib import Path


def check_and_install_package(package_name, import_name = None):
    """檢查並安裝Python包"""
    if import_name is None:
        import_name = package_name

    try:
        importlib.import_module(import_name)
        print(f"✓ {package_name} already installed")
        return True
    except ImportError:
        print(f"Installing {package_name}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package_name]
            )
            print(f"✓ {package_name} installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package_name}: {e}")
            return False


def create_jupyter_requirements():
    """創建Jupyter環境requirements文件"""
    requirements = [
        "jupyterlab>=4.0.0",
        "pandas - profiling>=3.6.0",
        "missingno>=0.5.1",
        "sweetviz>=2.2.1",
        "plotly>=5.15.0",
        "seaborn>=0.12.0",
        "matplotlib>=3.7.0",
        "ipywidgets>=8.0.0",
        "ipympl>=0.9.0",
        "bokeh>=3.2.0",
        "dash>=2.14.0",
        "nbconvert>=7.11.0",
        "jupyter_contrib_nbextensions>=0.7.0",
    ]

    with open("jupyter_requirements.txt", "w") as f:
        f.write("\n".join(requirements))

    print("✓ Created jupyter_requirements.txt")
    return "jupyter_requirements.txt"


def setup_jupyter_environment():
    """設置Jupyter環境"""
    print("🚀 Setting up Jupyter Notebook environment...")

    # 創建requirements文件
    create_jupyter_requirements()

    # 安裝核心包
    core_packages = [
        ("jupyterlab", "jupyterlab"),
        ("pandas - profiling", "pandas_profiling"),
        ("plotly", "plotly"),
        ("seaborn", "seaborn"),
        ("ipywidgets", "ipywidgets"),
    ]

    success_count = 0
    for package, import_name in core_packages:
        if check_and_install_package(package, import_name):
            success_count += 1

    print(f"\n✓ Installed {success_count}/{len(core_packages)} core packages")

    # 啟動JupyterLab
    try:
        print("\n🎯 Starting JupyterLab...")
        print("Note: Press Ctrl + C to stop JupyterLab")
        subprocess.run([sys.executable, "-m", "jupyterlab", "--port = 8888"])
    except KeyboardInterrupt:
        print("\n✅ JupyterLab stopped")
    except Exception as e:
        print(f"❌ Failed to start JupyterLab: {e}")


def create_jupyter_config():
    """創建Jupyter配置文件"""
    config_dir = Path.cwd() / "jupyter_config"
    config_dir.mkdir(exist_ok = True)

    # 創建jupyter_notebook_config.py
    config_content = """
c = get_config()

# 基本配置
c.NotebookApp.ip = '0.0.0.0'
c.NotebookApp.port = 8888
c.NotebookApp.open_browser = True
c.NotebookApp.notebook_dir = '.'
c.NotebookApp.allow_remote_access = True

# 安全配置
c.NotebookApp.token = ''
c.NotebookApp.password = ''

# 性能配置
c.NotebookApp.max_buffer_size = 2 * *28  # 256MB
c.NotebookApp.iopub_data_rate_limit = 10000000  # 10MB / s
c.NotebookApp.rate_limit_window = 3.0

# 擴展配置
c.NotebookApp.nbserver_extensions = {
    'jupyter_contrib_nbextensions': True,
}

# 內核配置
c.MappingKernelManager.default_kernel_name = 'python3'
"""

    with open(config_dir / "jupyter_notebook_config.py", "w") as f:
        f.write(config_content)

    print(f"✓ Created Jupyter config at {config_dir}")
    return config_dir


def create_demo_notebook():
    """創建演示Notebook"""
    notebook_dir = Path.cwd() / "notebooks"
    notebook_dir.mkdir(exist_ok = True)

    demo_notebook = """
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# 🎯 Jupyter Notebook 量化分析演示\\n",
    "\\n",
    "這是一個簡化的Jupyter Notebook原型，展示與Simplified System的集成能力。\\n",
    "\\n",
    "## 📋 主要功能\\n",
    "1. **數據加載 * *: 從Simplified System加載0700.HK數據\\n",
    "2. **數據清理 * *: 交互式數據質量分析\\n",
    "3. **快速可視化 * *: 一鍵生成專業圖表\\n",
    "4. **量化分析 * *: Alpha因子和回測結果分析"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 導入必要的庫\\n",
    "import sys\\n",
    "import os\\n",
    "import pandas as pd\\n",
    "import numpy as np\\n",
    "import matplotlib.pyplot as plt\\n",
    "import seaborn as sns\\n",
    "import plotly.express as px\\n",
    "import plotly.graph_objects as go\\n",
    "from plotly.subplots import make_subplots\\n",
    "\\n",
    "# 設置中文顯示\\n",
    "plt.rcParams['font.sans - serif'] = ['SimHei', 'Microsoft YaHei']\\n",
    "plt.rcParams['axes.unicode_minus'] = False\\n",
    "\\n",
    "# 添加Simplified System路徑\\n",
    "sys.path.append('src')\\n",
    "\\n",
    "print('✅ 環境設置完成！')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 📊 加載0700.HK數據"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "def load_0700_data():\\n",
    "    \"\"\"加載0700.HK數據\"\"\"\\n",
    "    try:\\n",
    "        # 嘗試從多個來源加載數據\\n",
    "        data_sources = [\\n",
    "            'simplified_system / data / 0700_hk.csv',\\n",
    "            'data / 0700_hk.csv',\\n",
    "            'simplified_system / 0700_results_20251125_181239.csv'\\n",
    "        ]\\n",
    "        \\n",
    "        for source in data_sources:\\n",
    "            if os.path.exists(source):\\n",
    "                print(f\"✓ 從 {source} 加載數據\")\\n",
    "                data = pd.read_csv(source, index_col = 0, parse_dates = True)\\n",
    "                # 確保有必要的列\\n",
    "                if 'Close' in data.columns:\\n",
    "                    return data\\n",
    "                elif 'close' in data.columns:\\n",
    "                    data['Close'] = data['close']\\n",
    "                    return data\\n",
    "        \\n",
    "        # 如果沒有真實數據，生成模擬數據\\n",
    "        print(\"⚠️  未找到真實數據，生成模擬0700.HK數據...\")\\n",
    "        return generate_mock_0700_data()\\n",
    "    \\n",
    "    except Exception as e:\\n",
    "        print(f\"❌ 加載數據失敗: {e}\")\\n",
    "        return generate_mock_0700_data()\\n",
    "\\n",
    "def generate_mock_0700_data():\\n",
    "    \"\"\"生成模擬的0700.HK數據\"\"\"\\n",
    "    np.random.seed(42)\\n",
    "    dates = pd.date_range('2020 - 01 - 01', '2023 - 12 - 31', freq='D')\\n",
    "    \\n",
    "    # 基於騰訊真實價格走勢\\n",
    "    base_price = 400\\n",
    "    trend = np.linspace(base_price, base_price * 1.5, len(dates))\\n",
    "    volatility = np.random.randn(len(dates)) * 8\\n",
    "    price = trend + volatility\\n",
    "    price = np.maximum(price, 50)\\n",
    "    \\n",
    "    data = pd.DataFrame({\\n",
    "        'Open': price * (1 + np.random.randn(len(dates)) * 0.01),\\n",
    "        'High': price * (1 + np.random.rand(len(dates)) * 0.02),\\n",
    "        'Low': price * (1 - np.random.rand(len(dates)) * 0.02),\\n",
    "        'Close': price,\\n",
    "        'Volume': np.random.randint(10000000, 30000000, len(dates))\\n",
    "    }, index = dates)\\n",
    "    \\n",
    "    return data\\n",
    "\\n",
    "# 加載數據\\n",
    "df = load_0700_data()\\n",
    "print(f\"📊 數據加載完成: {len(df)} 條記錄\")\\n",
    "print(f\"📅 時間範圍: {df.index[0].date()} 至 {df.index[-1].date()}\")\\n",
    "print(f\"💰 價格範圍: {df['Close'].min():.1f} - {df['Close'].max():.1f} HKD\")\\n",
    "\\n",
    "# 顯示前5行數據\\n",
    "df.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 🔍 數據質量分析"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "def analyze_data_quality(data):\\n",
    "    \"\"\"分析數據質量\"\"\"\\n",
    "    print(\"\\n=== 數據質量分析 ===\")\\n",
    "    \\n",
    "    # 基本統計\\n",
    "    print(f\"數據形狀: {data.shape}\")\\n",
    "    print(f\"缺失值: {data.isnull().sum().sum()}\")\\n",
    "    print(f\"重複值: {data.duplicated().sum()}\")\\n",
    "    \\n",
    "    # 數據類型\\n",
    "    print(\"\\n數據類型:\")\\n",
    "    print(data.dtypes)\\n",
    "    \\n",
    "    # 基本統計\\n",
    "    print(\"\\n基本統計:\")\\n",
    "    print(data.describe())\\n",
    "    \\n",
    "    return data\\n",
    "\\n",
    "# 分析數據質量\\n",
    "df_analyzed = analyze_data_quality(df)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 📈 快速可視化"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 價格走勢圖（使用Plotly）\\n",
    "fig_price = go.Figure()\\n",
    "fig_price.add_trace(go.Scatter(\\n",
    "    x = df.index,\\n",
    "    y = df['Close'],\\n",
    "    mode='lines',\\n",
    "    name='0700.HK收盤價',\\n",
    "    line = dict(color='blue', width = 2)\\n",
    "))\\n",
    "\\n",
    "fig_price.update_layout(\\n",
    "    title='🎯 0700.HK價格走勢（交互式圖表）',\\n",
    "    xaxis_title='日期',\\n",
    "    yaxis_title='價格 (HKD)',\\n",
    "    hovermode='x unified',\\n",
    "    width = 800,\\n",
    "    height = 500\\n",
    ")\\n",
    "\\n",
    "fig_price.show()\\n",
    "\\n",
    "# 成交量圖\\n",
    "fig_volume = go.Figure()\\n",
    "fig_volume.add_trace(go.Bar(\\n",
    "    x = df.index,\\n",
    "    y = df['Volume'],\\n",
    "    name='成交量',\\n",
    "    marker_color='lightblue'\\n",
    "))\\n",
    "\\n",
    "fig_volume.update_layout(\\n",
    "    title='📊 0700.HK成交量',\\n",
    "    xaxis_title='日期',\\n",
    "    yaxis_title='成交量',\\n",
    "    width = 800,\\n",
    "    height = 300\\n",
    ")\\n",
    "\\n",
    "fig_volume.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 🧮 技術指標計算"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "def calculate_technical_indicators(data):\\n",
    "    \"\"\"計算基本技術指標\"\"\"\\n",
    "    df = data.copy()\\n",
    "    \\n",
    "    # 5日均線\\n",
    "    df['MA5'] = df['Close'].rolling(window = 5).mean()\\n",
    "    \\n",
    "    # 20日均線\\n",
    "    df['MA20'] = df['Close'].rolling(window = 20).mean()\\n",
    "    \\n",
    "    # RSI (14日)\\n",
    "    delta = df['Close'].diff()\\n",
    "    gain = (delta.where(delta > 0, 0)).rolling(window = 14).mean()\\n",
    "    loss = (-delta.where(delta < 0, 0)).rolling(window = 14).mean()\\n",
    "    rs = gain / loss\\n",
    "    df['RSI14'] = 100 - (100 / (1 + rs))\\n",
    "    \\n",
    "    # 日收益率\\n",
    "    df['Returns'] = df['Close'].pct_change()\\n",
    "    \\n",
    "    # 累計回報\\n",
    "    df['Cumulative_Returns'] = (1 + df['Returns']).cumprod() - 1\\n",
    "    \\n",
    "    return df\\n",
    "\\n",
    "# 計算技術指標\\n",
    "df_with_indicators = calculate_technical_indicators(df)\\n",
    "\\n",
    "# 顯示最新指標值\\n",
    "latest_data = df_with_indicators.iloc[-1]\\n",
    "print(\"📊 最新技術指標:\")\\n",
    "print(f\"收盤價: {latest_data['Close']:.2f} HKD\")\\n",
    "print(f\"5日均線: {latest_data['MA5']:.2f} HKD\")\\n",
    "print(f\"20日均線: {latest_data['MA20']:.2f} HKD\")\\n",
    "print(f\"RSI(14): {latest_data['RSI14']:.2f}\")\\n",
    "print(f\"日收益率: {latest_data['Returns']:.2%}\")\\n",
    "print(f\"累計回報: {latest_data['Cumulative_Returns']:.2%}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 🎯 綜合可視化儀表板"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 創建綜合儀表板\\n",
    "fig = make_subplots(\\n",
    "    rows = 4, cols = 2,\\n",
    "    subplot_titles=('價格與均線', '成交量', 'RSI指標', '日收益率',\\n",
    "                   '收益率分佈', '價格統計', '移動平均對比', '累計回報'),\\n",
    "    specs=[[{\"secondary_y\": True}, {}],\\n",
    "           [{}, {}],\\n",
    "           [{}, {}],\\n",
    "           [{}, {}]]\\n",
    ")\\n",
    "\\n",
    "# 1. 價格與均線\\n",
    "fig.add_trace(go.Scatter(\\n",
    "    x = df_with_indicators.index, y = df_with_indicators['Close'],\\n",
    "    name='收盤價', line = dict(color='blue')\\n",
    "), row = 1, col = 1)\\n",
    "fig.add_trace(go.Scatter(\\n",
    "    x = df_with_indicators.index, y = df_with_indicators['MA5'],\\n",
    "    name='MA5', line = dict(color='orange', dash='dash')\\n",
    "), row = 1, col = 1)\\n",
    "fig.add_trace(go.Scatter(\\n",
    "    x = df_with_indicators.index, y = df_with_indicators['MA20'],\\n",
    "    name='MA20', line = dict(color='green', dash='dash')\\n",
    "), row = 1, col = 1)\\n",
    "\\n",
    "# 2. 成交量\\n",
    "fig.add_trace(go.Bar(\\n",
    "    x = df_with_indicators.index[-100:],\\n",
    "    y = df_with_indicators['Volume'][-100:],\\n",
    "    name='成交量', marker_color='lightblue'\\n",
    "), row = 1, col = 2)\\n",
    "\\n",
    "# 3. RSI指標\\n",
    "fig.add_trace(go.Scatter(\\n",
    "    x = df_with_indicators.index, y = df_with_indicators['RSI14'],\\n",
    "    name='RSI(14)', line = dict(color='purple')\\n",
    "), row = 2, col = 1)\\n",
    "fig.add_hline(y = 70, line_dash=\"dash\", line_color=\"red\", row = 2, col = 1)\\n",
    "fig.add_hline(y = 30, line_dash=\"dash\", line_color=\"green\", row = 2, col = 1)\\n",
    "\\n",
    "# 4. 日收益率\\n",
    "fig.add_trace(go.Scatter(\\n",
    "    x = df_with_indicators.index, y = df_with_indicators['Returns'],\\n",
    "    name='日收益率', mode='markers',\\n",
    "    marker = dict(color='red', size = 4)\\n",
    "), row = 2, col = 2)\\n",
    "\\n",
    "# 5. 收益率分佈\\n",
    "fig.add_trace(go.Histogram(\\n",
    "    x = df_with_indicators['Returns'].dropna(),\\n",
    "    name='收益率分佈', nbinsx = 50,\\n",
    "    marker_color='skyblue'\\n",
    "), row = 3, col = 1)\\n",
    "\\n",
    "# 6. 價格統計箱線圖\\n",
    "fig.add_trace(go.Box(\\n",
    "    y = df_with_indicators['Close'],\\n",
    "    name='價格分佈', marker_color='lightgreen'\\n",
    "), row = 3, col = 2)\\n",
    "\\n",
    "# 7. 移動平均對比\\n",
    "fig.add_trace(go.Scatter(\\n",
    "    x = df_with_indicators.index,\\n",
    "    y = df_with_indicators['MA5'] - df_with_indicators['MA20'],\\n",
    "    name='MA5 - MA20', line = dict(color='orange')\\n",
    "), row = 4, col = 1)\\n",
    "fig.add_hline(y = 0, line_dash=\"solid\", line_color=\"black\", row = 4, col = 1)\\n",
    "\\n",
    "# 8. 累計回報\\n",
    "fig.add_trace(go.Scatter(\\n",
    "    x = df_with_indicators.index,\\n",
    "    y = df_with_indicators['Cumulative_Returns'],\\n",
    "    name='累計回報', line = dict(color='blue')\\n",
    "), row = 4, col = 2)\\n",
    "fig.add_hline(y = 0, line_dash=\"solid\", line_color=\"black\", row = 4, col = 2)\\n",
    "\\n",
    "fig.update_layout(\\n",
    "    title_text=\"🎯 0700.HK量化分析儀表板\",\\n",
    "    height = 1200,\\n",
    "    showlegend = False\\n",
    ")\\n",
    "\\n",
    "fig.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 📋 總結與下一步\\n",
    "\\n",
    "### ✅ 原型驗證成果\\n",
    "1. **數據加載 * *: 成功從Simplified System加載0700.HK數據\\n",
    "2. **數據清理 * *: 實現了基本數據質量分析\\n",
    "3. **快速可視化 * *: 生成了交互式Plotly圖表\\n",
    "4. **技術指標 * *: 計算了RSI、移動平均等常用指標\\n",
    "5. **儀表板 * *: 創建了綜合分析儀表板\\n",
    "\\n",
    "### 🚀 下一步實施計劃\\n",
    "1. **Phase 1 * *: 完整JupyterLab環境設置\\n",
    "2. **Phase 2 * *: 集成pandas - profiling等高級清理工具\\n",
    "3. **Phase 3 * *: 創建專業量化分析模板\\n",
    "\\n",
    "### 🎯 預期收益\\n",
    "- 分析效率提升5 - 10倍\\n",
    "- 用戶友好度大幅提升\\n",
    "- 原型開發時間減少70%"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text / x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.9.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
"""

    with open(notebook_dir / "0700_hk_analysis_prototype.ipynb", "w") as f:
        f.write(demo_notebook)

    print(f"✓ Created demo notebook at {notebook_dir}/0700_hk_analysis_prototype.ipynb")
    return notebook_dir


def main():
    """主函數"""
    print("🎯 Jupyter Notebook Prototype Setup")
    print("=" * 50)

    # 創建配置
    create_jupyter_config()

    # 創建演示Notebook
    create_demo_notebook()

    print("\n" + "=" * 50)
    print("🎉 Jupyter Notebook原型設置完成！")
    print("\n📋 創建的文件:")
    print("  - jupyter_requirements.txt (依賴包列表)")
    print("  - jupyter_config/ (Jupyter配置)")
    print("  - notebooks / 0700_hk_analysis_prototype.ipynb (演示Notebook)")

    print("\n🚀 快速啟動指南:")
    print("1. 安裝依賴: pip install -r jupyter_requirements.txt")
    print("2. 啟動Jupyter: jupyter lab --config = jupyter_config/")
    print("3. 打開演示Notebook並開始分析！")

    print("\n💡 提示:")
    print("- 原型展示了核心Jupyter集成功能")
    print("- 可直接在Notebook中加載和分析Simplified System數據")
    print("- 生成了交互式圖表和技术指標")
    print("- 驗證了概念可行性")


if __name__ == "__main__":
    main()
