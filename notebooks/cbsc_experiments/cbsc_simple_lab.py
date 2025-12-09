# /// script
# requires-python = ">=3.9"
# dependencies = ["marimo", "pandas", "numpy", "yfinance"]
# ///

import marimo as mo
import pandas as pd
import numpy as np
from pathlib import Path

app = marimo.App()

@app.cell
def __(mo):
    """CBSC 策略研究實驗室"""

    title = mo.md("""
    # 🎯 CBSC 策略研究實驗室

    **極簡實施 - 2天最小風險方案**

    使用現有CBSC系統，不修改生產代碼。
    """)

    return title

@app.cell
def __(mo):
    """數據文件檢查"""

    sentiment_path = "CODEX--/warrant_sentiment_daily.csv"
    data_exists = Path(sentiment_path).exists()

    if data_exists:
        status = mo.md("✅ **CBSC數據文件已找到**")
    else:
        status = mo.md("❌ **CBSC數據文件未找到**")

    return status, sentiment_path, data_exists

@app.cell
def __(data_exists, mo):
    """策略參數設置"""

    if not data_exists:
        return mo.md("⚠️ 請確保CBSC數據文件存在後再繼續")

    rsi_period = mo.ui.slider(5, 50, value=14, label="RSI 週期")
    sentiment_threshold = mo.ui.slider(0.1, 1.0, value=0.7, step=0.05, label="情緒閾值")

    return rsi_period, sentiment_threshold

@app.cell
def __(sentiment_path, data_exists, mo):
    """數據加載"""

    if not data_exists:
        return mo.md("⚠️ 無法加載數據")

    try:
        # 簡化的數據加載 - 模擬現有data_loader功能
        df = pd.read_csv(sentiment_path)
        df['Date'] = pd.to_datetime(df['Date'])

        # 基本計算
        df['Total_Turnover'] = df['Bull_Turnover_HKD'] + df['Bear_Turnover_HKD']
        df['Sentiment_Strength'] = (df['Bull_Turnover_HKD'] - df['Bear_Turnover_HKD']) / df['Total_Turnover']

        success_msg = mo.md(f"""
        ✅ **數據加載成功！**

        - 記錄數量: {len(df)} 條
        - 日期範圍: {df['Date'].min().strftime('%Y-%m-%d')} 至 {df['Date'].max().strftime('%Y-%m-%d')}
        """)

        return success_msg, df

    except Exception as e:
        return mo.md(f"❌ **加載錯誤**: {str(e)}"), pd.DataFrame()

@app.cell
def __(df, rsi_period, sentiment_threshold, mo):
    """策略計算"""

    if df.empty:
        return mo.md("⚠️ 無數據可處理")

    # 簡化策略邏輯
    df['MA_5'] = df['Afternoon_Close'].rolling(5).mean()
    df['MA_20'] = df['Afternoon_Close'].rolling(20).mean()

    # 生成信號
    df['Signal'] = np.where(
        (df['MA_5'] > df['MA_20']) & (df['Sentiment_Strength'] > sentiment_threshold.value),
        "買入",
        np.where(
            (df['MA_5'] < df['MA_20']) & (df['Sentiment_Strength'] < -sentiment_threshold.value),
            "賣出",
            "持有"
        )
    )

    # 性能統計
    signal_counts = df['Signal'].value_counts()

    result = mo.md(f"""
    ## 📊 策略結果

    **當前參數:**
    - RSI週期: {rsi_period.value}
    - 情緒閾值: {sentiment_threshold.value}

    **信號統計:**
    - 買入: {signal_counts.get('買入', 0)} 次
    - 賣出: {signal_counts.get('賣出', 0)} 次
    - 持有: {signal_counts.get('持有', 0)} 次
    """)

    return result

if __name__ == "__main__":
    app.run()