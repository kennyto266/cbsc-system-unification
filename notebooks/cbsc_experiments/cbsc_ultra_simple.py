import marimo as mo

app = marimo.App(width="medium")

@app.cell
def __():
    import marimo as mo
    import pandas as pd
    from pathlib import Path

    return mo, pd, Path

@app.cell
def __(mo, pd, Path):
    sentiment_path = "CODEX--/warrant_sentiment_daily.csv"
    data_exists = Path(sentiment_path).exists()

    if data_exists:
        try:
            df = pd.read_csv(sentiment_path)
            df['Date'] = pd.to_datetime(df['Date'])

            # 基本清理
            df = df.dropna(subset=['Date', 'Afternoon_Close'])

            # 計算情緒強度
            df['Total_Turnover'] = df.get('Bull_Turnover_HKD', 0) + df.get('Bear_Turnover_HKD', 0)
            df['Sentiment_Strength'] = (df.get('Bull_Turnover_HKD', 0) - df.get('Bear_Turnover_HKD', 0)) / df['Total_Turnover'].replace(0, 1)

            success_msg = mo.md(f"""
            ✅ **CBSC數據加載成功**

            - 記錄數量: {len(df)}
            - 日期範圍: {df['Date'].min().strftime('%Y-%m-%d')} 至 {df['Date'].max().strftime('%Y-%m-%d')}
            - 平均情緒強度: {df['Sentiment_Strength'].mean():.3f}
            """)

        except Exception as e:
            df = pd.DataFrame()
            success_msg = mo.md(f"❌ 加載錯誤: {str(e)}")
    else:
        df = pd.DataFrame()
        success_msg = mo.md("❌ 數據文件未找到")

    return success_msg, df

@app.cell
def __(mo):
    rsi_period = mo.ui.slider(5, 50, value=14, label="RSI 週期")
    sentiment_threshold = mo.ui.slider(0.1, 1.0, value=0.7, step=0.05, label="情緒閾值")

    return rsi_period, sentiment_threshold

@app.cell
def __(df, rsi_period, sentiment_threshold, mo):
    if df.empty:
        return mo.md("⚠️ 無數據可處理")

    import numpy as np

    # 簡單RSI計算
    df_calc = df.copy()
    df_calc['Returns'] = df_calc['Afternoon_Close'].pct_change()

    delta = df_calc['Afternoon_Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period.value).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period.value).mean()
    rs = gain / loss.where(loss != 0, 1)
    df_calc['RSI'] = 100 - (100 / (1 + rs))

    # 簡單策略
    df_calc['Signal'] = np.where(
        (df_calc['RSI'] < 30) & (df_calc['Sentiment_Strength'] > sentiment_threshold.value),
        "買入",
        np.where((df_calc['RSI'] > 70) & (df_calc['Sentiment_Strength'] < -sentiment_threshold.value),
                 "賣出", "持有")
    )

    signal_counts = df_calc['Signal'].value_counts()

    result = mo.md(f"""
    ## 📊 策略結果

    **當前參數:**
    - RSI週期: {rsi_period.value}
    - 情緒閾值: {sentiment_threshold.value}

    **信號統計:**
    - 買入: {signal_counts.get('買入', 0)} 次
    - 賣出: {signal_counts.get('賣出', 0)} 次
    - 持有: {signal_counts.get('持有', 0)} 次

    **數據概況:**
    - 平均RSI: {df_calc['RSI'].mean():.1f}
    - 情緒強度範圍: {df_calc['Sentiment_Strength'].min():.3f} 至 {df_calc['Sentiment_Strength'].max():.3f}
    """)

    return result

if __name__ == "__main__":
    app.run()